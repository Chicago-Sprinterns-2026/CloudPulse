import json
import os
from google.cloud import bigquery
from bs4 import BeautifulSoup

def extract_and_chunk_historical_release_notes():
    client = bigquery.Client(project="sprinternship-chi1-2026")
    
    query = """
        SELECT 
            product_name, 
            product_version_name, 
            description, 
            published_at, 
            release_note_type
        FROM 
            `bigquery-public-data.google_cloud_release_notes.release_notes`
        ORDER BY 
            published_at DESC
    """
    
    print("⏳ Querying entire Google Cloud release notes history database...")
    query_job = client.query(query)
    results = query_job.result()
    
    cleaned_records = []
    for row in results:
        raw_html = row.description if row.description else ""
        soup = BeautifulSoup(raw_html, "html.parser")
        clean_text = soup.get_text(separator=" ").strip()
        
        cleaned_records.append({
            "product_name": row.product_name,
            "product_version": row.product_version_name,
            "description": clean_text,
            "publish_date": str(row.published_at),
            "release_note_type": row.release_note_type
        })

    # 🌟 FIX: Split the massive array into smaller chunks (5,000 records per file)
    chunk_size = 5000
    output_dir = "/home/znoman/CloudPulse/chunks"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📦 Total records retrieved: {len(cleaned_records)}. Splitting into files...")
    
    file_counter = 1
    for i in range(0, len(cleaned_records), chunk_size):
        chunk = cleaned_records[i:i + chunk_size]
        output_path = f"{output_dir}/release_notes_part_{file_counter}.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunk, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Generated: {output_path} ({len(chunk)} records)")
        file_counter += 1

    print("🎉 All parts successfully chunked and saved locally!")

if __name__ == "__main__":
    extract_and_chunk_historical_release_notes()