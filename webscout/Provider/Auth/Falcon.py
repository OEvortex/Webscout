import json
import uuid
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


class Falcon(Provider):
    """
    A class to interact with the Falcon LLM Chat API (https://chat.falconllm.tii.ae/).
    """

    required_auth = True
    AVAILABLE_MODELS = [
        "falcon-h1-7b",
        "falcon-h1-7b-instruct",
        "falcon-h1-7b-chat",
        "falcon-h1-13b",
        "falcon-h1-13b-instruct",
        "falcon-h1-13b-chat",
        "falcon-h1-34b",
        "falcon-h1-34b-instruct",
        "falcon-h1-34b-chat",
        "falcon-h1-arabic-3b-instruct",
        "falcon-h1-arabic-7b-instruct",
        "falcon-h1-arabic-34b-instruct",
        "falcon3-audio-7b-instruct",
    ]

    @staticmethod
    def _falcon_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from Falcon LLM stream JSON objects (SSE format)."""
        if isinstance(chunk, dict):
            delta = chunk.get("delta")
            if delta and isinstance(delta, dict):
                return delta.get("content")
        return None

    def __init__(
        self,
        cookies_path: str,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "falcon-h1r-7b",
        system_prompt: str = "You are a helpful assistant.",
    ):
        """Initializes the Falcon LLM API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = Session(impersonate="chrome")
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://chat.falconllm.tii.ae/api/chat/completions"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.cookies_path = cookies_path
        self.cookies_dict, self.token = self._load_cookies()
        self.chat_id = str(uuid.uuid4())

        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": f"Bearer {self.token}" if self.token else "",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Origin": "https://chat.falconllm.tii.ae",
            "Pragma": "no-cache",
            "Referer": "https://chat.falconllm.tii.ae/anonymous-chat",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        }

        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies_dict)
        if proxies:
            self.session.proxies.update(proxies)

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

    def _load_cookies(self) -> tuple[dict, str]:
        """Load cookies from a JSON file and build a cookie dict."""
        try:
            with open(self.cookies_path, "r") as f:
                cookies = json.load(f)
            cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
            token = cookies_dict.get("token", "")
            return cookies_dict, token
        except FileNotFoundError:
            raise exceptions.InvalidAuthenticationError("Error: cookies.json file not found!")
        except json.JSONDecodeError:
            raise exceptions.InvalidAuthenticationError(
                "Error: Invalid JSON format in cookies.json!"
            )

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """Chat with AI."""

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {list(self.__available_optimizers)}")

        payload = {
            "stream": stream,
            "model": self.model,
            "messages": [{"role": "user", "content": conversation_prompt}],
            "params": {},
            "tool_servers": [],
            "features": {
                "image_generation": False,
                "code_interpreter": False,
                "web_search": False,
            },
            "session_id": str(uuid.uuid4()),
            "chat_id": "local",
            "id": str(uuid.uuid4()),
        }

        def for_stream() -> Generator[Dict[str, Any], None, None]:
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                headers=self.headers,
                stream=True,
                timeout=self.timeout,
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_text = ""
            processed_stream = sanitize_stream(
                data=response.iter_lines(decode_unicode=False),
                intro_value="data:",
                to_json=True,
                skip_markers=["[DONE]"],
                content_extractor=self._falcon_extractor,
                yield_raw_on_error=False,
                raw=raw,
            )

            for content_chunk in processed_stream:
                if isinstance(content_chunk, bytes):
                    content_chunk = content_chunk.decode("utf-8", errors="ignore")

                if raw:
                    yield content_chunk
                else:
                    if content_chunk and isinstance(content_chunk, str):
                        streaming_text += content_chunk
                        yield dict(text=content_chunk)

            if not raw and streaming_text:
                self.last_response = {"text": streaming_text}
                self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream() -> Dict[str, Any]:
            """Handles non-streaming responses by making a non-streaming request."""
            non_stream_payload = payload.copy()
            non_stream_payload["stream"] = False

            response = self.session.post(
                self.api_endpoint,
                json=non_stream_payload,
                headers=self.headers,
                stream=False,
                timeout=self.timeout,
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            processed_stream = sanitize_stream(
                data=response.text,
                to_json=True,
                intro_value=None,
                content_extractor=lambda chunk: chunk.get("choices", [{}])[0]
                .get("message", {})
                .get("content")
                if isinstance(chunk, dict)
                else None,
                yield_raw_on_error=False,
                raw=raw,
            )
            if raw:
                return response.text

            content = next(processed_stream, None)
            content = content if isinstance(content, str) else ""

            self.last_response = {"text": content}
            self.conversation.update_chat_history(prompt, content)
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Generates a chat response from the Falcon API."""
        raw = kwargs.get("raw", False)

        def for_stream() -> Generator[str, None, None]:
            for response in self.ask(
                prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield cast(str, response)
                else:
                    yield cast(Dict[str, Any], response)["text"]

        def for_non_stream() -> str:
            result = self.ask(
                prompt, False, raw=raw, optimizer=optimizer, conversationally=conversationally
            )
            if raw:
                return cast(str, result)
            else:
                return self.get_message(cast(Dict[str, Any], result))

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        """Extracts the message content from a response dict."""
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    from rich import print

    cookies_path = r"C:\Users\koula\Desktop\Webscout\cookies.json"
    for model in Falcon.AVAILABLE_MODELS[:2]:
        try:
            ai = Falcon(cookies_path=cookies_path, model=model)
            response = ai.chat("hi")
            print(f"Model: {model}")
            print(response)
            print("-" * 50)
        except Exception as e:
            print(f"Error with model {model}: {e}")
