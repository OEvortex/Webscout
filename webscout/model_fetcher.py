"""Non-blocking model fetching utilities with caching support.

This module provides thread-safe utilities for fetching and caching AI model
lists from various providers in the background, preventing blocking operations
during initialization or model discovery.
"""

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from litprinter import ic

# Constants
DEFAULT_FETCH_TIMEOUT = 10
DEFAULT_CACHE_TTL = 86400  # 24 hours in seconds
CACHE_DIR = Path(tempfile.gettempdir()) / "webscout"


class ModelFetcherCache:
    """Thread-safe file-based cache for model lists with TTL support.

    Stores cached model data in the system temp directory under `webscout/model_cache.json`
    with per-provider expiration times. Supports disabling via `WEBSCOUT_NO_MODEL_CACHE`
    env var.

    Attributes:
        cache_path: Path to the cache file.
        lock: Threading lock for file operations.
        ttl: Default TTL in seconds (from env or default).
        cache_disabled: Whether caching is disabled.
    """

    def __init__(self, cache_ttl: Optional[int] = None, debug: bool = False) -> None:
        """Initialize the model fetcher cache.

        Args:
            cache_ttl: TTL in seconds. If None, reads from WEBSCOUT_MODEL_CACHE_TTL
                       env var or uses DEFAULT_CACHE_TTL.
            debug: Enable debug logging via ic.
        """
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.cache_path = CACHE_DIR / "model_cache.json"
        self.lock = threading.Lock()
        self.debug = debug
        self.cache_disabled = os.getenv("WEBSCOUT_NO_MODEL_CACHE", "").lower() in (
            "1",
            "true",
            "yes",
        )

        if cache_ttl is not None:
            self.ttl = cache_ttl
        else:
            env_ttl = os.getenv("WEBSCOUT_MODEL_CACHE_TTL")
            self.ttl = int(env_ttl) if env_ttl else DEFAULT_CACHE_TTL

    def get(self, provider_name: str) -> Optional[list[str]]:
        """Retrieve cached models for a provider if valid.

        Args:
            provider_name: Name of the provider.

        Returns:
            List of model names if cached and valid, None otherwise.
        """
        if self.cache_disabled:
            return None

        with self.lock:
            if not self.cache_path.exists():
                return None

            try:
                with open(self.cache_path, "r") as f:
                    cache_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                if self.debug:
                    ic(f"Failed to read cache: {e}")
                return None

            if provider_name not in cache_data:
                return None

            entry = cache_data[provider_name]
            if self._is_expired(entry["timestamp"]):
                return None

            return entry.get("models")

    def set(
        self, provider_name: str, models: list[str], ttl: Optional[int] = None
    ) -> None:
        """Cache models for a provider.

        Args:
            provider_name: Name of the provider.
            models: List of model names to cache.
            ttl: TTL in seconds for this entry. If None, uses instance TTL.
        """
        if self.cache_disabled:
            return

        ttl = ttl if ttl is not None else self.ttl

        with self.lock:
            cache_data = {}
            if self.cache_path.exists():
                try:
                    with open(self.cache_path, "r") as f:
                        cache_data = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    if self.debug:
                        ic(f"Failed to read existing cache: {e}")

            cache_data[provider_name] = {
                "models": models,
                "timestamp": time.time(),
                "ttl": ttl,
            }

            try:
                with open(self.cache_path, "w") as f:
                    json.dump(cache_data, f, indent=2)
            except IOError as e:
                if self.debug:
                    ic(f"Failed to write cache: {e}")

    def is_valid(self, provider_name: str) -> bool:
        """Check if a provider has a valid cached entry.

        Args:
            provider_name: Name of the provider.

        Returns:
            True if cached and not expired, False otherwise.
        """
        return self.get(provider_name) is not None

    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry has expired.

        Args:
            timestamp: Timestamp when entry was created.

        Returns:
            True if expired, False otherwise.
        """
        entry_data = {}
        try:
            if self.cache_path.exists():
                with open(self.cache_path, "r") as f:
                    all_data = json.load(f)
                    # Find the provider with this timestamp to get its TTL
                    for provider, data in all_data.items():
                        if data.get("timestamp") == timestamp:
                            entry_data = data
                            break
        except (json.JSONDecodeError, IOError):
            pass

        ttl = entry_data.get("ttl", self.ttl)
        return (time.time() - timestamp) > ttl


class BackgroundModelFetcher:
    """Manages background threads for non-blocking model fetching.

    Fetches models asynchronously and stores results in cache. Falls back to
    provided models on timeout or error.

    Attributes:
        cache: ModelFetcherCache instance.
        lock: Threading lock for thread-safe operations.
        _threads: Dict tracking active fetch threads.
    """

    def __init__(
        self, cache: Optional[ModelFetcherCache] = None, debug: bool = False
    ) -> None:
        """Initialize the background model fetcher.

        Args:
            cache: ModelFetcherCache instance. If None, creates a new one.
            debug: Enable debug logging via ic.
        """
        self.cache = cache or ModelFetcherCache(debug=debug)
        self.debug = debug
        self.lock = threading.Lock()
        self._threads: dict[str, threading.Thread] = {}

    def fetch_async(
        self,
        provider_name: str,
        fetch_func: Callable[[], list[str]],
        fallback_models: list[str],
        timeout: int = DEFAULT_FETCH_TIMEOUT,
    ) -> list[str]:
        """Fetch models asynchronously in background thread.

        Immediately returns fallback models or cached models. Spawns a background
        thread to fetch fresh models and update cache.

        Args:
            provider_name: Name of the provider.
            fetch_func: Callable that returns list of models. Should raise on error.
            fallback_models: Models to return immediately while fetching.
            timeout: Timeout in seconds for fetch operation.

        Returns:
            Cached models if valid, otherwise fallback_models.
        """
        # Try to get cached models first
        cached = self.cache.get(provider_name)
        if cached is not None:
            return cached

        # Start background fetch if not already running
        with self.lock:
            if provider_name not in self._threads or not self._threads[
                provider_name
            ].is_alive():
                thread = threading.Thread(
                    target=self._fetch_and_cache,
                    args=(provider_name, fetch_func, timeout),
                    daemon=True,
                    name=f"ModelFetcher-{provider_name}",
                )
                thread.start()
                self._threads[provider_name] = thread

        return fallback_models

    def _fetch_and_cache(
        self, provider_name: str, fetch_func: Callable[[], list[str]], timeout: int
    ) -> None:
        """Fetch models and cache them (background thread target).

        Args:
            provider_name: Name of the provider.
            fetch_func: Callable that returns list of models.
            timeout: Timeout in seconds for fetch operation.
        """
        try:
            # Use a timeout mechanism with threading
            result: list[str] = []
            error: Optional[Exception] = None

            def _fetch() -> None:
                nonlocal result, error
                try:
                    result = fetch_func()
                except Exception as e:
                    error = e

            fetch_thread = threading.Thread(
                target=_fetch, daemon=True, name=f"ModelFetch-Worker-{provider_name}"
            )
            fetch_thread.start()
            fetch_thread.join(timeout=timeout)

            if fetch_thread.is_alive():
                # Timeout occurred
                if self.debug:
                    ic(
                        f"Model fetch for '{provider_name}' timed out after {timeout}s"
                    )
                return

            if error is not None:
                if self.debug:
                    ic(f"Model fetch for '{provider_name}' failed: {error}")
                return

            if result:
                self.cache.set(provider_name, result)
                if self.debug:
                    ic(f"Cached {len(result)} models for '{provider_name}'")

        except Exception as e:
            if self.debug:
                ic(f"Unexpected error fetching models for '{provider_name}': {e}")

    def wait_for_provider(self, provider_name: str, timeout: int = 5) -> None:
        """Wait for a specific provider's fetch to complete.

        Args:
            provider_name: Name of the provider.
            timeout: Maximum time to wait in seconds.
        """
        with self.lock:
            thread = self._threads.get(provider_name)

        if thread is not None:
            thread.join(timeout=timeout)
