import pytest

from document_qa.documents.chunking import TextChunker


def test_chunker_splits_text_by_configured_size_and_overlap():
    chunker = TextChunker(chunk_size=5, chunk_overlap=2)

    chunks = chunker.chunk("doc-1", "abcdefghij")

    assert [chunk.content for chunk in chunks] == ["abcde", "defgh", "ghij"]
    assert [(chunk.start_char, chunk.end_char) for chunk in chunks] == [
        (0, 5),
        (3, 8),
        (6, 10),
    ]


def test_chunker_returns_no_chunks_for_empty_input():
    chunker = TextChunker(chunk_size=5, chunk_overlap=2)

    assert chunker.chunk("doc-1", "") == []


def test_chunker_output_is_deterministic():
    chunker = TextChunker(chunk_size=4, chunk_overlap=1)

    first = chunker.chunk("doc-1", "abcdefg")
    second = chunker.chunk("doc-1", "abcdefg")

    assert first == second
    assert [chunk.id for chunk in first] == ["doc-1:0", "doc-1:1"]


def test_chunker_rejects_invalid_configuration():
    with pytest.raises(ValueError, match="greater than 0"):
        TextChunker(chunk_size=0)

    with pytest.raises(ValueError, match="smaller than chunk_size"):
        TextChunker(chunk_size=5, chunk_overlap=5)
