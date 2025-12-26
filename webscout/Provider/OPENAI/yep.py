import json
import time
import uuid
from typing import cast, Any, Dict, Generator, List, Optional, Union

import cloudscraper  # Import cloudscraper

# Import base classes and utility structures
from webscout.Provider.OPENAI.base import BaseChat, BaseCompletions, OpenAICompatibleProvider, SimpleModelList
from webscout.Provider.OPENAI.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,  # Import count_tokens
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
)

# Attempt to import LitAgent, fallback if not available
try:
    from ...litagent import LitAgent
except ImportError:
    # Define a dummy LitAgent if webscout is not installed or accessible
    class LitAgent:
        def generate_fingerprint(self, browser: str = "chrome") -> Dict[str, Any]:
            print("Warning: LitAgent not found. Using default minimal headers.")
            return {
                "accept": "*/*",
                "accept_language": "en-US,en;q=0.9",
                "platform": "Windows",
                "sec_ch_ua": '"Not/A)Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "browser_type": browser,
            }

# --- YEPCHAT Client ---

# ANSI escape codes for formatting
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"

class Completions(BaseCompletions):
    def __init__(self, client: 'YEPCHAT'):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 1280,
        stream: bool = False,
        temperature: Optional[float] = 0.6,
        top_p: Optional[float] = 0.7,
        system_prompt: Optional[str] = None,  # Added for consistency, but will be ignored
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation using YEPCHAT API.
        Mimics openai.chat.completions.create
        Note: YEPCHAT does not support system messages. They will be converted to user messages.
        """
        # Only accept and use the raw model name (no prefix logic)
        model_raw = model
        # Validate model
        if model_raw not in self._client.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {self._client.AVAILABLE_MODELS}"
            )

        # Convert system messages to user messages for compatibility
        filtered_messages = []

        # If an explicit system_prompt is provided, prepend it as a user message
        if system_prompt:
            filtered_messages.append({"role": "user", "content": system_prompt})

        for msg in messages:
            if msg["role"] == "system":
                # Convert system message to user message
                new_msg = msg.copy()
                new_msg["role"] = "user"
                filtered_messages.append(new_msg)
            else:
                filtered_messages.append(msg)

        # If no messages left after filtering, raise an error
        if not filtered_messages:
            raise ValueError("At least one user or assistant message is required for YEPCHAT.")

        payload = {
            "stream": stream,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "temperature": temperature,
            "messages": filtered_messages,  # Use filtered messages
            "model": model_raw,  # Send only the raw model name to the API
        }

        # Add any extra kwargs to the payload
        payload.update(kwargs)

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, payload, timeout, proxies)
        else:
            return self._create_non_stream(request_id, created_time, model, payload, timeout, proxies)

    def _create_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any], timeout: Optional[int] = None, proxies: Optional[Dict[str, str]] = None
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                cookies=self._client.cookies,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None)
            )

            if not response.ok:
                raise IOError(
                    f"YEPCHAT API Error: {response.status_code} {response.reason} - {response.text}"
                )

            # Track tokens for streaming
            prompt_tokens = count_tokens([m.get('content', '') for m in payload.get('messages', [])])
            completion_tokens = 0
            total_tokens = prompt_tokens

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    line = line.strip()
                    if line.startswith("data: "):
                        json_str = line[6:]
                        if json_str == "[DONE]":
                            break
                        try:
                            data = json.loads(json_str)
                            choices = data.get('choices')
                            if not choices and choices is not None:
                                continue
                            choice_data = choices[0] if choices else {}
                            delta_data = choice_data.get('delta', {})
                            finish_reason = choice_data.get('finish_reason')
                            content = delta_data.get('content')
                            role = delta_data.get('role', None)

                            # Count tokens for this chunk
                            chunk_tokens = count_tokens(content) if content else 0
                            completion_tokens += chunk_tokens
                            total_tokens = prompt_tokens + completion_tokens

                            if content is not None or role is not None:
                                delta = ChoiceDelta(content=content, role=role)
                                choice = Choice(index=0, delta=delta, finish_reason=finish_reason)
                                chunk = ChatCompletionChunk(
                                    id=request_id,
                                    choices=[choice],
                                    created=created_time,
                                    model=model,
                                )
                                # Set usage directly on the chunk object
                                chunk.usage = {
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "total_tokens": total_tokens,
                                    "estimated_cost": None
                                }
                                # Yield the chunk with usage information
                                yield chunk

                        except json.JSONDecodeError:
                            print(f"Warning: Could not decode JSON line: {json_str}")
                            continue

            # Yield final chunk with finish reason if not already sent
            delta = ChoiceDelta()
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
            )
            # Set usage directly on the chunk object
            chunk.usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": None
            }
            yield chunk

        except cloudscraper.exceptions.CloudflareChallengeError:
            pass

    def _create_non_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any], timeout: Optional[int] = None, proxies: Optional[Dict[str, str]] = None
    ) -> ChatCompletion:
        full_response_content = ""
        finish_reason = "stop"
        try:
            # Make a non-streaming request to the API
            payload_copy = payload.copy()
            payload_copy["stream"] = False
            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                cookies=self._client.cookies,
                json=payload_copy,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None)
            )
            if not response.ok:
                raise IOError(
                    f"YEPCHAT API Error: {response.status_code} {response.reason} - {response.text}"
                )
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                # YEPCHAT non-streaming returns message content in choices[0]['message']['content']
                full_response_content = data['choices'][0].get('message', {}).get('content', '')
                finish_reason = data['choices'][0].get('finish_reason', 'stop')
            else:
                full_response_content = ''
                finish_reason = 'stop'
        except Exception as e:
            print(f"Error obtaining non-stream response from YEPCHAT: {e}")
            finish_reason = "error"

        message = ChatCompletionMessage(
            role="assistant",
            content=full_response_content
        )
        choice = Choice(
            index=0,
            message=message,
            finish_reason=finish_reason
        )
        # Use count_tokens to compute usage
        prompt_tokens = count_tokens([m.get('content', '') for m in payload.get('messages', [])])
        completion_tokens = count_tokens(full_response_content)
        usage = CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        completion = ChatCompletion(
            id=request_id,
            choices=[choice],
            created=created_time,
            model=model,
            usage=usage,
        )
        return completion

class Chat(BaseChat):
    def __init__(self, client: 'YEPCHAT'):
        self.completions = Completions(client)

class YEPCHAT(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for YEPCHAT API.

    Usage:
        client = YEPCHAT()
        response = client.chat.completions.create(
            model="DeepSeek-R1-Distill-Qwen-32B",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """
    _base_models = ["DeepSeek-R1-Distill-Qwen-32B", "Mixtral-8x7B-Instruct-v0.1"]

    # Create AVAILABLE_MODELS as a list of base model names (no prefix)
    AVAILABLE_MODELS = _base_models
    required_auth = False

    def __init__(
        self,
        browser: str = "chrome"
    ):
        """
        Initialize the YEPCHAT client.

        Args:
            browser: Browser name for LitAgent to generate User-Agent.
        """
        self.timeout = None
        self.api_endpoint = "https://api.yep.com/v1/chat/completions"
        self.session = cloudscraper.create_scraper()  # Use cloudscraper

        # Initialize LitAgent for user agent generation and fingerprinting
        try:
            agent = LitAgent()
            fingerprint = agent.generate_fingerprint(browser=browser)
        except Exception as e:
            print(f"Warning: Failed to generate fingerprint with LitAgent: {e}. Using fallback.")
            # Fallback fingerprint data
            fingerprint = {
                "accept": "*/*",
                "accept_language": "en-US,en;q=0.9",
                "sec_ch_ua": '"Not/A)Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
                "platform": "Windows",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            }

        # Initialize headers using the fingerprint
        self.headers = {
            "Accept": fingerprint["accept"],
            "Accept-Language": fingerprint["accept_language"],
            "Content-Type": "application/json; charset=utf-8",
            "DNT": "1",
            "Origin": "https://yep.com",
            "Referer": "https://yep.com/",
            "Sec-CH-UA": fingerprint.get("sec_ch_ua") or '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{fingerprint.get("platform", "Windows")}"',
            "User-Agent": fingerprint.get("user_agent", ""),
            "x-forwarded-for": fingerprint.get("x-forwarded-for", "127.0.0.1"),
            "x-real-ip": fingerprint.get("x-real-ip", "127.0.0.1"),
            "x-client-ip": fingerprint.get("x-client-ip", "127.0.0.1"),
            "forwarded": fingerprint.get("forwarded", "for=127.0.0.1;proto=https"),
            "x-forwarded-proto": "https",
            "x-request-id": fingerprint.get("x-request-id", uuid.uuid4().hex[:8]),
        }
        self.session.headers.update(self.headers)

        # Generate cookies (consider if these need refreshing or specific values)
        self.cookies = {"__Host-session": uuid.uuid4().hex, '__cf_bm': uuid.uuid4().hex}

        # Initialize the chat interface
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)

    def convert_model_name(self, model: str) -> str:
        """
        Ensures the model name is valid for YEPCHAT.
        Returns the validated model name or raises an error if invalid.
        """
        if model in self.AVAILABLE_MODELS:
            return model
        else:
            # Raise error instead of defaulting, as model is mandatory in create()
            raise ValueError(f"Model '{model}' not supported by YEPCHAT. Available: {self.AVAILABLE_MODELS}")

# Example usage (optional, for testing)
if __name__ == '__main__':
    print("Testing YEPCHAT OpenAI-Compatible Client...")

    # Test Non-Streaming
    try:
        print("\n--- Non-Streaming Test (DeepSeek) ---")
        client = YEPCHAT()
        response = client.chat.completions.create(
            model="DeepSeek-R1-Distill-Qwen-32B",
            messages=[
                {"role": "user", "content": "Say 'Hello World'"}
            ],
            stream=False
        )
        print("Response:", response.choices[0].message.content)
        print("Usage:", response.usage)  # Will show 0 tokens
    except Exception as e:
        print(f"Non-Streaming Test Failed: {e}")

    # Test Streaming
    try:
        print("\n--- Streaming Test (Mixtral) ---")
        client_stream = YEPCHAT()
        stream = client_stream.chat.completions.create(
            model="Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "user", "content": "Write a short sentence about AI."}
            ],
            stream=True
        )
        print("Streaming Response:")
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
        print()  # Add a newline at the end

    except Exception as e:
        print(f"Streaming Test Failed: {e}")
