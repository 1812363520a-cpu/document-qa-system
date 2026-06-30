from document_qa.persistence.conversations import SQLiteConversationRepository
from document_qa.qa.models import ConversationMessage


def test_sqlite_conversation_repository_stores_ordered_messages(tmp_path):
    repository = SQLiteConversationRepository(str(tmp_path / "document_qa.sqlite3"))
    repository.initialize()
    repository.create_conversation("conversation-1", "2026-06-30T00:00:00+00:00")
    repository.add_message(
        ConversationMessage(
            id="message-2",
            conversation_id="conversation-1",
            role="assistant",
            content="Second",
            created_at="2026-06-30T00:00:02+00:00",
            sequence=1,
        )
    )
    repository.add_message(
        ConversationMessage(
            id="message-1",
            conversation_id="conversation-1",
            role="user",
            content="First",
            created_at="2026-06-30T00:00:01+00:00",
            sequence=0,
        )
    )

    restarted_repository = SQLiteConversationRepository(str(tmp_path / "document_qa.sqlite3"))
    restarted_repository.initialize()

    assert restarted_repository.conversation_exists("conversation-1") is True
    assert restarted_repository.next_sequence("conversation-1") == 2
    assert [message.content for message in restarted_repository.list_messages("conversation-1")] == [
        "First",
        "Second",
    ]


def test_sqlite_conversation_repository_lists_conversation_summaries(tmp_path):
    repository = SQLiteConversationRepository(str(tmp_path / "document_qa.sqlite3"))
    repository.initialize()
    repository.create_conversation("older", "2026-06-30T00:00:00+00:00")
    repository.create_conversation("newer", "2026-06-30T00:10:00+00:00")
    repository.add_message(
        ConversationMessage(
            id="older-message",
            conversation_id="older",
            role="user",
            content="Older question",
            created_at="2026-06-30T00:00:01+00:00",
            sequence=0,
        )
    )
    repository.add_message(
        ConversationMessage(
            id="newer-message",
            conversation_id="newer",
            role="user",
            content="Newer question",
            created_at="2026-06-30T00:10:01+00:00",
            sequence=0,
        )
    )

    summaries = repository.list_conversations()

    assert [summary.id for summary in summaries] == ["newer", "older"]
    assert summaries[0].preview == "Newer question"
    assert summaries[0].message_count == 1
    assert summaries[0].last_message_at == "2026-06-30T00:10:01+00:00"
