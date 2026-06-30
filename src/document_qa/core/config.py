import os
from dataclasses import dataclass
from functools import lru_cache


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
    )
