# Document Q&A System PRD

## Problem Statement

Users need an AI-powered document question-answering system that can ingest common document formats, preserve searchable document content, and answer natural language questions accurately with support for conversational context. The system must be deliverable within a short three-day window, so it needs a focused MVP that satisfies the core requirements while keeping the architecture extensible for additional AI providers, document formats, and a Web UI.

## Solution

Build a Python-based Document Q&A System with a FastAPI backend. The MVP will support TXT and Markdown upload, parsing, storage, query, deletion, question answering over uploaded document content, multi-turn conversation history, AI provider configuration, question-answer logging, tests, Docker runtime, and project documentation.

The system will use a retrieval-augmented generation flow: parse documents into text, split text into chunks, store metadata in SQLite, index chunks in a vector store, retrieve relevant chunks for each question, and send retrieved context plus conversation history to the configured AI provider. The default implementation should support a low-friction provider path while exposing interfaces for OpenAI, Claude, and local models.

## User Stories

1. As an end user, I want to upload a TXT document, so that I can ask questions about its content.
2. As an end user, I want to upload a Markdown document, so that I can ask questions about notes, specs, or README-style files.
3. As an end user, I want unsupported file formats to be rejected clearly, so that I understand what I can upload.
4. As an end user, I want uploaded documents to be listed, so that I can see what knowledge is available in the system.
5. As an end user, I want to view document metadata such as filename, type, upload time, and size, so that I can identify uploaded files.
6. As an end user, I want to delete a document, so that outdated or incorrect content is removed from future answers.
7. As an end user, I want deleting a document to remove its searchable chunks, so that answers do not use stale content.
8. As an end user, I want to ask a natural language question, so that I can get a direct answer without manually searching the document.
9. As an end user, I want answers to be based on relevant document content, so that the response is grounded and useful.
10. As an end user, I want the answer to be coherent and readable, so that I can understand it quickly.
11. As an end user, I want the system to say when it cannot find enough supporting context, so that I do not mistake guesses for document-backed answers.
12. As an end user, I want to ask follow-up questions in the same conversation, so that I do not need to repeat previous context.
13. As an end user, I want the system to remember recent turns in a conversation, so that follow-up questions remain consistent.
14. As an end user, I want to start a new conversation, so that unrelated questions do not pollute each other.
15. As an end user, I want to retrieve conversation messages, so that I can review previous questions and answers.
16. As an operator, I want all questions and answers to be logged, so that I can analyze quality and improve prompts or retrieval.
17. As an operator, I want document upload, parsing, and deletion events to be persisted, so that the system state is auditable.
18. As an operator, I want AI provider settings to be configurable via environment variables, so that deployment does not require code changes.
19. As an operator, I want to configure OpenAI as a provider, so that I can use a hosted model quickly.
20. As an operator, I want the provider layer to support Claude or local models later, so that the system is not locked into one vendor.
21. As a developer, I want document parsing logic isolated behind a module interface, so that format support can be expanded safely.
22. As a developer, I want text chunking logic isolated and tested, so that retrieval quality can be tuned without touching API code.
23. As a developer, I want vector store operations behind a small interface, so that FAISS, Chroma, or another backend can be swapped.
24. As a developer, I want the AI provider behind a small interface, so that generation tests can use fake providers.
25. As a developer, I want database access separated from business logic, so that services are testable.
26. As a developer, I want unit tests for parsing, chunking, document management, retrieval, chat orchestration, and provider selection, so that the core behavior is protected.
27. As a developer, I want API tests for upload, list, delete, chat, and history endpoints, so that user-facing behavior is verified.
28. As a reviewer, I want a Dockerfile, so that I can build and run the project consistently.
29. As a reviewer, I want docker-compose support, so that I can run the API with minimal setup.
30. As a reviewer, I want complete README instructions, so that I can configure API keys, run tests, start the server, and try the API.
31. As a reviewer, I want architecture documentation, so that I can understand the module boundaries and data flow.
32. As a reviewer, I want interface documentation, so that I can call the system endpoints correctly.
33. As a reviewer, I want user documentation, so that I can upload documents and ask questions without reading code.
34. As an evaluator, I want a GitHub repository address, so that I can inspect the completed submission.
35. As an evaluator, I want the project to be realistic within three days, so that the delivered system is complete rather than over-scoped.
36. As an advanced user, I want optional PDF support, so that I can ask questions about common business documents.
37. As an advanced user, I want optional Word document support, so that I can use `.docx` files.
38. As an advanced user, I want an optional Web UI, so that I can upload documents and chat without using API tools.

## Implementation Decisions

- Build the backend in Python with FastAPI.
- Use SQLite for durable MVP persistence because it is simple, Docker-friendly, and sufficient for a single-node submission.
- Store document metadata, parsed text references, conversation records, messages, and question-answer logs in relational tables.
- Store uploaded source files under an application-controlled storage directory.
- Support TXT and Markdown in the MVP. PDF and Word are optional stretch goals.
- Implement a document ingestion module that validates the file type, saves the file, parses text, splits text into chunks, persists metadata, and indexes chunks.
- Implement a parser module with a stable interface such as "parse uploaded file to plain text".
- Implement a chunking module with configurable chunk size and overlap.
- Implement a vector store module with a small interface for upsert, search, and delete-by-document operations.
- Prefer a local-simple vector implementation or lightweight vector database for the MVP, while keeping the interface replaceable.
- Implement an AI provider module with a stable interface for answer generation.
- Provide at least one working provider path and one fake provider for tests.
- Configure provider choice and credentials via environment variables.
- Implement a retrieval-augmented QA service that retrieves relevant chunks, combines them with recent conversation history, calls the provider, and persists the answer.
- Include source context metadata internally so future source citation support can be added.
- Implement a conversation module that creates or reuses conversation IDs and stores ordered messages.
- Implement API endpoints for document upload, document listing, document deletion, chat, conversation history, and health checks.
- Keep the initial Web UI optional. If included, it should be a simple upload/list/chat interface rather than a separate product-scale frontend.
- Keep provider abstraction broad enough for OpenAI, Claude, and local model adapters, but do not implement every provider in the MVP unless time remains.
- Treat "cannot answer from available context" as a valid answer mode.
- Keep all generated answers and user questions in logs for later analysis.

## Testing Decisions

- Tests should verify external behavior and module contracts rather than implementation details.
- Parser tests should verify TXT and Markdown files produce expected plain text and unsupported formats fail clearly.
- Chunking tests should verify chunk size, overlap, empty input handling, and deterministic output.
- Document service tests should verify upload persistence, metadata creation, list behavior, and deletion behavior.
- Vector store tests should verify indexed chunks can be retrieved and deleted by document ID.
- QA service tests should use a fake AI provider to verify prompt context assembly, retrieval use, history inclusion, answer persistence, and insufficient-context behavior.
- Conversation tests should verify ordered message storage and conversation reuse.
- Configuration tests should verify provider selection and missing credentials behavior.
- API tests should verify upload, list, delete, chat, history, and health endpoints through FastAPI's test client.
- Docker verification should include building the image and starting the application successfully.

## Out of Scope

- Full enterprise authentication and authorization.
- Multi-tenant user management.
- Real-time collaborative editing.
- Large-scale distributed vector database deployment.
- Advanced document OCR.
- Fine-tuning custom models.
- Complex admin analytics dashboards.
- Guaranteed support for every AI provider in the first implementation.
- Production-grade observability beyond basic logs and health checks.

## Further Notes

- The best three-day delivery plan is to finish the backend MVP first, then add stretch items only after tests, Docker, and documentation are complete.
- The highest-risk areas are retrieval quality, provider integration, and time spent on optional UI. These should be kept deliberately small.
- Suggested implementation modules are: document ingestion, document parser, chunker, vector store, AI provider, QA orchestration, conversation history, persistence repositories, API routes, and optional Web UI.
- Suggested endpoint surface:
  - `POST /documents/upload`
  - `GET /documents`
  - `DELETE /documents/{document_id}`
  - `POST /chat`
  - `GET /conversations/{conversation_id}/messages`
  - `GET /health`
- Since this workspace has no configured issue tracker yet, this PRD is saved as a local deliverable and can later be published to GitHub Issues after the repository is created.
