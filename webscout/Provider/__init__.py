# This file marks the directory as a Python package.
# Static imports for all Provider modules
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
    QwenLM,
    Sambanova,
    TogetherAI,
    TwoAI,
    Upstage,
    WrDoChat,
)
from webscout.Provider.ai4chat import AI4Chat
from webscout.Provider.Apriel import Apriel
from webscout.Provider.Ayle import Ayle
from webscout.Provider.AvaSupernova import AvaSupernova
from webscout.Provider.CohereCommand import CohereCommand
from webscout.Provider.elmo import Elmo
from webscout.Provider.EssentialAI import EssentialAI
from webscout.Provider.ExaAI import ExaAI
from webscout.Provider.HeckAI import HeckAI
from webscout.Provider.IBM import IBM
from webscout.Provider.Jadve import JadveOpenAI
from webscout.Provider.k2think import K2Think

from webscout.Provider.llmchat import LLMChat
from webscout.Provider.llmchatco import LLMChatCo
from webscout.Provider.meta import Meta
from webscout.Provider.Netwrck import Netwrck
from webscout.Provider.PI import PiAI
from webscout.Provider.searchchat import SearchChatAI
from webscout.Provider.sonus import SonusAI
from webscout.Provider.TextPollinationsAI import TextPollinationsAI
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
    "Cerebras",
    "Cohere",
    "CohereCommand",
    "DeepAI",
    "DeepInfra",
    "AvaSupernova",
    "Falcon",
    "Elmo",
    "EssentialAI",
    "ExaAI",
    "Ayle",
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
    "LLMChatCo",
    "Meta",
    "Netwrck",
    "Nvidia",
    "OpenRouter",
    "PiAI",
    "QwenLM",
    "Sambanova",
    "SearchChatAI",
    "SonusAI",
    "TextPollinationsAI",
    "TogetherAI",
    "Toolbaz",
    "TurboSeek",
    "TwoAI",
    "Upstage",
    "WiseCat",
    "WrDoChat",
]
