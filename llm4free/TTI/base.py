from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union, cast

from .utils import ImageResponse


class BaseImages(ABC):
    @abstractmethod
    def create(
        self,
        *,
        model: str,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
        response_format: str = "url",
        user: Optional[str] = None,
        style: str = "none",
        aspect_ratio: str = "1:1",
        timeout: Optional[int] = None,
        image_format: str = "png",
        seed: Optional[int] = None,
        convert_format: bool = False,
        **kwargs,
    ) -> ImageResponse:
        """
        Abstract method to create images from a prompt.

        Args:
            model: The model to use for image generation.
            prompt: The prompt for the image.
            n: Number of images to generate.
            size: Image size.
            response_format: "url" or "b64_json".
            user: Optional user identifier.
            style: Optional style.
            aspect_ratio: Optional aspect ratio.
            timeout: Request timeout in seconds.
            image_format: "png" or "jpeg" for output format.
            seed: Optional random seed for reproducibility.
            **kwargs: Additional provider-specific parameters.

        Returns:
            ImageResponse: The generated images.
        """
        raise NotImplementedError


# class ProxyAutoMeta(ABCMeta):
#     """Metaclass providing seamless proxy injection for providers."""

#     def __call__(cls, *args, **kwargs):
#         # Determine if automatic proxying should be disabled
#         disable_auto_proxy = kwargs.get('disable_auto_proxy', False) or getattr(cls, 'DISABLE_AUTO_PROXY', False)

#         # Proxies may be supplied explicitly
#         proxies = kwargs.get('proxies', None)

#         # Otherwise try to fetch one automatically
#         if proxies is None and not disable_auto_proxy:
#             try:
#                 proxies = {"http": get_auto_proxy(), "https": get_auto_proxy()}
#             except Exception as e:
#                 print(f"Failed to fetch auto-proxy: {e}")
#                 proxies = {}
#         elif proxies is None:
#             proxies = {}

#         # No global monkeypatching, just set proxies on the instance
#         instance = super().__call__(*args, **kwargs)
#         instance.proxies = proxies

#         # If proxies are set, patch any existing session-like attributes
#         if proxies:
#             for attr in dir(instance):
#                 obj = getattr(instance, attr)
#                 if isinstance(obj, requests.Session):
#                     obj.proxies.update(proxies)
#                 if CurlSession and isinstance(obj, CurlSession):
#                     try:
#                         obj.proxies.update(proxies)
#                     except (ValueError, KeyError, AttributeError):
#                         print("Failed to update proxies for CurlSession due to an expected error.")
#                 if CurlAsyncSession and isinstance(obj, CurlAsyncSession):
#                     try:
#                         obj.proxies.update(proxies)
#                     except (ValueError, KeyError, AttributeError):
#                         print("Failed to update proxies for CurlAsyncSession due to an expected error.")

#         # Helper for backward compatibility
#         def get_proxied_session():
#             s = requests.Session()
#             s.proxies.update(proxies)
#             return s

#         instance.get_proxied_session = get_proxied_session

#         def get_proxied_curl_session(impersonate="chrome120", **kw):
#             if CurlSession:
#                 return CurlSession(proxies=proxies, impersonate=impersonate, **kw)
#             raise ImportError("curl_cffi is not installed")

#         instance.get_proxied_curl_session = get_proxied_curl_session

#         def get_proxied_curl_async_session(impersonate="chrome120", **kw):
#             if CurlAsyncSession:
#                 return CurlAsyncSession(proxies=proxies, impersonate=impersonate, **kw)
#             raise ImportError("curl_cffi is not installed")

#         instance.get_proxied_curl_async_session = get_proxied_curl_async_session

#         return instance


class TTICompatibleProvider(ABC):
    """
    Abstract Base Class for TTI providers mimicking the OpenAI Python client structure.
    Requires a nested 'images.create' structure.
    All subclasses automatically get proxy support via ProxyAutoMeta.

    Class Attributes:
        required_auth (bool): Whether this provider requires authentication (API key, cookie, etc.)
        working (bool): Whether this provider is currently working/operational

    Available proxy helpers:
    - self.get_proxied_session() - returns a requests.Session with proxies
    - self.get_proxied_curl_session() - returns a curl_cffi.Session with proxies
    - self.get_proxied_curl_async_session() - returns a curl_cffi.AsyncSession with proxies
    """

    images: BaseImages
    required_auth: bool = False  # Default: no auth required
    working: bool = True  # Default: provider is working
    AVAILABLE_MODELS: List[str] = []  # List of available models

    @abstractmethod
    def __init__(self, **kwargs: Any):
        pass

    @property
    @abstractmethod
    def models(self) -> Any:
        """
        Property that returns an object with a .list() method returning available models.
        Subclasses must implement this property.
        """
        raise NotImplementedError
