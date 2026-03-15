import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent
from webscout.model_fetcher import BackgroundModelFetcher


class AvaSupernova(Provider):
    """A provider for the Ava Supernova free chat API.

    The API is OpenAI-like and supports SSE streaming with the OpenAI SSE format.

    Example request:
      curl -N "https://ava-supernova.com/api/v1/free/chat" \
        -H "Content-Type: application/json" \
        -d '{"model":"glm-4.7-flash","messages":[{"role":"system","content":"You are a helpful coding assistant."},{"role":"user","content":"Hello!"}],"stream":true,"stream_options":{"include_usage":true}}'
    """

    required_auth = False
    AVAILABLE_MODELS = ["glm-4.7-flash", "glm-4.5-flash"]

    # Background model fetcher (no real endpoint, but keep pattern consistent)
    _model_fetcher = BackgroundModelFetcher()

    @classmethod
    def get_models(cls, api_key: Optional[str] = None):
        """Fetch available models for Ava Supernova."""
        # Ava Supernova does not expose a public model list endpoint (as of this implementation),
        # so we return a static list.
        return cls.AVAILABLE_MODELS

    @staticmethod
    def _openai_sse_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extract the assistant content from OpenAI-style SSE streaming chunks."""
        if isinstance(chunk, dict):
            return chunk.get("choices", [{}])[0].get("delta", {}).get("content")
        return None

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        temperature: float = 1,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "glm-4.7-flash",
        system_prompt: str = "You are a helpful coding assistant.",
        browser: str = "chrome",
    ):
        """Initializes the Ava Supernova client."""

        # Start background model fetch (non-blocking)
        self._model_fetcher.fetch_async(
            provider_name="AvaSupernova",
            fetch_func=lambda: self.get_models(None),
            fallback_models=self.AVAILABLE_MODELS,
            timeout=10,
        )

        self.url = "https://ava-supernova.com/api/v1/free/chat"

        # Setup headers with browser fingerprint
        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)

        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": self.fingerprint.get("user_agent", ""),
        }

        self.session = Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p
        self.timeout = timeout
        self.last_response = {}
        self.model = model

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = AwesomePrompts().get_act(
                cast(Union[str, int], act),
                default=self.conversation.intro,
                case_insensitive=True,
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """Send a prompt to Ava Supernova API."""
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

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.conversation.intro},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream,
            "stream_options": {"include_usage": True},
            "max_tokens": self.max_tokens_to_sample,
            "temperature": self.temperature,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "top_p": self.top_p,
        }
        payload.update(kwargs)

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                response.raise_for_status()

                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=self._openai_sse_extractor,
                    yield_raw_on_error=False,
                    raw=raw,
                )

                for content_chunk in processed_stream:
                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                            yield dict(text=content_chunk)

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {str(e)}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed ({type(e).__name__}): {str(e)}"
                ) from e
            finally:
                if not raw and streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            try:
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                response.raise_for_status()

                if raw:
                    return response.text

                # Parse JSON response
                processed_stream = sanitize_stream(
                    data=response.text,
                    to_json=True,
                    intro_value=None,
                    content_extractor=lambda chunk: chunk.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content")
                    if isinstance(chunk, dict)
                    else None,
                    yield_raw_on_error=False,
                    raw=raw,
                )
                content = next(processed_stream, None)
                if raw:
                    return content
                content = content if isinstance(content, str) else ""

                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return self.last_response if not raw else content

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                err_text = ""
                if hasattr(e, "response"):
                    response_obj = getattr(e, "response")
                    if hasattr(response_obj, "text"):
                        err_text = getattr(response_obj, "text")
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed ({type(e).__name__}): {e} - {err_text}"
                ) from e

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
        if stream:
            def for_stream_chat():
                gen = self.ask(
                    prompt, stream=True, raw=raw, optimizer=optimizer, conversationally=conversationally
                )
                if hasattr(gen, "__iter__"):
                    for response in gen:
                        if raw:
                            yield cast(str, response)
                        else:
                            yield self.get_message(response)

            return for_stream_chat()
        else:
            result = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, result)
            else:
                return self.get_message(result)

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        text = response.get("text")
        return cast(str, text) if text else ""


if __name__ == "__main__":
    ai = AvaSupernova()
    response = ai.chat("Hello", raw=False, stream=True)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="")
    else:
        print(response)
