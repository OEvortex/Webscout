import json
import random
import re
import string
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union

import cloudscraper
from curl_cffi.requests import Session
from rich import print

from webscout.litagent.agent import LitAgent

# Import base classes and utility structures
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


# --- ChutesAI API Key Auto-Generator ---
def generate_chutesai_api_key():
    url = "https://chutes.ai/auth/start?/create"
    def generate_username(length=8):
        return ''.join(random.choices(string.ascii_letters, k=length))
    username = generate_username()
    agent = LitAgent()
    fingerprint = agent.generate_fingerprint("chrome")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": fingerprint["user_agent"],
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": fingerprint["accept_language"],
        "DNT": "1",
        "Origin": "https://chutes.ai",
        "Referer": "https://chutes.ai/auth/start",
        "Sec-Ch-Ua": fingerprint["sec_ch_ua"],
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": fingerprint["platform"],
        "X-Sveltekit-Action": "true"
    }
    data = {
        "username": username,
        "coldkey": "hotkey",
        "__superform_id": "xpsmbd"
    }
    scraper = cloudscraper.create_scraper()
    response = scraper.post(url, headers=headers, data=data)
    print(f"[bold green]Status:[/] {response.status_code}")

    # Ensure response is decoded as UTF-8
    response.encoding = 'utf-8'

    try:
        resp_json = response.json()
    except Exception:
        try:
            # Try to decode the response text with UTF-8 explicitly
            decoded_text = response.content.decode('utf-8', errors='replace')
            print(decoded_text)
        except Exception:
            print("Failed to decode response content")
        return None
    print(resp_json)
    # Extract the api_key using regex from the 'data' field
    if 'data' in resp_json:
        api_key_match = re.search(r'(cpk_[a-zA-Z0-9.]+)', resp_json['data'])
        if api_key_match:
            api_key = api_key_match.group(1)
            print(f"[bold yellow]Auto-generated ChutesAI API Key:[/] {api_key}")
            return api_key
        else:
            print("[red]API key not found in response data.")
    return None

# --- ChutesAI Client ---

class Completions(BaseCompletions):
    def __init__(self, client: 'ChutesAI'):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 1024,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        **kwargs: Any
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create
        """
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        payload.update(kwargs)

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, payload)
        else:
            return self._create_non_stream(request_id, created_time, model, payload)

    def _create_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any]
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            response = self._client.scraper.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=self._client.timeout
            )
            response.raise_for_status()

            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8', errors='replace').strip()
                    if decoded_line.startswith("data: "):
                        json_str = decoded_line[6:]
                        if json_str == "[DONE]":
                            break
                        try:
                            data = json.loads(json_str)
                            choices = data.get('choices')
                            if not choices:
                                continue
                            choice_data = choices[0] if choices else {}
                            delta_data = choice_data.get('delta', {})
                            finish_reason = choice_data.get('finish_reason')

                            usage_data = data.get('usage', {})
                            if usage_data:
                                prompt_tokens = usage_data.get('prompt_tokens', prompt_tokens)
                                completion_tokens = usage_data.get('completion_tokens', completion_tokens)
                                total_tokens = usage_data.get('total_tokens', total_tokens)

                            delta = ChoiceDelta(
                                content=delta_data.get('content'),
                                role=delta_data.get('role'),
                                tool_calls=delta_data.get('tool_calls')
                            )
                            choice = Choice(
                                index=choice_data.get('index', 0),
                                delta=delta,
                                finish_reason=finish_reason,
                                logprobs=choice_data.get('logprobs')
                            )
                            chunk = ChatCompletionChunk(
                                id=request_id,
                                choices=[choice],
                                created=created_time,
                                model=model,
                                system_fingerprint=data.get('system_fingerprint')
                            )
                            if hasattr(chunk, "model_dump"):
                                chunk_dict = chunk.model_dump(exclude_none=True)
                            else:
                                chunk_dict = chunk.dict(exclude_none=True)
                            usage_dict = {
                                "prompt_tokens": prompt_tokens or 10,
                                "completion_tokens": completion_tokens or (len(delta_data.get('content', '')) if delta_data.get('content') else 0),
                                "total_tokens": total_tokens or (10 + (len(delta_data.get('content', '')) if delta_data.get('content') else 0)),
                                "estimated_cost": None
                            }
                            if delta_data.get('content'):
                                completion_tokens += 1
                                total_tokens = prompt_tokens + completion_tokens
                                usage_dict["completion_tokens"] = completion_tokens
                                usage_dict["total_tokens"] = total_tokens
                            chunk_dict["usage"] = usage_dict
                            yield chunk
                        except json.JSONDecodeError:
                            print(f"Warning: Could not decode JSON line: {json_str}")
                            continue
        except Exception as e:
            print(f"Error during ChutesAI stream request: {e}")
            raise IOError(f"ChutesAI request failed: {e}") from e
        except Exception as e:
            print(f"Error processing ChutesAI stream: {e}")
            raise

    def _create_non_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any]
    ) -> ChatCompletion:
        try:
            response = self._client.scraper.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                timeout=self._client.timeout
            )
            response.raise_for_status()
            data = response.json()
            choices_data = data.get('choices', [])
            usage_data = data.get('usage', {})
            choices = []
            for choice_d in choices_data:
                message_d = choice_d.get('message', {})
                message = ChatCompletionMessage(
                    role=message_d.get('role', 'assistant'),
                    content=message_d.get('content', '')
                )
                choice = Choice(
                    index=choice_d.get('index', 0),
                    message=message,
                    finish_reason=choice_d.get('finish_reason', 'stop')
                )
                choices.append(choice)
            usage = CompletionUsage(
                prompt_tokens=usage_data.get('prompt_tokens', 0),
                completion_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=usage_data.get('total_tokens', 0)
            )
            completion = ChatCompletion(
                id=request_id,
                choices=choices,
                created=created_time,
                model=data.get('model', model),
                usage=usage,
            )
            return completion
        except Exception as e:
            print(f"Error during ChutesAI non-stream request: {e}")
            raise IOError(f"ChutesAI request failed: {e}") from e
        except Exception as e:
            print(f"Error processing ChutesAI response: {e}")
            raise

class Chat(BaseChat):
    def __init__(self, client: 'ChutesAI'):
        self.completions = Completions(client)

class ChutesAI(OpenAICompatibleProvider):
    AVAILABLE_MODELS = [
        "deepseek-ai/DeepSeek-V3-0324",
        "deepseek-ai/DeepSeek-R1",
        "NousResearch/DeepHermes-3-Mistral-24B-Preview",
        "chutesai/Llama-4-Maverick-17B-128E-Instruct-FP8",
    ]
    def __init__(self, api_key: Optional[str] = None,):
        self.timeout = None  # Infinite timeout
        self.base_url = "https://llm.chutes.ai/v1/chat/completions"

        # Always generate a new API key, ignore any provided key
        print("[yellow]Generating new ChutesAI API key...[/]")
        self.api_key = generate_chutesai_api_key()

        if not self.api_key:
            print("[red]Failed to generate API key. Retrying...[/]")
            # Retry once more
            self.api_key = generate_chutesai_api_key()

        if not self.api_key:
            raise ValueError("Failed to generate ChutesAI API key after multiple attempts.")

        print(f"[green]Successfully generated API key: {self.api_key[:20]}...[/]")

        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.scraper.headers.update(self.headers)
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)

if __name__ == "__main__":
    try:
        # Example usage - always use generated API key
        client = ChutesAI()

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]

        print("[cyan]Making API request...[/]")
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            messages=messages,
            max_tokens=50,
            stream=True
        )
        for chunk in response:
            if isinstance(chunk, (bytes, str)):
                chunk_dict = {"chunk": chunk}
            elif hasattr(chunk, "model_dump") and callable(chunk.model_dump):
                chunk_dict = chunk.model_dump()  # type: ignore[call-arg]
            elif hasattr(chunk, "dict") and callable(chunk.dict):
                chunk_dict = chunk.dict()  # type: ignore[call-arg]
            else:
                chunk_dict = {"chunk": chunk}
            print(f"[green]Response Chunk:[/] {chunk_dict}")

    except Exception as e:
        print(f"[red]Error: {e}[/]")
        print("[yellow]If the issue persists, the ChutesAI service might be down or the API key generation method needs updating.[/]")
