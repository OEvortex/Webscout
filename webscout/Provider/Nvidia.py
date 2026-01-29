import json
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent
from webscout.model_fetcher import BackgroundModelFetcher


class Nvidia(Provider):
    """
    A class to interact with the Nvidia NIM API with LitAgent user-agent.
    Follows the DeepInfra standalone provider pattern.
    """

    required_auth = True
    AVAILABLE_MODELS = []
    # Background model fetcher
    _model_fetcher = BackgroundModelFetcher()

    @classmethod
    def get_models(cls, api_key: Optional[str] = None) -> list[str]:
        """Fetch available models from Nvidia API."""
        url = "https://integrate.api.nvidia.com/v1/models"
        try:
            temp_session = Session()
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            response = temp_session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    return [model["id"] for model in data["data"] if "id" in model]
            return cls.AVAILABLE_MODELS
        except Exception:
            return cls.AVAILABLE_MODELS

    @classmethod
    def update_available_models(cls, api_key: Optional[str] = None):
        """Update the available models list from Nvidia API dynamically."""
        try:
            models = cls.get_models(api_key)
            if models and len(models) > 0:
                cls.AVAILABLE_MODELS = models
        except Exception:
            pass

    def __init__(
        self,
        api_key: str,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "meta/llama-3.3-70b-instruct",
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        top_p: float = 0.9,
        browser: str = "chrome",
    ):
        """Initializes the Nvidia API client."""
        # Start background model fetch (non-blocking)
        self._model_fetcher.fetch_async(
            provider_name="Nvidia",
            fetch_func=lambda: self.get_models(api_key),
            fallback_models=self.AVAILABLE_MODELS,
            timeout=10,
        )

        self.url = "https://integrate.api.nvidia.com/v1/chat/completions"

        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.api = api_key
        self.headers = {
            "Accept": "application/json",
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api}",
            "User-Agent": self.fingerprint.get("user_agent", ""),
        }

        self.session = Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

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

    def refresh_identity(self, browser: Optional[str] = None):
        """Refreshes the browser identity fingerprint."""
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.session.headers.update({"User-Agent": self.fingerprint.get("user_agent", "")})
        return self.fingerprint

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """
        Sends a prompt to the Nvidia API and returns the response.
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream,
            "max_tokens": self.max_tokens_to_sample,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

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
                    content_extractor=lambda x: x.get("choices", [{}])[0]
                    .get("delta", {})
                    .get("content")
                    if isinstance(x, dict)
                    else None,
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
                content = content if isinstance(content, str) else ""

                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return self.last_response

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
        """Generates a chat response from the Nvidia API."""
        raw = kwargs.get("raw", False)
        if stream:

            def for_stream_chat():
                gen = self.ask(
                    prompt,
                    stream=True,
                    raw=raw,
                    optimizer=optimizer,
                    conversationally=conversationally,
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
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    # nv = Nvidia(api_key="your_nv_api_key")
    # for chunk in nv.chat("Hi!", stream=True):
    #     print(chunk, end="", flush=True)
    pass
