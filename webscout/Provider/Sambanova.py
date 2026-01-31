import json
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent as Lit
from webscout.model_fetcher import BackgroundModelFetcher


class Sambanova(Provider):
    """
    A class to interact with the Sambanova API.
    """
    required_auth = True
    AVAILABLE_MODELS = [
        "DeepSeek-R1",
        "DeepSeek-V3",
        "Meta-Llama-3.3-70B-Instruct",
        "Meta-Llama-3.1-8B-Instruct",
        "Meta-Llama-3.1-70B-Instruct",
        "Meta-Llama-3.1-405B-Instruct",
        "Qwen2.5-72B-Instruct",
        "Qwen2.5-Coder-32B-Instruct"
    ]
    # Background model fetcher
    _model_fetcher = BackgroundModelFetcher()

    @classmethod
    def get_models(cls, api_key: Optional[str] = None):
        """Fetch available models from Sambanova API."""
        if not api_key:
            return cls.AVAILABLE_MODELS

        try:
            temp_session = Session()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

            response = temp_session.get(
                "https://api.sambanova.ai/v1/models",
                headers=headers,
                impersonate="chrome120"
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    new_models = [model['id'] for model in data['data'] if 'id' in model]
                    if new_models:
                        return new_models

        except Exception:
            pass
        return cls.AVAILABLE_MODELS

    def __init__(
        self,
        api_key: Optional[str] = None,
        is_conversation: bool = True,
        max_tokens: int = 4096,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "Meta-Llama-3.1-8B-Instruct",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """
        Initializes the Sambanova API with given parameters.
        """
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.timeout = timeout

        # Start background model fetch (non-blocking)
        self._model_fetcher.fetch_async(
            provider_name="Sambanova",
            fetch_func=lambda: self.get_models(api_key),
            fallback_models=self.AVAILABLE_MODELS,
            timeout=10,
        )

        # Initialize curl_cffi Session
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.last_response = {}

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": Lit().random(),
        }

        # Update curl_cffi session headers and proxies
        self.session = Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.system_prompt = system_prompt

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

        # Configure the API base URL
        self.base_url = "https://api.sambanova.ai/v1/chat/completions"

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        """Chat with AI using the Sambanova API."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {list(self.__available_optimizers)}"
                )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "max_tokens": self.max_tokens_to_sample,
            "stream": stream
        }

        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        def for_stream():
            try:
                # Use curl_cffi session post with impersonate
                response = self.session.post(
                    self.base_url,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome120"
                )
                response.raise_for_status()

                streaming_text = ""
                processed_stream = sanitize_stream(
                    data=response.iter_lines(),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=lambda chunk: chunk.get('choices', [{}])[0].get('delta') if isinstance(chunk, dict) else None,
                    yield_raw_on_error=False,
                    raw=raw
                )

                for delta in processed_stream:
                    if isinstance(delta, dict):
                        if 'content' in delta and delta['content'] is not None:
                            content = delta['content']
                            if raw:
                                yield content
                            else:
                                streaming_text += content
                                yield {"text": content}
                        elif 'tool_calls' in delta:
                            tool_calls = delta['tool_calls']
                            if raw:
                                yield json.dumps(tool_calls)
                            else:
                                yield {"tool_calls": tool_calls}

                self.last_response.update({"text": streaming_text})
                if streaming_text:
                    self.conversation.update_chat_history(prompt, streaming_text)

            except CurlError as e:
                raise exceptions.ProviderConnectionError(f"Request failed (CurlError): {e}") from e
            except Exception as e:
                raise exceptions.ProviderConnectionError(f"Request failed ({type(e).__name__}): {e}") from e

        def for_non_stream():
            try:
                payload["stream"] = False
                response = self.session.post(
                    self.base_url,
                    json=payload,
                    timeout=self.timeout,
                    impersonate="chrome120"
                )
                response.raise_for_status()
                resp_json = response.json()

                if 'choices' in resp_json and len(resp_json['choices']) > 0:
                    choice = resp_json['choices'][0]
                    message = choice.get('message', {})
                    content = message.get('content', '')
                    tool_calls = message.get('tool_calls')

                    result = {}
                    if content:
                        result["text"] = content
                    if tool_calls:
                        result["tool_calls"] = tool_calls

                    self.last_response = result
                    self.conversation.update_chat_history(prompt, content or "")

                    if raw:
                        return content if content else (json.dumps(tool_calls) if tool_calls else "")
                    return result
                else:
                    return {}

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Non-stream request failed: {e}") from e

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
        raw = kwargs.get("raw", False)
        tools = kwargs.get("tools")
        tool_choice = kwargs.get("tool_choice")

        def for_stream_chat():
             # ask() yields dicts or strings when streaming
             gen = self.ask(
                 prompt, stream=True, raw=raw,
                 optimizer=optimizer, conversationally=conversationally,
                 tools=tools, tool_choice=tool_choice
             )
             for response_dict in gen:
                 if raw:
                     yield cast(str, response_dict)
                 else:
                     yield self.get_message(cast(Response, response_dict))

        def for_non_stream_chat():
             # ask() returns dict or str when not streaming
             response_data = self.ask(
                 prompt,
                 stream=False,
                 raw=raw,
                 optimizer=optimizer,
                 conversationally=conversationally,
                 tools=tools,
                 tool_choice=tool_choice
             )
             if raw:
                 return cast(str, response_data)
             return self.get_message(response_data)

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        """
        Retrieves a clean message from the provided response.

        Args:
            response: The raw response data.

        Returns:
            str: The extracted message.
        """
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            resp_dict = cast(Dict[str, Any], response)
            if "text" in resp_dict:
                return cast(str, resp_dict["text"])
            elif "tool_calls" in resp_dict:
                return json.dumps(resp_dict["tool_calls"])
        return str(response)

if __name__ == "__main__":
    # Ensure curl_cffi is installed
    from rich import print
    ai = Sambanova(api_key='')
    response = ai.chat(input(">>> "), stream=True)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
