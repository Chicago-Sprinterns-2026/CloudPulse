import sys
from google.cloud import aiplatform
from langchain_google_vertexai import VertexAIEmbeddings

def test_vertex_connection():
    # Target values assigned from your team's project architecture guide
    PROJECT_ID = "sprinternship-chi1-2026"
    LOCATION = "us-central1"
    
    print(f"🔄 Initializing Vertex AI Platform for Project: {PROJECT_ID}...")
    try:
        # Step 1: Initialize the underlying Google Cloud AI Platform SDK
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        
        # Step 2: Attempt to spin up the cloud embedding model class
        # Using Google's updated professional standard model
        embeddings = VertexAIEmbeddings(
            model_name="text-embedding-004",
            project=PROJECT_ID,
            location=LOCATION
        )
        print("✅ Model Class configured successfully.")
        
        # Step 3: Force a live execution test (this tests actual IAM credentials)
        print("📡 Sending sample query to Vertex AI vector API endpoints...")
        sample_text = "Testing CloudPulse RAG connectivity for Sprinternship 2026."
        
        # This calls the remote Google server API
        vector_result = embeddings.embed_query(sample_text)
        
        print("\n🎉 SUCCESS! CONNECTION GRANTED!")
        print(f"-> Generated a clean embedding vector with {len(vector_result)} dimensions.")
        print("-> Your cloud account has full permissions. You can use Pattern 1.")
        
    except Exception as e:
        print("\n❌ CONNECTION DENIED / ERROR DETECTED")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("="*60)
        print("\n💡 ACTION PLAN:")
        print("If you see 'PermissionDenied (403)' or 'API Not Enabled (403)', drop Vertex AI")
        print("and tell the AI pod to pivot immediately to our Local Sandbox fallback game plan.")
        sys.exit(1)

if __name__ == "__main__":
    test_vertex_connection()