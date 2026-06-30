import re
from io import BytesIO

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
