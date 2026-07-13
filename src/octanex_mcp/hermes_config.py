"""Bridge the canvas UI to the Hermes Agent harness model configuration.

The canvas lets the user pick which Hermes model powers the *agentic*
interaction (intent -> scene interpretation). That choice is authoritative only
if it is written back into Hermes's own ``~/.hermes/config.yaml``: the harness —
not this gateway — performs the interpretation, so the gateway's local planner
is just the offline preview. This module is the single, safe bridge between the
canvas UI and that config file.

Reads are non-destructive. Writes are *surgical*: only ``model.default`` is
edited in place (one line), preserving comments, key order, and everything else
in the user's config. We never re-dump the whole YAML document.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - gateway venv ships PyYAML
    yaml = None


def config_path() -> Path:
    return Path(os.environ.get("HERMES_CONFIG", os.path.expanduser("~/.hermes/config.yaml")))


def _capabilities(meta: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "vision": bool((meta or {}).get("supports_vision", False)),
        "tools": bool((meta or {}).get("supports_tools", False)),
        "thinking": bool((meta or {}).get("supports_thinking", False)),
    }


def list_models(path: Optional[Path] = None) -> Dict[str, Any]:
    """Return Hermes model options for the canvas selector.

    Shape::

        {"current": "<model.default>", "options": [
            {"id", "provider", "context_length", "capabilities": {...}}, ...]}
    """
    p = path or config_path()
    if yaml is None or not p.exists():
        return {"current": None, "options": [], "error": "config unavailable"}
    data = yaml.safe_load(p.read_text()) or {}
    current = (data.get("model") or {}).get("default")

    seen: Dict[str, Dict[str, Any]] = {}
    for section in ("custom_providers", "providers"):
        for prov in data.get(section) or []:
            pname = prov.get("name", "unknown")
            for mid, meta in (prov.get("models") or {}).items():
                seen.setdefault(
                    mid,
                    {
                        "id": mid,
                        "provider": pname,
                        "context_length": (meta or {}).get("context_length"),
                        "capabilities": _capabilities(meta),
                    },
                )
    # Always include the current default even if it isn't enumerated under a provider.
    if current and current not in seen:
        seen[current] = {
            "id": current,
            "provider": (data.get("model") or {}).get("provider", "default"),
            "context_length": None,
            "capabilities": {},
        }
    options = sorted(seen.values(), key=lambda o: o["id"])
    return {"current": current, "options": options}


def set_current_model(model_id: str, path: Optional[Path] = None) -> Dict[str, Any]:
    """Surgically set ``model.default`` to ``model_id`` (validated against known options).

    Returns ``{"current": model_id}`` or raises ``ValueError`` (unknown id or
    config not locatable).
    """
    p = path or config_path()
    known = {o["id"] for o in list_models(p).get("options", [])}
    if model_id not in known:
        raise ValueError(f"unknown model {model_id!r}")
    text = p.read_text()
    patched = re.sub(
        r"(?m)^(model:\s*\n)(\s*default:\s*).*$",
        lambda m: f"{m.group(1)}{m.group(2)}{model_id}",
        text,
        count=1,
    )
    if patched == text:
        raise ValueError("could not locate model.default in config")
    p.write_text(patched)
    return {"current": model_id}
