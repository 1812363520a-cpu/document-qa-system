import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass(frozen=True)
class Settings:
    app_name: str = "Document Q&A System"
    app_env: str = "local"
    api_prefix: str = "/api"
    log_level: str = "INFO"
    storage_dir: str = ".data/uploads"
    database_path: str = ".data/document_qa.sqlite3"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    ai_provider: str = "fake"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com"


def _normalized_api_prefix(value: str) -> str:
    prefix = value.strip() or "/api"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return prefix.rstrip("/") or "/"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", Settings.app_name),
        app_env=os.getenv("APP_ENV", Settings.app_env),
        api_prefix=_normalized_api_prefix(os.getenv("API_PREFIX", Settings.api_prefix)),
        log_level=os.getenv("LOG_LEVEL", Settings.log_level),
        storage_dir=os.getenv("STORAGE_DIR", Settings.storage_dir),
        database_path=os.getenv("DATABASE_PATH", Settings.database_path),
        chunk_size=int(os.getenv("CHUNK_SIZE", Settings.chunk_size)),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", Settings.chunk_overlap)),
        ai_provider=os.getenv("AI_PROVIDER", Settings.ai_provider),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", Settings.openai_model),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY") or None,
        deepseek_model=os.getenv("DEEPSEEK_MODEL", Settings.deepseek_model),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", Settings.deepseek_base_url),
    )
