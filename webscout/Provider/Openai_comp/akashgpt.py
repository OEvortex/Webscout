import json
import re
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi.requests import Session

from webscout.litagent import LitAgent as agent

# Import base classes and utility structures
from webscout.Provider.Openai_comp.base import (
    BaseChat,
    BaseCompletions,
    OpenAICompatibleProvider,
    SimpleModelList,
)
from webscout.Provider.Openai_comp.utils import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    Choice,
    ChoiceDelta,
    CompletionUsage,
    count_tokens,
    format_prompt,
)

# AkashGPT constants
AVAILABLE_MODELS = [
    "Qwen/Qwen3-30B-A3B",
    "DeepSeek-V3.1",
    "Meta-Llama-3-3-70B-Instruct",
    "DeepSeek-V3.2"
]


def _akash_extractor(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
    """Extracts content from the AkashGPT stream format '0:"..."'."""
    if isinstance(chunk, str):
        match = re.search(r'0:"(.*?)"', chunk)
        if match:
            # Decode potential unicode escapes like \u00e9
            content = match.group(1).encode().decode("unicode_escape")
            return content.replace("\\\\", "\\").replace(
                '\\"', '"'
            )  # Handle escaped backslashes and quotes
    return None


class Completions(BaseCompletions):
    def __init__(self, client: "AkashGPT"):
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
        proxies: Optional[dict] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Create a chat completion with AkashGPT API.
        Mimics openai.chat.completions.create
        """
        # Use format_prompt utility to format the conversation
        conversation_prompt = format_prompt(messages, add_special_tokens=True, include_system=True)
        # Generate request ID and timestamp
        request_id = str(uuid.uuid4())
        created_time = int(time.time())

        # Use the provided model directly
        akash_model = model

        if stream:
            return self._create_streaming(
                request_id,
                created_time,
                akash_model,
                conversation_prompt,
                messages,
                max_tokens,
                temperature,
                top_p,
                timeout,
                proxies,
            )
        else:
            return self._create_non_streaming(
                request_id,
                created_time,
                akash_model,
                conversation_prompt,
                messages,
                max_tokens,
                temperature,
                top_p,
                timeout,
                proxies,
            )

    def _create_streaming(
        self,
        request_id: str,
        created_time: int,
        model: str,
        conversation_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        temperature: Optional[float],
        top_p: Optional[float],
        timeout: Optional[int],
        proxies: Optional[dict],
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Implementation for streaming chat completions."""
        try:
            # Calculate prompt tokens
            prompt_tokens = count_tokens(conversation_prompt)
            completion_tokens = 0
            total_tokens = 0

            # Make the API request to AkashGPT
            payload = {
                "id": str(uuid.uuid4()).replace("-", ""),
                "messages": messages,
                "model": model,
                "temperature": temperature or 0.6,
                "topP": top_p or 0.9,
                "context": [],
            }

            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                timeout=timeout or 30,
                proxies=proxies,
                stream=True,
            )

            if not response.ok:
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            full_content = ""
            prompt_tokens = 0
            completion_tokens = 0

            # Process the streaming response
            for line in response.iter_lines(decode_unicode=False):
                if line:
                    if isinstance(line, bytes):
                        line = line.decode("utf-8")
                    line = line.strip()

                    # Parse the AkashGPT response format
                    if line.startswith('0:"') and line.endswith('"'):
                        # Extract content from 0:"content" format
                        content = line[3:-1]  # Remove 0:" and "
                        # Decode escaped characters
                        content = content.encode().decode('unicode_escape')

                        # Calculate delta (new content since last chunk)
                        delta_content = content[len(full_content):] if content.startswith(full_content) else content
                        full_content = content

                        if delta_content:
                            completion_tokens = count_tokens(full_content)
                            total_tokens = prompt_tokens + completion_tokens

                            delta = ChoiceDelta(content=delta_content, role="assistant")
                            choice = Choice(index=0, delta=delta, finish_reason=None)
                            chunk_response = ChatCompletionChunk(
                                id=request_id,
                                choices=[choice],
                                created=created_time,
                                model=model,
                            )
                            chunk_response.usage = {
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "total_tokens": total_tokens,
                            }
                            yield chunk_response

                    elif line.startswith('e:{'):
                        # Extract usage from e: line
                        import json
                        try:
                            usage_data = json.loads(line[2:])  # Remove 'e:'
                            prompt_tokens = usage_data.get('usage', {}).get('promptTokens', prompt_tokens)
                            completion_tokens = usage_data.get('usage', {}).get('completionTokens', completion_tokens)
                        except json.JSONDecodeError:
                            pass
                    elif line.startswith('d:{'):
                        # Alternative usage extraction from d: line
                        if prompt_tokens == 0:  # Only if not already set
                            import json
                            try:
                                usage_data = json.loads(line[2:])  # Remove 'd:'
                                prompt_tokens = usage_data.get('usage', {}).get('promptTokens', prompt_tokens)
                                completion_tokens = usage_data.get('usage', {}).get('completionTokens', completion_tokens)
                            except json.JSONDecodeError:
                                pass

            # Final chunk with finish_reason
            total_tokens = prompt_tokens + completion_tokens
            delta = ChoiceDelta(content=None)
            choice = Choice(index=0, delta=delta, finish_reason="stop")
            final_chunk = ChatCompletionChunk(
                id=request_id, choices=[choice], created=created_time, model=model
            )
            final_chunk.usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }
            yield final_chunk

        except Exception as e:
            raise IOError(f"AkashGPT streaming request failed: {e}") from e

    def _create_non_streaming(
        self,
        request_id: str,
        created_time: int,
        model: str,
        conversation_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        temperature: Optional[float],
        top_p: Optional[float],
        timeout: Optional[int],
        proxies: Optional[dict],
    ) -> ChatCompletion:
        """Implementation for non-streaming chat completions."""
        try:
            # Calculate prompt tokens
            prompt_tokens = count_tokens(conversation_prompt)

            # Make the API request to AkashGPT
            payload = {
                "id": str(uuid.uuid4()).replace("-", ""),
                "messages": messages,
                "model": model,
                "temperature": temperature or 0.6,
                "topP": top_p or 0.9,
                "context": [],
            }

            response = self._client.session.post(
                self._client.api_endpoint,
                headers=self._client.headers,
                json=payload,
                timeout=timeout or 30,
                proxies=proxies,
                stream=True,  # <-- Enable streaming mode for iter_lines
            )

            if not response.ok:
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            # Collect the full response
            full_content = ""
            prompt_tokens = 0
            completion_tokens = 0

            for line in response.iter_lines(decode_unicode=False):
                if line:
                    if isinstance(line, bytes):
                        line = line.decode("utf-8")
                    line = line.strip()

                    # Parse the AkashGPT response format
                    if line.startswith('0:"') and line.endswith('"'):
                        # Extract content from 0:"content" format
                        content = line[3:-1]  # Remove 0:" and "
                        # Decode escaped characters
                        content = content.encode().decode('unicode_escape')
                        full_content += content
                    elif line.startswith('e:{'):
                        # Extract usage from e: line
                        import json
                        try:
                            usage_data = json.loads(line[2:])  # Remove 'e:'
                            prompt_tokens = usage_data.get('usage', {}).get('promptTokens', 0)
                            completion_tokens = usage_data.get('usage', {}).get('completionTokens', 0)
                        except json.JSONDecodeError:
                            pass
                    elif line.startswith('d:{'):
                        # Alternative usage extraction from d: line
                        if prompt_tokens == 0:  # Only if not already set
                            import json
                            try:
                                usage_data = json.loads(line[2:])  # Remove 'd:'
                                prompt_tokens = usage_data.get('usage', {}).get('promptTokens', 0)
                                completion_tokens = usage_data.get('usage', {}).get('completionTokens', 0)
                            except json.JSONDecodeError:
                                pass

            # Calculate completion tokens if not provided by API
            if completion_tokens == 0:
                completion_tokens = count_tokens(full_content)
            total_tokens = prompt_tokens + completion_tokens

            # Create the completion message
            message = ChatCompletionMessage(role="assistant", content=full_content)

            # Create the choice
            choice = Choice(index=0, message=message, finish_reason="stop")

            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            # Create the completion object
            completion = ChatCompletion(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                usage=usage,
            )

            return completion

        except Exception as e:
            raise IOError(f"AkashGPT request failed: {e}") from e


class Chat(BaseChat):
    def __init__(self, client: "AkashGPT"):
        self.completions = Completions(client)


class AkashGPT(OpenAICompatibleProvider):
    """
    OpenAI-compatible client for AkashGPT API.

    Usage:
        client = AkashGPT()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """

    required_auth = False

    AVAILABLE_MODELS = AVAILABLE_MODELS

    def __init__(
        self, tools: Optional[List] = None, proxies: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the AkashGPT-compatible client.

        Args:
            tools: Optional list of tools to register with the provider
            proxies: Optional proxy configuration dict
        """
        super().__init__(api_key=None, tools=tools, proxies=proxies)

        # Replace requests.Session with curlcffi.requests.Session for better performance
        self.session = Session()
        if self.proxies:
            self.session.proxies.update(self.proxies)

        self.timeout = 30
        self.api_endpoint = "https://chat.akash.network/api/chat"
        self.user_agent = agent().random()
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "cookie": "cookie-consent=accepted; _ga=GA1.1.411212745.1768894804; cf_clearance=kUAFsdi8masn4kzDg.g3pDEYmIefkuN4kPT8kAmC.wI-1769979385-1.2.1.1-5i01zppXtcir7LNZjhp.JiQVGEU.ewcNSRnrhdm9uvnuqvgkv_IQmUI0ec9vI7u9kBibnMuKYvteTdmlMyCxXr9RUlhS5hT8MW860slfcjsTbzzsgk7os0LGu9yfVzbZfHm5Qeoo_FFF4ckJz_gnSxKkF0QVzAOv6uwGvICLvv3hNyzgzWV.sEJJi6Fx8dSlze5u5StYbYhbRD97W3rDMpqDyIQBTF8Ts3jh_2keQxA; _ga_LFRGN2J2RV=GS2.1.s1769979388$o2$g0$t1769979388$j60$l0$h0; session_token=ffe05badc451a5f1571a2cd85a5205f650cb2549a6c805162c27d18cc64d5ab7",
            "dnt": "1",
            "origin": "https://chat.akash.network",
            "priority": "u=1, i",
            "referer": "https://chat.akash.network/",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": self.user_agent,
        }

        self.session.headers.update(self.headers)

        # Initialize chat interface
        self.chat = Chat(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    from rich import print
    client = AkashGPT()
    print("NON-STREAMING RESPONSE:")
    response = client.chat.completions.create(
        model="DeepSeek-V3.2",
        messages=[
            {"role": "user", "content": "Hello, how are you?"},
        ],
    )
    print(response)
    print("\nSTREAMING RESPONSE:")
    stream_response = client.chat.completions.create(
        model="DeepSeek-V3.2",
        messages=[
            {"role": "user", "content": "Hello, how are you?"},
        ],
        stream=True,
    )
    for chunk in stream_response:
        print(chunk)
