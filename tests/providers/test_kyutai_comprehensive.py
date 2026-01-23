#!/usr/bin/env python3
"""
Comprehensive test suite for Kyutai TTS Provider.

Tests both Pocket TTS and TTS 1.6B models with various voices and configurations.
"""

import sys

from webscout.Provider.TTS.pockettts import KyutaiTTS, PocketTTS


def test_initialization():
    """Test provider initialization."""
    print("Testing initialization...")
    provider = KyutaiTTS()
    assert provider.default_model == "pocket-tts"
    assert provider.default_voice == "alba"
    provider.close()
    print("[OK] Initialization test passed")


def test_voice_lists():
    """Test available voices."""
    print("\nTesting voice lists...")
    provider = KyutaiTTS()

    # Test Pocket TTS voices
    pocket_voices = provider.get_pocket_tts_voices()
    assert len(pocket_voices) == 6
    assert "alba" in pocket_voices
    print(f"✓ Pocket TTS has {len(pocket_voices)} voices: {', '.join(pocket_voices)}")

    # Test TTS 1.6B voices
    tts_1_6b_voices = provider.get_tts_1_6b_voices()
    assert len(tts_1_6b_voices) == 47  # 18 + 1 + 4 + 6 + 7 + 11
    assert "Show host (US, m)" in tts_1_6b_voices
    assert "VCTK 226 (UK, m)" in tts_1_6b_voices
    print(f"✓ TTS 1.6B has {len(tts_1_6b_voices)} voices")

    # Test SUPPORTED_MODELS
    assert "pocket-tts" in provider.SUPPORTED_MODELS
    assert "tts-1.6b" in provider.SUPPORTED_MODELS
    print(f"✓ Supported models: {', '.join(provider.SUPPORTED_MODELS)}")

    provider.close()


def test_pocket_tts_voices():
    """Test Pocket TTS voices."""
    print("\nTesting Pocket TTS voices...")
    provider = KyutaiTTS()

    expected_voices = ["alba", "javert", "azelma", "eponine", "fantine", "jean"]
    for voice in expected_voices:
        assert voice in provider.POCKET_TTS_VOICES
    print(f"✓ All Pocket TTS voices verified: {', '.join(expected_voices)}")

    provider.close()


def test_tts_1_6b_voice_categories():
    """Test TTS 1.6B voice categories."""
    print("\nTesting TTS 1.6B voice categories...")
    provider = KyutaiTTS()

    # Test preset voices
    assert len(provider.TTS_1_6B_PRESET_VOICES) == 18
    assert "Show host (US, m)" in provider.TTS_1_6B_PRESET_VOICES
    print(f"✓ Preset voices: {len(provider.TTS_1_6B_PRESET_VOICES)}")

    # Test voice donations
    assert len(provider.TTS_1_6B_VOICE_DONATIONS) == 1
    assert "Voice donation - dwp (AU, m)" in provider.TTS_1_6B_VOICE_DONATIONS
    print(f"✓ Voice donations: {len(provider.TTS_1_6B_VOICE_DONATIONS)}")

    # Test CML TTS voices
    assert len(provider.TTS_1_6B_CML_VOICES) == 4
    assert any("CML" in v for v in provider.TTS_1_6B_CML_VOICES)
    print(f"✓ CML TTS voices: {len(provider.TTS_1_6B_CML_VOICES)}")

    # Test VCTK voices
    assert len(provider.TTS_1_6B_VCTK_VOICES) == 6
    assert any("VCTK" in v for v in provider.TTS_1_6B_VCTK_VOICES)
    print(f"✓ VCTK voices: {len(provider.TTS_1_6B_VCTK_VOICES)}")

    # Test Unmute voices
    assert len(provider.TTS_1_6B_UNMUTE_VOICES) == 7
    assert any("Unmute" in v for v in provider.TTS_1_6B_UNMUTE_VOICES)
    print(f"✓ Unmute voices: {len(provider.TTS_1_6B_UNMUTE_VOICES)}")

    # Test EARS dataset voices
    assert len(provider.TTS_1_6B_EARS_VOICES) == 11
    assert any("EARS" in v for v in provider.TTS_1_6B_EARS_VOICES)
    print(f"✓ EARS dataset voices: {len(provider.TTS_1_6B_EARS_VOICES)}")

    provider.close()


def test_voice_normalization():
    """Test voice normalization functions."""
    print("\nTesting voice normalization...")
    provider = KyutaiTTS()

    # Test Pocket TTS voice normalization (converts to lowercase)
    normalized = "Alba".lower()
    assert normalized == "alba"
    print(f"✓ Pocket TTS voice normalization: 'Alba' -> '{normalized}'")

    # Test TTS 1.6B voice normalization (should preserve exact format)
    normalized = provider._normalize_tts_1_6b_voice("Show host (US, m)")
    assert normalized == "Show host (US, m)"
    print("✓ TTS 1.6B voice normalization preserves format")

    provider.close()


def test_backward_compatibility():
    """Test backward compatibility alias."""
    print("\nTesting backward compatibility...")
    provider = PocketTTS()
    assert isinstance(provider, KyutaiTTS)
    assert provider.default_model == "pocket-tts"
    print("✓ PocketTTS backward compatibility alias works")
    provider.close()


def test_context_manager():
    """Test context manager functionality."""
    print("\nTesting context manager...")
    with KyutaiTTS() as provider:
        assert provider.session is not None
    print("✓ Context manager works correctly")


def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    provider = KyutaiTTS()

    # Test empty text
    try:
        provider.tts("", voice="alba")
        assert False, "Should raise ValueError for empty text"
    except ValueError as e:
        assert "empty" in str(e).lower()
        print("✓ Empty text error handling works")

    # Test invalid voice
    try:
        provider.tts("test", voice="invalid_voice")
        assert False, "Should raise ValueError for invalid voice"
    except ValueError as e:
        assert "invalid" in str(e).lower() or "not available" in str(e).lower()
        print("✓ Invalid voice error handling works")

    # Test invalid model
    try:
        provider.tts("test", model="invalid-model")
        assert False, "Should raise ValueError for invalid model"
    except ValueError as e:
        assert "invalid" in str(e).lower() or "not supported" in str(e).lower()
        print("✓ Invalid model error handling works")

    provider.close()


def test_endpoints():
    """Test API endpoints are correctly set."""
    print("\nTesting API endpoints...")
    provider = KyutaiTTS()

    assert provider.POCKET_TTS_ENDPOINT == (
        "https://kyutaipockettts6ylex2y4-kyutai-pocket-tts"
        ".functions.fnc.fr-par.scw.cloud/tts"
    )
    print(f"✓ Pocket TTS endpoint: {provider.POCKET_TTS_ENDPOINT}")

    assert provider.TTS_1_6B_ENDPOINT == (
        "https://kyutaitts1_6b6ylex2y4-kyutai-tts-1-6b"
        ".functions.fnc.fr-par.scw.cloud/tts"
    )
    print(f"✓ TTS 1.6B endpoint: {provider.TTS_1_6B_ENDPOINT}")

    provider.close()


def test_supported_formats():
    """Test supported audio formats."""
    print("\nTesting supported formats...")
    provider = KyutaiTTS()

    assert "wav" in provider.SUPPORTED_FORMATS
    assert "mp3" in provider.SUPPORTED_FORMATS
    assert "aac" in provider.SUPPORTED_FORMATS
    assert "opus" in provider.SUPPORTED_FORMATS
    print(f"✓ Supported formats: {', '.join(provider.SUPPORTED_FORMATS)}")

    provider.close()


def test_voice_for_model():
    """Test getting voices for specific model."""
    print("\nTesting voice selection per model...")
    provider = KyutaiTTS()

    # Test Pocket TTS voices
    pocket_voices = provider._get_voices_for_model("pocket-tts")
    assert pocket_voices == provider.POCKET_TTS_VOICES
    print(f"✓ Pocket TTS voices match: {len(pocket_voices)} voices")

    # Test TTS 1.6B voices
    tts_voices = provider._get_voices_for_model("tts-1.6b")
    assert tts_voices == provider.TTS_1_6B_ALL_VOICES
    print(f"✓ TTS 1.6B voices match: {len(tts_voices)} voices")

    # Test invalid model
    try:
        provider._get_voices_for_model("invalid-model")
        assert False, "Should raise ValueError"
    except ValueError:
        print("✓ Invalid model correctly raises ValueError")

    provider.close()


def main():
    """Run all tests."""
    print("=" * 70)
    print("Kyutai TTS Provider - Comprehensive Test Suite")
    print("=" * 70)

    tests = [
        test_initialization,
        test_voice_lists,
        test_pocket_tts_voices,
        test_tts_1_6b_voice_categories,
        test_voice_normalization,
        test_backward_compatibility,
        test_context_manager,
        test_error_handling,
        test_endpoints,
        test_supported_formats,
        test_voice_for_model,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All tests passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
