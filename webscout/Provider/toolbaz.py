import base64
import json
import random
import re
import string
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError  # type: ignore
from curl_cffi.requests import Session  # type: ignore

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import (
    AwesomePrompts,
    Conversation,
    Optimizers,
    sanitize_stream,
)


class Toolbaz(Provider):
    """
    A class to interact with the Toolbaz API. Supports streaming responses.
    """

    required_auth = False
    AVAILABLE_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash-thinking",
        "gemini-2.0-flash",
        "claude-sonnet-4",
        "gpt-5",
        "gpt-5.2",
        "gpt-oss-120b",
        "o3-mini",
        "gpt-4o-latest",
        "grok-4-fast",
        "grok-4.1-fast",
        "toolbaz-v4.5-fast",
        "toolbaz_v4",
        "toolbaz_v3.5_pro",
        "deepseek-r1",
        "deepseek-v3.1",
        "deepseek-v3",
        "Llama-4-Maverick",
        "Llama-3.3-70B",
        "mixtral_8x22b",
        "L3-70B-Euryale-v2.1",
        "midnight-rose",
        "unfiltered_x",
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "gemini-2.0-flash",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """
        Initializes the Toolbaz API with given parameters.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.model = model
        self.proxies = proxies

        # Set up headers for the curl_cffi session
        self.session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Linux; Android 10)",
                "accept": "*/*",
                "accept-language": "en-US",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": "https://toolbaz.com",
                "pragma": "no-cache",
                "referer": "https://toolbaz.com/",
                "sec-fetch-mode": "cors",
            }
        )

        if proxies:
            self.session.proxies.update(cast(Any, proxies))

        # Initialize conversation history
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        act_prompt = (
            AwesomePrompts().get_act(
                cast(Union[str, int], act), default=None, case_insensitive=True
            )
            if act
            else intro
        )
        if act_prompt:
            self.conversation.intro = act_prompt
        self.conversation.history_offset = history_offset

    def random_string(self, length: int) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def generate_token(self) -> str:
        payload = {
            "bR6wF": {
                "nV5kP": "Mozilla/5.0 (Linux; Android 10)",
                "lQ9jX": "en-US",
                "sD2zR": "431x958",
                "tY4hL": time.tzname[0] if time.tzname else "UTC",
                "pL8mC": "Linux armv81",
                "cQ3vD": datetime.now().year,
                "hK7jN": datetime.now().hour,
            },
            "uT4bX": {"mM9wZ": [], "kP8jY": []},
            "tuTcS": int(time.time()),
            "tDfxy": None,
            "RtyJt": str(uuid.uuid4()),
        }
        return "d8TW0v" + base64.b64encode(json.dumps(payload).encode()).decode()

    def get_auth(self) -> Dict[str, str]:
        resp = None
        try:
            session_id = self.random_string(36)
            token = self.generate_token()
            data = {"session_id": session_id, "token": token}
            resp = self.session.post(
                "https://data.toolbaz.com/token.php",
                data=data,
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("success"):
                return {"token": result["token"], "session_id": session_id}

            raise exceptions.FailedToGenerateResponseError(
                f"Authentication failed: API response indicates failure. Response: {result}"
            )
        except CurlError as e:
            raise exceptions.FailedToGenerateResponseError(
                f"Authentication failed due to network error (CurlError): {e}"
            ) from e
        except json.JSONDecodeError as e:
            raise exceptions.FailedToGenerateResponseError(
                f"Authentication failed: Could not decode JSON response. Error: {e}. Response text: {getattr(resp, 'text', 'N/A')}"
            ) from e
        except Exception as e:
            err_text = ""
            if hasattr(e, "response"):
                response_obj = getattr(e, "response")
                if hasattr(response_obj, "text"):
                    err_text = getattr(response_obj, "text")
            raise exceptions.FailedToGenerateResponseError(
                f"Authentication failed due to an unexpected error ({type(e).__name__}): {e} - {err_text}"
            ) from e

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """Sends a prompt to the Toolbaz API and returns the response."""
        if optimizer and optimizer not in self.__available_optimizers:
            raise exceptions.FailedToGenerateResponseError(
                f"Optimizer is not one of {self.__available_optimizers}"
            )

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            conversation_prompt = getattr(Optimizers, optimizer)(
                conversation_prompt if conversationally else prompt
            )

        auth = self.get_auth()

        data = {
            "text": conversation_prompt,
            "capcha": auth["token"],
            "model": self.model,
            "session_id": auth["session_id"],
        }

        def for_stream():
            try:
                resp = self.session.post(
                    "https://data.toolbaz.com/writing.php",
                    data=data,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                resp.raise_for_status()

                streaming_text = ""

                processed_stream = sanitize_stream(
                    data=resp.iter_content(chunk_size=None),
                    intro_value=None,
                    to_json=False,
                    skip_regexes=[r"\[model:.*?\]"],
                    yield_raw_on_error=True,
                    raw=raw,
                )

                for content_chunk in processed_stream:
                    if isinstance(content_chunk, bytes):
                        content_chunk = content_chunk.decode("utf-8", errors="ignore")
                    if content_chunk is None:
                        continue
                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                            yield {"text": content_chunk}

                self.last_response = {"text": streaming_text}
                self.conversation.update_chat_history(prompt, streaming_text)

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Network error (CurlError): {str(e)}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Unexpected error during stream: {str(e)}"
                ) from e

        def for_non_stream():
            try:
                resp = self.session.post(
                    "https://data.toolbaz.com/writing.php",
                    data=data,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                resp.raise_for_status()

                text = resp.text
                text = re.sub(r"\[model:.*?\]", "", text)

                self.last_response = {"text": text}
                self.conversation.update_chat_history(prompt, text)

                return self.last_response

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Network error (CurlError): {str(e)}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Unexpected error: {str(e)}") from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Generates a response from the Toolbaz API."""
        raw = kwargs.get("raw", False)

        def for_stream_chat():
            for response in self.ask(
                prompt, stream=True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield cast(str, response)
                else:
                    yield self.get_message(cast(Response, response))

        def for_non_stream_chat():
            response_dict = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, response_dict)
            else:
                return self.get_message(response_dict)

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        response_dict = cast(Dict[str, Any], response)
        return response_dict.get("text", "")


if __name__ == "__main__":
    from rich import print

    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in Toolbaz.AVAILABLE_MODELS:
        try:
            test_ai = Toolbaz(model=model, timeout=60)
            response_stream = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""

            if hasattr(response_stream, "__iter__") and not isinstance(
                response_stream, (str, bytes)
            ):
                for chunk in response_stream:
                    response_text += chunk
            else:
                response_text = str(response_stream)

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                clean_text = response_text.strip()
                display_text = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
            else:
                status = "✗ (Stream)"
                display_text = "Empty or invalid stream response"

            print(f"\r{model:<50} {status:<10} {display_text}")

        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} Error: {str(e)}")
