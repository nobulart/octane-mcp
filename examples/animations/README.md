# Animated Examples

Animated products are possible with the current OctaneX MCP architecture by treating animation as a sequence of scene states:

```text
Python generator -> OBJ frame states -> PNG frame renders/previews -> GIF/MP4 product
```

The MCP does not yet expose a native Octane timeline API. Until it does, the reliable pattern is frame-by-frame generation and rendering.

## Included example

- [`orbit-reveal/`](orbit-reveal/) — a short orbit/trajectory reveal with:
  - `animation.gif` for GitHub preview;
  - `animation.mp4` for video review;
  - `frames/*.png` lightweight deterministic preview frames;
  - `obj_frames/*.obj` reusable scene states for Octane re-rendering;
  - `storyboard.json` for agents.
- [`mandelbulb-morph/`](mandelbulb-morph/) — Mandelbulb power 6→11 evolutionary
  sweep with slow orbit + dolly-in (240 frames, 800×800, glossy rainbow bands);
  `animation.mp4` / `animation.gif` + sample OBJs and a regenerable driver.

## Good animation targets

- temporal data stories and changing metrics;
- flow diagrams and command lifecycle explanations;
- mathematical transformations and parameter sweeps;
- physical trajectories, fields, and simulations;
- visual debugging: before/after/fix progression.
