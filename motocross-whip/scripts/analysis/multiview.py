"""Multi-camera attitude measurement: draw the bike and a stick rider at a trial world attitude ON TOP of the
real frames of every phone that filmed the same jump at the same instant (clips 2 and 3 are one jump filmed by
two phones; research/whip-attitude-measured.md). Two lines of sight about 35 deg apart fix the angle a single
camera cannot see (the bike tipping toward or away from it).

Each phone pans with the rider, so the drawing is anchored on the red plastics: the centroid of the drawn red
parts is placed on the centroid of the red pixels in the frame.

python3 multiview.py OUT.jpg [--cams cams.json] SPEC [SPEC ...]
  SPEC = t:drop:yaw:pitch:roll[:rider_yaw:rider_pitch:rider_lean]   (t = s after the lip; angles in degrees,
         same convention as scripts/demo/whip_measured.py; t < 0 draws the bike on the ramp at its known attitude)
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "demo"))
sys.path.insert(0, HERE)
import air                  # noqa: E402
from attitude_overlay import Overlay, attitude, trajectory   # noqa: E402

FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
D = math.radians
RED_PARTS = ("#d01818",)


def red_pixels(img, near=None, radius=120):
    """Centroid and bbox of the bike's red plastics (saturated red; trees, sky and the kit are not red)."""
    a = np.asarray(img).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (r > 130) & (r - g > 60) & (r - b > 45)
    ys, xs = np.nonzero(m)
    if len(xs) < 10:
        return None
    if near is not None:
        k = np.hypot(xs - near[0], ys - near[1]) < radius
        if k.sum() >= 10:
            xs, ys = xs[k], ys[k]
    mx, my = np.median(xs), np.median(ys)
    k = (abs(xs - mx) < 90) & (abs(ys - my) < 90)
    xs, ys = xs[k], ys[k]
    return float(xs.mean()), float(ys.mean()), (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


class View:
    def __init__(self, name, frames_dir, cam, f_px, times, size=(478, 850), hint=None):
        self.name, self.dir, self.cam, self.f = name, frames_dir, np.asarray(cam, float), float(f_px)
        self.times = np.asarray(times, float)          # time after the lip of each frame (frame i at index i-1)
        self.size = size
        self.hint = hint or {}                         # frame -> (x, y) near which to look for red

    def frame_at(self, t):
        i = int(np.argmin(np.abs(self.times - t)))
        return i + 1, float(self.times[i])


def project(cam, look, f, pts, size):
    fwd = look - cam
    fwd = fwd / np.linalg.norm(fwd)
    right = np.cross(fwd, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    W, H = size
    out = []
    for p in pts:
        d = np.asarray(p) - cam
        z = d @ fwd
        out.append((W / 2 + f * (d @ right) / z, H / 2 - f * (d @ up) / z))
    return out


def ground_state(t):
    """Bike CoM and attitude on the ramp at t (< 0) seconds before the lip, from the ground simulation."""
    global _G
    if "_G" not in globals():
        import sim
        pl = sim.Pipeline()
        pl.S.T_face = 1344.4
        t_off, st, sp, rec = pl.to_takeoff(14.873)
        _G = (t_off, rec)
    t_off, rec = _G
    r = min(rec, key=lambda q: abs(q["t"] - (t_off + t)))
    X, Z, beta = r["st"][:3]
    return np.array([X, 0.0, Z]), air.Ry(-beta)


def tile(ov, view, t, RA, RB, pb, scale=3, half=70):
    fr, tf = view.frame_at(t)
    img = Image.open(f"{view.dir}/f_{fr:03d}.png").convert("RGB")
    polys, rider, head = ov.world_points(RA, RB, pb)
    P2 = lambda pts: project(view.cam, pb, view.f, pts, view.size)
    reds = [p for c, w, pts in polys if c in RED_PARTS for p in P2(pts)]
    dc = np.mean(np.array(reds), axis=0)
    rp = red_pixels(img, view.hint.get(fr))
    rc = np.array(rp[:2]) if rp else dc
    off = rc - dc
    x0, y0 = int(rc[0]) - half, int(rc[1]) - half
    crop = img.crop((x0, y0, x0 + 2 * half, y0 + 2 * half)).resize((2 * half * scale, 2 * half * scale), Image.LANCZOS)
    lay = Image.new("RGBA", crop.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(lay)
    T = lambda pts: [((x + off[0] - x0) * scale, (y + off[1] - y0) * scale) for x, y in pts]
    for c, w, pts in rider[:4]:
        dr.line(T(P2(pts)), fill=c + "b0", width=max(2, w * scale // 3))
    for c, w, pts in polys:
        dr.line(T(P2(pts)), fill=c + "c0", width=max(2, w * scale // 3))
    for c, w, pts in rider[4:]:
        dr.line(T(P2(pts)), fill=c + "b0", width=max(2, w * scale // 3))
    hx, hy = T(P2([head]))[0]
    rr = view.f * 0.15 / np.linalg.norm(head - view.cam) * scale
    dr.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], outline="#ffffffd0", width=3)
    out = crop.convert("RGBA")
    out.alpha_composite(lay)
    return out.convert("RGB"), fr, tf


def load_views(path):
    with open(path) as f:
        cfg = json.load(f)
    views = []
    for c in cfg["views"]:
        if "pts_file" in c:
            pts = np.loadtxt(c["pts_file"])
            times = pts - pts[c["lip_frame"] - 1] + c.get("lip_offset", 0.0)
        else:
            n = len(os.listdir(c["dir"]))
            times = (np.arange(1, n + 1) - c["lip_frame"]) / c.get("fps", 30.0) + c.get("lip_offset", 0.0)
        views.append(View(c["name"], c["dir"], c["cam"], c["f"], times,
                          hint={int(k): v for k, v in c.get("hint", {}).items()}))
    return views


def main():
    args = sys.argv[1:]
    cams = os.path.join(HERE, "cams_jump2.json")
    if "--cams" in args:
        i = args.index("--cams")
        cams = args[i + 1]
        del args[i:i + 2]
    out, specs = args[0], args[1:]
    views = load_views(cams)
    ov = Overlay()
    ts, pbs = trajectory()
    font = ImageFont.truetype(FONT, 16)
    cols = []
    for spec in specs:
        v = [float(s) for s in spec.split(":")]
        t = v[0]
        if t < 0:
            pb, RA = ground_state(t)
            RB = RA.copy()
            label = f"t {t:+.2f}  on the ramp"
        else:
            drop, yaw, pitch, roll = v[1:5]
            ry, rp, rl = v[5:8] if len(v) >= 8 else (0.0, 0.0, 0.0)
            RA = attitude(drop, yaw, pitch, roll)
            RB = air.Rz(D(ry)) @ air.Ry(-D(rp)) @ air.Rx(D(rl))
            pb = np.array([np.interp(t, ts, pbs[:, k]) for k in range(3)])
            label = f"t {t:.2f}  d{drop:.0f} y{yaw:.0f} p{pitch:.0f} r{roll:.0f} | {ry:.0f},{rp:.0f},{rl:.0f}"
        tiles = []
        for vw in views:
            im, fr, tf = tile(ov, vw, t, RA, RB, pb)
            d = ImageDraw.Draw(im)
            d.text((6, 4), f"{vw.name} f{fr} ({tf:+.2f}s)", fill="yellow", font=font)
            tiles.append(im)
        col = Image.new("RGB", (tiles[0].width, sum(tl.height for tl in tiles) + 26), (16, 20, 24))
        ImageDraw.Draw(col).text((6, 4), label, fill="white", font=font)
        y = 26
        for tl in tiles:
            col.paste(tl, (0, y))
            y += tl.height
        cols.append(col)
    sheet = Image.new("RGB", (sum(c.width for c in cols) + 4 * len(cols), cols[0].height), (0, 0, 0))
    x = 0
    for c in cols:
        sheet.paste(c, (x, 0))
        x += c.width + 4
    sheet.save(out, quality=88)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
