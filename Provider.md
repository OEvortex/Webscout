# LLM4Free Provider Documentation

This document provides a comprehensive overview of all AI providers available in the LLM4Free library, categorized by their implementation types.


## Table of Contents
- [Overview](#overview)
- [Providers with Both Normal and OpenAI-Compatible Versions](#providers-with-both-normal-and-openai-compatible-versions)
- [Providers with Only Normal Version](#providers-with-only-normal-version)
- [Providers with Only OpenAI-Compatible Version](#providers-with-only-openai-compatible-version)
- [Statistics](#statistics)
- [Provider Categories](#provider-categories)

## Overview

LLM4Free supports multiple AI providers with different implementation approaches:
- **Normal Providers**: Standard implementation located in `llm4free/Provider/`
- **OpenAI-Compatible Providers**: OpenAI API-compatible implementation located in `llm4free/Provider/Openai_comp/`
- **Hybrid Providers**: Available in both normal and OpenAI-compatible versions

---

## Providers with Both Normal and OpenAI-Compatible Versions

These providers have both standard and OpenAI-compatible implementations, giving users flexibility in how they interact with the API.

| # | Provider Name | Normal Path | OpenAI Path |
|---|---------------|-------------|-------------|
| 1 | **AI4Chat** | `llm4free/Provider/ai4chat.py` | `llm4free/Provider/Openai_comp/ai4chat.py` |
| 2 | **AkashGPT** | `llm4free/Provider/akashgpt.py` | `llm4free/Provider/Openai_comp/akashgpt.py` |
| 3 | **Algion** | `llm4free/Provider/Algion.py` | `llm4free/Provider/Openai_comp/algion.py` |
| 4 | **Cerebras** | `llm4free/Provider/cerebras.py` | `llm4free/Provider/Openai_comp/cerebras.py` |
| 5 | **DeepAI** | `llm4free/Provider/DeepAI.py` | `llm4free/Provider/Openai_comp/DeepAI.py` |
| 6 | **DeepInfra** | `llm4free/Provider/Deepinfra.py` | `llm4free/Provider/Openai_comp/deepinfra.py` |
| 7 | **Elmo** | `llm4free/Provider/elmo.py` | `llm4free/Provider/Openai_comp/elmo.py` |
| 8 | **ExaAI** | `llm4free/Provider/ExaAI.py` | `llm4free/Provider/Openai_comp/exaai.py` |
| 9 | **Ayle** | `llm4free/Provider/Ayle.py` | `llm4free/Provider/Openai_comp/ayle.py` |
| 10 | **Groq** | `llm4free/Provider/Groq.py` | `llm4free/Provider/Openai_comp/groq.py` |
| 11 | **HeckAI** | `llm4free/Provider/HeckAI.py` | `llm4free/Provider/Openai_comp/heckai.py` |
| 12 | **HuggingFace** | `llm4free/Provider/HuggingFace.py` | `llm4free/Provider/Openai_comp/huggingface.py` |
| 13 | **IBM** | `llm4free/Provider/IBM.py` | `llm4free/Provider/Openai_comp/ibm.py` |
| 14 | **K2Think** | `llm4free/Provider/k2think.py` | `llm4free/Provider/Openai_comp/k2think.py` |
| 15 | **LLMChatCo** | `llm4free/Provider/llmchatco.py` | `llm4free/Provider/Openai_comp/llmchatco.py` |
| 17 | **Netwrck** | `llm4free/Provider/Netwrck.py` | `llm4free/Provider/Openai_comp/netwrck.py` |
| 18 | **Nvidia** | `llm4free/Provider/Nvidia.py` | `llm4free/Provider/Openai_comp/nvidia.py` |
| 19 | **OIVSCode** | `llm4free/Provider/oivscode.py` | `llm4free/Provider/Openai_comp/oivscode.py` |
| 20 | **PI** | `llm4free/Provider/PI.py` | `llm4free/Provider/Openai_comp/PI.py` |
| 21 | **Sonus** | `llm4free/Provider/sonus.py` | `llm4free/Provider/Openai_comp/sonus.py` |
| 22 | **PollinationsAI** | `llm4free/Provider/Auth/PollinationsAI.py` | `llm4free/Provider/Openai_comp/textpollinations.py` |
| 23 | **TogetherAI** | `llm4free/Provider/TogetherAI.py` | `llm4free/Provider/Openai_comp/TogetherAI.py` |
| 24 | **Toolbaz** | `llm4free/Provider/toolbaz.py` | `llm4free/Provider/Openai_comp/toolbaz.py` |
| 25 | **TwoAI** | `llm4free/Provider/TwoAI.py" | `llm4free/Provider/Openai_comp/TwoAI.py` |
| 26 | **WiseCat** | `llm4free/Provider/WiseCat.py` | `llm4free/Provider/Openai_comp/wisecat.py` |
| 29 | **X0GPT** | `llm4free/Provider/x0gpt.py` | `llm4free/Provider/Openai_comp/x0gpt.py` |
| 30 | **Yep** | `llm4free/Provider/yep.py` | `llm4free/Provider/Openai_comp/yep.py` |

| 32 | **Sambanova** | `llm4free/Provider/Sambanova.py` | `llm4free/Provider/Openai_comp/sambanova.py` |
| 33 | **Meta** | `llm4free/Provider/meta.py` | `llm4free/Provider/Openai_comp/meta.py` |
| 34 | **TypliAI** | `llm4free/Provider/TypliAI.py` | `llm4free/Provider/Openai_comp/typliai.py` |
| 35 | **LLMChat** | `llm4free/Provider/llmchat.py` | `llm4free/Provider/Openai_comp/llmchat.py` |

| 37 | **OpenRouter** | `llm4free/Provider/OpenRouter.py` | `llm4free/Provider/Openai_comp/openrouter.py` |

**Total: 37 providers with dual implementations**

---

## Providers with Only Normal Version

These providers are only available in the standard implementation format.

| # | Provider Name | Path |
|---|---------------|------|
| 1 | **Apriel** | `llm4free/Provider/Apriel.py` |
| 2 | **Cohere** | `llm4free/Provider/Cohere.py` |
| 5 | **EssentialAI** | `llm4free/Provider/EssentialAI.py` |
| 6 | **Falcon** | `llm4free/Provider/Falcon.py` |
| 7 | **Gemini** | `llm4free/Provider/Gemini.py` |
| 8 | **GeminiAPI** | `llm4free/Provider/geminiapi.py` |
| 9 | **GithubChat** | `llm4free/Provider/GithubChat.py` |
| 10 | **Jadve** | `llm4free/Provider/Jadve.py` |
| 11 | **Julius** | `llm4free/Provider/julius.py` |

| 13 | **OpenAI** | `llm4free/Provider/Openai.py` |
| 16 | **QwenLM** | `llm4free/Provider/QwenLM.py` |
| 17 | **SearchChat** | `llm4free/Provider/searchchat.py` |
| 18 | **TurboSeek** | `llm4free/Provider/turboseek.py` |
| 19 | **Upstage** | `llm4free/Provider/Upstage.py` |
| 20 | **WrDoChat** | `llm4free/Provider/WrDoChat.py` |

**Total: 17 providers with only normal implementation**

---

## Providers with Only OpenAI-Compatible Version

These providers are only available in the OpenAI-compatible format and have no standard implementation.

| # | Provider Name | Path |
|---|---------------|------|
| 1 | **ChatGPT** | `llm4free/Provider/Openai_comp/chatgpt.py` |
| 2 | **E2B** | `llm4free/Provider/Openai_comp/e2b.py` |
| 3 | **FreeAssist** | `llm4free/Provider/Openai_comp/freeassist.py` |
| 4 | **WriteCream** | `llm4free/Provider/Openai_comp/writecream.py` |
| 5 | **Zenmux** | `llm4free/Provider/Openai_comp/zenmux.py` |

**Total: 5 providers with only OpenAI-compatible implementation**

---

## Statistics

### Provider Distribution

```
┌─────────────────────────────────────────┬───────┐
│ Category                                │ Count │
├─────────────────────────────────────────┼───────┤
│ Both Normal & OpenAI-Compatible         │  37   │
│ Only Normal Version                     │  21   │
│ Only OpenAI-Compatible Version          │   5   │
├─────────────────────────────────────────┼───────┤
│ TOTAL UNIQUE PROVIDERS                  │  63   │
└─────────────────────────────────────────┴───────┘
```

### Implementation Coverage

- **Total Normal Implementations**: 58 (37 hybrid + 21 normal-only)
- **Total OpenAI Implementations**: 42 (37 hybrid + 5 OpenAI-only)
- **Providers with Multiple Options**: 37 (59% of all providers)

---


### Text-to-Image Providers
Located in `llm4free/Provider/TTI/`:
- AI Arta
- Bing
- Claude Online
- GPT1 Image
- Imagen
- Infip
- Magic Studio
- MonoChat
- PicLumen
- PixelMuse
- Pollinations
- Together

### Text-to-Speech Providers
Located in `llm4free/Provider/TTS/`:
- DeepGram
- ElevenLabs
- Faster Qwen3-TTS
- KittenTTS
- LuxTTS
- Murf AI
- OpenAI FM
- Parler
- Stream Elements
- Qwen
- Sherpa
- PocketTTS
- XLNK TTS

### Speech-to-Text Providers
Located in `llm4free/Provider/STT/`:
- Cohere (Multilingual ASR)
- ElevenLabs

### Unfinished/Experimental Providers
Located in `llm4free/Provider/UNFINISHED/`:
- ChatHub
- ChutesAI
- GizAI
- Liner
- Marcus
- Qodo
- Samurai
- XenAI
- YouChat

---
## Usage Notes

### Choosing Between Normal and OpenAI-Compatible Versions

**Use Normal Version when:**
- You want provider-specific features and customizations
- You need direct access to native provider capabilities
- You're building custom integrations

**Use OpenAI-Compatible Version when:**
- You want to easily switch between providers without code changes
- You're migrating from OpenAI and want minimal code changes
- You need standardized API interface across multiple providers

### Normal Provider Implementation
Concrete guidance when creating a "normal" (non-OpenAI-compatible) provider under `llm4free/Provider/`:
- Subclass `Provider` from `llm4free.AIbase` and implement these methods: `ask(prompt, ...)`, `chat(prompt, ...)`, and `get_message(response)`.
- Keep provider class names and filenames consistent (CamelCase class name matching the filename) and add a static import in `llm4free/Provider/__init__.py` to expose the provider at the package root.
- Prefer `requests.Session` for HTTP clients and avoid global mutable state so provider instances are safe to reuse.
- Add unit tests under `tests/providers/` that mock HTTP and validate normal and error behavior (including streaming if supported).
- Document the provider in `Provider.md` and a short usage snippet in `docs/` when appropriate.

### Use uv for All Commands
We use `uv` to manage the Python environment and run tools. Never run bare `python` or `pip` directly — always run commands with `uv` to avoid environment drift and to use the project's lockfile. Examples:
- `uv add <package>` / `uv remove <package>` — manage dependencies
- `uv sync` — install dependencies declared in `pyproject.toml` and `uv.lock`
- `uv run <command>` — run a script or tool inside the uv environment (e.g., `uv run pytest`, `uv run llm4free`)
- `uv run --extra api llm4free-server` — run the API server with extra dependencies

### Example Usage

```python
# Normal Provider
from llm4free.Provider import Groq
provider = Groq()
response = provider.chat("Hello, how are you?")

# OpenAI-Compatible Provider
from llm4free.Provider.Openai_comp import groq
client = groq.GroqProvider()
response = client.chat.completions.create(
    model="mixtral-8x7b",
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)
```

---

## Contributing

When adding new providers:
1. Implement the normal version in `llm4free/Provider/`
2. If applicable, create an OpenAI-compatible version in `llm4free/Provider/Openai_comp/`
3. Update this documentation
4. Add tests for both implementations

---

## License

This documentation is part of the LLM4Free project. See LICENSE.md for details.

---

**Last Updated**: 2025
**Version**: 1.0
**Maintained by**: LLM4Free Development Team