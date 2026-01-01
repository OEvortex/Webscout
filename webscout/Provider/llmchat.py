from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


class LLMChat(Provider):
    """
    A class to interact with the LLMChat API
    """

    required_auth = False
    AVAILABLE_MODELS = [
        "@cf/aisingapore/gemma-sea-lion-v4-27b-it",
        "@cf/deepseek-ai/deepseek-math-7b-instruct",
        "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
        "@cf/defog/sqlcoder-7b-2",
        "@cf/fblgit/una-cybertron-7b-v2-bf16",
        "@cf/google/gemma-2b-it-lora",
        "@cf/google/gemma-3-12b-it",
        "@cf/ibm-granite/granite-4.0-h-micro",
        "@cf/meta-llama/llama-2-7b-chat-hf-lora",
        "@cf/meta/llama-2-7b-chat-fp16",
        "@cf/meta/llama-2-7b-chat-int8",
        "@cf/meta/llama-3-8b-instruct",
        "@cf/meta/llama-3-8b-instruct-awq",
        "@cf/meta/llama-3.1-70b-instruct",
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/meta/llama-3.2-1b-instruct",
        "@cf/meta/llama-3.2-3b-instruct",
        "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        "@cf/meta/llama-4-scout-17b-16e-instruct",
        "@cf/meta/llama/llama-2-7b-chat-hf-lora",
        "@cf/meta/meta-llama-3-8b-instruct",
        "@cf/microsoft/phi-2",
        "@cf/mistral/mistral-7b-instruct-v0.1-vllm",
        "@cf/mistral/mistral-7b-instruct-v0.2-lora",
        "@cf/mistralai/mistral-small-3.1-24b-instruct",
        "@cf/openchat/openchat-3.5-0106",
        "@cf/qwen/qwen1.5-0.5b-chat",
        "@cf/qwen/qwen1.5-1.8b-chat",
        "@cf/qwen/qwen1.5-14b-chat-awq",
        "@cf/qwen/qwen1.5-7b-chat-awq",
        "@cf/qwen/qwen2.5-coder-32b-instruct",
        "@cf/qwen/qwen3-30b-a3b-fp8",
        "@cf/qwen/qwq-32b",
        "@cf/tiiuae/falcon-7b-instruct",
        "@cf/tinyllama/tinyllama-1.1b-chat-v1.0",
        "@hf/google/gemma-7b-it",
        "@hf/meta-llama/meta-llama-3-8b-instruct",
        "@hf/mistral/mistral-7b-instruct-v0.2",
        "@hf/nexusflow/starling-lm-7b-beta",
        "@hf/thebloke/deepseek-coder-6.7b-base-awq",
        "@hf/thebloke/deepseek-coder-6.7b-instruct-awq",
        "@hf/thebloke/llama-2-13b-chat-awq",
        "@hf/thebloke/llamaguard-7b-awq",
        "@hf/thebloke/mistral-7b-instruct-v0.1-awq",
        "@hf/thebloke/neural-chat-7b-v3-1-awq",
        "@hf/thebloke/openhermes-2.5-mistral-7b-awq",
        "@hf/thebloke/zephyr-7b-beta-awq",
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2048,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "@cf/meta/llama-3.1-70b-instruct",
        system_prompt: str = "You are a helpful assistant.",
    ):
        """
        Initializes the LLMChat API with given parameters.
        """

        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        # Initialize curl_cffi Session
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://llmchat.in/inference/stream"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://llmchat.in",
            "Referer": "https://llmchat.in/",
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        act_prompt = (
            AwesomePrompts().get_act(
                cast(Union[str, int], act), default=None, case_insensitive=True
            )
            if act
            else intro
        )
        if act_prompt:
            self.conversation.intro = act_prompt
        self.conversation.history_offset = history_offset

        # Update curl_cffi session headers and proxies
        self.session = Session(impersonate="chrome110")
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.system_prompt = system_prompt

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], Generator[Any, None, None], str]:
        """Chat with LLMChat with logging capabilities and raw output support using sanitize_stream."""

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        url = f"{self.api_endpoint}?model={self.model}"
        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "max_tokens": self.max_tokens_to_sample,
            "stream": True,
        }

        def for_stream():
            full_response = ""
            try:
                response = self.session.post(
                    url, json=payload, stream=True, timeout=self.timeout, impersonate="chrome110"
                )
                response.raise_for_status()

                # Use sanitize_stream to process SSE lines
                processed_stream = sanitize_stream(
                    data=response.iter_lines(),
                    intro_value="data: ",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=lambda chunk: chunk.get("response")
                    if isinstance(chunk, dict)
                    else None,
                    yield_raw_on_error=False,
                    raw=raw,
                )
                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
                        full_response += content_chunk
                        if raw:
                            yield content_chunk
                        else:
                            yield dict(text=content_chunk)
                self.last_response = dict(text=full_response)
                self.conversation.update_chat_history(prompt, full_response)
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                err_text = ""
                if hasattr(e, "response"):
                    response_obj = getattr(e, "response")
                    if hasattr(response_obj, "text"):
                        err_text = getattr(response_obj, "text")
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed ({type(e).__name__}): {e} - {err_text}"
                ) from e

        def for_non_stream():
            full_response = ""
            try:
                for content_chunk in for_stream():
                    if raw and isinstance(content_chunk, str):
                        full_response += content_chunk
                    elif isinstance(content_chunk, dict) and "text" in content_chunk:
                        full_response += content_chunk["text"]
            except Exception as e:
                if not full_response:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to get non-stream response: {str(e)}"
                    ) from e
            return full_response if raw else self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response with logging capabilities and raw output support"""

        def for_stream_chat():
            gen = self.ask(
                prompt, stream=True, raw=raw, optimizer=optimizer, conversationally=conversationally
            )
            for response in gen:
                if raw:
                    yield response
                else:
                    yield self.get_message(response)

        def for_non_stream_chat():
            response_data = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return (
                    response_data
                    if isinstance(response_data, str)
                    else self.get_message(response_data)
                )
            else:
                return self.get_message(response_data)

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        """Retrieves message from response with validation"""
        if not isinstance(response, dict):
            return str(response)
        response_dict = cast(Dict[str, Any], response)
        return response_dict.get("text", "")


if __name__ == "__main__":
    # Ensure curl_cffi is installed
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    # Test all available models
    working = 0
    total = len(LLMChat.AVAILABLE_MODELS)

    for model in LLMChat.AVAILABLE_MODELS:
        try:
            test_ai = LLMChat(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            for chunk in response:
                response_text += chunk
                print(f"\r{model:<50} {'Testing...':<10}", end="", flush=True)

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Truncate response if too long
                display_text = (
                    response_text.strip()[:50] + "..."
                    if len(response_text.strip()) > 50
                    else response_text.strip()
                )
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")
    # ai = LLMChat(model="@cf/meta/llama-3.1-70b-instruct")
    # response = ai.chat("Say 'Hello' in one word", stream=True, raw=False)
    # for chunk in response:
    #     print(chunk, end="", flush=True)
