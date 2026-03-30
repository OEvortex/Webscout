import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Union

from litprinter import ic
from typing_extensions import TypeAlias

# from webscout.Extra.proxy_manager import ProxyManager

# # Type aliases for better readability
Response: TypeAlias = Union[Dict[str, Any], Generator[Any, None, None], str]


# class ProviderMeta(ABC.__class__):
#     """Metaclass for Provider that automatically applies proxy patching."""

#     def __new__(mcs, name: str, bases: tuple, namespace: dict):
#         cls = super().__new__(mcs, name, bases, namespace)

#         # Apply proxy patch to the class if it's a concrete Provider
#         if name != 'Provider' and hasattr(cls, '__init__'):
#             try:
#                 pm = ProxyManager(auto_fetch=True, debug=True)
#                 pm.patch()
#             except Exception:
#                 pass  # Silently fail if proxy manager fails

#         return cls


class SearchResponse:
    """A wrapper class for search API responses.

    This class automatically converts response objects to their text representation
    when printed or converted to string.

    Attributes:
        text (str): The text content of the response

    Example:
        >>> response = SearchResponse("Hello, world!")
        >>> print(response)
        Hello, world!
        >>> str(response)
        'Hello, world!'
    """

    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text


class AIProviderError(Exception):
    pass


class ModelList(ABC):
    @abstractmethod
    def list(self) -> List[str]:
        """Return a list of available models"""
        raise NotImplementedError


class SimpleModelList(ModelList):
    def __init__(self, models: List[str]):
        self._models = models

    def list(self) -> List[str]:
        return self._models


@dataclass
class Tool:
    """Tool definition for function calling support in providers.

    Attributes:
        name: The tool/function name.
        description: What the tool does.
        parameters: Parameter definitions as {name: {type, description, ...}}.
        required_params: List of required parameter names. Defaults to all parameters.
        implementation: Optional callable that executes the tool.

    Example:
        >>> def get_weather(city: str) -> str:
        ...     return f"Weather in {city}: Sunny, 75F"
        >>> tool = Tool(
        ...     name="get_weather",
        ...     description="Get current weather for a city",
        ...     parameters={"city": {"type": "string", "description": "City name"}},
        ...     implementation=get_weather,
        ... )
        >>> tool.execute({"city": "London"})
        'Weather in London: Sunny, 75F'
    """

    name: str
    description: str
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required_params: Optional[List[str]] = None
    implementation: Optional[Callable[..., Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAI-compatible tool definition format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required_params or list(self.parameters.keys()),
                },
            },
        }

    def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool with the given arguments."""
        if not self.implementation:
            return f"Tool '{self.name}' does not have an implementation."
        try:
            return self.implementation(**arguments)
        except Exception as e:
            return f"Error executing tool '{self.name}': {e}"


class Provider(ABC):
    required_auth: bool = False
    conversation: Any

    def __init__(self, *args, **kwargs):
        self._last_response: Dict[str, Any] = {}
        self.conversation = None
        self.available_tools: Dict[str, Tool] = {}
        self.supports_tools: bool = False

    @property
    def last_response(self) -> Dict[str, Any]:
        return self._last_response

    @last_response.setter
    def last_response(self, value: Dict[str, Any]):
        self._last_response = value

    # --- Tool support methods ---

    def register_tools(self, tools: List[Tool]) -> None:
        """Register tools available for function calling.

        Args:
            tools: List of Tool objects to make available.
        """
        for tool in tools:
            self.available_tools[tool.name] = tool

    def format_tools_for_prompt(self, tools: Optional[List[Tool]] = None) -> str:
        """Format tool definitions as text for injection into prompts.

        This converts tool schemas into a text representation that can be
        prepended to prompts for providers that don't support native
        structured tool calling.

        Args:
            tools: Tools to format. Uses registered tools if not provided.

        Returns:
            Formatted tool descriptions string, or empty string if no tools.
        """
        tool_list = tools or list(self.available_tools.values())
        if not tool_list:
            return ""

        lines = [
            "You have access to the following tools. To use a tool, respond with"
            " EXACTLY this format and nothing else:",
            "",
            "```json",
            '{"tool_call": {"name": "<tool_name>", "arguments": {<args>}}}',
            "```",
            "",
            "Available tools:",
        ]
        for tool in tool_list:
            lines.append(f"\n## {tool.name}")
            lines.append(f"Description: {tool.description}")
            lines.append("Parameters:")
            if tool.parameters:
                for param_name, param_info in tool.parameters.items():
                    param_type = param_info.get("type", "any")
                    param_desc = param_info.get("description", "")
                    required = tool.required_params is None or param_name in (
                        tool.required_params or []
                    )
                    req_tag = " (required)" if required else " (optional)"
                    lines.append(f"  - {param_name} ({param_type}){req_tag}: {param_desc}")
            else:
                lines.append("  (none)")

        lines.append("")
        lines.append("If no tool is needed, respond normally without using the tool format.")
        return "\n".join(lines)

    def process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results.

        Args:
            tool_calls: List of dicts with 'name' and 'arguments' keys.

        Returns:
            List of result dicts with 'tool_name', 'arguments', and 'result' keys.
        """
        results = []
        for call in tool_calls:
            tool_name = call.get("name")
            arguments = call.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    results.append(
                        {
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "result": f"Error: Could not parse arguments: {arguments}",
                        }
                    )
                    continue
            if tool_name in self.available_tools:
                result = self.available_tools[tool_name].execute(arguments)
                results.append(
                    {
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": str(result),
                    }
                )
            else:
                results.append(
                    {
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": f"Error: Tool '{tool_name}' not found.",
                    }
                )
        return results

    def format_tool_response(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool execution results as text for inclusion in conversation.

        Args:
            tool_results: Results from process_tool_calls().

        Returns:
            Formatted string of tool results.
        """
        if not tool_results:
            return ""
        lines = []
        for result in tool_results:
            lines.append(f"[Tool: {result['tool_name']}] {result['result']}")
        return "\n".join(lines)

    def extract_tool_calls(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """Parse tool calls from LLM response text.

        Looks for JSON blocks matching the format produced by
        format_tools_for_prompt().

        Args:
            response_text: Raw text response from the LLM.

        Returns:
            List of tool call dicts, or None if no tool calls found.
        """
        import re

        json_pattern = r"```json\s*(.*?)\s*```"
        matches = re.findall(json_pattern, response_text, re.DOTALL)

        tool_calls = []
        for match in matches:
            try:
                parsed = json.loads(match)
                if "tool_call" in parsed:
                    tc = parsed["tool_call"]
                    tool_calls.append(
                        {
                            "name": tc.get("name"),
                            "arguments": tc.get("arguments", {}),
                        }
                    )
            except json.JSONDecodeError:
                continue

        return tool_calls if tool_calls else None

    # --- Abstract methods ---

    @abstractmethod
    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Response:
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
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
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def get_message(self, response: Response) -> str:
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def get_message(self, response: Response) -> str:
        raise NotImplementedError("Method needs to be implemented in subclass")


class TTSProvider(ABC):
    @abstractmethod
    def tts(self, text: str, voice: Optional[str] = None, verbose: bool = False, **kwargs) -> str:
        """Convert text to speech and save to a temporary file.

        Args:
            text (str): The text to convert to speech
            voice (str, optional): The voice to use. Defaults to provider's default voice.
            verbose (bool, optional): Whether to print debug information. Defaults to False.

        Returns:
            str: Path to the generated audio file
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

    def save_audio(
        self, audio_file: str, destination: Optional[str] = None, verbose: bool = False
    ) -> str:
        """Save audio to a specific destination.

        Args:
            audio_file (str): Path to the source audio file
            destination (str, optional): Destination path. Defaults to current directory with timestamp.
            verbose (bool, optional): Whether to print debug information. Defaults to False.

        Returns:
            str: Path to the saved audio file
        """
        import os
        import shutil
        import time
        from pathlib import Path

        source_path = Path(audio_file)

        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        if destination is None:
            # Create a default destination with timestamp in current directory
            timestamp = int(time.time())
            destination = os.path.join(os.getcwd(), f"tts_audio_{timestamp}{source_path.suffix}")

        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)

        # Copy the file
        shutil.copy2(source_path, destination)

        if verbose:
            print(f"[debug] Audio saved to {destination}")

        return destination

    def stream_audio(
        self,
        text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: Optional[str] = None,
        instructions: Optional[str] = None,
        chunk_size: int = 1024,
        verbose: bool = False,
    ) -> Generator[bytes, None, None]:
        """Stream audio in chunks.

        Args:
            text (str): The text to convert to speech
            model (str, optional): The model to use.
            voice (str, optional): The voice to use. Defaults to provider's default voice.
            response_format (str, optional): The audio format.
            instructions (str, optional): Voice instructions.
            chunk_size (int, optional): Size of audio chunks to yield. Defaults to 1024.
            verbose (bool, optional): Whether to print debug information. Defaults to False.

        Yields:
            Generator[bytes, None, None]: Audio data chunks
        """
        # Generate the audio file
        audio_file = self.tts(text, voice=voice, verbose=verbose)

        # Stream the file in chunks
        with open(audio_file, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk


class STTProvider(ABC):
    """Abstract base class for Speech-to-Text providers."""

    @abstractmethod
    def transcribe(self, audio_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
        """Transcribe audio file to text.

        Args:
            audio_path (Union[str, Path]): Path to the audio file
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict[str, Any]: Transcription result in OpenAI Whisper format
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def transcribe_from_url(self, audio_url: str, **kwargs) -> Dict[str, Any]:
        """Transcribe audio from URL to text.

        Args:
            audio_url (str): URL of the audio file
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict[str, Any]: Transcription result in OpenAI Whisper format
        """
        raise NotImplementedError("Method needs to be implemented in subclass")


class AISearch(ABC):
    """Abstract base class for AI-powered search providers.

    This class defines the interface for AI search providers that can perform
    web searches and return AI-generated responses based on search results.

    All search providers should inherit from this class and implement the
    required methods.
    """

    @abstractmethod
    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[
        SearchResponse,
        Generator[Union[Dict[str, str], SearchResponse], None, None],
        List[Any],
        Dict[str, Any],
        str,
    ]:
        """Search using the provider's API and get AI-generated responses.

        This method sends a search query to the provider and returns the AI-generated response.
        It supports both streaming and non-streaming modes, as well as raw response format.

        Args:
            prompt (str): The search query or prompt to send to the API.
            stream (bool, optional): If True, yields response chunks as they arrive.
                                   If False, returns complete response. Defaults to False.
            raw (bool, optional): If True, returns raw response dictionaries.
                                If False, returns SearchResponse objects that convert to text automatically.
                                Defaults to False.

        Returns:
            Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None]]:
                - If stream=False: Returns complete response as SearchResponse object
                - If stream=True: Yields response chunks as either Dict or SearchResponse objects

        Raises:
            APIConnectionError: If the API request fails
        """
        raise NotImplementedError("Method needs to be implemented in subclass")
