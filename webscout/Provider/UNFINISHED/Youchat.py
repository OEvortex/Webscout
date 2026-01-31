import datetime
import json
from typing import Any, Generator, Optional, Union, cast
from uuid import uuid4

import cloudscraper  # type: ignore

from webscout import exceptions
from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers


class YouChat(Provider):
    """
    This class provides methods for interacting with the You.com chat API in a consistent provider structure.
    """

    # Updated available models based on latest aiModels list
    # All models with isProOnly: false are included
    AVAILABLE_MODELS = [
        # ProOnly models (not available without subscription)
        # "gpt_4_5_preview",  # isProOnly: true
        # "openai_o3_mini_high",  # isProOnly: true
        # "openai_o3_mini_medium",  # isProOnly: true
        # "openai_o1",  # isProOnly: true
        # "openai_o1_preview",  # isProOnly: true
        # "openai_o1_mini",  # isProOnly: true
        # "gpt_4",  # isProOnly: true
        # "claude_3_7_sonnet_thinking",  # isProOnly: true
        # "claude_3_7_sonnet",  # isProOnly: true
        # "claude_3_5_sonnet",  # isProOnly: true
        # "claude_3_opus",  # isProOnly: true
        # "qwq_32b",  # isProOnly: true
        # "deepseek_r1",  # isProOnly: true
        # "deepseek_v3",  # isProOnly: true
        # "gemini_2_5_pro_experimental",  # isProOnly: true

        # Free models (isProOnly: false)
        "gpt_4o_mini",
        "gpt_4o",
        "gpt_4_turbo",
        "claude_3_sonnet",
        "claude_3_5_haiku",
        "qwen2p5_72b",
        "qwen2p5_coder_32b",
        "gemini_2_flash",
        "gemini_1_5_flash",
        "gemini_1_5_pro",
        "grok_2",
        "llama4_maverick",
        "llama4_scout",
        "llama3_1_405b",
        "mistral_large_2",
        "command_r_plus",

        # Free models not enabled for user chat modes
        "llama3_3_70b",  # isAllowedForUserChatModes: false
        "llama3_2_90b",  # isAllowedForUserChatModes: false
        "databricks_dbrx_instruct",  # isAllowedForUserChatModes: false
        "solar_1_mini",  # isAllowedForUserChatModes: false
        "dolphin_2_5",  # isAllowedForUserChatModes: false, isUncensoredModel: true
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
        model: str = "gemini_2_flash",
    ):
        """Instantiates YouChat

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
            model (str, optional): Model to use. Defaults to "gemini_2_flash".
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = cloudscraper.create_scraper()  # Create a Cloudscraper session
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://you.com/api/streamingSearch"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
            "Accept": "text/event-stream",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Referer": "https://you.com/search?q=hi&fromSearchBar=true&tbm=youchat",
            "Connection": "keep-alive",
            "DNT": "1",
            "Content-Type": "text/plain;charset=UTF-8",
        }
        self.cookies = {
            "uuid_guest": uuid4().hex,
            "uuid_guest_backup": uuid4().hex,
            "youchat_personalization": "true",
            "youchat_smart_learn": "true",
            "youpro_subscription": "false",
            "you_subscription": "freemium",
            "safesearch_guest": "Moderate",
            "__cf_bm": uuid4().hex,
        }

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
    ) -> dict:
        """Chat with AI

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to None.
            **kwargs: Additional keyword arguments.
        Returns:
           dict : {}
        ```json
        {
           "text" : "How may I assist you today?"
        }
        ```
        """
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

        trace_id = str(uuid4())
        conversation_turn_id = str(uuid4())

        # Current timestamp in ISO format for traceId
        current_time = datetime.datetime.now().isoformat()

        # Updated query parameters to match the new API format
        params = {
            "page": 1,
            "count": 10,
            "safeSearch": "Moderate",
            "mkt": "en-IN",
            "enable_worklow_generation_ux": "true",
            "domain": "youchat",
            "use_personalization_extraction": "true",
            "queryTraceId": trace_id,
            "chatId": trace_id,
            "conversationTurnId": conversation_turn_id,
            "pastChatLength": len(self.conversation.history) if hasattr(self.conversation, "history") else 0,
            "selectedChatMode": "custom",
            "selectedAiModel": self.model,
            # "enable_agent_clarification_questions": "true",
            "traceId": f"{trace_id}|{conversation_turn_id}|{current_time}",
            "use_nested_youchat_updates": "true"
        }

        # New payload format is JSON
        payload = {
            "query": conversation_prompt,
            "chat": "[]"
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint,
                headers=self.headers,
                cookies=self.cookies,
                params=params,
                data=json.dumps(payload),
                stream=True,
                timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_text = ""
            # New SSE event-based parsing
            event_type = None
            for value in response.iter_lines(
                decode_unicode=True,
                chunk_size=self.stream_chunk_size,
                delimiter="\n",
            ):
                if not value:
                    continue
                if value.startswith("event: "):
                    event_type = value[7:].strip()
                    continue
                if value.startswith("data: "):
                    data_str = value[6:]
                    if event_type == "youChatToken":
                        try:
                            data = json.loads(data_str)
                            token = data.get("youChatToken", "")
                            if token:
                                streaming_text += token
                                yield token if raw else dict(text=token)
                        except Exception:
                            pass
                    # Reset event_type after processing
                    event_type = None

            self.last_response.update(dict(text=streaming_text))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

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
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            raw (bool, optional): Return raw response chunks. Defaults to False.
            **kwargs: Additional keyword arguments.
        Returns:
            str: Response generated
        """

        def for_stream():
            for response in self.ask(
                prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield response
                else:
                    yield self.get_message(response)

        def for_non_stream():
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return result
            return self.get_message(result)

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        """Retrieves message only from response

            str: Message extracted
        """
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            return dict(response)["text"]
        return str(response)

if __name__ == '__main__':
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    # Test all available models
    working = 0
    total = len(YouChat.AVAILABLE_MODELS)

    for model in YouChat.AVAILABLE_MODELS:
        try:
            test_ai = YouChat(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            for chunk in response:
                response_text += chunk
                print(f"\r{model:<50} {'Testing...':<10}", end="", flush=True)

            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Truncate response if too long
                display_text = response_text.strip()[:50] + "..." if len(response_text.strip()) > 50 else response_text.strip()
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")
