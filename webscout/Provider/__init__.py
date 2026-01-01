# This file marks the directory as a Python package.
# Static imports for all Provider modules
from webscout.Provider.ai4chat import AI4Chat
from webscout.Provider.akashgpt import AkashGPT
from webscout.Provider.Algion import Algion
from webscout.Provider.Andi import AndiSearch
from webscout.Provider.Apriel import Apriel
from webscout.Provider.Ayle import Ayle
from webscout.Provider.cerebras import Cerebras
from webscout.Provider.ChatSandbox import ChatSandbox
from webscout.Provider.ClaudeOnline import ClaudeOnline
from webscout.Provider.cleeai import Cleeai
from webscout.Provider.Cohere import Cohere
from webscout.Provider.DeepAI import DeepAI
from webscout.Provider.Deepinfra import DeepInfra
from webscout.Provider.elmo import Elmo
from webscout.Provider.EssentialAI import EssentialAI
from webscout.Provider.ExaAI import ExaAI
from webscout.Provider.Gemini import GEMINI
from webscout.Provider.geminiapi import GEMINIAPI
from webscout.Provider.GithubChat import GithubChat
from webscout.Provider.Gradient import Gradient
from webscout.Provider.Groq import GROQ
from webscout.Provider.HadadXYZ import HadadXYZ
from webscout.Provider.HeckAI import HeckAI
from webscout.Provider.HuggingFace import HuggingFace
from webscout.Provider.IBM import IBM
from webscout.Provider.Jadve import JadveOpenAI
from webscout.Provider.julius import Julius
from webscout.Provider.K2Think import K2Think
from webscout.Provider.Koboldai import KOBOLDAI
from webscout.Provider.learnfastai import LearnFast
from webscout.Provider.llama3mitril import Llama3Mitril
from webscout.Provider.llmchat import LLMChat
from webscout.Provider.llmchatco import LLMChatCo
from webscout.Provider.meta import Meta
from webscout.Provider.Netwrck import Netwrck
from webscout.Provider.Nvidia import Nvidia
from webscout.Provider.oivscode import oivscode
from webscout.Provider.OpenRouter import OpenRouter
from webscout.Provider.PI import PiAI
from webscout.Provider.QwenLM import QwenLM
from webscout.Provider.Sambanova import Sambanova
from webscout.Provider.searchchat import SearchChatAI
from webscout.Provider.sonus import SonusAI
from webscout.Provider.TextPollinationsAI import TextPollinationsAI
from webscout.Provider.TogetherAI import TogetherAI
from webscout.Provider.toolbaz import Toolbaz
from webscout.Provider.turboseek import TurboSeek
from webscout.Provider.TwoAI import TwoAI
from webscout.Provider.typefully import TypefullyAI
from webscout.Provider.TypliAI import TypliAI
from webscout.Provider.WiseCat import WiseCat
from webscout.Provider.WrDoChat import WrDoChat
from webscout.Provider.x0gpt import X0GPT

from .Openai import OpenAI

# List of all exported names
__all__ = [
    "OpenAI",
    "TypliAI",
    "AI4Chat",
    "AkashGPT",
    "Algion",
    "AndiSearch",
    "Apriel",
    "Cerebras",
    "ChatSandbox",
    "ClaudeOnline",
    "Cleeai",
    "Cohere",
    "DeepAI",
    "DeepInfra",
    "Elmo",
    "EssentialAI",
    "ExaAI",
    "Ayle",
    "GEMINI",
    "GEMINIAPI",
    "GithubChat",
    "HadadXYZ",
    "Gradient",
    "GROQ",
    "HeckAI",
    "HuggingFace",
    "IBM",
    "JadveOpenAI",
    "Julius",
    "K2Think",
    "KOBOLDAI",
    "LearnFast",
    "Llama3Mitril",
    "LLMChat",
    "LLMChatCo",
    "Meta",
    "Netwrck",
    "Nvidia",
    "OpenRouter",
    "oivscode",
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
    "TypefullyAI",
    "WiseCat",
    "WrDoChat",
    "X0GPT",
]
