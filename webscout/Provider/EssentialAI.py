import json
import random
import string
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers
from webscout.litagent import LitAgent


class EssentialAI(Provider):
    """
    A class to interact with the EssentialAI rnj-1-instruct Space Gradio API.
    Implemented using curl_cffi.
    """
    required_auth = False
    AVAILABLE_MODELS = ["rnj-1-instruct"]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 512,
        timeout: int = 60,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        system_prompt: str = "You are a helpful AI assistant.",
        model: str = "rnj-1-instruct",
        temperature: float = 0.2,
        top_p: float = 0.95,
    ):
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://essentialai-rnj-1-instruct-space.hf.space"
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.top_p = top_p

        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()
        self.zerogpu_uuid = "".join(random.choices(string.ascii_letters + string.digits + "_", k=21))

        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": self.agent.random(),
            "Accept": "text/event-stream",
            "x-zerogpu-uuid": self.zerogpu_uuid,
            "X-Gradio-Expand-Data": "true",
            "X-Gradio-Target": "chat"
        }

        # Initialize curl_cffi Session
        self.session = Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

        # Get initial cookies
        try:
            self.session.get(self.api_endpoint, timeout=self.timeout)
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
            self.conversation.intro = AwesomePrompts().get_act(cast(Union[str, int], act), default=self.conversation.intro, case_insensitive=True
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro

    def _get_session_hash(self) -> str:
        import random
        import string
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=11))

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

        self._get_session_hash()

        # Gradio 5 /call pattern
        payload = {
            "data": [
                conversation_prompt,
                [], # history
                self.system_prompt,
                float(self.max_tokens_to_sample),
                float(self.temperature),
                float(self.top_p)
            ]
        }

        def for_stream():
            streaming_text = ""
            try:
                # 1. POST /call
                call_url = f"{self.api_endpoint}/gradio_api/call/chat"
                call_response = self.session.post(call_url, json=payload, timeout=self.timeout)
                call_response.raise_for_status()
                event_id = call_response.json().get("event_id")

                if not event_id:
                    raise exceptions.FailedToGenerateResponseError("Failed to get event_id")

                # 2. GET /call/chat/{event_id}
                url = f"{self.api_endpoint}/gradio_api/call/chat/{event_id}"
                response = self.session.get(
                    url,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(f"Stream failed: {response.status_code}")

                last_full_text = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        try:
                            data = json.loads(line_str[6:])
                            if isinstance(data, list) and len(data) > 0:
                                current_full_text = data[0]
                                if isinstance(current_full_text, str):
                                    if current_full_text.startswith(last_full_text):
                                        delta = current_full_text[len(last_full_text):]
                                    else:
                                        delta = current_full_text
                                    last_full_text = current_full_text
                                    if delta:
                                        if raw:
                                            yield delta
                                        else:
                                            streaming_text += delta
                                            yield {"text": delta}
                        except Exception:
                            pass

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Error: {e}")
            finally:
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response if not raw else self.last_response.get("text", "")

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        raw = kwargs.get("raw", False)
        def for_stream():
            for response in self.ask(prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally):
                yield self.get_message(response) if not raw else cast(str, response)
        def for_non_stream():
            result = self.ask(prompt, False, raw=raw, optimizer=optimizer, conversationally=conversationally)
            return self.get_message(result) if not raw else cast(str, result)
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")

if __name__ == "__main__":
    ai = EssentialAI()
    response = ai.chat("Hello!", stream=True)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
