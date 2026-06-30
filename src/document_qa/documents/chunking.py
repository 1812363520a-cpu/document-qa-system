from dataclasses import dataclass

from document_qa.documents.models import DocumentChunk


@dataclass(frozen=True)
class TextChunker:
    chunk_size: int
    chunk_overlap: int = 0

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

    def chunk(self, document_id: str, text: str) -> list[DocumentChunk]:
        if not text:
            return []

        chunks: list[DocumentChunk] = []
        start = 0
        step = self.chunk_size - self.chunk_overlap

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(
                DocumentChunk(
                    id=f"{document_id}:{len(chunks)}",
                    document_id=document_id,
                    chunk_index=len(chunks),
                    content=text[start:end],
                    start_char=start,
                    end_char=end,
                )
            )
            if end == len(text):
                break
            start += step

        return chunks
