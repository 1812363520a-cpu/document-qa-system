## What to build

Add conversation support for follow-up questions. Users should be able to start a new conversation, continue an existing conversation by passing its ID, have recent turns included in QA context, and retrieve ordered conversation messages.

## Acceptance criteria

- [ ] `POST /chat` can create a new conversation when no conversation ID is supplied.
- [ ] `POST /chat` can append to an existing conversation when a conversation ID is supplied.
- [ ] Recent conversation turns are included in QA context for follow-up questions.
- [ ] `GET /conversations/{conversation_id}/messages` returns ordered messages.
- [ ] Tests cover new conversations, conversation reuse, ordered message storage, history retrieval, and history inclusion in the QA service.

## Blocked by

- #6
