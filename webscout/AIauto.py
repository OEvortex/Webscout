"""
This module provides the AUTO provider, which automatically selects and uses
an available LLM provider from the webscout library that doesn't require
API keys or cookies.
"""

import difflib
import importlib
import inspect
import pkgutil
import random
from typing import Any, Dict, Generator, List, Optional, Tuple, Type, Union

from webscout.AIbase import Provider, Response
from webscout.exceptions import AllProvidersFailure


def load_providers() -> Tuple[Dict[str, Type[Provider]], set]:
    """
    Dynamically loads all Provider classes from the `webscout.Provider` package.

    This function iterates through the modules in the `webscout.Provider` package,
    imports each module, and inspects its attributes to identify classes that
    inherit from the `Provider` base class. It also identifies providers that
    require special authentication parameters.

    Returns:
        Tuple[Dict[str, Type[Provider]], set]: A tuple containing two elements:
            - provider_map (Dict[str, Type[Provider]]): A dictionary mapping uppercase provider names to their classes.
            - api_key_providers (set): A set of uppercase provider names requiring special authentication.
    """
    provider_map: Dict[str, Type[Provider]] = {}
    api_key_providers: set = set()
    provider_package = importlib.import_module("webscout.Provider")

    for _, module_name, _ in pkgutil.iter_modules(provider_package.__path__):
        try:
            module = importlib.import_module(f"webscout.Provider.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Provider) and attr != Provider:
                    p_name = attr_name.upper()
                    provider_map[p_name] = attr

                    if hasattr(attr, "required_auth") and attr.required_auth:
                        api_key_providers.add(p_name)
                    else:
                        try:
                            sig = inspect.signature(attr.__init__).parameters
                            if any(k in sig for k in ('api_key', 'cookie_file', 'cookie_path', 'access_token')):
                                api_key_providers.add(p_name)
                        except (ValueError, TypeError):
                            pass
        except Exception:
            pass
    return provider_map, api_key_providers

def _get_models_safely(provider_cls: type) -> List[str]:
    """
    Safely retrieves the list of available models from a provider class.

    This function attempts to find model information through the `AVAILABLE_MODELS`
    attribute or by calling the `get_models` class method. It handles potential
    errors gracefully to ensure the loading process is not interrupted.

    Args:
        provider_cls (type): The provider class to inspect.

    Returns:
        List[str]: A list of unique model names supported by the provider.
    """
    models = []
    try:
        if hasattr(provider_cls, "AVAILABLE_MODELS"):
            val = getattr(provider_cls, "AVAILABLE_MODELS")
            if isinstance(val, list):
                models.extend(val)

        if hasattr(provider_cls, "get_models"):
            try:
                # Use getattr to call the class method safely
                get_models_method = getattr(provider_cls, "get_models")
                if callable(get_models_method):
                    res = get_models_method()
                    if isinstance(res, list):
                        models.extend(res)
            except Exception:
                pass
    except Exception:
        pass
    return list(set(models))

provider_map, api_key_providers = load_providers()

class AUTO(Provider):
    """
    An automatic provider that intelligently selects and utilizes an available
    LLM provider from the webscout library.

    It cycles through available free providers
    until one successfully processes the request. Excludes providers
    requiring API keys or cookies by default.
    """
    def __init__(
        self,
        model: str = "auto",
        api_key: Optional[str] = None,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        exclude: Optional[List[str]] = None,
        print_provider_info: bool = False,
        **kwargs: Any,
    ):
        """
        Initializes the AUTO provider, setting up the parameters for provider selection and request handling.

        This constructor initializes the AUTO provider with various configuration options,
        including conversation settings, request limits, and provider exclusions.

        Args:
            model (str): The model to use. Defaults to "auto".
            api_key (str, optional): API key for providers that require it. Defaults to None.
            is_conversation (bool): Flag for conversational mode. Defaults to True.
            max_tokens (int): Maximum tokens for the response. Defaults to 600.
            timeout (int): Request timeout in seconds. Defaults to 30.
            intro (str, optional): Introductory prompt. Defaults to None.
            filepath (str, optional): Path for conversation history. Defaults to None.
            update_file (bool): Whether to update the history file. Defaults to True.
            proxies (dict): Proxies for requests. Defaults to {}.
            history_offset (int): History character offset limit. Defaults to 10250.
            act (str, optional): Awesome prompt key. Defaults to None.
            exclude (Optional[list[str]]): List of provider names (uppercase) to exclude. Defaults to None.
            print_provider_info (bool): Whether to print the name of the successful provider. Defaults to False.
            **kwargs: Additional keyword arguments for providers.
        """
        self.provider: Optional[Provider] = None
        self.provider_name: Optional[str] = None
        self.model: str = model
        self.api_key: Optional[str] = api_key
        self.is_conversation: bool = is_conversation
        self.max_tokens: int = max_tokens
        self.timeout: int = timeout
        self.intro: Optional[str] = intro
        self.filepath: Optional[str] = filepath
        self.update_file: bool = update_file
        self.proxies: dict = proxies
        self.history_offset: int = history_offset
        self.act: Optional[str] = act
        self.exclude: list[str] = [e.upper() for e in exclude] if exclude else []
        self.print_provider_info: bool = print_provider_info
        self.kwargs: dict = kwargs


    @property
    def last_response(self) -> Dict[str, Any]:
        """
        Retrieves the last response dictionary from the successfully used provider.

        Returns:
            dict[str, Any]: The last response dictionary, or an empty dictionary if no provider has been used yet.
        """
        return self.provider.last_response if self.provider else {}

    @last_response.setter
    def last_response(self, value: Dict[str, Any]):
        if self.provider:
            self.provider.last_response = value

    @property
    def conversation(self) -> object:
        """
        Retrieves the conversation object from the successfully used provider.

        Returns:
            object: The conversation object, or None if no provider has been used yet.
        """
        return self.provider.conversation if self.provider else None

    def _fuzzy_resolve_provider_and_model(
        self, model: str
    ) -> Optional[Tuple[Type[Provider], str]]:
        """
        Performs an enhanced search to find the closest provider and model match.

        The search follows a three-step priority:
        1. Exact case-insensitive match.
        2. Substring match (e.g., 'gpt4' matching 'gpt-4o').
        3. Fuzzy match using difflib for close string similarity.

        Args:
            model (str): The model name to search for.

        Returns:
            Optional[Tuple[Type[Provider], str]]: A tuple containing the provider class
                                                  and the resolved model name, or None if no match is found.
        """
        available = [
            (name, cls) for name, cls in provider_map.items()
            if name not in self.exclude
        ]

        if not self.api_key:
             available = [p for p in available if p[0] not in api_key_providers]

        model_to_provider = {}
        for p_name, p_cls in available:
            p_models = _get_models_safely(p_cls)
            for m in p_models:
                if m not in model_to_provider:
                    model_to_provider[m] = p_cls

        if not model_to_provider:
            return None

        for m_name in model_to_provider:
            if m_name.lower() == model.lower():
                return model_to_provider[m_name], m_name

        for m_name in model_to_provider:
            if model.lower() in m_name.lower() or m_name.lower() in model.lower():
                if self.print_provider_info:
                    print(f"\033[1;33mSubstring match: '{model}' -> '{m_name}'\033[0m")
                return model_to_provider[m_name], m_name

        matches = difflib.get_close_matches(model, model_to_provider.keys(), n=1, cutoff=0.5)
        if matches:
            matched_model = matches[0]
            if self.print_provider_info:
                print(f"\033[1;33mFuzzy match: '{model}' -> '{matched_model}'\033[0m")
            return model_to_provider[matched_model], matched_model
        return None

    def _resolve_provider_and_model(
        self, model: str
    ) -> Tuple[Optional[Type[Provider]], str]:
        """
        Resolves the appropriate provider and model name based on the input string.

        The resolution logic handles:
        - 'Provider/Model' format for direct targeting.
        - 'auto' for automatic random selection.
        - Exact model name matches across all available providers.
        - Fuzzy resolution as a fallback.

        Args:
            model (str): The model specification string.

        Returns:
            Tuple[Optional[Type[Provider]], str]: A tuple of (ProviderClass, ResolvedModelName).
        """
        if "/" in model:
            p_name, m_name = model.split("/", 1)
            found_p = next(
                (cls for name, cls in provider_map.items() if name.lower() == p_name.lower()),
                None,
            )
            if found_p:
                return found_p, m_name

        if model == "auto":
            return None, "auto"

        available = [
            (name, cls) for name, cls in provider_map.items()
            if name not in self.exclude
        ]

        if not self.api_key:
             available = [p for p in available if p[0] not in api_key_providers]

        for p_name, p_cls in available:
            p_models = _get_models_safely(p_cls)
            if model in p_models:
                return p_cls, model

        fuzzy_result = self._fuzzy_resolve_provider_and_model(model)
        if fuzzy_result:
            return fuzzy_result

        return None, model

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        """
        Sends the prompt to available providers, attempting to get a response from each until one succeeds.

        This method iterates through a prioritized list of available providers based on the requested model
        and attempts to send the prompt to each provider until a successful response is received.

        Args:
            prompt (str): The user's prompt.
            stream (bool): Whether to stream the response. Defaults to False.
            raw (bool): Whether to return the raw response format. Defaults to False.
            optimizer (str, optional): Name of the optimizer to use. Defaults to None.
            conversationally (bool): Whether to apply optimizer conversationally. Defaults to False.
            **kwargs: Additional keyword arguments for the provider's ask method.

        Returns:
            Union[Dict, Generator]: The response dictionary or generator from the successful provider.
        """
        ask_kwargs = {
            "prompt": prompt,
            "stream": stream,
            "raw": raw,
            "optimizer": optimizer,
            "conversationally": conversationally,
        }
        ask_kwargs.update(kwargs)

        resolved_provider, resolved_model = self._resolve_provider_and_model(self.model)

        queue = []
        if resolved_provider:
            queue.append((resolved_provider.__name__.upper(), resolved_provider, resolved_model))

        all_available = [
            (name, cls) for name, cls in provider_map.items()
            if name not in self.exclude and (resolved_provider is None or cls != resolved_provider)
        ]

        if not self.api_key:
             all_available = [p for p in all_available if p[0] not in api_key_providers]

        random.shuffle(all_available)

        model_prio = []
        others = []

        for name, cls in all_available:
            p_models = _get_models_safely(cls)
            if resolved_model != "auto" and resolved_model in p_models:
                model_prio.append((name, cls, resolved_model))
            else:
                m = resolved_model
                if resolved_model != "auto" and p_models:
                    m = random.choice(p_models)
                elif resolved_model == "auto" and p_models:
                    m = random.choice(p_models)
                queue_model = m if m else "auto"
                others.append((name, cls, queue_model))

        queue.extend(model_prio)
        queue.extend(others)

        for provider_name, provider_class, model_to_use in queue:
            try:
                sig = inspect.signature(provider_class.__init__).parameters
                init_kwargs = {
                    "is_conversation": self.is_conversation,
                    "max_tokens": self.max_tokens,
                    "timeout": self.timeout,
                    "intro": self.intro,
                    "filepath": self.filepath,
                    "update_file": self.update_file,
                    "proxies": self.proxies,
                    "history_offset": self.history_offset,
                    "act": self.act,
                }

                if 'model' in sig:
                    init_kwargs['model'] = model_to_use
                if 'api_key' in sig and self.api_key:
                    init_kwargs['api_key'] = self.api_key

                for k, v in self.kwargs.items():
                    if k in sig or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.values()):
                        init_kwargs[k] = v

                if not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.values()):
                    init_kwargs = {k: v for k, v in init_kwargs.items() if k in sig}

                provider_instance = provider_class(**init_kwargs)
                self.provider = provider_instance
                self.provider_name = provider_name
                response = provider_instance.ask(**ask_kwargs)

                if stream and inspect.isgenerator(response):
                    try:
                        first_chunk = next(response)
                    except StopIteration:
                        continue
                    except Exception:
                        continue

                    def chained_gen() -> Any:
                        if self.print_provider_info:
                            model = getattr(self.provider, "model", None)
                            provider_class_name = self.provider.__class__.__name__
                            if model:
                                print(f"\033[1;34m{provider_class_name}:{model}\033[0m\n")
                            else:
                                print(f"\033[1;34m{provider_class_name}\033[0m\n")
                        yield first_chunk
                        yield from response
                    return chained_gen()

                if not stream and inspect.isgenerator(response):
                    try:
                        while True:
                            next(response)
                    except StopIteration as e:
                        response = e.value
                    except Exception:
                        continue

                if self.print_provider_info:
                    model = getattr(self.provider, "model", None)
                    provider_class_name = self.provider.__class__.__name__
                    if model:
                        print(f"\033[1;34m{provider_class_name}:{model}\033[0m\n")
                    else:
                        print(f"\033[1;34m{provider_class_name}\033[0m\n")
                return response
            except Exception:
                continue

        raise AllProvidersFailure("All providers failed to process the request")

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Provides a simplified chat interface, returning the message string or a generator of message strings.

        Args:
            prompt (str): The user's prompt.
            stream (bool): Whether to stream the response. Defaults to False.
            optimizer (str, optional): Name of the optimizer to use. Defaults to None.
            conversationally (bool): Whether to apply optimizer conversationally. Defaults to False.

        Returns:
            Union[str, Generator[str, None, None]]: The response string or a generator yielding
                                                     response chunks.
        """
        if stream:
            return self._chat_stream(prompt, optimizer, conversationally)
        else:
            return self._chat_non_stream(prompt, optimizer, conversationally)

    def _chat_stream(self, prompt: str, optimizer: Optional[str], conversationally: bool) -> Generator[str, None, None]:
        """
        Internal helper for streaming chat responses.

        Args:
            prompt (str): The user's prompt.
            optimizer (Optional[str]): Name of the optimizer.
            conversationally (bool): Whether to apply optimizer conversationally.

        Yields:
            str: Message chunks extracted from the provider's stream.
        """
        response = self.ask(
            prompt,
            stream=True,
            optimizer=optimizer,
            conversationally=conversationally,
        )
        if hasattr(response, "__iter__") and not isinstance(response, (str, bytes, dict)):
            for chunk in response:
                yield self.get_message(chunk)
        elif isinstance(response, dict):
             yield self.get_message(response)

    def _chat_non_stream(self, prompt: str, optimizer: Optional[str], conversationally: bool) -> str:
        """
        Internal helper for non-streaming chat responses.

        Args:
            prompt (str): The user's prompt.
            optimizer (Optional[str]): Name of the optimizer.
            conversationally (bool): Whether to apply optimizer conversationally.

        Returns:
            str: The full message text extracted from the provider's response.
        """
        response = self.ask(
            prompt,
            stream=False,
            optimizer=optimizer,
            conversationally=conversationally,
        )
        if isinstance(response, dict):
            return self.get_message(response)
        return str(response)

    def get_message(self, response: Response) -> str:
        """
        Extracts the message text from the provider's response dictionary.

        Args:
            response (Response): The response obtained from the `ask` method.

        Returns:
            str: The extracted message string.
        """
        assert self.provider is not None, "Chat with AI first"
        if not isinstance(response, dict):
            return str(response)
        return self.provider.get_message(response)

if __name__ == "__main__":
    auto = AUTO(print_provider_info=True)
    response = auto.chat("Hello, how are you?", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
