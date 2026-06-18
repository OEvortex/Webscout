"""
Cohere Command chat provider via HuggingChat chat-ui.

The space at https://coherelabs-c4ai-command.hf.space is no longer a Gradio
deployment. As of 2026-06-12 it runs **HuggingChat chat-ui v0.9.4**
(SvelteKit + Node/Express backend). The full backend stack is open source
at https://github.com/huggingface/chat-ui.

The wire protocol reverse-engineered from the live HTML + SvelteKit
hydrated state is:

  POST /conversation
    body : ``{"model": "<modelId>", "preprompt": ""}``
    reply: ``{"conversationId": "<24-char hex>"}``

  POST /conversation/{conversationId}
    body : ``{
              "id":          "<messageId>",
              "inputs":      "<user message>",
              "is_retry":    false,
              "is_continue": false,
              "web_search":  false,
              "tools":       []
            }``
    reply: ``text/event-stream`` of
            ``data: {"type":"stream","token":"..."}`` chunks followed by a
            ``data: {"type":"finalAnswer","text":"..."}`` event that
            terminates the stream.

Available models (from the hydrated ``/models`` JSON in the HTML):
  - command-a-03-2025           (active default)
  - command-r-plus-08-2024
  - command-r-08-2024
  - command-r-plus
  - command-r
  - command-r7b-12-2024
  - command-r7b-arabic-02-2025

NOTE (2026-06-12): the live space currently returns
``{"message":"Conversation not found"}`` for every freshly-created
conversation, regardless of payload shape — the underlying inference
backend is broken on this space. The client below is protocol-correct and
will work when the upstream recovers.
"""

import json
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from llm4free import exceptions
from llm4free.AIbase import Provider, Response, Tool
from llm4free.AIutel import AwesomePrompts, Conversation, Optimizers


class CohereCommand(Provider):
    """Provider for Cohere Command models via HuggingChat chat-ui."""

    required_auth = False
    BASE_URL = "https://coherelabs-c4ai-command.hf.space"

    # Pulled from the live `/models` JSON in the page HTML on 2026-06-12.
    AVAILABLE_MODELS = [
        "command-a-03-2025",
        "command-r-plus-08-2024",
        "command-r-08-2024",
        "command-r-plus",
        "command-r",
        "command-r7b-12-2024",
        "command-r7b-arabic-02-2025",
    ]
    DEFAULT_MODEL = "command-a-03-2025"

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 4096,
        timeout: int = 60,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: Optional[dict] = None,
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        system_prompt: str = "You are a helpful AI assistant.",
        tools: Optional[list[Tool]] = None,
    ) -> None:
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}"
            )

        self.session = Session(impersonate="chrome110")
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response: Dict[str, Any] = {}
        self.model = model
        self.system_prompt = system_prompt
        self.proxies = proxies or {}
        self.conversation_id: Optional[str] = None

        self.headers = {
            "Accept": "text/event-stream",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        self.session.headers.update(self.headers)
        if self.proxies:
            self.session.proxies.update(self.proxies)

        # Touch / so any baseline cookies are set.
        try:
            self.session.get(self.BASE_URL, timeout=self.timeout)
        except Exception:
            pass

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

        if tools:
            self.register_tools(tools)

    # ── chat-ui helpers ─────────────────────────────────────────── #

    def _create_conversation(self) -> str:
        """POST /conversation and return the new conversationId."""
        resp = self.session.post(
            f"{self.BASE_URL}/conversation",
            json={"model": self.model, "preprompt": ""},
            timeout=self.timeout,
        )
        if not resp.ok:
            raise exceptions.FailedToGenerateResponseError(
                f"create_conversation failed: {resp.status_code} {resp.reason} - {resp.text[:200]}"
            )
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            raise exceptions.FailedToGenerateResponseError(
                f"create_conversation returned non-JSON: {e}"
            ) from e
        cid = data.get("conversationId")
        if not cid:
            raise exceptions.FailedToGenerateResponseError(
                f"create_conversation: no conversationId in response: {data}"
            )
        self.conversation_id = cid
        return cid

    @staticmethod
    def _extract_stream_payload(line: str) -> Optional[Dict[str, Any]]:
        """Parse a single ``data: {...}`` line from the chat-ui SSE stream."""
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if not line or line == "[DONE]":
            return None
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None

    # ── Provider interface ───────────────────────────────────────── #

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

        if not self.conversation_id:
            self._create_conversation()
        message_endpoint = f"{self.BASE_URL}/conversation/{self.conversation_id}"

        message_body = {
            "id": uuid.uuid4().hex[:20],
            "inputs": prompt,
            "is_retry": False,
            "is_continue": False,
            "web_search": False,
            "tools": [],
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    message_endpoint,
                    json=message_body,
                    stream=True,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                for raw_line in response.iter_lines():
                    if raw_line is None:
                        continue
                    if isinstance(raw_line, bytes):
                        raw_line = raw_line.decode("utf-8", errors="replace")
                    payload = self._extract_stream_payload(raw_line)
                    if not payload:
                        continue
                    ptype = payload.get("type")
                    if ptype == "stream" and isinstance(payload.get("token"), str):
                        token = payload["token"]
                        streaming_text += token
                        if raw:
                            yield token
                        else:
                            yield {"text": token}
                    elif ptype == "finalAnswer":
                        final_text = payload.get("text", streaming_text)
                        if final_text and not streaming_text:
                            # Server sent final only without streamed tokens
                            streaming_text = final_text
                            if raw:
                                yield final_text
                            else:
                                yield {"text": final_text}
                        break
                    elif ptype == "error":
                        raise exceptions.FailedToGenerateResponseError(
                            f"chat-ui error event: {payload}"
                        )
                    # Other event types (status, webSearch updates, etc.) ignored.

                self.last_response = {"text": streaming_text}
                if streaming_text:
                    self.conversation.update_chat_history(prompt, streaming_text)
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Stream request failed ({type(e).__name__}): {e}"
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
    print("Testing CohereCommand provider...")
    print("-" * 60)
    try:
        ai = CohereCommand(model="command-a-03-2025", timeout=60)
        print("\n[Non-streaming]")
        resp = ai.ask("What is 2+2?", stream=False)
        print(f"Response: {resp}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 60)
