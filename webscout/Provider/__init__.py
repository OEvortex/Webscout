# webscout/providers/__init__.py
from .PI import *
from .Llama import LLAMA
from .Cohere import Cohere
from .Reka import REKA
from .Groq import GROQ
from .Groq import AsyncGROQ
from .Openai import OPENAI
from .Openai import AsyncOPENAI
from .Koboldai import KOBOLDAI
from .Koboldai import AsyncKOBOLDAI
from .Blackboxai import BLACKBOXAI
from .Phind import PhindSearch
from .Phind import Phindv2
from .ai4chat import *
from .Gemini import GEMINI
from .Deepinfra import DeepInfra
from .typefully import *
from .cleeai import *
from .OLLAMA import OLLAMA
from .Andi import AndiSearch
from .PizzaGPT import *
from .Llama3 import *
from .koala import *
from .meta import *
from .julius import *
from .Youchat import *
from .yep import *
from .Cloudflare import *
from .turboseek import *
from .Free2GPT import *
from .TeachAnything import *
from .AI21 import *
from .Chatify import *
from .x0gpt import *
from .cerebras import *
from .lepton import *
from .geminiapi import *
from .elmo import *
from .GPTWeb import *
from .Netwrck import Netwrck
from .llamatutor import *
from .promptrefine import *
from .tutorai import *
from .ChatGPTES import *
from .bagoodex import *
from .aimathgpt import *
from .gaurish import *
from .geminiprorealtime import *
from .llmchat import *
from .llmchatco import LLMChatCo  # Add new LLMChat.co provider
from .talkai import *
from .askmyai import *
from .llama3mitril import *
from .Marcus import *
from .typegpt import *
from .multichat import *
from .Jadve import *
from .chatglm import *
from .hermes import *
from .TextPollinationsAI import *
from .Glider import *
from .ChatGPTGratis import *
from .QwenLM import *
from .granite import *
from .WiseCat import *
from .DeepSeek import *
from .freeaichat import FreeAIChat
from .akashgpt import *
from .Perplexitylabs import *
from .AllenAI import *
from .HeckAI import *
from .TwoAI import *
from .Venice import *
from .ElectronHub import *
from .HuggingFaceChat import *
from .GithubChat import *
from .copilot import *
from .C4ai import *
from .sonus import *
from .uncovr import *
from .labyrinth import *
from .WebSim import *
from .LambdaChat import *
from .ChatGPTClone import *
from .VercelAI import *
from .ExaChat import *
from .asksteve import *
from .Aitopia import *
from .searchchat import *
from .ExaAI import ExaAI
from .OpenGPT import OpenGPT
from .scira_chat import *
from .StandardInput import *

__all__ = [
    'LLAMA',
    'SciraAI',
    'StandardInputAI',
    'LabyrinthAI',
    'OpenGPT',
    'C4ai',
    'Venice',
    'ExaAI',
    'Copilot',
    'HuggingFaceChat',
    'TwoAI',
    'HeckAI',
    'AllenAI',
    'PerplexityLabs',
    'AkashGPT',
    'DeepSeek',
    'WiseCat',
    'IBMGranite',
    'QwenLM',
    'ChatGPTGratis',
    'LambdaChat',
    'TextPollinationsAI',
    'GliderAI',
    'Cohere',
    'REKA',
    'GROQ',
    'AsyncGROQ',
    'OPENAI',
    'AsyncOPENAI',
    'KOBOLDAI',
    'AsyncKOBOLDAI',
    'BLACKBOXAI',
    'PhindSearch',
    'GEMINI',
    'DeepInfra',
    'AI4Chat',
    'Phindv2',
    'OLLAMA',
    'AndiSearch',
    'PIZZAGPT',
    'Sambanova',
    'KOALA',
    'Meta',
    'AskMyAI',
    'PiAI',
    'Julius',
    'YouChat',
    'YEPCHAT',
    'Cloudflare',
    'TurboSeek',
    'TeachAnything',
    'AI21',
    'Chatify',
    'X0GPT',
    'Cerebras',
    'Lepton',
    'GEMINIAPI',
    'SonusAI',
    'Cleeai',
    'Elmo',
    'ChatGPTClone',
    'TypefullyAI',
    'Free2GPT',
    'GPTWeb',
    'Netwrck',
    'LlamaTutor',
    'PromptRefine',
    'TutorAI',
    'ChatGPTES',
    'Bagoodex',
    'AIMathGPT',
    'GaurishCerebras',
    'GeminiPro',
    'LLMChat',
    'LLMChatCo',
    'Talkai',
    'Llama3Mitril',
    'Marcus',
    'TypeGPT',
    'Netwrck',
    'MultiChatAI',
    'JadveOpenAI',
    'ChatGLM',
    'NousHermes',
    'FreeAIChat',
    'ElectronHub',
    'GithubChat',
    'UncovrAI',
    'WebSim',
    'VercelAI',
    'ExaChat',
    'AskSteve',
    'Aitopia',
    'SearchChatAI',
]
