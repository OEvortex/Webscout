import json
import random
import string
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
    count_tokens,
    format_prompt,
)

from llm4free.litagent import LitAgent

class Completions(BaseCompletions):
    def __init__(self, client: "EssentialAI"):
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

        payload = {
            "data": [
                question,
                [],
                "You are a helpful AI assistant.",
                float(max_tokens or self._client.max_tokens),
                float(temperature or self._client.temperature),
                float(top_p or self._client.top_p),
            ]
        }

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, payload, timeout, proxies)
        else:
            return self._create_non_stream(
                request_id, created_time, payload, timeout, proxies
            )

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            call_url = f"{self._client.api_endpoint}/gradio_api/call/chat"
            call_response = self._client.session.post(call_url, json=payload, timeout=timeout or self._client.timeout)
            call_response.raise_for_status()
            event_id = call_response.json().get("event_id")

            if not event_id:
                raise IOError("Failed to get event_id")

            url = f"{self._client.api_endpoint}/gradio_api/call/chat/{event_id}"
            resp = self._client.session.get(
                url,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=cast(Any, proxies or getattr(self._client, "proxies", None)),
                impersonate="chrome110",
            )
            if not resp.ok:
                raise IOError(f"EssentialAI stream failed: {resp.status_code}")

            last_full_text = ""
            for line in resp.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        if isinstance(data, list) and len(data) > 0:
                            current_full_text = data[0]
                            if isinstance(current_full_text, str):
                                if current_full_text.startswith(last_full_text):
                                    delta_text = current_full_text[len(last_full_text):]
                                else:
                                    delta_text = current_full_text
                                last_full_text = current_full_text
                                if delta_text:
                                    delta = ChoiceDelta(content=delta_text)
                                    choice = Choice(index=0, delta=delta, finish_reason=None)
                                    chunk = ChatCompletionChunk(
                                        id=request_id,
                                        choices=[choice],
                                        created=created_time,
                                        model="rnj-1-instruct",
                                    )
                                    yield chunk
                    except Exception:
                        pass

            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model="rnj-1-instruct",
            )
            yield chunk
        except CurlError as e:
            raise IOError(f"EssentialAI request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        try:
            full_text = ""
            for chunk in self._create_stream(request_id, created_time, payload, timeout, proxies):
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    full_text += chunk.choices[0].delta.content

            usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
            message = ChatCompletionMessage(role="assistant", content=full_text)
            choice = Choice(index=0, message=message, finish_reason="stop")
            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model="rnj-1-instruct",
                usage=usage,
            )
            return completion
        except Exception as e:
            raise IOError(f"EssentialAI request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "EssentialAI"):
        self.completions = Completions(client)


class EssentialAI(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = ["rnj-1-instruct"]

    def __init__(self, timeout: int = 30, temperature: float = 0.2, top_p: float = 0.95, max_tokens: int = 512):
        self.timeout = timeout
        self.api_endpoint = "https://essentialai-rnj-1-instruct-space.hf.space"
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.proxies = {}

        agent = LitAgent()
        zerogpu_uuid = "".join(
            random.choices(string.ascii_letters + string.digits + "_", k=21)
        )
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": agent.random(),
            "Accept": "text/event-stream",
            "x-zerogpu-uuid": zerogpu_uuid,
            "X-Gradio-Expand-Data": "true",
            "X-Gradio-Target": "chat",
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)

        try:
            self.session.get(self.api_endpoint, timeout=self.timeout)
        except Exception:
            pass

        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in EssentialAI.AVAILABLE_MODELS:
        try:
            client = EssentialAI(timeout=60)
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
