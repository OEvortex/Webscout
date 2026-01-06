from typing import Any, Dict, Generator, List, Optional, Union, cast

import requests

from webscout import exceptions
from webscout.AIbase import AISearch, SearchResponse
from webscout.litagent import LitAgent
from webscout.sanitize import sanitize_stream


class PERPLEXED(AISearch):
    """
    A class to interact with the PERPLEXED stream search API.
    """

    def __init__(
        self,
        timeout: int = 30,
        proxies: Optional[dict] = None,
    ):
        """Initializes the PERPLEXED API client."""
        self.session = requests.Session()
        self.api_endpoint = "https://d21l5c617zttgr.cloudfront.net/stream_search"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://d37ozmhmvu2kcg.cloudfront.net",
            "referer": "https://d37ozmhmvu2kcg.cloudfront.net/",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sec-gpc": "1",
            "user-agent": LitAgent().random(),
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
        """
        Sends a prompt to the PERPLEXED API and returns the response.

        Args:
            prompt: The search query or prompt to send to the API
            stream: Whether to stream the response
            raw: If True, returns unprocessed response chunks without any
                processing or sanitization. Useful for debugging or custom
                processing pipelines. Defaults to False.

        Returns:
            When raw=False: SearchResponse object (non-streaming) or
                Generator yielding SearchResponse objects (streaming)
            When raw=True: Raw string response (non-streaming) or
                Generator yielding raw string chunks (streaming)

        Examples:
            >>> ai = PERPLEXED()
            >>> # Get processed response
            >>> response = ai.search("Hello")
            >>> print(response)

            >>> # Get raw response
            >>> raw_response = ai.search("Hello", raw=True)
            >>> print(raw_response)

            >>> # Stream raw chunks
            >>> for chunk in ai.search("Hello", stream=True, raw=True):
            ...     print(chunk, end='', flush=True)
        """
        payload = {"user_prompt": prompt}

        def for_stream():
            try:
                with self.session.post(
                    self.api_endpoint,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    proxies=self.proxies,
                ) as response:
                    if not response.ok:
                        raise exceptions.APIConnectionError(
                            f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                        )

                    processed_chunks = sanitize_stream(
                        data=response.iter_content(chunk_size=1024),
                        intro_value="",
                        to_json=True,
                        content_extractor=lambda chunk: (chunk.get("answer") if isinstance(chunk, dict) and chunk.get("success") and chunk.get("answer") is not None else None),
                        yield_raw_on_error=False,
                        encoding='utf-8',
                        encoding_errors='replace',
                        line_delimiter="[/PERPLEXED-SEPARATOR]",
                        raw=raw,
                        output_formatter=None if raw else lambda x: SearchResponse(x) if isinstance(x, str) else x,
                    )

                    for chunk in processed_chunks:
                        yield chunk

            except requests.exceptions.RequestException as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        def for_non_stream():
            try:
                with self.session.post(
                    self.api_endpoint,
                    json=payload,
                    stream=False,
                    timeout=self.timeout,
                    proxies=self.proxies,
                ) as response:
                    if not response.ok:
                        raise exceptions.APIConnectionError(
                            f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                        )

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
                            content_extractor=lambda chunk: (chunk.get("answer") if isinstance(chunk, dict) and chunk.get("success") and chunk.get("answer") is not None else None),
                            yield_raw_on_error=False,
                            encoding='utf-8',
                            encoding_errors='replace',
                            buffer_size=8192,
                            line_delimiter="[/PERPLEXED-SEPARATOR]",
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

            except requests.exceptions.RequestException as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        return for_stream() if stream else for_non_stream()


if __name__ == "__main__":
    ai = PERPLEXED()
    response = ai.search("What is Python?", stream=False, raw=False)
    print(response)
