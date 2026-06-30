from document_qa.documents.models import DocumentChunk
from document_qa.retrieval.vector_store import SQLiteVectorStore


def make_store(tmp_path):
    store = SQLiteVectorStore(str(tmp_path / "document_qa.sqlite3"))
    store.initialize()
    return store


def test_vector_store_indexes_and_searches_relevant_chunks(tmp_path):
    store = make_store(tmp_path)
    store.upsert(
        [
            DocumentChunk(
                id="doc-1:0",
                document_id="doc-1",
                chunk_index=0,
                content="FastAPI accepts uploaded text documents.",
                start_char=0,
                end_char=40,
            ),
            DocumentChunk(
                id="doc-2:0",
                document_id="doc-2",
                chunk_index=0,
                content="SQLite stores metadata for later inspection.",
                start_char=0,
                end_char=45,
            ),
        ]
    )

    results = store.search("uploaded documents", limit=2)

    assert len(results) == 1
    assert results[0].chunk.id == "doc-1:0"
    assert results[0].chunk.document_id == "doc-1"
    assert results[0].score > 0


def test_vector_store_indexes_and_searches_chinese_chunks(tmp_path):
    store = make_store(tmp_path)
    store.upsert(
        [
            DocumentChunk(
                id="doc-1:0",
                document_id="doc-1",
                chunk_index=0,
                content="瀑布模型的优点是阶段清晰、文档驱动，适合需求明确的项目。",
                start_char=0,
                end_char=32,
            )
        ]
    )

    results = store.search("瀑布模型的优点")

    assert len(results) == 1
    assert results[0].chunk.id == "doc-1:0"


def test_vector_store_does_not_match_chinese_single_character_overlap(tmp_path):
    store = make_store(tmp_path)
    store.upsert(
        [
            DocumentChunk(
                id="doc-1:0",
                document_id="doc-1",
                chunk_index=0,
                content="瀑布模型适合需求明确的项目。",
                start_char=0,
                end_char=14,
            )
        ]
    )

    results = store.search("火星农业")

    assert results == []


def test_vector_store_rebuilds_index_from_persisted_document_chunks(tmp_path):
    store = make_store(tmp_path)
    with store._connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                start_char INTEGER NOT NULL,
                end_char INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO document_chunks (
                id, document_id, chunk_index, content, start_char, end_char
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "doc-1:0",
                "doc-1",
                0,
                "瀑布模型适合需求明确、变更较少的项目。",
                0,
                22,
            ),
        )

    store.rebuild_from_chunks()

    results = store.search("瀑布模型")
    assert len(results) == 1
    assert results[0].chunk.id == "doc-1:0"


def test_vector_store_upsert_replaces_existing_chunk(tmp_path):
    store = make_store(tmp_path)
    store.upsert(
        [
            DocumentChunk(
                id="doc-1:0",
                document_id="doc-1",
                chunk_index=0,
                content="old content",
                start_char=0,
                end_char=11,
            )
        ]
    )

    store.upsert(
        [
            DocumentChunk(
                id="doc-1:0",
                document_id="doc-1",
                chunk_index=0,
                content="new searchable content",
                start_char=0,
                end_char=22,
            )
        ]
    )

    assert store.search("old") == []
    results = store.search("new")
    assert len(results) == 1
    assert results[0].chunk.content == "new searchable content"


def test_vector_store_delete_by_document_removes_indexed_chunks(tmp_path):
    store = make_store(tmp_path)
    store.upsert(
        [
            DocumentChunk(
                id="doc-1:0",
                document_id="doc-1",
                chunk_index=0,
                content="alpha searchable",
                start_char=0,
                end_char=16,
            ),
            DocumentChunk(
                id="doc-2:0",
                document_id="doc-2",
                chunk_index=0,
                content="alpha retained",
                start_char=0,
                end_char=14,
            ),
        ]
    )

    store.delete_by_document("doc-1")

    results = store.search("alpha", limit=10)
    assert [result.chunk.document_id for result in results] == ["doc-2"]


def test_vector_store_returns_empty_results_for_empty_query_or_limit(tmp_path):
    store = make_store(tmp_path)

    assert store.search("") == []
    assert store.search("anything", limit=0) == []
