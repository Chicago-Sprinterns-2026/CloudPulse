import os
from google import genai
from google.genai import types

def generate_unified_cloudpulse_response(prompt_text: str):
    """
    Queries Gemini using Vertex AI RAG Corpus Grounding.
    """
    # 1. Initialize the Gen AI SDK client
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GCP_PROJECT", "sprinternship-chi1-2026"),
        location="us-central1"
    )

    # 2. Configure RAG Corpus Tool using rag_corpora
    corpus_resource_name = "projects/sprinternship-chi1-2026/locations/us-central1/ragCorpora/5175911405336920064"

    rag_corpus_tool = types.Tool(
        retrieval=types.Retrieval(
            vertex_rag_store=types.VertexRagStore(
                rag_corpora=[corpus_resource_name],
                similarity_top_k=5
            )
        )
    )

    print("🤖 Synthesizing answer using CloudPulse RAG Corpus...\n")

    # 3. Call Gemini with RAG Corpus grounding
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_text,
        config=types.GenerateContentConfig(
            tools=[rag_corpus_tool],
            temperature=0.2
        )
    )

    return response.text

if __name__ == "__main__":
    test_prompt = "What are the latest critical migration updates for Gemini and historical release notes?"
    answer = generate_unified_cloudpulse_response(test_prompt)
    print("--- Response ---")
    print(answer)