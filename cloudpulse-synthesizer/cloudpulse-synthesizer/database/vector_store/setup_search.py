"""Initialize or document the Vertex AI Search datastore setup.

The exact API calls depend on the datastore type and Google Cloud project
configuration. This starter validates the required environment variables.
"""

from src.backend.config import Settings


def setup_datastore() -> None:
    settings = Settings.from_env()
    print(
        "Configure Vertex AI Search datastore",
        {
            "project_id": settings.google_cloud_project,
            "location": settings.google_cloud_location,
            "data_store_id": settings.vertex_search_data_store_id,
        },
    )


if __name__ == "__main__":
    setup_datastore()
