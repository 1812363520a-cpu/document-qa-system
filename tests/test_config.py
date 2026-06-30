from document_qa.core.config import get_settings


def test_settings_load_local_defaults(monkeypatch):
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("API_PREFIX", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.app_name == "Document Q&A System"
    assert settings.app_env == "local"
    assert settings.api_prefix == "/api"
    assert settings.log_level == "INFO"


def test_settings_load_environment_overrides(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Test Docs")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("API_PREFIX", "v1")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.app_name == "Test Docs"
    assert settings.app_env == "test"
    assert settings.api_prefix == "/v1"
    assert settings.log_level == "DEBUG"
