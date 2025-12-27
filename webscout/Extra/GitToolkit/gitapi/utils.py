import json
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    from webscout.litagent.agent import LitAgent
    _USER_AGENT_GENERATOR = LitAgent()
except ImportError:
    _USER_AGENT_GENERATOR = None

class GitError(Exception):
    """Base exception for GitHub API errors"""
    pass

class RateLimitError(GitError):
    """Raised when hitting GitHub API rate limits"""
    pass

class NotFoundError(GitError):
    """Raised when resource is not found"""
    pass

class RequestError(GitError):
    """Raised for general request errors"""
    pass


def request(url: str, retry_attempts: int = 3) -> Any:
    """
    Send a request to GitHub API with retry mechanism

    Args:
        url: GitHub API endpoint URL
        retry_attempts: Number of retry attempts

    Returns:
        Parsed JSON response

    Raises:
        NotFoundError: If resource not found
        RateLimitError: If rate limited
        RequestError: For other request errors
    """
    headers = {
        "User-Agent": _USER_AGENT_GENERATOR.random() if _USER_AGENT_GENERATOR else "webscout-gitapi/1.0",
        "Accept": "application/vnd.github+json"
    }

    for attempt in range(retry_attempts):
        try:
            req = Request(url, headers=headers)
            response = urlopen(req, timeout=30)
            data = response.read().decode('utf-8')
            try:
                return json.loads(data)
            except json.JSONDecodeError as json_err:
                raise RequestError(f"Invalid JSON response from {url}: {str(json_err)}")

        except HTTPError as e:
            if e.code == 404:
                raise NotFoundError(f"Resource not found: {url}")
            if e.code == 429:
                if attempt < retry_attempts - 1:
                    # Wait before retrying on rate limit
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise RateLimitError(f"Rate limited after {retry_attempts} attempts")
            if e.code == 403:
                raise RequestError("Forbidden: Check your authentication token")
            if attempt == retry_attempts - 1:
                raise RequestError(f"HTTP Error {e.code}: {e.reason}")
            # Wait before retrying on other HTTP errors
            time.sleep(1)

        except Exception as e:
            if attempt == retry_attempts - 1:
                raise RequestError(f"Request failed: {str(e)}")
            time.sleep(1)

    raise RequestError(f"Request to {url} failed after {retry_attempts} attempts")
