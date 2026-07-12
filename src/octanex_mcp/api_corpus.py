from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .config import resolve_config

# Phase-1 artifact (docs/octane-lua-api-bridge-review.md): the Lua
# exporter (octane_lua/export_api_docs_v3.lua) runs INSIDE Octane X,
# writes OctaneMCP/octane_lua_api.<build>.json, and this module
# ingests it into a capability registry. The bridge is then validated
# against the ACTUAL Octane X build instead of hardcoded folklore.

DEFAULT_REQUIRED_PROBES = (
    "project.getSceneGraph",
    "node.create",
    "render.start",
    "render.saveImage",
    "render.getRenderResultStatistics",
)

# Node-type / constant probes that flip bridge strategy per build.
DEFAULT_REQUIRED_CONSTANTS = (
    "NT_GEO_MESH",
    "NT_RENDERTARGET",
    "NT_ENV_DAYLIGHT",
    "NT_MAT_DIFFUSE",
    "NT_MAT_EMISSIVE",
    "P_MAX_SAMPLES",
    "A_FILENAME",
)


@dataclass(frozen=True)
class ApiCorpus:
    """Ingested Octane X Lua API corpus for one build."""

    schema: str = "octanex-api-corpus/v1"
    exported_at: str = ""
    octane_available: bool = False
    octane_help_available: bool = False
    build: dict[str, Any] = field(default_factory=dict)
    modules: dict[str, Any] = field(default_factory=dict)
    constants_by_prefix: dict[str, dict[str, bool]] = field(default_factory=dict)
    feature_probes: dict[str, Any] = field(default_factory=dict)
    constant_probes: dict[str, Any] = field(default_factory=dict)
    source_path: str = ""

    @property
    def build_tag(self) -> str:
        return (
            str(self.build.get("octane_build") or self.build.get("octane_version") or "unknown")
        )

    def probe_available(self, name: str) -> bool:
        probe = self.feature_probes.get(name)
        if isinstance(probe, Mapping):
            return bool(probe.get("available"))
        return False

    def constant_exists(self, name: str) -> bool:
        probe = self.constant_probes.get(name)
        if isinstance(probe, Mapping):
            return bool(probe.get("exists"))
        # Fall back to scanning the grouped constant tables.
        for _prefix, table in self.constants_by_prefix.items():
            if isinstance(table, Mapping) and name in table:
                return True
        return False

    def capability_report(self) -> dict[str, Any]:
        """What the bridge can rely on for THIS build."""
        required_probes = {
            name: self.probe_available(name) for name in DEFAULT_REQUIRED_PROBES
        }
        required_constants = {
            name: self.constant_exists(name) for name in DEFAULT_REQUIRED_CONSTANTS
        }
        # Lighting strategy: native NT_LIGHT_* constants are nil on some builds.
        native_light = self.constant_exists("NT_LIGHT_AREA") or self.constant_exists("NT_LIGHT_SUN")
        lighting_strategy = "native_light" if native_light else "daylight_env_or_emissive_proxy"
        return {
            "schema": self.schema,
            "build_tag": self.build_tag,
            "octane_available": self.octane_available,
            "octane_help_available": self.octane_help_available,
            "required_probes": required_probes,
            "required_constants": required_constants,
            "lighting_strategy": lighting_strategy,
            "save_preview_signature_known": (
                self.probe_available("render.saveImage")
                and self.constant_exists("P_MAX_SAMPLES")
            ),
            "all_required_probes_present": all(required_probes.values()),
            "all_required_constants_present": all(required_constants.values()),
        }


def _coerce(data: Mapping[str, Any]) -> ApiCorpus:
    return ApiCorpus(
        schema=str(data.get("schema", "octanex-api-corpus/v1")),
        exported_at=str(data.get("exported_at", "")),
        octane_available=bool(data.get("octane_available", False)),
        octane_help_available=bool(data.get("octane_help_available", False)),
        build=dict(data.get("build") or {}),
        modules=dict(data.get("modules") or {}),
        constants_by_prefix=dict(data.get("constants_by_prefix") or {}),
        feature_probes=dict(data.get("feature_probes") or {}),
        constant_probes=dict(data.get("constant_probes") or {}),
        source_path=str(data.get("source_path", "")),
    )


def latest_corpus_path(workspace: Path | None = None) -> Path | None:
    """Return the newest octane_lua_api.*.json in the workspace, if any."""
    cfg = resolve_config()
    root = workspace or cfg.workspace
    if not root.exists():
        return None
    candidates = sorted(
        (p for p in root.glob("octane_lua_api.*.json") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_corpus(workspace: Path | None = None, *, path: Path | None = None) -> ApiCorpus | None:
    """Load the API corpus from an explicit path, or the latest one in the workspace.

    ``path`` takes precedence; ``workspace`` selects the newest
    octane_lua_api.*.json under that directory.
    """
    target = path or latest_corpus_path(workspace=workspace)
    if target is None or not target.exists():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return None
    corpus = _coerce(data)
    # Attach the source path for traceability.
    object.__setattr__(corpus, "source_path", str(target))
    return corpus


def validate_corpus(corpus: ApiCorpus) -> dict[str, Any]:
    """Validate corpus shape and report capability gaps.

    A passing validate_corpus means the bridge's required Octane
    surfaces exist on this build. Missing probes/constants are
    reported as warnings, not hard errors, so a partial export
    still yields a usable capability report.
    """
    report = corpus.capability_report()
    errors: list[str] = []
    warnings: list[str] = []

    if not corpus.octane_available:
        errors.append("octane was not available when the corpus was exported")
    if not corpus.octane_help_available:
        warnings.append("octane.help was unavailable; module inventory is empty")

    missing_probes = [
        name for name, ok in report["required_probes"].items() if not ok
    ]
    if missing_probes:
        warnings.append(
            "missing required runtime probes: " + ", ".join(sorted(missing_probes))
        )

    missing_constants = [
        name for name, ok in report["required_constants"].items() if not ok
    ]
    if missing_constants:
        warnings.append(
            "missing required constants (bridge fallbacks will engage): "
            + ", ".join(sorted(missing_constants))
        )

    return {
        "schema_ok": corpus.schema.startswith("octanex-api-corpus/"),
        "errors": errors,
        "warnings": warnings,
        "capabilities": report,
        "ok": (not errors) and report["all_required_probes_present"],
    }


# --- CLI surface ---------------------------------------------------------

def export_command(*, workspace: Path | None = None) -> dict[str, Any]:
    """Instructions for running the exporter inside Octane X.

    The Lua exporter itself runs inside Octane X (no CLI entry point on
    macOS — see docs/octane-x-no-cli.md), so this returns the script
    the user fires and where the JSON lands, rather than executing it.
    """
    cfg = resolve_config()
    root = workspace or cfg.workspace
    return {
        "ok": True,
        "exporter_script": "export_api_docs_v3.lua",
        "fire_via": "Octane X Scripts menu (hermes_bridge_oneshot is NOT needed)",
        "output_glob": str(root / "octane_lua_api.*.json"),
        "note": (
            "Run export_api_docs_v3.lua from the Octane X Scripts menu, "
            "then call load_corpus()/validate_corpus() to ingest the result."
        ),
    }


def inspect_command(*, workspace: Path | None = None) -> dict[str, Any]:
    corpus = load_corpus(workspace=workspace)
    if corpus is None:
        return {
            "ok": False,
            "error": "no octane_lua_api.*.json found in the workspace",
            "next_steps": [
                "Launch Octane X, run export_api_docs_v3.lua from the Scripts menu",
                "Re-run octanex-mcp api-corpus inspect",
            ],
        }
    return {
        "ok": True,
        "source_path": corpus.source_path,
        "build_tag": corpus.build_tag,
        "module_count": len(corpus.modules),
        "validation": validate_corpus(corpus),
    }


def validate_command(*, workspace: Path | None = None) -> dict[str, Any]:
    corpus = load_corpus(workspace=workspace)
    if corpus is None:
        return {"ok": False, "error": "no octane_lua_api.*.json found in the workspace"}
    result = validate_corpus(corpus)
    result["ok"] = result["ok"]
    result["source_path"] = corpus.source_path
    return result
