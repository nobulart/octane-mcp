#!/usr/bin/env python3
"""Pixel verification for the pawn-on-board preview (3-material scene).

Robust authoritative checks (pixels, per skill - NOT the model):
  - non-blank (large mean deviation from a corner bg proxy)
  - green pawn present and colored green
  - a CHECKERBOARD pattern on the board: a horizontal scan line across the
    board floor must alternate dark/light squares several times (>=3 cycles),
    which unambiguously distinguishes a chessboard from a flat plane.
"""
from PIL import Image
import numpy as np

p = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/pawn_on_board_preview.png"
im = np.asarray(Image.open(p).convert("RGB")).astype(float)
h, w, _ = im.shape
corners = np.stack([im[5, 5], im[5, w - 5], im[h - 5, 5], im[h - 5, w - 5]])
bg = corners.mean(0)
print("shape", im.shape, "bg proxy RGB", bg.round(1))
dev = float(np.abs(im - bg).mean())
print("mean abs dev from bg", round(dev, 2))

content = np.abs(im.mean(2) - bg.mean()) > 25
rows = np.where(content.any(1))[0]
cols = np.where(content.any(0))[0]
fill_h = (rows.max() - rows.min()) / h
print("content bbox rows", int(rows.min()), "-", int(rows.max()),
      "cols", int(cols.min()), "-", int(cols.max()),
      "fill_w", round((cols.max() - cols.min()) / w, 2), "fill_h", round(fill_h, 2))

sub = im[content]
green = (sub[:, 1] > sub[:, 0] + 15) & (sub[:, 1] > sub[:, 2] + 15)
green_frac = green.mean()
print(f"green pawn frac = {green_frac:.3f} (count {green.sum()})")

# Checkerboard pattern detection: scan a horizontal line through the board
# floor (just above the pawn's mid-height), measure per-column brightness,
# threshold into dark/light, and count alternations. A real board => many cycles.
scan_y = int(h * 0.78)  # lower board, below pawn head, above front edge
row = im[scan_y].mean(1)  # horizontal profile of brightness
thr = (row.max() + row.min()) / 2
bits = (row > thr).astype(int)
# count transitions (0->1 or 1->0) along the row, excluding near-edges
trans = int(np.sum(bits[1:] != bits[:-1]))
print(f"board scan line @y={scan_y}: brightness min={row.min():.0f} max={row.max():.0f} transitions={trans}")
checker = trans >= 6  # >=3 full dark/light squares each side

ok = dev > 5 and green_frac > 0.05 and fill_h > 0.7 and checker
print("checkerboard transitions>=6:", checker)
print("VERDICT:", "PASS (green pawn + checkerboard pattern, non-blank, full-frame)" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
