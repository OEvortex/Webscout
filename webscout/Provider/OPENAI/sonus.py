import json
import time
import uuid
from typing import cast, Any, Dict, Generator, List, Optional, Union

import requests

from ...litagent import LitAgent
from webscout.Provider.OPENAI.base import BaseChat, BaseCompletions, OpenAICompatibleProvider, SimpleModelList
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
    def __init__(self, client: 'SonusAI'):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,  # Not used by SonusAI but kept for compatibility
        stream: bool = False,
        temperature: Optional[float] = None,  # Not used by SonusAI but kept for compatibility
        top_p: Optional[float] = None,  # Not used by SonusAI but kept for compatibility
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any  # Not used by SonusAI but kept for compatibility
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create
        """
        # Format the messages using the format_prompt utility
        # This creates a conversation in the format: "User: message\nAssistant: response\nUser: message\nAssistant:"
        # SonusAI works better with a properly formatted conversation
        question = format_prompt(messages, add_special_tokens=True, do_continue=True)

        # Extract reasoning parameter if provided
        reasoning = kwargs.get('reasoning', False)

        # Prepare the multipart form data for SonusAI API
        files = {
            'message': (None, question),
            'history': (None),
            'reasoning': (None, str(reasoning).lower()),
            'model': (None, self._client.convert_model_name(model))
        }

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, files, timeout, proxies)
        else:
            return self._create_non_stream(request_id, created_time, model, files, timeout, proxies)

    def _create_stream(
        self, request_id: str, created_time: int, model: str, files: Dict[str, Any], timeout: Optional[int] = None, proxies: Optional[Dict[str, str]] = None
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            response = requests.post(
                self._client.url,
                files=files,
                headers=self._client.headers,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None)
            )
            response.raise_for_status()

            # Track token usage across chunks
            completion_tokens = 0
            streaming_text = ""

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    # Decode the line and remove 'data: ' prefix if present
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        line_text = line_text[6:]

                    data = json.loads(line_text)
                    if "content" in data:
                        content = data["content"]
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
            print(f"{RED}Error during SonusAI stream request: {e}{RESET}")
            raise IOError(f"SonusAI request failed: {e}") from e

    def _create_non_stream(
        self, request_id: str, created_time: int, model: str, files: Dict[str, Any], timeout: Optional[int] = None, proxies: Optional[Dict[str, str]] = None
    ) -> ChatCompletion:
        try:
            response = requests.post(
                self._client.url,
                files=files,
                headers=self._client.headers,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None)
            )
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data: '):
                            line_text = line_text[6:]
                        data = json.loads(line_text)
                        if "content" in data:
                            full_response += data["content"]
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue

            # Create usage statistics using count_tokens
            prompt_tokens = count_tokens(files.get('message', ['',''])[1])
            completion_tokens = count_tokens(full_response)
            total_tokens = prompt_tokens + completion_tokens

            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

            # Create the message object
            message = ChatCompletionMessage(
                role="assistant",
                content=full_response
            )

            # Create the choice object
            choice = Choice(
                index=0,
                message=message,
                finish_reason="stop"
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
            print(f"{RED}Error during SonusAI non-stream request: {e}{RESET}")
            raise IOError(f"SonusAI request failed: {e}") from e

class Chat(BaseChat):
    def __init__(self, client: 'SonusAI'):
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
    AVAILABLE_MODELS = [
        "pro",
        "air",
        "mini"
    ]

    def __init__(
        self,
        timeout: int = 30
    ):
        """
        Initialize the SonusAI client.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self.url = "https://chat.sonus.ai/chat.php"

        # Headers for the request
        agent = LitAgent()
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://chat.sonus.ai',
            'Referer': 'https://chat.sonus.ai/',
            'User-Agent': agent.random()
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Initialize the chat interface
        self.chat = Chat(self)

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

        # Default to pro if no match
        print(f"{BOLD}Warning: Model '{model}' not found, using default model 'pro'{RESET}")
        return "pro"

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)




# Simple test if run directly
if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in SonusAI.AVAILABLE_MODELS:
        try:
            client = SonusAI(timeout=60)
            # Test with a simple conversation to demonstrate format_prompt usage
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello' in one word"},
                ],
                stream=False
            )

            if isinstance(response, ChatCompletion) and response.choices and response.choices[0].message.content:
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
