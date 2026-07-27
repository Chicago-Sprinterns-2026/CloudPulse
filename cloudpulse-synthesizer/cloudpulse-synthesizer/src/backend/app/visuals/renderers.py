"""Renders a visual spec into something displayable.

    infographic  -> SVG, drawn here in Python from a validated spec
    diagram      -> SVG, drawn here in Python from nodes + edges
    illustration -> PNG bytes from a Gemini image model

The first two are deterministic on purpose. An infographic about release notes
is mostly text and numbers, and the whole point is that they're *right*: laying
them out ourselves means the string in the spec is the string on screen. Asking
an image model to draw a chart gets you something that looks like a chart and
says things that aren't true.

Illustrations go to the image model precisely because nothing in them needs to
be accurate.
"""

from __future__ import annotations

import base64
import html
import os
import textwrap
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.tools import _PROJECT_ID, _LOCATION
from app.visuals.schemas import DiagramSpec, IllustrationSpec, InfographicSpec

# Nano Banana. Imagen was retired in June 2026, so the Gemini image models are
# the path on Vertex now. These are preview IDs and they move -- override with
# the env var rather than editing code when it changes.
_IMAGE_MODEL = os.getenv("VISUAL_IMAGE_MODEL", "gemini-3.1-flash-image-preview")

_client = genai.Client(vertexai=True, project=_PROJECT_ID, location=_LOCATION)
_RETRY = types.HttpRetryOptions(initial_delay=1, attempts=3)

BLUE = "#4285F4"
RED = "#EA4335"
YELLOW = "#FBBC05"
GREEN = "#34A853"
INK = "#202124"
INK_SOFT = "#5f6368"
BORDER = "#dadce0"
SURFACE = "#ffffff"
TINT = "#f1f3f4"

_FONT = "'Google Sans', 'Product Sans', Roboto, Arial, Helvetica, sans-serif"
_MONO = "'Roboto Mono', ui-monospace, Menlo, Consolas, monospace"


# --------------------------------------------------------------------------- #
# SVG helpers
# --------------------------------------------------------------------------- #

def _esc(text: Optional[str]) -> str:
    """Everything user- or model-supplied goes through here. SVG is XML, and an
    unescaped & or < silently breaks the whole document."""
    return html.escape(text or "", quote=True)


def _wrap(text: str, width: int, max_lines: int) -> List[str]:
    """Wrap to `width` chars, clipping with an ellipsis past `max_lines`.

    SVG has no text flow, so wrapping has to happen before drawing. Clipping
    rather than shrinking keeps type sizes consistent across every card.
    """
    if not text:
        return []
    lines = textwrap.wrap(text, width=width) or [""]
    if len(lines) <= max_lines:
        return lines
    kept = lines[:max_lines]
    kept[-1] = kept[-1][: max(0, width - 1)].rstrip() + "…"
    return kept


def _text(
    x: float,
    y: float,
    content: str,
    size: float = 13,
    color: str = INK,
    weight: str = "normal",
    anchor: str = "start",
    family: str = _FONT,
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
        f'fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{_esc(content)}</text>'
    )


def _svg_document(width: float, height: float, body: str, defs: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img">'
        f"{defs}"
        f'<rect width="{width:.0f}" height="{height:.0f}" rx="14" fill="{SURFACE}"/>'
        f'<rect width="{width:.0f}" height="{height:.0f}" rx="14" fill="none" stroke="{BORDER}"/>'
        f"{body}</svg>"
    )


def _accent_bar(width: float, y: float = 0) -> str:
    """The four-colour Google bar, matching the one in the PDF one-pagers."""
    quarter = width / 4
    parts = []
    for index, colour in enumerate((BLUE, RED, YELLOW, GREEN)):
        parts.append(
            f'<rect x="{index * quarter:.1f}" y="{y}" width="{quarter:.1f}" height="4" fill="{colour}"/>'
        )
    return "".join(parts)


# --------------------------------------------------------------------------- #
# Infographic
# --------------------------------------------------------------------------- #

_TONE_COLOURS = {
    "info": (BLUE, "#e8f0fe"),
    "warning": (RED, "#fce8e6"),
    "success": (GREEN, "#e6f4ea"),
}


def _render_infographic(spec: InfographicSpec) -> Dict[str, Any]:
    width = 760
    pad = 32
    y = 34  # below the accent bar

    body: List[str] = [_accent_bar(width)]

    body.append(_text(pad, y, spec.title, size=22, weight="bold"))
    y += 12

    if spec.subtitle:
        for line in _wrap(spec.subtitle, width=78, max_lines=2):
            y += 18
            body.append(_text(pad, y, line, size=13, color=INK_SOFT))
    y += 26

    # --- stat blocks -------------------------------------------------------
    if spec.stats:
        count = len(spec.stats)
        gap = 14
        box_w = (width - 2 * pad - gap * (count - 1)) / count
        box_h = 92 if any(s.caption for s in spec.stats) else 76

        for index, stat in enumerate(spec.stats):
            x = pad + index * (box_w + gap)
            accent = (BLUE, GREEN, YELLOW, RED)[index % 4]
            body.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{box_w:.1f}" height="{box_h}" '
                f'rx="10" fill="{TINT}"/>'
            )
            body.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="4" height="{box_h}" '
                f'rx="2" fill="{accent}"/>'
            )
            body.append(_text(x + 18, y + 40, stat.value, size=30, weight="bold", color=INK))
            body.append(_text(x + 18, y + 60, stat.label, size=11.5, color=INK_SOFT))
            if stat.caption:
                for offset, line in enumerate(_wrap(stat.caption, width=26, max_lines=2)):
                    body.append(_text(x + 18, y + 76 + offset * 13, line, size=10.5, color=INK_SOFT))
        y += box_h + 30

    # --- timeline ----------------------------------------------------------
    if spec.timeline:
        rail_x = pad + 8
        body.append(_text(pad, y, "Timeline", size=12, color=INK_SOFT, weight="bold"))
        y += 16
        start_y = y

        for entry in spec.timeline:
            dot_y = y + 6
            colour = RED if entry.emphasis else BLUE
            body.append(f'<circle cx="{rail_x}" cy="{dot_y}" r="5.5" fill="{colour}"/>')
            if entry.emphasis:
                body.append(
                    f'<circle cx="{rail_x}" cy="{dot_y}" r="9" fill="none" '
                    f'stroke="{colour}" stroke-opacity="0.3"/>'
                )
            body.append(_text(rail_x + 20, dot_y + 4, entry.date, size=11, color=INK_SOFT, family=_MONO))
            body.append(_text(rail_x + 108, dot_y + 4, entry.title, size=13.5, weight="bold"))
            y += 22
            if entry.detail:
                for line in _wrap(entry.detail, width=72, max_lines=2):
                    body.append(_text(rail_x + 108, y + 4, line, size=11.5, color=INK_SOFT))
                    y += 15
            y += 10

        # Rail sits behind the dots, so it's emitted after but inserted before.
        body.insert(
            1,
            f'<line x1="{rail_x}" y1="{start_y + 6}" x2="{rail_x}" y2="{y - 16}" '
            f'stroke="{BORDER}" stroke-width="2"/>',
        )
        y += 12

    # --- bars --------------------------------------------------------------
    if spec.bars:
        if spec.bars_title:
            body.append(_text(pad, y, spec.bars_title, size=12, color=INK_SOFT, weight="bold"))
            y += 18

        label_w = 150
        track_x = pad + label_w
        track_w = width - track_x - pad - 52
        peak = max((b.value for b in spec.bars), default=0) or 1

        for index, bar in enumerate(spec.bars):
            fill_w = max(2.0, (bar.value / peak) * track_w)
            colour = (BLUE, GREEN, YELLOW, RED)[index % 4]
            body.append(_text(pad, y + 13, bar.label, size=12, color=INK))
            body.append(
                f'<rect x="{track_x}" y="{y}" width="{track_w:.1f}" height="18" rx="9" fill="{TINT}"/>'
            )
            body.append(
                f'<rect x="{track_x}" y="{y}" width="{fill_w:.1f}" height="18" rx="9" fill="{colour}"/>'
            )
            shown = bar.display_value or (
                str(int(bar.value)) if float(bar.value).is_integer() else f"{bar.value:g}"
            )
            body.append(
                _text(track_x + track_w + 10, y + 13, shown, size=11.5, color=INK_SOFT, family=_MONO)
            )
            y += 28
        y += 8

    # --- callout -----------------------------------------------------------
    if spec.callout:
        accent, background = _TONE_COLOURS.get(spec.callout.tone, _TONE_COLOURS["info"])
        lines = _wrap(spec.callout.text, width=84, max_lines=3)
        box_h = 20 + len(lines) * 17
        body.append(
            f'<rect x="{pad}" y="{y:.1f}" width="{width - 2 * pad}" height="{box_h}" '
            f'rx="8" fill="{background}"/>'
        )
        body.append(
            f'<rect x="{pad}" y="{y:.1f}" width="4" height="{box_h}" rx="2" fill="{accent}"/>'
        )
        for offset, line in enumerate(lines):
            body.append(_text(pad + 18, y + 24 + offset * 17, line, size=12.5, color=INK))
        y += box_h + 18

    if spec.footer:
        y += 4
        body.append(_text(pad, y + 8, spec.footer, size=10.5, color=INK_SOFT))
        y += 16

    height = y + pad
    return {
        "asset_type": "infographic",
        "format": "svg",
        "title": spec.title,
        "content": _svg_document(width, height, "".join(body)),
        "width": width,
        "height": round(height),
    }


# --------------------------------------------------------------------------- #
# Diagram
# --------------------------------------------------------------------------- #

_NODE_STYLES = {
    "default": (TINT, BORDER, INK),
    "service": ("#e8f0fe", BLUE, "#174ea6"),
    "store": ("#e6f4ea", GREEN, "#0d652d"),
    "external": ("#ffffff", INK_SOFT, INK_SOFT),
    "decision": ("#fef7e0", YELLOW, "#b06000"),
}


def _render_diagram(spec: DiagramSpec) -> Dict[str, Any]:
    horizontal = spec.direction == "horizontal"

    layers: Dict[int, List] = {}
    for node in spec.nodes:
        layers.setdefault(node.layer, []).append(node)
    ordered_layers = sorted(layers)

    node_w, node_h = 172, 60
    gap_within = 26
    gap_between = 74
    pad = 32
    header_h = 78

    # Position every node first; edges are drawn from those coordinates.
    positions: Dict[str, Dict[str, float]] = {}
    widest = max(len(nodes) for nodes in layers.values())

    if horizontal:
        canvas_w = pad * 2 + len(ordered_layers) * node_w + (len(ordered_layers) - 1) * gap_between
        canvas_h = header_h + pad + widest * node_h + (widest - 1) * gap_within
    else:
        canvas_w = pad * 2 + widest * node_w + (widest - 1) * gap_within
        canvas_h = header_h + pad + len(ordered_layers) * node_h + (len(ordered_layers) - 1) * gap_between

    for layer_index, layer in enumerate(ordered_layers):
        nodes = layers[layer]
        if horizontal:
            x = pad + layer_index * (node_w + gap_between)
            block_h = len(nodes) * node_h + (len(nodes) - 1) * gap_within
            start_y = header_h + (canvas_h - header_h - pad - block_h) / 2
            for node_index, node in enumerate(nodes):
                positions[node.id] = {"x": x, "y": start_y + node_index * (node_h + gap_within)}
        else:
            y = header_h + layer_index * (node_h + gap_between)
            block_w = len(nodes) * node_w + (len(nodes) - 1) * gap_within
            start_x = (canvas_w - block_w) / 2
            for node_index, node in enumerate(nodes):
                positions[node.id] = {"x": start_x + node_index * (node_w + gap_within), "y": y}

    defs = (
        f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{INK_SOFT}"/></marker></defs>'
    )

    body: List[str] = [_accent_bar(canvas_w)]
    body.append(_text(pad, 38, spec.title, size=19, weight="bold"))
    if spec.subtitle:
        body.append(_text(pad, 58, _wrap(spec.subtitle, 86, 1)[0], size=12, color=INK_SOFT))

    # Edges before nodes so the boxes sit on top of the lines.
    for edge in spec.edges:
        source, target = positions.get(edge.source), positions.get(edge.target)
        if not source or not target:
            continue

        if horizontal:
            x1, y1 = source["x"] + node_w, source["y"] + node_h / 2
            x2, y2 = target["x"], target["y"] + node_h / 2
            mid = (x1 + x2) / 2
            path = f"M {x1:.1f} {y1:.1f} C {mid:.1f} {y1:.1f}, {mid:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}"
            label_x, label_y = (x1 + x2) / 2, min(y1, y2) - 8 if y1 != y2 else y1 - 8
        else:
            x1, y1 = source["x"] + node_w / 2, source["y"] + node_h
            x2, y2 = target["x"] + node_w / 2, target["y"]
            mid = (y1 + y2) / 2
            path = f"M {x1:.1f} {y1:.1f} C {x1:.1f} {mid:.1f}, {x2:.1f} {mid:.1f}, {x2:.1f} {y2:.1f}"
            label_x, label_y = (x1 + x2) / 2, (y1 + y2) / 2 - 6

        dash = ' stroke-dasharray="5 4"' if edge.style == "dashed" else ""
        body.append(
            f'<path d="{path}" fill="none" stroke="{INK_SOFT}" stroke-width="1.6"'
            f'{dash} marker-end="url(#arrow)"/>'
        )
        if edge.label:
            text_w = len(edge.label) * 6.2 + 10
            body.append(
                f'<rect x="{label_x - text_w / 2:.1f}" y="{label_y - 11:.1f}" '
                f'width="{text_w:.1f}" height="15" rx="7" fill="{SURFACE}" '
                f'stroke="{BORDER}" stroke-width="0.8"/>'
            )
            body.append(_text(label_x, label_y, edge.label, size=10, color=INK_SOFT, anchor="middle"))

    for node in spec.nodes:
        position = positions[node.id]
        fill, stroke, ink = _NODE_STYLES.get(node.kind, _NODE_STYLES["default"])
        x, y = position["x"], position["y"]
        body.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{node_w}" height="{node_h}" rx="10" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
        )
        label_lines = _wrap(node.label, width=22, max_lines=2)
        offset = node_h / 2 - (len(label_lines) - 1) * 8 - (5 if node.note else 0)
        for index, line in enumerate(label_lines):
            body.append(
                _text(x + node_w / 2, y + offset + index * 15 + 4, line,
                      size=12.5, weight="bold", color=ink, anchor="middle")
            )
        if node.note:
            note_line = _wrap(node.note, width=26, max_lines=1)[0]
            body.append(
                _text(x + node_w / 2, y + node_h - 11, note_line,
                      size=10, color=INK_SOFT, anchor="middle")
            )

    return {
        "asset_type": "diagram",
        "format": "svg",
        "title": spec.title,
        "content": _svg_document(canvas_w, canvas_h, "".join(body), defs=defs),
        "width": round(canvas_w),
        "height": round(canvas_h),
    }


# --------------------------------------------------------------------------- #
# Illustration
# --------------------------------------------------------------------------- #

_STYLE_PHRASES = {
    "flat_vector": "clean flat vector illustration, simple geometric shapes, generous white space",
    "isometric": "isometric illustration, subtle depth, soft consistent lighting",
    "line_art": "minimal line art, thin uniform strokes, limited accent colour",
    "soft_3d": "soft 3D render, matte surfaces, gentle diffuse shadows",
}


def _generate_image(spec: IllustrationSpec) -> Dict[str, Any]:
    prompt = f"{spec.prompt}\n\nStyle: {_STYLE_PHRASES.get(spec.style, '')}."
    if spec.avoid_text:
        # Repeated deliberately: image models treat "no text" as a weak
        # suggestion, and half-formed lettering is the most common way one of
        # these images ends up unusable.
        prompt += (
            " Contain no text, no words, no letters, no numbers, and no labels "
            "of any kind. Purely visual, wordless composition."
        )
    prompt += " No brand logos, no real people, no watermarks."

    response = _client.models.generate_content(
        model=_IMAGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=spec.aspect_ratio),
            http_options=types.HttpOptions(retry_options=_RETRY),
        ),
    )

    for candidate in response.candidates or []:
        for part in getattr(candidate.content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                raw = inline.data
                encoded = raw if isinstance(raw, str) else base64.b64encode(raw).decode("ascii")
                return {
                    "asset_type": "illustration",
                    "format": "image",
                    "title": spec.title,
                    "mime_type": getattr(inline, "mime_type", "image/png"),
                    "content": encoded,
                    "aspect_ratio": spec.aspect_ratio,
                }

    # Usually a safety filter. Surfacing it plainly beats returning a broken
    # <img> and letting the user guess.
    raise RuntimeError("Image model returned no image (it may have been filtered)")


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #

def render_visual(visual_plan: Dict[str, Any] | Any) -> Dict[str, Any]:
    """Render a spec according to its asset type.

    Accepts either a validated spec object with `.asset_type`, or a plain dict
    carrying `asset_type` plus the spec fields.
    """
    if isinstance(visual_plan, dict):
        asset_type = visual_plan.get("asset_type")
        payload = {k: v for k, v in visual_plan.items() if k != "asset_type"}
        spec = {
            "infographic": InfographicSpec,
            "diagram": DiagramSpec,
            "illustration": IllustrationSpec,
        }[asset_type](**payload)
    else:
        spec = visual_plan
        asset_type = {
            InfographicSpec: "infographic",
            DiagramSpec: "diagram",
            IllustrationSpec: "illustration",
        }[type(spec)]

    if asset_type == "infographic":
        return _render_infographic(spec)

    elif asset_type == "illustration":
        return _generate_image(spec)

    elif asset_type == "diagram":
        return _render_diagram(spec)

    raise ValueError(f"Unknown asset_type: {asset_type!r}")