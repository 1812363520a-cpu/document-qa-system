import re
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


class DocumentParseError(ValueError):
    pass


class DocumentParser:
    def parse(self, file_type: str, content: bytes) -> str:
        if file_type == "txt":
            return self._decode_utf8(content)
        if file_type == "markdown":
            text = self._decode_utf8(content)
            return self._markdown_to_plain_text(text)
        if file_type == "pdf":
            return self._pdf_to_plain_text(content)
        if file_type == "doc":
            return self._doc_to_plain_text(content)
        if file_type == "docx":
            return self._docx_to_plain_text(content)
        raise DocumentParseError(f"Unsupported parser document type: {file_type}")

    def _decode_utf8(self, content: bytes) -> str:
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentParseError("Document content must be valid UTF-8 text") from exc

    def _markdown_to_plain_text(self, text: str) -> str:
        without_code_fences = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
        without_inline_code = re.sub(r"`([^`]*)`", r"\1", without_code_fences)
        without_links = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", without_inline_code)
        without_markup = re.sub(r"^[#>*\-\s]+", "", without_links, flags=re.MULTILINE)
        without_emphasis = without_markup.replace("**", "").replace("__", "")
        without_emphasis = without_emphasis.replace("*", "").replace("_", "")
        return without_emphasis

    def _pdf_to_plain_text(self, content: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(content))
            page_text = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:
            raise DocumentParseError("PDF content could not be parsed") from exc

        text = "\n".join(page_text).strip()
        if not text:
            raise DocumentParseError("PDF did not contain extractable text")
        return text

    def _doc_to_plain_text(self, content: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".doc") as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            temporary_path = Path(temporary_file.name)

            try:
                result = subprocess.run(
                    ["antiword", str(temporary_path)],
                    capture_output=True,
                    check=False,
                    text=True,
                )
            except FileNotFoundError as exc:
                raise DocumentParseError(
                    "Word .doc parsing requires the antiword command to be installed"
                ) from exc

        if result.returncode != 0:
            raise DocumentParseError("Word .doc content could not be parsed")

        text = result.stdout.strip()
        if not text:
            raise DocumentParseError("Word .doc document did not contain extractable text")
        return text

    def _docx_to_plain_text(self, content: bytes) -> str:
        try:
            document = Document(BytesIO(content))
        except Exception as exc:
            raise DocumentParseError("Word document content could not be parsed") from exc

        parts = []
        parts.extend(paragraph.text for paragraph in document.paragraphs if paragraph.text)
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))

        text = "\n".join(parts).strip()
        if not text:
            raise DocumentParseError("Word document did not contain extractable text")
        return text
