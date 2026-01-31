import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

import requests

# Attempt to import LitAgent, fallback if not available
from ...litagent import LitAgent

# Import base classes and utility structures
from .base import BaseChat, BaseCompletions, OpenAICompatibleProvider, SimpleModelList
from .utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
)


class Completions(BaseCompletions):
    def __init__(self, client: "Writecream"):
        self._client = client

    def create(
        self,
        *,
        model: str,  # Not used by Writecream, for compatibility
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,  # Not used by Writecream
        stream: bool = False,
        temperature: Optional[float] = None,  # Not used by Writecream
        top_p: Optional[float] = None,  # Not used by Writecream
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create
        """
        payload = messages
        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())
        if stream:
            return self._create_stream(request_id, created_time, payload, timeout, proxies)
        else:
            return self._create_non_stream(request_id, created_time, payload, timeout, proxies)

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        payload: List[Dict[str, str]],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        # Writecream does not support streaming, so yield the full response as a single chunk
        completion = self._create_non_stream(request_id, created_time, payload, timeout, proxies)
        message = completion.choices[0].message
        content = message.content if message else None
        # Yield as a single chunk
        delta = ChoiceDelta(content=content)
        choice = Choice(index=0, delta=delta, finish_reason=None)
        chunk = ChatCompletionChunk(
            id=request_id,
            choices=[choice],
            created=created_time,
            model="writecream",
        )
        yield chunk
        # Final chunk with finish_reason
        delta = ChoiceDelta(content=None)
        choice = Choice(index=0, delta=delta, finish_reason="stop")
        chunk = ChatCompletionChunk(
            id=request_id,
            choices=[choice],
            created=created_time,
            model="writecream",
        )
        yield chunk

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        payload: List[Dict[str, str]],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        try:
            params = {"query": json.dumps(payload), "link": "writecream.com"}
            response = self._client.session.get(
                self._client.base_url,
                params=params,
                headers=self._client.headers,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),
            )
            response.raise_for_status()
            data = response.json()
            # Extract the response content according to the new API format
            content = data.get("response_content", "")
            # Estimate tokens
            prompt_tokens = sum(count_tokens(m.get("content", "")) for m in payload)
            completion_tokens = count_tokens(content)
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )
            message = ChatCompletionMessage(role="assistant", content=content)
            choice = Choice(index=0, message=message, finish_reason="stop")
            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model="writecream",
                usage=usage,
            )
            return completion
        except Exception as e:
            print(f"Error during Writecream request: {e}")
            raise IOError(f"Writecream request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "Writecream"):
        self.completions = Completions(client)


class Writecream(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for Writecream API.

    Usage:
        client = Writecream()
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": "What is the capital of France?"}]
        )
        print(response.choices[0].message.content)
    """

    AVAILABLE_MODELS = ["writecream"]

    def __init__(self, browser: str = "chrome"):
        self.timeout = None
        self.base_url = "https://8pe3nv3qha.execute-api.us-east-1.amazonaws.com/default/llm_chat"
        self.session = requests.Session()
        agent = LitAgent()
        self.headers = {
            "User-Agent": agent.random(),
            "Referer": "https://www.writecream.com/chatgpt-chat/",
        }
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    def convert_model_name(self, model: str) -> str:
        return "writecream"

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


# Simple test if run directly
if __name__ == "__main__":
    client = Writecream()
    response = client.chat.completions.create(
        model="writecream",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"},
        ],
    )
    if isinstance(response, ChatCompletion):
        if not isinstance(response, Generator):
            message = response.choices[0].message
            print(message.content if message else "")
    else:
        print(response)
