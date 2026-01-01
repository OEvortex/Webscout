import json
from typing import Any, Dict, Generator, List, Optional, Union, cast

import requests

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent as Lit


class TextPollinationsAI(Provider):
    """
    A class to interact with the Pollinations AI API.
    """

    required_auth = False
    _models_url = "https://text.pollinations.ai/models"

    # Static list as fallback
    AVAILABLE_MODELS = [
        "deepseek",
        "gemini",
        "gemini-search",
        "mistral",
        "openai",
        "openai-audio",
        "openai-fast",
        "openai-large",
        "openai-reasoning",
        "qwen-coder",
        "roblox-rp",
        "bidara",
        "chickytutor",
        "evil",
        "midijourney",
        "rtist",
        "unity",
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 8096,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "openai",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """Initializes the TextPollinationsAI API client."""
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://text.pollinations.ai/openai"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.proxies = proxies

        # Fetch latest models dynamically to ensure we have the most up-to-date list
        self.update_available_models()

        if model not in self.AVAILABLE_MODELS:
            # warn or just allow it? allowing it for flexibility
            if model not in self.AVAILABLE_MODELS:
                pass  # User might know a model we don't

        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": Lit().random(),
            "Content-Type": "application/json",
        }

        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = (
                AwesomePrompts().get_act(
                    cast(Union[str, int], act),
                    default=self.conversation.intro,
                    case_insensitive=True,
                )
                or self.conversation.intro
            )
        elif intro:
            self.conversation.intro = intro

    def update_available_models(self):
        try:
            response = requests.get(
                self._models_url, headers={"Accept": "application/json"}, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    new_models = [
                        m.get("name") for m in data if isinstance(m, dict) and "name" in m
                    ]
                    if new_models:
                        self.AVAILABLE_MODELS = new_models
        except Exception:
            pass

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        """Chat with AI"""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "model": self.model,
            "stream": stream,
        }

        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        def for_stream():
            try:
                response = self.session.post(
                    self.api_endpoint, json=payload, stream=True, timeout=self.timeout
                )
                response.raise_for_status()

                streaming_text = ""
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",  # Standard OpenAI SSE prefix
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=lambda chunk: chunk.get("choices", [{}])[0].get("delta")
                    if isinstance(chunk, dict)
                    else None,
                    yield_raw_on_error=False,
                    raw=raw,
                )

                for delta in processed_stream:
                    if isinstance(delta, dict):
                        # Extract content if available
                        if "content" in delta and delta["content"] is not None:
                            content = delta["content"]
                            if raw:
                                yield content
                            else:
                                streaming_text += content
                                yield dict(text=content)
                        # Extract tool calls if available
                        elif "tool_calls" in delta:
                            tool_calls = delta["tool_calls"]
                            if raw:
                                yield json.dumps(tool_calls)
                            else:
                                yield dict(tool_calls=tool_calls)

                self.last_response = {"text": streaming_text}
                if streaming_text:
                    self.conversation.update_chat_history(prompt, streaming_text)

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Stream request failed: {e}") from e

        def for_non_stream():
            try:
                # Force stream=False for non-streaming request
                payload["stream"] = False
                response = self.session.post(self.api_endpoint, json=payload, timeout=self.timeout)
                response.raise_for_status()

                # Use sanitize_stream to parse the non-streaming JSON response
                processed_stream = sanitize_stream(
                    data=response.text,
                    to_json=True,
                    intro_value=None,
                    content_extractor=lambda chunk: chunk if isinstance(chunk, dict) else None,
                    yield_raw_on_error=False,
                )
                # Extract the single result
                resp_json = next(processed_stream, None)

                # Check for standard OpenAI response structure
                if resp_json and "choices" in resp_json and len(resp_json["choices"]) > 0:
                    choice = resp_json["choices"][0]
                    content = choice.get("message", {}).get("content")
                    tool_calls = choice.get("message", {}).get("tool_calls")
                    result = content if content else (tool_calls if tool_calls else "")

                    self.last_response = (
                        {"text": content or ""}
                        if content
                        else ({"tool_calls": tool_calls} if tool_calls else {})
                    )
                    self.conversation.update_chat_history(prompt, content or "")

                    if raw:
                        return (
                            content if content else (json.dumps(tool_calls) if tool_calls else "")
                        )
                    return result

                else:
                    return {}

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"Non-stream request failed: {e}"
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
        raw = kwargs.get("raw", False)
        tools = kwargs.get("tools")
        tool_choice = kwargs.get("tool_choice")

        def for_stream():
            for response in self.ask(
                prompt,
                True,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
                tools=tools,
                tool_choice=tool_choice,
            ):
                if raw:
                    yield cast(str, response)
                else:
                    yield self.get_message(cast(Dict[str, Any], response))

        def for_non_stream():
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
                tools=tools,
                tool_choice=tool_choice,
            )
            if raw:
                return cast(str, result)
            return self.get_message(cast(Dict[str, Any], result))

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        """Retrieves message only from response"""
        if not isinstance(response, dict):
            return str(response)
        if "text" in response:
            return response["text"]
        elif "tool_calls" in response:
            return json.dumps(response["tool_calls"])
        return ""


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    # Test only a subset to be fast
    test_models = ["openai", "gemini"]

    for model in test_models:
        try:
            print(f"\r{model:<50} {'Testing...':<10}", end="", flush=True)
            test_ai = TextPollinationsAI(model=model, timeout=60)

            # Non-stream test
            start_response = test_ai.chat("Hello!", stream=False)
            if start_response and isinstance(start_response, str):
                status = "✓"
                display = start_response[:30] + "..."
            else:
                status = "✗"
                display = "Empty or invalid type"

            print(f"\r{model:<50} {status:<10} {display}")

        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)[:50]}")
