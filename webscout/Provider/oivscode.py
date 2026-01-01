import random
import secrets
import string
import uuid
from typing import Any, Dict, Generator, Optional, Union, cast

import requests

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream


class oivscode(Provider):
    """
    A class to interact with a test API.
    """

    required_auth = False
    AVAILABLE_MODELS = ["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet", "o1-mini"]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 1024,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "gpt-4o-mini",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """
        Initializes the oivscode with given parameters.
        """
        # Skip strict validation - the API will handle invalid models
        # We have fallback models defined, so any model in that list is acceptable

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoints = [
            "https://oi-vscode-server-5.onrender.com/v1/chat/completions",
            "https://oi-vscode-server-0501.onrender.com/v1/chat/completions",
        ]
        self.api_endpoint = random.choice(self.api_endpoints)
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt

        # Generate ClientId (UUID)
        self.client_id = str(uuid.uuid4())

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,en-GB;q=0.8,en-IN;q=0.7",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "ClientId": self.client_id,  # Add ClientId
        }
        self.userid = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(21)
        )
        self.headers["userid"] = self.userid

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath or "", update_file
        )
        self.conversation.history_offset = history_offset

        act_prompt = (
            AwesomePrompts().get_act(
                cast(Union[str, int], act), default=None, case_insensitive=True
            )
            if act
            else intro
        )
        if act_prompt:
            self.conversation.intro = act_prompt

        if proxies:
            self.session.proxies.update(proxies)

    def _post_with_failover(self, payload, stream, timeout):
        """Try all endpoints until one succeeds, else raise last error."""
        endpoints = self.api_endpoints.copy()
        random.shuffle(endpoints)
        last_exception = None
        for endpoint in endpoints:
            try:
                response = self.session.post(endpoint, json=payload, stream=stream, timeout=timeout)
                if not response.ok:
                    last_exception = exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )
                    continue
                return response
            except Exception as e:
                last_exception = e
                continue
        if last_exception:
            raise last_exception
        raise exceptions.FailedToGenerateResponseError("All API endpoints failed.")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Chat with AI (DeepInfra-style streaming and non-streaming)"""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream,
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self._post_with_failover(payload, stream=True, timeout=self.timeout)
                response.raise_for_status()
                # Use sanitize_stream for robust OpenAI-style streaming
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=lambda chunk: chunk.get("choices", [{}])[0]
                    .get("delta", {})
                    .get("content")
                    if isinstance(chunk, dict)
                    else None,
                    yield_raw_on_error=False,
                    raw=raw,
                )
                for content_chunk in processed_stream:
                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                            resp = dict(text=content_chunk)
                            yield resp if not raw else content_chunk
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Streaming request failed: {e}"
                ) from e
            finally:
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            try:
                response = self._post_with_failover(payload, stream=False, timeout=self.timeout)
                response.raise_for_status()
                response_text = response.text
                processed_stream = sanitize_stream(
                    data=response_text,
                    to_json=True,
                    intro_value="",
                    content_extractor=lambda chunk: chunk.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content")
                    if isinstance(chunk, dict)
                    else None,
                    yield_raw_on_error=False,
                    raw=raw,
                )
                content = next(processed_stream, None)
                if raw:
                    return content
                content = content if isinstance(content, str) else ""
                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return self.last_response if not raw else content
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Non-streaming request failed: {e}"
                ) from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            **kwargs: Additional parameters including raw.
        Returns:
            str: Response generated
        """
        raw = kwargs.get("raw", False)
        if stream:

            def for_stream():
                gen = self.ask(
                    prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally
                )
                if hasattr(gen, "__iter__"):
                    for response in gen:
                        if raw:
                            yield cast(str, response)
                        else:
                            yield self.get_message(response)

            return for_stream()
        else:
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, result)
            return self.get_message(result)

    def get_message(self, response: Response) -> str:
        """Retrieves message content from response, handling both streaming and non-streaming formats."""
        if not isinstance(response, dict):
            return str(response)
        # Streaming chunk: choices[0]["delta"]["content"]
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            if "delta" in choice and "content" in choice["delta"]:
                return choice["delta"]["content"]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
        # Fallback for non-standard or legacy responses
        if "text" in response:
            return response["text"]
        return ""

    def fetch_available_models(self):
        """Fetches available models from the /models endpoint of all API endpoints."""
        endpoints = self.api_endpoints.copy()
        random.shuffle(endpoints)
        results = {}
        errors = []
        for endpoint in endpoints:
            models_url = endpoint.replace("/v1/chat/completions", "/v1/models")
            try:
                response = self.session.get(models_url, timeout=self.timeout)
                if response.ok:
                    data = response.json()
                    if isinstance(data, dict) and "data" in data:
                        models = [
                            m["id"] if isinstance(m, dict) and "id" in m else m
                            for m in data["data"]
                        ]
                    elif isinstance(data, list):
                        models = data
                    else:
                        models = list(data.keys()) if isinstance(data, dict) else []
                    results[models_url] = models
                else:
                    errors.append(
                        f"Failed to fetch models from {models_url}: {response.status_code} {response.text}"
                    )
            except Exception as e:
                errors.append(f"Error fetching from {models_url}: {e}")
        if results:
            return results
        else:
            return {}


try:
    _temp_client = oivscode()
    _fetched = _temp_client.fetch_available_models()
    if _fetched:
        oivscode.AVAILABLE_MODELS = list(
            set(
                oivscode.AVAILABLE_MODELS + [m for models in _fetched.values() for m in models if m]
            )
        )
except Exception:
    pass

if __name__ == "__main__":
    from rich import print

    chatbot = oivscode()
    chatbot.fetch_available_models()
    response = chatbot.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
