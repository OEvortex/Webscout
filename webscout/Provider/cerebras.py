import re

# Import trio before curl_cffi to prevent eventlet socket monkey-patching conflicts
# See: https://github.com/python-trio/trio/issues/3015
try:
    import trio  # noqa: F401 # type: ignore
except ImportError:
    pass  # trio is optional, ignore if not available
import json
from typing import Any, Dict, Generator, List, Optional, Union, cast

import curl_cffi
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import (  # Import sanitize_stream
    AwesomePrompts,
    Conversation,
    Optimizers,
    sanitize_stream,
)
from webscout.litagent import LitAgent as UserAgent
from webscout.model_fetcher import BackgroundModelFetcher


class Cerebras(Provider):
    """
    A class to interact with the Cerebras API using a cookie for authentication.
    """
    required_auth = True
    AVAILABLE_MODELS = [
        "qwen-3-coder-480b",
        "qwen-3-235b-a22b-instruct-2507",
        "qwen-3-235b-a22b-thinking-2507",
        "qwen-3-32b",
        "llama-3.3-70b",
        "llama-4-maverick-17b-128e-instruct",
        "gpt-oss-120b",
        "llama-4-scout-17b-16e-instruct",
        "llama3.1-8b"
    ]
    # Background model fetcher
    _model_fetcher = BackgroundModelFetcher()

    @classmethod
    def get_models(cls, api_key: Optional[str] = None):
        """Fetch available models from Cerebras API.

        Args:
            api_key (str, optional): Cerebras API key. If not provided, returns default models.

        Returns:
            list: List of available model IDs
        """
        if not api_key:
            raise Exception("API key required to fetch models")

        try:
            # Use a temporary curl_cffi session for this class method
            temp_session = Session()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

            response = temp_session.get(
                "https://api.cerebras.ai/v1/models",
                headers=headers,
                impersonate="chrome120"
            )

            if response.status_code != 200:
                raise Exception(f"Failed to fetch models: HTTP {response.status_code}")

            data = response.json()
            if "data" in data and isinstance(data["data"], list):
                return [model['id'] for model in data['data']]
            raise Exception("Invalid response format from API")

        except (curl_cffi.CurlError, Exception) as e:
            raise Exception(f"Failed to fetch models: {str(e)}")

    def __init__(
        self,
        cookie_path: Optional[str] = None,
        is_conversation: bool = True,
        max_tokens: int = 40000,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "qwen-3-coder-480b",
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        top_p: float = 0.8,
    ):
        # Initialize basic settings first
        self.timeout = timeout
        self.model = model
        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.last_response = {}

        # Start background model fetch (non-blocking)
        if api_key:
            self._model_fetcher.fetch_async(
                provider_name="Cerebras",
                fetch_func=lambda: self.get_models(api_key),
                fallback_models=self.AVAILABLE_MODELS,
                timeout=10,
            )

        self.session = Session() # Initialize curl_cffi session

        # Handle API key - either provided directly or retrieved from cookies
        if api_key:
            self.api_key = api_key.strip()
            # Basic validation for API key format
            if not self.api_key or len(self.api_key) < 10:
                raise ValueError("Invalid API key format. API key must be at least 10 characters long.")
        elif cookie_path:
            # Get API key from cookies
            try:
                self.api_key = self.get_demo_api_key(cookie_path)
            except Exception as e:
                raise exceptions.APIConnectionError(f"Failed to initialize Cerebras client: {e}")
        else:
            raise ValueError("Either api_key must be provided or cookie_path must be specified")

        # Validate model choice after updating models
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}"
            )

        # Initialize optimizers
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        # Initialize conversation settings
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = AwesomePrompts().get_act(cast(Union[str, int], act), default=self.conversation.intro, case_insensitive=True
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro

        # Set headers for the session
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": UserAgent().random(),
        }

        # Apply proxies to the session
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(cast(Any, proxies))
        self.last_response = {}

    # Rest of the class implementation remains the same...
    @staticmethod
    def extract_query(text: str) -> str:
        """Extracts the first code block from the given text."""
        pattern = r"```(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches[0].strip() if matches else text.strip()

    @staticmethod
    def refiner(text: str) -> str:
        """Refines the input text by removing surrounding quotes."""
        return text.strip('"')

    @staticmethod
    def _cerebras_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from Cerebras stream JSON objects."""
        if isinstance(chunk, dict):
            return chunk.get("choices", [{}])[0].get("delta", {}).get("content")
        return None

    def get_demo_api_key(self, cookie_path: Optional[str] = None) -> str: # Keep this using requests or switch to curl_cffi
        """Retrieves the demo API key using the provided cookie."""
        if not cookie_path:
            raise ValueError("cookie_path must be provided when using cookie-based authentication")
        try:
            with open(cookie_path, "r") as file:
                cookies = {item["name"]: item["value"] for item in json.load(file)}
        except FileNotFoundError:
            raise FileNotFoundError(f"Cookie file not found at path: {cookie_path}")
        except json.JSONDecodeError:
            raise json.JSONDecodeError("Invalid JSON format in the cookie file.", "", 0)

        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://inference.cerebras.ai",
            "Referer": "https://inference.cerebras.ai/",
            "user-agent": UserAgent().random(),
        }

        json_data = {
            "operationName": "GetMyDemoApiKey",
            "variables": {},
            "query": "query GetMyDemoApiKey {\n  GetMyDemoApiKey\n}",
        }

        try:
            # Use the initialized curl_cffi session
            response = self.session.post(
                "https://inference.cerebras.ai/api/graphql",
                cookies=cookies,
                headers=headers,
                json=json_data,
                timeout=self.timeout,
                impersonate="chrome120" # Add impersonate
            )
            response.raise_for_status()
            api_key = response.json().get("data", {}).get("GetMyDemoApiKey")
            return api_key
        except curl_cffi.CurlError as e:
            raise exceptions.APIConnectionError(f"Failed to retrieve API key: {e}")
        except KeyError:
            raise exceptions.InvalidResponseError("API key not found in response.")

    def _make_request(self, messages: List[Dict], stream: bool = False) -> Union[Dict, Generator, str]:
        """Make a request to the Cerebras API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": UserAgent().random(),
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "max_tokens": self.max_tokens_to_sample,
            "temperature": self.temperature,
            "top_p": self.top_p
        }

        try:
            # Use the initialized curl_cffi session
            response = self.session.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                stream=stream,
                timeout=self.timeout,
                impersonate="chrome120" # Add impersonate
            )
            response.raise_for_status()

            if stream:
                def generate_stream() -> Generator[str, None, None]:
                    # Use sanitize_stream
                    processed_stream = sanitize_stream(
                        data=response.iter_content(chunk_size=None), # Pass byte iterator
                        intro_value="data:",
                        to_json=True,     # Stream sends JSON
                        content_extractor=self._cerebras_extractor, # Use the specific extractor
                        yield_raw_on_error=False # Skip non-JSON lines or lines where extractor fails
                    )
                    for content_chunk in processed_stream:
                        if content_chunk and isinstance(content_chunk, str):
                            yield content_chunk # Yield the extracted text chunk

                return generate_stream()
            else:
                response_json = response.json()
                # Extract content for non-streaming response
                content = response_json.get("choices", [{}])[0].get("message", {}).get("content")
                return content if content else "" # Return empty string if not found

        except curl_cffi.CurlError as e:
            raise exceptions.APIConnectionError(f"Request failed (CurlError): {e}") from e
        except Exception as e:
            # Check if it's an HTTP error with status code
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
                if status_code == 401:
                    raise exceptions.APIConnectionError(
                        "Authentication failed (401): Invalid API key. Please check your API key and try again."
                    ) from e
                elif status_code == 403:
                    raise exceptions.APIConnectionError(
                        "Access forbidden (403): Your API key may not have permission to access this resource."
                    ) from e
                elif status_code == 429:
                    raise exceptions.APIConnectionError(
                        "Rate limit exceeded (429): Too many requests. Please wait and try again."
                    ) from e
                else:
                    raise exceptions.APIConnectionError(f"HTTP {status_code} error: {e}") from e
            else:
                raise exceptions.APIConnectionError(f"Request failed: {e}") from e

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False, # Add raw parameter for consistency
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """Send a prompt to the model and get a response."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": conversation_prompt}
        ]

        try:
            response = self._make_request(messages, stream)

            if stream:
                # Wrap the generator to yield dicts or raw strings
                def stream_wrapper() -> Generator[Union[str, Dict[str, str]], None, None]:
                    full_text = ""
                    for chunk in response:
                        full_text += chunk
                        yield chunk if raw else {"text": chunk}
                    # Update history after stream finishes
                    self.last_response = {"text": full_text}
                    self.conversation.update_chat_history(prompt, full_text)
                return stream_wrapper()
            else:
                # Non-streaming response is already the full text string
                self.last_response = {"text": response}
                self.conversation.update_chat_history(prompt, response)
                return self.last_response if not raw else json.dumps(self.last_response)

        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Error during request: {e}")

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Chat with the model."""
        raw = kwargs.get("raw", False)
        # Ask returns a generator for stream=True, dict/str for stream=False
        response_gen_or_dict = self.ask(prompt, stream, raw=raw, optimizer=optimizer, conversationally=conversationally, **kwargs)

        if stream:
            # Wrap the generator from ask() to get message text
            def stream_wrapper() -> Generator[str, None, None]:
                for chunk in response_gen_or_dict:
                    if raw:
                        yield chunk
                    else:
                        yield self.get_message(cast(Response, chunk))
            return stream_wrapper()
        else:
            # Non-streaming response
            if raw:
                return str(response_gen_or_dict)
            return self.get_message(response_gen_or_dict)

    def get_message(self, response: Response) -> str:
        """Retrieves message from response."""
        # Updated to handle dict input from ask()
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")

if __name__ == "__main__":
    from rich import print

    # Example usage
    cerebras = Cerebras(
        api_key='csk-**********************',  # Replace with your actual API key
        model='qwen-3-235b-a22b-instruct-2507',
        system_prompt="You are a helpful AI assistant."
    )

    # Test with streaming
    response = cerebras.chat("Hello!", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
