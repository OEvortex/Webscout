# This file marks the directory as a Python package.
# Static imports for all llm provider modules
#
# 2026-06-12: Ayle, Elmo, SonusAI, LLMChatCo, Meta were moved to
# llm4free/Provider/UNFINISHED/ (their upstreams went away).

# Base classes and utilities
from llm4free.Provider.llm.ai4chat import AI4Chat
from llm4free.Provider.llm.akashgpt import AkashGPT
from llm4free.Provider.llm.base import (
    BaseChat,
    BaseCompletions,
    FunctionDefinition,
    FunctionParameters,
    OpenAICompatibleProvider,
    SimpleModelList,
    Tool,
    ToolDefinition,
)
from llm4free.Provider.llm.Auth import (
    Cerebras,
    DeepAI,
    DeepInfra,
    Groq,
    HuggingFace,
    Nvidia,
    OpenRouter,
    Sambanova,
    TogetherAI,
    TwoAI,
    Upstage,
    Zenmux,
)
from llm4free.Provider.llm.chatgpt import ChatGPT, ChatGPTReversed

# Provider implementations
from llm4free.Provider.llm.e2b import E2B
from llm4free.Provider.llm.exaai import ExaAI
from llm4free.Provider.llm.freeassist import FreeAssist
from llm4free.Provider.llm.heckai import HeckAI
from llm4free.Provider.llm.ibm import IBM
from llm4free.Provider.llm.k2think import K2Think
from llm4free.Provider.llm.llmchat import LLMChat
from llm4free.Provider.llm.netwrck import Netwrck
from llm4free.Provider.llm.OllamaSwarm import OllamaSwarm
from llm4free.Provider.llm.OperaAria import OperaAria
from llm4free.Provider.llm.PI import PiAI
from llm4free.Provider.llm.textpollinations import TextPollinations
from llm4free.Provider.llm.toolbaz import Toolbaz
from llm4free.Provider.llm.typliai import TypliAI
from llm4free.Provider.llm.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    FunctionCall,
    ModelData,
    ModelList,
    ToolCall,
    ToolCallType,
    ToolFunction,
    count_tokens,
    format_prompt,
    get_last_user_message,
    get_system_prompt,
)
from llm4free.Provider.llm.apriel import Apriel
from llm4free.Provider.llm.artingai import ArtingAI
from llm4free.Provider.llm.essentialai import EssentialAI
from llm4free.Provider.llm.freeai import FreeAI
from llm4free.Provider.llm.jadve import JadveOpenAI
from llm4free.Provider.llm.turboseek import TurboSeek
from llm4free.Provider.llm.wisecat import WiseCat
from llm4free.Provider.llm.writecream import Writecream

# List of all exported names
__all__ = [
    # Base classes and utilities
    "OpenAICompatibleProvider",
    "SimpleModelList",
    "BaseChat",
    "BaseCompletions",
    "Tool",
    "ToolDefinition",
    "FunctionParameters",
    "FunctionDefinition",
    # Utils
    "ChatCompletion",
    "ChatCompletionChunk",
    "Choice",
    "ChoiceDelta",
    "ChatCompletionMessage",
    "CompletionUsage",
    "ToolCall",
    "ToolFunction",
    "FunctionCall",
    "ToolCallType",
    "ModelData",
    "ModelList",
    "format_prompt",
    "get_system_prompt",
    "get_last_user_message",
    "count_tokens",
    # Provider implementations
    "Apriel",
    "ArtingAI",
    "DeepAI",
    "EssentialAI",
    "FreeAI",
    "JadveOpenAI",
    "TurboSeek",
    "PiAI",
    "TogetherAI",
    "TwoAI",
    "AI4Chat",
    "AkashGPT",
    "Cerebras",
    "ChatGPT",
    "ChatGPTReversed",
    "DeepInfra",
    "E2B",
    "ExaAI",
    "FreeAssist",
    "HuggingFace",
    "Groq",
    "HeckAI",
    "IBM",
    "K2Think",
    "LLMChat",
    "Netwrck",
    "Nvidia",
    "OllamaSwarm",
    "OpenRouter",
    "OperaAria",
    "TextPollinations",
    "Toolbaz",
    "Upstage",
    "WiseCat",
    "Writecream",
    "YEPCHAT",
    "Zenmux",
    "Sambanova",
    "TypliAI",
]
