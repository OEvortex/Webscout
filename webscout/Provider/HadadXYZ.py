"""HadadXYZ provider-style client.

This provider targets a HuggingFace Space-style endpoint that streams JSON objects
with items like `{type: 'reasoning-delta'|'text-delta', delta: '...'}`.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


class _DeltaExtractor:
    """Stateful extractor that merges `reasoning-delta` and `text-delta` into a single text stream.

    The upstream stream sends JSON objects of the shape:
        {"type": "reasoning-delta", "delta": "..."}
        {"type": "text-delta", "delta": "..."}

    When a reasoning section starts, it emits an opening `<think>` tag; when reasoning ends
    (first text-delta after reasoning), it emits `</think>`.
    """

    def __init__(self) -> None:
        self._in_reasoning = False

    def __call__(self, obj: Union[str, Dict[str, Any]]) -> Optional[str]:
        if not isinstance(obj, dict):
            return None

        t = obj.get("type")
        if t == "reasoning-delta":
            delta = obj.get("delta") or ""
            if not self._in_reasoning:
                self._in_reasoning = True
                return f"\n<think>\n{delta}"
            return delta

        if t == "text-delta":
            delta = obj.get("delta") or ""
            if self._in_reasoning:
                self._in_reasoning = False
                return f"\n</think>\n\n{delta}"
            return delta

        return None


class HadadXYZ(Provider):
    """A Webscout-style provider wrapper around the HadadXYZ HF Space endpoint."""

    required_auth = False

    DEFAULT_API_ENDPOINT = (
        "https://hadadxyz-ai.hf.space/api/"
        "aynzy5127hgsba5f3a9c2d1gduqb7e84fygd016c9a2d1f8b3c41gut432pjctr75"
        "hhspjae5d6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d7e2b4c9f83da4f1bb6c152"
        "f9e3c7a88d91f3c2b76513bpaneyx43vdaw074"
    )

    AVAILABLE_MODELS = [
        "deepseek-ai/deepseek-r1-0528",
        "deepseek-ai/deepseek-v3.2-thinking",
        "google/gemini-2.5-flash-lite-search",
        "google/gemini-2.5-flash-lite",
        "google/gemini-3-pro-preview",
        "minimaxai/minimax-m2",
        "mistralai/devstral-2-123b-instruct-2512",
        "mistralai/devstral-small-2-24b-instruct-2512",
        "mistralai/mistral-large-3-675b-instruct-2512",
        "moonshotai/kimi-k2-thinking",
        "nvidia/nvidia-nemotron-3-nano-30b-a3b",
        "nvidia/nvidia-nemotron-3-nano-30b-a3b-thinking",
        "openai/gpt-4.1-nano-2025-04-14",
        "openai",
        "openai-fast",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-safeguard-20b",
        "perplexity-fast",
        "qwen/qwen3-next-80b-a3b-thinking",
        "qwen/qwen3-vl-235b-a22b-instruct",
        "qwen/qwen3-vl-235b-a22b-thinking",
        "grok",
        "zai-org/glm-4.6",
        "anthropic/claude-opus-4-5-20251101",
        "anthropic/claude-sonnet-4-5-20250929",
        "anthropic/claude-haiku-4-5-20251001/legacy",
    ]

    def __init__(
        self,
        model: str = "deepseek-ai/deepseek-r1-0528",
        api_endpoint: str = DEFAULT_API_ENDPOINT,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 60,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: Optional[dict] = None,
        history_offset: int = 10250,
        act: Optional[str] = None,
        include_think_tags: bool = True,
    ) -> None:
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.api_endpoint = api_endpoint
        self.model = model
        self.timeout = timeout
        self.include_think_tags = include_think_tags

        self.session = Session()
        if proxies:
            if proxies:
                self.session.proxies.update(proxies)

        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
        }

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.last_response: Dict[str, Any] = {}

        self.__available_optimizers = [
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        ]

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = (
                AwesomePrompts().get_act(
                    cast(Union[str, int], act),
                    default=self.conversation.intro,
                    case_insensitive=True,
                )
                or self.conversation.intro
            )
        elif intro:
            self.conversation.intro = intro

    def _build_payload(self, prompt: str) -> Dict[str, Any]:
        return {
            "tools": {},
            "modelId": self.model,
            "sessionId": uuid.uuid4().hex,
            "clientId": uuid.uuid4().hex,
            "requestId": uuid.uuid4().hex,
            "id": "DEFAULT_THREAD_ID",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": prompt}],
                    "id": uuid.uuid4().hex,
                }
            ],
            "trigger": "submit-message",
            "metadata": {},
        }

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], Generator[Union[str, Dict[str, str]], None, None]]:
        """Send a prompt and return either a full response dict or a streaming generator."""

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        payload = self._build_payload(conversation_prompt)

        def for_stream():
            extractor = _DeltaExtractor()
            if not self.include_think_tags:

                def extractor_no_tags(obj: Union[str, Dict[str, Any]]) -> Optional[str]:
                    if isinstance(obj, dict) and obj.get("type") in {
                        "reasoning-delta",
                        "text-delta",
                    }:
                        return obj.get("delta") or ""
                    return None

                extractor = extractor_no_tags  # type: ignore[assignment]

            streaming_text = ""
            try:
                response = self.session.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome120",
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}) - {response.text}"
                    )

                processed_stream = sanitize_stream(
                    data=response.iter_lines(),
                    intro_value="data:",
                    to_json=True,
                    content_extractor=extractor,
                    yield_raw_on_error=False,
                    raw=raw,
                )

                for content_chunk in processed_stream:
                    if isinstance(content_chunk, bytes):
                        content_chunk = content_chunk.decode("utf-8", errors="ignore")

                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                            yield {"text": content_chunk}

                self.last_response = {"text": streaming_text}
                if streaming_text:
                    self.conversation.update_chat_history(prompt, streaming_text)

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed ({type(e).__name__}): {e}"
                ) from e

        def for_non_stream():
            full_text_parts = []
            for chunk in for_stream():
                if isinstance(chunk, dict):
                    full_text_parts.append(chunk.get("text", ""))
                else:
                    full_text_parts.append(str(chunk))
            full_text = "".join(full_text_parts)
            self.last_response = {"text": full_text}
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        raw = kwargs.get("raw", False)

        def for_stream_chat():
            for resp in self.ask(
                prompt,
                stream=True,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            ):
                if raw:
                    yield cast(str, resp)
                else:
                    yield self.get_message(cast(Dict[str, Any], resp))

        def for_non_stream_chat():
            resp = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, resp)
            return self.get_message(cast(Dict[str, Any], resp))

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return str(cast(Dict[str, Any], response).get("text", ""))


if __name__ == "__main__":
    from rich import print

    ai = HadadXYZ(model="deepseek-ai/deepseek-r1-0528")
    for chunk in ai.chat("how many r in strawberry", stream=True):
        print(chunk, end="", flush=True)
