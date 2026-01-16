<div align="center">
  <h1>🔍 Webscout AI Search Providers</h1>
  <p><strong>Powerful AI-powered search capabilities with multiple provider support</strong></p>
</div>

> [!NOTE]
> AI Search Providers leverage advanced language models and search algorithms to deliver high-quality, context-aware responses with web search integration.

## ✨ Features

- **Multiple Search Providers**: Support for 6 specialized AI search services
- **Streaming Responses**: Real-time streaming of AI-generated responses
- **Raw Response Format**: Access to raw response data when needed
- **Automatic Text Handling**: Smart response formatting and cleaning
- **Robust Error Handling**: Comprehensive error management
- **Cross-Platform Compatibility**: Works seamlessly across different environments

## 📦 Supported Search Providers

| Provider | Description | Key Features |
|----------|-------------|-------------|
| **PERPLEXED** | Resilient AI search | High availability, clean formatting |
| **Perplexity** | Advanced AI search & chat | Multiple modes, model selection, source control |
| **IAsk** | Multi-mode research | Academic, Question, Fast modes, detail levels |
| **Monica** | Comprehensive AI search | Clean formatted responses, web integration |
| **BraveAI** | Privacy-focused AI search | Fast, accurate, web-integrated responses |
| **WebPilotAI** | Web-integrated analysis | Content extraction, source references |
| **Stellar** | Agentic AI search | Next.js powered, deep search capabilities (Quota limited) |

## 🚀 Installation

```bash
pip install -U webscout
```

## 💻 Quick Start Guide

### Basic Usage Pattern

All AI Search providers follow a consistent usage pattern:

```python
from webscout.Provider.AISEARCH import PERPLEXED

# Initialize the provider
ai = PERPLEXED()

# Basic search
response = ai.search("Your query here")
print(response)  # Automatically formats the response

# Streaming search
for chunk in ai.search("Your query here", stream=True):
    print(chunk, end="", flush=True)  # Print response as it arrives
```

### Provider Examples

<details>
<summary><strong>Perplexity Example</strong></summary>

```python
from webscout.Provider.AISEARCH import Perplexity

ai = Perplexity()

# Basic search (auto mode)
response = ai.search("What is the weather in London?")
print(response)

# Streaming search
for chunk in ai.search("Explain black holes", stream=True):
    print(chunk, end="", flush=True)
```
</details>

<details>
<summary><strong>IAsk Example</strong></summary>

```python
from webscout.Provider.AISEARCH import IAsk

# Initialize with academic mode
ai = IAsk(mode="academic")

response = ai.search("Recent developments in mRNA vaccines")
print(response)
```
</details>

## 🛡️ Error Handling

```python
from webscout import exceptions

try:
    response = ai.search("Your query")
except exceptions.APIConnectionError as e:
    print(f"API error: {e}")
except exceptions.FailedToGenerateResponseError as e:
    print(f"Generation error: {e}")
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.