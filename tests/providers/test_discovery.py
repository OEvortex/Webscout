import inspect
import unittest

from llm4free import llm
from llm4free.AIbase import Provider as BaseProvider
from llm4free.llm.base import OpenAICompatibleProvider


def _is_provider_class(obj: object) -> bool:
    """Return True if obj is a concrete provider class (not a base/utility)."""
    return (
        inspect.isclass(obj)
        and issubclass(obj, BaseProvider)
        and obj is not BaseProvider
        and not obj.__name__.startswith(("Base", "_"))
    )


# All items in __all__ that are NOT provider classes
NON_PROVIDER_NAMES = {
    "OpenAICompatibleProvider", "SimpleModelList", "BaseChat",
    "BaseCompletions", "Tool", "ToolDefinition", "FunctionParameters",
    "FunctionDefinition", "ChatCompletion", "ChatCompletionChunk",
    "Choice", "ChoiceDelta", "ChatCompletionMessage", "CompletionUsage",
    "ToolCall", "ToolFunction", "FunctionCall", "ToolCallType",
    "ModelData", "ModelList", "format_prompt", "get_system_prompt",
    "get_last_user_message", "count_tokens", "ChatGPTReversed",
}


class TestProviderDiscovery(unittest.TestCase):
    def test_all_providers_importable(self):
        """Verify that all providers listed in __all__ can be imported."""
        provider_all = getattr(llm, "__all__", [])
        for name in provider_all:
            with self.subTest(provider=name):
                obj = getattr(llm, name)
                self.assertTrue(
                    inspect.isclass(obj) or callable(obj),
                    f"{name} is not importable",
                )

    def test_provider_classes_have_required_interface(self):
        """Verify provider classes expose a chat.completions.create interface."""
        provider_all = getattr(llm, "__all__", [])
        for name in provider_all:
            if name in NON_PROVIDER_NAMES:
                continue
            obj = getattr(llm, name)
            if not inspect.isclass(obj):
                continue
            with self.subTest(provider=name):
                # Provider classes should either inherit from OpenAICompatibleProvider
                # or from BaseProvider (AIbase). Both are valid.
                is_oai = issubclass(obj, OpenAICompatibleProvider)
                is_base = issubclass(obj, BaseProvider)
                self.assertTrue(
                    is_oai or is_base,
                    f"{name} does not inherit from OpenAICompatibleProvider or BaseProvider",
                )

    def test_provider_classes_have_chat(self):
        """Verify that provider classes have 'chat' or 'models' attributes."""
        provider_all = getattr(llm, "__all__", [])
        for name in provider_all:
            if name in NON_PROVIDER_NAMES:
                continue
            obj = getattr(llm, name)
            if not inspect.isclass(obj):
                continue
            with self.subTest(provider=name):
                self.assertTrue(
                    hasattr(obj, "chat") or hasattr(obj, "models"),
                    f"Provider {name} lacks 'chat' or 'models' attribute",
                )

    def test_no_duplicate_provider_names(self):
        """Ensure no two provider classes share the same name in __all__."""
        provider_all = getattr(llm, "__all__", [])
        seen = set()
        dupes = set()
        for name in provider_all:
            if name in seen:
                dupes.add(name)
            seen.add(name)
        self.assertEqual(dupes, set(), f"Duplicate names in __all__: {dupes}")


if __name__ == "__main__":
    unittest.main()
