import sqlite3
from pathlib import Path
from typing import Protocol

from document_qa.documents.models import DocumentMetadata


class DocumentRepository(Protocol):
    def add(self, document: DocumentMetadata) -> None:
        ...

    def list(self) -> list[DocumentMetadata]:
        ...


class SQLiteDocumentRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    storage_path TEXT NOT NULL
                )
                """
            )

    def add(self, document: DocumentMetadata) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id,
                    filename,
                    file_type,
                    uploaded_at,
                    size_bytes,
                    storage_path
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.filename,
                    document.file_type,
                    document.uploaded_at,
                    document.size_bytes,
                    document.storage_path,
                ),
            )

    def list(self) -> list[DocumentMetadata]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, filename, file_type, uploaded_at, size_bytes, storage_path
                FROM documents
                ORDER BY uploaded_at ASC
                """
            ).fetchall()

        return [
            DocumentMetadata(
                id=row["id"],
                filename=row["filename"],
                file_type=row["file_type"],
                uploaded_at=row["uploaded_at"],
                size_bytes=row["size_bytes"],
                storage_path=row["storage_path"],
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
