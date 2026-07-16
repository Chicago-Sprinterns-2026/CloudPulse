import os
import json
import html
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from google.cloud import bigquery
from google.cloud import storage

# Setup targets
BUCKET_NAME = "cloudpulse-raw-docs-2026"
DESTINATION_PATH = "release-notes/latest_release_notes.json"

def clean_html_content(raw_html):
    """
    Takes a raw HTML string and returns formatted, clean plain-text 
    by resolving HTML entities and stripping out tag elements.
    """
    if not raw_html:
        return ""
    
    # Unescape common HTML entities (e.g., &#39; to ' or &gt; to >) 
    unescaped_html = html.unescape(raw_html)
    
    # Parse HTML structure
    soup = BeautifulSoup(unescaped_html, "html.parser")
    
    # Format list items nicely as markdown bullet points
    for li in soup.find_all("li"):
        li.insert_before("\n* ")
        
    # Get text and clean up redundant line breaks
    text = soup.get_text()
    cleaned_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    
    return cleaned_text

def fetch_and_upload_bq_release_notes():
    # Pass your actual project ID to the clients explicitly 
    PROJECT_ID = "sprinternship-chi1-2026"
    
    bq_client = bigquery.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # Define SQL targeting the public dataset verified in Cloud Console [cite: 591, 592]
    query = """
        SELECT 
            CAST(published_at AS STRING) as date, 
            product_name, 
            description 
        FROM `bigquery-public-data.google_cloud_release_notes.release_notes` 
        WHERE DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        ORDER BY published_at DESC
    """
    
    print("Executing query against BigQuery Public Dataset...")
    query_job = bq_client.query(query)
    results = query_job.result() # Awaits query execution completion
    
    # Structure rows cleanly into objects with parsed text [cite: 594]
    release_records = []
    for row in results:
        release_records.append({
            "date": row.date, # [cite: 596]
            "product": row.product_name, # [cite: 597]
            "update": clean_html_content(row.description) # Cleaned on-the-fly [cite: 598]
        })
        
    # Wrap with standard internal pipeline metadata [cite: 588]
    payload = {
        "metadata": {
            "source": "bigquery-public-dataset", # [cite: 591]
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(), # [cite: 592]
            "records_count": len(release_records) # [cite: 593]
        },
        "releases": release_records # [cite: 594]
    }
    
    # Save the structured file directly into the bucket
    json_data = json.dumps(payload, ensure_ascii=False, indent=2)
    blob = bucket.blob(DESTINATION_PATH)
    blob.upload_from_string(json_data, content_type="application/json")
    print(f"-> Successfully extracted BigQuery rows and uploaded JSON to gs://{BUCKET_NAME}/{DESTINATION_PATH}")

if __name__ == "__main__":
    fetch_and_upload_bq_release_notes()