"""
TTS.ai Provider - Text-to-speech using TTS.ai free API.
https://tts.ai/text-to-speech/

Free tier models with no authentication required.
"""

import pathlib
import tempfile
import time
from typing import Any, Optional

from curl_cffi import CurlError, requests
from litprinter import ic

from webscout import exceptions
from webscout.litagent import LitAgent

try:
    from . import utils
    from .base import BaseTTSProvider
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from webscout.Provider.TTS import utils
    from webscout.Provider.TTS.base import BaseTTSProvider


class TTSAI(BaseTTSProvider):
    """
    TTS.ai provider.

    Uses the free TTS.ai API which doesn't require authentication.
    Supports multiple models and voices.

    Free tier models:
    - piper: 35 voices
    - vits: 10 voices
    - melotts: 7 voices
    - kitten-tts: 8 voices
    - kokoro: 26 voices
    - outetts: 1 voice
    - pocket-tts: 10 voices
    - ming-omni-tts: 2 voices
    """

    required_auth = False

    # Request headers
    headers: dict[str, str] = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://tts.ai",
        "referer": "https://tts.ai/text-to-speech/",
        "user-agent": LitAgent().random(),
    }

    # Supported models (free tier)
    SUPPORTED_MODELS = [
        "piper",
        "vits",
        "melotts",
        "kitten-tts",
        "kokoro",
        "outetts",
        "pocket-tts",
        "ming-omni-tts",
    ]

    # Default voices by model (sample)
    DEFAULT_VOICES = {
        "piper": "en_GB-alan-medium",
        "vits": "css10_nl",
        "melotts": "EN-BR",
        "kitten-tts": "bella",
        "kokoro": "am_adam",
        "outetts": "en-female-1-neutral",
        "pocket-tts": "alba",
        "ming-omni-tts": "default",
    }

    # Supported formats
    SUPPORTED_FORMATS = ["wav", "mp3"]

    def __init__(self, timeout: int = 120, **kwargs):
        """
        Initialize TTS.ai provider.

        Args:
            timeout (int): Request timeout in seconds
            **kwargs: Additional configuration
        """
        super().__init__()
        self.api_url = "https://tts.ai/api/v1/tts"
        self.voices_url = "https://tts.ai/api/v1/voices"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.timeout = timeout
        self.default_voice = "en_GB-alan-medium"

    def get_available_voices(self, model: Optional[str] = None) -> list:
        """
        Get available voices, optionally filtered by model.

        Args:
            model (str): Optional model name to filter voices

        Returns:
            list: List of voice dictionaries
        """
        response = self.session.get(self.voices_url, timeout=30)
        response.raise_for_status()
        voices = response.json()["voices"]

        if model:
            voices = [v for v in voices if v["model_name"] == model]
        return voices

    def get_available_models(self) -> dict:
        """
        Get available models with voice counts.

        Returns:
            dict: Dictionary mapping model names to voice counts
        """
        voices = self.get_available_voices()
        model_counts = {}
        for v in voices:
            model = v["model_name"]
            model_counts[model] = model_counts.get(model, 0) + 1
        return model_counts

    def tts(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        response_format: Optional[str] = None,
        verbose: bool = False,
        **kwargs,
    ) -> str:
        """
        Convert text to speech using TTS.ai API.

        Args:
            text (str): The text to convert to speech
            voice (str): The voice to use
            model (str): The TTS model to use
            response_format (str): Output format (wav, mp3)
            verbose (bool): Whether to print debug information
            **kwargs: Additional parameters

        Returns:
            str: Path to the generated audio file
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Set defaults
        voice = voice or self.default_voice
        model = model or "piper"
        response_format = response_format or "wav"

        if not text:
            raise ValueError("Input text must be a non-empty string")

        # Map format
        response_format = response_format.lower().replace(".", "")

        if verbose:
            ic.configureOutput(prefix="DEBUG| ")
            ic(f"TTS.ai: Generating speech for {len(text)} chars")
            ic(f"Model: {model}, Voice: {voice}, Format: {response_format}")

        # Create temporary file
        file_extension = f".{response_format}"
        filename = pathlib.Path(
            tempfile.NamedTemporaryFile(suffix=file_extension, dir=self.temp_dir, delete=False).name
        )

        # Split text into sentences
        sentences = utils.split_sentences(text)

        def generate_audio_for_chunk(part_text: str, part_number: int):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    payload = {
                        "text": part_text,
                        "model": model,
                        "voice": voice,
                    }

                    response = self.session.post(self.api_url, json=payload, timeout=self.timeout)
                    response.raise_for_status()
                    result = response.json()

                    # Check for errors
                    if "error" in result:
                        raise exceptions.FailedToGenerateResponseError(
                            f"TTS.ai error: {result.get('message', result['error'])}"
                        )

                    # Get job status
                    status = result.get("status", "queued")

                    # Poll for completion if still queued
                    if status == "queued":
                        max_polls = 30
                        poll_interval = 2
                        for _ in range(max_polls):
                            time.sleep(poll_interval)

                            check_resp = self.session.post(
                                self.api_url, json=payload, timeout=self.timeout
                            )
                            check_resp.raise_for_status()
                            check_result = check_resp.json()

                            if check_result.get("status") == "completed":
                                result = check_result
                                break
                            elif check_result.get("error"):
                                raise exceptions.FailedToGenerateResponseError(
                                    f"TTS error: {check_result.get('error')}"
                                )

                    # Get audio URL
                    audio_url = result.get("audio_url")
                    if not audio_url:
                        audio_url = result.get("url")
                        if not audio_url:
                            share_uuid = result.get("share_uuid")
                            if share_uuid:
                                audio_url = f"https://tts.ai/share/{share_uuid}"

                    if not audio_url:
                        raise exceptions.FailedToGenerateResponseError(
                            f"No audio URL in response: {result}"
                        )

                    # Download audio
                    audio_resp = self.session.get(audio_url, timeout=self.timeout)
                    audio_resp.raise_for_status()

                    if verbose:
                        ic.configureOutput(prefix="DEBUG| ")
                        ic(f"Chunk {part_number} processed successfully")

                    return part_number, audio_resp.content

                except CurlError as e:
                    if verbose:
                        ic.configureOutput(prefix="WARNING| ")
                        ic(f"CurlError: {e}. Retrying {attempt + 1}/{max_retries}")
                    time.sleep(1)
                except Exception as e:
                    if verbose:
                        ic.configureOutput(prefix="WARNING| ")
                        ic(f"Error: {e}. Retrying {attempt + 1}/{max_retries}")
                    time.sleep(1)

            raise exceptions.FailedToGenerateResponseError(
                f"Failed to generate audio for chunk {part_number}"
            )

        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(generate_audio_for_chunk, sentence.strip(), i): i
                    for i, sentence in enumerate(sentences)
                }

                audio_chunks = {}
                for future in as_completed(futures):
                    part_num, data = future.result()
                    audio_chunks[part_num] = data

                # Combine audio chunks
                with open(filename, "wb") as f:
                    for i in sorted(audio_chunks.keys()):
                        f.write(audio_chunks[i])

                if verbose:
                    ic.configureOutput(prefix="INFO| ")
                    ic(f"Audio saved to {filename}")

                return str(filename)

        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"TTS.ai generation failed: {e}")

    def create_speech(
        self,
        input_text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: Optional[str] = None,
        instructions: Optional[str] = None,
        verbose: bool = False,
    ) -> str:
        """
        Create speech from input text (OpenAI-compatible interface).

        Args:
            input_text (str): The text to convert to speech
            model (str): The TTS model to use
            voice (str): The voice to use
            response_format (str): Audio format
            instructions (str): Voice instructions (ignored)
            verbose (bool): Print debug information

        Returns:
            str: Path to the generated audio file
        """
        return self.tts(
            text=input_text,
            model=model or "piper",
            voice=voice or self.default_voice,
            response_format=response_format or "wav",
            verbose=verbose,
        )


if __name__ == "__main__":
    client = TTSAI()

    print("Available models:", client.models.list())

    voices = client.get_available_voices("piper")[:5]
    print("\nSample piper voices:", [v["voice_id"] for v in voices])

    print("\nGenerating speech...")
    result = client.speech(
        text="Hello world, this is a test of text to speech.",
        model="piper",
        voice="en_GB-alan-medium",
    )
    print("Audio file:", result)
