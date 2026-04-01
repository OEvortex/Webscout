"""Tests for LuxTTS TTS provider."""

import tempfile
from pathlib import Path
from unittest import TestCase, mock

from webscout.Provider.TTS.luxtts import LuxTTS


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
        import json

        file_data = {
            "path": "/tmp/gradio/test/audio.wav",
            "url": "https://yatharths-luxtts.hf.space/gradio_api/file=/tmp/gradio/test/audio.wav",
            "meta": {"_type": "gradio.FileData"},
            "orig_name": "audio.wav",
        }
        data = [file_data, "✨ Generation complete in **20.73s**."]
        yield f"data: {json.dumps(data)}".encode("utf-8")


class TestLuxTTS(TestCase):
    """Test cases for LuxTTS provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = LuxTTS()

    def test_initialization(self):
        """Test provider initializes with correct defaults."""
        self.assertEqual(self.provider.default_model, "luxtts")
        self.assertEqual(self.provider.default_voice, "default")
        self.assertEqual(self.provider.default_format, "wav")
        self.assertEqual(self.provider.default_rms, 0.01)
        self.assertEqual(self.provider.default_ref_duration, 5)
        self.assertEqual(self.provider.default_t_shift, 0.9)
        self.assertEqual(self.provider.default_num_steps, 4)
        self.assertEqual(self.provider.default_speed, 0.8)
        self.assertFalse(self.provider.default_return_smooth)

    def test_supported_models(self):
        """Test supported models are defined."""
        self.assertIn("luxtts", self.provider.SUPPORTED_MODELS)

    def test_supported_formats(self):
        """Test supported formats are defined."""
        self.assertIn("wav", self.provider.SUPPORTED_FORMATS)
        self.assertIn("mp3", self.provider.SUPPORTED_FORMATS)

    def test_preset_voices(self):
        """Test preset voices are defined."""
        self.assertIn("default", self.provider.PRESET_VOICES)
        self.assertIn("male_1", self.provider.PRESET_VOICES)

    def test_get_available_voices(self):
        """Test getting available voices."""
        voices = self.provider.get_available_voices()
        self.assertIsInstance(voices, dict)
        self.assertIn("default", voices)

    def test_set_reference_audio(self):
        """Test setting custom reference audio."""
        url = "https://example.com/audio.wav"
        self.provider.set_reference_audio(url)
        self.assertEqual(self.provider.reference_audio, url)

    def test_set_reference_audio_invalid_url(self):
        """Test setting invalid reference audio URL."""
        with self.assertRaises(ValueError):
            self.provider.set_reference_audio("not-a-url")

    def test_tts_empty_text(self):
        """Test TTS with empty text raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("")

    def test_tts_whitespace_text(self):
        """Test TTS with whitespace-only text raises error."""
        with self.assertRaises(ValueError):
            self.provider.tts("   ")

    @mock.patch.object(LuxTTS, "_submit_inference", return_value="test-event-id")
    @mock.patch.object(LuxTTS, "_get_result", return_value="https://example.com/audio.wav")
    @mock.patch.object(LuxTTS, "_download_audio", return_value=b"fake audio data")
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

    @mock.patch.object(LuxTTS, "_submit_inference", return_value="test-event-id")
    @mock.patch.object(LuxTTS, "_get_result", return_value="https://example.com/audio.wav")
    @mock.patch.object(LuxTTS, "_download_audio", return_value=b"fake audio data")
    def test_tts_with_custom_voice(self, mock_download, mock_get_result, mock_submit):
        """Test TTS with custom voice preset."""
        result = self.provider.tts("Hello world", voice="male_1", verbose=False)

        self.assertIsInstance(result, str)
        self.assertTrue(Path(result).exists())

    @mock.patch.object(LuxTTS, "_submit_inference", return_value="test-event-id")
    @mock.patch.object(LuxTTS, "_get_result", return_value="https://example.com/audio.wav")
    @mock.patch.object(LuxTTS, "_download_audio", return_value=b"fake audio data")
    def test_tts_with_custom_reference_url(self, mock_download, mock_get_result, mock_submit):
        """Test TTS with custom reference audio URL."""
        custom_url = "https://example.com/custom-audio.wav"
        result = self.provider.tts("Hello world", voice=custom_url, verbose=False)

        self.assertIsInstance(result, str)
        self.assertTrue(Path(result).exists())

    def test_tts_invalid_voice(self):
        """Test TTS with invalid voice name."""
        with self.assertRaises(ValueError):
            self.provider.tts("Hello world", voice="invalid-voice")

    @mock.patch.object(LuxTTS, "_submit_inference", side_effect=Exception("API Error"))
    def test_tts_api_error(self, mock_submit):
        """Test TTS handles API errors gracefully."""
        from webscout import exceptions

        with self.assertRaises(exceptions.FailedToGenerateResponseError):
            self.provider.tts("Hello world")

    def test_submit_inference(self):
        """Test submitting inference request."""
        mock_response = FakeResponse(json_data={"event_id": "test-event-123"})

        with mock.patch.object(self.provider.session, 'post', return_value=mock_response):
            event_id = self.provider._submit_inference(
                text="Hello world",
                reference_audio="https://example.com/audio.wav",
                rms=0.01,
                ref_duration=5,
                t_shift=0.9,
                num_steps=4,
                speed=0.8,
                return_smooth=False,
            )

            self.assertEqual(event_id, "test-event-123")

    def test_get_result(self):
        """Test getting result from SSE stream."""
        mock_response = FakeResponse()

        with mock.patch.object(self.provider.session, 'get', return_value=mock_response):
            audio_url = self.provider._get_result("test-event-id")

            self.assertIn("https://", audio_url)
            self.assertIn("audio.wav", audio_url)

    def test_download_audio(self):
        """Test downloading audio file."""
        mock_response = FakeResponse(content=b"audio bytes")

        with mock.patch.object(self.provider.session, 'get', return_value=mock_response):
            audio_data = self.provider._download_audio("https://example.com/audio.wav")

            self.assertEqual(audio_data, b"audio bytes")

    def test_required_auth(self):
        """Test that LuxTTS doesn't require authentication."""
        self.assertFalse(self.provider.required_auth)
