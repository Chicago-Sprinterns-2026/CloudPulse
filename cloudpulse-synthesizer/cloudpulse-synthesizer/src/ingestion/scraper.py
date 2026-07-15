"""Utilities for collecting public Google Cloud documentation."""

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests


@dataclass
class ScrapedDocument:
    source_url: str
    content: str
    content_type: str


def fetch_url(url: str, timeout_seconds: int = 30) -> ScrapedDocument:
    """Fetch a public web document and return its raw content."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are supported.")

    response = requests.get(
        url,
        timeout=timeout_seconds,
        headers={"User-Agent": "CloudPulse-Synthesizer/0.1"},
    )
    response.raise_for_status()

    return ScrapedDocument(
        source_url=url,
        content=response.text,
        content_type=response.headers.get("content-type", "text/html"),
    )


def save_raw_document(document: ScrapedDocument, output_path: Path) -> Path:
    """Save a fetched document to local raw-data storage."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document.content, encoding="utf-8")
    return output_path
