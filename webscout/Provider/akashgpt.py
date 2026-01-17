import re
import time
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

    Attributes:
        system_prompt (str): The system prompt to define the assistant's role.
        model (str): The model to use for generation.

    Examples:
        >>> from webscout.Provider.akashgpt import AkashGPT
        >>> ai = AkashGPT()
        >>> response = ai.chat("What's the weather today?")
        >>> print(response)
        'The weather today depends on your location. I don't have access to real-time weather data.'
    """
    required_auth = True
    AVAILABLE_MODELS = [
        "Qwen/Qwen3-30B-A3B",
        "DeepSeek-V3.1",
        "Meta-Llama-3-3-70B-Instruct",
    ]

    def __init__(
        self,
        api_key: str,
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
        model: str = "meta-llama-3-3-70b-instruct",
        temperature: float = 0.6,
        top_p: float = 0.9,
    ):
        """
        Initializes the AkashGPT API with given parameters.

        Args:
            api_key (str): Session token (used as API key here) for authentication. If None, auto-generates one.
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
        """
        # Validate model choice
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://chat.akash.network/api/chat"
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

        # Generate session token if not provided
        if not api_key:
            self.api_key = str(uuid4()).replace("-", "") + str(int(time.time()))
        else:
            self.api_key = api_key

        self.agent = LitAgent()

        self.headers = {
            "authority": "chat.akash.network",
            "method": "POST",
            "path": "/api/chat",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://chat.akash.network",
            "priority": "u=1, i",
            "referer": "https://chat.akash.network/",
            "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": self.agent.random()
        }

        # Set cookies with the session token
        self.session.cookies.set("session_token", self.api_key, domain="chat.akash.network")

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        act_prompt = (
            AwesomePrompts().get_act(cast(Union[str, int], act), default=None, case_insensitive=True
            )
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
                {"role": "user", "content": conversation_prompt}
            ],
            "model": self.model,
            "system": self.system_prompt,
            "temperature": self.temperature,
            "topP": self.top_p,
            "context": []
        }

        def for_stream():
            try:
                response = self.session.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=self.timeout
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
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in AkashGPT.AVAILABLE_MODELS:
        try:
            test_ai = AkashGPT(model=model, timeout=60, api_key="5ef9b0782df982fab720810f6ee72a9af01ebadbd9eb05adae0ecc8711ec79c5; _ga_LFRGN2J2RV=GS2.1.s1763554272$o4$g1$t1763554284$j48$l0$h0") # Example key
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
