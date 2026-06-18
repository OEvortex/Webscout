# This file marks the directory as a Python package.
# Static imports for all TTS (Text-to-Speech) provider modules

# Base classes
from llm4free.TTS.base import (
    AsyncBaseTTSProvider,
    BaseTTSProvider,
)

# Provider implementations
from llm4free.TTS.deepgram import DeepgramTTS
from llm4free.TTS.elevenlabs import ElevenlabsTTS
from llm4free.TTS.faster_qwen3 import FasterQwen3TTS
from llm4free.TTS.kittentts import KittenTTS
from llm4free.TTS.luxtts import LuxTTS
from llm4free.TTS.murfai import MurfAITTS
from llm4free.TTS.openai_fm import OpenAIFMTTS
from llm4free.TTS.parler import ParlerTTS
from llm4free.TTS.pockettts import PocketTTS
from llm4free.TTS.qwen import QwenTTS
from llm4free.TTS.sherpa import SherpaTTS
from llm4free.TTS.streamElements import StreamElements
from llm4free.TTS.ttsai import TTSAI
from llm4free.TTS.xlnk import XLNKTTS

# Utility classes
from llm4free.TTS.utils import SentenceTokenizer

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
