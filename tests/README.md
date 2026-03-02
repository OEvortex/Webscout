# Webscout Testing Suite

This directory contains the testing suite for the Webscout project.

## 🧪 Unit Tests (Mocked)

These tests use mocks to simulate API responses and are safe to run in CI environments.

- `tests/providers/test_discovery.py`: Verifies that all providers are importable and inherit from the base `Provider` class.
- `tests/providers/test_all_mocked.py`: Tests the `ask` method of all providers using generic mocks to ensure no crashes.
- `tests/providers/test_<provider>.py`: Specific unit tests for major providers (OpenAI, Groq, Gemini, etc.).

### Running Unit Tests

```powershell
uv run pytest tests/providers/
```

## 🚀 Live Testing

The `tests/live_test.py` script provides a CLI for performing live tests against real AI providers.

### Features

- List all available providers and their models.
- Test a specific provider and model.
- Test all providers at once.
- Test all models of a specific provider.
- Support for API keys via CLI or JSON file.

### Usage

**List all providers:**
```powershell
uv run python tests/live_test.py --list
```

**Test a specific provider:**
```powershell
uv run python tests/live_test.py --provider OpenAI --api-key YOUR_KEY
```

**Test all models of a provider:**
```powershell
uv run python tests/live_test.py --provider Groq --api-key YOUR_KEY --test-models
```

**Test all providers (live):**
```powershell
uv run python tests/live_test.py --test-all --api-keys-file keys.json
```

### API Keys JSON Format
```json
{
    "OpenAI": "sk-...",
    "Groq": "gsk_...",
    "default": "some-generic-key"
}
```

## 🛠️ Utilities

- `tests/providers/utils.py`: Contains `FakeResp`, a mock response object for testing.
