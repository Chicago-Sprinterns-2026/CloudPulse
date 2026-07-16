import json
from datetime import datetime, timezone
from google.cloud import bigquery
from google.cloud import storage

# Setup targets
BUCKET_NAME = "cloudpulse-raw-docs-2026"
DESTINATION_PATH = "release-notes/latest_release_notes.json"

def fetch_and_upload_bq_release_notes():
    # Pass your actual project ID to the clients explicitly
    PROJECT_ID = "sprinternship-chi1-2026"  # Taken from your original console link
    
    bq_client = bigquery.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # Define SQL targeting the public dataset verified in Cloud Console
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
    
    # Structure rows cleanly into objects
    release_records = []
    for row in results:
        release_records.append({
            "date": row.date,
            "product": row.product_name,
            "update": row.description
        })
        
    # Wrap with standard internal pipeline metadata
    payload = {
        "metadata": {
            "source": "bigquery-public-dataset",
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "records_count": len(release_records)
        },
        "releases": release_records
    }
    
    # Save the structured file directly into the bucket
    json_data = json.dumps(payload, ensure_ascii=False, indent=2)
    blob = bucket.blob(DESTINATION_PATH)
    blob.upload_from_string(json_data, content_type="application/json")
    print(f"-> Successfully extracted BigQuery rows and uploaded JSON to gs://{BUCKET_NAME}/{DESTINATION_PATH}")

if __name__ == "__main__":
    fetch_and_upload_bq_release_notes()