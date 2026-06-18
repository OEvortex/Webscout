<div align="center">
  <a href="https://github.com/OEvortex/Webscout">
    <picture>
    <!-- When GitHub is in Dark Mode, force a light background canvas directly behind your black SVG logo -->
      <source media="(prefers-color-scheme: dark)" srcset="https://github.com/OEvortex/Webscout/blob/main/logo.svg" style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; display: inline-block;">
      <!-- Default Light Mode rendering -->
      <img src="https://github.com/OEvortex/Webscout/blob/main/logo.svg" alt="WebScout Logo">
  </picture>
  </a>
  <a href="https://github.com/OEvortex/Webscout">
    <img src="https://img.shields.io/badge/WebScout-Ultimate%20Toolkit-blue?style=for-the-badge&logo=python&logoColor=white" alt="WebScout Logo">
  </a>

  <h1>LLM4Free</h1>

  <p><strong>Your All-in-One Python Toolkit for Web Search, AI Interaction, Digital Utilities, and More</strong></p>

  <p>
    Access diverse search engines, cutting-edge AI models, temporary communication tools, media utilities, developer helpers, and powerful CLI interfaces -- all through one unified library.
  </p>

  <!-- Badges -->
  <p>
    <a href="https://pypi.org/project/llm4free/"><img src="https://img.shields.io/pypi/v/llm4free.svg?style=flat-square&logo=pypi&label=PyPI" alt="PyPI Version"></a>
    <a href="https://pepy.tech/project/llm4free"><img src="https://static.pepy.tech/badge/llm4free/month?style=flat-square" alt="Monthly Downloads"></a>
    <a href="https://pepy.tech/project/llm4free"><img src="https://static.pepy.tech/badge/llm4free?style=flat-square" alt="Total Downloads"></a>
    <a href="#"><img src="https://img.shields.io/pypi/pyversions/llm4free?style=flat-square&logo=python" alt="Python Version"></a>
    <a href="https://deepwiki.com/OEvortex/LLM4Free"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
  </p>
</div>

<hr/>

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI](#command-line-interface)
- [AI Chat Providers](#ai-chat-providers)
- [Search Engines](#search-engines)
- [Text-to-Image](#text-to-image)
- [Text-to-Speech](#text-to-speech)
- [OpenAI-Compatible API Server](#openai-compatible-api-server)
- [Python Client](#python-client)
- [Tool Calling](#tool-calling)
- [Model Registry](#model-registry)
- [Developer Tools](#developer-tools)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

<hr/>

> [!IMPORTANT]
> LLM4Free uses a **single unified OpenAI-compatible interface** for all providers.
> Every provider implements `client.chat.completions.create(...)` — identical to the OpenAI Python SDK.

> [!NOTE]
> LLM4Free supports 40+ AI providers including: HeckAI, ChatGPT, Groq, DeepInfra, Nvidia, Sambanova, OpenRouter, HuggingFace, OllamaSwarm, and many more. See the full [Provider Matrix](Provider.md).

<div align="center">
  <p>
    <a href="https://t.me/OEvortexAI"><img alt="Telegram Group" src="https://img.shields.io/badge/Telegram%20Group-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
    <a href="https://youtube.com/@OEvortex"><img alt="YouTube" src="https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white"></a>
    <a href="https://buymeacoffee.com/oevortex"><img alt="Buy Me A Coffee" src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>
  </p>
</div>

<hr/>

## Features

### Search & AI

- **Multi-Engine Search** -- DuckDuckGo, Bing, Brave, Yahoo, Yep, Yandex, Mojeek, Wikipedia. ([Search Docs](docs/search.md))
- **40+ AI Providers** -- All OpenAI-compatible for easy switching. ([Architecture](docs/architecture.md))
- **AI-Powered Search** -- Perplexity, IAsk, Monica, AyeSoul, WebPilotAI. ([Provider Matrix](Provider.md))
- **OpenAI-Compatible API Server** -- Serve any LLM4Free provider via OpenAI endpoints. ([Server Docs](docs/openai-api-server.md))
- **Unified Python Client** -- Auto-failover chat and image generation. ([Client Docs](docs/client.md))

### Media & Content

- **Text-to-Image** -- PollinationsAI, Together, Miragic, MagicStudio. ([TTI Docs](docs/getting-started.md#image-generation))
- **Text-to-Speech** -- ElevenLabs, Deepgram, OpenAI FM, Parler, Qwen, MurfAI, and more. ([Model Registry](docs/models.md))
- **Speech-to-Text** -- ElevenLabs STT. ([Provider Matrix](Provider.md))
- **YouTube Toolkit** -- Video downloads, transcription, API access. ([Docs](docs/gitapi.md))
- **Weather Tools** -- Detailed weather info with ASCII display. ([Weather Docs](docs/weather.md))

### Developer Tools

- **SwiftCLI** -- Elegant CLI framework. ([SwiftCLI Docs](docs/swiftcli.md))
- **Scout** -- HTML parser and web crawler. ([Scout Docs](docs/scout.md))
- **LitPrinter** -- Styled console output. ([LitPrinter Docs](docs/litprinter.md))
- **LitAgent** -- User-agent rotation and IP toolkit. ([LitAgent Docs](docs/litagent.md))
- **GitAPI** -- GitHub data extraction without auth. ([GitAPI Docs](docs/gitapi.md))
- **GGUF Conversion** -- Quantize HuggingFace models to GGUF. ([GGUF Docs](docs/gguf.md))
- **ZeroArt** -- Zero-dependency ASCII art generator. ([ZeroArt Docs](docs/zeroart.md))
- **Utility Decorators** -- `@timeIt` and `@retry` helpers. ([Decorator Docs](docs/decorators.md))
- **Stream Sanitization** -- SSE/HTTP stream processing. ([Sanitize Docs](docs/sanitize.md))

### Privacy & Utilities

- **Temp Mail** -- Disposable email via Emailnator, MailTM, TempMailIO.
- **Proxy Manager** -- Automatic proxy rotation. ([Architecture](docs/architecture.md))
- **Awesome Prompts** -- Curated system prompts for AI personas. ([Prompts Docs](docs/awesome-prompts.md))

<hr/>

## Installation

### pip (Standard)

```bash
pip install -U llm4free

# With API server support
pip install -U "llm4free[api]"

# With development tools
pip install -U "llm4free[dev]"
```

### uv (Recommended)

```bash
uv add llm4free

# Run without installing
uv run llm4free --help

# Install as global tool
uv tool install llm4free
```

### Docker

```bash
docker pull OEvortex/llm4free:latest
docker run -it OEvortex/llm4free:latest
```

See [docs/DOCKER.md](docs/DOCKER.md) for full Docker deployment options including compose profiles.

<hr/>

## Quick Start

### AI Chat (No API Key)

```python
from llm4free.Provider.Openai_comp.heckai import HeckAI

client = HeckAI()
response = client.chat.completions.create(
    model="google/gemini-2.5-flash-preview",
    messages=[{"role": "user", "content": "Explain quantum computing in simple terms"}],
)
print(response.choices[0].message.content)
```

### Web Search

```python
from llm4free import DuckDuckGoSearch

search = DuckDuckGoSearch()
results = search.text("best practices for API design", max_results=5)
for result in results:
    print(f"{result['title']}: {result['href']}")
```

### Image Generation

```python
from llm4free.Provider.TTI import PollinationsAI

gen = PollinationsAI()
path = gen.generate_image(prompt="A serene mountain landscape at sunset")
print(f"Saved to: {path}")
```

See [docs/getting-started.md](docs/getting-started.md) for the full quick-start guide.

<hr/>

## Command Line Interface

LLM4Free provides a rich CLI powered by [Rich](https://github.com/Textualize/rich) with multi-engine support.

```bash
llm4free --help                       # List all commands
llm4free version                      # Show version
llm4free text -k "python programming" # DuckDuckGo search (default)
llm4free images -k "mountains"        # Image search
llm4free news -k "AI breakthrough" -t w  # News from last week
llm4free weather -l "New York"        # Weather info
llm4free translate -k "Hola" --to en  # Translation
```

### Supported Engines

| Category     | Engines                                                        |
| ------------ | -------------------------------------------------------------- |
| `text`       | `ddg`, `bing`, `brave`, `yahoo`, `yep`, `mojeek`, `dogpile`, `wikipedia`, `yandex` |
| `images`     | `ddg`, `bing`, `brave`, `yahoo`, `yep`                        |
| `videos`     | `ddg`, `brave`, `yahoo`                                        |
| `news`       | `ddg`, `bing`, `brave`, `yahoo`                                |
| `suggestions`| `ddg`, `bing`, `brave`, `yahoo`, `yep`                         |
| `weather`    | `ddg`, `yahoo`                                                 |
| `answers`    | `ddg`                                                          |
| `translate`  | `ddg`                                                          |
| `maps`       | `ddg`                                                          |

```bash
# Use a specific engine
llm4free text -k "climate change" -e bing
llm4free text -k "quantum physics" -e wikipedia
```

Full CLI reference: [docs/cli.md](docs/cli.md)

<hr/>

## AI Chat Providers

All providers use the **OpenAI-compatible interface** (`client.chat.completions.create(...)`).

### Free Providers (No Auth Required)

```python
from llm4free.Provider.Openai_comp.heckai import HeckAI
from llm4free.Provider.Openai_comp.artingai import ArtingAI
from llm4free.Provider.Openai_comp.freeai import FreeAI

# HeckAI - multiple models
client = HeckAI()
response = client.chat.completions.create(
    model="google/gemini-2.5-flash-preview",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)

# ArtingAI
client = ArtingAI()
response = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Authenticated Providers

```python
from llm4free.Provider.Openai_comp.Auth.groq import Groq
from llm4free.Provider.Openai_comp.Auth.deepinfra import DeepInfra

groq = Groq(api_key="your-key")
response = groq.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Write a Python function to sort a list"}],
)
print(response.choices[0].message.content)
```

### Streaming

```python
from llm4free.Provider.Openai_comp.heckai import HeckAI

client = HeckAI()
stream = client.chat.completions.create(
    model="google/gemini-2.5-flash-preview",
    messages=[{"role": "user", "content": "Tell me a joke"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

See [Provider.md](Provider.md) for the complete provider matrix with file locations.

<hr/>

## Search Engines

```python
from llm4free import DuckDuckGoSearch, BingSearch, YepSearch, YahooSearch, BraveSearch

# DuckDuckGo
ddg = DuckDuckGoSearch()
results = ddg.text("python frameworks", max_results=5)

# Bing
bing = BingSearch()
results = bing.text("climate change solutions")

# Brave
brave = BraveSearch()
results = brave.text("machine learning tutorials")
```

Search docs: [docs/search.md](docs/search.md)

<hr/>

## Text-to-Image

```python
from llm4free.Provider.TTI import PollinationsAI, TogetherImage

# PollinationsAI
poll = PollinationsAI()
poll.generate_image(prompt="A cyberpunk city at night")

# Together AI
together = TogetherImage()
together.generate_image(prompt="A robot playing chess")
```

TTI docs: [docs/getting-started.md#image-generation](docs/getting-started.md#image-generation)

<hr/>

## Text-to-Speech

```python
from llm4free.Provider.TTS import ElevenlabsTTS, ParlerTTS

tts = ElevenlabsTTS()
tts.text_to_speech("Hello, world!", voice="alloy")
```

TTS model registry: [docs/models.md](docs/models.md)

<hr/>

## OpenAI-Compatible API Server

Run a local FastAPI server that serves any LLM4Free provider through standard OpenAI endpoints.

```bash
# Start the server
llm4free-server

# Custom config
llm4free-server --port 8080 --host 0.0.0.0 --debug
```

### Use with the OpenAI Python Client

```python
from openai import OpenAI

client = OpenAI(api_key="dummy", base_url="http://localhost:8000/v1")

response = client.chat.completions.create(
    model="ChatGPT/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Docker Deployment

```bash
docker-compose up llm4free-api
docker-compose -f docker-compose.yml -f docker-compose.no-auth.yml up llm4free-api
```

Full server docs: [docs/openai-api-server.md](docs/openai-api-server.md) | Docker: [docs/DOCKER.md](docs/DOCKER.md)

<hr/>

## Python Client

The unified `Client` class provides auto-failover across providers with smart model resolution.

```python
from llm4free.client import Client

client = Client(print_provider_info=True)

# Auto provider + model selection
resp = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Summarize LLM4Free."}]
)
print(resp.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="ChatGPT/gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a limerick about Python."}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)

# Image generation
img = client.images.generate(prompt="A neon owl", model="auto", size="1024x1024")
print(img.data[0].url)
```

Client docs: [docs/client.md](docs/client.md)

<hr/>

## Tool Calling

LLM4Free has a built-in tool calling system that works with any provider.

```python
from llm4free.Provider.Openai_comp.heckai import HeckAI
from llm4free.Provider.Openai_comp.base import Tool

def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny, 25C"

weather_tool = Tool(
    name="get_weather",
    description="Get current weather for a city.",
    parameters={"city": {"type": "string", "description": "City name."}},
    implementation=get_weather,
)

client = HeckAI(tools=[weather_tool])
response = client.chat.completions.create(
    model="google/gemini-2.5-flash-preview",
    messages=[{"role": "user", "content": "What is the weather in London?"}],
)
print(response.choices[0].message.content)
```

Tool calling docs: [docs/tool-calling.md](docs/tool-calling.md)

<hr/>

## Model Registry

Enumerate available models across all providers.

```python
from llm4free import model

# All LLM models
all_models = model.llm.list()
print(f"Total: {len(all_models)}")

# Models by provider
summary = model.llm.summary()
for provider, count in summary.items():
    print(f"  {provider}: {count}")

# TTS voices
voices = model.tts.list()
print(f"Total voices: {len(voices)}")
```

Model registry docs: [docs/models.md](docs/models.md)

<hr/>

## Developer Tools

| Tool | Description | Docs |
|------|-------------|------|
| [SwiftCLI](docs/swiftcli.md) | CLI framework with decorators | [docs/swiftcli.md](docs/swiftcli.md) |
| [Scout](docs/scout.md) | HTML parser & web crawler | [docs/scout.md](docs/scout.md) |
| [LitPrinter](docs/litprinter.md) | Styled debug printing | [docs/litprinter.md](docs/litprinter.md) |
| [LitAgent](docs/litagent.md) | User-agent rotation | [docs/litagent.md](docs/litagent.md) |
| [GitAPI](docs/gitapi.md) | GitHub data extraction | [docs/gitapi.md](docs/gitapi.md) |
| [GGUF](docs/gguf.md) | Model conversion & quantization | [docs/gguf.md](docs/gguf.md) |
| [ZeroArt](docs/zeroart.md) | ASCII art generator | [docs/zeroart.md](docs/zeroart.md) |
| [Weather](docs/weather.md) | Weather toolkit | [docs/weather.md](docs/weather.md) |
| [Decorators](docs/decorators.md) | `@timeIt` and `@retry` | [docs/decorators.md](docs/decorators.md) |
| [Sanitize](docs/sanitize.md) | Stream sanitization | [docs/sanitize.md](docs/sanitize.md) |
| [Prompts](docs/awesome-prompts.md) | System prompt manager | [docs/awesome-prompts.md](docs/awesome-prompts.md) |

<hr/>

## Documentation

| Resource | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Installation, first chat, web search, image generation |
| [Architecture](docs/architecture.md) | System design, layers, and data flows |
| [CLI Reference](docs/cli.md) | All CLI commands and options |
| [Python Client](docs/client.md) | Unified client with auto-failover |
| [API Server](docs/openai-api-server.md) | OpenAI-compatible FastAPI server |
| [Model Registry](docs/models.md) | Enumerate LLM, TTS, TTI models |
| [Tool Calling](docs/tool-calling.md) | Function calling with any provider |
| [Search Docs](docs/search.md) | Multi-engine search API |
| [Scout](docs/scout.md) | HTML parser and crawler |
| [Provider Development](docs/provider-development.md) | Create custom providers |
| [Deployment](docs/deployment.md) | Production deployment guide |
| [Docker](docs/DOCKER.md) | Docker setup and compose profiles |
| [Inferno](docs/inferno.md) | Local LLM server |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [Contributing](docs/contributing.md) | How to contribute |
| [Provider Matrix](Provider.md) | Complete provider listing |
| [Docs Hub](docs/README.md) | Full documentation index |

<hr/>

## Contributing

See [docs/contributing.md](docs/contributing.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make changes with descriptive commits
4. Submit a pull request

<hr/>

## License

Apache-2.0. See [LICENSE.md](LICENSE.md).

<hr/>

<div align="center">
  <p>Made with by the LLM4Free team</p>
</div>
