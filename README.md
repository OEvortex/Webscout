<div align="center">
  <a href="https://github.com/OEvortex/Webscout">
    <img src="https://img.shields.io/badge/WebScout-Ultimate%20Toolkit-blue?style=for-the-badge&logo=python&logoColor=white" alt="WebScout Logo">
  </a>

  <h1>Webscout</h1>

  <p><strong>Your All-in-One Python Toolkit for Web Search, AI Interaction, Digital Utilities, and More</strong></p>

  <p>
    Access diverse search engines, cutting-edge AI models, temporary communication tools, media utilities, developer helpers, and powerful CLI interfaces -- all through one unified library.
  </p>

  <!-- Badges -->
  <p>
    <a href="https://pypi.org/project/webscout/"><img src="https://img.shields.io/pypi/v/webscout.svg?style=flat-square&logo=pypi&label=PyPI" alt="PyPI Version"></a>
    <a href="https://pepy.tech/project/webscout"><img src="https://static.pepy.tech/badge/webscout/month?style=flat-square" alt="Monthly Downloads"></a>
    <a href="https://pepy.tech/project/webscout"><img src="https://static.pepy.tech/badge/webscout?style=flat-square" alt="Total Downloads"></a>
    <a href="#"><img src="https://img.shields.io/pypi/pyversions/webscout?style=flat-square&logo=python" alt="Python Version"></a>
    <a href="https://deepwiki.com/OEvortex/Webscout"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
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
> Webscout supports three types of compatibility:
>
> - **Native:** Webscout's own native API for maximum flexibility
> - **OpenAI-Compatible:** Use providers with OpenAI-compatible interfaces
> - **Local LLMs:** Run local models with OpenAI-compatible servers via [Inferno](docs/inferno.md)

> [!NOTE]
> Webscout supports 90+ AI providers including: OpenAI, GROQ, Gemini, Meta, DeepInfra, Cohere, Cerebras, HuggingFace, OpenRouter, Nvidia, Sambanova, PerplexityLabs, and many more. See the full [Provider Matrix](Provider.md).

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
- **90+ AI Providers** -- Native, OpenAI-compatible, and local LLM interfaces. ([Architecture](docs/architecture.md))
- **AI-Powered Search** -- Perplexity, IAsk, Monica, AyeSoul, WebPilotAI. ([Provider Matrix](Provider.md))
- **OpenAI-Compatible API Server** -- Serve any Webscout provider via OpenAI endpoints. ([Server Docs](docs/openai-api-server.md))
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
pip install -U webscout

# With API server support
pip install -U "webscout[api]"

# With development tools
pip install -U "webscout[dev]"
```

### uv (Recommended)

```bash
uv add webscout

# Run without installing
uv run webscout --help

# Install as global tool
uv tool install webscout
```

### Docker

```bash
docker pull OEvortex/webscout:latest
docker run -it OEvortex/webscout:latest
```

See [docs/DOCKER.md](docs/DOCKER.md) for full Docker deployment options including compose profiles.

<hr/>

## Quick Start

### AI Chat (No API Key)

```python
from webscout import Meta

ai = Meta()
response = ai.chat("Explain quantum computing in simple terms")
print(response)
```

### Web Search

```python
from webscout import DuckDuckGoSearch

search = DuckDuckGoSearch()
results = search.text("best practices for API design", max_results=5)
for result in results:
    print(f"{result['title']}: {result['href']}")
```

### Image Generation

```python
from webscout.Provider.TTI import PollinationsAI

gen = PollinationsAI()
path = gen.generate_image(prompt="A serene mountain landscape at sunset")
print(f"Saved to: {path}")
```

See [docs/getting-started.md](docs/getting-started.md) for the full quick-start guide.

<hr/>

## Command Line Interface

Webscout provides a rich CLI powered by [Rich](https://github.com/Textualize/rich) with multi-engine support.

```bash
webscout --help                       # List all commands
webscout version                      # Show version
webscout text -k "python programming" # DuckDuckGo search (default)
webscout images -k "mountains"        # Image search
webscout news -k "AI breakthrough" -t w  # News from last week
webscout weather -l "New York"        # Weather info
webscout translate -k "Hola" --to en  # Translation
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
webscout text -k "climate change" -e bing
webscout text -k "quantum physics" -e wikipedia
```

Full CLI reference: [docs/cli.md](docs/cli.md)

<hr/>

## AI Chat Providers

### Native Providers (No Auth Required)

```python
from webscout import Meta, Toolbaz, LLMChat, SonusAI, Netwrck, PiAI

ai = Meta()
print(ai.chat("What is the capital of France?"))
```

### Authenticated Providers

```python
from webscout import OpenAI, GROQ, GEMINI, Cohere, DeepInfra

groq = GROQ(api_key="your-key")
response = groq.chat("Write a Python function to sort a list")
```

### OpenAI-Compatible Providers

```python
from webscout.Provider.OPENAI import ChatGPT, Groq, DeepInfra

chatgpt = ChatGPT()  # No auth required
response = chatgpt.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

See [Provider.md](Provider.md) for the complete provider matrix with file locations.

<hr/>

## Search Engines

```python
from webscout import DuckDuckGoSearch, BingSearch, YepSearch, YahooSearch, BraveSearch

# DuckDuckGo
ddg = DuckDuckGoSearch()
results = ddg.text("python frameworks", max_results=5)

# Bing
bing = BingSearch()
results = bing.text("climate change solutions")

# Brave
brave = BraveSearch()
results = bravesearch.text("machine learning tutorials")
```

Search docs: [docs/search.md](docs/search.md)

<hr/>

## Text-to-Image

```python
from webscout.Provider.TTI import PollinationsAI, TogetherImage

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
from webscout.Provider.TTS import ElevenlabsTTS, FreeTTS, ParlerTTS

tts = FreeTTS()
tts.text_to_speech("Hello, world!", voice="en-US")
```

TTS model registry: [docs/models.md](docs/models.md)

<hr/>

## OpenAI-Compatible API Server

Run a local FastAPI server that serves any Webscout provider through standard OpenAI endpoints.

```bash
# Start the server
webscout-server

# Custom config
webscout-server --port 8080 --host 0.0.0.0 --debug
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
docker-compose up webscout-api
docker-compose -f docker-compose.yml -f docker-compose.no-auth.yml up webscout-api
```

Full server docs: [docs/openai-api-server.md](docs/openai-api-server.md) | Docker: [docs/DOCKER.md](docs/DOCKER.md)

<hr/>

## Python Client

The unified `Client` class provides auto-failover across providers with smart model resolution.

```python
from webscout.client import Client

client = Client(print_provider_info=True)

# Auto provider + model selection
resp = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Summarize Webscout."}]
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

Webscout has a built-in tool calling system that works with any provider.

```python
from webscout.Provider.Apriel import Apriel
from webscout.AIbase import Tool

def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny, 25C"

weather_tool = Tool(
    name="get_weather",
    description="Get current weather for a city.",
    parameters={"city": {"type": "string", "description": "City name."}},
    implementation=get_weather,
)

ai = Apriel(tools=[weather_tool])
print(ai.chat("What is the weather in London?"))
```

Tool calling docs: [docs/tool-calling.md](docs/tool-calling.md)

<hr/>

## Model Registry

Enumerate available models across all providers.

```python
from webscout import model

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
  <p>Made with by the Webscout team</p>
</div>
