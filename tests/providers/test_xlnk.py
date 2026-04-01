"""Tests for XLNK TTS provider."""

import json
from pathlib import Path
from unittest import TestCase, mock

from webscout.Provider.TTS.xlnk import XLNKTTS


class FakeResponse:
    """Mock response for testing."""

    def __init__(self, json_data=None, content=b"fake audio data", status_code=200):
        self._json_data = json_data or {}
        self.content = content
        self.status_code = status_code
        self.ok = status_code == 200

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP {self.status_code}")

    def iter_lines(self):
        """Simulate SSE events."""
        file_data = {
            "path": "/tmp/gradio/test/audio.wav",
            "url": "https://xlnk-tts.hf.space/gradio_api/file=/tmp/gradio/test/audio.wav",
            "size": None,
            "orig_name": "audio.wav",
            "mime_type": None,
            "is_stream": False,
            "meta": {"_type": "gradio.FileData"},
        }
        data = [file_data]
        yield f"data: {json.dumps(data)}".encode("utf-8")


class TestXLNKTTS(TestCase):
    """Test cases for XLNK TTS provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = XLNKTTS()

    def test_initialization(self):
        """Test provider initializes with correct defaults."""
        self.assertEqual(self.provider.default_model, "xlnk-tts")
        self.assertEqual(self.provider.default_voice, "alba")
        self.assertEqual(self.provider.default_format, "wav")
        self.assertEqual(self.provider.default_temperature, 0.1)
        self.assertEqual(self.provider.default_lsd_decode_steps, 1)
        self.assertEqual(self.provider.default_noise_clamp, 0.0)
        self.assertEqual(self.provider.default_eos_threshold, -4.0)
        self.assertEqual(self.provider.default_frames_after_eos, 10)
        self.assertFalse(self.provider.default_enable_custom_frames)

    def test_supported_models(self):
        """Test supported models are defined."""
        self.assertIn("xlnk-tts", self.provider.SUPPORTED_MODELS)

    def test_supported_voices(self):
        """Test supported voices are defined."""
        expected_voices = [
            "alba",
            "marius",
            "javert",
            "jean",
            "fantine",
            "cosette",
            "eponine",
            "azelma",
        ]
        for voice in expected_voices:
            self.assertIn(voice, self.provider.SUPPORTED_VOICES)

    def test_supported_formats(self):
        """Test supported formats are defined."""
        self.assertIn("wav", self.provider.SUPPORTED_FORMATS)

    def test_get_available_voices(self):
        """Test getting available voices."""
        voices = self.provider.get_available_voices()
        self.assertIsInstance(voices, list)
        self.assertIn("alba", voices)
        self.assertEqual(len(voices), 8)

    def test_tts_empty_text(self):
        """Test TTS with empty text raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("")

    def test_tts_whitespace_text(self):
        """Test TTS with whitespace-only text raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("   ")

    def test_tts_invalid_voice(self):
        """Test TTS with invalid voice raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("Hello", voice="invalid_voice")

    @mock.patch.object(XLNKTTS, "_submit_generation", return_value="test-event-id")
    @mock.patch.object(XLNKTTS, "_get_result", return_value="https://example.com/audio.wav")
    @mock.patch.object(XLNKTTS, "_download_audio", return_value=b"fake audio data")
    def test_tts_success(self, mock_download, mock_get_result, mock_submit):
        """Test successful TTS generation."""
        result = self.provider.tts("Hello world", verbose=False)

        self.assertIsInstance(result, str)
        self.assertTrue(Path(result).exists())
        self.assertGreater(Path(result).stat().st_size, 0)

        with open(result, "rb") as f:
            self.assertEqual(f.read(), b"fake audio data")

    @mock.patch.object(XLNKTTS, "_submit_generation", return_value="test-event-id")
    @mock.patch.object(XLNKTTS, "_get_result", return_value="https://example.com/audio.wav")
    @mock.patch.object(XLNKTTS, "_download_audio", return_value=b"fake audio data")
    def test_tts_with_custom_voice(self, mock_download, mock_get_result, mock_submit):
        """Test TTS with custom voice."""
        result = self.provider.tts("Hello world", voice="marius", verbose=False)
        self.assertIsInstance(result, str)
        self.assertTrue(Path(result).exists())

    @mock.patch.object(XLNKTTS, "_submit_generation", return_value="test-event-id")
    @mock.patch.object(XLNKTTS, "_get_result", return_value="https://example.com/audio.wav")
    @mock.patch.object(XLNKTTS, "_download_audio", return_value=b"fake audio data")
    def test_tts_with_custom_params(self, mock_download, mock_get_result, mock_submit):
        """Test TTS with custom generation parameters."""
        result = self.provider.tts(
            "Hello world",
            temperature=0.5,
            lsd_decode_steps=5,
            noise_clamp=0.5,
            verbose=False,
        )
        self.assertIsInstance(result, str)
        self.assertTrue(Path(result).exists())

    @mock.patch.object(XLNKTTS, "_submit_generation", side_effect=Exception("API Error"))
    def test_tts_api_error(self, mock_submit):
        """Test TTS handles API errors gracefully."""
        from webscout import exceptions

        with self.assertRaises(exceptions.FailedToGenerateResponseError):
            self.provider.tts("Hello world")

    def test_submit_generation(self):
        """Test submitting generation request."""
        mock_response = FakeResponse(json_data={"event_id": "test-event-123"})

        with mock.patch.object(self.provider.session, "post", return_value=mock_response):
            event_id = self.provider._submit_generation(
                text="Hello world",
                voice="alba",
                temperature=0.1,
                lsd_decode_steps=1,
                noise_clamp=0.0,
                eos_threshold=-4.0,
                frames_after_eos=10,
                enable_custom_frames=False,
            )

            self.assertEqual(event_id, "test-event-123")

    def test_get_result(self):
        """Test getting result from SSE stream."""
        mock_response = FakeResponse()

        with mock.patch.object(self.provider.session, "get", return_value=mock_response):
            audio_url = self.provider._get_result("test-event-id")

            self.assertIn("https://", audio_url)
            self.assertIn("audio.wav", audio_url)

    def test_download_audio(self):
        """Test downloading audio file."""
        mock_response = FakeResponse(content=b"audio bytes")

        with mock.patch.object(self.provider.session, "get", return_value=mock_response):
            audio_data = self.provider._download_audio("https://example.com/audio.wav")

            self.assertEqual(audio_data, b"audio bytes")

    def test_required_auth(self):
        """Test that XLNK TTS doesn't require authentication."""
        self.assertFalse(self.provider.required_auth)
