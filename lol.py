"""External tool calling like OpenAI — non-native providers."""

import json
import sys

# Try Toolbaz first, fall back to K2Think
try:
    from llm4free.llm.toolbaz import Toolbaz
    client = Toolbaz()
    MODEL = "toolbaz_v4"
    print("Using Toolbaz (toolbaz_v4)")
except Exception:
    from llm4free.llm.k2think import K2Think
    client = K2Think()
    MODEL = "MBZUAI-IFM/K2-Think-v2"
    print("Using K2Think (MBZUAI-IFM/K2-Think-v2)")

from llm4free.llm.base import Tool


# ── 1. Define a tool ──────────────────────────────────────────────────
def get_capital(country: str) -> str:
    capitals = {"france": "Paris", "germany": "Berlin", "japan": "Tokyo"}
    return capitals.get(country.lower(), f"unknown: {country}")

tool = Tool(
    name="get_capital",
    description="Get the capital city of a country",
    parameters={"country": {"type": "string", "description": "Country name"}},
    implementation=get_capital,
)

# ── 2. First call: ask with tools ─────────────────────────────────────
resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
    tools=[tool],
    stream=False,
    timeout=20,
)

msg = resp.choices[0].message

if msg.tool_calls:
    # ── 3. Execute tools manually (just like OpenAI SDK) ──────────────
    print(f"\nModel wants to call: {msg.tool_calls[0].function.name}")
    msgs = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": msg.content, "tool_calls": [t.model_dump() for t in msg.tool_calls]},
    ]
    for tc in msg.tool_calls:
        args = json.loads(tc.function.arguments)
        result = get_capital(**args)
        print(f"  → {tc.function.name}({args}) = {result}")
        msgs.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})

    # ── 4. Second call: feed results back ────────────────────────────
    resp2 = client.chat.completions.create(
        model=MODEL,
        messages=msgs,
        stream=False,
        timeout=20,
    )
    print(f"\nFinal answer: {resp2.choices[0].message.content}")
else:
    print(f"Direct answer: {msg.content}")
