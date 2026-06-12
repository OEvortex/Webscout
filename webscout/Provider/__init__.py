# This file marks the directory as a Python package.
# Static imports for all Provider modules
#
# Providers moved to UNFINISHED/ on 2026-06-12 (their upstreams went away):
#   Ayle, Elmo, SonusAI, LLMChatCo, Meta
# See webscout/Provider/UNFINISHED/README.md and
# BROKEN_PROVIDERS_ANALYSIS.md for the full rationale.
from webscout.Provider.Auth import (
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
from webscout.Provider.ai4chat import AI4Chat
from webscout.Provider.Apriel import Apriel
from webscout.Provider.ArtingAI import ArtingAI
from webscout.Provider.AskaiFree import AskaiFree
from webscout.Provider.CohereCommand import CohereCommand
from webscout.Provider.EssentialAI import EssentialAI
from webscout.Provider.ExaAI import ExaAI
from webscout.Provider.FreeAI import FreeAI
from webscout.Provider.HeckAI import HeckAI
from webscout.Provider.IBM import IBM
from webscout.Provider.Jadve import JadveOpenAI
from webscout.Provider.k2think import K2Think

from webscout.Provider.llmchat import LLMChat
from webscout.Provider.Netwrck import Netwrck
from webscout.Provider.OllamaSwarm import OllamaSwarm
from webscout.Provider.OperaAria import OperaAria
from webscout.Provider.PI import PiAI
from webscout.Provider.searchchat import SearchChatAI
from webscout.Provider.toolbaz import Toolbaz
from webscout.Provider.turboseek import TurboSeek
from webscout.Provider.TypliAI import TypliAI
from webscout.Provider.WiseCat import WiseCat


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
