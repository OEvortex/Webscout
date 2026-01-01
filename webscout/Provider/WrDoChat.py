import json
import re
from datetime import datetime
from typing import Any, Dict, Generator, Optional, Union, cast
from uuid import uuid4

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent


class WrDoChat(Provider):
    """
    A class to interact with the oi.wr.do chat API.

    Attributes:
        system_prompt (str): The system prompt to define the assistant's role.
        model (str): The model to use for chat completion.

    Examples:
        >>> from webscout.Provider.api_request import WrDoChat
        >>> ai = WrDoChat(cookies_path="cookies.json")
        >>> response = ai.chat("What's the weather today?")
        >>> print(response)
    """

    required_auth = True
    AVAILABLE_MODELS = [
        "deepseek-chat-v3-0324",
        "deepseek-r1",
        "deepseek-r1-distill",
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp",
        "gemini-2.5-flash-preview-04-17",
        "gemini-2.5-pro-exp-03-25",
        "gemma2-9b-it",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "gpt-4o-mini",
        "grok-2-1212",
        "grok-3-mini",
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "llama-4-maverick-17b",
        "llama3-70b-8192",
        "mai-ds-r1",
        "qwen-qwq-32b",
        "qwen3-30b-a3b",
    ]

    def __init__(
        self,
        cookies_path: str,
        is_conversation: bool = True,
        max_tokens: int = 2000,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "gemini-2.5-flash-preview-04-17",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """
        Initialize the WrDoChat client.

        Args:
            cookies_path (str): Path to the cookies JSON file for authentication.
            is_conversation (bool): Whether to maintain conversation history.
            max_tokens (int): Maximum number of tokens to generate.
            timeout (int): Request timeout in seconds.
            intro (str): Introduction message for conversation.
            filepath (str): Path to save conversation history.
            update_file (bool): Whether to update conversation history file.
            proxies (dict): Proxy configuration for requests.
            history_offset (int): Offset for conversation history.
            act (str): Role/act for the conversation.
            model (str): Model to use for completion.
            system_prompt (str): System prompt for the assistant.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.api_endpoint = "https://oi.wr.do/api/chat"
        self.cookies_path = cookies_path
        self.cookies = self._load_cookies()

        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://oi.wr.do",
            "user-agent": self.agent.random(),
            "x-requested-with": "XMLHttpRequest",
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        # Update session headers and proxies
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

        # Apply cookies to session
        if self.cookies:
            for name, value in self.cookies.items():
                self.session.cookies.set(name, value, domain="oi.wr.do")

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = (
                AwesomePrompts().get_act(
                    cast(Union[str, int], act),
                    default=self.conversation.intro,
                    case_insensitive=True,
                )
                or self.conversation.intro
            )
        elif intro:
            self.conversation.intro = intro

        self.last_message_id = None  # Store the last message ID from the API

    def _load_cookies(self) -> Optional[Dict[str, str]]:
        """Load cookies from a JSON file and return them as a dictionary."""
        try:
            with open(self.cookies_path, "r") as f:
                cookies_data = json.load(f)
            return {
                cookie["name"]: cookie["value"]
                for cookie in cookies_data
                if "name" in cookie and "value" in cookie
            }
        except Exception as e:
            raise exceptions.AuthenticationError(f"Failed to load cookies: {str(e)}")

    def _wrdo_extractor(self, line: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from the oi.wr.do stream format.

        Format:
        f:{"messageId":"..."}
        0:"content chunk"
        e:{"finishReason":"stop",...}
        d:{"finishReason":"stop",...}
        """
        if isinstance(line, str):
            # Handle content chunks that start with "0:"
            match = re.search(r'0:"(.*?)"', line)
            if match:
                # Decode potential unicode escapes like \u00e9
                content = match.group(1).encode().decode("unicode_escape")
                return content.replace("\\\\", "\\").replace(
                    '\\"', '"'
                )  # Handle escaped backslashes and quotes

            # Store message ID from 'f:' response
            elif line.startswith("f:"):
                try:
                    msg_data = json.loads(line[2:])  # Skip 'f:' prefix
                    self.last_message_id = msg_data.get("messageId")
                except json.JSONDecodeError:
                    pass
            # Check for error messages in 'e:' response
            elif line.startswith("e:"):
                try:
                    error_data = json.loads(line[2:])  # Skip 'e:' prefix
                    if error_data.get("error"):
                        raise exceptions.FailedToGenerateResponseError(
                            f"API Error: {error_data['error']}"
                        )
                except json.JSONDecodeError:
                    pass
        return None

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """
        Send a message to the oi.wr.do API.

        Args:
            prompt (str): The prompt to send.
            stream (bool): Whether to stream the response.
            raw (bool): Whether to return raw response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to use conversation context.

        Returns:
            Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]: The API response.
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        chat_id = str(uuid4())
        message_id = str(uuid4())
        from datetime import timezone

        current_time = datetime.now(timezone.utc).isoformat() + "Z"

        payload = {
            "id": chat_id,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {
                    "id": message_id,
                    "createdAt": current_time,
                    "role": "user",
                    "content": conversation_prompt,
                    "parts": [{"type": "text", "text": conversation_prompt}],
                },
            ],
            "selectedChatModel": self.model,
        }

        def for_stream():
            try:
                self.headers["referer"] = f"https://oi.wr.do/chat/{chat_id}"
                response = self.session.post(
                    self.api_endpoint,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                if response.status_code == 401:
                    raise exceptions.AuthenticationError(
                        "Authentication failed. Please check your cookies."
                    )
                response.raise_for_status()
                streaming_response = ""
                has_content = False
                processed_stream = sanitize_stream(
                    data=response.iter_lines(),
                    intro_value=None,  # No intro to remove
                    to_json=False,  # Response is not JSON
                    content_extractor=self._wrdo_extractor,
                    yield_raw_on_error=False,
                    raw=raw,
                )
                for content in processed_stream:
                    # Always yield as string, even in raw mode
                    if isinstance(content, bytes):
                        content = content.decode("utf-8", errors="ignore")
                    if content and isinstance(content, str):
                        streaming_response += content
                        has_content = True
                        yield content if raw else {"text": content}
                if has_content:
                    self.last_response = {"text": streaming_response}
                    self.conversation.update_chat_history(
                        prompt, self.get_message(self.last_response)
                    )
                else:
                    raise exceptions.FailedToGenerateResponseError("No content received from API")
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {e}")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"An error occurred: {str(e)}")

        def for_non_stream():
            response_text = ""
            try:
                for chunk in for_stream():
                    if isinstance(chunk, dict) and "text" in chunk:
                        response_text += chunk["text"]
                    elif raw and isinstance(chunk, str):
                        response_text += chunk
            except Exception as e:
                if not response_text:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to get response: {str(e)}"
                    )
            return response_text if raw else {"text": response_text}

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Generate a response to a prompt.

        Args:
            prompt (str): The prompt to send.
            stream (bool): Whether to stream the response.
            optimizer (str): Optimizer to use for the prompt.
            conversationally (bool): Whether to use conversation context.
            **kwargs: Additional parameters including raw.

        Returns:
            Union[str, Generator[str, None, None]]: The generated response.
        """
        raw = kwargs.get("raw", False)

        def for_stream():
            for response in self.ask(
                prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield response
                else:
                    yield self.get_message(response)

        def for_non_stream():
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return result
            else:
                return self.get_message(result)

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        """
        Extract message from response.

        Args:
            response (Response): The response dictionary.

        Returns:
            str: The extracted message.
        """
        if not isinstance(response, dict):
            return str(response)
        response_dict = cast(Dict[str, Any], response)
        return response_dict.get("text", "")


if __name__ == "__main__":
    import json

    from rich import print

    # Example usage
    ai = WrDoChat(cookies_path="cookies.json")
    response = ai.chat("write me a poem about AI", stream=True)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
