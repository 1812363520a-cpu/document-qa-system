## What to build

Delete documents end-to-end so outdated or incorrect content is removed from the system. Deletion should remove the document record, source file, and searchable chunks so future answers cannot use stale content.

## Acceptance criteria

- [ ] `DELETE /documents/{document_id}` deletes an existing document.
- [ ] Deleting a document removes its persisted metadata or marks it unavailable according to the chosen persistence convention.
- [ ] Deleting a document removes the stored source file.
- [ ] Deleting a document removes all searchable chunks for that document.
- [ ] API tests cover deletion success, deletion of a missing document, list behavior after deletion, and retrieval state after deletion.

## Blocked by

- #4
