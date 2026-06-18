# Getting Started with LLM4Free

> **Last updated:** 2026-01-24  
> **Status:** Current & maintained  
> **Target audience:** New users, developers getting started

## Quick Navigation

- [Installation](#installation)
- [Your First Chat](#your-first-chat)
- [Web Search](#web-search)
- [Image Generation](#image-generation)
- [Common Issues](#common-issues)
- [Next Steps](#next-steps)

---

## Installation

### Option 1: Using pip (Standard)

```bash
# Basic installation
pip install -U llm4free

# With OpenAI-compatible API server
pip install -U "llm4free[api]"

# Development installation
pip install -U "llm4free[dev]"
```

### Option 2: Using uv (Recommended)

[UV](https://github.com/astral-sh/uv) is a fast Python package manager that LLM4Free fully supports:

```bash
# Install LLM4Free with uv
uv add llm4free

# Or install as a global tool
uv tool install llm4free

# Run immediately without installing
uv run llm4free --help
```

### Option 3: Docker

```bash
# Pull and run the official Docker image
docker pull OEvortex/llm4free:latest
docker run -it OEvortex/llm4free:latest
```

### Verify Installation

```bash
# Check version
llm4free version

# List available commands
llm4free --help
```

---

## Your First Chat

### Simple Chat (No API Key Required)

Many LLM4Free providers work without authentication. Here's a quick example:

```python
from llm4free import Meta

# Initialize the provider
ai = Meta()

# Ask a question
response = ai.chat("Explain quantum computing in simple terms")
print(response)
```

**Expected output:**
```
Quantum computing is a type of computing that uses quantum bits...
```

### Using OpenAI (With API Key)

If you have an OpenAI API key:

```python
from llm4free import OpenAI

# Initialize with your API key
client = OpenAI(api_key="sk-your-api-key-here")

# Simple chat
response = client.chat("What are the benefits of renewable energy?")
print(response)
```

### Using Other Popular Providers

```python
# GROQ - Fast inference
from llm4free import GROQ
groq = GROQ(api_key="your-groq-api-key")
response = groq.chat("Write a Python function to sort a list")
print(response)

# Cohere - Powerful language model
from llm4free import Cohere
cohere = Cohere(api_key="your-cohere-api-key")
response = cohere.chat("Summarize the theory of relativity")
print(response)

# Google Gemini
from llm4free import GEMINI
gemini = GEMINI(api_key="your-gemini-api-key")
response = gemini.chat("What is machine learning?")
print(response)
```

### Streaming Responses

For longer responses, stream them in real-time:

```python
from llm4free import GROQ

client = GROQ(api_key="your-groq-api-key")

# Enable streaming
response = client.chat("Write a 500-word essay on AI ethics", stream=True)

# Print each chunk as it arrives
for chunk in response:
    print(chunk, end="", flush=True)
```

---

## Web Search

### DuckDuckGo Search (CLI)

```bash
# Basic text search
llm4free text -k "python programming"

# Image search
llm4free images -k "mountain landscape"

# News search
llm4free news -k "AI breakthrough"

# Weather
llm4free weather -l "New York"
```

### Search with Python

```python
from llm4free import DuckDuckGoSearch

# Initialize
search = DuckDuckGoSearch()

# Perform text search
results = search.text("best practices for API design", max_results=5)

for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['href']}")
    print(f"Snippet: {result['body']}\n")
```

### Using Different Search Engines

```python
from llm4free import BingSearch, YepSearch, YahooSearch

# Bing
bing = BingSearch()
results = bing.text("climate change solutions")

# Yep (privacy-focused)
yep = YepSearch()
results = yep.text("machine learning")

# Yahoo
yahoo = YahooSearch()
results = yahoo.text("python frameworks")
```

---

## Image Generation

### Text-to-Image Basics

```python
from llm4free.Provider.TTI import Pollinations

# Initialize
image_generator = Pollinations()

# Generate an image
image_path = image_generator.generate_image(
    prompt="A serene mountain landscape at sunset",
    model="pollinations"
)

print(f"Image saved to: {image_path}")
```

### Using Different TTI Providers

```python
from llm4free.Provider.TTI import Together, MiraGic

# Together AI
together = Together()
image = together.generate_image("A futuristic city")

# MiraGic
miragic = MiraGic()
image = miragic.generate_image("A robot playing chess")
```

---

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'llm4free'"

**Solution:**
```bash
# Ensure the package is installed
pip install -U llm4free

# Or if using uv
uv add llm4free

# If developing locally
cd /path/to/LLM4Free
pip install -e .
```

### Issue: "API Key not valid" or "401 Unauthorized"

**Solution:**
1. Verify your API key is correct and copied without extra spaces
2. Check that your API key hasn't expired
3. Ensure you're using the correct provider class for your key

```python
# Good - API key is set correctly
client = OpenAI(api_key="sk-your-actual-key-here")

# Bad - Extra spaces or quotes
client = OpenAI(api_key=" sk-your-key ") # Extra spaces!
```

### Issue: "Rate limit exceeded" or "Too many requests"

**Solution:**
```python
import time
from llm4free import GROQ

client = GROQ(api_key="your-api-key")

# Add delay between requests
for i in range(10):
    response = client.chat(f"Question {i}")
    print(response)
    time.sleep(2)  # Wait 2 seconds between requests
```

### Issue: Network timeout or connection errors

**Solution:**
```python
from llm4free import OpenAI

# Increase timeout from default 30 seconds
client = OpenAI(
    api_key="your-api-key",
    timeout=60  # 60 seconds
)

try:
    response = client.chat("Your question here")
except Exception as e:
    print(f"Error: {e}")
    # Handle the error gracefully
```

### Issue: No streaming data received

**Solution:**
```python
from llm4free import GROQ

client = GROQ(api_key="your-api-key")

# Use proper streaming syntax
response = client.chat("Write a poem", stream=True)

# Check if response is a generator
import types
if isinstance(response, types.GeneratorType):
    for chunk in response:
        print(chunk, end="", flush=True)
else:
    print(response)
```

---

## Next Steps

### 📚 Learn More

- **[API Reference](api-reference.md)** — Deep dive into all available classes and methods
- **[Provider Development](provider-development.md)** — Create custom providers
- **[Examples](examples/README.md)** — Real-world code examples
- **[Troubleshooting](troubleshooting.md)** — Solution to common problems

### 🚀 Try Advanced Features

1. **Conversational AI** — Maintain multi-turn conversations
   ```python
   from llm4free import Meta
   
   ai = Meta(is_conversation=True)
   ai.chat("Hello, what's your name?")
   ai.chat("Can you remember my question?")  # Context preserved
   ```

2. **Web Search Integration** — Combine search with AI
   ```python
   from llm4free import DuckDuckGoSearch, Meta
   
   search = DuckDuckGoSearch()
   results = search.text("latest AI news")
   
   ai = Meta()
   response = ai.chat(f"Summarize this news: {results[0]['body']}")
   ```

3. **CLI Interface** — Use LLM4Free from terminal
   ```bash
   llm4free text -k "python tips and tricks"
   llm4free images -k "nature photography" --size large
   ```

### 🔧 Customize Your Setup

- **Environment variables** — Set default API keys
- **Configuration** — Adjust timeouts, retries, and more
- **Custom providers** — Build your own integrations

---

## Command Reference

### Chat Commands

```bash
# Interactive chat (if supported by provider)
llm4free chat

# Show available AI providers
llm4free providers list
```

### Search Commands

```bash
# DuckDuckGo (default)
llm4free text -k "search term"
llm4free images -k "search term"
llm4free news -k "search term"

# Alternative engines
llm4free bing_text -k "search term"
llm4free yep_text -k "search term"
llm4free yahoo_text -k "search term"
```

### Utility Commands

```bash
# Show version
llm4free version

# Help for specific command
llm4free text --help
```

---

## IDE Setup

### VSCode

1. Install Python extension
2. Select your Python interpreter (where you installed LLM4Free)
3. Create a `.code-workspace` file:

```json
{
  "folders": [{"path": "."}],
  "settings": {
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python"
  }
}
```

### PyCharm

1. **File → Settings → Project → Python Interpreter**
2. Click the gear icon and select **Add...**
3. Choose **Existing Environment** and select your Python interpreter
4. LLM4Free should now autocomplete and provide IntelliSense

---

## Summary

You're now ready to:
- ✅ Use LLM4Free for chat and search
- ✅ Generate images
- ✅ Integrate with your projects
- ✅ Troubleshoot basic issues

**Next:** Explore the [API Reference](api-reference.md) for advanced usage patterns.

For detailed troubleshooting, see [Troubleshooting Guide](troubleshooting.md).
