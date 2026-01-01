import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers


class Llama3Mitril(Provider):
    """
    A class to interact with the Llama3 Mitril API. Implements the WebScout provider interface.
    """

    required_auth = False

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2048,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        system_prompt: str = "You are a helpful, respectful and honest assistant.",
        temperature: float = 0.8,
    ):
        """Initializes the Llama3Mitril API."""
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api_endpoint = "https://llama3.mithrilsecurity.io/generate_stream"
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.headers = {
            "Content-Type": "application/json",
            "DNT": "1",
        }
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.conversation = Conversation(is_conversation, self.max_tokens, filepath, update_file)
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
        # Update curl_cffi session headers and proxies
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(cast(Any, proxies))

    def _format_prompt(self, prompt: str) -> str:
        """Format the prompt for the Llama3 model"""
        return (
            f"<|begin_of_text|>"
            f"<|start_header_id|>system<|end_header_id|>{self.system_prompt}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>{prompt}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|><|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )

    def ask(
        self,
        prompt: str,
        stream: bool = True,  # API supports streaming
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """Sends a prompt to the Llama3 Mitril API and returns the response."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        data = {
            "inputs": self._format_prompt(conversation_prompt),
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "return_full_text": False,
            },
        }

        def for_stream():
            streaming_response = ""  # Initialize outside try block
            try:
                # Use curl_cffi session post with impersonate
                response = self.session.post(
                    self.api_endpoint,
                    # headers are set on the session
                    json=data,
                    stream=True,
                    timeout=self.timeout,
                    # proxies are set on the session
                    impersonate="chrome110",  # Use a common impersonation profile
                )
                response.raise_for_status()  # Check for HTTP errors

                # Iterate over bytes and decode manually
                for line_bytes in response.iter_lines():
                    if line_bytes:
                        try:
                            line = line_bytes.decode("utf-8")
                            if line.startswith("data: "):
                                chunk_str = line.split("data: ", 1)[1]
                                chunk = json.loads(chunk_str)
                                if token_text := chunk.get("token", {}).get("text"):
                                    if "<|eot_id|>" not in token_text:
                                        streaming_response += token_text
                                        resp = {"text": token_text}
                                        # Yield dict or raw string chunk
                                        yield resp if not raw else token_text
                        except (json.JSONDecodeError, IndexError, UnicodeDecodeError):
                            # Ignore errors in parsing specific lines
                            continue

                # Update history after stream finishes
                self.last_response = {"text": streaming_response}
                self.conversation.update_chat_history(prompt, streaming_response)

            except CurlError as e:  # Catch CurlError
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:  # Catch other potential exceptions (like HTTPError)
                err_text = ""
                if hasattr(e, "response"):
                    response_obj = getattr(e, "response")
                    if hasattr(response_obj, "text"):
                        err_text = getattr(response_obj, "text")
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response ({type(e).__name__}): {e} - {err_text}"
                ) from e

        def for_non_stream():
            # Aggregate the stream using the updated for_stream logic
            full_response_text = ""
            try:
                # Ensure raw=False so for_stream yields dicts
                for chunk_data in for_stream():
                    if isinstance(chunk_data, dict) and "text" in chunk_data:
                        full_response_text += chunk_data["text"]
                    # Handle raw string case if raw=True was passed
                    elif raw and isinstance(chunk_data, str):
                        full_response_text += chunk_data
            except Exception as e:
                # If aggregation fails but some text was received, use it. Otherwise, re-raise.
                if not full_response_text:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to get non-stream response: {str(e)}"
                    ) from e

            # last_response and history are updated within for_stream
            # Return the final aggregated response dict or raw string
            return full_response_text if raw else self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = True,  # Default to True as API supports it
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Generates a response from the Llama3 Mitril API."""

        def for_stream_chat():
            # ask() yields dicts or strings when streaming
            gen = self.ask(
                prompt,
                stream=True,
                raw=False,  # Ensure ask yields dicts
                optimizer=optimizer,
                conversationally=conversationally,
            )
            for response_dict in gen:
                yield self.get_message(response_dict)  # get_message expects dict

        def for_non_stream_chat():
            # ask() returns dict or str when not streaming
            response_data = self.ask(
                prompt,
                stream=False,
                raw=False,  # Ensure ask returns dict
                optimizer=optimizer,
                conversationally=conversationally,
            )
            return self.get_message(response_data)  # get_message expects dict

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return response["text"]


if __name__ == "__main__":
    # Ensure curl_cffi is installed
    from rich import print

    ai = Llama3Mitril(max_tokens=2048, temperature=0.8, timeout=30)

    for response in ai.chat("Hello", stream=True):
        print(response, end="", flush=True)
