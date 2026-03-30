"""Authentication-required OpenAI-compatible providers."""

from webscout.Provider.Openai_comp.Auth.DeepAI import DeepAI
from webscout.Provider.Openai_comp.Auth.TogetherAI import TogetherAI
from webscout.Provider.Openai_comp.Auth.TwoAI import TwoAI
from webscout.Provider.Openai_comp.Auth.cerebras import Cerebras
from webscout.Provider.Openai_comp.Auth.deepinfra import DeepInfra
from webscout.Provider.Openai_comp.Auth.groq import Groq
from webscout.Provider.Openai_comp.Auth.huggingface import HuggingFace
from webscout.Provider.Openai_comp.Auth.nvidia import Nvidia
from webscout.Provider.Openai_comp.Auth.openrouter import OpenRouter
from webscout.Provider.Openai_comp.Auth.sambanova import Sambanova
from webscout.Provider.Openai_comp.Auth.upstage import Upstage
from webscout.Provider.Openai_comp.Auth.zenmux import Zenmux

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
