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

from webscout.Provider.Openai_comp.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    Tool,
)
from webscout.Provider.Openai_comp.utils import (
    ChatCompletion,
    ChatCompletionChunk,
)
from webscout.Provider.TTI.base import BaseImages, TTICompatibleProvider
from webscout.Provider.TTI.utils import ImageResponse


def load_openai_providers() -> Tuple[Dict[str, Type[OpenAICompatibleProvider]], Set[str]]:
    """
    Dynamically loads all OpenAI-compatible provider classes from the Openai_comp module.

    Scans the webscout.Provider.Openai_comp package and imports all subclasses of
    OpenAICompatibleProvider. Excludes base classes, utility modules, and private classes.

    Returns:
        A tuple containing:
        - A dictionary mapping provider class names to their class objects.
        - A set of provider names that require API authentication.

    Raises:
        No exceptions are raised; failures are silently handled to ensure robust loading.

    Examples:
        >>> providers, auth_required = load_openai_providers()
        >>> print(list(providers.keys())[:3])
        ['Claude', 'GPT4Free', 'OpenRouter']
        >>> print('Claude' in auth_required)
        True
    """
    provider_map = {}
    auth_required_providers = set()

    try:
        provider_package = importlib.import_module("webscout.Provider.Openai_comp")
        for _, module_name, _ in pkgutil.iter_modules(provider_package.__path__):
            if module_name.startswith(("base", "utils", "pydantic", "__")):
                continue
            try:
                module = importlib.import_module(f"webscout.Provider.Openai_comp.{module_name}")
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
    Dynamically loads all TTI (Text-to-Image) provider classes from the TTI module.

    Scans the webscout.Provider.TTI package and imports all subclasses of
    TTICompatibleProvider. Excludes base classes, utility modules, and private classes.

    Returns:
        A tuple containing:
        - A dictionary mapping TTI provider class names to their class objects.
        - A set of TTI provider names that require API authentication.

    Raises:
        No exceptions are raised; failures are silently handled to ensure robust loading.

    Examples:
        >>> providers, auth_required = load_tti_providers()
        >>> print('DALL-E' in providers)
        True
        >>> print('Stable Diffusion' in auth_required)
        False
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
    Safely retrieves the list of available models from a provider.

    Attempts to instantiate the provider class and call its models.list() method.
    If a Client instance is provided, uses the client's provider cache to avoid
    redundant instantiations. Handles all exceptions gracefully and returns an
    empty list if model retrieval fails.

    Args:
        provider_cls: The provider class to retrieve models from.
        client: Optional Client instance to use for caching and configuration.
                If provided, uses client's proxies and api_key for initialization.

    Returns:
        A list of available model identifiers (strings). Returns an empty list
        if the provider has no models or if instantiation fails.

    Note:
        This function silently handles all exceptions and will not raise errors.
        Model names are extracted from both string lists and dicts with 'id' keys.

    Examples:
        >>> from webscout.client import _get_models_safely, Client
        >>> client = Client()
        >>> from webscout.Provider.Openai_comp.some_provider import SomeProvider
        >>> models = _get_models_safely(SomeProvider, client)
        >>> print(models)
        ['gpt-4', 'gpt-3.5-turbo']
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
    Unified completions interface with intelligent provider and model resolution.

    This class manages chat completions by automatically selecting appropriate
    providers and models based on user input. It supports:
    - Automatic model discovery and fuzzy matching
    - Provider failover for reliability
    - Provider and model caching for performance
    - Streaming and non-streaming responses
    - Tools and function calling support

    Attributes:
        _client: Reference to the parent Client instance.
        _last_provider: Name of the last successfully used provider.

    Examples:
        >>> from webscout.client import Client
        >>> client = Client(print_provider_info=True)
        >>> response = client.chat.completions.create(
        ...     model="auto",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """

    def __init__(self, client: "Client"):
        self._client = client
        self._last_provider: Optional[str] = None

    @property
    def last_provider(self) -> Optional[str]:
        """
        Returns the name of the last successfully used provider.

        This property tracks which provider was most recently used to generate
        a completion. Useful for debugging and understanding which fallback
        providers are being utilized.

        Returns:
            The name of the last provider as a string, or None if no provider
            has been successfully used yet.

        Examples:
            >>> completions = client.chat.completions
            >>> response = completions.create(model="auto", messages=[...])
            >>> print(completions.last_provider)
            'GPT4Free'
        """
        return self._last_provider

    def _get_provider_instance(
        self, provider_class: Type[OpenAICompatibleProvider], **kwargs
    ) -> OpenAICompatibleProvider:
        """
        Retrieves or creates a cached provider instance.

        Checks if a provider instance already exists in the client's cache.
        If not, initializes a new instance with client-level configuration
        (proxies, api_key) merged with any additional kwargs.

        Args:
            provider_class: The OpenAI-compatible provider class to instantiate.
            **kwargs: Additional keyword arguments to pass to the provider's constructor.

        Returns:
            An instantiated and initialized provider instance.

        Raises:
            RuntimeError: If the provider cannot be initialized with or without
                         client configuration.

        Examples:
            >>> from webscout.Provider.Openai_comp.gpt4free import GPT4Free
            >>> completions = client.chat.completions
            >>> instance = completions._get_provider_instance(GPT4Free)
        """
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
        Performs fuzzy matching to find the closest model match across all providers.

        Attempts three levels of matching:
        1. Exact case-insensitive match
        2. Substring match (model contains query or vice versa)
        3. Fuzzy match using difflib with 50% cutoff

        Args:
            model: The model name or partial name to search for.

        Returns:
            A tuple of (provider_class, resolved_model_name) if a match is found,
            or None if no suitable match is found.

        Note:
            Prints informational messages if client.print_provider_info is enabled.

        Examples:
            >>> result = completions._fuzzy_resolve_provider_and_model("gpt-4")
            >>> if result:
            ...     provider_cls, model_name = result
            ...     print(f"Found: {model_name} via {provider_cls.__name__}")
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
        Resolves the best provider and model name based on input specifications.

        Handles multiple input formats:
        - "provider/model" format: Parses and resolves to exact provider
        - "auto": Randomly selects an available provider and model
        - Named model: Searches across all providers for exact or fuzzy match

        Resolution strategy:
        1. If "provider/model" format, find provider by name
        2. If provider specified, use it with given or auto-selected model
        3. If "auto", randomly select from available providers and models
        4. Otherwise, search across providers for exact match
        5. Fall back to fuzzy matching
        6. Finally, randomly select from available providers

        Args:
            model: Model identifier. Can be "auto", "provider/model", or model name.
            provider: Optional provider class to constrain resolution.

        Returns:
            A tuple of (provider_class, resolved_model_name).

        Raises:
            RuntimeError: If no providers are available or model cannot be resolved.

        Examples:
            >>> # Auto resolution
            >>> p_cls, m_name = completions._resolve_provider_and_model("auto", None)
            >>> # Explicit provider/model
            >>> p_cls, m_name = completions._resolve_provider_and_model(
            ...     "GPT4Free/gpt-3.5-turbo", None
            ... )
            >>> # Model name fuzzy matching
            >>> p_cls, m_name = completions._resolve_provider_and_model("gpt-4", None)
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
        """
        Returns a list of available chat providers for the current client configuration.

        Filters the global provider registry based on:
        - Client's exclude list
        - API key availability (if api_key is set, includes auth-required providers)

        Returns:
            A list of tuples containing (provider_name, provider_class) pairs
            for all available providers.

        Examples:
            >>> providers = completions._get_available_providers()
            >>> print([p[0] for p in providers])
            ['GPT4Free', 'OpenRouter', 'Groq']
        """
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
        Creates a chat completion with automatic provider selection and failover.

        Attempts to resolve the specified model to a provider and model name,
        then creates a completion. If the initial attempt fails, automatically
        falls back to other available providers, prioritizing:
        1. Providers with exact model matches
        2. Providers with fuzzy model matches
        3. Providers with any available model

        Args:
            model: Model identifier. Default "auto" randomly selects available models.
                   Can be "provider/model" format or model name. Required.
            messages: List of message dicts with 'role' and 'content' keys. Required.
            max_tokens: Maximum tokens in the response. Optional.
            stream: Whether to stream the response. Default is False.
            temperature: Sampling temperature (0-2). Controls response randomness. Optional.
            top_p: Nucleus sampling parameter (0-1). Optional.
            tools: List of tools or tool definitions for function calling. Optional.
            tool_choice: Which tool to use or how to select tools. Optional.
            timeout: Request timeout in seconds. Optional.
            proxies: HTTP proxy configuration dict. Optional.
            provider: Specific provider class to use. Optional.
            **kwargs: Additional arguments passed to the provider.

        Returns:
            ChatCompletion object for non-streaming requests.
            Generator[ChatCompletionChunk, None, None] for streaming requests.

        Raises:
            RuntimeError: If all chat providers fail or no providers are available.

        Note:
            If print_provider_info is True, provider name and model are printed
            to stdout in color-formatted text. Streaming responses print on first chunk.

        Examples:
            >>> client = Client(print_provider_info=True)
            >>> response = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[{"role": "user", "content": "Hello!"}]
            ... )
            >>> print(response.choices[0].message.content)

            >>> # Streaming example
            >>> for chunk in client.chat.completions.create(
            ...     model="auto",
            ...     messages=[{"role": "user", "content": "Hello!"}],
            ...     stream=True
            ... ):
            ...     print(chunk.choices[0].delta.content, end="")
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
    Standard chat interface wrapper for the Client.

    Provides access to chat completions through a completions property that
    implements the BaseChat interface. Acts as an adapter between the Client
    and the underlying OpenAI-compatible completion system.

    Attributes:
        completions: ClientCompletions instance for creating chat completions.

    Examples:
        >>> chat = client.chat
        >>> response = chat.completions.create(
        ...     model="auto",
        ...     messages=[{"role": "user", "content": "Hi"}]
        ... )
    """

    def __init__(self, client: "Client"):
        self.completions = ClientCompletions(client)


class ClientImages(BaseImages):
    """
    Unified image generation interface with automatic provider selection and failover.

    Manages text-to-image (TTI) generation by automatically selecting appropriate
    providers and models based on user input. Implements similar resolution and
    failover logic as ClientCompletions but for image generation.

    Features:
    - Automatic model discovery and fuzzy matching
    - Provider failover for reliability
    - Provider and model caching for performance
    - Structured parameter validation
    - Support for multiple image output formats

    Attributes:
        _client: Reference to the parent Client instance.
        _last_provider: Name of the last successfully used image provider.

    Examples:
        >>> client = Client(print_provider_info=True)
        >>> response = client.images.generate(
        ...     prompt="A beautiful sunset",
        ...     model="auto",
        ...     n=1,
        ...     size="1024x1024"
        ... )
        >>> print(response.data[0].url)
    """

    def __init__(self, client: "Client"):
        self._client = client
        self._last_provider: Optional[str] = None

    @property
    def last_provider(self) -> Optional[str]:
        """
        Returns the name of the last successfully used image provider.

        Tracks which TTI provider was most recently used to generate images.
        Useful for debugging and understanding which fallback providers are
        being utilized.

        Returns:
            The name of the last provider as a string, or None if no provider
            has been successfully used yet.

        Examples:
            >>> images = client.images
            >>> response = images.generate(prompt="...", model="auto")
            >>> print(images.last_provider)
            'StableDiffusion'
        """
        return self._last_provider

    def _get_provider_instance(
        self, provider_class: Type[TTICompatibleProvider], **kwargs
    ) -> TTICompatibleProvider:
        """
        Retrieves or creates a cached TTI provider instance.

        Checks if a TTI provider instance already exists in the client's cache.
        If not, initializes a new instance with client-level configuration
        (proxies) merged with any additional kwargs.

        Args:
            provider_class: The TTI-compatible provider class to instantiate.
            **kwargs: Additional keyword arguments to pass to the provider's constructor.

        Returns:
            An instantiated and initialized TTI provider instance.

        Raises:
            RuntimeError: If the provider cannot be initialized with or without
                         client configuration.

        Examples:
            >>> from webscout.Provider.TTI.dalle import DALLE
            >>> images = client.images
            >>> instance = images._get_provider_instance(DALLE)
        """
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
        """
        Performs fuzzy matching to find the closest image model match across providers.

        Attempts three levels of matching:
        1. Exact case-insensitive match
        2. Substring match (model contains query or vice versa)
        3. Fuzzy match using difflib with 50% cutoff

        Args:
            model: The model name or partial name to search for.

        Returns:
            A tuple of (provider_class, resolved_model_name) if a match is found,
            or None if no suitable match is found.

        Note:
            Prints informational messages if client.print_provider_info is enabled.

        Examples:
            >>> result = images._fuzzy_resolve_provider_and_model("dall-e")
            >>> if result:
            ...     provider_cls, model_name = result
            ...     print(f"Found: {model_name} via {provider_cls.__name__}")
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
        """
        Resolves the best TTI provider and model name based on input specifications.

        Handles multiple input formats:
        - "provider/model" format: Parses and resolves to exact provider
        - "auto": Randomly selects an available provider and model
        - Named model: Searches across all providers for exact or fuzzy match

        Resolution strategy:
        1. If "provider/model" format, find provider by name
        2. If provider specified, use it with given or auto-selected model
        3. If "auto", randomly select from available providers and models
        4. Otherwise, search across providers for exact match
        5. Fall back to fuzzy matching
        6. Finally, randomly select from available providers

        Args:
            model: Model identifier. Can be "auto", "provider/model", or model name.
            provider: Optional TTI provider class to constrain resolution.

        Returns:
            A tuple of (provider_class, resolved_model_name).

        Raises:
            RuntimeError: If no providers are available or model cannot be resolved.

        Examples:
            >>> # Auto resolution
            >>> p_cls, m_name = images._resolve_provider_and_model("auto", None)
            >>> # Explicit provider/model
            >>> p_cls, m_name = images._resolve_provider_and_model(
            ...     "StableDiffusion/stable-diffusion-v1-5", None
            ... )
        """
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
        """
        Returns a list of available image providers for the current client configuration.

        Filters the global TTI provider registry based on:
        - Client's exclude_images list
        - API key availability (if api_key is set, includes auth-required providers)

        Returns:
            A list of tuples containing (provider_name, provider_class) pairs
            for all available image providers.

        Examples:
            >>> providers = images._get_available_providers()
            >>> print([p[0] for p in providers])
            ['StableDiffusion', 'DALL-E', 'Midjourney']
        """
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
        """
        Generates images with automatic provider selection and failover.

        Attempts to resolve the specified model to a provider and model name,
        then creates images. If the initial attempt fails, automatically falls
        back to other available providers, prioritizing:
        1. Providers with exact model matches
        2. Providers with fuzzy model matches
        3. Providers with any available model

        Args:
            prompt: Text description of the image(s) to generate. Required.
            model: Model identifier. Default "auto" randomly selects available models.
                   Can be "provider/model" format or model name.
            n: Number of images to generate. Default is 1.
            size: Image size specification (e.g., "1024x1024", "512x512"). Default is "1024x1024".
            response_format: Format for image response ("url" or "b64_json"). Default is "url".
            provider: Specific TTI provider class to use. Optional.
            **kwargs: Additional arguments passed to the provider.

        Returns:
            ImageResponse object containing generated images with URLs or base64 data.

        Raises:
            RuntimeError: If all image providers fail or no providers are available.

        Note:
            If print_provider_info is True, provider name and model are printed
            to stdout in color-formatted text.

        Examples:
            >>> client = Client(print_provider_info=True)
            >>> response = client.images.generate(
            ...     prompt="A beautiful sunset over mountains",
            ...     model="auto",
            ...     n=1,
            ...     size="1024x1024"
            ... )
            >>> print(response.data[0].url)

            >>> # Using specific provider
            >>> from webscout.Provider.TTI.stable import StableDiffusion
            >>> response = client.images.generate(
            ...     prompt="A cat wearing sunglasses",
            ...     provider=StableDiffusion
            ... )
        """
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
        """
        Alias for generate() method.

        Provides compatibility with OpenAI-style image API where create() is
        the standard method name for image generation.

        Args:
            **kwargs: All arguments accepted by generate().

        Returns:
            ImageResponse object containing generated images.

        Examples:
            >>> response = client.images.create(
            ...     prompt="A robot painting a picture",
            ...     model="auto"
            ... )
        """
        return self.generate(**kwargs)


class Client:
    """
    Unified Webscout Client for AI chat and image generation.

    A high-level client that provides a single interface for interacting with
    multiple AI providers (chat completions and image generation). Automatically
    selects, caches, and fails over between providers based on availability
    and model support.

    This client aims to provide a seamless, provider-agnostic experience by:
    - Supporting automatic provider selection and fallback
    - Caching provider instances for performance
    - Offering intelligent model resolution (auto, provider/model, or model name)
    - Handling authentication across multiple providers
    - Providing detailed provider information when enabled

    Attributes:
        provider: Optional default provider for chat completions.
        image_provider: Optional default provider for image generation.
        api_key: Optional API key for providers that support authentication.
        proxies: HTTP proxy configuration dictionary.
        exclude: List of provider names to exclude from chat completions.
        exclude_images: List of provider names to exclude from image generation.
        print_provider_info: Whether to print selected provider and model info.
        chat: ClientChat instance for chat completions.
        images: ClientImages instance for image generation.

    Examples:
        >>> # Basic usage with automatic provider selection
        >>> client = Client()
        >>> response = client.chat.completions.create(
        ...     model="auto",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.choices[0].message.content)

        >>> # With provider information and image generation
        >>> client = Client(print_provider_info=True)
        >>> chat_response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Describe an image"}]
        ... )
        >>> image_response = client.images.generate(
        ...     prompt="A sunset over mountains",
        ...     model="auto"
        ... )

        >>> # Excluding certain providers and using API key
        >>> client = Client(
        ...     api_key="your-api-key-here",
        ...     exclude=["BadProvider"],
        ...     exclude_images=["SlowProvider"]
        ... )
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
        Initialize the Webscout Client with optional configuration.

        Args:
            provider: Default provider class for chat completions. If specified,
                     this provider is prioritized in provider resolution. Optional.
            image_provider: Default provider class for image generation. If specified,
                           this provider is prioritized in image resolution. Optional.
            api_key: API key for authenticated providers. If provided, enables access
                    to providers that require authentication. Optional.
            proxies: Dictionary of proxy settings (e.g., {"http": "http://proxy:8080"}).
                    Applied to all provider requests. Optional.
            exclude: List of provider names to exclude from chat completion selection.
                    Names are case-insensitive. Optional.
            exclude_images: List of provider names to exclude from image generation selection.
                           Names are case-insensitive. Optional.
            print_provider_info: If True, prints selected provider name and model to stdout
                                before each request. Useful for debugging. Default is False.
            **kwargs: Additional keyword arguments stored for future use.

        Examples:
            >>> # Minimal setup - use default providers
            >>> client = Client()

            >>> # With authentication and custom settings
            >>> client = Client(
            ...     api_key="sk-1234567890abcdef",
            ...     proxies={"http": "http://proxy.example.com:8080"},
            ...     exclude=["UnreliableProvider"],
            ...     print_provider_info=True
            ... )

            >>> # With specific default providers
            >>> from webscout.Provider.Openai_comp.groq import Groq
            >>> from webscout.Provider.TTI.stable import StableDiffusion
            >>> client = Client(
            ...     provider=Groq,
            ...     image_provider=StableDiffusion
            ... )
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
        """
        Returns a list of all available chat provider names.

        Queries the global OPENAI_PROVIDERS registry that is populated
        at module load time. Names are not normalized and appear as
        defined in their respective classes.

        Returns:
            List of provider class names available for chat completions.

        Examples:
            >>> providers = Client.get_chat_providers()
            >>> print("GPT4Free" in providers)
            True
            >>> print(len(providers))
            42
        """
        return list(OPENAI_PROVIDERS.keys())

    @staticmethod
    def get_image_providers() -> List[str]:
        """
        Returns a list of all available image provider names.

        Queries the global TTI_PROVIDERS registry that is populated
        at module load time. Names are not normalized and appear as
        defined in their respective classes.

        Returns:
            List of provider class names available for image generation.

        Examples:
            >>> providers = Client.get_image_providers()
            >>> print("StableDiffusion" in providers)
            True
            >>> print(len(providers))
            8
        """
        return list(TTI_PROVIDERS.keys())

    @staticmethod
    def get_free_chat_providers() -> List[str]:
        """
        Returns a list of chat providers that don't require authentication.

        Filters the global OPENAI_PROVIDERS registry to include only providers
        where required_auth is False. These providers can be used without
        an API key.

        Returns:
            List of free chat provider class names.

        Examples:
            >>> free_providers = Client.get_free_chat_providers()
            >>> print("GPT4Free" in free_providers)
            True
            >>> print(len(free_providers))
            35
        """
        return [name for name in OPENAI_PROVIDERS.keys() if name not in OPENAI_AUTH_REQUIRED]

    @staticmethod
    def get_free_image_providers() -> List[str]:
        """
        Returns a list of image providers that don't require authentication.

        Filters the global TTI_PROVIDERS registry to include only providers
        where required_auth is False. These providers can be used without
        an API key.

        Returns:
            List of free image provider class names.

        Examples:
            >>> free_providers = Client.get_free_image_providers()
            >>> print("StableDiffusion" in free_providers)
            True
            >>> print(len(free_providers))
            6
        """
        return [name for name in TTI_PROVIDERS.keys() if name not in TTI_AUTH_REQUIRED]


try:
    from webscout.server.server import run_api as _run_api_impl
    from webscout.server.server import run_api as _start_server_impl

    def run_api(*args: Any, **kwargs: Any) -> Any:
        """
        Runs the FastAPI OpenAI-compatible API server.

        Delegates to webscout.server.server.run_api to start an OpenAI-compatible
        HTTP API server that provides chat and image endpoints. Requires the
        'api' optional dependencies to be installed.

        Args:
            *args: Positional arguments passed to the underlying run_api implementation.
            **kwargs: Keyword arguments passed to the underlying run_api implementation.
                     Common options include host, port, debug, and reload.

        Returns:
            The return value from the underlying FastAPI run function.

        Raises:
            ImportError: If webscout.server.server is not available.

        Examples:
            >>> from webscout.client import run_api
            >>> run_api(host="0.0.0.0", port=8000)
        """
        return _run_api_impl(*args, **kwargs)

    def start_server(*args: Any, **kwargs: Any) -> Any:
        """
        Starts the FastAPI OpenAI-compatible API server.

        Delegates to webscout.server.server.start_server to initialize and run
        an OpenAI-compatible HTTP API server. This is typically the main entry
        point for starting the webscout server in production or development.

        Args:
            *args: Positional arguments passed to the underlying start_server implementation.
            **kwargs: Keyword arguments passed to the underlying start_server implementation.
                     Common options include host, port, workers, and config paths.

        Returns:
            The return value from the underlying server implementation.

        Raises:
            ImportError: If webscout.server.server is not available.

        Examples:
            >>> from webscout.client import start_server
            >>> start_server()
        """
        return _start_server_impl(*args, **kwargs)

except ImportError:

    def run_api(*args: Any, **kwargs: Any) -> Any:
        """
        Runs the FastAPI OpenAI-compatible API server.

        Raises ImportError if the server module is not available.
        Install with: pip install webscout[api]

        Raises:
            ImportError: Always raised; server not available in current environment.
        """
        raise ImportError("webscout.server.server.run_api is not available.")

    def start_server(*args: Any, **kwargs: Any) -> Any:
        """
        Starts the FastAPI OpenAI-compatible API server.

        Raises ImportError if the server module is not available.
        Install with: pip install webscout[api]

        Raises:
            ImportError: Always raised; server not available in current environment.
        """
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
