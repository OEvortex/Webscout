import base64
import hashlib
import json
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional, Union, cast

import requests

# Import base classes and utility structures
from webscout.Provider.OPENAI.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
    Tool,
)
from webscout.Provider.OPENAI.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
)

# ANSI escape codes for formatting
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"


class ChatGPTReversed:
    AVAILABLE_MODELS = [
        "auto",
        "gpt-5-1",
        "gpt-5-1-instant",
        "gpt-5-1-thinking",
        "gpt-5",
        "gpt-5-instant",
        "gpt-5-thinking",
        "gpt-4",
        "gpt-4.1",
        "gpt-4-1",
        "gpt-4.1-mini",
        "gpt-4-1-mini",
        "gpt-4.5",
        "gpt-4-5",
        "gpt-4o",
        "gpt-4o-mini",
        "o1",
        "o1-mini",
        "o3-mini",
        "o3-mini-high",
        "o4-mini",
        "o4-mini-high",
    ]
    csrf_token = None
    initialized = False

    _instance = None

    def __new__(cls, model="auto"):
        if cls._instance is None:
            cls._instance = super(ChatGPTReversed, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, model="auto"):
        if self.initialized:
            # Already initialized, just update model if needed
            if model not in self.AVAILABLE_MODELS:
                raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            self.model = model
            return

        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.model = model
        self.initialize()

    def initialize(self):
        ChatGPTReversed.initialized = True

    def random_ip(self):
        """Generate a random IP address."""
        return ".".join(str(random.randint(0, 255)) for _ in range(4))

    def random_uuid(self):
        """Generate a random UUID."""
        return str(uuid.uuid4())

    def random_float(self, min_val, max_val):
        """Generate a random float between min and max."""
        return round(random.uniform(min_val, max_val), 4)

    def simulate_bypass_headers(self, accept, spoof_address=False, pre_oai_uuid=None):
        """Simulate browser headers to bypass detection."""
        simulated = {
            "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "platform": "Windows",
            "mobile": "?0",
            "ua": 'Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132',
        }

        ip = self.random_ip()
        uuid_val = pre_oai_uuid or self.random_uuid()

        headers = {
            "accept": accept,
            "Content-Type": "application/json",
            "cache-control": "no-cache",
            "Referer": "https://chatgpt.com/",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "oai-device-id": uuid_val,
            "User-Agent": simulated["agent"],
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": f"{simulated['ua']}",
            "sec-ch-ua-mobile": simulated["mobile"],
            "sec-ch-ua-platform": f"{simulated['platform']}",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
        }

        if spoof_address:
            headers.update(
                {
                    "X-Forwarded-For": ip,
                    "X-Originating-IP": ip,
                    "X-Remote-IP": ip,
                    "X-Remote-Addr": ip,
                    "X-Host": ip,
                    "X-Forwarded-Host": ip,
                }
            )

        return headers

    def generate_proof_token(self, seed: str, difficulty: str, user_agent: Optional[str] = None):
        """
        Improved proof-of-work implementation based on gpt4free/g4f/Provider/openai/proofofwork.py

        Args:
            seed: The seed string for the challenge
            difficulty: The difficulty hex string
            user_agent: Optional user agent string

        Returns:
            The proof token starting with 'gAAAAAB'
        """
        if user_agent is None:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"

        screen = random.choice([3008, 4010, 6000]) * random.choice([1, 2, 4])

        # Get current UTC time
        now_utc = datetime.now(timezone.utc)
        parse_time = now_utc.strftime("%a, %d %b %Y %H:%M:%S GMT")

        proof_token = [
            screen,
            parse_time,
            None,
            0,
            user_agent,
            "https://tcr9i.chat.openai.com/v2/35536E1E-65B4-4D96-9D97-6ADB7EFF8147/api.js",
            "dpl=1440a687921de39ff5ee56b92807faaadce73f13",
            "en",
            "en-US",
            None,
            "plugins−[object PluginArray]",
            random.choice(
                [
                    "_reactListeningcfilawjnerp",
                    "_reactListening9ne2dfo1i47",
                    "_reactListening410nzwhan2a",
                ]
            ),
            random.choice(["alert", "ontransitionend", "onprogress"]),
        ]

        diff_len = len(difficulty)
        for i in range(100000):
            proof_token[3] = i
            json_data = json.dumps(proof_token)
            base = base64.b64encode(json_data.encode()).decode()
            hash_value = hashlib.sha3_512((seed + base).encode()).digest()

            if hash_value.hex()[:diff_len] <= difficulty:
                return "gAAAAAB" + base

        # Fallback
        fallback_base = base64.b64encode(f'"{seed}"'.encode()).decode()
        return "gAAAAABwQ8Lk5FbGpA2NcR9dShT6gYjU7VxZ4D" + fallback_base

    def solve_sentinel_challenge(self, seed, difficulty):
        """Solve the sentinel challenge for authentication using improved algorithm."""
        return self.generate_proof_token(seed, difficulty)

    def generate_fake_sentinel_token(self):
        """Generate a fake sentinel token for initial authentication."""
        prefix = "gAAAAAC"

        # More realistic screen sizes
        screen = random.choice([3008, 4010, 6000]) * random.choice([1, 2, 4])

        # Get current UTC time
        now_utc = datetime.now(timezone.utc)
        parse_time = now_utc.strftime("%a, %d %b %Y %H:%M:%S GMT")

        config = [
            screen,
            parse_time,
            4294705152,
            0,
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "de",
            "de",
            401,
            "mediaSession",
            "location",
            "scrollX",
            self.random_float(1000, 5000),
            str(uuid.uuid4()),
            "",
            12,
            int(time.time() * 1000),
        ]

        base64_str = base64.b64encode(json.dumps(config).encode()).decode()
        return prefix + base64_str

    def parse_response(self, input_text):
        """Parse the response from ChatGPT.

        Args:
            input_text (str): The response text from ChatGPT.

        Returns:
            The complete response as a string.
        """
        parts = [part.strip() for part in input_text.split("\n") if part.strip()]

        for part in parts:
            try:
                if part.startswith("data: "):
                    json_data = json.loads(part[6:])
                    if (
                        json_data.get("message")
                        and json_data["message"].get("status") == "finished_successfully"
                        and json_data["message"].get("metadata", {}).get("is_complete")
                    ):
                        return json_data["message"]["content"]["parts"][0]
            except Exception:
                pass

        return input_text  # Return raw text if parsing fails or no complete message found

    def rotate_session_data(self):
        """Rotate session data to maintain fresh authentication."""
        uuid_val = self.random_uuid()
        csrf_token = self.get_csrf_token(uuid_val)
        sentinel_token = self.get_sentinel_token(uuid_val, csrf_token)

        ChatGPTReversed.csrf_token = csrf_token

        return {"uuid": uuid_val, "csrf": csrf_token, "sentinel": sentinel_token}

    def get_csrf_token(self, uuid_val):
        """Get CSRF token for authentication."""
        if ChatGPTReversed.csrf_token is not None:
            return ChatGPTReversed.csrf_token

        headers = self.simulate_bypass_headers(
            accept="application/json", spoof_address=True, pre_oai_uuid=uuid_val
        )

        response = requests.get("https://chatgpt.com/api/auth/csrf", headers=headers)

        data = response.json()
        if "csrfToken" not in data:
            raise Exception("Failed to fetch required CSRF token")

        return data["csrfToken"]

    def get_sentinel_token(self, uuid_val, csrf):
        """Get sentinel token for authentication."""
        headers = self.simulate_bypass_headers(
            accept="application/json", spoof_address=True, pre_oai_uuid=uuid_val
        )

        test = self.generate_fake_sentinel_token()

        response = requests.post(
            "https://chatgpt.com/backend-anon/sentinel/chat-requirements",
            json={"p": test},
            headers={
                **headers,
                "Cookie": f"__Host-next-auth.csrf-token={csrf}; oai-did={uuid_val}; oai-nav-state=1;",
            },
        )

        data = response.json()
        if "token" not in data or "proofofwork" not in data:
            raise Exception("Failed to fetch required sentinel token")

        oai_sc = None
        for cookie in response.cookies:
            if cookie.name == "oai-sc":
                oai_sc = cookie.value
                break

        if not oai_sc:
            raise Exception("Failed to fetch required oai-sc token")

        challenge_token = self.solve_sentinel_challenge(
            data["proofofwork"]["seed"], data["proofofwork"]["difficulty"]
        )

        return {"token": data["token"], "proof": challenge_token, "oaiSc": oai_sc}

    def complete(self, message, model=None):
        """Complete a message using ChatGPT.

        Args:
            message (str): The message to send to ChatGPT.
            model (str, optional): The model to use. If None, uses the model specified during initialization.
                                   Defaults to None.

        Returns:
            The complete response as a string.
        """
        if not ChatGPTReversed.initialized:
            raise Exception(
                "ChatGPTReversed has not been initialized. Please initialize the instance before calling this method."
            )

        # Use the provided model or fall back to the instance model
        selected_model = model if model else self.model

        # Validate the model
        if selected_model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {selected_model}. Choose from: {self.AVAILABLE_MODELS}"
            )

        session_data = self.rotate_session_data()

        headers = self.simulate_bypass_headers(
            accept="plain/text",  # Changed accept header as we expect full response now
            spoof_address=True,
            pre_oai_uuid=session_data["uuid"],
        )

        headers.update(
            {
                "Cookie": f"__Host-next-auth.csrf-token={session_data['csrf']}; oai-did={session_data['uuid']}; oai-nav-state=1; oai-sc={session_data['sentinel']['oaiSc']};",
                "openai-sentinel-chat-requirements-token": session_data["sentinel"]["token"],
                "openai-sentinel-proof-token": session_data["sentinel"]["proof"],
            }
        )

        payload = {
            "action": "next",
            "messages": [
                {
                    "id": self.random_uuid(),
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": [message]},
                    "metadata": {},
                }
            ],
            "parent_message_id": self.random_uuid(),
            "model": selected_model,  # Use the selected model
            "timezone_offset_min": -120,
            "suggestions": [],
            "history_and_training_disabled": False,
            "conversation_mode": {
                "kind": "primary_assistant",
                "plugin_ids": None,  # Ensure web search is not used
            },
            "force_paragen": False,
            "force_paragen_model_slug": "",
            "force_nulligen": False,
            "force_rate_limit": False,
            "reset_rate_limits": False,
            "websocket_request_id": self.random_uuid(),
            "force_use_sse": True,  # Keep SSE for receiving the full response
        }

        response = requests.post(
            "https://chatgpt.com/backend-anon/conversation", json=payload, headers=headers
        )

        if response.status_code != 200:
            raise Exception(f"HTTP error! status: {response.status_code}")

        return self.parse_response(response.text)


class Completions(BaseCompletions):
    def __init__(self, client: "ChatGPT"):
        self._client = client
        self._chatgpt_reversed = None

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Union[Tool, Dict[str, Any]]]] = None,  # Support for tool definitions
        tool_choice: Optional[
            Union[str, Dict[str, Any]]
        ] = None,  # Support for tool_choice parameter
        timeout: Optional[int] = None,
        proxies: Optional[dict] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Create a chat completion with ChatGPT API.

        Args:
            model: The model to use (from AVAILABLE_MODELS)
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter (0-1)
            tools: List of tool definitions available for the model to use
            tool_choice: Control over which tool the model should use
            **kwargs: Additional parameters to pass to the API

        Returns:
            If stream=False, returns a ChatCompletion object
            If stream=True, returns a Generator yielding ChatCompletionChunk objects
        """
        # Initialize ChatGPTReversed if not already initialized
        if self._chatgpt_reversed is None:
            self._chatgpt_reversed = ChatGPTReversed(model=model)

        # Use streaming implementation if requested
        if stream:
            return self._create_streaming(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                tools=tools,
                tool_choice=tool_choice,
                timeout=timeout,
                proxies=proxies,
                **kwargs,
            )

        # Otherwise use non-streaming implementation
        return self._create_non_streaming(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            timeout=timeout,
            proxies=proxies,
            **kwargs,
        )

    def _create_streaming(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Union[Tool, Dict[str, Any]]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: Optional[int] = None,
        proxies: Optional[dict] = None,
        **kwargs: Any,
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Implementation for streaming chat completions."""
        try:
            # Generate request ID and timestamp
            request_id = str(uuid.uuid4())
            created_time = int(time.time())

            # Get the last user message
            last_user_message = None
            for msg in reversed(messages):
                if msg["role"] == "user":
                    last_user_message = msg["content"]
                    break

            if not last_user_message:
                raise ValueError("No user message found in the conversation")

            # Initialize ChatGPTReversed if not already initialized
            if self._chatgpt_reversed is None:
                self._chatgpt_reversed = ChatGPTReversed(model=model)

            # Create a proper streaming request to ChatGPT
            session_data = self._chatgpt_reversed.rotate_session_data()

            headers = self._chatgpt_reversed.simulate_bypass_headers(
                accept="text/event-stream", spoof_address=True, pre_oai_uuid=session_data["uuid"]
            )

            headers.update(
                {
                    "Cookie": f"__Host-next-auth.csrf-token={session_data['csrf']}; oai-did={session_data['uuid']}; oai-nav-state=1; oai-sc={session_data['sentinel']['oaiSc']};",
                    "openai-sentinel-chat-requirements-token": session_data["sentinel"]["token"],
                    "openai-sentinel-proof-token": session_data["sentinel"]["proof"],
                }
            )

            # Format messages properly for ChatGPT
            formatted_messages = []
            for i, msg in enumerate(messages):
                formatted_messages.append(
                    {
                        "id": str(uuid.uuid4()),
                        "author": {"role": msg["role"]},
                        "content": {"content_type": "text", "parts": [msg["content"]]},
                        "metadata": {},
                    }
                )

            payload = {
                "action": "next",
                "messages": formatted_messages,
                "parent_message_id": str(uuid.uuid4()),
                "model": model,
                "timezone_offset_min": -120,
                "suggestions": [],
                "history_and_training_disabled": False,
                "conversation_mode": {"kind": "primary_assistant", "plugin_ids": None},
                "force_paragem": False,
                "force_paragem_model_slug": "",
                "force_nulligen": False,
                "force_rate_limit": False,
                "reset_rate_limits": False,
                "websocket_request_id": str(uuid.uuid4()),
                "force_use_sse": True,
            }

            # Add optional parameters if provided
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if temperature is not None:
                payload["temperature"] = temperature
            if top_p is not None:
                payload["top_p"] = top_p

            # Make the actual streaming request
            response = requests.post(
                "https://chatgpt.com/backend-anon/conversation",
                json=payload,
                headers=headers,
                stream=True,
                timeout=timeout or 30,
            )

            response.raise_for_status()

            # Track conversation state
            full_content = ""
            prompt_tokens = count_tokens(str(messages))
            completion_tokens = 0
            total_tokens = prompt_tokens

            # Process the streaming response
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        # Handle [DONE] message
                        if data_str.strip() == "[DONE]":
                            # Final chunk with finish_reason
                            delta = ChoiceDelta(content=None)
                            choice = Choice(index=0, delta=delta, finish_reason="stop")
                            chunk = ChatCompletionChunk(
                                id=request_id, choices=[choice], created=created_time, model=model
                            )
                            chunk.usage = {
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "total_tokens": total_tokens,
                            }
                            yield chunk
                            break

                        try:
                            data = json.loads(data_str)

                            # Handle different types of messages
                            if data.get("message"):
                                message = data["message"]

                                # Handle assistant responses
                                if message.get("author", {}).get("role") == "assistant":
                                    content_parts = message.get("content", {}).get("parts", [])
                                    if content_parts:
                                        new_content = content_parts[0]

                                        # Get the delta (new content since last chunk)
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
                                            delta = ChoiceDelta(
                                                content=delta_content, role="assistant"
                                            )
                                            choice = Choice(
                                                index=0, delta=delta, finish_reason=None
                                            )
                                            chunk = ChatCompletionChunk(
                                                id=request_id,
                                                choices=[choice],
                                                created=created_time,
                                                model=model,
                                            )
                                            chunk.usage = {
                                                "prompt_tokens": prompt_tokens,
                                                "completion_tokens": completion_tokens,
                                                "total_tokens": total_tokens,
                                            }
                                            yield chunk

                                # Handle finish status
                                if message.get("status") == "finished_successfully":
                                    pass

                            elif data.get("type") == "message_stream_complete":
                                # Stream is complete
                                pass

                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue

        except Exception as e:
            raise IOError(f"ChatGPT request failed: {e}") from e

    def _create_non_streaming(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Union[Tool, Dict[str, Any]]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: Optional[int] = None,
        proxies: Optional[dict] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        """Implementation for non-streaming chat completions."""
        try:
            # Generate request ID and timestamp
            request_id = str(uuid.uuid4())
            created_time = int(time.time())

            # Initialize ChatGPTReversed if not already initialized
            if self._chatgpt_reversed is None:
                self._chatgpt_reversed = ChatGPTReversed(model=model)

            # Create a proper request to ChatGPT
            session_data = self._chatgpt_reversed.rotate_session_data()

            headers = self._chatgpt_reversed.simulate_bypass_headers(
                accept="text/event-stream", spoof_address=True, pre_oai_uuid=session_data["uuid"]
            )

            headers.update(
                {
                    "Cookie": f"__Host-next-auth.csrf-token={session_data['csrf']}; oai-did={session_data['uuid']}; oai-nav-state=1; oai-sc={session_data['sentinel']['oaiSc']};",
                    "openai-sentinel-chat-requirements-token": session_data["sentinel"]["token"],
                    "openai-sentinel-proof-token": session_data["sentinel"]["proof"],
                }
            )

            # Format messages properly for ChatGPT
            formatted_messages = []
            for i, msg in enumerate(messages):
                formatted_messages.append(
                    {
                        "id": str(uuid.uuid4()),
                        "author": {"role": msg["role"]},
                        "content": {"content_type": "text", "parts": [msg["content"]]},
                        "metadata": {},
                    }
                )

            payload = {
                "action": "next",
                "messages": formatted_messages,
                "parent_message_id": str(uuid.uuid4()),
                "model": model,
                "timezone_offset_min": -120,
                "suggestions": [],
                "history_and_training_disabled": False,
                "conversation_mode": {"kind": "primary_assistant", "plugin_ids": None},
                "force_paragem": False,
                "force_paragem_model_slug": "",
                "force_nulligen": False,
                "force_rate_limit": False,
                "reset_rate_limits": False,
                "websocket_request_id": str(uuid.uuid4()),
                "force_use_sse": True,
            }

            # Add optional parameters if provided
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if temperature is not None:
                payload["temperature"] = temperature
            if top_p is not None:
                payload["top_p"] = top_p

            # Make the request and collect full response
            response = requests.post(
                "https://chatgpt.com/backend-anon/conversation",
                json=payload,
                headers=headers,
                stream=True,
                timeout=timeout or 30,
            )

            response.raise_for_status()

            # Collect and parse the full response
            full_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        # Handle [DONE] message
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)

                            # Handle assistant responses
                            if (
                                data.get("message")
                                and data["message"].get("author", {}).get("role") == "assistant"
                            ):
                                content_parts = data["message"].get("content", {}).get("parts", [])
                                if content_parts:
                                    full_response = content_parts[0]

                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue

            # Create the completion message
            message = ChatCompletionMessage(role="assistant", content=full_response)

            # Create the choice
            choice = Choice(index=0, message=message, finish_reason="stop")

            # Calculate token usage using count_tokens
            # Count tokens in the input messages (prompt)
            prompt_tokens = count_tokens(str(messages))
            # Count tokens in the response (completion)
            completion_tokens = count_tokens(full_response)
            total_tokens = prompt_tokens + completion_tokens

            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            # Create the completion object with correct OpenAI format
            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )

            return completion

        except Exception as e:
            print(f"{RED}Error during ChatGPT non-stream request: {e}{RESET}")
            raise IOError(f"ChatGPT request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "ChatGPT"):
        self.completions = Completions(client)


class ChatGPT(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for ChatGPT API.

    Usage:
        client = ChatGPT()
        response = client.chat.completions.create(
            model="auto",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """

    required_auth = False

    def __init__(
        self,
        api_key: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        proxies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the ChatGPT client.

        Args:
            api_key: Optional API key (not used by ChatGPTReversed but included for interface compatibility)
            tools: Optional list of tools to register with the provider
            proxies: Optional proxy configuration dict, e.g. {"http": "http://proxy:8080", "https": "https://proxy:8080"}
        """
        super().__init__(api_key=api_key, tools=tools, proxies=proxies)
        # Initialize chat interface
        self.chat = Chat(self)

    @property
    def AVAILABLE_MODELS(self):
        return ChatGPTReversed.AVAILABLE_MODELS

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(self.AVAILABLE_MODELS)


if __name__ == "__main__":
    # Example usage
    client = ChatGPT()
    response = client.chat.completions.create(
        model="o4-mini-high", messages=[{"role": "user", "content": "How many r in strawberry"}]
    )
    if isinstance(response, ChatCompletion):
        if response.choices[0].message and response.choices[0].message.content:
            print(response.choices[0].message.content)
    print()
