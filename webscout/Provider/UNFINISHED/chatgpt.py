import json
import random
import uuid
import time
import base64
import hashlib
import requests
from datetime import datetime, timedelta

class ChatGPTReversed:
    csrf_token = None
    initialized = False
    AVAILABLE_MODELS = ["auto", "gpt-4o-mini", "gpt-4o",]

    def __init__(self, model="auto"):
        if ChatGPTReversed.initialized:
            raise Exception("ChatGPTReversed has already been initialized.")

        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.model = model
        self.initialize()

    def initialize(self):
        ChatGPTReversed.initialized = True

    def random_ip(self):
        """Generate a random IP address."""
        return ".".join(str(random.randint(0, 255)) for _ in range(4))

    def random_uuid(self):
        """Generate a random UUID."""
        return str(uuid.uuid4())

    def random_float(self, min_val, max_val):
        """Generate a random float between min and max."""
        return round(random.uniform(min_val, max_val), 4)

    def simulate_bypass_headers(self, accept, spoof_address=False, pre_oai_uuid=None):
        """Simulate browser headers to bypass detection."""
        simulated = {
            "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "platform": "Windows",
            "mobile": "?0",
            "ua": 'Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132'
        }

        ip = self.random_ip()
        uuid_val = pre_oai_uuid or self.random_uuid()

        headers = {
            "accept": accept,
            "Content-Type": "application/json",
            "cache-control": "no-cache",
            "Referer": "https://chatgpt.com/",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "oai-device-id": uuid_val,
            "User-Agent": simulated["agent"],
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": f"{simulated['ua']}",
            "sec-ch-ua-mobile": simulated["mobile"],
            "sec-ch-ua-platform": f"{simulated['platform']}",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
        }

        if spoof_address:
            headers.update({
                "X-Forwarded-For": ip,
                "X-Originating-IP": ip,
                "X-Remote-IP": ip,
                "X-Remote-Addr": ip,
                "X-Host": ip,
                "X-Forwarded-Host": ip
            })

        return headers

    def solve_sentinel_challenge(self, seed, difficulty):
        """Solve the sentinel challenge for authentication."""
        cores = [8, 12, 16, 24]
        screens = [3000, 4000, 6000]
        core = random.choice(cores)
        screen = random.choice(screens)

        # Adjust time to match expected timezone
        now = datetime.now() - timedelta(hours=8)
        parse_time = now.strftime("%a, %d %b %Y %H:%M:%S GMT+0100 (Central European Time)")

        config = [core + screen, parse_time, 4294705152, 0,
                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"]

        diff_len = len(difficulty) // 2

        for i in range(100000):
            config[3] = i
            json_data = json.dumps(config)
            base = base64.b64encode(json_data.encode()).decode()
            hash_value = hashlib.sha3_512((seed + base).encode()).hexdigest()

            if hash_value[:diff_len] <= difficulty:
                result = "gAAAAAB" + base
                return result

        # Fallback
        fallback_base = base64.b64encode(seed.encode()).decode()
        return "gAAAAABwQ8Lk5FbGpA2NcR9dShT6gYjU7VxZ4D" + fallback_base

    def generate_fake_sentinel_token(self):
        """Generate a fake sentinel token for initial authentication."""
        prefix = "gAAAAAC"
        config = [
            random.randint(3000, 6000),
            datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT+0100 (Central European Time)"),
            4294705152, 0,
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "de", "de", 401, "mediaSession", "location", "scrollX",
            self.random_float(1000, 5000),
            str(uuid.uuid4()), "", 12, int(time.time() * 1000)
        ]

        base64_str = base64.b64encode(json.dumps(config).encode()).decode()
        return prefix + base64_str

    def parse_response(self, input_text):
        """Parse the response from ChatGPT.

        Args:
            input_text (str): The response text from ChatGPT.

        Returns:
            The complete response as a string.
        """
        parts = [part.strip() for part in input_text.split("\n") if part.strip()]

        for part in parts:
            try:
                if part.startswith("data: "):
                    json_data = json.loads(part[6:])
                    if (json_data.get("message") and
                        json_data["message"].get("status") == "finished_successfully" and
                        json_data["message"].get("metadata", {}).get("is_complete")):
                        return json_data["message"]["content"]["parts"][0]
            except:
                pass

        return input_text # Return raw text if parsing fails or no complete message found

    def rotate_session_data(self):
        """Rotate session data to maintain fresh authentication."""
        uuid_val = self.random_uuid()
        csrf_token = self.get_csrf_token(uuid_val)
        sentinel_token = self.get_sentinel_token(uuid_val, csrf_token)

        ChatGPTReversed.csrf_token = csrf_token

        return {
            "uuid": uuid_val,
            "csrf": csrf_token,
            "sentinel": sentinel_token
        }

    def get_csrf_token(self, uuid_val):
        """Get CSRF token for authentication."""
        if ChatGPTReversed.csrf_token is not None:
            return ChatGPTReversed.csrf_token

        headers = self.simulate_bypass_headers(
            accept="application/json",
            spoof_address=True,
            pre_oai_uuid=uuid_val
        )

        response = requests.get(
            "https://chatgpt.com/api/auth/csrf",
            headers=headers
        )

        data = response.json()
        if "csrfToken" not in data:
            raise Exception("Failed to fetch required CSRF token")

        return data["csrfToken"]

    def get_sentinel_token(self, uuid_val, csrf):
        """Get sentinel token for authentication."""
        headers = self.simulate_bypass_headers(
            accept="application/json",
            spoof_address=True,
            pre_oai_uuid=uuid_val
        )

        test = self.generate_fake_sentinel_token()

        response = requests.post(
            "https://chatgpt.com/backend-anon/sentinel/chat-requirements",
            json={"p": test},
            headers={
                **headers,
                "Cookie": f"__Host-next-auth.csrf-token={csrf}; oai-did={uuid_val}; oai-nav-state=1;"
            }
        )

        data = response.json()
        if "token" not in data or "proofofwork" not in data:
            raise Exception("Failed to fetch required sentinel token")

        oai_sc = None
        for cookie in response.cookies:
            if cookie.name == "oai-sc":
                oai_sc = cookie.value
                break

        if not oai_sc:
            raise Exception("Failed to fetch required oai-sc token")

        challenge_token = self.solve_sentinel_challenge(
            data["proofofwork"]["seed"],
            data["proofofwork"]["difficulty"]
        )

        return {
            "token": data["token"],
            "proof": challenge_token,
            "oaiSc": oai_sc
        }

    def complete(self, message, model=None):
        """Complete a message using ChatGPT.

        Args:
            message (str): The message to send to ChatGPT.
            model (str, optional): The model to use. If None, uses the model specified during initialization.
                                   Defaults to None.

        Returns:
            The complete response as a string.
        """
        if not ChatGPTReversed.initialized:
            raise Exception("ChatGPTReversed has not been initialized. Please initialize the instance before calling this method.")

        # Use the provided model or fall back to the instance model
        selected_model = model if model else self.model

        # Validate the model
        if selected_model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {selected_model}. Choose from: {self.AVAILABLE_MODELS}")

        session_data = self.rotate_session_data()

        headers = self.simulate_bypass_headers(
            accept="plain/text", # Changed accept header as we expect full response now
            spoof_address=True,
            pre_oai_uuid=session_data["uuid"]
        )

        headers.update({
            "Cookie": f"__Host-next-auth.csrf-token={session_data['csrf']}; oai-did={session_data['uuid']}; oai-nav-state=1; oai-sc={session_data['sentinel']['oaiSc']};",
            "openai-sentinel-chat-requirements-token": session_data["sentinel"]["token"],
            "openai-sentinel-proof-token": session_data["sentinel"]["proof"]
        })

        payload = {
            "action": "next",
            "messages": [{
                "id": self.random_uuid(),
                "author": {
                    "role": "user"
                },
                "content": {
                    "content_type": "text",
                    "parts": [message]
                },
                "metadata": {}
            }],
            "parent_message_id": self.random_uuid(),
            "model": selected_model,  # Use the selected model
            "timezone_offset_min": -120,
            "suggestions": [],
            "history_and_training_disabled": False,
            "conversation_mode": {
                "kind": "primary_assistant",
                "plugin_ids": None # Ensure web search is not used
            },
            "force_paragen": False,
            "force_paragen_model_slug": "",
            "force_nulligen": False,
            "force_rate_limit": False,
            "reset_rate_limits": False,
            "websocket_request_id": self.random_uuid(),
            "force_use_sse": True # Keep SSE for receiving the full response
        }

        response = requests.post(
            "https://chatgpt.com/backend-anon/conversation",
            json=payload,
            headers=headers
        )

        if response.status_code != 200:
            raise Exception(f"HTTP error! status: {response.status_code}")

        return self.parse_response(response.text)



# Example usage when running the file directly
if __name__ == "__main__":
    ai = ChatGPTReversed(model="gpt-4o")
    response = ai.complete("Hello, how are you?")
    print(response)
