# LuisaRender Backend Investigation

**Status:** Feasibility investigation, not yet an implemented backend.  
**Date:** 2026-07-15.  
**Question:** Could `/Users/craig/src/LuisaRender` provide an alternate render backend to Octane X for `octanex-mcp`?

---

## Verdict

**Yes, plausibly — but as an offline quality/path-tracing backend, not as the realtime Canvas tier.**

LuisaRender is a CLI-driven Monte Carlo renderer with a macOS Metal backend and a scene-description language that can ingest OBJ/glTF-derived geometry via Assimp. That makes it a credible alternative to Octane for reproducible local final renders, especially when Octane X's AppleScript/TCC/sandbox path is the bottleneck.

It is not a drop-in replacement for the current Octane bridge. The current `octanex-mcp` scene grammar is an Octane command queue (`import_geometry`, `create_material`, `assign_material`, `set_camera`, `set_lighting`, `save_preview`). LuisaRender wants a complete scene-description file (`.luisa` or JSON-derived scene) and then a one-shot CLI invocation:

```bash
luisa-render-cli -b metal scene.luisa
```

So the right architecture is a new `LuisaBackend` adapter that compiles the renderer-neutral scene/recipe state into a `.luisa` scene file, runs the CLI, converts its EXR output to PNG, and feeds the same pixel-acceptance path used by Octane previews.

---

## Evidence gathered

### Local checkout

Inspected local source at:

```text
/Users/craig/src/LuisaRender
```

Observed:

- HEAD: `59725304`
- CMake cache exists under `build/`
- configured Release build has Metal enabled:
  - `LUISA_COMPUTE_ENABLE_METAL:BOOL=ON`
  - `LUISA_COMPUTE_ENABLE_CUDA:BOOL=OFF`
  - `LUISA_COMPUTE_ENABLE_DX:BOOL=OFF`
  - `LUISA_COMPUTE_ENABLE_FALLBACK:BOOL=OFF`
- `build/bin/` exists but contained no finished `luisa-render-cli` executable before build attempt.
- local submodules show modified state in `src/compute`, `src/ext/assimp`, `src/ext/json`, etc.; treat the checkout as not pristine.

### Build attempt

Attempted:

```bash
cmake --build build --target luisa-render-cli -j 4
```

Result: configuration succeeded and began compiling, but build failed in bundled Assimp:

```text
/Users/craig/src/LuisaRender/src/ext/assimp/code/Common/ZipArchiveIOSystem.cpp:57:14: fatal error: 'unzip.h' file not found
```

Interpretation:

- The local checkout is close enough to configure for macOS/Metal.
- Current blocker is a build dependency/include issue around minizip/unzip headers, not an architectural failure.
- Fix candidates to test later:
  - install/locate Homebrew minizip headers and pass include path into CMake;
  - configure Assimp to avoid ZIP/minizip support if possible;
  - use a known-good LuisaRender branch/build recipe for Apple Silicon.

### CLI and scene model

From `src/apps/cli.cpp`, LuisaRender's CLI requires:

- `-b/--backend` backend name;
- positional scene file;
- optional `-d/--device`;
- optional `-D key=value` macro definitions.

The CLI creates a Luisa compute device, parses the scene, creates the scene/pipeline, renders, and synchronizes. There is no GUI scripting dependency in this path.

From `README.md` / `BUILD.md`:

- supported backend names include `metal`, `cuda`, `dx`, `cpu`, and `fallback`, depending on build flags;
- macOS 12+ and Apple Silicon are explicitly supported for Metal;
- LuisaRender supports both JSON-based and custom text-based scene descriptions;
- demo scenes live in a separate `LuisaRenderScenes` repo;
- `tools/tungsten2luisa.py` converts Tungsten JSON scenes to `.luisa`;
- `luisa-render-export` can convert glTF scenes into LuisaRender's JSON-based format, once built.

From `tools/tungsten2luisa.py`, a minimal `.luisa` scene can express:

- `Surface` nodes: `Matte`, `Plastic`, `Glass`, `Mirror`, `Metal`, `Null`;
- `Texture` nodes: `Constant`, `Image`, `Checkerboard`;
- `Shape` nodes: `Mesh`, `InlineMesh`, sphere/cube/disk via mesh files, quad via inline mesh;
- `Camera camera : Pinhole` with `fov`, `spp`, `filter`, `film`, output `file`, and `View` transform;
- `render` block with camera, integrator, shape list, and environment.

From source inspection:

- `src/shapes/mesh.cpp` uses Assimp, strips lines/points, requires a single imported mesh, and supports OBJ-like triangle meshes.
- `src/shapes/inline_mesh.cpp` supports explicit `positions` and `indices`; useful for tiny generated fixtures and avoiding OBJ/material edge cases.
- `src/films/color.cpp` exposes `Color` film with `resolution`, `exposure`, `clamp`, and downloadable framebuffer.
- `src/cameras/pinhole.cpp` exposes `Pinhole` camera with FOV and `View` transform.

### Web extraction caveat

`web_extract` could not fetch DeepWiki/GitHub pages because Firecrawl is not configured. Web search located the relevant LuisaRender and LuisaRenderScenes pages, but detailed external docs were not extracted. Findings above are grounded primarily in the local checkout and repository source.

---

## Fit against `octanex-mcp`

| Dimension | LuisaRender fit | Notes |
| --- | --- | --- |
| Local-first | Strong | CLI + Metal backend, no cloud. |
| Scriptability | Strong if built | Normal executable, no AppleScript/TCC bridge. |
| Photoreal/final quality | Strong | Monte Carlo/path-tracing class renderer. |
| Realtime Canvas | Weak | Offline renderer, not interactive WebGL. |
| Existing recipe geometry | Medium | OBJ input possible; combined OBJ single-mesh rule roughly aligns with Luisa's single-mesh loader. |
| Material translation | Medium | Need Octane material kind → Luisa Surface/Texture mapping. |
| Preview verification | Strong | Output can feed existing PNG pixel QA after EXR→PNG tonemap. |
| Build/ops complexity | Medium-high | Current local build blocked by `unzip.h`; demo scenes separate. |
| License | Verify before shipping | Keep adapter as a subprocess boundary regardless. |

---

## Proposed `LuisaBackend` shape

### Do not map Octane queue commands directly

Avoid implementing a fake Octane command drain. LuisaRender is scene-file based, so translation should happen from a renderer-neutral scene model or recipe bundle, not from the ordered Octane queue.

Preferred flow:

```text
recipe / BenchmarkTask / canvas.scene.v1
        |
        v
LuisaBackend.compile(scene)
        |
        +-- write scene.obj or inline mesh
        +-- write scene.luisa
        +-- map materials
        +-- map camera / lighting / samples / resolution
        v
luisa-render-cli -b metal scene.luisa
        |
        v
render.exr -> tonemap/convert -> preview.png
        |
        v
benchmarks.acceptance.evaluate_acceptance(preview.png, criteria)
```

### Minimal translation table

| Octane / recipe concept | LuisaRender target | Initial mapping |
| --- | --- | --- |
| `diffuse` material | `Surface ... : Matte` | `Kd : Constant { v { r,g,b } }` |
| `glossy` / rough plastic | `Surface ... : Plastic` | `Kd`, `eta≈1.5`, `roughness` |
| `glass` / transmission | `Surface ... : Glass` | `Kt`, `eta`, `roughness` |
| `metallic` | `Surface ... : Metal` | start with named material or approximate `eta/k`; fallback to `Plastic` until calibrated |
| emissive material | shape `light : Diffuse` | map `emission` to diffuse area light |
| OBJ combined mesh | `Shape ... : Mesh` | `file { "scene.obj" }`; one material per shape initially |
| small generated geometry | `Shape ... : InlineMesh` | direct positions/indices for smoke tests |
| `set_camera` | `Camera ... : Pinhole` + `View` | position/front/up, FOV, resolution, SPP |
| `set_lighting soft_studio` | environment + area light shapes | start with simple directional/spherical environment |
| `save_preview` | film `file { "render.exr" }` | convert EXR to PNG after CLI exits |

### Key design choice: one shape per material group

Luisa's `Mesh` shape loads a single mesh and assigns one `surface` to the shape. Octane recipes encode multiple material groups inside one OBJ and then bind via `assign_material(group_index)`.

For Luisa, the first robust strategy is to split the combined OBJ into one OBJ per material group or emit one `InlineMesh` per group. This preserves existing recipe semantics and avoids depending on MTL interpretation.

Possible helper:

```text
combined OBJ -> parse g/usemtl groups -> emit luisa_<slug>_<group>.obj -> Shape per group
```

This is also useful for Blender/Mitsuba later.

---

## Spike plan

### Spike 001 — Build and CLI smoke

**Given** the local checkout, **when** `luisa-render-cli` is built with Metal, **then** `luisa-render-cli -h` prints available options and `context.installed_backends()` includes `metal`.

Actions:

1. Resolve `unzip.h` build blocker.
2. Build target:
   ```bash
   cmake --build /Users/craig/src/LuisaRender/build --target luisa-render-cli -j 4
   ```
3. Run:
   ```bash
   /Users/craig/src/LuisaRender/build/bin/luisa-render-cli -h
   ```

Verdict gate: executable exists and help runs.

### Spike 002 — Minimal `.luisa` inline triangle/sphere render

**Given** a hand-authored tiny `.luisa` scene with `InlineMesh`, `Matte`, `Pinhole`, `Color` film, and `MegaPath`, **when** rendered with `-b metal`, **then** an EXR is produced and can be converted to PNG.

Use no Octane assets yet. This isolates Luisa build/runtime from octanex translation.

Verdict gate: non-empty PNG passes existing `review_preview` / `evaluate_acceptance`.

### Spike 003 — Translate one `BenchmarkTask`

**Given** `t1_glossy_cube` or `t1_surface_field`, **when** `LuisaBackend` compiles its spec into Luisa scene files, **then** Luisa produces a PNG that passes a simplified acceptance set.

Start with one material per group. Use `InlineMesh` to avoid OBJ/Assimp/MTL uncertainty if possible.

Verdict gate: same BenchmarkTask can run through OctaneBackend and LuisaBackend with comparable pixel acceptance, not identical pixels.

### Spike 004 — Recipe group split

**Given** a multi-material recipe such as `data-bars` or `t2_multi_material`, **when** group splitting is applied, **then** each material group becomes a distinct Luisa shape and the rendered output preserves semantic colours.

Verdict gate: colour-family checks detect at least two expected material families.

---

## Recommended implementation path

1. **Keep three.js/WebGL as the realtime Canvas priority.** LuisaRender does not replace the immediate live interaction need.
2. **Add LuisaRender as a candidate quality backend in the backend abstraction docs.** It belongs beside Mitsuba/OSPRay, not beside WebGL.
3. **Run the build/runtime smoke spike before writing production adapter code.** The local checkout currently does not build due to `unzip.h`.
4. **If smoke passes, implement `scripts/spike_luisa_scene.py` first**, not `src/octanex_mcp/backends/luisa_backend.py`. Prove scene generation and EXR→PNG first.
5. **Only after one BenchmarkTask renders**, promote the adapter into `src/octanex_mcp/backends/` with tests around scene-file generation, not live rendering.

---

## Open questions

- What is the cleanest fix for the local `unzip.h` build failure?
- Does LuisaRender's output filename always come from `Camera.file`, and is EXR the only practical output format?
- Which EXR→PNG path should be standard here: Luisa's own tools, `tools/hdr2srgb.py`, ImageMagick, OpenImageIO, or a small Python dependency?
- Can `luisa-render-export` convert our existing OBJ/glTF fixtures cleanly enough to avoid writing `.luisa` directly?
- How robust is Metal backend performance on the Mac Studio / current macOS 26.6 setup?
- Does Luisa's Assimp path preserve object/group boundaries, or should the adapter always split groups itself?

---

## Bottom line

LuisaRender is worth a spike. It would not replace Octane X as an immediate drop-in, and it would not solve the realtime Canvas problem. But it could become a cleaner local quality backend with a normal CLI, Metal support, reproducible scene files, and no AppleScript/TCC dependency.

The next concrete step is **not** adapter architecture. It is a build/runtime smoke test that fixes `unzip.h`, renders one minimal `.luisa` scene, and converts the EXR to a PNG that the existing pixel QA can judge.
