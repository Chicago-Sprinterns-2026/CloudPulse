"""Schemas for the three visual asset types.

The strictness gradient is the whole design. Each type gets exactly as much
structure as its failure mode demands:

  infographic  STRICT     Carries facts -- dates, counts, product names. Every
                          string is placed by our own renderer, so what the
                          model writes is what the user reads. A hallucinated
                          number here is a wrong number in front of a customer,
                          so the schema is tight and validated.

  diagram      SEMI       Carries structure -- boxes, arrows, flow. The layout
                          is ours; the model only supplies nodes and edges. It
                          can invent shapes we don't support, but it can't
                          produce something misleading in the way a wrong
                          statistic is misleading.

  illustration LOOSE      Carries mood. No data, minimal text, generated as
                          pixels by an image model. Text inside generated
                          images is unreliable, which is exactly why this type
                          is reserved for content where text doesn't matter.

That gradient is also the routing rule: if a visual needs to be *correct*, it
must not be an illustration.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

AssetType = Literal["infographic", "diagram", "illustration"]


# --------------------------------------------------------------------------- #
# Infographic -- strict
# --------------------------------------------------------------------------- #

class StatBlock(BaseModel):
    """A single headline number. `value` is rendered verbatim, so the model must
    write it exactly as it should appear ("14", "3 days", "99.95%")."""
    value: str = Field(max_length=12)
    label: str = Field(max_length=40)
    caption: Optional[str] = Field(default=None, max_length=70)


class TimelineEntry(BaseModel):
    date: str = Field(max_length=24)
    title: str = Field(max_length=60)
    detail: Optional[str] = Field(default=None, max_length=140)
    emphasis: bool = False


class BarItem(BaseModel):
    label: str = Field(max_length=32)
    value: float
    display_value: Optional[str] = Field(default=None, max_length=12)

    @field_validator("value")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("bar values must be >= 0")
        return v


class Callout(BaseModel):
    tone: Literal["info", "warning", "success"] = "info"
    text: str = Field(max_length=200)


class InfographicSpec(BaseModel):
    """At least one content section must be present, otherwise we'd render an
    empty card with a title -- worse than no visual at all."""
    title: str = Field(max_length=70)
    subtitle: Optional[str] = Field(default=None, max_length=110)
    stats: List[StatBlock] = Field(default_factory=list, max_length=4)
    timeline: List[TimelineEntry] = Field(default_factory=list, max_length=7)
    bars: List[BarItem] = Field(default_factory=list, max_length=8)
    bars_title: Optional[str] = Field(default=None, max_length=50)
    callout: Optional[Callout] = None
    footer: Optional[str] = Field(default=None, max_length=90)

    @field_validator("stats", "timeline", "bars", mode="before")
    @classmethod
    def none_to_empty(cls, value):
        """Models write "bars": null rather than omitting the key. A default
        only applies when a key is absent, so coerce the explicit null."""
        return [] if value is None else value

    def has_content(self) -> bool:
        """An infographic needs enough material to be worth the space.

        A title plus a single callout is a sentence in a box — it takes more
        room than the sentence and implies more substance than it has. Require
        either a real content section, or at least two elements together.
        """
        sections = sum(1 for s in (self.stats, self.timeline, self.bars) if s)
        if sections:
            return True
        return False


# --------------------------------------------------------------------------- #
# Diagram -- semi-strict
# --------------------------------------------------------------------------- #

class DiagramNode(BaseModel):
    id: str = Field(max_length=32)
    label: str = Field(max_length=44)
    # `layer` drives horizontal placement: same layer = same column. The model
    # decides grouping; we decide pixels.
    layer: int = Field(ge=0, le=6)
    kind: Literal["default", "service", "store", "external", "decision"] = "default"
    note: Optional[str] = Field(default=None, max_length=60)


class DiagramEdge(BaseModel):
    source: str = Field(max_length=32)
    target: str = Field(max_length=32)
    label: Optional[str] = Field(default=None, max_length=28)
    style: Literal["solid", "dashed"] = "solid"


class DiagramSpec(BaseModel):
    title: str = Field(max_length=70)
    subtitle: Optional[str] = Field(default=None, max_length=110)
    nodes: List[DiagramNode] = Field(min_length=2, max_length=14)
    edges: List[DiagramEdge] = Field(default_factory=list, max_length=24)
    direction: Literal["horizontal", "vertical"] = "horizontal"

    @field_validator("edges", mode="before")
    @classmethod
    def none_to_empty(cls, value):
        return [] if value is None else value

    @field_validator("edges")
    @classmethod
    def edges_reference_real_nodes(cls, edges, info):
        nodes = info.data.get("nodes") or []
        ids = {n.id for n in nodes}
        # Drop dangling edges rather than rejecting the whole diagram -- a model
        # inventing one bad edge id shouldn't cost the user their visual.
        return [e for e in edges if e.source in ids and e.target in ids]


# --------------------------------------------------------------------------- #
# Illustration -- loose
# --------------------------------------------------------------------------- #

class IllustrationSpec(BaseModel):
    """`prompt` goes to an image model, so it's prose, not structure.

    `avoid_text` defaults to True on purpose: image models render text as
    pixels that resemble letters, and misspelled labels in an otherwise polished
    graphic read as carelessness. If a visual needs words, it should have been
    routed to infographic or diagram.
    """
    title: str = Field(max_length=70)
    prompt: str = Field(max_length=900)
    aspect_ratio: Literal["1:1", "16:9", "4:3", "3:2"] = "16:9"
    style: Literal["flat_vector", "isometric", "line_art", "soft_3d"] = "flat_vector"
    avoid_text: bool = True


# --------------------------------------------------------------------------- #
# Planner output
# --------------------------------------------------------------------------- #

class VisualProposal(BaseModel):
    """What the planner returns *before* anything is rendered.

    Split from the spec deliberately: proposing is one cheap text call, building
    is a more expensive call (and for illustrations, a paid image generation).
    The user gets to decline in between.
    """
    should_offer: bool
    asset_type: Optional[AssetType] = None
    title: Optional[str] = Field(default=None, max_length=70)
    # Shown to the user as the offer text, so it reads as an invitation.
    pitch: Optional[str] = Field(default=None, max_length=140)
    # Not shown -- kept for logging and for tuning the planner prompt later.
    reason: Optional[str] = Field(default=None, max_length=200)
    subject: Optional[str] = Field(default=None, max_length=120)