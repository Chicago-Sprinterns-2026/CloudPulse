"""Backend tools used by the CloudPulse agent.

Team Instructions:
- Claim a function to work on.
- Do NOT change the function names, inputs, or return types.
- Replace the 'TODO' section and 'return' placeholders with your actual code.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

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
def lookup_product_metadata(product_name: str) -> Dict[str, str]:
    """Pulls precise service details like owners, versions, and shutdown protocols.
    
    Args:
        product_name (str): The name of the Google Cloud product (e.g., 'Cloud Run').
        
    Returns:
        Dict: A dictionary containing the product's metadata fields.
    """
    # TODO: Write BigQuery SQL to fetch product metadata.
    
    return {"product": product_name, "status": "placeholder"}


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