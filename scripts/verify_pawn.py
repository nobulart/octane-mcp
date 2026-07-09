from PIL import Image
import numpy as np

p = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/green_pawn_preview.png"
im = np.asarray(Image.open(p).convert("RGB")).astype(float)
h, w, _ = im.shape
corners = np.stack([im[5, 5], im[5, w - 5], im[h - 5, 5], im[h - 5, w - 5]])
bg = corners.mean(0)
print("shape", im.shape)
print("bg proxy RGB", bg.round(1))
print("mean abs dev from bg", round(float(np.abs(im - bg).mean()), 2))
gray = im.mean(2)
mask = np.abs(gray - bg.mean()) > 25
rows = np.where(mask.any(1))[0]
if len(rows):
    print("subject rows", int(rows.min()), "-", int(rows.max()), "height_frac", round((rows.max() - rows.min()) / h, 2))
    sub = im[mask]
    green = (sub[:, 1] > sub[:, 0] + 15) & (sub[:, 1] > sub[:, 2] + 15)
    print("green frac in subject", round(float(green.mean()), 3))
else:
    print("NO SUBJECT -> blank")
