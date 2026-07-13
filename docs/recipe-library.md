# Example Recipe Library

This library gives agents copyable scenes, preview renders, and operational recipes for exploring OctaneX MCP applications. Each recipe includes:

- `scene.obj` reusable geometry;
- `scene.mtl` material hints for OBJ import;
- `scene.json` MCP command/camera metadata;
- `preview.png` or `photoreal-preview.png` generated preview/target render for quick review;
- `README.md` with prompts, steps, variations, and quality checklist.

The previews are intentionally small, deterministic repo-generated renders so they can be reviewed on GitHub and reused without launching Octane. For final quality, run the listed command sequence through the Octane Lua bridge and save an Octane preview next to the sample.

Photoreal target examples may include an external target/reference image. These are visual quality bars, not claims of native Octane success until an `octane-preview.png` is saved and inspected.

Animated products are also possible by generating frame-by-frame scene states. See [`examples/animations/orbit-reveal/`](../examples/animations/orbit-reveal/README.md) for a checked-in GIF/MP4 example with PNG frames and OBJ frame states.

| Recipe | Application area | Slug | Why it matters |
| --- | --- | --- | --- |
| [3D KPI Bar Chart](../examples/recipes/data-bars/README.md) | Data visualization | `data-bars` | Compare a short numeric sequence as spatial bars with a clear baseline and highlight bars above threshold. |
| [Radial Math Surface](../examples/recipes/math-surface/README.md) | Mathematics | `math-surface` | Render a height field for z = sin(r*2.2)/max(r, 0.45) to explain radial damping and singularity protection. |
| [Rotating Vector Field](../examples/recipes/vector-field/README.md) | Math/physics | `vector-field` | Show a 2D rotational vector field lifted into 3D with arrow tips to explain flow direction. |
| [Knowledge Graph Topology](../examples/recipes/network-graph/README.md) | Graphs/knowledge | `network-graph` | Render nodes and links as spatial graph geometry to discuss hubs, bridges, and communities. |
| [Terrain and Site Markers](../examples/recipes/geospatial-terrain/README.md) | Geospatial/science | `geospatial-terrain` | Represent a small terrain tile with highlighted points of interest, suitable for GIS-to-Octane experiments. |
| [Orbital Trajectories](../examples/recipes/physics-orbits/README.md) | Physics/simulation | `physics-orbits` | Show several trajectories around a central body to explain orbital state, phase, or simulation snapshots. |
| [MCP Architecture Flow](../examples/recipes/architecture-flow/README.md) | Architecture/explanation | `architecture-flow` | Turn an architecture diagram into geometry: user, agent, queue, and Octane as spatial blocks connected by flow lines. |
| [Hermes Avatar Guide](../examples/recipes/avatar-guide/README.md) | Agent communication | `avatar-guide` | Place a geometric Hermes guide in a scene with a pointer so agents can direct attention visually. |
| [Wave Interference Field](../examples/recipes/wave-interference-field/README.md) | Math/physics | `wave-interference-field` | Show constructive and destructive interference from two point sources as a height field with source markers. |
| [Render/Vision Feedback Loop](../examples/recipes/vision-feedback-loop/README.md) | Agent workflow | `vision-feedback-loop` | Represent the closed loop where an agent queues geometry, Octane saves a PNG, local vision reviews it, and the next scene patch is chosen. |
| [Annotated Text Labels](../examples/recipes/annotated-text-labels/README.md) | Annotation/text rendering | `annotated-text-labels` | Demonstrate labels, backing plates, and callouts as generated OBJ geometry rather than native Octane text nodes. |
| [Image Heightfield and Mask Inspection](../examples/recipes/image-heightfield-mask/README.md) | Image processing/vision | `image-heightfield-mask` | Turn a small image, heatmap, or segmentation mask into raised tile geometry for visual QA in Octane. |
| [Document OCR Layout Inspection](../examples/recipes/document-ocr-layout/README.md) | Document AI/OCR | `document-ocr-layout` | Represent OCR/document-layout output as raised boxes for text lines, tables, images, and uncertain detections. |
| [Transformer Attention Map](../examples/recipes/transformer-attention-map/README.md) | LLM interpretability | `transformer-attention-map` | Visualize an attention matrix as raised cells, with token rails and a highlighted focus region for interpretability discussions. |
| [Photoreal Product Studio](../examples/recipes/photoreal-product-studio/README.md) | Photoreal/PBR rendering | `photoreal-product-studio` | Set a quality target for glass, metal, softbox lighting, camera, and native-render validation. |
| [Photoreal Multi-Vase Studio](../examples/recipes/photoreal-vase-studio/README.md) | Photoreal/PBR rendering | `photoreal-vase-studio` | Stage several vases with visibly different silhouettes, colours, textures, and material intent for product visualization. |
| [Photoreal Earth in Space](../examples/recipes/photoreal-earth-space/README.md) | Photoreal/PBR space rendering | `photoreal-earth-space` | Set a quality target for Earth, cloud shells, atmosphere rim glow, and space lighting. |
| [Earth and Moon — Orbital Space](../examples/recipes/earth-moon-space/README.md) | Photoreal/PBR space rendering | `earth-moon-space` | Similar to photoreal-earth-space but with explicit Earth-Moon system and orbital positioning. |
| [Helicoid Spiral](../examples/recipes/helicoid-spiral/README.md) | Mathematics/geometry | `helicoid-spiral` | Render a helicoid spiral surface to explain rotational translation and parametric curves. |
| [Saturn and Moons in Space](../examples/recipes/saturn-moons-space/README.md) | Photoreal/PBR space rendering | `saturn-moons-space` | Set a quality target for Saturn bands, rings, Cassini division cues, moons, and space lighting. |
| [Green Chess Pawn (Studio)](../examples/recipes/green-pawn/README.md) | Photoreal/PBR rendering | `green-pawn` | A single photorealistic green glossy chess pawn under soft studio lighting, built from a lathed surface-of-revolution OBJ (not a primitive). |
| [Green Chess Pawn on a Studio Chessboard](../examples/recipes/green-pawn-board/README.md) | Photoreal/PBR rendering | `green-pawn-board` | A green glossy pawn on an 8×8 chessboard under studio lighting, with three group-indexed materials (board slab, light squares, pawn). |
| [Bowl of Fruit (Studio)](../examples/recipes/bowl-of-fruit/README.md) | Product / prop studio | `bowl-of-fruit` | A stylised ceramic bowl of glossy fruit, demonstrating a reusable multi-group still-life OBJ with explicit material binding. |
| [Desk Fan with Cord and Plug](../examples/recipes/desk-fan/README.md) | Product / prop studio | `desk-fan` | A stylised desk fan with blue blades, tubular front/back guard cage, stand/base, tubular cord, plug body, and brass prongs. |
| [Cutaway Earth — point-cloud hemisphere](../examples/recipes/earth-hemisphere/README.md) | Geoscience / planet visualization | `earth-hemisphere` | Dense to-scale interior-shell point cloud (PREM-like) + atmospheric sheaths as translucent jello with a glowing solid inner core; WGS84 oblateness, differentiated continental/oceanic crust, smooth-sphere particles, LLSVP provinces + plume tendrils, off-axis "Hermes Camera" framing. |

## Recommended agent loop

1. Read the recipe README and inspect `preview.png` or the recipe-specific target preview.
2. Reuse or modify `scene.obj` / the generator pattern.
3. Queue import/camera/render commands through MCP.
4. Drain the complete queue once with `octane_run_oneshot_bridge()` or Octane X → **Script** → `hermes_bridge_oneshot.generated`, then poll `queue/` to zero.
5. Save an Octane preview.
6. If the result teaches anything reusable, call `octane_record_recipe(...)` or edit `docs/recipe-book.md`.

## Coverage map

- **Data:** KPI bars.
- **Math:** radial surface and vector field.
- **Graphs:** knowledge/dependency graph.
- **Geospatial:** terrain tile and site markers.
- **Physics:** orbital trajectories.
- **Systems:** MCP architecture flow.
- **Agent communication:** Hermes avatar guide.
- **Feedback loops:** render/vision review loop and corrective camera/material iteration.
- **Annotation/text:** block-letter labels, backing plates, and callouts as OBJ geometry.
- **Image processing/vision:** scalar heatmaps, segmentation masks, and OCR/document layouts as raised tile geometry.
- **LLM interpretability:** attention/saliency matrices as token-aligned heightfields.
- **Photoreal / product props:** product-studio, multi-vase studio, bowl-of-fruit, desk-fan, Earth, and Saturn scenes with PBR/studio material and lighting intent plus target/native renders.

## Recipe registry tools

The MCP server can now inspect and queue checked-in recipes directly:

| Tool | Purpose |
| --- | --- |
| `octane_recipe_index()` | List recipe slugs, titles, domains, assets, preview paths, command counts, and native-Octane verification flags. |
| `octane_load_recipe(slug)` | Load one recipe with resolved repo-local asset paths and command metadata. |
| `octane_queue_recipe(slug, overrides=None)` | Queue a recipe's command sequence; optionally override per-op payload fields such as render resolution/samples. |
| `octane_validate_recipe_library()` | Validate that recipe directories include required files, previews, metadata, and valid command payloads. |

Recipe registry tools only prove that commands were queued. Native Octane success still requires bridge result metadata plus a saved preview review.

## Visual iteration protocol

For target-matching recipes, especially photoreal references, use [`visual-iteration-protocol.md`](visual-iteration-protocol.md): render a native Octane candidate, review reference and candidate with local `qwen2.5vl:7b` (or `glm-ocr` for parity), patch one bounded scene dimension, re-render, and bundle the final native render plus iteration records with the recipe.

## Animation pattern

Current reliable animation flow:

```text
Python generator -> obj_frames/scene_000.obj ... -> frame PNGs -> animation.gif / animation.mp4
```

Native Octane timeline controls are not yet exposed by the MCP. For now, generate one OBJ scene state per frame, render or preview each frame, then encode with `ffmpeg`. This is enough for data stories, trajectory reveals, system-flow explainers, and parameter sweeps.
