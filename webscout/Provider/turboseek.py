import re
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


class TurboSeek(Provider):
    """
    This class provides methods for interacting with the TurboSeek API.
    """

    required_auth = False
    AVAILABLE_MODELS = ["Llama 3.1 70B"]

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
        model: str = "Llama 3.1 70B",  # Note: model parameter is not used by the API endpoint
    ):
        """Instantiates TurboSeek

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        # Initialize curl_cffi Session
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://www.turboseek.io/api/getAnswer"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://www.turboseek.io",
            "priority": "u=1, i",
            "referer": "https://www.turboseek.io/",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": LitAgent().random(),
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        # Update curl_cffi session headers and proxies
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)  # Assign proxies directly
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

    @staticmethod
    def _html_to_markdown(text: str) -> str:
        """Convert basic HTML tags to Markdown."""
        if not text:
            return ""

        # Unescape HTML entities first
        import html

        text = html.unescape(text)

        # Headers
        text = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n# \1\n", text)

        # Lists
        text = re.sub(r"<li[^>]*>(.*?)</li>", r"\n* \1", text)
        text = re.sub(r"<(ul|ol)[^>]*>", r"\n", text)
        text = re.sub(r"</(ul|ol)>", r"\n", text)

        # Paragraphs and Breaks
        text = re.sub(r"</p>", r"\n\n", text)
        text = re.sub(r"<p[^>]*>", r"\n", text)
        text = re.sub(r"<br\s*/?>", r"\n", text)

        # Bold and Italic
        text = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", text)
        text = re.sub(r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", text)

        # Remove structural tags
        text = re.sub(
            r"</?(section|div|span|article|header|footer)[^>]*>", "", text, flags=re.IGNORECASE
        )

        # Final cleanup of remaining tags
        text = re.sub(r"<[^>]*>", "", text)

        return text

    @staticmethod
    def _turboseek_extractor(chunk: Any) -> Optional[str]:
        """Extracts content from TurboSeek stream."""
        if isinstance(chunk, str):
            # The API now returns raw HTML chunks
            return chunk
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
        """Chat with AI"""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        payload = {"question": conversation_prompt, "sources": []}

        def for_stream():
            try:
                response = self.session.post(
                    self.chat_endpoint,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome120",
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )

                streaming_text = ""
                # The API returns raw HTML chunks now, no "data:" prefix
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value=None,
                    to_json=False,
                    strip_chars="",  # Disable default lstrip to preserve spacing
                    content_extractor=self._turboseek_extractor,
                    yield_raw_on_error=True,
                    raw=raw,
                )

                for content_chunk in processed_stream:
                    if content_chunk is None:
                        continue

                    if raw:
                        yield content_chunk
                    else:
                        if isinstance(content_chunk, str):
                            # In streaming mode, stripping HTML incrementally is hard.
                            # We'll just yield the chunk but clean it slightly.
                            # For full Markdown conversion, use non-streaming or aggregate it.
                            clean_chunk = re.sub(r"<[^>]*>", "", content_chunk)
                            if clean_chunk:
                                streaming_text += clean_chunk
                                self.last_response.update(dict(text=streaming_text))
                                yield dict(text=clean_chunk)

                if not raw and streaming_text:
                    self.conversation.update_chat_history(prompt, streaming_text)
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {e}")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"An unexpected error occurred ({type(e).__name__}): {e}"
                )

        def for_non_stream():
            full_html = ""
            try:
                # Iterate over the stream in raw mode to get full HTML
                # We use ask(..., raw=True) internally or just the local for_stream
                # Actually, let's just make a sub-call
                response = self.session.post(
                    self.chat_endpoint, json=payload, timeout=self.timeout, impersonate="chrome120"
                )
                full_html = response.text
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to get non-stream response: {e}"
                ) from e

            # Convert full HTML to Markdown
            final_text = self._html_to_markdown(full_html).strip()
            self.last_response = {"text": final_text}
            return self.last_response

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
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            **kwargs: Additional parameters including raw.
        Returns:
            str: Response generated
        """
        raw = kwargs.get("raw", False)

        def for_stream():
            for response in self.ask(
                prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield cast(str, response)
                else:
                    yield self.get_message(cast(Response, response))

        def for_non_stream():
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, result)
            else:
                return self.get_message(result)

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        """Retrieves message only from response

        Args:
            response (Response): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        if not isinstance(response, dict):
            return str(response)
        response_dict = cast(Dict[str, Any], response)
        return response_dict.get("text", "")


if __name__ == "__main__":
    import sys

    ai = TurboSeek(timeout=60)

    # helper for safe printing on windows
    def safe_print(text, end="\n"):
        try:
            sys.stdout.write(text + end)
        except UnicodeEncodeError:
            sys.stdout.write(text.encode("ascii", "ignore").decode("ascii") + end)
        sys.stdout.flush()

    safe_print("\n=== Testing Non-Streaming ===")
    response = ai.chat("How can I get a 6 pack in 3 months?", stream=False)
    if isinstance(response, str):
        safe_print(response)
    else:
        safe_print(str(response))

    safe_print("\n=== Testing Streaming ===")
    stream_resp = ai.chat("How can I get a 6 pack in 3 months?", stream=True)
    if hasattr(stream_resp, "__iter__") and not isinstance(stream_resp, (str, bytes)):
        for chunk in stream_resp:
            safe_print(chunk, end="")
    else:
        safe_print(str(stream_resp))
    safe_print("")
