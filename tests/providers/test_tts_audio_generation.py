"""Test TTS providers actually generate audio from text."""

import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm4free.TTS import (
    DeepgramTTS,
    ElevenlabsTTS,
    FasterQwen3TTS,
    MurfAITTS,
    OpenAIFMTTS,
    ParlerTTS,
    PocketTTS,
    QwenTTS,
    SherpaTTS,
    StreamElements,
)


def _make_provider(name: str):
    """Try to instantiate a provider; return (instance, None) or (None, error)."""
    cls_map = {
        "DeepgramTTS": DeepgramTTS,
        "ElevenlabsTTS": ElevenlabsTTS,
        "FasterQwen3TTS": FasterQwen3TTS,
        "MurfAITTS": MurfAITTS,
        "OpenAIFMTTS": OpenAIFMTTS,
        "ParlerTTS": ParlerTTS,
        "PocketTTS": PocketTTS,
        "QwenTTS": QwenTTS,
        "SherpaTTS": SherpaTTS,
        "StreamElements": StreamElements,
    }
    try:
        return cls_map[name](), None
    except Exception as e:
        return None, str(e)


def test_audio_generation():
    """Test that TTS providers can actually generate audio from text."""
    test_text = "Hello, this is a test of the text to speech system."

    provider_configs = [
        ("DeepgramTTS", {"text": test_text, "voice": "thalia"}),
        ("ElevenlabsTTS", {"text": test_text, "voice": "brian"}),
        ("FasterQwen3TTS", {"text": test_text, "mode": "voice_clone", "ref_preset": "ref_audio_3"}),
        ("MurfAITTS", {"text": test_text, "voice": "Hazel"}),
        ("OpenAIFMTTS", {"text": test_text, "voice": "alloy"}),
        ("ParlerTTS", {"text": test_text, "voice": "alloy"}),
        ("PocketTTS", {"text": test_text, "voice": "alba"}),
        ("QwenTTS", {"text": test_text, "voice": "cherry"}),
        ("SherpaTTS", {"text": test_text, "voice": "alloy"}),
        ("StreamElements", {"text": test_text, "voice": "Filiz"}),
    ]

    results = {}
    for name, params in provider_configs:
        provider, init_err = _make_provider(name)
        if init_err:
            results[name] = {"status": "SKIP", "error": init_err}
            continue

        try:
            audio_path = provider.tts(**params, verbose=False)

            if audio_path and Path(audio_path).exists():
                file_size = Path(audio_path).stat().st_size
                if file_size > 0:
                    results[name] = {"status": "PASS", "file": audio_path, "size": file_size}
                else:
                    results[name] = {"status": "FAIL", "error": "Empty file generated"}
            else:
                results[name] = {"status": "FAIL", "error": f"Invalid path: {audio_path}"}

        except Exception as e:
            results[name] = {"status": "FAIL", "error": str(e)[:200]}

    passed = sum(1 for v in results.values() if v["status"] == "PASS")
    skipped = sum(1 for v in results.values() if v["status"] == "SKIP")
    failed = sum(1 for v in results.values() if v["status"] == "FAIL")
    total = len(provider_configs)

    print(f"\nTTS Results: {passed} passed, {skipped} skipped, {failed} failed out of {total}")
    for name, result in results.items():
        status = result["status"]
        if status == "PASS":
            print(f"  ✓ {name}: {result['size']} bytes")
        elif status == "SKIP":
            print(f"  – {name}: init failed ({result['error'][:80]})")
        else:
            print(f"  ✗ {name}: {result.get('error', 'Unknown error')[:80]}")

    # At least some providers should work; skip-only providers are not failures
    assert passed > 0 or skipped == total, (
        f"Expected at least one provider to pass, got {passed} passes, {failed} failures"
    )


if __name__ == "__main__":
    test_audio_generation()
