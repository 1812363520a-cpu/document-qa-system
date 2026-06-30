# 接口文档

默认 API 前缀是 `/api`，可以通过 `API_PREFIX` 修改。

本地 Docker 开发时的 base URL：

```text
http://localhost:8000
```

## 错误格式

FastAPI 默认返回包含 `detail` 字段的错误：

```json
{
  "detail": "Error message"
}
```

常见状态码：

| 状态码 | 含义 |
| --- | --- |
| `400` | 文档格式不支持，或文档无法解析 |
| `404` | 文档不存在 |
| `413` | 上传文件超过 `MAX_UPLOAD_BYTES` |
| `422` | 请求体不合法，或缺少必要字段 |
| `503` | AI Provider 调用失败 |

## 健康检查

```http
GET /api/health
```

返回服务状态、服务名和当前环境。

响应示例：

```json
{
  "status": "ok",
  "service": "Document Q&A System",
  "environment": "docker"
}
```

## 上传文档

```http
POST /api/documents/upload
Content-Type: multipart/form-data
```

表单字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | file | 是 | `.txt`、`.md`、`.markdown`、`.pdf`、`.doc`、`.docx` 文件 |

请求示例：

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@README.md"
```

成功响应：`201 Created`

```json
{
  "id": "a-document-id",
  "filename": "README.md",
  "file_type": "markdown",
  "uploaded_at": "2026-06-30T13:00:00+00:00",
  "size_bytes": 12345
}
```

可能的错误：

- `400`：文件类型不支持，或解析失败。
- `413`：文件超过上传大小限制。
- `422`：缺少 `file` 字段。

## 查看文档列表

```http
GET /api/documents
```

请求示例：

```bash
curl http://localhost:8000/api/documents
```

成功响应：`200 OK`

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

## 删除文档

```http
DELETE /api/documents/{document_id}
```

请求示例：

```bash
curl -X DELETE http://localhost:8000/api/documents/a-document-id
```

成功响应：`204 No Content`

可能的错误：

- `404`：文档 id 不存在。

删除文档会移除原始上传文件、文档元数据、解析后的 chunks 和检索索引条目。

## 提问

```http
POST /api/chat
Content-Type: application/json
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `question` | string | 是 | 用户问题 |
| `conversation_id` | string | 否 | 已有会话 id，用于继续追问 |

新会话请求示例：

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"这个项目是做什么的？"}'
```

继续会话请求示例：

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"总结一下重点","conversation_id":"a-conversation-id"}'
```

成功响应：`200 OK`

```json
{
  "answer": "Answer text",
  "insufficient_context": false,
  "retrieved_chunk_ids": ["a-document-id:0"],
  "log_id": "a-log-id",
  "conversation_id": "a-conversation-id"
}
```

上下文不足响应示例：

```json
{
  "answer": "我没有在当前已上传的文档中找到足够相关的内容来回答这个问题。\n\n你可以尝试：\n- 换一种更具体的问法，加入文档里的关键词；\n- 确认相关文件已经上传并解析成功；\n- 上传包含该问题答案的文档后再提问。",
  "insufficient_context": true,
  "retrieved_chunk_ids": [],
  "log_id": "a-log-id",
  "conversation_id": "a-conversation-id"
}
```

可能的错误：

- `422`：缺少 `question`，或请求体不合法。
- `503`：当前配置的 AI Provider 调用失败。

## 查看会话列表

```http
GET /api/conversations
```

请求示例：

```bash
curl http://localhost:8000/api/conversations
```

成功响应：`200 OK`

```json
[
  {
    "id": "a-conversation-id",
    "created_at": "2026-06-30T13:00:00+00:00",
    "last_message_at": "2026-06-30T13:01:00+00:00",
    "message_count": 2,
    "preview": "这个项目是做什么的？"
  }
]
```

`preview` 来自该会话的第一条消息。

## 查看会话消息

```http
GET /api/conversations/{conversation_id}/messages
```

请求示例：

```bash
curl http://localhost:8000/api/conversations/a-conversation-id/messages
```

成功响应：`200 OK`

```json
[
  {
    "id": "a-message-id",
    "conversation_id": "a-conversation-id",
    "role": "user",
    "content": "这个项目是做什么的？",
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

如果会话 id 不存在，当前实现会返回空数组。

## OpenAPI 文档

应用运行后，FastAPI 会自动提供 OpenAPI 文档：

```text
http://localhost:8000/docs
http://localhost:8000/openapi.json
```
