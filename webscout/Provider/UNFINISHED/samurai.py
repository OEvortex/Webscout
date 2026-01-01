import json
from typing import Any, Dict, Generator, Iterable, Optional, Union, cast

from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


class samurai(Provider):
    """
    A class to interact with a custom API endpoint.
    """
    AVAILABLE_MODELS = [
        "openai/gpt-4.1",
        "openai/gpt-4o-search-preview",
        "openai/gpt-4o-mini-search-preview",
        "openai/gpt-4.1-nano",
        "openai/chatgpt-4o-latest",
        "openai/gpt-4.1-mini",
        "gpt-4o",
        "o3-mini",
        "Claude-sonnet-3.7",
        "uncensored-r1",
        "anthropic/claude-3.5-sonnet",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-flash-2.0",
        "gemini-1.5-flash",
        "llama-3.1-405b",
        "Meta-Llama-3.1-405B-Instruct-Turbo",
        "Meta-Llama-3.3-70B-Instruct-Turbo",
        "chutesai/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "chutesai/Llama-4-Scout-17B-16E-Instruct",
        "Qwen-QwQ-32B-Preview",
        "Qwen/Qwen3-235B-A22B-fp8-tput",
        "deepseek-r1",
        "deepseek-v3",
        "deepseek-ai/DeepSeek-V3-0324",
        "dbrx-instruct",
        "x-ai/grok-3-",
        "perplexity-ai/r1-1776"
    ]
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
        model: str = "openai/gpt-4.1",
        system_prompt: str = "You are a helpful assistant."
    ):
        """Initializes the Custom API client."""
        self.url = "https://newapi-9qln.onrender.com/v1/chat/completions"
        self.headers = {
            "Authorization": "Bearer Samurai-AP1-Fr33",
            "Content-Type": "application/json"
        }
        self.session = Session()
        self.session.headers.update(self.headers)
        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model

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

    @staticmethod
    def _extractor(chunk: dict) -> Optional[str]:
        """Extracts content from stream JSON objects."""
        return chunk.get("choices", [{}])[0].get("delta", {}).get("content")

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

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()

                # Convert to list - using type: ignore for compatibility with sanitize_stream
                lines_list = list(response.iter_lines())
                processed_stream = sanitize_stream(  # type: ignore[no-overload-impl]
                    data=lines_list,
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=self._extractor,
                    yield_raw_on_error=False
                )

                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
                        streaming_text += content_chunk
                        resp = dict(text=content_chunk)
                        yield resp if not raw else content_chunk

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}") from e
            finally:
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            try:
                response = self.session.post(
                self.url,
                data=json.dumps(payload),
                timeout=self.timeout,
                impersonate="chrome110"
            )
                response.raise_for_status()
                json_response = response.json()
                content = json_response.get("choices", [{}])[0].get("message", {}).get("content", "")

                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return self.last_response if not raw else content

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}") from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        def for_stream_chat():
            gen = self.ask(prompt, stream=True, raw=False, optimizer=optimizer, conversationally=conversationally)
            for response_item in gen:
                yield self.get_message(response_item)

        def for_non_stream_chat():
            response_data = self.ask(prompt, stream=False, raw=False, optimizer=optimizer, conversationally=conversationally)
            return self.get_message(response_data)

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            return dict(response)["text"]
        return str(response)

if __name__ == "__main__":
    # Ensure curl_cffi is installed
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in samurai.AVAILABLE_MODELS:
        try:
            test_ai = samurai(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            for chunk in response:
                response_text += chunk

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Clean and truncate response
                clean_text = response_text.strip().encode('utf-8', errors='ignore').decode('utf-8')
                display_text = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")
