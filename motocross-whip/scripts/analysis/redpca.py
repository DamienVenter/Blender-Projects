"""Shape of the red plastics per frame: principal-axis angle (deg, image y up, mod 180), elongation (minor/major
std), extents. json {frame: [angle, elong, sd_major_px, n]}"""
import sys, json, numpy as np
from PIL import Image
d, boxf = sys.argv[1], sys.argv[2]
box = json.load(open(boxf)); out = {}
for k, (cx, cy, w, h, n) in box.items():
    if n < 15: continue
    a = np.asarray(Image.open(f"{d}/f_{int(k):03d}.png").convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (r > 110) & (r - g > 45) & (r - b > 30)
    ys, xs = np.nonzero(m)
    s = np.hypot(xs - cx, ys - cy) < max(w, h) * 0.75 + 15
    xs, ys = xs[s].astype(float), -ys[s].astype(float)
    P = np.stack([xs - xs.mean(), ys - ys.mean()]); C = P @ P.T / P.shape[1]
    ev, evec = np.linalg.eigh(C)
    v = evec[:, 1]; ang = np.degrees(np.arctan2(v[1], v[0])) % 180
    out[k] = [round(float(ang), 1), round(float(np.sqrt(ev[0] / ev[1])), 3), round(float(np.sqrt(ev[1])), 1), int(s.sum())]
print(json.dumps(out))
