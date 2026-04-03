"""
Provider management and initialization for the Webscout API.
"""

import inspect
import sys
from typing import Any, Dict, Optional, Tuple

from litprinter import ic
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from .config import AppConfig
from .exceptions import APIError

# Cache for provider instances to avoid reinitialization on every request
provider_instances: Dict[str, Any] = {}
tti_provider_instances: Dict[str, Any] = {}
tts_provider_instances: Dict[str, Any] = {}


def _get_available_models(provider_class: Any, attribute_name: str = "AVAILABLE_MODELS") -> list[str]:
    """Return a normalized list of model names for a provider class."""
    available = getattr(provider_class, attribute_name, None)

    # Many providers expose AVAILABLE_MODELS as a property on the instance.
    if isinstance(available, property):
        try:
            available = getattr(provider_class(), attribute_name, [])
        except Exception:
            available = []

    if available is None:
        return []

    if isinstance(available, str):
        return [available]

    if isinstance(available, (list, tuple, set)):
        return [model for model in available if isinstance(model, str) and model]

    if hasattr(available, "__iter__"):
        return [model for model in available if isinstance(model, str) and model]

    return []


def initialize_provider_map() -> None:
    """Initialize the provider map by discovering available providers."""
    ic.configureOutput(prefix='INFO| ')
    ic("Initializing provider map...")

    try:
        import importlib
        # Ensure Openai_comp is loaded in sys.modules
        importlib.import_module("webscout.Provider.Openai_comp")
        module = sys.modules["webscout.Provider.Openai_comp"]
        from webscout.Provider.Openai_comp.base import OpenAICompatibleProvider, SimpleModelList

        provider_count = 0
        model_count = 0

        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, OpenAICompatibleProvider)
                and obj.__name__ != "OpenAICompatibleProvider"
            ):
                # Only include providers that don't require authentication
                if hasattr(obj, 'required_auth') and not getattr(obj, 'required_auth', True):
                    provider_name = obj.__name__
                    AppConfig.provider_map[provider_name] = obj
                    provider_count += 1

                    # Register available models for this provider
                    for model in _get_available_models(obj):
                        model_key = f"{provider_name}/{model}"
                        AppConfig.provider_map[model_key] = obj
                        model_count += 1

        # Fallback to ChatGPT if no providers found
        if not AppConfig.provider_map:
            ic.configureOutput(prefix='WARNING| ')
            ic("No providers found, using ChatGPT fallback")
            try:
                from webscout.Provider.Openai_comp.chatgpt import ChatGPT
                fallback_models = ["gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]

                AppConfig.provider_map["ChatGPT"] = ChatGPT

                for model in fallback_models:
                    model_key = f"ChatGPT/{model}"
                    AppConfig.provider_map[model_key] = ChatGPT

                AppConfig.default_provider = "ChatGPT"
                provider_count = 1
                model_count = len(fallback_models)
            except ImportError as e:
                ic.configureOutput(prefix='ERROR| ')
                ic(f"Failed to import ChatGPT fallback: {e}")
                raise APIError("No providers available", HTTP_500_INTERNAL_SERVER_ERROR)

        ic.configureOutput(prefix='INFO| ')
        ic(f"Initialized {provider_count} providers with {model_count} models")

    except Exception as e:
        ic.configureOutput(prefix='ERROR| ')
        ic(f"Failed to initialize provider map: {e}")
        raise APIError(f"Provider initialization failed: {e}", HTTP_500_INTERNAL_SERVER_ERROR)


def initialize_tti_provider_map() -> None:
    """Initialize the TTI provider map by discovering available TTI providers."""
    ic.configureOutput(prefix='INFO| ')
    ic("Initializing TTI provider map...")

    try:
        import importlib
        # Ensure TTI is loaded in sys.modules
        importlib.import_module("webscout.Provider.TTI")
        module = sys.modules["webscout.Provider.TTI"]
        from webscout.Provider.TTI.base import TTICompatibleProvider

        provider_count = 0
        model_count = 0

        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, TTICompatibleProvider)
                and obj.__name__ != "TTICompatibleProvider"
                and obj.__name__ != "BaseImages"
            ):
                provider_name = obj.__name__
                AppConfig.tti_provider_map[provider_name] = obj
                provider_count += 1

                # Register available models for this TTI provider
                for model in _get_available_models(obj):
                    model_key = f"{provider_name}/{model}"
                    AppConfig.tti_provider_map[model_key] = obj
                    model_count += 1

        # Fallback to PollinationsAI if no TTI providers found
        if not AppConfig.tti_provider_map:
            ic.configureOutput(prefix='WARNING| ')
            ic("No TTI providers found, using PollinationsAI fallback")
            try:
                from webscout.Provider.TTI.pollinations import PollinationsAI
                fallback_models = ["flux", "turbo", "gptimage"]

                AppConfig.tti_provider_map["PollinationsAI"] = PollinationsAI

                for model in fallback_models:
                    model_key = f"PollinationsAI/{model}"
                    AppConfig.tti_provider_map[model_key] = PollinationsAI

                AppConfig.default_tti_provider = "PollinationsAI"
                provider_count = 1
                model_count = len(fallback_models)
            except ImportError as e:
                ic.configureOutput(prefix='ERROR| ')
                ic(f"Failed to import PollinationsAI fallback: {e}")
                raise APIError("No TTI providers available", HTTP_500_INTERNAL_SERVER_ERROR)

        ic.configureOutput(prefix='INFO| ')
        ic(f"Initialized {provider_count} TTI providers with {model_count} models")

    except Exception as e:
        ic.configureOutput(prefix='ERROR| ')
        ic(f"Failed to initialize TTI provider map: {e}")
        raise APIError(f"TTI Provider initialization failed: {e}", HTTP_500_INTERNAL_SERVER_ERROR)


def initialize_tts_provider_map() -> None:
    """Initialize the TTS provider map by discovering available TTS providers."""
    ic.configureOutput(prefix='INFO| ')
    ic("Initializing TTS provider map...")

    try:
        import importlib
        # Ensure TTS is loaded in sys.modules
        importlib.import_module("webscout.Provider.TTS")
        module = sys.modules["webscout.Provider.TTS"]
        from webscout.Provider.TTS.base import BaseTTSProvider

        provider_count = 0
        model_count = 0

        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseTTSProvider)
                and obj.__name__ not in ("BaseTTSProvider", "TTSProvider")
            ):
                provider_name = obj.__name__
                AppConfig.tts_provider_map[provider_name] = obj
                provider_count += 1

                # Register available models for this TTS provider
                for model in _get_available_models(obj, "SUPPORTED_MODELS") or _get_available_models(obj):
                    model_key = f"{provider_name}/{model}"
                    AppConfig.tts_provider_map[model_key] = obj
                    model_count += 1

        # Fallback if no TTS providers found
        if not AppConfig.tts_provider_map:
            ic.configureOutput(prefix='WARNING| ')
            ic("No TTS providers found")
            raise APIError("No TTS providers available", HTTP_500_INTERNAL_SERVER_ERROR)

        ic.configureOutput(prefix='INFO| ')
        ic(f"Initialized {provider_count} TTS providers with {model_count} models")

    except Exception as e:
        ic.configureOutput(prefix='ERROR| ')
        ic(f"Failed to initialize TTS provider map: {e}")
        raise APIError(f"TTS Provider initialization failed: {e}", HTTP_500_INTERNAL_SERVER_ERROR)


def resolve_provider_and_model(model_identifier: str) -> Tuple[Any, str]:
    """Resolve provider class and model name from model identifier."""
    provider_class = None
    model_name = None

    # Check for explicit provider/model syntax
    if model_identifier in AppConfig.provider_map and "/" in model_identifier:
        provider_class = AppConfig.provider_map[model_identifier]
        _, model_name = model_identifier.split("/", 1)
    elif "/" in model_identifier:
        provider_name, model_name = model_identifier.split("/", 1)
        provider_class = AppConfig.provider_map.get(provider_name)
    else:
        provider_class = AppConfig.provider_map.get(AppConfig.default_provider)
        model_name = model_identifier

    if not provider_class:
        available_providers = list(set(v.__name__ for v in AppConfig.provider_map.values()))
        raise APIError(
            f"Provider for model '{model_identifier}' not found. Available providers: {available_providers}",
            HTTP_404_NOT_FOUND,
            "model_not_found",
            param="model"
        )

    # Validate model availability
    if hasattr(provider_class, "AVAILABLE_MODELS") and model_name is not None:
        available = getattr(provider_class, "AVAILABLE_MODELS", None)
        # If it's a property, get from instance
        if isinstance(available, property):
            try:
                available = getattr(provider_class(), "AVAILABLE_MODELS", [])
            except Exception:
                available = []
        # If still not iterable, fallback to empty list
        if not isinstance(available, (list, tuple, set)):
            available = list(available) if available and hasattr(available, "__iter__") and not isinstance(available, str) else []
        if available and model_name not in available:
            raise APIError(
                f"Model '{model_name}' not supported by provider '{provider_class.__name__}'. Available models: {available}",
                HTTP_404_NOT_FOUND,
                "model_not_found",
                param="model"
            )

    return provider_class, model_name


def resolve_tti_provider_and_model(model_identifier: str) -> Tuple[Any, str]:
    """Resolve TTI provider class and model name from model identifier."""
    provider_class = None
    model_name = None

    # Check for explicit provider/model syntax
    if model_identifier in AppConfig.tti_provider_map and "/" in model_identifier:
        provider_class = AppConfig.tti_provider_map[model_identifier]
        _, model_name = model_identifier.split("/", 1)
    elif "/" in model_identifier:
        provider_name, model_name = model_identifier.split("/", 1)
        provider_class = AppConfig.tti_provider_map.get(provider_name)
    else:
        provider_class = AppConfig.tti_provider_map.get(AppConfig.default_tti_provider)
        model_name = model_identifier

    if not provider_class:
        available_providers = list(set(v.__name__ for v in AppConfig.tti_provider_map.values()))
        raise APIError(
            f"TTI Provider for model '{model_identifier}' not found. Available TTI providers: {available_providers}",
            HTTP_404_NOT_FOUND,
            "model_not_found",
            param="model"
        )

    # Validate model availability
    if hasattr(provider_class, "AVAILABLE_MODELS") and model_name is not None:
        available = getattr(provider_class, "AVAILABLE_MODELS", None)
        # If it's a property, get from instance
        if isinstance(available, property):
            try:
                available = getattr(provider_class(), "AVAILABLE_MODELS", [])
            except Exception:
                available = []
        # If still not iterable, fallback to empty list
        if not isinstance(available, (list, tuple, set)):
            available = list(available) if available and hasattr(available, "__iter__") and not isinstance(available, str) else []
        if available and model_name not in available:
            raise APIError(
                f"Model '{model_name}' not supported by TTI provider '{provider_class.__name__}'. Available models: {available}",
                HTTP_404_NOT_FOUND,
                "model_not_found",
                param="model"
            )

    return provider_class, model_name


def get_provider_instance(provider_class: Any):
    """Return a cached instance of the provider, creating it if necessary."""
    key = provider_class.__name__
    instance = provider_instances.get(key)
    if instance is None:
        try:
            instance = provider_class()
        except TypeError as e:
            # Handle abstract class instantiation error
            if "abstract class" in str(e):
                from .exceptions import APIError
                raise APIError(
                    f"Provider misconfiguration: Cannot instantiate abstract class '{provider_class.__name__}'. Please check the provider implementation.",
                    HTTP_500_INTERNAL_SERVER_ERROR,
                    "provider_error"
                )
            raise
        provider_instances[key] = instance
    return instance


def get_tti_provider_instance(provider_class: Any):
    """Return a cached instance of the TTI provider, creating it if needed."""
    key = provider_class.__name__
    instance = tti_provider_instances.get(key)
    if instance is None:
        try:
            instance = provider_class()
        except TypeError as e:
            # Handle abstract class instantiation error
            if "abstract class" in str(e):
                from .exceptions import APIError
                raise APIError(
                    f"Provider misconfiguration: Cannot instantiate abstract class '{provider_class.__name__}'. Please check the provider implementation.",
                    HTTP_500_INTERNAL_SERVER_ERROR,
                    "provider_error",
                )
            raise
        tti_provider_instances[key] = instance
    return instance


def resolve_tts_provider_and_model(model_identifier: str) -> Tuple[Any, str]:
    """Resolve TTS provider class and model name from model identifier."""
    provider_class = None
    model_name = None

    # Check for explicit provider/model syntax
    if model_identifier in AppConfig.tts_provider_map and "/" in model_identifier:
        provider_class = AppConfig.tts_provider_map[model_identifier]
        _, model_name = model_identifier.split("/", 1)
    elif "/" in model_identifier:
        provider_name, model_name = model_identifier.split("/", 1)
        provider_class = AppConfig.tts_provider_map.get(provider_name)
    else:
        provider_class = AppConfig.tts_provider_map.get(AppConfig.default_tts_provider)
        model_name = model_identifier

    if not provider_class:
        available_providers = list(set(v.__name__ for v in AppConfig.tts_provider_map.values()))
        raise APIError(
            f"TTS Provider for model '{model_identifier}' not found. Available TTS providers: {available_providers}",
            HTTP_404_NOT_FOUND,
            "model_not_found",
            param="model"
        )

    # Validate model availability
    if hasattr(provider_class, "SUPPORTED_MODELS") and model_name is not None:
        available = getattr(provider_class, "SUPPORTED_MODELS", None) or getattr(provider_class, "AVAILABLE_MODELS", None)
        if isinstance(available, property):
            try:
                available = getattr(provider_class(), "SUPPORTED_MODELS", [])
            except Exception:
                available = []
        if not isinstance(available, (list, tuple, set)):
            available = list(available) if available and hasattr(available, "__iter__") and not isinstance(available, str) else []
        if available and model_name not in available:
            raise APIError(
                f"Model '{model_name}' not supported by TTS provider '{provider_class.__name__}'. Available models: {available}",
                HTTP_404_NOT_FOUND,
                "model_not_found",
                param="model"
            )

    return provider_class, model_name


def get_tts_provider_instance(provider_class: Any):
    """Return a cached instance of the TTS provider, creating it if needed."""
    key = provider_class.__name__
    instance = tts_provider_instances.get(key)
    if instance is None:
        try:
            instance = provider_class()
        except TypeError as e:
            if "abstract class" in str(e):
                from .exceptions import APIError
                raise APIError(
                    f"Provider misconfiguration: Cannot instantiate abstract class '{provider_class.__name__}'. Please check the provider implementation.",
                    HTTP_500_INTERNAL_SERVER_ERROR,
                    "provider_error",
                )
            raise
        tts_provider_instances[key] = instance
    return instance
