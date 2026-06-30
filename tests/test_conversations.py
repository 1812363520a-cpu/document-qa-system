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
