# User Guide

## Start The API

With Docker:

```bash
docker compose up --build
```

Locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn document_qa.main:app --reload
```

The API listens on `http://localhost:8000` by default.

## Use The Web UI

Open `http://localhost:8000/` after starting the app. The page lets you upload supported documents, refresh or delete the document list, start a new conversation, and ask document-grounded questions.

## Upload A Document

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@README.md"
```

Supported formats are TXT, Markdown, PDF, and Word `.doc`/`.docx`.

## List Documents

```bash
curl http://localhost:8000/api/documents
```

Copy the `id` from a listed document when you need to delete it.

## Ask A Question

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this project about?"}'
```

The response includes a `conversation_id`. Use it for follow-up questions:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Can you summarize that again?","conversation_id":"PASTE_CONVERSATION_ID"}'
```

## Review Conversation History

```bash
curl http://localhost:8000/api/conversations/PASTE_CONVERSATION_ID/messages
```

## Delete A Document

```bash
curl -X DELETE http://localhost:8000/api/documents/PASTE_DOCUMENT_ID
```

Deletion removes the stored source file, document metadata, persisted chunks, and retrieval index entries.

## Use OpenAI

The default provider is `fake`, which is deterministic and useful for local verification. To use OpenAI:

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-4o-mini
uvicorn document_qa.main:app --reload
```

For Docker Compose:

```bash
AI_PROVIDER=openai OPENAI_API_KEY=your-api-key docker compose up --build
```

## Use DeepSeek

DeepSeek is supported through its OpenAI-compatible chat completions API. To use DeepSeek locally:

```bash
export AI_PROVIDER=deepseek
export DEEPSEEK_API_KEY=your-api-key
export DEEPSEEK_MODEL=deepseek-v4-flash
uvicorn document_qa.main:app --reload
```

For Docker Compose:

```bash
AI_PROVIDER=deepseek DEEPSEEK_API_KEY=your-api-key docker compose up --build
```

The default DeepSeek base URL is `https://api.deepseek.com`. Override `DEEPSEEK_BASE_URL` only if you need a compatible proxy or custom endpoint.
