from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Protocol

from document_qa.qa.models import QuestionAnswerLog


class QARepository(Protocol):
    def add(self, log: QuestionAnswerLog) -> None:
        ...

    def list(self) -> list[QuestionAnswerLog]:
        ...


class SQLiteQARepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS qa_logs (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    retrieved_chunk_ids TEXT NOT NULL,
                    insufficient_context INTEGER NOT NULL
                )
                """
            )

    def add(self, log: QuestionAnswerLog) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO qa_logs (
                    id,
                    question,
                    answer,
                    created_at,
                    retrieved_chunk_ids,
                    insufficient_context
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    log.id,
                    log.question,
                    log.answer,
                    log.created_at,
                    json.dumps(log.retrieved_chunk_ids),
                    int(log.insufficient_context),
                ),
            )

    def list(self) -> list[QuestionAnswerLog]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, question, answer, created_at, retrieved_chunk_ids, insufficient_context
                FROM qa_logs
                ORDER BY created_at ASC
                """
            ).fetchall()

        return [
            QuestionAnswerLog(
                id=row["id"],
                question=row["question"],
                answer=row["answer"],
                created_at=row["created_at"],
                retrieved_chunk_ids=json.loads(row["retrieved_chunk_ids"]),
                insufficient_context=bool(row["insufficient_context"]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
