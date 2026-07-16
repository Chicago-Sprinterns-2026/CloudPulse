import os
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings, ChatVertexAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Workspace paths
VECTOR_DB_DIR = "release-notes/faiss_index"

def generate_cloud_pulse_response(user_query: str) -> dict:
    """
    Loads the FAISS index database, searches for context, and uses Vertex AI 
    to generate an accurate chat response or structured product one-pager.
    """
    PROJECT_ID = "sprinternship-chi1-2026"
    LOCATION = "us-central1"
    
    if not os.path.exists(VECTOR_DB_DIR):
        raise FileNotFoundError(f"FAISS index folder missing at {VECTOR_DB_DIR}. Please run ingest.py first.")

    # 1. Initialize our embedding model wrapper to process the user's inquiry query
    embeddings = VertexAIEmbeddings(
        model_name="text-embedding-004",
        project=PROJECT_ID,
        location=LOCATION
    )
    
    # 2. Load the compiled FAISS vector index database safely from the workspace
    vector_store = FAISS.load_local(
        VECTOR_DB_DIR, 
        embeddings, 
        allow_dangerous_deserialization=True # Required for loading local file binaries safely
    )
    
    # 3. Create a retriever to fetch the top 4 most semantically relevant documentation chunks
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    
    # 4. Initialize Google's current standard generation engine on Vertex AI
    llm = ChatVertexAI(
        model="gemini-2.5-flash", # Migrated to the active model tier
        project=PROJECT_ID,
        location=LOCATION,
        temperature=0.2 
    )
    
    # 5. Craft an explicit system prompt optimized for your engineering & TAM use-cases
    system_prompt = (
        "You are an expert Google Cloud Solutions Architect and Technical Account Manager.\n"
        "Your mission is to synthesize complex, technical release updates into highly actionable answers.\n\n"
        "Instructions:\n"
        "- If the user asks for a 'one-pager', format your response with clean Markdown headers: "
        "### Executive Summary, ### Key Feature Upgrades, and ### Breaking Changes / Actions Required.\n"
        "- Base your response ONLY on the provided context below. Do not make up facts.\n"
        "- For every feature or update you mention, include an inline citation indicating which Google Cloud product it belongs to.\n\n"
        "Contextual Documentation Chunks:\n"
        "{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    # 6. Assemble the LangChain retrieval QA chain execution block
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    # 7. Run the query execution block
    print(f"📡 Querying CloudPulse RAG engine for: '{user_query}'...")
    response = rag_chain.invoke({"input": user_query})
    
    return {
        "answer": response["answer"],
        "source_documents": response.get("context", [])
    }

# Standalone manual verification test block
if __name__ == "__main__":
    # Test Use Case 7: The Startup CTO requesting a summary
    test_query = "Give me a one-pager summary for the latest Cloud SQL updates."
    try:
        result = generate_cloud_pulse_response(test_query)
        print("\n✨ [TEST OUTPUT ANSWER]:\n")
        print(result["answer"])
    except Exception as e:
        print(f"\n❌ Test Failed: {str(e)}")