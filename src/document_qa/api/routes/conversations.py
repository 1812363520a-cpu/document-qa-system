from fastapi import APIRouter, Request

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/{conversation_id}/messages")
def list_conversation_messages(
    request: Request,
    conversation_id: str,
) -> list[dict[str, object]]:
    messages = request.app.state.qa_service.list_messages(conversation_id)
    return [message.to_api_dict() for message in messages]
