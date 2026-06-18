import re
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError, requests

from llm4free.llm.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from llm4free.llm.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
)

from llm4free.litagent import LitAgent

BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"


def _extract_answer(text: str) -> str:
    text = re.sub(r"\[REASON_START\].*?\[REASON_DONE\]", "", text, flags=re.DOTALL)
    text = re.sub(r"\[REASON_DONE\]", "", text)
    text = re.sub(r"\[REASON_START\]", "", text)
    return text.strip()


class Completions(BaseCompletions):
    def __init__(self, client: "HeckAI"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        model = self._client.convert_model_name(model)

        question = ""
        for msg in messages:
            if msg.get("role") == "user":
                question = msg.get("content", "")

        payload: Dict[str, Any] = {
            "model": model,
            "question": question,
            "language": self._client.language,
            "sessionId": self._client.session_id,
            "previousQuestion": None,
            "previousAnswer": None,
            "imgUrls": [],
            "superSmartMode": False,
        }

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, payload, timeout, proxies)
        else:
            return self._create_non_stream(
                request_id, created_time, model, payload, timeout, proxies
            )

    def _create_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            response = self._client.session.post(
                self._client.url,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),  # ty:ignore[invalid-argument-type]
            )
            response.raise_for_status()

            full_text = ""

            for line in response.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="replace")
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data in ("[ANSWER_START]", "[ANSWER_DONE]", "[RELATE_Q_START]", "[RELATE_Q_DONE]"):
                    continue
                if data.startswith("[") and data.endswith("]"):
                    continue
                if data.startswith("{") or data.startswith('"'):
                    continue
                full_text += data

            cleaned = _extract_answer(full_text)
            if cleaned:
                delta = ChoiceDelta(content=cleaned)
                choice = Choice(index=0, delta=delta, finish_reason=None)
                yield ChatCompletionChunk(
                    id=request_id,
                    choices=[choice],
                    created=created_time,
                    model=model,
                )

            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            yield ChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
            )
        except CurlError as e:
            print(f"{RED}Error during HeckAI stream request: {e}{RESET}")
            raise IOError(f"HeckAI request failed: {e}") from e

    def _create_non_stream(
        self,
        request_id: str,
        created_time: int,
        model: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
    ) -> ChatCompletion:
        try:
            answer_parts: List[str] = []
            in_answer = False
            response = self._client.session.post(
                self._client.url,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies or getattr(self._client, "proxies", None),  # ty:ignore[invalid-argument-type]
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="replace")
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[ANSWER_START]":
                    in_answer = True
                    continue
                if data == "[ANSWER_DONE]":
                    in_answer = False
                    continue
                if data.startswith("[") and data.endswith("]"):
                    continue
                if in_answer:
                    answer_parts.append(data)

            full_text = "".join(answer_parts)
            full_text = _extract_answer(full_text)

            prompt_tokens = count_tokens(payload.get("question", ""))
            completion_tokens = count_tokens(full_text)
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )
            message = ChatCompletionMessage(role="assistant", content=full_text)
            choice = Choice(index=0, message=message, finish_reason="stop")
            return ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )
        except Exception as e:
            print(f"{RED}Error during HeckAI non-stream request: {e}{RESET}")
            raise IOError(f"HeckAI request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "HeckAI"):
        self.completions = Completions(client)


class HeckAI(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = [
        "deepseek/deepseek-v4-flash",
        "deepseek/deepseek-v4-pro",
        "tencent/hy3-preview",
        "qwen/qwen3.7-plus",
        "stepfun/step-3.7-flash",
        "google/gemini-3.1-flash-lite",
        "google/gemini-3-flash-preview",
        "openai/gpt-5.4-mini",
        "minimax/minimax-m3",
    ]

    def __init__(self, timeout: int = 30, language: str = "English"):
        self.timeout = timeout
        self.language = language
        self.url = "https://api.heckai.weight-wave.com/api/ha/v1/chat"
        self.session_id = str(uuid.uuid4())

        agent = LitAgent()
        self.headers = {
            "User-Agent": agent.random(),
            "Content-Type": "application/json",
            "Origin": "https://heck.ai",
            "Referer": "https://heck.ai/",
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    def convert_model_name(self, model: str) -> str:
        if model in self.AVAILABLE_MODELS:
            return model
        for available_model in self.AVAILABLE_MODELS:
            if model.lower() in available_model.lower():
                return available_model
        print(
            f"{BOLD}Warning: Model '{model}' not found, using default 'openai/gpt-5.4-mini'{RESET}"
        )
        return "openai/gpt-5.4-mini"

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in HeckAI.AVAILABLE_MODELS:
        try:
            client = HeckAI(timeout=60)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Say 'Hello' in one word"},
                ],
                stream=False,
            )

            if (
                isinstance(response, ChatCompletion)
                and response.choices
                and response.choices[0].message
                and response.choices[0].message.content
            ):
                status = "✓"
                display_text = response.choices[0].message.content.strip()
                display_text = display_text[:50] + "..." if len(display_text) > 50 else display_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"{model:<50} {'✗':<10} {str(e)}")