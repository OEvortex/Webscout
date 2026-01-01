import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi.requests import Session

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
    format_prompt,
)

from ...litagent import LitAgent


class _DeltaExtractor:
    """Stateful extractor that merges `reasoning-delta` and `text-delta` into a single text stream.
    Used for OpenAI compatibility to provide a unified content stream.
    """

    def __init__(self, include_think_tags: bool = True) -> None:
        self._in_reasoning = False
        self.include_think_tags = include_think_tags

    def __call__(self, obj: Union[str, Dict[str, Any]]) -> Optional[str]:
        if not isinstance(obj, dict):
            return None

        t = obj.get("type")
        if t == "reasoning-delta":
            delta = obj.get("delta") or ""
            if self.include_think_tags:
                if not self._in_reasoning:
                    self._in_reasoning = True
                    return f"\n<think>\n{delta}"
                return delta
            return delta  # If not including tags, just return the reasoning delta

        if t == "text-delta":
            delta = obj.get("delta") or ""
            if self._in_reasoning:
                self._in_reasoning = False
                if self.include_think_tags:
                    return f"\n</think>\n\n{delta}"
            return delta

        return None


class Completions(BaseCompletions):
    def __init__(self, client: "HadadXYZ"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 2049,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        include_think_tags: bool = True,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        # Format the prompt using the utility
        prompt = format_prompt(messages, include_system=True)

        payload = {
            "tools": {},
            "modelId": model,
            "sessionId": uuid.uuid4().hex,
            "clientId": uuid.uuid4().hex,
            "requestId": uuid.uuid4().hex,
            "id": "DEFAULT_THREAD_ID",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": prompt}],
                    "id": uuid.uuid4().hex,
                }
            ],
            "trigger": "submit-message",
            "metadata": {},
        }

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(
                request_id, created_time, model, payload, timeout, proxies, include_think_tags
            )
        else:
            return self._create_non_stream(
                request_id, created_time, model, payload, timeout, proxies, include_think_tags
            )

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        include_think_tags: bool = True,
    ) -> Generator[ChatCompletionChunk, None, None]:
        extractor = _DeltaExtractor(include_think_tags=include_think_tags)

        try:
            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies,
                impersonate="chrome120",
            )
            response.raise_for_status()

            prompt_tokens = count_tokens(payload["messages"][0]["parts"][0]["text"])
            completion_tokens = 0

            from webscout.AIutel import sanitize_stream

            processed_stream = sanitize_stream(
                data=response.iter_lines(),
                intro_value="data:",
                to_json=True,
                content_extractor=extractor,
                yield_raw_on_error=False,
                raw=False,
            )

            for content_chunk in processed_stream:
                if content_chunk and isinstance(content_chunk, str):
                    completion_tokens += count_tokens(content_chunk)

                    delta = ChoiceDelta(content=content_chunk, role="assistant")
                    choice = Choice(index=0, delta=delta, finish_reason=None)
                    chunk = ChatCompletionChunk(
                        id=request_id,
                        choices=[choice],
                        created=created_time,
                        model=model,
                    )
                    chunk.usage = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    }
                    yield chunk

            # Final chunk
            yield ChatCompletionChunk(
                id=request_id,
                choices=[Choice(index=0, delta=ChoiceDelta(), finish_reason="stop")],
                created=created_time,
                model=model,
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            )

        except Exception as e:
            raise IOError(f"HadadXYZ stream request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        include_think_tags: bool = True,
    ) -> ChatCompletion:
        full_content = ""
        prompt_tokens = count_tokens(payload["messages"][0]["parts"][0]["text"])

        try:
            for chunk in self._create_stream(
                request_id, created_time, model, payload, timeout, proxies, include_think_tags
            ):
                if chunk.choices and chunk.choices[0].delta.content:
                    full_content += chunk.choices[0].delta.content

            completion_tokens = count_tokens(full_content)

            message = ChatCompletionMessage(role="assistant", content=full_content)
            choice = Choice(index=0, message=message, finish_reason="stop")
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )
            return ChatCompletion(
                id=request_id, choices=[choice], created=created_time, model=model, usage=usage
            )
        except Exception as e:
            raise IOError(f"HadadXYZ non-stream request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "HadadXYZ"):
        self.completions = Completions(client)


class HadadXYZ(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for HadadXYZ API.
    """

    required_auth = False
    AVAILABLE_MODELS = [
        "deepseek-ai/deepseek-r1-0528",
        "deepseek-ai/deepseek-v3.2-thinking",
        "google/gemini-2.5-flash-lite-search",
        "google/gemini-2.5-flash-lite",
        "google/gemini-3-pro-preview",
        "minimaxai/minimax-m2",
        "mistralai/devstral-2-123b-instruct-2512",
        "mistralai/devstral-small-2-24b-instruct-2512",
        "mistralai/mistral-large-3-675b-instruct-2512",
        "moonshotai/kimi-k2-thinking",
        "nvidia/nvidia-nemotron-3-nano-30b-a3b",
        "nvidia/nvidia-nemotron-3-nano-30b-a3b-thinking",
        "openai/gpt-4.1-nano-2025-04-14",
        "openai",
        "openai-fast",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-safeguard-20b",
        "perplexity-fast",
        "qwen/qwen3-next-80b-a3b-thinking",
        "qwen/qwen3-vl-235b-a22b-instruct",
        "qwen/qwen3-vl-235b-a22b-thinking",
        "grok",
        "zai-org/glm-4.6",
        "anthropic/claude-opus-4-5-20251101",
        "anthropic/claude-sonnet-4-5-20250929",
        "anthropic/claude-haiku-4-5-20251001/legacy",
    ]

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.api_endpoint = (
            "https://hadadxyz-ai.hf.space/api/"
            "aynzy5127hgsba5f3a9c2d1gduqb7e84fygd016c9a2d1f8b3c41gut432pjctr75"
            "hhspjae5d6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d7e2b4c9f83da4f1bb6c152"
            "f9e3c7a88d91f3c2b76513bpaneyx43vdaw074"
        )
        self.session = Session()
        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
        }
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    client = HadadXYZ()
    response = client.chat.completions.create(
        model="deepseek-ai/deepseek-r1-0528",
        messages=[{"role": "user", "content": "How many r in strawberry"}],
        stream=True,
    )
    for chunk in cast(Generator[ChatCompletionChunk, None, None], response):
        if chunk.choices[0].delta and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
