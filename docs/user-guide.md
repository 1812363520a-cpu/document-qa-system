# User Guide

This guide explains how to run the Document Q&A System, upload documents, ask questions, manage conversations, and configure AI providers.

## Quick Start

Clone the repository:

```bash
git clone https://github.com/1812363520a-cpu/document-qa-system.git
cd document-qa-system
```

Create a local environment file:

```bash
cp .env.example .env
```

Start with Docker:

```bash
docker compose up --build
```

Open the Web UI:

```text
http://localhost:8000/
```

Stop the service:

```bash
docker compose down
```

## Web UI

The Web UI is the main way to use the system.

### Documents Tab

Use the `Docs` tab to:

- Upload supported documents.
- Refresh the document list.
- Search uploaded files by filename.
- Delete a document after confirming the delete prompt.

Supported formats:

- `.txt`
- `.md`
- `.markdown`
- `.pdf`
- `.doc`
- `.docx`

The default upload limit is 20 MB. Change `MAX_UPLOAD_BYTES` in `.env` if you need a different limit.

### Chats Tab

Use the `Chats` tab to:

- Browse previous conversations.
- Select a conversation and load its messages.
- Continue asking follow-up questions in that conversation.

Conversation history is persisted in SQLite. The model receives recent conversation messages as context. The default history window is 20 messages and can be changed with `CONVERSATION_HISTORY_LIMIT`.

### Chat Panel

Use the chat panel to:

- Start a new conversation.
- Ask questions about uploaded documents.
- See your question immediately while the assistant answer is loading.
- Read assistant answers rendered as Markdown.

If the system cannot find relevant document context, it returns a friendly message asking you to upload or select more relevant material, or to ask a more specific question.

## API Examples

Health check:

```bash
curl http://localhost:8000/api/health
```

Upload a document:

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@README.md"
```

List uploaded documents:

```bash
curl http://localhost:8000/api/documents
```

Ask a question:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this project about?"}'
```

Continue a conversation:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Can you explain that in more detail?","conversation_id":"PASTE_CONVERSATION_ID"}'
```

List conversations:

```bash
curl http://localhost:8000/api/conversations
```

Load conversation messages:

```bash
curl http://localhost:8000/api/conversations/PASTE_CONVERSATION_ID/messages
```

Delete a document:

```bash
curl -X DELETE http://localhost:8000/api/documents/PASTE_DOCUMENT_ID
```

## AI Provider Configuration

By default the app uses `AI_PROVIDER=fake`. This is useful for local verification but does not call a real model.

After changing `.env`, restart Docker:

```bash
docker compose up --build
```

### OpenAI

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

### DeepSeek

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### Anthropic Claude

```env
AI_PROVIDER=claude
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

### OpenAI-Compatible Provider

Use this for services that expose an OpenAI-compatible chat completions API.

```env
AI_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_KEY=your-api-key
OPENAI_COMPATIBLE_MODEL=your-model-name
OPENAI_COMPATIBLE_BASE_URL=https://your-provider.example/v1
```

### Ollama Or Local Model

Run Ollama on your machine:

```bash
ollama serve
ollama pull qwen2.5:7b
```

Configure Docker to reach the host Ollama service:

```env
AI_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

For local non-Docker development, `OLLAMA_BASE_URL=http://localhost:11434` is usually correct.

## Local Development

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Start the API locally:

```bash
uvicorn document_qa.main:app --reload
```

Then open:

```text
http://localhost:8000/
```

## Troubleshooting

### `docker compose up --build` says no configuration file found

Run the command from the project root, the directory containing `docker-compose.yml`.

### Upload returns `400 Bad Request`

Common causes:

- Unsupported file extension.
- The document cannot be parsed.
- A PDF has no extractable text.
- A Word file is encrypted, corrupted, or not readable by the available parser.

### Upload returns `413 Request Entity Too Large`

The file exceeds `MAX_UPLOAD_BYTES`. Increase the value in `.env` and restart the app.

### Chat returns insufficient context

The retrieval layer did not find chunks above `RETRIEVAL_MIN_SCORE`. Try:

- Uploading the relevant document.
- Asking with more specific keywords from the document.
- Lowering `RETRIEVAL_MIN_SCORE` slightly.
- Confirming the upload succeeded and the file appears in the document list.

### Chat returns `503 Service Unavailable`

The AI provider request failed. Check:

- API key is configured.
- Model name is valid.
- Base URL is correct.
- Local model service is running.
- Network access is available from the Docker container.
