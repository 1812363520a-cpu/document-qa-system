# 用户使用文档

本文档说明如何运行 Document Q&A System、上传文档、提问、管理会话，以及配置不同 AI 服务提供方。

## 快速开始

克隆仓库：

```bash
git clone https://github.com/1812363520a-cpu/document-qa-system.git
cd document-qa-system
```

创建本地环境变量文件：

```bash
cp .env.example .env
```

使用 Docker 启动：

```bash
docker compose up --build
```

打开 Web UI：

```text
http://localhost:8000/
```

停止服务：

```bash
docker compose down
```

## Web UI 使用说明

Web UI 是当前最主要的使用入口。

### Docs 文档 tab

在 `Docs` tab 中可以：

- 上传支持的文档。
- 刷新文档列表。
- 按文件名搜索已上传文档。
- 删除文档。删除前会有二次确认。

支持格式：

- `.txt`
- `.md`
- `.markdown`
- `.pdf`
- `.doc`
- `.docx`

默认上传大小限制是 20 MB。如果需要调整，可以修改 `.env` 中的 `MAX_UPLOAD_BYTES`。

### Chats 会话 tab

在 `Chats` tab 中可以：

- 浏览历史会话。
- 点击某个会话并加载消息列表。
- 在已有会话里继续追问。

会话历史会保存到 SQLite。模型回答时会带上最近的会话消息作为上下文。默认上下文窗口是最近 20 条消息，可以通过 `CONVERSATION_HISTORY_LIMIT` 修改。

### Chat 问答区域

在聊天区域可以：

- 创建新会话。
- 针对已上传文档提问。
- 发送后立即看到用户问题，assistant 回答加载期间会显示思考状态。
- 阅读 Markdown 渲染后的 assistant 回答。

如果系统没有找到足够相关的文档上下文，会返回提示，建议你上传相关文档、换更具体的问法，或检查文档是否解析成功。

## API 使用示例

健康检查：

```bash
curl http://localhost:8000/api/health
```

上传文档：

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@README.md"
```

查看文档列表：

```bash
curl http://localhost:8000/api/documents
```

提问：

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"这个项目是做什么的？"}'
```

在已有会话里继续追问：

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"再详细解释一下","conversation_id":"PASTE_CONVERSATION_ID"}'
```

查看会话列表：

```bash
curl http://localhost:8000/api/conversations
```

加载某个会话的消息：

```bash
curl http://localhost:8000/api/conversations/PASTE_CONVERSATION_ID/messages
```

删除文档：

```bash
curl -X DELETE http://localhost:8000/api/documents/PASTE_DOCUMENT_ID
```

## AI Provider 配置

默认配置是 `AI_PROVIDER=fake`。它用于本地验证，不会真正调用大模型服务。

修改 `.env` 后，需要重启 Docker：

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

### OpenAI-compatible 服务

如果某个模型服务提供 OpenAI-compatible chat completions API，可以使用这个配置：

```env
AI_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_KEY=your-api-key
OPENAI_COMPATIBLE_MODEL=your-model-name
OPENAI_COMPATIBLE_BASE_URL=https://your-provider.example/v1
```

### Ollama 或本地模型

先在本机运行 Ollama：

```bash
ollama serve
ollama pull qwen2.5:7b
```

如果使用 Docker 启动项目，推荐这样配置，让容器访问宿主机上的 Ollama：

```env
AI_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

如果是非 Docker 的本地开发，通常可以使用：

```env
OLLAMA_BASE_URL=http://localhost:11434
```

## 本地开发

创建并激活虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

运行测试：

```bash
pytest
```

本地启动 API：

```bash
uvicorn document_qa.main:app --reload
```

然后打开：

```text
http://localhost:8000/
```

## 常见问题

### `docker compose up --build` 提示找不到配置文件

请确认你是在项目根目录执行命令，也就是包含 `docker-compose.yml` 的目录。

### 上传返回 `400 Bad Request`

常见原因：

- 文件扩展名不支持。
- 文档内容无法解析。
- PDF 没有可提取的文本。
- Word 文件被加密、损坏，或者当前解析器无法读取。

### 上传返回 `413 Request Entity Too Large`

文件超过了 `MAX_UPLOAD_BYTES`。可以在 `.env` 中增大这个值，然后重启应用。

### 问答返回上下文不足

说明检索层没有找到超过 `RETRIEVAL_MIN_SCORE` 的相关文本块。可以尝试：

- 上传包含答案的相关文档。
- 用文档里的关键词提出更具体的问题。
- 适当调低 `RETRIEVAL_MIN_SCORE`。
- 确认文档上传成功，并且出现在文档列表中。

### 问答返回 `503 Service Unavailable`

说明 AI Provider 调用失败。请检查：

- API key 是否配置。
- model 名称是否正确。
- base URL 是否正确。
- 本地模型服务是否已经运行。
- Docker 容器是否能访问对应服务。
