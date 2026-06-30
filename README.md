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

Configuration is loaded from environment variables. See `.env.example` for the current local defaults.
