## What to build

Support uploading TXT and Markdown documents and listing uploaded document metadata. The slice should let a user add source material to the system, reject unsupported formats clearly, persist the uploaded file, and expose the current document inventory through the API.

## Acceptance criteria

- [ ] `POST /documents/upload` accepts `.txt` and Markdown files and rejects unsupported file types with a clear error response.
- [ ] Uploaded source files are stored under an application-controlled storage directory.
- [ ] Document metadata is persisted, including filename, type, upload time, and size.
- [ ] `GET /documents` returns uploaded documents with their metadata.
- [ ] Unit or API tests cover successful TXT upload, successful Markdown upload, unsupported format rejection, and document listing.

## Blocked by

- #1
