import os
from typing import Optional, Any, Dict, List
 
import agentplatform
from agentplatform import types
from google.genai import types as genai_types
from google.cloud import bigquery


from langchain_google_community import VertexAIAgentBuilderRetriever
 
_PROJECT_ID = "sprinternship-chi1-2026"
_LOCATION = "us-central1"
_CORPUS_ID = "5175911405336920064"
_DATA_STORE_LOCATION = "global"
_DATA_STORE_ID = "google-cloud-official-docs_1784562830724"
 
 
def _search_docs_raw(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """Internal helper: runs Vertex AI RAG retrieval, not exposed to the model."""
    if not query or not query.strip() or limit <= 0:
        return []
 
    query = query.strip()
    corpus_name = (
        f"projects/{_PROJECT_ID}/locations/{_LOCATION}/ragCorpora/{_CORPUS_ID}"
    )
    client = agentplatform.Client(project=_PROJECT_ID, location=_LOCATION)
 
    try:
        response = client.rag.retrieve_contexts(
            vertex_rag_store=genai_types.VertexRagStore(
                rag_resources=[
                    genai_types.VertexRagStoreRagResource(rag_corpus=corpus_name)
                ]
            ),
            query=types.RagQuery(
                text=query,
                rag_retrieval_config=genai_types.RagRetrievalConfig(top_k=limit),
            ),
        )
    except Exception as error:
        raise RuntimeError(f"RAG document search failed: {error}") from error
 
    chunks: List[Dict[str, str]] = []
    if response.contexts:
        for context in response.contexts.contexts:
            if not context.text or not context.text.strip():
                continue
            chunks.append(
                {
                    "text": context.text.strip(),
                    "source_url": context.source_uri or "",
                    "title": context.source_display_name or "",
                }
            )
            if len(chunks) >= limit:
                break
    return chunks


def _search_datastore_raw(
    query: str,
    limit: int = 5,
) -> List[Dict[str, str]]:
    """Internal helper: searches the Google Cloud documentation data store."""


    if not query or not query.strip() or limit <= 0:
        return []


    retriever = VertexAIAgentBuilderRetriever(
        project_id=_PROJECT_ID,
        location_id=_DATA_STORE_LOCATION,
        data_store_id=_DATA_STORE_ID,
    )


    try:
        documents = retriever.invoke(query.strip())
    except Exception as error:
        raise RuntimeError(
            f"Data store search failed: {error}"
        ) from error


    results: List[Dict[str, str]] = []


    for document in documents[:limit]:
        metadata = document.metadata or {}
        text = (document.page_content or "").strip()


        if not text:
            continue


        results.append(
            {
                "text": text,
                "title": metadata.get("title", ""),
                "source_url": (
                    metadata.get("source", "")
                    or metadata.get("uri", "")
                    or metadata.get("link", "")
                    or metadata.get("source_url", "")
                ),
            }
        )


    return results
 
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
            "search_docs" -- free-text documentation search (RAG). Requires `query`.
            "search_datastore" -- searches the Google Cloud documentation data store.
            Requires `query`.
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
        - "search_datastore": list of dicts with "text", "source_url", "title".
        - "metadata": dict with product metadata, or {"error": ...}.
        - "release_notes": list of dicts with "product_name", "release_date",
          "description", "release_note_type".
        - "msas": list of dicts with "product", "severity_filter", "title",
          "description", "source_url".
    """
    if action == "search_docs":
        if not query:
            return {"error": "query is required for search_docs."}


        return _search_docs_raw(
            query=query,
            limit=limit,
        )


    elif action == "search_datastore":
        if not query:
            return {
                "error": "query is required for search_datastore."
            }


        return _search_datastore_raw(
            query=query,
            limit=limit,
        )


    elif action == "metadata":
        if not product_name:
            return {"error": "product_name is required for metadata lookup."}
        try:
            client = bigquery.Client()
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-default-project")
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
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-default-project")
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
 
        chunks = _search_docs_raw(query=search_query, limit=5)
        return [
            {
                "product": product_name,
                "severity_filter": severity,
                "title": chunk["title"],
                "description": chunk["text"],
                "source_url": chunk["source_url"],
            }
            for chunk in chunks
        ]
 
    else:
        return {
            "error": f"Unknown action '{action}'. Must be one of: "
            "search_docs, search_datastore, metadata, release_notes, msas."
        }

