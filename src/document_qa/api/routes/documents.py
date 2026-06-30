from fastapi import APIRouter, HTTPException, Request, UploadFile, status

from document_qa.documents.service import (
    DocumentIngestionError,
    DocumentNotFoundError,
    UnsupportedDocumentTypeError,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(request: Request, file: UploadFile) -> dict[str, object]:
    try:
        document = await request.app.state.document_service.upload(file)
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DocumentIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return document.to_api_dict()


@router.get("")
def list_documents(request: Request) -> list[dict[str, object]]:
    documents = request.app.state.document_service.list_documents()
    return [document.to_api_dict() for document in documents]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(request: Request, document_id: str) -> None:
    try:
        request.app.state.document_service.delete_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
