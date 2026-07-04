# Animated Orbit Reveal

![Animated preview](animation.gif)

This is a minimal animated product example for OctaneX MCP. It demonstrates the practical pattern before native Octane animation controls exist in the MCP surface:

1. Generate a sequence of scene states (`obj_frames/scene_000.obj` ...).
2. Render or preview each state as a PNG frame (`frames/frame_000.png` ...).
3. Encode the frames into a reviewable artifact (`animation.gif` and `animation.mp4`).

## Files

- `animation.gif` — GitHub-friendly animated preview.
- `animation.mp4` — video product encoded with ffmpeg.
- `frames/` — deterministic lightweight PNG frames.
- `obj_frames/` — reusable OBJ scene states for Octane re-rendering. These use line primitives for orbit paths; convert paths to thin cylinders/tubes if the native importer drops lines.
- `storyboard.json` — metadata, FPS, product list, and agent pattern.

## Why this matters

Animated products are useful for:

- temporal data stories;
- orbit/trajectory/physics explanations;
- architecture flows and command lifecycle diagrams;
- optimization progress over time;
- before/after or step-by-step debugging explanations.

## Re-rendering in Octane

For final-quality native renders, process each OBJ frame through the Octane bridge:

1. Import `obj_frames/scene_000.obj` with `octane_import_geometry(...)`.
2. Apply a stable camera and lighting preset.
3. Save a PNG preview for that frame.
4. Repeat for each frame, then encode the saved PNG sequence with:

```bash
ffmpeg -y -framerate 12 -i frame_%03d.png -pix_fmt yuv420p animation.mp4
```

The repo-generated preview keeps the learning artifact available even when Octane is not running.
