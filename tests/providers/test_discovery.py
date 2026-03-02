import unittest
import webscout.Provider as ProviderModule
import inspect

class TestProviderDiscovery(unittest.TestCase):
    def test_all_providers_importable(self):
        """Verify that all providers listed in __all__ can be imported."""
        # Access __all__ from the module's dict to avoid shadowing issues
        provider_all = getattr(ProviderModule, "__all__", [])
        for name in provider_all:
            with self.subTest(provider=name):
                provider_cls = getattr(ProviderModule, name)
                self.assertTrue(inspect.isclass(provider_cls), f"{name} is not a class")

    def test_provider_inheritance(self):
        """Verify that all providers inherit from the base Provider class."""
        from webscout.AIbase import Provider as BaseProvider
        provider_all = getattr(ProviderModule, "__all__", [])
        for name in provider_all:
            with self.subTest(provider=name):
                provider_cls = getattr(ProviderModule, name)
                # Some might inherit from OpenAICompatibleProvider which inherits from BaseProvider
                self.assertTrue(issubclass(provider_cls, BaseProvider), f"{name} does not inherit from BaseProvider")

if __name__ == "__main__":
    unittest.main()
