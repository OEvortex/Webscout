import html
import re
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


def html_to_markdown(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n# \1\n", text)
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"\n* \1", text)
    text = re.sub(r"<(ul|ol)[^>]*>", r"\n", text)
    text = re.sub(r"</(ul|ol)>", r"\n", text)
    text = re.sub(r"</p>", r"\n\n", text)
    text = re.sub(r"<p[^>]*>", r"\n", text)
    text = re.sub(r"<br\s*/?>", r"\n", text)
    text = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", text)
    text = re.sub(r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", text)
    text = re.sub(r"</?(section|div|span|article|header|footer)[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]*>", "", text)
    return text


class Completions(BaseCompletions):
    def __init__(self, client: "TurboSeek"):
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

        payload = {"question": question, "sources": []}

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
            response = self._client.session.post(
                self._client.url,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=cast(Any, proxies or getattr(self._client, "proxies", None)),
                impersonate="chrome120",
            )
            if not response.ok:
                raise IOError(f"TurboSeek request failed: {response.status_code}")

            raw_buffer = b""
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    raw_buffer += chunk

            full_html = raw_buffer.decode("utf-8", errors="replace")
            final_text = html_to_markdown(full_html).strip()

            if final_text:
                words = final_text.split()
                current = ""
                for word in words:
                    current += word + " "
                    if len(current) >= 40 or word.endswith((".", "!", "?", "\n")):
                        delta = ChoiceDelta(content=current)
                        choice = Choice(index=0, delta=delta, finish_reason=None)
                        chunk_obj = ChatCompletionChunk(
                            id=request_id,
                            choices=[choice],
                            created=created_time,
                            model="Llama 3.1 70B",
                        )
                        yield chunk_obj
                        current = ""
                if current.strip():
                    delta = ChoiceDelta(content=current)
                    choice = Choice(index=0, delta=delta, finish_reason=None)
                    chunk_obj = ChatCompletionChunk(
                        id=request_id,
                        choices=[choice],
                        created=created_time,
                        model="Llama 3.1 70B",
                    )
                    yield chunk_obj

            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model="Llama 3.1 70B",
            )
            yield chunk
        except CurlError as e:
            raise IOError(f"TurboSeek request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
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
                impersonate="chrome120",
            )
            full_html = response.text
            full_text = html_to_markdown(full_html).strip()

            prompt_tokens = len(payload.get("question", "").split())
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
                model="Llama 3.1 70B",
                usage=usage,
            )
            return completion
        except Exception as e:
            raise IOError(f"TurboSeek request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "TurboSeek"):
        self.completions = Completions(client)


class TurboSeek(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = ["gpt-oss"]

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.url = "https://www.turboseek.io/api/getAnswer"
        self.proxies = {}

        agent = LitAgent()
        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://www.turboseek.io",
            "referer": "https://www.turboseek.io/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": agent.random(),
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in TurboSeek.AVAILABLE_MODELS:
        try:
            client = TurboSeek(timeout=60)
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
