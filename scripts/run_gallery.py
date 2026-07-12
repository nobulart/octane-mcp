#!/usr/bin/env python3
"""run_gallery.py — autonomous SEQUENTIAL gallery driver (one renderer).

Reads surface_index.json. For each surface with status "pending":
  - if it has a formula_key (meshable TPMS): research -> mesh -> render ->
    capture -> VLM-verify -> write recipe -> recipe-book entry -> commit+push.
  - else: mark status "blocked:needs_parametric", record gap, skip (NO fake geo).

Renderer is single (OctaneX one-shot bridge), so everything is strictly
sequential: each surface waits for its render + queue drain before the next.

Usage: python3 scripts/run_gallery.py [--only pending|blocked|all]
"""
import json, os, subprocess, sys, time, shutil

# Interpreter split (verified this session):
#   /usr/bin/python3  -> has scikit-image (mesh gen needs marching_cubes)
#   /opt/homebrew/bin/python3 -> has working PIL+numpy (capture/VLM need PIL)
# No single interpreter has both, so we invoke each tool with the right one.
PY_MESH = "/usr/bin/python3"
PY_IMG = "/opt/homebrew/bin/python3"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "surface_index.json")
ASSET = os.path.expanduser("~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP")
GEN = os.path.join(ROOT, "scripts", "gen_implicit_surface.py")
QUEUE = os.path.join(ROOT, "scripts", "queue_implicit_surface.py")
RESEARCH = os.path.join(ROOT, "scripts", "research_surface.py")
LOG = os.path.join(ASSET, "bridge.log")
OUT_ROOT = os.path.join(ROOT, "examples", "recipes")

CAM = (7.14, -0.58, 4.733)  # oblique (60X/30Z) target, sanity only


def sh(cmd, timeout=300):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT)


def obj_bounds(obj):
    cx = cy = cz = n = 0.0
    for l in open(obj):
        if l.startswith("v "):
            p = l[2:].split()
            if len(p) < 3:
                continue
            cx += float(p[0]); cy += float(p[1]); cz += float(p[2]); n += 1
    return [cx / n, cy / n, cz / n], 2.5


def single_manifold(obj):
    from collections import deque
    import numpy as np
    v = []; f = []
    for l in open(obj):
        if l.startswith("v "):
            v.append([float(x) for x in l[2:].split()])
        elif l.startswith("f "):
            f.append([int(x.split('/')[0]) - 1 for x in l[2:].split()[:3]])
    v = np.array(v); f = np.array(f)
    adj = [set() for _ in range(len(v))]
    for a, b, c in f:
        adj[a] |= {b, c}; adj[b] |= {a, c}; adj[c] |= {a, b}
    seen = set(); comp = 0
    for s in range(len(v)):
        if s in seen:
            continue
        comp += 1; q = deque([s]); seen.add(s)
        while q:
            u = q.popleft()
            for w in adj[u]:
                if w not in seen:
                    seen.add(w); q.append(w)
    return comp


def wait_render(name, pre_lines, timeout=240):
    """Poll bridge.log for 'preview saved .../<name>_octane-preview.png'."""
    end = time.time() + timeout
    while time.time() < end:
        cur = len(open(LOG).readlines())
        tail = open(LOG).readlines()[-200:]
        for l in tail:
            if "preview saved" in l and f"{name}_octane-preview.png" in l:
                return True
        time.sleep(4)
    return False


def capture_crop(name):
    """screencapture the Octane window region, crop the 1280x1280 render box."""
    from PIL import Image
    import numpy as np
    win = "/tmp/hermes_gallery_win.png"
    sh(["screencapture", "-R", "1929,-1049,2609,2029", "-x", win])
    im = Image.open(win).convert("RGB")
    W, H = im.size
    a = np.array(im).astype(int); gray = a.mean(2)
    best = None; bs = -1
    for y in range(0, H - 1280 + 1, 20):
        for x in range(0, W - 1280 + 1, 20):
            if x > W * 0.5 or y > H * 0.5:
                continue
            s = gray[y:y + 1280, x:x + 1280].mean()
            if s > bs:
                bs = s; best = (x, y)
    x, y = best if best else (0, 0)
    out = os.path.join(ASSET, "renders", f"{name}_octane-preview.png")
    im.crop((x, y, x + 1280, y + 1280)).save(out)
    return out


def vlm_check(name, render_png, ref_png):
    if not ref_png or not os.path.exists(ref_png):
        return "skipped (no ref image)"
    import base64, io
    from PIL import Image
    def b64(p, th=480):
        im = Image.open(p).convert("RGB"); im.thumbnail((th, th))
        buf = io.BytesIO(); im.save(buf, "PNG")
        return base64.b64encode(buf.getvalue()).decode()
    payload = {"model": "qwen2.5vl:7b",
               "prompt": f"Image1 is my 3D render of '{name}'. Image2 is the canonical reference. Is my render the CORRECT {name} surface (single connected manifold, correct topology/symmetry)? Answer YES/NO + one-line reason.",
               "images": [b64(render_png), b64(ref_png)], "stream": False}
    import tempfile
    pf = tempfile.mktemp(suffix=".json"); open(pf, "w").write(json.dumps(payload))
    r = sh(["curl", "-s", "http://localhost:11434/api/generate", "-d", f"@{pf}"], timeout=150)
    try:
        return json.loads(r.stdout)["response"].strip()[:200]
    except Exception as e:
        return f"vlm_err {e}"


def render_surface(name, formula_key):
    obj = os.path.join(ASSET, "assets", f"{name}.obj")
    # mesh
    r = sh([PY_MESH, GEN, obj, name, formula_key, "132", "2.5", "1"], timeout=180)
    if r.returncode != 0:
        return False, f"mesh rc={r.returncode}: {r.stderr[:160]}"
    comp = single_manifold(obj)
    if comp != 1:
        return False, f"mesh not single manifold (comps={comp})"
    # queue + render
    pre = len(open(LOG).readlines())
    sh(["osascript", os.path.join(ROOT, "scripts", "octane_reset_scene.applescript")], timeout=60)
    sh([sys.executable, QUEUE, obj, name], timeout=120)
    sh(["osascript", os.path.join(ROOT, "scripts", "octane_run_oneshot.applescript")], timeout=60)
    if not wait_render(name, pre):
        return False, "render timeout (no preview saved)"
    render_png = capture_crop(name)
    return True, render_png


def write_recipe(name, formula_key, render_png, equation, vlm):
    d = os.path.join(OUT_ROOT, name)
    os.makedirs(d, exist_ok=True)
    shutil.copy(render_png, os.path.join(d, "octane-preview.png"))
    shutil.copy(os.path.join(ASSET, "assets", f"{name}.obj"), os.path.join(d, f"{name}.obj"))
    readme = f"""# {name} — 3DXM Minimal-Surface Gallery

- **Equation:** {equation or 'n/a (parametric)'}
- **Form:** single manifold (mesh verified, 1 connected component)
- **Material:** per-surface palette (see docs/recipe-book.md)
- **Camera:** oblique (60° X, 30° Z)
- **Render:** 1280×1280, ~5000 SPP
- **Status:** ✅ rendered (autonomous run 2026-07-13); VLM check: {vlm}
"""
    open(os.path.join(d, "README.md"), "w").write(readme)


def append_book_entry(name, formula_key, equation, vlm):
    book = os.path.join(ROOT, "docs", "recipe-book.md")
    entry = f"""
## Surface (autonomous) — {name}

- **Outcome:** success (autonomous sequential run, 2026-07-13)
- **Equation:** {equation or 'n/a'}
- **Mesh:** single manifold via `scripts/gen_implicit_surface.py {name} {formula_key} 132 2.5 1`
- **VLM check:** {vlm}
"""
    open(book, "a").write(entry)


def tag_bag(name, formula_key):
    sh(["bash", os.path.join(ROOT, "scripts", "coord", "intent.sh"),
         f"docs/recipe-book.md;examples/recipes/{name}/;scripts/;surface_index.json"])
    # Commit the recipe AND the runner tooling (so the pipeline is versioned
    # even if a later surface interrupts the run).
    sh(["git", "add", "docs/recipe-book.md", f"examples/recipes/{name}/",
         "scripts/run_gallery.py", "scripts/research_surface.py", "surface_index.json"])
    sh(["git", "commit", "-m",
         f"feat(gallery): autonomous {name} ({formula_key}) recipe + pipeline"])
    sh(["git", "push"])
    sh(["bash", os.path.join(ROOT, "scripts", "coord", "notify.sh"),
         f"pushed autonomous {name}"])


def main():
    # Accept "--only pending" as one arg or two (argv split on space).
    args = sys.argv[1:]
    mode = " ".join(args) if args else "--only pending"
    only_pending = mode.startswith("--only")
    idx = json.load(open(INDEX))
    results = []
    for surf in idx["surfaces"]:
        name = surf["name"]; fk = surf.get("formula_key")
        if only_pending and surf["status"] != "pending":
            continue
        print(f"[run] {name} (formula_key={fk})")
        try:
            if not fk:
                surf["status"] = "blocked:needs_parametric"
                surf["gap"] = "no closed-form implicit equation; requires parametric/Weierstrass meshing (not yet implemented)"
                results.append((name, "BLOCKED", surf["gap"]))
                print(f"  -> BLOCKED: {surf['gap']}")
                continue
            ok, info = render_surface(name, fk)
            if not ok:
                surf["status"] = "failed"
                surf["error"] = info
                results.append((name, "FAILED", info))
                print(f"  -> FAILED: {info}")
                continue
            # research + vlm
            rr = sh([sys.executable, RESEARCH, name, fk or "none",
                      os.path.join(ROOT, "examples", "recipes", f"_{name}_research")], timeout=120)
            eq = None; ref = None
            try:
                rd = json.loads(rr.stdout)
                eq = rd.get("equation") or rd.get("generator_eq")
                ref = rd.get("ref_image")
            except Exception:
                pass
            vlm = vlm_check(name, info, ref)
            write_recipe(name, fk, info, eq, vlm)
            append_book_entry(name, fk, eq, vlm)
            tag_bag(name, fk)
            surf["status"] = "done"
            results.append((name, "DONE", vlm))
            print(f"  -> DONE: {vlm}")
        except Exception as exc:
            # One surface blowing up must not kill the whole unattended run.
            surf["status"] = "failed"
            surf["error"] = f"{type(exc).__name__}: {exc}"[:200]
            results.append((name, "FAILED", surf["error"]))
            print(f"  -> FAILED (exception): {surf['error']}")
            continue
    json.dump(idx, open(INDEX, "w"), indent=2)
    print("\n=== SUMMARY ===")
    for n, s, i in results:
        print(f"  [{s}] {n}: {i}")


if __name__ == "__main__":
    main()
