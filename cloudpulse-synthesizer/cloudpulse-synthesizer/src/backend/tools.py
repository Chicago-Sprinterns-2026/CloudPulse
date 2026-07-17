"""Backend tools used by the CloudPulse agent.

Team Instructions:
- Claim a function to work on.
- Do NOT change the function names, inputs, or return types.
- Replace the 'TODO' section and 'return' placeholders with your actual code.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from google.cloud import bigquery
from src.backend.config import settings
from langchain_core.tools import tool

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
def lookup_product_metadata(product_name: str) -> Dict[str, str]:
    """Pulls precise service details like owners, versions, and shutdown protocols.
    
    Args:
        product_name (str): The name of the Google Cloud product (e.g., 'Cloud Run').
        
    Returns:
        Dict: A dictionary containing the product's metadata fields.
    """
    # TODO: Write BigQuery SQL to fetch product metadata.
    # 1. Initialize the client using your configuration
    client = bigquery.Client(project=settings.google_cloud_project)

    # 2. Write the SQL Query (Using parameters for security)
    # Be sure to update the table name to match your actual dataset structure
    query = f"""
        SELECT 
            product_name, 
            owner_team, 
            current_version, 
            shutdown_protocol,
            status
        FROM `{settings.google_cloud_project}.{settings.bigquery_dataset}.product_metadata`
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
    results = query_job.result() # Waits for the query to finish

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

    # If no results are found, return a helpful default
    if not metadata:
        return {"product": product_name, "error": "No metadata found for this product."}

    return metadata


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
    
    Args:
        product_name (str): The target Google Cloud product.
        severity (str, optional): Filter by severity (e.g., 'Critical', 'Warning').
        
    Returns:
        List[Dict]: A list of Mandatory Service Announcements.
    """
    # TODO: Write BigQuery SQL to fetch MSAs, applying the severity filter if provided.
    
    return []


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