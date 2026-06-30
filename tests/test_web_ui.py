from fastapi.testclient import TestClient

from document_qa.core.config import Settings
from document_qa.main import create_app


def make_client(tmp_path):
    app = create_app(
        Settings(
            app_name="Document Q&A Test",
            app_env="test",
            api_prefix="/api",
            storage_dir=str(tmp_path / "uploads"),
            database_path=str(tmp_path / "document_qa.sqlite3"),
        )
    )
    return TestClient(app)


def test_web_ui_root_serves_index(tmp_path):
    client = make_client(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert "Document Q&A" in response.text
    assert "/assets/app.js" in response.text
    assert 'id="sendButton"' in response.text
    assert 'id="documentSearch"' in response.text
    assert 'id="conversationList"' in response.text
    assert 'id="refreshConversations"' in response.text


def test_web_ui_static_assets_are_served(tmp_path):
    client = make_client(tmp_path)

    script_response = client.get("/assets/app.js")
    style_response = client.get("/assets/styles.css")

    assert script_response.status_code == 200
    assert "loadDocuments" in script_response.text
    assert "filteredDocuments" in script_response.text
    assert "confirmDeleteDocument" in script_response.text
    assert "window.confirm" in script_response.text
    assert "loadConversations" in script_response.text
    assert "selectConversation" in script_response.text
    assert "renderMarkdown" in script_response.text
    assert "renderInlineMarkdown" in script_response.text
    assert "setChatLoading" in script_response.text
    assert "AI is thinking" in script_response.text
    assert style_response.status_code == 200
    assert ".layout-grid" in style_response.text
    assert ".search-input" in style_response.text
    assert ".empty-list-item" in style_response.text
    assert ".conversation-item" in style_response.text
    assert ".bubble-content strong" in style_response.text
    assert ".inline-spinner" in style_response.text
    assert "text-overflow: ellipsis" in style_response.text
