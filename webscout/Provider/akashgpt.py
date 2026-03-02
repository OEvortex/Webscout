import json
import re
import time
from os import path
from typing import Any, Dict, Generator, Optional, Union, cast
from uuid import uuid4

from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import (  # Import sanitize_stream
    AwesomePrompts,
    Conversation,
    Optimizers,
    sanitize_stream,
)
from webscout.litagent import LitAgent


class AkashGPT(Provider):
    """
    A class to interact with the Akash Network Chat API.

    This provider requires Cloudflare clearance cookies (cf_clearance and session_token)
    that must be obtained from a browser session. To get these:
    1. Visit https://chat.akash.network in your browser
    2. Complete any Cloudflare challenge if presented
    3. Export cookies using a browser extension (e.g., "Get cookies.txt LOCALLY")
       or manually create a JSON file with the format:
       [{"name": "cf_clearance", "value": "YOUR_TOKEN", ...}, {"name": "session_token", "value": "YOUR_TOKEN", ...}]
    4. Pass the path to this JSON file as the `cookie_file` parameter.

    Attributes:
        system_prompt (str): The system prompt to define the assistant's role.
        model (str): The model to use for generation.

    Examples:
        >>> from webscout.Provider.akashgpt import AkashGPT
        >>> ai = AkashGPT(cookie_file="/path/to/cookies.json")
        >>> response = ai.chat("What's the weather today?")
        >>> print(response)
    """
    required_auth = True
    AVAILABLE_MODELS = [
        "Qwen/Qwen3-30B-A3B",
        "DeepSeek-V3.1",
        "Meta-Llama-3-3-70B-Instruct",
        "DeepSeek-V3.2",
        "AkashGen"
    ]

    def __init__(
        self,
        cookie_file: Optional[str] = None,
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
        model: str = "Meta-Llama-3-3-70B-Instruct",
        temperature: float = 0.6,
        top_p: float = 0.9,
    ):
        """
        Initializes the AkashGPT API with given parameters.

        Args:
            cookie_file (str): Path to a JSON file containing cookies (cf_clearance and session_token).
            is_conversation (bool): Whether the provider is in conversation mode.
            max_tokens (int): Maximum number of tokens to sample.
            timeout (int): Timeout for API requests.
            intro (str): Introduction message for the conversation.
            filepath (str): Filepath for storing conversation history.
            update_file (bool): Whether to update the conversation history file.
            proxies (dict): Proxies for the API requests.
            history_offset (int): Offset for conversation history.
            act (str): Act for the conversation.
            system_prompt (str): The system prompt to define the assistant's role.
            model (str): The model to use for generation.
            temperature (float): Controls randomness in generation.
            top_p (float): Controls diversity via nucleus sampling.

        Raises:
            ValueError: If cookie_file is not provided or doesn't exist.
            ValueError: If cf_clearance or session_token cookies are missing from the file.
        """
        if not cookie_file:
            raise ValueError(
                "AkashGPT requires a cookie_file path. "
                "Visit https://chat.akash.network in your browser, complete any Cloudflare challenge, "
                "export cookies to a JSON file, and pass the file path."
            )

        if not path.isfile(cookie_file):
            raise ValueError(f"Cookie file not found: {cookie_file}")

        # Load cookies from the JSON file
        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies_list = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in cookie file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read cookie file: {e}")

        # Convert cookie list to dictionary
        self.cookies = {}
        if isinstance(cookies_list, list):
            for cookie in cookies_list:
                if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
                    self.cookies[cookie["name"]] = cookie["value"]
        elif isinstance(cookies_list, dict):
            self.cookies = cookies_list

        # Validate required cookies
        if "cf_clearance" not in self.cookies or "session_token" not in self.cookies:
            raise ValueError(
                "Cookie file must contain 'cf_clearance' and 'session_token' cookies. "
                "These can be obtained from DevTools -> Application -> Cookies after visiting "
                "https://chat.akash.network"
            )
        # Validate model choice
        if model not in self.AVAILABLE_MODELS:
            # Try case-insensitive match
            matched_model = next((m for m in self.AVAILABLE_MODELS if m.lower() == model.lower()), None)
            if matched_model:
                model = matched_model
            else:
                raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://chat.akash.network/api/chat/"
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

        self.agent = LitAgent()

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "origin": "https://chat.akash.network",
            "referer": "https://chat.akash.network/",
            "user-agent": self.agent.random()
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies)

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        act_prompt = (
            AwesomePrompts().get_act(cast(Union[str, int], act), default=None, case_insensitive=True)
            if act
            else intro
        )
        if act_prompt:
            self.conversation.intro = act_prompt
        self.conversation.history_offset = history_offset
        if proxies:
            self.session.proxies.update(cast(Any, proxies))

    @staticmethod
    def _akash_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from the AkashGPT stream format '0:"..."'."""
        if isinstance(chunk, str):
            match = re.search(r'0:"(.*?)"', chunk)
            if match:
                # Decode potential unicode escapes like \u00e9
                content = match.group(1).encode().decode('unicode_escape')
                return content.replace('\\\\', '\\').replace('\\"', '"') # Handle escaped backslashes and quotes
        return None

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
        Sends a prompt to the Akash Network API and returns the response.

        Args:
            prompt (str): The prompt to send to the API.
            stream (bool): Whether to stream the response.
            raw (bool): Whether to return the raw response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to generate the prompt conversationally.

        Returns:
            Dict[str, Any]: The API response.

        Examples:
            >>> ai = AkashGPT()
            >>> response = ai.ask("Tell me a joke!")
            >>> print(response)
            {'text': 'Why did the scarecrow win an award? Because he was outstanding in his field!'}
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        payload = {
            "id": str(uuid4()).replace("-", ""),  # Generate a unique request ID in the correct format
            "messages": [
                {
                    "role": "user",
                    "content": conversation_prompt,
                    "parts": [{"type": "text", "text": conversation_prompt}]
                }
            ],
            "model": self.model,
            "system": self.system_prompt,
            "temperature": str(self.temperature),
            "topP": str(self.top_p),
            "context": []
        }

        def for_stream():
            try:
                response = self.session.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )

                streaming_response = ""
                # Use sanitize_stream with the custom extractor
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None), # Pass byte iterator
                    intro_value=None, # No simple prefix
                    to_json=False,    # Content is not JSON, handled by extractor
                    content_extractor=self._akash_extractor, # Use the specific extractor
                    raw=raw
                )

                for content_chunk in processed_stream:
                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_response += content_chunk
                            yield dict(text=content_chunk)

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"An unexpected error occurred during streaming ({type(e).__name__}): {e}")

            self.last_response.update(dict(text=streaming_response)) # message_id is not easily accessible with this stream format
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            for _ in for_stream():
                pass
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
        Generates a response from the AkashGPT API.

        Args:
            prompt (str): The prompt to send to the API.
            stream (bool): Whether to stream the response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to generate the prompt conversationally.

        Returns:
            str: The API response.

        Examples:
            >>> ai = AkashGPT()
            >>> response = ai.chat("What's the weather today?")
            >>> print(response)
            'The weather today depends on your location. I don't have access to real-time weather data.'
        """

        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt,
                    False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")

if __name__ == "__main__":
    import os
    import sys

    # Get cookie file path from environment variable or command line argument
    cookie_file = os.environ.get("AKASH_COOKIES") or (sys.argv[1] if len(sys.argv) > 1 else None)

    if not cookie_file:
        print("Error: Cookie file path required.")
        print("Usage: python akashgpt.py <cookie_file.json>")
        print("   or: AKASH_COOKIES=/path/to/cookies.json python akashgpt.py")
        print("")
        print("To obtain cookies:")
        print("1. Visit https://chat.akash.network in your browser")
        print("2. Complete any Cloudflare challenge if presented")
        print("3. Export cookies using 'Get cookies.txt LOCALLY' extension")
        print("4. Save as cookies.json in the format:")
        print('   [{"name": "cf_clearance", "value": "..."}, {"name": "session_token", "value": "..."}]')
        sys.exit(1)

    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in AkashGPT.AVAILABLE_MODELS:
        try:
            test_ai = AkashGPT(cookie_file=cookie_file, model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word")

            if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
                response_text = "".join(list(response))
            else:
                response_text = str(response)

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Truncate response if too long
                display_text = response_text.strip()[:50] + "..." if len(response_text.strip()) > 50 else response_text.strip()
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"{model:<50} {'✗':<10} {str(e)}")
