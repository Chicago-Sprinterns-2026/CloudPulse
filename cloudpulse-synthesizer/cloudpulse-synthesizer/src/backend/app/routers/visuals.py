"""Visual explanation endpoints.

  POST /api/visuals/propose   Should we offer a visual here, and which kind?
  POST /api/visuals/render    The user said yes -- build and render it.
  POST /api/visuals/render-direct   Skip the planner; caller names the type.

Two calls rather than one because proposing is cheap and rendering isn't
(illustrations bill per image). The chat UI calls /propose after an assistant
turn, shows the offer if there is one, and only calls /render when the user
accepts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.visuals import build_spec, propose_visual, render_visual

router = APIRouter(prefix="/api/visuals", tags=["visuals"])


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ProposeRequest(BaseModel):
    messages: List[Message] = Field(min_length=1)


class RenderRequest(BaseModel):
    messages: List[Message] = Field(min_length=1)
    asset_type: Literal["infographic", "diagram", "illustration"]
    subject: Optional[str] = None
    title: Optional[str] = None


class RenderDirectRequest(BaseModel):
    """For callers that already have a spec -- tests, or a 'regenerate as a
    diagram instead' button that shouldn't re-run the planner."""
    spec: Dict[str, Any]
    asset_type: Literal["infographic", "diagram", "illustration"]


@router.post("/propose")
async def propose(request: ProposeRequest) -> Dict[str, Any]:
    """Never fails. No offer is a valid, common answer -- most turns don't need
    a visual, and a planner outage shouldn't break the chat."""
    proposal = propose_visual([m.model_dump() for m in request.messages])
    return proposal.model_dump()


@router.post("/render")
async def render(request: RenderRequest) -> Dict[str, Any]:
    messages = [m.model_dump() for m in request.messages]

    try:
        spec = build_spec(
            asset_type=request.asset_type,
            messages=messages,
            subject=request.subject,
            title=request.title,
        )
    except Exception as error:
        print(f"Visual spec generation failed ({request.asset_type}): {error}")
        raise HTTPException(
            status_code=502,
            detail=f"Couldn't plan that visual: {error}",
        )

    try:
        result = render_visual(spec)
    except Exception as error:
        print(f"Visual render failed ({request.asset_type}): {error}")
        raise HTTPException(
            status_code=502,
            detail=f"Couldn't render that visual: {error}",
        )

    # Echoed back so the client can show what the visual was built from, and so
    # a "regenerate" button has something to resend.
    result["spec"] = spec.model_dump()
    return result


@router.post("/render-direct")
async def render_direct(request: RenderDirectRequest) -> Dict[str, Any]:
    try:
        return render_visual({"asset_type": request.asset_type, **request.spec})
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Couldn't render that spec: {error}")