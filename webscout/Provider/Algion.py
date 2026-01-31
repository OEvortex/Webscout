import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent
from webscout.model_fetcher import BackgroundModelFetcher


class Algion(Provider):
    """
    A class to interact with the Algion API (OpenAI-compatible free API).

    Attributes:
        AVAILABLE_MODELS: List of available models
        url: API endpoint URL
        api: API key for authentication

    Examples:
        >>> from webscout.Provider.Algion import Algion
        >>> ai = Algion()
        >>> response = ai.chat("Hello, how are you?")
        >>> print(response)
    """
    # Background model fetcher
    _model_fetcher = BackgroundModelFetcher()

    @classmethod
    def get_models(cls, api_key: Optional[str] = None):
        """Fetch available models from Algion API.

        Args:
            api_key (str, optional): Algion API key. If not provided, uses default free key.

        Returns:
            list: List of available model IDs
        """
        api_key = api_key or "123123"

        try:
            # Use a temporary curl_cffi session for this class method
            temp_session = Session()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

            response = temp_session.get(
                "https://api.algion.dev/v1/models",
                headers=headers,
                impersonate="chrome110"
            )

            if response.status_code != 200:
                raise Exception(f"Failed to fetch models: HTTP {response.status_code}")

            data = response.json()
            if "data" in data and isinstance(data["data"], list):
                return [model["id"] for model in data["data"]]
            raise Exception("Invalid response format from API")

        except (CurlError, Exception) as e:
            raise Exception(f"Failed to fetch models: {str(e)}")

    required_auth = False
    AVAILABLE_MODELS = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "o1-mini"]

    @staticmethod
    def _algion_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from Algion stream JSON objects (OpenAI format)."""
        if isinstance(chunk, dict):
            return chunk.get("choices", [{}])[0].get("delta", {}).get("content")
        return None

    def __init__(
        self,
        api_key: Optional[str] = "123123",  # Default free API key
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "gpt-4o",
        system_prompt: str = "You are a helpful assistant.",
        browser: str = "chrome"
    ):
        """Initializes the Algion API client.

        Args:
            api_key: API key for authentication (default: "123123" - free key)
            is_conversation: Whether to use conversation mode
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            intro: Introduction message for conversation
            filepath: Path to save conversation history
            update_file: Whether to update conversation file
            proxies: Proxy configuration
            history_offset: Conversation history offset
            act: Act/role for the assistant
            model: Model to use (default: "gpt-4o")
            system_prompt: System prompt for the assistant
            browser: Browser fingerprint to use
        """
        # Start background model fetch (non-blocking)
        self._model_fetcher.fetch_async(
            provider_name="Algion",
            fetch_func=lambda: self.get_models(api_key),
            fallback_models=self.AVAILABLE_MODELS,
            timeout=10,
        )

        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.url = "https://api.algion.dev/v1/chat/completions"

        # Initialize LitAgent
        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.api = api_key

        # Set up headers
        self.headers = {
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api}",
            "User-Agent": self.fingerprint.get("user_agent", ""),
            "Sec-CH-UA": self.fingerprint.get("sec_ch_ua", ""),
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self.fingerprint.get("platform", "")}"',
            "Origin": "https://algion.dev",
            "Referer": "https://algion.dev/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

        # Initialize curl_cffi Session
        self.session = Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

        self.system_prompt = system_prompt
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
        self.conversation.history_offset = history_offset

        if act:
            act_val = cast(Union[str, int], act)
            self.conversation.intro = AwesomePrompts().get_act(
                act_val, default=self.conversation.intro, case_insensitive=True
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro

    def refresh_identity(self, browser: Optional[str] = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint

        Returns:
            dict: New fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)

        # Update headers with new fingerprint
        self.headers.update({
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "User-Agent": self.fingerprint.get("user_agent", ""),
            "Sec-CH-UA": self.fingerprint.get("sec_ch_ua", ""),
            "Sec-CH-UA-Platform": f'"{self.fingerprint.get("platform", "")}"',
        })

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
        **kwargs: Any,
    ) -> Response:
        """
        Sends a prompt to the Algion API and returns the response.

        Args:
            prompt: The prompt to send
            stream: Whether to stream the response
            raw: Whether to return raw response
            optimizer: Optimizer to use for the prompt
            conversationally: Whether to use conversation mode

        Returns:
            Dict or Generator: Response from the API

        Examples:
            >>> ai = Algion()
            >>> response = ai.ask("What is AI?")
            >>> print(response['text'])
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        # Payload construction (OpenAI format)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()

                # Use sanitize_stream for OpenAI-format streaming
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=self._algion_extractor,
                    yield_raw_on_error=False,
                    raw=raw
                )

                for content_chunk in processed_stream:
                    # Always yield as string, even in raw mode
                    if isinstance(content_chunk, bytes):
                        content_chunk = content_chunk.decode('utf-8', errors='ignore')

                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                            yield dict(text=content_chunk)

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {str(e)}"
                ) from e
            except Exception as e:
                err_text = ""
                if hasattr(e, 'response'):
                    response_obj = getattr(e, 'response')
                    if hasattr(response_obj, 'text'):
                        err_text = getattr(response_obj, 'text')
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed ({type(e).__name__}): {e} - {err_text}"
                ) from e
            finally:
                if not raw and streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            try:
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()

                response_text = response.text

                # Parse non-streaming JSON response
                processed_stream = sanitize_stream(
                    data=response_text,
                    to_json=True,
                    intro_value=None,
                    content_extractor=lambda chunk: chunk.get("choices", [{}])[0].get("message", {}).get("content") if isinstance(chunk, dict) else None,
                    yield_raw_on_error=False
                )
                content = next(processed_stream, None)
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
                if hasattr(e, 'response'):
                    response_obj = getattr(e, 'response')
                    if hasattr(response_obj, 'text'):
                        err_text = getattr(response_obj, 'text')
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
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        raw = kwargs.get("raw", False)
        if stream:
            def for_stream_chat():
                gen = self.ask(
                    prompt, stream=True, raw=raw,
                    optimizer=optimizer, conversationally=conversationally
                )
                if hasattr(gen, "__iter__"):
                    for response in gen:
                        if raw:
                            yield cast(str, response)
                        else:
                            yield self.get_message(response)
            return for_stream_chat()
        else:
            result = self.ask(
                prompt, stream=False, raw=raw,
                optimizer=optimizer, conversationally=conversationally
            )
            if raw:
                return cast(str, result)
            else:
                return self.get_message(result)

    def get_message(self, response: Response) -> str:
        """
        Extracts the message from the API response.

        Args:
            response: The API response dictionary

        Returns:
            str: The message content
        """
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    from rich import print

    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in Algion.AVAILABLE_MODELS:
        try:
            test_ai = Algion(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            for chunk in response:
                response_text += chunk

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                clean_text = response_text.strip().encode('utf-8', errors='ignore').decode('utf-8')
                display_text = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")
