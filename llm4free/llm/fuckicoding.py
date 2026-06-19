"""
FuckICoding - Free ChatGPT Mirror via link.fuckicoding.com (Lite-GPT)

A free provider that provides access to GPT-4o, Claude, Gemini and other
models through the Lite-GPT mirror at link.fuckicoding.com.

API: POST https://apilite.icoding.ink/api/v1/gpt/message
Auth: Guest access via guest-id header (Bearer null)
SSE format: data: {"c":"content","rc":"reasoning_content"}
"""

import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union

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
)


class Completions(BaseCompletions):
    def __init__(self, client: "FuckICoding"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        model = self._client.convert_model_name(model)
        self._client.ensure_guest_id()

        mwai_messages = []
        for msg in messages:
            mwai_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "time": time.strftime("%d/%m/%Y, %H:%M:%S"),
                "attachments": [],
            })

        payload: Dict[str, Any] = {
            "model": model,
            "chatId": -32,
            "messages": mwai_messages,
            "plugins": [],
            "systemPrompt": kwargs.get("system_prompt", ""),
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(
                request_id, created_time, model, payload, timeout, proxies
            )
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
            headers = {
                "Authorization": "Bearer null",
                "Content-Type": "application/json;charset=utf-8",
                "Accept": "text/event-stream",
                "Origin": "https://link.fuckicoding.com",
                "Referer": "https://link.fuckicoding.com/",
                "guest-id": self._client.guest_id,
                "version": "v2",
            }

            response = self._client.session.post(
                self._client.api_endpoint,
                json=payload,
                headers=headers,
                stream=True,
                timeout=timeout or self._client.timeout,
                impersonate="chrome120",
            )

            if response.status_code == 401:
                raise IOError("Authentication failed - guest access denied")
            if response.status_code != 200:
                raise IOError(
                    f"FuckICoding request failed: {response.status_code}"
                )

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                data = response.json()
                if not data.get("success", True):
                    raise IOError(
                        f"FuckICoding API error: {data.get('message', 'unknown')}"
                    )

            buffer = ""
            for chunk in response.iter_content(chunk_size=None):
                if not chunk:
                    continue
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8", errors="replace")
                buffer += chunk

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if not data_str:
                        continue
                    if data_str == "[DONE]":
                        break

                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    content = event.get("c", "")
                    if content:
                        delta = ChoiceDelta(content=content)
                        choice = Choice(
                            index=0, delta=delta, finish_reason=None
                        )
                        yield ChatCompletionChunk(
                            id=request_id,
                            choices=[choice],
                            created=created_time,
                            model=model,
                        )

            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            yield ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
            )
        except CurlError as e:
            raise IOError(f"FuckICoding request failed: {e}") from e

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
            full_text = ""
            for chunk in self._create_stream(
                request_id, created_time, model, payload, timeout, proxies
            ):
                if (
                    chunk.choices
                    and chunk.choices[0].delta
                    and chunk.choices[0].delta.content
                ):
                    full_text += chunk.choices[0].delta.content

            usage = CompletionUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
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
            raise IOError(f"FuckICoding request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "FuckICoding"):
        self.completions = Completions(client)


class FuckICoding(OpenAICompatibleProvider):
    """
    Free ChatGPT Mirror via link.fuckicoding.com (Lite-GPT)

    Provides free access to various AI models through the Lite-GPT mirror.
    No authentication required - uses guest-id header.

    Usage:
        client = FuckICoding()
        response = client.chat.completions.create(
            model="mimo-v2.5-pro",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response.choices[0].message.content)
    """

    required_auth = False
    AVAILABLE_MODELS = [
        "mimo-v2.5-pro",
        "gpt-4o",
        "gpt-4-turbo",
        "deepseek-chat",
        "claude-3.5",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "claude-4.5-haiku",
        "gemini-2.5-lite",
        "gpt-5.4-mini",
    ]

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.api_endpoint = "https://apilite.icoding.ink/api/v1/gpt/message"
        self.guest_id = uuid.uuid4().hex

        agent = LitAgent()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": agent.random(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
        self.chat = Chat(self)

    def ensure_guest_id(self) -> None:
        if not self.guest_id:
            self.guest_id = uuid.uuid4().hex

    def convert_model_name(self, model: str) -> str:
        if model in self.AVAILABLE_MODELS:
            return model
        for m in self.AVAILABLE_MODELS:
            if model.lower() in m.lower() or m.lower() in model.lower():
                return m
        return "mimo-v2.5-pro"

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in FuckICoding.AVAILABLE_MODELS:
        try:
            client = FuckICoding(timeout=120)
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
                display_text = (
                    display_text[:50] + "..."
                    if len(display_text) > 50
                    else display_text
                )
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"{model:<50} {'✗':<10} {str(e)[:80]}")
