import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError, requests

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
    format_prompt,
)

from llm4free.litagent import LitAgent


class Completions(BaseCompletions):
    def __init__(self, client: "ArtingAI"):
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
        question = format_prompt(messages, add_special_tokens=True)

        model = self._client.convert_model_name(model)
        session_id = str(uuid.uuid4())

        payload = {
            "generation_type": model,
            "task_type": "ai-chat",
            "session_id": session_id,
            "stream": True,
            "files": [],
            "text": question,
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
            auth_token = str(uuid.uuid4())
            response = self._client.session.post(
                self._client.url,
                headers={
                    "Authorization": auth_token,
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream, application/json, text/plain, */*",
                },
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=cast(Any, proxies or getattr(self._client, "proxies", None)),
                impersonate="chrome110",
            )
            response.raise_for_status()

            streaming_text = []
            for chunk in response.iter_content(chunk_size=None):
                if not chunk:
                    continue
                if isinstance(chunk, bytes):
                    try:
                        chunk = chunk.decode("utf-8", errors="replace")
                    except Exception:
                        continue
                if not chunk:
                    continue
                streaming_text.append(chunk)
                delta = ChoiceDelta(content=chunk)
                choice = Choice(index=0, delta=delta, finish_reason=None)
                chunk_obj = ChatCompletionChunk(
                    id=request_id,
                    choices=[choice],
                    created=created_time,
                    model=model,
                )
                yield chunk_obj

            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
            )
            yield chunk
        except CurlError as e:
            raise IOError(f"ArtingAI request failed: {e}") from e

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
            auth_token = str(uuid.uuid4())
            payload["stream"] = False
            response = self._client.session.post(
                self._client.url,
                headers={
                    "Authorization": auth_token,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=timeout or self._client.timeout,
                proxies=cast(Any, proxies or getattr(self._client, "proxies", None)),
                impersonate="chrome110",
            )
            response.raise_for_status()
            data = response.json()
            full_text = data.get("data", {}).get("result", "")

            prompt_tokens = len(payload.get("text", "").split())
            completion_tokens = len(full_text.split())
            total_tokens = prompt_tokens + completion_tokens
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
            message = ChatCompletionMessage(role="assistant", content=full_text)
            choice = Choice(index=0, message=message, finish_reason="stop")
            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )
            return completion
        except Exception as e:
            raise IOError(f"ArtingAI request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "ArtingAI"):
        self.completions = Completions(client)


class ArtingAI(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = [
        "gpt-5",
        "gpt-5.1",
        "gpt-5.2",
        "gpt-4o-mini",
        "o4-mini",
        "gemini-2.5-pro",
        "gemini-3-pro-preview",
        "deepseek-chat",
        "deepseek-reasoner",
    ]

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.url = "https://arting.ai/api/aigc/comprehensive/chat/create-task"
        self.proxies = {}

        agent = LitAgent()
        self.headers = {
            "User-Agent": agent.random(),
            "Content-Type": "application/json",
            "Origin": "https://arting.ai",
            "Referer": "https://arting.ai/ai-chat/",
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    def convert_model_name(self, model: str) -> str:
        if model in self.AVAILABLE_MODELS:
            return model
        for m in self.AVAILABLE_MODELS:
            if model.lower() in m.lower():
                return m
        return "gpt-5"

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in ArtingAI.AVAILABLE_MODELS:
        try:
            client = ArtingAI(timeout=60)
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
