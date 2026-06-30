from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Protocol

from document_qa.documents.models import DocumentChunk, DocumentMetadata


class DocumentRepository(Protocol):
    def add(self, document: DocumentMetadata, chunks: list[DocumentChunk]) -> None:
        ...

    def get(self, document_id: str) -> DocumentMetadata | None:
        ...

    def list(self) -> list[DocumentMetadata]:
        ...

    def list_chunks(self, document_id: str) -> list[DocumentChunk]:
        ...

    def delete(self, document_id: str) -> None:
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    start_char INTEGER NOT NULL,
                    end_char INTEGER NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
                ON document_chunks(document_id)
                """
            )

    def add(self, document: DocumentMetadata, chunks: list[DocumentChunk]) -> None:
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
            connection.executemany(
                """
                INSERT INTO document_chunks (
                    id,
                    document_id,
                    chunk_index,
                    content,
                    start_char,
                    end_char
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.content,
                        chunk.start_char,
                        chunk.end_char,
                    )
                    for chunk in chunks
                ],
            )

    def get(self, document_id: str) -> DocumentMetadata | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, filename, file_type, uploaded_at, size_bytes, storage_path
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()

        if row is None:
            return None
        return self._document_from_row(row)

    def list(self) -> list[DocumentMetadata]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, filename, file_type, uploaded_at, size_bytes, storage_path
                FROM documents
                ORDER BY uploaded_at ASC
                """
            ).fetchall()

        return [self._document_from_row(row) for row in rows]

    def list_chunks(self, document_id: str) -> list[DocumentChunk]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, document_id, chunk_index, content, start_char, end_char
                FROM document_chunks
                WHERE document_id = ?
                ORDER BY chunk_index ASC
                """,
                (document_id,),
            ).fetchall()

        return [
            DocumentChunk(
                id=row["id"],
                document_id=row["document_id"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                start_char=row["start_char"],
                end_char=row["end_char"],
            )
            for row in rows
        ]

    def delete(self, document_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM document_chunks WHERE document_id = ?",
                (document_id,),
            )
            connection.execute(
                "DELETE FROM documents WHERE id = ?",
                (document_id,),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _document_from_row(self, row: sqlite3.Row) -> DocumentMetadata:
        return DocumentMetadata(
            id=row["id"],
            filename=row["filename"],
            file_type=row["file_type"],
            uploaded_at=row["uploaded_at"],
            size_bytes=row["size_bytes"],
            storage_path=row["storage_path"],
        )
