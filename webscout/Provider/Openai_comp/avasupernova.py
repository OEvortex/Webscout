from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import requests

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
    count_tokens,
)


class Completions(BaseCompletions):
    """Handles chat completion requests for Ava Supernova."""

    def __init__(self, client: "AvaSupernova"):
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
        tools: Optional[List[Union[Dict[str, Any], Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "stream_options": {"include_usage": True},
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if tools:
            payload["tools"] = self.format_tool_calls(tools)
        if tool_choice:
            payload["tool_choice"] = tool_choice
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
        try:
            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),
            )

            # Some response mocks may not have `.ok`; fallback to status_code.
            response_ok = getattr(response, "ok", None)
            if response_ok is False or (response_ok is None and getattr(response, "status_code", 0) >= 400):
                raise IOError(
                    f"Failed to generate response - ({getattr(response, 'status_code', 'N/A')}, {getattr(response, 'reason', 'N/A')}) - {getattr(response, 'text', '')}"
                )

            prompt_tokens = count_tokens([msg.get("content", "") for msg in payload.get("messages", [])])
            completion_tokens = 0
            total_tokens = 0

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
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

                        content = delta_data.get("content")
                        if content:
                            completion_tokens += count_tokens(content)
                            total_tokens = prompt_tokens + completion_tokens

                        delta = ChoiceDelta(
                            content=content,
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
            raise IOError(f"AvaSupernova stream request failed: {e}") from e

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
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),
            )

            # Some response mocks may not have `.ok`; fallback to status_code.
            response_ok = getattr(response, "ok", None)
            if response_ok is False or (response_ok is None and getattr(response, "status_code", 0) >= 400):
                raise IOError(
                    f"Failed to generate response - ({getattr(response, 'status_code', 'N/A')}, {getattr(response, 'reason', 'N/A')}) - {getattr(response, 'text', '')}"
                )

            data = response.json()
            choices_data = data.get("choices", [])
            usage_data = data.get("usage", {})
            choices: List[Choice] = []

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
                    role=message_d.get("role", "assistant"),
                    content=message_d.get("content", ""),
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
            raise IOError(f"AvaSupernova request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "AvaSupernova"):
        self.completions = Completions(client)


class AvaSupernova(OpenAICompatibleProvider):
    """Ava Supernova OpenAI-compatible provider."""

    required_auth = False
    AVAILABLE_MODELS = ["glm-4.7-flash", "glm-4.5-flash"]

    @classmethod
    def get_models(cls, api_key: Optional[str] = None) -> List[str]:
        return cls.AVAILABLE_MODELS

    def __init__(self, timeout: int = 30, proxies: dict = {}):
        self.timeout = timeout
        self.api_endpoint = "https://ava-supernova.com/api/v1/free/chat"
        self.proxies = proxies

        self.session = requests.Session()
        if proxies:
            self.session.proxies.update(cast(Any, proxies))

        agent = LitAgent()
        self.user_agent = agent.random()

        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
        }

        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    @classmethod
    def update_available_models(cls, api_key: Optional[str] = None):
        models = cls.get_models(api_key)
        if models:
            cls.AVAILABLE_MODELS = models

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    client = AvaSupernova()
    response = client.chat.completions.create(
        model="glm-4.7-flash",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=1000,
        stream=True,
    )
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta:
                print(chunk.choices[0].delta.content, end="")
    else:
        print(response)
