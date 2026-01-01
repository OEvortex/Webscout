import json
import uuid
from datetime import datetime
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import (  # Import sanitize_stream
    AwesomePrompts,
    Conversation,
    Optimizers,
    sanitize_stream,
)
from webscout.litagent import LitAgent


class IBM(Provider):
    """
    A class to interact with the IBM Granite Playground API.
    """
    required_auth = False
    AVAILABLE_MODELS = [
        "granite-chat",
        "granite-thinking",
        "granite-search",
        "granite-research",
    ]

    @staticmethod
    def _ibm_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from IBM Granite stream JSON objects."""
        if isinstance(chunk, dict):
            if chunk.get("type") == "message.part":
                part = chunk.get("part", {})
                return part.get("content")
        return None

    def get_token(self) -> str:
        """Fetches a fresh dynamic Bearer token from the IBM UI auth endpoint."""
        auth_url = "https://www.ibm.com/granite/playground/api/v1/ui/auth"
        try:
            # Use the existing session to benefit from cookies/headers
            response = self.session.get(auth_url, timeout=self.timeout, impersonate="chrome110")
            if response.ok:
                data = response.json()
                token = data.get("token")
                if token:
                    self.headers["Authorization"] = f"Bearer {token}"
                    self.session.headers.update(self.headers)
                    return token
            raise exceptions.FailedToGenerateResponseError(f"Failed to fetch auth token: {response.status_code}")
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Error fetching auth token: {str(e)}")

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "granite-chat",
        system_prompt: str = "You are a helpful assistant.",
        browser: str = "chrome" # Note: browser fingerprinting might be less effective with impersonate
    ):
        """Initializes the IBM Granite API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.url = "https://d1eh1ubv87xmm5.cloudfront.net/granite/playground/api/v1/acp/runs"

        # Initialize LitAgent
        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.headers = {
            "Accept": "text/event-stream",
            "Accept-Language": self.fingerprint.get("accept_language", "en-US,en;q=0.9"),
            "Authorization": "", # Will be filled by get_token
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Origin": "https://www.ibm.com",
            "Pragma": "no-cache",
            "Referer": "https://www.ibm.com/granite/playground",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": self.fingerprint.get("user_agent", ""),
            "Sec-CH-UA": self.fingerprint.get("sec_ch_ua", ""),
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self.fingerprint.get("platform", "")}"',
        }

        # Initialize curl_cffi Session
        self.session = Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = AwesomePrompts().get_act(cast(Union[str, int], act), default=self.conversation.intro, case_insensitive=True
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro

    def refresh_identity(self, browser: Optional[str] = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)

        # Update headers with new fingerprint
        self.headers.update({
            "Accept-Language": self.fingerprint.get("accept_language", "en-US,en;q=0.9"),
            "User-Agent": self.fingerprint.get("user_agent", ""),
            "Sec-CH-UA": self.fingerprint.get("sec_ch_ua", ""),
            "Sec-CH-UA-Platform": f'"{self.fingerprint.get("platform", "")}"',
        })

        # Update session headers
        self.session.headers.update(self.headers)

        return self.fingerprint

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        now = datetime.now().isoformat()
        payload = {
            "agent_name": self.model,
            "input": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "content_type": "text/plain",
                            "content": conversation_prompt,
                            "content_encoding": "plain",
                            "role": "user"
                        }
                    ],
                    "created_at": now,
                    "completed_at": now
                }
            ],
            "mode": "stream",
            "session_id": str(uuid.uuid4())
        }

        def for_stream():
            streaming_text = "" # Initialize outside try block
            try:
                # Use curl_cffi session post with impersonate
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110" # Use a common impersonation profile
                )

                if response.status_code in [401, 403]:
                    # Token expired, refresh and retry once
                    self.get_token()
                    response = self.session.post(
                        self.url,
                        data=json.dumps(payload),
                        stream=True,
                        timeout=self.timeout,
                        impersonate="chrome110"
                    )

                response.raise_for_status() # Check for HTTP errors

                # Use sanitize_stream
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None), # Pass byte iterator
                    intro_value="data:",
                    to_json=True,     # Stream sends JSON
                    skip_markers=["[DONE]"],
                    content_extractor=self._ibm_extractor, # Use the specific extractor
                    yield_raw_on_error=False # Skip non-JSON lines or lines where extractor fails
                )

                for content_chunk in processed_stream:
                    # content_chunk is the string extracted by _ibm_extractor
                    if content_chunk and isinstance(content_chunk, str):
                        streaming_text += content_chunk
                        resp = dict(text=content_chunk)
                        yield resp if not raw else content_chunk

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {str(e)}") from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed ({type(e).__name__}): {str(e)}") from e
            finally:
                # Update history after stream finishes or fails
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)


        def for_non_stream():
            try:
                # For non-stream, we collect from stream
                final_content = ""
                for chunk_data in for_stream():
                    if raw:
                        if isinstance(chunk_data, str):
                            final_content += chunk_data
                        elif isinstance(chunk_data, bytes):
                            final_content += chunk_data.decode('utf-8', errors='ignore')
                    else:
                        if isinstance(chunk_data, dict):
                            if "text" in chunk_data:
                                final_content += chunk_data["text"]
                        elif isinstance(chunk_data, str):
                            final_content += chunk_data

                if not final_content:
                    raise exceptions.FailedToGenerateResponseError("Empty response from provider")

                self.last_response = {"text": final_content}
                return self.last_response if not raw else final_content

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Failed to get non-stream response: {str(e)}") from e


        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        raw = kwargs.get("raw", False)
        def for_stream_chat():
            # ask() yields dicts or strings when streaming
            gen = self.ask(
                prompt, stream=True, raw=raw,
                optimizer=optimizer, conversationally=conversationally
            )
            for response_dict in gen:
                if raw:
                    yield cast(str, response_dict)
                else:
                    yield self.get_message(cast(Dict[str, Any], response_dict)) # get_message expects dict

        def for_non_stream_chat():
            # ask() returns dict or str when not streaming
            response_data = self.ask(
                prompt, stream=False, raw=raw,
                optimizer=optimizer, conversationally=conversationally
            )
            if raw:
                return cast(str, response_data)
            else:
                return self.get_message(cast(Dict[str, Any], response_data)) # get_message expects dict

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return response["text"]

if __name__ == "__main__":
    # Ensure curl_cffi is installed
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in IBM.AVAILABLE_MODELS:
        try:
            test_ai = IBM(model=model, timeout=60,)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
                for chunk in response:
                    response_text += chunk
            else:
                response_text = str(response)

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Clean and truncate response
                clean_text = response_text.strip().encode('utf-8', errors='ignore').decode('utf-8')
                display_text = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")
