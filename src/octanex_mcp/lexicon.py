"""WP10 — lexical intent graph: words -> Octane scene assets.

A small, typed lexicon that maps natural-language fragments onto the exact
scene-spec contract the OctaneX bridge consumes (``materials`` + 1-based
``assignments``, per ``benchmarks/spec.py``). It is the *word -> asset*
compiler discussed in the language-graph brainstorm:

  * **nouns**      -> mesh primitive + material intent
  * **adjectives** -> material / size / emission param overrides
  * **color words**-> sRGB target (resolved from language, NOT from a photo)
  * **verbs**      -> animation / camera-motion specs (WP8)
  * **connectors** -> relative placement ("on", "with", "next to")

Why this exists (grounded in prior failures, not speculation):

  * **Material-binding trap (A).** The Lua bridge ignores OBJ ``usemtl``/MTL
    color; materials only reach the mesh via explicit ``create_material`` +
    ``assign_material``. ``scripts/fix_recipe_materials.py`` patches that gap
    *after the fact*. The lexicon emits the binding **by construction**, so a
    word-resolved scene can never render as default white/grey.
  * **Photo-hue drift (B).** ``iteration.build_candidate_scene`` derives a
    material color from *whole-frame* k-means on a reference image — the
    ``red-sphere`` corpus entry resolved to **blue (218 deg)** because the
    background dominated. The lexicon resolves "red" -> red from the lexicon,
    independent of any reference pixels.
  * **Self-verifying acceptance.** Because colors come from words, the
    resolved scene emits ``color_family`` acceptance criteria derived from its
    *own* material colors (``evaluate_acceptance`` consumes them with no vision
    model). A render that drifts off the requested hue fails its own gate.

Library layering: imports ONLY ``octanex_mcp.visuals`` + ``octanex_mcp.acceptance``
(no ``benchmarks`` import), so it boots inside the console-script server.

Offline + deterministic: no embeddings, no network, no LLM. Unknown *nouns*
raise ``LexiconError`` (explicit, never a silent default-white subject);
unrecognized adjectives/colors are tolerated and recorded in ``unresolved``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from octanex_mcp.acceptance import _hue_to_rgb
from octanex_mcp.visuals import ObjBuilder, bounds_from_points, camera_for_bounds

# ---------------------------------------------------------------------------
# Bridge material kinds (the only 4 the Lua create_material handler supports;
# mirrors scripts/fix_recipe_materials.normalize_kind).
# ---------------------------------------------------------------------------

_KIND_ALIASES = (
    ("glass", "specular"), ("specular", "specular"), ("transparent", "specular"),
    ("metal", "metallic"), ("metallic", "metallic"), ("brushed", "metallic"),
    ("chrome", "metallic"), ("steel", "metallic"),
    ("glossy", "glossy"), ("ceramic", "glossy"), ("porcelain", "glossy"),
    ("pearl", "glossy"), ("silk", "glossy"), ("plastic", "glossy"),
)


def normalize_kind(kind: str | None) -> str:
    """Map a verbose material 'kind' string onto one of the 4 bridge kinds."""
    if not kind:
        return "diffuse"
    k = kind.lower()
    for token, mapped in _KIND_ALIASES:
        if token in k:
            return mapped
    return "diffuse"


# ---------------------------------------------------------------------------
# Color words -> sRGB 0..1 triple or hue (deg). Achromatic entries are explicit
# RGB; chromatic entries are hues (resolved via _hue_to_rgb so saturation/value
# are irrelevant to acceptance, which converts back to hue internally).
# ---------------------------------------------------------------------------

COLOR_WORDS: dict[str, Any] = {
    "red": 0.0, "orange": 30.0, "yellow": 60.0, "green": 120.0,
    "cyan": 180.0, "blue": 240.0, "violet": 270.0, "purple": 280.0,
    "magenta": 300.0, "pink": 330.0, "brown": [0.40, 0.25, 0.12],
    "white": [0.92, 0.92, 0.94], "black": [0.04, 0.04, 0.05],
    "grey": [0.50, 0.50, 0.52], "gray": [0.50, 0.50, 0.52],
}


def _color_to_rgb(entry: Any) -> list[float]:
    if isinstance(entry, (list, tuple)):
        return [round(float(c), 4) for c in entry[:3]]
    return _hue_to_rgb(float(entry))


# ---------------------------------------------------------------------------
# Noun -> mesh primitive + default material intent.
#   shape: one of box / ellipsoid / cylinder / cone
#   params: geometry kwargs passed to ObjBuilder
#   half: bbox half-extents [hx, hy, hz] used for relative placement
#   material: default {"kind", "color", "roughness", **extra}
# ---------------------------------------------------------------------------

NOUN_MESH: dict[str, dict[str, Any]] = {
    "cube": {"shape": "box", "params": {"size": (1.6, 1.6, 1.6)}, "half": [0.8, 0.8, 0.8],
             "material": {"kind": "glossy", "color": [0.6, 0.6, 0.65], "roughness": 0.25}},
    "box": {"shape": "box", "params": {"size": (1.6, 1.6, 1.6)}, "half": [0.8, 0.8, 0.8],
            "material": {"kind": "glossy", "color": [0.6, 0.6, 0.65], "roughness": 0.25}},
    "sphere": {"shape": "ellipsoid", "params": {"radii": (1.1, 1.1, 1.1)}, "half": [1.1, 1.1, 1.1],
               "material": {"kind": "glossy", "color": [0.6, 0.6, 0.65], "roughness": 0.2}},
    "ball": {"shape": "ellipsoid", "params": {"radii": (1.1, 1.1, 1.1)}, "half": [1.1, 1.1, 1.1],
             "material": {"kind": "glossy", "color": [0.6, 0.6, 0.65], "roughness": 0.2}},
    "planet": {"shape": "ellipsoid", "params": {"radii": (1.3, 1.3, 1.3)}, "half": [1.3, 1.3, 1.3],
               "material": {"kind": "glossy", "color": [0.35, 0.55, 0.85], "roughness": 0.35}},
    "moon": {"shape": "ellipsoid", "params": {"radii": (1.0, 1.0, 1.0)}, "half": [1.0, 1.0, 1.0],
             "material": {"kind": "diffuse", "color": [0.82, 0.82, 0.80], "roughness": 0.9}},
    "star": {"shape": "ellipsoid", "params": {"radii": (1.0, 1.0, 1.0)}, "half": [1.0, 1.0, 1.0],
             "material": {"kind": "glossy", "color": [1.0, 0.85, 0.4], "roughness": 0.3, "emission": 6.0}},
    "cylinder": {"shape": "cylinder", "params": {"radius": 0.9, "height": 1.8}, "half": [0.9, 0.9, 0.9],
                 "material": {"kind": "glossy", "color": [0.6, 0.6, 0.65], "roughness": 0.25}},
    "tube": {"shape": "cylinder", "params": {"radius": 0.9, "height": 1.8}, "half": [0.9, 0.9, 0.9],
             "material": {"kind": "glossy", "color": [0.6, 0.6, 0.65], "roughness": 0.25}},
    "cone": {"shape": "cone", "params": {"radius": 1.0, "height": 2.0}, "half": [1.0, 1.0, 1.0],
             "material": {"kind": "glossy", "color": [0.6, 0.6, 0.65], "roughness": 0.25}},
    "mountain": {"shape": "cone", "params": {"radius": 1.4, "height": 2.6}, "half": [1.4, 1.3, 1.4],
                 "material": {"kind": "diffuse", "color": [0.45, 0.40, 0.36], "roughness": 0.95}},
    "vase": {"shape": "cylinder", "params": {"radius": 0.85, "height": 1.9}, "half": [0.85, 0.95, 0.85],
             "material": {"kind": "glossy", "color": [0.75, 0.20, 0.18], "roughness": 0.1, "clearcoat": 1.0}},
    "pedestal": {"shape": "box", "params": {"size": (2.2, 0.5, 2.2)}, "half": [1.1, 0.25, 1.1],
                 "material": {"kind": "diffuse", "color": [0.80, 0.80, 0.82], "roughness": 0.9}},
    "plinth": {"shape": "box", "params": {"size": (2.2, 0.5, 2.2)}, "half": [1.1, 0.25, 1.1],
               "material": {"kind": "diffuse", "color": [0.80, 0.80, 0.82], "roughness": 0.9}},
    "stand": {"shape": "box", "params": {"size": (2.2, 0.5, 2.2)}, "half": [1.1, 0.25, 1.1],
              "material": {"kind": "diffuse", "color": [0.80, 0.80, 0.82], "roughness": 0.9}},
    "tower": {"shape": "box", "params": {"size": (1.0, 2.6, 1.0)}, "half": [0.5, 1.3, 0.5],
              "material": {"kind": "glossy", "color": [0.55, 0.60, 0.68], "roughness": 0.3}},
    "dome": {"shape": "ellipsoid", "params": {"radii": (1.4, 0.9, 1.4)}, "half": [1.4, 0.9, 1.4],
             "material": {"kind": "glossy", "color": [0.85, 0.82, 0.78], "roughness": 0.2}},
    "gem": {"shape": "ellipsoid", "params": {"radii": (0.9, 1.2, 0.9)}, "half": [0.9, 1.2, 0.9],
            "material": {"kind": "specular", "color": [0.3, 0.8, 0.9], "roughness": 0.02, "transmission": 0.7, "ior": 1.5}},
    "coin": {"shape": "cylinder", "params": {"radius": 0.9, "height": 0.18}, "half": [0.9, 0.09, 0.9],
             "material": {"kind": "metallic", "color": [0.72, 0.45, 0.20], "roughness": 0.25, "metallic": 1.0}},
}

# Material-word overrides keyed by noun/adj ('gold', 'glass', 'ceramic', ...).
MATERIAL_WORDS: dict[str, dict[str, Any]] = {
    "gold": {"kind": "metallic", "color": [1.0, 0.67, 0.18], "roughness": 0.18, "metallic": 1.0},
    "silver": {"kind": "metallic", "color": [0.88, 0.90, 0.93], "roughness": 0.15, "metallic": 1.0},
    "copper": {"kind": "metallic", "color": [0.72, 0.45, 0.20], "roughness": 0.28, "metallic": 1.0},
    "brass": {"kind": "metallic", "color": [0.80, 0.62, 0.24], "roughness": 0.30, "metallic": 1.0},
    "chrome": {"kind": "metallic", "color": [0.90, 0.90, 0.95], "roughness": 0.05, "metallic": 1.0},
    "steel": {"kind": "metallic", "color": [0.70, 0.72, 0.76], "roughness": 0.25, "metallic": 1.0},
    "iron": {"kind": "metallic", "color": [0.36, 0.36, 0.40], "roughness": 0.45, "metallic": 1.0},
    "glass": {"kind": "specular", "color": [0.80, 0.90, 1.0], "roughness": 0.02, "transmission": 1.0, "ior": 1.5, "opacity": 0.4},
    "crystal": {"kind": "specular", "color": [0.75, 0.95, 1.0], "roughness": 0.02, "transmission": 0.9, "ior": 1.5},
    "ceramic": {"kind": "glossy", "color": [0.85, 0.85, 0.88], "roughness": 0.1, "clearcoat": 1.0},
    "porcelain": {"kind": "glossy", "color": [0.90, 0.86, 0.78], "roughness": 0.16, "clearcoat": 0.85},
    "clay": {"kind": "diffuse", "color": [0.74, 0.30, 0.14], "roughness": 0.72},
    "terracotta": {"kind": "diffuse", "color": [0.74, 0.30, 0.14], "roughness": 0.72},
    "wood": {"kind": "diffuse", "color": [0.45, 0.30, 0.16], "roughness": 0.6},
    "stone": {"kind": "diffuse", "color": [0.62, 0.62, 0.60], "roughness": 0.9},
    "marble": {"kind": "glossy", "color": [0.90, 0.88, 0.85], "roughness": 0.2},
    "metal": {"kind": "metallic", "color": [0.75, 0.76, 0.80], "roughness": 0.25, "metallic": 1.0},
    "plastic": {"kind": "glossy", "color": [0.70, 0.70, 0.75], "roughness": 0.35},
    "rubber": {"kind": "diffuse", "color": [0.20, 0.20, 0.22], "roughness": 0.85},
}

# Adjective -> param override (applied after noun + material-word resolution).
ADJECTIVE_OVERRIDES: dict[str, dict[str, Any]] = {
    "small": {"scale": 0.6}, "tiny": {"scale": 0.4}, "little": {"scale": 0.6},
    "large": {"scale": 1.6}, "big": {"scale": 1.6}, "huge": {"scale": 2.2}, "giant": {"scale": 2.4},
    "shiny": {"roughness": 0.05}, "glossy": {"roughness": 0.08}, "smooth": {"roughness": 0.2},
    "rough": {"roughness": 0.7}, "matte": {"roughness": 0.9}, "dull": {"roughness": 0.9},
    "glowing": {"emission": 6.0}, "emissive": {"emission": 6.0}, "luminous": {"emission": 5.0},
    "transparent": {"transmission": 0.9, "opacity": 0.3, "kind": "specular"},
    "clear": {"transmission": 0.85, "opacity": 0.35, "kind": "specular"},
    "dark": {"tint": 0.4}, "bright": {"tint": 1.25}, "light": {"tint": 1.3},
}

# Verb -> motion spec (payloads compatible with octane_animate_objects /
# octane_build_animation). refs are "#N" where N = the group_index (1-based).
VERB_MOTION: dict[str, dict[str, Any]] = {
    "spinning": {"type": "object_rotate", "motion": "rotate", "axis": "y", "degrees": 360, "easing": "linear"},
    "spin": {"type": "object_rotate", "motion": "rotate", "axis": "y", "degrees": 360, "easing": "linear"},
    "rotating": {"type": "object_rotate", "motion": "rotate", "axis": "y", "degrees": 360, "easing": "linear"},
    "turning": {"type": "object_rotate", "motion": "rotate", "axis": "y", "degrees": 90},
    "swaying": {"type": "object_rotate", "motion": "rotate", "axis": "z", "degrees": 18, "easing": "ease_in_out_quad"},
    "wobbling": {"type": "object_rotate", "motion": "rotate", "axis": "z", "degrees": 10, "easing": "ease_in_out_quad"},
    "rising": {"type": "object_translate", "motion": "translate", "offset": [0, 1.0, 0], "easing": "ease_in_out_quad"},
    "floating": {"type": "object_translate", "motion": "translate", "offset": [0, 0.6, 0], "easing": "ease_in_out_quad"},
    "pulsing": {"type": "object_scale", "motion": "scale", "scale": [1.12, 1.12, 1.12], "easing": "ease_in_out_quad"},
    "orbiting": {"type": "camera_orbit", "center": [0, 0, 0], "radius": 8, "duration": 6, "fov": 45},
    "orbit": {"type": "camera_orbit", "center": [0, 0, 0], "radius": 8, "duration": 6, "fov": 45},
}

# Connectors that split a prompt into composed object phrases.
_CONNECTOR_RE = re.compile(r"\b(with|on top of|on|upon|next to|beside|nextto|and|\+)\b", re.IGNORECASE)
_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "at", "by", "for", "is", "are", "make",
    "render", "create", "show", "draw", "me", "please", "some", "its", "their",
    "that", "this", "top", "up", "down", "left", "right", "front", "behind",
}


class LexiconError(ValueError):
    """Raised when a phrase has no resolvable noun (no silent white subject)."""


class MergedObj:
    """Local merged-OBJ builder (no benchmarks import; respects layering).

    The Octane bridge connects one mesh per render target, so multi-object
    scenes must merge geometry and assign materials per group. Face indices are
    corrected relative to the *total emitted vertex count* so the harness index
    guard (``_validate_obj_indices``: max face idx <= vertex count) always
    passes. ``bounds()`` returns the union of all group points in the
    ``{min, max, center, radius}`` dict the camera helper consumes.
    """

    def __init__(self, mesh_name: str) -> None:
        self.mesh_name = mesh_name
        self._v_lines: list[str] = []
        self._groups: list[tuple[str, str, list[str]]] = []
        self._global_v = 0
        self._points: list[tuple[float, float, float]] = []

    def add_group(self, group_name: str, material: str, builder: ObjBuilder) -> None:
        v_lines: list[str] = []
        f_lines: list[str] = []
        for line in builder.lines:
            if line.startswith("v "):
                v_lines.append(line)
                parts = line.split()
                self._points.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("f "):
                tokens = line.split()
                new_indices = " ".join(
                    str(int(t) + self._global_v) for t in tokens[1:])
                f_lines.append("f " + new_indices)
        self._groups.append((group_name, material, f_lines))
        self._v_lines.extend(v_lines)
        self._global_v += builder.vertex_count

    def text(self) -> str:
        header = f"# combined mesh {self.mesh_name}"
        lines = [header, "o " + self.mesh_name]
        for group, material, f_lines in self._groups:
            lines.append(f"g {group}")
            lines.append(f"usemtl {material}")
            lines.extend(f_lines)
        return header + "\n" + "\n".join(self._v_lines) + "\n" + "\n".join(lines[1:]) + "\n"

    def bounds(self) -> dict[str, Any]:
        return bounds_from_points(self._points)


@dataclass
class _Phrase:
    raw: str
    words: list[str]
    noun: str | None = None
    material_word: str | None = None
    color: Any | None = None
    adjectives: list[str] = field(default_factory=list)
    connector: str | None = None  # how this phrase attaches to the previous one


def _split_phrases(prompt: str) -> list[_Phrase]:
    """Split a prompt into composed object phrases on known connectors.

    ``re.split`` with a capturing group returns [text, connector, text, ...],
    so odd indices are the connectors joining phrase[i] to phrase[i+1].
    """
    segs = _CONNECTOR_RE.split(prompt)
    phrases: list[_Phrase] = []
    pending_connector: str | None = None
    for i, seg in enumerate(segs):
        seg = seg.strip().strip(",").strip()
        if not seg:
            continue
        if i % 2 == 1:  # connector token between phrases
            pending_connector = seg.lower()
            continue
        phrases.append(_Phrase(raw=seg, words=_tokenize(seg), connector=pending_connector))
        pending_connector = None
    if not phrases:
        phrases.append(_Phrase(raw=prompt, words=_tokenize(prompt)))
    return phrases


def _tokenize(text: str) -> list[str]:
    return [w for w in re.split(r"[\s,]+", text.lower()) if w]


def _resolve_phrase(p: _Phrase) -> dict[str, Any]:
    """Resolve one phrase into a mesh spec + material overrides.

    Returns {"noun", "shape", "params", "half", "material", "color_override",
    "adj", "unresolved"} or raises LexiconError if no noun is found.
    """
    nouns = [w for w in p.words if w in NOUN_MESH]
    mat_words = [w for w in p.words if w in MATERIAL_WORDS]
    color_words = [w for w in p.words if w in COLOR_WORDS]
    adjs = [w for w in p.words
            if w in ADJECTIVE_OVERRIDES and w not in COLOR_WORDS]
    # Noun resolution: prefer an explicit noun; else a material-word that also
    # has a mesh sense (e.g. "glass sphere").
    noun = nouns[0] if nouns else None
    if noun is None and mat_words:
        # e.g. "a gold" with no shape -> treat as sphere proxy.
        noun = "sphere"
    if noun is None:
        raise LexiconError(f"no resolvable noun in phrase {p.raw!r}; known nouns: {sorted(NOUN_MESH)}")

    spec = dict(NOUN_MESH[noun])
    material = dict(spec["material"])

    # Material-word override (e.g. "gold", "glass").
    if mat_words:
        mw = mat_words[0]
        material.update({k: v for k, v in MATERIAL_WORDS[mw].items()})
        p.material_word = mw

    # Color-word override (resolves from language, not pixels).
    if color_words:
        p.color = COLOR_WORDS[color_words[0]]

    # Adjective overrides.
    scale = 1.0
    tint = 1.0
    for adj in adjs:
        ov = ADJECTIVE_OVERRIDES[adj]
        if "scale" in ov:
            scale *= ov["scale"]
        if "tint" in ov:
            tint *= ov["tint"]
        for k, v in ov.items():
            if k in ("scale", "tint"):
                continue
            material[k] = v
        p.adjectives.append(adj)

    # Apply scale to geometry half-extents + params.
    if scale != 1.0:
        spec["half"] = [h * scale for h in spec["half"]]
        if spec["shape"] == "box":
            sz = spec["params"]["size"]
            spec["params"] = {"size": tuple(s * scale for s in sz)}
        elif spec["shape"] == "ellipsoid":
            r = spec["params"]["radii"]
            spec["params"] = {"radii": tuple(r * scale for r in r)}
        elif spec["shape"] == "cylinder":
            spec["params"] = {"radius": spec["params"]["radius"] * scale,
                              "height": spec["params"]["height"] * scale}
        elif spec["shape"] == "cone":
            spec["params"] = {"radius": spec["params"]["radius"] * scale,
                              "height": spec["params"]["height"] * scale}

    # Apply color override (word beats noun default; tint scales it).
    if p.color is not None:
        rgb = _color_to_rgb(p.color)
        material["color"] = [min(1.0, c * tint) for c in rgb]
    elif tint != 1.0:
        material["color"] = [min(1.0, c * tint) for c in material["color"]]

    # Bridge kind normalization (verbose -> 4 supported kinds).
    material["kind"] = normalize_kind(material.get("kind"))

    # Unresolved content words (for explicit reporting / strict mode).
    # Verbs are recognized too: a handled verb (e.g. "spinning") must not be
    # reported as unresolved just because it isn't a noun/color/adjective.
    recognized = (set(nouns) | set(mat_words) | set(color_words)
                  | set(adjs) | set(VERB_MOTION) | _STOPWORDS)
    unresolved = [w for w in p.words if w not in recognized]

    return {"noun": noun, "shape": spec["shape"], "params": spec["params"],
            "half": spec["half"], "material": material, "unresolved": unresolved}


def _add_shape(b: ObjBuilder, shape: str, params: dict[str, Any],
               center: tuple[float, float, float], mat_name: str) -> None:
    if shape == "box":
        b.add_box(center=center, size=params["size"], material=mat_name)
    elif shape == "ellipsoid":
        b.add_ellipsoid(center=center, radii=params["radii"], material=mat_name)
    elif shape == "cylinder":
        b.add_cylinder(center=center, radius=params["radius"], height=params["height"], material=mat_name)
    elif shape == "cone":
        b.add_cone(center=center, radius=params["radius"], height=params["height"], material=mat_name)


def resolve(prompt: str, *, strict: bool = False,
            warm_start: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compile a natural-language prompt into a harness scene_spec.

    Returns a dict matching ``benchmarks/spec.py``'s ``build()`` contract, plus:
      * ``motion``        — list of animation/camera specs (WP8)
      * ``unresolved``    — recognized-but-unmapped words across all phrases
      * ``phrases``       — resolved phrase summaries (for debugging / #N badges)

    In ``strict`` mode, ANY unresolved content word raises ``LexiconError``.
    Otherwise unresolved adjectives/colors are tolerated and reported.

    ``warm_start`` (optional dict from ``corpus.find_grammar``) is accepted for
    API symmetry: if the lexicon produces no camera/lighting cues of its own,
    the warm-start entry's provenance is recorded (the word-resolved spec always
    wins over photo-derived values).
    """
    phrases = _split_phrases(prompt)
    resolved: list[dict[str, Any]] = []
    all_unresolved: list[str] = []
    for p in phrases:
        r = _resolve_phrase(p)
        r["connector"] = p.connector
        resolved.append(r)
        all_unresolved.extend(r["unresolved"])

    if strict and all_unresolved:
        raise LexiconError(f"unresolved words: {sorted(set(all_unresolved))}")

    # ---- relative placement (C) -------------------------------------------
    obj = MergedObj("lexicon_scene")
    materials: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    phrases_out: list[dict[str, Any]] = []

    # Place objects before emitting geometry. The connector belongs to the
    # current phrase, so "cube on pedestal" means the *previous* object/stack is
    # lifted onto the current base, not that the pedestal is placed atop the cube.
    centers: list[tuple[float, float, float]] = []
    cursor_x = 0.0
    half_extents: list[list[float]] = []
    for group_index, r in enumerate(resolved):
        hx, hy, hz = r["half"]
        if group_index == 0:
            center = (0.0, 0.0, 0.0)
        elif (r["connector"] or "").startswith("on") or r["connector"] == "upon":
            current_min_y = min(c[1] - half_extents[i][1] for i, c in enumerate(centers))
            lift = hy - current_min_y
            centers = [(c[0], c[1] + lift, c[2]) for c in centers]
            center = (0.0, 0.0, 0.0)
        else:  # "with" / "next to" / "and" / default -> side by side
            center = (cursor_x + hx, 0.0, 0.0)
            cursor_x += hx
        centers.append(center)
        half_extents.append([hx, hy, hz])
        cursor_x = max(cursor_x, center[0] + hx)

    group_index = 0
    for r, center in zip(resolved, centers):
        hx, hy, hz = r["half"]
        mat_name = f"mat_{r['noun']}_{group_index + 1}"
        b = ObjBuilder(f"obj{group_index + 1}")
        _add_shape(b, r["shape"], r["params"], center, mat_name)
        obj.add_group(f"obj{group_index + 1}", mat_name, b)

        m = dict(r["material"])
        m["name"] = mat_name
        materials.append(m)
        assignments.append({"group_index": group_index + 1, "material_name": mat_name})

        group_index += 1

        phrases_out.append({
            "group_index": group_index, "noun": r["noun"],
            "material_name": mat_name, "color": m["color"], "kind": m["kind"],
            "connector": r["connector"], "center": [round(v, 6) for v in center],
            "unresolved": r["unresolved"],
        })

    bounds = obj.bounds()
    lighting = "soft_studio"
    if any(w in prompt.lower() for w in ("bright", "daylight", "sunlit")):
        lighting = "bright_studio"

    # ---- self-verifying acceptance (B): derived from resolved colors -------
    acceptance: list[dict[str, Any]] = [
        {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
        {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
    ]
    for m in materials:
        c = m.get("color")
        if c and any(v > 0.02 for v in c):
            acceptance.append({
                "kind": "color_family", "target": [round(v, 4) for v in c],
                "hue_tol": 45, "min_fraction": 0.005,
            })

    # ---- motion verbs (D) -------------------------------------------------
    motion: list[dict[str, Any]] = []
    for w in _tokenize(prompt):
        if w in VERB_MOTION:
            spec = dict(VERB_MOTION[w])
            if spec["type"] in ("object_rotate", "object_translate", "object_scale"):
                spec["refs"] = "#1"  # default to the first (primary) object
            motion.append(spec)

    scene_spec: dict[str, Any] = {
        "mesh_name": "lexicon_scene",
        "obj": obj.text(),
        "bounds": bounds,
        "materials": materials,
        "assignments": assignments,
        "camera": camera_for_bounds(bounds, view="iso", margin=1.4),
        "lighting": lighting,
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": acceptance,
        # lexicon-only extensions:
        "motion": motion,
        "unresolved": sorted(set(all_unresolved)),
        "phrases": phrases_out,
        "warm_start": warm_start,
    }
    return scene_spec
