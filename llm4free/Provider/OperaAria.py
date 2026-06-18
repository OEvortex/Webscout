"""
Opera Aria provider for llm4free.

Implements access to Opera's AI assistant "Aria" through Opera's internal
``composer.opera-api.com`` endpoints. The implementation is ported from
xtekky/gpt4free's ``g4f/Provider/OperaAria.py`` and rewritten in llm4free's
synchronous ``curl_cffi`` style (the g4f version is ``aiohttp``-async).

**No API key required.** Aria is reached via an anonymous signup flow that
issues a refresh token, which is then exchanged for short-lived access
tokens per request.

Models
------
* ``aria``         — v2 endpoint (newer, default)
* ``aria-legacy``  — v1 endpoint (older)

Both endpoints stream ``text/event-stream`` replies; the v2 endpoint can
also generate images which we surface as plain image URLs in the response
text.

This file deliberately omits the g4f v2 file-upload pipeline. Aria's
v2 image-upload is a 3-step GCS signed-URL flow (upload → poll → attach)
that doesn't add value for the text-only chat use case the rest of
llm4free targets. Add it back if a future TTI provider needs it.
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from llm4free import exceptions
from llm4free.AIbase import Provider, Response, Tool
from llm4free.AIutel import (
    AwesomePrompts,
    Conversation,
    Optimizers,
)


# ──────────────────────────────────────────────────────────────────────
#  Conversation state (refresh token, access token, encryption key)
# ──────────────────────────────────────────────────────────────────────


class OperaAriaConversation:
    """Holds per-session credentials and the conversation id.

    Mirrors the ``Conversation`` dataclass from g4f/Provider/OperaAria.py
    but is implemented as a plain class so it can be embedded in a
    llm4free ``Provider`` instance without the g4f JsonConversation
    machinery.
    """

    def __init__(self, refresh_token: Optional[str] = None) -> None:
        self.refresh_token = refresh_token
        self.access_token: Optional[str] = None
        self.expires_at: float = 0.0
        self.conversation_id: Optional[str] = None
        self.is_first_request: bool = True
        # Random 32-byte base64 key the server expects in the payload
        self.encryption_key = base64.b64encode(os.urandom(32)).decode("utf-8")

    def is_token_expired(self) -> bool:
        return time.time() >= self.expires_at

    def update_token(self, access_token: str, expires_in: int) -> None:
        self.access_token = access_token
        # 60s buffer so we don't race the server's clock
        self.expires_at = time.time() + max(1, int(expires_in)) - 60


# ──────────────────────────────────────────────────────────────────────
#  Provider
# ──────────────────────────────────────────────────────────────────────


class OperaAria(Provider):
    """Sync llm4free provider for Opera Aria.

    Example::

        from llm4free.Provider.OperaAria import OperaAria
        ai = OperaAria()
        print(ai.chat("Tell me a joke"))
    """

    label = "Opera Aria"
    required_auth = False

    # Endpoints (publicly documented in g4f)
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
    DEFAULT_MODEL = "aria"
    _MODEL_TO_VERSION = {"aria": "v2", "aria-legacy": "v1"}

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 60,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        system_prompt: str = "You are a helpful assistant.",
        refresh_token: Optional[str] = None,
        tools: Optional[list[Tool]] = None,
    ) -> None:
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model!r}. Choose from: {self.AVAILABLE_MODELS}"
            )

        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response: Dict[str, Any] = {}
        self.model = model
        self.system_prompt = system_prompt
        self.proxies = proxies

        # Auth state
        self._conversation = OperaAriaConversation(refresh_token=refresh_token)

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = (
                AwesomePrompts().get_act(
                    cast(Union[str, int], act),
                    default=self.conversation.intro,
                    case_insensitive=True,
                )
                or self.conversation.intro
            )
        elif intro:
            self.conversation.intro = intro

        if proxies:
            self.session.proxies.update(proxies)

        if tools:
            self.register_tools(tools)

    # ── internal helpers ────────────────────────────────────────────

    def _api_version(self) -> str:
        return self._MODEL_TO_VERSION.get(self.model, "v2")

    def _api_endpoint(self) -> str:
        return self.API_ENDPOINT_V1 if self._api_version() == "v1" else self.API_ENDPOINT_V2

    def _generate_refresh_token(self) -> str:
        """3-step anonymous signup to obtain a long-lived refresh token.

        1. POST /oauth2/v1/token/  (client_credentials, scope anonymous_account)
        2. POST /account/v2/external/anonymous/signup  (returns short-lived auth_token)
        3. POST /oauth2/v1/token/  (grant_type=auth_token)  → refresh_token
        """
        auth_headers = {
            "User-Agent": "okhttp/5.3.2",
            "Content-Type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
            "x-opera-client-cache": "1",
        }

        # Step 1: client-credentials token
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
            impersonate="chrome110",
        )
        r1.raise_for_status()
        anon_token = r1.json().get("access_token")
        if not anon_token:
            raise exceptions.FailedToGenerateResponseError(
                f"OperaAria: step-1 (client_credentials) returned no access_token: {r1.text[:200]}"
            )

        # Step 2: anonymous signup
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
            impersonate="chrome110",
        )
        r2.raise_for_status()
        auth_token = r2.json().get("token")
        if not auth_token:
            raise exceptions.FailedToGenerateResponseError(
                f"OperaAria: step-2 (anonymous signup) returned no auth_token: {r2.text[:200]}"
            )

        # Step 3: exchange auth_token for refresh_token
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
            impersonate="chrome110",
        )
        r3.raise_for_status()
        refresh_token = r3.json().get("refresh_token")
        if not refresh_token:
            raise exceptions.FailedToGenerateResponseError(
                f"OperaAria: step-3 (auth_token grant) returned no refresh_token: {r3.text[:200]}"
            )
        return refresh_token

    def get_access_token(self) -> str:
        """Return a fresh access token, signing up anonymously on first use."""
        if not self._conversation.refresh_token:
            self._conversation.refresh_token = self._generate_refresh_token()

        if self._conversation.access_token and not self._conversation.is_token_expired():
            return cast(str, self._conversation.access_token)

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
                "refresh_token": self._conversation.refresh_token,
                "scope": "shodan:aria",
            },
            timeout=self.timeout,
            impersonate="chrome110",
        )
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        if not token:
            # Refresh token may have expired — try a full re-signup once
            self._conversation.refresh_token = self._generate_refresh_token()
            return self.get_access_token()
        self._conversation.update_token(token, int(data.get("expires_in", 3600)))
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

    def _build_payload(
        self,
        prompt: str,
        messages_payload: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Build the JSON body the chat endpoint expects.

        v1 wants a flat ``query`` string; v2 wants the same plus a
        ``supported_features`` list and an encryption envelope. Both
        accept ``conversation_id`` for turns after the first.
        """
        version = self._api_version()
        query = messages_payload[-1]["content"] if messages_payload else prompt

        if version == "v1":
            data: Dict[str, Any] = {
                "query": query,
                "stream": True,
                "linkify": True,
                "linkify_version": 3,
                "sia": True,
                "media_attachments": [],
                "encryption": {"key": self._conversation.encryption_key},
            }
        else:
            data = {
                "query": query,
                "sia": True,
                "think_harder": False,
                "supported_features": [],
                "file_attachments": [],
                "encryption": {"key": self._conversation.encryption_key},
            }

        if not self._conversation.is_first_request and self._conversation.conversation_id:
            data["conversation_id"] = self._conversation.conversation_id
        return data

    @staticmethod
    def _parse_sse(line: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Split one SSE line into (event_type, data_dict)."""
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

    def _extract_content(self, data: Dict[str, Any], version: str) -> tuple[Optional[str], Optional[str]]:
        """Return (text_chunk, image_url) from a parsed SSE payload.

        For image responses (v2 only), the surrounding text is just
        "I've put together the image…" — we surface the image_url instead.
        """
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

    def _extract_conversation_id(self, data: Dict[str, Any], version: str) -> Optional[str]:
        if version == "v1":
            cid = data.get("conversation_id")
            return cid if isinstance(cid, str) else None
        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            cid = metadata.get("conversation_id")
            return cid if isinstance(cid, str) else None
        return None

    # ── Provider interface ──────────────────────────────────────────

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """Chat with Opera Aria.

        Anonymous signup happens on the first request; subsequent requests
        reuse the cached refresh token and rotate the short-lived access
        token transparently.
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        version = self._api_version()
        access_token = self.get_access_token()
        headers = self._build_headers(access_token, version)
        payload = self._build_payload(prompt, [{"role": "user", "content": conversation_prompt}])

        def for_stream() -> Generator[Any, None, None]:
            streaming_text = ""
            try:
                response = self.session.post(
                    self._api_endpoint(),
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                response.raise_for_status()

                skip_next = False
                for raw_line in response.iter_lines():
                    if raw_line is None:
                        continue
                    if isinstance(raw_line, bytes):
                        raw_line = raw_line.decode("utf-8", errors="replace")
                    event_type, payload_obj = self._parse_sse(raw_line)
                    if event_type == "thinking_status":
                        # The data line right after this carries the
                        # thinking payload — drop it.
                        skip_next = True
                        continue
                    if skip_next:
                        skip_next = False
                        continue
                    if payload_obj is None:
                        continue

                    text, image_url = self._extract_content(payload_obj, version)
                    if image_url:
                        marker = f"\n[image: {image_url}]\n"
                        streaming_text += marker
                        if raw:
                            yield marker
                        else:
                            yield {"text": marker}
                    if text:
                        streaming_text += text
                        if raw:
                            yield text
                        else:
                            yield {"text": text}

                    cid = self._extract_conversation_id(payload_obj, version)
                    if cid:
                        self._conversation.conversation_id = cid

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Unexpected error ({type(e).__name__}): {e}"
                ) from e
            finally:
                self._conversation.is_first_request = False
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream() -> Union[Dict[str, Any], str]:
            full_text = ""
            try:
                for chunk in for_stream():
                    if raw and isinstance(chunk, str):
                        full_text += chunk
                    elif isinstance(chunk, dict) and "text" in chunk:
                        full_text += chunk["text"]
            except Exception as e:
                if not full_text:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to get non-stream response: {e}"
                    ) from e
            self.last_response = {"text": full_text}
            return full_text if raw else self.last_response

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    from rich import print

    for model in OperaAria.AVAILABLE_MODELS:
        print(f"\n[bold cyan]=== {model} ===[/bold cyan]")
        try:
            ai = OperaAria(model=model, timeout=60)
            response = ai.chat("Say hi in one short word", stream=True, raw=False)
            if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
                for chunk in response:
                    print(chunk, end="", flush=True)
            else:
                print(response)
        except Exception as e:
            print(f"[red]ERROR:[/red] {e}")
