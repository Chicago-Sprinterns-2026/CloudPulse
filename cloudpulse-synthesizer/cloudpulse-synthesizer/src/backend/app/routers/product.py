from fastapi import APIRouter, HTTPException, Query
from typing import Dict
from google import genai
from app.tools import _search_google_docs_datastore, _PROJECT_ID, _LOCATION

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


@router.get("/summary")
async def product_summary(
    product_name: str = Query(..., description="Google Cloud product name, e.g. 'Compute Engine'")
) -> Dict:
    """Return one synthesized paragraph summarizing a product, built from datastore snippets."""
    try:
        # raise_on_error=True here (unlike the agent's own tool calls) so a
        # genuine datastore/permissions failure surfaces as a real error
        # instead of silently looking identical to "no docs exist".
        chunks = _search_google_docs_datastore(query=product_name, limit=5, raise_on_error=True)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Documentation search backend failed: {error}",
        )

    if not chunks:
        return {"product": product_name, "summary": "No documentation found for this product."}

    snippet_block = "\n\n".join(
        f"- {c['title']}: {c['text']}" for c in chunks if c.get("text")
    )

    client = genai.Client(vertexai=True, project=_PROJECT_ID, location=_LOCATION)
    prompt = (
        f"Based only on the following documentation snippets about '{product_name}', "
        "write a clear, plain-language summary that covers exactly these three things, "
        "in this order, as flowing prose (not bullet points):\n"
        "1. What the product is\n"
        "2. What it consists of (its main components, architecture, or how it's structured)\n"
        "3. What it's used for (common use cases and who it's for)\n\n"
        "Write 3-4 well-developed paragraphs — one per point is fine, or combine points 2 and 3 "
        "if that reads better. Go into real detail for each point rather than a single quick line. "
        "Do not invent details not present below. If the snippets don't cover one of the three "
        "points, skip that point rather than guessing.\n\n"
        f"{snippet_block}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return {"product": product_name, "summary": response.text.strip()}