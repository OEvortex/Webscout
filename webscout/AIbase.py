from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

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

class Provider(ABC):
    required_auth: bool = False
    conversation: Any

    def __init__(self, *args, **kwargs):
        self._last_response: Dict[str, Any] = {}
        self.conversation = None

    @property
    def last_response(self) -> Dict[str, Any]:
        return self._last_response

    @last_response.setter
    def last_response(self, value: Dict[str, Any]):
        self._last_response = value

    @abstractmethod
    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
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

    def save_audio(self, audio_file: str, destination: Optional[str] = None, verbose: bool = False) -> str:
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
        verbose: bool = False
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
        with open(audio_file, 'rb') as f:
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
    ) -> Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None], List[Any], Dict[str, Any], str]:
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
