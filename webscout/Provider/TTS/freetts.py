##################################################################################
##  FreeTTS Provider                                                             ##
##################################################################################
import pathlib
import tempfile
import time
from typing import Any, Optional, Union, cast

import requests
from litprinter import ic

from webscout import exceptions
from webscout.litagent import LitAgent
from webscout.Provider.TTS.base import BaseTTSProvider


class FreeTTS(BaseTTSProvider):
    """
    Text-to-speech provider using the FreeTTS.ru API.

    Features:
    - Multiple languages (Russian, English, Ukrainian, etc.)
    - High-quality neural voices
    - Supports long texts via polling
    """
    required_auth = False

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://freetts.ru",
        "Referer": "https://freetts.ru/",
        "User-Agent": LitAgent().random()
    }

    # Supported formats
    SUPPORTED_FORMATS = ["mp3"]

    def __init__(self, lang="ru-RU", timeout: int = 30, proxies: Optional[dict] = None):
        """
        Initialize the FreeTTS TTS client.

        Args:
            lang (str): Language code for voice filtering
            timeout (int): Request timeout in seconds
            proxies (dict): Proxy configuration
        """
        super().__init__()
        self.lang = lang
        self.base_url = "https://freetts.ru"
        self.api_url = f"{self.base_url}/api/synthesis"
        self.list_url = f"{self.base_url}/api/list"
        self.history_url = f"{self.base_url}/api/history"

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.timeout = timeout

        self.voices = {}
        self.load_voices()
        # Set default voice to first available for requested lang
        self.default_voice = self._get_default_voice()

    def load_voices(self):
        """Load voice data from the API."""
        try:
            response = self.session.get(self.list_url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    voices_list = data.get("data", {}).get("voices", [])
                    for voice in voices_list:
                        v_id = voice.get("id")
                        v_lang = voice.get("lang")
                        v_name = voice.get("name")
                        if v_id:
                            self.voices[v_id] = {
                                "lang": v_lang,
                                "name": v_name,
                                "sex": voice.get("sex")
                            }
                            if v_id not in self.SUPPORTED_VOICES:
                                self.SUPPORTED_VOICES.append(v_id)
        except Exception as e:
            ic.configureOutput(prefix='WARNING| ')
            ic(f"Error loading FreeTTS voices: {e}")

    def _get_default_voice(self):
        for v_id, info in self.voices.items():
            if info["lang"] == self.lang:
                return v_id
        return next(iter(self.voices.keys())) if self.voices else None

    def get_available_voices(self):
        """Return all available voices for the current language."""
        return [v_id for v_id, info in self.voices.items() if info["lang"] == self.lang]

    def tts(
        self,
        text: str,
        voice: Optional[str] = None,
        verbose: bool = False,
        **kwargs
    ) -> str:
        """
        Convert text to speech.
        """
        response_format = kwargs.get("response_format", "mp3")
        if not text:
            raise ValueError("Input text must be a non-empty string")

        voice = voice or self.default_voice
        if not voice:
            raise ValueError("No voices available")

        payload = {
            "text": text,
            "voiceid": voice,
            "ext": response_format
        }

        try:
            # Step 1: Start synthesis
            if verbose:
                ic.configureOutput(prefix='DEBUG| ')
                ic(f"FreeTTS: Starting synthesis for voice {voice}")

            response = self.session.post(self.api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            # Step 2: Poll for completion
            max_polls = 20
            poll_interval = 2

            for i in range(max_polls):
                poll_resp = self.session.get(self.api_url, timeout=self.timeout)
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()

                if poll_data.get("status") == 200 or poll_data.get("message") == "Обработка: 100%":
                    if verbose:
                        ic.configureOutput(prefix='DEBUG| ')
                        ic("FreeTTS: Synthesis completed")
                    break

                if verbose:
                    ic.configureOutput(prefix='DEBUG| ')
                    ic(f"FreeTTS: {poll_data.get('message', 'Processing...')}")

                time.sleep(poll_interval)
            else:
                raise exceptions.FailedToGenerateResponseError("FreeTTS synthesis timed out")

            # Step 3: Get result from history
            hist_resp = self.session.get(self.history_url, timeout=self.timeout)
            hist_resp.raise_for_status()
            hist_data = hist_resp.json()

            if hist_data.get("status") == "success":
                history = hist_data.get("data", [])
                if history:
                    # Find matching item in history
                    # For simplicity, take the first one as it's the latest
                    audio_url = history[0].get("url")
                    if audio_url:
                        if not audio_url.startswith("http"):
                            audio_url = self.base_url + audio_url

                        # Download the file
                        audio_file_resp = self.session.get(audio_url, timeout=self.timeout)
                        audio_file_resp.raise_for_status()

                        # Save to temp file
                        temp_file = tempfile.NamedTemporaryFile(suffix=f".{response_format}", dir=self.temp_dir, delete=False)
                        temp_file.close()
                        filename = pathlib.Path(temp_file.name)
                        with open(filename, "wb") as f:
                            f.write(audio_file_resp.content)

                        if verbose:
                            ic.configureOutput(prefix='DEBUG| ')
                            ic(f"FreeTTS: Audio saved to {filename}")
                        return str(filename)

            raise exceptions.FailedToGenerateResponseError("Failed to retrieve audio URL from history")

        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"FreeTTS failed: {e}")

    def create_speech(
        self,
        input_text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: Optional[str] = None,
        instructions: Optional[str] = None,
        verbose: bool = False,
        **kwargs: Any
    ) -> str:
        return self.tts(
            text=input_text,
            model=model,
            voice=voice,
            response_format=response_format or "mp3",
            instructions=instructions,
            verbose=verbose
        )

if __name__ == "__main__":
    tts = FreeTTS()
    try:
        path = tts.tts("Привет, это проверка FreeTTS.", verbose=True)
        print(f"Saved to: {path}")
    except Exception as e:
        print(f"Error: {e}")
