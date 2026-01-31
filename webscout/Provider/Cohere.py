import json
from typing import Any, Dict, Generator, Optional, Union, cast

import requests

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


#-----------------------------------------------Cohere--------------------------------------------
class Cohere(Provider):
    required_auth = True
    def __init__(
        self,
        api_key: str,
        is_conversation: bool = True,
        max_tokens: int = 600,
        model: str = "command-r-plus",
        temperature: float = 0.7,
        system_prompt: str = "You are helpful AI",
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        top_k: int = -1,
        top_p: float = 0.999,
    ):
        """Initializes Cohere

        Args:
            api_key (str): Cohere API key.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            model (str, optional): Model to use for generating text. Defaults to "command-r-plus".
            temperature (float, optional): Diversity of the generated text. Higher values produce more diverse outputs.
                            Defaults to 0.7.
            system_prompt (str, optional): A system_prompt or context to set the style or tone of the generated text.
                            Defaults to "You are helpful AI".
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.chat_endpoint = "https://production.api.os.cohere.ai/coral/v1/chat"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
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
        """Chat with AI

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
           dict : {}
        ```json
        {
           "text" : "How may I assist you today?"
        }
        ```
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
        self.session.headers.update(self.headers)
        payload = {
            "message": conversation_prompt,
            "model": self.model,
            "temperature": self.temperature,
            "preamble": self.system_prompt,
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            # Use sanitize_stream with content_extractor for Cohere's JSON format
            processed_stream = sanitize_stream(
                data=response.iter_lines(decode_unicode=True, chunk_size=self.stream_chunk_size),
                intro_value=None,
                to_json=True,
                yield_raw_on_error=False,
                raw=raw
            )

            for chunk in processed_stream:
                if chunk:
                    if raw:
                        yield chunk if isinstance(chunk, str) else json.dumps(chunk)
                    else:
                        if isinstance(chunk, dict):
                            self.last_response.update(chunk)
                            yield chunk

            if self.last_response:
                try:
                    text = self.get_message(self.last_response)
                    self.conversation.update_chat_history(prompt, text)
                except (KeyError, TypeError):
                    pass

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
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            **kwargs: Additional parameters including raw.
        Returns:
            str: Response generated
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
        """Retrieves message only from response

        Args:
            response (Response): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        if not isinstance(response, dict):
            return str(response)
        resp_dict = cast(Dict[str, Any], response)
        return cast(str, resp_dict["result"]["chatStreamEndEvent"]["response"]["text"])
if __name__ == '__main__':
    from rich import print
    ai = Cohere(api_key="")
    response = ai.chat("tell me about india")
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
