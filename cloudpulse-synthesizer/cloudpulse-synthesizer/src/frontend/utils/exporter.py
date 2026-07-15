"""Export helpers for generated one-pagers."""


def build_text_export(content: str) -> bytes:
    """Convert one-pager text into downloadable UTF-8 bytes."""
    return content.encode("utf-8")


def build_pdf_export(content: str) -> bytes:
    """Placeholder for PDF generation."""
    raise NotImplementedError(
        "Add a PDF library such as ReportLab to enable PDF exports."
    )
