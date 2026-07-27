"""Visual asset generation: propose a visual, then render it.

    from app.visuals import propose_visual, build_spec, render_visual
"""

from app.visuals.planner import build_spec, propose_visual
from app.visuals.renderers import render_visual
from app.visuals.schemas import (
    DiagramSpec,
    IllustrationSpec,
    InfographicSpec,
    VisualProposal,
)

__all__ = [
    "propose_visual",
    "build_spec",
    "render_visual",
    "VisualProposal",
    "InfographicSpec",
    "DiagramSpec",
    "IllustrationSpec",
]