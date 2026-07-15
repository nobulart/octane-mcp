# Mandelbulb Evolutionary Morph

![Animated preview](animation.gif)

An animated parameter sweep of the **Mandelbulb** fractal, demonstrating the
current OctaneX MCP animation pattern: generate a sequence of OBJ scene states
→ render each as a PNG frame → encode a reviewable artifact (GIF/MP4).

## What it shows

A one-way evolutionary morph of the Mandelbulb over 10 s @ 24 fps (240 frames),
800×800:

- **Power 6 → 11** (one-way; the driving geometric parameter — low power is a
  chunky, lobed bulb, high power is a dense, spiky/irregular fractal).
- **Radius 2.2 → 3.2** (subtle iso-surface swell alongside the power sweep).
- **Slow camera orbit** (azimuth 0° → 330°) + **dolly-in** (camera radius 11 → 7).
- **Glossy 7-band rainbow** materials bound on every frame.

## Files

- `animation.mp4` — 800×800, 24 fps, H.264 (9.7 MB) — primary deliverable.
- `animation.gif` — 360px, 12 fps, GitHub-friendly preview.
- `frames/` — 16 representative PNG frames (start/mid/end + evenly spaced),
  for quick review without the full 240-set.
- `obj_frames/` — 3 sample OBJ scene states (power 6 / 8.5 / 11) for
  re-rendering without regenerating the full set.
- `storyboard.json` — metadata, FPS, parameter curve, and the agent pipeline.

> The full 240-frame PNG set and 240-frame OBJ set (~2.7 GB) are **not** checked
> in (no git-lfs on this repo). Regenerate them with the driver below; the
> artifacts here are sufficient to preview and re-render.

## Reproduce

```bash
# 1) generate 240 morph meshes + queue 18 commands/frame (4320 total)
python scripts/anim_mandelbulb_morph.py 240 140 0
# 2) drain the queue (ONE oneshot click per Octane process)
#    via the MCP octane_run_oneshot_bridge tool, then poll for 240 frames
# 3) encode
ffmpeg -y -framerate 24 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p \
  -crf 18 -movflags +faststart animation.mp4
```

## Key engineering notes (pitfalls)

- **`gen_mandelbulb.py` must honor a per-frame OBJ path.** An earlier version
  hardcoded its output to `assets/mandelbulb.obj` and ignored the per-frame
  filename argument, so every `import_geometry` pointed at a nonexistent file →
  **blank/sky frames**. Fixed: the 5th argv is the output path.
- **Self-contained frames.** Each frame re-issues `import_geometry` + 7×
  `create_material` + 7× `assign_material` + `set_camera` + `set_lighting` +
  `save_preview`. Do NOT rely on cross-frame node identity: re-importing a
  different OBJ under the same node name rebuilds the mesh node and drops the
  band-material bindings → blank.
- **One bridge click per Octane process.** The oneshot drains the entire queue
  synchronously; a second click mid-render is ignored and can race the PNG write
  into a blank frame. Poll the disk for `frame_NNNN.png`, don't re-click.
- **Resolution/res for 240 frames:** res 140 keeps the 240-OBJ footprint ≈ 2.7 GB.
  res 200 (used for stills) would exceed the container disk budget at this frame
  count.
- **Last frame drop:** the full drain occasionally drops the final frame; verify
  all 240 are present and re-queue the missing one with
  `scripts/queue_one_frame.py <N>`.
