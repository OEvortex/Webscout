"""
OllamaSwarm — OpenAI-compatible variant.

Wraps :class:`llm4free.Provider.OllamaSwarm` (the regular llm4free
provider) in an :class:`OpenAICompatibleProvider` interface so it can
be dropped into any code expecting ``openai.chat.completions.create``.

Usage::

    from llm4free.Provider.Openai_comp.OllamaSwarm import OllamaSwarm
    client = OllamaSwarm()       # auto-discovers alive Ollama nodes
    resp = client.chat.completions.create(
        model="qwen3:14b",
        messages=[{"role": "user", "content": "Tell me a joke"}],
    )
    print(resp.choices[0].message.content)

How it works
------------
* On construction, ``discover_servers()`` probes the same seed list as
  the regular provider (plus optional FOFA discovery via
  ``FOFA_EMAIL`` / ``FOFA_KEY`` env vars) and builds an in-memory
  ``{model_name: [server_url, ...]}`` map.
* Each ``create()`` call picks a server that has the requested model
  and forwards a vanilla ``POST <host>/v1/chat/completions`` request
  to it. The wire format is OpenAI's, so the base
  ``OpenAICompatibleProvider`` handles headers, streaming parsing and
  ``ChatCompletion`` shape.
* If a request fails *before* the first chunk lands (TTFT, connect,
  4xx model-not-found), the next server in the swarm is tried.
  Once any chunk has been yielded we stop swapping so we never
  produce a duplicated / interleaved reply.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union

from curl_cffi import CurlError
from curl_cffi import requests

from llm4free.Provider.OllamaSwarm import (
    OllamaSwarm as _BaseOllamaSwarm,
    discover_servers,
    build_model_index,
    _models_cache_file,
)
from llm4free.Provider.Openai_comp.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from llm4free.Provider.Openai_comp.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
)
from llm4free.Provider.Openai_comp.OperaAria import _approx_tokens  # ty:ignore[import-not-found]

BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"

# Per-server first-chunk budget (seconds) before we give up and try
# the next node. Mirrors the regular provider's ttft_timeout knob.
DEFAULT_TTFT_TIMEOUT = 10.0


# ──────────────────────────────────────────────────────────────────────
#  OpenAI-compat completions class
# ──────────────────────────────────────────────────────────────────────


class Completions(BaseCompletions):
    def __init__(self, client: "OllamaSwarm"):
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
        model = self._client.convert_model_name(model)
        prompt = self._client._last_user_text(messages)
        request_id = f"chatcmpl-{uuid.uuid4().hex}"
        created_time = int(time.time())
        if stream:
            return self._create_stream(
                request_id, created_time, model, prompt, timeout, proxies
            )
        return self._create_non_stream(
            request_id, created_time, model, prompt, timeout, proxies
        )

    # ── helpers ────────────────────────────────────────────────────

    def _post_to(self, server_url: str, model: str, prompt: str, timeout: int):
        """POST to ``<server>/v1/chat/completions`` and return the
        streaming response. Raises on network / HTTP errors."""
        url = f"{server_url}/v1/chat/completions"
        return self._client.session.post(
            url,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                **({"max_tokens": self._client.max_tokens} if self._client.max_tokens else {}),
            },
            stream=True,
            timeout=timeout or self._client.timeout,
            proxies=None,  # the Openai_comp session already has its proxies
        )

    # ── streaming ──────────────────────────────────────────────────

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        prompt: str,
        timeout: Optional[int],
        proxies: Optional[Dict[str, str]],
    ) -> Generator[ChatCompletionChunk, None, None]:
        prompt_tokens = self._client._safe_count(prompt)
        completion_tokens = 0
        finish_reason = None

        yielded = False
        for server_url in self._client.servers_for(model):
            try:
                response = self._post_to(server_url, model, prompt, timeout or self._client.timeout)
                if not response.ok:
                    # 4xx on the *first* attempt means "model not on this server"
                    # — try the next swarm member.
                    if response.status_code in (400, 404, 422):
                        continue
                    response.raise_for_status()
                response.raise_for_status()
            except CurlError:
                continue
            except Exception:
                continue

            try:
                for raw_line in response.iter_lines():
                    if raw_line is None:
                        continue
                    if isinstance(raw_line, bytes):
                        raw_line = raw_line.decode("utf-8", errors="replace")
                    line = raw_line.strip()
                    if not line.startswith("data:"):
                        continue
                    payload_str = line[5:].strip()
                    if payload_str in ("[DONE]", ""):
                        if completion_tokens:
                            break
                        continue
                    try:
                        evt = json.loads(payload_str)
                    except json.JSONDecodeError:
                        continue

                    choice = (evt.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    text = delta.get("content") or ""
                    finish = choice.get("finish_reason")

                    if text:
                        completion_tokens += self._client._safe_count(text)
                        chunk = ChoiceDelta(content=text, role="assistant", tool_calls=None)
                        ch = Choice(index=0, delta=chunk, finish_reason=None, logprobs=None)
                        c = ChatCompletionChunk(
                            id=request_id,
                            choices=[ch],
                            created=created_time,
                            model=model,
                            system_fingerprint=None,
                        )
                        if hasattr(c, "model_dump"):
                            d = c.model_dump(exclude_none=True)
                        else:
                            d = c.dict(exclude_none=True)
                        d["usage"] = {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": prompt_tokens + completion_tokens,
                            "estimated_cost": None,
                        }
                        yielded = True
                        yield c
                    elif finish and finish not in (None, "null"):
                        finish_reason = finish
                        break

                # Success — promote this server to the front.
                self._client._promote(model, server_url)
                if finish_reason is None:
                    finish_reason = "stop"
                delta = ChoiceDelta(content=None, role=None, tool_calls=None)
                ch = Choice(index=0, delta=delta, finish_reason=finish_reason, logprobs=None)
                stop_chunk = ChatCompletionChunk(
                    id=request_id,
                    choices=[ch],
                    created=created_time,
                    model=model,
                    system_fingerprint=None,
                )
                if hasattr(stop_chunk, "model_dump"):
                    d = stop_chunk.model_dump(exclude_none=True)
                else:
                    d = stop_chunk.dict(exclude_none=True)
                d["usage"] = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "estimated_cost": None,
                }
                yield stop_chunk
                return

            except CurlError:
                if yielded:
                    raise
                continue
            except Exception:
                if yielded:
                    raise
                continue

        raise IOError(
            f"OllamaSwarm (Openai_comp): no server in the swarm accepted model {model!r}"
        )

    # ── non-streaming ─────────────────────────────────────────────

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        prompt: str,
        timeout: Optional[int],
        proxies: Optional[Dict[str, str]],
    ) -> ChatCompletion:
        full_text = ""
        yielded = False
        for server_url in self._client.servers_for(model):
            try:
                response = self._post_to(server_url, model, prompt, timeout or self._client.timeout)
                if not response.ok:
                    if response.status_code in (400, 404, 422):
                        continue
                    response.raise_for_status()
                response.raise_for_status()
            except Exception:
                continue

            try:
                for raw_line in response.iter_lines():
                    if raw_line is None:
                        continue
                    if isinstance(raw_line, bytes):
                        raw_line = raw_line.decode("utf-8", errors="replace")
                    line = raw_line.strip()
                    if not line.startswith("data:"):
                        continue
                    payload_str = line[5:].strip()
                    if payload_str in ("[DONE]", ""):
                        if full_text:
                            break
                        continue
                    try:
                        evt = json.loads(payload_str)
                    except json.JSONDecodeError:
                        continue
                    choice = (evt.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    text = delta.get("content") or ""
                    if text:
                        full_text += text
                        yielded = True
                    finish = choice.get("finish_reason")
                    if finish and finish not in (None, "null"):
                        break
            except Exception:
                if yielded:
                    raise
                continue

            self._client._promote(model, server_url)
            prompt_tokens = self._client._safe_count(prompt)
            completion_tokens = self._client._safe_count(full_text)
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )
            message = ChatCompletionMessage(role="assistant", content=full_text)
            choice = Choice(index=0, message=message, finish_reason="stop", logprobs=None)
            return ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
                system_fingerprint=None,
            )

        raise IOError(
            f"OllamaSwarm (Openai_comp): no server in the swarm accepted model {model!r}"
        )


class Chat(BaseChat):
    def __init__(self, client: "OllamaSwarm"):
        self.completions = Completions(client)


# ──────────────────────────────────────────────────────────────────────
#  Public client
# ──────────────────────────────────────────────────────────────────────


class OllamaSwarm(OpenAICompatibleProvider):
    """OpenAI-compatible client for the Ollama swarm.

    Usage::

        client = OllamaSwarm()
        response = client.chat.completions.create(
            model="qwen3:14b",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response.choices[0].message.content)
    """

    required_auth = False

    def __init__(
        self,
        timeout: int = 60,
        seed_servers: Optional[List[str]] = None,
        skip_discovery: bool = False,
    ):
        self.timeout = timeout
        self.proxies: Optional[Dict[str, str]] = None
        # Mirrors the regular provider's discovery pipeline.  We re-use
        # the helpers from llm4free/Provider/OllamaSwarm.py so both
        # variants share the same seed list, FOFA path and disk cache.
        if skip_discovery:
            assert seed_servers, "skip_discovery=True requires an explicit seed_servers=[...] list"
            self._servers: Dict[str, List[str]] = {s: ["*"] for s in seed_servers}
        else:
            self._servers = discover_servers(seed_servers=seed_servers)
        self._model_to_servers: Dict[str, List[str]] = build_model_index(self._servers)
        if not self._model_to_servers and seed_servers:
            self._servers = {s: ["*"] for s in seed_servers}
            self._model_to_servers = {"*": list(seed_servers)}

        self.session = requests.Session(impersonate="chrome110")
        self.max_tokens: Optional[int] = None
        self.chat = Chat(self)

    # ── helpers exposed for Completions ────────────────────────────

    def convert_model_name(self, model: str) -> str:
        """Resolve the user-supplied model name.

        Returns the model name as-is if the swarm has it explicitly
        registered, or if a wildcard ``*`` entry exists.  If neither,
        returns the input verbatim so the swarm can still attempt the
        POST — the per-server 400/404 will gracefully fall through to
        the next node.
        """
        if not model:
            return next(iter(self._model_to_servers), "*")
        if model in self._model_to_servers or "*" in self._model_to_servers:
            return model
        # Last resort: return what the user asked for.  Servers that
        # don't have it will return 400/404 and the swarm will skip them.
        return model

    @staticmethod
    def _last_user_text(messages: List[Dict[str, str]]) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                content = m.get("content", "")
                if isinstance(content, str):
                    return content
        return ""

    def servers_for(self, model: str) -> List[str]:
        return list(self._model_to_servers.get(model) or self._model_to_servers.get("*") or [])

    def _promote(self, model: str, server_url: str) -> None:
        """Move a successful server to the front of its model list so
        the next call hits it first."""
        if model in self._model_to_servers:
            self._model_to_servers[model] = [server_url] + [
                s for s in self._model_to_servers[model] if s != server_url
            ]

    def _safe_count(self, text: str) -> int:
        """Token counter with character-based fallback when ``tiktoken``
        isn't installed."""
        try:
            return count_tokens(text)
        except (ImportError, ModuleNotFoundError, OSError):
            return _approx_tokens(text)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(list(self._model_to_servers.keys()))


if __name__ == "__main__":
    client = OllamaSwarm()
    response = client.chat.completions.create(
        model="qwen3:14b",
        messages=[{"role": "user", "content": "Tell me a joke"}],
    )
    if isinstance(response, ChatCompletion):
        message = response.choices[0].message
        print(message.content if message else "")
