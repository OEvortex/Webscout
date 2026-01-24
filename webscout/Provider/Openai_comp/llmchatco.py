import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

import requests

# Import base classes and utility structures
from webscout.Provider.Openai_comp.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from webscout.Provider.Openai_comp.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,  # Import format_prompt
    Choice,
    ChoiceDelta,
    CompletionUsage,
    get_last_user_message,
    get_system_prompt,
)

# Attempt to import LitAgent, fallback if not available
from ...litagent import LitAgent

# --- LLMChatCo Client ---


class Completions(BaseCompletions):
    def __init__(self, client: "LLMChatCo"):
        self._client = client

    def create(
        self,
        *,
        model: str,  # Model is now mandatory per request
        messages: List[Dict[str, str]],
        max_tokens: Optional[
            int
        ] = 2048,  # Note: LLMChatCo doesn't seem to use max_tokens directly in payload
        stream: bool = False,
        temperature: Optional[
            float
        ] = None,  # Note: LLMChatCo doesn't seem to use temperature directly in payload
        top_p: Optional[
            float
        ] = None,  # Note: LLMChatCo doesn't seem to use top_p directly in payload
        web_search: bool = False,  # LLMChatCo specific parameter
        system_prompt: Optional[
            str
        ] = "You are a helpful assistant.",  # Default system prompt if not provided
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create
        """
        if model not in self._client.AVAILABLE_MODELS:
            # Raise error as model is mandatory and must be valid for this provider
            raise ValueError(
                f"Model '{model}' not supported by LLMChatCo. Available: {self._client.AVAILABLE_MODELS}"
            )
        actual_model = model

        # Determine the effective system prompt
        effective_system_prompt = system_prompt  # Use the provided system_prompt or its default
        get_system_prompt(messages)
        # If a system prompt is also in messages, the explicit one takes precedence.
        # We'll use the effective_system_prompt determined above.

        # Prepare final messages list, ensuring only one system message at the start
        final_messages = []
        if effective_system_prompt:
            final_messages.append({"role": "system", "content": effective_system_prompt})
        final_messages.extend([msg for msg in messages if msg.get("role") != "system"])

        # Extract the last user prompt using the utility function for the separate 'prompt' field
        last_user_prompt = get_last_user_message(final_messages)

        # Note: format_prompt is not directly used here as the API requires the structured 'messages' list
        # and a separate 'prompt' field, rather than a single formatted string.

        # Generate a unique ID for this message
        thread_item_id = "".join(str(uuid.uuid4()).split("-"))[:20]

        payload = {
            "mode": actual_model,
            "prompt": last_user_prompt,  # LLMChatCo seems to require the last prompt separately
            "threadId": self._client.thread_id,
            "messages": final_messages,  # Use the reconstructed final_messages list
            "mcpConfig": {},  # Keep structure as observed
            "threadItemId": thread_item_id,
            "parentThreadItemId": "",  # Assuming no parent for simplicity
            "webSearch": web_search,
            "showSuggestions": True,  # Keep structure as observed
        }

        # Add any extra kwargs to the payload if needed, though LLMChatCo seems limited
        payload.update(kwargs)

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(
                request_id, created_time, actual_model, payload, timeout, proxies
            )
        else:
            return self._create_non_stream(
                request_id, created_time, actual_model, payload, timeout, proxies
            )

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),
            )

            if not response.ok:
                raise IOError(
                    f"LLMChatCo API Error: {response.status_code} {response.reason} - {response.text}"
                )

            full_response_text = ""
            current_event = None
            buffer = ""

            for chunk_bytes in response.iter_content(chunk_size=None, decode_unicode=False):
                if not chunk_bytes:
                    continue

                buffer += chunk_bytes.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line:  # End of an event block
                        current_event = None
                        continue

                    if line.startswith("event:"):
                        current_event = line[len("event:") :].strip()
                    elif line.startswith("data:"):
                        data_content = line[len("data:") :].strip()
                        if data_content and current_event == "answer":
                            try:
                                json_data = json.loads(data_content)
                                answer_data = json_data.get("answer", {})
                                text_chunk = answer_data.get("text", "")
                                full_text = answer_data.get("fullText")
                                status = answer_data.get("status")

                                # Prefer fullText if available and status is COMPLETED
                                if full_text is not None and status == "COMPLETED":
                                    delta_content = full_text[len(full_response_text) :]
                                    full_response_text = full_text  # Update full response tracker
                                elif text_chunk is not None:
                                    # Calculate delta based on potentially partial 'text' field
                                    delta_content = text_chunk[len(full_response_text) :]
                                    full_response_text = text_chunk  # Update full response tracker
                                else:
                                    delta_content = None

                                if delta_content:
                                    delta = ChoiceDelta(content=delta_content, role="assistant")
                                    choice = Choice(index=0, delta=delta, finish_reason=None)
                                    chunk = ChatCompletionChunk(
                                        id=request_id,
                                        choices=[choice],
                                        created=created_time,
                                        model=model,
                                    )
                                    yield chunk

                            except json.JSONDecodeError:
                                print(f"Warning: Could not decode JSON data line: {data_content}")
                                continue
                        elif data_content and current_event == "done":
                            # The 'done' event signals the end of the stream
                            delta = ChoiceDelta()  # Empty delta
                            choice = Choice(index=0, delta=delta, finish_reason="stop")
                            chunk = ChatCompletionChunk(
                                id=request_id,
                                choices=[choice],
                                created=created_time,
                                model=model,
                            )
                            yield chunk
                            return  # End the generator

        except requests.exceptions.RequestException as e:
            print(f"Error during LLMChatCo stream request: {e}")
            raise IOError(f"LLMChatCo request failed: {e}") from e
        except Exception as e:
            print(f"Unexpected error during LLMChatCo stream: {e}")
            raise IOError(f"LLMChatCo stream processing failed: {e}") from e

        # Fallback final chunk if 'done' event wasn't received properly
        delta = ChoiceDelta()
        choice = Choice(index=0, delta=delta, finish_reason="stop")
        chunk = ChatCompletionChunk(
            id=request_id,
            choices=[choice],
            created=created_time,
            model=model,
        )
        yield chunk

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        # Non-streaming requires accumulating stream chunks
        full_response_content = ""
        finish_reason = "stop"  # Assume stop unless error occurs

        try:
            stream_generator = self._create_stream(
                request_id, created_time, model, payload, timeout, proxies
            )
            for chunk in stream_generator:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    full_response_content += chunk.choices[0].delta.content
                if chunk.choices and chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

        except IOError as e:
            print(f"Error obtaining non-stream response from LLMChatCo: {e}")
            # Return a partial or error response if needed, or re-raise
            # For simplicity, we'll return what we have, potentially empty
            finish_reason = "error"  # Indicate an issue

        # Construct the final ChatCompletion object
        message = ChatCompletionMessage(role="assistant", content=full_response_content)
        choice = Choice(index=0, message=message, finish_reason=finish_reason)
        # Usage data is not provided by this API, so set to 0
        usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        completion = ChatCompletion(
            id=request_id,
            choices=[choice],
            created=created_time,
            model=model,
            usage=usage,
        )
        return completion


class Chat(BaseChat):
    def __init__(self, client: "LLMChatCo"):
        self.completions = Completions(client)


class LLMChatCo(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for LLMChat.co API.

    Usage:
        client = LLMChatCo()
        response = client.chat.completions.create(
            model="gemini-flash-2.0", # Model must be specified here
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """

    required_auth = False  # No API key required for LLMChatCo
    AVAILABLE_MODELS = [
        "gemini-flash-2.0",  # Default model
        "llama-4-scout",
        "gpt-4o-mini",
        # "gpt-4.1",
        # "gpt-4.1-mini",
        "gpt-4.1-nano",
    ]

    def __init__(
        self,
        timeout: int = 60,
        browser: str = "chrome",  # For User-Agent generation
    ):
        """
        Initialize the LLMChatCo client.

        Args:
            timeout: Request timeout in seconds.
            browser: Browser name for LitAgent to generate User-Agent.
        """
        # Removed model, system_prompt, proxies parameters

        self.timeout = timeout
        # Removed self.system_prompt assignment
        self.api_endpoint = "https://llmchat.co/api/completion"
        self.session = requests.Session()
        self.thread_id = str(uuid.uuid4())  # Unique thread ID per client instance

        # Removed proxy handling block

        # Initialize LitAgent for user agent generation and fingerprinting
        try:
            agent = LitAgent()
            fingerprint = agent.generate_fingerprint(browser=browser)
        except Exception as e:
            print(f"Warning: Failed to generate fingerprint with LitAgent: {e}. Using fallback.")
            # Fallback fingerprint data
            fingerprint = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept_language": "en-US,en;q=0.9",
                "sec_ch_ua": '"Not/A)Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
                "platform": "Windows",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            }

        # Initialize headers using the fingerprint
        self.headers = {
            "Accept": fingerprint["accept"],
            "Accept-Language": fingerprint["accept_language"],
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Origin": "https://llmchat.co",  # Specific origin for LLMChatCo
            "Pragma": "no-cache",
            "Referer": f"https://llmchat.co/chat/{self.thread_id}",  # Specific referer for LLMChatCo
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-CH-UA": fingerprint["sec_ch_ua"]
            or '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',  # Fallback if empty
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{fingerprint["platform"]}"',
            "User-Agent": fingerprint["user_agent"],
            "DNT": "1",  # Added back from previous version
        }
        self.session.headers.update(self.headers)

        # Initialize the chat interface
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    # Example usage
    client = LLMChatCo()
    response = client.chat.completions.create(
        model="gemini-flash-2.0",
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        stream=False,
    )
    if isinstance(response, ChatCompletion):
        if response.choices[0].message and response.choices[0].message.content:
            print(response.choices[0].message.content)
