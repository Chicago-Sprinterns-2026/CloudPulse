"""Text cleaning and normalization helpers."""

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


def clean_html(html: str) -> str:
    """Remove scripts, styles, HTML tags, and excessive whitespace."""
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "nav", "footer"]):
        element.decompose()

    text = soup.get_text(separator=" ")
    return normalize_text(text)


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving readable text."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def save_processed_document(
    text: str,
    output_path: Path,
    metadata: dict | None = None,
) -> Path:
    """Save cleaned content and optional metadata as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"text": text, "metadata": metadata or {}}
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
