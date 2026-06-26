"""
Opera Aria — OpenAI-compatible variant.

Mirrors :class:`llm4free.opera_aria` (the regular llm4free provider)
but exposes an ``OpenAICompatibleProvider`` interface so it can be used
wherever an ``openai.chat.completions.create`` shape is expected:

    from llm4free.llm.opera_aria import OperaAria
    client = OperaAria()
    resp = client.chat.completions.create(
        model="aria",
        messages=[{"role": "user", "content": "Tell me a joke"}],
    )
    print(resp.choices[0].message.content)

The underlying wire protocol is the same as the regular provider — see
``llm4free/Provider/OperaAria.py`` for the full reverse-engineering notes
(anonymous 3-step OAuth signup, v1/v2 endpoints, SSE response format).

Differences from the regular llm4free ``OperaAria``:

* Streaming yields ``ChatCompletionChunk`` objects with token-level
  ``ChoiceDelta`` updates.
* Non-streaming returns a single ``ChatCompletion`` whose
  ``choices[0].message.content`` holds the full reply.
* The OperaAria-specific conversation id is captured into the
  client's internal state for follow-up turns, but the public
  ``create()`` API is one-shot per call (matches the OpenAI surface).
"""

import base64
import json
import os
import time
from typing import Any, Dict, Generator, List, Optional, Union

from curl_cffi import CurlError
from curl_cffi import requests

from llm4free.llm.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from llm4free.llm.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
)

BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"


def _approx_tokens(text: str) -> int:
    """Fallback token estimator when ``tiktoken`` is unavailable.

    Rough heuristic: ~4 characters per token. Used purely for the
    ``usage`` accounting fields in the OpenAI-compat response — accuracy
    doesn't matter, just non-zero values that the client code can read.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


# ──────────────────────────────────────────────────────────────────────
#  Per-instance auth state
# ──────────────────────────────────────────────────────────────────────


class _OperaAriaState:
    """Mirrors the g4f Conversation dataclass but is a plain class so it
    can sit on the llm4free client instance without dragging in any g4f
    types.

    Captures:
    * the long-lived refresh_token (rotated only when the OAuth server
      invalidates it),
    * the short-lived access_token and its expiry,
    * the per-session encryption_key the v1/v2 payloads must contain,
    * the conversation_id returned by the server on turns after the
      first, so follow-up messages stay in the same thread.
    """

    def __init__(self, refresh_token: Optional[str] = None) -> None:
        self.refresh_token = refresh_token
        self.access_token: Optional[str] = None
        self.expires_at: float = 0.0
        self.conversation_id: Optional[str] = None
        self.is_first_request: bool = True
        self.encryption_key = base64.b64encode(os.urandom(32)).decode("utf-8")

    def is_token_expired(self) -> bool:
        return time.time() >= self.expires_at

    def update_token(self, access_token: str, expires_in: int) -> None:
        self.access_token = access_token
        self.expires_at = time.time() + max(1, int(expires_in)) - 60


# ──────────────────────────────────────────────────────────────────────
#  OpenAI-compat completions class
# ──────────────────────────────────────────────────────────────────────


class Completions(BaseCompletions):
    def __init__(self, client: "OperaAria"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """Mimics ``openai.chat.completions.create``.

        System messages are dropped — Opera Aria's wire format only
        carries a single ``query`` string and we extract the last user
        message from ``messages``.
        """
        model = self._client.convert_model_name(model)
        version = self._client._api_version(model)
        prompt = self._client._last_user_text(messages)

        request_id = f"chatcmpl-{self._client._uuid()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(
                request_id, created_time, model, prompt, version, timeout, proxies
            )
        return self._create_non_stream(
            request_id, created_time, model, prompt, version, timeout, proxies
        )

    # ── streaming ─────────────────────────────────────────────────

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        prompt: str,
        version: str,
        timeout: Optional[int],
        proxies: Optional[Dict[str, str]],
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            access_token = self._client.get_access_token()
            headers = self._client._build_headers(access_token, version)
            payload = self._client._build_payload(prompt, version)

            response = self._client.session.post(
                self._client._api_endpoint(version),
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),  # ty:ignore[invalid-argument-type]
            )
            response.raise_for_status()

            # Rough token estimate up front; we'll refine as we yield.
            prompt_tokens = self._client._safe_count(prompt)
            completion_tokens = 0
            finish_reason = None

            skip_next = False
            for raw_line in response.iter_lines():
                if raw_line is None:
                    continue
                if isinstance(raw_line, bytes):
                    raw_line = raw_line.decode("utf-8", errors="replace")
                event_type, payload_obj = self._client._parse_sse(raw_line)
                if event_type == "thinking_status":
                    skip_next = True
                    continue
                if skip_next:
                    skip_next = False
                    continue
                if payload_obj is None:
                    continue

                text, image_url = self._client._extract_content(payload_obj, version)
                if text:
                    completion_tokens += self._client._safe_count(text)
                chunk_text = text or (f"[image: {image_url}]" if image_url else "")
                if not chunk_text:
                    # Still check for conversation id even on empty events
                    cid = self._client._extract_conversation_id(payload_obj, version)
                    if cid:
                        self._client._state.conversation_id = cid
                    continue

                delta = ChoiceDelta(content=chunk_text, role="assistant", tool_calls=None)
                choice = Choice(index=0, delta=delta, finish_reason=None, logprobs=None)
                chunk = ChatCompletionChunk(
                    id=request_id,
                    choices=[choice],
                    created=created_time,
                    model=model,
                    system_fingerprint=None,
                )
                if hasattr(chunk, "model_dump"):
                    chunk_dict = chunk.model_dump(exclude_none=True)
                else:
                    chunk_dict = chunk.dict(exclude_none=True)
                chunk_dict["usage"] = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "estimated_cost": None,
                }
                yield chunk

                cid = self._client._extract_conversation_id(payload_obj, version)
                if cid:
                    self._client._state.conversation_id = cid

            # Final stop chunk
            delta = ChoiceDelta(content=None, role=None, tool_calls=None)
            choice = Choice(
                index=0,
                delta=delta,
                finish_reason=finish_reason or "stop",
                logprobs=None,
            )
            stop_chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                system_fingerprint=None,
            )
            if hasattr(stop_chunk, "model_dump"):
                stop_dict = stop_chunk.model_dump(exclude_none=True)
            else:
                stop_dict = stop_chunk.dict(exclude_none=True)
            stop_dict["usage"] = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "estimated_cost": None,
            }
            yield stop_chunk

        except Exception as e:
            print(f"Error during OperaAria stream request: {e}")
            raise IOError(f"OperaAria request failed: {e}") from e

    # ── non-streaming ─────────────────────────────────────────────

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        prompt: str,
        version: str,
        timeout: Optional[int],
        proxies: Optional[Dict[str, str]],
    ) -> ChatCompletion:
        try:
            access_token = self._client.get_access_token()
            headers = self._client._build_headers(access_token, version)
            payload = self._client._build_payload(prompt, version)

            response = self._client.session.post(
                self._client._api_endpoint(version),
                headers=headers,
                json=payload,
                stream=True,  # the API only streams, we collect
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),  # ty:ignore[invalid-argument-type]
            )
            response.raise_for_status()

            full_text = ""
            skip_next = False
            for raw_line in response.iter_lines():
                if raw_line is None:
                    continue
                if isinstance(raw_line, bytes):
                    raw_line = raw_line.decode("utf-8", errors="replace")
                event_type, payload_obj = self._client._parse_sse(raw_line)
                if event_type == "thinking_status":
                    skip_next = True
                    continue
                if skip_next:
                    skip_next = False
                    continue
                if payload_obj is None:
                    continue
                text, image_url = self._client._extract_content(payload_obj, version)
                if text:
                    full_text += text
                elif image_url:
                    full_text += f"[image: {image_url}]"

                cid = self._client._extract_conversation_id(payload_obj, version)
                if cid:
                    self._client._state.conversation_id = cid

            self._client._state.is_first_request = False

            prompt_tokens = self._client._safe_count(prompt)
            completion_tokens = self._client._safe_count(full_text)
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )
            message = ChatCompletionMessage(role="assistant", content=full_text)
            choice = Choice(index=0, message=message, finish_reason="stop", logprobs=None)
            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
                system_fingerprint=None,
            )
            return completion

        except Exception as e:
            print(f"Error during OperaAria non-stream request: {e}")
            raise IOError(f"OperaAria request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "OperaAria"):
        self.completions = Completions(client)


# ──────────────────────────────────────────────────────────────────────
#  Public client
# ──────────────────────────────────────────────────────────────────────


class OperaAria(OpenAICompatibleProvider):
    """OpenAI-compatible client for Opera Aria.

    Usage::

        client = OperaAria()
        response = client.chat.completions.create(
            model="aria",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response.choices[0].message.content)
    """

    required_auth = False

    # Endpoints
    API_ENDPOINT_V1 = "https://composer.opera-api.com/api/v1/a-chat"
    API_ENDPOINT_V2 = "https://composer.opera-api.com/api/v2/a-chat"
    TOKEN_ENDPOINT = "https://oauth2.opera-api.com/oauth2/v1/token/"
    SIGNUP_ENDPOINT = "https://auth.opera.com/account/v2/external/anonymous/signup"

    _USER_AGENT_V1 = (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36 OPR/89.0.0.0"
    )
    _USER_AGENT_V2 = (
        "Mozilla/5.0 (Linux; U; Android 8.1.0; DRA-L21 Build/HUAWEIDRA-L21; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
        "Chrome/138.0.7204.179 Mobile Safari/537.36 OPR/99.0.2254.81922"
    )

    AVAILABLE_MODELS = ["aria", "aria-legacy"]
    _MODEL_TO_VERSION = {"aria": "v2", "aria-legacy": "v1"}

    def __init__(self, timeout: int = 60, refresh_token: Optional[str] = None):
        self.timeout = timeout
        self.proxies: Optional[Dict[str, str]] = None
        self.session = requests.Session(impersonate="chrome110")
        self._state = _OperaAriaState(refresh_token=refresh_token)
        # Eagerly authenticate so the first chat call doesn't pay the
        # 3-step signup latency.
        try:
            self.get_access_token()
        except Exception:
            # Fall back to lazy auth in create() if signup fails here
            pass
        self.chat = Chat(self)

    # ── helpers exposed for Completions ────────────────────────────

    def _uuid(self) -> str:
        import uuid
        return uuid.uuid4().hex

    def _safe_count(self, text: str) -> int:
        """Count tokens via ``tiktoken`` if installed, else the
        character-based fallback. Keeps the provider usable in slim
        installs that don't have the optional ``tiktoken`` dep."""
        try:
            return count_tokens(text)
        except (ImportError, ModuleNotFoundError, OSError):
            return _approx_tokens(text)

    def _api_version(self, model: str) -> str:
        return self._MODEL_TO_VERSION.get(model, "v2")

    def _api_endpoint(self, version: str) -> str:
        return self.API_ENDPOINT_V1 if version == "v1" else self.API_ENDPOINT_V2

    def convert_model_name(self, model: str) -> str:
        if not model:
            return "aria"
        return model if model in self.AVAILABLE_MODELS else "aria"

    @staticmethod
    def _last_user_text(messages: List[Dict[str, str]]) -> str:
        """Opera Aria takes a single query string — pull the last user
        message and ignore everything else."""
        for m in reversed(messages):
            if m.get("role") == "user":
                content = m.get("content", "")
                if isinstance(content, str):
                    return content
        return ""

    # ── auth (mirrors llm4free/Provider/OperaAria.py) ─────────────

    def _generate_refresh_token(self) -> str:
        auth_headers = {
            "User-Agent": "okhttp/5.3.2",
            "Content-Type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
            "x-opera-client-cache": "1",
        }

        r1 = self.session.post(
            self.TOKEN_ENDPOINT,
            headers=auth_headers,
            data={
                "client_id": "mini-client",
                "client_secret": (
                    "Pcc5NvlCrxl02pMw32kO6WrnhpS0pUZ95YrDP8XNKJJQvFht4wQDkFJ7v9x5hn7C"
                ),
                "grant_type": "client_credentials",
                "scope": "anonymous_account",
            },
            timeout=self.timeout,
        )
        r1.raise_for_status()
        anon_token = r1.json().get("access_token")
        if not anon_token:
            raise IOError(f"OperaAria: step-1 (client_credentials) returned no access_token: {r1.text[:200]}")

        r2 = self.session.post(
            self.SIGNUP_ENDPOINT,
            headers={
                **auth_headers,
                "Authorization": f"Bearer {anon_token}",
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={"client_id": "mini"},
            timeout=self.timeout,
        )
        r2.raise_for_status()
        auth_token = r2.json().get("token")
        if not auth_token:
            raise IOError(f"OperaAria: step-2 (anonymous signup) returned no auth_token: {r2.text[:200]}")

        r3 = self.session.post(
            self.TOKEN_ENDPOINT,
            headers=auth_headers,
            data={
                "auth_token": auth_token,
                "client_id": "mini",
                "grant_type": "auth_token",
                "scope": "shodan:aria",
            },
            timeout=self.timeout,
        )
        r3.raise_for_status()
        refresh_token = r3.json().get("refresh_token")
        if not refresh_token:
            raise IOError(f"OperaAria: step-3 (auth_token grant) returned no refresh_token: {r3.text[:200]}")
        return refresh_token

    def get_access_token(self) -> str:
        if not self._state.refresh_token:
            self._state.refresh_token = self._generate_refresh_token()
        if self._state.access_token and not self._state.is_token_expired():
            return self._state.access_token  # type: ignore[return-value]

        r = self.session.post(
            self.TOKEN_ENDPOINT,
            headers={
                "User-Agent": "okhttp/5.3.2",
                "Content-Type": "application/x-www-form-urlencoded",
                "x-requested-with": "XMLHttpRequest",
                "x-opera-client-cache": "1",
            },
            data={
                "client_id": "mini",
                "grant_type": "refresh_token",
                "refresh_token": self._state.refresh_token,
                "scope": "shodan:aria",
            },
            timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        if not token:
            # Refresh token likely expired — re-signup once
            self._state.refresh_token = self._generate_refresh_token()
            return self.get_access_token()
        self._state.update_token(token, int(data.get("expires_in", 3600)))
        return token

    def _build_headers(self, access_token: str, version: str) -> Dict[str, str]:
        if version == "v1":
            return {
                "Accept": "text/event-stream",
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Origin": "opera-aria://ui",
                "User-Agent": self._USER_AGENT_V1,
                "X-Opera-Timezone": "+02:00",
                "X-Opera-UI-Language": "en",
            }
        return {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Origin": "https://composer.opera-api.com",
            "Referer": "https://composer.opera-api.com/assets/aria/index.html",
            "User-Agent": self._USER_AGENT_V2,
            "X-Opera-Timezone": "+02:00",
            "X-Opera-UI-Language": "en",
            "X-Requested-With": "com.opera.mini.native",
        }

    def _build_payload(self, prompt: str, version: str) -> Dict[str, Any]:
        if version == "v1":
            data: Dict[str, Any] = {
                "query": prompt,
                "stream": True,
                "linkify": True,
                "linkify_version": 3,
                "sia": True,
                "media_attachments": [],
                "encryption": {"key": self._state.encryption_key},
            }
        else:
            data = {
                "query": prompt,
                "sia": True,
                "think_harder": False,
                "supported_features": [],
                "file_attachments": [],
                "encryption": {"key": self._state.encryption_key},
            }
        if not self._state.is_first_request and self._state.conversation_id:
            data["conversation_id"] = self._state.conversation_id
        return data

    # ── SSE helpers (also used by Completions) ─────────────────────

    @staticmethod
    def _parse_sse(line: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        line = line.strip()
        if line.startswith("event:"):
            return line[6:].strip(), None
        if line.startswith("data:"):
            content = line[5:].strip()
            if content in ("[DONE]", "null", ""):
                return None, None
            try:
                return None, json.loads(content)
            except json.JSONDecodeError:
                return None, None
        return None, None

    @staticmethod
    def _extract_content(
        data: Dict[str, Any], version: str
    ) -> tuple[Optional[str], Optional[str]]:
        if version == "v1":
            msg = data.get("message")
            return (msg, None) if isinstance(msg, str) else (None, None)
        response = data.get("response")
        if not isinstance(response, dict):
            return None, None
        if response.get("content_type") == "image":
            image_url = response.get("image_url")
            return None, image_url if isinstance(image_url, str) else None
        text = response.get("message")
        return (text, None) if isinstance(text, str) else (None, None)

    @staticmethod
    def _extract_conversation_id(
        data: Dict[str, Any], version: str
    ) -> Optional[str]:
        if version == "v1":
            cid = data.get("conversation_id")
            return cid if isinstance(cid, str) else None
        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            cid = metadata.get("conversation_id")
            return cid if isinstance(cid, str) else None
        return None

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    client = OperaAria()
    response = client.chat.completions.create(
        model="aria",
        messages=[{"role": "user", "content": "Tell me a joke"}],
    )
    if isinstance(response, ChatCompletion):
        message = response.choices[0].message
        print(message.content if message else "")
