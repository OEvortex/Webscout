import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union

from curl_cffi.requests import Session

from webscout.litagent import LitAgent
from webscout.Provider.OPENAI.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from webscout.Provider.OPENAI.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
    format_prompt,
)

# ANSI escape codes for formatting
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"


class Completions(BaseCompletions):
    def __init__(self, client: "SonusAI"):
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
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create
        """
        question = format_prompt(messages, add_special_tokens=True, do_continue=True)

        reasoning = kwargs.get("reasoning", False)

        data = {
            "message": question,
            "history": "",
            "reasoning": str(reasoning).lower(),
            "model": self._client.convert_model_name(model),
        }

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, data, timeout, proxies)
        else:
            return self._create_non_stream(request_id, created_time, model, data, timeout, proxies)

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        data: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            response = self._client.session.post(
                self._client.url,
                data=data,
                stream=True,
                timeout=timeout or self._client.timeout,
                impersonate="chrome110",
            )
            response.raise_for_status()

            completion_tokens = 0
            streaming_text = ""

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    line_text = line.decode("utf-8") if isinstance(line, bytes) else line
                    if line_text.startswith("data: "):
                        line_text = line_text[6:]

                    data_json = json.loads(line_text)
                    if "content" in data_json:
                        content = data_json["content"]
                        streaming_text += content
                        completion_tokens += count_tokens(content)

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

            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")

            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
            )

            yield chunk

        except Exception as e:
            print(f"{RED}Error during SonusAI stream request: {e}{RESET}")
            raise IOError(f"SonusAI request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        data: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        try:
            response = self._client.session.post(
                self._client.url,
                data=data,
                timeout=timeout or self._client.timeout,
                impersonate="chrome110",
            )
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        line_text = line.decode("utf-8") if isinstance(line, bytes) else line
                        if line_text.startswith("data: "):
                            line_text = line_text[6:]
                        data_json = json.loads(line_text)
                        if "content" in data_json:
                            full_response += data_json["content"]
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue

            prompt_tokens = count_tokens(data.get("message", ""))
            completion_tokens = count_tokens(full_response)
            total_tokens = prompt_tokens + completion_tokens

            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            message = ChatCompletionMessage(role="assistant", content=full_response)

            choice = Choice(index=0, message=message, finish_reason="stop")

            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )

            return completion

        except Exception as e:
            print(f"{RED}Error during SonusAI non-stream request: {e}{RESET}")
            raise IOError(f"SonusAI request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "SonusAI"):
        self.completions = Completions(client)


class SonusAI(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for Sonus AI API.

    Usage:
        client = SonusAI()
        response = client.chat.completions.create(
            model="pro",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """

    required_auth = False
    AVAILABLE_MODELS = ["pro", "air", "mini"]

    def __init__(self, timeout: int = 30, proxies: dict = {}):
        """
        Initialize the SonusAI client.

        Args:
            timeout: Request timeout in seconds.
            proxies: Proxy configuration for requests.
        """
        self.timeout = timeout
        self.proxies = proxies
        self.url = "https://chat.sonus.ai/chat.php"

        agent = LitAgent()
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://chat.sonus.ai",
            "Referer": "https://chat.sonus.ai/",
            "User-Agent": agent.random(),
        }

        self.session = Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

        self.chat = Chat(self)

    def convert_model_name(self, model: str) -> str:
        """
        Ensure the model name is in the correct format.
        """
        if model in self.AVAILABLE_MODELS:
            return model

        for available_model in self.AVAILABLE_MODELS:
            if model.lower() in available_model.lower():
                return available_model

        print(f"{BOLD}Warning: Model '{model}' not found, using default model 'pro'{RESET}")
        return "pro"

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in SonusAI.AVAILABLE_MODELS:
        try:
            client = SonusAI(timeout=60)
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
            ):
                message = response.choices[0].message
                if message and message.content:
                    status = "✓"
                    display_text = message.content.strip()
                    display_text = (
                        display_text[:50] + "..." if len(display_text) > 50 else display_text
                    )
                else:
                    status = "✗"
                    display_text = "Empty or invalid response"
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"{model:<50} {'✗':<10} {str(e)}")
