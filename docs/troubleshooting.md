# Troubleshooting Guide

> **Last updated:** 2026-01-24  
> **Type:** Support & FAQ  
> **Audience:** All users

## Quick Navigation

- [Installation Issues](#installation-issues)
- [Authentication Errors](#authentication-errors)
- [Runtime Errors](#runtime-errors)
- [Performance Issues](#performance-issues)
- [Streaming Problems](#streaming-problems)
- [FAQ](#faq)

---

## Installation Issues

### "ModuleNotFoundError: No module named 'webscout'"

**Diagnosis:** Webscout is not installed or not in your Python path.

**Solutions:**

```bash
# 1. Install via pip
pip install -U webscout

# 2. Or use uv (recommended)
uv add webscout

# 3. If developing locally, install in editable mode
cd /path/to/Webscout
pip install -e .

# 4. Verify installation worked
python -c "import webscout; print(webscout.__version__)"
```

### "pip: command not found"

**Diagnosis:** Python or pip is not installed, or not in PATH.

**Solutions:**

```bash
# 1. Check if Python is installed
python --version
python3 --version

# 2. Install pip if missing
python -m ensurepip --upgrade

# 3. Use uv instead (easier)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv add webscout

# 4. Use python -m pip instead
python -m pip install webscout
```

### "Permission denied" during installation

**Windows:**
```bash
# Run Command Prompt as Administrator
# Then run
pip install -U webscout
```

**Linux/macOS:**
```bash
# Use --user flag to install for current user only
pip install --user webscout

# Or use a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install webscout
```

### "Could not find a version that satisfies the requirement"

**Diagnosis:** Package version doesn't exist or your Python version is incompatible.

**Solutions:**

```bash
# 1. Check your Python version
python --version

# 2. Install latest version
pip install --upgrade webscout

# 3. Install specific version
pip install webscout==2024.12.01

# 4. Clear pip cache and retry
pip cache purge
pip install webscout
```

---

## Authentication Errors

### "401 Unauthorized" or "Invalid API Key"

**Diagnosis:** API key is invalid, expired, or has wrong permissions.

**Solutions:**

```python
# 1. Check for typos and whitespace
api_key = "sk-your-key"  # Good
api_key = "sk-your-key " # Bad - trailing space!
api_key = " sk-your-key" # Bad - leading space!

# 2. Verify key is from correct service
# For OpenAI, keys start with "sk-"
# For GROQ, keys start with "gsk_"
# For other services, check their documentation

client = OpenAI(api_key=api_key.strip())  # Remove whitespace
```

**For each service:**

| Service | Key Format | Where to Get |
|---------|-----------|-------------|
| OpenAI | `sk-...` | https://platform.openai.com/api-keys |
| GROQ | `gsk_...` | https://console.groq.com/keys |
| Cohere | `co_...` | https://dashboard.cohere.com/api-keys |
| Google | See docs | https://cloud.google.com/docs/authentication |

### "API key not provided"

**Diagnosis:** Required API key is missing.

**Solutions:**

```python
# 1. Pass key directly (for testing only)
client = OpenAI(api_key="your-actual-key-here")

# 2. Use environment variable (more secure)
import os
os.environ["OPENAI_API_KEY"] = "your-key-here"
client = OpenAI()  # Will read from environment

# 3. Set in your shell
# Linux/macOS: export OPENAI_API_KEY=your-key-here
# Windows PowerShell: $env:OPENAI_API_KEY="your-key-here"
# Windows CMD: set OPENAI_API_KEY=your-key-here

# 4. For providers that don't require auth
from webscout import Meta
meta = Meta()  # No key needed
response = meta.chat("Hello")
```

### "Invalid authentication credentials"

**Diagnosis:** API key exists but is not properly formatted or has been revoked.

**Solutions:**

```python
# 1. Generate a new API key from the service's dashboard
# 2. Make sure you're using the latest key
# 3. Check if the key has the required permissions

# 4. Test connectivity with curl
import subprocess
import json

api_key = "your-key"
headers = {"Authorization": f"Bearer {api_key}"}

# Test OpenAI connectivity
result = subprocess.run([
    "curl", "-H", f"Authorization: Bearer {api_key}",
    "https://api.openai.com/v1/models"
], capture_output=True, text=True)

print(result.stdout)  # Should show available models
```

---

## Runtime Errors

### "ConnectionError" or "Failed to establish connection"

**Diagnosis:** Network issue or server is unreachable.

**Solutions:**

```python
# 1. Check your internet connection
import socket
try:
    socket.create_connection(("8.8.8.8", 53))
    print("Internet connection: OK")
except OSError:
    print("No internet connection")

# 2. Increase timeout
from webscout import GROQ
client = GROQ(api_key="key", timeout=60)  # 60 seconds instead of default 30

# 3. Check if server is up
import subprocess
result = subprocess.run(["ping", "-c", "1", "api.groq.com"], 
                       capture_output=True, text=True)
print(result.stdout)

# 4. Use a retry mechanism
from webscout.AIutel import retry

@retry(max_attempts=3, delay=2)
def safe_chat(prompt):
    client = GROQ(api_key="key")
    return client.chat(prompt)

response = safe_chat("Hello")
```

### "TimeoutError: request timed out"

**Diagnosis:** Request took too long to complete.

**Solutions:**

```python
# 1. Increase timeout value
from webscout import OpenAI

client = OpenAI(
    api_key="key",
    timeout=120  # 2 minutes
)

# 2. Try with a simpler prompt
response = client.chat("Hello")  # Simple first

# 3. Check network speed
import subprocess
import time

start = time.time()
try:
    client.chat("Test")
except TimeoutError:
    duration = time.time() - start
    print(f"Timed out after {duration:.1f}s - your network may be slow")

# 4. Use a proxy/VPN if certain services are blocked
client = OpenAI(
    api_key="key",
    proxies={
        "http": "http://proxy.example.com:8080",
        "https": "http://proxy.example.com:8080",
    }
)
```

### "RateLimitError" or "Too many requests"

**Diagnosis:** You're making requests too frequently.

**Solutions:**

```python
# 1. Add delays between requests
import time
from webscout import GROQ

client = GROQ(api_key="key")

for i in range(10):
    response = client.chat(f"Question {i}")
    print(response)
    time.sleep(5)  # Wait 5 seconds between requests

# 2. Use request queuing
from queue import Queue
from threading import Thread
import time

def rate_limited_chat(prompts):
    queue = Queue(maxsize=1)  # Max 1 concurrent request
    
    def worker():
        client = GROQ(api_key="key")
        while True:
            prompt = queue.get()
            if prompt is None:
                break
            response = client.chat(prompt)
            print(response)
            time.sleep(2)
            queue.task_done()
    
    # Start worker thread
    thread = Thread(target=worker, daemon=False)
    thread.start()
    
    # Add prompts to queue
    for prompt in prompts:
        queue.put(prompt)
    
    queue.put(None)  # Signal worker to stop
    thread.join()

rate_limited_chat(["Question 1", "Question 2"])

# 3. Check rate limits
print("Check service documentation for rate limits:")
print("- OpenAI: https://platform.openai.com/account/rate-limits")
print("- GROQ: https://console.groq.com/docs/rate-limits")
```

### "AttributeError" or "TypeError"

**Diagnosis:** Using wrong method names or parameters.

**Solutions:**

```python
# 1. Check method names (Python is case-sensitive)
from webscout import Meta

ai = Meta()

# Good - correct method name
response = ai.chat("Hello")

# Bad - wrong method name
# response = ai.Chat("Hello")  # AttributeError!

# 2. Check method signatures
from inspect import signature

sig = signature(ai.chat)
print(sig)  # Shows what parameters are expected

# 3. Use dir() to list available methods
print(dir(ai))  # Shows all available methods

# 4. Check docstrings
help(ai.chat)  # Shows full documentation

# 5. Use IDE autocomplete/IntelliSense
# In VSCode/PyCharm, type and press Ctrl+Space for suggestions
```

### "ImportError" for specific modules

**Diagnosis:** Optional dependencies not installed.

**Solutions:**

```bash
# 1. Install with extras for API server
pip install "webscout[api]"

# 2. Install with dev dependencies
pip install "webscout[dev]"

# 3. Install specific missing packages
pip install beautifulsoup4
pip install requests
pip install curl-cffi

# 4. Check what's installed
pip list | grep webscout
```

---

## Streaming Problems

### "No streaming data received" or "Generator is empty"

**Diagnosis:** Streaming isn't enabled or response format is wrong.

**Solutions:**

```python
from webscout import GROQ

client = GROQ(api_key="key")

# 1. Make sure stream=True
response = client.chat("Write a story", stream=True)

# 2. Check if it's actually a generator
import types
if isinstance(response, types.GeneratorType):
    print("✓ Streaming enabled")
    for chunk in response:
        print(chunk, end="", flush=True)
else:
    print("✗ Not streaming - got direct response")
    print(response)

# 3. Handle both streaming and non-streaming
def safe_print_response(response):
    if isinstance(response, types.GeneratorType):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)

response = client.chat("Hello", stream=True)
safe_print_response(response)
```

### "Incomplete response while streaming"

**Diagnosis:** Connection interrupted during streaming.

**Solutions:**

```python
from webscout import GROQ

client = GROQ(api_key="key", timeout=120)

full_response = ""
try:
    for chunk in client.chat("Your prompt", stream=True):
        full_response += chunk
        print(chunk, end="", flush=True)
except Exception as e:
    print(f"\n\nStream interrupted: {e}")
    print(f"Partial response received:\n{full_response}")

# Use with larger timeout for long responses
```

---

## Performance Issues

### "Response is very slow"

**Diagnosis:** Network latency, server load, or model complexity.

**Solutions:**

```python
# 1. Check network speed
import time

start = time.time()
response = client.chat("What is AI?")
duration = time.time() - start

if duration > 10:
    print(f"⚠️  Slow response: {duration:.1f}s")
else:
    print(f"✓ Normal response time: {duration:.1f}s")

# 2. Use faster models
from webscout import GROQ

# Slower but more capable
client = GROQ(api_key="key")
response = client.chat("Prompt", model="llama-3.1-70b-versatile")

# Faster but less capable
response = client.chat("Prompt", model="llama-3.1-8b-instant")

# 3. Reduce response length
response = client.chat(
    "What is AI?",
    max_tokens=100  # Shorter response = faster
)

# 4. Use dedicated APIs vs free services
# Official APIs (OpenAI, GROQ with key) are usually faster
# Than free alternatives
```

### "High memory usage" or "Out of memory"

**Diagnosis:** Large response, long conversation history, or memory leak.

**Solutions:**

```python
# 1. Clear conversation history periodically
from webscout import Meta

ai = Meta(is_conversation=True)

# Chat several times
for i in range(10):
    response = ai.chat(f"Question {i}")
    
    if i % 5 == 0:
        # Clear history to free memory
        ai.conversation = None
        ai.messages = []

# 2. Limit max tokens
response = client.chat(
    "Your prompt",
    max_tokens=500  # Limit response size
)

# 3. Don't store large responses in memory
# Instead, process and discard
for chunk in client.chat("Long prompt", stream=True):
    # Process each chunk and discard
    process_chunk(chunk)
    # Don't accumulate in memory

# 4. Process large lists in batches
prompts = ["Q1", "Q2", ...]  # Potentially huge list

batch_size = 10
for i in range(0, len(prompts), batch_size):
    batch = prompts[i:i+batch_size]
    
    for prompt in batch:
        response = client.chat(prompt)
        # Process response
    
    # Clear batch from memory
    del batch
    
    import gc
    gc.collect()  # Force garbage collection
```

---

## FAQ

### Q: Which provider should I use?

**A:** Depends on your needs:

- **Free, no API key:** `Meta`, `GEMINI` (limited)
- **Fast and affordable:** `GROQ` (free tier available)
- **Most capable:** `OpenAI` (GPT-4)
- **Good balance:** `GROQ`, `DeepInfra`
- **Experimental:** `Cohere`, `TogetherAI`

### Q: How do I use multiple providers as fallback?

**A:** Use the `Client` with automatic fallback:

```python
from webscout.client import Client

client = Client()

# Automatically tries providers in order
response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

Or implement manual fallback:

```python
def chat_with_fallback(prompt):
    providers = [
        ("GROQ", lambda: GROQ(api_key="key").chat(prompt)),
        ("OpenAI", lambda: OpenAI(api_key="key").chat(prompt)),
        ("Meta", lambda: Meta().chat(prompt)),
    ]
    
    for name, chat_fn in providers:
        try:
            return chat_fn()
        except Exception as e:
            print(f"{name} failed, trying next...")
    
    raise Exception("All providers failed")
```

### Q: How do I save API keys securely?

**A:** Never hardcode API keys:

```python
# ❌ Bad - hardcoded keys
client = OpenAI(api_key="sk-1234567890")

# ✓ Good - environment variables
import os
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# ✓ Good - .env file
from dotenv import load_dotenv
load_dotenv()  # Load from .env file
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# ✓ Good - configuration file
import json
with open("config.json") as f:
    config = json.load(f)
    api_key = config.get("openai_api_key")
client = OpenAI(api_key=api_key)
```

### Q: How do I use Webscout with asyncio?

**A:** Webscout is synchronous, but you can use `asyncio` with `run_in_executor`:

```python
import asyncio
from webscout import GROQ

async def async_chat(prompt):
    loop = asyncio.get_event_loop()
    client = GROQ(api_key="key")
    # Run blocking call in thread pool
    return await loop.run_in_executor(None, client.chat, prompt)

# Use it
response = await async_chat("Hello")
```

### Q: How do I handle special characters in prompts?

**A:** They're handled automatically, but you can check encoding:

```python
prompt = "你好 مرحبا שלום"  # Multiple languages

client = GROQ(api_key="key")
response = client.chat(prompt)
print(response)  # Works fine

# For edge cases, explicitly encode
prompt = "Special chars: ñ, ü, é"
prompt_encoded = prompt.encode('utf-8').decode('utf-8')
response = client.chat(prompt_encoded)
```

### Q: How do I report a bug?

**A:**

1. Check the [GitHub Issues](https://github.com/OEvortex/Webscout/issues)
2. Create a minimal reproducible example:

```python
from webscout import GROQ

client = GROQ(api_key="your-key")
response = client.chat("Simple test")
print(response)  # Expected vs actual output
```

3. Include:
   - Python version: `python --version`
   - Webscout version: `pip show webscout`
   - Full error traceback
   - Steps to reproduce

---

## Still Having Issues?

- **Documentation:** [docs/README.md](README.md)
- **API Reference:** [docs/api-reference.md](api-reference.md)
- **Examples:** [docs/examples/](examples/README.md)
- **GitHub Issues:** https://github.com/OEvortex/Webscout/issues
- **Telegram Group:** https://t.me/OEvortexAI
