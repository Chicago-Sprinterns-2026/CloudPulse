"""Backend tools used by the CloudPulse agent."""

from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    text: str
    source_url: str
    title: str = ""


def search_vertex_documents(query: str, limit: int = 5) -> list[RetrievedChunk]:
    """Placeholder for Vertex AI Search retrieval."""
    if not query.strip():
        return []

    # TODO: Connect to Google Cloud Discovery Engine / Vertex AI Search.
    return []


def query_bigquery_metadata(product_name: str) -> list[dict]:
    """Placeholder for querying product and document metadata."""
    if not product_name.strip():
        return []

    # TODO: Use google-cloud-bigquery to retrieve metadata.
    return []


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks for an LLM prompt."""
    if not chunks:
        return "No relevant context was retrieved."

    sections = []
    for index, chunk in enumerate(chunks, start=1):
        sections.append(
            f"[Source {index}] {chunk.title}\n"
            f"{chunk.text}\n"
            f"URL: {chunk.source_url}"
        )
    return "\n\n".join(sections)
