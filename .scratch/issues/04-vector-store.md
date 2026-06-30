## What to build

Index parsed document chunks into a replaceable vector store interface and support searching and deleting chunks by document. The MVP implementation can be local and simple, but the service boundary should allow FAISS, Chroma, or another backend to be swapped later.

## Acceptance criteria

- [ ] The vector store module exposes upsert, search, and delete-by-document operations.
- [ ] Ingested chunks are indexed with document and chunk metadata.
- [ ] Search returns relevant chunks for a natural language query.
- [ ] Delete-by-document removes all indexed chunks for that document.
- [ ] Tests verify chunks can be indexed, retrieved, and deleted by document ID.

## Blocked by

- #3
