import json
from typing import Any, Dict, Generator, Optional, Union, cast
from uuid import uuid4

import requests

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent


class ExaAI(Provider):
    """
    A class to interact with the o3minichat.exa.ai API.

    Attributes:
        system_prompt (str): The system prompt to define the assistant's role.

    Examples:
        >>> from webscout.Provider.ExaAI import ExaAI
        >>> ai = ExaAI()
        >>> response = ai.chat("What's the weather today?")
        >>> print(response)
        'The weather today depends on your location...'
    """
    AVAILABLE_MODELS = ["O3-Mini"]
    required_auth = False
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
        # system_prompt: str = "You are a helpful assistant.",
        model: str = "O3-Mini", # >>> THIS FLAG IS NOT USED <<<
    ):
        """
        Initializes the ExaAI API with given parameters.

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

        Examples:
            >>> ai = ExaAI(system_prompt="You are a friendly assistant.")
            >>> print(ai.system_prompt)
            'You are a friendly assistant.'
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://o3minichat.exa.ai/api/chat"
        self.timeout = timeout
        self.last_response = {}
        # self.system_prompt = system_prompt

        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()

        self.headers = {
            "authority": "o3minichat.exa.ai",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://o3minichat.exa.ai",
            "priority": "u=1, i",
            "referer": "https://o3minichat.exa.ai/",
            "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": self.agent.random()  # Use LitAgent to generate a random user agent
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = AwesomePrompts().get_act(cast(Union[str, int], act), default=self.conversation.intro, case_insensitive=True
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro
        if proxies:
            self.session.proxies.update(proxies)

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
        Sends a prompt to the o3minichat.exa.ai API and returns the response.

        Args:
            prompt (str): The prompt to send to the API.
            stream (bool): Whether to stream the response.
            raw (bool): Whether to return the raw response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to generate the prompt conversationally.

        Returns:
            Dict[str, Any]: The API response.

        Examples:
            >>> ai = ExaAI()
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

        # Generate a unique ID for the conversation
        conversation_id = uuid4().hex[:16]

        payload = {
            "id": conversation_id,
            "messages": [
                # {"role": "system", "content": self.system_prompt}, # system role not supported by this provider
                {"role": "user", "content": conversation_prompt}
            ]
        }

        def for_stream():
            response = self.session.post(self.api_endpoint, headers=self.headers, json=payload, stream=True, timeout=self.timeout)
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_response = ""
            # Use sanitize_stream with extract_regexes for Exa AI format
            processed_stream = sanitize_stream(
                data=response.iter_lines(decode_unicode=True),
                intro_value=None,
                to_json=False,
                extract_regexes=[r'0:"(.*?)"'],
                yield_raw_on_error=False,
                raw=raw
            )

            for content in processed_stream:
                if content:
                    if raw:
                        yield content
                    else:
                        if isinstance(content, str):
                            streaming_response += content
                            yield dict(text=content)

            self.last_response = {"text": streaming_response}
            self.conversation.update_chat_history(prompt, streaming_response)

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response if not raw else json.dumps(self.last_response)

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
        Generates a response from the ExaAI API.

        Args:
            prompt (str): The prompt to send to the API.
            stream (bool): Whether to stream the response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to generate the prompt conversationally.
            **kwargs: Additional parameters including raw.

        Returns:
            Union[str, Generator[str, None, None]]: The API response as a string or a generator of string chunks.

        Examples:
            >>> ai = ExaAI()
            >>> response = ai.chat("What's the weather today?")
            >>> print(response)
            'The weather today depends on your location...'
        """
        raw = kwargs.get("raw", False)
        def for_stream():
            for response in self.ask(
                prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield response
                else:
                    yield self.get_message(response)

        def for_non_stream():
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, result)
            return self.get_message(result)

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
        resp_dict = cast(Dict[str, Any], response)
        formatted_text = cast(str, resp_dict["text"]).replace('\\n', '\n').replace('\\n\\n', '\n\n')
        return formatted_text

if __name__ == "__main__":
    from rich import print
    ai = ExaAI(timeout=5000)
    response = ai.chat("Tell me about HelpingAI", stream=True)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
