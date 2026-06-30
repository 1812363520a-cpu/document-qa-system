from pathlib import Path

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
    return TestClient(app), app


def test_upload_txt_document_persists_metadata_and_file(tmp_path):
    client, app = make_client(tmp_path)

    response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"hello document", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "notes.txt"
    assert body["file_type"] == "txt"
    assert body["size_bytes"] == len(b"hello document")
    assert body["uploaded_at"]

    stored_files = list(Path(app.state.settings.storage_dir).iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].suffix == ".txt"
    assert stored_files[0].read_bytes() == b"hello document"


def test_upload_markdown_document(tmp_path):
    client, _ = make_client(tmp_path)

    response = client.post(
        "/api/documents/upload",
        files={"file": ("readme.md", b"# Title\n\nBody", "text/markdown")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "readme.md"
    assert body["file_type"] == "markdown"
    assert body["size_bytes"] == len(b"# Title\n\nBody")


def test_upload_persists_parsed_chunks(tmp_path):
    client, app = make_client(tmp_path)

    response = client.post(
        "/api/documents/upload",
        files={"file": ("readme.md", b"# Title\n\nSearchable **body**", "text/markdown")},
    )

    assert response.status_code == 201
    document_id = response.json()["id"]
    chunks = app.state.document_repository.list_chunks(document_id)
    assert len(chunks) == 1
    assert chunks[0].document_id == document_id
    assert chunks[0].chunk_index == 0
    assert "Title" in chunks[0].content
    assert "Searchable body" in chunks[0].content


def test_upload_indexes_chunks_for_search(tmp_path):
    client, app = make_client(tmp_path)

    response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"retrieval uses indexed chunks", "text/plain")},
    )

    assert response.status_code == 201
    document_id = response.json()["id"]
    results = app.state.vector_store.search("indexed retrieval")
    assert len(results) == 1
    assert results[0].chunk.document_id == document_id
    assert results[0].chunk.content == "retrieval uses indexed chunks"


def test_upload_unsupported_document_type_returns_clear_error(tmp_path):
    client, _ = make_client(tmp_path)

    response = client.post(
        "/api/documents/upload",
        files={"file": ("report.pdf", b"%PDF", "application/pdf")},
    )

    assert response.status_code == 400
    assert "Unsupported document type" in response.json()["detail"]
    assert ".txt" in response.json()["detail"]
    assert ".md" in response.json()["detail"]


def test_list_documents_returns_persisted_metadata(tmp_path):
    client, _ = make_client(tmp_path)
    client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"alpha", "text/plain")},
    )
    client.post(
        "/api/documents/upload",
        files={"file": ("spec.markdown", b"beta", "text/markdown")},
    )

    restarted_client, _ = make_client(tmp_path)
    response = restarted_client.get("/api/documents")

    assert response.status_code == 200
    documents = response.json()
    assert [document["filename"] for document in documents] == [
        "notes.txt",
        "spec.markdown",
    ]
    assert [document["file_type"] for document in documents] == ["txt", "markdown"]
    assert {document["size_bytes"] for document in documents} == {5, 4}


def test_delete_document_removes_metadata_file_chunks_and_index(tmp_path):
    client, app = make_client(tmp_path)
    upload_response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"alpha searchable", "text/plain")},
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]
    stored_file = next(Path(app.state.settings.storage_dir).iterdir())
    assert stored_file.exists()
    assert app.state.document_repository.list_chunks(document_id)
    assert app.state.vector_store.search("alpha")

    response = client.delete(f"/api/documents/{document_id}")

    assert response.status_code == 204
    assert not stored_file.exists()
    assert app.state.document_repository.get(document_id) is None
    assert app.state.document_repository.list_chunks(document_id) == []
    assert app.state.vector_store.search("alpha") == []


def test_delete_missing_document_returns_404(tmp_path):
    client, _ = make_client(tmp_path)

    response = client.delete("/api/documents/missing-document")

    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]


def test_list_documents_excludes_deleted_document(tmp_path):
    client, _ = make_client(tmp_path)
    upload_response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"alpha", "text/plain")},
    )
    document_id = upload_response.json()["id"]

    delete_response = client.delete(f"/api/documents/{document_id}")
    list_response = client.get("/api/documents")

    assert delete_response.status_code == 204
    assert list_response.status_code == 200
    assert list_response.json() == []
