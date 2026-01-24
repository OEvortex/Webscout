"""
Gradient Network OpenAI-compatible Provider
Reverse engineered from https://chat.gradient.network/

Provides OpenAI-compatible API interface for Gradient Network's distributed GPU clusters.
"""

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
    count_tokens,
)

# ANSI escape codes for formatting
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"


class Completions(BaseCompletions):
    """Handles chat completions for Gradient Network."""

    def __init__(self, client: "Gradient"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 2048,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        enable_thinking: Optional[bool] = None,
        cluster_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create

        Args:
            model: The model to use for completion
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate (not used by Gradient API)
            stream: Whether to stream the response
            temperature: Sampling temperature (not used by Gradient API)
            top_p: Top-p sampling (not used by Gradient API)
            timeout: Request timeout in seconds
            proxies: Proxy configuration
            enable_thinking: Enable thinking/reasoning mode (default: client setting)
            cluster_mode: GPU cluster mode (auto-detected based on model if None)
            **kwargs: Additional arguments

        Returns:
            ChatCompletion or Generator[ChatCompletionChunk] depending on stream
        """
        # Convert model name and get appropriate cluster mode
        converted_model = self._client.convert_model_name(model)
        actual_cluster_mode = cluster_mode or self._client.MODEL_CLUSTERS.get(
            converted_model, self._client.cluster_mode
        )

        # Build the payload - pass messages directly as the API accepts them
        payload = {
            "model": converted_model,
            "clusterMode": actual_cluster_mode,
            "messages": messages,
            "enableThinking": enable_thinking
            if enable_thinking is not None
            else self._client.enable_thinking,
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
        """Handle streaming response from Gradient API."""
        try:
            response = self._client.session.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or self._client.proxies or None,
            )
            response.raise_for_status()

            completion_tokens = 0
            prompt_tokens = count_tokens(str(payload.get("messages", [])))
            first_chunk = True

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    # Decode bytes to string
                    decoded_line = line.decode("utf-8") if isinstance(line, bytes) else line
                    decoded_line = decoded_line.strip()
                    if not decoded_line:
                        continue

                    # Parse JSON response
                    data = json.loads(decoded_line)

                    # Only process "reply" type chunks
                    chunk_type = data.get("type")
                    if chunk_type != "reply":
                        continue

                    # Extract content - prefer "content" over "reasoningContent"
                    reply_data = data.get("data", {})
                    content = reply_data.get("content") or reply_data.get("reasoningContent")

                    if content:
                        completion_tokens += count_tokens(content)

                        delta = ChoiceDelta(
                            content=content, role="assistant" if first_chunk else None
                        )
                        first_chunk = False

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
                            "total_tokens": prompt_tokens + completion_tokens,
                            "estimated_cost": None,
                        }
                        yield chunk

                except json.JSONDecodeError:
                    continue
                except Exception:
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
                "total_tokens": prompt_tokens + completion_tokens,
                "estimated_cost": None,
            }
            yield chunk

        except requests.exceptions.RequestException as e:
            print(f"{RED}Error during Gradient stream request: {e}{RESET}")
            raise IOError(f"Gradient request failed: {e}") from e
        except Exception as e:
            print(f"{RED}Error during Gradient stream request: {type(e).__name__}: {e}{RESET}")
            raise IOError(f"Gradient request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        """Handle non-streaming response from Gradient API."""
        try:
            # Collect all chunks from streaming
            full_content = ""
            prompt_tokens = count_tokens(str(payload.get("messages", [])))

            response = self._client.session.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or self._client.proxies or None,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    # Decode bytes to string
                    decoded_line = line.decode("utf-8") if isinstance(line, bytes) else line
                    decoded_line = decoded_line.strip()
                    if not decoded_line:
                        continue

                    data = json.loads(decoded_line)

                    # Only process "reply" type chunks
                    chunk_type = data.get("type")
                    if chunk_type != "reply":
                        continue

                    reply_data = data.get("data", {})
                    # Prefer "content" over "reasoningContent"
                    content = reply_data.get("content") or reply_data.get("reasoningContent")
                    if content:
                        full_content += content

                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

            completion_tokens = count_tokens(full_content)
            total_tokens = prompt_tokens + completion_tokens

            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            message = ChatCompletionMessage(role="assistant", content=full_content)

            choice = Choice(index=0, message=message, finish_reason="stop")

            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )

            return completion

        except requests.exceptions.RequestException as e:
            print(f"{RED}Error during Gradient non-stream request: {e}{RESET}")
            raise IOError(f"Gradient request failed: {e}") from e
        except Exception as e:
            print(f"{RED}Error during Gradient non-stream request: {type(e).__name__}: {e}{RESET}")
            raise IOError(f"Gradient request failed: {e}") from e


class Chat(BaseChat):
    """Chat interface for Gradient Network."""

    def __init__(self, client: "Gradient"):
        self.completions = Completions(client)


class Gradient(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for Gradient Network API.

    Gradient Network provides access to distributed GPU clusters running large language models.
    This provider supports real-time streaming responses.

    Note: GPT OSS 120B works on "nvidia" cluster, Qwen3 235B works on "hybrid" cluster.
    Cluster mode is auto-detected based on model selection.

    Usage:
        client = Gradient()
        response = client.chat.completions.create(
            model="GPT OSS 120B",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)

        # Streaming
        for chunk in client.chat.completions.create(
            model="Qwen3 235B",
            messages=[{"role": "user", "content": "Tell me a story"}],
            stream=True
        ):
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
    """

    required_auth = False

    AVAILABLE_MODELS = [
        "GPT OSS 120B",
        "Qwen3 235B",
    ]

    # Model to cluster mapping
    MODEL_CLUSTERS = {
        "GPT OSS 120B": "nvidia",
        "Qwen3 235B": "hybrid",
    }

    def __init__(
        self,
        timeout: int = 60,
        cluster_mode: str = "nvidia",
        enable_thinking: bool = True,
        proxies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the Gradient client.

        Args:
            timeout: Request timeout in seconds (default: 60)
            cluster_mode: Default GPU cluster mode (default: "nvidia", auto-detected per model)
            enable_thinking: Enable thinking/reasoning mode (default: True)
            proxies: Optional proxy configuration
        """
        self.timeout = timeout
        self.cluster_mode = cluster_mode
        self.enable_thinking = enable_thinking
        self.proxies = proxies or {}

        self.base_url = "https://chat.gradient.network/api/generate"
        self.session = requests.Session()

        # Set up headers matching the curl request
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://chat.gradient.network",
            "priority": "u=1, i",
            "referer": "https://chat.gradient.network/",
            "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
        }

        self.session.headers.update(self.headers)

        # Initialize the chat interface
        self.chat = Chat(self)

    def convert_model_name(self, model: str) -> str:
        """
        Ensure the model name is in the correct format.

        Args:
            model: Model name to convert

        Returns:
            Valid model name
        """
        if model in self.AVAILABLE_MODELS:
            return model

        # Try case-insensitive matching with dash to space conversion
        model_lower = model.lower().replace("-", " ")
        for available_model in self.AVAILABLE_MODELS:
            if model_lower == available_model.lower():
                return available_model

        # Default to first available model
        print(
            f"{BOLD}Warning: Model '{model}' not found, using default model '{self.AVAILABLE_MODELS[0]}'{RESET}"
        )
        return self.AVAILABLE_MODELS[0]

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in Gradient.AVAILABLE_MODELS:
        try:
            client = Gradient(timeout=120)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Say 'Hello' in one word"},
                ],
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
            print(f"{model:<50} {'✗':<10} {str(e)[:50]}")
