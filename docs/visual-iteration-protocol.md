# Visual iteration protocol

OctaneX MCP should treat rendering as an iterative visual-control loop, not a one-shot asset export. A generated OBJ can be a useful first approximation, but photoreal targets often need repeated native Octane renders, cheap local visual critique, and scene patches before the model matches the reference content, lighting, and perspective.

## Core loop

1. **Reference** — keep the target image/path in recipe metadata, e.g. `photoreal-preview.png`.
2. **Generate candidate** — build or patch `scene.obj`, `scene.mtl`, `scene.json`, material intent, camera, and lighting.
3. **Queue native render** — use `octane_queue_recipe(...)` or scene tools, then drain through the one-shot or persistent bridge.
4. **Capture evidence** — save Octane output as `octane-preview.png`; do not claim native success from repo previews alone.
5. **Baseline sweep** — before fine matching, render a small set of camera/scene orientations so the agent can establish a rapid visual baseline. Start with front, left three-quarter, right three-quarter, and top-oblique variants; extend the same sweep idea to focal length, camera distance, lighting direction, and material/readability contrast when those are uncertain.
6. **Cheap visual review** — run local `glm-ocr` via Ollama against the reference and candidate preview to extract visible content/layout/material/lighting notes.
7. **Patch** — apply one bounded change set: geometry proportions/counts, object placement, camera position/FOV, lighting/exposure, material intent, or texture proxies.
8. **Repeat** — keep iteration records until the review no longer finds material mismatches or the remaining gaps are known renderer/schema limitations.
9. **Bundle final evidence** — the final iterated native Octane render, result metadata, iteration notes, and all reproduction assets must live inside the recipe directory.

## Local vision model

Preferred cheap local reviewer:

```bash
ollama run glm-ocr 'Please output JSON only: {"visible_objects":"","materials":"","lighting":"","camera_perspective":"","mismatch_risks":""}' path/to/image.png
```

GLM-OCR's documentation frames the model primarily as OCR/document parsing plus schema-constrained information extraction. For render review, use the information-extraction mode: ask for a tiny JSON schema instead of open-ended critique. Review both images with the same schema prompt, then ask the agent to produce a patch plan from the two extracted descriptions. `glm-ocr` is not a perfect critic, but it is cheap enough to run every iteration and good enough to catch broad composition, object-count, material, and lighting drift.

## Patch categories

Each iteration should output structured patch intent:

```json
{
  "iteration": 2,
  "reference": "examples/recipes/.../photoreal-preview.png",
  "candidate": "examples/recipes/.../octane-preview.png",
  "model": "ollama:glm-ocr",
  "observed_gaps": [
    "candidate has only four vases; reference has five",
    "camera is too high and too far left",
    "glass material imports too opaque"
  ],
  "patch_plan": {
    "geometry": ["add or widen missing vase silhouette"],
    "camera": {"move": "right", "lower": true, "fov": 34},
    "lighting": ["increase left softbox reflection"],
    "materials": ["increase glass transmission / lower roughness"]
  }
}
```

## Recipe metadata fields

Recipes that are trying to match a target/reference should include:

- `target_preview` — repo path to target/reference image.
- `native_octane_verified` — `false` until an inspected native `octane-preview.png` exists.
- `visual_iteration_protocol` — model, candidate path, max iterations, review focus, and patch dimensions.
- `final_bundle` — final native render path, iteration log paths, result metadata path/pattern, and required assets to check in with the recipe.
- `known_pitfalls` — explicit renderer/schema limitations that may block perfect matching.

## Final recipe bundle contract

Once a target-matching recipe has been iterated in Octane, the recipe directory should contain the complete final bundle:

```text
examples/recipes/<slug>/
├── scene.json                 recipe metadata and final protocol state
├── scene.obj                  final or current best candidate geometry
├── scene.mtl                  material hints
├── photoreal-preview.png      reference/target image
├── octane-preview.png         final native Octane render
├── iterations/
│   ├── iteration-001.json     review + patch plan
│   ├── iteration-001.png      native candidate render, if useful
│   └── final-review.json      final glm-ocr/native review summary
└── assets/                    texture maps, HDRIs, masks, normals, refs
```

If `octane-preview.png` is missing, `native_octane_verified` must stay `false` and the recipe must say what action is required to produce it.

## Stop conditions

Stop iterating when:

- native candidate has the same object count and broad composition as the reference;
- material classes are distinguishable in the Octane output;
- camera perspective and framing are close enough for the task;
- remaining mismatches require bridge schema work rather than scene-patch work;
- or the configured iteration budget is exhausted.

## Current limitation

The bridge can queue imports/camera/lighting/render commands, but it does not yet expose rich native material controls for transmission, IOR, clearcoat, anisotropy, texture maps, or procedural glazes. Until those payloads exist, the loop should record those gaps honestly instead of overfitting OBJ geometry.
