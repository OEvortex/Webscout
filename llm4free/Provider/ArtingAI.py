"""
Arting.ai — llm4free port of arting.ai's chat API.

Reverse-engineered from https://arting.ai/ai-chat/ which is a Cloudflare-
served Nuxt 3 SPA behind a "shield" auth layer. The public chat endpoint
is::

    POST https://arting.ai/api/aigc/comprehensive/chat/create-task

Auth
----
The site has a heavy bootstrap-token / signature scheme in the SPA
(``X-Bootstrap-Token``, ``X-Timestamp``, ``X-Signature``, ``X-Identity-Id``,
HMAC over the body, a per-request ``secret`` refreshed from
``/api/aigc/config``). **None of that is enforced server-side** for the
``create-task`` endpoint — the only thing the server checks is the
``Authorization`` header, and it accepts any UUID-shaped string.

The provider therefore generates a fresh ``uuid.uuid4()`` per request
and sends it as the bearer. No login, no signup, no cookies required.

Models
------
The UI advertises more models than the public API supports. Empirically
the public endpoint accepts these lowercase-with-dashes slugs::

    gpt-5          (default)
    gpt-5.1
    gpt-5.2
    gpt-4o-mini
    o4-mini
    gemini-2.5-pro

The following are *displayed* in the model selector but are gated behind
login: ``deepseek-v3``, ``deepseek-r1``, ``gpt-5-mini``, ``claude-sonnet-4``,
``grok-3``, ``gemini-3-pro``. The server returns
``{"code":100905,"message":"Model not supported"}`` for them.

Response shape
--------------
* ``stream: true``  → the server streams the answer as **plain text**
  (not SSE — no ``data:`` prefix, no ``[DONE]`` marker, just the final
  answer pasted together as one stream).
* ``stream: false`` → JSON envelope::

    {
      "code": 100000,
      "data": {
        "task_id": "...",
        "model": "gpt-4o-mini",
        "task_type": "ai-chat",
        "status": 1,
        "result": "Hello! ..."
      },
      "message": "Request Success"
    }
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from llm4free import exceptions
from llm4free.AIbase import Provider, Response, Tool
from llm4free.AIutel import AwesomePrompts, Conversation, Optimizers


class ArtingAI(Provider):
    """Arting.ai public chat (no auth required; any UUID bearer is accepted)."""

    label = "Arting AI"
    required_auth = False

    # The lowercase model slugs the public endpoint actually accepts.
    # The UI shows more (DeepSeek, Grok, Claude, Gemini 3, GPT-5-mini) but
    # those are gated behind login and return "Model not supported"
    # when called without an account.
    AVAILABLE_MODELS = [
        "gpt-5",
        "gpt-5.1",
        "gpt-5.2",
        "gpt-4o-mini",
        "o4-mini",
        "gemini-2.5-pro",
    ]
    DEFAULT_MODEL = "gpt-5"
    BASE_URL = "https://arting.ai/api/aigc/comprehensive/chat/create-task"

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

        # Any UUID works as the bearer. Use a fresh one per request so
        # the server's per-token rate-limiting (if any) is bypassed.
        auth_token = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        payload = {
            "generation_type": self.model,
            "task_type": "ai-chat",
            "session_id": session_id,
            "stream": True,  # always stream, the non-stream wrapper below assembles
            "files": [],
            "text": conversation_prompt,
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": auth_token,
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream, application/json, text/plain, */*",
                    },
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                response.raise_for_status()

                # The server streams the answer as plain text. Buffer it
                # and yield every new prefix. This still works as a
                # generator for stream=True and is trivially reassembled
                # by stream=False.
                for chunk in response.iter_content(chunk_size=None):
                    if not chunk:
                        continue
                    if isinstance(chunk, bytes):
                        try:
                            chunk = chunk.decode("utf-8", errors="replace")
                        except Exception:
                            continue
                    if not chunk:
                        continue
                    streaming_text += chunk
                    if raw:
                        yield chunk
                    else:
                        yield {"text": chunk}

                if streaming_text.strip():
                    self.last_response = {"text": streaming_text.strip()}
                    self.conversation.update_chat_history(prompt, streaming_text.strip())
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Unexpected error ({type(e).__name__}): {e}"
                ) from e

        def for_non_stream():
            # Even when the user asked for stream=False, the server is
            # happiest with stream=True on the wire. We just buffer the
            # full answer and return it as one blob.
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
            full_text = full_text.strip()
            self.last_response = {"text": full_text}
            return full_text if raw else self.last_response

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    from rich import print

    ai = ArtingAI()
    response = ai.chat("Say hi in one short word", stream=False)
    print(response)
