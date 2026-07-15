# CloudPulse Synthesizer

CloudPulse is an AI-powered Google Cloud Product Synthesizer created for the
Chicago Sprinternship 2026 Challenge. It is designed to ingest public Google
Cloud documentation, release notes, and Mandatory Service Announcements,
then use a Retrieval-Augmented Generation pipeline to produce concise
one-pagers and grounded troubleshooting responses.

## Planned Features

- Product update one-pager generation
- Persona-aware summaries for architects, sales representatives, TAMs, and developers
- Troubleshooting chatbot with verifiable source links
- Product catalog and technology-stack filtering
- BigQuery metadata storage
- Vertex AI Search semantic retrieval
- Gemini-powered generation
- Downloadable TXT and PDF one-pagers

## Architecture

1. The ingestion pipeline collects public Google Cloud documents.
2. The cleaner removes irrelevant markup and normalizes content.
3. Structured metadata is stored in BigQuery.
4. Processed documents are indexed in Vertex AI Search.
5. LangChain or custom orchestration retrieves relevant document chunks.
6. Gemini synthesizes a one-pager or troubleshooting response.
7. Streamlit presents the result and its source references.

## Repository Structure

```text
cloudpulse-synthesizer/
├── .github/workflows/
├── data/raw/
├── data/processed/
├── database/
├── src/ingestion/
├── src/backend/
├── src/frontend/
└── tests/
```

## Local Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and replace the placeholder values.

```bash
cp .env.example .env
```

Authenticate with Google Cloud using Application Default Credentials:

```bash
gcloud auth application-default login
```

### 4. Run the Streamlit application

```bash
streamlit run src/frontend/app.py
```

### 5. Run tests

```bash
pytest
```

## Suggested First Milestone

For the moderate project approach:

1. Select a small set of Google Cloud products.
2. Manually download or fetch several release-note pages.
3. Clean and store the content as JSON.
4. Create the BigQuery metadata table.
5. Import processed documents into Vertex AI Search.
6. Implement one working retrieval function.
7. Connect retrieval results to Gemini.
8. Display the grounded response in Streamlit.

## Security Notes

- Never commit service-account files or API keys.
- Prefer Application Default Credentials during local development.
- Store deployment secrets in GitHub Actions secrets or the target cloud platform.
- Validate source URLs before scraping.
- Respect public-site terms, rate limits, and robots.txt rules.

## Project Status

This repository is an initial scaffold. Google Cloud integrations are marked
with `TODO` comments and should be implemented using the project credentials,
datastore identifiers, and APIs approved by the Sprinternship team.
