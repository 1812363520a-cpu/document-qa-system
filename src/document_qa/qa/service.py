from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from document_qa.persistence.conversations import ConversationRepository
from document_qa.persistence.qa_logs import QARepository
from document_qa.qa.models import (
    ConversationMessage,
    ConversationSummary,
    QAResponse,
    QuestionAnswerLog,
)
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
        conversation_repository: ConversationRepository,
        retrieval_limit: int = 5,
        retrieval_min_score: float = 0.015,
        history_limit: int = 20,
    ) -> None:
        self.vector_store = vector_store
        self.provider = provider
        self.repository = repository
        self.conversation_repository = conversation_repository
        self.retrieval_limit = retrieval_limit
        self.retrieval_min_score = retrieval_min_score
        self.history_limit = history_limit

    def answer_question(
        self,
        question: str,
        conversation_id: Optional[str] = None,
    ) -> QAResponse:
        normalized_question = question.strip()
        active_conversation_id = self._ensure_conversation(conversation_id)
        history = self._recent_history(active_conversation_id)
        retrieved = self._filter_relevant_results(
            self.vector_store.search(normalized_question, limit=self.retrieval_limit)
        )

        if not normalized_question or not retrieved:
            return self._persist_response(
                conversation_id=active_conversation_id,
                question=normalized_question,
                answer=INSUFFICIENT_CONTEXT_ANSWER,
                retrieved=[],
                insufficient_context=True,
            )

        prompt = ProviderPrompt(
            question=normalized_question,
            context=self._build_context(retrieved, history),
        )
        answer = self.provider.generate_answer(prompt)
        return self._persist_response(
            conversation_id=active_conversation_id,
            question=normalized_question,
            answer=answer,
            retrieved=retrieved,
            insufficient_context=False,
        )

    def _filter_relevant_results(self, results: list[SearchResult]) -> list[SearchResult]:
        return [
            result
            for result in results
            if result.score >= self.retrieval_min_score
        ]

    def _build_context(
        self,
        retrieved: list[SearchResult],
        history: list[ConversationMessage],
    ) -> str:
        sections = []
        if history:
            history_text = "\n".join(
                f"{message.role}: {message.content}" for message in history
            )
            sections.append(f"Recent conversation:\n{history_text}")
        document_context = "\n\n".join(
            f"[{result.chunk.id}]\n{result.chunk.content}" for result in retrieved
        )
        sections.append(f"Document context:\n{document_context}")
        return "\n\n".join(sections)

    def _persist_response(
        self,
        conversation_id: str,
        question: str,
        answer: str,
        retrieved: list[SearchResult],
        insufficient_context: bool,
    ) -> QAResponse:
        log = QuestionAnswerLog(
            id=str(uuid4()),
            conversation_id=conversation_id,
            question=question,
            answer=answer,
            created_at=datetime.now(timezone.utc).isoformat(),
            retrieved_chunk_ids=[result.chunk.id for result in retrieved],
            insufficient_context=insufficient_context,
        )
        self.repository.add(log)
        next_sequence = self.conversation_repository.next_sequence(conversation_id)
        self._add_message(
            conversation_id=conversation_id,
            role="user",
            content=question,
            sequence=next_sequence,
        )
        self._add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            sequence=next_sequence + 1,
        )
        return QAResponse(
            answer=answer,
            insufficient_context=insufficient_context,
            retrieved_chunk_ids=log.retrieved_chunk_ids,
            log_id=log.id,
            conversation_id=conversation_id,
        )

    def list_messages(self, conversation_id: str) -> list[ConversationMessage]:
        return self.conversation_repository.list_messages(conversation_id)

    def list_conversations(self) -> list[ConversationSummary]:
        return self.conversation_repository.list_conversations()

    def _ensure_conversation(self, conversation_id: Optional[str]) -> str:
        active_conversation_id = conversation_id or str(uuid4())
        if not self.conversation_repository.conversation_exists(active_conversation_id):
            self.conversation_repository.create_conversation(
                active_conversation_id,
                datetime.now(timezone.utc).isoformat(),
            )
        return active_conversation_id

    def _recent_history(self, conversation_id: str) -> list[ConversationMessage]:
        messages = self.conversation_repository.list_messages(conversation_id)
        return messages[-self.history_limit :]

    def _add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sequence: int,
    ) -> None:
        self.conversation_repository.add_message(
            ConversationMessage(
                id=str(uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                created_at=datetime.now(timezone.utc).isoformat(),
                sequence=sequence,
            )
        )
