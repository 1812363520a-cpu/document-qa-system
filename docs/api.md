# API Reference

The default API prefix is `/api`. Change it with `API_PREFIX`.

Base URL in local Docker development:

```text
http://localhost:8000
```

## Error Format

FastAPI returns errors with a `detail` field:

```json
{
  "detail": "Error message"
}
```

Common status codes:

| Status | Meaning |
| --- | --- |
| `400` | Unsupported or unparseable document |
| `404` | Document not found |
| `413` | Uploaded file exceeds `MAX_UPLOAD_BYTES` |
| `422` | Invalid request body or missing required field |
| `503` | AI provider request failed |

## Health

```http
GET /api/health
```

Returns service status, service name, and environment.

Example response:

```json
{
  "status": "ok",
  "service": "Document Q&A System",
  "environment": "docker"
}
```

## Upload Document

```http
POST /api/documents/upload
Content-Type: multipart/form-data
```

Form fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | file | Yes | `.txt`, `.md`, `.markdown`, `.pdf`, `.doc`, or `.docx` file |

Example:

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@README.md"
```

Success response: `201 Created`

```json
{
  "id": "a-document-id",
  "filename": "README.md",
  "file_type": "markdown",
  "uploaded_at": "2026-06-30T13:00:00+00:00",
  "size_bytes": 12345
}
```

Possible errors:

- `400`: unsupported file type or parse failure.
- `413`: file exceeds upload limit.
- `422`: missing `file` field.

## List Documents

```http
GET /api/documents
```

Example:

```bash
curl http://localhost:8000/api/documents
```

Success response: `200 OK`

```json
[
  {
    "id": "a-document-id",
    "filename": "README.md",
    "file_type": "markdown",
    "uploaded_at": "2026-06-30T13:00:00+00:00",
    "size_bytes": 12345
  }
]
```

## Delete Document

```http
DELETE /api/documents/{document_id}
```

Example:

```bash
curl -X DELETE http://localhost:8000/api/documents/a-document-id
```

Success response: `204 No Content`

Possible errors:

- `404`: document id does not exist.

Deletion removes the uploaded source file, document metadata, parsed chunks, and retrieval index entries.

## Ask A Question

```http
POST /api/chat
Content-Type: application/json
```

Request body:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `question` | string | Yes | User question |
| `conversation_id` | string | No | Existing conversation id for follow-up questions |

Example new conversation:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this project about?"}'
```

Example follow-up:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize the key points again.","conversation_id":"a-conversation-id"}'
```

Success response: `200 OK`

```json
{
  "answer": "Answer text",
  "insufficient_context": false,
  "retrieved_chunk_ids": ["a-document-id:0"],
  "log_id": "a-log-id",
  "conversation_id": "a-conversation-id"
}
```

Insufficient context response:

```json
{
  "answer": "我没有在当前已上传的文档中找到足够相关的内容来回答这个问题。\n\n你可以尝试：\n- 换一种更具体的问法，加入文档里的关键词；\n- 确认相关文件已经上传并解析成功；\n- 上传包含该问题答案的文档后再提问。",
  "insufficient_context": true,
  "retrieved_chunk_ids": [],
  "log_id": "a-log-id",
  "conversation_id": "a-conversation-id"
}
```

Possible errors:

- `422`: missing or invalid `question`.
- `503`: configured AI provider failed.

## List Conversations

```http
GET /api/conversations
```

Example:

```bash
curl http://localhost:8000/api/conversations
```

Success response: `200 OK`

```json
[
  {
    "id": "a-conversation-id",
    "created_at": "2026-06-30T13:00:00+00:00",
    "last_message_at": "2026-06-30T13:01:00+00:00",
    "message_count": 2,
    "preview": "What is this project about?"
  }
]
```

The `preview` field is derived from the first message in the conversation.

## List Conversation Messages

```http
GET /api/conversations/{conversation_id}/messages
```

Example:

```bash
curl http://localhost:8000/api/conversations/a-conversation-id/messages
```

Success response: `200 OK`

```json
[
  {
    "id": "a-message-id",
    "conversation_id": "a-conversation-id",
    "role": "user",
    "content": "What is this project about?",
    "created_at": "2026-06-30T13:00:00+00:00",
    "sequence": 0
  },
  {
    "id": "another-message-id",
    "conversation_id": "a-conversation-id",
    "role": "assistant",
    "content": "Answer text",
    "created_at": "2026-06-30T13:00:01+00:00",
    "sequence": 1
  }
]
```

If the conversation id does not exist, the current implementation returns an empty list.

## OpenAPI Schema

FastAPI also exposes generated API docs while the app is running:

```text
http://localhost:8000/docs
http://localhost:8000/openapi.json
```
