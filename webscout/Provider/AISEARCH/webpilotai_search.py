import re
from typing import cast, Any, Dict, Generator, List, Optional, Union

import requests

from webscout import exceptions
from webscout.AIbase import AISearch, SearchResponse
from webscout.litagent import LitAgent
from webscout.sanitize import sanitize_stream


class webpilotai(AISearch):
    """A class to interact with the webpilotai (WebPilot) AI search API.

    webpilotai provides a web-based comprehensive search SearchResponse interface that returns AI-generated
    SearchResponses with source references and related questions. It supports both streaming and
    non-streaming SearchResponses.

    Basic Usage:
        >>> from webscout import webpilotai
        >>> ai = webpilotai()
        >>> # Non-streaming example
        >>> response = ai.search("What is Python?")
        >>> print(response)
        Python is a high-level programming language...

        >>> # Streaming example
        >>> for chunk in ai.search("Tell me about AI", stream=True):
        ...     print(chunk, end="", flush=True)
        Artificial Intelligence is...

        >>> # Raw SearchResponse format
        >>> for chunk in ai.search("Hello", stream=True, raw=True):
        ...     print(chunk)
        {'text': 'Hello'}
        {'text': ' there!'}

    Args:
        timeout (int, optional): Request timeout in seconds. Defaults to 90.
        proxies (dict, optional): Proxy configuration for requests. Defaults to None.
    """

    def __init__(
        self,
        timeout: int = 90,
        proxies: Optional[dict] = None,
    ):
        """Initialize the webpilotai API client.

        Args:
            timeout (int, optional): Request timeout in seconds. Defaults to 90.
            proxies (dict, optional): Proxy configuration for requests. Defaults to None.
        """
        self.session = requests.Session()
        self.api_endpoint = "https://api.webpilotai.com/rupee/v1/search"
        self.timeout = timeout
        self.last_response = {}

        # The 'Bearer null' is part of the API's expected headers
        self.headers = {
            'Accept': 'application/json, text/plain, */*, text/event-stream',
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': 'Bearer null',
            'Origin': 'https://www.webpilot.ai',
            'Referer': 'https://www.webpilot.ai/',
            'User-Agent': LitAgent().random(),
        }

        self.session.headers.update(self.headers)
        self.proxies = proxies

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None], List[Any], Dict[str, Any], str]:
        """Search using the webpilotai API and get AI-generated SearchResponses.

        This method sends a search query to webpilotai and returns the AI-generated SearchResponse.
        It supports both streaming and non-streaming modes, as well as raw SearchResponse format.

        Args:
            prompt (str): The search query or prompt to send to the API.
            stream (bool, optional): If True, yields SearchResponse chunks as they arrive.
                                   If False, returns complete SearchResponse. Defaults to False.
            raw (bool, optional): If True, returns raw SearchResponse dictionaries with 'text' key.
                                If False, returns SearchResponse objects that convert to text automatically.
                                Defaults to False.

        Returns:
            Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None]]:
                - If stream=False: Returns complete SearchResponse as SearchResponse object
                - If stream=True: Yields SearchResponse chunks as either Dict or SearchResponse objects

        Raises:
            APIConnectionError: If the API request fails
        """
        payload = {
            "q": prompt,
            "threadId": ""  # Empty for new search
        }

        def for_stream():

            try:
                with self.session.post(
                    self.api_endpoint,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    proxies=self.proxies
                ) as response:
                    if not response.ok:
                        raise exceptions.APIConnectionError(
                            f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                        )

                    def extract_webpilot_content(data):
                        if isinstance(data, dict):
                            if data.get('type') == 'data':
                                return data.get('data', {}).get('content', "")
                        return None

                    processed_chunks = sanitize_stream(
                        data=response.iter_content(chunk_size=1024),
                        to_json=True,
                        extract_regexes=[r"(\{.*\})"],
                        content_extractor=lambda chunk: extract_webpilot_content(chunk),
                        yield_raw_on_error=False,
                        encoding='utf-8',
                        encoding_errors='replace',
                        line_delimiter="\n",
                        raw=raw,
                        output_formatter=None if raw else lambda x: SearchResponse(x) if isinstance(x, str) else x,
                    )

                    for chunk in processed_chunks:
                        yield chunk

            except requests.exceptions.Timeout:
                raise exceptions.APIConnectionError("Request timed out")
            except requests.exceptions.RequestException as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        def for_non_stream():
            full_content = ""
            for chunk in for_stream():
                if raw:
                    full_content += str(chunk)
                else:
                    full_content += str(chunk)

            if raw:
                return full_content
            else:
                formatted_response = self.format_SearchResponse(full_content)
                self.last_response = SearchResponse(formatted_response)
                return self.last_response

        if stream:
            return for_stream()
        else:
            return for_non_stream()

    @staticmethod
    def format_SearchResponse(text: str) -> str:
        """Format the SearchResponse text for better readability.

        Args:
            text (str): The raw SearchResponse text

        Returns:
            str: Formatted text with improved structure
        """
        # Clean up formatting
        # Remove excessive newlines
        clean_text = re.sub(r'\n{3,}', '\n\n', text)

        # Ensure consistent spacing around sections
        clean_text = re.sub(r'([.!?])\s*\n\s*([A-Z])', r'\1\n\n\2', clean_text)

        # Clean up any leftover HTML or markdown artifacts
        clean_text = re.sub(r'<[^>]*>', '', clean_text)

        # Remove trailing whitespace on each line
        clean_text = '\n'.join(line.rstrip() for line in clean_text.split('\n'))

        return clean_text.strip()


if __name__ == "__main__":
    from rich import print

    ai = webpilotai()
    r = ai.search("What is Python?", stream=True, raw=False)
    if hasattr(r, "__iter__") and not isinstance(r, (str, SearchResponse)):
        for chunk in r:
            print(chunk, end="", flush=True)
    else:
        print(r)
