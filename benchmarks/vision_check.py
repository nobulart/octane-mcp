"""Opt-in vision acceptance tier for recipe renders.

Pixel acceptance (``benchmarks.acceptance``) proves a render is *non-blank and
structured*, but it cannot judge *semantic correctness* — a grey cylinder passes
``non_empty`` just as well as a vase. During 2026-07-09 live verification, five
recipes rendered valid-but-wrong subjects (e.g. a grey cylinder instead of a
vase, a white voxel grid instead of Earth) that pixel-QA accepted but a vision
model (and a human) immediately rejected.

This module adds a SECOND, opt-in tier: ask a vision model whether the rendered
PNG actually shows the recipe's stated subject. It is deliberately **never**
authoritative on its own — the harness records it as extra evidence and only
blocks promotion when it fails. The default pixel tier remains the primary gate.

The vision call is injected (``vision_fn``) so the offline test suite can stub it
without invoking a real model. The live default uses the Hermes vision tool via a
thin shim.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

# A vision function takes (image_path, intent_text) and returns a tuple of
# (passed: bool, reasoning: str). Default live impl is injected by the harness.
VisionFn = Callable[[str, str], tuple[bool, str]]

# Recipes whose subject meaning depends on color/material (a wrong-subject render
# is invisible to pixel-QA). These are the ones that benefit most from the vision
# tier; the tier is still runnable on any recipe that declares an ``intent``.
COLOR_DEPENDENT_DOMAINS = {
    "photoreal/pbr rendering",
    "photoreal/pbr space rendering",
    "geospatial/science",
}


def derive_intent(data: dict[str, Any]) -> str:
    """Build a short subject description the vision model should confirm."""
    title = data.get("title") or data.get("slug") or "scene"
    purpose = data.get("purpose") or ""
    # Trim the purpose to a single descriptive sentence.
    purpose = re.split(r"[.;]", str(purpose))[0].strip()
    intent = f"{title}: {purpose}" if purpose else title
    return intent[:280]


def vision_review(
    png_path: str | Path,
    data: dict[str, Any],
    vision_fn: VisionFn,
) -> dict[str, Any]:
    """Ask the (injected) vision model whether ``png_path`` shows the recipe subject.

    Returns a structured dict; never raises on vision failure — a failed review is
    itself evidence recorded in the result.
    """
    intent = derive_intent(data)
    try:
        passed, reasoning = vision_fn(str(png_path), intent)
    except Exception as exc:  # noqa: BLE001 - vision is best-effort evidence
        return {
            "ran": False,
            "passed": False,
            "error": f"vision call failed: {exc}",
            "intent": intent,
            "reasoning": "",
        }
    return {
        "ran": True,
        "passed": bool(passed),
        "intent": intent,
        "reasoning": str(reasoning)[:600],
    }


def _live_vision_shim(image_path: str, intent: str) -> tuple[bool, str]:
    """Real vision review used in live mode (imported lazily to keep the module
    importable offline and in the test suite).

    Uses the Hermes ``vision_analyze`` tool. The prompt forces a strict yes/no on
    the stated subject so the verdict is not a vague 'looks plausible'.
    """
    try:
        from hermes_tools import vision_analyze  # type: ignore
    except Exception:  # pragma: no cover - tool availability varies
        return (False, "vision_analyze unavailable in this environment")

    question = (
        f"Does this render actually show: {intent}? "
        "Answer with a clear YES or NO first, then one sentence of evidence. "
        "If the main subject is wrong (e.g. a plain cylinder instead of a vase, "
        "a flat panel instead of a planet), answer NO."
    )
    try:
        result = vision_analyze(image_path, question)
    except Exception as exc:  # noqa: BLE001
        return (False, f"vision_analyze raised: {exc}")
    text = json.dumps(result) if not isinstance(result, str) else result
    verdict = bool(re.search(r"\bYES\b", text[:400].upper()))
    return (verdict, text[:600])
