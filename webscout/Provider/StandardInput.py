from os import system
import requests
import json
import uuid
import re
from datetime import datetime
from typing import Any, Dict, Optional, Union, Generator
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent

class StandardInputAI(Provider):
    """
    A class to interact with the Standard Input chat API.
    """

    AVAILABLE_MODELS = {
        "standard-quick": "quick",
        "standard-reasoning": "quick",  # Same model but with reasoning enabled
    }

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "standard-quick",
        chat_id: str = None,
        user_id: str = None,
        browser: str = "chrome",
        system_prompt: str = "You are a helpful assistant.",
        enable_reasoning: bool = False,
    ):
        """
        Initializes the Standard Input API client.

        Args:
            is_conversation (bool): Whether to maintain conversation history.
            max_tokens (int): Maximum number of tokens to generate.
            timeout (int): Request timeout in seconds.
            intro (str): Introduction text for the conversation.
            filepath (str): Path to save conversation history.
            update_file (bool): Whether to update the conversation history file.
            proxies (dict): Proxy configuration for requests.
            history_offset (int): Maximum history length in characters.
            act (str): Persona for the AI to adopt.
            model (str): Model to use, must be one of AVAILABLE_MODELS.
            chat_id (str): Unique identifier for the chat session.
            user_id (str): Unique identifier for the user.
            browser (str): Browser to emulate in requests.
            system_prompt (str): System prompt for the AI.
            enable_reasoning (bool): Whether to enable reasoning feature.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.url = "https://chat.standard-input.com/api/chat"

        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()
        # Use fingerprinting to create a consistent browser identity
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.system_prompt = system_prompt

        # Use the fingerprint for headers
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": self.fingerprint["accept_language"],
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://chat.standard-input.com",
            "referer": "https://chat.standard-input.com/",
            "sec-ch-ua": self.fingerprint["sec_ch_ua"] or '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": f'"{self.fingerprint["platform"]}"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": self.fingerprint["user_agent"],
        }

        # Default cookies - these should be updated for production use
        self.cookies = {
            "auth-chat": '''%7B%22user%22%3A%7B%22id%22%3A%2243a26ebd-7691-4a5a-8321-12aff017af86%22%2C%22email%22%3A%22iu511inmev%40illubd.com%22%2C%22accountId%22%3A%22057d78c9-06db-48eb-aeaa-0efdbaeb9446%22%2C%22provider%22%3A%22password%22%7D%2C%22tokens%22%3A%7B%22access%22%3A%22eyJhbGciOiJFUzI1NiIsImtpZCI6Ijg1NDhmZWY1LTk5MjYtNDk2Yi1hMjI2LTQ5OTExYjllYzU2NSIsInR5cCI6IkpXVCJ9.eyJtb2RlIjoiYWNjZXNzIiwidHlwZSI6InVzZXIiLCJwcm9wZXJ0aWVzIjp7ImlkIjoiNDNhMjZlYmQtNzY5MS00YTVhLTgzMzEtMTJhZmYwMTdhZjg2IiwiZW1haWwiOiJpdTUxMWlubWV2QGlsbHViZC5jb20iLCJhY2NvdW50SWQiOiIwNTdkNzhjOS0wNmRiLTQ4ZWItYWVhYS0wZWZkYmFlYjk0NDYiLCJwcm92aWRlciI6InBhc3N3b3JkIn0sImF1ZCI6InN0YW5kYXJkLWlucHV0LWlvcyIsImlzcyI6Imh0dHBzOi8vYXV0aC5zdGFuZGFyZC1pbnB1dC5jb20iLCJzdWIiOiJ1c2VyOjRmYWMzMTllZjA4MDRiZmMiLCJleHAiOjE3NDU0MDU5MDN9.d3VsEq-UCNsQWkiPlTVw7caS0wTXfCYe6yeFLeb4Ce6ZYTIFFn685SF-aKvLOxaYaq7Pyk4D2qr24riPVhxUWQ%22%2C%22refresh%22%3A%22user%3A4fac319ef0804bfc%3A3a757177-5507-4a36-9356-492f5ed06105%22%7D%7D''',
            "auth": '''%7B%22user%22%3A%7B%22id%22%3A%22c51e291f-8f44-439d-a38b-9ea147581a13%22%2C%22email%22%3A%22r6cigexlsb%40mrotzis.com%22%2C%22accountId%22%3A%22599fd4ce-04a2-40f6-a78f-d33d0059b77f%22%2C%22provider%22%3A%22password%22%7D%2C%22tokens%22%3A%7B%22access%22%3A%22eyJhbGciOiJFUzI1NiIsImtpZCI6Ijg1NDhmZWY1LTk5MjYtNDk2Yi1hMjI2LTQ5OTExYjllYzU2NSIsInR5cCI6IkpXVCJ9.eyJtb2RlIjoiYWNjZXNzIiwidHlwZSI6InVzZXIiLCJwcm9wZXJ0aWVzIjp7ImlkIjoiYzUxZTI5MWYtOGY0NC00MzlkLWEzOGItOWVhMTQ3NTgxYTEzIiwiZW1haWwiOiJyNmNpZ2V4bHNiQG1yb3R6aXMuY29tIiwiYWNjb3VudElkIjoiNTk5ZmQ0Y2UtMDRhMi00MGY2LWE3OGYtZDMzZDAwNTliNzdmIiwicHJvdmlkZXIiOiJwYXNzd29yZCJ9LCJhdWQiOiJzdGFuZGFyZC1pbnB1dC1pb3MiLCJpc3MiOiJodHRwczovL2F1dGguc3RhbmRhcmQtaW5wdXQuY29tIiwic3ViIjoidXNlcjo4Y2FmMjRkYzUxNDc4MmNkIiwiZXhwIjoxNzQ2NzI0MTU3fQ.a3970nBJkd8JoU-khRA2JlRMuYeJ7378QS4ZL446kOkDi35uTwuC4qGrWH9efk9GkFaVcWPtYeOJjRb7f2SeJA%22%2C%22refresh%22%3A%22user%3A8caf24dc514782cd%3A14e24386-8443-4df0-ae25-234ad59218ef%22%7D%7D''',
            "sidebar:state": "true",
            "ph_phc_f3wUUyCfmKlKtkc2pfT7OsdcW2mBEVGN2A87yEYbG3c_posthog": '''%7B%22distinct_id%22%3A%220195c7cc-ac8f-79ff-b901-e14a78fc2a67%22%2C%22%24sesid%22%3A%5B1744688627860%2C%220196377f-9f12-77e6-a9ea-0e9669423803%22%2C1744687832850%5D%2C%22%24initial_person_info%22%3A%7B%22r%22%3A%22%24direct%22%2C%22u%22%3A%22https%3A%2F%2Fstandard-input.com%2F%22%7D%7D'''
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.chat_id = chat_id or str(uuid.uuid4())
        self.user_id = user_id or f"user_{str(uuid.uuid4())[:8].upper()}"
        self.enable_reasoning = enable_reasoning

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or Conversation.intro
        )

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

    def refresh_identity(self, browser: str = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)

        # Update headers with new fingerprint
        self.headers.update({
            "Accept-Language": self.fingerprint["accept_language"],
            "Sec-CH-UA": self.fingerprint["sec_ch_ua"] or self.headers["sec-ch-ua"],
            "Sec-CH-UA-Platform": f'"{self.fingerprint["platform"]}"',
            "User-Agent": self.fingerprint["user_agent"],
        })

        # Update session headers
        for header, value in self.headers.items():
            self.session.headers[header] = value

        return self.fingerprint

    def ask(
        self,
        prompt: str,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        # Prepare the messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": conversation_prompt, "parts": [{"type": "text", "text": conversation_prompt}]}
        ]

        # Prepare the request payload
        payload = {
            "id": self.chat_id,
            "messages": messages,
            "modelId": self.AVAILABLE_MODELS[self.model],
            "enabledFeatures": ["reasoning"] if self.enable_reasoning or self.model == "standard-reasoning" else []
        }

        try:
            response = self.session.post(self.url, cookies=self.cookies, json=payload, stream=True, timeout=self.timeout)
            if response.status_code != 200:
                # Try to get response content for better error messages
                try:
                    error_content = response.text
                except:
                    error_content = "<could not read response content>"

                if response.status_code in [403, 429]:
                    print(f"Received status code {response.status_code}, refreshing identity...")
                    self.refresh_identity()
                    response = self.session.post(self.url, cookies=self.cookies, json=payload, stream=True, timeout=self.timeout)
                    if not response.ok:
                        raise exceptions.FailedToGenerateResponseError(
                            f"Failed to generate response after identity refresh - ({response.status_code}, {response.reason}) - {error_content}"
                        )
                    print("Identity refreshed successfully.")
                else:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Request failed with status code {response.status_code}. Response: {error_content}"
                    )

            full_response = ""
            debug_lines = []

            # Process the streaming response
            for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                if line:
                    try:
                        line_str = line
                        debug_lines.append(line_str)

                        # Extract content from the response
                        match = re.search(r'0:"(.*?)"', line_str)
                        if match:
                            content = match.group(1)
                            full_response += content
                            continue
                    except: pass

            self.last_response = {"text": full_response}
            self.conversation.update_chat_history(prompt, full_response)
            return {"text": full_response}
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")

    def chat(
        self,
        prompt: str,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        return self.get_message(
            self.ask(
                prompt, optimizer=optimizer, conversationally=conversationally
            )
        )

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')

if __name__ == "__main__":
    print("-" * 100)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 100)

    test_prompt = "Say 'Hello' in one word"

    # Test each model
    for model in StandardInputAI.AVAILABLE_MODELS:
        print(f"\rTesting {model}...", end="")

        try:
            test_ai = StandardInputAI(model=model, timeout=120)  # Increased timeout
            response = test_ai.chat(test_prompt)

            if response and len(response.strip()) > 0:
                status = "✓"
                # Clean and truncate response
                clean_text = response.strip().encode('utf-8', errors='ignore').decode('utf-8')
                display_text = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"

            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            error_msg = str(e)
            # Truncate very long error messages
            if len(error_msg) > 100:
                error_msg = error_msg[:97] + "..."
            print(f"\r{model:<50} {'✗':<10} Error: {error_msg}")
