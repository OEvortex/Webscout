"""
Gradient Network Chat API Provider
Reverse engineered from https://chat.gradient.network/
"""

from typing import Any, Dict, Generator, Optional, Union, cast

import requests

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


class Gradient(Provider):
    """
    Provider for Gradient Network chat API
    Supports real-time streaming responses from distributed GPU clusters

    Note: GPT OSS 120B works on "nvidia" cluster, Qwen3 235B works on "hybrid" cluster
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
        model: str = "GPT OSS 120B",
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 60,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: Optional[dict] = None,
        history_offset: int = 10250,
        act: Optional[str] = None,
        system_prompt: str = "You are a helpful assistant.",
        cluster_mode: Optional[str] = None,  # Auto-detected based on model if None
        enable_thinking: bool = True,
    ):
        # Normalize model name (convert dashes to spaces)
        model = model.replace("-", " ")
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.model = model
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.proxies = proxies
        self.system_prompt = system_prompt
        # Auto-detect cluster mode based on model if not specified
        self.cluster_mode = cluster_mode or self.MODEL_CLUSTERS.get(model, "nvidia")
        self.enable_thinking = enable_thinking
        self.last_response = {}

        self.session = requests.Session()
        if proxies:
            self.session.proxies.update(proxies)

        # Headers matching the working curl request
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

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        # Conversation setup
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        act_prompt = (
            AwesomePrompts().get_act(cast(Union[str, int], act), default=None, case_insensitive=True
            )
            if act
            else intro
        )
        if act_prompt:
            self.conversation.intro = act_prompt

    @staticmethod
    def _gradient_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """
        Extracts content from Gradient API stream response.

        The API returns JSON objects like:
        {"type": "reply", "data": {"role": "assistant", "content": "text"}}
        {"type": "reply", "data": {"role": "assistant", "reasoningContent": "text"}}

        Args:
            chunk: Parsed JSON dict from the stream

        Returns:
            Extracted content string or None
        """
        if isinstance(chunk, dict):
            chunk_type = chunk.get("type")
            if chunk_type == "reply":
                data = cast(Dict[str, Any], chunk.get("data", {}))
                # Prefer "content" over "reasoningContent"
                content = data.get("content") or data.get("reasoningContent")
                if content:
                    return content
        return None

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": conversation_prompt},
        ]

        payload = {
            "model": self.model,
            "clusterMode": self.cluster_mode,
            "messages": messages,
            "enableThinking": self.enable_thinking,
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    "https://chat.gradient.network/api/generate",
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                # Use sanitize_stream for processing
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value=None,  # No prefix to remove
                    to_json=True,  # Parse as JSON
                    skip_markers=[],
                    content_extractor=self._gradient_extractor,
                    yield_raw_on_error=False,
                    raw=raw
                )

                for content_chunk in processed_stream:
                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                        yield {"text": content_chunk}

            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}") from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed ({type(e).__name__}): {str(e)}") from e
            finally:
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            try:
                full_response = ""
                for chunk in for_stream():
                    content = self.get_message(chunk) if not raw else chunk
                    if isinstance(content, str):
                        full_response += content

                self.last_response = {"text": full_response}
                self.conversation.update_chat_history(prompt, full_response)
                return self.last_response if not raw else full_response

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed ({type(e).__name__}): {str(e)}") from e

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")

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
            gen = self.ask(
                prompt, stream=True, raw=raw,
                optimizer=optimizer, conversationally=conversationally
            )
            for response_dict in gen:
                if raw:
                    yield response_dict
                else:
                    yield self.get_message(cast(Dict[str, Any], response_dict))

        def for_non_stream_chat():
            response_data = self.ask(
                prompt, stream=False, raw=raw,
                optimizer=optimizer, conversationally=conversationally
            )
            if raw:
                return cast(str, response_data)
            else:
                return self.get_message(cast(Dict[str, Any], response_data))

        return for_stream_chat() if stream else for_non_stream_chat()


if __name__ == "__main__":
    gradient = Gradient(model="GPT OSS 120B", is_conversation=True)
    response = gradient.chat("Hello, how are you?", stream=False, raw=True)
    print(response)
