# Basic Chat Examples

> **Last updated:** 2026-01-24  
> **Level:** Beginner  
> **Time to learn:** 5 minutes

Simple question-answer patterns with Webscout providers.

---

## Table of Contents

1. [Simplest Example](#simplest-example)
2. [Different Providers](#different-providers)
3. [Customizing Responses](#customizing-responses)
4. [Saving Conversations](#saving-conversations)
5. [Common Issues](#common-issues)

---

## Simplest Example

### No API Key Needed

```python
from webscout import Meta

# Initialize the provider
ai = Meta()

# Ask a question
response = ai.chat("What is artificial intelligence?")

# Print the response
print(response)
```

**Output:**
```
Artificial intelligence (AI) refers to computer systems designed to 
perform tasks that typically require human intelligence. These tasks 
include learning, reasoning, problem-solving, language understanding, 
and visual perception...
```

### With an API Key

```python
from webscout import OpenAI

# Initialize with your API key
client = OpenAI(api_key="sk-your-openai-api-key-here")

# Ask a question
response = client.chat("Explain machine learning simply")

# Print the response
print(response)
```

---

## Different Providers

### Provider 1: GROQ (Fast & Free Tier)

```python
from webscout import GROQ

# Initialize - get key from https://console.groq.com/keys
client = GROQ(api_key="gsk_your-groq-api-key-here")

# Ask a question
questions = [
    "What is Python?",
    "How does machine learning work?",
    "Explain quantum computing",
]

for question in questions:
    response = client.chat(question)
    print(f"Q: {question}")
    print(f"A: {response[:100]}...\n")
```

### Provider 2: Google Gemini

```python
from webscout import GEMINI

# Initialize - get key from https://ai.google.dev/
client = GEMINI(api_key="your-gemini-api-key-here")

# Ask a question
response = client.chat("What are neural networks?")
print(response)
```

### Provider 3: Cohere

```python
from webscout import Cohere

# Initialize - get key from https://dashboard.cohere.com/
client = Cohere(api_key="your-cohere-api-key-here")

# Ask a question
response = client.chat("What is natural language processing?")
print(response)
```

### Provider 4: OpenRouter (Multiple Models)

```python
from webscout import OpenRouter

# Initialize - get key from https://openrouter.ai/
client = OpenRouter(api_key="your-openrouter-api-key-here")

# Ask a question with a specific model
response = client.chat(
    "Explain blockchain technology",
    model="openai/gpt-3.5-turbo"
)
print(response)
```

---

## Customizing Responses

### Control Response Length

```python
from webscout import GROQ

client = GROQ(api_key="your-api-key")

# Short response
short = client.chat(
    "What is AI?",
    max_tokens=50  # Very brief answer
)
print("Short:", short)

# Long response
long = client.chat(
    "Explain AI in detail",
    max_tokens=500  # Comprehensive answer
)
print("Long:", long)
```

### Control Creativity (Temperature)

```python
from webscout import OpenAI

client = OpenAI(api_key="your-api-key")

# Deterministic - same answer every time (for facts)
factual = client.chat(
    "What is the capital of France?",
    temperature=0.0  # 0 = deterministic
)
print("Factual:", factual)

# Creative - diverse answers (for brainstorming)
creative = client.chat(
    "Come up with creative business ideas",
    temperature=2.0  # 2 = very creative
)
print("Creative:", creative)
```

### Use System Prompts

```python
from webscout import Meta

# The library doesn't directly support custom system prompts,
# but you can engineer your prompt:

ai = Meta()

# Engineer the prompt to get desired behavior
system_instruction = "You are a Python expert. Answer all questions about Python."

response = ai.chat(system_instruction + "\n\nHow do I read a file in Python?")
print(response)
```

---

## Saving Conversations

### Save to File

```python
from webscout import GROQ
from datetime import datetime

client = GROQ(api_key="your-api-key")

# List of questions
conversations = [
    ("What is Python?", ""),
    ("How do I install it?", ""),
    ("Give me a simple example", ""),
]

# Get responses and save
for i, (question, _) in enumerate(conversations):
    response = client.chat(question)
    conversations[i] = (question, response)

# Save to text file
filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

with open(filename, "w", encoding="utf-8") as f:
    for question, answer in conversations:
        f.write(f"Q: {question}\n")
        f.write(f"A: {answer}\n")
        f.write("-" * 80 + "\n")

print(f"Conversation saved to {filename}")
```

### Save to JSON

```python
import json
from webscout import Meta

ai = Meta()

# Create conversation
conversation = []

questions = ["Hello!", "How are you?", "What's your name?"]

for question in questions:
    response = ai.chat(question)
    conversation.append({
        "question": question,
        "answer": response
    })

# Save to JSON
with open("conversation.json", "w", encoding="utf-8") as f:
    json.dump(conversation, f, indent=2, ensure_ascii=False)

print("Saved to conversation.json")

# Load and display
with open("conversation.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
    for item in loaded:
        print(f"Q: {item['question']}")
        print(f"A: {item['answer']}\n")
```

---

## Multi-Turn Conversations

### Maintain Context

```python
from webscout import Meta

# Enable conversation mode to maintain context
ai = Meta(is_conversation=True)

# First turn
print("You: My name is Alice")
response1 = ai.chat("My name is Alice")
print(f"AI: {response1}\n")

# Second turn - AI remembers your name
print("You: What is my name?")
response2 = ai.chat("What is my name?")
print(f"AI: {response2}\n")

# The AI should reference "Alice" because context is preserved
```

**Note:** Not all providers support conversation mode. Check your provider's documentation.

---

## Compare Providers

### Find the Best Provider for Your Task

```python
from webscout import Meta, GROQ, OpenAI

# Simulate having different API keys
providers = {
    "Meta": lambda: Meta(),
    "GROQ": lambda: GROQ(api_key="your-groq-key"),
}

question = "What is the best programming language to learn first?"

print(f"Question: {question}\n")
print("=" * 80)

for name, init_provider in providers.items():
    try:
        provider = init_provider()
        response = provider.chat(question)
        
        print(f"\n{name}:")
        print(response[:200] + "...\n")
        
    except Exception as e:
        print(f"\n{name}: Error - {e}\n")
```

---

## Error Handling

### Safe Chat with Error Handling

```python
from webscout import GROQ
from webscout.exceptions import AIProviderError

def safe_chat(question: str, api_key: str) -> str:
    """
    Ask a question with error handling.
    
    Args:
        question: The question to ask
        api_key: API key for GROQ
    
    Returns:
        The response, or error message if it fails
    """
    try:
        client = GROQ(api_key=api_key)
        response = client.chat(question)
        return response
    
    except AIProviderError as e:
        print(f"Provider error: {e}")
        return f"Error: {e}"
    
    except TimeoutError:
        print("Request timed out")
        return "Error: Request timed out. Please try again."
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return f"Error: {e}"

# Use it
result = safe_chat(
    "What is AI?",
    api_key="your-api-key"
)
print(result)
```

---

## Example: Build a Simple Q&A Bot

```python
from webscout import Meta

def main():
    """Simple Q&A bot using Webscout."""
    
    print("=" * 60)
    print("Welcome to Webscout Q&A Bot")
    print("Type 'quit' or 'exit' to stop")
    print("=" * 60)
    
    ai = Meta()
    
    while True:
        # Get user input
        question = input("\nYou: ").strip()
        
        # Check for exit command
        if question.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        # Skip empty input
        if not question:
            print("Please enter a question.")
            continue
        
        # Get response
        try:
            response = ai.chat(question)
            print(f"\nAI: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python bot.py
```

**Sample interaction:**
```
==========================================
Welcome to Webscout Q&A Bot
Type 'quit' or 'exit' to stop
==========================================

You: Hello
AI: Hello! How can I help you today?

You: What is Python?
AI: Python is a high-level, interpreted programming language...

You: quit
Goodbye!
```

---

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'webscout'"

**Fix:**
```bash
pip install -U webscout
```

### Issue: "401 Unauthorized" with API key

**Fix:** Check your API key:
```python
# Make sure there are no extra spaces
api_key = "gsk_your_key_here"  # ✓ Good

# Not
api_key = "gsk_your_key_here " # ✗ Bad (trailing space)
```

### Issue: No response or empty response

**Fix:**
```python
# Make sure you're using the right method
response = ai.chat("question")  # ✓ chat()
response = ai.Chat("question")  # ✗ Wrong method name (case-sensitive)
```

---

## Next Steps

- Learn about [Streaming Responses](streaming-responses.md)
- Explore [Error Handling](error-handling.md)
- Read the [API Reference](../api-reference.md)

---

## See Also

- [Getting Started](../getting-started.md)
- [API Reference](../api-reference.md)
- [All Examples](README.md)
