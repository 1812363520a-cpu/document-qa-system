# API Reference

The default API prefix is `/api`.

## Health

```http
GET /api/health
```

Returns service status, service name, and environment.

## Upload Document

```http
POST /api/documents/upload
Content-Type: multipart/form-data
```

Form fields:

- `file`: `.txt`, `.md`, `.markdown`, or `.pdf` file.

Returns document metadata:

```json
{
  "id": "document-id",
  "filename": "notes.txt",
  "file_type": "txt",
  "uploaded_at": "2026-06-30T00:00:00+00:00",
  "size_bytes": 123
}
```

Unsupported formats return `400`.

## List Documents

```http
GET /api/documents
```

Returns an array of document metadata.

## Delete Document

```http
DELETE /api/documents/{document_id}
```

Returns `204` when the document is deleted. Missing documents return `404`.

## Ask A Question

```http
POST /api/chat
Content-Type: application/json
```

Body:

```json
{
  "question": "What does the document say about FastAPI?",
  "conversation_id": "optional-existing-conversation-id"
}
```

Returns:

```json
{
  "answer": "Answer text",
  "insufficient_context": false,
  "retrieved_chunk_ids": ["document-id:0"],
  "log_id": "qa-log-id",
  "conversation_id": "conversation-id"
}
```

If no relevant chunks are found, `insufficient_context` is `true` and the answer explains that the system cannot answer from available document context.

## Conversation Messages

```http
GET /api/conversations/{conversation_id}/messages
```

Returns ordered conversation messages:

```json
[
  {
    "id": "message-id",
    "conversation_id": "conversation-id",
    "role": "user",
    "content": "Question text",
    "created_at": "2026-06-30T00:00:00+00:00",
    "sequence": 0
  }
]
```
