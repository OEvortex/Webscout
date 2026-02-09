import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent


class K2Think(Provider):
    """
    A class to interact with the K2 Think AI API with LitAgent user-agent.
    """

    required_auth = False
    AVAILABLE_MODELS = [
        "MBZUAI-IFM/K2-Think-v2",
    ]

    @staticmethod
    def _k2think_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from K2Think response chunks."""
        if isinstance(chunk, dict):
            # Handle OpenAI-compatible response format (non-streaming)
            if "choices" in chunk and chunk["choices"]:
                choice = chunk["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                elif "delta" in choice and "content" in choice["delta"]:
                    return choice["delta"]["content"]
            # Handle direct content (streaming)
            if "content" in chunk:
                return chunk["content"]
        return None

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
        model: str = "MBZUAI-IFM/K2-Think-v2",
        system_prompt: str = "You are a helpful assistant.",
        browser: str = "chrome",
    ):
        """Initializes the K2Think API client."""

        self.chat_endpoint = "https://www.k2think.ai/api/guest/chat/completions"

        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.headers = {
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Origin": "https://www.k2think.ai",
            "Pragma": "no-cache",
            "Referer": "https://www.k2think.ai/guest",
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
            "Forwarded": self.fingerprint.get("forwarded", ""),
            "X-Forwarded-Proto": self.fingerprint.get("x-forwarded-proto", ""),
            "X-Request-Id": self.fingerprint.get("x-request-id", ""),
        }

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

        self.__available_optimizers = [
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        ]
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

        self.headers.update(
            {
                "Accept": self.fingerprint["accept"],
                "Accept-Language": self.fingerprint["accept_language"],
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
        """Chat with K2Think AI.

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            **kwargs: Additional parameters.

        Returns:
            dict or Generator: Response from the API
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

        messages = [{"role": "user", "content": conversation_prompt}]
        if self.system_prompt:
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        self.session.headers.update(self.headers)
        payload = {
            "stream": stream,
            "model": self.model,
            "messages": messages,
            "params": {},
            "features": {"web_search": False},
        }

        def for_stream():
            """Generator function for streaming response."""
            try:
                response = self.session.post(
                    self.chat_endpoint,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                )
                if not response.status_code == 200:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}) - "
                        f"{response.text}"
                    )

                streaming_text = ""
                # Use sanitize_stream for proper SSE processing
                processed_stream = sanitize_stream(
                    data=response.iter_lines(),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=self._k2think_extractor,
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

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Error: {str(e)}")

        def for_non_stream():
            """Non-streaming response function."""
            try:
                response = self.session.post(
                    self.chat_endpoint,
                    json=payload,
                    stream=False,
                    timeout=self.timeout,
                )
                if not response.status_code == 200:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}) - "
                        f"{response.text}"
                    )

                # Use sanitize_stream to parse the non-streaming JSON response
                processed_stream = sanitize_stream(
                    data=response.text,
                    to_json=True,
                    intro_value=None,
                    content_extractor=self._k2think_extractor,
                    yield_raw_on_error=False,
                    raw=raw,
                )
                # Extract the single result
                content = next(processed_stream, None)
                if raw:
                    return content
                content = content if isinstance(content, str) else ""

                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return self.last_response

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Error: {str(e)}")

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response `str`

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            **kwargs: Additional parameters.

        Returns:
            str or Generator[str]: Response generated
        """
        raw = kwargs.get("raw", False)
        if stream:

            def for_stream():
                gen = self.ask(
                    prompt,
                    True,
                    raw=raw,
                    optimizer=optimizer,
                    conversationally=conversationally,
                    **{k: v for k, v in kwargs.items() if k != "raw"},
                )
                if hasattr(gen, "__iter__"):
                    for response in gen:
                        if raw:
                            yield cast(str, response)
                        else:
                            yield self.get_message(response)

            return for_stream()
        else:
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
                **{k: v for k, v in kwargs.items() if k != "raw"},
            )
            if raw:
                return cast(str, result)
            return self.get_message(result)

    def get_message(self, response: Response) -> str:
        """Retrieves message only from response.

        Args:
            response (Response): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        if not isinstance(response, dict):
            return str(response)

        resp_dict = cast(Dict[str, Any], response)
        return resp_dict.get("text", "")

if __name__ == "__main__":
    ai = K2Think()
    response = ai.chat("Hello", raw=False, stream=True)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="")
    else:
        print(response)
