import sys
from PIL import Image
import colorsys, collections

PNG = sys.argv[1]
im = Image.open(PNG).convert("RGB")
px = list(im.getdata())
hue_bucket = collections.Counter()
sat = 0
n = len(px)
for r, g, b in px:
    mx = max(r, g, b) / 255.0
    mn = min(r, g, b) / 255.0
    s = (mx - mn) if mx > 0 else 0
    if s > 0.25 and mx > 0.15:
        hue = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)[0]
        hue_bucket[int(hue * 12) % 12] += 1
        sat += 1
print(f"pixels={n} saturated={sat} ({100*sat/n:.1f}%)")
print("hue buckets (0=red .. 11=magenta):", dict(sorted(hue_bucket.items())))
distinct = sum(1 for c in hue_bucket.values() if c > n * 0.01)
print("distinct dominant hues (>1% of image):", distinct)
