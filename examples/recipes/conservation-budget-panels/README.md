# Conservation Budget Panels (C2)

Phase C numerical-diagnostics recipe. Shows MHD energy near-conservation as 3D bars across 8 timesteps (kinetic / magnetic / internal) plus a red relative-drift (error) panel. Trace from a real Orszag-Tang MHD integration (`benchmarks.spec._orszag_tang_mhd`), committed deterministically.

Re-render:

```
PYTHONPATH=scripts:. uv run python scripts/gen_conservation_budget_recipe.py
```

Promote via the live Octane path: `benchmarks.verify_recipes --live --copy-back --slug conservation-budget-panels`.
