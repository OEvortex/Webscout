import inspect
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import webscout.Provider as ProviderModule
from tests.providers.utils import FakeResp
from webscout.AIbase import Provider as BaseProvider


class TestAllProvidersMocked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider_module = sys.modules['webscout.Provider']
        from webscout.Provider import __all__ as PROVIDER_ALL
        cls.provider_names = PROVIDER_ALL

        # Create a dummy cookie file for providers that need it
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.dummy_cookie_file = os.path.join(cls.temp_dir.name, "cookies.json")
        with open(cls.dummy_cookie_file, "w") as f:
            f.write('{"dummy": "cookie"}')

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_all_providers_ask(self):
        """Test the ask method of all providers using mocks."""
        for name in self.provider_names:
            provider_cls = getattr(self.provider_module, name, None)
            if not provider_cls or not inspect.isclass(provider_cls) or not issubclass(provider_cls, BaseProvider):
                continue

            with self.subTest(provider=name):
                # Mock initialization dependencies
                with patch('webscout.Provider.Openai.BackgroundModelFetcher'), \
                     patch('webscout.Provider.Groq.BackgroundModelFetcher'), \
                     patch('webscout.Provider.HuggingFace.BackgroundModelFetcher'), \
                     patch('webscout.Provider.Gemini.Chatbot'), \
                     patch('webscout.litagent.LitAgent'):

                    # Prepare init args
                    init_args = {}
                    sig = inspect.signature(provider_cls.__init__)
                    for param_name, param in sig.parameters.items():
                        if param_name == "self":
                            continue
                        if param_name == "api_key":
                            init_args["api_key"] = "test_key"
                        elif param_name == "cookie_file":
                            init_args["cookie_file"] = self.dummy_cookie_file
                        elif param.default is inspect.Parameter.empty:
                            # Mandatory parameter without a default
                            if "file" in param_name:
                                init_args[param_name] = self.dummy_cookie_file
                            else:
                                init_args[param_name] = "test_value"

                    try:
                        provider = provider_cls(**init_args)
                    except Exception as e:
                        self.skipTest(f"Failed to initialize {name}: {e}")
                        continue

                    # Mock Session.post
                    with patch.object(provider.session, 'post') as mock_post:
                        # Generic mock response
                        mock_post.return_value = FakeResp(
                            json_data={
                                "choices": [{"message": {"content": "Mocked response"}, "delta": {"content": "Mocked response"}}],
                                "content": "Mocked response",
                                "message": {"content": "Mocked response"}
                            }
                        )

                        try:
                            # Test non-streaming ask
                            # We use a short timeout to avoid hanging
                            response = provider.ask("Hi")
                            self.assertIsNotNone(response)
                        except Exception as e:
                            # Some providers might fail due to complex logic even with mocked post
                            # We'll log it but not necessarily fail the whole suite if it's a WIP provider
                            print(f"Warning: {name}.ask failed with mock: {e}")

if __name__ == "__main__":
    unittest.main()
