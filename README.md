<div align="center">
  <a href="https://github.com/OEvortex/Webscout">
    <img src="https://img.shields.io/badge/WebScout-Ultimate%20Toolkit-blue?style=for-the-badge&logo=python&logoColor=white" alt="WebScout Logo">
  </a>

  <h1>Webscout</h1>

  <p><strong>Your All-in-One Python Toolkit for Web Search, AI Interaction, Digital Utilities, and More</strong></p>

  <p>
    Access diverse search engines, cutting-edge AI models, temporary communication tools, media utilities, developer helpers, and powerful CLI interfaces – all through one unified library.
  </p>

  <!-- Badges -->
  <p>
    <a href="https://pypi.org/project/webscout/"><img src="https://img.shields.io/pypi/v/webscout.svg?style=flat-square&logo=pypi&label=PyPI" alt="PyPI Version"></a>
    <a href="https://pepy.tech/project/webscout"><img src="https://static.pepy.tech/badge/webscout/month?style=flat-square" alt="Monthly Downloads"></a>
    <a href="https://pepy.tech/project/webscout"><img src="https://static.pepy.tech/badge/webscout?style=flat-square" alt="Total Downloads"></a>
    <a href="#"><img src="https://img.shields.io/pypi/pyversions/webscout?style=flat-square&logo=python" alt="Python Version"></a>
  </p>
</div>

<hr/>

## 📋 Table of Contents

- [🌟 Key Features](#-features)
- [⚙️ Installation](#️-installation)
- [🖥️ Command Line Interface](#️-command-line-interface)
- [🔍 Search Engines](#-search-engines)
- [🦆 DuckDuckGo Search](#-duckduckgo-search-with-webs-and-asyncwebs)
- [💻 WEBS API Reference](#-webs-api-reference)
- [🤖 AI Models and Voices](#-ai-models-and-voices)
- [💬 AI Chat Providers](#-ai-chat-providers)
- [👨‍💻 Advanced AI Interfaces](#-advanced-ai-interfaces)
- [🤝 Contributing](#-contributing)
- [🙏 Acknowledgments](#-acknowledgments)

<hr/>

> [!IMPORTANT]
> **Webscout supports three types of compatibility:**
> - **Native Compatibility:** Webscout's own native API for maximum flexibility
> - **OpenAI Compatibility:** Use providers with OpenAI-compatible interfaces
> - **Local LLM Compatibility:** Run local models with [Inferno](webscout/Local/README.md), an OpenAI-compatible server
>
> Choose the approach that best fits your needs! For OpenAI compatibility, check the [OpenAI Providers README](webscout/Provider/OPENAI/README.md).

> [!NOTE]
> Webscout supports over 90 AI providers including: LLAMA, C4ai, Venice, Copilot, HuggingFaceChat, PerplexityLabs, DeepSeek, WiseCat, GROQ, OPENAI, GEMINI, DeepInfra, Meta, YEPCHAT, TypeGPT, ChatGPTClone, ExaAI, Claude, Anthropic, Cloudflare, AI21, Cerebras, and many more. All providers follow similar usage patterns with consistent interfaces.

<div align="center">
  <!-- Social/Support Links -->
  <p>
    <a href="https://t.me/PyscoutAI"><img alt="Telegram Group" src="https://img.shields.io/badge/Telegram%20Group-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
    <a href="https://t.me/ANONYMOUS_56788"><img alt="Developer Telegram" src="https://img.shields.io/badge/Developer%20Contact-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
    <a href="https://youtube.com/@OEvortex"><img alt="YouTube" src="https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white"></a>
    <a href="https://www.linkedin.com/in/oe-vortex-29a407265/"><img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"></a>
    <a href="https://www.instagram.com/oevortex/"><img alt="Instagram" src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white"></a>
    <a href="https://buymeacoffee.com/oevortex"><img alt="Buy Me A Coffee" src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>
  </p>
</div>

<hr/>

## 🚀 Features

<details open>
<summary><b>Search & AI</b></summary>
<p>

* **Comprehensive Search:** Leverage Google, DuckDuckGo, and Yep for diverse search results
* **AI Powerhouse:** Access and interact with various AI models through three compatibility options:
  * **Native API:** Use Webscout's native interfaces for providers like OpenAI, Cohere, Gemini, and many more
  * **[OpenAI-Compatible Providers](webscout/Provider/OPENAI/README.md):** Seamlessly integrate with various AI providers using standardized OpenAI-compatible interfaces
  * **[Local LLMs with Inferno](webscout/Local/README.md):** Run local models with an OpenAI-compatible server
* **[AI Search](webscout/Provider/AISEARCH/README.md):** AI-powered search engines with advanced capabilities
</p>
</details>

<details open>
<summary><b>Media & Content Tools</b></summary>
<p>

* **[YouTube Toolkit](webscout/Extra/YTToolkit/README.md):** Advanced YouTube video and transcript management with multi-language support
* **[Text-to-Speech (TTS)](webscout/Provider/TTS/README.md):** Convert text into natural-sounding speech using multiple AI-powered providers
* **[Text-to-Image](webscout/Provider/TTI/README.md):** Generate high-quality images using a wide range of AI art providers
* **[Weather Tools](webscout/Extra/weather.md):** Retrieve detailed weather information for any location
</p>
</details>

<details open>
<summary><b>Developer Tools</b></summary>
<p>

* **[GitAPI](webscout/Extra/GitToolkit/gitapi):** Powerful GitHub data extraction toolkit without authentication requirements for public data
* **[SwiftCLI](webscout/swiftcli/Readme.md):** A powerful and elegant CLI framework for beautiful command-line interfaces
* **[LitPrinter](webscout/litprinter/Readme.md):** Styled console output with rich formatting and colors
* **[LitLogger](webscout/litlogger/Readme.md):** Simplified logging with customizable formats and color schemes
* **[LitAgent](webscout/litagent/Readme.md):** Modern user agent generator that keeps your requests undetectable
* **[Scout](webscout/scout/README.md):** Advanced web parsing and crawling library with intelligent HTML/XML parsing
* **[Inferno](webscout/Local/README.md):** Run local LLMs with an OpenAI-compatible API and interactive CLI
* **GGUF Conversion:** Convert and quantize Hugging Face models to GGUF format
</p>
</details>

<details open>
<summary><b>Privacy & Utilities</b></summary>
<p>

* **[Tempmail](webscout/Extra/tempmail/README.md) & Temp Number:** Generate temporary email addresses and phone numbers
* **[Awesome Prompts](webscout/Extra/Act.md):** Curated collection of system prompts for specialized AI personas
</p>
</details>

<hr/>

## ⚙️ Installation

Install Webscout using pip:

```bash
pip install -U webscout
```
</div>

<hr/>

## 🖥️ Command Line Interface

Webscout provides a powerful command-line interface for quick access to its features:

```bash
python -m webscout --help
```

<details open>
<summary><b>Web Search Commands</b></summary>
<p>

| Command | Description |
|---------|-------------|
| `python -m webscout answers -k "query"` | Perform an answers search |
| `python -m webscout chat` | Start an interactive AI chat session |
| `python -m webscout images -k "query"` | Search for images |
| `python -m webscout maps -k "query"` | Perform a maps search |
| `python -m webscout news -k "query"` | Search for news articles |
| `python -m webscout suggestions -k "query"` | Get search suggestions |
| `python -m webscout text -k "query"` | Perform a text search |
| `python -m webscout translate -k "text"` | Translate text |
| `python -m webscout version` | Display the current version |
| `python -m webscout videos -k "query"` | Search for videos |
| `python -m webscout weather -l "location"` | Get weather information |
| `python -m webscout google_text -k "query"` | Perform a text search using Google |
| `python -m webscout google_news -k "query"` | Search for news using Google |
| `python -m webscout google_suggestions -q "query"` | Get search suggestions from Google |
| `python -m webscout yep_text -k "query"` | Perform a text search using Yep |
| `python -m webscout yep_images -k "query"` | Search for images using Yep |
| `python -m webscout yep_suggestions -q "query"` | Get search suggestions from Yep |
</p>
</details>

<details open>
<summary><b>Inferno LLM Commands</b></summary>
<p>

Inferno provides commands for managing and using local LLMs:

```bash
python -m inferno --help
```

| Command | Description |
|---------|-------------|
| `python -m inferno pull <model>` | Download a model from Hugging Face |
| `python -m inferno list` | List downloaded models |
| `python -m inferno serve <model>` | Start a model server with OpenAI-compatible API |
| `python -m inferno run <model>` | Chat with a model interactively |
| `python -m inferno remove <model>` | Remove a downloaded model |
| `python -m inferno version` | Show version information |
</p>
</details>

> [!NOTE]
> **Hardware requirements for running models:**
> - Around 2 GB of RAM for 1B models
> - Around 4 GB of RAM for 3B models
> - At least 8 GB of RAM for 7B models
> - 16 GB of RAM for 13B models
> - 32 GB of RAM for 33B models
> - GPU acceleration is recommended for better performance

<hr/>

## 🔍 Search Engines

Webscout provides multiple search engine interfaces for diverse search capabilities.

### YepSearch - Yep.com Interface

```python
from webscout import YepSearch

# Initialize YepSearch
yep = YepSearch(
    timeout=20,  # Optional: Set custom timeout
    proxies=None,  # Optional: Use proxies
    verify=True   # Optional: SSL verification
)

# Text Search
text_results = yep.text(
    keywords="artificial intelligence",
    region="all",           # Optional: Region for results
    safesearch="moderate",  # Optional: "on", "moderate", "off"
    max_results=10          # Optional: Limit number of results
)

# Image Search
image_results = yep.images(
    keywords="nature photography",
    region="all",
    safesearch="moderate",
    max_results=10
)

# Get search suggestions
suggestions = yep.suggestions("hist")
```

### GoogleSearch - Google Interface

```python
from webscout import GoogleSearch

# Initialize GoogleSearch
google = GoogleSearch(
    timeout=10,  # Optional: Set custom timeout
    proxies=None,  # Optional: Use proxies
    verify=True   # Optional: SSL verification
)

# Text Search
text_results = google.text(
    keywords="artificial intelligence",
    region="us",           # Optional: Region for results
    safesearch="moderate",  # Optional: "on", "moderate", "off"
    max_results=10          # Optional: Limit number of results
)
for result in text_results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Description: {result.description}")

# News Search
news_results = google.news(
    keywords="technology trends",
    region="us",
    safesearch="moderate",
    max_results=5
)

# Get search suggestions
suggestions = google.suggestions("how to")

# Legacy usage is still supported
from webscout import search
results = search("Python programming", num_results=5)
```

<hr/>

## 🦆 DuckDuckGo Search with WEBS and AsyncWEBS

Webscout provides powerful interfaces to DuckDuckGo's search capabilities through the `WEBS` and `AsyncWEBS` classes.

<details open>
<summary><b>Synchronous Usage with WEBS</b></summary>
<p>

```python
from webscout import WEBS

# Use as a context manager for proper resource management
with WEBS() as webs:
    # Simple text search
    results = webs.text("python programming", max_results=5)
    for result in results:
        print(f"Title: {result['title']}\nURL: {result['url']}")
```
</p>
</details>

<details open>
<summary><b>Asynchronous Usage with AsyncWEBS</b></summary>
<p>

```python
import asyncio
from webscout import AsyncWEBS

async def search_multiple_terms(search_terms):
    async with AsyncWEBS() as webs:
        # Create tasks for each search term
        tasks = [webs.text(term, max_results=5) for term in search_terms]
        # Run all searches concurrently
        results = await asyncio.gather(*tasks)
        return results

async def main():
    terms = ["python", "javascript", "machine learning"]
    all_results = await search_multiple_terms(terms)

    # Process results
    for i, term_results in enumerate(all_results):
        print(f"Results for '{terms[i]}':\n")
        for result in term_results:
            print(f"- {result['title']}")
        print("\n")

# Run the async function
asyncio.run(main())
```
</p>
</details>

> [!TIP]
> Always use these classes with a context manager (`with` statement) to ensure proper resource management and cleanup.

<hr/>

## 💻 WEBS API Reference

The WEBS class provides comprehensive access to DuckDuckGo's search capabilities through a clean, intuitive API.

### Available Search Methods

| Method | Description | Example |
|--------|-------------|--------|
| `text()` | General web search | `webs.text('python programming')` |
| `answers()` | Instant answers | `webs.answers('population of france')` |
| `images()` | Image search | `webs.images('nature photography')` |
| `videos()` | Video search | `webs.videos('documentary')` |
| `news()` | News articles | `webs.news('technology')` |
| `maps()` | Location search | `webs.maps('restaurants', place='new york')` |
| `translate()` | Text translation | `webs.translate('hello', to='es')` |
| `suggestions()` | Search suggestions | `webs.suggestions('how to')` |
| `weather()` | Weather information | `webs.weather('london')` |

<details>
<summary><b>Example: Text Search</b></summary>
<p>

```python
from webscout import WEBS

with WEBS() as webs:
    results = webs.text(
        'artificial intelligence',
        region='wt-wt',        # Optional: Region for results
        safesearch='off',      # Optional: 'on', 'moderate', 'off'
        timelimit='y',         # Optional: Time limit ('d'=day, 'w'=week, 'm'=month, 'y'=year)
        max_results=10         # Optional: Limit number of results
    )

    for result in results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Description: {result['body']}\n")
```
</p>
</details>

<details>
<summary><b>Example: News Search with Formatting</b></summary>
<p>

```python
from webscout import WEBS
import datetime

def fetch_formatted_news(keywords, timelimit='d', max_results=20):
    """Fetch and format news articles"""
    with WEBS() as webs:
        # Get news results
        news_results = webs.news(
            keywords,
            region="wt-wt",
            safesearch="off",
            timelimit=timelimit,  # 'd'=day, 'w'=week, 'm'=month
            max_results=max_results
        )

        # Format the results
        formatted_news = []
        for i, item in enumerate(news_results, 1):
            # Format the date
            date = datetime.datetime.fromisoformat(item['date']).strftime('%B %d, %Y')

            # Create formatted entry
            entry = f"{i}. {item['title']}\n"
            entry += f"   Published: {date}\n"
            entry += f"   {item['body']}\n"
            entry += f"   URL: {item['url']}\n"

            formatted_news.append(entry)

        return formatted_news

# Example usage
news = fetch_formatted_news('artificial intelligence', timelimit='w', max_results=5)
print('\n'.join(news))
```
</p>
</details>

<details>
<summary><b>Example: Weather Information</b></summary>
<p>

```python
from webscout import WEBS

with WEBS() as webs:
    # Get weather for a location
    weather = webs.weather("New York")

    # Access weather data
    if weather:
        print(f"Location: {weather.get('location', 'Unknown')}")
        print(f"Temperature: {weather.get('temperature', 'N/A')}")
        print(f"Conditions: {weather.get('condition', 'N/A')}")
```
</p>
</details>

<hr/>

## 🤖 AI Models and Voices

Webscout provides easy access to a wide range of AI models and voice options.

<details open>
<summary><b>LLM Models</b></summary>
<p>

Access and manage Large Language Models with Webscout's model utilities.

```python
from webscout import model
from rich import print

# List all available LLM models
all_models = model.llm.list()
print(f"Total available models: {len(all_models)}")

# Get a summary of models by provider
summary = model.llm.summary()
print("Models by provider:")
for provider, count in summary.items():
    print(f"  {provider}: {count} models")

# Get models for a specific provider
provider_name = "PerplexityLabs"
available_models = model.llm.get(provider_name)
print(f"\n{provider_name} models:")
if isinstance(available_models, list):
    for i, model_name in enumerate(available_models, 1):
        print(f"  {i}. {model_name}")
else:
    print(f"  {available_models}")
```
</p>
</details>

<details open>
<summary><b>TTS Voices</b></summary>
<p>

Access and manage Text-to-Speech voices across multiple providers.

```python
from webscout import model
from rich import print

# List all available TTS voices
all_voices = model.tts.list()
print(f"Total available voices: {len(all_voices)}")

# Get a summary of voices by provider
summary = model.tts.summary()
print("\nVoices by provider:")
for provider, count in summary.items():
    print(f"  {provider}: {count} voices")

# Get voices for a specific provider
provider_name = "ElevenlabsTTS"
available_voices = model.tts.get(provider_name)
print(f"\n{provider_name} voices:")
if isinstance(available_voices, dict):
    for voice_name, voice_id in list(available_voices.items())[:5]:  # Show first 5 voices
        print(f"  - {voice_name}: {voice_id}")
    if len(available_voices) > 5:
        print(f"  ... and {len(available_voices) - 5} more")
```
</p>
</details>

<hr/>

## 💬 AI Chat Providers

Webscout offers a comprehensive collection of AI chat providers, giving you access to various language models through a consistent interface.

### Popular AI Providers

<div class="provider-table">

| Provider | Description | Key Features |
|----------|-------------|-------------|
| `OPENAI` | OpenAI's models | GPT-3.5, GPT-4, tool calling |
| `GEMINI` | Google's Gemini models | Web search capabilities |
| `Meta` | Meta's AI assistant | Image generation, web search |
| `GROQ` | Fast inference platform | High-speed inference, tool calling |
| `LLAMA` | Meta's Llama models | Open weights models |
| `DeepInfra` | Various open models | Multiple model options |
| `Cohere` | Cohere's language models | Command models |
| `PerplexityLabs` | Perplexity AI | Web search integration |
| `Anthropic` | Claude models | Long context windows |
| `YEPCHAT` | Yep.com's AI | Streaming responses |
| `ChatGPTClone` | ChatGPT-like interface | Multiple model options |
| `TypeGPT` | TypeChat models | Code generation focus |

</div>

<details>
<summary><b>Example: Using Duckchat</b></summary>
<p>

```python
from webscout import WEBS

# Initialize and use Duckchat
with WEBS() as webs:
    response = webs.chat(
        "Explain quantum computing in simple terms",
        model='gpt-4o-mini'  # Options: mixtral-8x7b, llama-3.1-70b, claude-3-haiku, etc.
    )
    print(response)
```
</p>
</details>

<details>
<summary><b>Example: Using Meta AI</b></summary>
<p>

```python
from webscout import Meta

# For basic usage (no authentication required)
meta_ai = Meta()

# Simple text prompt
response = meta_ai.chat("What is the capital of France?")
print(response)

# For authenticated usage with web search and image generation
meta_ai = Meta(fb_email="your_email@example.com", fb_password="your_password")

# Text prompt with web search
response = meta_ai.ask("What are the latest developments in quantum computing?")
print(response["message"])
print("Sources:", response["sources"])

# Image generation
response = meta_ai.ask("Create an image of a futuristic city")
for media in response.get("media", []):
    print(media["url"])
```
</p>
</details>

<details>
<summary><b>Example: GROQ with Tool Calling</b></summary>
<p>

```python
from webscout import GROQ, WEBS
import json

# Initialize GROQ client
client = GROQ(api_key="your_api_key")

# Define helper functions
def calculate(expression):
    """Evaluate a mathematical expression"""
    try:
        result = eval(expression)
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})

def search(query):
    """Perform a web search"""
    try:
        results = WEBS().text(query, max_results=3)
        return json.dumps({"results": results})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Register functions with GROQ
client.add_function("calculate", calculate)
client.add_function("search", search)

# Define tool specifications
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Perform a web search",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Use the tools
response = client.chat("What is 25 * 4 + 10?", tools=tools)
print(response)

response = client.chat("Find information about quantum computing", tools=tools)
print(response)
```
</p>
</details>

<hr/>

## 👨‍💻 Advanced AI Interfaces

<details open>
<summary><b>Direct Model Access with LLM and VLM</b></summary>
<p>

Webscout provides direct interfaces to language and vision-language models through the `LLM` and `VLM` classes.

```python
from webscout.LLM import LLM, VLM

# Text-only model interaction
llm = LLM("meta-llama/Meta-Llama-3-70B-Instruct")
response = llm.chat([
    {"role": "user", "content": "Explain the concept of neural networks"}
])
print(response)

# Vision-language model interaction
vlm = VLM("cogvlm-grounding-generalist")
response = vlm.chat([
    {
        "role": "user",
        "content": [
            {"type": "image", "image_url": "path/to/image.jpg"},
            {"type": "text", "text": "Describe what you see in this image"}
        ]
    }
])
print(response)
```
</p>
</details>

<details open>
<summary><b>GGUF Model Conversion</b></summary>
<p>

Webscout provides tools to convert and quantize Hugging Face models into the GGUF format for offline use.

```python
from webscout.Extra.gguf import ModelConverter

# Create a converter instance
converter = ModelConverter(
    model_id="mistralai/Mistral-7B-Instruct-v0.2",  # Hugging Face model ID
    quantization_methods="q4_k_m"                  # Quantization method
)

# Run the conversion
converter.convert()
```

#### Available Quantization Methods

| Method | Description |
|--------|-------------|
| `fp16` | 16-bit floating point - maximum accuracy, largest size |
| `q2_k` | 2-bit quantization (smallest size, lowest accuracy) |
| `q3_k_l` | 3-bit quantization (large) - balanced for size/accuracy |
| `q3_k_m` | 3-bit quantization (medium) - good balance for most use cases |
| `q3_k_s` | 3-bit quantization (small) - optimized for speed |
| `q4_0` | 4-bit quantization (version 0) - standard 4-bit compression |
| `q4_1` | 4-bit quantization (version 1) - improved accuracy over q4_0 |
| `q4_k_m` | 4-bit quantization (medium) - balanced for most models |
| `q4_k_s` | 4-bit quantization (small) - optimized for speed |
| `q5_0` | 5-bit quantization (version 0) - high accuracy, larger size |
| `q5_1` | 5-bit quantization (version 1) - improved accuracy over q5_0 |
| `q5_k_m` | 5-bit quantization (medium) - best balance for quality/size |
| `q5_k_s` | 5-bit quantization (small) - optimized for speed |
| `q6_k` | 6-bit quantization - highest accuracy, largest size |
| `q8_0` | 8-bit quantization - maximum accuracy, largest size |

#### Command Line Usage

```bash
python -m webscout.Extra.gguf convert -m "mistralai/Mistral-7B-Instruct-v0.2" -q "q4_k_m"
```
</p>
</details>

<div align="center">
  <p>
    <a href="https://youtube.com/@OEvortex">▶️ Vortex's YouTube Channel</a> |
    <a href="https://t.me/ANONYMOUS_56788">📢 Anonymous Coder's Telegram</a>
  </p>
</div>

<hr/>

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute to Webscout, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and commit them with descriptive messages
4. Push your branch to your forked repository
5. Submit a pull request to the main repository

## 🙏 Acknowledgments

* All the amazing developers who have contributed to the project
* The open-source community for their support and inspiration

<hr/>

<div align="center">
  <p>Made with ❤️ by the Webscout team</p>
</div>
