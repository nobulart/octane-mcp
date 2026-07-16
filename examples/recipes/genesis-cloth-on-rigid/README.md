# Genesis Cloth on Rigid Body

Phase B fixture-first adapter for a Genesis-style cloth sheet draping over a translating rigid body with emergent contact markers.

## Provenance

- Fixture: `examples/fixtures/genesis/cloth-on-rigid/cloth-on-rigid.json`
- SHA-256: `03b1b497ca0dbac6…`
- Grid: `24×24`
- Contact markers: `65`

## Regenerate

```bash
PYTHONPATH=scripts:. uv run python scripts/export_genesis_cloth_on_rigid_fixture.py
PYTHONPATH=scripts:. uv run python scripts/gen_genesis_cloth_on_rigid_recipe.py
```

## Pitfalls

- The committed fixture is an analytic drape snapshot; the local Genesis build does not yet expose a stable CLOTH/RIGID Python entity API, so the fixture regeneration script documents the call sequence for when it does.
- OBJ/MTL colours are ignored by the bridge; scene.json material commands are required.
- Contact markers are ellipsoid meshes (OBJ line primitives may be dropped).
