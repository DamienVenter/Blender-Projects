"""Template crops of single panels for the kit artwork (see kit_canvas.py): the panel in grey with a black outline,
everything else white, padded to an aspect ratio the image model offers.

python3 kit_crops.py TEMPLATE_DIR SIDE PART ASPECT OUT.png     (ASPECT e.g. 16:9, 4:3, 1:1)
Prints the kit.json entry (crop and pad).
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter


def main():
    tdir, side, part, aspect, out = sys.argv[1:6]
    fr = json.load(open(os.path.join(tdir, "frame.json")))
    pid = np.asarray(Image.open(os.path.join(tdir, f"parts_{side}.png")))
    m = pid == fr["names"].index(part) + 1
    ys, xs = np.nonzero(m)
    u0, v0, u1, v1 = xs.min() - 40, ys.min() - 40, xs.max() + 41, ys.max() + 41
    img = np.full(m.shape + (3,), 255, np.uint8)
    img[m] = (200, 200, 203)
    e = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))) > 0
    img[e] = (20, 20, 22)
    crop = img[v0:v1, u0:u1]
    aw, ah = (int(a) for a in aspect.split(":"))
    w, h = u1 - u0, v1 - v0
    if w / h > aw / ah:
        H = int(round(w * ah / aw)); W = w
    else:
        W = int(round(h * aw / ah)); H = h
    pl, pt = (W - w) // 2, (H - h) // 2
    canvas = np.full((H, W, 3), 255, np.uint8)
    canvas[pt:pt + h, pl:pl + w] = crop
    Image.fromarray(canvas).save(out)
    print(json.dumps(dict(side=side, part=part, crop=[int(u0), int(v0), int(u1), int(v1)], pad=[int(pl), int(pt)],
                          size=[int(W), int(H)])))


if __name__ == "__main__":
    main()
