from webscout.Provider.Deepinfra import DeepInfra as NativeDeepInfra
from webscout.Provider.OPENAI.deepinfra import DeepInfra


def test_openai_get_models_returns_list():
    models = DeepInfra.get_models(api_key=None)
    assert isinstance(models, list)
    assert len(models) > 0
    # Check for a known default model
    assert any("Kimi-K2" in m or "DeepSeek" in m or "Qwen" in m for m in models)


def test_openai_init_updates_models_and_models_property():
    client = DeepInfra()
    model_list = client.models.list()
    assert isinstance(model_list, list)
    assert len(model_list) > 0


def test_native_provider_get_models():
    models = NativeDeepInfra.get_models(api_key=None)
    assert isinstance(models, list)
    assert len(models) > 0
