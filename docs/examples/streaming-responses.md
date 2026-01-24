# Streaming Responses

> **Last updated:** 2026-01-24  
> **Level:** Beginner  
> **Time to learn:** 5 minutes

Handle long responses efficiently with streaming.

---

## What is Streaming?

Streaming allows you to receive responses word-by-word or chunk-by-chunk instead of waiting for the entire response:

```
Non-streaming: WAIT... WAIT... [Complete response all at once]
Streaming:     Word → by → word → as → it → arrives
```

**Benefits:**
- Better user experience (shows progress)
- Lower latency (start reading faster)
- Smaller memory usage (don't store entire response)
- Works well for long responses

---

## Table of Contents

1. [Basic Streaming](#basic-streaming)
2. [Streaming with Different Providers](#streaming-with-different-providers)
3. [Processing Streamed Data](#processing-streamed-data)
4. [Saving Streamed Responses](#saving-streamed-responses)
5. [Troubleshooting](#troubleshooting)

---

## Basic Streaming

### Simple Streaming Example

```python
from webscout import GROQ

client = GROQ(api_key="your-groq-api-key")

# Enable streaming with stream=True
print("AI Response:")
print("-" * 40)

for chunk in client.chat("Write a short poem about Python", stream=True):
    print(chunk, end="", flush=True)

print()  # Newline at end
print("-" * 40)
```

**Output (real-time):**
```
AI Response:
----------------------------------------
Python is a language so fine,
With syntax that's easy, by design.
From scripts to data, it can do,
Libraries aplenty to choose from too.
----------------------------------------
```

### Streaming vs Non-Streaming

```python
from webscout import GROQ
import time

client = GROQ(api_key="your-api-key")

print("1. WITHOUT STREAMING (waits for complete response)")
print("-" * 50)
start = time.time()
response = client.chat("Write a 100-word essay on AI")
elapsed = time.time() - start
print(response[:100] + "...")
print(f"Time: {elapsed:.1f}s\n")

print("2. WITH STREAMING (starts immediately)")
print("-" * 50)
start = time.time()
for chunk in client.chat("Write a 100-word essay on AI", stream=True):
    print(chunk, end="", flush=True)
elapsed = time.time() - start
print(f"\nTime: {elapsed:.1f}s")
```

---

## Streaming with Different Providers

### GROQ Streaming

```python
from webscout import GROQ

client = GROQ(api_key="your-groq-api-key")

for chunk in client.chat("Hello, write something nice", stream=True):
    print(chunk, end="", flush=True)
print()
```

### OpenAI Streaming

```python
from webscout import OpenAI

client = OpenAI(api_key="sk-your-openai-api-key")

for chunk in client.chat("Write a story", stream=True):
    print(chunk, end="", flush=True)
print()
```

### Check if Streaming is Supported

```python
from webscout import Meta, GROQ
import types

def check_streaming(provider, prompt: str):
    """Check if a provider supports streaming."""
    
    response = provider.chat(prompt, stream=True)
    
    if isinstance(response, types.GeneratorType):
        print("✓ Streaming supported")
        # Consume the generator
        list(response)
    else:
        print("✗ Streaming not supported (got direct response)")

# Test
check_streaming(Meta(), "Hello")
check_streaming(GROQ(api_key="key"), "Hello")
```

---

## Processing Streamed Data

### Collect Into a String

```python
from webscout import GROQ

client = GROQ(api_key="your-api-key")

# Collect all chunks into one string
full_response = ""
for chunk in client.chat("Write a poem", stream=True):
    full_response += chunk

print(f"Full response ({len(full_response)} chars):")
print(full_response)
```

### Count Words in Real-Time

```python
from webscout import GROQ

client = GROQ(api_key="your-api-key")

word_count = 0
for chunk in client.chat("Write an essay on machine learning", stream=True):
    word_count += len(chunk.split())
    print(chunk, end="", flush=True)

print(f"\n\nTotal words: {word_count}")
```

### Collect Words Into a List

```python
from webscout import GROQ

client = GROQ(api_key="your-api-key")

words = []
for chunk in client.chat("Count this", stream=True):
    words.extend(chunk.split())
    print(chunk, end="", flush=True)

print(f"\n\nWord list: {words}")
print(f"Total: {len(words)} words")
```

### Process and Filter Chunks

```python
from webscout import GROQ

client = GROQ(api_key="your-api-key")

print("Filtering chunks (only showing those with 'AI'):\n")

for chunk in client.chat("Discuss artificial intelligence", stream=True):
    # Only show chunks containing 'AI'
    if "AI" in chunk or "intelligence" in chunk:
        print(f"[{chunk}]", end="", flush=True)
    else:
        print(chunk, end="", flush=True)

print("\n")
```

---

## Saving Streamed Responses

### Save to File While Streaming

```python
from webscout import GROQ
from datetime import datetime

client = GROQ(api_key="your-api-key")

# Create filename
filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

print(f"Streaming to {filename}...\n")

# Stream and save simultaneously
with open(filename, "w", encoding="utf-8") as f:
    for chunk in client.chat("Write about the future of technology", stream=True):
        f.write(chunk)
        print(chunk, end="", flush=True)

print(f"\n\nSaved to {filename}")

# Verify file was created
with open(filename, "r") as f:
    content = f.read()
    print(f"File size: {len(content)} bytes")
```

### Save Multiple Streams

```python
from webscout import GROQ
import json
from datetime import datetime

client = GROQ(api_key="your-api-key")

prompts = [
    "What is AI?",
    "Explain machine learning",
    "Define deep learning"
]

# Store all responses
responses = {}

for prompt in prompts:
    print(f"\nProcessing: {prompt}")
    
    # Stream and collect
    full_response = ""
    for chunk in client.chat(prompt, stream=True):
        full_response += chunk
        print(chunk, end="", flush=True)
    
    responses[prompt] = full_response

# Save as JSON
with open("responses.json", "w", encoding="utf-8") as f:
    json.dump(responses, f, indent=2, ensure_ascii=False)

print("\n\nAll responses saved to responses.json")
```

---

## Streaming with Error Handling

### Handle Interrupted Streams

```python
from webscout import GROQ

client = GROQ(api_key="your-api-key", timeout=60)

full_response = ""

try:
    print("Streaming response...")
    for chunk in client.chat("Write a long story", stream=True):
        full_response += chunk
        print(chunk, end="", flush=True)
    
    print("\n✓ Stream completed successfully")

except TimeoutError:
    print("\n⚠ Stream interrupted by timeout")
    print(f"Partial response ({len(full_response)} chars received):")
    print(full_response)

except Exception as e:
    print(f"\n✗ Error during streaming: {e}")
    print(f"Partial response received: {full_response[:100]}...")
```

### Timeout Per Chunk

```python
from webscout import GROQ
import time

client = GROQ(api_key="your-api-key")

chunk_timeout = 10  # seconds per chunk
last_chunk_time = time.time()
times_out = False

try:
    for chunk in client.chat("Your prompt", stream=True):
        current_time = time.time()
        
        if current_time - last_chunk_time > chunk_timeout:
            print(f"\n⚠ No chunk received for {chunk_timeout}s - giving up")
            times_out = True
            break
        
        last_chunk_time = current_time
        print(chunk, end="", flush=True)

except Exception as e:
    print(f"\nError: {e}")
```

---

## Advanced Streaming Patterns

### Stream with Progress Bar

Requires `tqdm` library:

```bash
pip install tqdm
```

```python
from webscout import GROQ
from tqdm import tqdm
import time

client = GROQ(api_key="your-api-key")

# Collect in background to get length
chunks = []
print("Buffering... ", end="", flush=True)
for chunk in client.chat("Your prompt", stream=True):
    chunks.append(chunk)
print("ready!\n")

# Display with progress bar
with tqdm(total=len(chunks), desc="Displaying") as pbar:
    for chunk in chunks:
        print(chunk, end="", flush=True)
        time.sleep(0.01)  # Simulate reading
        pbar.update(1)

print()
```

### Stream with Highlighting

```python
from webscout import GROQ

client = GROQ(api_key="your-api-key")

print("Streaming response (keywords highlighted):\n")

keywords = ["Python", "AI", "machine learning", "data"]

for chunk in client.chat("Explain Python and AI", stream=True):
    # Highlight keywords
    highlighted = chunk
    for keyword in keywords:
        highlighted = highlighted.replace(
            keyword,
            f"\033[92m{keyword}\033[0m"  # Green highlight
        )
    
    print(highlighted, end="", flush=True)

print()
```

### Stream Multiple Responses in Parallel

```python
from webscout import GROQ
from threading import Thread

client = GROQ(api_key="your-api-key")

prompts = [
    "What is Python?",
    "Explain machine learning",
]

def stream_response(prompt: str, output_list: list):
    """Stream a response to a list."""
    response = ""
    for chunk in client.chat(prompt, stream=True):
        response += chunk
    output_list.append(response)

# Run both in parallel
responses = [None, None]
threads = []

for i, prompt in enumerate(prompts):
    t = Thread(target=lambda p=prompt, o=responses, idx=i: 
               o.append(stream_response(p, [])) or o.pop(idx))
    threads.append(t)
    t.start()

# Wait for completion
for t in threads:
    t.join()

# Print results
for prompt, response in zip(prompts, responses):
    if response:
        print(f"Q: {prompt}")
        print(f"A: {response[:100]}...\n")
```

---

## Real-World Example: Chatbot with Streaming

```python
from webscout import GROQ
import sys

def streaming_chatbot():
    """Interactive chatbot that streams responses."""
    
    client = GROQ(api_key="your-api-key")
    
    print("=" * 60)
    print("Streaming Chatbot")
    print("Type 'quit' to exit")
    print("=" * 60)
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        # Stream response
        print("Bot: ", end="", flush=True)
        try:
            for chunk in client.chat(user_input, stream=True):
                print(chunk, end="", flush=True)
            print()  # Newline
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    streaming_chatbot()
```

---

## Troubleshooting

### "No streaming data received"

**Problem:** Response is not a generator

**Solution:**
```python
import types

response = ai.chat("test", stream=True)

if not isinstance(response, types.GeneratorType):
    print("Not streaming - provider doesn't support it")
    print(f"Got: {type(response)}")
    print(f"Response: {response}")
```

### "Generator is empty" or "No output"

**Problem:** Generator is exhausted or provider returned error

**Solution:**
```python
from webscout import GROQ

client = GROQ(api_key="your-api-key")

# Check if you're iterating correctly
response_gen = client.chat("test", stream=True)
chunks = list(response_gen)

if not chunks:
    print("No chunks received")
else:
    print(f"Received {len(chunks)} chunks")
    for chunk in chunks:
        print(chunk, end="")
```

### "Incomplete response while streaming"

**Problem:** Connection interrupted

**Solution:**
```python
from webscout import GROQ

client = GROQ(api_key="your-api-key", timeout=120)

full_response = ""
try:
    for chunk in client.chat("Long prompt", stream=True):
        full_response += chunk
except Exception as e:
    print(f"Stream interrupted: {e}")
    print(f"Partial response: {full_response}")
```

---

## See Also

- [Basic Chat Examples](basic-chat.md)
- [API Reference](../api-reference.md)
- [Troubleshooting](../troubleshooting.md)

Next: Learn about [Search Queries](search-queries.md)
