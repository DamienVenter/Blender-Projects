"""Class runs along rows or columns of a studio photo: the numbers behind every "FRONT rows 900..1000" note.

python3 rowscan.py VIEW rows|cols START STOP STEP [LO HI]
  e.g. python3 rowscan.py front rows 560 1060 20 1500 2500
Prints, for each row (or column), the runs of each class with their pixel range:
  R red plastic   G gold (fork tubes)   K dark (rubber, black plastic)   o anything else   (white background skipped)
Convert pixels to metres with cams.CAMS[VIEW].on_plane(u, v, axis, value). Never read numbers off a scaled picture.
Gold fork tubes reflect the red plastics: an R run next to a G run on a tube is a reflection, not plastic.
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams                                             # noqa: E402


def classes(view):
    a = np.asarray(Image.open(os.path.join(HERE, "..", "..", "reference", "crf250r-2026", cams.FILES[view]))
                   .convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 105) & (r - g > 55) & (r - b > 45)
    cls = np.full(r.shape, "o")
    cls[a.min(axis=2) > 235] = "."
    cls[(~red) & (r > 110) & (r - b > 30) & (g - b > 12) & (r - g < 60)] = "G"
    cls[red] = "R"
    cls[a.max(axis=2) < 70] = "K"
    return cls


def runs(line, lo, minlen=5):
    out, s = [], 0
    for i in range(1, len(line) + 1):
        if i == len(line) or line[i] != line[s]:
            if i - s >= minlen and line[s] != ".":
                out.append(f"{line[s]}{lo + s}-{lo + i - 1}")
            s = i
    return out


if __name__ == "__main__":
    view, mode = sys.argv[1], sys.argv[2]
    start, stop, step = map(int, sys.argv[3:6])
    lo, hi = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (0, 4000 if mode == "rows" else 2250)
    cls = classes(view)
    for k in range(start, stop, step):
        line = cls[k, lo:hi] if mode == "rows" else cls[lo:hi, k]
        print(k, " ".join(runs(line, lo)))
