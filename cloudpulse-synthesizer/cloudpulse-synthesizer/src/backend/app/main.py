# app/main.py
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pdf
# chat router intentionally not wired yet — routers/chat.py is still a stub,
# a teammate is building it and will push their own version

app = FastAPI(title="Agent API")

# CORS — required so your React frontend (different origin) can call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",       # local React dev
        "https://your-frontend.web.app"  # your deployed frontend, once you have it
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire in your router
app.include_router(pdf.router)

@app.get("/")
async def root():
    return {"status": "ok"}