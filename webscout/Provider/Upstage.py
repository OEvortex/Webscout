"""Upstage Solar API Provider for Webscout."""

import json
from typing import Any, Dict, Generator, Optional, Union, cast

import requests

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import (
    AwesomePrompts,
    Conversation,
    Optimizers,
    sanitize_stream,
)


class Upstage(Provider):
    """Upstage Solar API Provider.

    A provider for interacting with Upstage Solar models. Enables integration
    with Upstage's Solar family including Solar 1 Pro, Solar Pro 2, and
    Solar Pro 3. The API supports streaming responses and multi-turn conversations.

    Required API Key:
        - Get from https://console.upstage.ai/api-keys
        - Set via api_key parameter or UPSTAGE_API_KEY environment variable

    Attributes:
        api_key (str): Your Upstage API key
        is_conversation (bool): Whether to maintain conversation history
        max_tokens (int): Maximum tokens in response (default: 4096)
        temperature (float): Sampling temperature (0.0-2.0, default: 0.7)
        top_p (float): Nucleus sampling parameter (default: 0.9)
        timeout (int): Request timeout in seconds (default: 30)

    Available Models:
        - solar-1-pro: Upstage Solar 1 Pro
        - solar-pro-2: Upstage Solar Pro 2
        - solar-pro-3: Upstage Solar Pro 3 (default)

    Examples:
        >>> from webscout import Upstage
        >>> api = Upstage(api_key="YOUR_API_KEY")
        >>> response = api.chat("What is machine learning?")
        >>> print(response)

        >>> for chunk in api.chat("Explain quantum computing", stream=True):
        ...     print(chunk, end="", flush=True)
    """

    required_auth = True
    AVAILABLE_MODELS = [
        "solar-1-pro",
        "solar-pro-2",
        "solar-pro-3",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        is_conversation: bool = True,
        max_tokens: int = 4096,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: Optional[Dict[str, str]] = None,
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "solar-pro-3",
        temperature: float = 0.7,
        top_p: float = 0.9,
        system_message: str = "You are a helpful assistant.",
    ):
        """
        Initialize the Upstage API client.

        Args:
            api_key: Upstage API key. If None, uses UPSTAGE_API_KEY env var.
            is_conversation: Whether to maintain conversation history.
            max_tokens: Maximum tokens in the response.
            timeout: Request timeout in seconds.
            intro: Introduction text for the conversation.
            filepath: Path to save conversation history.
            update_file: Whether to update conversation history file.
            proxies: Proxy configuration for requests.
            history_offset: Maximum history length in characters.
            act: Persona/act for the conversation.
            model: Model to use. Must be one of AVAILABLE_MODELS.
            temperature: Sampling temperature (0.0-2.0).
            top_p: Nucleus sampling parameter (0.0-1.0).
            system_message: System prompt for the conversation.

        Raises:
            AuthenticationError: If API key is not provided.
            ValueError: If model is not in AVAILABLE_MODELS.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}"
            )

        if not api_key:
            import os

            api_key = os.getenv("UPSTAGE_API_KEY")
            if not api_key:
                raise exceptions.AuthenticationError(
                    "Upstage API key is required. "
                    "Set via api_key parameter or UPSTAGE_API_KEY env var."
                )

        self.api_key = api_key
        self.url = "https://api.upstage.ai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/144.0.0.0 Safari/537.36"
            ),
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.system_message = system_message

        self.__available_optimizers = (
            dir(Optimizers) if is_conversation else None
        )

        self.conversation: Conversation = Conversation(
            filepath=filepath,
            update_file=update_file,
            max_tokens=history_offset,
        )

        if intro:
            self.conversation.intro = intro
        elif act:
            self.conversation.intro = (
                AwesomePrompts().get_act(
                    cast(Union[str, int], act),
                    default=self.conversation.intro,
                    case_insensitive=True,
                )
                or self.conversation.intro
            )

    @staticmethod
    def _upstage_extractor(
        chunk_json: Union[str, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Extract content from Upstage streaming response.

        Args:
            chunk_json: JSON chunk from the stream

        Returns:
            Content string or None if not present
        """
        if (
            not isinstance(chunk_json, dict)
            or "choices" not in chunk_json
            or not chunk_json["choices"]
        ):
            return None

        delta = chunk_json["choices"][0].get("delta")
        if not isinstance(delta, dict):
            return None

        content = delta.get("content")
        return content if isinstance(content, str) else None

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], Generator[str, None, None]]:
        """
        Send a request to the Upstage API.

        Args:
            prompt: The user's prompt/question.
            stream: Whether to stream the response.
            raw: Whether to return raw response without formatting.
            optimizer: Optimization mode for the prompt.
            conversationally: Whether to include conversation history.
            **kwargs: Additional arguments (unused).

        Returns:
            Dictionary or generator depending on stream setting.

        Raises:
            FailedToGenerateResponseError: If the API request fails.
            InvalidArgumentError: If optimizer is not valid.
        """
        conversation_prompt = (
            self.conversation.gen_complete_prompt(prompt)
            if conversationally
            else prompt
        )

        if optimizer:
            if (
                self.__available_optimizers
                and optimizer in self.__available_optimizers
            ):
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt
                )
            else:
                raise exceptions.InvalidOptimizerError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        # Prepare messages list
        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": conversation_prompt})

        # Prepare the payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }

        def for_stream() -> Generator[str, None, None]:
            """Handle streaming response."""
            streaming_text = ""
            try:
                response = self.session.post(
                    self.url, json=payload, stream=True, timeout=self.timeout
                )

                if response.status_code != 200:
                    try:
                        error_detail = response.json()
                        error_msg = error_detail.get("error", {}).get(
                            "message", response.text
                        )
                    except (json.JSONDecodeError, AttributeError):
                        error_msg = response.text

                    raise exceptions.FailedToGenerateResponseError(
                        f"Status {response.status_code}: {error_msg}"
                    )

                # Process the SSE stream
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=self._upstage_extractor,
                    yield_raw_on_error=False,
                )

                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
                        streaming_text += content_chunk
                        resp = {"text": content_chunk}
                        yield resp if not raw else content_chunk

                # Update conversation history
                self.last_response = {"text": streaming_text}
                if conversationally:
                    self.conversation.update_chat_history(
                        prompt, streaming_text
                    )

            except requests.RequestException as e:
                raise exceptions.APIConnectionError(
                    f"Network error: {e}"
                ) from e
            except exceptions.WebscoutE:
                raise
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Unexpected error: {e}"
                ) from e

        def for_non_stream() -> Dict[str, Any]:
            """Handle non-streaming response."""
            try:
                response = self.session.post(
                    self.url, json=payload, stream=False, timeout=self.timeout
                )

                if response.status_code != 200:
                    try:
                        error_detail = response.json()
                        error_msg = error_detail.get("error", {}).get(
                            "message", response.text
                        )
                    except (json.JSONDecodeError, AttributeError):
                        error_msg = response.text

                    raise exceptions.FailedToGenerateResponseError(
                        f"Status {response.status_code}: {error_msg}"
                    )

                response_json = response.json()

                # Extract the response text
                if (
                    "choices" in response_json
                    and response_json["choices"]
                    and "message" in response_json["choices"][0]
                ):
                    content = response_json["choices"][0]["message"].get(
                        "content", ""
                    )
                else:
                    content = ""

                self.last_response = {
                    "text": content,
                    "raw": response_json,
                }

                # Update conversation history
                if conversationally:
                    self.conversation.update_chat_history(prompt, content)

                return {"text": content} if not raw else response_json

            except requests.RequestException as e:
                raise exceptions.APIConnectionError(
                    f"Network error: {e}"
                ) from e
            except exceptions.WebscoutE:
                raise
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Unexpected error: {e}"
                ) from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = True,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Send a chat message and get a response.

        Args:
            prompt: The user's message.
            stream: Whether to stream the response (default: True).
            optimizer: Optimization mode for the prompt.
            conversationally: Whether to include conversation history.
            **kwargs: Additional arguments (unused).

        Returns:
            String response or generator yielding response chunks.

        Examples:
            >>> api = Upstage(api_key="...")
            >>> response = api.chat("What is AI?")
            >>> print(response)

            >>> # Streaming
            >>> for chunk in api.chat("Hello", stream=True):
            ...     print(chunk, end="", flush=True)
        """
        raw = kwargs.get("raw", False)

        def stream_generator() -> Generator[str, None, None]:
            """Generate streamed responses."""
            gen = self.ask(
                prompt,
                stream=True,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            for response in gen:
                if raw:
                    yield response
                else:
                    yield self.get_message(cast(Response, response))

        def non_stream_response() -> str:
            """Get non-streamed response."""
            result = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, result)
            return self.get_message(cast(Response, result))

        return stream_generator() if stream else non_stream_response()

    def get_message(self, response: Response) -> str:
        """
        Extract message text from response.

        Args:
            response: Response object (dict or string).

        Returns:
            Extracted message text.
        """
        if not isinstance(response, dict):
            return str(response)

        response_dict = cast(Dict[str, Any], response)
        return response_dict.get("text", "")


if __name__ == "__main__":
    from rich import print

    # Example usage
    try:
        api = Upstage(api_key="YOUR_API_KEY_HERE")

        # Non-streaming example
        print("[cyan]Non-Streaming Response:[/cyan]")
        response = api.chat(
            "What are the limitations of current AI models?", stream=False
        )
        print(response)

        print("\n[cyan]Streaming Response:[/cyan]")
        # Streaming example
        for chunk in api.chat(
            "Write a short poem about machine learning", stream=True
        ):
            print(chunk, end="", flush=True)
        print()

    except exceptions.AuthenticationError as e:
        print(f"[red]Auth Error: {e}[/red]")
    except exceptions.FailedToGenerateResponseError as e:
        print(f"[red]Generation Error: {e}[/red]")
