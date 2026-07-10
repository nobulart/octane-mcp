"""Scope -> domain disambiguation for human-to-agent scene edits.

This module is the *brain* behind intent phrases like "increase the resolution
of #1 and #3". It resolves which semantic domain a property word applies to
based on what the phrase scopes over (an object/group, or the render/canvas).

Design rule (established in project review, 2026-07-10):

    referent is an object/group (#N, #Gk)
        -> the property lives in the *object* domain (mesh, material, transform)
    referent is the render/canvas/frame (output, canvas, render res)
        -> the property lives in the *render-output* domain (WxH, spp, AA)
    referent absent
        -> default to the statistically-common domain, but mark low
           confidence and signal that the caller should confirm.

This generalizes: the same binding table applies to *every* property word
(resolution, size, quality, smoothing, color, brightness, sharpness), so the
resolver is a data table, not a one-off special-case for "resolution".

Layering rule: stdlib only. No numpy/Pillow/network. This keeps the policy
importable from the console-script server (repo root off sys.path) and from
the label overlay (which imports it for the "render" shortcut).

Edge-case learning (record to skill): "resolution" is NOT inherently ambiguous.
User said "increase the resolution of #1" -> object scope -> mesh. Only
*unscoped* "increase resolution" is genuinely ambiguous (default render +
confirm). Do not re-litigate this in the NL layer -- resolve from scope first.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

__all__ = [
    "Domain",
    "Ambiguity",
    "Resolution",
    "PROPERTY_TABLE",
    "resolve",
    "parse_scope_refs",
]

# Semantic domains a property can resolve into.
Domain = str  # "object" | "render"
# How ambiguous a phrase was.
Ambiguity = str  # "none" | "scope_default" | "unknown_property"

#: Referent tokens that explicitly scope a phrase to the render/canvas/frame.
_RENDER_SCOPE_TOKENS = (
    "output", "canvas", "frame", "image", "render", "film", "export",
    "final", "picture",
)
#: Property words that need scoping to pick a domain.
_PROPERTY_WORDS = (
    "resolution", "res", "size", "quality", "sharpness", "smoothing",
    "smoothness", "detail", "density",
)


@dataclass(frozen=True)
class Resolution:
    """Resolved intent: which domain, how confident, what to say back."""

    domain: Domain
    ambiguity: Ambiguity
    confidence: float  # 0.0 .. 1.0
    needs_confirm: bool
    note: str = ""


# property -> {object: <object-domain meaning>, render: <render meaning>,
#            default: "object"|"render", hint: <what confirm would ask>}
PROPERTY_TABLE: Dict[str, Dict[str, str]] = {
    "resolution": {
        "object": "mesh tessellation (subdivision / LOD / subdiv level)",
        "render": "output image WxH + samples/AA",
        "default": "render",
        "hint": "Did you mean output resolution (render) or mesh density (object)?",
    },
    "size": {
        "object": "geometry dimensions (scale/extents)",
        "render": "canvas dimensions (WxH)",
        "default": "object",
        "hint": "Did you mean the object's physical size or the canvas size?",
    },
    "quality": {
        "object": "mesh quality (decimation tolerance / subdiv)",
        "render": "convergence tier (samples per pixel)",
        "default": "render",
        "hint": "Did you mean mesh quality or render convergence quality?",
    },
    "smoothing": {
        "object": "mesh modifier (Laplacian / subdivision smoothing)",
        "render": "post denoise / filter strength",
        "default": "object",
        "hint": "Did you mean mesh smoothing or render denoise?",
    },
    "smoothness": {
        "object": "mesh modifier (Laplacian / subdivision smoothing)",
        "render": "post denoise / filter strength",
        "default": "object",
        "hint": "Did you mean mesh smoothing or render denoise?",
    },
    "sharpness": {
        "object": "subdiv crispness / edge hardness",
        "render": "depth-of-field / focus / sharpen",
        "default": "render",
        "hint": "Did you mean mesh crispness or camera focus/sharpen?",
    },
    "detail": {
        "object": "mesh subdivision / displacement detail",
        "render": "render sampling / texture detail",
        "default": "object",
        "hint": "Did you mean geometry detail or render detail?",
    },
    "density": {
        "object": "mesh tessellation density",
        "render": "pixel density / DPI of export",
        "default": "object",
        "hint": "Did you mean mesh density or export pixel density?",
    },
}


def parse_scope_refs(text: str) -> Tuple[bool, bool]:
    """Return (has_object_ref, has_render_ref) for a phrase.

    Object refs: ``#12``, ``#3-#7``, ``#G2``, ``object 4``.
    Render refs: the ``_RENDER_SCOPE_TOKENS`` list.
    """
    lowered = text.lower()
    has_render = any(tok in lowered for tok in _RENDER_SCOPE_TOKENS)
    has_object = bool(_OBJECT_REF_RE.search(text)) or "object" in lowered.split()
    return has_object, has_render


# Matches #N, #N-#M, #Gk  (single pass; groups irrelevant here)
_OBJECT_REF_RE = re.compile(r"#\s*[A-Za-z]?\s*\d+(?:\s*-\s*#?\s*\d+)?")


def resolve(text: str, *, object_refs: Optional[List[str]] = None) -> Resolution:
    """Resolve the dominant property word in ``text`` to a domain.

    Args:
        text: the natural-language edit phrase.
        object_refs: optional pre-parsed list of object refs (e.g. ["#1","#3"])
            from the label/ref resolver. If provided, it overrides the in-text
            object-ref scan so the two systems agree on what was referenced.

    Returns a :class:`Resolution` describing the resolved domain, confidence,
    and whether the caller should confirm before acting.
    """
    lowered = text.lower()

    # 1) Which property word is present?
    prop = None
    for candidate in _PROPERTY_WORDS:
        if re.search(r"\b" + re.escape(candidate) + r"\b", lowered):
            prop = candidate
            break
    if prop is None:
        return Resolution(
            domain="object",
            ambiguity="unknown_property",
            confidence=0.0,
            needs_confirm=True,
            note="No scope-bound property word recognized; caller must classify.",
        )

    entry = PROPERTY_TABLE[prop]

    # 2) What does the phrase scope over?
    if object_refs is not None:
        # The ref-resolver is authoritative about WHAT was referenced; a stray
        # render token in free text must not override explicit object refs.
        has_object = bool(object_refs)
        has_render = False
    else:
        has_object, _ = parse_scope_refs(text)
        has_render = any(tok in lowered for tok in _RENDER_SCOPE_TOKENS)

    if has_object and not has_render:
        # Explicit object scope: bind to object domain, high confidence.
        return Resolution(
            domain="object",
            ambiguity="none",
            confidence=0.95,
            needs_confirm=False,
            note=f"{prop} over object(s) -> {entry['object']}",
        )
    if has_render and not has_object:
        return Resolution(
            domain="render",
            ambiguity="none",
            confidence=0.95,
            needs_confirm=False,
            note=f"{prop} over render -> {entry['render']}",
        )
    if has_object and has_render:
        # Both scopes present -- unusual; defer to caller with low confidence.
        return Resolution(
            domain=entry["default"],
            ambiguity="scope_default",
            confidence=0.5,
            needs_confirm=True,
            note=f"{prop} mentions both object and render scope; confirm target.",
        )

    # 3) No explicit scope: use the property's default, but flag for confirm.
    default = entry["default"]
    return Resolution(
        domain=default,
        ambiguity="scope_default",
        confidence=0.6,
        needs_confirm=True,
        note=entry["hint"],
    )
