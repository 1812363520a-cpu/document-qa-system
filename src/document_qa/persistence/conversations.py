from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Protocol

from document_qa.qa.models import ConversationMessage, ConversationSummary


class ConversationRepository(Protocol):
    def create_conversation(self, conversation_id: str, created_at: str) -> None:
        ...

    def conversation_exists(self, conversation_id: str) -> bool:
        ...

    def add_message(self, message: ConversationMessage) -> None:
        ...

    def list_messages(self, conversation_id: str) -> list[ConversationMessage]:
        ...

    def list_conversations(self) -> list[ConversationSummary]:
        ...

    def next_sequence(self, conversation_id: str) -> int:
        ...


class SQLiteConversationRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id
                ON conversation_messages(conversation_id, sequence)
                """
            )

    def create_conversation(self, conversation_id: str, created_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO conversations (id, created_at)
                VALUES (?, ?)
                """,
                (conversation_id, created_at),
            )

    def conversation_exists(self, conversation_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
        return row is not None

    def add_message(self, message: ConversationMessage) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_messages (
                    id,
                    conversation_id,
                    role,
                    content,
                    created_at,
                    sequence
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.conversation_id,
                    message.role,
                    message.content,
                    message.created_at,
                    message.sequence,
                ),
            )

    def list_messages(self, conversation_id: str) -> list[ConversationMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, conversation_id, role, content, created_at, sequence
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY sequence ASC
                """,
                (conversation_id,),
            ).fetchall()

        return [
            ConversationMessage(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
                sequence=row["sequence"],
            )
            for row in rows
        ]

    def list_conversations(self) -> list[ConversationSummary]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    c.id,
                    c.created_at,
                    COALESCE(MAX(m.created_at), c.created_at) AS last_message_at,
                    COUNT(m.id) AS message_count,
                    COALESCE(
                        (
                            SELECT cm.content
                            FROM conversation_messages cm
                            WHERE cm.conversation_id = c.id
                            ORDER BY cm.sequence ASC
                            LIMIT 1
                        ),
                        ''
                    ) AS preview
                FROM conversations c
                LEFT JOIN conversation_messages m ON m.conversation_id = c.id
                GROUP BY c.id, c.created_at
                ORDER BY last_message_at DESC
                """
            ).fetchall()

        return [
            ConversationSummary(
                id=row["id"],
                created_at=row["created_at"],
                last_message_at=row["last_message_at"],
                message_count=row["message_count"],
                preview=row["preview"],
            )
            for row in rows
        ]

    def next_sequence(self, conversation_id: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(MAX(sequence), -1) + 1 AS next_sequence
                FROM conversation_messages
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()
        return int(row["next_sequence"])

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
