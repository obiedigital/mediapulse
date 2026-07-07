from mediapulse.config import Settings


def test_defaults_do_not_hardcode_a_dead_model_string():
    settings = Settings(_env_file=None)
    assert settings.classify_model == "claude-sonnet-4-6"
    assert settings.synthesis_model
    assert settings.database_url.startswith("sqlite")


def test_anthropic_api_key_read_without_prefix(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-123")
    settings = Settings(_env_file=None)
    assert settings.anthropic_api_key == "sk-ant-test-123"


def test_model_overridable_via_env(monkeypatch):
    monkeypatch.setenv("MEDIAPULSE_CLASSIFY_MODEL", "claude-sonnet-4-7")
    settings = Settings(_env_file=None)
    assert settings.classify_model == "claude-sonnet-4-7"
