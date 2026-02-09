import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union

from curl_cffi.requests import Session

from webscout.litagent import LitAgent
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
)


class Completions(BaseCompletions):
    def __init__(self, client: "K2Think"):
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
        # Generate a unique request ID
        request_id = f"chatcmpl-{uuid.uuid4().hex}"
        created_time = int(time.time())

        # Prepare the payload for K2Think API
        payload = {
            "stream": stream,
            "model": model,
            "messages": messages,
            "params": {},
            "features": {"web_search": False},
        }

        # Handle streaming response
        if stream:
            return self._handle_streaming_response(
                request_id, created_time, model, payload, timeout, proxies
            )
        else:
            return self._handle_non_streaming_response(
                request_id, created_time, model, payload, timeout, proxies
            )

    def _handle_streaming_response(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Handle streaming response from K2Think API"""
        try:
            response = self._client.session.post(
                self._client.chat_endpoint,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
            )
            response.raise_for_status()

            streaming_text = ""

            streaming_text = ""
            previous_content = ""

            for line in response.iter_lines(decode_unicode=False):
                if line:
                    if isinstance(line, bytes):
                        line = line.decode("utf-8")
                    if line.startswith("data: "):
                        json_str = line[6:]
                        if json_str == "[DONE]":
                            break
                        try:
                            data = json.loads(json_str)

                            # Handle K2Think's custom streaming format
                            if "content" in data and "done" not in data:
                                current_content = data["content"]
                                # Extract the new content since last chunk
                                if len(current_content) > len(previous_content):
                                    new_content = current_content[len(previous_content):]
                                    if new_content:
                                        streaming_text += new_content
                                        previous_content = current_content

                                        delta = ChoiceDelta(content=new_content, role="assistant")
                                        choice = Choice(
                                            index=0,
                                            delta=delta,
                                            finish_reason=None,
                                        )

                                        chunk = ChatCompletionChunk(
                                            id=request_id,
                                            choices=[choice],
                                            created=created_time,
                                            model=model,
                                        )

                                        yield chunk
                            elif "done" in data and data.get("done"):
                                # Final chunk
                                break

                        except json.JSONDecodeError:
                            continue

            # Final chunk with finish_reason="stop"
            delta = ChoiceDelta(content=None, role=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
            )
            yield chunk

        except Exception as e:
            raise IOError(f"K2Think streaming request failed: {e}") from e

    def _handle_non_streaming_response(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        """Handle non-streaming response from K2Think API"""
        try:
            response = self._client.session.post(
                self._client.chat_endpoint,
                json=payload,
                stream=False,
                timeout=timeout or self._client.timeout,
            )
            response.raise_for_status()

            data = response.json()
            choices_data = data.get("choices", [])
            usage_data = data.get("usage", {})

            choices = []
            for choice_d in choices_data:
                message_d = choice_d.get("message")
                if not message_d and "delta" in choice_d:
                    delta = choice_d["delta"]
                    message_d = {
                        "role": delta.get("role", "assistant"),
                        "content": delta.get("content", ""),
                    }
                if not message_d:
                    message_d = {"role": "assistant", "content": ""}

                message = ChatCompletionMessage(
                    role=message_d.get("role", "assistant"),
                    content=message_d.get("content", "")
                )
                choice = Choice(
                    index=choice_d.get("index", 0),
                    message=message,
                    finish_reason=choice_d.get("finish_reason", "stop"),
                )
                choices.append(choice)

            usage = CompletionUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

            completion = ChatCompletion(
                id=request_id,
                choices=choices,
                created=created_time,
                model=data.get("model", model),
                usage=usage,
            )

            return completion

        except Exception as e:
            raise IOError(f"K2Think request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "K2Think"):
        self.completions = Completions(client)


class K2Think(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for K2Think AI API.

    Usage:
        client = K2Think()
        response = client.chat.completions.create(
            model="MBZUAI-IFM/K2-Think-v2",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """

    required_auth = False
    AVAILABLE_MODELS = [
        "MBZUAI-IFM/K2-Think-v2",
    ]

    def __init__(self, timeout: int = 30, proxies: dict = {}, browser: str = "chrome"):
        """
        Initialize the K2Think client.

        Args:
            timeout: Request timeout in seconds
            proxies: Proxy configuration for requests
            browser: Browser name for LitAgent to generate User-Agent
        """
        self.timeout = timeout
        self.proxies = proxies
        self.chat_endpoint = "https://www.k2think.ai/api/guest/chat/completions"

        # Initialize session with curl_cffi
        self.session = Session()

        # Set up browser fingerprinting
        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)

        # Set headers
        self.session.headers.update({
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Origin": "https://www.k2think.ai",
            "Pragma": "no-cache",
            "Referer": "https://www.k2think.ai/guest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
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
        })

        # Set proxies if provided
        if proxies:
            self.session.proxies.update(proxies)

        # Initialize chat property
        self.chat = Chat(self)

    def refresh_identity(self, browser: Optional[str] = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)

        self.session.headers.update(
            {
                "Accept": self.fingerprint["accept"],
                "Accept-Language": self.fingerprint["accept_language"],
            }
        )

        return self.fingerprint

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


# Example usage
if __name__ == "__main__":
    # Test the provider
    client = K2Think()
    response = client.chat.completions.create(
        model="MBZUAI-IFM/K2-Think-v2",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! How are you today?"},
        ],
    )
    if isinstance(response, ChatCompletion):
        message = response.choices[0].message
        if message:
            print(message.content)
