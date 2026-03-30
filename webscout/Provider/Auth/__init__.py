"""Authentication-required providers for Webscout."""

from webscout.Provider.Auth.akashgpt import AkashGPT
from webscout.Provider.Auth.cerebras import Cerebras
from webscout.Provider.Auth.Cohere import Cohere
from webscout.Provider.Auth.DeepAI import DeepAI
from webscout.Provider.Auth.Deepinfra import DeepInfra
from webscout.Provider.Auth.Falcon import Falcon
from webscout.Provider.Auth.Gemini import GEMINI
from webscout.Provider.Auth.geminiapi import GEMINIAPI
from webscout.Provider.Auth.GithubChat import GithubChat
from webscout.Provider.Auth.Groq import GROQ
from webscout.Provider.Auth.HuggingFace import HuggingFace
from webscout.Provider.Auth.julius import Julius
from webscout.Provider.Auth.Nvidia import Nvidia
from webscout.Provider.Auth.Openai import OpenAI
from webscout.Provider.Auth.OpenRouter import OpenRouter
from webscout.Provider.Auth.QwenLM import QwenLM
from webscout.Provider.Auth.Sambanova import Sambanova
from webscout.Provider.Auth.TogetherAI import TogetherAI
from webscout.Provider.Auth.TwoAI import TwoAI
from webscout.Provider.Auth.Upstage import Upstage
from webscout.Provider.Auth.WrDoChat import WrDoChat

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
    "QwenLM",
    "Sambanova",
    "TogetherAI",
    "TwoAI",
    "Upstage",
    "WrDoChat",
]
