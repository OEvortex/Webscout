import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout.litagent import LitAgent
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


class Completions(BaseCompletions):
    def __init__(self, client: "Blackbox"):
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
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        payload.update(kwargs)
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
        if proxies is not None:
            self._client.session.proxies.update(cast(Any, proxies))
        try:
            response = self._client.session.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                impersonate="chrome120",
            )
            response.raise_for_status()
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            for line in response.iter_lines():
                if line:
                    if isinstance(line, bytes):
                        line = line.decode("utf-8")
                    if line.startswith("data: "):
                        json_str = line[6:]
                        if json_str == "[DONE]":
                            break
                        try:
                            data = json.loads(json_str)
                            choices = data.get("choices")
                            if not choices and choices is not None:
                                continue
                            choice_data = choices[0] if choices else {}
                            delta_data = choice_data.get("delta", {})
                            finish_reason = choice_data.get("finish_reason")
                            usage_data = data.get("usage", {})
                            if usage_data:
                                prompt_tokens = usage_data.get("prompt_tokens", prompt_tokens)
                                completion_tokens = usage_data.get(
                                    "completion_tokens", completion_tokens
                                )
                                total_tokens = usage_data.get("total_tokens", total_tokens)
                            if delta_data.get("content"):
                                completion_tokens += 1
                                total_tokens = prompt_tokens + completion_tokens
                            delta = ChoiceDelta(
                                content=delta_data.get("content"),
                                role=delta_data.get("role"),
                                tool_calls=delta_data.get("tool_calls"),
                            )
                            choice = Choice(
                                index=choice_data.get("index", 0),
                                delta=delta,
                                finish_reason=finish_reason,
                                logprobs=choice_data.get("logprobs"),
                            )
                            chunk = ChatCompletionChunk(
                                id=request_id,
                                choices=[choice],
                                created=created_time,
                                model=model,
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
            print(f"Error during Blackbox stream request: {e}")
            raise IOError(f"Blackbox request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        if proxies is not None:
            self._client.session.proxies.update(cast(Any, proxies))
        try:
            response = self._client.session.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                timeout=timeout or self._client.timeout,
                impersonate="chrome120",
            )
            response.raise_for_status()
            data = response.json()
            choices_data = data.get("choices", [])
            usage_data = data.get("usage", {})
            choices = []
            for choice_d in choices_data:
                message_d = choice_d.get("message")
                if not message_d and "delta" in choice_d:
                    delta = choice_d["delta"]
                    message_d = {
                        "role": delta.get("role", "assistant"),
                        "content": delta.get("content", ""),
                    }
                if not message_d:
                    message_d = {"role": "assistant", "content": ""}
                message = ChatCompletionMessage(
                    role=message_d.get("role", "assistant"), content=message_d.get("content", "")
                )
                choice = Choice(
                    index=choice_d.get("index", 0),
                    message=message,
                    finish_reason=choice_d.get("finish_reason", "stop"),
                )
                choices.append(choice)
            usage = CompletionUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )
            completion = ChatCompletion(
                id=request_id,
                choices=choices,
                created=created_time,
                model=data.get("model", model),
                usage=usage,
            )
            return completion
        except Exception as e:
            print(f"Error during Blackbox non-stream request: {e}")
            raise IOError(f"Blackbox request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "Blackbox"):
        self.completions = Completions(client)


class Blackbox(OpenAICompatibleProvider):
    """
    Blackbox AI provider - OpenAI Compatible implementation.

    This provider mimics the OpenAI API structure to work with Blackbox AI's API endpoint.
    It supports both streaming and non-streaming responses.

    Example:
        >>> client = Blackbox()
        >>> response = client.chat.completions.create(
        ...     model="moonshotai/kimi-k2.5",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    required_auth = False
    AVAILABLE_MODELS = [
        "moonshotai/kimi-k2.5",
        "custom/blackbox-base-2",
        "minimax-m2",
    ]

    @classmethod
    def get_models(cls, api_key: Optional[str] = None):
        """Fetch available models from Blackbox API.

        Note: Blackbox API doesn't have a public models endpoint,
        so we return the default known models.

        Args:
            api_key: Optional API key (not used for Blackbox)

        Returns:
            list: List of available model IDs
        """
        return cls.AVAILABLE_MODELS

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: Optional[int] = 60,
        browser: str = "chrome",
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ):
        """Initialize Blackbox provider.

        Args:
            api_key: API key (optional, Blackbox may not require it)
            timeout: Request timeout in seconds
            browser: Browser type for fingerprint generation
            proxies: Optional proxy configuration
            **kwargs: Additional parameters
        """
        # Defer model fetch to background (non-blocking)
        self._start_background_model_fetch(api_key=api_key)

        self.timeout = timeout or 60
        self.base_url = "https://oi-vscode-server-985058387028.europe-west1.run.app/chat/completions"
        self.api_key = api_key

        # Initialize curl_cffi Session
        self.session = Session()

        # Generate browser fingerprint
        agent = LitAgent()
        fingerprint = agent.generate_fingerprint(browser)

        # Build headers
        self.headers = {
            "Accept": fingerprint["accept"],
            "Accept-Language": fingerprint["accept_language"],
            "Content-Type": "application/json",
            "User-Agent": fingerprint.get("user_agent", ""),
            "Sec-CH-UA": fingerprint.get("sec_ch_ua", ""),
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{fingerprint.get("platform", "")}"',
        }

        # Add API key if provided
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

        # Add required Blackbox headers
        self.headers["customerId"] = kwargs.get("customerId", "")
        self.headers["userId"] = kwargs.get("userId", "")
        self.headers["version"] = kwargs.get("version", "1.1")

        # Update session headers and proxies
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(cast(Any, proxies))

        # Initialize chat interface
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        """Returns available models."""
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    # Test the provider
    client = Blackbox()

    # Test streaming
    print("Testing streaming:")
    response = client.chat.completions.create(
        model="moonshotai/kimi-k2.5",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a python function that calculates the factorial of a number."}
        ],
        stream=True,
        max_tokens=500,
    )

    for chunk in response:
        if (
            isinstance(chunk, ChatCompletionChunk)
            and chunk.choices
            and chunk.choices[0].delta
            and chunk.choices[0].delta.content
        ):
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n")

    # Test non-streaming
    print("Testing non-streaming:")
    response = client.chat.completions.create(
        model="minimax-m2",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2 + 2?"}
        ],
        stream=False,
        max_tokens=100,
    )

    if isinstance(response, ChatCompletion):
        if (
            response.choices
            and response.choices[0].message
            and response.choices[0].message.content
        ):
            print(response.choices[0].message.content)
