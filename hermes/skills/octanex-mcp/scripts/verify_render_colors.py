#!/usr/bin/env python3
"""Objective color verification for an OctaneX render PNG.

Scans the image (every Nth pixel) and classifies each pixel as red-dominant,
green-dominant, blue-dominant, or other, using simple channel-delta thresholds.
Prints counts, percentages, and the most-saturated example pixel per hue.

WHY: vision_analyze (auxiliary model) loops on open-ended questions, and a naive
box-average over lit geometry is fooled by warm studio rim light -- a green
sphere's lit edge reads tan even though its shielded core is green. A full-frame
hue scan is deterministic and lights the core correctly.

USAGE (any venv that has Pillow):

    python verify_render_colors.py --path renders/preview.png --step 2

If running under the Hermes agent runtime, its PYTHONPATH forces a broken venv,
so unset it first:

    env -u PYTHONPATH /tmp/pixcheck/bin/python verify_render_colors.py \
        --path renders/preview.png --step 2
"""
import argparse
from PIL import Image


def classify(r, g, b, thr=40):
    if g > r + thr and g > b + thr:
        return "green"
    if r > g + thr and r > b + thr:
        return "red"
    if b > r + thr and b > g + thr:
        return "blue"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--step", type=int, default=2, help="pixel stride (2 = every 2nd)")
    ap.add_argument("--thr", type=int, default=40, help="channel-delta threshold")
    args = ap.parse_args()

    im = Image.open(args.path).convert("RGB")
    W, H = im.size
    px = im.load()
    counts = {"red": 0, "green": 0, "blue": 0, "other": 0}
    best = {"red": (-1, None), "green": (-1, None), "blue": (-1, None)}
    for x in range(0, W, args.step):
        for y in range(0, H, args.step):
            r, g, b = px[x, y]
            hue = classify(r, g, b, args.thr)
            counts[hue] += 1
            if hue != "other":
                delta = {"red": r - g, "green": g - r, "blue": b - r}[hue]
                if delta > best[hue][0]:
                    best[hue] = (delta, (r, g, b))
    tot = sum(counts.values())
    print(f"size {W}x{H}  step {args.step}")
    for hue in ("red", "green", "blue", "other"):
        c = counts[hue]
        print(f"  {hue:6s}: {c:7d}  ({100 * c // tot}%)")
    for hue in ("red", "green", "blue"):
        delta, val = best[hue]
        if val:
            print(f"  most-{hue:5s} pixel: {val}  (delta {delta})")


if __name__ == "__main__":
    main()
