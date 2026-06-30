## What to build

Add optional PDF upload support by extending the document parser and ingestion path. PDF files should follow the same upload, parse, chunk, index, list, delete, and question-answering behavior as MVP TXT and Markdown documents.

## Acceptance criteria

- [ ] `POST /documents/upload` accepts PDF files when PDF support is enabled.
- [ ] PDF parsing extracts useful searchable plain text.
- [ ] Parsed PDF content is chunked and indexed through the existing ingestion flow.
- [ ] Deleting a PDF removes its metadata, source file, and searchable chunks.
- [ ] Tests cover successful PDF upload, PDF parsing, indexing, and deletion behavior.

## Blocked by

- #3
