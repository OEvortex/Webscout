import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi.requests import Session

# Import LitAgent for user agent generation
# Import base classes and utility structures
from webscout.Provider.OPENAI.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from webscout.Provider.OPENAI.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
)


class Completions(BaseCompletions):
    def __init__(self, client: "LLMChat"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 2048,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[dict] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        # In this case, we pass messages directly to the API
        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_streaming(
                request_id, created_time, model, messages, max_tokens, timeout, proxies
            )
        else:
            return self._create_non_streaming(
                request_id, created_time, model, messages, max_tokens, timeout, proxies
            )

    def _create_streaming(
        self,
        request_id: str,
        created_time: int,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        timeout: Optional[int],
        proxies: Optional[dict],
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            prompt_tokens = count_tokens(json.dumps(messages))
            completion_tokens = 0

            url = f"{self._client.api_endpoint}?model={model}"
            payload = {"messages": messages, "max_tokens": max_tokens or 2048, "stream": True}

            response = self._client.session.post(
                url,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                impersonate="chrome110",
            )
            response.raise_for_status()

            full_content = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            content = data.get("response", "")
                            if content:
                                full_content += content
                                completion_tokens += 1

                                delta = ChoiceDelta(content=content, role="assistant")
                                choice = Choice(index=0, delta=delta, finish_reason=None)
                                chunk = ChatCompletionChunk(
                                    id=request_id,
                                    choices=[choice],
                                    created=created_time,
                                    model=model,
                                )
                                yield chunk
                        except json.JSONDecodeError:
                            continue

            # Final chunk
            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            final_chunk = ChatCompletionChunk(
                id=request_id, choices=[choice], created=created_time, model=model
            )
            usage_obj = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=count_tokens(full_content),
                total_tokens=prompt_tokens + count_tokens(full_content),
            )
            final_chunk.usage = usage_obj.model_dump(exclude_none=True)
            yield final_chunk

        except Exception as e:
            raise IOError(f"LLMChat streaming request failed: {e}") from e

    def _create_non_streaming(
        self,
        request_id: str,
        created_time: int,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        timeout: Optional[int],
        proxies: Optional[dict],
    ) -> ChatCompletion:
        try:
            full_content = ""
            prompt_tokens = count_tokens(json.dumps(messages))

            for chunk in self._create_streaming(
                request_id, created_time, model, messages, max_tokens, timeout, proxies
            ):
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    full_content += chunk.choices[0].delta.content

            message = ChatCompletionMessage(role="assistant", content=full_content)
            choice = Choice(index=0, message=message, finish_reason="stop")
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=count_tokens(full_content),
                total_tokens=prompt_tokens + count_tokens(full_content),
            )

            return ChatCompletion(
                id=request_id, choices=[choice], created=created_time, model=model, usage=usage
            )
        except Exception as e:
            raise IOError(f"LLMChat request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "LLMChat"):
        self.completions = Completions(client)


class LLMChat(OpenAICompatibleProvider):
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

    def __init__(self, proxies: dict = {}, timeout: int = 30):
        self.session = Session()
        self.timeout = timeout
        self.api_endpoint = "https://llmchat.in/inference/stream"
        self.proxies = proxies
        if proxies:
            self.session.proxies.update(cast(Any, proxies))

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://llmchat.in",
            "Referer": "https://llmchat.in/",
        }
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    client = LLMChat()
    response = client.chat.completions.create(
        model="@cf/meta/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": "Say 'Hello' in one word"}],
        stream=True,
    )
    for chunk in response:
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                print(delta.content, end="", flush=True)
