import json
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import requests
from curl_cffi.curl import CurlMime

from webscout import exceptions
from webscout.AIbase import Provider, Response, Tool
from webscout.AIutel import (
    AwesomePrompts,
    Conversation,
    Optimizers,
    sanitize_stream,
)


class CohereCommand(Provider):
    """Provider for Cohere Command models via HuggingChat UI.

    Accesses the Cohere Command family through the public Hugging Face Space at
    https://coherelabs-c4ai-command.hf.space.

    No API key is required — the service uses an ``hf-chat`` session cookie
    that is automatically obtained on the first request.
    """

    required_auth = False
    BASE_URL = "https://coherelabs-c4ai-command.hf.space"

    AVAILABLE_MODELS = [
        "command-a-03-2025",
        "command-r7b-03-2025",
        "command-r-plus-03-2025",
        "command-a-plus-03-2025",
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 4096,
        timeout: int = 60,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: Optional[dict] = None,
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "command-a-03-2025",
        system_prompt: str = "You are a helpful AI assistant.",
        tools: Optional[list[Tool]] = None,
    ) -> None:
        """Initialises the CohereCommand API client."""
        self.session = requests.Session(impersonate="chrome110")
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = f"{self.BASE_URL}/conversation"
        self.timeout = timeout
        self.last_response: Dict[str, Any] = {}
        self.model = model
        self.system_prompt = system_prompt
        self.proxies = proxies or {}
        self.conversation_id: Optional[str] = None

        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        self.session.headers.update(self.headers)
        if self.proxies:
            self.session.proxies.update(self.proxies)

        # Obtain hf-chat session cookie
        self._obtain_session_cookie()

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

        if tools:
            self.register_tools(tools)

    def _obtain_session_cookie(self) -> None:
        """Obtain the ``hf-chat`` session cookie from the server."""
        try:
            self.session.get(self.BASE_URL, timeout=self.timeout)
        except Exception:
            pass

    def _create_conversation(self) -> str:
        """Create a new conversation and return the conversation ID."""
        payload = {"model": self.model, "preprompt": ""}
        response = self.session.post(
            self.api_endpoint,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        conv_id = data.get("conversationId")
        if not conv_id:
            raise exceptions.FailedToGenerateResponseError(
                "Failed to create conversation: no conversationId in response"
            )
        self.conversation_id = conv_id
        return conv_id

    @staticmethod
    def _sse_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extract token text from SSE lines."""
        if isinstance(chunk, dict):
            if chunk.get("type") == "stream":
                return chunk.get("token")
            if chunk.get("type") == "finalAnswer":
                return chunk.get("text")
        elif isinstance(chunk, str):
            try:
                data = json.loads(chunk)
                if data.get("type") == "stream":
                    return data.get("token")
                if data.get("type") == "finalAnswer":
                    return data.get("text")
            except (json.JSONDecodeError, AttributeError):
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
        """Chat with the Cohere Command model."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        if not self.conversation_id:
            self._create_conversation()

        message_endpoint = f"{self.BASE_URL}/conversation/{self.conversation_id}"

        message_data = {
            "inputs": prompt,
            "id": str(uuid.uuid4()),
            "is_retry": False,
            "is_continue": False,
            "web_search": False,
            "tools": [],
        }

        # Build multipart form data using CurlMime
        mime = CurlMime()
        mime.addpart(
            name="data",
            content_type="application/json",
            data=json.dumps(message_data).encode(),
        )

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    message_endpoint,
                    multipart=mime,
                    stream=True,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=[],
                    content_extractor=self._sse_extractor,
                    yield_raw_on_error=False,
                    raw=raw,
                )

                for token in processed_stream:
                    if token is not None:
                        if raw:
                            yield token
                        else:
                            streaming_text += token
                            yield dict(text=token)

                self.last_response = {"text": streaming_text}
                if streaming_text:
                    self.conversation.update_chat_history(prompt, streaming_text)

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Stream request failed: {e}"
                ) from e

        def for_non_stream():
            full_text = ""
            try:
                response = self.session.post(
                    message_endpoint,
                    multipart=mime,
                    stream=True,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue
                    decoded = line.decode("utf-8", errors="replace")
                    if decoded.startswith("data:"):
                        decoded = decoded[5:].strip()
                    if not decoded:
                        continue
                    try:
                        data = json.loads(decoded)
                        if data.get("type") == "stream":
                            full_text += data.get("token", "")
                        elif data.get("type") == "finalAnswer":
                            full_text = data.get("text", full_text)
                            break
                    except json.JSONDecodeError:
                        continue

                self.last_response = {"text": full_text}
                if full_text:
                    self.conversation.update_chat_history(prompt, full_text)
                return full_text

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Non-stream request failed: {e}"
                ) from e

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        """Extract the text message from a response."""
        if not isinstance(response, dict):
            return str(response)
        resp_dict = cast(Dict[str, Any], response)
        if "text" in resp_dict:
            return cast(str, resp_dict["text"])
        return ""


if __name__ == "__main__":
    print("Testing CohereCommand provider...")
    print("-" * 60)

    ai = CohereCommand(model="command-a-03-2025", timeout=60)

    print("\n[Non-streaming]")
    resp = ai.ask("What is 2+2?", stream=False)
    print(f"Response: {resp}")

    print("\n[Streaming]")
    for chunk in ai.ask("Say hello in three words.", stream=True):
        if isinstance(chunk, dict):
            print(chunk.get("text", ""), end="", flush=True)
    print()

    print("-" * 60)
    print("Done.")
