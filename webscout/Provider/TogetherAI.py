import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent


class TogetherAI(Provider):
    """
    A class to interact with the Together AI Chat API (https://chat.together.ai/).
    Uses the chat interface API endpoint with model UUIDs.
    """

    required_auth = True
    AVAILABLE_MODELS = []

    @classmethod
    def get_models(cls, api_key: Optional[str] = None):
        """Fetch available models from Together API."""
        if not api_key:
            return cls.AVAILABLE_MODELS

        try:
            # Use a temporary session for fetching models
            session = Session()
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

            response = session.get(
                "https://api.together.xyz/v1/models", headers=headers, impersonate="chrome110"
            )

            if response.status_code != 200:
                return cls.AVAILABLE_MODELS

            data = response.json()
            # Together API returns a list of model objects
            if isinstance(data, list):
                # Filter for chat/language models if possible, or just return all IDs
                # The API returns objects with 'id', 'type', etc.
                return [model["id"] for model in data if isinstance(model, dict) and "id" in model]

            return cls.AVAILABLE_MODELS

        except Exception:
            return cls.AVAILABLE_MODELS

    @classmethod
    def update_available_models(cls, api_key=None):
        """Update the available models list from Together API"""
        try:
            models = cls.get_models(api_key)
            if models:
                cls.AVAILABLE_MODELS = models
        except Exception:
            pass

    @staticmethod
    def _together_ai_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from Together AI stream JSON objects."""
        if isinstance(chunk, dict):
            # Extract from streaming response format
            choices = chunk.get("choices", [])
            if choices and len(choices) > 0:
                delta = choices[0].get("delta", {})
                if isinstance(delta, dict):
                    return delta.get("content")
        return None

    def __init__(
        self,
        api_key: str,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "DeepSeek R1 (0528)",
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.6,
        top_p: float = 0.95,
        browser: str = "chrome",
    ):
        """Initializes the Together AI chat client."""
        self.update_available_models(api_key)

        if model not in self.AVAILABLE_MODELS:
            if self.AVAILABLE_MODELS:
                raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.url = "https://api.together.xyz/v1/chat/completions"
        self.model_name = model
        self.model_id = model
        self.temperature = temperature
        self.top_p = top_p

        # Initialize LitAgent and generate consistent fingerprint
        self.agent = LitAgent()
        self.fingerprint = self._generate_consistent_fingerprint(browser)
        self.api = api_key

        # Setup headers
        self.headers = {
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Origin": "https://chat.together.ai",
            "Pragma": "no-cache",
            "Referer": "https://chat.together.ai/",
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
        }

        if self.api is not None:
            self.headers["Authorization"] = f"Bearer {self.api}"

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

    def _generate_consistent_fingerprint(self, browser: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a consistent browser fingerprint using the instance's LitAgent.

        This method uses the same LitAgent instance to ensure consistent IP addresses
        and user agent across multiple requests in a conversation, preventing 404 errors
        caused by rapidly changing fingerprints.

        Args:
            browser (Optional[str]): The browser name to generate the fingerprint for.
                If not specified, a random browser is used.

        Returns:
            Dict[str, str]: A dictionary containing fingerprinting headers and values.
        """
        import random

        from webscout.litagent.constants import BROWSERS, FINGERPRINTS

        # Get a user agent from the instance's agent
        if browser:
            browser = browser.lower()
            if browser in BROWSERS:
                user_agent = self.agent.browser(browser)
            else:
                user_agent = self.agent.random()
        else:
            user_agent = self.agent.random()

        accept_language = random.choice(FINGERPRINTS["accept_language"])
        accept = random.choice(FINGERPRINTS["accept"])
        platform = random.choice(FINGERPRINTS["platforms"])

        # Generate sec-ch-ua based on the user agent
        sec_ch_ua = ""
        sec_ch_ua_dict = cast(Dict[str, str], FINGERPRINTS["sec_ch_ua"])
        for browser_name in sec_ch_ua_dict:
            if browser_name in user_agent.lower():
                version = random.randint(*BROWSERS[browser_name])
                sec_ch_ua = sec_ch_ua_dict[browser_name].format(version, version)
                break

        # Use the instance's agent for consistent IP rotation
        ip = self.agent.rotate_ip()
        fingerprint = {
            "user_agent": user_agent,
            "accept_language": accept_language,
            "accept": accept,
            "sec_ch_ua": sec_ch_ua,
            "platform": platform,
            "x-forwarded-for": ip,
            "x-real-ip": ip,
            "x-client-ip": ip,
            "forwarded": f"for={ip};proto=https",
            "x-forwarded-proto": "https",
            "x-request-id": self.agent.random_id(8)
            if hasattr(self.agent, "random_id")
            else "".join(random.choices("0123456789abcdef", k=8)),
        }

        return fingerprint

    def refresh_identity(self, browser: Optional[str] = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self._generate_consistent_fingerprint(browser)

        # Update headers with new fingerprint
        self.headers.update(
            {
                "Accept": self.fingerprint["accept"],
                "Accept-Language": self.fingerprint["accept_language"],
                "User-Agent": self.fingerprint.get("user_agent", ""),
                "Sec-CH-UA": self.fingerprint.get("sec_ch_ua", ""),
                "X-Forwarded-For": self.fingerprint.get("x-forwarded-for", ""),
                "X-Real-IP": self.fingerprint.get("x-real-ip", ""),
                "X-Client-IP": self.fingerprint.get("x-client-ip", ""),
            }
        )

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

        # Payload construction
        payload = {
            "model": self.model_id,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream,
            "max_tokens": self.max_tokens_to_sample,
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                response.raise_for_status()

                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=self._together_ai_extractor,
                    yield_raw_on_error=False,
                    raw=raw,
                )

                for content_chunk in processed_stream:
                    if isinstance(content_chunk, bytes):
                        content_chunk = content_chunk.decode("utf-8", errors="ignore")

                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                            yield dict(text=content_chunk)

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {str(e)}"
                ) from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed ({type(e).__name__}): {str(e)}"
                ) from e
            finally:
                if not raw and streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            try:
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                    impersonate="chrome110",
                )
                response.raise_for_status()

                response_text = response.text

                processed_stream = sanitize_stream(
                    data=response_text,
                    to_json=True,
                    intro_value=None,
                    content_extractor=lambda chunk: chunk.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content")
                    if isinstance(chunk, dict)
                    else None,
                    yield_raw_on_error=False,
                )
                content = next(processed_stream, None)
                content = content if isinstance(content, str) else ""

                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return self.last_response if not raw else content

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed (CurlError): {e}"
                ) from e
            except Exception as e:
                err_text = ""
                if hasattr(e, "response"):
                    response_obj = getattr(e, "response")
                    if hasattr(response_obj, "text"):
                        err_text = getattr(response_obj, "text")
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed ({type(e).__name__}): {e} - {err_text}"
                ) from e

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
        if stream:

            def for_stream_chat():
                gen = self.ask(
                    prompt,
                    stream=True,
                    raw=raw,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
                if hasattr(gen, "__iter__"):
                    for response in gen:
                        if raw:
                            yield cast(str, response)
                        else:
                            yield self.get_message(response)

            return for_stream_chat()
        else:
            result = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, result)
            else:
                return self.get_message(result)

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        response_dict = cast(Dict[str, Any], response)
        return response_dict.get("text", "")


if __name__ == "__main__":
    print("-" * 100)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 100)

    import os

    api_key = os.environ.get("TOGETHER_API_KEY", "")
    if not api_key:
        print("Please set TOGETHER_API_KEY environment variable")
        exit(1)
    for model_name in TogetherAI.AVAILABLE_MODELS:
        try:
            test_ai = TogetherAI(api_key=api_key, model=model_name, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            for chunk in response:
                response_text += chunk

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                clean_text = response_text.strip().encode("utf-8", errors="ignore").decode("utf-8")
                display_text = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model_name:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model_name:<50} {'✗':<10} {str(e)[:50]}")
