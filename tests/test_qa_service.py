from document_qa.documents.models import DocumentChunk
from document_qa.qa.models import ConversationMessage, QuestionAnswerLog
from document_qa.qa.provider import ProviderPrompt
from document_qa.qa.service import INSUFFICIENT_CONTEXT_ANSWER, QAService
from document_qa.retrieval.vector_store import SearchResult


class RecordingVectorStore:
    def __init__(self, results):
        self.results = results
        self.queries = []

    def search(self, query: str, limit: int = 5):
        self.queries.append((query, limit))
        return self.results


class RecordingProvider:
    def __init__(self):
        self.prompts = []

    def generate_answer(self, prompt: ProviderPrompt) -> str:
        self.prompts.append(prompt)
        return "generated answer"


class InMemoryQARepository:
    def __init__(self):
        self.logs = []

    def add(self, log: QuestionAnswerLog) -> None:
        self.logs.append(log)

    def list(self):
        return self.logs


class InMemoryConversationRepository:
    def __init__(self):
        self.conversations = set()
        self.messages = {}

    def create_conversation(self, conversation_id: str, created_at: str) -> None:
        self.conversations.add(conversation_id)
        self.messages.setdefault(conversation_id, [])

    def conversation_exists(self, conversation_id: str) -> bool:
        return conversation_id in self.conversations

    def add_message(self, message: ConversationMessage) -> None:
        self.messages.setdefault(message.conversation_id, []).append(message)

    def list_messages(self, conversation_id: str):
        return sorted(
            self.messages.get(conversation_id, []),
            key=lambda message: message.sequence,
        )

    def next_sequence(self, conversation_id: str) -> int:
        messages = self.messages.get(conversation_id, [])
        if not messages:
            return 0
        return max(message.sequence for message in messages) + 1


def test_qa_service_retrieves_context_invokes_provider_and_persists_answer():
    chunk = DocumentChunk(
        id="doc-1:0",
        document_id="doc-1",
        chunk_index=0,
        content="FastAPI handles document uploads.",
        start_char=0,
        end_char=33,
    )
    vector_store = RecordingVectorStore([SearchResult(chunk=chunk, score=0.8)])
    provider = RecordingProvider()
    repository = InMemoryQARepository()
    conversation_repository = InMemoryConversationRepository()
    service = QAService(
        vector_store=vector_store,
        provider=provider,
        repository=repository,
        conversation_repository=conversation_repository,
        retrieval_limit=3,
    )

    response = service.answer_question("How are uploads handled?")

    assert vector_store.queries == [("How are uploads handled?", 3)]
    assert len(provider.prompts) == 1
    assert provider.prompts[0].question == "How are uploads handled?"
    assert "[doc-1:0]" in provider.prompts[0].context
    assert "FastAPI handles document uploads." in provider.prompts[0].context
    assert response.answer == "generated answer"
    assert response.conversation_id
    assert response.insufficient_context is False
    assert response.retrieved_chunk_ids == ["doc-1:0"]
    assert len(repository.logs) == 1
    assert repository.logs[0].conversation_id == response.conversation_id
    assert repository.logs[0].question == "How are uploads handled?"
    assert repository.logs[0].answer == "generated answer"
    assert repository.logs[0].retrieved_chunk_ids == ["doc-1:0"]
    assert repository.logs[0].insufficient_context is False
    messages = conversation_repository.list_messages(response.conversation_id)
    assert [message.role for message in messages] == ["user", "assistant"]
    assert [message.sequence for message in messages] == [0, 1]


def test_qa_service_returns_insufficient_context_without_provider_call():
    vector_store = RecordingVectorStore([])
    provider = RecordingProvider()
    repository = InMemoryQARepository()
    conversation_repository = InMemoryConversationRepository()
    service = QAService(
        vector_store=vector_store,
        provider=provider,
        repository=repository,
        conversation_repository=conversation_repository,
    )

    response = service.answer_question("Unknown topic?")

    assert provider.prompts == []
    assert response.answer == INSUFFICIENT_CONTEXT_ANSWER
    assert response.insufficient_context is True
    assert response.retrieved_chunk_ids == []
    assert len(repository.logs) == 1
    assert repository.logs[0].insufficient_context is True


def test_qa_service_returns_insufficient_context_for_low_score_results():
    chunk = DocumentChunk(
        id="doc-1:0",
        document_id="doc-1",
        chunk_index=0,
        content="A barely related document chunk.",
        start_char=0,
        end_char=32,
    )
    vector_store = RecordingVectorStore([SearchResult(chunk=chunk, score=0.03)])
    provider = RecordingProvider()
    repository = InMemoryQARepository()
    conversation_repository = InMemoryConversationRepository()
    service = QAService(
        vector_store=vector_store,
        provider=provider,
        repository=repository,
        conversation_repository=conversation_repository,
        retrieval_min_score=0.1,
    )

    response = service.answer_question("Unrelated question?")

    assert provider.prompts == []
    assert response.answer == INSUFFICIENT_CONTEXT_ANSWER
    assert response.insufficient_context is True
    assert response.retrieved_chunk_ids == []
    assert repository.logs[0].retrieved_chunk_ids == []


def test_qa_service_keeps_moderate_score_results_by_default():
    chunk = DocumentChunk(
        id="doc-1:0",
        document_id="doc-1",
        chunk_index=0,
        content="瀑布模型：优点是容易理解，管理成本低。",
        start_char=0,
        end_char=21,
    )
    vector_store = RecordingVectorStore([SearchResult(chunk=chunk, score=0.08)])
    provider = RecordingProvider()
    repository = InMemoryQARepository()
    conversation_repository = InMemoryConversationRepository()
    service = QAService(
        vector_store=vector_store,
        provider=provider,
        repository=repository,
        conversation_repository=conversation_repository,
    )

    response = service.answer_question("瀑布模型的优点")

    assert len(provider.prompts) == 1
    assert response.insufficient_context is False
    assert response.retrieved_chunk_ids == ["doc-1:0"]


def test_qa_service_filters_low_score_results_from_prompt():
    low_score_chunk = DocumentChunk(
        id="doc-1:0",
        document_id="doc-1",
        chunk_index=0,
        content="Low confidence context.",
        start_char=0,
        end_char=23,
    )
    high_score_chunk = DocumentChunk(
        id="doc-2:0",
        document_id="doc-2",
        chunk_index=0,
        content="High confidence context.",
        start_char=0,
        end_char=24,
    )
    vector_store = RecordingVectorStore(
        [
            SearchResult(chunk=low_score_chunk, score=0.04),
            SearchResult(chunk=high_score_chunk, score=0.6),
        ]
    )
    provider = RecordingProvider()
    repository = InMemoryQARepository()
    conversation_repository = InMemoryConversationRepository()
    service = QAService(
        vector_store=vector_store,
        provider=provider,
        repository=repository,
        conversation_repository=conversation_repository,
        retrieval_min_score=0.1,
    )

    response = service.answer_question("Relevant question?")

    assert response.insufficient_context is False
    assert response.retrieved_chunk_ids == ["doc-2:0"]
    assert "High confidence context." in provider.prompts[0].context
    assert "Low confidence context." not in provider.prompts[0].context


def test_qa_service_reuses_conversation_and_includes_recent_history():
    chunk = DocumentChunk(
        id="doc-1:0",
        document_id="doc-1",
        chunk_index=0,
        content="Uploads are handled by FastAPI.",
        start_char=0,
        end_char=31,
    )
    vector_store = RecordingVectorStore([SearchResult(chunk=chunk, score=0.8)])
    provider = RecordingProvider()
    repository = InMemoryQARepository()
    conversation_repository = InMemoryConversationRepository()
    service = QAService(
        vector_store=vector_store,
        provider=provider,
        repository=repository,
        conversation_repository=conversation_repository,
    )

    first = service.answer_question("How are uploads handled?")
    second = service.answer_question("Can you repeat that?", conversation_id=first.conversation_id)

    assert second.conversation_id == first.conversation_id
    assert "Recent conversation:" in provider.prompts[1].context
    assert "user: How are uploads handled?" in provider.prompts[1].context
    assert "assistant: generated answer" in provider.prompts[1].context
    messages = conversation_repository.list_messages(first.conversation_id)
    assert [message.sequence for message in messages] == [0, 1, 2, 3]
