import os
import json
from datetime import datetime, timezone
from google.cloud import storage

BUCKET_NAME = "cloudpulse-raw-docs-2026"
LOCAL_SOURCE_PATH = "/home/kduggirala/CloudPulse/cloudpulse-synthesizer/cloudpulse-synthesizer/data/Data_Pipeline/real_msa_email_source.txt"
DESTINATION_PATH = "msas/latest_msas.json"
PROJECT_ID = "sprinternship-chi1-2026"

def parse_multi_tagged_emails():
    if not os.path.exists(LOCAL_SOURCE_PATH):
        print(f"[ERROR] Source file not found at {LOCAL_SOURCE_PATH}.")
        return []

    print(f"📖 Reading and parsing text file from: {LOCAL_SOURCE_PATH}...")
    with open(LOCAL_SOURCE_PATH, "r", encoding="utf-8") as f:
        full_text = f.read()

    # Split the file dynamically by the 3 dashes
    email_blocks = full_text.split("\n---\n")
    parsed_announcements = []

    for index, block in enumerate(email_blocks):
        if not block.strip():
            continue

        # Build individual announcement object blueprint
        parsed_data = {
            "announcement_id": f"MSA-REAL-TEMPLATE-{index+1:03d}",
            "title": "Unknown Title",
            "category": "Unknown Category",
            "impacted_service": "Unknown Service",
            "severity": "MEDIUM",
            "effective_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "action_required": False,
            "description": ""
        }

        lines = block.strip().splitlines()
        capturing_content = False
        content_lines = []

        for line in lines:
            stripped = line.strip()
            
            # Map tags dynamically
            if stripped.upper().startswith("TITLE:"):
                parsed_data["title"] = line.split(":", 1)[1].strip()
            elif stripped.upper().startswith("CATEGORY:"):
                parsed_data["category"] = line.split(":", 1)[1].strip()
            elif stripped.upper().startswith("SERVICE:"):
                parsed_data["impacted_service"] = line.split(":", 1)[1].strip()
            elif stripped.upper().startswith("SEVERITY:"):
                parsed_data["severity"] = line.split(":", 1)[1].strip().upper()
            elif stripped.upper().startswith("DATE:"):
                parsed_data["effective_date"] = line.split(":", 1)[1].strip()
            elif stripped.upper().startswith("ACTION_REQUIRED:"):
                val = line.split(":", 1)[1].strip().upper()
                parsed_data["action_required"] = (val == "TRUE")
            elif stripped.upper().startswith("CONTENT:"):
                capturing_content = True
            elif capturing_content:
                content_lines.append(line)

        parsed_data["description"] = "\n".join(content_lines).strip()
        parsed_announcements.append(parsed_data)

    return parsed_announcements

def convert_real_msa_to_pipeline_json():
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    announcements = parse_multi_tagged_emails()
    if not announcements:
        print("❌ Error: Parsing returned 0 announcements.")
        return

    # Wrap inside our standard pipeline JSON container
    payload = {
        "metadata": {
            "source": "real-email-msa-multi-template",
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "records_count": len(announcements)
        },
        "announcements": announcements
    }
    
    json_data = json.dumps(payload, ensure_ascii=False, indent=2)
    
    # 1. Write the output to GCS Bucket
    blob = bucket.blob(DESTINATION_PATH)
    blob.upload_from_string(json_data, content_type="application/json")
    print(f"-> Cloud Upload Successful: gs://{BUCKET_NAME}/{DESTINATION_PATH}")

    # 2. Save a local copy in your workspace
    os.makedirs("msas", exist_ok=True)
    with open(DESTINATION_PATH, "w", encoding="utf-8") as local_file:
        local_file.write(json_data)
    print(f"✅ Local copy saved to: {DESTINATION_PATH}")

if __name__ == "__main__":
    convert_real_msa_to_pipeline_json()
