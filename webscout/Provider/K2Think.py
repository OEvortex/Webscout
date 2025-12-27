import json
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers
from webscout.litagent import LitAgent
from webscout.sanitize import sanitize_stream


class K2Think(Provider):
    """
    A class to interact with the K2Think AI API.
    """
    required_auth = False
    AVAILABLE_MODELS = [
        "MBZUAI-IFM/K2-Think",

    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 1,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1,
        model: str = "MBZUAI-IFM/K2-Think",
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        base_url: str = "https://www.k2think.ai/api/guest/chat/completions",
        system_prompt: str = "You are a helpful assistant.",
        browser: str = "chrome"
    ):
        """Initializes the K2Think AI client."""
        self.url = base_url

        # Initialize LitAgent
        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)

        # Use the fingerprint for headers
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "User-Agent": self.fingerprint.get("user_agent", ""),
            "Origin": "https://www.k2think.ai",
            "Referer": "https://www.k2think.ai/guest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Ch-Ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Priority": "u=1, i"
        }

        # Initialize curl_cffi Session
        self.session = Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        act_prompt = (
            AwesomePrompts().get_act(cast(Union[str, int], act), default=None, case_insensitive=True
            )
            if act
            else intro
        )
        if act_prompt:
            self.conversation.intro = act_prompt
        self.conversation.history_offset = history_offset

    def refresh_identity(self, browser: Optional[str] = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)

        # Update headers with new fingerprint (only relevant ones)
        self.headers.update({
            "Accept-Language": self.fingerprint["accept_language"],
            "User-Agent": self.fingerprint.get("user_agent", ""),
        })

        # Update session headers
        self.session.headers.update(self.headers)

        return self.fingerprint

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
                raise exceptions.FailedToGenerateResponseError(f"Optimizer is not one of {self.__available_optimizers}")

        # Payload construction
        payload = {
            "stream": stream,
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ],
            "params": {}
        }

        def for_stream():
            try:
                # Use curl_cffi session post with impersonate
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()

                streaming_text = ""

                # Use sanitize_stream with extract_regexes
                answer_pattern = r'<answer>([\s\S]*?)<\/answer>'

                def content_extractor(data):
                    """Extract 'content' field from JSON object"""
                    if isinstance(data, dict):
                        return data.get('content', '')
                    return None

                for chunk in sanitize_stream(
                    response.iter_lines(),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=content_extractor,
                    extract_regexes=[answer_pattern],
                    raw=raw
                ):
                    if chunk:
                        if raw:
                            streaming_text += chunk if isinstance(chunk, str) else str(chunk)
                            yield chunk
                        else:
                            text = chunk if isinstance(chunk, str) else chunk.get('text', str(chunk))
                            streaming_text += text
                            yield {"text": text}

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {str(e)}") from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed ({type(e).__name__}): {str(e)}") from e
            finally:
                # Update history after stream finishes or fails
                if streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)

        def for_non_stream():
            streaming_text = ""
            try:
                # For non-streaming, we can get the full response
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()

                data = response.json()
                # The response is usually a standard OpenAI-like JSON or just has content
                content = ""
                if isinstance(data, dict):
                    if "choices" in data:
                        content = data["choices"][0].get("message", {}).get("content", "")
                    else:
                        content = data.get("content", "")

                # Extract using regex if needed (for reasoning models)
                import re
                answer_match = re.search(r'<answer>([\s\S]*?)<\/answer>', content)
                if answer_match:
                    streaming_text = answer_match.group(1)
                else:
                    # Strip think tag if present
                    streaming_text = re.sub(r'<think>[\s\S]*?<\/think>', '', content).strip()
                    if not streaming_text:
                        streaming_text = content

                self.last_response = {"text": streaming_text}
                self.conversation.update_chat_history(prompt, streaming_text)
                return self.last_response if not raw else streaming_text

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {str(e)}") from e
            except Exception as e:
                err_text = ""
                if hasattr(e, 'response'):
                    response_obj = getattr(e, 'response')
                    if hasattr(response_obj, 'text'):
                        err_text = getattr(response_obj, 'text')
                raise exceptions.FailedToGenerateResponseError(f"Request failed ({type(e).__name__}): {e} - {err_text}") from e

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
        if stream:
            def for_stream_chat():
                gen = self.ask(
                    prompt, stream=True, raw=raw,
                    optimizer=optimizer, conversationally=conversationally
                )
                if hasattr(gen, "__iter__"):
                    for response in gen:
                        if raw:
                            yield cast(str, response)
                        else:
                            yield self.get_message(response)
            return for_stream_chat()
        else:
            result = self.ask(
                prompt,
                stream=False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return cast(str, result)
            return self.get_message(result)

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')

if __name__ == "__main__":
    # Simple test
    try:
        ai = K2Think(model="MBZUAI-IFM/K2-Think", timeout=30)
        response = ai.chat("What is artificial intelligence?", stream=True, raw=False)
        if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
            for chunk in response:
                print(chunk, end="", flush=True)
        else:
            print(response)
        print()
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
