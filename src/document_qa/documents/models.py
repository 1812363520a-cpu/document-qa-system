from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentMetadata:
    id: str
    filename: str
    file_type: str
    uploaded_at: str
    size_bytes: int
    storage_path: str

    def to_api_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "uploaded_at": self.uploaded_at,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    document_id: str
    chunk_index: int
    content: str
    start_char: int
    end_char: int
