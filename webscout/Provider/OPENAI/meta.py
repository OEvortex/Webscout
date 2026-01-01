"""
Meta AI OpenAI-compatible provider.
Uses Meta AI's chat API via web authentication.
"""

import json
import time
import urllib.parse
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from webscout.Provider.OPENAI.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from webscout.Provider.OPENAI.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
)

try:
    from ...litagent import LitAgent
except ImportError:
    LitAgent = None  # type: ignore


def generate_offline_threading_id() -> str:
    """Generates an offline threading ID."""
    import random
    max_int = (1 << 64) - 1
    mask22_bits = (1 << 22) - 1
    timestamp = int(time.time() * 1000)
    random_value = random.getrandbits(64)
    shifted_timestamp = timestamp << 22
    masked_random = random_value & mask22_bits
    return str((shifted_timestamp | masked_random) & max_int)


def extract_value(text: str, start_str: str, end_str: str) -> str:
    """Helper function to extract a specific value from the given text."""
    start = text.find(start_str) + len(start_str)
    end = text.find(end_str, start)
    return text[start:end]


def format_response(response: dict) -> str:
    """Formats the response from Meta AI."""
    text = ""
    for content in (
        response.get("data", {})
        .get("node", {})
        .get("bot_response_message", {})
        .get("composed_text", {})
        .get("content", [])
    ):
        text += content.get("text", "") + "\n"
    return text.strip()


class Completions(BaseCompletions):
    def __init__(self, client: 'Meta'):
        self._client = client

    def create(
        self,
        *,
        model: str = "meta-ai",
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 4096,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create
        """
        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        # Get just the last user message content for the prompt
        prompt = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
                break

        if stream:
            return self._create_stream(request_id, created_time, model, prompt, timeout, proxies)
        else:
            return self._create_non_stream(request_id, created_time, model, prompt, timeout, proxies)

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        prompt: str,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Implementation for streaming chat completions."""
        try:
            # Get access token if not authenticated
            if not self._client.is_authed:
                self._client.access_token = self._client.get_access_token()
                auth_payload = {"access_token": self._client.access_token}
                url = "https://graph.meta.ai/graphql?locale=user"
            else:
                auth_payload = {"fb_dtsg": self._client.cookies["fb_dtsg"]}
                url = "https://www.meta.ai/api/graphql/"

            if not self._client.external_conversation_id:
                self._client.external_conversation_id = str(uuid.uuid4())

            payload = {
                **auth_payload,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useAbraSendMessageMutation",
                "variables": json.dumps({
                    "message": {"sensitive_string_value": prompt},
                    "externalConversationId": self._client.external_conversation_id,
                    "offlineThreadingId": generate_offline_threading_id(),
                    "suggestedPromptIndex": None,
                    "flashVideoRecapInput": {"images": []},
                    "flashPreviewInput": None,
                    "promptPrefix": None,
                    "entrypoint": "ABRA__CHAT__TEXT",
                    "icebreaker_type": "TEXT",
                    "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                    "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
                }),
                "server_timestamps": "true",
                "doc_id": "7783822248314888",
            }
            payload = urllib.parse.urlencode(payload)

            headers = {
                "content-type": "application/x-www-form-urlencoded",
                "x-fb-friendly-name": "useAbraSendMessageMutation",
            }
            if self._client.is_authed:
                headers["cookie"] = f'abra_sess={self._client.cookies["abra_sess"]}'

            response = self._client.session.post(
                url,
                headers=headers,
                data=payload,
                stream=True,
                timeout=timeout or self._client.timeout
            )

            if not response.ok:
                raise IOError(f"Meta AI request failed: {response.status_code} - {response.text}")

            prompt_tokens = 0
            completion_tokens = 0
            full_response = ""

            lines = response.iter_lines()
            # Check first line for errors
            first_line = next(lines, None)
            if first_line:
                try:
                    is_error = json.loads(first_line)
                    if len(is_error.get("errors", [])) > 0:
                        raise IOError(f"Meta AI returned error: {first_line}")
                except json.JSONDecodeError:
                    pass

            for line in lines:
                if line:
                    try:
                        json_line = json.loads(line)
                        message_text = format_response(json_line)

                        if not message_text:
                            continue

                        # Yield only the new content (delta)
                        if message_text and len(message_text) > len(full_response):
                            new_content = message_text[len(full_response):]
                            full_response = message_text
                            completion_tokens += 1

                            delta = ChoiceDelta(
                                content=new_content,
                                role="assistant" if completion_tokens == 1 else None,
                                tool_calls=None
                            )
                            choice = Choice(
                                index=0,
                                delta=delta,
                                finish_reason=None,
                                logprobs=None
                            )
                            chunk = ChatCompletionChunk(
                                id=request_id,
                                choices=[choice],
                                created=created_time,
                                model=model,
                                system_fingerprint=None
                            )
                            chunk.usage = {
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "total_tokens": prompt_tokens + completion_tokens,
                                "estimated_cost": None
                            }
                            yield chunk

                    except json.JSONDecodeError:
                        continue

            # Final chunk with finish_reason="stop"
            delta = ChoiceDelta(content=None, role=None, tool_calls=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop", logprobs=None)
            chunk = ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                system_fingerprint=None
            )
            chunk.usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "estimated_cost": None
            }
            yield chunk

        except CurlError as e:
            raise IOError(f"Meta AI stream request failed (CurlError): {e}") from e
        except Exception as e:
            raise IOError(f"Meta AI stream request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        prompt: str,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None
    ) -> ChatCompletion:
        """Implementation for non-streaming chat completions."""
        try:
            # Get access token if not authenticated
            if not self._client.is_authed:
                self._client.access_token = self._client.get_access_token()
                auth_payload = {"access_token": self._client.access_token}
                url = "https://graph.meta.ai/graphql?locale=user"
            else:
                auth_payload = {"fb_dtsg": self._client.cookies["fb_dtsg"]}
                url = "https://www.meta.ai/api/graphql/"

            if not self._client.external_conversation_id:
                self._client.external_conversation_id = str(uuid.uuid4())

            payload = {
                **auth_payload,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useAbraSendMessageMutation",
                "variables": json.dumps({
                    "message": {"sensitive_string_value": prompt},
                    "externalConversationId": self._client.external_conversation_id,
                    "offlineThreadingId": generate_offline_threading_id(),
                    "suggestedPromptIndex": None,
                    "flashVideoRecapInput": {"images": []},
                    "flashPreviewInput": None,
                    "promptPrefix": None,
                    "entrypoint": "ABRA__CHAT__TEXT",
                    "icebreaker_type": "TEXT",
                    "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                    "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
                }),
                "server_timestamps": "true",
                "doc_id": "7783822248314888",
            }
            payload = urllib.parse.urlencode(payload)

            headers = {
                "content-type": "application/x-www-form-urlencoded",
                "x-fb-friendly-name": "useAbraSendMessageMutation",
            }
            if self._client.is_authed:
                headers["cookie"] = f'abra_sess={self._client.cookies["abra_sess"]}'

            response = self._client.session.post(
                url,
                headers=headers,
                data=payload,
                timeout=timeout or self._client.timeout
            )

            if not response.ok:
                raise IOError(f"Meta AI request failed: {response.status_code} - {response.text}")

            # Extract the last response from the streamed data
            raw_response = response.text
            last_response = None
            full_message = ""

            for line in raw_response.split("\n"):
                try:
                    json_line = json.loads(line)
                    bot_response_message = (
                        json_line.get("data", {})
                        .get("node", {})
                        .get("bot_response_message", {})
                    )
                    streaming_state = bot_response_message.get("streaming_state")
                    if streaming_state == "OVERALL_DONE":
                        last_response = json_line
                except json.JSONDecodeError:
                    continue

            if last_response:
                full_message = format_response(last_response)

            message = ChatCompletionMessage(
                role="assistant",
                content=full_message
            )
            choice = Choice(
                index=0,
                message=message,
                finish_reason="stop"
            )
            usage = CompletionUsage(
                prompt_tokens=0,
                completion_tokens=len(full_message.split()),
                total_tokens=len(full_message.split())
            )

            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )
            return completion

        except CurlError as e:
            raise IOError(f"Meta AI non-stream request failed (CurlError): {e}") from e
        except Exception as e:
            raise IOError(f"Meta AI non-stream request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: 'Meta'):
        self.completions = Completions(client)


class Meta(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for Meta AI.
    No API key required - uses web authentication.
    """
    required_auth = False

    AVAILABLE_MODELS = [
        "meta-ai",
        "llama-3"
    ]

    def __init__(
        self,
        fb_email: Optional[str] = None,
        fb_password: Optional[str] = None,
        timeout: int = 60,
        proxies: Optional[Dict[str, str]] = None,
        browser: str = "chrome"
    ):
        """
        Initialize the Meta AI OpenAI-compatible client.

        Args:
            fb_email: Optional Facebook email for authenticated access
            fb_password: Optional Facebook password for authenticated access
            timeout: Request timeout in seconds
            proxies: Proxy settings
            browser: Browser type for fingerprinting
        """
        self.fb_email = fb_email
        self.fb_password = fb_password
        self.timeout = timeout
        self.proxies = proxies or {}

        self.session = Session()
        if LitAgent:
            agent = LitAgent()
            self.session.headers.update({
                "user-agent": agent.random()
            })

        self.access_token = None
        self.is_authed = fb_password is not None and fb_email is not None
        self.cookies = self._get_cookies()
        self.external_conversation_id = None
        self.offline_threading_id = None

        if proxies:
            if proxies:
                self.session.proxies.update(cast(Any, proxies))

        # Initialize chat interface
        self.chat = Chat(self)

    def _get_cookies(self) -> dict:
        """Extracts necessary cookies from the Meta AI main page."""
        headers = {}

        # Import Facebook login if needed
        if self.fb_email is not None and self.fb_password is not None:
            try:
                from webscout.Provider.meta import get_fb_session
                fb_session = get_fb_session(self.fb_email, self.fb_password, self.proxies)
                headers = {"cookie": f"abra_sess={fb_session['abra_sess']}"}
            except Exception:
                pass

        response = self.session.get(
            url="https://www.meta.ai/",
            headers=headers,
            proxies=self.proxies,
        )

        cookies = {
            "_js_datr": extract_value(
                response.text, start_str='_js_datr":{"value":"', end_str='",'
            ),
            "datr": extract_value(
                response.text, start_str='datr":{"value":"', end_str='",'
            ),
            "lsd": extract_value(
                response.text, start_str='"LSD",[],{"token":"', end_str='"}'
            ),
            "fb_dtsg": extract_value(
                response.text, start_str='DTSGInitData",[],{"token":"', end_str='"'
            ),
        }

        if len(headers) > 0:
            try:
                from webscout.Provider.meta import get_fb_session
                fb_session = get_fb_session(self.fb_email, self.fb_password, self.proxies)
                cookies["abra_sess"] = fb_session["abra_sess"]
            except Exception:
                pass
        else:
            cookies["abra_csrf"] = extract_value(
                response.text, start_str='abra_csrf":{"value":"', end_str='",'
            )
        return cookies

    def get_access_token(self) -> str:
        """Retrieves an access token using Meta's authentication API."""
        if self.access_token:
            return self.access_token

        url = "https://www.meta.ai/api/graphql/"
        payload = {
            "lsd": self.cookies["lsd"],
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraAcceptTOSForTempUserMutation",
            "variables": {
                "dob": "1999-01-01",
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            },
            "doc_id": "7604648749596940",
        }
        payload = urllib.parse.urlencode(payload)
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "cookie": f'_js_datr={self.cookies["_js_datr"]}; '
            f'abra_csrf={self.cookies.get("abra_csrf", "")}; datr={self.cookies["datr"]};',
            "sec-fetch-site": "same-origin",
            "x-fb-friendly-name": "useAbraAcceptTOSForTempUserMutation",
        }

        response = self.session.post(url, headers=headers, data=payload)

        try:
            auth_json = response.json()
        except json.JSONDecodeError:
            raise IOError(
                "Unable to receive a valid response from Meta AI. "
                "This is likely due to your region being blocked."
            )

        access_token = auth_json["data"]["xab_abra_accept_terms_of_service"][
            "new_temp_user_auth"
        ]["access_token"]

        time.sleep(1)  # Meta needs time to register cookies
        return access_token

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    # Example usage - no API key required
    client = Meta()
    print(f"Available models: {client.models.list()}")

    # Test non-streaming
    response = client.chat.completions.create(
        model="meta-ai",
        messages=[{"role": "user", "content": "Hello!"}],
        stream=False
    )
    print(f"Response: {response.choices[0].message.content}")  # type: ignore

    # Test streaming
    print("\nStreaming response:")
    for chunk in client.chat.completions.create(
        model="meta-ai",
        messages=[{"role": "user", "content": "Tell me a short joke"}],
        stream=True
    ):
        if chunk.choices[0].delta.content:  # type: ignore
            print(chunk.choices[0].delta.content, end="", flush=True)  # type: ignore
    print()
