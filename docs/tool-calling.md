# Tool Calling

> **Last updated:** 2026-03-30
> **Status:** Current & maintained
> **Target audience:** Developers building agentic AI applications

## Quick Navigation

- [Overview](#overview)
- [Creating Tools](#creating-tools)
- [Registering Tools](#registering-tools)
- [Using Tools in Chat](#using-tools-in-chat)
- [How It Works Internally](#how-it-works-internally)
- [Tool Definition Reference](#tool-definition-reference)
- [Examples](#examples)

---

## Overview

Webscout provides a built-in tool calling system that lets any provider invoke
Python functions during a conversation. The base `Provider` class handles the
entire loop automatically — you define tools, pass them to the provider, and the
model decides when to call them.

**Key concepts:**

- **`Tool`** — a dataclass that wraps a name, description, parameters, and an
  optional callable implementation.
- **`register_tools()`** — stores tools on the provider instance so the
  base class can find them.
- **`chat(tools=[...])`** — the main entry point. When tools are present the
  base class runs an automatic tool-calling loop (inject definitions into the
  prompt, parse `<invoke>` blocks, execute tools, feed `<tool_result>` back).

---

## Creating Tools

Import `Tool` from `webscout.AIbase` and create instances with a name,
description, parameter schema, and an optional implementation function.

```python
from webscout.AIbase import Tool

# 1. Define the Python function that does the work
def get_weather(city: str, unit: str = "celsius") -> str:
    """Fetch current weather (stub)."""
    return f"Weather in {city}: 22 degrees {unit[0].upper()}, sunny"

# 2. Wrap it in a Tool
weather_tool = Tool(
    name="get_weather",
    description="Get the current weather for a given city.",
    parameters={
        "city": {
            "type": "string",
            "description": "The city to look up weather for.",
        },
        "unit": {
            "type": "string",
            "description": "Temperature unit: 'celsius' or 'fahrenheit'.",
        },
    },
    required_params=["city"],          # only city is mandatory
    implementation=get_weather,         # callable that executes the tool
)
```

### Tool with no implementation

If you omit `implementation`, calling `execute()` returns a placeholder string.
This is useful when you want the model to *describe* what it would do without
actually executing.

```python
search_tool = Tool(
    name="web_search",
    description="Search the web for a query.",
    parameters={
        "query": {"type": "string", "description": "Search query."},
    },
)
# tool.execute({"query": "python"}) -> "Tool 'web_search' does not have an implementation."
```

---

## Registering Tools

### Option A — at init time (recommended)

Every Webscout provider accepts a `tools` parameter in its constructor. The
tools are registered automatically.

```python
from webscout.Provider.Apriel import Apriel
from webscout.AIbase import Tool

def add(a: int, b: int) -> int:
    return a + b

calculator = Tool(
    name="add",
    description="Add two numbers.",
    parameters={
        "a": {"type": "integer", "description": "First number."},
        "b": {"type": "integer", "description": "Second number."},
    },
    implementation=add,
)

ai = Apriel(tools=[calculator])   # tools are registered here
```

### Option B — call `register_tools()` manually

```python
ai = Apriel()
ai.register_tools([calculator])
```

Both approaches populate `ai.available_tools`, a `dict[str, Tool]` that the
base class uses during the tool-calling loop.

---

## Using Tools in Chat

Once tools are registered you can call `chat()` normally. The base class
detects the tools and runs the loop automatically.

```python
from webscout.Provider.Apriel import Apriel
from webscout.AIbase import Tool

def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny, 25C"

weather_tool = Tool(
    name="get_weather",
    description="Get current weather for a city.",
    parameters={
        "city": {"type": "string", "description": "City name."},
    },
    implementation=get_weather,
)

ai = Apriel(tools=[weather_tool])

# The model will decide whether to call get_weather
response = ai.chat("What is the weather in London?")
print(response)
```

### Passing tools per-request

You can also pass tools directly to `chat()` without registering them at
init time:

```python
ai = Apriel()
response = ai.chat(
    "What is the weather in Paris?",
    tools=[weather_tool],
)
```

### Controlling the loop

```python
response = ai.chat(
    "What is the weather?",
    tools=[weather_tool],
    max_tool_rounds=3,      # max iterations (default: 5)
)
```

> **Note:** `stream=True` is silently ignored when tools are present because
> the loop needs to inspect the full response before deciding whether to
> continue.

---

## How It Works Internally

The automatic tool-calling loop in `Provider.chat()` follows these steps:

```
┌──────────────────────────────────────────────────────┐
│  1. Format tool definitions as an XML instruction     │
│     block and inject it into the prompt.              │
│                                                       │
│  2. Call provider.ask() with the enriched prompt.     │
│                                                       │
│  3. Parse the response for <invoke> blocks.           │
│                                                       │
│  4. If no <invoke> found → return response as final.  │
│                                                       │
│  5. Execute matching tools via Tool.execute().        │
│                                                       │
│  6. Format results as <tool_result> XML blocks.       │
│                                                       │
│  7. Append results to the conversation prompt.        │
│                                                       │
│  8. Go to step 2 (up to max_tool_rounds).             │
└──────────────────────────────────────────────────────┘
```

### XML format the model uses

**Tool invocation** (model output):

```xml
<invoke>
  <tool_name>get_weather</tool_name>
  <parameters>{"city": "London"}</parameters>
</invoke>
```

**Tool result** (fed back to model):

```xml
<tool_result>
  <tool_name>get_weather</tool_name>
  <result>Weather in London: Sunny, 25C</result>
</tool_result>
```

The model sees these in its conversation context and can chain multiple tool
calls before producing a final text answer.

---

## Tool Definition Reference

### `Tool` dataclass

| Field              | Type                                | Required | Description                                           |
| ------------------ | ----------------------------------- | -------- | ----------------------------------------------------- |
| `name`             | `str`                               | Yes      | Unique function name the model will invoke.           |
| `description`      | `str`                               | Yes      | What the tool does.                                   |
| `parameters`       | `Dict[str, Dict[str, Any]]`         | No       | Parameter schema (name → info dict). Default: `{}`.   |
| `required_params`  | `Optional[List[str]]`               | No       | Required parameter names. Default: all parameters.    |
| `implementation`   | `Optional[Callable[..., Any]]`      | No       | Python function that executes the tool.               |

### Parameter schema format

Each entry in `parameters` is a dict with at least `type` and `description`:

```python
{
    "city": {
        "type": "string",
        "description": "City name.",
    },
    "unit": {
        "type": "string",
        "description": "Temperature unit.",
        "enum": ["celsius", "fahrenheit"],   # optional constraint
    },
}
```

### `Tool` methods

| Method      | Signature                          | Returns          |
| ----------- | ---------------------------------- | ---------------- |
| `to_dict()` | `() -> Dict[str, Any]`             | OpenAI-compatible tool definition dict |
| `execute()` | `(arguments: Dict[str, Any]) -> Any` | Result of calling `implementation(**arguments)` |

---

## Examples

### Example 1 — Calculator

```python
from webscout.Provider.llmchat import LLMChat
from webscout.AIbase import Tool

def calculate(expression: str) -> str:
    """Safe calculator using eval (demo only)."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"

calc_tool = Tool(
    name="calculate",
    description="Evaluate a mathematical expression.",
    parameters={
        "expression": {
            "type": "string",
            "description": "Math expression, e.g. '2 + 3 * 4'.",
        },
    },
    implementation=calculate,
)

ai = LLMChat(tools=[calc_tool])
print(ai.chat("What is 142 * 37?"))
```

### Example 2 — Multiple tools

```python
from webscout.Provider.Toolbaz import Toolbaz
from webscout.AIbase import Tool
import datetime

def get_time() -> str:
    return datetime.datetime.now().isoformat()

def get_random_number(min_val: int = 1, max_val: int = 100) -> int:
    import random
    return random.randint(min_val, max_val)

time_tool = Tool(
    name="get_time",
    description="Get the current date and time.",
    parameters={},
    implementation=get_time,
)

random_tool = Tool(
    name="get_random_number",
    description="Generate a random integer in a range.",
    parameters={
        "min_val": {"type": "integer", "description": "Minimum value (inclusive)."},
        "max_val": {"type": "integer", "description": "Maximum value (inclusive)."},
    },
    required_params=[],
    implementation=get_random_number,
)

ai = Toolbaz(tools=[time_tool, random_tool])
print(ai.chat("What time is it? And give me a random number between 1 and 50."))
```

### Example 3 — Web search stub

```python
from webscout.Provider.Ayle import Ayle
from webscout.AIbase import Tool

def web_search(query: str, num_results: int = 3) -> str:
    """Stub that simulates a web search."""
    return f"Found {num_results} results for '{query}': [result links would appear here]"

search_tool = Tool(
    name="web_search",
    description="Search the web and return top results.",
    parameters={
        "query": {"type": "string", "description": "The search query."},
        "num_results": {
            "type": "integer",
            "description": "Number of results to return.",
        },
    },
    required_params=["query"],
    implementation=web_search,
)

ai = Ayle(tools=[search_tool])
print(ai.chat("Search for the latest news about Python 3.14"))
```

### Example 4 — Streaming with tool results

When tools are registered but the model doesn't call them, streaming works
normally:

```python
ai = Ayle(tools=[search_tool])

# If the model answers directly (no tool call), streaming works
for chunk in ai.chat("Tell me a joke", stream=True):
    print(chunk, end="")
```


