# Dam-Break Splash (SPlisHSPlasH fixture)

Phase B adapter recipe. Source: `examples/fixtures/particles/dam-break-small/dam-break-small.csv` (sha256 `6299186d5b57f9f5…`), loaded via `scripts/physics_fixture_io.py`.

Re-render:

```
PYTHONPATH=scripts:. uv run python scripts/gen_splishsplash_recipe.py
```

Then promote via the live Octane path with `benchmarks.verify_recipes --live --copy-back`.
