import json
from typing import Any, Dict, Generator, Optional, Union, cast
from uuid import uuid4

import requests

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent
from webscout.search import DuckDuckGoSearch


class AndiSearch(Provider):
    required_auth = False
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
    ):
        """Instantiates AndiSearch

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://write.andisearch.com/v1/write_streaming"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "accept": "text/event-stream",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "andi-auth-key": "andi-summarizer",
            "andi-origin": "x-andi-origin",
            "authorization": str(uuid4()),
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://andisearch.com",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": LitAgent().random(),
            "x-amz-date": "20240730T031106Z",
            "x-amz-security-token": str(uuid4()),
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = AwesomePrompts().get_act(cast(Union[str, int], act), default=self.conversation.intro, case_insensitive=True
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro
        if proxies:
            self.session.proxies.update(proxies)

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        # Initialize the DuckDuckGo search instance
        ddg_search = DuckDuckGoSearch()

        # Fetch search results
        search_query = prompt
        search_results = ddg_search.text(search_query, max_results=7)

        # Format the search results into the required serp payload structure
        serp_payload = {
            "query": search_query,
            "serp": {
                "results_type": "Search",
                "answer": "",
                "type": "navigation",
                "title": "",
                "description": "",
                "image": "",
                "link": "",
                "source": "liftndrift.com",
                "engine": "andi-b",
                "results": [
                    {
                        "title": result.title,
                        "link": result.href,
                        "desc": result.body,
                        "image": "",
                        "type": "website",
                        "source": result.href.split("//")[1].split("/")[0] if "//" in result.href else result.href.split("/")[0]  # Extract the domain name
                    }
                    for result in search_results
                ]
            }
        }
        self.session.headers.update(self.headers)
        payload = serp_payload

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_text = ""
            # Use sanitize_stream for processing
            processed_stream = sanitize_stream(
                data=response.iter_lines(decode_unicode=True, chunk_size=self.stream_chunk_size, delimiter="\n"),
                intro_value=None,  # No prefix to strip
                to_json=False,  # Response is plain text
                yield_raw_on_error=True,
                raw=raw
            )

            for content_chunk in processed_stream:
                if content_chunk:
                    if raw:
                        yield content_chunk
                    else:
                        streaming_text += content_chunk + "\n"
                        yield dict(text=content_chunk)

            self.last_response = {"text": streaming_text.strip()}
            self.conversation.update_chat_history(prompt, streaming_text.strip())

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response if not raw else json.dumps(self.last_response)

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        raw = kwargs.get("raw", False)
        def for_stream():
            for response in self.ask(
                prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield response
                else:
                    yield self.get_message(cast(Dict[str, Any], response))

        def for_non_stream():
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, result)
            return self.get_message(cast(Dict[str, Any], result))

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        """Retrieves message only from response

        Args:
            response (Response): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        if not isinstance(response, dict):
            return str(response)
        resp_dict = cast(Dict[str, Any], response)
        return cast(str, resp_dict["text"])

if __name__ == '__main__':
    from rich import print
    ai = AndiSearch()
    response = ai.chat("tell me about india")
    for chunk in response:
        print(chunk, end="", flush=True)
