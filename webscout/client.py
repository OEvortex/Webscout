"""
Webscout Unified Client Interface

A unified client for webscout that provides a simple interface
to interact with multiple AI providers for chat completions and image generation.

Features:
- Automatic provider failover
- Support for specifying exact provider
- Intelligent model resolution (auto, provider/model, or model name)
- Caching of provider instances
- Full streaming support
"""

import difflib
import importlib
import inspect
import pkgutil
import random
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Type, Union, cast

from webscout.Provider.OPENAI.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    Tool,
)
from webscout.Provider.OPENAI.utils import (
    ChatCompletion,
    ChatCompletionChunk,
)
from webscout.Provider.TTI.base import BaseImages, TTICompatibleProvider
from webscout.Provider.TTI.utils import ImageResponse


def load_openai_providers() -> Tuple[Dict[str, Type[OpenAICompatibleProvider]], Set[str]]:
    """
    Dynamically loads all OpenAI-compatible provider classes.
    """
    provider_map = {}
    auth_required_providers = set()

    try:
        provider_package = importlib.import_module("webscout.Provider.OPENAI")
        for _, module_name, _ in pkgutil.iter_modules(provider_package.__path__):
            if module_name.startswith(("base", "utils", "pydantic", "__")):
                continue
            try:
                module = importlib.import_module(f"webscout.Provider.OPENAI.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, OpenAICompatibleProvider)
                        and attr != OpenAICompatibleProvider
                        and not attr_name.startswith(("Base", "_"))
                    ):
                        provider_map[attr_name] = attr
                        if hasattr(attr, "required_auth") and attr.required_auth:
                            auth_required_providers.add(attr_name)
            except Exception:
                pass
    except Exception:
        pass
    return provider_map, auth_required_providers


def load_tti_providers() -> Tuple[Dict[str, Type[TTICompatibleProvider]], Set[str]]:
    """
    Dynamically loads all TTI provider classes.
    """
    provider_map = {}
    auth_required_providers = set()

    try:
        provider_package = importlib.import_module("webscout.Provider.TTI")
        for _, module_name, _ in pkgutil.iter_modules(provider_package.__path__):
            if module_name.startswith(("base", "utils", "__")):
                continue
            try:
                module = importlib.import_module(f"webscout.Provider.TTI.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, TTICompatibleProvider)
                        and attr != TTICompatibleProvider
                        and not attr_name.startswith(("Base", "_"))
                    ):
                        provider_map[attr_name] = attr
                        if hasattr(attr, "required_auth") and attr.required_auth:
                            auth_required_providers.add(attr_name)
            except Exception:
                pass
    except Exception:
        pass
    return provider_map, auth_required_providers


OPENAI_PROVIDERS, OPENAI_AUTH_REQUIRED = load_openai_providers()
TTI_PROVIDERS, TTI_AUTH_REQUIRED = load_tti_providers()


def _get_models_safely(provider_cls: type, client: Optional["Client"] = None) -> List[str]:
    """
    Safely get the list of available models from a provider using models.list().
    Utilizes client cache if available.
    """
    models = []

    try:
        instance = None
        if client:
            p_name = provider_cls.__name__
            if p_name in client._provider_cache:
                instance = client._provider_cache[p_name]
            else:
                try:
                    init_kwargs = {}
                    if client.proxies:
                        init_kwargs["proxies"] = client.proxies
                    if client.api_key:
                        init_kwargs["api_key"] = client.api_key
                    instance = provider_cls(**init_kwargs)
                except Exception:
                    try:
                        instance = provider_cls()
                    except Exception:
                        pass

                if instance:
                    client._provider_cache[p_name] = instance
        else:
            try:
                instance = provider_cls()
            except Exception:
                pass

        if instance and hasattr(instance, "models") and hasattr(instance.models, "list"):
            res = instance.models.list()
            if isinstance(res, list):
                for m in res:
                    if isinstance(m, str):
                        models.append(m)
                    elif isinstance(m, dict) and "id" in m:
                        models.append(m["id"])
    except Exception:
        pass

    return models


class ClientCompletions(BaseCompletions):
    """
    Unified completions interface with automatic provider and model resolution.
    """

    def __init__(self, client: "Client"):
        self._client = client
        self._last_provider: Optional[str] = None

    @property
    def last_provider(self) -> Optional[str]:
        """Returns the name of the last successfully used provider."""
        return self._last_provider

    def _get_provider_instance(
        self, provider_class: Type[OpenAICompatibleProvider], **kwargs
    ) -> OpenAICompatibleProvider:
        """Retrieves or creates a provider instance, utilizing the client cache."""
        p_name = provider_class.__name__
        if p_name in self._client._provider_cache:
            return self._client._provider_cache[p_name]

        init_kwargs = {}
        if self._client.proxies:
            init_kwargs["proxies"] = self._client.proxies
        if self._client.api_key:
            init_kwargs["api_key"] = self._client.api_key
        init_kwargs.update(kwargs)

        try:
            instance = provider_class(**init_kwargs)
            self._client._provider_cache[p_name] = instance
            return instance
        except Exception:
            try:
                instance = provider_class()
                self._client._provider_cache[p_name] = instance
                return instance
            except Exception as e:
                raise RuntimeError(f"Failed to initialize provider {provider_class.__name__}: {e}")

    def _fuzzy_resolve_provider_and_model(
        self, model: str
    ) -> Optional[Tuple[Type[OpenAICompatibleProvider], str]]:
        """
        Performs enhanced fuzzy search to find the closest model match across all providers.
        """
        available = self._get_available_providers()
        model_to_provider = {}

        for p_name, p_cls in available:
            p_models = _get_models_safely(p_cls, self._client)
            for m in p_models:
                if m not in model_to_provider:
                    model_to_provider[m] = p_cls

        if not model_to_provider:
            return None

        # 1. Exact case-insensitive match
        for m_name in model_to_provider:
            if m_name.lower() == model.lower():
                return model_to_provider[m_name], m_name

        # 2. Substring match
        for m_name in model_to_provider:
            if model.lower() in m_name.lower() or m_name.lower() in model.lower():
                if self._client.print_provider_info:
                    print(f"\033[1;33mSubstring match: '{model}' -> '{m_name}'\033[0m")
                return model_to_provider[m_name], m_name

        # 3. Fuzzy match with difflib
        matches = difflib.get_close_matches(model, model_to_provider.keys(), n=1, cutoff=0.5)
        if matches:
            matched_model = matches[0]
            if self._client.print_provider_info:
                print(f"\033[1;33mFuzzy match: '{model}' -> '{matched_model}'\033[0m")
            return model_to_provider[matched_model], matched_model
        return None

    def _resolve_provider_and_model(
        self, model: str, provider: Optional[Type[OpenAICompatibleProvider]]
    ) -> Tuple[Type[OpenAICompatibleProvider], str]:
        """
        Resolves the best provider and model name based on input.
        """
        if "/" in model:
            p_name, m_name = model.split("/", 1)
            found_p = next(
                (cls for name, cls in OPENAI_PROVIDERS.items() if name.lower() == p_name.lower()),
                None,
            )
            if found_p:
                return found_p, m_name

        if provider:
            resolved_model = model
            if model == "auto":
                p_models = _get_models_safely(provider, self._client)
                if p_models:
                    resolved_model = random.choice(p_models)
                else:
                    raise RuntimeError(f"Provider {provider.__name__} has no available models.")
            return provider, resolved_model

        if model == "auto":
            available = self._get_available_providers()
            if not available:
                raise RuntimeError("No available chat providers found.")

            providers_with_models = []
            for name, cls in available:
                p_models = _get_models_safely(cls, self._client)
                if p_models:
                    providers_with_models.append((cls, p_models))

            if providers_with_models:
                p_cls, p_models = random.choice(providers_with_models)
                m_name = random.choice(p_models)
                return p_cls, m_name
            else:
                raise RuntimeError("No available chat providers with models found.")

        available = self._get_available_providers()
        for p_name, p_cls in available:
            p_models = _get_models_safely(p_cls, self._client)
            if p_models and model in p_models:
                return p_cls, model

        fuzzy_result = self._fuzzy_resolve_provider_and_model(model)
        if fuzzy_result:
            return fuzzy_result

        if available:
            random.shuffle(available)
            return available[0][1], model

        raise RuntimeError(f"No providers found for model '{model}'")

    def _get_available_providers(self) -> List[Tuple[str, Type[OpenAICompatibleProvider]]]:
        """Returns a list of providers that are currently available to the client."""
        exclude = set(self._client.exclude or [])
        if self._client.api_key:
            return [(name, cls) for name, cls in OPENAI_PROVIDERS.items() if name not in exclude]
        return [
            (name, cls)
            for name, cls in OPENAI_PROVIDERS.items()
            if name not in OPENAI_AUTH_REQUIRED and name not in exclude
        ]

    def create(
        self,
        *,
        model: str = "auto",
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Union[Tool, Dict[str, Any]]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: Optional[int] = None,
        proxies: Optional[dict] = None,
        provider: Optional[Type[OpenAICompatibleProvider]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a chat completion with automatic failover and intelligent resolution.
        """
        try:
            resolved_provider, resolved_model = self._resolve_provider_and_model(model, provider)
        except Exception:
            resolved_provider, resolved_model = None, model

        call_kwargs = {
            "model": resolved_model,
            "messages": messages,
            "stream": stream,
        }
        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        if top_p is not None:
            call_kwargs["top_p"] = top_p
        if tools is not None:
            call_kwargs["tools"] = tools
        if tool_choice is not None:
            call_kwargs["tool_choice"] = tool_choice
        if timeout is not None:
            call_kwargs["timeout"] = timeout
        if proxies is not None:
            call_kwargs["proxies"] = proxies
        call_kwargs.update(kwargs)

        if resolved_provider:
            try:
                provider_instance = self._get_provider_instance(resolved_provider)
                response = provider_instance.chat.completions.create(
                    **cast(Dict[str, Any], call_kwargs)
                )

                if stream and inspect.isgenerator(response):
                    try:
                        first_chunk = next(response)
                        self._last_provider = resolved_provider.__name__

                        def _chained_gen_stream(
                            first: ChatCompletionChunk,
                            rest: Generator[ChatCompletionChunk, None, None],
                            pname: str,
                        ) -> Generator[ChatCompletionChunk, None, None]:
                            if self._client.print_provider_info:
                                print(f"\033[1;34m{pname}:{resolved_model}\033[0m\n")
                            yield first
                            yield from rest

                        return _chained_gen_stream(
                            first_chunk, response, resolved_provider.__name__
                        )
                    except StopIteration:
                        pass
                    except Exception:
                        pass
                else:
                    # Type narrowing for non-streaming response
                    if not inspect.isgenerator(response):
                        completion_response = cast(ChatCompletion, response)
                        if (
                            completion_response
                            and hasattr(completion_response, "choices")
                            and completion_response.choices
                            and completion_response.choices[0].message
                            and completion_response.choices[0].message.content
                            and completion_response.choices[0].message.content.strip()
                        ):
                            self._last_provider = resolved_provider.__name__
                            if self._client.print_provider_info:
                                print(
                                    f"\033[1;34m{resolved_provider.__name__}:{resolved_model}\033[0m\n"
                                )
                            return completion_response
                        else:
                            raise ValueError(
                                f"Provider {resolved_provider.__name__} returned empty content"
                            )
            except Exception:
                pass

        all_available = self._get_available_providers()
        tier1, tier2, tier3 = [], [], []
        base_model = model.split("/")[-1] if "/" in model else model
        search_models = {base_model, resolved_model} if resolved_model else {base_model}

        for p_name, p_cls in all_available:
            if p_cls == resolved_provider:
                continue

            p_models = _get_models_safely(p_cls, self._client)
            if not p_models:
                fallback_model = (
                    base_model
                    if base_model != "auto"
                    else (p_models[0] if p_models else base_model)
                )
                tier3.append((p_name, p_cls, fallback_model))
                continue

            found_exact = False
            for sm in search_models:
                if sm != "auto" and sm in p_models:
                    tier1.append((p_name, p_cls, sm))
                    found_exact = True
                    break
            if found_exact:
                continue

            if base_model != "auto":
                matches = difflib.get_close_matches(base_model, p_models, n=1, cutoff=0.5)
                if matches:
                    tier2.append((p_name, p_cls, matches[0]))
                    continue

            tier3.append((p_name, p_cls, random.choice(p_models)))

        random.shuffle(tier1)
        random.shuffle(tier2)
        random.shuffle(tier3)
        fallback_queue = tier1 + tier2 + tier3

        errors = []
        for p_name, p_cls, p_model in fallback_queue:
            try:
                provider_instance = self._get_provider_instance(p_cls)
                fallback_kwargs = cast(
                    Dict[str, Any], {**call_kwargs, "model": p_model}
                )
                response = provider_instance.chat.completions.create(**fallback_kwargs)

                if stream and inspect.isgenerator(response):
                    try:
                        first_chunk = next(response)
                        self._last_provider = p_name

                        def _chained_gen_fallback(first, rest, pname, mname):
                            if self._client.print_provider_info:
                                print(f"\033[1;34m{pname}:{mname} (Fallback)\033[0m\n")
                            yield first
                            yield from rest

                        return _chained_gen_fallback(first_chunk, response, p_name, p_model)
                    except (StopIteration, Exception):
                        continue

                if not inspect.isgenerator(response):
                    completion_response = cast(ChatCompletion, response)
                    if (
                        completion_response
                        and hasattr(completion_response, "choices")
                        and completion_response.choices
                        and completion_response.choices[0].message
                        and completion_response.choices[0].message.content
                        and completion_response.choices[0].message.content.strip()
                    ):
                        self._last_provider = p_name
                        if self._client.print_provider_info:
                            print(f"\033[1;34m{p_name}:{p_model} (Fallback)\033[0m\n")
                        return completion_response
                    else:
                        errors.append(f"{p_name}: Returned empty response.")
                        continue
            except Exception as e:
                errors.append(f"{p_name}: {str(e)}")
                continue

        raise RuntimeError(f"All chat providers failed. Errors: {'; '.join(errors[:3])}")


class ClientChat(BaseChat):
    """
    Standard chat interface for the client.
    """

    def __init__(self, client: "Client"):
        self.completions = ClientCompletions(client)


class ClientImages(BaseImages):
    """
    Unified image generation interface with automatic resolution and caching.
    """

    def __init__(self, client: "Client"):
        self._client = client
        self._last_provider: Optional[str] = None

    @property
    def last_provider(self) -> Optional[str]:
        """Returns the name of the last successfully used image provider."""
        return self._last_provider

    def _get_provider_instance(
        self, provider_class: Type[TTICompatibleProvider], **kwargs
    ) -> TTICompatibleProvider:
        """Retrieves or creates a TTI provider instance, utilizing the client cache."""
        p_name = provider_class.__name__
        if p_name in self._client._provider_cache:
            return self._client._provider_cache[p_name]

        init_kwargs = {}
        if self._client.proxies:
            init_kwargs["proxies"] = self._client.proxies
        init_kwargs.update(kwargs)

        try:
            instance = provider_class(**init_kwargs)
            self._client._provider_cache[p_name] = instance
            return instance
        except Exception:
            try:
                instance = provider_class()
                self._client._provider_cache[p_name] = instance
                return instance
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize TTI provider {provider_class.__name__}: {e}"
                )

    def _fuzzy_resolve_provider_and_model(
        self, model: str
    ) -> Optional[Tuple[Type[TTICompatibleProvider], str]]:
        """Performs enhanced fuzzy search to find the closest image model match across all providers."""
        available = self._get_available_providers()
        model_to_provider = {}

        for p_name, p_cls in available:
            p_models = _get_models_safely(p_cls, self._client)
            for m in p_models:
                if m not in model_to_provider:
                    model_to_provider[m] = p_cls

        if not model_to_provider:
            return None

        # 1. Exact match
        for m_name in model_to_provider:
            if m_name.lower() == model.lower():
                return model_to_provider[m_name], m_name

        # 2. Substring match
        for m_name in model_to_provider:
            if model.lower() in m_name.lower() or m_name.lower() in model.lower():
                if self._client.print_provider_info:
                    print(f"\033[1;33mSubstring match (TTI): '{model}' -> '{m_name}'\033[0m")
                return model_to_provider[m_name], m_name

        # 3. Fuzzy match
        matches = difflib.get_close_matches(model, model_to_provider.keys(), n=1, cutoff=0.5)
        if matches:
            matched_model = matches[0]
            if self._client.print_provider_info:
                print(f"\033[1;33mFuzzy match (TTI): '{model}' -> '{matched_model}'\033[0m")
            return model_to_provider[matched_model], matched_model
        return None

    def _resolve_provider_and_model(
        self, model: str, provider: Optional[Type[TTICompatibleProvider]]
    ) -> Tuple[Type[TTICompatibleProvider], str]:
        """Resolves the best provider and model name for image generation."""
        if "/" in model:
            p_name, m_name = model.split("/", 1)
            found_p = next(
                (cls for name, cls in TTI_PROVIDERS.items() if name.lower() == p_name.lower()), None
            )
            if found_p:
                return found_p, m_name

        if provider:
            resolved_model = model
            if model == "auto":
                p_models = _get_models_safely(provider, self._client)
                if p_models:
                    resolved_model = random.choice(p_models)
                else:
                    raise RuntimeError(f"TTI Provider {provider.__name__} has no available models.")
            return provider, resolved_model

        if model == "auto":
            available = self._get_available_providers()
            if not available:
                raise RuntimeError("No available image providers found.")

            providers_with_models = []
            for name, cls in available:
                p_models = _get_models_safely(cls, self._client)
                if p_models:
                    providers_with_models.append((cls, p_models))

            if providers_with_models:
                p_cls, p_models = random.choice(providers_with_models)
                return p_cls, random.choice(p_models)
            else:
                raise RuntimeError("No available image providers with models found.")

        available = self._get_available_providers()
        for p_name, p_cls in available:
            p_models = _get_models_safely(p_cls, self._client)
            if p_models and model in p_models:
                return p_cls, model

        fuzzy_result = self._fuzzy_resolve_provider_and_model(model)
        if fuzzy_result:
            return fuzzy_result

        if available:
            random.shuffle(available)
            return available[0][1], model
        raise RuntimeError(f"No image providers found for model '{model}'")

    def _get_available_providers(self) -> List[Tuple[str, Type[TTICompatibleProvider]]]:
        """Returns a list of image providers that are currently available."""
        exclude = set(self._client.exclude_images or [])
        if self._client.api_key:
            return [(name, cls) for name, cls in TTI_PROVIDERS.items() if name not in exclude]
        return [
            (name, cls)
            for name, cls in TTI_PROVIDERS.items()
            if name not in TTI_AUTH_REQUIRED and name not in exclude
        ]

    def generate(
        self,
        *,
        prompt: str,
        model: str = "auto",
        n: int = 1,
        size: str = "1024x1024",
        response_format: str = "url",
        provider: Optional[Type[TTICompatibleProvider]] = None,
        **kwargs: Any,
    ) -> ImageResponse:
        """Generates images with automatic failover and resolution."""
        try:
            resolved_provider, resolved_model = self._resolve_provider_and_model(model, provider)
        except Exception:
            resolved_provider, resolved_model = None, model

        call_kwargs = {
            "prompt": prompt,
            "model": resolved_model,
            "n": n,
            "size": size,
            "response_format": response_format,
        }
        call_kwargs.update(kwargs)

        if resolved_provider:
            try:
                provider_instance = self._get_provider_instance(resolved_provider)
                response = provider_instance.images.create(
                    **cast(Dict[str, Any], call_kwargs)
                )
                self._last_provider = resolved_provider.__name__
                if self._client.print_provider_info:
                    print(f"\033[1;34m{resolved_provider.__name__}:{resolved_model}\033[0m\n")
                return response
            except Exception:
                pass

        all_available = self._get_available_providers()
        tier1, tier2, tier3 = [], [], []
        base_model = model.split("/")[-1] if "/" in model else model
        search_models = {base_model, resolved_model} if resolved_model else {base_model}

        for p_name, p_cls in all_available:
            if p_cls == resolved_provider:
                continue

            p_models = _get_models_safely(p_cls, self._client)
            if not p_models:
                fallback_model = (
                    base_model
                    if base_model != "auto"
                    else (p_models[0] if p_models else base_model)
                )
                tier3.append((p_name, p_cls, fallback_model))
                continue

            found_exact = False
            for sm in search_models:
                if sm != "auto" and sm in p_models:
                    tier1.append((p_name, p_cls, sm))
                    found_exact = True
                    break
            if found_exact:
                continue

            if base_model != "auto":
                matches = difflib.get_close_matches(base_model, p_models, n=1, cutoff=0.5)
                if matches:
                    tier2.append((p_name, p_cls, matches[0]))
                    continue

            tier3.append((p_name, p_cls, random.choice(p_models)))

        random.shuffle(tier1)
        random.shuffle(tier2)
        random.shuffle(tier3)
        fallback_queue = tier1 + tier2 + tier3

        for p_name, p_cls, p_model in fallback_queue:
            try:
                provider_instance = self._get_provider_instance(p_cls)
                fallback_kwargs = cast(
                    Dict[str, Any], {**call_kwargs, "model": p_model}
                )
                response = provider_instance.images.create(**fallback_kwargs)
                self._last_provider = p_name
                if self._client.print_provider_info:
                    print(f"\033[1;34m{p_name}:{p_model} (Fallback)\033[0m\n")
                return response
            except Exception:
                continue
        raise RuntimeError("All image providers failed.")

    def create(self, **kwargs) -> ImageResponse:
        """Alias for generate."""
        return self.generate(**kwargs)


class Client:
    """
    Unified Webscout Client for AI providers.
    Manages chat and image generation across multiple free and authenticated providers.
    """

    def __init__(
        self,
        provider: Optional[Type[OpenAICompatibleProvider]] = None,
        image_provider: Optional[Type[TTICompatibleProvider]] = None,
        api_key: Optional[str] = None,
        proxies: Optional[dict] = None,
        exclude: Optional[List[str]] = None,
        exclude_images: Optional[List[str]] = None,
        print_provider_info: bool = False,
        **kwargs: Any,
    ):
        """
        Initialize the Webscout client.
        """
        self.provider = provider
        self.image_provider = image_provider
        self.api_key = api_key
        self.proxies = proxies or {}
        self.exclude = [e.upper() if e else e for e in (exclude or [])]
        self.exclude_images = [e.upper() if e else e for e in (exclude_images or [])]
        self.print_provider_info = print_provider_info
        self.kwargs = kwargs

        self._provider_cache = {}
        self.chat = ClientChat(self)
        self.images = ClientImages(self)

    @staticmethod
    def get_chat_providers() -> List[str]:
        """Returns names of all chat providers."""
        return list(OPENAI_PROVIDERS.keys())

    @staticmethod
    def get_image_providers() -> List[str]:
        """Returns names of all image providers."""
        return list(TTI_PROVIDERS.keys())

    @staticmethod
    def get_free_chat_providers() -> List[str]:
        """Returns names of free chat providers."""
        return [name for name in OPENAI_PROVIDERS.keys() if name not in OPENAI_AUTH_REQUIRED]

    @staticmethod
    def get_free_image_providers() -> List[str]:
        """Returns names of free image providers."""
        return [name for name in TTI_PROVIDERS.keys() if name not in TTI_AUTH_REQUIRED]


try:
    from webscout.server.server import run_api as _run_api_impl
    from webscout.server.server import run_api as _start_server_impl

    def run_api(*args: Any, **kwargs: Any) -> Any:
        """Runs the FastAPI server."""
        return _run_api_impl(*args, **kwargs)

    def start_server(*args: Any, **kwargs: Any) -> Any:
        """Starts the FastAPI server."""
        return _start_server_impl(*args, **kwargs)

except ImportError:

    def run_api(*args: Any, **kwargs: Any) -> Any:
        """Runs the FastAPI server."""
        raise ImportError("webscout.server.server.run_api is not available.")

    def start_server(*args: Any, **kwargs: Any) -> Any:
        """Starts the FastAPI server."""
        raise ImportError("webscout.server.server.start_server is not available.")


if __name__ == "__main__":
    client = Client(print_provider_info=True)
    print("Testing auto resolution...")
    try:
        response = client.chat.completions.create(
            model="auto", messages=[{"role": "user", "content": "Hi"}]
        )
        if not inspect.isgenerator(response):
            completion = cast(ChatCompletion, response)
            if (
                completion
                and completion.choices
                and completion.choices[0].message
                and completion.choices[0].message.content
            ):
                print(f"Auto Result: {completion.choices[0].message.content[:50]}...")
            else:
                print("Auto Result: Empty response")
        else:
            print("Streaming response received")
    except Exception as e:
        print(f"Error: {e}")
