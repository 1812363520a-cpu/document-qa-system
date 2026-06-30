from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from document_qa.documents.chunking import TextChunker
from document_qa.documents.models import DocumentMetadata
from document_qa.documents.parser import DocumentParseError, DocumentParser
from document_qa.persistence.documents import DocumentRepository
from document_qa.retrieval.vector_store import VectorStore


class UnsupportedDocumentTypeError(ValueError):
    pass


class DocumentIngestionError(ValueError):
    pass


class DocumentNotFoundError(ValueError):
    pass


SUPPORTED_EXTENSIONS = {
    ".txt": "txt",
    ".md": "markdown",
    ".markdown": "markdown",
    ".pdf": "pdf",
    ".doc": "doc",
    ".docx": "docx",
}


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        vector_store: VectorStore,
        storage_dir: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self.repository = repository
        self.vector_store = vector_store
        self.storage_dir = Path(storage_dir)
        self.parser = DocumentParser()
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    async def upload(self, file: UploadFile) -> DocumentMetadata:
        file_type = self._file_type_for(file.filename or "")
        content = await file.read()
        try:
            parsed_text = self.parser.parse(file_type, content)
        except DocumentParseError as exc:
            raise DocumentIngestionError(str(exc)) from exc

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        document_id = str(uuid4())
        suffix = Path(file.filename or "").suffix.lower()
        storage_path = self.storage_dir / f"{document_id}{suffix}"
        storage_path.write_bytes(content)
        chunks = self.chunker.chunk(document_id=document_id, text=parsed_text)

        document = DocumentMetadata(
            id=document_id,
            filename=file.filename or "uploaded-document",
            file_type=file_type,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            size_bytes=len(content),
            storage_path=str(storage_path),
        )
        self.repository.add(document, chunks)
        self.vector_store.upsert(chunks)
        return document

    def list_documents(self) -> list[DocumentMetadata]:
        return self.repository.list()

    def delete_document(self, document_id: str) -> None:
        document = self.repository.get(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        self.repository.delete(document_id)
        self.vector_store.delete_by_document(document_id)

        storage_path = Path(document.storage_path)
        if storage_path.exists():
            storage_path.unlink()

    def _file_type_for(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        try:
            return SUPPORTED_EXTENSIONS[suffix]
        except KeyError as exc:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type. Supported extensions: {supported}"
            ) from exc
