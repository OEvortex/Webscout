import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError, requests

from llm4free.litagent import LitAgent
from llm4free.llm.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from llm4free.llm.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
)

BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"


class Completions(BaseCompletions):
    def __init__(self, client: "FreeAI"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        model = self._client.convert_model_name(model)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, payload, timeout, proxies)
        else:
            return self._create_non_stream(
                request_id, created_time, model, payload, timeout, proxies
            )

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            response = self._client.session.post(
                self._client.url,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=cast(Any, proxies or getattr(self._client, "proxies", None)),
                impersonate="chrome110",
            )
            response.raise_for_status()

            for raw_line in response.iter_lines():
                if raw_line is None:
                    continue
                if isinstance(raw_line, bytes):
                    raw_line = raw_line.decode("utf-8", errors="replace")
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                payload_str = line[5:].strip()
                if payload_str == "[DONE]":
                    break
                try:
                    import json

                    evt = json.loads(payload_str)
                except json.JSONDecodeError:
                    continue
                choices = evt.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                text = delta.get("content")
                if not text:
                    continue
                delta_obj = ChoiceDelta(content=text)
                choice = Choice(index=0, delta=delta_obj, finish_reason=None)
                chunk = ChatCompletionChunk(
                    id=request_id,
                    choices=[choice],
                    created=created_time,
                    model=model,
                )
                yield chunk

            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            yield ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
            )
        except CurlError as e:
            raise IOError(f"FreeAI request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        try:
            response = self._client.session.post(
                self._client.url,
                json=payload,
                timeout=timeout or self._client.timeout,
                proxies=cast(Any, proxies or getattr(self._client, "proxies", None)),
                impersonate="chrome110",
            )
            response.raise_for_status()
            data = response.json()
            full_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            prompt_tokens = count_tokens(str(payload.get("messages", "")))
            completion_tokens = count_tokens(full_text)
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )
            message = ChatCompletionMessage(role="assistant", content=full_text)
            choice = Choice(index=0, message=message, finish_reason="stop")
            return ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )
        except Exception as e:
            raise IOError(f"FreeAI request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "FreeAI"):
        self.completions = Completions(client)


class FreeAI(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = [
        "qwen7b",
        "qwen3-8b",
        "deepseek-r1",
        "deepseek-r1-7b",
        "mistral",
        "qwen/qwen3-8b",
        "deepseek/deepseek-chat-v3-0324",
        "deepseek/deepseek-r1",
        "openai/gpt-4o-mini",
        "openai/gpt-4.1-nano",
        "openai/gpt-4.1-mini",
        "openai/gpt-4.1",
        "openai/gpt-5",
        "openai/gpt-5-mini",
        "openai/gpt-5-nano",
        "openai/o4-mini",
        "anthropic/claude-haiku-4.5",
        "anthropic/claude-sonnet-4.6",
        "anthropic/claude-opus-4.6",
        "google/gemini-2.5-flash",
        "google/gemini-2.5-pro",
        "google/gemini-3.1-flash-lite",
        "google/gemini-3-flash-preview",
        "meta-llama/llama-4-scout",
        "meta-llama/llama-4-maverick",
        "meta-llama/llama-3.3-70b-instruct",
        "mistralai/mistral-small-3.2-24b-instruct",
        "mistralai/mistral-large-2411",
        "qwen/qwen2.5-72b-instruct",
        "qwen/qwen3-32b",
        "qwen/qwen3-235b-a22b",
        "deepseek/deepseek-v3-0324",
        "deepseek/deepseek-v3.1",
        "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "cohere/command-a",
        "x-ai/grok-4.3",
        "z-ai/glm-5",
        "minimax/minimax-m3",
        "qwen/qwen3.7-plus",
        "stepfun/step-3.7-flash",
    ]

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.url = "https://api.free.ai/v1/chat/"
        self.proxies = {}

        agent = LitAgent()
        self.headers = {
            "User-Agent": agent.random(),
            "Content-Type": "application/json",
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    def convert_model_name(self, model: str) -> str:
        if model in self.AVAILABLE_MODELS:
            return model
        for available_model in self.AVAILABLE_MODELS:
            if model.lower() in available_model.lower():
                return available_model
        print(f"{BOLD}Warning: Model '{model}' not found, using default 'qwen7b'{RESET}")
        return "qwen7b"

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in FreeAI.AVAILABLE_MODELS:
        try:
            client = FreeAI(timeout=300)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say 'Hello' in one word"}],
                stream=False,
            )
            if (
                isinstance(response, ChatCompletion)
                and response.choices
                and response.choices[0].message
                and response.choices[0].message.content
            ):
                status = "✓"
                display_text = response.choices[0].message.content.strip()
                display_text = display_text[:50] + "..." if len(display_text) > 50 else display_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"{model:<50} {'✗':<10} {str(e)[:80]}")
