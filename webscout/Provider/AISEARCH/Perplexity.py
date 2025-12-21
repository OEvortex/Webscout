import json
import random
import time
from typing import Any, Dict, Generator, List, Optional, Union
from uuid import uuid4

from curl_cffi import requests

from webscout import exceptions
from webscout.AIbase import AISearch, SearchResponse
from webscout.litagent import LitAgent
from webscout.sanitize import sanitize_stream


class Perplexity(AISearch):
    """A class to interact with the Perplexity AI search API.

    Perplexity provides a powerful search interface that returns AI-generated responses
    based on web content. It supports both streaming and non-streaming responses,
    multiple search modes, and model selection.

    Basic Usage:
        >>> from webscout import Perplexity
        >>> ai = Perplexity()
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
        Initialize the Perplexity client.
        """
        self.timeout = timeout
        self.agent = LitAgent()
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "dnt": "1",
            "priority": "u=0, i",
            "sec-ch-ua": '"Not;A=Brand";v="24", "Chromium";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": self.agent.random(),
        }
        self.session = requests.Session(
            headers=self.headers, cookies=cookies or {}, impersonate="chrome"
        )

        if proxies:
            self.session.proxies.update(proxies)

        # Initialize session info if possible
        try:
            self.timestamp = format(random.getrandbits(32), "08x")
            response: requests.Response = self.session.get(
                f"https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.timestamp}"
            )
            if response.status_code == 200 and response.text.startswith("0"):
                self.sid = json.loads(response.text[1:])["sid"]
                self.session.post(
                    f"https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.timestamp}&sid={self.sid}",
                    data='40{"jwt":"anonymous-ask-user"}',
                )
            self.session.get("https://www.perplexity.ai/api/auth/session")
        except Exception:
            pass

    def search(
        self,
        prompt: str,
        mode: str = "auto",
        model: Optional[str] = None,
        sources: Optional[List[str]] = None,
        stream: bool = False,
        raw: bool = False,
        language: str = "en-US",
        follow_up: Optional[Dict[str, Any]] = None,
        incognito: bool = False,
        max_retries: int = 3,
    ) -> Union[
        SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None], List[Any]
    ]:
        """Search using the Perplexity API and get AI-generated responses."""
        if sources is None:
            sources = ["web"]

        # Prepare request data
        json_data: Dict[str, Any] = {
            "query_str": prompt,
            "params": {
                "attachments": follow_up["attachments"] if follow_up else [],
                "frontend_context_uuid": str(uuid4()),
                "frontend_uuid": str(uuid4()),
                "is_incognito": incognito,
                "language": language,
                "last_backend_uuid": follow_up["backend_uuid"] if follow_up else None,
                "mode": "concise" if mode == "auto" else "copilot",
                "model_preference": "turbo",  # Default
                "source": "default",
                "sources": sources,
                "version": "2.18",
            },
        }

        # Handle model selection if provided
        if model:
            json_data["params"]["model_preference"] = model

        for attempt in range(max_retries):
            try:
                resp = self.session.post(
                    "https://www.perplexity.ai/rest/sse/perplexity_ask",
                    json=json_data,
                    stream=True,
                    timeout=self.timeout,
                )

                if resp.status_code == 502:
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)
                        continue
                    raise exceptions.APIConnectionError(
                        f"Perplexity API returned 502 Bad Gateway after {max_retries} attempts."
                    )

                if resp.status_code != 200:
                    raise exceptions.APIConnectionError(
                        f"API returned status code {resp.status_code}: {resp.text}"
                    )

                def stream_response() -> Generator[
                    Union[Dict[str, str], SearchResponse], None, None
                ]:
                    processed_chunks = sanitize_stream(
                        data=resp.iter_content(chunk_size=1024),
                        to_json=False,
                        extract_regexes=[r'"answer":\s*"((?:\\.|[^"\\])*)"'],
                        yield_raw_on_error=False,
                        encoding="utf-8",
                        encoding_errors="replace",
                        line_delimiter="event: message",
                        raw=raw,
                        output_formatter=None
                        if raw
                        else lambda x: (
                            SearchResponse(
                                x.get("text", "").replace("\\n", "\n").replace("\\n\\n", "\n\n")
                            )
                            if isinstance(x, dict) and "text" in x
                            else (
                                SearchResponse(x.replace("\\n", "\n").replace("\\n\\n", "\n\n"))
                                if isinstance(x, str)
                                else SearchResponse(str(x))
                            )
                        ),
                    )

                    yield from processed_chunks

                if stream:
                    return stream_response()
                else:
                    if raw:
                        return resp.text

                    full_response_text = ""
                    for chunk in stream_response():
                        full_response_text += str(chunk)

                    return SearchResponse(full_response_text)

            except requests.RequestsError as e:
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise exceptions.APIConnectionError(f"Connection error: {str(e)}")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Error: {str(e)}")

        raise exceptions.FailedToGenerateResponseError(
            "Failed to get response after multiple attempts"
        )


if __name__ == "__main__":
    ai = Perplexity()
    for chunk in ai.search("Explain the theory of relativity.", stream=True, raw=False):
        print(chunk, end="", flush=True)
