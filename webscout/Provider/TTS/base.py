"""
Base class for TTS providers with OpenAI-compatible functionality.
"""

import asyncio
import functools
import os
import tempfile
from pathlib import Path
from typing import Any, Generator, List, Optional, Union, cast

from litprinter import ic

from webscout.AIbase import TTSProvider


class BaseTTSProvider(TTSProvider):
    """
    Base class for TTS providers with OpenAI-compatible functionality.

    This class implements common methods and follows OpenAI TTS API patterns
    for speech generation, streaming, and audio handling.
    """

    required_auth = False

    # Supported models (can be overridden by subclasses)
    SUPPORTED_MODELS = [
        "gpt-4o-mini-tts",  # Latest intelligent realtime model
        "tts-1",  # Lower latency model
        "tts-1-hd",  # Higher quality model
    ]

    # Supported voices (can be overridden by subclasses)
    SUPPORTED_VOICES = [
        "alloy",
        "ash",
        "ballad",
        "coral",
        "echo",
        "fable",
        "nova",
        "onyx",
        "sage",
        "shimmer",
    ]

    # Supported output formats
    SUPPORTED_FORMATS = [
        "mp3",  # Default format
        "opus",  # Internet streaming, low latency
        "aac",  # Digital audio compression
        "flac",  # Lossless compression
        "wav",  # Uncompressed, low latency
        "pcm",  # Raw samples, 24kHz 16-bit
    ]

    def __init__(self):
        """Initialize the base TTS provider."""
        self.temp_dir = tempfile.mkdtemp(prefix="webscout_tts_")
        self.default_model = "gpt-4o-mini-tts"
        self.default_voice = "coral"
        self.default_format = "mp3"

    def validate_model(self, model: str) -> str:
        """
        Validate and return the model name.

        Args:
            model (str): Model name to validate

        Returns:
            str: Validated model name

        Raises:
            ValueError: If model is not supported
        """
        # If provider doesn't support models, return the model as-is
        if self.SUPPORTED_MODELS is None:
            return model

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Model '{model}' not supported. Available models: {', '.join(self.SUPPORTED_MODELS)}"
            )
        return model

    def validate_voice(self, voice: str) -> str:
        """
        Validate and return the voice name.

        Args:
            voice (str): Voice name to validate

        Returns:
            str: Validated voice name

        Raises:
            ValueError: If voice is not supported
        """
        if voice not in self.SUPPORTED_VOICES:
            raise ValueError(
                f"Voice '{voice}' not supported. Available voices: {', '.join(self.SUPPORTED_VOICES)}"
            )
        return voice

    def validate_format(self, response_format: str) -> str:
        """
        Validate and return the response format.

        Args:
            response_format (str): Response format to validate

        Returns:
            str: Validated response format

        Raises:
            ValueError: If format is not supported
        """
        if response_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Format '{response_format}' not supported. Available formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        return response_format

    def save_audio(
        self, audio_file: str, destination: Optional[str] = None, verbose: bool = False
    ) -> str:
        """
        Save audio to a specific destination.

        Args:
            audio_file (str): Path to the source audio file
            destination (str, optional): Destination path. Defaults to current directory with timestamp.
            verbose (bool, optional): Whether to print debug information. Defaults to False.

        Returns:
            str: Path to the saved audio file

        Raises:
            FileNotFoundError: If the audio file doesn't exist
        """
        import shutil
        import time

        source_path = Path(audio_file)

        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        if destination is None:
            # Create a default destination with timestamp in current directory
            timestamp = int(time.time())
            destination = os.path.join(os.getcwd(), f"speech_{timestamp}{source_path.suffix}")

        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)

        # Copy the file
        shutil.copy2(source_path, destination)

        if verbose:
            ic.configureOutput(prefix="DEBUG| ")
            ic(f"Audio saved to {destination}")

        return destination

    def create_speech(
        self,
        input_text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: Optional[str] = None,
        instructions: Optional[str] = None,
        verbose: bool = False,
    ) -> str:
        """
        Create speech from input text (OpenAI-compatible interface).

        Args:
            input_text (str): The text to convert to speech
            model (str, optional): The TTS model to use
            voice (str, optional): The voice to use
            response_format (str, optional): Audio format (mp3, opus, aac, flac, wav, pcm)
            instructions (str, optional): Voice instructions for controlling speech aspects
            verbose (bool, optional): Whether to print debug information

        Returns:
            str: Path to the generated audio file
        """
        # Use defaults if not provided
        model = model or self.default_model
        voice = voice or self.default_voice
        response_format = response_format or self.default_format

        # Validate parameters
        self.validate_model(model)
        self.validate_voice(voice)
        self.validate_format(response_format)

        # Call the provider-specific TTS implementation
        return self.tts(
            text=input_text,
            model=model,
            voice=voice,
            response_format=response_format,
            instructions=instructions,
            verbose=verbose,
        )

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
        """
        Stream audio in chunks with OpenAI-compatible parameters.

        Args:
            text (str): The text to convert to speech
            model (str, optional): The TTS model to use
            voice (str, optional): The voice to use
            response_format (str, optional): Audio format
            instructions (str, optional): Voice instructions
            chunk_size (int, optional): Size of audio chunks to yield. Defaults to 1024.
            verbose (bool, optional): Whether to print debug information. Defaults to False.

        Yields:
            Generator[bytes, None, None]: Audio data chunks
        """
        # Generate the audio file using create_speech
        audio_file = self.create_speech(
            input_text=text,
            model=model,
            voice=voice,
            response_format=response_format,
            instructions=instructions,
            verbose=verbose,
        )

        # Stream the file in chunks
        with open(audio_file, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    def tts(self, text: str, voice: Optional[str] = None, verbose: bool = False, **kwargs) -> str:
        """
        Abstract method for text-to-speech conversion.
        Must be implemented by subclasses.

        Args:
            text (str): The text to convert to speech
            **kwargs: Additional provider-specific parameters

        Returns:
            str: Path to the generated audio file

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement the tts method")


class AsyncBaseTTSProvider:
    """
    Base class for async TTS providers with OpenAI-compatible functionality.

    This class implements common async methods following OpenAI TTS API patterns
    for speech generation, streaming, and audio handling.
    """

    required_auth = False

    # Supported models (can be overridden by subclasses)
    SUPPORTED_MODELS = [
        "gpt-4o-mini-tts",  # Latest intelligent realtime model
        "tts-1",  # Lower latency model
        "tts-1-hd",  # Higher quality model
    ]

    # Supported voices (can be overridden by subclasses)
    SUPPORTED_VOICES = [
        "alloy",
        "ash",
        "ballad",
        "coral",
        "echo",
        "fable",
        "nova",
        "onyx",
        "sage",
        "shimmer",
    ]

    # Supported output formats
    SUPPORTED_FORMATS = [
        "mp3",  # Default format
        "opus",  # Internet streaming, low latency
        "aac",  # Digital audio compression
        "flac",  # Lossless compression
        "wav",  # Uncompressed, low latency
        "pcm",  # Raw samples, 24kHz 16-bit
    ]

    def __init__(self):
        """Initialize the async base TTS provider."""
        self.temp_dir = tempfile.mkdtemp(prefix="webscout_tts_")
        self.default_model = "gpt-4o-mini-tts"
        self.default_voice = "coral"
        self.default_format = "mp3"

    async def validate_model(self, model: str) -> str:
        """
        Validate and return the model name.

        Args:
            model (str): Model name to validate

        Returns:
            str: Validated model name

        Raises:
            ValueError: If model is not supported
        """
        # If provider doesn't support models, return the model as-is
        if self.SUPPORTED_MODELS is None:
            return model

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Model '{model}' not supported. Available models: {', '.join(self.SUPPORTED_MODELS)}"
            )
        return model

    async def validate_voice(self, voice: str) -> str:
        """
        Validate and return the voice name.

        Args:
            voice (str): Voice name to validate

        Returns:
            str: Validated voice name

        Raises:
            ValueError: If voice is not supported
        """
        if voice not in self.SUPPORTED_VOICES:
            raise ValueError(
                f"Voice '{voice}' not supported. Available voices: {', '.join(self.SUPPORTED_VOICES)}"
            )
        return voice

    async def validate_format(self, response_format: str) -> str:
        """
        Validate and return the response format.

        Args:
            response_format (str): Response format to validate

        Returns:
            str: Validated response format

        Raises:
            ValueError: If format is not supported
        """
        if response_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Format '{response_format}' not supported. Available formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        return response_format

    async def save_audio(
        self, audio_file: str, destination: Optional[str] = None, verbose: bool = False
    ) -> str:
        """
        Save audio to a specific destination asynchronously.

        Args:
            audio_file (str): Path to the source audio file
            destination (str, optional): Destination path. Defaults to current directory with timestamp.
            verbose (bool, optional): Whether to print debug information. Defaults to False.

        Returns:
            str: Path to the saved audio file

        Raises:
            FileNotFoundError: If the audio file doesn't exist
        """
        import asyncio
        import shutil
        import time

        source_path = Path(audio_file)

        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        if destination is None:
            # Create a default destination with timestamp in current directory
            timestamp = int(time.time())
            destination = os.path.join(os.getcwd(), f"speech_{timestamp}{source_path.suffix}")

        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)

        # Copy the file using asyncio to avoid blocking
        await asyncio.to_thread(functools.partial(shutil.copy2, str(source_path), destination))

        if verbose:
            ic.configureOutput(prefix="DEBUG| ")
            ic(f"Audio saved to {destination}")

        return destination

    async def create_speech(
        self,
        input_text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: Optional[str] = None,
        instructions: Optional[str] = None,
        verbose: bool = False,
    ) -> str:
        """
        Create speech from input text asynchronously (OpenAI-compatible interface).

        Args:
            input_text (str): The text to convert to speech
            model (str, optional): The TTS model to use
            voice (str, optional): The voice to use
            response_format (str, optional): Audio format (mp3, opus, aac, flac, wav, pcm)
            instructions (str, optional): Voice instructions for controlling speech aspects
            verbose (bool, optional): Whether to print debug information

        Returns:
            str: Path to the generated audio file
        """
        # Use defaults if not provided
        model = model or self.default_model
        voice = voice or self.default_voice
        response_format = response_format or self.default_format

        # Validate parameters
        await self.validate_model(model)
        await self.validate_voice(voice)
        await self.validate_format(response_format)

        # Call the provider-specific TTS implementation
        return await self.tts(
            text=input_text,
            model=model,
            voice=voice,
            response_format=response_format,
            instructions=instructions,
            verbose=verbose,
        )

    async def stream_audio(
        self,
        input_text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: Optional[str] = None,
        instructions: Optional[str] = None,
        chunk_size: int = 1024,
        verbose: bool = False,
    ):
        """
        Stream audio in chunks asynchronously with OpenAI-compatible parameters.

        Args:
            input_text (str): The text to convert to speech
            model (str, optional): The TTS model to use
            voice (str, optional): The voice to use
            response_format (str, optional): Audio format
            instructions (str, optional): Voice instructions
            chunk_size (int, optional): Size of audio chunks to yield. Defaults to 1024.
            verbose (bool, optional): Whether to print debug information. Defaults to False.

        Yields:
            AsyncGenerator[bytes, None]: Audio data chunks
        """
        # Generate the audio file using create_speech
        audio_file = await self.create_speech(
            input_text=input_text,
            model=model,
            voice=voice,
            response_format=response_format,
            instructions=instructions,
            verbose=verbose,
        )

        # Stream the file in chunks using thread pool
        def read_file_chunks(file_path, chunk_size):
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    yield chunk

        for chunk in await asyncio.to_thread(read_file_chunks, audio_file, chunk_size):
            yield chunk

    async def tts(self, text: str, **kwargs) -> str:
        """
        Abstract async method for text-to-speech conversion.
        Must be implemented by subclasses.

        Args:
            text (str): The text to convert to speech
            **kwargs: Additional provider-specific parameters

        Returns:
            str: Path to the generated audio file

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement the async tts method")
