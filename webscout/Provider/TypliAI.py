import random
import string
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response

#
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent


def generate_random_id(length=16):
    """Generates a random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for i in range(length))


class TypliAI(Provider):
    """
    A class to interact with the Typli.ai API.

    Attributes:
        system_prompt (str): The system prompt to define the assistant's role.

    Examples:
        >>> from webscout.Provider import TypliAI
        >>> ai = TypliAI()
        >>> response = ai.chat("What's the weather today?")
        >>> print(response)
        'I don't have access to real-time weather information...'
    """

    required_auth = False
    AVAILABLE_MODELS = [
        "openai/gpt-4.1-mini",
        "openai/gpt-4.1",
        "openai/gpt-5-mini",
        "openai/gpt-5.2",
        "openai/gpt-5.2-pro",
        "google/gemini-2.5-flash",
        "anthropic/claude-haiku-4-5",
        "xai/grok-4-fast-reasoning",
        "xai/grok-4-fast",
    ]

    def __init__(
        self,
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
        model: str = "openai/gpt-4.1-mini",
    ):
        """
        Initializes the TypliAI API with given parameters.

        Args:
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
        """
        # Initialize curl_cffi Session instead of requests.Session
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://typli.ai/api/generators/chat"
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.model = model

        # Initialize LitAgent for user agent generation if available

        self.agent = LitAgent()
        user_agent = self.agent.random()  # Let impersonate handle the user-agent
        self.headers = {
            "accept": "/",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://typli.ai",
            "priority": "u=1, i",
            "referer": "https://typli.ai/free-no-sign-up-chatgpt",
            "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": user_agent,
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        # Update curl_cffi session headers and proxies
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

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

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], Generator[Union[str, Dict[str, Any]], None, None]]:
        """Sends a prompt to the Typli.ai API and returns the response.

        Args:
            prompt (str): The prompt to send to the API.
            stream (bool): Whether to stream the response.
            raw (bool): Whether to return the raw response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to generate the prompt conversationally.

        Returns:
            Union[Dict[str, Any], Generator[Union[str, Dict[str, Any]], None, None]]: The API response.
        """

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        payload = {
            "slug": "free-no-sign-up-chatgpt",
            "modelId": self.model,
            "id": generate_random_id(),
            "messages": [
                {
                    "id": generate_random_id(),
                    "role": "user",
                    "parts": [{"type": "text", "text": conversation_prompt}],
                }
            ],
            "trigger": "submit-message",
        }

        def for_stream():
            try:
                # Use curl_cffi session post with updated impersonate and http_version
                response = self.session.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome120",  # Switch to a more common profile
                    # http_version=CurlHttpVersion.V1_1 # Usually not needed
                )
                if not response.ok:
                    error_msg = f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    raise exceptions.FailedToGenerateResponseError(error_msg)

                streaming_response = ""
                # Use sanitize_stream with content_extractor for the new JSON format
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data: ",
                    to_json=True,
                    content_extractor=lambda x: x.get("delta")
                    if isinstance(x, dict) and x.get("type") == "text-delta"
                    else None,
                    skip_markers=["[DONE]"],
                    raw=raw,
                )

                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
                        streaming_response += content_chunk
                        yield content_chunk if raw else dict(text=content_chunk)

                self.last_response.update(dict(text=streaming_response))

                self.conversation.update_chat_history(prompt, self.get_message(self.last_response))

            except CurlError as e:  # Catch CurlError
                error_msg = f"Request failed (CurlError): {e}"
                raise exceptions.FailedToGenerateResponseError(error_msg)

            except Exception as e:  # Catch other potential exceptions
                # Include the original exception type in the message for clarity
                error_msg = f"An unexpected error occurred ({type(e).__name__}): {e}"
                raise exceptions.FailedToGenerateResponseError(error_msg)

        def for_non_stream():
            # This function implicitly uses the updated for_stream
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
        Generates a response from the Typli.ai API.

        Args:
            prompt (str): The prompt to send to the API.
            stream (bool): Whether to stream the response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to generate the prompt conversationally.
            **kwargs: Additional parameters including raw.

        Returns:
            Union[str, Generator[str, None, None]]: The API response.
        """
        raw = kwargs.get("raw", False)

        def for_stream():
            for response in self.ask(
                prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield cast(Dict[str, Any], response)
                else:
                    yield self.get_message(cast(Response, response))

        def for_non_stream():
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(Dict[str, Any], result)
            else:
                return self.get_message(cast(Response, result))

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        """
        Extracts the message from the API response.

        Args:
            response (Response): The API response.

        Returns:
            str: The message content.
        """
        if not isinstance(response, dict):
            return str(response)
        response_dict = cast(Dict[str, Any], response)
        return response_dict.get("text", "").replace("\\n", "\n").replace("\\n\\n", "\n\n")


if __name__ == "__main__":
    from rich import print

    try:
        ai = TypliAI(timeout=60)
        response = ai.chat("Write a short poem about AI", stream=True, raw=False)
        for chunk in response:
            print(chunk, end="", flush=True)
    except Exception as e:
        print(f"An error occurred: {e}")
