"""Bike centre and extent per frame from the red plastics: robust bbox (2..98 percentile) of saturated red pixels
within a window that follows the bike. prints json {frame: [cx, cy, w, h, n]}"""
import sys, json, numpy as np
from PIL import Image
d, f0, f1, sx, sy, ymax = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6])
prev = np.array([sx, sy]); out = {}
for f in range(f0, f1 + 1):
    a = np.asarray(Image.open(f"{d}/f_{f:03d}.png").convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (r > 110) & (r - g > 45) & (r - b > 30)
    m[ymax:] = False
    ys, xs = np.nonzero(m)
    k = np.hypot(xs - prev[0], ys - prev[1]) < 200
    if k.sum() >= 12:
        xs, ys = xs[k], ys[k]
        x0, x1 = np.percentile(xs, [2, 98]); y0, y1 = np.percentile(ys, [2, 98])
        c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        out[f] = [int(c[0]), int(c[1]), int(x1 - x0), int(y1 - y0), int(k.sum())]
        prev = c
    else:
        out[f] = [int(prev[0]), int(prev[1]), 0, 0, 0]
print(json.dumps(out))
