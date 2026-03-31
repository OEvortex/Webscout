"""Test TTS providers actually generate audio from text."""

import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from webscout.Provider.TTS import (
    DeepgramTTS,
    ElevenlabsTTS,
    FasterQwen3TTS,
    FreeTTS,
    MurfAITTS,
    OpenAIFMTTS,
    ParlerTTS,
    PocketTTS,
    QwenTTS,
    SherpaTTS,
    SpeechMaTTS,
    StreamElements,
)


def test_audio_generation():
    """Test that TTS providers can actually generate audio from text."""
    test_text = "Hello, this is a test of the text to speech system."
    output_dir = Path(tempfile.mkdtemp(prefix="tts_test_"))
    
    providers = {
        "DeepgramTTS": {
            "instance": DeepgramTTS(),
            "params": {"text": test_text, "voice": "thalia"},
        },
        "ElevenlabsTTS": {
            "instance": ElevenlabsTTS(),
            "params": {"text": test_text, "voice": "brian"},
        },
        "FasterQwen3TTS": {
            "instance": FasterQwen3TTS(),
            "params": {
                "text": test_text,
                "mode": "voice_clone",
                "ref_preset": "ref_audio_3",
            },
        },
        "FreeTTS": {
            "instance": FreeTTS(),
            "params": {"text": test_text, "voice": "alloy"},
        },
        "MurfAITTS": {
            "instance": MurfAITTS(),
            "params": {"text": test_text, "voice": "Hazel"},
        },
        "OpenAIFMTTS": {
            "instance": OpenAIFMTTS(),
            "params": {"text": test_text, "voice": "alloy"},
        },
        "ParlerTTS": {
            "instance": ParlerTTS(),
            "params": {"text": test_text, "voice": "alloy"},
        },
        "PocketTTS": {
            "instance": PocketTTS(),
            "params": {"text": test_text, "voice": "alba"},
        },
        "QwenTTS": {
            "instance": QwenTTS(),
            "params": {"text": test_text, "voice": "cherry"},
        },
        "SherpaTTS": {
            "instance": SherpaTTS(),
            "params": {"text": test_text, "voice": "alloy"},
        },
        "SpeechMaTTS": {
            "instance": SpeechMaTTS(),
            "params": {"text": test_text, "voice": "aditi"},
        },
        "StreamElements": {
            "instance": StreamElements(),
            "params": {"text": test_text, "voice": "Filiz"},
        },
    }

    print("=== Testing TTS Audio Generation ===\n")
    print(f"Test text: '{test_text}'")
    print(f"Output directory: {output_dir}\n")
    
    results = {}
    for name, config in providers.items():
        provider = config["instance"]
        params = config["params"]
        
        try:
            print(f"Testing {name}...")
            audio_path = provider.tts(**params, verbose=False)  # ty:ignore[possibly-missing-attribute, invalid-argument-type]
            
            # Verify the file exists and has content
            if audio_path and Path(audio_path).exists():
                file_size = Path(audio_path).stat().st_size
                if file_size > 0:
                    results[name] = {
                        "status": "✅ PASS",
                        "file": audio_path,
                        "size": file_size,
                    }
                    print(f"  ✓ Generated: {audio_path} ({file_size} bytes)")
                else:
                    results[name] = {
                        "status": "❌ FAIL",
                        "error": "Empty file generated",
                    }
                    print(f"  ✗ Empty file generated")
            else:
                results[name] = {
                    "status": "❌ FAIL",
                    "error": f"Invalid path: {audio_path}",
                }
                print(f"  ✗ Invalid path: {audio_path}")
                
        except Exception as e:
            results[name] = {
                "status": "❌ FAIL",
                "error": str(e),
            }
            print(f"  ✗ Error: {str(e)[:100]}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"=== RESULTS ===")
    print(f"{'='*60}")
    
    passed = sum(1 for v in results.values() if v["status"].startswith("✅"))
    failed = sum(1 for v in results.values() if v["status"].startswith("❌"))
    
    print(f"\nPassed: {passed}/{len(providers)}")
    print(f"Failed: {failed}/{len(providers)}")
    
    print(f"\n{'='*60}")
    for name, result in results.items():
        status = result["status"]
        if status.startswith("✅"):
            print(f"✓ {name}: {result['size']} bytes -> {result['file']}")
        else:
            print(f"✗ {name}: {result.get('error', 'Unknown error')}")
    
    return results


if __name__ == "__main__":
    test_audio_generation()
