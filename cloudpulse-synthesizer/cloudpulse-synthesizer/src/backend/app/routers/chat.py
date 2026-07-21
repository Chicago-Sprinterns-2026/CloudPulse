from fastapi import APIRouter
from pydantic import BaseModel
from app.agent import run_agent

router = APIRouter(prefix="/api", tags=["agent"])

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

@router.post("/chat")
async def chat(request: ChatRequest):
    response = await run_agent(request.message, request.session_id)
    return {"response": response}