import base64
import datetime
import hashlib
import hmac
import json
import re
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast
from urllib.parse import urljoin, urlparse

from curl_cffi.requests import Session

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import (
    AwesomePrompts,
    Conversation,
    Optimizers,
    sanitize_stream,
)


class ChatZAI(Provider):
    """
    A class to interact with the ChatZAI AI API.
    """

    required_auth = False
    AVAILABLE_MODELS = ["GLM-4-6-API-V1"]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 1,
        model: str = "GLM-4-6-API-V1",
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ):
        """Instantiates ChatZAI

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 1.
            model (str, optional): LLM model name. Defaults to "GLM-4-6-API-V1".
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            system_prompt (str, optional): System prompt to guide the conversation. Defaults to None.
        """
        super().__init__(**kwargs)
        self.config: Dict[str, Any] = {
            "baseURL": "https://chat.z.ai",
            "endpoint": {
                "auth": "/api/v1/auths/",
                "models": "/api/models",
                "chat": "/api/v1/chats/new",
                "completions": "/api/chat/completions",
            },
            "secret": "junjie",
        }
        self.session = Session()
        self.session.headers.update(
            {
                "user-agent": (
                    "Mozilla/5.0 (Android 15; Mobile; SM-F958; rv:130.0) "
                    "Gecko/130.0 Firefox/130.0"
                )
            }
        )

        self.title = "Wi5haSBDaGF0IC0gRnJlZSBBSSBwb3dlcmVkIGJ5IEdMTS00LjYgJiBHTE0tNC41"
        self.models_data: Optional[List[Dict[str, Any]]] = None
        self.token: Optional[str] = None
        self.userId: Optional[str] = None
        self.chatId: Optional[str] = None
        self.cookies: Dict[str, str] = {"date": datetime.datetime.now().date().isoformat()}

        self.is_conversation = is_conversation
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.model = model
        self.timeout = timeout
        self.system_prompt = system_prompt
        self.proxies = proxies

        if proxies:
            self.session.proxies.update(proxies)

        self.conversation = Conversation(
            is_conversation, max_tokens, filepath, update_file
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

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

    def _get_cookie_string(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    def _authenticate(self) -> Dict[str, Any]:
        try:
            url = urljoin(str(self.config["baseURL"]), "/api/v1/auths/")
            r = self.session.get(
                url,
                headers={"Cookie": self._get_cookie_string()},
                timeout=self.timeout,
                impersonate="chrome110",
            )
            r.raise_for_status()
            auth_data = r.json()
            self.token = auth_data.get("token")
            self.userId = auth_data.get("id")
            self.cookies["token"] = self.token or ""
            # Note: curl_cffi handles cookies in session, but we keep this for compatibility
            return auth_data
        except Exception as exc:
            raise exceptions.FailedToGenerateResponseError(f"Authentication failed: {str(exc)}")

    def _fetch_models(self) -> List[Dict[str, Any]]:
        if not self.token:
            self._authenticate()
        try:
            url = urljoin(str(self.config["baseURL"]), "/api/models")
            r = self.session.get(
                url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Cookie": self._get_cookie_string(),
                },
                timeout=self.timeout,
                impersonate="chrome110",
            )
            r.raise_for_status()
            data = r.json()
            self.models_data = data.get("data", [])
            if self.models_data:
                self.AVAILABLE_MODELS = [m["id"] for m in self.models_data]
            return self.models_data or []
        except Exception as exc:
            raise exceptions.FailedToGenerateResponseError(f"Failed to fetch models: {str(exc)}")

    def _get_model_item(self, model_id: str) -> Dict[str, Any]:
        if not self.models_data:
            self._fetch_models()
        assert self.models_data is not None, "Models not loaded"
        model = next((m for m in self.models_data if m.get("id") == model_id), None)
        if not model:
            raise ValueError(f"Model {model_id} not found.")
        model_copy = json.loads(json.dumps(model))
        model_copy.setdefault("info", {})["user_id"] = self.userId
        return model_copy

    def _create_new_chat(self, prompt: str, model_id: str) -> str:
        if not self.token:
            self._authenticate()
        if not self.models_data:
            self._fetch_models()

        timestamp = int(time.time())
        message_id = str(uuid.uuid4())
        payload = {
            "chat": {
                "id": "",
                "title": "New Chat",
                "models": [model_id],
                "params": {},
                "history": {
                    "messages": {
                        message_id: {
                            "id": message_id,
                            "parentId": None,
                            "childrenIds": [],
                            "role": "user",
                            "content": prompt,
                            "timestamp": timestamp,
                            "models": [model_id],
                        }
                    },
                    "currentId": message_id,
                },
                "messages": [
                    {
                        "id": message_id,
                        "parentId": None,
                        "childrenIds": [],
                        "role": "user",
                        "content": prompt,
                        "timestamp": timestamp,
                        "models": [model_id],
                    }
                ],
                "tags": [],
                "flags": [],
                "features": [
                    {"type": "mcp", "server": "vibe-coding", "status": "hidden"},
                    {"type": "mcp", "server": "ppt-maker", "status": "hidden"},
                    {"type": "mcp", "server": "image-search", "status": "hidden"},
                    {"type": "mcp", "server": "deep-research", "status": "hidden"},
                    {"type": "tool_selector", "server": "tool_selector", "status": "hidden"},
                    {"type": "mcp", "server": "advanced-search", "status": "hidden"},
                ],
                "mcp_servers": [],
                "enable_thinking": True,
                "auto_web_search": False,
                "timestamp": timestamp * 1000 - 253,
            }
        }
        try:
            url = urljoin(str(self.config["baseURL"]), "/api/v1/chats/new")
            r = self.session.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Cookie": self._get_cookie_string(),
                },
                timeout=self.timeout,
                impersonate="chrome110",
            )
            r.raise_for_status()
            data = r.json()
            self.chatId = data.get("id")
            return self.chatId or ""
        except Exception as exc:
            raise exceptions.FailedToGenerateResponseError(f"Failed to create chat: {str(exc)}")

    def _sign(self, prompt: str, chat_id: str) -> Dict[str, Any]:
        url = urljoin(self.config["baseURL"], f"/c/{chat_id}")
        timestamp = str(int(time.time() * 1000))
        request_id = str(uuid.uuid4())
        current_date = datetime.datetime.now()

        params = {
            "timestamp": timestamp,
            "requestId": request_id,
            "user_id": self.userId,
            "version": "0.0.1",
            "platform": "web",
            "token": self.token,
            "user_agent": self.session.headers.get("user-agent"),
            "language": "id-ID",
            "languages": "id-ID,en-US,id,en",
            "timezone": "UTC", # Simplified
            "cookie_enabled": "true",
            "screen_width": "461",
            "screen_height": "1024",
            "screen_resolution": "461x1024",
            "viewport_height": "1051",
            "viewport_width": "543",
            "viewport_size": "543x1051",
            "color_depth": "24",
            "pixel_ratio": "1.328460693359375",
            "current_url": url,
            "pathname": urlparse(url).path,
            "search": urlparse(url).query,
            "hash": urlparse(url).fragment,
            "host": urlparse(url).netloc,
            "hostname": urlparse(url).hostname,
            "protocol": urlparse(url).scheme,
            "referrer": "",
            "title": base64.b64decode(self.title).decode("utf-8", errors="ignore"),
            "timezone_offset": "0",
            "local_time": current_date.isoformat(),
            "utc_time": datetime.datetime.now(datetime.timezone.utc).ctime(),
            "is_mobile": "true",
            "is_touch": "true",
            "max_touch_points": "5",
            "browser_name": "Chrome",
            "os_name": "Android",
        }

        sp_items = sorted(
            {"timestamp": timestamp, "requestId": request_id, "user_id": self.userId}.items()
        )
        sorted_params = ",".join(f"{k},{v}" for k, v in sp_items)
        encoded_prompt = base64.b64encode(prompt.strip().encode("utf-8")).decode("utf-8")
        time_bucket = int(int(timestamp) / 300000)

        key = hmac.new(
            str(self.config["secret"]).encode("utf-8"),
            str(time_bucket).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        signature = hmac.new(
            key.encode("utf-8"),
            "|".join([sorted_params, encoded_prompt, timestamp]).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return {"signature": signature, "params": params}

    def _finalize_parsed_data(self, accumulated_data: Dict[str, Any]) -> Dict[str, Any]:
        result = {"thinking": "", "answer": "", "search": [], "usage": accumulated_data.get("usage")}

        if accumulated_data.get("thinking") and accumulated_data["thinking"].get("content"):
            tcontent = accumulated_data["thinking"]["content"]
            thinking_match = re.search(r"<details[^>]*>([\s\S]*)$", tcontent, re.S)
            result["thinking"] = (thinking_match.group(1).strip() if thinking_match else tcontent.strip())

        if accumulated_data.get("answer") and accumulated_data["answer"].get("content"):
            finish_content = accumulated_data["answer"]["content"]
            tool_call_match = re.search(r"<glm_block[\s\S]*?>[\s\S]*?<\/glm_block>", finish_content, re.S)
            if tool_call_match:
                tool_call_string = tool_call_match.group(0)
                end_index = tool_call_match.end()
                result["answer"] = finish_content[end_index:].strip()
                try:
                    inner_match = re.search(r"<glm_block[^>]*>([\s\S]*?)<\/glm_block>", tool_call_string, re.S)
                    if inner_match and inner_match.group(1):
                        tool_data = json.loads(inner_match.group(1))
                        result["search"] = tool_data.get("data", {}).get("browser", {}).get("search_result", [])
                except Exception:
                    pass
            else:
                result["answer"] = finish_content.strip()

        result["thinking"] = re.sub(r"【turn0search(\d+)】", r"[\1]", str(result["thinking"]))
        result["answer"] = re.sub(r"【turn0search(\d+)】", r"[\1]", str(result["answer"]))
        return result

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        if not prompt:
            raise ValueError("Prompt is required.")

        if not self.token or not self.userId:
            self._authenticate()

        if not self.chatId:
            self._create_new_chat(prompt, self.model)

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        chat_id_for_sign = str(uuid.uuid4())
        sign_res = self._sign(prompt, chat_id_for_sign)
        signature = sign_res["signature"]
        params = sign_res["params"]
        model_item = self._get_model_item(self.model)

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        # Add history if conversation
        if self.is_conversation:
            # Simple history integration for now
            messages.append({"role": "user", "content": conversation_prompt})
        else:
            messages.append({"role": "user", "content": prompt})

        chat_data = {
            "stream": True,
            "model": self.model,
            "messages": messages,
            "signature_prompt": prompt,
            "params": {},
            "tool_servers": [],
            "features": {
                "image_generation": False,
                "code_interpreter": False,
                "web_search": kwargs.get("search", False),
                "auto_web_search": kwargs.get("search", False),
                "preview_mode": True,
                "flags": [],
                "features": [
                    {"type": "mcp", "server": "vibe-coding", "status": "hidden"},
                    {"type": "mcp", "server": "ppt-maker", "status": "hidden"},
                    {"type": "mcp", "server": "image-search", "status": "hidden"},
                    {"type": "mcp", "server": "deep-research", "status": "hidden"},
                    {"type": "tool_selector", "server": "tool_selector", "status": "hidden"},
                    {"type": "mcp", "server": "advanced-search", "status": "hidden"},
                ],
                "enable_thinking": kwargs.get("deepthink", True),
            },
            "variables": {
                "{{USER_NAME}}": f"Guest-{int(time.time() * 1000)}",
                "{{USER_LOCATION}}": "Unknown",
                "{{CURRENT_DATETIME}}": datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
                "{{CURRENT_DATE}}": datetime.date.today().isoformat(),
                "{{CURRENT_TIME}}": datetime.datetime.now().time().strftime("%H:%M:%S"),
                "{{CURRENT_WEEKDAY}}": datetime.datetime.now().strftime("%A"),
                "{{CURRENT_TIMEZONE}}": params.get("timezone"),
                "{{USER_LANGUAGE}}": params.get("language"),
            },
            "model_item": model_item,
            "chat_id": chat_id_for_sign,
            "id": str(uuid.uuid4()),
        }

        def for_stream():
            accumulated_data = {"thinking": {"content": ""}, "answer": {"content": ""}, "usage": None}
            try:
                url = urljoin(str(self.config["baseURL"]), "/api/chat/completions")
                response = self.session.post(
                    url,
                    json=chat_data,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Cookie": self._get_cookie_string(),
                        "X-Signature": signature,
                        "X-FE-Version": "prod-fe-1.0.52",
                    },
                    params=params,
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )

                if response.status_code != 200:
                    raise exceptions.FailedToGenerateResponseError(f"Failed: {response.status_code} - {response.text}")

                for line in response.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue

                    json_string = line[len("data:"):].strip()
                    if json_string == "[DONE]":
                        continue

                    try:
                        parsed = json.loads(json_string)
                        data = parsed.get("data")
                        if not data or "phase" not in data:
                            continue

                        phase = data["phase"]
                        delta = data.get("delta_content")
                        if delta is not None:
                            if phase not in accumulated_data:
                                accumulated_data[phase] = {"content": ""}
                            accumulated_data[phase]["content"] += delta
                            if not raw:
                                yield {"text": delta, "phase": phase}
                            else:
                                yield line

                        if data.get("usage"):
                            accumulated_data["usage"] = data["usage"]
                    except Exception:
                        continue

                self.last_response = self._finalize_parsed_data(accumulated_data)
                self.conversation.update_chat_history(prompt, self.get_message(self.last_response))
            except Exception as exc:
                raise exceptions.FailedToGenerateResponseError(str(exc))

        def for_non_stream():
            # We reuse the stream logic but collect it
            full_text = ""
            for chunk in for_stream():
                if isinstance(chunk, dict) and chunk.get("phase") == "answer":
                    full_text += chunk.get("text", "")
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
        if stream:
            def for_stream():
                gen = self.ask(prompt, True, raw, optimizer, conversationally, **kwargs)
                for response in gen:
                    if raw:
                        yield cast(str, response)
                    else:
                        # Only yield answer phase text for chat()
                        if not isinstance(response, dict):
                            continue
                        if response.get("phase") == "answer":
                            yield response.get("text", "")
            return for_stream()
        else:
            result = self.ask(prompt, False, raw, optimizer, conversationally, **kwargs)
            if raw:
                return cast(str, result)
            return self.get_message(result)

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        resp_dict = cast(Dict[str, Any], response)
        return cast(str, (resp_dict.get("answer") or ""))


if __name__ == "__main__":

    client = ChatZAI()
    for chunk in client.chat("Hello, who are you?", stream=True):
        print(chunk, end="", flush=True)
