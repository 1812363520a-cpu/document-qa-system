from fastapi import FastAPI
from typing import Optional

from document_qa.api.routes.health import router as health_router
from document_qa.core.config import Settings, get_settings


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    app_settings = settings or get_settings()
    app = FastAPI(title=app_settings.app_name)

    app.state.settings = app_settings
    app.include_router(health_router, prefix=app_settings.api_prefix)

    return app


app = create_app()
