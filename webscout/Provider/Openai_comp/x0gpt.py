import re
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union

from curl_cffi.const import CurlHttpVersion
from curl_cffi.requests import Session

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

try:
    from webscout.litagent import LitAgent
except ImportError:
    LitAgent = None  # type: ignore


class Completions(BaseCompletions):
    """Completions handler for X0GPT API."""

    def __init__(self, client: "X0GPT") -> None:
        """Initialize Completions with X0GPT client."""
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = 2049,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """Create a model response for the given chat conversation.

        Mimics openai.chat.completions.create

        Args:
            model: Model name to use
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            timeout: Request timeout in seconds
            proxies: Proxy configuration
            **kwargs: Additional parameters

        Returns:
            ChatCompletion or generator of ChatCompletionChunk
        """
        # Prepare the payload for X0GPT API
        payload: Dict[str, Any] = {
            "messages": messages,
            "chatId": uuid.uuid4().hex,
            "namespace": None,
        }

        # Add optional parameters if provided
        if max_tokens is not None and max_tokens > 0:
            payload["max_tokens"] = max_tokens

        if temperature is not None:
            payload["temperature"] = temperature

        if top_p is not None:
            payload["top_p"] = top_p

        # Add any additional parameters
        payload.update(kwargs)

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, payload, timeout, proxies)
        return self._create_non_stream(request_id, created_time, model, payload, timeout, proxies)

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Create a streaming response from X0GPT API.

        Args:
            request_id: Unique request identifier
            created_time: Timestamp of request creation
            model: Model name
            payload: Request payload
            timeout: Request timeout
            proxies: Proxy configuration

        Yields:
            ChatCompletionChunk objects

        Raises:
            IOError: If request fails
        """
        try:
            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout if timeout is not None else self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),
                impersonate="chrome120",
                http_version=CurlHttpVersion.V1_1,
            )

            # Handle non-200 responses
            if response.status_code != 200:
                raise IOError(
                    f"Failed to generate response - ({response.status_code}, "
                    f"{response.reason}) - {response.text}"
                )

            # Track token usage across chunks
            prompt_tokens = 0
            completion_tokens = 0

            # Estimate prompt tokens based on message length
            for msg in payload.get("messages", []):
                prompt_tokens += count_tokens(msg.get("content", ""))

            for line in response.iter_lines():
                if line:
                    # Handle both bytes and string responses
                    decoded_line = (
                        line.strip() if isinstance(line, str) else line.decode("utf-8").strip()
                    )

                    # X0GPT uses a different format, extract the content
                    match = re.search(r'"([^"]*)"', decoded_line)
                    if match:
                        content = match.group(1)

                        # Format the content (replace escaped sequences)
                        content = self._client.format_text(content)

                        # Update token counts
                        completion_tokens += count_tokens(content)

                        # Create the delta object
                        delta = ChoiceDelta(
                            content=content,
                            role="assistant",
                            tool_calls=None,
                        )

                        # Create the choice object
                        choice = Choice(
                            index=0,
                            delta=delta,
                            finish_reason=None,
                            logprobs=None,
                        )

                        # Create the chunk object
                        chunk = ChatCompletionChunk(
                            id=request_id,
                            choices=[choice],
                            created=created_time,
                            model=model,
                            system_fingerprint=None,
                        )

                        # Return the chunk object for internal processing
                        yield chunk

            # Final chunk with finish_reason="stop"
            delta = ChoiceDelta(
                content=None,
                role=None,
                tool_calls=None,
            )

            choice = Choice(
                index=0,
                delta=delta,
                finish_reason="stop",
                logprobs=None,
            )

            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                system_fingerprint=None,
            )

            yield chunk

        except Exception as e:
            raise IOError(f"X0GPT request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        """Create a non-streaming response from X0GPT API.

        Args:
            request_id: Unique request identifier
            created_time: Timestamp of request creation
            model: Model name
            payload: Request payload
            timeout: Request timeout
            proxies: Proxy configuration

        Returns:
            ChatCompletion object

        Raises:
            IOError: If request fails
        """
        try:
            # For non-streaming, we still use streaming internally
            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout if timeout is not None else self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),
                impersonate="chrome120",
                http_version=CurlHttpVersion.V1_1,
            )

            # Handle non-200 responses
            if response.status_code != 200:
                raise IOError(
                    f"Failed to generate response - ({response.status_code}, "
                    f"{response.reason}) - {response.text}"
                )

            # Collect the full response
            full_text = ""
            for line in response.iter_lines():
                if line:
                    # Handle both bytes and string responses
                    decoded_line = (
                        line.strip() if isinstance(line, str) else line.decode("utf-8").strip()
                    )
                    match = re.search(r'"([^"]*)"', decoded_line)
                    if match:
                        content = match.group(1)
                        full_text += content

            # Format the text (replace escaped sequences)
            full_text = self._client.format_text(full_text)

            # Estimate token counts
            prompt_tokens = 0
            for msg in payload.get("messages", []):
                prompt_tokens += count_tokens(msg.get("content", ""))

            completion_tokens = count_tokens(full_text)
            total_tokens = prompt_tokens + completion_tokens

            # Create the message object
            message = ChatCompletionMessage(role="assistant", content=full_text)

            # Create the choice object
            choice = Choice(index=0, message=message, finish_reason="stop")

            # Create the usage object
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

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
            raise IOError(f"X0GPT request failed: {e}") from e


class Chat(BaseChat):
    """Chat handler for X0GPT API."""

    def __init__(self, client: "X0GPT") -> None:
        """Initialize Chat with X0GPT client."""
        self.completions = Completions(client)


class X0GPT(OpenAICompatibleProvider):
    """OpenAI-compatible client for X0GPT API.

    Usage:
        client = X0GPT()
        response = client.chat.completions.create(
            model="X0GPT",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """

    required_auth = False
    AVAILABLE_MODELS = ["X0GPT"]

    def __init__(self, timeout: Optional[int] = None, browser: str = "chrome") -> None:
        """Initialize the X0GPT client.

        Args:
            timeout: Request timeout in seconds (None for no timeout)
            browser: Browser to emulate in user agent
        """
        self.timeout = timeout
        self.api_endpoint = "https://x0-gpt.devwtf.in/api/stream/reply"
        self.session: Session = Session()

        # Initialize user agent
        user_agent = self._get_user_agent(browser)

        self.headers: Dict[str, str] = {
            "authority": "x0-gpt.devwtf.in",
            "method": "POST",
            "path": "/api/stream/reply",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://x0-gpt.devwtf.in",
            "referer": "https://x0-gpt.devwtf.in/chat",
            "sec-ch-ua": ('"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"'),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": user_agent,
        }

        self.session.headers.update(self.headers)

        # Initialize the chat interface
        self.chat: Chat = Chat(self)

    @staticmethod
    def _get_user_agent(browser: str) -> str:
        """Get a user agent string, with fallback if LitAgent unavailable.

        Args:
            browser: Browser to emulate

        Returns:
            User agent string
        """
        if LitAgent is not None:
            try:
                agent = LitAgent()
                fingerprint = agent.generate_fingerprint(browser)
                return fingerprint.get("user_agent", X0GPT._default_user_agent())
            except Exception:
                return X0GPT._default_user_agent()
        return X0GPT._default_user_agent()

    @staticmethod
    def _default_user_agent() -> str:
        """Return a default user agent string.

        Returns:
            Default user agent
        """
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"
        )

    def format_text(self, text: str) -> str:
        """Format text by replacing escaped sequences with actual characters.

        Args:
            text: Text to format

        Returns:
            Formatted text
        """
        try:
            # Replace common escape sequences
            text = text.replace("\\n", "\n")
            text = text.replace("\\r", "\r")
            text = text.replace("\\t", "\t")
            text = text.replace('\\"', '"')
            text = text.replace("\\\\", "\\")
            return text
        except Exception:
            # If any error occurs, return the original text
            return text

    def convert_model_name(self, model: str) -> str:
        """Convert model names to ones supported by X0GPT.

        Args:
            model: Model name to convert

        Returns:
            X0GPT model name
        """
        # X0GPT doesn't use model names, but keep for compatibility
        return model

    @property
    def models(self) -> SimpleModelList:
        """Get available models.

        Returns:
            SimpleModelList of available models
        """
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    # Test the provider
    client = X0GPT()
    response = client.chat.completions.create(
        model="X0GPT",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! How are you today?"},
        ],
    )
    if not isinstance(response, Generator):
        message = response.choices[0].message if response.choices else None
        print(message.content if message else "")
