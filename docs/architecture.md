# Architecture

The Document Q&A System is a FastAPI backend that ingests supported documents, stores metadata and chunks in SQLite, indexes chunks for local retrieval, and answers questions with a configurable AI provider.

## Runtime flow

1. A client uploads a TXT or Markdown file through `POST /api/documents/upload`.
2. The document service validates the extension, stores the source file, parses the file to plain text, chunks the text, persists document metadata and chunks, and indexes chunks in the retrieval store.
3. A client asks a question through `POST /api/chat`.
4. The QA service retrieves relevant chunks, loads recent conversation messages, builds provider context, calls the configured provider, persists the QA log, stores conversation messages, and returns the answer.
5. A client can review history through `GET /api/conversations/{conversation_id}/messages`.
6. Deleting a document removes metadata, source file, persisted chunks, and indexed chunks.

## Module boundaries

- `document_qa.api.routes`: FastAPI route definitions and request/response wiring.
- `document_qa.core.config`: Environment-backed runtime configuration.
- `document_qa.documents`: Upload validation, parsing, chunking, document metadata models, and ingestion orchestration.
- `document_qa.persistence`: SQLite adapters for documents, QA logs, and conversations.
- `document_qa.retrieval`: Replaceable retrieval/vector-store boundary. The MVP implementation is SQLite-backed token-overlap search.
- `document_qa.qa`: Question-answer orchestration, provider interface, fake provider, OpenAI provider, response models, and conversation context assembly.

## Persistence

SQLite is used for the MVP:

- `documents`: uploaded document metadata.
- `document_chunks`: parsed and chunked text.
- `vector_chunks`: local retrieval index.
- `qa_logs`: question-answer logs.
- `conversations`: conversation records.
- `conversation_messages`: ordered user and assistant messages.

Uploaded source files are stored under `STORAGE_DIR`.

## Provider configuration

The default provider is `fake`, which is deterministic and suitable for local testing. Set `AI_PROVIDER=openai`, `OPENAI_API_KEY`, and optionally `OPENAI_MODEL` to use the OpenAI provider.
