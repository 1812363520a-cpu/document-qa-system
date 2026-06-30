from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionAnswerLog:
    id: str
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

    def to_api_dict(self) -> dict[str, object]:
        return {
            "answer": self.answer,
            "insufficient_context": self.insufficient_context,
            "retrieved_chunk_ids": self.retrieved_chunk_ids,
            "log_id": self.log_id,
        }
