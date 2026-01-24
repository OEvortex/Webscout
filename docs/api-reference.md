# API Reference

> **Last updated:** 2026-01-24  
> **Type:** Technical Reference  
> **Audience:** Developers

## Table of Contents

1. [Core Classes](#core-classes)
2. [Provider Base Class](#provider-base-class)
3. [Chat Methods](#chat-methods)
4. [Client API](#client-api)
5. [Exceptions](#exceptions)
6. [Type Definitions](#type-definitions)

---

## Core Classes

### AIbase.Provider

The base class for all AI providers. Do not use this directly; instead, use the specific provider implementations.

```python
from webscout.AIbase import Provider
```

**Key attributes:**
- `required_auth` (bool) — Whether the provider requires API authentication
- `conversation` (Any) — Stores conversation history if enabled

---

## Provider Base Class

### Abstract Methods

All provider implementations must implement these three methods:

#### `ask()`

Sends a prompt and returns raw response data.

```python
def ask(
    self,
    prompt: str,
    stream: bool = False,
    raw: bool = False,
    optimizer: Optional[str] = None,
    conversationally: bool = False,
    **kwargs: Any,
) -> Response:
    """
    Send a prompt to the provider.
    
    Args:
        prompt (str): The user's input prompt
        stream (bool): Return streaming response if True. Default: False
        raw (bool): Return raw data without post-processing. Default: False
        optimizer (Optional[str]): Apply a system prompt optimizer. See AwesomePrompts
        conversationally (bool): Maintain conversation history. Default: False
        **kwargs: Provider-specific arguments
    
    Returns:
        Response: Either a string, dict, or generator depending on parameters
    
    Raises:
        AIProviderError: If the provider encounters an error
    
    Example:
        >>> from webscout import Meta
        >>> ai = Meta()
        >>> response = ai.ask("Hello")
        >>> print(response)
    """
```

#### `chat()`

Sends a prompt and extracts the message from the response.

```python
def chat(
    self,
    prompt: str,
    stream: bool = False,
    optimizer: Optional[str] = None,
    conversationally: bool = False,
    **kwargs: Any,
) -> Union[str, Generator[str, None, None]]:
    """
    Send a prompt and get a clean message response.
    
    Args:
        prompt (str): The user's input prompt
        stream (bool): Stream the response if True. Default: False
        optimizer (Optional[str]): Apply system prompt optimization
        conversationally (bool): Use conversation history. Default: False
        **kwargs: Provider-specific arguments
    
    Returns:
        str | Generator[str, None, None]: The message response
    
    Example:
        >>> from webscout import GROQ
        >>> client = GROQ(api_key="YOUR_KEY")
        >>> response = client.chat("Explain machine learning")
        >>> print(response)
        
        >>> # With streaming
        >>> for chunk in client.chat("Write a poem", stream=True):
        ...     print(chunk, end="", flush=True)
    """
```

#### `get_message()`

Extracts the message from a response object.

```python
def get_message(self, response: Response) -> str:
    """
    Extract the message text from a provider response.
    
    Args:
        response (Response): The response from ask() method
    
    Returns:
        str: The extracted message text
    
    Example:
        >>> response = ai.ask("What is AI?", raw=True)
        >>> message = ai.get_message(response)
        >>> print(message)
    """
```

---

## Chat Methods

### Common Parameters

Most chat providers accept these standard parameters:

```python
# All providers support these
client.chat(
    prompt="Your question here",          # Required: The user's prompt
    stream=False,                          # Optional: Enable streaming
    optimizer=None,                        # Optional: System prompt optimizer
    conversationally=False,                # Optional: Use conversation history
)

# OpenAI and compatible providers also support
client.chat(
    temperature=0.7,                       # Control randomness (0-2)
    top_p=0.9,                             # Nucleus sampling
    max_tokens=500,                        # Response length limit
    presence_penalty=0,                    # Reduce repetition
    frequency_penalty=0,                   # Reduce common words
)
```

### Streaming Examples

```python
from webscout import GROQ

client = GROQ(api_key="your-api-key")

# Stream text response
print("Streaming response:")
for chunk in client.chat("Write a haiku", stream=True):
    print(chunk, end="", flush=True)

print("\n")

# Collect streamed response
def collect_stream(generator):
    full_response = ""
    for chunk in generator:
        full_response += chunk
    return full_response

full_text = collect_stream(client.chat("Your prompt", stream=True))
```

### Conversation Management

```python
from webscout import Meta

# Enable conversation mode to maintain context
ai = Meta(is_conversation=True)

# First turn
response1 = ai.chat("My name is Alice")
print(response1)

# Second turn - context is preserved
response2 = ai.chat("What is my name?")  # AI remembers "Alice"
print(response2)
```

---

## Client API

### Unified Client

The `webscout.client` module provides a unified interface for interacting with all providers.

```python
from webscout.client import Client

# Create client
client = Client()

# Chat with automatic provider selection
response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)
print(response.choices[0].message.content)

# Specify provider and model
response = client.chat.completions.create(
    model="GROQ/llama-3.1-8b-instant",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)

# With streaming
stream = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Write a story"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Available Providers

Common providers available in the client:

| Provider | Required Auth | Notes |
|----------|--------------|-------|
| `Meta` | No | Free, no API key needed |
| `GROQ` | Yes | Fast inference, free tier available |
| `OpenAI` | Yes | GPT models |
| `GEMINI` | Yes | Google's Gemini models |
| `Cohere` | Yes | Command models |
| `OpenRouter` | Yes | Multi-model provider |
| `TogetherAI` | Yes | Open models |

For a complete list, see [Provider Documentation](../Provider.md)

---

## Exceptions

### AIProviderError

Base exception for provider-related errors.

```python
from webscout.exceptions import AIProviderError

try:
    response = ai.chat("prompt")
except AIProviderError as e:
    print(f"Provider error: {e}")
```

### Common Error Scenarios

```python
from webscout import OpenAI
from webscout.exceptions import AIProviderError

client = OpenAI(api_key="invalid-key")

try:
    response = client.chat("Hello")
except AIProviderError as e:
    if "401" in str(e):
        print("Invalid API key")
    elif "429" in str(e):
        print("Rate limited - wait before retrying")
    else:
        print(f"Unknown error: {e}")
except Exception as e:
    print(f"Network or other error: {e}")
```

---

## Type Definitions

### Response Type

```python
from typing import Union, Dict, Generator, Any

Response = Union[Dict[str, Any], Generator[Any, None, None], str]
```

The response can be:
- **str** — Simple string response
- **Dict** — Complex response with metadata (raw response from `ask()`)
- **Generator** — Stream of chunks when `stream=True`

### Message Format

```python
# Typical message structure for OpenAI-compatible providers
message = {
    "role": "assistant",  # "assistant" or "user"
    "content": "Response text"
}

# With tool calls (if supported)
message = {
    "role": "assistant",
    "content": "Text response",
    "tool_calls": [
        {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"location": "NYC"}'
            }
        }
    ]
}
```

---

## Code Examples

### Basic Chat

```python
from webscout import GROQ

# Initialize
client = GROQ(api_key="your-groq-api-key")

# Simple chat
response = client.chat("What is Python?")
print(response)

# Output:
# Python is a high-level, interpreted programming language...
```

### Multi-turn Conversation

```python
from webscout import Meta

ai = Meta(is_conversation=True)

# Turn 1
ai.chat("I like programming")
# Output: That's great! Programming is a valuable skill...

# Turn 2
response = ai.chat("What languages should I learn?")
# AI considers previous messages in context
print(response)
```

### Image Generation

```python
from webscout.Provider.TTI import Pollinations

generator = Pollinations()

# Generate image
image_path = generator.generate_image(
    prompt="A peaceful river in autumn",
    size="1024x1024"
)

print(f"Image saved to: {image_path}")
```

### Error Handling

```python
from webscout import OpenAI
from webscout.exceptions import AIProviderError

client = OpenAI(api_key="your-key")

try:
    response = client.chat("Hello")
except AIProviderError as e:
    print(f"Provider error: {e}")
except TimeoutError:
    print("Request timed out - try again")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### With Decorators

```python
from webscout import GROQ
from webscout.AIutel import retry

@retry(max_attempts=3, delay=2)
def chat_with_retry(prompt: str) -> str:
    client = GROQ(api_key="your-key")
    return client.chat(prompt)

# Call will retry up to 3 times if it fails
response = chat_with_retry("Your prompt here")
```

---

## Common Patterns

### Fallback to Multiple Providers

```python
from webscout import GROQ, OpenAI, Meta

def chat_with_fallback(prompt: str) -> str:
    providers = [
        ("GROQ", lambda: GROQ(api_key="key").chat(prompt)),
        ("OpenAI", lambda: OpenAI(api_key="key").chat(prompt)),
        ("Meta", lambda: Meta().chat(prompt)),
    ]
    
    for name, chat_fn in providers:
        try:
            return chat_fn()
        except Exception as e:
            print(f"{name} failed: {e}")
            continue
    
    raise Exception("All providers failed")
```

### Batch Processing

```python
from webscout import GROQ

client = GROQ(api_key="your-key")
prompts = ["What is AI?", "Explain ML", "Define DL"]

responses = []
for prompt in prompts:
    response = client.chat(prompt)
    responses.append(response)
    
    # Parse and process each response
    print(f"Q: {prompt}")
    print(f"A: {response[:100]}...\n")
```

### Streaming with Progress

```python
from webscout import GROQ
import sys

client = GROQ(api_key="your-key")

print("Generating response...")
for chunk in client.chat("Write a story", stream=True):
    print(chunk, end="", flush=True)
    sys.stdout.flush()

print()  # Newline at end
```

---

## See Also

- [Getting Started](getting-started.md) — Quick start guide
- [Provider Development](provider-development.md) — Create custom providers
- [Troubleshooting](troubleshooting.md) — Solutions to common issues
- [Examples](examples/README.md) — Real-world code examples
