import json
import uuid
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Response as CurlResponse  # Import Response
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import (  # Import sanitize_stream
    AwesomePrompts,
    Conversation,
    Optimizers,
    sanitize_stream,
)
from webscout.litagent import LitAgent

# Model configurations
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "ayle": {
        "endpoint": "https://ayle.chat/api/chat",
        "models": [
            # Google Generative AI
            "gemini-2.5-flash",
            # Groq
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            # OpenRouter
            "mistralai/devstral-2512:free",
            "z-ai/glm-4.5-air:free",
            # Inception AI
            "mercury",
            "mercury-coder",
            # Perplexity
            "sonar",
            "sonar-pro",
        ],
    },
}


class Ayle(Provider):
    """
    A class to interact with multiple AI APIs through the Ayle Chat interface.
    """

    required_auth = False
    AVAILABLE_MODELS = [
        # Google Generative AI
        "gemini-2.5-flash",
        # Groq
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        # OpenRouter
        "mistralai/devstral-2512:free",
        "z-ai/glm-4.5-air:free",
        # Inception AI
        "mercury",
        "mercury-coder",
        # Perplexity
        "sonar",
        "sonar-pro",
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 4000,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        system_prompt: str = "You are a friendly, helpful AI assistant.",
        temperature: float = 0.5,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1,
    ):
        """Initializes the Ayle client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = Session()  # Use curl_cffi Session
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p

        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://ayle.chat/",
            "referer": "https://ayle.chat/",
            "user-agent": self.agent.random(),
        }

        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(cast(Any, proxies))  # Assign proxies directly
        self.session.cookies.update({"session": uuid.uuid4().hex})

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

        self.provider = self._get_provider_from_model(self.model)
        self.model_name = self.model

    def _get_endpoint(self) -> str:
        """Get the API endpoint for the current provider."""
        return MODEL_CONFIGS[self.provider]["endpoint"]

    def _get_provider_from_model(self, model: str) -> str:
        """Determine the provider based on the model name."""
        for provider, config in MODEL_CONFIGS.items():
            if model in config["models"]:
                return provider

        available_models = []
        for provider, config in MODEL_CONFIGS.items():
            for model_name in config["models"]:
                available_models.append(f"{provider}/{model_name}")

        error_msg = f"Invalid model: {model}\nAvailable models: {', '.join(available_models)}"
        raise ValueError(error_msg)

    @staticmethod
    def _ayle_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from Ayle stream."""
        if isinstance(chunk, str):
            if chunk.startswith('0:"'):
                try:
                    return json.loads(chunk[2:])
                except Exception:
                    return None
        elif isinstance(chunk, dict):
            return chunk.get("choices", [{}])[0].get("delta", {}).get("content")
        return None

    def _make_request(
        self, payload: Dict[str, Any]
    ) -> CurlResponse:  # Change type hint to Response
        """Make the API request with proper error handling."""
        try:
            response = self.session.post(
                self._get_endpoint(),
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
                stream=True,  # Enable streaming for the request
                impersonate="chrome120",  # Add impersonate
            )
            response.raise_for_status()
            return response
        except (
            CurlError,
            exceptions.FailedToGenerateResponseError,
            Exception,
        ) as e:  # Catch CurlError and others
            raise exceptions.FailedToGenerateResponseError(f"API request failed: {e}") from e

    def _build_payload(self, conversation_prompt: str) -> Dict[str, Any]:
        """Build the appropriate payload based on the provider."""
        return {"messages": [{"role": "user", "content": conversation_prompt}], "model": self.model}

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """Sends a prompt to the API and returns the response."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                error_msg = f"Optimizer is not one of {self.__available_optimizers}"
                raise exceptions.FailedToGenerateResponseError(error_msg)

        payload = self._build_payload(conversation_prompt)
        response = self._make_request(payload)
        processed_stream = sanitize_stream(
            data=response.iter_content(chunk_size=None),
            intro_value=None,
            to_json=False,
            content_extractor=self._ayle_extractor,
            yield_raw_on_error=False,
            raw=raw,
        )

        if stream:
            return self._ask_stream(prompt, processed_stream, raw)
        else:
            return self._ask_non_stream(prompt, processed_stream, raw)

    def _ask_stream(self, prompt: str, processed_stream: Generator, raw: bool) -> Generator:
        streaming_text = ""
        for content_chunk in processed_stream:
            if content_chunk and isinstance(content_chunk, str):
                content_chunk = content_chunk.replace("\\\\", "\\").replace('\\"', '"')
            if raw:
                if content_chunk and isinstance(content_chunk, str):
                    streaming_text += content_chunk
                yield content_chunk
            else:
                if content_chunk and isinstance(content_chunk, str):
                    streaming_text += content_chunk
                    yield dict(text=content_chunk)
        self.last_response = {"text": streaming_text}
        self.conversation.update_chat_history(prompt, streaming_text)

    def _ask_non_stream(
        self, prompt: str, processed_stream: Generator, raw: bool
    ) -> Union[Dict[str, Any], str]:
        full_response = ""
        for content_chunk in processed_stream:
            if content_chunk and isinstance(content_chunk, str):
                content_chunk = content_chunk.replace("\\\\", "\\").replace('\\"', '"')
            if raw:
                if content_chunk and isinstance(content_chunk, str):
                    full_response += content_chunk
            else:
                if content_chunk and isinstance(content_chunk, str):
                    full_response += content_chunk
        self.last_response = {"text": full_response}
        self.conversation.update_chat_history(prompt, full_response)
        return self.last_response if not raw else full_response

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        raw = kwargs.get("raw", False)

        def for_stream() -> Generator[str, None, None]:
            for response in self.ask(
                prompt, stream=True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield response
                else:
                    yield self.get_message(response)

        def for_non_stream() -> str:
            result = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return result if isinstance(result, str) else str(result)
            return self.get_message(result)

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        if isinstance(response, dict):
            text = cast(Dict[str, Any], response).get("text", "")
        else:
            text = str(response)
        return text.replace("\\\\", "\\").replace('\\"', '"')


if __name__ == "__main__":
    from rich import print

    ai = Ayle(model="gemini-2.5-flash")
    response = ai.chat("tell me a joke", stream=True, raw=False)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
