from fastapi import FastAPI
from typing import Optional

from document_qa.api.routes.chat import router as chat_router
from document_qa.api.routes.conversations import router as conversations_router
from document_qa.api.routes.documents import router as documents_router
from document_qa.api.routes.health import router as health_router
from document_qa.core.config import Settings, get_settings
from document_qa.documents.service import DocumentService
from document_qa.persistence.conversations import SQLiteConversationRepository
from document_qa.persistence.documents import SQLiteDocumentRepository
from document_qa.persistence.qa_logs import SQLiteQARepository
from document_qa.qa.provider import FakeAIProvider
from document_qa.qa.service import QAService
from document_qa.retrieval.vector_store import SQLiteVectorStore


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    app_settings = settings or get_settings()
    app = FastAPI(title=app_settings.app_name)

    app.state.settings = app_settings
    app.state.document_repository = SQLiteDocumentRepository(app_settings.database_path)
    app.state.document_repository.initialize()
    app.state.vector_store = SQLiteVectorStore(app_settings.database_path)
    app.state.vector_store.initialize()
    app.state.qa_repository = SQLiteQARepository(app_settings.database_path)
    app.state.qa_repository.initialize()
    app.state.conversation_repository = SQLiteConversationRepository(app_settings.database_path)
    app.state.conversation_repository.initialize()
    app.state.document_service = DocumentService(
        repository=app.state.document_repository,
        vector_store=app.state.vector_store,
        storage_dir=app_settings.storage_dir,
        chunk_size=app_settings.chunk_size,
        chunk_overlap=app_settings.chunk_overlap,
    )
    app.state.qa_service = QAService(
        vector_store=app.state.vector_store,
        provider=FakeAIProvider(),
        repository=app.state.qa_repository,
        conversation_repository=app.state.conversation_repository,
    )
    app.include_router(health_router, prefix=app_settings.api_prefix)
    app.include_router(documents_router, prefix=app_settings.api_prefix)
    app.include_router(chat_router, prefix=app_settings.api_prefix)
    app.include_router(conversations_router, prefix=app_settings.api_prefix)

    return app


app = create_app()
