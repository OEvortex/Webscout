"""
Free.ai — webscout port of free.ai's public chat API.

Reverse-engineered from https://free.ai/chat/ which advertises a
fully OpenAI-compatible endpoint at ``https://api.free.ai/v1/chat/``
with no auth required (any bearer token is accepted — the server
appears not to validate the token format).

Models
------
* ``qwen7b``  — only model that returns a reply without authentication
* every other model (``gpt-4o``, ``gpt-4o-mini``, ``claude-haiku``,
  ``mistral``, …) returns an empty/timeout response unless the
  caller has a real account. The public models list (in the page
  source) advertises 380+ but they're all gated behind the
  30K-tokens-per-day signup.

Streaming
---------
SSE format:
::

    data: {"choices": [{"delta": {"content": "..."}}], "model": "..."}

    data: [DONE]

So the provider yields raw ``{text: ...}`` chunks and stops on
``[DONE]``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response, Tool
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers


class FreeAI(Provider):
    """Free.ai public OpenAI-compatible chat (no auth required)."""

    label = "Free.ai"
    required_auth = False
    AVAILABLE_MODELS = ["qwen7b"]
    DEFAULT_MODEL = "qwen7b"
    BASE_URL = "https://api.free.ai/v1/chat/"

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
                f"Invalid model: {model!r}. Publicly available: {self.AVAILABLE_MODELS}"
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

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": True,
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": "Bearer ***",  # any string is accepted
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                response.raise_for_status()

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
                        if streaming_text:
                            break
                        continue
                    try:
                        evt = json.loads(payload_str)
                    except json.JSONDecodeError:
                        continue
                    choices = evt.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    text = delta.get("content")
                    if not text:
                        # Some events may carry finish_reason only
                        finish = choices[0].get("finish_reason")
                        if finish and finish != "null":
                            break
                        continue
                    streaming_text += text
                    if raw:
                        yield text
                    else:
                        yield {"text": text}

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

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    from rich import print

    ai = FreeAI()
    response = ai.chat("Say hi in one short word", stream=False)
    print(response)
