"""
Faster Qwen3-TTS provider with OpenAI-compatible interface.

This module provides an OpenAI TTS API-compatible interface for the
Faster Qwen3-TTS demo hosted on Hugging Face Spaces. It supports:
- Voice cloning from reference audio
- Custom voice generation with instructions
- Voice design from text descriptions
- Streaming and non-streaming modes
- Multiple model variants
"""

import base64
import json
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, Generator, List, Optional, Union, cast

from curl_cffi import requests

from webscout import exceptions
from webscout.litagent import LitAgent
from webscout.Provider.TTS.base import BaseTTSProvider


class FasterQwen3TTS(BaseTTSProvider):
    """
    Text-to-speech provider using the Faster Qwen3-TTS API (Hugging Face Spaces).

    This provider supports:
    - Voice cloning from reference audio or preset voices
    - Custom voice generation with style instructions
    - Voice design from text descriptions
    - Streaming and non-streaming generation
    - Multiple model variants (Base, CustomVoice, VoiceDesign)

    Usage:
        client = FasterQwen3TTS()
        audio_path = client.tts("Hello world", mode="voice_clone", ref_preset="ref_audio_3")
    """

    required_auth = False

    BASE_URL = "https://huggingfacem4-faster-qwen3-tts-demo.hf.space"

    # Request headers
    headers: dict[str, str] = {
        "User-Agent": LitAgent().random(),
    }

    # Override supported models
    SUPPORTED_MODELS = [
        "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    ]

    # Supported voices (preset reference voices)
    SUPPORTED_VOICES = [
        "ref_audio_1",
        "ref_audio_2",
        "ref_audio_3",
        "ref_audio_4",
        "ref_audio_5",
    ]

    # Supported generation modes
    SUPPORTED_MODES = ["voice_clone", "custom", "voice_design"]

    # Supported languages
    SUPPORTED_LANGUAGES = ["English", "Chinese", "French", "German", "Spanish", "Auto"]

    def __init__(
        self,
        model: str = "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        timeout: int = 120,
        proxy: Optional[str] = None,
    ):
        """
        Initialize the FasterQwen3TTS client.

        Args:
            model (str): Model ID to use for generation
            timeout (int): Request timeout in seconds
            proxy (str): Proxy configuration string
        """
        super().__init__()
        self.model = model
        self.timeout = timeout
        self.proxy = proxy
        self.default_voice = "ref_audio_3"
        self.default_model = model
        self.default_mode = "voice_clone"
        self._session = requests.Session()
        self._session.headers.update(self.headers)

        # Load the model on initialization
        self._load_model(model)

    def _load_model(self, model_id: str) -> None:
        """Load a TTS model into memory."""
        try:
            response = self._session.post(
                f"{self.BASE_URL}/load",
                data={"model_id": model_id},
                timeout=self.timeout,
            )
            if response.status_code != 200:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to load model: {response.status_code} - {response.text}"
                )
            result = response.json()
            if result.get("status") not in ("loaded", "already_loaded"):
                raise exceptions.FailedToGenerateResponseError(
                    f"Model loading failed: {result}"
                )
        except exceptions.FailedToGenerateResponseError:
            raise
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(
                f"Model loading error: {str(e)}"
            )

    def get_status(self) -> dict[str, Any]:
        """Get the current model status."""
        try:
            response = self._session.get(
                f"{self.BASE_URL}/status",
                timeout=self.timeout,
            )
            if response.status_code != 200:
                raise exceptions.FailedToGenerateResponseError(
                    f"Status check failed: {response.status_code} - {response.text}"
                )
            return response.json()
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(
                f"Status check error: {str(e)}"
            )

    def get_preset_ref(self, ref_id: str) -> dict[str, Any]:
        """Get preset reference audio information."""
        try:
            response = self._session.get(
                f"{self.BASE_URL}/preset_ref/{ref_id}",
                timeout=self.timeout,
            )
            if response.status_code != 200:
                raise exceptions.FailedToGenerateResponseError(
                    f"Preset ref fetch failed: {response.status_code} - {response.text}"
                )
            return response.json()
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(
                f"Preset ref fetch error: {str(e)}"
            )

    def tts(
        self,
        text: str,
        voice: Optional[str] = None,
        verbose: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Convert text to speech using Faster Qwen3-TTS API.

        Args:
            text (str): The text to convert to speech (max 1000 characters)
            voice (str): Voice/preset reference ID (for voice_clone mode)
            verbose (bool): Whether to print debug information
            **kwargs: Additional parameters:
                - mode (str): Generation mode (voice_clone, custom, voice_design)
                - language (str): Language (English, Chinese, French, German, Spanish, Auto)
                - ref_preset (str): Preset reference ID
                - ref_text (str): Transcript of reference audio
                - ref_audio (file): Reference audio file for voice cloning
                - speaker (str): Speaker ID for custom mode
                - instruct (str): Voice style instructions
                - xvec_only (bool): Use only x-vector for voice cloning
                - temperature (float): Sampling temperature (0.0-1.0)
                - top_k (int): Top-K sampling
                - repetition_penalty (float): Repetition penalty
                - response_format (str): Output format (wav, mp3, etc.)
                - stream (bool): Whether to stream the response

        Returns:
            str: Path to the generated audio file
        """
        # Extract parameters from kwargs
        mode = kwargs.get("mode", self.default_mode)
        language = kwargs.get("language", "English")
        ref_preset = kwargs.get("ref_preset", voice or self.default_voice)
        ref_text = kwargs.get("ref_text", "")
        ref_audio = kwargs.get("ref_audio")
        speaker = kwargs.get("speaker", "")
        instruct = kwargs.get("instruct", "")
        xvec_only = kwargs.get("xvec_only", True)
        temperature = kwargs.get("temperature", 0.9)
        top_k = kwargs.get("top_k", 50)
        repetition_penalty = kwargs.get("repetition_penalty", 1.05)
        response_format = kwargs.get("response_format", "wav")
        stream = kwargs.get("stream", False)

        # Validate inputs
        if not text or not isinstance(text, str):
            raise ValueError("Input text must be a non-empty string")
        if len(text) > 1000:
            raise ValueError("Text exceeds maximum length of 1000 characters")
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(
                f"Mode '{mode}' not supported. Available modes: {', '.join(self.SUPPORTED_MODES)}"
            )
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Language '{language}' not supported. Available languages: {', '.join(self.SUPPORTED_LANGUAGES)}"
            )

        # Build request data
        data: dict[str, Any] = {
            "text": text,
            "language": language,
            "mode": mode,
            "temperature": str(temperature),
            "top_k": str(top_k),
            "repetition_penalty": str(repetition_penalty),
        }

        # Add mode-specific parameters
        if mode == "voice_clone":
            data["ref_preset"] = ref_preset
            data["ref_text"] = ref_text
            data["xvec_only"] = str(xvec_only).lower()
        elif mode == "custom":
            data["speaker"] = speaker
            data["instruct"] = instruct
        elif mode == "voice_design":
            data["instruct"] = instruct

        # Handle reference audio file upload
        files: dict[str, Any] = {}
        if ref_audio is not None:
            if isinstance(ref_audio, (str, Path)):
                files["ref_audio"] = open(str(ref_audio), "rb")
            else:
                files["ref_audio"] = ref_audio

        try:
            if stream:
                return self._generate_stream(data, files, response_format, verbose)
            else:
                return self._generate_non_stream(data, files, response_format, verbose)
        finally:
            # Close any open file handles
            for f in files.values():
                if hasattr(f, "close"):
                    f.close()

    def _generate_non_stream(
        self,
        data: dict[str, Any],
        files: dict[str, Any],
        response_format: str,
        verbose: bool,
    ) -> str:
        """Generate audio using non-streaming endpoint."""
        try:
            response = self._session.post(
                f"{self.BASE_URL}/generate",
                data=data,
                files=files if files else None,
                timeout=self.timeout,
            )
            if response.status_code != 200:
                raise exceptions.FailedToGenerateResponseError(
                    f"TTS generation failed: {response.status_code} - {response.text}"
                )
            result = response.json()

            # Extract base64 audio data
            audio_b64 = result.get("audio_b64")
            if not audio_b64:
                raise exceptions.FailedToGenerateResponseError(
                    f"No audio data in response: {result}"
                )

            # Decode and save audio
            audio_data = base64.b64decode(audio_b64)
            return self._save_audio_data(audio_data, response_format, verbose)
        except exceptions.FailedToGenerateResponseError:
            raise
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(
                f"TTS generation error: {str(e)}"
            )

    def _generate_stream(
        self,
        data: dict[str, Any],
        files: dict[str, Any],
        response_format: str,
        verbose: bool,
    ) -> str:
        """Generate audio using streaming endpoint."""
        try:
            response = self._session.post(
                f"{self.BASE_URL}/generate/stream",
                data=data,
                files=files if files else None,
                timeout=self.timeout,
                stream=True,
            )
            if response.status_code != 200:
                raise exceptions.FailedToGenerateResponseError(
                    f"Streaming TTS failed: {response.status_code} - {response.text}"
                )

            # Collect audio chunks
            audio_chunks: list[bytes] = []

            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data_str = line[5:].strip()
                    try:
                        chunk_data = json.loads(data_str)
                        chunk_type = chunk_data.get("type")

                        if chunk_type == "chunk":
                            audio_b64 = chunk_data.get("audio_b64")
                            if audio_b64:
                                audio_chunks.append(base64.b64decode(audio_b64))
                            if verbose:
                                metrics = chunk_data.get("rtf", "N/A")
                                print(f"  Chunk received (RTF: {metrics})")
                        elif chunk_type == "error":
                            error_msg = chunk_data.get("message", "Unknown error")
                            raise exceptions.FailedToGenerateResponseError(
                                f"Streaming error: {error_msg}"
                            )
                        elif chunk_type == "done":
                            if verbose:
                                total_ms = chunk_data.get("total_ms", "N/A")
                                total_audio = chunk_data.get("total_audio_s", "N/A")
                                print(f"  Generation complete ({total_ms}ms, {total_audio}s audio)")
                    except json.JSONDecodeError:
                        continue

            if not audio_chunks:
                raise exceptions.FailedToGenerateResponseError(
                    "No audio chunks received from streaming endpoint"
                )

            # Combine all chunks
            combined_audio = b"".join(audio_chunks)
            return self._save_audio_data(combined_audio, response_format, verbose)
        except exceptions.FailedToGenerateResponseError:
            raise
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(
                f"Streaming TTS error: {str(e)}"
            )

    def _save_audio_data(
        self, audio_data: bytes, response_format: str, verbose: bool
    ) -> str:
        """Save audio data to a temporary file."""
        file_extension = f".{response_format}" if not response_format.startswith(".") else response_format
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension,
            prefix="faster_qwen3_tts_",
        )
        try:
            temp_file.write(audio_data)
            temp_file.close()
            if verbose:
                print(f"Audio saved to: {temp_file.name}")
            return temp_file.name
        except Exception as e:
            temp_file.close()
            raise exceptions.FailedToGenerateResponseError(
                f"Failed to save audio: {str(e)}"
            )

    def transcribe(self, audio_file: Union[str, Path, BinaryIO]) -> str:
        """
        Transcribe reference audio to text.

        Args:
            audio_file: Path to audio file or file-like object

        Returns:
            str: Transcribed text
        """
        try:
            if isinstance(audio_file, (str, Path)):
                files = {"audio": open(str(audio_file), "rb")}
                close_file = True
            else:
                files = {"audio": audio_file}
                close_file = False

            response = self._session.post(
                f"{self.BASE_URL}/transcribe",
                files=files,
                timeout=self.timeout,
            )
            if response.status_code != 200:
                raise exceptions.FailedToGenerateResponseError(
                    f"Transcription failed: {response.status_code} - {response.text}"
                )
            result = response.json()
            return result.get("text", "")
        except exceptions.FailedToGenerateResponseError:
            raise
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(
                f"Transcription error: {str(e)}"
            )
        finally:
            if close_file and hasattr(files["audio"], "close"):
                files["audio"].close()


if __name__ == "__main__":
    from rich import print

    client = FasterQwen3TTS()

    # Check status
    print("=== Model Status ===")
    status = client.get_status()
    print(status)

    # Non-streaming example
    print("\n=== Non-streaming TTS ===")
    audio_path = client.tts(
        text="Hello, this is a test of the Faster Qwen3 text-to-speech system.",
        mode="voice_clone",
        ref_preset="ref_audio_3",
        verbose=True,
    )
    print(f"Audio saved to: {audio_path}")

    # Streaming example
    print("\n=== Streaming TTS ===")
    audio_path = client.tts(
        text="This is a streaming test of the Faster Qwen3 text-to-speech system.",
        mode="voice_clone",
        ref_preset="ref_audio_3",
        stream=True,
        verbose=True,
    )
    print(f"Audio saved to: {audio_path}")
