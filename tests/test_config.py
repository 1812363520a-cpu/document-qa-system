from document_qa.core.config import get_settings


def test_settings_load_local_defaults(monkeypatch):
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("API_PREFIX", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("STORAGE_DIR", raising=False)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.delenv("CHUNK_SIZE", raising=False)
    monkeypatch.delenv("CHUNK_OVERLAP", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.app_name == "Document Q&A System"
    assert settings.app_env == "local"
    assert settings.api_prefix == "/api"
    assert settings.log_level == "INFO"
    assert settings.storage_dir == ".data/uploads"
    assert settings.database_path == ".data/document_qa.sqlite3"
    assert settings.chunk_size == 1000
    assert settings.chunk_overlap == 200
    assert settings.ai_provider == "fake"
    assert settings.openai_api_key is None
    assert settings.openai_model == "gpt-4o-mini"


def test_settings_load_environment_overrides(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Test Docs")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("API_PREFIX", "v1")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("STORAGE_DIR", "/tmp/uploads")
    monkeypatch.setenv("DATABASE_PATH", "/tmp/document_qa.sqlite3")
    monkeypatch.setenv("CHUNK_SIZE", "256")
    monkeypatch.setenv("CHUNK_OVERLAP", "32")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.app_name == "Test Docs"
    assert settings.app_env == "test"
    assert settings.api_prefix == "/v1"
    assert settings.log_level == "DEBUG"
    assert settings.storage_dir == "/tmp/uploads"
    assert settings.database_path == "/tmp/document_qa.sqlite3"
    assert settings.chunk_size == 256
    assert settings.chunk_overlap == 32
    assert settings.ai_provider == "openai"
    assert settings.openai_api_key == "test-key"
    assert settings.openai_model == "test-model"
