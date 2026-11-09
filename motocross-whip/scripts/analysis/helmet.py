"""Track Damien's white helmet frame by frame in one phone clip, relative to the bike's red plastics.

The helmet is the largest round white blob at the head end of the body (the boots and jersey patches are white
too, so the search follows the previous frame's helmet). Seeded by eye on the lip frame.

python3 helmet.py FRAMES_DIR BOX.json F0 F1 SEED_DX SEED_DY R_PX OUT.json [SHEET.jpg]
  BOX.json: red plastics bbox centres per frame (bikebox.py); SEED: helmet offset from that centre on frame F0 (px);
  R_PX: expected helmet radius in px. Writes {frame: [dx, dy, area_px, ok]} (offset of the helmet centre from the
  red bbox centre).
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def white_mask(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    return (mn > 165) & (mx - mn < 50)


def main():
    d, box, f0, f1 = sys.argv[1], json.load(open(sys.argv[2])), int(sys.argv[3]), int(sys.argv[4])
    seed = np.array([float(sys.argv[5]), float(sys.argv[6])])
    rpx, out_path = float(sys.argv[7]), sys.argv[8]
    sheet_path = sys.argv[9] if len(sys.argv) > 9 else None
    prev, vel = seed.copy(), np.zeros(2)
    out, tiles = {}, []
    for f in range(f0, f1 + 1):
        cx, cy = box[str(f)][:2]
        a = np.asarray(Image.open(f"{d}/f_{f:03d}.png").convert("RGB")).astype(int)
        m = white_mask(a)
        m = ndimage.binary_opening(m, iterations=1)
        lab, n = ndimage.label(m)
        pred = prev + vel
        best, best_s = None, 1e9
        for k in range(1, n + 1):
            ys, xs = np.nonzero(lab == k)
            if len(xs) < 0.2 * np.pi * rpx ** 2 or len(xs) > 4.0 * np.pi * rpx ** 2:
                continue
            c = np.array([xs.mean() - cx, ys.mean() - cy])
            dist = np.linalg.norm(c - pred)
            if dist > 5.0 * rpx:
                continue
            s = dist / rpx + abs(np.log(len(xs) / (np.pi * rpx ** 2)))
            if s < best_s:
                best, best_s = (c, len(xs)), s
        if best is None:                     # not found: hold the last fix (no drift), flag the frame
            out[f] = [float(prev[0]), float(prev[1]), 0, 0]
            c = prev
            vel = np.zeros(2)
        else:
            c = best[0]
            vel = 0.5 * vel + 0.5 * (c - prev) if f > f0 else vel
            out[f] = [float(c[0]), float(c[1]), int(best[1]), 1]
        prev = c
        if sheet_path:
            h = int(9 * rpx)
            im = Image.fromarray(a.astype(np.uint8)).crop((cx - h, cy - h, cx + h, cy + h)).resize((240, 240))
            dr = ImageDraw.Draw(im)
            s_ = 240 / (2 * h)
            px, py = (c[0] + h) * s_, (c[1] + h) * s_
            col = "lime" if out[f][3] else "red"
            dr.ellipse([px - rpx * s_, py - rpx * s_, px + rpx * s_, py + rpx * s_], outline=col, width=2)
            dr.line([(120 - 5, 120), (120 + 5, 120)], fill="yellow"); dr.line([(120, 115), (120, 125)], fill="yellow")
            dr.text((3, 2), f"f{f}", fill="yellow")
            tiles.append(im)
    json.dump(out, open(out_path, "w"))
    if sheet_path:
        cols = 12
        rows = (len(tiles) + cols - 1) // cols
        sh = Image.new("RGB", (240 * cols, 240 * rows))
        for i, t in enumerate(tiles):
            sh.paste(t, ((i % cols) * 240, (i // cols) * 240))
        sh.save(sheet_path, quality=88)
    print(sum(v[3] for v in out.values()), "of", len(out), "frames found")


if __name__ == "__main__":
    main()
