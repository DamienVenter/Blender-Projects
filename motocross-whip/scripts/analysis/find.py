"""Find the rider+bike blob (dark or red pixels) in a sky frame. Returns centre and size.
Restrict to a search window (x0,y0,x1,y1) to skip the ground and trees."""
import numpy as np
from PIL import Image
from scipy import ndimage


def blob(path, win=None, prev=None):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    luma = 0.3 * r + 0.59 * g + 0.11 * b
    m = (luma < 110) | ((r - b > 50) & (r > 120)) | ((g - b > 15) & (g > r + 10))
    if win:
        x0, y0, x1, y1 = win
        mm = np.zeros_like(m)
        mm[y0:y1, x0:x1] = m[y0:y1, x0:x1]
        m = mm
    m = ndimage.binary_closing(m, iterations=3)
    lab, n = ndimage.label(m)
    if n == 0:
        return None
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    if prev is not None:   # prefer the blob nearest the previous centre among the big ones
        best, bd = None, 1e9
        for i in np.argsort(sizes)[::-1][:5]:
            ys, xs = np.nonzero(lab == i + 1)
            d = np.hypot(xs.mean() - prev[0], ys.mean() - prev[1])
            if sizes[i] > 60 and d < bd:
                best, bd = i, d
        k = best if best is not None else int(np.argmax(sizes))
    else:
        k = int(np.argmax(sizes))
    ys, xs = np.nonzero(lab == k + 1)
    return (int((xs.min() + xs.max()) / 2), int((ys.min() + ys.max()) / 2),
            int(xs.max() - xs.min()), int(ys.max() - ys.min()))


if __name__ == "__main__":
    import sys
    d, f0, f1, step = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    win = tuple(map(int, sys.argv[5].split(","))) if len(sys.argv) > 5 else None
    prev = None
    for f in range(f0, f1 + 1, step):
        r = blob(f"{d}/f_{f:03d}.png", win, prev)
        print(f, r)
        if r:
            prev = r[:2]
