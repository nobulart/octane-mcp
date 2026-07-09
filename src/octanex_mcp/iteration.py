"""WP9 iteration loop — reference grammar -> converged render -> auto-promotion.

A harvested corpus entry carries a derived pixel-acceptance spec
(``entry.derived_acceptance``, produced by
``octanex_mcp.acceptance.reference_to_acceptance``). This module closes the WP9
loop:

  1. WARM START — build a candidate Octane scene spec from the entry's derived
     grammar (dominant hue -> material color, iso camera, soft studio). An
     optional ``warm_start`` entry (nearest grammar via ``corpus.find_grammar``)
     can condition the candidate against the closest prior reference.
  2. ITERATE — render the spec (``render_fn`` injected; live = Octane drain),
     evaluate against ``entry.derived_acceptance``. On a cheap failure
     (near-black / missing color family) apply a bounded material/lighting
     tweak and re-render. Stop at first convergence or after ``max_iters``.
  3. PROMOTE — a converged render is auto-promoted: the converged PNG and a
     generated ``BenchmarkTask`` generator snippet are written into the entry,
     and the task is appended to the runtime ``PROMOTED_TASKS`` registry (and a
     paste-ready ``promotion_snippet.py`` is emitted for ``benchmarks/spec.py``).

Everything is offline-testable: ``render_fn`` is injectable, the live adapter
(``live_render_fn``) lazy-imports the harness only when actually rendering.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Callable

from octanex_mcp.acceptance import evaluate_acceptance
from octanex_mcp.acceptance import _hue_to_rgb  # pure helper, no IO
from octanex_mcp.visuals import ObjBuilder, bounds_from_points, camera_for_bounds

from benchmarks.spec import BenchmarkTask

# Runtime registry of auto-promoted tasks (importable; `run_all` can extend to
# include these). Persistence to benchmarks/spec.py is via the per-entry
# promotion_snippet.py (copy-paste keeps spec.py the single source of truth).
PROMOTED_TASKS: list[BenchmarkTask] = []

# Default candidate scene parameters (mirror benchmarks/spec.py conventions).
_DEFAULT_LIGHTING = "soft_studio"
_DEFAULT_SIZE = 1280
_MAX_ITERS = 4


def _dominant_hue(entry) -> float | None:
    """Top derived hue family hue (degrees), or None if the ref is achromatic."""
    families = (entry.derived or {}).get("hue_families") or []
    if not families:
        return None
    return float(families[0]["hue"])


def build_candidate_scene(entry, *, warm_start: Any | None = None) -> dict[str, Any]:
    """Build an initial Octane scene spec from a corpus entry's derived grammar.

    The scene is a single primitive (sphere) tinted with the reference's
    dominant hue, framed with a bounds-aware iso camera under soft studio light.
    Its ``acceptance`` list is the entry's own ``derived_acceptance`` so that a
    *converged* render means "this Octane scene reproduces the reference's
    visual grammar".

    ``warm_start`` (optional ``CorpusEntry``) is accepted for API symmetry with
    the find_grammar warm-start design; the dominant hue is taken from the entry
    itself (the reference we are trying to reproduce), not the neighbor.
    """
    hue = _dominant_hue(entry)
    if hue is None:
        color: list[float] = [0.85, 0.85, 0.9]  # neutral fallback
    else:
        color = _hue_to_rgb(hue)

    b = ObjBuilder("subject")
    b.add_ellipsoid(center=(0, 0, 0), radii=(1.1, 1.1, 1.1), material="subject_mat")
    verts: list[tuple[float, float, float]] = []
    v_lines: list[str] = []
    face_lines: list[str] = []
    for line in b.lines:
        if line.startswith("v "):
            v_lines.append(line)
            parts = line.split()
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif line.startswith("f "):
            face_lines.append(line)
    # One combined-OBJ group so the spec is structurally identical to a benchmark
    # task and can be fed straight to the harness.
    obj_text = "# candidate\n" + "\n".join(v_lines) + "\no subject\nusemtl subject_mat\n" + "\n".join(face_lines) + "\n"

    bounds = bounds_from_points(verts)
    mat = {
        "name": "subject_mat",
        "kind": "glossy",
        "color": [round(c, 4) for c in color],
        "roughness": 0.25,
    }
    return {
        "mesh_name": f"wp9_{entry.slug}",
        "obj": obj_text,
        "bounds": bounds,
        "materials": [mat],
        "assignments": [{"group_index": 1, "material_name": "subject_mat"}],
        "camera": camera_for_bounds(bounds, view="iso", margin=1.4),
        "lighting": _DEFAULT_LIGHTING,
        "save": {"quality": "high", "width": _DEFAULT_SIZE, "height": _DEFAULT_SIZE},
        "acceptance": list(entry.derived_acceptance),
    }


def _tweak_scene(spec: dict[str, Any], attempt: int) -> dict[str, Any]:
    """Apply a deterministic, bounded tweak to escape common cheap failures.

    attempt 0: as built. 1: bump emission (escapes near-black). 2: brighten
    lighting. 3: roughen material. Geometry/shape failures are NOT fixable here
    and are flagged ``needs_human`` by the caller.
    """
    spec = {**spec, "materials": [{**m} for m in spec["materials"]]}
    if attempt >= 1:
        spec["materials"][0]["emission"] = spec["materials"][0].get("emission", 0.0) + 1.5
    if attempt >= 2:
        spec["lighting"] = "bright_studio"
    if attempt >= 3:
        spec["materials"][0]["roughness"] = min(1.0, spec["materials"][0].get("roughness", 0.25) + 0.3)
    return spec


# review_ok triggers that are STRUCTURAL (geometry/composition) and cannot be
# fixed by the bounded material/lighting tweaks — these halt the loop as
# needs_human. Brightness/contrast triggers (near-black, low-contrast,
# near-white) are cheap-fixable and must NOT halt the loop.
_STRUCTURAL_REVIEW_TRIGGERS = {
    "likely object too small",
    "likely object clipped at frame edge",
}


def iterate_entry(
    entry,
    *,
    render_fn: Callable[[dict[str, Any]], Any],
    max_iters: int = _MAX_ITERS,
    warm_start: Any | None = None,
) -> dict[str, Any]:
    """Run the warm-start -> render -> evaluate -> tweak loop for one entry.

    ``render_fn(spec) -> path`` produces a saved PNG for a scene spec. Injected
    for offline tests; ``live_render_fn`` (below) drains Octane.

    Returns ``{converged, png_path, report, iters, scene_spec, needs_human}``.
    """
    base_spec = build_candidate_scene(entry, warm_start=warm_start)
    png_path = None
    report = None
    needs_human = False

    for attempt in range(max_iters):
        spec = _tweak_scene(base_spec, attempt) if attempt > 0 else base_spec
        try:
            out = render_fn(spec)
            png_path = Path(out)
        except Exception as exc:  # noqa: BLE001 - surface render failure, do not loop forever
            return {
                "converged": False, "png_path": None, "report": None,
                "iters": attempt, "scene_spec": spec, "needs_human": False,
                "error": f"render_fn failed: {exc}",
            }
        report = evaluate_acceptance(png_path, spec["acceptance"])
        if report.get("passed"):
            return {
                "converged": True, "png_path": png_path, "report": report,
                "iters": attempt + 1, "scene_spec": spec, "needs_human": False,
            }
        # Classify the failure. A failure is STRUCTURAL (needs human) only when
        # it cannot be fixed by the bounded material/lighting tweaks:
        #   * shape_profile fails but the render is NOT near-empty -> geometry/
        #     composition is wrong (real structure problem). If the render is
        #     near-empty the shape failure is merely a consequence of blackness
        #     and is cheap-fixable via the emission/lighting tweaks.
        #   * review_ok triggered a structural trigger (object too small /
        #     clipped). Brightness/contrast triggers are cheap-fixable.
        failing = [c for c in report.get("checks", []) if not c.get("passed")]
        check_kinds = {c.get("kind") for c in failing}
        non_empty_ok = not any(
            c.get("kind") == "non_empty" and not c.get("passed") for c in failing
        )
        if "shape_profile" in check_kinds and non_empty_ok:
            needs_human = True
            break
        review_fail = next((c for c in failing if c.get("kind") == "review_ok"), None)
        if review_fail:
            triggered = review_fail.get("triggered", [])
            if any(t in _STRUCTURAL_REVIEW_TRIGGERS for t in triggered):
                needs_human = True
                break
        # Otherwise (near-empty, color_family miss, near-black, low-contrast,
        # near-white, or shape_profile-with-empty-render): cheap-fixable ->
        # apply the next bounded tweak and retry.

    return {
        "converged": False, "png_path": png_path, "report": report,
        "iters": max_iters, "scene_spec": base_spec, "needs_human": needs_human,
    }


def make_promoted_task(slug: str, title: str, tier: int, scene_spec: dict[str, Any]) -> BenchmarkTask:
    """Wrap a converged scene spec as a first-class ``BenchmarkTask``."""
    captured = dict(scene_spec)
    return BenchmarkTask(
        tier=tier,
        slug=slug,
        title=title,
        archetype="corpus-promoted",
        description=f"Auto-promoted from WP9 corpus entry '{slug}'.",
        build=lambda: dict(captured),
        native_octane_verified=True,
    )


def _snippet(slug: str, title: str, tier: int, scene_spec: dict[str, Any]) -> str:
    """Paste-ready generator for benchmarks/spec.py (keeps spec.py as source of truth)."""
    spec_json = json.dumps(scene_spec, indent=2)
    return (
        f"def _t{tier}_{slug}() -> dict[str, Any]:\n"
        f"    # Auto-promoted from WP9 corpus entry '{slug}'.\n"
        f"    return {spec_json}\n"
        f"\n"
        f"# Append to ALL_TASKS:\n"
        f"# ALL_TASKS.append(BenchmarkTask({tier}, {slug!r}, {title!r}, \"corpus-promoted\",\n"
        f"#     \"Auto-promoted from WP9 corpus.\", _t{tier}_{slug}))\n"
    )


def promote_entry(
    entry,
    scene_spec: dict[str, Any],
    png_path: Any,
    report: dict[str, Any],
    *,
    tier: int = 7,
    registry: list[BenchmarkTask] | None = None,
) -> dict[str, Any]:
    """Persist a converged render as an auto-promoted benchmark task.

    Writes into the entry dir:
      * ``octane-preview.png`` — the converged render (copied from ``png_path``)
      * ``promotion.json`` — provenance + scene spec + acceptance report
      * ``promotion_snippet.py`` — paste-ready generator for benchmarks/spec.py
    Appends the generated ``BenchmarkTask`` to ``registry`` (default module-level
    ``PROMOTED_TASKS``) and flips the entry ``status`` to ``converged``.
    """
    entry_dir = Path(entry.dir)
    entry_dir.mkdir(parents=True, exist_ok=True)

    src = Path(png_path)
    preview = entry_dir / "octane-preview.png"
    if src.exists():
        preview.write_bytes(src.read_bytes())

    slug = entry.slug
    title = entry.title
    task = make_promoted_task(slug, title, tier, scene_spec)
    (registry if registry is not None else PROMOTED_TASKS).append(task)

    promotion = {
        "slug": slug,
        "title": title,
        "tier": tier,
        "promoted_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "scene_spec": scene_spec,
        "acceptance_report": report,
        "preview": str(preview),
    }
    (entry_dir / "promotion.json").write_text(json.dumps(promotion, indent=2) + "\n", encoding="utf-8")
    (entry_dir / "promotion_snippet.py").write_text(_snippet(slug, title, tier, scene_spec), encoding="utf-8")

    # Flip status so corpus_index() reports converged=True.
    entry.status = "converged"
    entry.manifest_path.write_text(json.dumps(entry.to_manifest(), indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True, "slug": slug, "tier": tier, "preview": str(preview),
        "task_slug": task.slug, "registry_size": len(registry if registry is not None else PROMOTED_TASKS),
    }


def live_render_fn(spec: dict[str, Any], *, container=None, dry_run: bool = False) -> Path:
    """Live adapter: render a scene spec by draining Octane via the harness.

    Lazy-imports benchmarks.harness so this module stays offline-importable.
    """
    from benchmarks.harness import run_task

    task = BenchmarkTask(
        tier=0, slug=spec.get("mesh_name", "wp9_live"), title="WP9 live render",
        archetype="corpus", description="live iteration render",
        build=lambda: dict(spec),
    )
    run = run_task(task, container=container, dry_run=dry_run, drain=not dry_run)
    if run.error:
        raise RuntimeError(run.error)
    if run.preview_path is None or not Path(run.preview_path).exists():
        raise RuntimeError("live render produced no preview PNG")
    return Path(run.preview_path)
