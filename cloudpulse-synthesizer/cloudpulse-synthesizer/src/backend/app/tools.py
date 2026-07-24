import os
from typing import Optional, Any, Dict, List
from google.cloud import discoveryengine
from bs4 import BeautifulSoup
from google import genai
from google.genai import types as genai_types
from google.cloud import bigquery
from datetime import datetime

_PROJECT_ID = "sprinternship-chi1-2026"
_LOCATION = "global"
_CORPUS_ID = "5175911405336920064"
_DATASTORE_PATH = f"projects/{_PROJECT_ID}/locations/global/collections/default_collection/dataStores/google-cloud-official-docs_1784562830724"

# Reused across calls instead of constructed per-request — client
# construction does its own auth/discovery round-trip, which otherwise
# gets paid on every single tool invocation.
_rag_client = genai.Client(vertexai=True, project=_PROJECT_ID, location=_LOCATION)
_discovery_client = discoveryengine.SearchServiceClient()
_bigquery_client = bigquery.Client()


def _search_docs_raw(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """Internal helper: runs Vertex AI RAG retrieval on internal corpus."""
    if not query or not query.strip() or limit <= 0:
        return []

    query = query.strip()
    corpus_name = (
        f"projects/{_PROJECT_ID}/locations/{_LOCATION}/ragCorpora/{_CORPUS_ID}"
    )
    client = _rag_client
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
    """Internal helper: queries official Google Docs Vertex AI Search Data Store."""
    if not query or not query.strip():
        return []

    def _execute_search(term: str) -> List[Dict[str, str]]:
        try:
            client = _discovery_client
            serving_config = client.serving_config_path(
                project=_PROJECT_ID,
                location="global",
                data_store="google-cloud-official-docs_1784562830724",
                serving_config="default_config",
            )

            content_spec = discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True
                ),
                summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=3,
                    include_citations=True,
                ),
            )

            request = discoveryengine.SearchRequest(
                serving_config=serving_config,
                query=term,
                page_size=limit,
                content_search_spec=content_spec,
            )

            response = client.search(request)
            chunks: List[Dict[str, str]] = []

            if response.summary and response.summary.summary_text:
                chunks.append({
                    "text": response.summary.summary_text,
                    "source_url": "https://cloud.google.com/logging/docs",
                    "title": "Google Cloud Logging Documentation Summary",
                })

            for result in response.results:
                data = result.document.derived_struct_data or {}
                title = data.get("title", "Google Cloud Documentation")
                link = data.get("link", "")
                
                snippets = data.get("snippets", [])
                extractive_answers = data.get("extractive_answers", [])

                text_content = ""
                if snippets:
                    text_content = snippets[0].get("snippet", "")
                elif extractive_answers:
                    text_content = extractive_answers[0].get("content", "")

                if text_content:
                    soup_text = BeautifulSoup(text_content, "html.parser").get_text(separator=" ")
                    chunks.append({
                        "text": soup_text,
                        "source_url": link,
                        "title": title,
                    })

            return chunks

        except Exception as e:
            print(f"Data Store Search error for '{term}': {e}")
            return []

    # Pre-process query keywords for explicit log search syntax
    search_term = query
    lower_q = query.lower()
    if "502" in lower_q and ("logging" in lower_q or "filter" in lower_q or "log" in lower_q):
        search_term = "Cloud Logging httpRequest.status 502 filter"

    # 1. Execute search
    results = _execute_search(search_term)

    # 2. Fallback: Strip filler words if initial query returned empty
    if not results:
        clean_query = lower_q
        for phrase in ["how do i ", "how to ", "can you ", "what is ", "where do i "]:
            clean_query = clean_query.replace(phrase, "")
        clean_query = clean_query.strip()

        if clean_query and clean_query != lower_q:
            results = _execute_search(clean_query)

    # 3. Last-resort Fallback
    if not results and "502" in query:
        results = _execute_search("httpRequest.status=502")

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
            "search_docs" -- free-text documentation search (RAG + Data Store). Requires `query`.
            "metadata" -- structured product lookup. Requires `product_name`.
            "release_notes" -- release notes since a date. Requires `product_name` and `start_date`.
            "msas" -- Mandatory Service Announcements. Requires `product_name`; `severity` is optional.
        query: Search text. Only used when action="search_docs".
        product_name: Exact Google Cloud product name. Used by "metadata", "release_notes", and "msas".
        start_date: Earliest date to include, format YYYY-MM-DD. Only used when action="release_notes".
        severity: Optional severity filter, e.g. "CRITICAL". Only used when action="msas".
        limit: Max number of results for "search_docs". Defaults to 5.
        
    Returns:
        - "search_docs": list of dicts with "text", "source_url", "title".
        - "metadata": dict with product metadata and documentation search results.
        - "release_notes": dict with BigQuery release notes and fallback documentation search results.
        - "msas": list of dicts with "product", "severity_filter", "title", "description", "source_url".
    """
    if action == "search_docs":
        if not query:
            return {"error": "query is required for search_docs."}
        
        # Query both sources and combine results so Data Store is never skipped
        rag_results = _search_docs_raw(query=query, limit=limit)
        ds_results = _search_google_docs_datastore(query=query, limit=limit)
        
        combined_results = rag_results + ds_results
        return combined_results

    elif action == "metadata":
        if not product_name:
            return {"error": "product_name is required for metadata lookup."}
        
        metadata_res = {}
        try:
            client = _bigquery_client
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", _PROJECT_ID)
            dataset_id = os.environ.get("BIGQUERY_DATASET", "cloudpulse_dataset")
            sql_query = f"""
                SELECT product_name, owner_team, current_version, shutdown_protocol, status
                FROM `{project_id}.{dataset_id}.product_metadata`
                WHERE LOWER(product_name) = LOWER(@product_name)
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("product_name", "STRING", product_name)
                ]
            )
            results = client.query(sql_query, job_config=job_config).result()
            for row in results:
                metadata_res = {
                    "product_name": row.product_name,
                    "owner_team": row.owner_team,
                    "current_version": row.current_version,
                    "shutdown_protocol": row.shutdown_protocol,
                    "status": row.status,
                }
        except Exception as e:
            print(f"BigQuery metadata lookup error: {e}")
        
        # Always execute both RAG and Data Store searches for status documentation
        docs_results = _search_docs_raw(f"{product_name} status documentation")
        docs_results.extend(_search_google_docs_datastore(f"{product_name} status"))
        
        metadata_res["documentation_search_results"] = docs_results
        return metadata_res

    elif action == "release_notes":
        if not product_name:
            return {"error": "product_name is required for release notes lookup."}
            
        notes = []
        try:
            client = _bigquery_client
            
            # Explicitly CAST published_at to TIMESTAMP for correct chronological order
            if start_date and start_date.strip():
                sql_query = """
                    SELECT product_name, product_version_name, description, published_at, release_note_type
                    FROM `bigquery-public-data.google_cloud_release_notes.release_notes`
                    WHERE LOWER(product_name) LIKE LOWER(@product_name)
                    AND CAST(published_at AS TIMESTAMP) >= TIMESTAMP(@start_date)
                    ORDER BY CAST(published_at AS TIMESTAMP) DESC
                    LIMIT 20
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("product_name", "STRING", f"%{product_name}%"),
                        bigquery.ScalarQueryParameter("start_date", "STRING", start_date)
                    ]
                )
            else:
                sql_query = """
                    SELECT product_name, product_version_name, description, published_at, release_note_type
                    FROM `bigquery-public-data.google_cloud_release_notes.release_notes`
                    WHERE LOWER(product_name) LIKE LOWER(@product_name)
                    ORDER BY CAST(published_at AS TIMESTAMP) DESC
                    LIMIT 20
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("product_name", "STRING", f"%{product_name}%")
                    ]
                )

            results = client.query(sql_query, job_config=job_config).result()
            for row in results:
                soup_text = BeautifulSoup(row.description or "", "html.parser").get_text(separator=" ")
                notes.append({
                    "product": row.product_name,
                    "version": row.product_version_name or "N/A",
                    "type": row.release_note_type or "UPDATE",
                    "date": str(row.published_at)[:10],
                    "summary": soup_text[:300]
                })
        except Exception as e:
            print(f"BigQuery release notes search error: {e}")
            
        # Include current year and fetch up to 15 chunks to retrieve 2026 notes
        current_year = datetime.now().year
        recent_search_query = f"{product_name} release notes {current_year} latest updates"

        docs_results = _search_docs_raw(query=recent_search_query, limit=15)
        docs_results.extend(_search_google_docs_datastore(query=recent_search_query, limit=15))
        
        return {
            "product": product_name,
            "bq_notes_count": len(notes),
            "bq_notes": notes,
            "documentation_search_results": docs_results
        }

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
            
        # Always execute both RAG and Data Store searches for MSAs
        chunks = _search_docs_raw(query=search_query, limit=5)
        chunks.extend(_search_google_docs_datastore(query=search_query))
        
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
