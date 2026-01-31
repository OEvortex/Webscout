import json
import uuid
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


class QwenLM(Provider):
    """
    A class to interact with the QwenLM API
    """

    required_auth = True
    AVAILABLE_MODELS = [
        "qwen3-max-2026-01-23",
        "qwen3-vl-plus",
        "qwen3-coder-plus",
        "qwen3-vl-32b",
        "qwen3-vl-30b-a3b",
        "qwen3-omni-flash-2025-12-01",
        "qwen-plus-2025-09-11",
        "qwen-plus-2025-07-28",
        "qwen3-30b-a3b",
        "qwen3-coder-30b-a3b-instruct",
        "qwen-max-latest",
        "qwen-plus-2025-01-25",
        "qwq-32b",
        "qwen-turbo-2025-02-11",
        "qwen2.5-omni-7b",
        "qvq-72b-preview-0310",
        "qwen2.5-vl-32b-instruct",
        "qwen2.5-14b-instruct-1m",
        "qwen2.5-coder-32b-instruct",
        "qwen2.5-72b-instruct",
    ]

    @staticmethod
    def _qwenlm_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from QwenLM stream JSON objects."""
        if isinstance(chunk, dict):
            choices = chunk.get("choices")
            if choices:
                delta = choices[0].get("delta", {})
                status = delta.get("status")
                if status == "finished":
                    return None
                return delta.get("content")
        return None

    def __init__(
        self,
        cookies_path: str,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "qwen3-max-2026-01-23",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """Initializes the QwenLM API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = Session(impersonate="chrome")
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://chat.qwen.ai/api/chat/completions"
        self.stream_chunk_size = 64
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
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Origin": "https://chat.qwen.ai",
            "Pragma": "no-cache",
            "Referer": f"https://chat.qwen.ai/c/{self.chat_id}",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "authorization": f"Bearer {self.token}" if self.token else "",
        }
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies_dict)
        if proxies:
            self.session.proxies.update(proxies)
        self.chat_type = "t2t"  # search - used WEB, t2t - chatbot, t2i - image_gen

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
            "incremental_output": False,
            "chat_type": "t2t",
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": conversation_prompt,
                    "chat_type": "t2t",
                    "extra": {},
                    "feature_config": {"thinking_enabled": False},
                }
            ],
            "session_id": str(uuid.uuid4()),
            "chat_id": str(uuid.uuid4()),
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
                content_extractor=self._qwenlm_extractor,
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
            """
            Handles non-streaming responses by making a non-streaming request.
            """

            # Create a non-streaming payload
            non_stream_payload = payload.copy()
            non_stream_payload["stream"] = False
            non_stream_payload["incremental_output"] = False

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

            # Use sanitize_stream to parse the non-streaming JSON response
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

            # Extract the single result
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
        """
        Generates a chat response from the QwenLM API.

        Args:
            prompt: The prompt to send to the API
            stream: Whether to stream the response
            optimizer: Optional prompt optimizer name
            conversationally: Whether to use conversation context
            **kwargs: Additional parameters including raw.

        Returns:
            When raw=False: Extracted message string or Generator yielding strings
            When raw=True: Raw response or Generator yielding raw chunks

        Examples:
            >>> ai = QwenLM(cookies_path="cookies.json")
            >>> # Get processed response
            >>> response = ai.chat("Hello")
            >>> print(response)

            >>> # Get raw response
            >>> raw_response = ai.chat("Hello", raw=True)
            >>> print(raw_response)

            >>> # Stream raw chunks
            >>> for chunk in ai.chat("Hello", stream=True, raw=True):
            ...     print(chunk, end='', flush=True)
        """
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
    for model in QwenLM.AVAILABLE_MODELS:
        ai = QwenLM(cookies_path=cookies_path, model=model)
        response = ai.chat("hi")
        print(f"Model: {model}")
        print(response)
        print("-" * 50)
    # for chunk in response:
    #     print(chunk, end="", flush=True)
