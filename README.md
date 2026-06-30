# document-qa-system

AI document question-answering system.

## What It Does

This FastAPI backend uploads TXT, Markdown, PDF, and Word `.doc`/`.docx` documents, stores source files and metadata, parses documents into chunks, indexes chunks for local retrieval, answers document-grounded questions, tracks conversation history, and supports configurable AI providers.

## Quick Start From GitHub

Clone the repository:

```bash
git clone https://github.com/1812363520a-cpu/document-qa-system.git
cd document-qa-system
```

Create a local environment file:

```bash
cp .env.example .env
```

Start the app with Docker:

```bash
docker compose up --build
```

Open the Web UI:

```text
http://localhost:8000/
```

Check the API health endpoint:

```bash
curl http://localhost:8000/api/health
```

Stop the app:

```bash
docker compose down
```

## AI Providers

The default provider is `fake`, which is deterministic and does not call an external AI service.
To use a real model, edit `.env`, set `AI_PROVIDER`, and configure the matching variables.

OpenAI:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

DeepSeek:

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

Anthropic Claude:

```env
AI_PROVIDER=claude
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

Any OpenAI-compatible service:

```env
AI_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_KEY=your-api-key
OPENAI_COMPATIBLE_MODEL=your-model-name
OPENAI_COMPATIBLE_BASE_URL=https://your-provider.example/v1
```

Ollama local model:

```env
AI_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

For Ollama, run the model on your machine first:

```bash
ollama serve
ollama pull qwen2.5:7b
```

Restart Docker after changing `.env`:

```bash
docker compose up --build
```

## Local Development

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

Then open `http://localhost:8000/` to use the Web UI for uploading documents, managing the document list, and asking questions.

## Configuration

Configuration is loaded from environment variables. See `.env.example` for the current local defaults, including storage, database, chunking, and provider settings.
Supported `AI_PROVIDER` values are `fake`, `openai`, `deepseek`, `openai_compatible`, `anthropic`, `claude`, `ollama`, and `local`.

## Try The API

Health check:

```text
GET /api/health
```

Document and chat endpoints:

```text
POST /api/documents/upload
GET /api/documents
DELETE /api/documents/{document_id}
POST /api/chat
GET /api/conversations/{conversation_id}/messages
```

Example:

```bash
curl -X POST http://localhost:8000/api/documents/upload -F "file=@README.md"
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this project about?"}'
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [User Guide](docs/user-guide.md)
