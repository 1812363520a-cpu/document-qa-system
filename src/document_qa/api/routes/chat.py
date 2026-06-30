from typing import Optional

from pydantic import BaseModel
from fastapi import APIRouter, Request

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


@router.post("")
def ask_question(request: Request, payload: ChatRequest) -> dict[str, object]:
    response = request.app.state.qa_service.answer_question(
        payload.question,
        conversation_id=payload.conversation_id,
    )
    return response.to_api_dict()
