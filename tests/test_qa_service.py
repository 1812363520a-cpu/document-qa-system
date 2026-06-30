from document_qa.documents.models import DocumentChunk
from document_qa.qa.models import QuestionAnswerLog
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
    service = QAService(
        vector_store=vector_store,
        provider=provider,
        repository=repository,
        retrieval_limit=3,
    )

    response = service.answer_question("How are uploads handled?")

    assert vector_store.queries == [("How are uploads handled?", 3)]
    assert len(provider.prompts) == 1
    assert provider.prompts[0].question == "How are uploads handled?"
    assert "[doc-1:0]" in provider.prompts[0].context
    assert "FastAPI handles document uploads." in provider.prompts[0].context
    assert response.answer == "generated answer"
    assert response.insufficient_context is False
    assert response.retrieved_chunk_ids == ["doc-1:0"]
    assert len(repository.logs) == 1
    assert repository.logs[0].question == "How are uploads handled?"
    assert repository.logs[0].answer == "generated answer"
    assert repository.logs[0].retrieved_chunk_ids == ["doc-1:0"]
    assert repository.logs[0].insufficient_context is False


def test_qa_service_returns_insufficient_context_without_provider_call():
    vector_store = RecordingVectorStore([])
    provider = RecordingProvider()
    repository = InMemoryQARepository()
    service = QAService(
        vector_store=vector_store,
        provider=provider,
        repository=repository,
    )

    response = service.answer_question("Unknown topic?")

    assert provider.prompts == []
    assert response.answer == INSUFFICIENT_CONTEXT_ANSWER
    assert response.insufficient_context is True
    assert response.retrieved_chunk_ids == []
    assert len(repository.logs) == 1
    assert repository.logs[0].insufficient_context is True
