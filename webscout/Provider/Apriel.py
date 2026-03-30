"""
A class to interact with the Apriel Gradio chat API (servicenow-ai-apriel-chat.hf.space).

This provider integrates the Apriel chat model into the Webscout framework.
"""

import time
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response, Tool
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers
from webscout.litagent import LitAgent
from webscout.sanitize import sanitize_stream


class Apriel(Provider):
    """
    A class to interact with the Apriel Gradio API.

    Supports optional tool/function calling via prompt injection.

    Attributes:
        system_prompt (str): The system prompt to define the assistant's role.

    Examples:
        >>> from webscout.Provider.apriel import Apriel
        >>> ai = Apriel()
        >>> response = ai.chat("What's the weather today?")
        >>> print(response)
        'The weather today is sunny with a high of 75F.'

        >>> # With tools
        >>> from webscout.AIbase import Tool
        >>> tool = Tool(
        ...     name="get_weather",
        ...     description="Get weather for a city",
        ...     parameters={"city": {"type": "string", "description": "City name"}},
        ...     implementation=lambda city: f"Sunny in {city}",
        ... )
        >>> ai = Apriel(tools=[tool])
        >>> result = ai.chat("What's the weather in London?", auto_execute_tools=True)
    """

    required_auth = False
    AVAILABLE_MODELS = ["UNKNOWN"]

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
        system_prompt: str = "You are a helpful assistant.",
        model: str = "UNKNOWN",
        tools: Optional[List[Tool]] = None,
    ):
        """
        Initializes the Apriel API with given parameters.

        Args:
            is_conversation: Whether the provider is in conversation mode.
            max_tokens: Maximum number of tokens to sample.
            timeout: Timeout for API requests.
            intro: Introduction message for the conversation.
            filepath: Filepath for storing conversation history.
            update_file: Whether to update the conversation history file.
            proxies: Proxies for the API requests.
            history_offset: Offset for conversation history.
            act: Act for the conversation.
            system_prompt: The system prompt to define the assistant's role.
            tools: Optional list of Tool objects for function calling.
        """
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://servicenow-ai-apriel-chat.hf.space"
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt

        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()

        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": self.agent.random(),
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

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

        # Register tools if provided
        if tools:
            self.register_tools(tools)

    def _get_session_hash(self) -> str:
        """Generate or get a session hash for the Gradio API."""
        try:
            url = f"{self.api_endpoint}/gradio_api/heartbeat"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return str(int(time.time()))
        except Exception:
            return str(int(time.time()))

    def _join_queue(
        self, session_hash: str, message: str, fn_index: int = 1, trigger_id: int = 16
    ) -> Optional[str]:
        """Send the user message to /gradio_api/queue/join and return event_id if available."""
        url = f"{self.api_endpoint}/gradio_api/queue/join"
        payload = {
            "data": [[], {"text": message, "files": []}, None],
            "event_data": None,
            "fn_index": fn_index,
            "trigger_id": trigger_id,
            "session_hash": session_hash,
        }
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        try:
            return response.json().get("event_id")
        except Exception:
            return None

    def _run_predict(self, session_hash: str, fn_index: int = 3, trigger_id: int = 16) -> None:
        """Call /gradio_api/run/predict to start processing the queued request."""
        url = f"{self.api_endpoint}/gradio_api/run/predict"
        payload = {
            "data": [],
            "event_data": None,
            "fn_index": fn_index,
            "trigger_id": trigger_id,
            "session_hash": session_hash,
        }
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()

    @staticmethod
    def _apriel_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extracts content from Apriel Gradio stream JSON objects."""
        if isinstance(chunk, dict):
            msg = chunk.get("msg")
            if msg == "process_generating":
                output = chunk.get("output", {})
                data = output.get("data")
                if data and isinstance(data, list) and len(data) > 0:
                    ops = data[0]
                    for op in ops:
                        if isinstance(op, list) and len(op) > 2 and op[0] == "append":
                            return op[2]
        return None

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        auto_execute_tools: bool = False,
        **kwargs: Any,
    ) -> Response:
        """
        Sends a prompt to the Apriel Gradio API and returns the response.

        When tools are provided, tool definitions are injected into the prompt
        so the model can respond with tool calls. If auto_execute_tools is True,
        detected tool calls are executed and results fed back automatically.

        Args:
            prompt: The prompt to send to the API.
            stream: Whether to stream the response.
            raw: Whether to return the raw response.
            optimizer: Optimizer to use for the prompt.
            conversationally: Whether to generate the prompt conversationally.
            tools: Optional list of Tool objects for this request.
            tool_choice: Optional tool choice hint (unused by this provider).
            auto_execute_tools: If True, automatically execute detected tool calls.

        Returns:
            Dict[str, Any]: The API response.
        """
        # Merge tools: instance-level + per-request
        effective_tools = list(self.available_tools.values())
        if tools:
            effective_tools.extend(tools)
            self.register_tools(tools)

        tool_defs_text = ""
        if effective_tools:
            tool_defs_text = self.format_tools_for_prompt(effective_tools)

        conversation_prompt = self.conversation.gen_complete_prompt(
            prompt, tool_definitions=tool_defs_text or None
        )
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        session_hash = self._get_session_hash()
        self._join_queue(session_hash, conversation_prompt)
        self._run_predict(session_hash)

        def for_stream():
            streaming_text = ""
            try:
                url = f"{self.api_endpoint}/gradio_api/queue/data?session_hash={session_hash}"
                response = self.session.get(
                    url, stream=True, timeout=self.timeout, impersonate="chrome110"
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )

                # Use sanitize_stream
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    content_extractor=self._apriel_extractor,
                    yield_raw_on_error=False,
                    raw=raw,
                )

                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
                        if raw:
                            yield content_chunk
                        else:
                            streaming_text += content_chunk
                            resp = dict(text=content_chunk)
                            yield resp

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {e}")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"An unexpected error occurred ({type(e).__name__}): {e}"
                )
            finally:
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

                    # Auto-execute tool calls if enabled
                    if auto_execute_tools and effective_tools:
                        tool_calls = self.extract_tool_calls(streaming_text)
                        if tool_calls:
                            results = self.process_tool_calls(tool_calls)
                            for r in results:
                                self.conversation.add_tool_call_result(
                                    r["tool_name"], r["arguments"], r["result"]
                                )

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response if not raw else self.last_response.get("text", "")

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Generates a response from the Apriel API.

        Args:
            prompt: The prompt to send to the API.
            stream: Whether to stream the response.
            optimizer: Optimizer to use for the prompt.
            conversationally: Whether to generate the prompt conversationally.
            tools: Optional list of Tool objects for this request.
            tool_choice: Optional tool choice hint.
            **kwargs: Additional parameters including raw and auto_execute_tools.

        Returns:
            str: The API response.
        """
        raw = kwargs.get("raw", False)
        auto_execute_tools = kwargs.get("auto_execute_tools", False)

        def for_stream():
            for response in self.ask(
                prompt,
                True,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
                tools=tools,
                tool_choice=tool_choice,
                auto_execute_tools=auto_execute_tools,
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
                tools=tools,
                tool_choice=tool_choice,
                auto_execute_tools=auto_execute_tools,
            )
            if raw:
                return cast(str, result)
            else:
                return self.get_message(result)

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        """
        Extracts the message from the API response.

        Args:
            response (Response): The API response.

        Returns:
            str: The message content.
        """
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    from rich import print

    ai = Apriel(timeout=60)
    response = ai.chat("write a poem about AI", stream=True, raw=False)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
