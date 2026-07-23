from dotenv import load_dotenv
load_dotenv()  # must run before importing chat/agent, so env vars are set when root_agent is built

import os
print("VERTEXAI:", os.getenv("GOOGLE_GENAI_USE_VERTEXAI"))
print("PROJECT:", os.getenv("GOOGLE_CLOUD_PROJECT"))
print("LOCATION:", os.getenv("GOOGLE_CLOUD_LOCATION"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, pdf


app = FastAPI(title="Agent API")


# CORS — required so your React frontend (different origin) can call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "*"  # your deployed frontend, once you have it
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Wire in your routers
app.include_router(chat.router)
app.include_router(pdf.router)
# app.include_router(product.router)


@app.get("/")
async def root():
    return {"status": "ok"}