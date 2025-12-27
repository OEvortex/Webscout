##################################################################################
##  SherpaTTS Provider                                                         ##
##################################################################################
import json
import pathlib
import random
import string
import tempfile
from typing import Any, Generator, Optional, Union, cast

import httpx
from litprinter import ic

from webscout import exceptions
from webscout.litagent import LitAgent

try:
    from . import utils
    from .base import BaseTTSProvider
except ImportError:
    # Handle direct execution
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from webscout.Provider.TTS.base import BaseTTSProvider

class SherpaTTS(BaseTTSProvider):
    """
    Text-to-speech provider using the Next-gen Kaldi (Sherpa-ONNX) API.

    This provider follows the OpenAI TTS API structure with support for:
    - 50+ languages including English, Chinese, Cantonese, Arabic, French, etc.
    - Multiple ONNX-based models (Kokoro, Piper, Coqui, etc.)
    - Speaker ID and Speed control
    - Multiple output formats
    """
    required_auth = False

    BASE_URL = "https://k2-fsa-text-to-speech.hf.space"

    # Request headers
    headers: dict[str, str] = {
        "User-Agent": LitAgent().random(),
        "origin": BASE_URL,
        "referer": f"{BASE_URL}/",
    }

    SUPPORTED_MODELS = [
        "csukuangfj/kokoro-en-v0_19|11 speakers",
        "csukuangfj/kitten-kitten-en-v0_1-fp16|8 speakers",
        "csukuangfj/kitten-nano-en-v0_2-fp16|8 speakers",
        "csukuangfj/kitten-nano-en-v0_1-fp16|8 speakers",
        "csukuangfj/vits-piper-en_US-glados-high|1 speaker",
        "csukuangfj/vits-piper-en_US-glados|1 speaker",
        "csukuangfj/vits-piper-en_GB-southern_english_male-medium|8 speakers",
        "csukuangfj/vits-piper-en_GB-southern_english_female-medium|6 speakers",
        "csukuangfj/vits-piper-en_US-bryce-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-john-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-norman-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-miro-high|1 speaker",
        "csukuangfj/vits-coqui-en-ljspeech|1 speaker",
        "csukuangfj/vits-coqui-en-ljspeech-neon|1 speaker",
        "csukuangfj/vits-coqui-en-vctk|109 speakers",
        "csukuangfj/vits-piper-en_GB-miro-high|1 speaker",
        "csukuangfj/vits-piper-en_GB-dii-high|1 speaker",
        "csukuangfj/vits-piper-en_GB-sweetbbak-amy|1 speaker",
        "csukuangfj/vits-piper-en_US-amy-low|1 speaker",
        "csukuangfj/vits-piper-en_US-amy-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-arctic-medium|18 speakers",
        "csukuangfj/vits-piper-en_US-danny-low|1 speaker",
        "csukuangfj/vits-piper-en_US-hfc_male-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-hfc_female-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-joe-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-kathleen-low|1 speaker",
        "csukuangfj/vits-piper-en_US-kusal-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-l2arctic-medium|24 speakers",
        "csukuangfj/vits-piper-en_US-lessac-high|1 speaker",
        "csukuangfj/vits-piper-en_US-lessac-low|1 speaker",
        "csukuangfj/vits-piper-en_US-lessac-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-libritts-high|904 speakers",
        "csukuangfj/vits-piper-en_US-libritts_r-medium|904 speakers",
        "csukuangfj/vits-piper-en_US-ljspeech-high|1 speaker",
        "csukuangfj/vits-piper-en_US-ljspeech-medium|1 speaker",
        "csukuangfj/vits-piper-en_US-ryan-high|1 speaker",
        "csukuangfj/vits-piper-en_US-ryan-low|1 speaker",
        "csukuangfj/vits-piper-en_US-ryan-medium|1 speaker",
        "csukuangfj/vits-piper-en_GB-alan-low|1 speaker",
        "csukuangfj/vits-piper-en_GB-alan-medium|1 speaker",
        "csukuangfj/vits-piper-en_GB-alan-medium",
        "csukuangfj/vits-piper-en_GB-cori-high|1 speaker",
        "csukuangfj/vits-piper-en_GB-cori-medium|1 speaker",
        "csukuangfj/vits-piper-en_GB-jenny_dioco-medium|1 speaker",
        "csukuangfj/vits-piper-en_GB-northern_english_male-medium|1 speaker",
        "csukuangfj/vits-piper-en_GB-semaine-medium|4 speakers",
        "csukuangfj/vits-piper-en_GB-southern_english_female-low|1 speaker",
        "csukuangfj/vits-piper-en_GB-vctk-medium|109 speakers",
        "csukuangfj/vits-vctk|109 speakers",
        "csukuangfj/vits-ljs|1 speaker"
    ]

    LANGUAGES = [
        "English", "Chinese (Mandarin, 普通话)", "Chinese+English", "Persian+English",
        "Cantonese (粤语)", "Min-nan (闽南话)", "Arabic", "Afrikaans", "Bengali",
        "Bulgarian", "Catalan", "Croatian", "Czech", "Danish", "Dutch", "Estonian",
        "Finnish", "French", "Georgian", "German", "Greek", "Gujarati", "Hindi",
        "Hungarian", "Icelandic", "Indonesian", "Irish", "Italian", "Kazakh",
        "Korean", "Latvian", "Lithuanian", "Luxembourgish", "Maltese", "Nepali",
        "Norwegian", "Persian", "Polish", "Portuguese", "Romanian", "Russian",
        "Serbian", "Slovak", "Slovenian", "Spanish", "Swahili", "Swedish", "Thai",
        "Tswana", "Turkish", "Ukrainian", "Vietnamese", "Welsh"
    ]

    def __init__(self, timeout: int = 60, proxy: Optional[str] = None):
        """
        Initialize the SherpaTTS client.
        """
        super().__init__()
        self.timeout = timeout
        self.proxy = proxy
        self.default_language = "English"
        self.default_model_choice = "csukuangfj/kokoro-en-v0_19|11 speakers"

    def _generate_session_hash(self) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=11))

    def tts(self, text: str, voice: Optional[str] = None, verbose: bool = False, **kwargs) -> str:
        """
        Convert text to speech using Sherpa-ONNX API.

        Args:
            text: Input text
            **kwargs: Additional parameters (language, model_choice, speaker_id, speed, response_format, verbose)
        """
        # Extract parameters from kwargs with defaults
        language = kwargs.get('language', "English")
        model_choice = kwargs.get('model_choice', "csukuangfj/kokoro-en-v0_19|11 speakers")
        speaker_id = kwargs.get('speaker_id', "0")
        speed = kwargs.get('speed', 1.0)
        response_format = kwargs.get('response_format', "wav")
        verbose = kwargs.get('verbose', True)
        if not text:
            raise ValueError("Input text must be a non-empty string")

        model_choice = self.validate_model(model_choice)

        session_hash = self._generate_session_hash()
        filename = pathlib.Path(tempfile.NamedTemporaryFile(suffix=f".{response_format}", dir=self.temp_dir, delete=False).name)

        if verbose:
            ic.configureOutput(prefix='DEBUG| ')
            ic(f"SherpaTTS: Generating speech for '{text[:20]}...' using {language}/{model_choice}")

        client_kwargs: dict[str, Any] = {"headers": self.headers, "timeout": self.timeout}
        if self.proxy:
            client_kwargs["proxy"] = self.proxy

        try:
            with httpx.Client(**client_kwargs) as client:
                # Step 1: Join the queue
                join_url = f"{self.BASE_URL}/gradio_api/queue/join?"
                payload = {
                    "data": [language, model_choice, text, speaker_id, speed],
                    "event_data": None,
                    "fn_index": 1,
                    "trigger_id": 9,
                    "session_hash": session_hash
                }

                response = client.post(join_url, json=payload)
                response.raise_for_status()

                # Step 2: Poll for data
                data_url = f"{self.BASE_URL}/gradio_api/queue/data?session_hash={session_hash}"
                audio_url = None

                with client.stream("GET", data_url) as stream:
                    for line in stream.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                            except json.JSONDecodeError:
                                continue

                            msg = data.get("msg")
                            if msg == "process_completed":
                                if data.get("success"):
                                    output_data = data.get("output", {}).get("data", [])
                                    if output_data:
                                        audio_info = output_data[0]
                                        path = audio_info["path"] if isinstance(audio_info, dict) else audio_info
                                        audio_url = f"{self.BASE_URL}/gradio_api/file={path}"
                                    break
                                else:
                                    raise exceptions.FailedToGenerateResponseError(f"Generation failed: {data}")
                            elif msg == "queue_full":
                                raise exceptions.FailedToGenerateResponseError("Queue is full")

                if not audio_url:
                    raise exceptions.FailedToGenerateResponseError("Failed to get audio URL from stream")

                # Step 3: Download the audio file
                audio_response = client.get(audio_url)
                audio_response.raise_for_status()

                with open(filename, "wb") as f:
                    f.write(audio_response.content)

                if verbose:
                    ic.configureOutput(prefix='DEBUG| ')
                    ic(f"Speech generated successfully: {filename}")

                return filename.as_posix()

        except Exception as e:
            if verbose:
                ic.configureOutput(prefix='DEBUG| ')
                ic(f"Error in SherpaTTS: {e}")
            raise exceptions.FailedToGenerateResponseError(f"Failed to generate audio: {e}")

    def create_speech(
        self,
        input_text: str,
        model: Optional[str] = "csukuangfj/kokoro-en-v0_19|11 speakers",
        voice: Optional[str] = None,
        response_format: Optional[str] = "mp3",
        instructions: Optional[str] = None,
        verbose: bool = False
    ) -> str:
        """
        OpenAI-compatible speech creation interface.

        Args:
            input_text (str): The text to convert to speech
            model (str): The TTS model to use
            voice (str): The voice to use (not used by SherpaAI directly)
            response_format (str): Audio format
            instructions (str): Voice instructions
            verbose (bool): Whether to print debug information

        Returns:
            str: Path to the generated audio file
        """
        model_choice = model or "csukuangfj/kokoro-en-v0_19|11 speakers"
        return self.tts(
            text=input_text,
            model_choice=model_choice,
            response_format=response_format or "mp3",
            verbose=verbose
        )

    def with_streaming_response(self):
        return StreamingResponseContextManager(self)

class StreamingResponseContextManager:
    def __init__(self, tts_provider: SherpaTTS):
        self.tts_provider = tts_provider
    def create(self, **kwargs):
        audio_file = self.tts_provider.create_speech(**kwargs)
        return StreamingResponse(audio_file)
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): pass

class StreamingResponse:
    def __init__(self, audio_file: str):
        self.audio_file = audio_file
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): pass
    def stream_to_file(self, file_path: str):
        import shutil
        shutil.copy2(self.audio_file, file_path)
    def iter_bytes(self, chunk_size: int = 1024):
        with open(self.audio_file, 'rb') as f:
            while chunk := f.read(chunk_size):
                yield chunk

if __name__ == "__main__":
    tts = SherpaTTS()
    try:
        path = tts.tts("This is a Sherpa-ONNX test.", verbose=True)
        ic.configureOutput(prefix='INFO| ')
        ic(f"Result: {path}")
    except Exception as e:
        ic.configureOutput(prefix='ERROR| ')
        ic(f"Error: {e}")
