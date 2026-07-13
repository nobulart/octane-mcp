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

import json
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


def _cache_dir() -> Path:
    return Path(os.environ.get("HERMES_CACHE", os.path.expanduser("~/.hermes/cache")))


def _capabilities(meta: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "vision": bool((meta or {}).get("supports_vision", False)),
        "tools": bool((meta or {}).get("supports_tools", False)),
        "thinking": bool((meta or {}).get("supports_thinking", False)),
    }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else None
    except (OSError, ValueError):
        return None


def _cloud_catalog_options() -> List[Dict[str, Any]]:
    """Merge Hermes's curated cloud catalog + live provider caches.

    These are the cloud models the *harness* can route to (OpenRouter, Nous
    Portal, and any provider with a live /v1/models cache). They are not in
    ``config.yaml`` — they live in Hermes's disk caches, which is the same
    source ``hermes model`` reads. Tagged ``cloud: True`` so the UI can mark
    them, and ``selectable`` reflects whether the harness can currently use
    them (Nous Portal is authed here; OpenRouter key is not).
    """
    out: Dict[str, Dict[str, Any]] = {}
    # 1) Curated catalog: providers -> models[{id, description, metadata}]
    catalog = _load_json(_cache_dir() / "model_catalog.json") or {}
    for prov, blk in (catalog.get("providers") or {}).items():
        for m in (blk.get("models") or []):
            mid = m.get("id") if isinstance(m, dict) else m
            if not mid:
                continue
            out.setdefault(
                mid,
                {
                    "id": mid,
                    "provider": prov,
                    "cloud": True,
                    "context_length": None,
                    "capabilities": {},
                    "selectable": prov == "nous",  # Nous Portal authed; others gated on key
                },
            )
    # 2) Live provider /v1/models caches (copilot, ollama-cloud, ...). Augment
    #    context_length where present; add any not already in the catalog.
    provider_cache = _load_json(Path(os.path.expanduser("~/.hermes/provider_models_cache.json"))) or {}
    for prov, blk in provider_cache.items():
        for mid in (blk.get("models") or []):
            if not mid:
                continue
            if mid not in out:
                out[mid] = {
                    "id": mid,
                    "provider": prov,
                    "cloud": True,
                    "context_length": None,
                    "capabilities": {},
                    "selectable": False,
                }
    return list(out.values())


def list_models(path: Optional[Path] = None) -> Dict[str, Any]:
    """Return Hermes model options for the canvas selector.

    Merges three sources so the selector reflects *every* model the harness can
    route to:

    - local/custom providers from ``config.yaml`` (with capability metadata);
    - the current ``model.default`` (always included, even if not enumerated);
    - cloud models from Hermes's disk caches (curated catalog + live provider
      caches), tagged ``cloud``.

    Shape::

        {"current": "<model.default>", "options": [
            {"id", "provider", "cloud", "context_length",
             "capabilities": {...}, "selectable"}, ...]}
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
                        "cloud": False,
                        "context_length": (meta or {}).get("context_length"),
                        "capabilities": _capabilities(meta),
                        "selectable": True,
                    },
                )
    # Cloud catalog options (curated + live caches).
    for opt in _cloud_catalog_options():
        seen.setdefault(opt["id"], opt)
    # Always include the current default even if it isn't enumerated anywhere.
    if current and current not in seen:
        seen[current] = {
            "id": current,
            "provider": (data.get("model") or {}).get("provider", "default"),
            "cloud": False,
            "context_length": None,
            "capabilities": {},
            "selectable": True,
        }
    options = sorted(seen.values(), key=lambda o: (not o.get("cloud", False), o["provider"], o["id"]))
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


# ---------------------------------------------------------------------------
# VOX (speech-in / speech-out) voice-conversation mode
# ---------------------------------------------------------------------------

# The terse conversation contract the harness adopts when VOX is on. Voice turns
# are short; the agent should answer in the same register — no preamble, no
# markdown walls, just the next concrete step or answer.
VOX_CONTRACT = (
    "Voice mode. Be terse and conversational: short spoken-length replies, "
    "one idea per turn, no lists or markdown unless asked. Lead with the action "
    "or answer. Ask at most one clarifying question. Keep it shaped for speech."
)


def get_vox(path: Optional[Path] = None) -> Dict[str, Any]:
    """Return the VOX voice-mode state.

    Shape::

        {"enabled": bool, "contract": "<terse voice contract>"}
    """
    p = path or config_path()
    if yaml is None or not p.exists():
        return {"enabled": False, "contract": VOX_CONTRACT, "error": "config unavailable"}
    data = yaml.safe_load(p.read_text()) or {}
    enabled = bool((data.get("vox") or {}).get("enabled", False))
    return {"enabled": enabled, "contract": VOX_CONTRACT}


def set_vox(enabled: bool, path: Optional[Path] = None) -> Dict[str, Any]:
    """Surgically enable/disable VOX by writing ``vox.enabled``.

    Only the ``vox:`` block is touched — the rest of the user's config
    (comments, other keys) is preserved verbatim. Inserts a ``vox:`` block
    if one is absent.
    """
    p = path or config_path()
    if yaml is None or not p.exists():
        raise ValueError("config unavailable")
    text = p.read_text()
    flag = "true" if enabled else "false"

    # Locate the vox: block (top-level key: column 0, no leading space).
    m = re.search(r"(?m)^vox\s*:", text)
    if not m:
        # No vox: block — append a clean one, preserving file trailing newline.
        sep = "" if text.endswith("\n") or not text else "\n"
        patched = f"{text}{sep}vox:\n  enabled: {flag}\n"
    else:
        start = m.start()
        # Find the block's end: the next top-level (col-0) key, or EOF.
        rest = text[m.end():]
        nxt = re.search(r"(?m)\n[A-Za-z_][\w-]*\s*:", rest)
        if nxt is not None:
            end = m.end() + nxt.start()
        else:
            end = m.end() + len(rest)
        block = text[start:end]
        if re.search(r"(?m)^\s*enabled\s*:", block):
            # Replace the enabled line *inside this block only*.
            new_block = re.sub(
                r"(?m)^(\s*)enabled\s*:.*$",
                lambda mm: f"{mm.group(1)}enabled: {flag}",
                block,
                count=1,
            )
        else:
            # Block exists but has no enabled line yet — add it under vox:.
            indent = re.match(r"\s*", block[m.end() - start:]).group(0)
            new_block = f"{block.rstrip()}\n{indent}  enabled: {flag}\n"
        patched = text[:start] + new_block + text[end:]

    if patched == text:
        # Idempotent no-op: the flag was already in the requested state.
        # Don't error — just report success without rewriting the file.
        return {"enabled": enabled}
    p.write_text(patched)
    return {"enabled": enabled}
