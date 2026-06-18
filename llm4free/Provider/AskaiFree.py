"""
askai.free — llm4free port of askai.free's chat API.

Reverse-engineered from https://askai.free/. The chat endpoint is
``POST /api/chat/stream`` (yes, "stream" is in the path even though
the response is currently a single JSON blob — not an SSE stream).
The wire format reverse-engineered from the page's JavaScript bundle:

* Body: ``{"message": str, "messages": [{role, content}], "modelName": str}``
  * ``modelName`` is the field name (NOT ``model`` — that field is
    silently ignored, leading to the misleading
    ``"Model 'None' not found"`` error string).
  * The display name is required, e.g. ``"ChatGPT 4o"``, not the
    machine id like ``"gpt-4o"`` or ``"openai/gpt-4o-mini"``.
* Auth: none — public free credits per IP.
* Limits: rate-limited per IP via free credits. Once exhausted, the
  server returns ``{"error":"limit_reached", ...}`` until the
  caller creates an account.

Models (display names as the API expects them)
------------------------------------------------
* ``"ChatGPT 4o"``  — works for free (subject to free credits)
* ``"ChatGPT 5"``, ``"Claude Sonnet 4"`` — require ``premium_required``
* ``"Gemini 2.5 Pro"`` — not currently available
"""

from __future__ import annotations

import json
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from llm4free import exceptions
from llm4free.AIbase import Provider, Response, Tool
from llm4free.AIutel import AwesomePrompts, Conversation, Optimizers


class AskaiFree(Provider):
    """askai.free public chat (no auth; rate-limited by IP)."""

    label = "askai.free"
    required_auth = False

    # The API takes display names, not slugs. The list below mirrors
    # what the page shows in the model selector.
    AVAILABLE_MODELS = [
        "ChatGPT 4o",
        "ChatGPT 5",
        "Claude Sonnet 4",
        "Claude Opus 4",
        "Claude Haiku 4-5",
        "Gemini 2.0 Flash",
        "GPT-4.1",
    ]
    DEFAULT_MODEL = "ChatGPT 4o"
    BASE_URL = "https://askai.free/api/chat/stream"

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
        tools: Optional[list[Tool]] = None,
    ) -> None:
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model display name: {model!r}. "
                f"Choose from: {self.AVAILABLE_MODELS}"
            )

        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response: Dict[str, Any] = {}
        self.model = model
        self.system_prompt = system_prompt
        self.proxies = proxies

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

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        # The API takes a `message` field and a `messages` array.
        # The `messages` array is the OpenAI-style history; `message`
        # is the current user input the server appends to it.
        payload = {
            "message": conversation_prompt,
            "messages": [{"role": "user", "content": conversation_prompt}],
            "modelName": self.model,
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    self.BASE_URL,
                    json=payload,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                response.raise_for_status()

                # The endpoint name is "stream" but the body is currently
                # a single JSON blob. If/when the server adds true SSE
                # support the parsing below still works because the
                # `delta.content` shape is OpenAI-compatible.
                ctype = response.headers.get("content-type", "")
                if "event-stream" in ctype:
                    for raw_line in response.iter_lines():
                        if raw_line is None:
                            continue
                        if isinstance(raw_line, bytes):
                            raw_line = raw_line.decode("utf-8", errors="replace")
                        line = raw_line.strip()
                        if not line.startswith("data:"):
                            continue
                        payload_str = line[5:].strip()
                        if payload_str == "[DONE]":
                            break
                        try:
                            evt = json.loads(payload_str)
                        except json.JSONDecodeError:
                            continue
                        chunk_text = self._extract_text(evt)
                        if chunk_text:
                            streaming_text += chunk_text
                            if raw:
                                yield chunk_text
                            else:
                                yield {"text": chunk_text}
                else:
                    try:
                        evt = response.json()
                    except json.JSONDecodeError:
                        raise exceptions.FailedToGenerateResponseError(
                            f"askai.free: non-JSON response (HTTP {response.status_code}): {response.text[:200]}"
                        )
                    err = self._extract_error(evt)
                    if err:
                        raise exceptions.FailedToGenerateResponseError(
                            f"askai.free: {err}"
                        )
                    chunk_text = self._extract_text(evt)
                    if chunk_text:
                        streaming_text += chunk_text
                        if raw:
                            yield chunk_text
                        else:
                            yield {"text": chunk_text}

                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Unexpected error ({type(e).__name__}): {e}"
                ) from e

        def for_non_stream():
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

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _extract_text(payload: Any) -> str:
        """Pull the assistant text out of an OpenAI-style or askai-
        specific JSON response."""
        if not isinstance(payload, dict):
            return ""
        # OpenAI streaming shape
        choices = payload.get("choices") or []
        if choices:
            first = choices[0]
            delta = first.get("delta") or {}
            text = delta.get("content")
            if isinstance(text, str):
                return text
            text = first.get("message", {}).get("content")
            if isinstance(text, str):
                return text
        # askai-native shape
        for key in ("text", "content", "answer", "message"):
            v = payload.get(key)
            if isinstance(v, str):
                return v
        return ""

    @staticmethod
    def _extract_error(payload: Any) -> Optional[str]:
        if not isinstance(payload, dict):
            return None
        err = payload.get("error")
        if not err:
            return None
        if isinstance(err, str):
            return err
        if isinstance(err, dict):
            return err.get("message") or str(err)
        return str(err)

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    from rich import print

    ai = AskaiFree(timeout=30)
    try:
        r = ai.chat("Say hi in one short word", stream=False)
        print("OK:", r)
    except Exception as e:
        print(f"ERR: {type(e).__name__}: {e}")
