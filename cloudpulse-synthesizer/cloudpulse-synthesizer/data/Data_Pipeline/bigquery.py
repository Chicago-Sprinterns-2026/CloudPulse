import os
import json
import html
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from google.cloud import bigquery
from google.cloud import storage

BUCKET_NAME = "cloudpulse-raw-docs-2026"
DESTINATION_PATH = "release-notes/latest_release_notes.json"
PROJECT_ID = "sprinternship-chi1-2026"

def clean_html_content(raw_html):
    if not raw_html: return ""
    unescaped_html = html.unescape(raw_html)
    soup = BeautifulSoup(unescaped_html, "html.parser")
    for li in soup.find_all("li"):
        li.insert_before("\n* ")
    text = soup.get_text()
    return "\n".join([line.strip() for line in text.splitlines() if line.strip()])

def fetch_and_upload_bq_release_notes():
    bq_client = bigquery.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    query = """
        SELECT CAST(published_at AS STRING) as date, product_name, description 
        FROM `bigquery-public-data.google_cloud_release_notes.release_notes` 
        WHERE DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        ORDER BY published_at DESC
    """
    
    print("Executing query against BigQuery Public Dataset...")
    query_job = bq_client.query(query)
    results = query_job.result()
    
    release_records = []
    for row in results:
        release_records.append({
            "date": row.date,
            "product": row.product_name,
            "update": clean_html_content(row.description)
        })
        
    payload = {
        "metadata": {
            "source": "bigquery-public-dataset",
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "records_count": len(release_records)
        },
        "releases": release_records
    }
    
    json_data = json.dumps(payload, ensure_ascii=False, indent=2)
    blob = bucket.blob(DESTINATION_PATH)
    blob.upload_from_string(json_data, content_type="application/json")
    print(f"✅ Live Cloud Upload Successful: gs://{BUCKET_NAME}/{DESTINATION_PATH}")

if __name__ == "__main__":
    fetch_and_upload_bq_release_notes()