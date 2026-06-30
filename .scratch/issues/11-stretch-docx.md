## What to build

Add optional Word `.docx` upload support by extending the document parser and ingestion path. Word documents should follow the same upload, parse, chunk, index, list, delete, and question-answering behavior as MVP TXT and Markdown documents.

## Acceptance criteria

- [ ] `POST /documents/upload` accepts `.docx` files when Word support is enabled.
- [ ] `.docx` parsing extracts useful searchable plain text.
- [ ] Parsed Word content is chunked and indexed through the existing ingestion flow.
- [ ] Deleting a Word document removes its metadata, source file, and searchable chunks.
- [ ] Tests cover successful `.docx` upload, parsing, indexing, and deletion behavior.

## Blocked by

- #3
