import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError, requests

from llm4free.Provider.llm.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from llm4free.Provider.llm.utils import (
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

APP_ID = 8685039810546182577
CHAT_FN_INDEX = 1
SEND_TRIGGER_ID = 19


def uuid_hex_short() -> str:
    return uuid.uuid4().hex[:12]


class Completions(BaseCompletions):
    def __init__(self, client: "Apriel"):
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

        session_hash = uuid_hex_short()
        self._client._join_queue(session_hash, question)

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, session_hash, timeout, proxies)
        else:
            return self._create_non_stream(
                request_id, created_time, session_hash, timeout, proxies
            )

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        session_hash: str,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            url = f"{self._client.api_endpoint}/gradio_api/queue/data?session_hash={session_hash}"
            resp = self._client.session.get(
                url,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=cast(Any, proxies or getattr(self._client, "proxies", None)),
                impersonate="chrome110",
            )
            if not resp.ok:
                raise IOError(f"Apriel stream failed: {resp.status_code}")

            emitted_length = 0
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else raw_line
                if not line.startswith("data:"):
                    continue
                try:
                    evt = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue
                if not isinstance(evt, dict):
                    continue
                msg = evt.get("msg")
                if msg == "process_completed":
                    break
                if msg != "process_generating":
                    continue
                output = evt.get("output") or {}
                data = output.get("data") or []
                if not data or not isinstance(data, list):
                    continue
                head = data[0]
                if not isinstance(head, list):
                    continue
                messages = [m for m in head if isinstance(m, dict)]
                full = "".join(
                    str(m.get("content") or "")
                    for m in messages
                    if m.get("role") in (None, "assistant")
                )
                delta_text = full[emitted_length:]
                if not delta_text:
                    continue
                emitted_length = len(full)
                delta = ChoiceDelta(content=delta_text)
                choice = Choice(index=0, delta=delta, finish_reason=None)
                chunk = ChatCompletionChunk(
                    id=request_id,
                    choices=[choice],
                    created=created_time,
                    model="Apriel-1.6-15B-Thinker",
                )
                yield chunk

            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model="Apriel-1.6-15B-Thinker",
            )
            yield chunk
        except CurlError as e:
            raise IOError(f"Apriel request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        session_hash: str,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        try:
            full_text = ""
            for chunk in self._create_stream(request_id, created_time, session_hash, timeout, proxies):
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    full_text += chunk.choices[0].delta.content

            usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
            message = ChatCompletionMessage(role="assistant", content=full_text)
            choice = Choice(index=0, message=message, finish_reason="stop")
            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model="Apriel-1.6-15B-Thinker",
                usage=usage,
            )
            return completion
        except Exception as e:
            raise IOError(f"Apriel request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "Apriel"):
        self.completions = Completions(client)


class Apriel(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = ["Apriel-1.6-15B-Thinker"]

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.api_endpoint = "https://servicenow-ai-apriel-chat.hf.space"
        self.proxies = {}

        agent = LitAgent()
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": agent.random(),
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    def _join_queue(self, session_hash: str, message: str) -> Optional[str]:
        url = f"{self.api_endpoint}/gradio_api/queue/join"
        payload = {
            "data": [
                [],
                {"text": message, "files": []},
                None,
            ],
            "event_data": None,
            "fn_index": CHAT_FN_INDEX,
            "trigger_id": SEND_TRIGGER_ID,
            "session_hash": session_hash,
        }
        resp = self.session.post(url, json=payload, timeout=self.timeout)
        if not resp.ok:
            raise IOError(f"queue/join failed: {resp.status_code}")
        try:
            return resp.json().get("event_id")
        except Exception:
            return None

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in Apriel.AVAILABLE_MODELS:
        try:
            client = Apriel(timeout=60)
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
