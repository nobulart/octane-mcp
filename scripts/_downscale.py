from PIL import Image
import sys
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
print("dims:", im.size)
im.resize((810, 810)).save(dst, "JPEG", quality=88)
print("saved", dst)
