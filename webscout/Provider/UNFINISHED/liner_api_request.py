import json
import random
from typing import Any, Dict, Generator, List, Optional, Union
from uuid import uuid4

from curl_cffi.requests import Session

from webscout import LitAgent, exceptions
from webscout.AIbase import AISearch, SearchResponse


class Liner(AISearch):
    """A class to interact with the Liner AI search API.

    Liner provides a powerful search interface that returns AI-generated responses
    based on web content. It supports both streaming and non-streaming responses.

    Basic Usage:
        >>> from webscout import Liner
        >>> ai = Liner(cookies_path="cookies.json")
        >>> # Non-streaming example
        >>> response = ai.search("What is Python?")
        >>> print(response)
        Python is a high-level programming language...

        >>> # Streaming example
        >>> for chunk in ai.search("Tell me about AI", stream=True):
        ...     print(chunk, end="", flush=True)
        Artificial Intelligence is...

        >>> # Raw response format
        >>> for chunk in ai.search("Hello", stream=True, raw=True):
        ...     print(chunk)
        {'text': 'Hello'}
        {'text': ' there!'}

    Args:
        cookies_path (str): Path to the cookies JSON file
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
        proxies (dict, optional): Proxy configuration for requests. Defaults to None.
        deep_search (bool, optional): Enable deep research mode. Defaults to True.
        reasoning_mode (bool, optional): Enable reasoning mode. Defaults to False.
    """

    def __init__(
        self,
        cookies_path: str,
        timeout: int = 600,
        proxies: Optional[dict] = None,
        deep_search: bool = True,
        reasoning_mode: bool = False,
    ):
        """Initialize the Liner API client.

        Args:
            cookies_path (str): Path to the cookies JSON file
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
            proxies (dict, optional): Proxy configuration for requests. Defaults to None.
            deep_search (bool, optional): Enable deep research mode. Defaults to True.
            reasoning_mode (bool, optional): Enable reasoning mode. Defaults to False.
        """
        self.session = Session()
        self.chat_endpoint = "https://getliner.com/lisa/v1/answer"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.cookies_path = cookies_path
        self.deep_search = deep_search
        self.reasoning_mode = reasoning_mode

        # Generate random IDs
        self.space_id = random.randint(10000000, 99999999)
        self.thread_id = random.randint(10000000, 99999999)
        self.user_message_id = random.randint(100000000, 999999999)
        self.user_id = random.randint(1000000, 9999999)

        self.headers = {
            "accept": "text/event-stream",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://getliner.com",
            "referer": f"https://getliner.com/search/s/{self.space_id}/t/t_{uuid4()}?mode=temp&msg-entry-type=main&build-id=kwJaNRjnCKjh7PijZgqV2",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": LitAgent().random()
        }

        # Load cookies from JSON file
        self.cookies = self._load_cookies()
        if not self.cookies:
            raise ValueError("Failed to load cookies from file")

        # Set headers and cookies in session
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies)
        if proxies:
            self.session.proxies.update(proxies) or {}

    def _load_cookies(self) -> Optional[Dict[str, str]]:
        """Load cookies from a JSON file.

        Returns:
            Optional[Dict[str, str]]: Dictionary of cookies if successful, None otherwise
        """
        try:
            with open(self.cookies_path, 'r') as f:
                cookies_data = json.load(f)
            return {cookie['name']: cookie['value'] for cookie in cookies_data}
        except FileNotFoundError:
            print(f"Error: {self.cookies_path} file not found!")
            return None
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {self.cookies_path}!")
            return None
        except KeyError:
            print(f"Error: Invalid cookie format in {self.cookies_path}! Each cookie must have 'name' and 'value' keys.")
            return None

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None], List[Any], Dict[str, Any], str]:
        """Search using the Liner API and get AI-generated responses.

        Args:
            prompt (str): The search query or prompt to send to the API.
            stream (bool, optional): If True, yields response chunks as they arrive.
                                   If False, returns complete response. Defaults to False.
            raw (bool, optional): If True, returns raw response dictionaries with 'text' key.
                                If False, returns SearchResponse objects that convert to text automatically.
                                Defaults to False.
            **kwargs: Additional keyword arguments.

        Returns:
            Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None], List[Any], Dict[str, Any], str]:
                - If stream=False: Returns complete response
                - If stream=True: Yields response chunks as they arrive

        Raises:
            APIConnectionError: If the API request fails
        """
        payload = {
            "spaceId": self.space_id,
            "threadId": self.thread_id,
            "userMessageId": self.user_message_id,
            "userId": self.user_id,
            "query": prompt,
            "agentId": "liner",
            "platform": "web",
            "regenerate": False,
            "showReferenceChunks": True,
            "mode": "general",
            "answerMode": "search",
            "isReasoningMode": self.reasoning_mode,
            "experimentId": random.randint(80, 90),
            "modelType": "liner",
            "experimentVariants": [],
            "isDeepResearchMode": self.deep_search
        }

        def for_stream():
            try:
                with self.session.post(
                    self.chat_endpoint,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                ) as response:
                    if not response.ok:
                        raise exceptions.APIConnectionError(
                            f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                        )

                    current_reasoning = ""
                    current_answer = ""

                    for line in response.iter_lines(decode_unicode=True):
                        if line == "event:finish_answer":
                            break

                        if line.startswith('data:'):
                            try:
                                data = json.loads(line[5:])  # Remove 'data:' prefix

                                # Handle reasoning updates if enabled
                                if self.reasoning_mode and 'reasoning' in data:
                                    current_reasoning += data['reasoning']
                                    if raw:
                                        yield {"text": data['reasoning']}
                                    else:
                                        yield SearchResponse(data['reasoning'])

                                # Handle answer updates
                                if 'answer' in data:
                                    current_answer += data['answer']
                                    if raw:
                                        yield {"text": data['answer']}
                                    else:
                                        yield SearchResponse(data['answer'])

                            except json.JSONDecodeError:
                                continue

            except Exception as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        def for_non_stream():
            full_response = ""
            for chunk in for_stream():
                if raw:
                    full_response = chunk
                    break
                else:
                    full_response += str(chunk)

            if raw:
                return full_response
            else:
                self.last_response = SearchResponse(full_response)
                return self.last_response

        return for_stream() if stream else for_non_stream()


if __name__ == "__main__":
    from typing import Generator

    from rich import print

    ai = Liner(cookies_path="cookies.json")
    response = ai.search(input(">>> "), stream=True, raw=False)
    if isinstance(response, Generator):
        for chunk in response:
            print(chunk, end="", flush=True)
    else:
        print(response)
