import os
import warnings

# Hide ADC user credentials notices to keep output clean
warnings.filterwarnings("ignore", category=UserWarning)

from google import genai
from google.genai import types

def test_google_docs_grounding(prompt_text: str):
    project_id = os.getenv("GCP_PROJECT", "sprinternship-chi1-2026")
    
    # Client for global Vertex AI Search Data Store
    search_client = genai.Client(
        vertexai=True,
        project=project_id,
        location="global"
    )

    # Official Google Cloud Docs Grounding via Google Search Tool
    google_search_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    print("🔍 Direct Test: Querying with Live Google Search Grounding...\n")
    
    try:
        response = search_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_text,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                temperature=0.2
            )
        )
        response_text = response.text or "No text returned from Data Store."

        # -------------------------------------------------------------
        # 📌 Grounding Debug Inspection Snippet (Safe Iteration)
        # -------------------------------------------------------------
        candidate = response.candidates[0] if response.candidates else None
        grounding_meta = getattr(candidate, "grounding_metadata", None) if candidate else None
        chunks = getattr(grounding_meta, "grounding_chunks", []) or []

        if chunks:
            print("--- GROUNDED SOURCES RETRIEVED ---")
            for chunk in chunks:
                if hasattr(chunk, "web") and chunk.web:
                    print(f"• Source URL: {chunk.web.uri}")
                    print(f"  Title: {chunk.web.title}")
            print("------------------------------------\n")
        else:
            print("⚠️ No grounded chunks returned from Data Store.\n")

        return response_text

    except Exception as e:
        return f"Error querying Data Store: {e}"

if __name__ == "__main__":
    test_prompt = "What is the exact Logging query syntax to filter for HTTP status code 502 Bad Gateway errors in Cloud Logging?"
    answer = test_google_docs_grounding(test_prompt)
    print("--- Response ---")
    print(answer)