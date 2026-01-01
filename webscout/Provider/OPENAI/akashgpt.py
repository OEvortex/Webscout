import json
import re
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

# Import base classes and utility structures
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

# Import LitAgent for user agent generation
from ...litagent import LitAgent

# AkashGPT constants
AVAILABLE_MODELS = [
    "Qwen/Qwen3-30B-A3B",
    "DeepSeek-V3.1",
    "Meta-Llama-3-3-70B-Instruct",
]


def _akash_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
    """Extracts content from the AkashGPT stream format '0:"..."'."""
    if isinstance(chunk, str):
        match = re.search(r'0:"(.*?)"', chunk)
        if match:
            # Decode potential unicode escapes like \u00e9
            content = match.group(1).encode().decode("unicode_escape")
            return content.replace("\\\\", "\\").replace(
                '\\"', '"'
            )  # Handle escaped backslashes and quotes
    return None


class Completions(BaseCompletions):
    def __init__(self, client: "AkashGPT"):
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
        proxies: Optional[dict] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Create a chat completion with AkashGPT API.
        Mimics openai.chat.completions.create
        """
        # Use format_prompt utility to format the conversation
        conversation_prompt = format_prompt(messages, add_special_tokens=True, include_system=True)

        # Set up request parameters
        kwargs.get("api_key", self._client.api_key)

        # Generate request ID and timestamp
        request_id = str(uuid.uuid4())
        created_time = int(time.time())

        # Use the provided model directly
        akash_model = model

        if stream:
            return self._create_streaming(
                request_id,
                created_time,
                akash_model,
                conversation_prompt,
                messages,
                max_tokens,
                temperature,
                top_p,
                timeout,
                proxies,
            )
        else:
            return self._create_non_streaming(
                request_id,
                created_time,
                akash_model,
                conversation_prompt,
                messages,
                max_tokens,
                temperature,
                top_p,
                timeout,
                proxies,
            )

    def _create_streaming(
        self,
        request_id: str,
        created_time: int,
        model: str,
        conversation_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        temperature: Optional[float],
        top_p: Optional[float],
        timeout: Optional[int],
        proxies: Optional[dict],
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Implementation for streaming chat completions."""
        try:
            # Calculate prompt tokens
            prompt_tokens = count_tokens(conversation_prompt)
            completion_tokens = 0
            total_tokens = 0

            # Make the API request to AkashGPT
            payload = {
                "id": str(uuid.uuid4()).replace("-", ""),
                "messages": messages,
                "model": model,
                "temperature": temperature or 0.6,
                "topP": top_p or 0.9,
                "context": [],
            }

            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or 30,
                proxies=proxies,
            )

            if not response.ok:
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            full_content = ""

            # Process the streaming response
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        # Try to parse as JSON first
                        data = json.loads(data_str)
                        if isinstance(data, dict) and "text" in data:
                            new_content = data["text"]
                        elif isinstance(data, str):
                            # Use the extractor for raw string responses
                            extracted = _akash_extractor(data_str)
                            new_content = extracted or data_str
                        else:
                            continue

                        if new_content and new_content != full_content:
                            # Calculate delta (new content since last chunk)
                            delta_content = (
                                new_content[len(full_content) :]
                                if new_content.startswith(full_content)
                                else new_content
                            )
                            full_content = new_content
                            completion_tokens = count_tokens(full_content)
                            total_tokens = prompt_tokens + completion_tokens

                            # Only yield chunk if there's new content
                            if delta_content:
                                delta = ChoiceDelta(content=delta_content, role="assistant")
                                choice = Choice(index=0, delta=delta, finish_reason=None)
                                chunk_response = ChatCompletionChunk(
                                    id=request_id,
                                    choices=[choice],
                                    created=created_time,
                                    model=model,
                                )
                                chunk_response.usage = {
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "total_tokens": total_tokens,
                                }
                                yield chunk_response

                    except json.JSONDecodeError:
                        # Handle non-JSON responses
                        extracted = _akash_extractor(data_str)
                        if extracted and extracted != full_content:
                            delta_content = (
                                extracted[len(full_content) :]
                                if extracted.startswith(full_content)
                                else extracted
                            )
                            full_content = extracted
                            completion_tokens = count_tokens(full_content)
                            total_tokens = prompt_tokens + completion_tokens

                            if delta_content:
                                delta = ChoiceDelta(content=delta_content, role="assistant")
                                choice = Choice(index=0, delta=delta, finish_reason=None)
                                chunk_response = ChatCompletionChunk(
                                    id=request_id,
                                    choices=[choice],
                                    created=created_time,
                                    model=model,
                                )
                                chunk_response.usage = {
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "total_tokens": total_tokens,
                                }
                                yield chunk_response

            # Final chunk with finish_reason
            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            final_chunk = ChatCompletionChunk(
                id=request_id, choices=[choice], created=created_time, model=model
            )
            final_chunk.usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }
            yield final_chunk

        except Exception as e:
            raise IOError(f"AkashGPT streaming request failed: {e}") from e

    def _create_non_streaming(
        self,
        request_id: str,
        created_time: int,
        model: str,
        conversation_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        temperature: Optional[float],
        top_p: Optional[float],
        timeout: Optional[int],
        proxies: Optional[dict],
    ) -> ChatCompletion:
        """Implementation for non-streaming chat completions."""
        try:
            # Calculate prompt tokens
            prompt_tokens = count_tokens(conversation_prompt)

            # Make the API request to AkashGPT
            payload = {
                "id": str(uuid.uuid4()).replace("-", ""),
                "messages": messages,
                "model": model,
                "temperature": temperature or 0.6,
                "topP": top_p or 0.9,
                "context": [],
            }

            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                timeout=timeout or 30,
                proxies=proxies,
            )

            if not response.ok:
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            # Collect the full response
            full_content = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        # Try to parse as JSON first
                        data = json.loads(data_str)
                        if isinstance(data, dict) and "text" in data:
                            full_content = data["text"]
                        elif isinstance(data, str):
                            # Use the extractor for raw string responses
                            extracted = _akash_extractor(data_str)
                            if extracted:
                                full_content = extracted
                    except json.JSONDecodeError:
                        # Handle non-JSON responses
                        extracted = _akash_extractor(data_str)
                        if extracted:
                            full_content = extracted

            # Calculate completion tokens
            completion_tokens = count_tokens(full_content)
            total_tokens = prompt_tokens + completion_tokens

            # Create the completion message
            message = ChatCompletionMessage(role="assistant", content=full_content)

            # Create the choice
            choice = Choice(index=0, message=message, finish_reason="stop")

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
            raise IOError(f"AkashGPT request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "AkashGPT"):
        self.completions = Completions(client)


class AkashGPT(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for AkashGPT API.

    Usage:
        client = AkashGPT(api_key="your_api_key")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """

    required_auth = True

    AVAILABLE_MODELS = AVAILABLE_MODELS

    def __init__(
        self, api_key: str, tools: Optional[List] = None, proxies: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the AkashGPT-compatible client.

        Args:
            api_key: Required API key for AkashGPT
            tools: Optional list of tools to register with the provider
            proxies: Optional proxy configuration dict
        """
        super().__init__(api_key=api_key, tools=tools, proxies=proxies)

        # Store the api_key for use in completions
        self.api_key = api_key
        self.timeout = 30
        self.api_endpoint = "https://chat.akash.network/api/chat"

        # Initialize LitAgent for user agent generation
        agent = LitAgent()
        user_agent = agent.random()

        self.headers = {
            "authority": "chat.akash.network",
            "method": "POST",
            "path": "/api/chat",
            "scheme": "https",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://chat.akash.network",
            "priority": "u=1, i",
            "referer": "https://chat.akash.network/",
            "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": user_agent,
        }

        self.session.headers.update(self.headers)

        # Initialize chat interface
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    # Example usage
    client = AkashGPT(api_key="your_api_key_here")
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": "Hello! How are you?"}]
    )
    if isinstance(response, ChatCompletion):
        if response.choices[0].message and response.choices[0].message.content:
            print(response.choices[0].message.content)
        print(f"Usage: {response.usage}")
