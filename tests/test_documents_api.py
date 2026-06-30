from pathlib import Path
from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from document_qa.core.config import Settings
from document_qa.main import create_app


def make_pdf_bytes(text: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


def make_docx_bytes(text: str) -> bytes:
    buffer = BytesIO()
    document = Document()
    document.add_paragraph(text)
    document.save(buffer)
    return buffer.getvalue()


def install_fake_antiword(tmp_path, monkeypatch, output: str):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    antiword = bin_dir / "antiword"
    antiword.write_text(f"#!/bin/sh\nprintf '%s' '{output}'\n")
    antiword.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))


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


def test_upload_pdf_document_persists_metadata_file_chunks_and_index(tmp_path):
    client, app = make_client(tmp_path)
    content = make_pdf_bytes("PDF upload searchable content")

    response = client.post(
        "/api/documents/upload",
        files={"file": ("report.pdf", content, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "report.pdf"
    assert body["file_type"] == "pdf"
    assert body["size_bytes"] == len(content)
    stored_files = list(Path(app.state.settings.storage_dir).iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].suffix == ".pdf"
    chunks = app.state.document_repository.list_chunks(body["id"])
    assert len(chunks) == 1
    assert "PDF upload searchable content" in chunks[0].content
    results = app.state.vector_store.search("PDF searchable")
    assert len(results) == 1
    assert results[0].chunk.document_id == body["id"]


def test_upload_docx_document_persists_metadata_file_chunks_and_index(tmp_path):
    client, app = make_client(tmp_path)
    content = make_docx_bytes("DOCX upload searchable content")

    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "brief.docx",
                content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "brief.docx"
    assert body["file_type"] == "docx"
    assert body["size_bytes"] == len(content)
    stored_files = list(Path(app.state.settings.storage_dir).iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].suffix == ".docx"
    chunks = app.state.document_repository.list_chunks(body["id"])
    assert len(chunks) == 1
    assert "DOCX upload searchable content" in chunks[0].content
    results = app.state.vector_store.search("DOCX searchable")
    assert len(results) == 1
    assert results[0].chunk.document_id == body["id"]


def test_upload_doc_document_persists_metadata_file_chunks_and_index(tmp_path, monkeypatch):
    install_fake_antiword(tmp_path, monkeypatch, "DOC upload searchable content")
    client, app = make_client(tmp_path)
    content = b"legacy word bytes"

    response = client.post(
        "/api/documents/upload",
        files={"file": ("legacy.doc", content, "application/msword")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "legacy.doc"
    assert body["file_type"] == "doc"
    assert body["size_bytes"] == len(content)
    stored_files = list(Path(app.state.settings.storage_dir).iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].suffix == ".doc"
    chunks = app.state.document_repository.list_chunks(body["id"])
    assert len(chunks) == 1
    assert "DOC upload searchable content" in chunks[0].content
    results = app.state.vector_store.search("DOC searchable")
    assert len(results) == 1
    assert results[0].chunk.document_id == body["id"]


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
        files={"file": ("report.xlsx", b"spreadsheet", "application/vnd.ms-excel")},
    )

    assert response.status_code == 400
    assert "Unsupported document type" in response.json()["detail"]
    assert ".txt" in response.json()["detail"]
    assert ".md" in response.json()["detail"]
    assert ".pdf" in response.json()["detail"]
    assert ".doc" in response.json()["detail"]
    assert ".docx" in response.json()["detail"]


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


def test_delete_pdf_document_removes_metadata_file_chunks_and_index(tmp_path):
    client, app = make_client(tmp_path)
    upload_response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "report.pdf",
                make_pdf_bytes("PDF deletion searchable"),
                "application/pdf",
            )
        },
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]
    stored_file = next(Path(app.state.settings.storage_dir).iterdir())
    assert stored_file.exists()
    assert app.state.document_repository.list_chunks(document_id)
    assert app.state.vector_store.search("deletion")

    response = client.delete(f"/api/documents/{document_id}")

    assert response.status_code == 204
    assert not stored_file.exists()
    assert app.state.document_repository.get(document_id) is None
    assert app.state.document_repository.list_chunks(document_id) == []
    assert app.state.vector_store.search("deletion") == []


def test_delete_docx_document_removes_metadata_file_chunks_and_index(tmp_path):
    client, app = make_client(tmp_path)
    upload_response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "brief.docx",
                make_docx_bytes("DOCX deletion searchable"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]
    stored_file = next(Path(app.state.settings.storage_dir).iterdir())
    assert stored_file.exists()
    assert app.state.document_repository.list_chunks(document_id)
    assert app.state.vector_store.search("deletion")

    response = client.delete(f"/api/documents/{document_id}")

    assert response.status_code == 204
    assert not stored_file.exists()
    assert app.state.document_repository.get(document_id) is None
    assert app.state.document_repository.list_chunks(document_id) == []
    assert app.state.vector_store.search("deletion") == []


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


def test_chat_returns_document_grounded_answer_and_logs_it(tmp_path):
    client, app = make_client(tmp_path)
    upload_response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"FastAPI handles document uploads", "text/plain")},
    )
    assert upload_response.status_code == 201

    response = client.post(
        "/api/chat",
        json={"question": "How does FastAPI handle uploads?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("Fake answer")
    assert body["insufficient_context"] is False
    assert body["retrieved_chunk_ids"]
    assert body["log_id"]
    assert body["conversation_id"]
    logs = app.state.qa_repository.list()
    assert len(logs) == 1
    assert logs[0].question == "How does FastAPI handle uploads?"
    assert logs[0].conversation_id == body["conversation_id"]
    assert logs[0].answer == body["answer"]
    assert logs[0].retrieved_chunk_ids == body["retrieved_chunk_ids"]
    assert logs[0].insufficient_context is False
    messages_response = client.get(f"/api/conversations/{body['conversation_id']}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert [message["content"] for message in messages] == [
        "How does FastAPI handle uploads?",
        body["answer"],
    ]


def test_chat_returns_insufficient_context_when_no_chunks_match(tmp_path):
    client, app = make_client(tmp_path)

    response = client.post("/api/chat", json={"question": "What is missing?"})

    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_context"] is True
    assert "cannot answer" in body["answer"]
    assert body["retrieved_chunk_ids"] == []
    logs = app.state.qa_repository.list()
    assert len(logs) == 1
    assert logs[0].insufficient_context is True


def test_chat_reuses_conversation_for_follow_up_questions(tmp_path):
    client, _ = make_client(tmp_path)
    upload_response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"FastAPI handles document uploads", "text/plain")},
    )
    assert upload_response.status_code == 201
    first_response = client.post(
        "/api/chat",
        json={"question": "How does FastAPI handle uploads?"},
    )
    conversation_id = first_response.json()["conversation_id"]

    second_response = client.post(
        "/api/chat",
        json={
            "question": "Can you restate that?",
            "conversation_id": conversation_id,
        },
    )
    messages_response = client.get(f"/api/conversations/{conversation_id}/messages")

    assert second_response.status_code == 200
    assert second_response.json()["conversation_id"] == conversation_id
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert [message["sequence"] for message in messages] == [0, 1, 2, 3]
