"""Push processed documents into the configured semantic search datastore."""

from pathlib import Path

from src.backend.config import Settings


def ingest_processed_file(file_path: Path) -> None:
    """Placeholder for uploading a processed document to Vertex AI Search."""
    settings = Settings.from_env()

    if not file_path.exists():
        raise FileNotFoundError(f"Processed file not found: {file_path}")

    print(
        f"Ready to ingest {file_path.name} into "
        f"{settings.vertex_search_data_store_id}."
    )
    # TODO: Add Discovery Engine / Vertex AI Search document import logic.
