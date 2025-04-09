from os import path
from json import load, dumps
import warnings
from typing import Union, Any, Dict

# Import internal modules and dependencies
from ..AIutel import Optimizers, Conversation, AwesomePrompts, sanitize_stream
from ..AIbase import Provider, AsyncProvider
from ..Bard import Chatbot, Model

warnings.simplefilter("ignore", category=UserWarning)

# Define model aliases for easy usage
MODEL_ALIASES: Dict[str, Model] = {
    "unspecified": Model.UNSPECIFIED,
    "gemini-2.0-flash": Model.G_2_0_FLASH,
    "gemini-2.0-flash-thinking": Model.G_2_0_FLASH_THINKING,
    "gemini-2.5-pro": Model.G_2_5_PRO,
    "gemini-2.0-exp-advanced": Model.G_2_0_EXP_ADVANCED,
    "gemini-2.5-exp-advanced": Model.G_2_5_EXP_ADVANCED,
    # Add shorter aliases for convenience
    "flash": Model.G_2_0_FLASH,
    "thinking": Model.G_2_0_FLASH_THINKING,
    "pro": Model.G_2_5_PRO,
    "advanced": Model.G_2_0_EXP_ADVANCED,
    "advanced-2.5": Model.G_2_5_EXP_ADVANCED,
}

# List of available models (friendly names)
AVAILABLE_MODELS = list(MODEL_ALIASES.keys())

class GEMINI(Provider):
    def __init__(
        self,
        cookie_file: str,
        model: str = "flash",  # Accepts either a Model enum or a str alias.
        proxy: dict = {},
        timeout: int = 30,
    ):
        """
        Initializes GEMINI with model support.

        Args:
            cookie_file (str): Path to the cookies JSON file.
            model (Model or str): Selected model for the session. Can be a Model enum
                or a string alias. Available aliases: flash, flash-exp, thinking, thinking-with-apps,
                exp-advanced, 2.5-exp-advanced, 2.5-pro, 1.5-flash, 1.5-pro, 1.5-pro-research.
            proxy (dict, optional): HTTP request proxy. Defaults to {}.
            timeout (int, optional): HTTP request timeout in seconds. Defaults to 30.
        """
        self.conversation = Conversation(False)

        # Ensure cookie_file existence.
        if not isinstance(cookie_file, str):
            raise TypeError(f"cookie_file should be of type str, not '{type(cookie_file)}'")
        if not path.isfile(cookie_file):
            raise Exception(f"{cookie_file} is not a valid file path")

        # If model is provided as alias (str), convert to Model enum.
        if isinstance(model, str):
            alias = model.lower()
            if alias in MODEL_ALIASES:
                selected_model = MODEL_ALIASES[alias]
            else:
                raise Exception(f"Unknown model alias: '{model}'. Available aliases: {', '.join(AVAILABLE_MODELS)}")
        elif isinstance(model, Model):
            selected_model = model
        else:
            raise TypeError("model must be a string alias or an instance of Model")

        # Initialize the Chatbot session using the cookie file.
        self.session = Chatbot(cookie_file, proxy, timeout, selected_model)
        self.last_response = {}
        self.__available_optimizers = (
            method for method in dir(Optimizers) if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        # Store cookies from Chatbot for later use (e.g. image generation)
        self.session_auth1 = self.session.secure_1psid
        self.session_auth2 = self.session.secure_1psidts

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with AI.

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name (e.g., 'code', 'shell_command'). Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.

        Returns:
            dict: Response generated by the underlying Chatbot.
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {', '.join(self.__available_optimizers)}")

        def for_stream():
            response = self.session.ask(prompt)
            self.last_response.update(response)
            self.conversation.update_chat_history(prompt, self.get_message(self.last_response))
            yield dumps(response) if raw else response

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """Generate response text.

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.

        Returns:
            str: Response generated.
        """
        def for_stream():
            for response in self.ask(prompt, True, optimizer=optimizer, conversationally=conversationally):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(self.ask(prompt, False, optimizer=optimizer, conversationally=conversationally))

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message content from the response.

        Args:
            response (dict): Response generated by `self.ask`.

        Returns:
            str: Extracted message content.
        """
        if not isinstance(response, dict):
            raise TypeError("Response should be of type dict")
        return response["content"]

    def reset(self):
        """Reset the current conversation."""
        self.session.async_chatbot.conversation_id = ""
        self.session.async_chatbot.response_id = ""
        self.session.async_chatbot.choice_id = ""
