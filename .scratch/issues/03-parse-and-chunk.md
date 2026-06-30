## What to build

Parse uploaded TXT and Markdown documents into plain text and split the text into deterministic chunks that can be indexed for retrieval. This should happen as part of ingestion so each accepted document becomes searchable input for later question answering.

## Acceptance criteria

- [ ] The parser module exposes a stable interface for turning an uploaded supported file into plain text.
- [ ] TXT and Markdown parsing preserve useful searchable content.
- [ ] Chunking supports configurable chunk size and overlap.
- [ ] Chunking handles empty input and produces deterministic output.
- [ ] Tests cover parsing, unsupported parse failures, chunk size, overlap, empty input, and deterministic chunk output.

## Blocked by

- #2
