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
- The fixture is a *real* conservative-Rusanov MHD evolution (8 steps) of the Orszag-Tang initial condition, run via `scripts/mhd_integrator.py` by `export_mpipymhd_orszag_tang_fixture.py`. The sidecar records `mpi_enabled: true` / `mpi_mode: serial_in_mpi` (or `domain_decomposed` under `mpirun`). The local MPIPyMHD checkout remains a minimal MPI scaffold; this exporter is the actual solver.
- Vector fields are arrow meshes, not OBJ line primitives.
