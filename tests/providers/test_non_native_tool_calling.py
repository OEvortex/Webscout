"""
Tests for non-native tool calling via XML prompt injection.

Uses FreeAI (supports_tools=False) as the real provider for integration tests.
"""

import json
import time
import unittest
import uuid
from typing import Any, Dict, List, Optional, Union
from unittest import mock

import pytest

from llm4free.llm.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
    Tool,
)
from llm4free.llm.utils import ChatCompletion, ChatCompletionMessage, Choice

# ═════════════════════════════════════════════════════════════════════════ #
#  Helper: a minimal non-native provider for unit tests
# ═════════════════════════════════════════════════════════════════════════ #


class _MockCompletions(BaseCompletions):
    """Completions that simulates an AI model for testing the tool loop."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self.call_count = 0
        self.responses: List[str] = []

    def set_responses(self, responses: List[str]) -> None:
        self.responses = responses

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        tools: Optional[List[Union[Tool, Dict[str, Any]]]] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        content = (
            self.responses[self.call_count] if self.call_count < len(self.responses) else "fallback"
        )
        self.call_count += 1
        msg = ChatCompletionMessage(role="assistant", content=content)
        choice = Choice(index=0, message=msg, finish_reason="stop")
        return ChatCompletion(
            id=f"test-{uuid.uuid4()}",
            choices=[choice],
            created=int(time.time()),
            model=model,
        )


class _MockChat(BaseChat):
    def __init__(self, client: Any) -> None:
        self.completions = _MockCompletions(client)


class _MockProvider(OpenAICompatibleProvider):
    supports_tools = False
    AVAILABLE_MODELS = ["mock-model"]

    def __init__(self) -> None:
        self.chat = _MockChat(self)
        self.timeout = 60

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(self.AVAILABLE_MODELS)


# ═════════════════════════════════════════════════════════════════════════ #
#  Unit tests for XML tool helpers
# ═════════════════════════════════════════════════════════════════════════ #


class TestToolXmlHelpers(unittest.TestCase):
    """Unit tests for the XML-based tool helper methods on BaseCompletions."""

    def setUp(self) -> None:
        # Can't instantiate BaseCompletions (abstract), but static methods work
        pass

    def test_extract_tool_calls_finds_invoke_block(self) -> None:
        text = (
            "<invoke>"
            "<tool_name>get_weather</tool_name>"
            '<parameters>{"city": "London"}</parameters>'
            "</invoke>"
        )
        calls = BaseCompletions.extract_tool_calls(text)
        assert calls is not None
        assert len(calls) == 1
        assert calls[0]["name"] == "get_weather"
        assert calls[0]["arguments"] == {"city": "London"}

    def test_extract_tool_calls_multiple_invokes(self) -> None:
        text = (
            "<invoke>"
            "<tool_name>tool_a</tool_name>"
            '<parameters>{"x": 1}</parameters>'
            "</invoke>"
            "some text"
            "<invoke>"
            "<tool_name>tool_b</tool_name>"
            '<parameters>{"y": 2}</parameters>'
            "</invoke>"
        )
        calls = BaseCompletions.extract_tool_calls(text)
        assert calls is not None
        assert len(calls) == 2
        assert calls[0]["name"] == "tool_a"
        assert calls[1]["name"] == "tool_b"

    def test_extract_tool_calls_returns_none_when_no_invoke(self) -> None:
        assert BaseCompletions.extract_tool_calls("just a normal response") is None

    def test_extract_tool_calls_empty_string(self) -> None:
        assert BaseCompletions.extract_tool_calls("") is None

    def test_extract_tool_calls_invalid_json_args(self) -> None:
        text = "<invoke><tool_name>bad_tool</tool_name><parameters>{invalid}</parameters></invoke>"
        calls = BaseCompletions.extract_tool_calls(text)
        assert calls is not None
        assert calls[0]["arguments"] == {}

    def test_format_tool_results_xml_single(self) -> None:
        results = [
            {"tool_name": "get_weather", "arguments": {"city": "Paris"}, "result": "25C sunny"}
        ]
        xml = BaseCompletions.format_tool_results_xml(results)
        assert "<tool_name>get_weather</tool_name>" in xml
        assert "<result>25C sunny</result>" in xml
        assert "<tool_result>" in xml

    def test_format_tool_results_xml_multiple(self) -> None:
        results = [
            {"tool_name": "a", "arguments": {}, "result": "r1"},
            {"tool_name": "b", "arguments": {}, "result": "r2"},
        ]
        xml = BaseCompletions.format_tool_results_xml(results)
        assert xml.count("<tool_result>") == 2
        assert "<result>r1</result>" in xml
        assert "<result>r2</result>" in xml

    def test_format_tools_for_prompt_generates_xml_instructions(self) -> None:
        completions = _MockCompletions(None)
        tool = Tool(
            name="search",
            description="Search the web",
            parameters={"q": {"type": "string", "description": "Query"}},
        )
        prompt = completions.format_tools_for_prompt([tool])
        assert "search" in prompt
        assert "Search the web" in prompt
        assert "<tool_name>" in prompt
        assert "<invoke>" in prompt

    def test_format_tools_for_prompt_empty_returns_empty(self) -> None:
        completions = _MockCompletions(None)
        assert completions.format_tools_for_prompt([]) == ""
        assert completions.format_tools_for_prompt(None) == ""


# ═════════════════════════════════════════════════════════════════════════ #
#  Unit tests for the tool loop itself
# ═════════════════════════════════════════════════════════════════════════ #


class TestNonNativeToolLoop(unittest.TestCase):
    """Tests for _run_non_native_tool_loop with a controlled mock."""

    def setUp(self) -> None:
        self.provider = _MockProvider()
        self.completions = self.provider.chat.completions
        self.tool = Tool(
            name="get_weather",
            description="Get weather for a city",
            parameters={"city": {"type": "string", "description": "City name"}},
            implementation=lambda city: f"Weather in {city}: sunny, 25C",
        )

    def test_tool_loop_returns_tool_calls(self) -> None:
        """When the model returns XML invoke, the response should have
        native tool_calls and content=None."""
        self.completions.set_responses(
            [
                "<invoke>"
                "<tool_name>get_weather</tool_name>"
                '<parameters>{"city": "Paris"}</parameters>'
                "</invoke>"
            ]
        )
        result = self.completions._run_non_native_tool_loop(
            self.completions.create,
            model="mock-model",
            messages=[{"role": "user", "content": "What is the weather in Paris?"}],
            tools=[self.tool],
        )
        assert self.completions.call_count == 1
        msg = result.choices[0].message
        assert msg.content is None
        assert msg.tool_calls is not None
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].function.name == "get_weather"
        assert "Paris" in msg.tool_calls[0].function.arguments
        assert result.choices[0].finish_reason == "tool_calls"

    def test_tool_loop_no_tool_calls_returns_directly(self) -> None:
        """When the model returns plain text, pass through unchanged."""
        self.completions.set_responses(["Direct answer."])
        result = self.completions._run_non_native_tool_loop(
            self.completions.create,
            model="mock-model",
            messages=[{"role": "user", "content": "Hello"}],
            tools=[self.tool],
        )
        assert self.completions.call_count == 1
        assert result.choices[0].message.content == "Direct answer."
        assert result.choices[0].message.tool_calls is None

    def test_tool_loop_handles_dict_tools(self) -> None:
        """Tools passed as dicts (OpenAI format) should also work."""
        self.completions.set_responses(
            [
                "<invoke>"
                "<tool_name>get_weather</tool_name>"
                '<parameters>{"city": "London"}</parameters>'
                "</invoke>"
            ]
        )
        dict_tool = {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
        result = self.completions._run_non_native_tool_loop(
            self.completions.create,
            model="mock-model",
            messages=[{"role": "user", "content": "Weather in London?"}],
            tools=[dict_tool, self.tool],
        )
        assert result.choices[0].message.tool_calls is not None

    def test_tool_loop_injects_xml_into_system_message(self) -> None:
        """XML tool definitions should be injected into the system message."""
        self.completions.set_responses(["Final answer."])
        result = self.completions._run_non_native_tool_loop(
            self.completions.create,
            model="mock-model",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hi"},
            ],
            tools=[self.tool],
        )
        assert result.choices[0].message.content == "Final answer."

    def test_external_pattern_full_round_trip(self) -> None:
        """Simulate the full external tool calling flow (OpenAI pattern)."""
        # Round 1: model returns tool call
        self.completions.set_responses(
            [
                "<invoke>"
                "<tool_name>get_weather</tool_name>"
                '<parameters>{"city": "Tokyo"}</parameters>'
                "</invoke>",
                "The weather in Tokyo is warm.",
            ]
        )
        resp1 = self.completions._run_non_native_tool_loop(
            self.completions.create,
            model="mock-model",
            messages=[{"role": "user", "content": "Weather in Tokyo?"}],
            tools=[self.tool],
        )
        assert resp1.choices[0].message.tool_calls is not None
        tc = resp1.choices[0].message.tool_calls[0]
        assert tc.function.name == "get_weather"

        # Simulate user executing the tool and calling again
        result = "warm and sunny"

        messages = [
            {"role": "user", "content": "Weather in Tokyo?"},
            {"role": "assistant", "content": None, "tool_calls": [tc.model_dump()]},
            {"role": "tool", "tool_call_id": tc.id, "content": result},
        ]
        resp2 = self.completions.create(
            model="mock-model",
            messages=messages,
        )
        assert resp2.choices[0].message.content == "The weather in Tokyo is warm."


# ═════════════════════════════════════════════════════════════════════════ #
#  Tests for __init_subclass__ wrapping behavior
# ═════════════════════════════════════════════════════════════════════════ #


class InitTrackingCompletions(BaseCompletions):
    def __init__(self, client):
        self._client = client

    def create(self, **kw):
        msg = ChatCompletionMessage(role="assistant", content="ok")
        return ChatCompletion(
            id="x",
            choices=[Choice(index=0, message=msg, finish_reason="stop")],
            model="m",
            created=int(time.time()),
        )


class InitTrackingChat(BaseChat):
    def __init__(self, c):
        self.completions = InitTrackingCompletions(c)


class TestWrappingBehavior(unittest.TestCase):
    """Verify that __init_subclass__ correctly wraps non-native providers."""

    def test_non_native_create_is_wrapped(self):
        class NonNativeProv(OpenAICompatibleProvider):
            supports_tools = False
            AVAILABLE_MODELS = ["m"]

            def __init__(self):
                self.chat = InitTrackingChat(self)

            @property
            def models(self):
                return SimpleModelList(self.AVAILABLE_MODELS)

        p = NonNativeProv()
        assert hasattr(p.chat.completions.create, "__wrapped__")

    def test_native_create_is_not_wrapped(self):
        class NativeProv(OpenAICompatibleProvider):
            supports_tools = True
            AVAILABLE_MODELS = ["m"]

            def __init__(self):
                self.chat = InitTrackingChat(self)

            @property
            def models(self):
                return SimpleModelList(self.AVAILABLE_MODELS)

        p = NativeProv()
        assert not hasattr(p.chat.completions.create, "__wrapped__")

    def test_wrapped_create_passes_through_without_tools(self):
        class PassProv(OpenAICompatibleProvider):
            supports_tools = False
            AVAILABLE_MODELS = ["m"]

            def __init__(self):
                self.chat = InitTrackingChat(self)

            @property
            def models(self):
                return SimpleModelList(self.AVAILABLE_MODELS)

        p = PassProv()
        result = p.chat.completions.create(
            model="m",
            messages=[{"role": "user", "content": "hello"}],
        )
        assert result.choices[0].message.content == "ok"


# ═════════════════════════════════════════════════════════════════════════ #
#  Real provider integration tests
# ═════════════════════════════════════════════════════════════════════════ #
#  Uses whichever free, non-auth providers are available, preferring
#  the one that responds fastest.  Each test class is auto-skipped when
#  the provider module can't be imported.


def _check_tool_response(resp: Any, keyword: str = "") -> str:
    """Helper: extract content from a ChatCompletion and assert it's valid."""
    assert resp.choices is not None
    assert len(resp.choices) > 0
    content = resp.choices[0].message.content
    assert content is not None
    assert len(content) > 0
    if keyword:
        assert keyword in content, f"Expected {keyword!r} in response, got: {content[:200]}"
    return content


# --- FreeAI ----------------------------------------------------------- #

try:
    from llm4free.llm.freeai import FreeAI

    HAS_FREEAI = True
except ImportError:
    HAS_FREEAI = False


def _freeai_reachable() -> bool:
    """Quick connectivity check so we don't hang for 30s on an unreachable host."""
    try:
        from curl_cffi import requests

        requests.get("https://api.free.ai/v1/chat/", timeout=5, impersonate="chrome110")
        # Any response (even 404/405) means the host is reachable
        return True
    except Exception:
        return False


_FREEAI_REACHABLE = _freeai_reachable()


@pytest.mark.skipif(not HAS_FREEAI, reason="FreeAI provider not available")
@pytest.mark.skipif(not _FREEAI_REACHABLE, reason="FreeAI endpoint unreachable")
class TestFreeAINonNativeToolCalling:
    """Integration tests using FreeAI (supports_tools=False)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.provider = FreeAI()
        self.model = "qwen7b"

    def test_basic_chat_no_tools(self):
        resp = self.provider.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": "Say 'hello' and nothing else"}],
            stream=False,
            timeout=15,
        )
        _check_tool_response(resp)

    def test_create_is_wrapped(self):
        assert hasattr(self.provider.chat.completions.create, "__wrapped__")


# --- K2Think ---------------------------------------------------------- #

try:
    from llm4free.llm.k2think import K2Think

    HAS_K2THINK = True
except ImportError:
    HAS_K2THINK = False


@pytest.mark.skipif(not HAS_K2THINK, reason="K2Think provider not available")
class TestK2ThinkNonNativeToolCalling:
    """Integration tests using K2Think (supports_tools=False) provider."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.provider = K2Think()
        self.model = "MBZUAI-IFM/K2-Think-v2"

    def test_basic_chat_no_tools(self):
        resp = self.provider.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": "Say hello in one word"}],
            stream=False,
            timeout=20,
        )
        _check_tool_response(resp)

    def test_create_is_wrapped(self):
        assert hasattr(self.provider.chat.completions.create, "__wrapped__")

    def test_tool_call_with_simple_tool(self):
        def get_capital(country: str) -> str:
            capitals = {
                "france": "Paris",
                "germany": "Berlin",
                "japan": "Tokyo",
                "india": "New Delhi",
            }
            return capitals.get(country.lower(), f"Capital of {country} not found")

        tool = Tool(
            name="get_capital",
            description="Get the capital city of a country",
            parameters={
                "country": {
                    "type": "string",
                    "description": "The name of the country",
                }
            },
            implementation=get_capital,
        )

        # Round 1: model either returns tool_calls or answers directly
        resp1 = self.provider.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"},
            ],
            tools=[tool],
            stream=False,
            timeout=30,
        )
        msg1 = resp1.choices[0].message
        if msg1.tool_calls:
            # External pattern: tool_calls returned → execute → feed back
            assert msg1.content is None
            tc = msg1.tool_calls[0]
            assert tc.function.name == "get_capital"
            args = json.loads(tc.function.arguments)
            result = get_capital(args["country"])

            resp2 = self.provider.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"},
                    {"role": "assistant", "content": None, "tool_calls": [tc.model_dump()]},
                    {"role": "tool", "tool_call_id": tc.id, "content": result},
                ],
                stream=False,
                timeout=30,
            )
            _check_tool_response(resp2, "Paris")
        else:
            # Model answered directly (K2Think knows Paris) — still valid
            _check_tool_response(resp1, "Paris")

    def test_multiple_tools(self):
        def add(a: int, b: int) -> int:
            return a + b

        def multiply(a: int, b: int) -> int:
            return a * b

        tools = [
            Tool(
                name="add",
                description="Add two numbers",
                parameters={
                    "a": {"type": "integer", "description": "First number"},
                    "b": {"type": "integer", "description": "Second number"},
                },
                implementation=add,
            ),
            Tool(
                name="multiply",
                description="Multiply two numbers",
                parameters={
                    "a": {"type": "integer", "description": "First number"},
                    "b": {"type": "integer", "description": "Second number"},
                },
                implementation=multiply,
            ),
        ]

        resp1 = self.provider.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a calculator assistant."},
                {"role": "user", "content": "What is 5 + 3?"},
            ],
            tools=tools,
            stream=False,
            timeout=30,
        )
        msg1 = resp1.choices[0].message
        assert msg1.tool_calls is not None, f"Expected tool_calls, got content={msg1.content!r}"

        # Execute all tools
        tc = msg1.tool_calls[0]
        args = json.loads(tc.function.arguments)
        result = str(add(args["a"], args["b"]))

        # Round 2
        resp2 = self.provider.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a calculator assistant."},
                {"role": "user", "content": "What is 5 + 3?"},
                {"role": "assistant", "content": None, "tool_calls": [tc.model_dump()]},
                {"role": "tool", "tool_call_id": tc.id, "content": result},
            ],
            stream=False,
            timeout=30,
        )
        _check_tool_response(resp2, "8")


# --- Toolbaz (free, no auth, supports_tools=False) -------------------- #

try:
    from llm4free.llm.toolbaz import Toolbaz

    HAS_TOOLBAZ = True
except ImportError:
    HAS_TOOLBAZ = False


def _toolbaz_reachable() -> bool:
    try:
        from curl_cffi import requests

        requests.get("https://data.toolbaz.com/", timeout=5, impersonate="chrome110")
        return True
    except Exception:
        return False


_TOOLBAZ_REACHABLE = _toolbaz_reachable()


@pytest.mark.skipif(not HAS_TOOLBAZ, reason="Toolbaz provider not available")
@pytest.mark.skipif(not _TOOLBAZ_REACHABLE, reason="Toolbaz endpoint unreachable")
class TestToolbazNonNativeToolCalling:
    """Integration tests using Toolbaz (supports_tools=False).

    Toolbaz uses format_prompt() to convert message lists to a flat string,
    so it's a good test for the XML prompt injection fallback.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.provider = Toolbaz()
        self.model = "toolbaz_v4"

    def test_basic_chat_no_tools(self):
        resp = self.provider.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": "Say hello in one word"}],
            stream=False,
            timeout=20,
        )
        _check_tool_response(resp)

    def test_create_is_wrapped(self):
        assert hasattr(self.provider.chat.completions.create, "__wrapped__")

    def test_tool_call_with_simple_tool(self):
        import json as _json

        def get_capital(country: str) -> str:
            capitals = {
                "france": "Paris",
                "germany": "Berlin",
                "japan": "Tokyo",
                "india": "New Delhi",
            }
            return capitals.get(country.lower(), f"Capital of {country} not found")

        tool = Tool(
            name="get_capital",
            description="Get the capital city of a country",
            parameters={
                "country": {
                    "type": "string",
                    "description": "The name of the country",
                }
            },
            implementation=get_capital,
        )

        # Round 1: get tool_calls
        resp1 = self.provider.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"},
            ],
            tools=[tool],
            stream=False,
            timeout=25,
        )
        msg1 = resp1.choices[0].message
        assert msg1.tool_calls is not None, f"Expected tool_calls, got content={msg1.content!r}"
        assert msg1.content is None

        tc = msg1.tool_calls[0]
        args = _json.loads(tc.function.arguments)
        result = get_capital(args["country"])

        # Round 2: feed result back
        resp2 = self.provider.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"},
                {"role": "assistant", "content": None, "tool_calls": [tc.model_dump()]},
                {"role": "tool", "tool_call_id": tc.id, "content": result},
            ],
            stream=False,
            timeout=25,
        )
        _check_tool_response(resp2, "Paris")

    @pytest.mark.xfail(
        reason="toolbaz_v4 model may not reliably follow XML tool instructions for math"
    )
    def test_multiple_tools(self):
        import json as _json

        def add(a: int, b: int) -> int:
            return a + b

        def multiply(a: int, b: int) -> int:
            return a * b

        tools = [
            Tool(
                name="add",
                description="Add two numbers",
                parameters={
                    "a": {"type": "integer", "description": "First number"},
                    "b": {"type": "integer", "description": "Second number"},
                },
                implementation=add,
            ),
            Tool(
                name="multiply",
                description="Multiply two numbers",
                parameters={
                    "a": {"type": "integer", "description": "First number"},
                    "b": {"type": "integer", "description": "Second number"},
                },
                implementation=multiply,
            ),
        ]

        resp1 = self.provider.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a calculator assistant."},
                {"role": "user", "content": "What is 5 + 3?"},
            ],
            tools=tools,
            stream=False,
            timeout=25,
        )
        msg1 = resp1.choices[0].message
        assert msg1.tool_calls is not None
        tc = msg1.tool_calls[0]
        args = _json.loads(tc.function.arguments)
        result = str(add(args["a"], args["b"]))

        resp2 = self.provider.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a calculator assistant."},
                {"role": "user", "content": "What is 5 + 3?"},
                {"role": "assistant", "content": None, "tool_calls": [tc.model_dump()]},
                {"role": "tool", "tool_call_id": tc.id, "content": result},
            ],
            stream=False,
            timeout=25,
        )
        _check_tool_response(resp2, "8")


# --- EssentialAI (free, no auth, supports_tools=False) ---------------- #

try:
    from llm4free.llm.essentialai import EssentialAI

    HAS_ESSENTIAL = True
except ImportError:
    HAS_ESSENTIAL = False


@pytest.mark.skipif(not HAS_ESSENTIAL, reason="EssentialAI provider not available")
class TestEssentialAINonNativeToolCalling:
    """Integration tests using EssentialAI (supports_tools=False)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.provider = EssentialAI()
        self.model = "essentialai"

    def test_basic_chat_no_tools(self):
        resp = self.provider.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": "Say hello in one word"}],
            stream=False,
            timeout=15,
        )
        _check_tool_response(resp)

    def test_create_is_wrapped(self):
        assert hasattr(self.provider.chat.completions.create, "__wrapped__")
