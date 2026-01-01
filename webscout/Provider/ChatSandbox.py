import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


class ChatSandbox(Provider):
    """
    Sends a chat message to the specified model via the chatsandbox API.

    This provider allows you to interact with various AI models through the chatsandbox.com
    interface, supporting different models/models like OpenAI, DeepSeek, Llama, etc.

    Attributes:
        model (str): The model to chat with (e.g., "openai", "deepseek", "llama").

    Examples:
        >>> from webscout.Provider.ChatSandbox import ChatSandbox
        >>> ai = ChatSandbox(model="openai")
        >>> response = ai.chat("Hello, how are you?")
        >>> print(response)
        'I'm doing well, thank you for asking! How can I assist you today?'
    """
    required_auth = False
    AVAILABLE_MODELS = [
        "openai",
        "openai-gpt-4o",
        "openai-o1-mini",
        "deepseek",
        "deepseek-r1",
        "deepseek-r1-full",
        "gemini",
        "gemini-thinking",
        "mistral",
        "mistral-large",
        "gemma-3",
        "llama"
    ]


    def __init__(
        self,
        model: str = "openai",
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
    ):
        """
        Initializes the ChatSandbox API with given parameters.

        Args:
            model (str): The model to chat with (e.g., "openai", "deepseek", "llama").
            is_conversation (bool): Whether the provider is in conversation mode.
            max_tokens (int): Maximum number of tokens to sample.
            timeout (int): Timeout for API requests.
            intro (str): Introduction message for the conversation.
            filepath (str): Filepath for storing conversation history.
            update_file (bool): Whether to update the conversation history file.
            proxies (dict): Proxies for the API requests.
            history_offset (int): Offset for conversation history.
            act (str): Act for the conversation.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        # Initialize curl_cffi Session with impersonation
        self.session = Session(impersonate="chrome120")
        self.model = model
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://chatsandbox.com/api/chat"
        self.timeout = timeout
        self.last_response = {}

        # Set up headers
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://chatsandbox.com',
            'referer': f'https://chatsandbox.com/chat/{self.model}',
        }

        # Update curl_cffi session headers and proxies
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

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
            self.conversation.intro = AwesomePrompts().get_act(cast(Union[str, int], act), default=self.conversation.intro, case_insensitive=True
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro

    @staticmethod
    def _chatsandbox_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from the chatsandbox stream format."""
        if isinstance(chunk, str):
            try:
                data = json.loads(chunk)
                if isinstance(data, dict):
                    if "reasoning_content" in data and data["reasoning_content"]:
                        return data["reasoning_content"]
                    if "content" in data and data["content"]:
                        return data["content"]
                return chunk
            except json.JSONDecodeError:
                return chunk
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
        Sends a prompt to the ChatSandbox API and returns the response.

        Args:
            prompt (str): The prompt to send to the API.
            stream (bool): Whether to stream the response.
            raw (bool): Whether to return the raw response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to generate the prompt conversationally.

        Returns:
            Union[Dict[str, Any], Generator]: The API response.
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

        # Prepare the payload
        payload = {
            "messages": [conversation_prompt],
            "character": self.model
        }

        def for_stream():
            try:
                response = self.session.post(
                    self.api_endpoint,
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
                    data=response.iter_content(chunk_size=None),  # Pass byte iterator
                    intro_value=None,
                    to_json=False,
                    content_extractor=self._chatsandbox_extractor,
                    raw=raw,
                )

                for content_chunk in processed_stream:
                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_response += content_chunk
                            yield dict(text=content_chunk)

                self.last_response.update(dict(text=streaming_response))
                self.conversation.update_chat_history(
                    prompt, self.get_message(self.last_response)
                )
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {e}")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"An unexpected error occurred ({type(e).__name__}): {e}")

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
        Generates a response from the ChatSandbox API.

        Args:
            prompt (str): The prompt to send to the API.
            stream (bool): Whether to stream the response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to generate the prompt conversationally.
            **kwargs: Additional parameters including raw.

        Returns:
            str: The API response.
        """
        raw = kwargs.get("raw", False)
        def for_stream():
            for response in self.ask(
                prompt,
                stream=True,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            ):
                if raw:
                    yield response
                else:
                    yield self.get_message(response)

        if stream:
            return for_stream()
        else:
            result = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, result)
            else:
                return self.get_message(result)

    def get_message(self, response: Response) -> str:
        """
        Extract the message from the API response.

        Args:
            response (Response): The API response.

        Returns:
            str: The extracted message.
        """
        if not isinstance(response, dict):
            return str(response)

        raw_text = cast(Dict[str, Any], response).get("text", "")

        # Try to parse as JSON
        try:
            data = json.loads(raw_text)
            if isinstance(data, dict):
                if "reasoning_content" in data and data["reasoning_content"]:
                    return data["reasoning_content"]
                elif "content" in data and data["content"]:
                    return data["content"]
                elif "message" in data:
                    return data["message"]
                elif "response" in data:
                    return data["response"]
                elif "text" in data:
                    return data["text"]
                return json.dumps(data, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

        return raw_text.strip()

# --- Example Usage ---
if __name__ == "__main__":
    from rich import print
    print("-" * 80)
    print(f"{ 'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in ChatSandbox.AVAILABLE_MODELS:
        try:
            test_ai = ChatSandbox(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word")

            if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
                response_text = "".join(list(response))
            else:
                response_text = str(response)

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                display_text = response_text.strip()[:50].replace('\n', ' ') + ("..." if len(response_text.strip()) > 50 else "")
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"{model:<50} {'✗':<10} {str(e)}")
