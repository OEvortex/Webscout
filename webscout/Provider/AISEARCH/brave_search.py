import asyncio
import base64
import json
import os
from typing import Any, AsyncIterator, Dict, Generator, List, Optional, Union, cast
from urllib.parse import quote

from curl_cffi.requests import AsyncSession

from webscout import exceptions
from webscout.AIbase import AISearch, SearchResponse


class BraveAI(AISearch):
    """
    A class to interact with Brave Search AI Chat.

    BraveAI provides AI-generated responses based on web search results.
    It supports both streaming and non-streaming responses.

    Basic Usage:
        >>> from webscout.Provider.AISEARCH import BraveAI
        >>> ai = BraveAI()
        >>> response = ai.search("What is Python?")
        >>> print(response)

    Args:
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
        proxies (dict, optional): Proxy configuration for requests. Defaults to None.
    """
    BASE_URL = "https://search.brave.com/api/tap/v1"


    def __init__(
        self,
        timeout: int = 30,
        proxies: Optional[dict] = None,
    ):
        self.timeout = timeout
        self.proxies = proxies or {}
        self.last_response = {}
        self.chat_id = None
        self.symmetric_key = None
        self.headers = {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="127", "Not)A;Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "referer": "https://search.brave.com/ask"
        }

    def _generate_key_b64(self) -> str:
        """Generates a 256-bit AES-GCM key in JWK format, base64 encoded."""
        key = os.urandom(32)
        k = base64.urlsafe_b64encode(key).decode().rstrip("=")
        jwk = {
            "alg": "A256GCM",
            "ext": True,
            "k": k,
            "key_ops": ["encrypt", "decrypt"],
            "kty": "oct"
        }
        return base64.b64encode(json.dumps(jwk, separators=(',', ':')).encode()).decode()

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None]]:
        """Search using the Brave Search AI and get AI-generated responses."""

        if not stream:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self._async_search(prompt, False, raw)
                )
                return cast(Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None]], result)
            finally:
                loop.close()

        buffer = ""

        def sync_generator():
            nonlocal buffer
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async_gen = loop.run_until_complete(self._async_search(prompt, True, raw))
                if hasattr(async_gen, "__anext__"):
                    async_iterator = cast(AsyncIterator, async_gen)
                    while True:
                        try:
                            chunk = loop.run_until_complete(async_iterator.__anext__())
                            if isinstance(chunk, dict) and "text" in chunk:
                                buffer += chunk["text"]
                            elif isinstance(chunk, SearchResponse):
                                buffer += chunk.text
                            yield chunk
                        except StopAsyncIteration:
                            break
                elif isinstance(async_gen, SearchResponse):
                    yield async_gen
            finally:
                self.last_response = {"text": buffer}
                loop.close()

        return cast(Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None]], sync_generator())

    async def _async_search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
    ) -> Union[
        SearchResponse,
        str,
        AsyncIterator[Union[Dict[str, str], SearchResponse]],
    ]:
        """Internal async implementation of the search method."""

        session = AsyncSession()
        try:
            session.headers.update(self.headers)
            if self.proxies:
                session.proxies.update(self.proxies)

            # Initialize new chat if needed
            if not self.chat_id or not self.symmetric_key:
                key_b64 = self._generate_key_b64()
                params = {
                    "language": "en",
                    "country": "US",
                    "ui_lang": "en",
                    "symmetric_key": key_b64,
                    "source": "llmSuggest",
                    "query": prompt
                }
                response = await session.get(
                    f"{self.BASE_URL}/new",
                    params=params,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                if response.status_code != 200:
                    raise exceptions.FailedToGenerateResponseError(f"Failed to create new chat: {response.text}")

                data = response.json()
                self.chat_id = data.get("id")
                self.symmetric_key = key_b64

            params = {
                "id": self.chat_id,
                "query": prompt,
                "symmetric_key": self.symmetric_key,
                "language": "en",
                "country": "US",
                "ui_lang": "en"
            }

            ref = f"https://search.brave.com/ask?q={quote(prompt)}&conversation={self.chat_id}"
            headers = {"referer": ref}

            if not stream:
                full_text = ""
                response = await session.get(
                    f"{self.BASE_URL}/stream",
                    params=params,
                    headers=headers,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        j = json.loads(line)
                        if j.get("type") == "text_delta":
                            full_text += j.get("delta", "")
                    except json.JSONDecodeError:
                        continue

                self.last_response = SearchResponse(full_text)
                return full_text if raw else self.last_response

            async def process_stream():
                buffer = ""
                try:
                    response = await session.get(
                        f"{self.BASE_URL}/stream",
                        params=params,
                        headers=headers,
                        stream=True,
                        timeout=self.timeout,
                        impersonate="chrome110"
                    )
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            j = json.loads(line)
                            t = j.get("type")
                            if t == "text_delta":
                                delta = j.get("delta", "")
                                buffer += delta
                                if raw:
                                    yield j
                                else:
                                    yield SearchResponse(delta)
                        except json.JSONDecodeError:
                            continue
                    self.last_response = SearchResponse(buffer)
                finally:
                    await session.close()

            return process_stream()
        except Exception:
            if not stream:
                await session.close()
            raise

if __name__ == "__main__":
    ai = BraveAI()
    res = ai.search("What is Python?", stream=True)
    from collections.abc import Iterable

    if isinstance(res, Iterable):
        for chunk in res:
            print(chunk, end="", flush=True)
    else:
        print(res)
