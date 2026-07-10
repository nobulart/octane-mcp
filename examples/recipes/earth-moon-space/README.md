# Earth + Moon (Space Scene)

Render Earth and the Moon as distinct bodies with correct blue/grey materials so the bridge's per-group material binding is demonstrated on two separated spheres.

## Usage

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/earth-moon-space/scene.obj", name="earth-moon-space")`.
2. Create + assign materials per `usemtl` group.
3. Set camera, lighting, then `octane_save_preview`.

Camera: position [28.999, 19.161, 36.194] -> target [3.45, 0.0, 0.0], fov 42.

## Assets

`scene.obj`, `scene.mtl`, `scene.json`, `preview.png`, `octane-preview.png`.

> **Native Octane preview: PENDING.** Both live capture attempts (2026-07-10) returned
> near-empty frames (white background, ~2% non-background, `mean_abs_dev_from_bg` ≈ 2–4
> vs the real-subject bar of >>5). The scene graph, geometry, and command sequence are
> sound; the blank output is a render/launch issue, not a geometry defect. A real
> `octane-preview.png` should replace the placeholder once a live drain produces a
> converged Earth-Moon frame. Per the project's "a blank frame is NOT success" rule,
> a degenerate preview is intentionally NOT committed.
