import os
import requests
from bs4 import BeautifulSoup
from google.cloud import storage

# Read bucket dynamically
BUCKET_NAME = "cloudpulse-raw-docs-2026"
#os.environ.get("GCS_BUCKET_NAME", "cloudpulse-raw-docs-2026")

# 1. Define a dictionary matching target pages to their folder paths in Cloud Storage
SOURCES = {
    "release-notes": "https://cloud.google.com/release-notes",
    # Swapped to Google's terms of service, which is static and scrapes perfectly:
    "msas": "https://policies.google.com/terms", 
}

def scrape_and_upload():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    # 2. Loop through each source url
    for doc_type, url in SOURCES.items():
        print(f"Scraping {doc_type} from {url}...")
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            clean_text = soup.get_text(separator='\n')
            
            # 3. Save to a unique folder path based on the document type
            # e.g., "release-notes/latest.txt" or "msas/latest.txt"
            destination_path = f"{doc_type}/latest_{doc_type}.txt"
            
            blob = bucket.blob(destination_path)
            blob.upload_from_string(clean_text)
            print(f"-> Successfully uploaded {doc_type} to gs://{BUCKET_NAME}/{destination_path}")
        else:
            print(f"-> [ERROR] Failed to fetch {doc_type}: Status Code {response.status_code}")

if __name__ == "__main__":
    scrape_and_upload()
