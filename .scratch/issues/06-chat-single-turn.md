## What to build

Implement the first document-grounded question answering path. A user should be able to ask a natural language question, have the system retrieve relevant chunks, call a fake AI provider in tests, persist the question and answer, and return either a grounded response or a clear insufficient-context response.

## Acceptance criteria

- [ ] `POST /chat` accepts a question and returns an answer.
- [ ] The QA service retrieves relevant document chunks and includes them in provider context.
- [ ] The AI provider is behind a stable interface and has a fake provider for tests.
- [ ] Questions and answers are persisted for later analysis.
- [ ] The system returns a clear cannot-answer response when there is not enough supporting context.
- [ ] Tests cover retrieval use, prompt context assembly, answer persistence, provider invocation, and insufficient-context behavior.

## Blocked by

- #4
