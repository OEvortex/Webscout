"""Tests for KittenTTS TTS provider."""

import json
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from webscout.Provider.TTS.kittentts import KittenTTS


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
            "url": "https://kittenml-kittentts-demo.hf.space/gradio_api/file=/tmp/gradio/test/audio.wav",
            "size": None,
            "orig_name": "audio.wav",
            "mime_type": None,
            "is_stream": False,
            "meta": {"_type": "gradio.FileData"},
        }
        data = [file_data]
        yield f"data: {json.dumps(data)}".encode("utf-8")


class TestKittenTTS(TestCase):
    """Test cases for KittenTTS provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = KittenTTS()

    def test_initialization(self):
        """Test provider initializes with correct defaults."""
        self.assertEqual(self.provider.default_model, "micro")
        self.assertEqual(self.provider.default_voice, "Jasper")
        self.assertEqual(self.provider.default_format, "wav")
        self.assertEqual(self.provider.default_speed, 1.0)

    def test_supported_models(self):
        """Test supported models are defined."""
        self.assertIn("nano", self.provider.SUPPORTED_MODELS)
        self.assertIn("micro", self.provider.SUPPORTED_MODELS)
        self.assertIn("mini", self.provider.SUPPORTED_MODELS)

    def test_model_names_mapping(self):
        """Test model names mapping to Gradio API names."""
        self.assertEqual(
            self.provider.MODEL_NAMES["nano"], "Nano (15M - Fastest)"
        )
        self.assertEqual(
            self.provider.MODEL_NAMES["micro"], "Micro (40M - Balanced)"
        )
        self.assertEqual(
            self.provider.MODEL_NAMES["mini"], "Mini (80M - Best Quality)"
        )

    def test_supported_voices(self):
        """Test supported voices are defined."""
        expected_voices = [
            "Bella",
            "Jasper",
            "Luna",
            "Bruno",
            "Rosie",
            "Hugo",
            "Kiki",
            "Leo",
        ]
        for voice in expected_voices:
            self.assertIn(voice, self.provider.SUPPORTED_VOICES)

    def test_supported_formats(self):
        """Test supported formats are defined."""
        self.assertIn("wav", self.provider.SUPPORTED_FORMATS)

    def test_get_available_models(self):
        """Test getting available models."""
        models = self.provider.get_available_models()
        self.assertIsInstance(models, dict)
        self.assertIn("nano", models)
        self.assertIn("micro", models)
        self.assertIn("mini", models)

    def test_get_available_voices(self):
        """Test getting available voices."""
        voices = self.provider.get_available_voices()
        self.assertIsInstance(voices, list)
        self.assertIn("Jasper", voices)
        self.assertEqual(len(voices), 8)

    def test_tts_empty_text(self):
        """Test TTS with empty text raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("")

    def test_tts_whitespace_text(self):
        """Test TTS with whitespace-only text raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("   ")

    def test_tts_invalid_speed_low(self):
        """Test TTS with speed too low raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("Hello", speed=0.4)

    def test_tts_invalid_speed_high(self):
        """Test TTS with speed too high raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("Hello", speed=2.1)

    def test_tts_invalid_voice(self):
        """Test TTS with invalid voice raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("Hello", voice="InvalidVoice")

    def test_tts_invalid_model(self):
        """Test TTS with invalid model raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("Hello", model="invalid")

    @mock.patch.object(KittenTTS, "_submit_synthesis", return_value="test-event-id")
    @mock.patch.object(KittenTTS, "_get_result", return_value="https://example.com/audio.wav")
    @mock.patch.object(KittenTTS, "_download_audio", return_value=b"fake audio data")
    def test_tts_success(self, mock_download, mock_get_result, mock_submit):
        """Test successful TTS generation."""
        result = self.provider.tts("Hello world", verbose=False)

        # Verify the result is a file path
        self.assertIsInstance(result, str)
        self.assertTrue(Path(result).exists())

        # Verify the file has content
        self.assertGreater(Path(result).stat().st_size, 0)

        # Verify the audio content is correct
        with open(result, "rb") as f:
            self.assertEqual(f.read(), b"fake audio data")

    @mock.patch.object(KittenTTS, "_submit_synthesis", return_value="test-event-id")
    @mock.patch.object(KittenTTS, "_get_result", return_value="https://example.com/audio.wav")
    @mock.patch.object(KittenTTS, "_download_audio", return_value=b"fake audio data")
    def test_tts_with_custom_model(self, mock_download, mock_get_result, mock_submit):
        """Test TTS with custom model."""
        result = self.provider.tts("Hello world", model="nano", verbose=False)

        self.assertIsInstance(result, str)
        self.assertTrue(Path(result).exists())

    @mock.patch.object(KittenTTS, "_submit_synthesis", return_value="test-event-id")
    @mock.patch.object(KittenTTS, "_get_result", return_value="https://example.com/audio.wav")
    @mock.patch.object(KittenTTS, "_download_audio", return_value=b"fake audio data")
    def test_tts_with_custom_speed(self, mock_download, mock_get_result, mock_submit):
        """Test TTS with custom speed."""
        result = self.provider.tts("Hello world", speed=1.5, verbose=False)

        self.assertIsInstance(result, str)
        self.assertTrue(Path(result).exists())

    @mock.patch.object(KittenTTS, "_submit_synthesis", side_effect=Exception("API Error"))
    def test_tts_api_error(self, mock_submit):
        """Test TTS handles API errors gracefully."""
        from webscout import exceptions

        with self.assertRaises(exceptions.FailedToGenerateResponseError):
            self.provider.tts("Hello world")

    def test_submit_synthesis(self):
        """Test submitting synthesis request."""
        mock_response = FakeResponse(json_data={"event_id": "test-event-123"})

        with mock.patch.object(self.provider.session, "post", return_value=mock_response):
            event_id = self.provider._submit_synthesis(
                text="Hello world",
                model_name="Micro (40M - Balanced)",
                voice="Jasper",
                speed=1.0,
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
        """Test that KittenTTS doesn't require authentication."""
        self.assertFalse(self.provider.required_auth)
