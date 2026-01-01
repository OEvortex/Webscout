from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError  # Import CurlError

# Replace requests with curl_cffi
from curl_cffi.requests import Session  # Import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers  # Import sanitize_stream
from webscout.litagent import LitAgent


class Netwrck(Provider):
    """
    A class to interact with the Netwrck.com API. Supports streaming.
    """
    greeting = """Hello! I'm a helpful assistant. How can I help you today?"""
    required_auth = False
    AVAILABLE_MODELS = [
        "thedrummer/valkyrie-49b-v1",
        "thedrummer/skyfall-36b-v2",
        "sao10k/l3-euryale-70b",
        "deepseek/deepseek-chat",
        "deepseek/deepseek-r1",
        "gryphe/mythomax-l2-13b",
        "nvidia/llama-3.1-nemotron-70b-instruct",
    ]

    def __init__(
        self,
        model: str = "deepseek/deepseek-r1",
        is_conversation: bool = True,
        max_tokens: int = 4096, # Note: max_tokens is not used by this API
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = False,
        proxies: Optional[dict] = None,
        history_offset: int = 0,
        act: Optional[str] = None,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7, # Note: temperature is not used by this API
        top_p: float = 0.8 # Note: top_p is not used by this API
    ):
        """Initializes the Netwrck API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.model = model
        self.model_name = model
        self.system_prompt = system_prompt
        # Initialize curl_cffi Session
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response: Dict[str, Any] = {}
        self.temperature = temperature
        self.top_p = top_p

        self.agent = LitAgent() # Keep for potential future use or other headers
        self.headers = {
            'authority': 'netwrck.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://netwrck.com',
            'referer': 'https://netwrck.com/',
            'user-agent': self.agent.random()
            # Add sec-ch-ua headers if needed for impersonation consistency
        }

        # Update curl_cffi session headers and proxies
        self.session.headers.update(self.headers)
        self.proxies = proxies or {}
        if self.proxies:
            self.session.proxies.update(self.proxies)

        self.conversation = Conversation(is_conversation, max_tokens, filepath, update_file)
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = AwesomePrompts().get_act(cast(Union[str, int], act), default=self.conversation.intro, case_insensitive=True) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro
        self.__available_optimizers = (
            method for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

    @staticmethod
    def _netwrck_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Removes surrounding quotes and handles potential escapes."""
        if isinstance(chunk, str):
            text = chunk.strip('"')
            # Handle potential unicode escapes if they appear
            # text = text.encode().decode('unicode_escape') # Uncomment if needed
            return text
        return None
    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False, # Keep raw param for interface consistency
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """Sends a prompt to the Netwrck API and returns the response."""
        if optimizer and optimizer not in self.__available_optimizers:
            raise exceptions.FailedToGenerateResponseError(f"Optimizer is not one of {self.__available_optimizers}")

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            conversation_prompt = getattr(Optimizers, optimizer)(
                conversation_prompt if conversationally else prompt
            )

        payload = {
            "query": prompt,
            "context": self.system_prompt,
            "examples": [],
            "model_name": self.model_name,
            "greeting": self.greeting
        }

        def for_stream():
            try:
                response = self.session.post(
                    "https://netwrck.com/api/chatpred_or",
                    json=payload,
                    timeout=self.timeout,
                    stream=True,
                    impersonate="chrome110"
                )
                response.raise_for_status()
                buffer = ""
                chunk_size = 32
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    text = chunk.decode(errors="ignore")
                    buffer += text
                    while len(buffer) >= chunk_size:
                        out = buffer[:chunk_size]
                        buffer = buffer[chunk_size:]
                        if out.strip():
                            if raw:
                                yield out
                            else:
                                yield {"text": out}
                if buffer.strip():
                    if raw:
                        yield buffer
                    else:
                        yield {"text": buffer}
                self.last_response = {"text": buffer}
                self.conversation.update_chat_history(payload["query"], buffer)
            except CurlError as e:
                raise exceptions.APIConnectionError(f"Network error (CurlError): {str(e)}") from e
            except Exception as e:
                err_text = ""
                if hasattr(e, 'response'):
                    response_obj = getattr(e, 'response')
                    if hasattr(response_obj, 'text'):
                        err_text = getattr(response_obj, 'text')
                raise exceptions.APIConnectionError(f"Unexpected error ({type(e).__name__}): {str(e)} - {err_text}") from e

        def for_non_stream():
            try:
                response = self.session.post(
                    "https://netwrck.com/api/chatpred_or",
                    json=payload,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()
                response_text_raw = response.text
                self.last_response = {"text": response_text_raw}
                self.conversation.update_chat_history(prompt, response_text_raw)
                return response_text_raw if raw else self.last_response
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Network error (CurlError): {str(e)}") from e
            except Exception as e:
                err_text = ""
                if hasattr(e, 'response'):
                    response_obj = getattr(e, 'response')
                    if hasattr(response_obj, 'text'):
                        err_text = getattr(response_obj, 'text')
                raise exceptions.FailedToGenerateResponseError(f"Unexpected error ({type(e).__name__}): {str(e)} - {err_text}") from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Generates a response from the Netwrck API."""
        raw = kwargs.get("raw", False)
        def for_stream_chat():
            # ask() yields dicts or strings when streaming
            gen = self.ask(
                prompt,
                stream=True,
                raw=raw, # Ensure ask yields dicts for get_message if not raw
                optimizer=optimizer,
                conversationally=conversationally
            )
            for response_dict in gen:
                if raw:
                    yield cast(str, response_dict)
                else:
                    yield self.get_message(cast(Dict[str, Any], response_dict)) # get_message expects dict

        def for_non_stream_chat():
            # ask() returns dict or str when not streaming
            response_data = self.ask(
                prompt,
                stream=False,
                raw=raw, # Ensure ask returns dict for get_message if not raw
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, response_data)
            else:
                return self.get_message(cast(Dict[str, Any], response_data)) # get_message expects dict

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        """Retrieves message only from response"""
        if not isinstance(response, dict):
            return str(response)
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')

if __name__ == "__main__":
    # Ensure curl_cffi is installed
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    # Test all available models
    working = 0
    total = len(Netwrck.AVAILABLE_MODELS)

    for model in Netwrck.AVAILABLE_MODELS:
        try:
            test_ai = Netwrck(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
                for chunk in response:
                    response_text += chunk
                    print(f"\r{model:<50} {'Testing...':<10}", end="", flush=True)
            else:
                response_text = str(response)

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Truncate response if too long
                display_text = response_text.strip()[:50] + "..." if len(response_text.strip()) > 50 else response_text.strip()
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")
