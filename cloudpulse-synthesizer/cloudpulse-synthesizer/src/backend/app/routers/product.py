from fastapi import APIRouter, Query
from typing import List, Dict
from app.tools import _search_google_docs_datastore

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/search-datastore")
async def search_datastore(
    query: str = Query(..., description="Search query for Google Cloud documentation"),
    limit: int = Query(5, ge=1, le=100, description="Maximum number of results")
) -> Dict:
    """Search Google Cloud documentation datastore for products and features."""
    results = _search_google_docs_datastore(query=query, limit=limit)
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }
