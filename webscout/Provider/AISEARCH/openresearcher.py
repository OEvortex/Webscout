"""
OpenResearcher Provider - AI-powered research search using OpenResearcher Gradio API.

This provider uses the OpenResearcher model hosted on HuggingFace Spaces.
It performs multi-round iterative research with web search capabilities.

Features:
- Multi-round iterative research (search → open page → find → answer)
- Real-time streaming via Server-Sent Events
- Configurable max research rounds
- Built-in Serper API key (or custom key)
- HTML-formatted results with citations and thought process

Reference: https://openresearcher-openresearcher.hf.space
"""

from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import requests
from curl_cffi.requests.exceptions import RequestException

from webscout import exceptions
from webscout.AIbase import AISearch, SearchResponse
from webscout.litagent import LitAgent
from webscout.sanitize import sanitize_stream


class OpenResearcher(AISearch):
    """
    A class to interact with the OpenResearcher API.

    OpenResearcher performs multi-round iterative research by:
    1. Searching the web for relevant information
    2. Opening and reading pages
    3. Finding specific information
    4. Synthesizing a comprehensive answer

    Basic Usage:
        >>> from webscout.Provider.AISEARCH import OpenResearcher
        >>> ai = OpenResearcher()
        >>> # Non-streaming
        >>> response = ai.search("What is quantum computing?")
        >>> print(response)

        >>> # Streaming
        >>> for chunk in ai.search("Explain machine learning", stream=True):
        ...     print(chunk, end="", flush=True)

        >>> # Custom max rounds
        >>> response = ai.search("Climate change", max_rounds=10)

    Args:
        timeout (int, optional): Request timeout in seconds. Defaults to 120.
        proxies (dict, optional): Proxy configuration for requests. Defaults to None.
        serper_key (str, optional): Serper API key. Uses default if not provided.
        max_rounds (int, optional): Default maximum research rounds. Defaults to 50.
    """

    required_auth = False

    # Default Serper API key embedded in the original app
    DEFAULT_SERPER_KEY = "b4ccaa60ac4905631ff4692ed09cf730bf9e9190"

    # Gradio API endpoint
    BASE_URL = "https://openresearcher-openresearcher.hf.space"
    RESEARCH_ENDPOINT = f"{BASE_URL}/gradio_api/call/start_research"

    def __init__(
        self,
        timeout: int = 120,
        proxies: Optional[dict] = None,
        serper_key: Optional[str] = None,
        max_rounds: int = 50,
    ):
        """
        Initialize the OpenResearcher API client.

        Args:
            timeout (int, optional): Request timeout in seconds. Defaults to 120.
            proxies (dict, optional): Proxy configuration for requests. Defaults to None.
            serper_key (str, optional): Serper API key. Uses default if not provided.
            max_rounds (int, optional): Default maximum research rounds. Defaults to 50.
        """
        self.session = requests.Session()
        self.timeout = timeout
        self.proxies = proxies or {}
        self.serper_key = serper_key or self.DEFAULT_SERPER_KEY
        self.default_max_rounds = max_rounds
        self.last_response: Dict[str, Any] = {}
        self.agent = LitAgent()

        self.session.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "User-Agent": self.agent.random(),
            }
        )

        if self.proxies:
            self.session.proxies.update(self.proxies)

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        max_rounds: Optional[int] = None,
        serper_key: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[
        SearchResponse,
        Generator[Union[Dict[str, str], SearchResponse], None, None],
        List[Any],
        Dict[str, Any],
        str,
    ]:
        """
        Sends a research query to the OpenResearcher API and returns the response.

        Args:
            prompt: The research query or prompt to send to the API
            stream: Whether to stream the response
            raw: If True, returns unprocessed response chunks without any
                processing or sanitization. Useful for debugging or custom
                processing pipelines. Defaults to False.
            max_rounds: Maximum number of research rounds. Defaults to 50.
            serper_key: Serper API key. Uses default if not provided.
            **kwargs: Additional parameters

        Returns:
            When raw=False: SearchResponse object (non-streaming) or
                Generator yielding SearchResponse objects (streaming)
            When raw=True: Raw string response (non-streaming) or
                Generator yielding raw string chunks (streaming)

        Examples:
            >>> ai = OpenResearcher()
            >>> # Get processed response
            >>> response = ai.search("What is quantum computing?")
            >>> print(response)

            >>> # Get raw response
            >>> raw_response = ai.search("Hello", raw=True)
            >>> print(raw_response)

            >>> # Stream raw chunks
            >>> for chunk in ai.search("Hello", stream=True, raw=True):
            ...     print(chunk, end='', flush=True)
        """
        rounds = max_rounds or self.default_max_rounds
        key = serper_key or self.serper_key

        def for_stream():
            try:
                event_id = self._submit_research(
                    question=prompt,
                    serper_key=key,
                    max_rounds=rounds,
                )

                result_url = f"{self.BASE_URL}/gradio_api/call/start_research/{event_id}"

                response = self.session.get(
                    result_url,
                    headers={"Accept": "text/event-stream"},
                    timeout=self.timeout,
                    stream=True,
                    proxies=self.proxies,
                )
                if not response.ok:
                    raise exceptions.APIConnectionError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )

                processed_chunks = sanitize_stream(
                    data=response.iter_lines(),
                    intro_value="data:",
                    to_json=True,
                    content_extractor=lambda chunk: chunk[1]
                    if isinstance(chunk, list)
                    and len(chunk) >= 2
                    and isinstance(chunk[1], str)
                    and chunk[1]
                    else (
                        chunk[0]
                        if isinstance(chunk, list)
                        and chunk
                        and isinstance(chunk[0], str)
                        and chunk[0]
                        else None
                    ),
                    yield_raw_on_error=False,
                    encoding="utf-8",
                    encoding_errors="replace",
                    raw=raw,
                    output_formatter=None
                    if raw
                    else lambda x: SearchResponse(x) if isinstance(x, str) else x,
                )

                yield from processed_chunks

            except RequestException as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        def for_non_stream():
            try:
                event_id = self._submit_research(
                    question=prompt,
                    serper_key=key,
                    max_rounds=rounds,
                )

                result_url = f"{self.BASE_URL}/gradio_api/call/start_research/{event_id}"

                response = self.session.get(
                    result_url,
                    headers={"Accept": "text/event-stream"},
                    timeout=self.timeout,
                    stream=True,
                    proxies=self.proxies,
                )
                if not response.ok:
                    raise exceptions.APIConnectionError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )

                if raw:
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            line_str = (
                                line.decode("utf-8")
                                if isinstance(line, bytes)
                                else line
                            )
                            full_response += line_str + "\n"
                    return full_response

                processed_chunks = sanitize_stream(
                    data=response.iter_lines(),
                    intro_value="data:",
                    to_json=True,
                    content_extractor=lambda chunk: chunk[1]
                    if isinstance(chunk, list)
                    and len(chunk) >= 2
                    and isinstance(chunk[1], str)
                    and chunk[1]
                    else (
                        chunk[0]
                        if isinstance(chunk, list)
                        and chunk
                        and isinstance(chunk[0], str)
                        and chunk[0]
                        else None
                    ),
                    yield_raw_on_error=False,
                    encoding="utf-8",
                    encoding_errors="replace",
                )

                full_response = ""
                for content_chunk in processed_chunks:
                    if content_chunk is not None and isinstance(content_chunk, str):
                        full_response += content_chunk

                self.last_response = SearchResponse(full_response)
                return self.last_response

            except RequestException as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        return for_stream() if stream else for_non_stream()

    def _submit_research(
        self,
        question: str,
        serper_key: str,
        max_rounds: int,
    ) -> str:
        """
        Submit a research request and return event_id.

        Args:
            question: The research query
            serper_key: Serper API key
            max_rounds: Maximum research rounds

        Returns:
            str: Event ID for polling results
        """
        payload = {"data": [question, serper_key, max_rounds]}

        response = self.session.post(
            self.RESEARCH_ENDPOINT,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        result = response.json()
        event_id = result.get("event_id")

        if not event_id:
            raise exceptions.FailedToGenerateResponseError(
                f"No event_id returned from OpenResearcher API: {result}"
            )

        return event_id


if __name__ == "__main__":
    ai = OpenResearcher()
    response = ai.search("What is Python?", stream=True, raw=False)
    if hasattr(response, "__iter__") and not isinstance(
        response, (str, bytes, SearchResponse)
    ):
        for chunks in response:
            print(chunks, end="", flush=True)
    else:
        print(response)
