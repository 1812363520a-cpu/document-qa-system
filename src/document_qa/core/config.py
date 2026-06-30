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
    max_upload_bytes: int = 20 * 1024 * 1024
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_min_score: float = 0.015
    ai_provider: str = "fake"
    ai_request_timeout_seconds: float = 30.0
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com"
    openai_compatible_api_key: Optional[str] = None
    openai_compatible_model: str = "gpt-4o-mini"
    openai_compatible_base_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-latest"
    anthropic_base_url: str = "https://api.anthropic.com"
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"


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
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", Settings.max_upload_bytes)),
        chunk_size=int(os.getenv("CHUNK_SIZE", Settings.chunk_size)),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", Settings.chunk_overlap)),
        retrieval_min_score=float(
            os.getenv("RETRIEVAL_MIN_SCORE", Settings.retrieval_min_score)
        ),
        ai_provider=os.getenv("AI_PROVIDER", Settings.ai_provider),
        ai_request_timeout_seconds=float(
            os.getenv(
                "AI_REQUEST_TIMEOUT_SECONDS",
                Settings.ai_request_timeout_seconds,
            )
        ),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", Settings.openai_model),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY") or None,
        deepseek_model=os.getenv("DEEPSEEK_MODEL", Settings.deepseek_model),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", Settings.deepseek_base_url),
        openai_compatible_api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY") or None,
        openai_compatible_model=os.getenv(
            "OPENAI_COMPATIBLE_MODEL",
            Settings.openai_compatible_model,
        ),
        openai_compatible_base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL") or None,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        anthropic_model=os.getenv("ANTHROPIC_MODEL", Settings.anthropic_model),
        anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", Settings.anthropic_base_url),
        ollama_model=os.getenv("OLLAMA_MODEL", Settings.ollama_model),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", Settings.ollama_base_url),
    )
