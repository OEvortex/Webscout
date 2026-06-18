# This file marks the directory as a Python package.
# Static imports for all STT (Speech-to-Text) provider modules

# Base classes
from llm4free.STT.base import (
    BaseSTTAudio,
    BaseSTTChat,
    BaseSTTTranscriptions,
    STTCompatibleProvider,
    STTModels,
    TranscriptionResponse,
)

# Provider implementations
from llm4free.STT.cohere import CohereSTT
from llm4free.STT.elevenlabs import ElevenLabsSTT

# List of all exported names
__all__ = [
    # Base classes
    "STTCompatibleProvider",
    "BaseSTTTranscriptions",
    "BaseSTTAudio",
    "BaseSTTChat",
    "TranscriptionResponse",
    "STTModels",
    # Providers
    "CohereSTT",
    "ElevenLabsSTT",
]
