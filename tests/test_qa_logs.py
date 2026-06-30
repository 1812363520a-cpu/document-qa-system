from document_qa.persistence.qa_logs import SQLiteQARepository
from document_qa.qa.models import QuestionAnswerLog


def test_sqlite_qa_repository_persists_question_answer_logs(tmp_path):
    database_path = str(tmp_path / "document_qa.sqlite3")
    repository = SQLiteQARepository(database_path)
    repository.initialize()
    repository.add(
        QuestionAnswerLog(
            id="log-1",
            conversation_id="conversation-1",
            question="What is indexed?",
            answer="Indexed chunks.",
            created_at="2026-06-30T00:00:00+00:00",
            retrieved_chunk_ids=["doc-1:0"],
            insufficient_context=False,
        )
    )

    restarted_repository = SQLiteQARepository(database_path)
    restarted_repository.initialize()

    assert restarted_repository.list() == [
        QuestionAnswerLog(
            id="log-1",
            conversation_id="conversation-1",
            question="What is indexed?",
            answer="Indexed chunks.",
            created_at="2026-06-30T00:00:00+00:00",
            retrieved_chunk_ids=["doc-1:0"],
            insufficient_context=False,
        )
    ]
