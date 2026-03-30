"""
Apriel Gradio chat API provider.

Demonstrates the clean provider pattern:
  - ``ask()``   → raw API call, returns ``{"text": ...}``
  - ``get_message()`` → extracts text from response
  - ``chat()``  → **inherited** from ``Provider`` — handles the full
                  tool-calling loop automatically when tools are supplied.
"""

import time
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response, Tool
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers
from webscout.litagent import LitAgent
from webscout.sanitize import sanitize_stream


class Apriel(Provider):
    """Interact with the Apriel Gradio chat API.

    Tool calling is handled automatically by the base ``Provider.chat()``
    method — just pass ``tools=[...]`` and the base class will inject tool
    definitions, parse ``<invoke>`` blocks, execute tools, and feed results
    back until the model produces a final text answer.

    Example::

        >>> ai = Apriel()
        >>> ai.chat("Hello!")                           # plain chat
        >>> ai = Apriel(tools=[my_tool])                # register at init
        >>> ai.chat("What is the weather in London?")   # auto tool loop
    """

    required_auth = False
    AVAILABLE_MODELS = ["UNKNOWN"]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        system_prompt: str = "You are a helpful assistant.",
        model: str = "UNKNOWN",
        tools: Optional[list[Tool]] = None,
    ):
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://servicenow-ai-apriel-chat.hf.space"
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt

        self.agent = LitAgent()
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": self.agent.random(),
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

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

    # ── internal helpers ─────────────────────────────────────────── #

    def _get_session_hash(self) -> str:
        try:
            url = f"{self.api_endpoint}/gradio_api/heartbeat"
            self.session.get(url, timeout=self.timeout)
            return str(int(time.time()))
        except Exception:
            return str(int(time.time()))

    def _join_queue(
        self, session_hash: str, message: str, fn_index: int = 1, trigger_id: int = 16
    ) -> Optional[str]:
        url = f"{self.api_endpoint}/gradio_api/queue/join"
        payload = {
            "data": [[], {"text": message, "files": []}, None],
            "event_data": None,
            "fn_index": fn_index,
            "trigger_id": trigger_id,
            "session_hash": session_hash,
        }
        resp = self.session.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        try:
            return resp.json().get("event_id")
        except Exception:
            return None

    def _run_predict(self, session_hash: str, fn_index: int = 3, trigger_id: int = 16) -> None:
        url = f"{self.api_endpoint}/gradio_api/run/predict"
        payload = {
            "data": [],
            "event_data": None,
            "fn_index": fn_index,
            "trigger_id": trigger_id,
            "session_hash": session_hash,
        }
        self.session.post(url, json=payload, timeout=self.timeout).raise_for_status()

    @staticmethod
    def _apriel_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        if isinstance(chunk, dict):
            if chunk.get("msg") == "process_generating":
                data = chunk.get("output", {}).get("data")
                if data and isinstance(data, list) and len(data) > 0:
                    for op in data[0]:
                        if isinstance(op, list) and len(op) > 2 and op[0] == "append":
                            return op[2]
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
        """Make a raw API call to the Apriel Gradio endpoint.

        This method does **not** handle tool calling — that is done by the
        inherited :meth:`Provider.chat` which calls this method in a loop.
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        session_hash = self._get_session_hash()
        self._join_queue(session_hash, conversation_prompt)
        self._run_predict(session_hash)

        def for_stream():
            streaming_text = ""
            try:
                url = f"{self.api_endpoint}/gradio_api/queue/data?session_hash={session_hash}"
                resp = self.session.get(
                    url, stream=True, timeout=self.timeout, impersonate="chrome110"
                )
                if not resp.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({resp.status_code}, {resp.reason})"
                    )
                processed = sanitize_stream(
                    data=resp.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    content_extractor=self._apriel_extractor,
                    yield_raw_on_error=False,
                    raw=raw,
                )
                for chunk in processed:
                    if chunk and isinstance(chunk, str):
                        if raw:
                            yield chunk
                        else:
                            streaming_text += chunk
                            yield {"text": chunk}
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {e}")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Unexpected error ({type(e).__name__}): {e}"
                )
            finally:
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response if not raw else self.last_response.get("text", "")

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    from rich import print

    ai = Apriel(timeout=60)
    response = ai.chat("write a poem about AI", stream=True, raw=False)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
