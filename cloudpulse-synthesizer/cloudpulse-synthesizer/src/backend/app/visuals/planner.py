"""Decides whether a visual would help, and which kind.

Two stages, on purpose:

  propose_visual()  One cheap text call over recent conversation. Returns an
                    offer or nothing. Nothing is rendered, nothing is billed
                    beyond a short completion.

  build_spec()      Runs only after the user accepts. Produces the full,
                    schema-validated spec for the chosen asset type.

Splitting them matters because illustrations cost real money per image, and
because an unsolicited visual on every turn is noise. The user says yes first.

The routing rule the planner is held to: **if the visual needs to be factually
correct, it cannot be an illustration.** Image models draw text as pixels, so
anything carrying a date, a count, or a product name goes to infographic or
diagram, where our own renderer places every string.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.tools import _PROJECT_ID, _LOCATION
from app.visuals.schemas import (
    DiagramSpec,
    IllustrationSpec,
    InfographicSpec,
    VisualProposal,
)

_TEXT_MODEL = "gemini-2.5-flash"

_client = genai.Client(vertexai=True, project=_PROJECT_ID, location=_LOCATION)

_RETRY = types.HttpRetryOptions(initial_delay=1, attempts=5)


PROPOSE_INSTRUCTION = """
You decide whether a visual would genuinely help the user in a Google Cloud
support conversation, and if so, which of exactly three kinds to build.

Return should_offer = false unless a visual adds something the text cannot.
Most turns do not need one. Short factual answers, yes/no answers, code
snippets, and simple definitions never need one. Offering constantly is worse
than never offering, because it trains the user to ignore the offer.

Choose the asset type by what the visual has to carry:

infographic — carries FACTS. Dates, counts, versions, comparisons, "what
  changed", release timelines, breakdowns by category, before/after numbers.
  Every string you provide is rendered exactly as written, so it must be
  correct and drawn only from the conversation.

diagram — carries STRUCTURE. How components connect, request flow, architecture,
  a sequence of stages, decision paths. Anything the user would otherwise draw
  on a whiteboard.

illustration — carries MOOD or ANALOGY only. A conceptual picture where no
  precise text is needed. Use sparingly. If the visual would need a single
  accurate label, date, or number, it is NOT an illustration — pick one of the
  other two.

`pitch` is shown to the user verbatim as an offer, so write it as one short
inviting sentence, e.g. "Want me to sketch how these components fit together?"

`subject` should name the specific thing the visual is about (product,
architecture, or comparison), so the next stage knows what to build.

Return ONLY a JSON object, no markdown fences, matching:
{
  "should_offer": boolean,
  "asset_type": "infographic" | "diagram" | "illustration" | null,
  "title": string | null,
  "pitch": string | null,
  "reason": string | null,
  "subject": string | null
}
""".strip()


_SPEC_INSTRUCTIONS = {
    "infographic": """
Build an infographic spec. Every string is rendered verbatim by a deterministic
renderer, so treat this as publishing, not drafting.

Rules:
- Use ONLY facts present in the conversation below. Invent nothing. If you do
  not have a number, omit the stat rather than estimating one.
- `value` in stats is rendered as-is and must be short ("14", "3 days", "99.9%").
- Prefer 3 stats over 4, 5 timeline entries over 7. Crowding kills legibility.
- Include at least one of: stats, timeline, bars, callout.
- Set `bars_title` whenever you provide bars.
- Respect every max length; text is clipped, not shrunk, when it overflows.

Return ONLY a JSON object matching:
{
  "title": string,
  "subtitle": string | null,
  "stats": [{"value": string, "label": string, "caption": string | null}],
  "timeline": [{"date": string, "title": string, "detail": string | null,
                "emphasis": boolean}],
  "bars": [{"label": string, "value": number, "display_value": string | null}],
  "bars_title": string | null,
  "callout": {"tone": "info"|"warning"|"success", "text": string} | null,
  "footer": string | null
}
""".strip(),

    "diagram": """
Build a diagram spec. You supply nodes and edges; layout, spacing, and arrows
are handled by the renderer, so do not describe positions.

Rules:
- `layer` is the column (horizontal) or row (vertical) index, starting at 0.
  Nodes sharing a layer are drawn side by side. Flow goes from layer 0 outward.
- Keep to 4-9 nodes. Beyond that the diagram stops being readable and starts
  being a map.
- Every edge's source and target must be an existing node id. Dangling edges
  are silently dropped.
- `kind` picks the styling: service (a GCP service), store (database/bucket),
  external (outside the system), decision (a branch point), default (anything
  else).
- Edge labels are optional and should be 1-3 words ("writes", "on failure").

Return ONLY a JSON object matching:
{
  "title": string,
  "subtitle": string | null,
  "direction": "horizontal" | "vertical",
  "nodes": [{"id": string, "label": string, "layer": number,
             "kind": "default"|"service"|"store"|"external"|"decision",
             "note": string | null}],
  "edges": [{"source": string, "target": string, "label": string | null,
             "style": "solid"|"dashed"}]
}
""".strip(),

    "illustration": """
Build an illustration spec for an image generation model.

Rules:
- `prompt` is prose describing a single clear conceptual image. Describe the
  subject, composition, palette, and mood.
- Do NOT ask for text, labels, numbers, logos, or UI screenshots in the image.
  The model renders text as approximate shapes and it will look wrong.
- Do not depict real people, brand marks, or copyrighted characters.
- Favour clean, calm, professional imagery suitable next to technical writing.
- Palette suggestion: Google blue #4285F4, red #EA4335, yellow #FBBC05,
  green #34A853 on white, unless the conversation implies otherwise.

Return ONLY a JSON object matching:
{
  "title": string,
  "prompt": string,
  "aspect_ratio": "1:1" | "16:9" | "4:3" | "3:2",
  "style": "flat_vector" | "isometric" | "line_art" | "soft_3d",
  "avoid_text": boolean
}
""".strip(),
}

_SPEC_MODELS = {
    "infographic": InfographicSpec,
    "diagram": DiagramSpec,
    "illustration": IllustrationSpec,
}


def _strip_fences(text: str) -> str:
    """Models wrap JSON in ```json fences often enough to be worth handling."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _generate_json(instruction: str, context: str, temperature: float) -> Dict[str, Any]:
    response = _client.models.generate_content(
        model=_TEXT_MODEL,
        contents=f"{instruction}\n\n--- CONVERSATION ---\n{context}",
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            http_options=types.HttpOptions(retry_options=_RETRY),
        ),
    )
    raw = _strip_fences(response.text or "")
    if not raw:
        raise ValueError("planner returned an empty response")
    return json.loads(raw)


def _format_conversation(messages: List[Dict[str, str]], limit: int = 8) -> str:
    recent = messages[-limit:]
    return "\n\n".join(
        f"{m.get('role', 'user').upper()}: {(m.get('content') or '').strip()[:1500]}"
        for m in recent
        if (m.get("content") or "").strip()
    )


def propose_visual(messages: List[Dict[str, str]]) -> VisualProposal:
    """Should we offer a visual for this conversation, and of what kind?

    Never raises. A planner failure means no offer -- the chat continues
    untouched, which is the correct degradation for an optional enhancement.
    """
    context = _format_conversation(messages)
    if not context:
        return VisualProposal(should_offer=False)

    try:
        # Low temperature: this is a routing decision, not a creative one, and
        # we want the same conversation to route the same way twice.
        data = _generate_json(PROPOSE_INSTRUCTION, context, temperature=0.1)
        proposal = VisualProposal(**data)
    except (ValidationError, ValueError, json.JSONDecodeError) as error:
        print(f"Visual planner returned unusable output: {error}")
        return VisualProposal(should_offer=False)
    except Exception as error:
        print(f"Visual planner call failed: {error}")
        return VisualProposal(should_offer=False)

    # An offer with no type or no pitch can't be rendered or displayed.
    if proposal.should_offer and (not proposal.asset_type or not proposal.pitch):
        return VisualProposal(should_offer=False)

    return proposal


def build_spec(
    asset_type: str,
    messages: List[Dict[str, str]],
    subject: Optional[str] = None,
    title: Optional[str] = None,
) -> Any:
    """Produce a validated spec for `asset_type`. Raises on failure.

    Callers should surface the failure rather than substituting a different
    asset type -- silently downgrading an infographic to an illustration would
    turn a factual request into a decorative image.
    """
    instruction = _SPEC_INSTRUCTIONS.get(asset_type)
    model_cls = _SPEC_MODELS.get(asset_type)
    if instruction is None or model_cls is None:
        raise ValueError(f"Unknown asset_type: {asset_type!r}")

    context = _format_conversation(messages)
    if subject:
        context += f"\n\nThe visual should be about: {subject}"
    if title:
        context += f"\n\nSuggested title: {title}"

    # Illustrations get a little more latitude; the other two are transcription
    # tasks where creativity is a liability.
    temperature = 0.6 if asset_type == "illustration" else 0.2

    data = _generate_json(instruction, context, temperature=temperature)
    spec = model_cls(**data)

    if asset_type == "infographic" and not spec.has_content():
        raise ValueError("infographic spec had a title but no content sections")

    return spec