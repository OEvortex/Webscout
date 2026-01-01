import re
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi.requests import Session

from webscout.AIutel import sanitize_stream
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
)

from ...litagent import LitAgent


class Completions(BaseCompletions):
    def __init__(self, client: "Elmo"):
        self._client = client

    @staticmethod
    def _elmo_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from the Elmo stream format '0:"..."'."""
        if isinstance(chunk, str):
            match = re.search(
                r'0:"(.*?)"(?=,|$)', chunk
            )  # Look for 0:"...", possibly followed by comma or end of string
            if match:
                # Decode potential unicode escapes like \u00e9 and handle escaped quotes/backslashes
                content = match.group(1).encode().decode("unicode_escape")
                return content.replace("\\\\", "\\").replace('\\"', '"')
        return None

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 600,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        # Elmo uses a fixed system prompt, but we can override if provided
        system_prompt = self._client.system_prompt
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", system_prompt)
                break

        # Build conversation in Elmo format
        conversation = []
        if system_prompt:
            conversation.append({"role": "system", "content": system_prompt})
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                conversation.append({"role": msg["role"], "content": msg["content"]})

        payload = {
            "metadata": {
                "system": {"language": "en-US"},
                "website": {
                    "url": "chrome-extension://ipnlcfhfdicbfbchfoihipknbaeenenm/options.html",
                    "origin": "chrome-extension://ipnlcfhfdicbfbchfoihipknbaeenenm",
                    "title": "Elmo Chat - Your AI Web Copilot",
                    "xpathIndexLength": 0,
                    "favicons": [],
                    "language": "en",
                    "content": "",
                    "type": "html",
                    "selection": "",
                    "hash": "d41d8cd98f00b204e9800998ecf8427e",
                },
            },
            "regenerate": True,
            "conversation": conversation,
            "enableCache": False,
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
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies,
                impersonate="chrome110",
            )
            response.raise_for_status()

            # Use sanitize_stream to process the response
            processed_stream = sanitize_stream(
                data=response.iter_content(chunk_size=None),  # Pass byte iterator
                intro_value=None,  # No simple prefix
                to_json=False,  # Content is text after extraction
                content_extractor=self._elmo_extractor,  # Use the specific extractor
                yield_raw_on_error=True,
                raw=False,
            )

            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            for content_chunk in processed_stream:
                if content_chunk and isinstance(content_chunk, str):
                    completion_tokens += len(content_chunk.split())
                    total_tokens = prompt_tokens + completion_tokens
                    delta = ChoiceDelta(content=content_chunk, role="assistant", tool_calls=None)
                    choice = Choice(index=0, delta=delta, finish_reason=None, logprobs=None)
                    chunk = ChatCompletionChunk(
                        id=request_id,
                        choices=[choice],
                        created=created_time,
                        model=model,
                        system_fingerprint=None,
                    )
                    chunk.usage = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                        "estimated_cost": None,
                    }
                    yield chunk

            # Final chunk
            delta = ChoiceDelta(content=None, role=None, tool_calls=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop", logprobs=None)
            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                system_fingerprint=None,
            )
            chunk.usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": None,
            }
            yield chunk
        except Exception as e:
            print(f"Error during Elmo stream request: {e}")
            raise IOError(f"Elmo request failed: {e}") from e

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
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,  # Still use stream=True to get the response as a stream
                timeout=timeout or self._client.timeout,
                proxies=proxies,
            )
            response.raise_for_status()

            # Use sanitize_stream to process the response and aggregate content
            processed_stream = sanitize_stream(
                data=response.iter_content(chunk_size=None),  # Pass byte iterator
                intro_value=None,  # No simple prefix
                to_json=False,  # Content is text after extraction
                content_extractor=self._elmo_extractor,  # Use the specific extractor
                yield_raw_on_error=True,
                raw=False,
            )

            # Aggregate all content
            content = ""
            for content_chunk in processed_stream:
                if content_chunk and isinstance(content_chunk, str):
                    content += content_chunk

            message = ChatCompletionMessage(role="assistant", content=content)
            choice = Choice(index=0, message=message, finish_reason="stop")
            usage = CompletionUsage(
                prompt_tokens=0,  # Elmo doesn't provide token counts
                completion_tokens=len(content.split()),
                total_tokens=len(content.split()),
            )
            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )
            return completion
        except Exception as e:
            print(f"Error during Elmo non-stream request: {e}")
            raise IOError(f"Elmo request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "Elmo"):
        self.completions = Completions(client)


class Elmo(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = ["elmo"]

    def __init__(self, browser: str = "chrome"):
        self.timeout = 30
        self.api_endpoint = "https://www.elmo.chat/api/v1/prompt"
        self.system_prompt = "You are a helpful AI assistant. Provide clear, concise, and well-structured information. Organize your responses into paragraphs for better readability."
        self.session = Session()
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "text/plain;charset=UTF-8",
            "dnt": "1",
            "origin": "chrome-extension://ipnlcfhfdicbfbchfoihipknbaeenenm",
            "priority": "u=1, i",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
        }
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    client = Elmo()
    response = client.chat.completions.create(
        model="elmo",
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        max_tokens=600,
        stream=False,
    )
    if isinstance(response, ChatCompletion):
        if response.choices[0].message and response.choices[0].message.content:
            print(response.choices[0].message.content)
