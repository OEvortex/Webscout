"""Test script for Cohere STT provider."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from webscout.Provider.STT.cohere import CohereSTT
from webscout.Provider.STT.base import TranscriptionResponse


def test_cohere_stt():
    """Test Cohere STT provider with a sample audio file."""
    client = CohereSTT()
    
    # Test with a remote audio URL (no file upload needed)
    print("=== Testing Cohere STT Provider ===")
    print(f"Base URL: {client.base_url}")
    print(f"Available models: {client.AVAILABLE_MODELS}")
    print(f"Default language: {client.default_language}")
    
    # Test models property
    models = client.models.list()
    print(f"\nModels list: {models}")
    
    # Test transcription with a sample audio file
    # Using a publicly available sample audio
    sample_audio_url = r"C:\Users\koula\Desktop\CODEBASE\Projects\OEvortex\Webscout\tests\test.wav"
    
    print(f"\n=== Testing transcription ===")
    print(f"Using sample audio: {sample_audio_url}")
    
    try:
        # Test non-streaming transcription
        print("\n--- Non-streaming test ---")
        with open(sample_audio_url, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="cohere-multilingual-asr",
                file=audio_file,
                response_format="text",
                stream=False
            )
            if isinstance(result, TranscriptionResponse):
                print(f"Transcription result: {result.text}")
            else:
                print(f"Unexpected result type: {type(result)}")
            
    except Exception as e:
        print(f"Error during transcription: {e}")
        print("This is expected if the audio file is not accessible or API is down")


if __name__ == "__main__":
    test_cohere_stt()
