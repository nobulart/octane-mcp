# Precision Error Landscape (C3)

Phase C numerical-diagnostics recipe. Shows floating-point precision error as a heightfield: a chaotic logistic map integrated to 60-digit `decimal` precision, compared against IEEE float64/float32. Height + colour encode relative error.

Re-render:

```
PYTHONPATH=scripts:. uv run python scripts/gen_precision_error_recipe.py
```

Promote via the live Octane path: `benchmarks.verify_recipes --live --copy-back --slug precision-error-landscape`.
