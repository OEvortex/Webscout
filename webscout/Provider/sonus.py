import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import (
    AwesomePrompts,
    Conversation,
    Optimizers,
)
from webscout.litagent import LitAgent


class SonusAI(Provider):
    """
    A class to interact with the Sonus AI chat API.
    """

    required_auth = False
    AVAILABLE_MODELS = ["pro", "air", "mini"]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "pro",
    ):
        """Initializes the Sonus AI API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.url = "https://chat.sonus.ai/chat.php"

        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://chat.sonus.ai",
            "Referer": "https://chat.sonus.ai/",
            "User-Agent": LitAgent().random(),
        }

        self.session = Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        act_prompt = (
            AwesomePrompts().get_act(
                cast(Union[str, int], act), default=None, case_insensitive=True
            )
            if act
            else intro
        )
        if act_prompt:
            self.conversation.intro = act_prompt
        self.conversation.history_offset = history_offset

    @staticmethod
    def _sonus_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from Sonus stream JSON objects."""
        if isinstance(chunk, dict) and "content" in chunk:
            return chunk.get("content")
        return None

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        reasoning: bool = False,
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

        form_data = {
            "message": conversation_prompt,
            "history": "",
            "reasoning": str(reasoning).lower(),
            "model": self.model,
            "stream": "true" if stream else "false",
        }

        def for_stream():
            try:
                response = self.session.post(
                    self.url,
                    data=form_data,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                if response.status_code != 200:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Request failed with status code {response.status_code} - {response.text}"
                    )

                streaming_text = ""
                # Parse JSON lines directly
                for line in response.iter_lines():
                    if not line:
                        continue
                    # Decode bytes to string
                    line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                    if line_str.startswith("data: "):
                        json_str = line_str[6:]  # Remove "data: " prefix
                        try:
                            data = json.loads(json_str)
                            if isinstance(data, dict) and "content" in data:
                                content = data.get("content", "")
                                if content:
                                    streaming_text += content
                                    if raw:
                                        yield content
                                    else:
                                        yield dict(text=content)
                        except json.JSONDecodeError:
                            continue

                # Update history and last response after stream finishes
                self.last_response = {"text": streaming_text}
                self.conversation.update_chat_history(prompt, streaming_text)

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {str(e)}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"An unexpected error occurred ({type(e).__name__}): {e}"
                ) from e

        def for_non_stream():
            try:
                response = self.session.post(
                    self.url, data=form_data, timeout=self.timeout, impersonate="chrome110"
                )
                if response.status_code != 200:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Request failed with status code {response.status_code} - {response.text}"
                    )

                response_text_raw = response.text

                full_response = ""
                for line in response_text_raw.splitlines():
                    if line.startswith("data: "):
                        json_str = line[6:]  # Remove "data: " prefix
                        try:
                            data = json.loads(json_str)
                            if isinstance(data, dict) and "content" in data:
                                content = data.get("content", "")
                                if content:
                                    full_response += content
                        except json.JSONDecodeError:
                            continue

                self.last_response = {"text": full_response}
                self.conversation.update_chat_history(prompt, full_response)
                # Return dict or raw string
                return full_response if raw else {"text": full_response}

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {str(e)}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"An unexpected error occurred ({type(e).__name__}): {e}"
                ) from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        reasoning: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        def for_stream_chat():
            for response in self.ask(
                prompt,
                stream=True,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
                reasoning=reasoning,
            ):
                if raw:
                    yield response
                else:
                    yield self.get_message(response)

        def for_non_stream_chat():
            response_data = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
                reasoning=reasoning,
            )
            if raw:
                return (
                    response_data
                    if isinstance(response_data, str)
                    else self.get_message(response_data)
                )
            else:
                return self.get_message(response_data)

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        response_dict = cast(Dict[str, Any], response)
        return response_dict.get("text", "")


if __name__ == "__main__":
    sonus = SonusAI()
    resp = sonus.chat("Hello", stream=True, raw=True)
    if hasattr(resp, "__iter__") and not isinstance(resp, (str, bytes)):
        for chunk in resp:
            print(chunk, end="")
    else:
        print(resp)
