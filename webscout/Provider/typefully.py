from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers, sanitize_stream
from webscout.litagent import LitAgent


class TypefullyAI(Provider):
    required_auth = False
    AVAILABLE_MODELS = [
        "openai:gpt-4o-mini",
        "openai:gpt-4o",
        "anthropic:claude-haiku-4-5-20251001",
        "groq:llama-3.3-70b-versatile",
    ]

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
        system_prompt: str = "You're a helpful assistant.",
        model: str = "openai:gpt-4o-mini",
    ):
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://typefully.com/tools/ai/api/completion"
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.model = model
        self.output_length = max_tokens
        self.agent = LitAgent()
        self.headers = {
            "authority": "typefully.com",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://typefully.com",
            "referer": "https://typefully.com/tools/ai/chat-gpt-alternative",
            "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": self.agent.random(),
        }
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = AwesomePrompts().get_act(cast(Union[str, int], act), default=self.conversation.intro, case_insensitive=True
            ) or self.conversation.intro
        elif intro:
            self.conversation.intro = intro

    @staticmethod
    def _typefully_extractor(chunk) -> str:
        """Extracts content from Typefully AI SSE format."""
        import json

        # Handle parsed JSON objects (when to_json=True)
        if isinstance(chunk, dict):
            data = chunk
        elif isinstance(chunk, str):
            # Handle raw strings (when to_json=False or direct strings)
            line = chunk.strip()
            if line.startswith("data: "):
                line = line[6:]  # Remove 'data: ' prefix

                try:
                    # Parse JSON content
                    data = json.loads(line)
                except json.JSONDecodeError:
                    # If JSON parsing fails, return empty for non-JSON content
                    return ""
            else:
                # For non-SSE lines, return empty
                return ""
        else:
            # For other types (bytes, etc.), return empty
            return ""

        # Extract delta content for text chunks
        if data.get("type") == "text-delta" and "delta" in data:
            return data["delta"]
        elif data.get("type") == "text-start":
            # Return empty for text-start to avoid duplication
            return ""
        elif data.get("type") == "text-end":
            # Return empty for text-end to avoid duplication
            return ""
        else:
            # Return empty for other event types
            return ""

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
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")
        payload = {
            "prompt": conversation_prompt,
            "systemPrompt": self.system_prompt,
            "modelIdentifier": self.model,
            "outputLength": self.output_length,
        }

        def for_stream():
            try:
                response = self.session.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome120",
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )
                streaming_text = ""
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    content_extractor=self._typefully_extractor,
                    raw=raw,
                )
                for content_chunk in processed_stream:
                    if isinstance(content_chunk, bytes):
                        content_chunk = content_chunk.decode("utf-8", errors="ignore")
                    if content_chunk is None:
                        continue
                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                            yield dict(text=content_chunk)
                self.last_response.update(dict(text=streaming_text))
                self.conversation.update_chat_history(prompt, self.get_message(self.last_response))
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {e}")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"An unexpected error occurred ({type(e).__name__}): {e}"
                )

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response

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
                    yield cast(str, response)
                else:
                    yield self.get_message(cast(Response, response))

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
            else:
                return self.get_message(result)

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        response_dict = cast(Dict[str, Any], response)
        text = response_dict.get("text", "")
        try:
            formatted_text = text.replace("\\n", "\n").replace("\\n\\n", "\n\n")
            return formatted_text
        except Exception:
            return text


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)
    working = 0
    total = len(TypefullyAI.AVAILABLE_MODELS)
    for model in TypefullyAI.AVAILABLE_MODELS:
        try:
            test_ai = TypefullyAI(model=model, timeout=60)
            response_stream = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            if hasattr(response_stream, "__iter__") and not isinstance(response_stream, (str, bytes)):
                for chunk in response_stream:
                    response_text += chunk
            else:
                response_text = str(response_stream)

            if response_text and len(response_text.strip()) > 0:
                status = "OK"
                clean_text = response_text.strip()
                display_text = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
            else:
                status = "FAIL (Stream)"
                display_text = "Empty or invalid stream response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'FAIL':<10} {str(e)}")
