from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from document_qa.qa.provider import AIProviderError

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


@router.post("")
def ask_question(request: Request, payload: ChatRequest) -> dict[str, object]:
    try:
        response = request.app.state.qa_service.answer_question(
            payload.question,
            conversation_id=payload.conversation_id,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return response.to_api_dict()
