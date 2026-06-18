# This file marks the directory as a Python package.
# Static imports for all Openai_comp provider modules
#
# 2026-06-12: Ayle, Elmo, SonusAI, LLMChatCo, Meta were moved to
# llm4free/Provider/UNFINISHED/ (their upstreams went away).

# Base classes and utilities
from llm4free.Provider.Openai_comp.ai4chat import AI4Chat
from llm4free.Provider.Openai_comp.akashgpt import AkashGPT
from llm4free.Provider.Openai_comp.base import (
    BaseChat,
    BaseCompletions,
    FunctionDefinition,
    FunctionParameters,
    OpenAICompatibleProvider,
    SimpleModelList,
    Tool,
    ToolDefinition,
)
from llm4free.Provider.Openai_comp.Auth import (
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
from llm4free.Provider.Openai_comp.chatgpt import ChatGPT, ChatGPTReversed

# Provider implementations
from llm4free.Provider.Openai_comp.e2b import E2B
from llm4free.Provider.Openai_comp.exaai import ExaAI
from llm4free.Provider.Openai_comp.freeassist import FreeAssist
from llm4free.Provider.Openai_comp.heckai import HeckAI
from llm4free.Provider.Openai_comp.ibm import IBM
from llm4free.Provider.Openai_comp.k2think import K2Think
from llm4free.Provider.Openai_comp.llmchat import LLMChat
from llm4free.Provider.Openai_comp.netwrck import Netwrck
from llm4free.Provider.Openai_comp.OllamaSwarm import OllamaSwarm
from llm4free.Provider.Openai_comp.OperaAria import OperaAria
from llm4free.Provider.Openai_comp.PI import PiAI
from llm4free.Provider.Openai_comp.textpollinations import TextPollinations
from llm4free.Provider.Openai_comp.toolbaz import Toolbaz
from llm4free.Provider.Openai_comp.typliai import TypliAI
from llm4free.Provider.Openai_comp.utils import (
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
from llm4free.Provider.Openai_comp.wisecat import WiseCat
from llm4free.Provider.Openai_comp.writecream import Writecream

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
    "DeepAI",
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
