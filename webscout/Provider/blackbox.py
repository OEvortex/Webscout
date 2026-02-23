import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent
from webscout.model_fetcher import BackgroundModelFetcher


class Blackbox(Provider):
    """
    A class to interact with Blackbox AI API.

    Blackbox AI is a code-focused AI assistant that provides code generation
    and understanding capabilities. This provider uses the Blackbox VSCode
    extension API endpoint.

    Example:
        >>> client = Blackbox()
        >>> response = client.ask("Write a Python function to calculate factorial")
        >>> print(response)
    """

    required_auth = False
    AVAILABLE_MODELS = [
        "moonshotai/kimi-k2.5",
        "custom/blackbox-base-2",
        "minimax-m2",
    ]
    # Background model fetcher
    _model_fetcher = BackgroundModelFetcher()

    @classmethod
    def get_models(cls, api_key: Optional[str] = None):
        """Fetch available models from Blackbox API.

        Note: Blackbox API doesn't have a public models endpoint,
        so we return the default known models.

        Args:
            api_key (str, optional): Blackbox API key (not required)

        Returns:
            list: List of available model IDs
        """
        return cls.AVAILABLE_MODELS

    @staticmethod
    def _blackbox_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from Blackbox stream JSON objects."""
        if isinstance(chunk, dict):
            try:
                return chunk.get("choices", [{}])[0].get("delta", {}).get("content")
            except (IndexError, KeyError, TypeError):
                return None
        return None

    def __init__(
        self,
        api_key: Optional[str] = None,
        is_conversation: bool = True,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1.0,
        model: str = "moonshotai/kimi-k2.5",
        timeout: int = 60,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        base_url: str = "https://oi-vscode-server-985058387028.europe-west1.run.app/chat/completions",
        system_prompt: str = "You are a helpful assistant for code generation and code understanding.",
        browser: str = "chrome",
        customer_id: str = "",
        user_id: str = "",
        version: str = "1.1",
    ):
        """Initializes the Blackbox AI client.

        Args:
            api_key: Optional API key for authentication
            is_conversation: Whether to maintain conversation context
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 - 2.0)
            presence_penalty: Presence penalty for diversity
            frequency_penalty: Frequency penalty for diversity
            top_p: Nucleus sampling parameter
            model: Model to use for generation
            timeout: Request timeout in seconds
            intro: Custom introduction message
            filepath: Path to save conversation history
            update_file: Whether to update conversation file
            proxies: Proxy configuration dictionary
            history_offset: Offset for conversation history
            act: Action prompt from AwesomePrompts
            base_url: API base URL
            system_prompt: System prompt for the assistant
            browser: Browser type for fingerprint generation
            customer_id: Customer ID header (required by Blackbox API)
            user_id: User ID header (required by Blackbox API)
            version: API version header
        """
        self.url = base_url

        # Initialize LitAgent for browser fingerprinting
        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.api_key = api_key

        # Build headers with fingerprint
        self.headers = {
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "User-Agent": self.fingerprint.get("user_agent", ""),
            "Sec-CH-UA": self.fingerprint.get("sec_ch_ua", ""),
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self.fingerprint.get("platform", "")}"',
        }

        # Add API key if provided
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

        # Add required Blackbox headers
        self.headers["customerId"] = customer_id
        self.headers["userId"] = user_id
        self.headers["version"] = version

        # Initialize curl_cffi Session
        self.session = Session()
        # Update curl_cffi session headers and proxies
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(cast(Any, proxies))

        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p

        # Start background model fetch (non-blocking)
        self._model_fetcher.fetch_async(
            provider_name="Blackbox",
            fetch_func=lambda: self.get_models(api_key),
            fallback_models=self.AVAILABLE_MODELS,
            timeout=10,
        )

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

    def refresh_identity(self, browser: Optional[str] = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint

        Returns:
            dict: New fingerprint dictionary
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)

        # Update headers with new fingerprint
        self.headers.update(
            {
                "Accept": self.fingerprint["accept"],
                "Accept-Language": self.fingerprint["accept_language"],
                "User-Agent": self.fingerprint.get("user_agent", ""),
            }
        )

        # Update session headers
        self.session.headers.update(self.headers)

        return self.fingerprint

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Response:
        """Send a prompt to Blackbox AI and get a response.

        Args:
            prompt: User input prompt
            stream: Whether to stream the response
            raw: Whether to return raw response
            optimizer: Optimizer to use for prompt enhancement
            conversationally: Whether to treat as conversation
            model: Model to use (overrides instance model)
            **kwargs: Additional parameters

        Returns:
            Response object or generator for streaming
        """
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

        # Payload construction
        payload = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream,
            "max_tokens": self.max_tokens_to_sample,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }
        payload.update(kwargs)

        def for_stream():
            streaming_text = ""
            try:
                # Use curl_cffi session post with impersonate
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome120",
                )
                response.raise_for_status()

                # Use sanitize_stream
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=self._blackbox_extractor,
                    yield_raw_on_error=False,
                    raw=raw,
                )

                for content_chunk in processed_stream:
                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                            resp = dict(text=content_chunk)
                            yield resp if not raw else content_chunk

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {str(e)}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed ({type(e).__name__}): {str(e)}"
                ) from e
            finally:
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            try:
                # Use curl_cffi session post with impersonate for non-streaming
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                    impersonate="chrome120",
                )
                response.raise_for_status()

                response_text = response.text

                # Use sanitize_stream to parse the non-streaming JSON response
                processed_stream = sanitize_stream(
                    data=response_text,
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
                # Extract the single result
                content = next(processed_stream, None)
                if raw:
                    return content
                content = content if isinstance(content, str) else ""

                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return self.last_response if not raw else content

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                err_text = ""
                if hasattr(e, "response"):
                    response_obj = getattr(e, "response")
                    if hasattr(response_obj, "text"):
                        err_text = getattr(response_obj, "text")
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed ({type(e).__name__}): {e} - {err_text}"
                ) from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Chat with Blackbox AI.

        Args:
            prompt: User input prompt
            stream: Whether to stream the response
            optimizer: Optimizer to use for prompt enhancement
            conversationally: Whether to treat as conversation
            model: Model to use (overrides instance model)
            **kwargs: Additional parameters

        Returns:
            String response or generator for streaming
        """
        def for_stream_chat():
            gen = self.ask(
                prompt,
                stream=True,
                raw=False,
                optimizer=optimizer,
                conversationally=conversationally,
                model=model,
                **kwargs,
            )
            for response_dict in gen:
                yield self.get_message(response_dict)

        def for_non_stream_chat():
            response_data = self.ask(
                prompt,
                stream=False,
                raw=False,
                optimizer=optimizer,
                conversationally=conversationally,
                model=model,
                **kwargs,
            )
            return self.get_message(response_data)

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        """Extract message text from response.

        Args:
            response: Response object or dictionary

        Returns:
            Extracted message text
        """
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    # Test the provider
    client = Blackbox()

    # Test streaming
    print("Testing streaming:")
    response = client.chat(
        "Write a Python function to calculate the factorial of a number.",
        stream=True,
        max_tokens=500,
    )

    for chunk in response:
        print(chunk, end="", flush=True)
    print("\n")

    # Test non-streaming
    print("Testing non-streaming:")
    response = client.chat(
        "What is 2 + 2?",
        stream=False,
        max_tokens=100,
    )
    print(response)
