# Webscout - Unified AI & Search Framework

> **Enterprise-grade Python toolkit for AI chat, web search, image generation, and beyond**

Welcome to Webscout's comprehensive documentation! Whether you're looking to integrate AI into your application, deploy a search service, or build custom providers, you're in the right place.

---

## 🚀 Quick Start

### Installation
```bash
# Using pip (recommended for beginners)
pip install webscout

# Using uv (recommended for developers)
uv pip install webscout

# Using Docker
docker pull oevortex/webscout:latest
```

### Your First Chat (30 seconds)
```python
from webscout import Meta

ai = Meta()
response = ai.chat("What is Python?")
print(response)
```

**[→ Full Getting Started Guide](getting-started.md)**

---

## 📚 Documentation Hub

### 🆕 **Start Here**
- **[Getting Started](getting-started.md)** - Installation, first examples, IDE setup
- **[Documentation Index](DOCUMENTATION_INDEX.md)** - Complete navigation guide with learning paths
- **[Examples](examples/README.md)** - 200+ copy-paste code examples

### 🎯 **By Your Role**

| I want to... | Start here |
|---|---|
| **Try it out (5 min)** | [Quick Start](#quick-start) |
| **Build an app (1 hour)** | [Getting Started](getting-started.md) → [API Reference](api-reference.md) → [Examples](examples/README.md) |
| **Understand the design** | [Architecture](architecture.md) |
| **Deploy to production** | [Deployment Guide](deployment.md) |
| **Create a provider** | [Provider Development](provider-development.md) |
| **Contribute code** | [Contributing Guide](contributing.md) |
| **Troubleshoot issues** | [Troubleshooting](troubleshooting.md) |

### 📖 **Core Documentation**
- [**API Reference**](api-reference.md) - Complete API documentation with 25+ code examples
- [**Client API**](client.md) - Python client for unified AI provider access
- [**Client Quick Reference**](CLIENT_QUICK_REFERENCE.md) - Quick reference with copy-paste examples
- [**Architecture**](architecture.md) - System design and component overview
- [**Models Guide**](models.md) - Available AI, TTS, and TTI models

### 💻 **Development**
- [**Provider Development**](provider-development.md) - Create custom AI providers
- [**Contributing Guide**](contributing.md) - Contribution process and standards
- [**CLI Reference**](cli.md) - Command-line interface reference
- [**Decorators**](decorators.md) - Utility decorators for error handling and optimization

### 🚀 **Advanced Topics**
- [**Deployment**](deployment.md) - Docker, Kubernetes, production setup
- [**OpenAI API Server**](openai-api-server.md) - Deploy OpenAI-compatible REST API
- [**Docker Guide**](DOCKER.md) - Containerization and Docker Compose
- [**Search Engines**](search.md) - Web search provider documentation
- [**Troubleshooting**](troubleshooting.md) - Common issues and solutions

### 🛠️ **Tools & Extensions**
- [**LitAgent**](litagent.md) - User Agent & IP rotation
- [**LitPrinter**](litprinter.md) - Advanced debugging output
- [**ZeroArt**](zeroart.md) - ASCII art generation
- [**GGUF Converter**](gguf.md) - Model format conversion
- [**Weather Utils**](weather.md) - Weather data retrieval
- [**Git API**](gitapi.md) - GitHub integration helpers
- [**SwiftCLI**](swiftcli.md) - CLI framework

---

## ✨ Key Features

```python
# 🤖 Multi-Provider AI Chat
from webscout import Meta, OpenAI, GROQ

# Free option - no API key needed
ai = Meta()
response = ai.chat("Hello!")

# Paid providers - faster & better
ai = OpenAI(api_key="sk-...")
ai = GROQ(api_key="...")

# Automatic failover across providers
from webscout.client import Client
client = Client()
response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Your prompt"}]
)  # Auto-retries on failure
print(response.choices[0].message.content)
```

```python
# 🔍 Web Search Integration
from webscout import DuckDuckGo

engine = DuckDuckGo()
results = engine.search("AI trends 2025")

# Or use with AI for powerful research
from webscout import Meta
ai = Meta()
research = ai.search("Latest AI developments")
```

```python
# 🖼️ Image Generation
from webscout import StableDiffusion

generator = StableDiffusion(api_key="...")
image = generator.generate_image("Beautiful sunset")
```

```python
# ⚡ Streaming Responses
from webscout import GROQ

ai = GROQ(api_key="...")
for chunk in ai.chat("Write a story", stream=True):
    print(chunk, end="", flush=True)
```

---

## 📊 Supported Providers

Webscout supports **90+ AI providers**, including:

| Category | Providers |
|----------|-----------|
| **Free** | Meta, Andi, Apriel, and 20+ others |
| **Popular Paid** | OpenAI, Google Gemini, Anthropic Claude, GROQ |
| **Open Source** | Hugging Face, Together AI, Mistral |
| **Specialized** | Cohere, Sambanova, Gradient, and many more |
| **Search** | DuckDuckGo, Bing, Yahoo, Yep |
| **Images** | Stable Diffusion, DALL-E, Midjourney |

[**→ Complete Provider List**](../Provider.md)

---

## 🎓 Learning Paths

### Path 1: Quick Prototyping (45 min)
```
Quick Start
    ↓
examples/basic-chat.md
    ↓
examples/search-queries.md
```
**Result:** Ready to build a prototype

### Path 2: Application Development (3 hours)
```
Getting Started
    ↓
API Reference
    ↓
All Examples
    ↓
Architecture (optional)
```
**Result:** Ready to build production apps

### Path 3: Provider Development (4 hours)
```
Architecture
    ↓
Provider Development
    ↓
Contributing Guide
    ↓
Check Examples
```
**Result:** Ready to contribute providers

### Path 4: Deployment (2-3 hours)
```
Deployment
    ↓
Docker Guide
    ↓
OpenAI API Server
    ↓
Troubleshooting
```
**Result:** Ready to deploy to production

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| 📦 PyPI Package | https://pypi.org/project/webscout |
| 📍 GitHub Repository | https://github.com/OEvortex/Webscout |
| 🐛 Issue Tracker | https://github.com/OEvortex/Webscout/issues |
| 💬 GitHub Discussions | https://github.com/OEvortex/Webscout/discussions |
| 📱 Telegram Community | https://t.me/OEvortexAI |
| 📹 YouTube Channel | https://youtube.com/@OEvortex |

---

## 📋 Popular Pages

1. **[Complete Documentation Index](DOCUMENTATION_INDEX.md)** - Navigate all docs and find your learning path
2. **[Getting Started](getting-started.md)** - Installation and first examples
3. **[API Reference](api-reference.md)** - Complete API documentation
4. **[Examples](examples/README.md)** - 200+ code examples
5. **[Deployment](deployment.md)** - Production deployment guide
6. **[Troubleshooting](troubleshooting.md)** - Common issues and fixes
7. **[Provider Development](provider-development.md)** - Create custom providers
8. **[Architecture](architecture.md)** - System design overview

---

## 🆘 Need Help?

### Documentation
- 🆕 **New to Webscout?** → [Getting Started](getting-started.md)
- 💻 **API Questions?** → [API Reference](api-reference.md)
- 🔧 **Setup Issues?** → [Troubleshooting](troubleshooting.md)
- 🏗️ **Architecture?** → [Architecture Guide](architecture.md)

### Community Support
- 🐛 **Found a bug?** → [GitHub Issues](https://github.com/OEvortex/Webscout/issues)
- 💬 **Have questions?** → [GitHub Discussions](https://github.com/OEvortex/Webscout/discussions)
- 👥 **Chat with community** → [Telegram Group](https://t.me/OEvortexAI)

---

## ✅ What Can You Do With Webscout?

✨ **Chat with AI**
- Multi-provider support with automatic failover
- Streaming responses for real-time output
- Conversation memory and context management
- Cost optimization across providers

🔍 **Web Search**
- DuckDuckGo, Bing, Yahoo, and more
- AI-powered result summarization
- Integration with chat for research tools
- Custom search result parsing

🖼️ **Image Generation**
- Text-to-image with Stable Diffusion
- Multiple quality levels and parameters
- Batch generation support

🎯 **CLI Tools**
- Built-in command-line interface
- Rich output formatting
- Script automation support
- Plugin system

📡 **API Server**
- OpenAI-compatible REST API
- Drop-in replacement for OpenAI SDK
- Docker deployment ready
- Multi-provider routing

🔧 **Custom Integration**
- Provider development framework
- Decorators and utilities
- Error handling and retry logic
- Performance optimization tools

---

## 🚀 Get Started Now!

### Installation (1 minute)
```bash
pip install webscout
```

### First Example (1 minute)
```python
from webscout import Meta
print(Meta().chat("Hello, world!"))
```

### Explore More (5-15 minutes)
- [→ Getting Started Guide](getting-started.md)
- [→ Run Examples](examples/README.md)
- [→ API Reference](api-reference.md)

---

## 📈 Project Statistics

```
✅ 90+ AI Providers Supported
✅ 200+ Code Examples
✅ 30+ Documentation Guides
✅ 100% Type Annotated
✅ Production Ready
✅ Active Development
```

---

## 📜 License

Webscout is released under the MIT License. See [LICENSE.md](../LICENSE.md) for details.

---

## 🎉 Ready?

**[→ Start with Getting Started](getting-started.md)** or **[→ View Complete Documentation Index](DOCUMENTATION_INDEX.md)**

**Happy coding! 🚀**

---

*Last updated: January 24, 2026*  
*[GitHub](https://github.com/OEvortex/Webscout) | [PyPI](https://pypi.org/project/webscout) | [Documentation](DOCUMENTATION_INDEX.md)*
