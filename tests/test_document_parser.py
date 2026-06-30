import pytest
from io import BytesIO
from docx import Document
from reportlab.pdfgen import canvas

from document_qa.documents.parser import DocumentParseError, DocumentParser


def make_pdf_bytes(text: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


def make_docx_bytes(text: str) -> bytes:
    buffer = BytesIO()
    document = Document()
    document.add_paragraph(text)
    document.save(buffer)
    return buffer.getvalue()


def install_fake_antiword(tmp_path, monkeypatch, output: str, exit_code: int = 0):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    antiword = bin_dir / "antiword"
    antiword.write_text(f"#!/bin/sh\nprintf '%s' '{output}'\nexit {exit_code}\n")
    antiword.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))


def test_txt_parser_preserves_plain_text_content():
    parser = DocumentParser()

    text = parser.parse("txt", b"First line\nSecond line")

    assert text == "First line\nSecond line"


def test_markdown_parser_preserves_searchable_text():
    parser = DocumentParser()

    text = parser.parse(
        "markdown",
        b"# Project Notes\n\nThis is **important**. See [docs](https://example.com).",
    )

    assert "Project Notes" in text
    assert "This is important" in text
    assert "docs" in text
    assert "**" not in text
    assert "https://example.com" not in text


def test_pdf_parser_extracts_searchable_text():
    parser = DocumentParser()

    text = parser.parse("pdf", make_pdf_bytes("PDF searchable content"))

    assert "PDF searchable content" in text


def test_docx_parser_extracts_searchable_text():
    parser = DocumentParser()

    text = parser.parse("docx", make_docx_bytes("DOCX searchable content"))

    assert "DOCX searchable content" in text


def test_doc_parser_extracts_searchable_text_with_antiword(tmp_path, monkeypatch):
    install_fake_antiword(tmp_path, monkeypatch, "DOC searchable content")
    parser = DocumentParser()

    text = parser.parse("doc", b"legacy word bytes")

    assert text == "DOC searchable content"


def test_doc_parser_handles_renamed_docx_content():
    parser = DocumentParser()

    text = parser.parse("doc", make_docx_bytes("Renamed DOCX searchable content"))

    assert "Renamed DOCX searchable content" in text


def test_doc_parser_falls_back_to_html_content(tmp_path, monkeypatch):
    install_fake_antiword(tmp_path, monkeypatch, "not a word document", exit_code=1)
    parser = DocumentParser()
    content = "<html><body><h1>HTML DOC</h1><p>Searchable body</p></body></html>"

    text = parser.parse("doc", content.encode("utf-8"))

    assert "HTML DOC" in text
    assert "Searchable body" in text


def test_doc_parser_falls_back_to_rtf_content():
    parser = DocumentParser()
    content = r"{\rtf1\ansi RTF searchable content\par Second line}"

    text = parser.parse("doc", content.encode("utf-8"))

    assert "RTF searchable content" in text
    assert "Second line" in text


def test_doc_parser_falls_back_to_gb18030_text(tmp_path, monkeypatch):
    install_fake_antiword(tmp_path, monkeypatch, "not a word document", exit_code=1)
    parser = DocumentParser()

    text = parser.parse("doc", "中文 可检索 内容".encode("gb18030"))

    assert text == "中文 可检索 内容"


def test_parser_rejects_unsupported_file_type():
    parser = DocumentParser()

    with pytest.raises(DocumentParseError, match="Unsupported parser document type"):
        parser.parse("xlsx", b"content")


def test_parser_rejects_non_utf8_content():
    parser = DocumentParser()

    with pytest.raises(DocumentParseError, match="valid UTF-8"):
        parser.parse("txt", b"\xff")


def test_parser_rejects_invalid_pdf_content():
    parser = DocumentParser()

    with pytest.raises(DocumentParseError, match="PDF content could not be parsed"):
        parser.parse("pdf", b"not a real pdf")


def test_parser_rejects_invalid_docx_content():
    parser = DocumentParser()

    with pytest.raises(DocumentParseError, match="Word document content could not be parsed"):
        parser.parse("docx", b"not a real docx")


def test_parser_rejects_doc_when_antiword_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    parser = DocumentParser()

    with pytest.raises(DocumentParseError, match="antiword command"):
        parser.parse("doc", b"\x00\x01\x02\x03\x04")


def test_parser_rejects_invalid_doc_content(tmp_path, monkeypatch):
    install_fake_antiword(tmp_path, monkeypatch, "", exit_code=1)
    parser = DocumentParser()

    with pytest.raises(DocumentParseError, match="readable RTF/HTML/text document"):
        parser.parse("doc", b"\x00\x01\x02\x03\x04")
