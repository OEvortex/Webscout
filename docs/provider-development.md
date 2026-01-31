# Provider Development Guide

> **Last updated:** 2026-01-24  
> **Type:** Developer Guide  
> **Audience:** Contributors, advanced users

## Overview

This guide teaches you how to create custom providers for Webscout, enabling integration with new AI services or local models.

### Two Provider Types

**Type 1: Native Providers** — Direct implementation from scratch, used for services with unique APIs

**Type 2: OpenAI-Compatible Providers** — For services that mimic the OpenAI API format

This guide covers both.

---

## Architecture Overview

### Provider Hierarchy

```
AIbase.Provider (Abstract)
├── Native Implementation (Custom API implementation)
└── OpenAI Providers
    └── OpenAICompatibleProvider (Abstract)
        └── Your Provider Implementation
```

### Key Concepts

- **Provider** — A class that translates user prompts into API calls
- **Model** — The actual AI model (e.g., "gpt-4", "llama-3.1-70b")
- **Session** — HTTP client for API communication (uses `curl_cffi` for reliability)
- **Conversation** — Optional context preservation across turns

---

## Native Provider Implementation

### Step 1: Create the Provider File

Create `webscout/Provider/YourProvider.py`:

```python
from typing import Any, Dict, Generator, Optional, Union

from curl_cffi.requests import Session
from webscout.AIbase import Provider, Response
from webscout import exceptions


class YourProvider(Provider):
    """
    A provider for Your AI Service.
    
    This provider integrates with the YourService API.
    """
    
    required_auth = True  # Set False if no API key needed
    
    def __init__(
        self,
        api_key: str,
        model: str = "default-model",
        is_conversation: bool = False,
        timeout: int = 30,
    ):
        """
        Initialize the provider.
        
        Args:
            api_key (str): Your API key
            model (str): Model to use. Default: default-model
            is_conversation (bool): Track conversation history
            timeout (int): Request timeout in seconds. Default: 30
        """
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.session = Session()
        
        # Conversation tracking
        self.conversation_id = None if is_conversation else None
        self.messages = []
```

### Step 2: Implement Required Methods

```python
    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Response:
        """
        Send a prompt and get raw response.
        """
        self.last_response = {}
        
        # Build API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
        }
        
        try:
            # Make API request
            response = self.session.post(
                "https://api.yourservice.com/v1/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            
            if response.status_code != 200:
                raise exceptions.APIConnectionError(
                    f"API error: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            self.last_response = data
            
            if stream:
                return self._stream_response(data)
            else:
                return data
                
        except Exception as e:
            raise exceptions.ProviderException(f"Failed to get response: {str(e)}")
    
    def _stream_response(self, response: Dict) -> Generator[str, None, None]:
        """Handle streaming responses."""
        if "choices" in response:
            for choice in response["choices"]:
                yield choice.get("text", "")
    
    def chat(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Send a prompt and get a clean message response.
        """
        response = self.ask(prompt, stream=stream, **kwargs)
        
        if stream:
            # For streaming, extract text from each chunk
            def extract_stream():
                for chunk in response:
                    yield self.get_message({"text": chunk})
            return extract_stream()
        else:
            return self.get_message(response)
    
    def get_message(self, response: Response) -> str:
        """
        Extract message text from response.
        """
        if isinstance(response, dict):
            # Adjust based on your API's response structure
            if "choices" in response:
                return response["choices"][0].get("text", "")
            elif "message" in response:
                return response["message"].get("content", "")
        
        return str(response)
```

### Step 3: Register Your Provider

Edit `webscout/Provider/__init__.py` and add:

```python
from webscout.Provider.YourProvider import YourProvider

# At the end of __all__ export list
__all__ = [
    # ... existing providers ...
    "YourProvider",
]
```

### Step 4: Add Unit Tests

Create `tests/providers/test_yourprovider.py`:

```python
import unittest
from unittest.mock import MagicMock, patch

from webscout.Provider.YourProvider import YourProvider


class TestYourProvider(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test-api-key"
        self.provider = YourProvider(api_key=self.api_key)
    
    @patch('webscout.Provider.YourProvider.Session.post')
    def test_chat(self, mock_post):
        """Test basic chat functionality."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "Hello, World!"}]
        }
        mock_post.return_value = mock_response
        
        # Test chat
        response = self.provider.chat("Hello")
        self.assertEqual(response, "Hello, World!")
    
    @patch('webscout.Provider.YourProvider.Session.post')
    def test_streaming(self, mock_post):
        """Test streaming response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "Chunk 1"}]
        }
        mock_post.return_value = mock_response
        
        # Collect streamed response
        response = self.provider.chat("Test", stream=True)
        chunks = list(response)
        self.assertTrue(len(chunks) > 0)


if __name__ == "__main__":
    unittest.main()
```

---

## OpenAI-Compatible Provider Implementation

For services that use OpenAI-like APIs:

### Step 1: Understand the Base Class

```python
from webscout.Provider.Openai_comp.base import OpenAICompatibleProvider

class YourOpenAIProvider(OpenAICompatibleProvider):
    """
    A provider that uses OpenAI-compatible API.
    """
    required_auth = True  # Or False if free
```

### Step 2: Implement Required Properties

```python
    @property
    def models(self):
        """Return available models."""
        return type("M", (), {
            "list": lambda self: [
                "model-1",
                "model-2",
                "model-3",
            ]
        })()
    
    @property
    def base_url(self) -> str:
        """API base URL."""
        return "https://api.yourservice.com/v1"
    
    @property
    def default_model(self) -> str:
        """Default model to use."""
        return "model-1"
    
    @property
    def default_timeout(self) -> int:
        """Default request timeout."""
        return 30
```

### Step 3: Implement the Completions Method

```python
    def create_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator]:
        """
        Create a chat completion using OpenAI-compatible format.
        """
        from webscout.Provider.Openai_comp.utils import ChatCompletion
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": stream,
            **kwargs,  # temperature, top_p, etc.
        }
        
        try:
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=kwargs.get("timeout", self.default_timeout),
            )
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.text}")
            
            if stream:
                return self._handle_stream(response)
            else:
                data = response.json()
                return ChatCompletion(
                    id="",
                    model=model or self.default_model,
                    choices=[{
                        "message": {
                            "content": data["choices"][0]["message"]["content"],
                            "role": "assistant"
                        }
                    }],
                    usage={"total_tokens": 0}
                )
        except Exception as e:
            raise Exception(f"Failed to create completion: {str(e)}")
```

---

## Best Practices

### 1. Error Handling

```python
def ask(self, prompt: str, **kwargs) -> Response:
    """Handle errors gracefully."""
    try:
        # API call
        response = self.session.post(...)
    except TimeoutError:
        raise exceptions.APITimeoutError("Request timed out")
    except ConnectionError:
        raise exceptions.APIConnectionError("Connection failed")
    except Exception as e:
        raise exceptions.ProviderException(f"Unexpected error: {str(e)}")
```

### 2. Rate Limiting

```python
import time

def chat(self, prompt: str, **kwargs) -> str:
    """Add rate limiting support."""
    # Check if we need to wait
    if self.last_request_time:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
    
    self.last_request_time = time.time()
    # ... make request
```

### 3. Response Validation

```python
def get_message(self, response: Response) -> str:
    """Validate response format."""
    if not isinstance(response, dict):
        raise ValueError(f"Expected dict, got {type(response)}")
    
    if "choices" not in response:
        raise ValueError("No choices in response")
    
    if not response["choices"]:
        raise ValueError("Empty choices list")
    
    return response["choices"][0].get("message", {}).get("content", "")
```

### 4. Type Hints

```python
from typing import Any, Dict, Generator, Optional, Union

def chat(
    self,
    prompt: str,
    stream: bool = False,
    **kwargs: Any,
) -> Union[str, Generator[str, None, None]]:
    """Always use type hints."""
    pass
```

### 5. Documentation

Every provider should have docstrings:

```python
class MyProvider(Provider):
    """
    Brief description of provider.
    
    This provider uses [Service Name] API to generate responses.
    
    Required API Key:
        - Get from https://website.com/api-keys
        - Set via parameter or environment variable MY_SERVICE_API_KEY
    
    Attributes:
        api_key (str): Your API key
        model (str): Model to use
    
    Examples:
        >>> provider = MyProvider(api_key="sk-...")
        >>> response = provider.chat("Hello")
        >>> print(response)
    """
```

---

## Testing Checklist

- [ ] All methods raise appropriate exceptions
- [ ] Streaming works correctly
- [ ] Conversation history is maintained
- [ ] API key validation works
- [ ] Timeout handling is correct
- [ ] Error messages are clear
- [ ] Type hints are complete
- [ ] Tests pass: `pytest tests/providers/`
- [ ] Linting passes: `ruff check .`
- [ ] Type checking passes: `ty check .`

---

## Deployment

### 1. Document Your Provider

Edit `Provider.md` and add:

```markdown
### YourProvider

**Location:** `webscout/Provider/YourProvider.py`

**Description:** Brief description of what it does

**Authentication:** API key required

**Models:** List available models

**Example:**
```python
from webscout import YourProvider
provider = YourProvider(api_key="your-key")
response = provider.chat("Hello")
```
```

### 2. Update Documentation

Add an example section to the getting-started guide if needed.

### 3. Create a PR

Follow the [Contributing Guidelines](contributing.md)

---

## Common Patterns

### Handling Different Response Formats

```python
def get_message(self, response: Response) -> str:
    """Handle multiple possible response formats."""
    if isinstance(response, str):
        return response
    
    if isinstance(response, dict):
        # Try multiple possible paths
        content = (
            response.get("message", {}).get("content")
            or response.get("choices", [{}])[0].get("message", {}).get("content")
            or response.get("text")
            or response.get("content")
        )
        
        if content:
            return str(content)
        
        raise ValueError(f"Could not extract message from: {response}")
    
    raise TypeError(f"Unexpected response type: {type(response)}")
```

### Implementing Conversation History

```python
def __init__(self, is_conversation: bool = True, **kwargs):
    super().__init__()
    self.is_conversation = is_conversation
    self.conversation_history = []

def chat(self, prompt: str, **kwargs) -> str:
    if self.is_conversation:
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })
    
    # Get response
    response = self.ask(prompt, **kwargs)
    message = self.get_message(response)
    
    if self.is_conversation:
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": message
        })
    
    return message
```

---

## See Also

- [API Reference](api-reference.md) — Full API documentation
- [Contributing Guide](contributing.md) — How to contribute
- [Testing Guidelines](../AGENTS.md) — Testing standards
- [Provider List](../Provider.md) — All available providers
