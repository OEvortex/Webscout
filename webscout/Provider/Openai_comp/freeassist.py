import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

import requests

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
)

from ...litagent import LitAgent


class Completions(BaseCompletions):
    def __init__(self, client: "FreeAssist"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 4096,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Create a chat completion with FreeAssist API.

        Args:
            model: Model identifier (e.g., 'google/gemini-2.5-flash-lite')
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens (not used by API but kept for interface)
            stream: Whether to stream the response
            temperature: Sampling temperature (not used by API)
            top_p: Nucleus sampling (not used by API)
            timeout: Request timeout
            proxies: Proxy configuration
            **kwargs: Additional parameters

        Returns:
            ChatCompletion or Generator of ChatCompletionChunk
        """
        payload = {
            "messages": messages,
            "model": model,
            "anonymousUserId": str(uuid.uuid4()),
            "isContinuation": False,
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
        """Handle streaming response from FreeAssist API."""
        try:
            response = self._client.session.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies,
            )
            response.raise_for_status()

            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                if isinstance(line, bytes):
                    try:
                        line = line.decode("utf-8")
                    except Exception:
                        continue

                if line.startswith("data: "):
                    json_str = line[6:]
                else:
                    json_str = line

                if json_str == "[DONE]":
                    break

                try:
                    data = json.loads(json_str)

                    # Extract usage if present
                    usage_data = data.get("usage", {})
                    if usage_data:
                        prompt_tokens = usage_data.get("prompt_tokens", prompt_tokens)
                        completion_tokens = usage_data.get("completion_tokens", completion_tokens)
                        total_tokens = usage_data.get("total_tokens", total_tokens)

                    choices = data.get("choices")
                    if not choices and choices is not None:
                        continue

                    choice_data = choices[0] if choices else {}
                    delta_data = choice_data.get("delta", {})
                    finish_reason = choice_data.get("finish_reason")

                    # Get content
                    content_piece = None
                    role = None
                    tool_calls = None

                    if delta_data:
                        content_piece = delta_data.get("content")
                        role = delta_data.get("role")
                        tool_calls = delta_data.get("tool_calls")
                    else:
                        message_d = choice_data.get("message", {})
                        role = message_d.get("role")
                        content_piece = message_d.get("content")
                        tool_calls = message_d.get("tool_calls")

                    if content_piece and not usage_data:
                        completion_tokens += 1
                        total_tokens = prompt_tokens + completion_tokens

                    delta = ChoiceDelta(content=content_piece, role=role, tool_calls=tool_calls)

                    choice = Choice(
                        index=choice_data.get("index", 0),
                        delta=delta,
                        finish_reason=finish_reason,
                        logprobs=choice_data.get("logprobs"),
                    )

                    chunk = ChatCompletionChunk(
                        id=data.get("id", request_id),
                        choices=[choice],
                        created=data.get("created", created_time),
                        model=data.get("model", model),
                        system_fingerprint=data.get("system_fingerprint"),
                    )

                    chunk.usage = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                        "estimated_cost": None,
                    }

                    yield chunk

                except json.JSONDecodeError:
                    continue

            # Final chunk with finish_reason="stop"
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
            print(f"Error during FreeAssist stream request: {e}")
            raise IOError(f"FreeAssist request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        """Handle non-streaming response from FreeAssist API (collects SSE stream)."""
        try:
            # FreeAssist always returns SSE format, so we stream and aggregate
            response = self._client.session.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies,
            )
            response.raise_for_status()

            full_content = ""
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            response_model = model

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                if isinstance(line, bytes):
                    try:
                        line = line.decode("utf-8")
                    except Exception:
                        continue

                if line.startswith("data: "):
                    json_str = line[6:]
                else:
                    json_str = line

                if json_str == "[DONE]":
                    break

                try:
                    data = json.loads(json_str)

                    # Extract usage if present
                    usage_data = data.get("usage", {})
                    if usage_data:
                        prompt_tokens = usage_data.get("prompt_tokens", prompt_tokens)
                        completion_tokens = usage_data.get("completion_tokens", completion_tokens)
                        total_tokens = usage_data.get("total_tokens", total_tokens)

                    choices = data.get("choices")
                    if not choices and choices is not None:
                        continue

                    choice_data = choices[0] if choices else {}
                    delta_data = choice_data.get("delta", {})
                    content = delta_data.get("content", "")

                    if content:
                        full_content += content

                    # Get model from response
                    if data.get("model"):
                        response_model = data.get("model")
                except json.JSONDecodeError:
                    continue

            message = ChatCompletionMessage(role="assistant", content=full_content)

            choice = Choice(index=0, message=message, finish_reason="stop")

            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=response_model,
                usage=usage,
            )

            return completion

        except Exception as e:
            print(f"Error during FreeAssist non-stream request: {e}")
            raise IOError(f"FreeAssist request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "FreeAssist"):
        self.completions = Completions(client)


class FreeAssist(OpenAICompatibleProvider):
    """
    FreeAssist - A free OpenAI-compatible provider using FreeAssist.ai

    This provider uses the FreeAssist API which provides access to various
    AI models including Google's Gemini series.

    Usage:
        from webscout.Provider.Openai_comp import FreeAssist

        client = FreeAssist()

        # Streaming
        for chunk in client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[{"role": "user", "content": "Hello!"}],
            stream=True
        ):
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)

        # Non-streaming
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[{"role": "user", "content": "Hello!"}],
            stream=False
        )
        print(response.choices[0].message.content)
    """

    AVAILABLE_MODELS = [
        "google/gemini-2.5-flash-lite",
        "google/gemini-2.5-flash",
        "openai/gpt-5-nano",
        "openai/gpt-5-mini",
    ]

    def __init__(
        self, browser: str = "chrome", timeout: int = 60, proxies: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the FreeAssist provider.

        Args:
            browser: Browser to impersonate for fingerprinting
            timeout: Request timeout in seconds
            proxies: Optional proxy configuration
        """
        self.timeout = timeout
        self.base_url = "https://qcpujeurnkbvwlvmylyx.supabase.co/functions/v1/chat"
        self.session = requests.Session()

        agent = LitAgent()
        fingerprint = agent.generate_fingerprint(browser)

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://freeassist.ai",
            "referer": "https://freeassist.ai/",
            "sec-ch-ua": fingerprint.get(
                "sec_ch_ua", '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"'
            ),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": f'"{fingerprint.get("platform", "Windows")}"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sec-gpc": "1",
            "user-agent": fingerprint.get(
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            ),
        }

        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(cast(Any, proxies))

        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print("Testing FreeAssist Provider")
    print("-" * 80)

    client = FreeAssist()

    # Test streaming
    print("\n[Streaming Test]")
    try:
        response_text = ""
        for chunk in client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[{"role": "user", "content": "Say 'Hello' in one word"}],
            stream=True,
        ):
            if (
                isinstance(chunk, ChatCompletionChunk)
                and chunk.choices[0].delta
                and chunk.choices[0].delta.content
            ):
                content = chunk.choices[0].delta.content
                response_text += content
                print(content, end="", flush=True)
        print(f"\n✓ Streaming works! Response: {response_text}")
    except Exception as e:
        print(f"✗ Streaming failed: {e}")

    # Test non-streaming
    print("\n[Non-Streaming Test]")
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[{"role": "user", "content": "Say 'World' in one word"}],
            stream=False,
        )
        if (
            isinstance(response, ChatCompletion)
            and response.choices
            and response.choices[0].message
            and response.choices[0].message.content
        ):
            print(f"✓ Non-streaming works! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"✗ Non-streaming failed: {e}")

    print("\n" + "-" * 80)
    print("Available models:", FreeAssist.AVAILABLE_MODELS)
