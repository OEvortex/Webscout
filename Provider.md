# LLM4Free Provider Documentation

This document provides a comprehensive overview of all AI providers available in the LLM4Free library.

## Table of Contents
- [Overview](#overview)
- [Chat Providers (OpenAI-Compatible)](#chat-providers-openai-compatible)
  - [Free / No-Auth Providers](#free--no-auth-providers)
  - [API-Key Providers](#api-key-providers)
  - [Cookie-Based Providers](#cookie-based-providers)
- [Specialty Providers](#specialty-providers)
- [Statistics](#statistics)
- [Usage](#usage)
- [Adding New Providers](#adding-new-providers)

---

## Overview

LLM4Free uses a **single unified interface** for all chat providers: the **OpenAI-compatible** format located in `llm4free/Provider/Openai_comp/`. Every provider implements `client.chat.completions.create(...)` — identical to the OpenAI Python SDK.

All providers are in `llm4free/Provider/Openai_comp/` (free) or `llm4free/Provider/Openai_comp/Auth/` (auth-required).

---

## Chat Providers (OpenAI-Compatible)

### Free / No-Auth Providers

No API key or cookies required.

| # | Provider | File | Models |
|---|----------|------|--------|
| 1 | **AI4Chat** | `Openai_comp/ai4chat.py` | 300+ models (GPT, Claude, Gemini, etc.) |
| 2 | **AkashGPT** | `Openai_comp/akashgpt.py` | AkashGPT models |
| 3 | **Apriel** | `Openai_comp/apriel.py` | Apriel-1.6-15B-Thinker |
| 4 | **ArtingAI** | `Openai_comp/artingai.py` | gpt-5, gpt-5.1, gpt-5.2, gpt-4o-mini, o4-mini, gemini-2.5-pro |
| 5 | **ChatGPT** | `Openai_comp/chatgpt.py` | ChatGPT models |
| 6 | **E2B** | `Openai_comp/e2b.py` | E2B models |
| 7 | **Elmo** | `Openai_comp/elmo.py` | Elmo models |
| 8 | **EssentialAI** | `Openai_comp/essentialai.py` | rnj-1-instruct |
| 9 | **ExaAI** | `Openai_comp/exaai.py` | ExaAI models |
| 10 | **FreeAI** | `Openai_comp/freeai.py` | qwen7b |
| 11 | **FreeAssist** | `Openai_comp/freeassist.py` | FreeAssist models |
| 12 | **HeckAI** | `Openai_comp/heckai.py` | gemini-2.5-flash, deepseek-chat, gpt-4o-mini, gpt-4.1-mini, etc. |
| 13 | **IBM** | `Openai_comp/ibm.py` | IBM models |
| 14 | **Jadve** | `Openai_comp/jadve.py` | gpt-5-mini, claude-3-5-haiku |
| 15 | **K2Think** | `Openai_comp/k2think.py` | K2Think models |
| 16 | **LLMChat** | `Openai_comp/llmchat.py` | LLMChat models |
| 17 | **LLMChatCo** | `Openai_comp/llmchatco.py` | LLMChatCo models |
| 18 | **Meta** | `Openai_comp/meta.py` | Meta AI models |
| 19 | **Netwrck** | `Openai_comp/netwrck.py` | Netwrck models |
| 20 | **OllamaSwarm** | `Openai_comp/OllamaSwarm.py` | Auto-discovered Ollama models |
| 21 | **OperaAria** | `Openai_comp/OperaAria.py` | Opera Aria models |
| 22 | **PiAI** | `Openai_comp/PI.py` | Pi AI models |
| 23 | **Sonus** | `Openai_comp/sonus.py` | Sonus models |
| 24 | **Toolbaz** | `Openai_comp/toolbaz.py` | Toolbaz models |
| 25 | **TurboSeek** | `Openai_comp/turboseek.py` | Llama 3.1 70B |
| 26 | **TypliAI** | `Openai_comp/typliai.py` | TypliAI models |
| 27 | **WiseCat** | `Openai_comp/wisecat.py` | WiseCat models |
| 28 | **Writecream** | `Openai_comp/writecream.py` | Writecream models |

### API-Key Providers

Require a paid API key.

| # | Provider | File | Auth |
|---|----------|------|------|
| 1 | **Cerebras** | `Openai_comp/Auth/cerebras.py` | API key |
| 2 | **DeepAI** | `Openai_comp/Auth/DeepAI.py` | API key |
| 3 | **DeepInfra** | `Openai_comp/Auth/deepinfra.py` | API key |
| 4 | **Groq** | `Openai_comp/Auth/groq.py` | API key |
| 5 | **HuggingFace** | `Openai_comp/Auth/huggingface.py` | API key |
| 6 | **Nvidia** | `Openai_comp/Auth/nvidia.py` | API key |
| 7 | **OpenRouter** | `Openai_comp/Auth/openrouter.py` | API key |
| 8 | **Sambanova** | `Openai_comp/Auth/sambanova.py` | API key |
| 9 | **TextPollinations** | `Openai_comp/textpollinations.py` | API key |
| 10 | **TogetherAI** | `Openai_comp/Auth/TogetherAI.py` | API key |
| 11 | **TwoAI** | `Openai_comp/Auth/TwoAI.py` | API key |
| 12 | **Upstage** | `Openai_comp/Auth/upstage.py` | API key |
| 13 | **Zenmux** | `Openai_comp/Auth/zenmux.py` | API key |

### Cookie-Based Providers

Require browser cookies from a logged-in session.

| # | Provider | File | Auth |
|---|----------|------|------|
| 1 | **Ayle** | `Openai_comp/ayle.py` | Cookies |

---

## Specialty Providers

### Text-to-Image (TTI)
Located in `llm4free/Provider/TTI/`:
- Bing Image, Magic Studio, Miragic, Pollinations, Together, VisualGPT, Image Hosting, MagiHour

### Text-to-Speech (TTS)
Located in `llm4free/Provider/TTS/`:
- DeepGram, ElevenLabs, Faster Qwen3-TTS, KittenTTS, LuxTTS, MurfAI, OpenAI FM, Parler, PocketTTS, Qwen, Sherpa, StreamElements, TTSai, XLNK

### Speech-to-Text (STT)
Located in `llm4free/Provider/STT/`:
- Cohere, ElevenLabs

### AI Search
Located in `llm4free/Provider/AISEARCH/`:
- Ayesoul, iAsk, Monica, OpenResearcher, Perplexity, WebPilotAI

---

## Statistics

```
┌──────────────────────────────┬───────┐
│ Category                     │ Count │
├──────────────────────────────┼───────┤
│ Free / No-Auth Providers     │  28   │
│ API-Key Providers            │  13   │
│ Cookie-Based Providers       │   1   │
├──────────────────────────────┼───────┤
│ TOTAL Chat Providers         │  42   │
├──────────────────────────────┼───────┤
│ TTI Providers                │   8   │
│ TTS Providers                │  14   │
│ STT Providers                │   2   │
│ AI Search Providers          │   6   │
├──────────────────────────────┼───────┤
│ GRAND TOTAL                  │  72   │
└──────────────────────────────┴───────┘
```

---

## Usage

All providers follow the same OpenAI-compatible interface:

```python
from llm4free.Provider.Openai_comp.heckai import HeckAI
from llm4free.Provider.Openai_comp.utils import ChatCompletion

client = HeckAI()
response = client.chat.completions.create(
    model="google/gemini-2.5-flash-preview",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="google/gemini-2.5-flash-preview",
    messages=[{"role": "user", "content": "Tell me a joke"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Auth-Required Providers

```python
from llm4free.Provider.Openai_comp.Auth.groq import Groq

client = Groq(api_key="gsk_...")
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

---

## Adding New Providers

To add a new provider:

1. Create `llm4free/Provider/Openai_comp/<provider_name>.py`
2. Subclass `OpenAICompatibleProvider` from `llm4free/Provider/Openai_comp/base.py`
3. Implement:
   - `models` property returning a `SimpleModelList`
   - `chat.completions` with a `Completions` class implementing `create()`
4. Add import in `llm4free/Provider/Openai_comp/__init__.py`
5. Test with `uv run pytest`

---

**Last Updated**: 2026-06-18
**Version**: 2.0
**Maintained by**: LLM4Free Development Team
