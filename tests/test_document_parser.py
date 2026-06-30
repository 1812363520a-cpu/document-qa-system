import pytest
from io import BytesIO
from reportlab.pdfgen import canvas

from document_qa.documents.parser import DocumentParseError, DocumentParser


def make_pdf_bytes(text: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


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


def test_parser_rejects_unsupported_file_type():
    parser = DocumentParser()

    with pytest.raises(DocumentParseError, match="Unsupported parser document type"):
        parser.parse("docx", b"content")


def test_parser_rejects_non_utf8_content():
    parser = DocumentParser()

    with pytest.raises(DocumentParseError, match="valid UTF-8"):
        parser.parse("txt", b"\xff")


def test_parser_rejects_invalid_pdf_content():
    parser = DocumentParser()

    with pytest.raises(DocumentParseError, match="PDF content could not be parsed"):
        parser.parse("pdf", b"not a real pdf")
