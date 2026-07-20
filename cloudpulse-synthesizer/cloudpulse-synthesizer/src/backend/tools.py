"""Backend tools used by the CloudPulse agent.

Team Instructions:
- Claim a function to work on.
- Do NOT change the function names, inputs, or return types.
- Replace the 'TODO' section and 'return' placeholders with your actual code.
"""

from dataclasses import dataclass
import json
import os
from typing import List, Dict, Optional
from google.cloud import bigquery
from src.backend.config import settings
from langchain_core.tools import tool
from data.Data_Pipeline.retriever import generate_agent_builder_response

@dataclass
class RetrievedChunk:
    text: str
    source_url: str
    title: str = ""


# ==========================================
# 1. UNSTRUCTURED SEARCH (Vertex AI)
# ==========================================
def search_docs(query: str, limit: int = 5) -> List[RetrievedChunk]:
    """Searches raw PDFs, web pages, and technical guides.
    
    Args:
        query (str): The search query from the user.
        limit (int): The maximum number of documents to return.
        
    Returns:
        List[RetrievedChunk]: A list of text chunks with their source URLs.
    """
    if not query.strip():
        return []
        
    # TODO: Connect to Vertex AI Search / Discovery Engine.
    
    return []


# ==========================================
# 2. STRUCTURED DATABASE (BigQuery)
# ==========================================
@tool
def lookup_product_metadata(product_name: str) -> str:
    """Pulls precise service details like owners, versions, and shutdown protocols.
    
    Args:
        product_name (str): The name of the Google Cloud product (e.g., 'Cloud Run').
        
    Returns:
        str: A JSON-formatted string containing the product's metadata fields.
    """
    try:
        # 1. Initialize client using default environment credentials
        # (Alternatively, you can keep your 'settings' object if you import it properly)
        client = bigquery.Client()
        
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-default-project")
        dataset_id = os.environ.get("BIGQUERY_DATASET", "your_default_dataset")

        # 2. Write the SQL Query (Using parameters for security)
        query = f"""
            SELECT 
                product_name, 
                owner_team, 
                current_version, 
                shutdown_protocol,
                status
            FROM `{project_id}.{dataset_id}.product_metadata`
            WHERE product_name = @product_name
            LIMIT 1
        """

        # 3. Configure the parameterized query
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("product_name", "STRING", product_name)
            ]
        )

        # 4. Execute the query
        query_job = client.query(query, job_config=job_config)
        results = query_job.result() 

        # 5. Process the result into a dictionary
        metadata = {}
        for row in results:
            metadata = {
                "product_name": row.product_name,
                "owner_team": row.owner_team,
                "current_version": row.current_version,
                "shutdown_protocol": row.shutdown_protocol,
                "status": row.status
            }

        # 6. Return a JSON string for maximum LangChain agent compatibility
        if not metadata:
            return json.dumps({"product": product_name, "error": "No metadata found for this product."})

        return json.dumps(metadata)
        
    except Exception as e:
        # Prevent the entire agent from crashing if BigQuery fails
        return json.dumps({"error": f"Failed to query BigQuery: {str(e)}"})


# ==========================================
# 3. TIME-BASED FILTERING (BigQuery)
# ==========================================
def get_release_notes(product_name: str, start_date: str) -> List[Dict]:
    """Finds the newest updates and feature changes for a specific product.
    
    Args:
        product_name (str): The target Google Cloud product.
        start_date (str): The date to filter from (Format: YYYY-MM-DD).
        
    Returns:
        List[Dict]: A list of release note records.
    """
    # TODO: Write BigQuery SQL to fetch release notes after the start_date.
    
    return []


# ==========================================
# 4. ACTIVE ALERT / LEGAL (BigQuery)
# ==========================================
def get_msas(product_name: str, severity: Optional[str] = None) -> List[Dict]:
    """Checks for mandatory actions or deprecation deadlines.

    Use this tool when the user asks about mandatory actions,
    deprecations, security updates, deadlines, or critical alerts.

    Args:
        product_name (str): Google Cloud product or service.
        severity (str, optional): Severity filter such as CRITICAL or HIGH.

    Returns:
        List[Dict]: Matching MSA records from the RAG corpus.
    """

    # Do not search with an empty product name
    if not product_name.strip():
        return []

    # Build a focused query for the RAG Engine
    query = (
        f"Mandatory Service Announcements for {product_name}. "
        "Find required actions, deprecations, security changes, "
        "effective dates, deadlines, and service impacts."
    )

    # Include severity when the user provides it
    if severity:
        query += f" Only return announcements with severity {severity}."

    # Search the shared RAG corpus
    chunks = search_docs(query, limit=5)

    # Convert RetrievedChunk objects to dictionaries
    return [
        {
            "product": product_name,
            "severity_filter": severity,
            "title": chunk.title,
            "description": chunk.text,
            "source_url": chunk.source_url,
        }
        for chunk in chunks
    ]

# ==========================================
# 5. UTILITY / UX
# ==========================================
def format_citations(chunks: List[RetrievedChunk]) -> str:
    """Formats clean references and links for the user to make the agent verifiable.
    
    Args:
        chunks (List[RetrievedChunk]): The raw chunks retrieved from search_docs.
        
    Returns:
        str: A neatly formatted markdown string containing the citations.
    """
    if not chunks:
        return "No documentation sources were referenced."
        
    # TODO: Iterate through the chunks and format them into a clean string.
    
    return "Placeholder formatted citation string."