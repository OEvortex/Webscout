# Webscout Provider Documentation

This document provides a comprehensive overview of all AI providers available in the Webscout library, categorized by their implementation types.


## Table of Contents
- [Overview](#overview)
- [Providers with Both Normal and OpenAI-Compatible Versions](#providers-with-both-normal-and-openai-compatible-versions)
- [Providers with Only Normal Version](#providers-with-only-normal-version)
- [Providers with Only OpenAI-Compatible Version](#providers-with-only-openai-compatible-version)
- [Statistics](#statistics)
- [Provider Categories](#provider-categories)

## Overview

Webscout supports multiple AI providers with different implementation approaches:
- **Normal Providers**: Standard implementation located in `webscout/Provider/`
- **OpenAI-Compatible Providers**: OpenAI API-compatible implementation located in `webscout/Provider/OPENAI/`
- **Hybrid Providers**: Available in both normal and OpenAI-compatible versions

---

## Providers with Both Normal and OpenAI-Compatible Versions

These providers have both standard and OpenAI-compatible implementations, giving users flexibility in how they interact with the API.

| # | Provider Name | Normal Path | OpenAI Path |
|---|---------------|-------------|-------------|
| 1 | **AI4Chat** | `webscout/Provider/ai4chat.py` | `webscout/Provider/OPENAI/ai4chat.py` |
| 2 | **AkashGPT** | `webscout/Provider/akashgpt.py` | `webscout/Provider/OPENAI/akashgpt.py` |
| 3 | **Algion** | `webscout/Provider/Algion.py` | `webscout/Provider/OPENAI/algion.py` |
| 4 | **Cerebras** | `webscout/Provider/cerebras.py` | `webscout/Provider/OPENAI/cerebras.py` |
| 5 | **DeepAI** | `webscout/Provider/DeepAI.py` | `webscout/Provider/OPENAI/DeepAI.py` |
| 6 | **DeepInfra** | `webscout/Provider/Deepinfra.py` | `webscout/Provider/OPENAI/deepinfra.py` |
| 7 | **Elmo** | `webscout/Provider/elmo.py` | `webscout/Provider/OPENAI/elmo.py` |
| 8 | **ExaAI** | `webscout/Provider/ExaAI.py` | `webscout/Provider/OPENAI/exaai.py` |
| 9 | **Ayle** | `webscout/Provider/Ayle.py` | `webscout/Provider/OPENAI/ayle.py` |
| 10 | **Groq** | `webscout/Provider/Groq.py` | `webscout/Provider/OPENAI/groq.py` |
| 11 | **HeckAI** | `webscout/Provider/HeckAI.py` | `webscout/Provider/OPENAI/heckai.py` |
| 12 | **HuggingFace** | `webscout/Provider/HuggingFace.py` | `webscout/Provider/OPENAI/huggingface.py` |
| 13 | **IBM** | `webscout/Provider/IBM.py` | `webscout/Provider/OPENAI/ibm.py` |
| 14 | **K2Think** | `webscout/Provider/K2Think.py` | `webscout/Provider/OPENAI/K2Think.py` |
| 15 | **LLMChatCo** | `webscout/Provider/llmchatco.py` | `webscout/Provider/OPENAI/llmchatco.py` |
| 17 | **Netwrck** | `webscout/Provider/Netwrck.py` | `webscout/Provider/OPENAI/netwrck.py` |
| 18 | **Nvidia** | `webscout/Provider/Nvidia.py` | `webscout/Provider/OPENAI/nvidia.py` |
| 19 | **OIVSCode** | `webscout/Provider/oivscode.py` | `webscout/Provider/OPENAI/oivscode.py` |
| 20 | **PI** | `webscout/Provider/PI.py` | `webscout/Provider/OPENAI/PI.py` |
| 21 | **Sonus** | `webscout/Provider/sonus.py` | `webscout/Provider/OPENAI/sonus.py` |
| 22 | **TextPollinationsAI** | `webscout/Provider/TextPollinationsAI.py` | `webscout/Provider/OPENAI/textpollinations.py` |
| 23 | **TogetherAI** | `webscout/Provider/TogetherAI.py` | `webscout/Provider/OPENAI/TogetherAI.py` |
| 24 | **Toolbaz** | `webscout/Provider/toolbaz.py` | `webscout/Provider/OPENAI/toolbaz.py` |
| 25 | **TwoAI** | `webscout/Provider/TwoAI.py" | `webscout/Provider/OPENAI/TwoAI.py` |
| 26 | **Typefully** | `webscout/Provider/typefully.py` | `webscout/Provider/OPENAI/typefully.py` |
| 27 | **WiseCat** | `webscout/Provider/WiseCat.py` | `webscout/Provider/OPENAI/wisecat.py` |
| 29 | **X0GPT** | `webscout/Provider/x0gpt.py` | `webscout/Provider/OPENAI/x0gpt.py` |
| 30 | **Yep** | `webscout/Provider/yep.py` | `webscout/Provider/OPENAI/yep.py` |
| 31 | **Gradient** | `webscout/Provider/Gradient.py` | `webscout/Provider/OPENAI/gradient.py` |
| 32 | **Sambanova** | `webscout/Provider/Sambanova.py` | `webscout/Provider/OPENAI/sambanova.py` |
| 33 | **Meta** | `webscout/Provider/meta.py` | `webscout/Provider/OPENAI/meta.py` |
| 34 | **TypliAI** | `webscout/Provider/TypliAI.py` | `webscout/Provider/OPENAI/typliai.py` |
| 35 | **LLMChat** | `webscout/Provider/llmchat.py` | `webscout/Provider/OPENAI/llmchat.py` |
| 36 | **HadadXYZ** | `webscout/Provider/HadadXYZ.py` | `webscout/Provider/OPENAI/hadadxyz.py` |

**Total: 36 providers with dual implementations**

---

## Providers with Only Normal Version

These providers are only available in the standard implementation format.

| # | Provider Name | Path |
|---|---------------|------|
| 1 | **Andi** | `webscout/Provider/Andi.py` |
| 2 | **Apriel** | `webscout/Provider/Apriel.py` |
| 3 | **ClaudeOnline** | `webscout/Provider/ClaudeOnline.py` |
| 4 | **CleeAI** | `webscout/Provider/cleeai.py` |
| 5 | **Cohere** | `webscout/Provider/Cohere.py` |
| 6 | **EssentialAI** | `webscout/Provider/EssentialAI.py` |
| 7 | **Gemini** | `webscout/Provider/Gemini.py` |
| 8 | **GeminiAPI** | `webscout/Provider/geminiapi.py` |
| 9 | **GithubChat** | `webscout/Provider/GithubChat.py` |
| 10 | **Jadve** | `webscout/Provider/Jadve.py` |
| 11 | **Julius** | `webscout/Provider/julius.py` |
| 12 | **KoboldAI** | `webscout/Provider/Koboldai.py` |
| 13 | **LearnFastAI** | `webscout/Provider/learnfastai.py` |
| 14 | **Llama3Mitril** | `webscout/Provider/llama3mitril.py` |
| 15 | **OpenAI** | `webscout/Provider/Openai.py` |
| 16 | **QwenLM** | `webscout/Provider/QwenLM.py` |
| 17 | **SearchChat** | `webscout/Provider/searchchat.py` |
| 18 | **TurboSeek** | `webscout/Provider/turboseek.py` |
| 19 | **WrDoChat** | `webscout/Provider/WrDoChat.py` |

**Total: 19 providers with only normal implementation**

---

## Providers with Only OpenAI-Compatible Version

These providers are only available in the OpenAI-compatible format and have no standard implementation.

| # | Provider Name | Path |
|---|---------------|------|
| 1 | **ChatGPT** | `webscout/Provider/OPENAI/chatgpt.py` |
| 2 | **E2B** | `webscout/Provider/OPENAI/e2b.py` |
| 3 | **FreeAssist** | `webscout/Provider/OPENAI/freeassist.py` |
| 4 | **WriteCream** | `webscout/Provider/OPENAI/writecream.py` |
| 5 | **Zenmux** | `webscout/Provider/OPENAI/zenmux.py" |

**Total: 5 providers with only OpenAI-compatible implementation**

---

## Statistics

### Provider Distribution

```
┌─────────────────────────────────────────┬───────┐
│ Category                                │ Count │
├─────────────────────────────────────────┼───────┤
│ Both Normal & OpenAI-Compatible         │  36   │
│ Only Normal Version                     │  20   │
│ Only OpenAI-Compatible Version          │   5   │
├─────────────────────────────────────────┼───────┤
│ TOTAL UNIQUE PROVIDERS                  │  61   │
└─────────────────────────────────────────┴───────┘
```

### Implementation Coverage

- **Total Normal Implementations**: 56 (36 hybrid + 20 normal-only)
- **Total OpenAI Implementations**: 41 (36 hybrid + 5 OpenAI-only)
- **Providers with Multiple Options**: 36 (59% of all providers)

---

## Provider Categories

### AI Search Providers
Located in `webscout/Provider/AISEARCH/`:
- GenSpark Search
- iAsk Search
- Monica Search
- Perplexed Search
- Perplexity
- Stellar Search
- WebPilot AI Search

### Text-to-Image Providers
Located in `webscout/Provider/TTI/`:
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
Located in `webscout/Provider/TTS/`:
- DeepGram
- ElevenLabs
- FreeTTS
- Gesserit
- Murf AI
- OpenAI FM
- Parler
- SpeechMA
- Stream Elements

### Speech-to-Text Providers
Located in `webscout/Provider/STT/`:
- ElevenLabs

### Unfinished/Experimental Providers
Located in `webscout/Provider/UNFINISHED/`:
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
Concrete guidance when creating a "normal" (non-OpenAI-compatible) provider under `webscout/Provider/`:
- Subclass `Provider` from `webscout.AIbase` and implement these methods: `ask(prompt, ...)`, `chat(prompt, ...)`, and `get_message(response)`.
- Keep provider class names and filenames consistent (CamelCase class name matching the filename) and add a static import in `webscout/Provider/__init__.py` to expose the provider at the package root.
- Prefer `requests.Session` for HTTP clients and avoid global mutable state so provider instances are safe to reuse.
- Add unit tests under `tests/providers/` that mock HTTP and validate normal and error behavior (including streaming if supported).
- Document the provider in `Provider.md` and a short usage snippet in `docs/` when appropriate.

### Use uv for All Commands
We use `uv` to manage the Python environment and run tools. Never run bare `python` or `pip` directly — always run commands with `uv` to avoid environment drift and to use the project's lockfile. Examples:
- `uv add <package>` / `uv remove <package>` — manage dependencies
- `uv sync` — install dependencies declared in `pyproject.toml` and `uv.lock`
- `uv run <command>` — run a script or tool inside the uv environment (e.g., `uv run pytest`, `uv run webscout`)
- `uv run --extra api webscout-server` — run the API server with extra dependencies

### Example Usage

```python
# Normal Provider
from webscout.Provider import Groq
provider = Groq()
response = provider.chat("Hello, how are you?")

# OpenAI-Compatible Provider
from webscout.Provider.OPENAI import groq
client = groq.GroqProvider()
response = client.chat.completions.create(
    model="mixtral-8x7b",
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)
```

---

## Contributing

When adding new providers:
1. Implement the normal version in `webscout/Provider/`
2. If applicable, create an OpenAI-compatible version in `webscout/Provider/OPENAI/`
3. Update this documentation
4. Add tests for both implementations

---

## License

This documentation is part of the Webscout project. See LICENSE.md for details.

---

**Last Updated**: 2025
**Version**: 1.0
**Maintained by**: Webscout Development Team