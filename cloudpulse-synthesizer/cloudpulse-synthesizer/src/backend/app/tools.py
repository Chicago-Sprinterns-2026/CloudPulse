import os
from typing import Optional, Any, Dict, List
from google.cloud import discoveryengine

from google import genai
from google.genai import types as genai_types
from google.cloud import bigquery

_PROJECT_ID = "sprinternship-chi1-2026"
_LOCATION = "us-central1"
_CORPUS_ID = "5175911405336920064"
_DATASTORE_PATH = f"projects/{_PROJECT_ID}/locations/global/collections/default_collection/dataStores/google-cloud-official-docs_1784562830724"


def _search_docs_raw(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """Internal helper: runs Vertex AI RAG retrieval on internal corpus."""
    if not query or not query.strip() or limit <= 0:
        return []

    query = query.strip()
    corpus_name = (
        f"projects/{_PROJECT_ID}/locations/{_LOCATION}/ragCorpora/{_CORPUS_ID}"
    )
    client = genai.Client(vertexai=True, project=_PROJECT_ID, location=_LOCATION)
    rag_tool = genai_types.Tool(
        retrieval=genai_types.Retrieval(
            vertex_rag_store=genai_types.VertexRagStore(
                rag_corpora=[corpus_name],
                similarity_top_k=limit,
            )
        )
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=genai_types.GenerateContentConfig(tools=[rag_tool], temperature=0.2),
        )
    except Exception as error:
        print(f"RAG document search warning: {error}")
        return []

    chunks: List[Dict[str, str]] = []
    try:
        grounding_chunks = response.candidates[0].grounding_metadata.grounding_chunks
        for gc in grounding_chunks[:limit]:
            ctx = getattr(gc, "retrieved_context", None)
            if not ctx or not getattr(ctx, "text", None):
                continue
            chunks.append({
                "text": ctx.text.strip(),
                "source_url": getattr(ctx, "uri", "") or "",
                "title": getattr(ctx, "title", "") or "",
            })
    except (AttributeError, IndexError, TypeError):
        if response.text:
            chunks.append({"text": response.text.strip(), "source_url": "", "title": ""})

    return chunks


def _search_google_docs_datastore(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """Internal helper: queries the official Google Docs Vertex AI Search Data Store."""
    if not query or not query.strip():
        return []

    try:
        client = discoveryengine.SearchServiceClient()
        serving_config = client.serving_config_path(
            project=_PROJECT_ID,
            location="global",
            data_store="google-cloud-official-docs_1784562830724",
            serving_config="default_config",
        )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=limit,
        )

        response = client.search(request)
        chunks: List[Dict[str, str]] = []

        for result in response.results:
            data = result.document.derived_struct_data
            title = data.get("title", "Google Cloud Documentation")
            link = data.get("link", "")
            
            # Extract text snippet from search result
            snippets = data.get("snippets", [])
            text_content = snippets[0].get("snippet", "") if snippets else ""

            if text_content:
                chunks.append({
                    "text": text_content,
                    "source_url": link,
                    "title": title,
                })

        return chunks

    except Exception as e:
        print(f"Data Store Search error: {e}")
        return []


def cloudpulse_tool(
    action: str,
    query: Optional[str] = None,
    product_name: Optional[str] = None,
    start_date: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 5,
) -> Any:
    """Single tool for docs search, product metadata, release notes, and MSAs.

    Args:
        action: Which operation to perform. Must be one of:
            "search_docs" -- free-text documentation search (RAG + Data Store). Requires `query`.
            "metadata" -- structured product lookup. Requires `product_name`.
            "release_notes" -- release notes since a date. Requires `product_name`
                and `start_date`.
            "msas" -- Mandatory Service Announcements. Requires `product_name`;
                `severity` is optional.
        query: Search text. Only used when action="search_docs".
        product_name: Exact Google Cloud product name. Used by "metadata",
            "release_notes", and "msas".
        start_date: Earliest date to include, format YYYY-MM-DD. Only used
            when action="release_notes".
        severity: Optional severity filter, e.g. "CRITICAL". Only used when
            action="msas".
        limit: Max number of results for "search_docs". Defaults to 5.

    Returns:
        - "search_docs": list of dicts with "text", "source_url", "title".
        - "metadata": dict with product metadata, or {"error": ...}.
        - "release_notes": list of dicts with "product_name", "release_date",
          "description", "release_note_type".
        - "msas": list of dicts with "product", "severity_filter", "title",
          "description", "source_url".
    """
    if action == "search_docs":
        if not query:
            return {"error": "query is required for search_docs."}

        # 1. Search internal RAG corpus
        results = _search_docs_raw(query=query, limit=limit)

        # 2. Fallback to Google Docs Data Store if no internal results found
        if not results:
            results = _search_google_docs_datastore(query=query)

        return results

    elif action == "metadata":
        if not product_name:
            return {"error": "product_name is required for metadata lookup."}
        try:
            client = bigquery.Client()
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", _PROJECT_ID)
            dataset_id = os.environ.get("BIGQUERY_DATASET", "your_default_dataset")

            sql_query = f"""
                SELECT product_name, owner_team, current_version, shutdown_protocol, status
                FROM `{project_id}.{dataset_id}.product_metadata`
                WHERE product_name = @product_name
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("product_name", "STRING", product_name)
                ]
            )
            results = client.query(sql_query, job_config=job_config).result()

            for row in results:
                return {
                    "product_name": row.product_name,
                    "owner_team": row.owner_team,
                    "current_version": row.current_version,
                    "shutdown_protocol": row.shutdown_protocol,
                    "status": row.status,
                }
            return {"product": product_name, "error": "No metadata found."}

        except Exception as e:
            return {"error": f"Failed to query BigQuery: {str(e)}"}

    elif action == "release_notes":
        if not product_name or not start_date:
            return {"error": "product_name and start_date are required for release notes."}
        try:
            client = bigquery.Client()
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", _PROJECT_ID)
            dataset_id = os.environ.get("BIGQUERY_DATASET", "your_default_dataset")
            table_id = f"{project_id}.{dataset_id}.release_notes_table"

            sql_query = f"""
                SELECT product_name, release_date, description, release_note_type
                FROM `{table_id}`
                WHERE LOWER(product_name) = LOWER(@product_name)
                AND release_date >= CAST(@start_date AS DATE)
                ORDER BY release_date DESC
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("product_name", "STRING", product_name),
                    bigquery.ScalarQueryParameter("start_date", "STRING", start_date),
                ]
            )
            results = client.query(sql_query, job_config=job_config).result()
            return [dict(row) for row in results]

        except Exception as e:
            print(f"Error fetching release notes from BigQuery: {e}")
            return []

    elif action == "msas":
        if not product_name or not product_name.strip():
            return []

        search_query = (
            f"Mandatory Service Announcements for {product_name}. "
            "Find required actions, deprecations, security changes, "
            "effective dates, deadlines, and service impacts."
        )
        if severity:
            search_query += f" Only return announcements with severity {severity}."

        # 1. Try internal search
        chunks = _search_docs_raw(query=search_query, limit=5)

        # 2. Fallback to Google Docs Data Store
        if not chunks:
            chunks = _search_google_docs_datastore(query=search_query)

        return [
            {
                "product": product_name,
                "severity_filter": severity,
                "title": chunk.get("title", ""),
                "description": chunk.get("text", ""),
                "source_url": chunk.get("source_url", ""),
            }
            for chunk in chunks
        ]

    else:
        return {
            "error": f"Unknown action '{action}'. Must be one of: "
            "search_docs, metadata, release_notes, msas."
        }