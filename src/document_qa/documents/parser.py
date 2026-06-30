import re


class DocumentParseError(ValueError):
    pass


class DocumentParser:
    def parse(self, file_type: str, content: bytes) -> str:
        text = self._decode_utf8(content)
        if file_type == "txt":
            return text
        if file_type == "markdown":
            return self._markdown_to_plain_text(text)
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
