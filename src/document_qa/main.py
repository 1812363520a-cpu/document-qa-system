from fastapi import FastAPI
from typing import Optional

from document_qa.api.routes.documents import router as documents_router
from document_qa.api.routes.health import router as health_router
from document_qa.core.config import Settings, get_settings
from document_qa.documents.service import DocumentService
from document_qa.persistence.documents import SQLiteDocumentRepository
from document_qa.retrieval.vector_store import SQLiteVectorStore


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    app_settings = settings or get_settings()
    app = FastAPI(title=app_settings.app_name)

    app.state.settings = app_settings
    app.state.document_repository = SQLiteDocumentRepository(app_settings.database_path)
    app.state.document_repository.initialize()
    app.state.vector_store = SQLiteVectorStore(app_settings.database_path)
    app.state.vector_store.initialize()
    app.state.document_service = DocumentService(
        repository=app.state.document_repository,
        vector_store=app.state.vector_store,
        storage_dir=app_settings.storage_dir,
        chunk_size=app_settings.chunk_size,
        chunk_overlap=app_settings.chunk_overlap,
    )
    app.include_router(health_router, prefix=app_settings.api_prefix)
    app.include_router(documents_router, prefix=app_settings.api_prefix)

    return app


app = create_app()
