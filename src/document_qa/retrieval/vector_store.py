from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from document_qa.documents.models import DocumentChunk


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    score: float


class VectorStore(Protocol):
    def upsert(self, chunks: list[DocumentChunk]) -> None:
        ...

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        ...

    def delete_by_document(self, document_id: str) -> None:
        ...


class SQLiteVectorStore:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vector_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    start_char INTEGER NOT NULL,
                    end_char INTEGER NOT NULL,
                    tokens TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_vector_chunks_document_id
                ON vector_chunks(document_id)
                """
            )

    def upsert(self, chunks: list[DocumentChunk]) -> None:
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO vector_chunks (
                    id,
                    document_id,
                    chunk_index,
                    content,
                    start_char,
                    end_char,
                    tokens
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    document_id = excluded.document_id,
                    chunk_index = excluded.chunk_index,
                    content = excluded.content,
                    start_char = excluded.start_char,
                    end_char = excluded.end_char,
                    tokens = excluded.tokens
                """,
                [
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.content,
                        chunk.start_char,
                        chunk.end_char,
                        " ".join(sorted(_tokenize(chunk.content))),
                    )
                    for chunk in chunks
                ],
            )

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        query_tokens = _tokenize(query)
        if limit <= 0 or not query_tokens:
            return []

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, document_id, chunk_index, content, start_char, end_char, tokens
                FROM vector_chunks
                """
            ).fetchall()

        results: list[SearchResult] = []
        for row in rows:
            chunk_tokens = set(row["tokens"].split())
            score = _score(query_tokens, chunk_tokens)
            if score <= 0:
                continue
            results.append(
                SearchResult(
                    chunk=DocumentChunk(
                        id=row["id"],
                        document_id=row["document_id"],
                        chunk_index=row["chunk_index"],
                        content=row["content"],
                        start_char=row["start_char"],
                        end_char=row["end_char"],
                    ),
                    score=score,
                )
            )

        return sorted(
            results,
            key=lambda result: (-result.score, result.chunk.document_id, result.chunk.chunk_index),
        )[:limit]

    def delete_by_document(self, document_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM vector_chunks WHERE document_id = ?",
                (document_id,),
            )

    def rebuild_from_chunks(self) -> None:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, document_id, chunk_index, content, start_char, end_char
                FROM document_chunks
                ORDER BY document_id ASC, chunk_index ASC
                """
            ).fetchall()

        self.upsert(
            [
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
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def _tokenize(text: str) -> set[str]:
    tokens = {token.lower() for token in re.findall(r"[a-zA-Z0-9]+", text)}
    chinese_runs = re.findall(r"[\u4e00-\u9fff]+", text)
    for run in chinese_runs:
        tokens.update(_character_ngrams(run, min_size=2, max_size=4))
    return tokens


def _character_ngrams(text: str, min_size: int, max_size: int) -> set[str]:
    grams: set[str] = set()
    for size in range(min_size, max_size + 1):
        if len(text) < size:
            continue
        for index in range(0, len(text) - size + 1):
            grams.add(text[index : index + size])
    return grams


def _score(query_tokens: set[str], chunk_tokens: set[str]) -> float:
    overlap = query_tokens.intersection(chunk_tokens)
    if not overlap:
        return 0.0
    return len(overlap) / math.sqrt(len(query_tokens) * len(chunk_tokens))
