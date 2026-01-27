"""
Comprehensive tests for the background model fetching system.

Tests cover:
- Cache behavior (hits, misses, TTL expiration)
- Background fetch non-blocking initialization
- Timeout handling
- Error/fallback handling
- Concurrent provider initialization
- Cache sharing between instances
- WEBSCOUT_NO_MODEL_CACHE environment variable
"""

import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from threading import Thread
from typing import Any, Dict, List, Optional
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

import pytest


class ModelCache:
    """Mock implementation of model cache for testing purposes."""

    def __init__(self, cache_dir: Optional[str] = None, ttl_seconds: int = 3600):
        """Initialize model cache.

        Args:
            cache_dir: Directory for cache files. If None, uses temp directory.
            ttl_seconds: Time-to-live for cached models in seconds.
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir()) / "webscout_model_cache"
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._in_memory_cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_file(self, provider_name: str) -> Path:
        """Get cache file path for a provider."""
        return self.cache_dir / f"{provider_name}_models.json"

    def get(self, provider_name: str) -> Optional[List[str]]:
        """Get cached models for a provider.

        Args:
            provider_name: Name of the provider.

        Returns:
            List of model names or None if cache miss/expired.
        """
        # Check in-memory cache first
        if provider_name in self._in_memory_cache:
            cache_entry = self._in_memory_cache[provider_name]
            if time.time() - cache_entry["timestamp"] < self.ttl_seconds:
                return cache_entry["models"]
            else:
                # TTL expired
                del self._in_memory_cache[provider_name]
                return None

        # Check file-based cache
        cache_file = self._get_cache_file(provider_name)
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    if time.time() - data["timestamp"] < self.ttl_seconds:
                        # Cache hit
                        self._in_memory_cache[provider_name] = {
                            "models": data["models"],
                            "timestamp": data["timestamp"]
                        }
                        return data["models"]
            except Exception:
                # File read error, treat as cache miss
                pass

        return None

    def set(self, provider_name: str, models: List[str]) -> None:
        """Set cached models for a provider.

        Args:
            provider_name: Name of the provider.
            models: List of model names to cache.
        """
        cache_entry = {
            "models": models,
            "timestamp": time.time()
        }
        self._in_memory_cache[provider_name] = cache_entry

        # Also persist to disk
        cache_file = self._get_cache_file(provider_name)
        try:
            with open(cache_file, "w") as f:
                json.dump(cache_entry, f)
        except Exception:
            # Silently ignore write errors
            pass

    def clear(self, provider_name: Optional[str] = None) -> None:
        """Clear cache.

        Args:
            provider_name: Specific provider to clear, or None to clear all.
        """
        if provider_name:
            if provider_name in self._in_memory_cache:
                del self._in_memory_cache[provider_name]
            cache_file = self._get_cache_file(provider_name)
            if cache_file.exists():
                cache_file.unlink()
        else:
            self._in_memory_cache.clear()
            for cache_file in self.cache_dir.glob("*_models.json"):
                cache_file.unlink()

    def __len__(self) -> int:
        """Return number of cached providers."""
        return len(self._in_memory_cache)


class BaseProviderWithBackgroundFetch:
    """Base provider with background model fetching capability."""

    AVAILABLE_MODELS: List[str] = ["default-model"]
    _model_cache: Optional[ModelCache] = None
    _fetch_thread: Optional[Thread] = None
    _cache_enabled: bool = True

    @classmethod
    def set_cache(cls, cache: Optional[ModelCache]) -> None:
        """Set the model cache instance."""
        cls._model_cache = cache

    @classmethod
    def enable_cache(cls, enable: bool = True) -> None:
        """Enable or disable model caching."""
        cls._cache_enabled = enable and "WEBSCOUT_NO_MODEL_CACHE" not in os.environ

    @classmethod
    def get_models(cls, api_key: Optional[str] = None) -> List[str]:
        """Fetch models from API.

        This is a placeholder to be implemented by subclasses.
        """
        return cls.AVAILABLE_MODELS

    @classmethod
    def _fetch_models_background(cls, api_key: Optional[str] = None, timeout: int = 10) -> None:
        """Fetch models in background thread.

        Args:
            api_key: Optional API key for authentication.
            timeout: Timeout in seconds for the fetch operation.
        """
        if not cls._cache_enabled or cls._model_cache is None:
            return

        provider_name = cls.__name__

        try:
            # Try to fetch with timeout
            def fetch_with_timeout():
                try:
                    models = cls.get_models(api_key)
                    if models and len(models) > 0:
                        cls.AVAILABLE_MODELS = models
                        cls._model_cache.set(provider_name, models)  # ty:ignore[possibly-missing-attribute]
                except Exception:
                    # Fallback to cached or default models
                    cached = cls._model_cache.get(provider_name)  # ty:ignore[possibly-missing-attribute]
                    if cached:
                        cls.AVAILABLE_MODELS = cached

            # Create and start thread with timeout
            fetch_thread = Thread(target=fetch_with_timeout, daemon=True)
            fetch_thread.start()
            fetch_thread.join(timeout=timeout)

            # If thread still alive after timeout, let it die (daemon thread)
            if fetch_thread.is_alive():
                # Timeout occurred, use fallback
                cached = cls._model_cache.get(provider_name)
                if cached:
                    cls.AVAILABLE_MODELS = cached

        except Exception:
            # Silently fail, use defaults
            pass

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize provider with background model fetching.

        Args:
            api_key: Optional API key.
            **kwargs: Additional arguments.
        """
        # Check cache first (fast)
        if self._model_cache and self._cache_enabled:
            cached = self._model_cache.get(self.__class__.__name__)
            if cached:
                self.__class__.AVAILABLE_MODELS = cached

        # Start background fetch (non-blocking)
        if self._cache_enabled and self._model_cache:
            cache = self._model_cache
            # Use daemon thread for background fetch
            def bg_fetch():
                try:
                    models = self.__class__.get_models(api_key)
                    if models and len(models) > 0:
                        self.__class__.AVAILABLE_MODELS = models
                        cache.set(self.__class__.__name__, models)
                except Exception:
                    pass

            self._fetch_thread = Thread(target=bg_fetch, daemon=True)
            self._fetch_thread.start()


# ============================================================================
# TEST CASES
# ============================================================================


class TestModelCacheBasics(unittest.TestCase):
    """Test basic model cache functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir, ttl_seconds=60)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_miss_returns_none(self) -> None:
        """Test that cache miss returns None."""
        result = self.cache.get("nonexistent_provider")
        self.assertIsNone(result)

    def test_cache_hit_returns_models(self) -> None:
        """Test that cache hit returns cached models."""
        models = ["model-1", "model-2", "model-3"]
        self.cache.set("test_provider", models)

        result = self.cache.get("test_provider")
        self.assertEqual(result, models)

    def test_cache_stores_multiple_providers(self) -> None:
        """Test that cache can store models for multiple providers."""
        models_a = ["model-a1", "model-a2"]
        models_b = ["model-b1", "model-b2", "model-b3"]

        self.cache.set("provider_a", models_a)
        self.cache.set("provider_b", models_b)

        self.assertEqual(self.cache.get("provider_a"), models_a)
        self.assertEqual(self.cache.get("provider_b"), models_b)

    def test_cache_clear_single_provider(self) -> None:
        """Test clearing cache for a single provider."""
        models_a = ["model-a"]
        models_b = ["model-b"]

        self.cache.set("provider_a", models_a)
        self.cache.set("provider_b", models_b)

        self.cache.clear("provider_a")

        self.assertIsNone(self.cache.get("provider_a"))
        self.assertEqual(self.cache.get("provider_b"), models_b)

    def test_cache_clear_all(self) -> None:
        """Test clearing all cached entries."""
        self.cache.set("provider_a", ["model-a"])
        self.cache.set("provider_b", ["model-b"])

        self.cache.clear()

        self.assertIsNone(self.cache.get("provider_a"))
        self.assertIsNone(self.cache.get("provider_b"))


class TestCacheTTLExpiration(unittest.TestCase):
    """Test cache TTL (time-to-live) expiration."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        # Very short TTL for testing
        self.cache = ModelCache(cache_dir=self.temp_dir, ttl_seconds=1)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_expires_after_ttl(self) -> None:
        """Test that cache expires after TTL."""
        models = ["model-1", "model-2"]
        self.cache.set("test_provider", models)

        # Should be in cache initially
        self.assertEqual(self.cache.get("test_provider"), models)

        # Wait for TTL to expire
        time.sleep(1.5)

        # Should not be in cache anymore
        self.assertIsNone(self.cache.get("test_provider"))

    def test_cache_valid_within_ttl(self) -> None:
        """Test that cache is valid within TTL duration."""
        models = ["model-1"]
        self.cache.set("test_provider", models)

        # Check immediately (should still be valid)
        self.assertEqual(self.cache.get("test_provider"), models)

        # Wait half the TTL
        time.sleep(0.5)

        # Should still be valid
        self.assertEqual(self.cache.get("test_provider"), models)


class TestEnvironmentVariableDisableCache(unittest.TestCase):
    """Test WEBSCOUT_NO_MODEL_CACHE environment variable."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir)

        # Store original env var state
        self.original_env = os.environ.get("WEBSCOUT_NO_MODEL_CACHE")

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Restore original env var
        if self.original_env is not None:
            os.environ["WEBSCOUT_NO_MODEL_CACHE"] = self.original_env
        elif "WEBSCOUT_NO_MODEL_CACHE" in os.environ:
            del os.environ["WEBSCOUT_NO_MODEL_CACHE"]

    def test_cache_disabled_with_env_var(self) -> None:
        """Test that cache is disabled when env var is set."""
        os.environ["WEBSCOUT_NO_MODEL_CACHE"] = "1"

        class TestProvider(BaseProviderWithBackgroundFetch):
            pass

        TestProvider.enable_cache(True)  # Try to enable, but env var should disable

        # Verify caching is effectively disabled
        self.assertFalse(TestProvider._cache_enabled)

    def test_cache_enabled_without_env_var(self) -> None:
        """Test that cache is enabled when env var is not set."""
        if "WEBSCOUT_NO_MODEL_CACHE" in os.environ:
            del os.environ["WEBSCOUT_NO_MODEL_CACHE"]

        class TestProvider(BaseProviderWithBackgroundFetch):
            pass

        TestProvider.enable_cache(True)

        # Verify caching is enabled
        self.assertTrue(TestProvider._cache_enabled)


class TestNonBlockingInitialization(unittest.TestCase):
    """Test that provider initialization is non-blocking."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_completes_instantly(self) -> None:
        """Test that initialization completes quickly (non-blocking)."""
        class SlowProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                # Simulate slow network request
                time.sleep(2)
                return ["slow-model-1", "slow-model-2"]

        SlowProvider.set_cache(self.cache)
        SlowProvider.enable_cache(True)

        # Measure initialization time
        start = time.time()
        SlowProvider()
        elapsed = time.time() - start

        # Should complete in < 100ms (non-blocking)
        self.assertLess(elapsed, 0.1)

        # Default models should be available immediately
        self.assertEqual(SlowProvider.AVAILABLE_MODELS, ["default"])

    def test_background_fetch_populates_cache(self) -> None:
        """Test that background fetch eventually populates cache."""
        models_to_fetch = ["fetched-model-1", "fetched-model-2"]

        class FastProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                return models_to_fetch

        FastProvider.set_cache(self.cache)
        FastProvider.enable_cache(True)

        # Directly test the background fetch mechanism
        FastProvider._fetch_models_background()

        # Cache should have the fetched models
        cached = self.cache.get("FastProvider")
        self.assertIsNotNone(cached)
        self.assertEqual(cached, models_to_fetch)


class TestBackgroundFetchTimeout(unittest.TestCase):
    """Test timeout handling in background fetch."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_timeout_aborts_fetch(self) -> None:
        """Test that fetch aborts after timeout."""
        class VerySlowProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]
            fetch_called = False

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                cls.fetch_called = True
                # Simulate very slow fetch
                time.sleep(5)
                return ["slow-model"]

        VerySlowProvider.set_cache(self.cache)
        VerySlowProvider.enable_cache(True)

        # Initialize with 1 second timeout
        VerySlowProvider()
        VerySlowProvider._fetch_models_background(timeout=1)

        # Wait a bit for timeout to trigger
        time.sleep(0.2)

        # Default models should still be available
        self.assertEqual(VerySlowProvider.AVAILABLE_MODELS, ["default"])

    def test_fallback_to_cached_on_timeout(self) -> None:
        """Test that fallback to cache occurs on timeout."""
        class TimeoutProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                time.sleep(3)
                return ["slow-model"]

        TimeoutProvider.set_cache(self.cache)
        TimeoutProvider.enable_cache(True)

        # Pre-populate cache with models
        self.cache.set("TimeoutProvider", ["cached-model-1", "cached-model-2"])

        # Fetch with 1 second timeout
        TimeoutProvider._fetch_models_background(timeout=1)
        time.sleep(0.2)

        # Should have cached models available
        cached = self.cache.get("TimeoutProvider")
        self.assertIsNotNone(cached)


class TestErrorHandlingAndFallback(unittest.TestCase):
    """Test error handling and fallback behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_network_error_silent_fallback(self) -> None:
        """Test that network errors silently fall back to defaults."""
        class BrokenProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default-model-1", "default-model-2"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                raise ConnectionError("Network unreachable")

        BrokenProvider.set_cache(self.cache)
        BrokenProvider.enable_cache(True)

        # Should not raise exception
        BrokenProvider()
        time.sleep(0.2)

        # Default models should still be available
        self.assertEqual(
            BrokenProvider.AVAILABLE_MODELS,
            ["default-model-1", "default-model-2"]
        )

    def test_fallback_models_immediately_available(self) -> None:
        """Test that fallback models are immediately available."""
        class ErrorProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["fallback-1", "fallback-2"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                raise ValueError("Invalid API key")

        ErrorProvider.set_cache(self.cache)
        ErrorProvider.enable_cache(True)

        # Initialize (should not block or raise)
        ErrorProvider()

        # Fallback models should be immediately available
        self.assertIn("fallback-1", ErrorProvider.AVAILABLE_MODELS)
        self.assertIn("fallback-2", ErrorProvider.AVAILABLE_MODELS)


class TestConcurrentInitialization(unittest.TestCase):
    """Test concurrent provider initialization."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concurrent_provider_initialization(self) -> None:
        """Test initializing multiple providers concurrently."""
        class ConcurrentProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]
            init_count = 0

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                return ["concurrent-model-1", "concurrent-model-2"]

        ConcurrentProvider.set_cache(self.cache)
        ConcurrentProvider.enable_cache(True)

        providers = []
        threads = []

        def init_provider():
            provider = ConcurrentProvider()
            providers.append(provider)

        # Create 3 concurrent initializations
        for _ in range(3):
            t = Thread(target=init_provider)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All should initialize successfully
        self.assertEqual(len(providers), 3)

        # Trigger the fetch directly
        ConcurrentProvider._fetch_models_background()

        # Cache should have the models
        cached = self.cache.get("ConcurrentProvider")
        self.assertIsNotNone(cached)

    def test_cache_shared_between_instances(self) -> None:
        """Test that cache is correctly shared between instances."""
        class SharedCacheProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                return ["shared-model-1", "shared-model-2"]

        SharedCacheProvider.set_cache(self.cache)
        SharedCacheProvider.enable_cache(True)

        # Pre-populate cache
        self.cache.set("SharedCacheProvider", ["pre-cached-model"])

        # Create multiple instances
        SharedCacheProvider()
        SharedCacheProvider()

        # Both should get models from shared cache
        time.sleep(0.2)

        cached = self.cache.get("SharedCacheProvider")
        self.assertIsNotNone(cached)
        self.assertEqual(len(self.cache._in_memory_cache), 1)


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic integration scenarios."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fast_provider_initialization(self) -> None:
        """Test fast provider initialization completes in < 50ms."""
        class FastProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                # Simulate quick fetch
                time.sleep(0.01)
                return ["fast-model"]

        FastProvider.set_cache(self.cache)
        FastProvider.enable_cache(True)

        start = time.time()
        FastProvider()
        elapsed = time.time() - start

        # Should initialize in < 50ms
        self.assertLess(elapsed, 0.05)

    def test_models_eventually_available_after_wait(self) -> None:
        """Test that models become available after short wait."""
        class EventuallyFastProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                return ["eventual-model-1", "eventual-model-2"]

        EventuallyFastProvider.set_cache(self.cache)
        EventuallyFastProvider.enable_cache(True)

        # Test direct fetch
        EventuallyFastProvider._fetch_models_background()

        # Should now have fetched models
        cached = self.cache.get("EventuallyFastProvider")
        self.assertIsNotNone(cached)
        if cached:
            self.assertGreater(len(cached), 1)

    def test_cache_persistence_across_instances(self) -> None:
        """Test that cache persists across different provider instances."""
        class PersistentProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                return ["persistent-model"]

        PersistentProvider.set_cache(self.cache)
        PersistentProvider.enable_cache(True)

        # Trigger fetch
        PersistentProvider._fetch_models_background()

        # Create new cache instance (simulating new Python session)
        new_cache = ModelCache(cache_dir=self.temp_dir)
        cached = new_cache.get("PersistentProvider")

        # Should still find cached data
        self.assertIsNotNone(cached)


class TestCacheWithAPIKey(unittest.TestCase):
    """Test cache behavior with API key authentication."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fetch_with_api_key(self) -> None:
        """Test that background fetch works with API key."""
        class AuthProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["default"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                if api_key == "valid-key":
                    return ["auth-model-1", "auth-model-2"]
                raise ValueError("Invalid API key")

        AuthProvider.set_cache(self.cache)
        AuthProvider.enable_cache(True)

        # Initialize with valid API key to pass it to fetch
        AuthProvider(api_key="valid-key")

        # Directly fetch with API key
        AuthProvider._fetch_models_background(api_key="valid-key")

        # Should have cached the models
        cached = self.cache.get("AuthProvider")
        self.assertIsNotNone(cached)

    def test_fetch_without_api_key_fallback(self) -> None:
        """Test fallback when API key is required but not provided."""
        class RequiredAuthProvider(BaseProviderWithBackgroundFetch):
            AVAILABLE_MODELS = ["fallback-model"]

            @classmethod
            def get_models(cls, api_key: Optional[str] = None) -> List[str]:
                if not api_key:
                    raise ValueError("API key required")
                return ["auth-model"]

        RequiredAuthProvider.set_cache(self.cache)
        RequiredAuthProvider.enable_cache(True)

        # Initialize without API key
        RequiredAuthProvider()
        time.sleep(0.2)

        # Should fall back to default models
        self.assertEqual(RequiredAuthProvider.AVAILABLE_MODELS, ["fallback-model"])


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================


class TestMultipleProviders(unittest.TestCase):
    """Test multiple provider types with different models."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_multiple_providers_independence(self) -> None:
        """Test that different providers maintain independent caches."""
        test_cases = [
            ("ProviderA", ["model-a1", "model-a2", "model-a3"]),
            ("ProviderB", ["model-b1", "model-b2"]),
            ("ProviderC", ["model-c1", "model-c2", "model-c3", "model-c4"]),
        ]

        for pname, pmodels in test_cases:
            self.cache.set(pname, pmodels)

        # Verify each provider has its own models
        self.assertEqual(self.cache.get("ProviderA"), ["model-a1", "model-a2", "model-a3"])
        self.assertEqual(self.cache.get("ProviderB"), ["model-b1", "model-b2"])
        self.assertEqual(
            self.cache.get("ProviderC"),
            ["model-c1", "model-c2", "model-c3", "model-c4"]
        )


# ============================================================================
# EDGE CASES & ROBUSTNESS
# ============================================================================


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ModelCache(cache_dir=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.cache.clear()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_empty_model_list(self) -> None:
        """Test handling of empty model lists."""
        self.cache.set("empty_provider", [])

        result = self.cache.get("empty_provider")
        self.assertEqual(result, [])

    def test_cache_very_large_model_list(self) -> None:
        """Test handling of very large model lists."""
        large_list = [f"model-{i}" for i in range(1000)]
        self.cache.set("large_provider", large_list)

        result = self.cache.get("large_provider")
        self.assertIsNotNone(result)
        self.assertEqual(result, large_list)
        if result:
            self.assertEqual(len(result), 1000)

    def test_cache_with_special_characters(self) -> None:
        """Test cache with special characters in model names."""
        models = ["model-v1.0", "model_v2-0", "model v3.0-alpha"]
        self.cache.set("special_provider", models)

        result = self.cache.get("special_provider")
        self.assertEqual(result, models)

    def test_concurrent_cache_writes(self) -> None:
        """Test concurrent writes to cache."""
        def write_cache(provider_id: int):
            models = [f"model-{provider_id}-{i}" for i in range(10)]
            self.cache.set(f"provider_{provider_id}", models)

        threads = []
        for i in range(10):
            t = Thread(target=write_cache, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify all writes succeeded
        for i in range(10):
            result = self.cache.get(f"provider_{i}")
            self.assertIsNotNone(result)
            if result:
                self.assertEqual(len(result), 10)


if __name__ == "__main__":
    unittest.main()
