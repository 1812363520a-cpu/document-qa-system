# document-qa-system

AI document question-answering system.

## Development

Create a virtual environment and install the project with development dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

Start the API locally:

```bash
uvicorn document_qa.main:app --reload
```

The health check is available at:

```text
GET /api/health
```

The first document endpoints are:

```text
POST /api/documents/upload
GET /api/documents
DELETE /api/documents/{document_id}
POST /api/chat
```

Uploaded TXT and Markdown documents are parsed into plain text and split into persisted chunks during ingestion.
Chunks are also indexed in the local SQLite-backed retrieval store for MVP search.
The chat endpoint retrieves relevant chunks, calls the configured provider, and logs each question and answer.

Configuration is loaded from environment variables. See `.env.example` for the current local defaults, including storage, database, and chunking settings.
