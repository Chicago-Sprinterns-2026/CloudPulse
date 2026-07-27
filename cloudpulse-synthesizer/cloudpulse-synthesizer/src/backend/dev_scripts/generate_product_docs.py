# src/backend/dev_scripts/generate_product_docs.py
import json
import time
import httpx
import os

API_BASE = "https://cloudpulsebackend-1098468887328.us-central1.run.app"
INPUT_NAMES_PATH = os.path.join(os.path.dirname(__file__), "product-names.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../../../frontend-app/src/data/productDocs.json")

def generate_docs():
    with open(INPUT_NAMES_PATH) as f:
        product_names = json.load(f)

    docs = {}
    failed = []

    with httpx.Client(timeout=60.0) as client:
        for name in product_names:
            print(f"Fetching: {name}")
            try:
                resp = client.get(
                    f"{API_BASE}/api/products/summary",
                    params={"product_name": name},
                )
                resp.raise_for_status()
                data = resp.json()
                docs[name] = data["summary"]
            except Exception as e:
                print(f"  Failed: {name} — {e}")
                failed.append(name)

            time.sleep(0.5)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(docs, f, indent=2)

    print(f"\nWrote {len(docs)} docs to {OUTPUT_PATH}")
    if failed:
        print(f"Failed ({len(failed)}): {failed}")

if __name__ == "__main__":
    generate_docs()