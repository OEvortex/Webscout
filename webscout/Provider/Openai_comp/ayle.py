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

from ...litagent import LitAgent

# ANSI escape codes for formatting
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"

# Model configurations
MODEL_CONFIGS = {
    "ayle": {
        "endpoint": "https://ayle.chat/api/chat",
        "models": [
            "gemini-2.5-flash",
            "llama-3.3-70b-versatile",
            "llama-3.3-70b",
            "tngtech/deepseek-r1t2-chimera:free",
            "openai/gpt-oss-120b",
            "qwen-3-235b-a22b-instruct-2507",
            "llama3.1-8b",
            "llama-4-scout-17b-16e-instruct",
            "qwen-3-32b",
        ],
    }
}


class Completions(BaseCompletions):
    def __init__(self, client: "Ayle"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,  # Not used directly but kept for compatibility
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create
        """
        # Determine the provider based on the model
        provider = self._client._get_provider_from_model(model)

        # Build the appropriate payload
        payload = {"messages": messages, "model": model}

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(
                request_id, created_time, model, provider, payload, timeout, proxies
            )
        else:
            return self._create_non_stream(
                request_id, created_time, model, provider, payload, timeout, proxies
            )

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        provider: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            endpoint = self._client._get_endpoint(provider)
            response = self._client.session.post(
                endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),
            )
            response.raise_for_status()

            # Track token usage across chunks
            completion_tokens = 0
            streaming_text = ""

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    line_str = line.decode("utf-8")
                    if line_str.startswith('0:"'):
                        content = json.loads(line_str[2:])
                        if content:
                            streaming_text += content
                            completion_tokens += count_tokens(content)

                        # Create a delta object for this chunk
                        delta = ChoiceDelta(content=content)
                        choice = Choice(index=0, delta=delta, finish_reason=None)

                        chunk = ChatCompletionChunk(
                            id=request_id,
                            choices=[choice],
                            created=created_time,
                            model=model,
                        )

                        yield chunk
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

            # Final chunk with finish_reason
            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")

            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
            )

            yield chunk

        except requests.exceptions.RequestException as e:
            print(f"{RED}Error during Ayle stream request: {e}{RESET}")
            raise IOError(f"Ayle request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        provider: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        try:
            endpoint = self._client._get_endpoint(provider)
            response = self._client.session.post(
                endpoint,
                headers=self._client.headers,
                json=payload,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),
            )
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        line_str = line.decode("utf-8")
                        if line_str.startswith('0:"'):
                            content = json.loads(line_str[2:])
                            if content:
                                full_response += content
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue

            # Create usage statistics (estimated)
            prompt_tokens = count_tokens(str(payload.get("messages", "")))
            completion_tokens = count_tokens(full_response)
            total_tokens = prompt_tokens + completion_tokens

            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            # Create the message object
            message = ChatCompletionMessage(role="assistant", content=full_response)

            # Create the choice object
            choice = Choice(index=0, message=message, finish_reason="stop")

            # Create the completion object
            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )

            return completion

        except Exception as e:
            print(f"{RED}Error during Ayle non-stream request: {e}{RESET}")
            raise IOError(f"Ayle request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "Ayle"):
        self.completions = Completions(client)


class Ayle(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for Ayle API.

    Usage:
        client = Ayle()
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """

    required_auth = False
    AVAILABLE_MODELS = [
        "gemini-2.5-flash",
        "llama-3.3-70b-versatile",
        "llama-3.3-70b",
        "tngtech/deepseek-r1t2-chimera:free",
        "openai/gpt-oss-120b",
        "qwen-3-235b-a22b-instruct-2507",
        "llama3.1-8b",
        "llama-4-scout-17b-16e-instruct",
        "qwen-3-32b",
    ]

    def __init__(self, timeout: int = 30, temperature: float = 0.5, top_p: float = 1.0):
        """
        Initialize the Ayle client.

        Args:
            timeout: Request timeout in seconds.
            temperature: Temperature for response generation.
            top_p: Top-p sampling parameter.
        """
        self.timeout = timeout
        self.temperature = temperature
        self.top_p = top_p

        # Initialize LitAgent for user agent generation
        agent = LitAgent()

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://ayle.chat/",
            "referer": "https://ayle.chat/",
            "user-agent": agent.random(),
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.cookies.update({"session": uuid.uuid4().hex})

        # Initialize the chat interface
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)

    def _get_endpoint(self, provider: str) -> str:
        """Get the API endpoint for the specified provider."""
        return cast(str, MODEL_CONFIGS[provider]["endpoint"])

    def _get_provider_from_model(self, model: str) -> str:
        """Determine the provider based on the model name."""
        for provider, config in MODEL_CONFIGS.items():
            if model in config["models"]:
                return provider

        # If model not found, use a default model
        print(f"{BOLD}Warning: Model '{model}' not found, using default model 'ayle'{RESET}")
        return "ayle"

    def convert_model_name(self, model: str) -> str:
        """
        Ensure the model name is in the correct format.
        """
        if model in self.AVAILABLE_MODELS:
            return model

        # Try to find a matching model
        for available_model in self.AVAILABLE_MODELS:
            if model.lower() in available_model.lower():
                return available_model

        # Default to gemini-2.5-flash if no match
        print(
            f"{BOLD}Warning: Model '{model}' not found, using default model 'gemini-2.5-flash'{RESET}"
        )
        return "gemini-2.5-flash"


# Simple test if run directly
if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    # Test a subset of models to avoid excessive API calls
    test_models = [
        "gemini-2.5-flash",
    ]

    for model in test_models:
        try:
            client = Ayle(timeout=60)
            # Test with a simple conversation to demonstrate format_prompt usage
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
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
                # Truncate response if too long
                display_text = response.choices[0].message.content.strip()
                display_text = display_text[:50] + "..." if len(display_text) > 50 else display_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"{model:<50} {'✗':<10} {str(e)}")
            print(f"{model:<50} {'✗':<10} {str(e)}")
