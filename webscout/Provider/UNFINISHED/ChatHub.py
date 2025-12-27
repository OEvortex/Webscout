import json
from typing import Any, Dict, Generator, Optional, Union, cast

import requests

from webscout import exceptions
from webscout.AIbase import Provider
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


class ChatHub(Provider):
    """
    A class to interact with the ChatHub API.
    """

    AVAILABLE_MODELS = [
        'meta/llama3.1-8b',
        'mistral/mixtral-8x7b',
        'google/gemma-2',
        'perplexity/sonar-online',
    ]
    model_aliases = {  # Aliases for shorter model names
        "llama3.1-8b": 'meta/llama3.1-8b',
        "mixtral-8x7b": 'mistral/mixtral-8x7b',
        "gemma-2": 'google/gemma-2',
        "sonar-online": 'perplexity/sonar-online',
    }
    default_model = "sonar-online"


    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "sonar-online",
    ):
        """Initializes the ChatHub API client."""
        self.url = "https://app.chathub.gg"
        self.api_endpoint = "https://app.chathub.gg/api/v3/chat/completions"
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': self.url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'X-App-Id': 'web'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.last_response = {}

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
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

        #Resolve the model
        self.model = self.get_model(model)


    def get_model(self, model: str) -> str:
        """
        Resolves the model name using aliases or defaults.
        """

        if model in self.AVAILABLE_MODELS:
            return model
        elif model in self.model_aliases:
            return self.model_aliases[model]
        else:
            print(f"Model '{model}' not found. Using default model '{self.default_model}'.")
            return self.default_model # Use class-level default

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], Generator]:

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")


        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": conversation_prompt}],
            "tools": []
        }

        # Set the Referer header dynamically based on the resolved model
        self.headers['Referer'] = f"{self.url}/chat/{self.model}"


        def for_stream():
            try:
                with requests.post(self.api_endpoint, headers=self.headers, json=data, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()
                    streaming_text = ""

                    # Use sanitize_stream for processing
                    processed_stream = sanitize_stream(
                        data=response.iter_lines(decode_unicode=True),
                        intro_value="data:",
                        to_json=True,
                        content_extractor=lambda x: x.get('textDelta') if isinstance(x, dict) else None,
                        skip_markers=["[DONE]"],
                        yield_raw_on_error=False,
                        raw=raw
                    )

                    for content in processed_stream:
                        if content:
                            if raw:
                                yield content if isinstance(content, str) else json.dumps(content)
                            else:
                                streaming_text += content if isinstance(content, str) else ""
                                yield dict(text=content)

                    self.conversation.update_chat_history(prompt, streaming_text)
                    self.last_response = {"text": streaming_text}
            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request error: {e}")


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
        """Generate response `str`"""

        def for_stream():
            for response in self.ask(
                prompt, stream=True, raw=False, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            result = self.ask(
                prompt,
                stream=False,
                raw=False,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            return self.get_message(result)

        return for_stream() if stream else for_non_stream()



    def get_message(self, response: Union[Dict[str, Any], Generator[Any, None, None], str]) -> str:
        """Retrieves message only from response"""
        if isinstance(response, dict):
            resp_dict = cast(Dict[str, Any], response)
            return resp_dict.get("text", "")
        elif isinstance(response, str):
            return response
        else:
            # Generator case - shouldn't happen here
            return ""


if __name__ == "__main__":
    from rich import print
    bot = ChatHub()
    try:
        response = bot.chat("tell me about Abhay koul, HelpingAI", stream=True)
        for chunk in response:
            print(chunk, end="", flush=True)
    except Exception as e:
        print(f"An error occurred: {e}")
