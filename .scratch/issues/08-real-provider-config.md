## What to build

Add a real AI provider path configured through environment variables while keeping the provider interface testable and extensible. The MVP should support OpenAI as the hosted provider path and retain the fake provider for deterministic tests.

## Acceptance criteria

- [ ] Provider selection is configurable via environment variables.
- [ ] OpenAI provider configuration supports credentials and model selection without code changes.
- [ ] Missing or invalid provider configuration fails with a clear error.
- [ ] The fake provider remains available for tests.
- [ ] The provider interface remains broad enough to support Claude or local model adapters later.
- [ ] Tests cover provider selection, missing credentials behavior, and fake provider usage.

## Blocked by

- #6
