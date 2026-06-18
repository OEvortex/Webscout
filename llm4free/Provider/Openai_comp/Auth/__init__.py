"""Authentication-required OpenAI-compatible providers."""

from llm4free.Provider.Openai_comp.Auth.DeepAI import DeepAI
from llm4free.Provider.Openai_comp.Auth.TogetherAI import TogetherAI
from llm4free.Provider.Openai_comp.Auth.TwoAI import TwoAI
from llm4free.Provider.Openai_comp.Auth.cerebras import Cerebras
from llm4free.Provider.Openai_comp.Auth.deepinfra import DeepInfra
from llm4free.Provider.Openai_comp.Auth.groq import Groq
from llm4free.Provider.Openai_comp.Auth.huggingface import HuggingFace
from llm4free.Provider.Openai_comp.Auth.nvidia import Nvidia
from llm4free.Provider.Openai_comp.Auth.openrouter import OpenRouter
from llm4free.Provider.Openai_comp.Auth.sambanova import Sambanova
from llm4free.Provider.Openai_comp.Auth.upstage import Upstage
from llm4free.Provider.Openai_comp.Auth.zenmux import Zenmux

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
