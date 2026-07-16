import os
import json
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.vectorstores import FAISS

# Target workspace paths matching your team repository guidelines
JSON_FILE_PATH = "release-notes/latest_release_notes.json"
VECTOR_DB_DIR = "release-notes/faiss_index"

def run_data_ingestion():
    print("🚀 Initializing CloudPulse Ingestion Pipeline (Vertex AI + FAISS)...")
    
    # 1. Verification Check: Confirm clean JSON source exists
    if not os.path.exists(JSON_FILE_PATH):
        print(f"❌ Error: Source file not found at {JSON_FILE_PATH}.")
        print("Please run bigquery.py first to extract the source data.")
        return

    # 2. Read the structured release notes payload
    print("📖 Loading structured release logs from workspace...")
    with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
        
    releases = payload.get("releases", [])
    print(f"-> Found {len(releases)} clean update records to process.")

    # 3. Restructure payload entries into LangChain Document formats
    raw_documents = []
    for item in releases:
        # We enrich the main text layout so the model keeps track of product/date context
        contextual_body = (
            f"Product: {item['product']}\n"
            f"Release Date: {item['date']}\n"
            f"Update details:\n{item['update']}"
        )
        # Store metadata variables alongside text chunk for granular filtering later
        metadata = {
            "product": item["product"],
            "date": item["date"],
            "source": "google_cloud_release_notes"
        }
        raw_documents.append(Document(page_content=contextual_body, metadata=metadata))

    # 4. Chunk text blocks into windowed sizes to handle prompt token capacity safely
    # chunk_size=1000 with a 150-character overlap balances semantic context windowing
    print("✂️ Splitting product blocks into overlapping token chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = text_splitter.split_documents(raw_documents)
    print(f"-> Created {len(docs)} text chunks optimized for RAG embeddings.")

    # 5. Connect to Google Cloud Vertex AI Embeddings (Pydantic-friendly)
    print("🧠 Initializing Vertex AI text-embedding-004 Engine...")
    embeddings = VertexAIEmbeddings(
        model_name="text-embedding-004",
        project="sprinternship-chi1-2026",
        location="us-central1"
    )

    # 6. Generate vector metrics in batches to respect the 20,000 token API limit
    print("📡 Communicating with Vertex AI API in batches...")
    
    # We will process 40 document chunks at a time
    BATCH_SIZE = 40
    vector_store = None
    
    for i in range(0, len(docs), BATCH_SIZE):
        batch_docs = docs[i:i + BATCH_SIZE]
        print(f"-> Processing batch {i // BATCH_SIZE + 1} ({len(batch_docs)} chunks)...")
        
        if vector_store is None:
            # First batch initializes the index
            vector_store = FAISS.from_documents(batch_docs, embeddings)
        else:
            # Subsequent batches are merged cleanly into our existing store
            batch_store = FAISS.from_documents(batch_docs, embeddings)
            vector_store.merge_from(batch_store)
    
    # 7. Persist the generated index vector matrix to your repository
    print("📁 Saving compiled vector binaries to local workspace directory...")
    vector_store.save_local(VECTOR_DB_DIR)
    
    print("\n✅ INGESTION PIPELINE SUCCESS!")
    print(f"-> Vector database matrix generated with 768 dimensions per slice.")
    print(f"-> FAISS indexing directory created successfully at: {VECTOR_DB_DIR}")

if __name__ == "__main__":
    run_data_ingestion()