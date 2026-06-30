from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionAnswerLog:
    id: str
    conversation_id: str
    question: str
    answer: str
    created_at: str
    retrieved_chunk_ids: list[str]
    insufficient_context: bool


@dataclass(frozen=True)
class QAResponse:
    answer: str
    insufficient_context: bool
    retrieved_chunk_ids: list[str]
    log_id: str
    conversation_id: str

    def to_api_dict(self) -> dict[str, object]:
        return {
            "answer": self.answer,
            "insufficient_context": self.insufficient_context,
            "retrieved_chunk_ids": self.retrieved_chunk_ids,
            "log_id": self.log_id,
            "conversation_id": self.conversation_id,
        }


@dataclass(frozen=True)
class ConversationSummary:
    id: str
    created_at: str
    last_message_at: str
    message_count: int
    preview: str

    def to_api_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "last_message_at": self.last_message_at,
            "message_count": self.message_count,
            "preview": self.preview,
        }


@dataclass(frozen=True)
class ConversationMessage:
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str
    sequence: int

    def to_api_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
            "sequence": self.sequence,
        }
