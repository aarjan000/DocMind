from backend.app.core.config import Settings
def test_default_settings():
    settings = Settings(_env_file=None)
    assert settings.app_name == "DocMind API"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.api_prefix == "/api/v1"
def test_environment_variable_override(monkeypatch):
    monkeypatch.setenv("APP_NAME", "DocMind Test")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    settings = Settings(_env_file=None)
    assert settings.app_name == "DocMind Test"
    assert settings.debug is True
    assert settings.environment == "testing"
def test_secrets_are_wrapped():
    settings = Settings(
        _env_file=None,
        groq_api_key="test-secret",
    )
    assert settings.groq_api_key.get_secret_value() == "test-secret"
    assert "test-secret" not in repr(settings.groq_api_key)
