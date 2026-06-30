from pydantic import BaseModel
from fastapi import APIRouter, Request

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("")
def ask_question(request: Request, payload: ChatRequest) -> dict[str, object]:
    response = request.app.state.qa_service.answer_question(payload.question)
    return response.to_api_dict()
