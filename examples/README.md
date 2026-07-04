# Example Recipes

Reusable OctaneX MCP sample scenes. Start with [`../docs/recipe-library.md`](../docs/recipe-library.md) for the overview table.

Each recipe directory contains:

- `README.md` — operational recipe and variations;
- `scene.obj` — reusable geometry;
- `scene.mtl` — material hints when the recipe uses OBJ materials;
- `scene.json` — camera and MCP command metadata;
- `preview.png` or a recipe-specific target preview — deterministic lightweight preview render for quick review.

These previews are not final Octane renders; they are repo-generated teaching previews or target/reference images. Re-render a selected recipe in Octane X when validating visual quality or producing final documentation, then record useful successes or failures in `../docs/recipe-book.md`.

Animated examples are under [`animations/`](animations/). They use the frame-sequence pattern: generated OBJ states plus PNG frames encoded into GIF/MP4 products.
