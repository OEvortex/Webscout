# This file marks the directory as a Python package.
# Static imports for all Provider modules
#
# Providers moved to UNFINISHED/ on 2026-06-12 (their upstreams went away):
#   Ayle, Elmo, SonusAI, LLMChatCo, Meta
# See llm4free/Provider/UNFINISHED/README.md and
# BROKEN_PROVIDERS_ANALYSIS.md for the full rationale.
from llm4free.Provider.Auth import (
    AkashGPT,
    Cerebras,
    Cohere,
    DeepAI,
    DeepInfra,
    Falcon,
    GEMINI,
    GEMINIAPI,
    GithubChat,
    GROQ,
    HuggingFace,
    Julius,
    Nvidia,
    OpenAI,
    OpenRouter,
    PollinationsAI,
    QwenLM,
    Sambanova,
    TogetherAI,
    TwoAI,
    Upstage,
    WrDoChat,
)
from llm4free.Provider.ai4chat import AI4Chat
from llm4free.Provider.Apriel import Apriel
from llm4free.Provider.ArtingAI import ArtingAI
from llm4free.Provider.AskaiFree import AskaiFree
from llm4free.Provider.CohereCommand import CohereCommand
from llm4free.Provider.EssentialAI import EssentialAI
from llm4free.Provider.ExaAI import ExaAI
from llm4free.Provider.FreeAI import FreeAI
from llm4free.Provider.HeckAI import HeckAI
from llm4free.Provider.IBM import IBM
from llm4free.Provider.Jadve import JadveOpenAI
from llm4free.Provider.k2think import K2Think

from llm4free.Provider.llmchat import LLMChat
from llm4free.Provider.Netwrck import Netwrck
from llm4free.Provider.OllamaSwarm import OllamaSwarm
from llm4free.Provider.OperaAria import OperaAria
from llm4free.Provider.PI import PiAI
from llm4free.Provider.searchchat import SearchChatAI
from llm4free.Provider.toolbaz import Toolbaz
from llm4free.Provider.turboseek import TurboSeek
from llm4free.Provider.TypliAI import TypliAI
from llm4free.Provider.WiseCat import WiseCat


# List of all exported names
__all__ = [
    "OpenAI",
    "TypliAI",
    "AI4Chat",
    "AkashGPT",
    "Apriel",
    "ArtingAI",
    "AskaiFree",
    "Cerebras",
    "Cohere",
    "CohereCommand",
    "DeepAI",
    "DeepInfra",
    "Falcon",
    "EssentialAI",
    "ExaAI",
    "FreeAI",
    "GEMINI",
    "GEMINIAPI",
    "GithubChat",

    "GROQ",
    "HeckAI",
    "HuggingFace",
    "IBM",
    "JadveOpenAI",
    "Julius",

    "LLMChat",
    "Netwrck",
    "Nvidia",
    "OllamaSwarm",
    "OpenRouter",
    "OperaAria",
    "PiAI",
    "QwenLM",
    "Sambanova",
    "SearchChatAI",
    "PollinationsAI",
    "TogetherAI",
    "Toolbaz",
    "TurboSeek",
    "TwoAI",
    "Upstage",
    "WiseCat",
    "WrDoChat",
]
