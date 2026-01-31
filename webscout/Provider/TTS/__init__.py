# This file marks the directory as a Python package.
# Static imports for all TTS (Text-to-Speech) provider modules

# Base classes
from webscout.Provider.TTS.base import (
    AsyncBaseTTSProvider,
    BaseTTSProvider,
)

# Provider implementations
from webscout.Provider.TTS.deepgram import DeepgramTTS
from webscout.Provider.TTS.elevenlabs import ElevenlabsTTS
from webscout.Provider.TTS.freetts import FreeTTS
from webscout.Provider.TTS.murfai import MurfAITTS
from webscout.Provider.TTS.openai_fm import OpenAIFMTTS
from webscout.Provider.TTS.parler import ParlerTTS
from webscout.Provider.TTS.pockettts import PocketTTS
from webscout.Provider.TTS.qwen import QwenTTS
from webscout.Provider.TTS.sherpa import SherpaTTS
from webscout.Provider.TTS.speechma import SpeechMaTTS
from webscout.Provider.TTS.streamElements import StreamElements

# Utility classes
from webscout.Provider.TTS.utils import SentenceTokenizer

# List of all exported names
__all__ = [
    # Base classes
    "BaseTTSProvider",
    "AsyncBaseTTSProvider",
    # Utilities
    "SentenceTokenizer",
    # Providers
    "DeepgramTTS",
    "ElevenlabsTTS",
    "FreeTTS",
    "MurfAITTS",
    "OpenAIFMTTS",
    "ParlerTTS",
    "PocketTTS",
    "QwenTTS",
    "SherpaTTS",
    "SpeechMaTTS",
    "StreamElements",
]
