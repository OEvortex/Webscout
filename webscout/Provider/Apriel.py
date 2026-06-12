"""
Apriel Gradio 5 chat API provider.

The space at https://servicenow-ai-apriel-chat.hf.space runs Gradio 5.47
using the ``sse_v3`` protocol. Reverse-engineered from the live ``/config``
endpoint:

* ``app_id``         = 8685039810546182577
* ``space_id``       = "ServiceNow-AI/Apriel-Chat"
* ``protocol``       = "sse_v3"
* Chat dependency   = id 1, with ``inputs=[11, 15, 1]`` (chatbot,
                       multimodaltextbox, state) and
                       ``outputs=[11, 15, 19, 20, 22, 1]``.
* Targets           = ``[[19, "click"], [15, "submit"]]`` — id 19 is the
                       Send button (NOT the legacy ``trigger_id=16`` the
                       previous Gradio-4 client used).

The flow is:

1. POST ``/gradio_api/queue/join`` with
   ``{data: [[], {"text": message, "files": []}, None],
     fn_index: 1, trigger_id: 19, session_hash, app_id}``
   → returns ``{"event_id": "..."}``
2. Open SSE stream at
   ``GET /gradio_api/queue/data?session_hash=...``
   and consume ``process_generating`` events whose ``output.data[0]`` is a
   list of ``{"role": "assistant", "content": "..."}`` message dicts
   (the Gradio 5 multimodal-chat wire format).

The model currently answered with "😔 The model is unavailable at the
moment" for every request, so this client is fully wired but upstream
may still be unavailable.
"""

import json
import time
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response, Tool
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers
from webscout.litagent import LitAgent


# Gradio 5 SSE v3 protocol constants reverse-engineered from the live
# ``/config`` endpoint of the Apriel space.
APP_ID = 8685039810546182577
CHAT_FN_INDEX = 1
SEND_TRIGGER_ID = 19  # The "Send" button id (NOT 16, which was the legacy
                      # Gradio 4 trigger id baked into the old client).


class Apriel(Provider):
    """Interact with the Apriel Gradio 5 chat space.

    The current model advertised by the space is
    ``Apriel-1.6-15B-Thinker``. The space may return
    "model unavailable" if its HF GPU quota is exhausted.
    """

    required_auth = False
    AVAILABLE_MODELS = ["Apriel-1.6-15B-Thinker"]

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
        model: str = "Apriel-1.6-15B-Thinker",
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

    # ── Gradio 5 helpers ─────────────────────────────────────────── #

    @staticmethod
    def _new_session_hash() -> str:
        return uuid_hex_short()

    def _join_queue(
        self,
        session_hash: str,
        message: str,
        fn_index: int = CHAT_FN_INDEX,
        trigger_id: int = SEND_TRIGGER_ID,
    ) -> Optional[str]:
        url = f"{self.api_endpoint}/gradio_api/queue/join"
        payload = {
            "data": [
                [],                            # chatbot history (state, server-managed)
                {"text": message, "files": []}, # multimodal textbox payload
                None,                          # opt-out flag
            ],
            "event_data": None,
            "fn_index": fn_index,
            "trigger_id": trigger_id,
            "session_hash": session_hash,
        }
        resp = self.session.post(url, json=payload, timeout=self.timeout)
        if not resp.ok:
            raise exceptions.FailedToGenerateResponseError(
                f"queue/join failed: {resp.status_code} {resp.reason} - {resp.text[:200]}"
            )
        try:
            return resp.json().get("event_id")
        except Exception:
            return None

    @staticmethod
    def _extract_chat_messages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the list of assistant message dicts in ``payload['data'][0]``.

        Gradio 5 multimodal-chat serialises the chatbot output as
        ``data: [[{role, content}, ...], ...]`` — a list-of-messages-in-a-list.
        Older code expected the Gradio 4 op-list ``[["append", "", text], ...]``
        which is no longer used.
        """
        try:
            data = payload.get("data") or []
            if not data or not isinstance(data, list):
                return []
            head = data[0]
            if not isinstance(head, list):
                return []
            return [m for m in head if isinstance(m, dict)]
        except Exception:
            return []

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
        """Make a raw API call to the Apriel Gradio 5 endpoint.

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

        session_hash = self._new_session_hash()
        self._join_queue(session_hash, conversation_prompt)

        def for_stream():
            streaming_text = ""
            try:
                url = f"{self.api_endpoint}/gradio_api/queue/data?session_hash={session_hash}"
                resp = self.session.get(
                    url,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                if not resp.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"queue/data failed: {resp.status_code} {resp.reason}"
                    )

                emitted_length = 0
                for raw_line in resp.iter_lines():
                    if not raw_line:
                        continue
                    line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else raw_line
                    if not line.startswith("data:"):
                        continue
                    try:
                        evt = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(evt, dict):
                        continue
                    msg = evt.get("msg")
                    if msg != "process_generating":
                        # Other event types we care about: estimation, process_starts,
                        # process_completed, close_stream. None carry new tokens.
                        if msg == "process_completed":
                            break
                        continue
                    output = evt.get("output") or {}
                    messages = self._extract_chat_messages(output)
                    if not messages:
                        continue
                    # Concatenate any new assistant content not yet yielded.
                    full = "".join(
                        str(m.get("content") or "")
                        for m in messages
                        if m.get("role") in (None, "assistant")
                    )
                    delta = full[emitted_length:]
                    if not delta:
                        continue
                    emitted_length = len(full)
                    streaming_text = full
                    if raw:
                        yield delta
                    else:
                        yield {"text": delta}
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Unexpected error ({type(e).__name__}): {e}"
                ) from e
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


# ── helpers ──────────────────────────────────────────────────────── #


def uuid_hex_short() -> str:
    """Return a 12-character hex string, Gradio 5 session-hash style."""
    import uuid as _uuid
    return _uuid.uuid4().hex[:12]


if __name__ == "__main__":
    from rich import print

    ai = Apriel(timeout=60)
    response = ai.chat("write a poem about AI", stream=True, raw=False)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
