import json
from typing import Any, Dict, Generator, Optional, Union, cast

import requests

from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers


# ------------------------------------------------------KOBOLDAI-----------------------------------------------------------
class KOBOLDAI(Provider):
    required_auth = False

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 1,
        top_p: float = 1,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
    ):
        """Instantiate TGPT

        Args:
            is_conversation (str, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 0.2.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 0.999.
            timeout (int, optional): Http requesting timeout. Defaults to 30
            intro (str, optional): Conversation introductory prompt. Defaults to `Conversation.intro`.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional) : Http reqiuest proxies (socks). Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.chat_endpoint = (
            "https://koboldai-koboldcpp-tiefighter.hf.space/api/extra/generate/stream"
        )
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
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
           "token" : "How may I assist you today?"
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
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        self.session.headers.update(self.headers)
        payload = {
            "prompt": conversation_prompt,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            message_load = ""
            final_resp = None
            for value in response.iter_lines(
                decode_unicode=True,
                delimiter="" if raw else "event: message\ndata:",
                chunk_size=self.stream_chunk_size,
            ):
                try:
                    resp = json.loads(value)
                    message_load += self.get_message(resp)
                    resp["token"] = message_load
                    self.last_response.update(resp)
                    final_resp = resp  # Always keep the latest
                except json.decoder.JSONDecodeError:
                    pass
            if final_resp:
                yield final_resp if not raw else json.dumps(final_resp)
                self.conversation.update_chat_history(prompt, self.get_message(self.last_response))

        def for_non_stream():
            # let's make use of stream
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
                    yield cast(str, response)
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
                return cast(str, result)
            else:
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
        return cast(Dict[str, Any], response).get("token", "")


if __name__ == "__main__":
    koboldai = KOBOLDAI(is_conversation=True, max_tokens=600, temperature=0.7)
    print(koboldai.chat("Explain quantum computing in simple terms", stream=False))
