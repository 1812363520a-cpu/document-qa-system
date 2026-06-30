from datetime import datetime, timezone
from uuid import uuid4

from document_qa.persistence.qa_logs import QARepository
from document_qa.qa.models import QAResponse, QuestionAnswerLog
from document_qa.qa.provider import AIProvider, ProviderPrompt
from document_qa.retrieval.vector_store import SearchResult, VectorStore


INSUFFICIENT_CONTEXT_ANSWER = (
    "I cannot answer from the available document context. Upload or index a relevant "
    "document and try again."
)


class QAService:
    def __init__(
        self,
        vector_store: VectorStore,
        provider: AIProvider,
        repository: QARepository,
        retrieval_limit: int = 5,
    ) -> None:
        self.vector_store = vector_store
        self.provider = provider
        self.repository = repository
        self.retrieval_limit = retrieval_limit

    def answer_question(self, question: str) -> QAResponse:
        normalized_question = question.strip()
        retrieved = self.vector_store.search(normalized_question, limit=self.retrieval_limit)

        if not normalized_question or not retrieved:
            return self._persist_response(
                question=normalized_question,
                answer=INSUFFICIENT_CONTEXT_ANSWER,
                retrieved=[],
                insufficient_context=True,
            )

        prompt = ProviderPrompt(
            question=normalized_question,
            context=self._build_context(retrieved),
        )
        answer = self.provider.generate_answer(prompt)
        return self._persist_response(
            question=normalized_question,
            answer=answer,
            retrieved=retrieved,
            insufficient_context=False,
        )

    def _build_context(self, retrieved: list[SearchResult]) -> str:
        return "\n\n".join(
            f"[{result.chunk.id}]\n{result.chunk.content}" for result in retrieved
        )

    def _persist_response(
        self,
        question: str,
        answer: str,
        retrieved: list[SearchResult],
        insufficient_context: bool,
    ) -> QAResponse:
        log = QuestionAnswerLog(
            id=str(uuid4()),
            question=question,
            answer=answer,
            created_at=datetime.now(timezone.utc).isoformat(),
            retrieved_chunk_ids=[result.chunk.id for result in retrieved],
            insufficient_context=insufficient_context,
        )
        self.repository.add(log)
        return QAResponse(
            answer=answer,
            insufficient_context=insufficient_context,
            retrieved_chunk_ids=log.retrieved_chunk_ids,
            log_id=log.id,
        )
