import time
import uuid
import requests
from typing import List, Dict, Optional, Union, Generator, Any

from webscout.litagent import LitAgent
from .base import BaseChat, BaseCompletions, OpenAICompatibleProvider
from .utils import (
    ChatCompletion,
    ChatCompletionChunk,
    Choice,
    ChatCompletionMessage,
    ChoiceDelta,
    CompletionUsage,
    format_prompt
)

# ANSI escape codes for formatting
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"

class Completions(BaseCompletions):
    def __init__(self, client: 'HeckAI'):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,  # Not used by HeckAI but kept for compatibility
        stream: bool = False,
        temperature: Optional[float] = None,  # Not used by HeckAI but kept for compatibility
        top_p: Optional[float] = None,  # Not used by HeckAI but kept for compatibility
        **kwargs: Any  # Not used by HeckAI but kept for compatibility
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create
        """
        # Format the messages using the format_prompt utility
        # This creates a conversation in the format: "User: message\nAssistant: response\nUser: message\nAssistant:"
        # HeckAI works better with a properly formatted conversation
        question = format_prompt(messages, add_special_tokens=True)

        # Prepare the payload for HeckAI API
        payload = {
            "model": model,
            "question": question,
            "language": self._client.language,
            "sessionId": self._client.session_id,
            "previousQuestion": None,  # Not needed when using format_prompt
            "previousAnswer": None,    # Not needed when using format_prompt
            "imgUrls": []
        }

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, payload)
        else:
            return self._create_non_stream(request_id, created_time, model, payload)

    def _create_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any]
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            response = self._client.session.post(
                self._client.url,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=self._client.timeout
            )
            response.raise_for_status()

            # Track token usage across chunks
            completion_tokens = 0

            streaming_text = ""
            in_answer = False

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                # Remove "data: " prefix
                if line.startswith("data: "):
                    data = line[6:]
                else:
                    continue

                # Check for control markers
                if data == "[ANSWER_START]":
                    in_answer = True
                    continue

                if data == "[ANSWER_DONE]":
                    in_answer = False
                    continue

                if data == "[RELATE_Q_START]" or data == "[RELATE_Q_DONE]":
                    continue

                # Process content if we're in an answer section
                if in_answer:
                    streaming_text += data
                    completion_tokens += len(data) // 4  # Rough estimate

                    # Create a delta object for this chunk
                    delta = ChoiceDelta(content=data)
                    choice = Choice(index=0, delta=delta, finish_reason=None)

                    chunk = ChatCompletionChunk(
                        id=request_id,
                        choices=[choice],
                        created=created_time,
                        model=model,
                    )

                    yield chunk

            # Store the response for future context
            # We don't need to store previous_question/answer as we're using format_prompt
            # which handles the conversation formatting

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
            print(f"{RED}Error during HeckAI stream request: {e}{RESET}")
            raise IOError(f"HeckAI request failed: {e}") from e

    def _create_non_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any]
    ) -> ChatCompletion:
        try:
            full_text = ""
            streaming_text = ""
            in_answer = False

            response = self._client.session.post(
                self._client.url,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=self._client.timeout
            )
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                # Remove "data: " prefix
                if line.startswith("data: "):
                    data = line[6:]
                else:
                    continue

                # Check for control markers
                if data == "[ANSWER_START]":
                    in_answer = True
                    continue

                if data == "[ANSWER_DONE]":
                    in_answer = False
                    continue

                if data == "[RELATE_Q_START]" or data == "[RELATE_Q_DONE]":
                    continue

                # Process content if we're in an answer section
                if in_answer:
                    streaming_text += data

            full_text = streaming_text

            # Store the response for future context
            # We don't need to store previous_question/answer as we're using format_prompt
            # which handles the conversation formatting

            # Create usage statistics (estimated)
            prompt_tokens = len(payload["question"]) // 4
            completion_tokens = len(full_text) // 4
            total_tokens = prompt_tokens + completion_tokens

            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

            # Create the message object
            message = ChatCompletionMessage(
                role="assistant",
                content=full_text
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
            print(f"{RED}Error during HeckAI non-stream request: {e}{RESET}")
            raise IOError(f"HeckAI request failed: {e}") from e

class Chat(BaseChat):
    def __init__(self, client: 'HeckAI'):
        self.completions = Completions(client)

class HeckAI(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for HeckAI API.

    Usage:
        client = HeckAI()
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """

    AVAILABLE_MODELS = [
        "deepseek/deepseek-chat",
        "openai/gpt-4o-mini",
        "deepseek/deepseek-r1",
        "google/gemini-2.0-flash-001"
    ]

    def __init__(
        self,
        timeout: int = 30,
        language: str = "English"
    ):
        """
        Initialize the HeckAI client.

        Args:
            timeout: Request timeout in seconds.
            language: Language for responses.
        """
        self.timeout = timeout
        self.language = language
        self.url = "https://api.heckai.weight-wave.com/api/ha/v1/chat"
        self.session_id = str(uuid.uuid4())

        # Use LitAgent for user-agent
        agent = LitAgent()
        self.headers = {
            'User-Agent': agent.random(),
            'Content-Type': 'application/json',
            'Origin': 'https://heck.ai',
            'Referer': 'https://heck.ai/',
            'Connection': 'keep-alive'
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

        # Default to gemini if no match
        print(f"{BOLD}Warning: Model '{model}' not found, using default model 'google/gemini-2.0-flash-001'{RESET}")
        return "google/gemini-2.0-flash-001"


# Simple test if run directly
if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in HeckAI.AVAILABLE_MODELS:
        try:
            client = HeckAI(timeout=60)
            # Test with a simple conversation to demonstrate format_prompt usage
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello' in one word"},
                ],
                stream=False
            )

            if response and response.choices and response.choices[0].message.content:
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
