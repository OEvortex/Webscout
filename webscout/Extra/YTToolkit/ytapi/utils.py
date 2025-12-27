from collections import OrderedDict
from typing import Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from webscout.litagent import LitAgent

from .errors import InvalidURL, RequestError, TooManyRequests

__all__ = ['dup_filter', 'request']


_USER_AGENT_GENERATOR = LitAgent()


def request(url: str, retry_attempts: int = 3) -> str:
    """
    Send a request with a random user agent and built-in retry mechanism.

    Args:
        url (str): The URL to request
        retry_attempts (int, optional): Number of retry attempts. Defaults to 3.

    Raises:
        InvalidURL: If the URL cannot be found
        TooManyRequests: If rate-limited
        RequestError: For other request-related errors

    Returns:
        str: Decoded response content
    """
    for attempt in range(retry_attempts):
        try:
            headers = {
                "User-Agent": _USER_AGENT_GENERATOR.random()
            }

            req = Request(url, headers=headers)
            response = urlopen(req)
            return response.read().decode('utf-8')

        except HTTPError as e:
            if e.code == 404:
                raise InvalidURL(f'Cannot find anything with the requested URL: {url}')
            if e.code == 429:
                raise TooManyRequests(f'Rate-limited on attempt {attempt + 1}')

            if attempt == retry_attempts - 1:
                raise RequestError(f'HTTP Error {e.code}: {e.reason}') from e

        except Exception as e:
            if attempt == retry_attempts - 1:
                raise RequestError(f'Request failed: {e!r}') from None

    raise RequestError(f"Request to {url} failed after {retry_attempts} attempts")


def dup_filter(iterable: list, limit: Optional[int] = None) -> list:
    if not iterable:
        return []
    lim = limit if limit else len(iterable)
    converted = list(OrderedDict.fromkeys(iterable))
    if len(converted) - lim > 0:
        return converted[:-len(converted) + lim]
    else:
        return converted
