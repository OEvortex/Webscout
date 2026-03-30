import urllib.parse
from typing import Any, Dict, Generator, Optional, Union, cast

from curl_cffi.requests import RequestsError, Session

from webscout.AIbase import Provider, Response
from webscout.AIutel import AwesomePrompts, Conversation, Optimizers

# Available models for AI4Chat
MODELS = {
    # Popular Models
    "gpt-5.2": "GPT 5.2",
    "claude-haiku-4.5": "Claude Haiku 4.5",
    "gemini-3-flash": "Gemini 3 Flash",
    "grok-4.1-fast": "Grok 4.1 Fast",
    "kimi-k2.5": "Kimi K2.5",
    # OpenAI Models
    "gpt-3.5": "ChatGPT (GPT 3.5)",
    "gpt-4o": "GPT 4o",
    "gpt-4.5": "GPT-4.5",
    "gpt-4o-mini": "GPT 4o Mini",
    "gpt-4o-search-preview": "GPT-4o Search Preview",
    "gpt-4o-mini-search-preview": "GPT-4o mini Search Preview",
    "gpt-4.1": "GPT 4.1",
    "gpt-4.1-mini": "GPT 4.1 Mini",
    "gpt-4.1-nano": "GPT 4.1 Nano",
    "codex-mini": "Codex Mini",
    "o1": "o1",
    "o1-pro": "o1-pro",
    "o3-mini": "o3-mini",
    "o3-mini-high": "o3-mini-high",
    "o4-mini": "o4 Mini",
    "o4-mini-high": "o4 Mini High",
    "gpt-oss-20b": "GPT OSS 20B",
    "gpt-oss-120b": "GPT OSS 120B",
    "gpt-5-mini": "GPT-5 Mini",
    "gpt-5-nano": "GPT-5 Nano",
    "gpt-5": "GPT-5",
    "gpt-5.1": "GPT 5.1",
    "gpt-5.1-codex": "GPT 5.1 Codex",
    "gpt-5.1-codex-mini": "GPT 5.1 Codex-Mini",
    "gpt-5.2-codex": "GPT 5.2 Codex",
    "gpt-5.3-codex": "GPT 5.3 Codex",
    "gpt-5.3": "GPT 5.3",
    "gpt-5.4": "GPT 5.4",
    "gpt-5.4-pro": "GPT 5.4 Pro",
    # Anthropic Models
    "claude-3-haiku": "Claude 3 Haiku",
    "claude-3.5-haiku": "Claude 3.5 Haiku",
    "claude-3.7-sonnet": "Claude 3.7 Sonnet",
    "claude-sonnet-4": "Claude Sonnet 4",
    "claude-opus-4": "Claude Opus 4",
    "claude-opus-4.1": "Claude Opus 4.1",
    "claude-sonnet-4.5": "Claude Sonnet 4.5",
    "claude-opus-4.6": "Claude Opus 4.6",
    "claude-sonnet-4.6": "Claude Sonnet 4.6",
    # DeepSeek Models
    "deepseek-v3": "DeepSeek V3",
    "deepseek-v3.1": "DeepSeek v3.1",
    "deepseek-v3.2": "DeepSeek v3.2",
    "r1-distill-qwen-1.5b": "R1 Distill Qwen 1.5B",
    "r1-distill-qwen-14b": "R1 Distill Qwen 14B",
    "r1-distill-qwen-32b": "R1 Distill Qwen 32B",
    "r1-distill-llama-70b": "R1 Distill Llama 70B",
    "r1": "R1",
    # Google Models
    "gemini-flash-2.0": "Gemini Flash 2.0",
    "gemini-flash-lite-2.0": "Gemini Flash Lite 2.0",
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite",
    "gemini-2.5-flash-preview": "Gemini 2.5 Flash Preview",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemma-2-9b": "Gemma 2 9B",
    "gemma-2-27b": "Gemma 2 27B",
    "gemma-3-27b": "Gemma 3 27B",
    "gemini-3-pro": "Gemini 3 Pro",
    "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite",
    "gemini-3.1-pro": "Gemini 3.1 Pro",
    # Meta Models
    "llama-v3-8b": "Llama v3 8B",
    "llama-v3-70b": "Llama v3 70B",
    "llama-v3.1-8b": "Llama v3.1 8B",
    "llama-v3.1-70b": "Llama v3.1 70B",
    "llama-v3.1-405b": "Llama v3.1 405B",
    "llama-v3.2-1b": "Llama v3.2 1B",
    "llama-v3.2-3b": "Llama v3.2 3B",
    "llama-v3.2-11b": "Llama v3.2 11B",
    "llama-v3.2-90b": "Llama v3.2 90B",
    "llama-v3.3-70b": "Llama v3.3 70B",
    "llama-4-scout": "Llama 4 Scout",
    "llama-4-maverick": "Llama 4 Maverick",
    # Mistral Models
    "mistral-7b-instruct": "Mistral 7B Instruct",
    "mistral-7b-instruct-v0.1": "Mistral 7B Instruct v0.1",
    "mistral-7b-instruct-v0.3": "Mistral 7B Instruct v0.3",
    "mixtral-8x7b-instruct": "Mixtral 8x7B Instruct",
    "mixtral-8x22b-instruct": "Mixtral 8x22B Instruct",
    "mistral-nemo": "Mistral Nemo",
    "mistral-large-2": "Mistral Large 2",
    "mistral-large-3": "Mistral Large 3",
    "ministral-3b": "Ministral 3B",
    "ministral-8b": "Ministral 8B",
    "ministral-3-3b": "Ministral 3 3B",
    "ministral-3-8b": "Ministral 3 8B",
    "ministral-3-14b": "Ministral 3 14B",
    "pixtral-12b": "Pixtral 12B",
    "mistral-small-3": "Mistral Small 3",
    "mistral-small-3.1-24b": "Mistral Small 3.1 24B",
    "mistral-small-3.2-24b": "Mistral Small 3.2 24B",
    "mistral-medium-3": "Mistral Medium 3",
    "codestral": "Codestral",
    "saba": "Saba",
    "devstral-small-1.1": "Devstral Small 1.1",
    "devstral-medium": "Devstral Medium",
    "devstral-2": "Devstral 2",
    # xAI Models
    "grok-2": "Grok 2",
    "grok-3-mini-beta": "Grok 3 Mini Beta",
    "grok-3-beta": "Grok 3 Beta",
    "grok-4": "Grok 4",
    "grok-4-fast": "Grok 4 Fast",
    "grok-code-fast-1": "Grok Code Fast 1",
    # Z.ai Models
    "glm-4-32b": "GLM 4 32B",
    "glm-4.5-air": "GLM 4.5 Air",
    "glm-4.5": "GLM 4.5",
    "glm-4.6": "GLM 4.6",
    "glm-4.7-flash": "GLM 4.7 Flash",
    "glm-5": "GLM 5",
    # AI21 Models
    "jamba-mini-1.7": "Jamba Mini 1.7",
    "jamba-large-1.7": "Jamba Large 1.7",
    # Amazon Models
    "nova-lite-1.0": "Nova Lite 1.0",
    "nova-micro-1.0": "Nova Micro 1.0",
    "nova-pro-1.0": "Nova Pro 1.0",
    "nova-premier-1.0": "Nova Premier 1.0",
    "nova-2-lite": "Nova 2 Lite",
    # Alibaba Cloud Models
    "qwen-2.5-7b": "Qwen 2.5 7B",
    "qwen-2.5-32b": "Qwen 2.5 32B",
    "qwen-2.5-72b": "Qwen 2.5 72B",
    "qwen-2.5-coder-32b": "Qwen 2.5 Coder 32B",
    "qwen-3-14b": "Qwen 3 14B",
    "qwen-3-32b": "Qwen 3 32B",
    "qwen-3-30b-a3b": "Qwen 3 30B A3B",
    "qwen-3-235b-a22b": "Qwen 3 235B A22B",
    "qwen-3-coder": "Qwen 3 Coder",
    "qwen3-coder-plus": "Qwen3 Coder Plus",
    "qwen3-max": "Qwen3 Max",
    "qwen-plus": "Qwen Plus",
    "qwen-max": "Qwen Max",
    "qwen-turbo": "Qwen Turbo",
    "qwq-32b": "QwQ 32B",
    "qwen-3-max-thinking": "Qwen 3 Max Thinking",
    "qwen-3-coder-next": "Qwen 3 Coder Next",
    "qwen-3.5-397b-a17b": "Qwen 3.5 397B A17B",
    "qwen-3.5-plus": "Qwen 3.5 Plus",
    # Cohere Models
    "command": "Command",
    "command-a": "Command A",
    "command-r": "Command R",
    "command-r7b": "Command R7B",
    "command-r-plus": "Command R+",
    # Dolphin Models
    "dolphin-2.9.2-mixtral-8x22b": "Dolphin 2.9.2 Mixtral 8x22B",
    # Inception Models
    "inception-mercury": "Inception Mercury",
    "mercury-2": "Mercury 2",
    # Inflection AI Models
    "inflection-3-pi": "Inflection 3 Pi",
    "inflection-3-productivity": "Inflection 3 Productivity",
    # Liquid Models
    "lfm-3b": "LFM 3B",
    "lfm-7b": "LFM 7B",
    "lfm2-2.6b": "LFM2 2.6B",
    "lfm2-8b": "LFM2 8B",
    # Magnum Models
    "magnum-v4-72b": "Magnum v4 72B",
    # Microsoft Models
    "phi-3-mini-instruct": "Phi-3 Mini Instruct",
    "phi-3.5-mini-128k-instruct": "Phi-3.5 Mini 128K Instruct",
    "phi-3-medium-instruct": "Phi-3 Medium Instruct",
    "phi-4": "Phi 4",
    "phi-4-reasoning-plus": "Phi 4 Reasoning Plus",
    "wizardlm-2-8x22b": "WizardLM-2 8x22B",
    # Midnight Rose Models
    "midnight-rose-70b": "Midnight Rose 70B",
    # MiniMax Models
    "minimax-01": "MiniMax-01",
    "minimax-m1": "MiniMax M1",
    "minimax-m2": "MiniMax M2",
    "minimax-m2.1": "MiniMax M2.1",
    "minimax-m2.5": "MiniMax M2.5",
    # MoonshotAI Models
    "kimi-k2": "Kimi K2",
    "kimi-k2-thinking": "Kimi K2 Thinking",
    # MythoMax Models
    "mythomax-13b": "MythoMax 13B",
    # Noromaid Models
    "noromaid-20b": "Noromaid 20B",
    # NousResearch Models
    "hermes-2-pro-llama-3-8b": "Hermes 2 Pro - Llama-3 8B",
    "hermes-2-mixtral-8x7b-dpo": "Hermes 2 Mixtral 8x7B DPO",
    "hermes-3-70b-instruct": "Hermes 3 70B Instruct",
    "hermes-3-405b-instruct": "Hermes 3 405B Instruct",
    # NVIDIA Models
    "nvidia-llama-3.1-nemotron-70b": "NVIDIA Llama 3.1 Nemotron 70B",
    # Perplexity Models
    "sonar": "Sonar",
    "sonar-reasoning": "Sonar Reasoning",
    "sonar-pro": "Sonar Pro",
    "sonar-reasoning-pro": "Sonar Reasoning Pro",
    "sonar-deep-research": "Sonar Deep Research",
    # Rocinante Models
    "rocinante-12b": "Rocinante 12B",
    "unslopnemo-v4.1": "UnslopNemo v4.1",
}


class AI4Chat(Provider):
    """
    A class to interact with the AI4Chat API with support for multiple AI models.
    """

    required_auth = False

    # Make models accessible as class attribute
    models = MODELS
    default_model = "gpt-5.2"

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
        system_prompt: str = "You are a helpful and informative AI assistant.",
        country: str = "Asia",
        user_id: str = "usersmjb2oaz7y",
        model: str = default_model,
    ) -> None:
        from typing import cast

        self.session = Session(timeout=timeout, proxies=cast(Any, proxies))
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = (
            "https://yw85opafq6.execute-api.us-east-1.amazonaws.com/default/boss_mode_15aug"
        )
        self.timeout = timeout
        self.last_response = {}
        self.country = country
        self.user_id = user_id

        # Validate and set model
        if model not in MODELS:
            raise ValueError(f"Invalid model '{model}'. Available models: {list(MODELS.keys())}")
        self.model = model
        self.model_name = MODELS[model]

        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "id-ID,id;q=0.9",
            "Origin": "https://www.ai4chat.co",
            "Priority": "u=1, i",
            "Referer": "https://www.ai4chat.co/",
            "Sec-CH-UA": '"Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge Simulate";v="131", "Lemur";v="131"',
            "Sec-CH-UA-Mobile": "?1",
            "Sec-CH-UA-Platform": '"Android"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        }
        self.__available_optimizers = tuple(
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
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

        self.system_prompt = system_prompt

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        country: Optional[str] = None,
        user_id: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Response:
        """
        Sends a prompt to the AI4Chat API and returns the response.
        If stream=True, yields small chunks of the response (simulated streaming).

        Args:
            prompt: The text prompt to send
            stream: Whether to stream the response
            raw: Return raw response
            optimizer: Optimizer to use
            conversationally: Apply optimizer conversationally
            country: Country parameter
            user_id: User ID parameter
            model: Model to use (overrides instance model)
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")
        country_param = country or self.country
        user_id_param = user_id or self.user_id
        model_param = model or self.model

        # Validate model if provided
        if model_param not in MODELS:
            raise ValueError(
                f"Invalid model '{model_param}'. Available models: {list(MODELS.keys())}"
            )
        model_name = MODELS[model_param]

        encoded_text = urllib.parse.quote(conversation_prompt)
        encoded_country = urllib.parse.quote(country_param)
        encoded_user_id = urllib.parse.quote(user_id_param)
        encoded_model = urllib.parse.quote(model_name)

        # Include model in the API request
        url = f"{self.api_endpoint}?text={encoded_text}&country={encoded_country}&user_id={encoded_user_id}&model={encoded_model}"
        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
        except RequestsError as e:
            raise Exception(f"Failed to generate response: {e}")
        if not response.ok:
            raise Exception(
                f"Failed to generate response: {response.status_code} - {response.reason}"
            )
        response_text = response.text
        if response_text.startswith('"'):
            response_text = response_text[1:]
        if response_text.endswith('"'):
            response_text = response_text[:-1]
        response_text = response_text.replace("\\n", "\n").replace("\\n\\n", "\n\n")
        self.last_response.update(dict(text=response_text))
        self.conversation.update_chat_history(prompt, response_text)
        if stream:
            # Simulate streaming by yielding fixed-size character chunks (e.g., 48 chars)
            buffer = response_text
            chunk_size = 48
            while buffer:
                chunk = buffer[:chunk_size]
                buffer = buffer[chunk_size:]
                if chunk.strip():
                    yield {"text": chunk}
        else:
            return self.last_response

    def get_message(self, response: Response) -> str:
        """
        Retrieves message only from response
        """
        if isinstance(response, str):
            return response.replace("\\n", "\n").replace("\\n\\n", "\n\n")
        if not isinstance(response, dict):
            return str(response)
        resp_dict = cast(Dict[str, Any], response)
        return cast(str, resp_dict["text"]).replace("\\n", "\n").replace("\\n\\n", "\n\n")


if __name__ == "__main__":
    from rich import print

    # List available models
    print("[bold cyan]Available Models:[/bold cyan]")
    for model_key, model_name in list(MODELS.items())[:10]:
        print(f"  - {model_key}: {model_name}")
    print(f"  ... and {len(MODELS) - 10} more models\n")

    # Example usage with different models
    print("[bold green]Testing with default model (gpt-5.2):[/bold green]")
    ai = AI4Chat(model="gpt-5.2")
    response = ai.chat("How many r in strawberrrry", stream=True)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for c in response:
            print(c, end="")
    else:
        print(response)

    print("\n\n[bold green]Testing with Claude Haiku 4.5:[/bold green]")
    ai_claude = AI4Chat(model="claude-haiku-4.5")
    response = ai_claude.chat("How many r in strawberrrry", stream=True)
    if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
        for c in response:
            print(c, end="")
    else:
        print(response)
