# MHD Orszag-Tang Vortex

Phase B fixture-first adapter recipe for an MPIPyMHD/Orszag-Tang-style MHD snapshot.

## Provenance

- Fixture: `/Users/craig/octanex-mcp/examples/fixtures/mpipymhd/orszag-tang-vortex/orszag-tang-vortex.npz`
- SHA-256: `980701398ae436f996e93d96a3b00d4b0e949832cc8616195acf395285aa7d6e`
- Grid: `32×32`
- Magnetic glyphs: `36`
- Velocity glyphs: `36`

## Regenerate

```bash
python3 scripts/export_mpipymhd_orszag_tang_fixture.py
PYTHONPATH=scripts:. uv run python scripts/gen_mpipymhd_orszag_tang_recipe.py
```

## Pitfalls

- Normal tests must not require mpi4py or an MPI runtime; the committed `.npz` is the boundary.
- The fixture is an analytic Orszag-Tang-style snapshot until the local MPIPyMHD source grows a full solver.
- Vector fields are arrow meshes, not OBJ line primitives.
