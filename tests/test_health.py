from fastapi.testclient import TestClient

from document_qa.core.config import Settings
from document_qa.main import create_app


def test_health_endpoint_returns_service_status():
    app = create_app(
        Settings(
            app_name="Document Q&A Test",
            app_env="test",
            api_prefix="/api",
        )
    )
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Document Q&A Test",
        "environment": "test",
    }
