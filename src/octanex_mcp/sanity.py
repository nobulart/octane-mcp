from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

# ---------------------------------------------------------------------------
# OctaneX node-graph sanity gate
# ---------------------------------------------------------------------------
# Two entry points, both pure and offline-testable (no Octane import):
#   * analyze_scene_graph(harvest, ...)  -> inspect the LIVE graph that the
#     bridge returns from scene_harvest (post build, pre save_preview).
#   * analyze_scene_plan(plan, ...)      -> inspect a scene MANIFEST before a
#     build is queued, so errors are caught even earlier.
#
# Neither function renders, edits, or blocks anything. They report issues with a
# severity, a stable code, and (where useful) the offending node name. The agent
# (or a later hard-gate) decides whether to proceed. This is deliberately
# report-only: it never spends GPU and never mutates the scene.
#
# Why two analyses and not one? The live harvest (Octane's node graph) carries
# connection / has_geometry / has_material / visible flags but NOT mesh bounds,
# so framing checks are approximate there. The manifest carries per-object
# ``bounds`` and an explicit camera + lighting block, so it supports precise
# framing math. Splitting keeps each check on the data it can actually prove.
# ---------------------------------------------------------------------------

# Severity ordering (for sorting / "worst first" reporting).
SEVERITY_RANK = {"error": 0, "warning": 1}


@dataclass(frozen=True)
class SanityIssue:
    severity: str  # "error" | "warning"
    code: str
    message: str
    node: str | None = None
    detail: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        item: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.node is not None:
            item["node"] = self.node
        if self.detail is not None:
            item["detail"] = self.detail
        return item


@dataclass
class SanityReport:
    checks: list[str] = field(default_factory=list)
    issues: list[SanityIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[SanityIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[SanityIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "passed_checks": self.checks,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [i.as_dict() for i in self._sorted()],
            "summary": self.summary(),
        }

    def _sorted(self) -> list[SanityIssue]:
        return sorted(
            self.issues,
            key=lambda i: (SEVERITY_RANK.get(i.severity, 9), i.code),
        )

    def summary(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for issue in self.issues:
            counts[issue.code] = counts.get(issue.code, 0) + 1
        return {
            "ok": self.ok,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "by_code": counts,
        }


# ---------------------------------------------------------------------------
# Node-type classification (works off the free-form ``type`` string the bridge
# serializes from Octane; intentionally fuzzy because Octane's displayed type
# names vary by locale / build).
# ---------------------------------------------------------------------------

def _norm(value: Any) -> str:
    return (value or "").lower().replace("_", " ").strip()


def _is_mesh(t: str) -> bool:
    return "mesh" in _norm(t)


def _is_camera(t: str) -> bool:
    return "camera" in _norm(t)


def _is_render_target(t: str) -> bool:
    n = _norm(t)
    return "render target" in n or n == "rendertarget" or "rendertarget" in n.replace(" ", "")


def _is_light(t: str) -> bool:
    n = _norm(t)
    return any(k in n for k in ("light", "daylight", "sun", "spot", "point light"))


def _is_environment(t: str) -> bool:
    return "environment" in _norm(t)


def _is_material(t: str) -> bool:
    return "material" in _norm(t)


# Default check sets. Subsets let callers run only what they need.
GRAPH_CHECKS: tuple[str, ...] = (
    "render_target",
    "camera",
    "lights",
    "meshes",
    "materials",
    "scale",
)

PLAN_CHECKS: tuple[str, ...] = (
    "render_target",      # manifest must declare an intent to render
    "camera",
    "lights",
    "meshes",
    "materials",
    "scale",
    "framing",
)


# Margins for the framing heuristic (offline only; uses manifest bounds).
_FRAMING_MARGIN = 1.25          # object should sit inside frame * margin
_FRAMING_FAR_FACTOR = 2.5        # beyond fit_distance * this => object too small
_FRAMING_CLOSE_FACTOR = 0.6       # closer than fit_distance * this => clip risk
_FRAMING_MIN_FIT = 0.5           # never divide by ~0


# ---------------------------------------------------------------------------
# LIVE graph analysis
# ---------------------------------------------------------------------------

def analyze_scene_graph(
    harvest: Mapping[str, Any],
    *,
    checks: Sequence[str] = GRAPH_CHECKS,
    strict: bool = False,
) -> SanityReport:
    """Inspect a scene_harvest() result (the live OctaneX node graph).

    Args:
        harvest: dict with a ``nodes`` list. Each node is expected to carry
            ``type``, ``name``, ``has_geometry``, ``has_material``,
            ``visible`` and optionally ``connected`` (list of node names).
        checks: which checks to run (see GRAPH_CHECKS).
        strict: when True, treat likely-blank signals (no lighting, camera not
            wired to the render target) as errors rather than warnings.

    Returns a SanityReport. Never raises for malformed input; it records an
    ``harvest_malformed`` issue instead so the caller still gets a verdict.
    """
    report = SanityReport()
    nodes = harvest.get("nodes")
    if not isinstance(nodes, list):
        report.issues.append(SanityIssue(
            "error", "harvest_malformed",
            "scene_harvest returned no 'nodes' list; cannot inspect graph",
            detail={"keys": list(harvest.keys()) if isinstance(harvest, Mapping) else None},
        ))
        report.checks = list(checks)
        return report

    valid = [n for n in nodes if isinstance(n, Mapping)]
    names = [str(n.get("name") or "") for n in valid]

    if "render_target" in checks:
        report.checks.append("render_target")
        rts = [n for n in valid if _is_render_target(str(n.get("type")))]
        if not rts:
            report.issues.append(SanityIssue(
                "error", "no_render_target",
                "No render target node found; nothing will accept the render"))
        elif len(rts) > 1:
            report.issues.append(SanityIssue(
                "error", "multiple_render_targets",
                f"{len(rts)} render target nodes found ({', '.join(names_of(rts))}); "
                "ambiguous which one renders",
                node=", ".join(names_of(rts))))

    if "camera" in checks:
        report.checks.append("camera")
        cams = [n for n in valid if _is_camera(str(n.get("type")))]
        if not cams:
            report.issues.append(SanityIssue(
                "error", "no_camera",
                "No camera node found; Octane cannot frame the scene"))
        else:
            rt_names = {str(n.get("name")) for n in valid if _is_render_target(str(n.get("type")))}
            for cam in cams:
                connected = cam.get("connected")
                connected = connected if isinstance(connected, list) else []
                wired = any(c in rt_names for c in connected)
                if rt_names and not wired:
                    sev = "error" if strict else "warning"
                    report.issues.append(SanityIssue(
                        sev, "camera_not_connected_to_rt",
                        f"Camera '{cam.get('name')}' is not wired to a render target",
                        node=str(cam.get("name")),
                        detail={"connected": connected}))

    if "lights" in checks:
        report.checks.append("lights")
        lights = [n for n in valid if _is_light(str(n.get("type")))]
        envs = [n for n in valid if _is_environment(str(n.get("type")))]
        if not lights and not envs:
            sev = "error" if strict else "warning"
            report.issues.append(SanityIssue(
                sev, "no_light_environment",
                "No light or environment node present; render will be black"))

    if "meshes" in checks:
        report.checks.append("meshes")
        meshes = [n for n in valid if _is_mesh(str(n.get("type")))]
        if not meshes:
            # Not always fatal (a pure lighting/material test scene could exist),
            # but most renders expect geometry. Report as warning.
            report.issues.append(SanityIssue(
                "warning", "no_mesh",
                "No mesh nodes found; the frame may be empty"))
        for mesh in meshes:
            if mesh.get("has_geometry") is False:
                report.issues.append(SanityIssue(
                    "error", "mesh_missing_geometry",
                    f"Mesh '{mesh.get('name')}' has no geometry attached",
                    node=str(mesh.get("name"))))
            if mesh.get("has_material") is False:
                report.issues.append(SanityIssue(
                    "error", "mesh_unassigned_material",
                    f"Mesh '{mesh.get('name')}' has no material connected",
                    node=str(mesh.get("name"))))
            connected = mesh.get("connected")
            connected = connected if isinstance(connected, list) else []
            if not connected:
                report.issues.append(SanityIssue(
                    "warning", "mesh_not_connected",
                    f"Mesh '{mesh.get('name')}' has no connections",
                    node=str(mesh.get("name"))))

    if "materials" in checks:
        report.checks.append("materials")
        materials = [n for n in valid if _is_material(str(n.get("type")))]
        meshes = [n for n in valid if _is_mesh(str(n.get("type")))]
        mesh_connected_names = set()
        for m in meshes:
            connected = m.get("connected")
            if isinstance(connected, list):
                mesh_connected_names.update(str(c) for c in connected)
        for mat in materials:
            if str(mat.get("name")) not in mesh_connected_names:
                report.issues.append(SanityIssue(
                    "warning", "orphan_material",
                    f"Material '{mat.get('name')}' is not connected to any mesh",
                    node=str(mat.get("name"))))

    if "scale" in checks:
        report.checks.append("scale")
        for n in valid:
            scale = n.get("scale")
            if isinstance(scale, (list, tuple)) and len(scale) == 3:
                if any(not _is_positive_number(s) for s in scale):
                    report.issues.append(SanityIssue(
                        "error", "scale_zero_or_negative",
                        f"Node '{n.get('name')}' has a zero/negative scale component",
                        node=str(n.get("name")),
                        detail={"scale": list(scale)}))

    return report


def names_of(nodes: Sequence[Mapping[str, Any]]) -> list[str]:
    return [str(n.get("name") or "?") for n in nodes]


# ---------------------------------------------------------------------------
# OFFLINE manifest analysis
# ---------------------------------------------------------------------------

def analyze_scene_plan(
    plan: Mapping[str, Any],
    *,
    checks: Sequence[str] = PLAN_CHECKS,
    strict: bool = False,
) -> SanityReport:
    """Inspect a scene manifest/plan BEFORE building, so errors are caught earliest.

    Reads the same semantic fields the build pipeline consumes
    (``objects``, ``materials``, ``camera``, ``lighting``, ``render``) plus the
    per-object ``bounds`` the OBJ generator attaches. Supports precise camera
    framing math that the live graph (which lacks bounds) cannot.
    """
    report = SanityReport()
    if not isinstance(plan, Mapping):
        report.issues.append(SanityIssue(
            "error", "plan_malformed", "scene plan is not a mapping"))
        report.checks = list(checks)
        return report

    objects = plan.get("objects")
    objects = objects if isinstance(objects, list) else []
    materials = plan.get("materials")
    materials = materials if isinstance(materials, list) else []
    camera = plan.get("camera") or {}
    lighting = plan.get("lighting") or {}
    render = plan.get("render") or {}

    def named_materials() -> set[str]:
        out: set[str] = set()
        for m in materials:
            if isinstance(m, Mapping):
                nm = m.get("name") or m.get("id")
                if nm:
                    out.add(str(nm))
        return out

    if "render_target" in checks:
        report.checks.append("render_target")
        # A manifest is assumed to intend rendering if it declares a render block
        # or any object/camera. If neither an object nor a camera nor a render
        # block is present, there is nothing to render.
        if not objects and not camera and not render:
            report.issues.append(SanityIssue(
                "error", "no_render_target",
                "Plan has no objects, camera, or render block; nothing to render"))

    if "camera" in checks:
        report.checks.append("camera")
        if not camera:
            report.issues.append(SanityIssue(
                "error", "no_camera",
                "Plan declares no camera; the scene cannot be framed"))
        else:
            pos = camera.get("position")
            tgt = camera.get("target")
            fov = camera.get("fov", 45)
            if not _is_vec3(pos):
                report.issues.append(SanityIssue(
                    "error", "camera_position_invalid",
                    "Camera position is missing or not a 3-number vector",
                    detail={"position": pos}))
            if not _is_vec3(tgt):
                report.issues.append(SanityIssue(
                    "error", "camera_target_invalid",
                    "Camera target is missing or not a 3-number vector",
                    detail={"target": tgt}))
            if not _is_number(fov) or float(fov) <= 0:
                report.issues.append(SanityIssue(
                    "warning", "degenerate_fov",
                    "Camera fov is missing or non-positive",
                    detail={"fov": fov}))

    if "lights" in checks:
        report.checks.append("lights")
        if not lighting and not render.get("environment"):
            sev = "error" if strict else "warning"
            report.issues.append(SanityIssue(
                sev, "no_light_environment",
                "Plan declares no lighting block; render may be black"))

    if "meshes" in checks:
        report.checks.append("meshes")
        if not objects:
            report.issues.append(SanityIssue(
                "warning", "no_mesh",
                "Plan declares no objects; the frame may be empty"))
        for obj in objects:
            if not isinstance(obj, Mapping):
                continue
            oid = str(obj.get("id") or obj.get("name") or "?")
            if obj.get("type") in ("box", "sphere", "ellipsoid", "cylinder"):
                pass  # primitive -> OBJ generated at build time; path set later
            elif str(obj.get("type", "mesh")) == "mesh":
                if not obj.get("path"):
                    report.issues.append(SanityIssue(
                        "error", "object_missing_path",
                        f"Mesh object '{oid}' has no geometry path",
                        node=oid))

    if "materials" in checks:
        report.checks.append("materials")
        referenced = {
            str(o.get("material"))
            for o in objects
            if isinstance(o, Mapping) and o.get("material")
        }
        for mat in named_materials():
            if mat not in referenced:
                report.issues.append(SanityIssue(
                    "warning", "material_unused",
                    f"Material '{mat}' is defined but no object references it",
                    node=mat))

    if "scale" in checks:
        report.checks.append("scale")
        for obj in objects:
            if not isinstance(obj, Mapping):
                continue
            oid = str(obj.get("id") or obj.get("name") or "?")
            tr = obj.get("transform") or {}
            scale = tr.get("scale") if isinstance(tr, Mapping) else None
            if isinstance(scale, (list, tuple)) and len(scale) == 3:
                if any(not _is_positive_number(s) for s in scale):
                    report.issues.append(SanityIssue(
                        "error", "scale_zero_or_negative",
                        f"Object '{oid}' has a zero/negative scale component",
                        node=oid, detail={"scale": list(scale)}))

    if "framing" in checks:
        report.checks.append("framing")
        _check_framing(plan, objects, camera, report)

    return report


def _check_framing(
    plan: Mapping[str, Any],
    objects: Sequence[Mapping[str, Any]],
    camera: Mapping[str, Any],
    report: SanityReport,
) -> None:
    bounds = [
        o.get("bounds")
        for o in objects
        if isinstance(o, Mapping) and isinstance(o.get("bounds"), Mapping)
    ]
    if not bounds:
        return  # cannot frame without bounds; not an error
    centers: list[list[float]] = []
    radii: list[float] = []
    for b in bounds:
        c = b.get("center", [0.0, 0.0, 0.0])
        r = max(float(b.get("radius", 1.0)), 0.01)
        if _is_vec3(c):
            centers.append([float(x) for x in c])
            radii.append(r)
    if not centers:
        return
    centroid = [sum(c[i] for c in centers) / len(centers) for i in range(3)]
    max_r = max(radii)
    pos = camera.get("position")
    tgt = camera.get("target")
    fov = float(camera.get("fov", 45))
    if not (_is_vec3(pos) and _is_vec3(tgt)) or fov <= 0:
        return
    pos_v = [float(x) for x in pos]
    tgt_v = [float(x) for x in tgt]
    dist_target = math.dist(pos_v, tgt_v)
    if dist_target < _FRAMING_MIN_FIT * max_r:
        report.issues.append(SanityIssue(
            "error", "camera_inside_geometry",
            "Camera is at/inside the scene bounds; the frame will be blank or clipped",
            detail={"distance_to_target": round(dist_target, 3), "scene_radius": round(max_r, 3)}))
        return
    fit_distance = (max_r / math.tan(math.radians(fov) / 2.0)) * _FRAMING_MARGIN
    fit_distance = max(fit_distance, _FRAMING_MIN_FIT)
    if dist_target > fit_distance * _FRAMING_FAR_FACTOR:
        report.issues.append(SanityIssue(
            "error", "camera_too_far",
            "Camera is too far from the subject; the object will render tiny/empty",
            detail={"distance_to_target": round(dist_target, 3),
                    "fit_distance": round(fit_distance, 3)}))
    elif dist_target < fit_distance * _FRAMING_CLOSE_FACTOR:
        report.issues.append(SanityIssue(
            "warning", "camera_too_close",
            "Camera is very close to the subject; risk of frame-edge clipping",
            detail={"distance_to_target": round(dist_target, 3),
                    "fit_distance": round(fit_distance, 3)}))


# ---------------------------------------------------------------------------
# Small type helpers
# ---------------------------------------------------------------------------

def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_positive_number(value: Any) -> bool:
    return _is_number(value) and float(value) > 0.0


def _is_vec3(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and len(value) == 3
        and all(_is_number(x) for x in value)
    )


# ---------------------------------------------------------------------------
# Chat-facing summary
# ---------------------------------------------------------------------------

def summarize(report: SanityReport) -> str:
    """One-line-ish human summary of a sanity report (for chat output)."""
    if not report.issues:
        return f"[OK] graph sane across {len(report.checks)} checks"
    verdict = "FAIL" if report.errors else "WARN"
    lines = [f"[{verdict}] {len(report.errors)} error(s), {len(report.warnings)} warning(s)"]
    for issue in report._sorted():
        icon = "✗" if issue.severity == "error" else "!"
        node = f" ({issue.node})" if issue.node else ""
        lines.append(f"  {icon} {issue.code}{node}: {issue.message}")
    return "\n".join(lines)
