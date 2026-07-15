# Oceananigans Shallow-Water Front

Phase B fixture-first adapter recipe. It renders a compact Oceananigans-style shallow-water export as a front/eddy free surface with velocity glyphs and a bathymetry/coastline base.

## Provenance

- Fixture: `/Users/craig/octanex-mcp/examples/fixtures/oceananigans/shallow-water-front/shallow-water-front.npz`
- SHA-256: `e8e9517d42be0e879724c5fc99097ba1f0932992e4b0f2b81a6c775fce5a4274`
- Grid: `24×36`
- Velocity glyphs: `15`

## Regenerate

```bash
python3 scripts/export_oceananigans_shallow_water_fixture.py --timeout 240
PYTHONPATH=scripts:. uv run python scripts/gen_oceananigans_shallow_water_recipe.py
```

Then promote through the live Octane recipe verifier when ready.

## Pitfalls

- This recipe must not import Julia/Oceananigans during normal tests; the committed `.npz` is the boundary.
- OBJ/MTL colours are documentation only. `scene.json` binds every material group explicitly.
- Velocity vectors are arrow meshes, not OBJ line primitives.
