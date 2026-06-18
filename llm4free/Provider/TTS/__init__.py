# This file marks the directory as a Python package.
# Static imports for all TTS (Text-to-Speech) provider modules

# Base classes
from llm4free.Provider.TTS.base import (
    AsyncBaseTTSProvider,
    BaseTTSProvider,
)

# Provider implementations
from llm4free.Provider.TTS.deepgram import DeepgramTTS
from llm4free.Provider.TTS.elevenlabs import ElevenlabsTTS
from llm4free.Provider.TTS.faster_qwen3 import FasterQwen3TTS
from llm4free.Provider.TTS.kittentts import KittenTTS
from llm4free.Provider.TTS.luxtts import LuxTTS
from llm4free.Provider.TTS.murfai import MurfAITTS
from llm4free.Provider.TTS.openai_fm import OpenAIFMTTS
from llm4free.Provider.TTS.parler import ParlerTTS
from llm4free.Provider.TTS.pockettts import PocketTTS
from llm4free.Provider.TTS.qwen import QwenTTS
from llm4free.Provider.TTS.sherpa import SherpaTTS
from llm4free.Provider.TTS.streamElements import StreamElements
from llm4free.Provider.TTS.ttsai import TTSAI
from llm4free.Provider.TTS.xlnk import XLNKTTS

# Utility classes
from llm4free.Provider.TTS.utils import SentenceTokenizer

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
    "FasterQwen3TTS",
    "KittenTTS",
    "LuxTTS",
    "MurfAITTS",
    "OpenAIFMTTS",
    "ParlerTTS",
    "PocketTTS",
    "QwenTTS",
    "SherpaTTS",
    "StreamElements",
    "TTSAI",
    "XLNKTTS",
]
