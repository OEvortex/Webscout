"""
FreeAIOnline - Free AI No Login Unlimited via free-ai-online.com

A WordPress-powered free AI chat site (AI Engine plugin) that provides
unlimited access to GPT-4o without login.

API Flow:
1. POST /wp-json/mwai/v1/start_session → get restNonce
2. POST /wp-json/mwai-ui/v1/chats/submit → SSE stream or JSON response

SSE format:
  data: {"type":"live","data":"token"}
  data: {"type":"end","data":"{json with success,reply,usage,...}"}
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
    def __init__(self, client: "FreeAIOnline"):
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
        self._client.ensure_session()

        chat_id = uuid.uuid4().hex[:20]
        mwai_messages = self._build_mwai_messages(messages)
        last_message = messages[-1].get("content", "") if messages else ""

        payload: Dict[str, Any] = {
            "botId": "AI FREE",
            "customId": None,
            "session": None,
            "chatId": chat_id,
            "contextId": self._client.context_id,
            "messages": mwai_messages,
            "newMessage": last_message,
            "newFileId": None,
            "newFileIds": None,
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

    def _build_mwai_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        mwai_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            who = "AI: " if role == "assistant" else "User: "
            mwai_messages.append(
                {
                    "id": uuid.uuid4().hex[:10],
                    "role": role,
                    "content": content,
                    "who": who,
                    "timestamp": int(time.time() * 1000),
                }
            )
        return mwai_messages

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
                self._client.chat_endpoint,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                impersonate="chrome120",
            )

            if response.status_code != 200:
                raise IOError(f"FreeAIOnline request failed: {response.status_code}")

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

                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type", "")

                    if event_type == "live":
                        content = event.get("data", "")
                        if content:
                            delta = ChoiceDelta(content=content)
                            choice = Choice(index=0, delta=delta, finish_reason=None)
                            yield ChatCompletionChunk(
                                id=request_id,
                                choices=[choice],
                                created=created_time,
                                model=model,
                            )
                    elif event_type == "end":
                        delta = ChoiceDelta(content=None)
                        choice = Choice(index=0, delta=delta, finish_reason="stop")
                        yield ChatCompletionChunk(
                            id=request_id,
                            choices=[choice],
                            created=created_time,
                            model=model,
                        )
                        return

            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            yield ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
            )
        except CurlError as e:
            raise IOError(f"FreeAIOnline request failed: {e}") from e

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
                self._client.chat_endpoint,
                json=payload,
                timeout=timeout or self._client.timeout,
                impersonate="chrome120",
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise IOError(f"FreeAIOnline API error: {data.get('message', 'unknown')}")

            full_text = data.get("reply", "")
            usage_data = data.get("usage", {})

            usage = CompletionUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
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
            raise IOError(f"FreeAIOnline request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "FreeAIOnline"):
        self.completions = Completions(client)


class FreeAIOnline(OpenAICompatibleProvider):
    """
    Free AI - No Login & Unlimited via free-ai-online.com

    Uses the WordPress AI Engine plugin REST API:
    - Session: POST /wp-json/mwai/v1/start_session
    - Chat: POST /wp-json/mwai-ui/v1/chats/submit

    Usage:
        client = FreeAIOnline()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response.choices[0].message.content)
    """

    required_auth = False
    AVAILABLE_MODELS = ["gpt-4o"]

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.base_url = "https://www.free-ai-online.com"
        self.session_endpoint = f"{self.base_url}/wp-json/mwai/v1/start_session"
        self.chat_endpoint = f"{self.base_url}/wp-json/mwai-ui/v1/chats/submit"
        self.context_id = 2108
        self._rest_nonce: Optional[str] = None
        self._session_ready = False

        agent = LitAgent()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": agent.random(),
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/free-ai-no-login-unlimited/",
            }
        )
        self.chat = Chat(self)

    def ensure_session(self) -> None:
        if self._session_ready:
            return
        try:
            resp = self.session.post(
                self.session_endpoint,
                json={},
                timeout=self.timeout,
                impersonate="chrome120",
            )
            data = resp.json()
            if data.get("success"):
                self._rest_nonce = data.get("restNonce")
                if self._rest_nonce:
                    self.session.headers["X-WP-Nonce"] = self._rest_nonce
                self._session_ready = True
        except Exception:
            self._session_ready = True

    def convert_model_name(self, model: str) -> str:
        return "gpt-4o"

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in FreeAIOnline.AVAILABLE_MODELS:
        try:
            client = FreeAIOnline(timeout=120)
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
