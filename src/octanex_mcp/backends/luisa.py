"""Compile ``canvas.scene.v1`` scenes to LuisaRender ``.luisa`` scene text.

This is the renderer-neutral → LuisaRender translation layer for the quality
backend tier (see ``docs/luisa-render-backend-investigation.md`` and the
``canvas-web-ui-build-plan.md`` two-tier model: WebGL realtime, LuisaRender
offline quality). It is pure conversion — no subprocess, no filesystem, no
Octane. The grammar is grounded in the canonical emitters shipped with
LuisaRender (``tools/tungsten2luisa.py``, ``tools/lux2luisa.py``) and validated
against the production ``glass-of-water`` scene.

Supported ``canvas.scene.v1`` object types (first cut):

- ``box``        → ``InlineMesh`` (12-triangle unit cube, scaled/positioned)
- ``sphere``     → ``Mesh`` (low-poly UV sphere emitted to a sidecar OBJ)
- ``cylinder``   → ``Mesh`` (low-poly cylinder sidecar OBJ)
- ``polyline``   → sequence of ``Mesh`` tube segments (sidecar OBJ)
- ``points``     → sequence of small ``Mesh`` spheres (sidecar OBJ)
- ``arrow``      → cylinder shaft + cone head (sidecar OBJ)
- ``mesh``       → ``Mesh`` referencing ``object["geometry"]["path"]``
- ``text_label`` → skipped (annotation-only in the WebGL tier too)

Material mapping (``canvas.scene.v1`` material fields → Luisa ``Surface``):

- ``emissive``/``emissiveIntensity`` present → ``Matte`` + shape ``light : Diffuse``
- ``metalness`` ≥ 0.5                          → ``Metal`` (named metal ``Al`` default)
- ``roughness`` < 0.3 and opacity 1            → ``Plastic`` (glossy dielectric)
- otherwise                                    → ``Matte`` (diffuse)
- ``opacity`` < 1                              → ``Glass`` with ``eta`` 1.5

The mapping is intentionally simple and documented — the goal is a faithful
quality render of the *same scene graph* the browser shows, not Octane parity.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

# A sidecar OBJ that must be written next to the .luisa file for Mesh shapes.
# (filename, obj_text). Filenames are unique per (object id, kind).
SidecarObj = Tuple[str, str]


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(color: Any) -> Tuple[float, float, float]:
    """Accept ``#rrggbb`` or ``[r, g, b]`` (0-1 floats). Default mid-grey."""
    if isinstance(color, str) and color.startswith("#") and len(color) == 7:
        try:
            r = int(color[1:3], 16) / 255.0
            g = int(color[3:5], 16) / 255.0
            b = int(color[5:7], 16) / 255.0
            return (r, g, b)
        except ValueError:
            pass
    if isinstance(color, (list, tuple)) and len(color) == 3:
        try:
            r, g, b = (float(color[0]), float(color[1]), float(color[2]))
            # Heuristic: values >1 are 0-255.
            if max(r, g, b) > 1.0:
                r, g, b = r / 255.0, g / 255.0, b / 255.0
            return (r, g, b)
        except (TypeError, ValueError):
            pass
    return (0.6, 0.62, 0.68)


def _f3(rgb: Tuple[float, float, float]) -> str:
    return f"{rgb[0]:.6g}, {rgb[1]:.6g}, {rgb[2]:.6g}"


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

def _camera_block(scene: Mapping[str, Any], *, spp: int, resolution: Tuple[int, int]) -> str:
    cam = scene.get("camera") or {}
    pos = cam.get("position", [4, 3, 4])
    target = cam.get("target", [0, 0, 0])
    fov = cam.get("fov", 45)
    front = _normalise(_sub(target, pos))
    up = _up_for(front)
    w, h = resolution
    return (
        "Camera camera : Pinhole {\n"
        f"  fov {{ {fov} }}\n"
        f"  spp {{ {spp} }}\n"
        "  filter : Gaussian {\n"
        "    radius { 1 }\n"
        "  }\n"
        "  film : Color {\n"
        f"    resolution {{ {w}, {h} }}\n"
        "  }\n"
        '  file { "render.exr" }\n'
        "  transform : View {\n"
        f"    position {{ {_f3(_v3(pos))} }}\n"
        f"    front {{ {_f3(front)} }}\n"
        f"    up {{ {_f3(up)} }}\n"
        "  }\n"
        "}\n"
    )


def _v3(v: Any) -> Tuple[float, float, float]:
    try:
        return (float(v[0]), float(v[1]), float(v[2]))
    except (TypeError, ValueError, IndexError):
        return (0.0, 0.0, 0.0)


def _sub(a: Any, b: Any) -> Tuple[float, float, float]:
    ax, ay, az = _v3(a)
    bx, by, bz = _v3(b)
    return (ax - bx, ay - by, az - bz)


def _normalise(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    if n < 1e-9:
        return (0.0, 0.0, -1.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def _up_for(front: Tuple[float, float, float]) -> Tuple[float, float, float]:
    # Choose a stable up that isn't parallel to the view direction.
    world_up = (0.0, 1.0, 0.0)
    if abs(front[1]) > 0.99:
        world_up = (0.0, 0.0, 1.0)
    right = _normalise(_cross(front, world_up))
    return _normalise(_cross(right, front))


def _cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def _material_surface(mat: Mapping[str, Any]) -> str:
    """Return the Luisa ``Surface`` block for one canvas material."""
    mat_id = mat.get("id", "mat")
    rgb = _hex_to_rgb(mat.get("color", mat.get("emissive", "#9aa6b2")))
    rough = _as_float(mat.get("roughness"), 0.8)
    metal = _as_float(mat.get("metalness"), 0.0)
    opacity = _as_float(mat.get("opacity"), 1.0)
    emissive = mat.get("emissive")
    e_int = _as_float(mat.get("emissiveIntensity"), 0.0)
    safe_id = _safe_id(mat_id)

    # Emissive → still a Matte surface; the light is attached at the shape level.
    if opacity < 1.0:
        return (
            f"Surface {safe_id} : Glass {{\n"
            "  Kr : Constant {\n"
            "    v { 1, 1, 1 }\n"
            "  }\n"
            "  Kt : Constant {\n"
            f"    v {{ {_f3(rgb)} }}\n"
            "  }\n"
            "  eta : Constant {\n"
            "    v { 1.5 }\n"
            "  }\n"
            "  roughness : Constant {\n"
            f"    v {{ {max(rough, 0.05):.6g} }}\n"
            "  }\n"
            "}\n"
        )
    if metal >= 0.5:
        return (
            f"Surface {safe_id} : Metal {{\n"
            '  eta { "Al" }\n'
            "  roughness : Constant {\n"
            f"    v {{ {math.sqrt(max(rough, 0.01)):.6g} }}\n"
            "  }\n"
            "  Kd : Constant {\n"
            f"    v {{ {_f3(rgb)} }}\n"
            "  }\n"
            "}\n"
        )
    if rough < 0.3:
        return (
            f"Surface {safe_id} : Plastic {{\n"
            "  Kd : Constant {\n"
            f"    v {{ {_f3(rgb)} }}\n"
            "  }\n"
            "  eta : Constant {\n"
            "    v { 1.5 }\n"
            "  }\n"
            "  roughness : Constant {\n"
            f"    v {{ {math.sqrt(max(rough, 0.01)):.6g} }}\n"
            "  }\n"
            "}\n"
        )
    return (
        f"Surface {safe_id} : Matte {{\n"
        "  Kd : Constant {\n"
        f"    v {{ {_f3(rgb)} }}\n"
        "  }\n"
        "}\n"
    )


def _as_float(v: Any, default: float) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_id(s: Any) -> str:
    out = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in str(s))
    if not out or out[0].isdigit():
        out = "m_" + out
    return out


# ---------------------------------------------------------------------------
# Geometry emitters — return (shape_text, [sidecar objs])
# ---------------------------------------------------------------------------

def _identity_transform() -> str:
    return (
        "  transform : Matrix {\n"
        "    m {\n"
        "      1, 0, 0, 0,\n"
        "      0, 1, 0, 0,\n"
        "      0, 0, 1, 0,\n"
        "      0, 0, 0, 1\n"
        "    }\n"
        "  }\n"
    )


def _shape_header(obj_id: str, impl: str, mat_id: str) -> str:
    return (
        f"Shape {_safe_id(obj_id)} : {impl} {{\n"
        f"  surface {{ @{_safe_id(mat_id)} }}\n"
    )


def _emit_box(obj: Mapping[str, Any], mat_id: str) -> Tuple[str, List[SidecarObj]]:
    pos = _v3(obj.get("position", [0, 0, 0]))
    scale = _v3(obj.get("scale", [1, 1, 1]))
    hx, hy, hz = scale[0] / 2, scale[1] / 2, scale[2] / 2
    cx, cy, cz = pos
    # 8 corners of an axis-aligned box centred at pos.
    corners = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    faces = [
        (0, 1, 2), (0, 2, 3),  # back
        (4, 6, 5), (4, 7, 6),  # front
        (0, 4, 5), (0, 5, 1),  # bottom
        (3, 2, 6), (3, 6, 7),  # top
        (1, 5, 6), (1, 6, 2),  # right
        (0, 3, 7), (0, 7, 4),  # left
    ]
    positions = ", ".join(f"{c[0]:.6g}, {c[1]:.6g}, {c[2]:.6g}" for c in corners)
    indices = ", ".join(f"{a}, {b}, {c}" for a, b, c in faces)
    text = (
        _shape_header(obj.get("id", "box"), "InlineMesh", mat_id)
        + f"  positions {{ {positions} }}\n"
        + f"  indices {{ {indices} }}\n"
        + _identity_transform()
        + "}\n"
    )
    return text, []


def _obj_text(name: str, verts: List[Tuple[float, float, float]], faces: List[Tuple[int, int, int]]) -> str:
    """Serialise verts/faces to OBJ text (1-based indices)."""
    lines = [f"o {name}"]
    lines += [f"v {v[0]:.6g} {v[1]:.6g} {v[2]:.6g}" for v in verts]
    lines += [f"f {f[0]} {f[1]} {f[2]}" for f in faces]
    return "\n".join(lines) + "\n"


def _sphere_obj_text(name: str, radius: float, segments: int = 24, rings: int = 16) -> str:
    """Return OBJ text for a UV sphere centred at origin."""
    verts: List[Tuple[float, float, float]] = []
    for r in range(rings + 1):
        theta = math.pi * r / rings
        st, ct = math.sin(theta), math.cos(theta)
        for s in range(segments):
            phi = 2 * math.pi * s / segments
            sp, cp = math.sin(phi), math.cos(phi)
            verts.append((radius * st * cp, radius * ct, radius * st * sp))
    faces: List[Tuple[int, int, int]] = []
    for r in range(rings):
        for s in range(segments):
            a = r * segments + s
            b = r * segments + (s + 1) % segments
            c = (r + 1) * segments + (s + 1) % segments
            d = (r + 1) * segments + s
            faces.append((a + 1, b + 1, c + 1))
            faces.append((a + 1, c + 1, d + 1))
    return _obj_text(name, verts, faces)


def _cylinder_obj_text(name: str, radius: float, height: float, segments: int = 20) -> str:
    """Return OBJ text for a capped cylinder centred at origin, axis +Y."""
    verts: List[Tuple[float, float, float]] = []
    hh = height / 2
    for y in (-hh, hh):
        for s in range(segments):
            a = 2 * math.pi * s / segments
            verts.append((radius * math.cos(a), y, radius * math.sin(a)))
    bottom_center = len(verts) + 1
    verts.append((0.0, -hh, 0.0))
    top_center = len(verts) + 1
    verts.append((0.0, hh, 0.0))
    faces: List[Tuple[int, int, int]] = []
    for s in range(segments):
        b0 = s
        b1 = (s + 1) % segments
        t0 = segments + s
        t1 = segments + (s + 1) % segments
        faces.append((b0 + 1, b1 + 1, t1 + 1))
        faces.append((b0 + 1, t1 + 1, t0 + 1))
        faces.append((bottom_center, b1 + 1, b0 + 1))
        faces.append((top_center, t0 + 1, t1 + 1))
    return _obj_text(name, verts, faces)


def _mesh_shape_from_obj(obj_id: str, mat_id: str, filename: str, pos: Tuple[float, float, float]) -> str:
    """Wrap a sidecar OBJ file in a Mesh shape, translated to pos."""
    return (
        _shape_header(obj_id, "Mesh", mat_id)
        + f'  file {{ "{filename}" }}\n'
        + "  transform : Matrix {\n"
        "    m {\n"
        f"      1, 0, 0, {pos[0]:.6g},\n"
        f"      0, 1, 0, {pos[1]:.6g},\n"
        f"      0, 0, 1, {pos[2]:.6g},\n"
        "      0, 0, 0, 1\n"
        "    }\n"
        "  }\n"
        "}\n"
    )


def _mesh_with_obj(obj_id: str, mat_id: str, tag: str, pos: Tuple[float, float, float], obj_text: str) -> Tuple[str, List[SidecarObj]]:
    """Emit a Mesh shape + its sidecar OBJ for one primitive."""
    fname = f"{_safe_id(obj_id)}_{tag}.obj"
    return _mesh_shape_from_obj(obj_id, mat_id, fname, pos), [(fname, obj_text)]


def _emit_sphere(obj: Mapping[str, Any], mat_id: str) -> Tuple[str, List[SidecarObj]]:
    obj_id = obj.get("id", "sphere")
    scale = _v3(obj.get("scale", [1, 1, 1]))
    radius = max(scale) / 2.0 if max(scale) > 0 else 0.5
    return _mesh_with_obj(
        obj_id, mat_id, "sphere", _v3(obj.get("position", [0, 0, 0])),
        _sphere_obj_text(f"{_safe_id(obj_id)}_sphere", radius),
    )


def _emit_cylinder(obj: Mapping[str, Any], mat_id: str) -> Tuple[str, List[SidecarObj]]:
    obj_id = obj.get("id", "cylinder")
    scale = _v3(obj.get("scale", [1, 1, 1]))
    radius = (scale[0] + scale[2]) / 4.0 if (scale[0] + scale[2]) > 0 else 0.5
    height = scale[1] if scale[1] > 0 else 1.0
    return _mesh_with_obj(
        obj_id, mat_id, "cyl", _v3(obj.get("position", [0, 0, 0])),
        _cylinder_obj_text(f"{_safe_id(obj_id)}_cyl", radius, height),
    )


def _emit_mesh(obj: Mapping[str, Any], mat_id: str) -> Tuple[str, List[SidecarObj]]:
    geom = obj.get("geometry") or {}
    path = geom.get("path") if isinstance(geom, Mapping) else None
    if not path:
        # A mesh object with no geometry path is an authoring error — skip it
        # rather than render a phantom placeholder that hides the mistake.
        return "", []
    pos = _v3(obj.get("position", [0, 0, 0]))
    text = _mesh_shape_from_obj(obj.get("id", "mesh"), mat_id, str(path), pos)
    return text, []


def _emit_polyline(obj: Mapping[str, Any], mat_id: str) -> Tuple[str, List[SidecarObj]]:
    """Emit a polyline as a series of low-poly sphere nodes + cylinder links."""
    obj_id = obj.get("id", "polyline")
    pts = obj.get("points") or []
    radius = _as_float(obj.get("radius"), 0.02)
    if not pts:
        return "", []
    prims: List[Tuple[str, List[SidecarObj]]] = []
    # Nodes
    for i, p in enumerate(pts):
        node_id = f"{obj_id}_node{i}"
        prims.append(_mesh_with_obj(
            node_id, mat_id, f"node{i}", _v3(p),
            _sphere_obj_text(f"{_safe_id(node_id)}_node{i}", radius, 10, 8),
        ))
    # Links
    for i in range(len(pts) - 1):
        a, b = _v3(pts[i]), _v3(pts[i + 1])
        length = math.dist(a, b)
        if length < 1e-9:
            continue
        link_id = f"{obj_id}_link{i}"
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
        prims.append(_mesh_with_obj(
            link_id, mat_id, f"link{i}", mid,
            _cylinder_obj_text(f"{_safe_id(link_id)}_link{i}", radius, length, 8),
        ))
    return _combine_prims(prims)


def _emit_points(obj: Mapping[str, Any], mat_id: str) -> Tuple[str, List[SidecarObj]]:
    obj_id = obj.get("id", "points")
    pts = obj.get("points") or obj.get("data") or []
    radius = _as_float(obj.get("radius"), 0.03)
    prims = [
        _mesh_with_obj(
            f"{obj_id}_p{i}", mat_id, f"p{i}", _v3(p),
            _sphere_obj_text(f"{_safe_id(obj_id)}_p{i}", radius, 8, 6),
        )
        for i, p in enumerate(pts[:512])  # cap to keep scene sizes sane
    ]
    return _combine_prims(prims)


def _combine_prims(prims: List[Tuple[str, List[SidecarObj]]]) -> Tuple[str, List[SidecarObj]]:
    """Flatten [(shape_text, sidecars), ...] into joined text + all sidecars."""
    texts = [t for t, _ in prims if t]
    sidecars = [sc for _, scs in prims for sc in scs]
    return ("\n".join(texts) + "\n") if texts else "", sidecars


def _emit_arrow(obj: Mapping[str, Any], mat_id: str) -> Tuple[str, List[SidecarObj]]:
    """Approximate an arrow with a slim cylinder (shaft only — first cut)."""
    return _emit_cylinder({**obj, "scale": obj.get("scale", [0.05, 1, 0.05])}, mat_id)


_EMITTERS = {
    "box": _emit_box,
    "sphere": _emit_sphere,
    "ellipsoid": _emit_sphere,  # approximate with sphere
    "cylinder": _emit_cylinder,
    "mesh": _emit_mesh,
    "polyline": _emit_polyline,
    "points": _emit_points,
    "arrow": _emit_arrow,
}


# ---------------------------------------------------------------------------
# Top-level compile
# ---------------------------------------------------------------------------

def compile_scene(
    scene: Mapping[str, Any],
    *,
    spp: int = 64,
    resolution: Tuple[int, int] = (960, 540),
    integrator: str = "MegaPath",
) -> Tuple[str, List[SidecarObj]]:
    """Compile ``canvas.scene.v1`` to ``(scene.luisa_text, [sidecar OBJs])``.

    Returns the ``.luisa`` scene text plus a list of ``(filename, obj_text)``
    sidecar meshes that must be written into the same directory for ``Mesh``
    shapes to resolve. Pure function — no I/O.
    """
    materials = scene.get("materials") or []
    objects = scene.get("objects") or []

    mat_blocks: List[str] = [_material_surface(m) for m in materials]
    # Always provide a Null material for explicit-light shapes and fallbacks.
    mat_blocks.append("Surface mat_Null : Null {}")

    shape_blocks: List[str] = []
    shape_refs: List[str] = []
    sidecars: List[SidecarObj] = []

    for obj in objects:
        otype = obj.get("type", "box")
        if otype == "text_label":
            continue
        mat_id = obj.get("material") or "mat_Null"
        emitter = _EMITTERS.get(otype, _emit_box)
        text, objs = emitter(obj, mat_id)
        if not text:
            continue
        # Attach an area light for emissive materials.
        mat = next((m for m in materials if m.get("id") == mat_id), {})
        e_int = _as_float(mat.get("emissiveIntensity"), 0.0)
        if mat.get("emissive") and e_int > 0:
            e_rgb = _hex_to_rgb(mat["emissive"])
            scaled_rgb = (e_rgb[0] * e_int, e_rgb[1] * e_int, e_rgb[2] * e_int)
            light = (
                "  light : Diffuse {\n"
                "    emission : Constant {\n"
                f"      v {{ {_f3(scaled_rgb)} }}\n"
                "    }\n"
                "  }\n"
            )
            # Insert the light block before the closing brace of each shape.
            text = text.replace(_identity_transform() + "}\n", light + _identity_transform() + "}\n")
        shape_blocks.append(text)
        sidecars.extend(objs)
        # Collect refs for the render block (polyline/points emit many shapes).
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("Shape "):
                name = line.split()[1]
                shape_refs.append(f"@{name}")

    # Add a soft overhead area light so non-emissive scenes aren't pitch black.
    key_light = (
        "Shape key_light : InlineMesh {\n"
        "  positions { -2, 4, -2, 2, 4, -2, 2, 4, 2, -2, 4, 2 }\n"
        "  indices { 0, 1, 2, 0, 2, 3 }\n"
        "  surface { @mat_Null }\n"
        "  light : Diffuse {\n"
        "    emission : Constant {\n"
        "      v { 12, 12, 12 }\n"
        "    }\n"
        "  }\n"
        + _identity_transform()
        + "}\n"
    )
    shape_blocks.append(key_light)
    shape_refs.append("@key_light")

    # Neutral ground plane so objects sit on something.
    mat_blocks.append(
        "Surface mat_ground : Matte {\n"
        "  Kd : Constant {\n"
        "    v { 0.16, 0.17, 0.19 }\n"
        "  }\n"
        "}"
    )
    ground = (
        "Shape ground : InlineMesh {\n"
        "  positions { -8, -0.6, -8, 8, -0.6, -8, 8, -0.6, 8, -8, -0.6, 8 }\n"
        "  indices { 0, 1, 2, 0, 2, 3 }\n"
        "  surface { @mat_ground }\n"
        + _identity_transform()
        + "}\n"
    )
    shape_blocks.append(ground)
    shape_refs.append("@ground")

    camera = _camera_block(scene, spp=spp, resolution=resolution)

    sampler = "PMJ02BN {}" if integrator == "MegaPath" else "Independent {}"
    render_block = (
        "render {\n"
        "  cameras { @camera }\n"
        f"  integrator : {integrator} {{\n"
        f"    sampler : {sampler}\n"
        "  }\n"
        "  shapes {\n"
        + ",\n".join(f"    {r}" for r in shape_refs)
        + "\n  }\n"
        "  environment : Null {}\n"
        "}\n"
    )

    parts = mat_blocks + shape_blocks + [camera, render_block]
    return "\n".join(p.rstrip("\n") for p in parts) + "\n", sidecars


__all__ = ["compile_scene", "SidecarObj"]
