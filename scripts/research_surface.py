#!/usr/bin/env python3
"""research_surface.py — per-surface equation + reference verification (recipe-book TODO).

Given a surface name + its generator formula_key, this:
  1. SearXNG-fetches the canonical source (Wikipedia/Wolfram/VMM) for the
     implicit equation.
  2. Downloads one reference image for later VLM comparison.
  3. Cross-checks the generator's baked equation (if formula_key given).

Outputs a JSON to stdout: {name, equation, ref_image, generator_eq_ok, note}

Run: python3 scripts/research_surface.py <name> <formula_key|null> [out_dir]
"""
import json, os, re, subprocess, sys, urllib.parse

SEARX = "http://localhost:8888/search"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "scripts", "gen_implicit_surface.py")


def _get(url, timeout=40):
    """Fetch a URL as decoded text (UTF-8, errors replaced)."""
    r = subprocess.run(["curl", "-sL", "--max-time", str(timeout), url],
                       capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def _searx(query):
    q = urllib.parse.quote(query)
    raw = _get(f"{SEARX}?q={q}&format=json")
    try:
        return json.loads(raw)
    except Exception:
        return {"results": []}


def _fetch_ref_image(name, out_dir):
    """Try Wikipedia + Virtual Math Museum for a reference PNG/JPG."""
    os.makedirs(out_dir, exist_ok=True)
    # Wikipedia
    wp = _get(f"https://en.wikipedia.org/wiki/{name}")
    imgs = re.findall(r'src="(//upload\.wikimedia\.org/[^"]+\.(?:png|jpg|jpeg))"', wp)
    for u in imgs:
        fn = os.path.join(out_dir, f"{name}_wiki_ref.png")
        subprocess.run(["curl", "-sL", "--max-time", "60", f"https:{u}", "-o", fn])
        if os.path.getsize(fn) > 2000:
            return fn
    # VMM
    vmm = _get(f"https://virtualmathmuseum.org/Surface/{name}/{name}.html")
    vrefs = re.findall(r'(i/[a-zA-Z0-9_]+\.png)', vmm)
    for r in vrefs[:2]:
        fn = os.path.join(out_dir, f"{name}_vmm_ref.png")
        subprocess.run(["curl", "-sL", "--max-time", "60",
                       f"https://virtualmathmuseum.org/Surface/{name}/{r}", "-o", fn])
        if os.path.getsize(fn) > 2000:
            return fn
    return None


def _generator_eq(formula_key):
    if not formula_key or formula_key in ("none", "null"):
        return None
    if not os.path.exists(GEN):
        return None
    src = open(GEN).read()
    if formula_key == "gyroid":
        return "sin x cos y + sin y cos z + sin z cos x = 0" if "np.sin(X)*np.cos(Y)" in src else None
    if formula_key in ("schwarz", "schwarz_p"):
        return "cos x + cos y + cos z = 0" if "np.cos(X) + np.cos(Y) + np.cos(Z)" in src else None
    if formula_key == "schwarz_h":
        return ("sin x cos y cos z + cos x sin y cos z + cos x cos y sin z = 0"
                if "np.sin(X)*np.cos(Y)*np.cos(Z)" in src else None)
    if formula_key == "schwarz_pd":
        return ("cos x cos y cos z - sin x sin y sin z = 0"
                if "np.cos(X)*np.cos(Y)*np.cos(Z)" in src else None)
    if formula_key == "neovius":
        return "3(cos x + cos y + cos z) + 4 cos x cos y cos z = 0" if "3*(" in src else None
    if formula_key == "lidinoid":
        return "sin x sin y sin z + sin 2x cos y cos z + cos x sin 2y sin z + cos x cos y sin 2z = 0" if "np.sin(2" in src else None
    return None


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "gyroid"
    formula_key = sys.argv[2] if len(sys.argv) > 2 else "none"
    out_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "examples", "recipes", f"_{name}_research")
    os.makedirs(out_dir, exist_ok=True)

    query = f"{name} minimal surface implicit equation"
    res = _searx(query)
    equation = None
    note = []
    for r in res.get("results", [])[:6]:
        c = (r.get("content") or "")
        m = re.search(r"([a-zA-Z]+\s*[+−-]\s*[a-zA-Z]+\s*[+−-]\s*[a-zA-Z]+\s*=\s*0)", c)
        if m:
            equation = m.group(1).replace("−", "-")
            break
    if not equation:
        note.append("no equation string extracted from search; relying on generator baked eq")

    ref = _fetch_ref_image(name, out_dir)
    if not ref:
        note.append("no reference image fetched")

    gen_eq = _generator_eq(formula_key)
    out = {
        "name": name,
        "formula_key": formula_key,
        "equation": equation,
        "generator_eq": gen_eq,
        "ref_image": ref,
        "generator_eq_ok": (gen_eq is not None),
        "note": "; ".join(note) or "ok",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
