"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
import os
from dotenv import load_dotenv

# This line finds your .env file and loads the variables into os.environ
load_dotenv()

@dataclass(frozen=True)
class Settings:
    google_cloud_project: str
    google_cloud_location: str
    vertex_search_data_store_id: str
    bigquery_dataset: str
    gemini_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            google_cloud_project=os.getenv(
                "GOOGLE_CLOUD_PROJECT", "your-project-id"
            ),
            google_cloud_location=os.getenv(
                "GOOGLE_CLOUD_LOCATION", "global"
            ),
            vertex_search_data_store_id=os.getenv(
                "VERTEX_SEARCH_DATA_STORE_ID", "cloudpulse-documents"
            ),
            bigquery_dataset=os.getenv(
                "BIGQUERY_DATASET", "cloudpulse"
            ),
            gemini_model=os.getenv(
                "GEMINI_MODEL", "gemini-2.5-flash"
            ),
        )

# Create a single instance to import across your app
settings = Settings.from_env()