"""Authentication-required OpenAI-compatible providers."""

from llm4free.Provider.llm.Auth.DeepAI import DeepAI
from llm4free.Provider.llm.Auth.TogetherAI import TogetherAI
from llm4free.Provider.llm.Auth.TwoAI import TwoAI
from llm4free.Provider.llm.Auth.cerebras import Cerebras
from llm4free.Provider.llm.Auth.deepinfra import DeepInfra
from llm4free.Provider.llm.Auth.groq import Groq
from llm4free.Provider.llm.Auth.huggingface import HuggingFace
from llm4free.Provider.llm.Auth.nvidia import Nvidia
from llm4free.Provider.llm.Auth.openrouter import OpenRouter
from llm4free.Provider.llm.Auth.sambanova import Sambanova
from llm4free.Provider.llm.Auth.upstage import Upstage
from llm4free.Provider.llm.Auth.zenmux import Zenmux

__all__ = [
    "DeepAI",
    "TogetherAI",
    "TwoAI",
    "Cerebras",
    "DeepInfra",
    "Groq",
    "HuggingFace",
    "Nvidia",
    "OpenRouter",
    "Sambanova",
    "Upstage",
    "Zenmux",
]
