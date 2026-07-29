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

On length limits: these clamp rather than reject. An earlier version used
`max_length`, which meant a model writing 210 characters where 200 were allowed
produced no visual at all -- the user asked for a picture and got a pydantic
traceback. The renderer already wraps and ellipsises overflowing text, so a
slightly-too-long string is a cosmetic issue at worst. Failing the whole render
over one is not a trade worth making.
"""

from __future__ import annotations

from typing import Annotated, List, Literal, Optional

from pydantic import BaseModel, BeforeValidator, Field, field_validator

AssetType = Literal["infographic", "diagram", "illustration"]


# --------------------------------------------------------------------------- #
# Length clamping
# --------------------------------------------------------------------------- #

def _clamp(limit: int):
    """Truncate an over-long string instead of rejecting it."""
    def _apply(value):
        if isinstance(value, str) and len(value) > limit:
            return value[: limit - 1].rstrip() + "…"
        return value
    return _apply


def Text(limit: int):
    """A string field that silently truncates past `limit` characters."""
    return Annotated[str, BeforeValidator(_clamp(limit))]


def OptText(limit: int):
    """Optional variant of `Text`."""
    return Annotated[Optional[str], BeforeValidator(_clamp(limit))]


def _none_to_empty(value):
    """Models write "bars": null rather than omitting the key. A default only
    applies when a key is absent, so coerce the explicit null."""
    return [] if value is None else value


# --------------------------------------------------------------------------- #
# Infographic -- strict
# --------------------------------------------------------------------------- #

class StatBlock(BaseModel):
    """A single headline number. `value` is rendered verbatim at large type, so
    it must read as a number, not a sentence."""
    value: Text(12)
    label: Text(40)
    caption: OptText(70) = None


class TimelineEntry(BaseModel):
    date: Text(24)
    title: Text(60)
    detail: OptText(140) = None
    emphasis: bool = False


class BarItem(BaseModel):
    label: Text(32)
    value: float
    display_value: OptText(12) = None

    @field_validator("value", mode="before")
    @classmethod
    def non_negative(cls, v):
        # Coerce rather than reject: a stray string or negative shouldn't cost
        # the user the whole visual.
        try:
            number = float(v)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, number)


class Callout(BaseModel):
    tone: Literal["info", "warning", "success"] = "info"
    text: Text(400)


class InfographicSpec(BaseModel):
    title: Text(70)
    subtitle: OptText(110) = None
    stats: Annotated[List[StatBlock], BeforeValidator(_none_to_empty)] = Field(
        default_factory=list, max_length=4
    )
    timeline: Annotated[List[TimelineEntry], BeforeValidator(_none_to_empty)] = Field(
        default_factory=list, max_length=7
    )
    bars: Annotated[List[BarItem], BeforeValidator(_none_to_empty)] = Field(
        default_factory=list, max_length=8
    )
    bars_title: OptText(50) = None
    callout: Optional[Callout] = None
    footer: OptText(90) = None

    @field_validator("stats", "timeline", "bars", mode="before")
    @classmethod
    def trim_to_max(cls, value, info):
        """Drop extras rather than failing when the model overshoots a cap."""
        caps = {"stats": 4, "timeline": 7, "bars": 8}
        if isinstance(value, list):
            return value[: caps[info.field_name]]
        return value

    def has_content(self) -> bool:
        """An infographic needs enough material to be worth the space.

        A title plus a single callout is a sentence in a box -- it takes more
        room than the sentence and implies more substance than it has.
        """
        return bool(self.stats or self.timeline or self.bars)


# --------------------------------------------------------------------------- #
# Diagram -- semi-strict
# --------------------------------------------------------------------------- #

class DiagramNode(BaseModel):
    id: Text(32)
    label: Text(44)
    # `layer` drives placement: same layer = same column (or row). The model
    # decides grouping; we decide pixels.
    layer: int = Field(ge=0, le=6)
    kind: Literal["default", "service", "store", "external", "decision"] = "default"
    note: OptText(60) = None

    @field_validator("layer", mode="before")
    @classmethod
    def clamp_layer(cls, value):
        try:
            return max(0, min(6, int(value)))
        except (TypeError, ValueError):
            return 0


class DiagramEdge(BaseModel):
    source: Text(32)
    target: Text(32)
    label: OptText(28) = None
    style: Literal["solid", "dashed"] = "solid"


class DiagramSpec(BaseModel):
    title: Text(70)
    subtitle: OptText(110) = None
    nodes: List[DiagramNode] = Field(min_length=2, max_length=14)
    edges: Annotated[List[DiagramEdge], BeforeValidator(_none_to_empty)] = Field(
        default_factory=list
    )
    direction: Literal["horizontal", "vertical"] = "horizontal"

    @field_validator("nodes", mode="before")
    @classmethod
    def trim_nodes(cls, value):
        return value[:14] if isinstance(value, list) else value

    @field_validator("edges")
    @classmethod
    def edges_reference_real_nodes(cls, edges, info):
        nodes = info.data.get("nodes") or []
        ids = {n.id for n in nodes}
        # Drop dangling edges rather than rejecting the whole diagram -- a model
        # inventing one bad edge id shouldn't cost the user their visual.
        return [e for e in edges if e.source in ids and e.target in ids][:24]


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
    title: Text(70)
    prompt: Text(1200)
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
    title: OptText(70) = None
    # Shown to the user as the offer text, so it reads as an invitation.
    pitch: OptText(140) = None
    # Not shown -- kept for logging and for tuning the planner prompt later.
    reason: OptText(200) = None
    subject: OptText(120) = None