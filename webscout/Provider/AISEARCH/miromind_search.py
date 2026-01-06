import json
import re
from typing import Any, Dict, Generator, Optional, Union

from curl_cffi import requests

from webscout import exceptions
from webscout.AIbase import AISearch, SearchResponse
from webscout.litagent import LitAgent
from webscout.sanitize import sanitize_stream


class MiroMind(AISearch):
    """A class to interact with the MiroMind AI search API.

    MiroMind provides a powerful search interface that returns AI-generated responses
    based on web content. It supports both streaming and non-streaming responses
    using server-sent events.

    Basic Usage:
        >>> from webscout import MiroMind
        >>> ai = MiroMind()
        >>> # Non-streaming example
        >>> response = ai.search("What is Python?")
        >>> print(response)
        Python is a high-level programming language...

        >>> # Streaming example
        >>> for chunk in ai.search("Tell me about AI", stream=True):
        ...     print(chunk, end="", flush=True)
        Artificial Intelligence is...
    """

    def __init__(
        self,
        cookies: Optional[Dict[str, str]] = None,
        timeout: int = 60,
        proxies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the MiroMind client.

        Args:
            cookies (Optional[Dict[str, str]]): Session cookies for authentication
            timeout (int): Request timeout in seconds. Defaults to 60.
            proxies (Optional[Dict[str, str]]): Proxy configuration
        """
        self.timeout = timeout
        self.agent = LitAgent()
        self.cookies = cookies or {}
        self.proxies = proxies
        self.session = requests.Session(
            timeout=timeout,
            proxies=proxies,
            headers=self._get_headers(),
        )
        self.last_response = {}

    def _get_headers(self) -> Dict[str, str]:
        """
        Get the required headers for API requests.

        Returns:
            Dict[str, str]: Dictionary of headers
        """
        return {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Authorization": "",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://dr.miromind.ai",
            "Referer": "https://dr.miromind.ai/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": self.agent.random(),
            "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-gpc": "1",
        }


    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None]]:
        """
        Search using MiroMind's API and get AI-generated responses.

        Args:
            prompt (str): The search query or prompt to send to the API
            stream (bool): If True, yields response chunks as they arrive
            raw (bool): If True, returns raw response dictionaries
            **kwargs: Additional parameters (not used in current implementation)

        Returns:
            Union[SearchResponse, Generator]: Response based on stream parameter

        Raises:
            exceptions.APIConnectionError: If the API request fails
        """
        url = "https://dr.miromind.ai/api/chat/stream"
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "debug": False,
        }

        def extract_message_content(data):
            """Extracts content from MiroMind SSE event data."""
            # When to_json=True, sanitize_stream parses the JSON from data: lines
            # So data is already a dict containing the parsed SSE content
            if isinstance(data, dict):
                # Handle the parsed SSE structure
                if data.get("event") == "message" and "data" in data:
                    data_content = data["data"]
                    if isinstance(data_content, dict) and "delta" in data_content and "content" in data_content["delta"]:
                        content = data_content["delta"]["content"]
                        if content:  # Only return non-empty content
                            return content
            return None

        def for_stream():
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    cookies=self.cookies,
                    stream=True,
                )
                response.raise_for_status()

                # Use sanitize_stream with comprehensive features
                processed_chunks = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    to_json=True,
                    content_extractor=lambda chunk: (
                        (chunk.get("data") or {}).get("delta", {}).get("content") if isinstance(chunk, dict) else None
                    ),
                    yield_raw_on_error=False,
                    encoding='utf-8',
                    encoding_errors='replace',
                    raw=raw,
                    output_formatter=None if raw else lambda x: SearchResponse(x) if x is not None else None,
                )

                yield from processed_chunks

            except Exception as e:
                raise exceptions.APIConnectionError(f"Failed to connect to MiroMind API: {e}")

        def for_non_stream():
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    cookies=self.cookies,
                    stream=False,
                )
                response.raise_for_status()

                if raw:
                    # Return raw response text when raw=True
                    return response.text
                else:
                    # Process response similar to streaming when raw=False
                    processed_chunks = sanitize_stream(
                        data=response.content,
                        intro_value="",
                        to_json=True,
                        skip_markers=[],
                        strip_chars=None,
                        start_marker=None,
                        end_marker=None,
                        content_extractor=lambda chunk: extract_message_content(chunk),
                        yield_raw_on_error=False,
                        encoding='utf-8',
                        encoding_errors='replace',
                        buffer_size=8192,
                        error_handler=None,
                        skip_regexes=None,
                        raw=False,
                        output_formatter=None,
                    )

                    full_response = ""
                    for content_chunk in processed_chunks:
                        if content_chunk is not None and isinstance(content_chunk, str):
                            full_response += content_chunk

                    self.last_response = SearchResponse(full_response)
                    return self.last_response

            except Exception as e:
                raise exceptions.APIConnectionError(f"Failed to connect to MiroMind API: {e}")

        return for_stream() if stream else for_non_stream()


if __name__ == "__main__":
    ai = MiroMind()
    response = ai.search("What is Python?", stream=True, raw=False)

    # Check if response is iterable (streaming) but not a basic type
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes, SearchResponse)):
        for chunks in response:
            # Convert SearchResponse to string for display
            print(str(chunks), end="", flush=True)
    else:
        # Handle direct response (non-streaming or single SearchResponse)
        print(str(response))
