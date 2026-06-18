"""Authentication-required providers for Webscout."""

from llm4free.Provider.Auth.akashgpt import AkashGPT
from llm4free.Provider.Auth.cerebras import Cerebras
from llm4free.Provider.Auth.Cohere import Cohere
from llm4free.Provider.Auth.DeepAI import DeepAI
from llm4free.Provider.Auth.Deepinfra import DeepInfra
from llm4free.Provider.Auth.Falcon import Falcon
from llm4free.Provider.Auth.Gemini import GEMINI
from llm4free.Provider.Auth.geminiapi import GEMINIAPI
from llm4free.Provider.Auth.GithubChat import GithubChat
from llm4free.Provider.Auth.Groq import GROQ
from llm4free.Provider.Auth.HuggingFace import HuggingFace
from llm4free.Provider.Auth.julius import Julius
from llm4free.Provider.Auth.Nvidia import Nvidia
from llm4free.Provider.Auth.Openai import OpenAI
from llm4free.Provider.Auth.OpenRouter import OpenRouter
from llm4free.Provider.Auth.PollinationsAI import PollinationsAI
from llm4free.Provider.Auth.QwenLM import QwenLM
from llm4free.Provider.Auth.Sambanova import Sambanova
from llm4free.Provider.Auth.TogetherAI import TogetherAI
from llm4free.Provider.Auth.TwoAI import TwoAI
from llm4free.Provider.Auth.Upstage import Upstage
from llm4free.Provider.Auth.WrDoChat import WrDoChat

__all__ = [
    "AkashGPT",
    "Cerebras",
    "Cohere",
    "DeepAI",
    "DeepInfra",
    "Falcon",
    "GEMINI",
    "GEMINIAPI",
    "GithubChat",
    "GROQ",
    "HuggingFace",
    "Julius",
    "Nvidia",
    "OpenAI",
    "OpenRouter",
    "PollinationsAI",
    "QwenLM",
    "Sambanova",
    "TogetherAI",
    "TwoAI",
    "Upstage",
    "WrDoChat",
]
