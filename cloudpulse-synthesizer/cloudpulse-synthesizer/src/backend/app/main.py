# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat # assuming your endpoint lives in routers/agent.py

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
app.include_router(chat.router)

@app.get("/")
async def root():
    return {"status": "ok"}