import re
import secrets
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union

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
    def __init__(self, client: "JadveOpenAI"):
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

        payload = {
            "id": secrets.token_hex(8),
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": question}]}
            ],
            "model": model,
            "botId": "",
            "chatId": "",
            "stream": True,
            "returnTokensUsage": True,
            "useTools": False,
        }

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, payload, timeout, proxies)
        else:
            return self._create_non_stream(
                request_id, created_time, model, payload, timeout, proxies
            )

    @staticmethod
    def _jadve_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        if isinstance(chunk, str):
            match = re.search(r'0:"(.*?)"(?=,|$)', chunk)
            if match:
                content = match.group(1).encode().decode("unicode_escape")
                return content.replace("\\\\", "\\").replace('\\"', '"')
        return None

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
                impersonate="chrome120",
            )
            response.raise_for_status()

            streaming_text = []
            for raw_chunk in response.iter_content(chunk_size=None):
                if not raw_chunk:
                    continue
                if isinstance(raw_chunk, bytes):
                    raw_chunk = raw_chunk.decode("utf-8", errors="replace")
                text = self._jadve_extractor(raw_chunk)
                if text:
                    streaming_text.append(text)
                    delta = ChoiceDelta(content=text)
                    choice = Choice(index=0, delta=delta, finish_reason=None)
                    chunk = ChatCompletionChunk(
                        id=request_id,
                        choices=[choice],
                        created=created_time,
                        model=model,
                    )
                    yield chunk

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
            raise IOError(f"JadveOpenAI request failed: {e}") from e

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
            for chunk in self._create_stream(request_id, created_time, model, payload, timeout, proxies):
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    full_text += chunk.choices[0].delta.content

            prompt_tokens = len(payload.get("messages", [{}])[0].get("content", [{}])[0].get("text", "").split()) if payload.get("messages") else 0
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
            raise IOError(f"JadveOpenAI request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "JadveOpenAI"):
        self.completions = Completions(client)


class JadveOpenAI(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = ["gpt-5-mini", "claude-3-5-haiku-20241022"]

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.url = "https://ai-api.jadve.com/api/chat"
        self.proxies = {}

        agent = LitAgent()
        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://jadve.com",
            "referer": "https://jadve.com/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": agent.random(),
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
        return "gpt-5-mini"

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in JadveOpenAI.AVAILABLE_MODELS:
        try:
            client = JadveOpenAI(timeout=60)
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
