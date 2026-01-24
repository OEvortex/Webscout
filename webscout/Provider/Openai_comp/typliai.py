"""
TypliAI OpenAI-compatible provider.
"""

import random
import string
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi.requests import Session

from webscout.AIutel import sanitize_stream
from webscout.Provider.Openai_comp.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from webscout.Provider.Openai_comp.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    format_prompt,
)

try:
    from ...litagent import LitAgent
except ImportError:
    LitAgent = None  # type: ignore


def generate_random_id(length=16):
    """Generates a random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for i in range(length))


class Completions(BaseCompletions):
    def __init__(self, client: "TypliAI"):
        self._client = client

    def create(
        self,
        *,
        model: str = "openai/gpt-4.1-mini",
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        """
        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        # Use format_prompt from utils
        prompt = format_prompt(messages)

        if stream:
            return self._create_stream(request_id, created_time, model, prompt, timeout, proxies)
        else:
            return self._create_non_stream(
                request_id, created_time, model, prompt, timeout, proxies
            )

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        prompt: str,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Implementation for streaming chat completions."""
        try:
            payload = {
                "slug": "free-no-sign-up-chatgpt",
                "modelId": model,
                "id": generate_random_id(),
                "messages": [
                    {
                        "id": generate_random_id(),
                        "role": "user",
                        "parts": [{"type": "text", "text": prompt}],
                    }
                ],
                "trigger": "submit-message",
            }

            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                impersonate="chrome120",
                proxies=proxies or self._client.proxies,
            )

            if not response.ok:
                raise IOError(f"TypliAI request failed: {response.status_code} - {response.text}")

            full_response = ""
            completion_tokens = 0

            # Use chunks from iter_content
            data_generator = response.iter_content(chunk_size=None)

            processed_stream = sanitize_stream(
                data=data_generator,
                intro_value="data: ",
                to_json=True,
                content_extractor=lambda x: x.get("delta")
                if isinstance(x, dict) and x.get("type") == "text-delta"
                else None,
                skip_markers=["[DONE]"],
            )

            for content in processed_stream:
                if content and isinstance(content, str):
                    full_response += content
                    completion_tokens += 1

                    delta = ChoiceDelta(
                        content=content, role="assistant" if completion_tokens == 1 else None
                    )
                    choice = Choice(index=0, delta=delta, finish_reason=None)
                    chunk = ChatCompletionChunk(
                        id=request_id, choices=[choice], created=created_time, model=model
                    )
                    yield chunk

            # Final chunk
            choice = Choice(index=0, delta=ChoiceDelta(content=None), finish_reason="stop")
            yield ChatCompletionChunk(
                id=request_id, choices=[choice], created=created_time, model=model
            )

        except Exception as e:
            raise IOError(f"TypliAI stream request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        prompt: str,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        """Implementation for non-streaming chat completions."""
        full_content = ""
        for chunk in self._create_stream(request_id, created_time, model, prompt, timeout, proxies):
            if chunk.choices[0].delta and chunk.choices[0].delta.content:
                full_content += chunk.choices[0].delta.content

        message = ChatCompletionMessage(role="assistant", content=full_content)
        choice = Choice(index=0, message=message, finish_reason="stop")
        usage = CompletionUsage(
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(full_content.split()),
            total_tokens=len(prompt.split()) + len(full_content.split()),
        )

        return ChatCompletion(
            id=request_id, choices=[choice], created=created_time, model=model, usage=usage
        )


class Chat(BaseChat):
    def __init__(self, client: "TypliAI"):
        self.completions = Completions(client)


class TypliAI(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for TypliAI.
    """

    required_auth = False

    AVAILABLE_MODELS = [
        "openai/gpt-4.1-mini",
        "openai/gpt-4.1",
        "openai/gpt-5-mini",
        "openai/gpt-5.2",
        "openai/gpt-5.2-pro",
        "google/gemini-2.5-flash",
        "anthropic/claude-haiku-4-5",
        "xai/grok-4-fast-reasoning",
        "xai/grok-4-fast",
    ]

    def __init__(self, timeout: int = 60, proxies: Optional[dict] = None, browser: str = "chrome"):
        self.timeout = timeout
        self.proxies = proxies or {}
        self.api_endpoint = "https://typli.ai/api/generators/chat"

        self.session = Session()
        self.agent = LitAgent() if LitAgent else None
        user_agent = (
            self.agent.random()
            if self.agent
            else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        self.headers = {
            "accept": "/",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://typli.ai",
            "priority": "u=1, i",
            "referer": "https://typli.ai/free-no-sign-up-chatgpt",
            "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": user_agent,
        }

        self.session.headers.update(self.headers)
        if proxies:
            if proxies:
                self.session.proxies.update(cast(Any, proxies))

        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    client = TypliAI()
    print(f"Available models: {client.models.list()}")

    # Test non-streaming
    print("\n=== Testing Non-Streaming ===")
    response = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "Hello! How are you?"}],
        stream=False,
    )
    if isinstance(response, ChatCompletion):
        if response.choices[0].message and response.choices[0].message.content:
            print(f"Response: {response.choices[0].message.content}")
    else:
        print(f"Response: {response}")

    # Test streaming
    print("\n=== Testing Streaming ===")
    stream_resp = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "Tell me a joke"}],
        stream=True,
    )
    if hasattr(stream_resp, "__iter__") and not isinstance(
        stream_resp, (str, bytes, ChatCompletion)
    ):
        for chunk in cast(Generator[ChatCompletionChunk, None, None], stream_resp):
            if chunk.choices[0].delta and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
    else:
        print(stream_resp)
    print()
