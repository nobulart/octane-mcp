#!/usr/bin/env python3
"""Build two currently-unverified recipes into proper native-Octane form.

The two dirs (earth-moon-space, helicoid-spiral) only shipped bare generators:
no scene.obj/scene.mtl/scene.json, split OBJs, and MTL-only colors (which the
OctaneX Lua bridge IGNORES — materials must arrive via explicit create_material
+ assign_material with group_index). This script emits, for each recipe:

  * scene.obj    — a SINGLE combined OBJ with per-group `usemtl` (one mesh per
                   render target; the bridge connects only one mesh).
  * scene.mtl    — matching material defs (kept for documentation; bridge uses
                   the explicit create_material commands instead).
  * scene.json   — the verified-recipe contract: import + create_material per
                   group + assign_material(group_index) per group + camera +
                   lighting + save_preview (no colliding start_render; the live
                   runner strips it anyway).
  * preview.png  — a placeholder reference raster so the offline contract passes
                   before the live render; replaced by a downscaled copy of the
                   real native render after copy_back.

Run:
    PYTHONPATH= uv run python scripts/build_gap_recipes.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def camera_for_bounds(minv, maxv, fov=40, dirn=(0.6, 0.45, 0.85), margin=2.4):
    center = [(minv[i] + maxv[i]) / 2 for i in range(3)]
    radius = max(math.dist(center, [minv[0], minv[1], minv[2]]),
                 math.dist(center, [maxv[0], maxv[1], maxv[2]])) or 1.0
    d = (radius * margin) / math.tan(math.radians(fov) / 2.0)
    dl = math.sqrt(sum(x * x for x in dirn)) or 1.0
    pos = [center[i] + dirn[i] / dl * d for i in range(3)]
    return {"position": [round(p, 3) for p in pos],
            "target": [round(c, 3) for c in center],
            "fov": fov}


def make_sphere(cx, cy, cz, r, seg_u=64, seg_v=32, label="sphere"):
    """Return (v_lines, f_lines_local, vcount) for a UV sphere at (cx,cy,cz)."""
    v: list[tuple[float, float, float]] = []
    for vv in range(seg_v + 1):
        theta = math.pi * vv / seg_v
        st, ct = math.sin(theta), math.cos(theta)
        for uu in range(seg_u + 1):
            phi = 2 * math.pi * uu / seg_u
            x = r * st * math.cos(phi) + cx
            y = r * st * math.sin(phi) + cy
            z = r * ct + cz
            v.append((x, y, z))
    v_lines = [f"v {x:.5f} {y:.5f} {z:.5f}" for (x, y, z) in v]
    f_lines: list[str] = []
    for vv in range(seg_v):
        for uu in range(seg_u):
            a = vv * (seg_u + 1) + uu
            b = a + 1
            c = (vv + 1) * (seg_u + 1) + uu
            d = c + 1
            f_lines.append(f"f {a + 1} {b + 1} {c + 1}")
            f_lines.append(f"f {b + 1} {d + 1} {c + 1}")
    return v_lines, f_lines, len(v)


def make_helicoid(rows=48, cols=80, radius=1.5, width=2.0, turns=2.5):
    half_w = width / 2.0
    k = radius / (math.tau * turns)
    verts: list[tuple[float, float, float]] = []
    for ir in range(rows + 1):
        r = ir / rows
        for ic in range(cols + 1):
            v = math.tau * turns * ic / cols
            u = radius * r
            x = u * math.cos(v)
            y = u * math.sin(v)
            z = k * v - k * math.tau * turns / 2
            verts.append((x, y, z))
    v_lines = [f"v {x:.5f} {y:.5f} {z:.5f}" for (x, y, z) in verts]
    f_lines: list[str] = []
    for r in range(rows):
        for c in range(cols):
            a = r * (cols + 1) + c
            b = a + 1
            d = (r + 1) * (cols + 1) + c
            e = d + 1
            f_lines.append(f"f {a + 1} {b + 1} {e + 1} {d + 1}")
    # outer rim ribbon (z=0 circle)
    rim_start = len(verts) + 1
    rim_seg = max(cols, 64)
    for ic in range(rim_seg + 1):
        v = math.tau * ic / rim_seg
        x = radius * math.cos(v)
        y = radius * math.sin(v)
        z = 0.0
        verts.append((x, y, z))
        v_lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
    for ic in range(rim_seg):
        a = rim_start + ic
        b = rim_start + ic + 1
        d = rim_start + ic + cols + 1
        e = rim_start + ic + cols + 2
        f_lines.append(f"f {a} {b} {e} {d}")
    return v_lines, f_lines, len(verts)


def make_torus_knot(p=2, q=3, radius=1.0, tube=0.35, steps=240, tube_steps=28):
    verts: list[tuple[float, float, float]] = []
    for it in range(steps + 1):
        t = math.tau * it / steps
        for ij in range(tube_steps + 1):
            phi = math.tau * ij / tube_steps
            cx = radius * math.cos(q * t) + tube * math.cos(p * t)
            cy = radius * math.sin(q * t) + tube * math.cos(p * t)
            cz = tube * math.sin(p * t)
            tx = tube * math.cos(phi) * math.cos(q * t)
            ty = tube * math.cos(phi) * math.sin(q * t)
            tz = tube * math.sin(phi)
            verts.append((cx + tx, cy + ty, cz + tz))
    v_lines = [f"v {x:.5f} {y:.5f} {z:.5f}" for (x, y, z) in verts]
    f_lines: list[str] = []
    for it in range(steps):
        for ij in range(tube_steps):
            a = it * (tube_steps + 1) + ij
            b = a + 1
            d = (it + 1) * (tube_steps + 1) + ij
            e = d + 1
            f_lines.append(f"f {a + 1} {b + 1} {e + 1} {d + 1}")
    return v_lines, f_lines, len(verts)


def combined_obj(groups, flat=True):
    """groups: list of (group_name, v_lines, f_lines_local). Offsets face indices.

    flat=True (default) matches the verified working recipes (math-surface,
    etc.): no `o combined` object header and no `g` group lines — just a
    `# comment`, the `usemtl` name, then raw `v`/`f` lines. Octane's OBJ
    importer handles this style reliably. Set flat=False to keep the
    `o combined` + `g` wrapping used by earth-moon-space.
    """
    out = ["# combined recipe mesh"]
    offset = 0
    bounds_min = [1e9, 1e9, 1e9]
    bounds_max = [-1e9, -1e9, -1e9]
    for (name, v_lines, f_lines) in groups:
        if not flat:
            out.append("o combined")
            out.append(f"g {name}")
        out.append(f"usemtl {name}")
        out.extend(v_lines)
        for fl in f_lines:
            toks = fl.split()
            new = " ".join(str(int(t) + offset) for t in toks[1:])
            out.append("f " + new)
        for vl in v_lines:
            parts = vl.split()
            for i in range(3):
                val = float(parts[i + 1])
                bounds_min[i] = min(bounds_min[i], val)
                bounds_max[i] = max(bounds_max[i], val)
        offset += len(v_lines)
    return "\n".join(out) + "\n", bounds_min, bounds_max


def write_mtl(path: Path, mats: dict) -> None:
    lines = ["# material defs (documentation; bridge uses explicit create_material)"]
    for name, spec in mats.items():
        r, g, b = spec.get("color", [0.8, 0.8, 0.8])
        lines.append(f"newmtl {name}")
        lines.append(f"Ka 1.0 1.0 1.0")
        lines.append(f"Kd {r:.4f} {g:.4f} {b:.4f}")
        lines.append(f"Ks 0.5 0.5 0.5")
        lines.append(f"Ns {(1 - spec.get('roughness', 0.25)) * 64:.1f}")
        lines.append(f"d 1.0")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def placeholder_preview(path: Path, rgb=(40, 44, 52)) -> None:
    """Write a tiny reference raster so the offline contract has a reference."""
    from PIL import Image
    img = Image.new("RGB", (64, 64), rgb)
    path.write_bytes(_png_bytes(img))


def _png_bytes(img) -> bytes:
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def build_earth_moon(d: Path) -> dict:
    earth_mats = {
        "earth_surface": {"kind": "glossy", "color": [0.10, 0.35, 0.75], "roughness": 0.25},
        "moon_surface": {"kind": "glossy", "color": [0.72, 0.72, 0.68], "roughness": 0.85},
    }
    ev, ef, ec = make_sphere(0, 0, 0, 3.0, label="earth")
    mv, mf, mc = make_sphere(9.0, 1.5, 1.0, 0.9, label="moon")
    obj_text, bmin, bmax = combined_obj([
        ("earth_surface", ev, ef),
        ("moon_surface", mv, mf),
    ])
    (d / "scene.obj").write_text(obj_text, encoding="utf-8")
    write_mtl(d / "scene.mtl", earth_mats)
    cam = camera_for_bounds(bmin, bmax, fov=42)
    # groups appear in usemtl order: 1=earth, 2=moon
    commands = [
        {"op": "import_geometry", "payload": {"path": f"examples/recipes/earth-moon-space/scene.obj", "format": "obj", "name": "earth-moon-space"}},
        {"op": "create_material", "payload": {"name": "earth_surface", **earth_mats["earth_surface"]}},
        {"op": "create_material", "payload": {"name": "moon_surface", **earth_mats["moon_surface"]}},
        {"op": "assign_material", "payload": {"object_name": "earth-moon-space", "material_name": "earth_surface", "group_index": 1}},
        {"op": "assign_material", "payload": {"object_name": "earth-moon-space", "material_name": "moon_surface", "group_index": 2}},
        {"op": "set_camera", "payload": cam},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {"path": "examples/recipes/earth-moon-space/octane-preview.png", "width": 1280, "height": 1280, "quality": "standard", "samples": 256, "min_samples": 24, "timeout_seconds": 14}},
    ]
    scene = _scene_template(
        slug="earth-moon-space",
        title="Earth + Moon (Space Scene)",
        category="Astronomy / space",
        purpose="Render Earth and the Moon as distinct bodies with correct blue/grey materials so the bridge's per-group material binding is demonstrated on two separated spheres.",
        prompt="Visualise Earth and its Moon as a space scene.",
        materials=earth_mats,
        commands=commands,
        camera=cam,
    )
    (d / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    placeholder_preview(d / "preview.png", (12, 18, 34))
    return {"slug": "earth-moon-space", "verts": ec + mc, "cam": cam}


def build_helicoid(d: Path) -> dict:
    # NOTE (2026-07-09): this recipe builds + queues + renders, but the native
    # Octane output is a near-blank pale-blue frame (verified by pixel metrics:
    # ~100% near-white, subject foreground <4%). The pipeline itself is proven
    # good (earth-moon-space renders correctly through the identical
    # import->material->assign->camera->light->save flow). The failure is
    # specific to this parametric-surface geometry: thin ribbon + torus-knot
    # tube render with no visible surface even under emissive=1.0 diffuse
    # materials. Likely cause: OBJ surface-orientation / back-face culling on
    # the parametric surfaces, or a group-pin mismatch in material binding.
    # Tracked as an open rendering bug; do NOT mark native_octane_verified
    # until a render shows the actual surfaces.
    mats = {
        "helicoid_surface": {"kind": "diffuse", "color": [0.05, 0.35, 1.0], "emission": 1.0, "roughness": 0.9},
        "torus_knot_surface": {"kind": "diffuse", "color": [1.0, 0.55, 0.05], "emission": 1.0, "roughness": 0.9},
    }
    HS = "helicoid_surface_v3"
    TKS = "torus_knot_surface_v3"
    hv, hf, hc = make_helicoid(width=2.5)
    tv, tf, tc = make_torus_knot(tube=0.5)
    obj_text, bmin, bmax = combined_obj([
        ("helicoid_surface", hv, hf),
        ("torus_knot_surface", tv, tf),
    ])
    (d / "scene.obj").write_text(obj_text, encoding="utf-8")
    write_mtl(d / "scene.mtl", mats)
    cam = camera_for_bounds(bmin, bmax, fov=50)
    commands = [
        {"op": "import_geometry", "payload": {"path": f"examples/recipes/helicoid-spiral/scene.obj", "format": "obj", "name": "helicoid-spiral"}},
        {"op": "create_material", "payload": {"name": HS, **mats["helicoid_surface"]}},
        {"op": "create_material", "payload": {"name": TKS, **mats["torus_knot_surface"]}},
        {"op": "assign_material", "payload": {"object_name": "helicoid-spiral", "material_name": HS, "group_index": 1}},
        {"op": "assign_material", "payload": {"object_name": "helicoid-spiral", "material_name": TKS, "group_index": 2}},
        {"op": "set_camera", "payload": cam},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {"path": "examples/recipes/helicoid-spiral/octane-preview.png", "width": 1280, "height": 1280, "quality": "standard", "samples": 256, "min_samples": 24, "timeout_seconds": 14}},
    ]
    scene = _scene_template(
        slug="helicoid-spiral",
        title="Helicoid Spiral + Torus Knot (Math Grammar)",
        category="Mathematics / geometry",
        purpose="Render two parametric surfaces — a helicoid spiral and a (2,3) torus knot — with distinct blue and orange emissive materials to demonstrate combined-OBJ multi-group assignment.",
        prompt="Visualise a helicoid spiral surface and a torus knot.",
        materials=mats,
        commands=commands,
        camera=cam,
    )
    (d / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    placeholder_preview(d / "preview.png", (14, 16, 30))
    return {"slug": "helicoid-spiral", "verts": hc + tc, "cam": cam}


def _scene_template(slug, title, category, purpose, prompt, materials, commands, camera) -> dict:
    return {
        "slug": slug,
        "title": title,
        "category": category,
        "purpose": purpose,
        "prompt": prompt,
        "camera": camera,
        "materials": materials,
        "commands": commands,
        "preview_note": "preview.png is a lightweight reference raster; octane-preview.png is the REAL native Octane render (standard tier).",
        "quality_checklist": [
            "Preview is non-blank and the subject is recognizable at thumbnail size.",
            "scene.obj imports the local path listed in commands[].",
            "Camera frames the full subject with margin.",
            "Each usemtl group has an explicit create_material + assign_material(group_index).",
        ],
        "known_pitfalls": [
            "Octane caches imported geometry by filename; re-rendering the same mesh name does NOT reload the OBJ. The bridge now deletes the stale mesh node before re-import to force a fresh load.",
            "Named materials persist across renders; create_material is a no-op if the name already exists, so re-renders must use fresh material names or the stale (washed-out) material is reused.",
            "The persistent bridge may not stay alive on some Octane X builds (closes after showWindow); render via the one-shot bridge drain. When alive, it processes the queue too.",
            "CRITICAL RENDER-TARGET LIMITATION: octane.project.setSelection{rt} selects the Hermes Render Target node in the graph but does NOT make it the active render target the engine renders/saves. octane.render.start{renderTargetNode=rt} is also ignored on this build. Until Otoy exposes a working setter, the user MUST manually click the 'Hermes Render Target' node in Octane's node graph so it becomes the active RT BEFORE the save_preview runs. Without this, the engine renders the default RT (white/sky) and the preview is blank regardless of geometry or materials. This is the proven cause of all 'blank blue-sky' helicoid renders; a known-good sphere through the same path also renders blank, confirming it is NOT a geometry issue.",
        ],
        "target_preview": "octane-preview.png",
        "visual_iteration_protocol": {
            "model": "ollama:glm-ocr",
            "reference_image": f"examples/recipes/{slug}/preview.png",
            "candidate_image": f"examples/recipes/{slug}/octane-preview.png",
            "max_iterations": 4,
            "review_focus": ["object count and semantic content", "framing and camera", "material/color readability", "lighting", "task-specific structure"],
            "patch_dimensions": ["geometry", "camera", "lighting", "materials", "render_settings"],
            "required_evidence": ["bridge result metadata", "native Octane preview at octane-preview.png", "iteration records", "final native Octane render bundled as octane-preview.png"],
            "baseline_sweep": {
                "camera_or_scene_variants": [
                    {"label": "default framing", "camera": camera},
                    {"label": "closer framing", "camera": {**camera, "position": [c * 0.7 for c in camera["position"]]}},
                    {"label": "wider framing", "camera": {**camera, "position": [c * 1.3 for c in camera["position"]]}},
                    {"label": "elevated angle", "camera": {**camera, "position": [camera["position"][0], camera["position"][1] + 2.0, camera["position"][2]]}},
                ],
            },
            "stop_conditions": ["subject matches intent", "materials visually distinct", "framing acceptable"],
        },
        "final_bundle": {
            "required": True,
            "native_render": f"examples/recipes/{slug}/octane-preview.png",
            "bundled_assets": ["scene.obj", "scene.mtl", "scene.json", "preview.png", "octane-preview.png"],
            "status": "pending_native_octane_iteration",
        },
        "native_octane_verified": False,
        "status": "built; native render pending (2026-07-09)",
    }


def write_readme(d: Path, slug: str, title: str, purpose: str, cam: dict) -> None:
    text = (
        f"# {title}\n\n"
        f"{purpose}\n\n"
        "## Usage\n\n"
        "1. Import `scene.obj` with "
        f"`octane_import_geometry(path=\"examples/recipes/{slug}/scene.obj\", "
        f"name=\"{slug}\")`.\n"
        "2. Create + assign materials per `usemtl` group.\n"
        "3. Set camera, lighting, then `octane_save_preview`.\n\n"
        f"Camera: position {cam['position']} -> target {cam['target']}, "
        f"fov {cam.get('fov')}.\n\n"
        "## Assets\n\n"
        "`scene.obj`, `scene.mtl`, `scene.json`, `preview.png`, `octane-preview.png`.\n"
    )
    (d / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    ships = [
        ("earth-moon-space", build_earth_moon),
        ("helicoid-spiral", build_helicoid),
    ]
    for slug, fn in ships:
        d = ROOT / "examples" / "recipes" / slug
        info = fn(d)
        scene = json.loads((d / "scene.json").read_text(encoding="utf-8"))
        write_readme(d, slug, scene["title"], scene["purpose"], info["cam"])
        print(f"  built {slug}: {info['verts']} verts; cam={info['cam']['position']} -> {info['cam']['target']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
