import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent


class DeepInfra(Provider):
    """
    A class to interact with the DeepInfra API with LitAgent user-agent.
    """

    required_auth = False
    # Default models list (will be updated dynamically)
    AVAILABLE_MODELS = [
        "moonshotai/Kimi-K2-Instruct",
        "moonshotai/Kimi-K2-Thinking",
        "MiniMaxAI/MiniMax-M2",
        "Qwen/Qwen3-Next-80B-A3B-Instruct",
        "Qwen/Qwen3-Next-80B-A3B-Thinking",
        "moonshotai/Kimi-K2-Instruct-0905",
        "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "deepseek-ai/DeepSeek-R1-0528-Turbo",
        "Qwen/Qwen3-235B-A22B-Thinking-2507",
        "deepseek-ai/DeepSeek-V3.1-Terminus",
        "deepseek-ai/DeepSeek-V3.2-Exp",
        "Qwen/Qwen3-Coder-480B-A35B-Instruct",
        "Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo",
        "Qwen/Qwen3-235B-A22B-Instruct-2507",
        "Qwen/Qwen3-235B-A22B",
        "Qwen/Qwen3-30B-A3B",
        "Qwen/Qwen3-32B",
        "Qwen/Qwen3-14B",
        "deepseek-ai/DeepSeek-V3-0324-Turbo",
        "deepseek-ai/DeepSeek-Prover-V2-671B",
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-Turbo",
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "deepseek-ai/DeepSeek-R1-0528",
        "deepseek-ai/DeepSeek-V3-0324",
        "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
        "microsoft/phi-4-reasoning-plus",
        "Qwen/QwQ-32B",
        "google/gemma-3-27b-it",
        "google/gemma-3-12b-it",
        "google/gemma-3-4b-it",
        "microsoft/Phi-4-multimodal-instruct",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-V3.1",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "meta-llama/Llama-3.3-70B-Instruct",
        "microsoft/phi-4",
        "Gryphe/MythoMax-L2-13b",
        "NousResearch/Hermes-3-Llama-3.1-405B",
        "NousResearch/Hermes-3-Llama-3.1-70B",
        "NovaSky-AI/Sky-T1-32B-Preview",
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "Sao10K/L3-8B-Lunaris-v1-Turbo",
        "Sao10K/L3.1-70B-Euryale-v2.2",
        "Sao10K/L3.3-70B-Euryale-v2.3",
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "deepseek-ai/DeepSeek-R1-Turbo",
        "google/gemini-2.0-flash-001",
        "meta-llama/Llama-3.2-11B-Vision-Instruct",
        "meta-llama/Llama-3.2-1B-Instruct",
        "meta-llama/Llama-3.2-3B-Instruct",
        "meta-llama/Llama-3.2-90B-Vision-Instruct",
        "meta-llama/Meta-Llama-3-70B-Instruct",
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "microsoft/WizardLM-2-8x22B",
        "mistralai/Devstral-Small-2505",
        "mistralai/Devstral-Small-2507",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "mistralai/Mistral-Nemo-Instruct-2407",
        "mistralai/Mistral-Small-24B-Instruct-2501",
        "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "nvidia/Llama-3.1-Nemotron-70B-Instruct",
        "nvidia/Nemotron-3-Nano-30B-A3B",
        "zai-org/GLM-4.5-Air",
        "zai-org/GLM-4.5",
        "zai-org/GLM-4.5V",
        "zai-org/GLM-4.6",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "allenai/olmOCR-7B-0725-FP8",
    ]

    @classmethod
    def get_models(cls, api_key: Optional[str] = None):
        """Fetch available models from DeepInfra API.

        Args:
            api_key (str, optional): DeepInfra API key. If not provided, returns default models.

        Returns:
            list: List of available model IDs
        """
        if not api_key:
            return cls.AVAILABLE_MODELS

        try:
            # Use a temporary curl_cffi session for this class method
            temp_session = Session()
            headers = {
                "Content-Type": "application/json",
            }
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            response = temp_session.get(
                "https://api.deepinfra.com/v1/models",
                headers=headers,
                impersonate="chrome110",  # Use impersonate for fetching
            )

            if response.status_code != 200:
                return cls.AVAILABLE_MODELS

            data = response.json()
            if "data" in data and isinstance(data["data"], list):
                return [model["id"] for model in data["data"]]
            return cls.AVAILABLE_MODELS

        except (CurlError, Exception):
            # Fallback to default models list if fetching fails
            return cls.AVAILABLE_MODELS

    @classmethod
    def update_available_models(cls, api_key=None):
        """Update the available models list from DeepInfra API"""
        try:
            models = cls.get_models(api_key)
            if models and len(models) > 0:
                cls.AVAILABLE_MODELS = models
        except Exception:
            # Fallback to default models list if fetching fails
            pass

    @staticmethod
    def _deepinfra_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from DeepInfra stream JSON objects."""
        if isinstance(chunk, dict):
            choices = chunk.get("choices")
            if choices:
                return choices[0].get("delta", {}).get("content")
        return None

    def __init__(
        self,
        api_key: Optional[str] = None,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        system_prompt: str = "You are a helpful assistant.",
        browser: str = "chrome",
    ):
        """Initializes the DeepInfra API client."""
        # Update available models from API
        self.update_available_models(api_key)

        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.url = "https://api.deepinfra.com/v1/openai/chat/completions"

        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.api = api_key
        self.headers = {
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Origin": "https://deepinfra.com",
            "Pragma": "no-cache",
            "Referer": "https://deepinfra.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "X-Deepinfra-Source": "web-embed",
            "User-Agent": self.fingerprint.get("user_agent", ""),
            "Sec-CH-UA": self.fingerprint.get("sec_ch_ua", ""),
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self.fingerprint.get("platform", "")}"',
            "X-Forwarded-For": self.fingerprint.get("x-forwarded-for", ""),
            "X-Real-IP": self.fingerprint.get("x-real-ip", ""),
            "X-Client-IP": self.fingerprint.get("x-client-ip", ""),
            "Forwarded": self.fingerprint.get("forwarded", ""),
            "X-Forwarded-Proto": self.fingerprint.get("x-forwarded-proto", ""),
            "X-Request-Id": self.fingerprint.get("x-request-id", ""),
        }
        if self.api is not None:
            self.headers["Authorization"] = f"Bearer {self.api}"

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
            self.conversation.intro = AwesomePrompts().get_act(cast(Union[str, int], act), default=self.conversation.intro, case_insensitive=True
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro

    def refresh_identity(self, browser: Optional[str] = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)

        self.headers.update(
            {
                "Accept": self.fingerprint["accept"],
                "Accept-Language": self.fingerprint["accept_language"],
            }
        )

        self.session.headers.update(self.headers)

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
        Sends a prompt to the DeepInfra API and returns the response.

        Args:
            prompt: The prompt to send to the API
            stream: Whether to stream the response
            raw: If True, returns unprocessed response chunks without any
                processing or sanitization. Useful for debugging or custom
                processing pipelines. Defaults to False.
            optimizer: Optional prompt optimizer name
            conversationally: Whether to use conversation context

        Returns:
            When raw=False: Dict with 'text' key (non-streaming) or
                Generator yielding dicts (streaming)
            When raw=True: Raw string response (non-streaming) or
                Generator yielding raw string chunks (streaming)

        Examples:
            >>> ai = DeepInfra()
            >>> # Get processed response
            >>> response = ai.ask("Hello")
            >>> print(response["text"])

            >>> # Get raw response
            >>> raw_response = ai.ask("Hello", raw=True)
            >>> print(raw_response)

            >>> # Stream raw chunks
            >>> for chunk in ai.ask("Hello", stream=True, raw=True):
            ...     print(chunk, end='', flush=True)
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
                    content_extractor=self._deepinfra_extractor,
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

                # Use sanitize_stream to parse the non-streaming JSON response
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
                # Extract the single result
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
                if hasattr(e, 'response'):
                    response_obj = getattr(e, 'response')
                    if hasattr(response_obj, 'text'):
                        err_text = getattr(response_obj, 'text')
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
        return response["text"]


if __name__ == "__main__":
    ai = DeepInfra()
    response = ai.chat("Hello", raw=False, stream=True)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="")
    else:
        print(response)
