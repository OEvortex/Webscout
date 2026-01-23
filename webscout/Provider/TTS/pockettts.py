"""
Pocket TTS Provider - Text-to-speech using Kyutai's official Pocket TTS API.

This provider interfaces with the official Kyutai Pocket TTS API endpoint,
a CPU-optimized text-to-speech service using the Kyutai Pocket TTS model.

Features:
- 6 preset voices: alba, javert, azelma, eponine, fantine, jean
- Fast, lightweight API with low latency
- Multiple audio format support
"""

import pathlib
import tempfile
from typing import Any, Optional

import requests
from litprinter import ic

from webscout import exceptions
from webscout.litagent import LitAgent
from webscout.Provider.TTS.base import BaseTTSProvider


class PocketTTS(BaseTTSProvider):
    """
    Pocket TTS provider using the official Kyutai Pocket TTS API.

    Provides text-to-speech conversion with support for multiple voices
    from the official Kyutai Pocket TTS service.

    Attributes:
        SUPPORTED_VOICES: List of available preset voices
        SUPPORTED_FORMATS: List of supported audio formats
    """

    required_auth = False

    # Supported voices
    SUPPORTED_VOICES = [
        "alba",
        "javert",
        "azelma",
        "eponine",
        "fantine",
        "jean",
    ]

    # Supported formats - Pocket TTS outputs WAV
    SUPPORTED_FORMATS = ["wav", "mp3", "aac", "opus"]

    def __init__(
        self,
        base_url: str = "https://kyutaipockettts6ylex2y4-kyutai-pocket-tts.functions.fnc.fr-par.scw.cloud",
        timeout: int = 30,
        proxies: Optional[dict] = None,
    ):
        """
        Initialize the Pocket TTS provider.

        Args:
            base_url (str): Base URL of the Kyutai Pocket TTS API.
                Defaults to the official API endpoint.
            timeout (int): Request timeout in seconds. Defaults to 30.
            proxies (dict, optional): Proxy configuration for requests.

        Raises:
            requests.RequestException: If unable to connect to the service.
        """
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/tts"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "User-Agent": LitAgent().random(),
            }
        )

        if proxies:
            self.session.proxies.update(proxies)

        # Set defaults
        self.default_voice = "alba"
        self.default_format = "wav"

    def tts(
        self,
        text: str,
        voice: Optional[str] = None,
        verbose: bool = False,
        **kwargs,
    ) -> str:
        """
        Convert text to speech using Pocket TTS API.

        Args:
            text (str): The text to convert to speech
            voice (str, optional): Voice to use. Defaults to 'alba'.
                Options: alba, javert, azelma, eponine, fantine, jean
            verbose (bool, optional): Print debug information. Defaults to False.
            **kwargs: Additional parameters (ignored for API compatibility)

        Returns:
            str: Path to the generated audio file

        Raises:
            ValueError: If text is empty or voice is invalid
            exceptions.FailedToGenerateResponseError: If generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Extract optional parameters from kwargs
        response_format = kwargs.get("response_format", self.default_format)

        # Use defaults
        voice = voice or self.default_voice

        # Validate voice
        if voice not in self.SUPPORTED_VOICES:
            raise ValueError(
                f"Voice '{voice}' not supported. Available voices: "
                f"{', '.join(self.SUPPORTED_VOICES)}"
            )

        try:
            if verbose:
                ic.configureOutput(prefix="DEBUG| ")
                ic(f"PocketTTS: Generating speech with voice={voice}")

            # Call the API directly with multipart form-data
            files = {
                "text": (None, text),
                "voice_url": (None, voice),
            }

            response = self.session.post(
                self.api_url,
                files=files,
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Save audio to temp file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f".{response_format}",
                dir=self.temp_dir,
                delete=False
            )
            temp_file.close()

            with open(temp_file.name, "wb") as f:
                f.write(response.content)

            if verbose:
                ic.configureOutput(prefix="DEBUG| ")
                ic(f"PocketTTS: Audio saved to {temp_file.name}")

            return temp_file.name

        except exceptions.FailedToGenerateResponseError:
            raise
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(
                f"PocketTTS generation failed: {e}"
            )

    def create_speech(
        self,
        input_text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: Optional[str] = None,
        instructions: Optional[str] = None,
        verbose: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Create speech from input text (OpenAI-compatible interface).

        Args:
            input_text (str): The text to convert to speech
            model (str, optional): Model name (ignored, for compatibility)
            voice (str, optional): Voice to use
            response_format (str, optional): Audio format
            instructions (str, optional): Voice instructions (ignored)
            verbose (bool, optional): Print debug information
            **kwargs: Additional arguments passed to tts()

        Returns:
            str: Path to the generated audio file
        """
        return self.tts(
            text=input_text,
            voice=voice,
            response_format=response_format or "wav",
            verbose=verbose,
            **kwargs,
        )


if __name__ == "__main__":
    # Test the provider
    import os

    print("Testing PocketTTS Provider...")
    print("=" * 60)

    # Initialize provider
    tts = PocketTTS()

    # Test 1: Basic generation with default voice
    print("\n[Test 1] Basic generation with default voice (alba)")
    try:
        audio_file = tts.tts(
            "Hello, this is a test of the Pocket TTS provider.",
            verbose=True,
        )
        print(f"✓ Audio generated: {audio_file}")
        print(f"  File size: {os.path.getsize(audio_file)} bytes")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 2: Generation with different voice
    print("\n[Test 2] Generation with different voice (javert)")
    try:
        audio_file = tts.tts(
            "The official Kyutai API provides excellent audio quality.",
            voice="javert",
            verbose=True,
        )
        print(f"✓ Audio generated: {audio_file}")
        print(f"  File size: {os.path.getsize(audio_file)} bytes")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 3: Error handling - invalid voice
    print("\n[Test 3] Error handling - invalid voice")
    try:
        audio_file = tts.tts(
            "This should fail.",
            voice="invalid_voice",
            verbose=True,
        )
        print("✗ Should have raised an error")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # Test 4: Using OpenAI-compatible interface
    print("\n[Test 4] OpenAI-compatible interface")
    try:
        audio_file = tts.create_speech(
            input_text="Pocket TTS makes text to speech simple and fast.",
            voice="fantine",
            response_format="wav",
            verbose=True,
        )
        print(f"✓ Audio generated: {audio_file}")
        print(f"  File size: {os.path.getsize(audio_file)} bytes")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Testing complete!")
