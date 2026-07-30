# CloudPulse

CloudPulse is an AI-powered Google Cloud "Product Synthesizer" built for the
Chicago Sprinternship 2026 Challenge. It's a RAG-backed chatbot and content
generator that helps engineers, architects, and sales/TAM roles stay current
on Google Cloud products — grounded troubleshooting answers, one-pager
summaries, live release notes, and generated visuals, all sourced from real
GCP documentation and public datasets rather than the model's own training
data.

## Features

- **Grounded troubleshooting chatbot** (`PulseChat`) — answers Google Cloud
  questions using retrieval-augmented generation, with source citations and
  a confidence indicator per response. Supports file attachments (PDF/DOCX)
  so a user can ask questions about their own document, follow-up "chip"
  suggestions, stop/regenerate controls, and per-conversation chat history
  (New Chat button, a history panel keyed by session).
- **One-pager generation** — synthesizes a structured, print-ready one-pager
  (executive summary, what changed, why it matters, impacted
  users/workloads, recommended actions, sources) for one or more products at
  once, downloadable as PDF.
- **Live release notes feed** — paginated, keyset-cursor feed read directly
  from `bigquery-public-data.google_cloud_release_notes`, so it's never a
  stale point-in-time snapshot. Filterable per-product release history is
  also available from each product's detail page.
- **Visual explainers** — on-demand infographics, diagrams, and
  illustrations generated to accompany a chat answer, proposed only when
  actually useful (a cheap "should we offer a visual" check runs before any
  billed image generation).
- **Product catalog & directory** — browse all supported GCP products by
  category, with a detail page combining documentation and release history
  tabs per product.
- **Guest mode** — try the app without signing in.

## Architecture

- **Frontend**: React + Vite, served as a static build behind nginx.
- **Backend**: FastAPI, orchestrated with Google's Agent Development Kit
  (google-adk) and LangChain/LangGraph, calling Gemini via Vertex AI.
- **Retrieval**: a Vertex AI RAG corpus and a Vertex AI Search Data Store
  (both over public GCP documentation), plus BigQuery for product metadata
  and the live release notes public dataset.
- **Deployment**: two separate Cloud Run services — `cloudpulse` (frontend)
  and `cloudpulsebackend` (backend) — each continuously deployed via a Cloud
  Build trigger on push to `main`. The frontend's nginx config
  (`frontend-app/nginx.conf`) reverse-proxies `/api/*` to the backend
  service, so the browser only ever talks to one origin and CORS isn't a
  concern for that path.

Request flow for a chat message: browser → same-origin `/api/chat` → nginx
proxy → backend `routers/chat.py` → `agent.py`'s `run_agent()` → an ADK
`Runner` wrapping a Gemini agent with `cloudpulse_tool` registered → Gemini
decides whether to call the tool → the tool dispatches to RAG retrieval,
the public Data Store, and/or BigQuery depending on the requested action →
results return to Gemini as a function response → the grounded answer comes
back to the browser.

## Project structure

The repo root has a redundant `cloudpulse-synthesizer/cloudpulse-synthesizer/`
wrapper around the actual project (a historical artifact, not yet cleaned
up) — everything below is relative to that inner folder, which is what you
should `cd` into for all the commands in this README.

```text
cloudpulse-synthesizer/cloudpulse-synthesizer/
├── .github/workflows/       CI (test job; deploy step is a placeholder —
│                             actual deploys run via Cloud Build triggers,
│                             not this workflow)
├── data/
│   └── Data_Pipeline/        one-off/ad-hoc data ingestion scripts (BigQuery
│                              extraction, MSA fetching, RAG corpus grounding)
├── database/
│   ├── bq_schemas/           BigQuery table DDL (product metadata)
│   └── vector_store/         Vertex AI Search Data Store setup script
├── frontend-app/             React + Vite frontend
│   ├── src/                  components (App, catalog, dashboard, chatbot,
│   │                          product directory/detail, release history,
│   │                          visual explainer, chat history panel, etc.)
│   ├── public/                static assets, generated release-data JSON
│   ├── scripts/                build-time data generation
│   ├── Dockerfile / nginx.conf  container build + reverse proxy config
│   └── vite.config.js
├── src/backend/               FastAPI backend
│   └── app/
│       ├── main.py             FastAPI app, CORS, router registration
│       ├── agent.py             ADK agent, run_agent(), one-pager generation
│       ├── tools.py              cloudpulse_tool — RAG + Data Store + BigQuery
│       ├── release_notes_source.py / release_note_links.py
│       ├── prompt_templates.py
│       ├── visuals/              visual-explainer planning + rendering
│       └── routers/              chat, pdf, product, release_notes, upload,
│                                   visuals — one module per API surface
├── tests/                     pytest suite
├── .env                       backend environment config (not committed
│                                with real secrets — see Local setup)
└── README.md
```

Both `frontend-app/` and `src/backend/` are self-contained Docker build
contexts (each Dockerfile's own directory is its build root), which is what
Cloud Build's continuous-deployment triggers point at.

## Local setup

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r src/backend/requirements.txt
gcloud auth application-default login
```

Create `.env` at the repo root with:

```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Optional — defaults to "cloudpulse_dataset" if unset.
BIGQUERY_DATASET=cloudpulse_dataset
```

Run the backend:

```bash
cd src/backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend-app
npm install
```

Create `frontend-app/.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

Run the frontend:

```bash
npm run dev
```

### Tests

```bash
pytest
```

## Deployment

Both Cloud Run services (`cloudpulse`, `cloudpulsebackend`) deploy
automatically on push to `main` via their own Cloud Build trigger — each
trigger's build config (build → push → `gcloud run services update`) lives
inline in the trigger itself, not as a `cloudbuild.yaml` in the repo. The
backend service needs its own environment variables (matching `.env` above)
set directly on the Cloud Run service, since nothing in `.env` reaches the
container — it's excluded from the Docker build context.
