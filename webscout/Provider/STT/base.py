"""
Base classes for OpenAI-compatible STT providers.

This module provides the base structure for STT providers that follow
the OpenAI Whisper API interface pattern.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, BinaryIO, Dict, Generator, List, Optional, Union, cast

# Import OpenAI response types from the main OPENAI module
try:
    from webscout.Provider.OPENAI.utils import (
        ChatCompletion as _ChatCompletion,
    )
    from webscout.Provider.OPENAI.utils import (
        ChatCompletionChunk as _ChatCompletionChunk,
    )
    from webscout.Provider.OPENAI.utils import (
        ChatCompletionMessage as _Message,
    )
    from webscout.Provider.OPENAI.utils import (
        Choice as _Choice,
    )
    from webscout.Provider.OPENAI.utils import (
        ChoiceDelta as _ChoiceDelta,
    )
    from webscout.Provider.OPENAI.utils import (
        CompletionUsage as _Usage,
    )
    from webscout.Provider.OPENAI.utils import (
        count_tokens as _count_tokens,
    )

    ChatCompletion = _ChatCompletion  # type: ignore
    ChatCompletionChunk = _ChatCompletionChunk  # type: ignore
    Choice = _Choice  # type: ignore
    ChoiceDelta = _ChoiceDelta  # type: ignore
    Message = _Message  # type: ignore
    Usage = _Usage  # type: ignore
    count_tokens = _count_tokens  # type: ignore
except ImportError:
    # Fallback if pydantic_imports is not available
    from dataclasses import dataclass

    @dataclass
    class Usage:
        prompt_tokens: int = 0
        completion_tokens: int = 0
        total_tokens: int = 0

    @dataclass
    class Message:
        role: str
        content: str

    @dataclass
    class Choice:
        index: int
        message: Message
        finish_reason: Optional[str] = None

    @dataclass
    class ChoiceDelta:
        content: Optional[str] = None
        role: Optional[str] = None

    @dataclass
    class ChatCompletionChunk:
        id: str
        choices: List[Dict[str, Any]]
        created: int
        model: str
        object: str = "chat.completion.chunk"

    @dataclass
    class ChatCompletion:
        id: str
        choices: List[Choice]
        created: int
        model: str
        usage: Usage
        object: str = "chat.completion"

    def count_tokens(text: str) -> int:
        return len(text.split())


class TranscriptionResponse:
    """Response object that mimics OpenAI's transcription response."""

    def __init__(self, data: Dict[str, Any], response_format: str = "json"):
        self._data = data
        self._response_format = response_format

    @property
    def text(self) -> str:
        """Get the transcribed text."""
        return self._data.get("text", "")

    @property
    def language(self) -> Optional[str]:
        """Get the detected language."""
        return self._data.get("language")

    @property
    def duration(self) -> Optional[float]:
        """Get the audio duration."""
        return self._data.get("duration")

    @property
    def segments(self) -> Optional[list]:
        """Get the segments with timestamps."""
        return self._data.get("segments")

    @property
    def words(self) -> Optional[list]:
        """Get the words with timestamps."""
        return self._data.get("words")

    def __str__(self) -> str:
        """Return string representation based on response format."""
        if self._response_format == "text":
            return self.text
        elif self._response_format == "srt":
            return self._to_srt()
        elif self._response_format == "vtt":
            return self._to_vtt()
        else:  # json or verbose_json
            return json.dumps(self._data, indent=2)

    def _to_srt(self) -> str:
        """Convert to SRT subtitle format."""
        if not self.segments:
            return ""

        srt_content = []
        for i, segment in enumerate(self.segments, 1):
            start_time = self._format_time_srt(segment.get("start", 0))
            end_time = self._format_time_srt(segment.get("end", 0))
            text = segment.get("text", "").strip()

            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")

        return "\n".join(srt_content)

    def _to_vtt(self) -> str:
        """Convert to VTT subtitle format."""
        if not self.segments:
            return "WEBVTT\n\n"

        vtt_content = ["WEBVTT", ""]
        for segment in self.segments:
            start_time = self._format_time_vtt(segment.get("start", 0))
            end_time = self._format_time_vtt(segment.get("end", 0))
            text = segment.get("text", "").strip()

            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(text)
            vtt_content.append("")

        return "\n".join(vtt_content)

    def _format_time_srt(self, seconds: float) -> str:
        """Format time for SRT format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def _format_time_vtt(self, seconds: float) -> str:
        """Format time for VTT format (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"


class BaseSTTTranscriptions(ABC):
    """Base class for STT transcriptions interface."""

    def __init__(self, client):
        self._client = client

    @abstractmethod
    def create(
        self,
        *,
        model: str,
        file: Union[BinaryIO, str, Path],
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "json",
        temperature: Optional[float] = None,
        timestamp_granularities: Optional[List[str]] = None,
        stream: bool = False,
        timeout: Optional[int] = None,
        proxies: Optional[dict] = None,
        **kwargs: Any,
    ) -> Union[TranscriptionResponse, Generator[str, None, None]]:
        """
        Create a transcription of the given audio file.

        Args:
            model: Model to use for transcription
            file: Audio file to transcribe
            language: Language of the audio (ISO-639-1 format)
            prompt: Optional text to guide the model's style
            response_format: Format of the response
            temperature: Sampling temperature (0 to 1)
            timestamp_granularities: Timestamp granularities to include
            stream: Whether to stream the response
            timeout: Request timeout
            proxies: Proxy configuration
            **kwargs: Additional parameters

        Returns:
            TranscriptionResponse or generator of SSE strings if streaming
        """
        raise NotImplementedError


class BaseSTTAudio(ABC):
    """Base class for STT audio interface."""

    def __init__(self, client):
        self.transcriptions = self._create_transcriptions(client)

    @abstractmethod
    def _create_transcriptions(self, client) -> BaseSTTTranscriptions:
        """Create the transcriptions interface."""
        raise NotImplementedError


class BaseSTTChat:
    """Base chat interface for STT providers (placeholder for consistency)."""

    def __init__(self, client):
        _ = client  # Unused but kept for interface consistency
        self.completions = None  # STT providers don't have completions


class STTCompatibleProvider(ABC):
    """
    Abstract Base Class for STT providers mimicking the OpenAI structure.
    Requires a nested 'audio.transcriptions' structure.
    """

    audio: BaseSTTAudio

    @abstractmethod
    def __init__(self, **kwargs: Any):
        """Initialize the STT provider."""
        pass

    @property
    @abstractmethod
    def models(self) -> STTModels:
        """
        Property that returns an object with a .list() method returning available models.
        """
        raise NotImplementedError


class STTModels:
    """Models interface for STT providers."""

    def __init__(self, available_models: List[str]):
        self._available_models = available_models

    def list(self) -> List[Dict[str, Any]]:
        """List available models."""
        return [
            {"id": model, "object": "model", "created": int(time.time()), "owned_by": "webscout"}
            for model in self._available_models
        ]


__all__ = [
    "TranscriptionResponse",
    "BaseSTTTranscriptions",
    "BaseSTTAudio",
    "BaseSTTChat",
    "STTCompatibleProvider",
    "STTModels",
    "ChatCompletion",
    "ChatCompletionChunk",
    "Choice",
    "ChoiceDelta",
    "Message",
    "Usage",
    "count_tokens",
]
