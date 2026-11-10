"""Damien's livery, version 0.1, painted as textures in bike coordinates (from his photos,
reference/damien-bike-2026-11-10). Text is plain lettering standing in for the sponsor logos; the graphic shapes are
approximate. Phase 3 (kit and bike graphics) replaces this with his real sticker kit.

side_L.png / side_R.png  side projection over x -0.32..1.20 m, z 0.58..1.06 m (shrouds, side panels): the bike's
                         front is at the image's left on the left side and at its right on the right side, so
                         lettering reads normally on both
fender.png               rear fender, top projection
front_fender.png         front fender, top projection
seat.png                 seat cover (GUTS: black ribbed top, red sides), top projection
plate.png                front number plate, plate coordinates
barpad.png               Renthal bar pad
swingarm.png             swingarm wrap (chrome black, PSALM 91), side projection

python3 livery.py OUT_DIR
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = "/usr/share/fonts/opentype/inter"
F_NUM = os.path.join(FONT_DIR, "InterDisplay-BlackItalic.otf")
F_BOLD = os.path.join(FONT_DIR, "Inter-ExtraBold.otf")
F_BLACK = os.path.join(FONT_DIR, "Inter-Black.otf")

RED = (200, 16, 28)            # Honda Extreme Red R292R (research/crf250r-2026.md), sRGB approx
DARK_RED = (120, 8, 14)
WHITE = (245, 245, 245)
BLACK = (14, 14, 16)
GLITTER = (128, 128, 132)

SIDE = dict(x0=-0.32, x1=1.20, z0=0.58, z1=1.06, ppm=2000)     # 2 px per mm
RNG = np.random.default_rng(114)


class SideCanvas:
    def __init__(self, side):
        self.side = side
        W = int((SIDE["x1"] - SIDE["x0"]) * SIDE["ppm"])
        H = int((SIDE["z1"] - SIDE["z0"]) * SIDE["ppm"])
        self.im = Image.new("RGB", (W, H), RED)
        self.d = ImageDraw.Draw(self.im)

    def px(self, x, z):
        c = (SIDE["x1"] - x) if self.side == "L" else (x - SIDE["x0"])
        return c * SIDE["ppm"], (SIDE["z1"] - z) * SIDE["ppm"]

    def poly(self, pts, fill):
        self.d.polygon([self.px(x, z) for x, z in pts], fill=fill)

    def text(self, s, x, z, h, font=F_BOLD, fill=WHITE, angle=0.0, stroke=0, stroke_fill=BLACK, anchor="mm"):
        """Text of cap height ~h metres centred at (x, z), rotated by angle (deg, positive = rising toward the bike's
        front on whichever side is shown)."""
        size = int(h * SIDE["ppm"] * 1.35)
        f = ImageFont.truetype(font, size)
        l, t, r, b = self.d.textbbox((0, 0), s, font=f, stroke_width=stroke)
        tile = Image.new("RGBA", (r - l + 20, b - t + 20), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((10 - l, 10 - t), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        a = angle if self.side == "R" else -angle
        tile = tile.rotate(a, expand=True, resample=Image.BICUBIC)
        cx, cy = self.px(x, z)
        self.im.paste(tile, (int(cx - tile.width / 2), int(cy - tile.height / 2)), tile)


def glitter_layer(size, base=GLITTER):
    """Silver-grey metal flake: base grey with bright and dark specks."""
    W, H = size
    a = np.empty((H, W, 3), np.float32)
    a[:] = base
    n = RNG.normal(0, 14, (H, W, 1)).astype(np.float32)
    a += n
    sp = RNG.random((H, W)) > 0.985
    a[sp] = 235
    sp2 = RNG.random((H, W)) > 0.99
    a[sp2] = 60
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def splatter(c, region_pts, colour, n=260, rmax=0.006):
    """Ink splatter dots inside a polygon (bike coords)."""
    from matplotlib.path import Path
    path = Path(region_pts)
    xs = [p[0] for p in region_pts]; zs = [p[1] for p in region_pts]
    for _ in range(n):
        x, z = RNG.uniform(min(xs), max(xs)), RNG.uniform(min(zs), max(zs))
        if path.contains_point((x, z)):
            r = RNG.uniform(0.0008, rmax) * SIDE["ppm"]
            cx, cy = c.px(x, z)
            c.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)


def paint_side(side, out_dir):
    c = SideCanvas(side)
    # silver-grey flake panel across the shroud's rear, the tank side and the side panel's front (DV photo 2)
    flake = [(1.03, 0.995), (0.62, 1.02), (0.30, 0.995), (0.17, 0.92), (0.30, 0.80), (0.50, 0.74), (0.70, 0.72),
             (0.92, 0.74), (1.02, 0.80)]
    mask = Image.new("L", c.im.size, 0)
    ImageDraw.Draw(mask).polygon([c.px(x, z) for x, z in flake], fill=255)
    c.im.paste(glitter_layer(c.im.size), (0, 0), mask)
    splatter(c, flake, (170, 12, 20), n=420, rmax=0.004)
    splatter(c, flake, BLACK, n=300, rmax=0.003)
    # red lower area of the side panel with black splatter (DV)
    low = [(0.62, 0.78), (0.20, 0.74), (0.02, 0.86), (-0.20, 0.97), (-0.20, 0.70), (0.62, 0.66)]
    splatter(c, low, BLACK, n=500, rmax=0.005)
    # white slashes across the shroud and the side panel (DV)
    for (x0, z0), (x1, z1), w in (((1.00, 0.86), (0.72, 0.985), 0.010), ((0.98, 0.82), (0.66, 0.965), 0.005),
                                  ((0.36, 0.93), (0.10, 0.985), 0.008)):
        d = np.array([x1 - x0, z1 - z0]); n = np.array([-d[1], d[0]]) / np.linalg.norm(d) * w
        c.poly([(x0 - n[0], z0 - n[1]), (x1 - n[0], z1 - n[1]), (x1 + n[0], z1 + n[1]), (x0 + n[0], z0 + n[1])], WHITE)
    # shroud front fin: black with a red swoosh and the stacked sponsors (DV photo 2: LEATT, MOTUL, USN)
    fin = [(1.16, 0.99), (1.06, 0.99), (0.99, 0.66), (1.07, 0.64)]
    c.poly(fin, BLACK)
    c.poly([(1.15, 0.94), (1.09, 0.95), (1.03, 0.70), (1.08, 0.69)], DARK_RED)
    b, t = np.array([1.035, 0.675]), np.array([1.115, 0.975])          # along the fin, bottom to top
    ang = math.degrees(math.atan2(t[1] - b[1], t[0] - b[0]))
    for (word, h), f in ((("USN", 0.022), 0.20), (("MOTUL", 0.018), 0.50), (("LEATT", 0.018), 0.80)):
        x, z = b + (t - b) * f
        c.text(word, x, z, h, font=F_BLACK, angle=ang)
    # number 114 on the side panel, PSALM 91 above, his name below (DV photos 2, 3, 5)
    c.text("114", 0.300, 0.872, 0.105, font=F_NUM, stroke=10, stroke_fill=BLACK)
    c.text("PSALM 91", 0.395, 0.968, 0.017, font=F_BLACK, angle=8)
    c.text("DAMIEN VENTER", 0.245, 0.786, 0.012, font=F_BOLD, angle=8)
    c.im.save(os.path.join(out_dir, f"side_{side}.png"))


def paint_top(name, x0, x1, y0, y1, ppm, draw_fn, out_dir):
    """Top projection texture: image columns along -x (front at the left), rows along y (left side at the top)."""
    W, H = int((x1 - x0) * ppm), int((y1 - y0) * ppm)
    im = Image.new("RGB", (W, H), RED)
    d = ImageDraw.Draw(im)
    px = lambda x, y: ((x1 - x) * ppm, (y1 - y) * ppm)
    draw_fn(im, d, px, ppm)
    im.save(os.path.join(out_dir, name))
    return dict(x0=x0, x1=x1, y0=y0, y1=y1)


def seat_fn(im, d, px, ppm):
    # GUTS cover: black ribbed top section over the front two thirds, red sides and rear (DV photos 2, 4)
    top = [(0.79, 0.030), (0.30, 0.058), (0.30, -0.058), (0.79, -0.030)]
    d.polygon([px(x, y) for x, y in top], fill=BLACK)
    for k in range(14):                                   # red ribs across
        x = 0.74 - k * 0.032
        d.line([px(x, -0.06), px(x - 0.006, 0.0), px(x, 0.06)], fill=RED, width=int(0.006 * ppm))
    for xx, yy in ((0.20, 0.0),):
        pass


def fender_fn(im, d, px, ppm):
    for y in (0.055, -0.055):
        d.line([px(0.10, y * 1.2), px(-0.29, y * 0.25)], fill=WHITE, width=int(0.004 * ppm))
    d.polygon([px(x, y) for x, y in [(0.10, 0.012), (-0.25, 0.006), (-0.25, -0.006), (0.10, -0.012)]], fill=BLACK)


def front_fender_fn(im, d, px, ppm):
    # black swoosh with a white edge and a MOTUL lettering (DV photo 1)
    sw = [(1.70, 0.00), (1.55, 0.06), (1.33, 0.08), (1.25, 0.05), (1.40, 0.02), (1.58, -0.02)]
    d.polygon([px(x, y) for x, y in sw], fill=BLACK)
    d.line([px(x, y) for x, y in sw[:4]], fill=WHITE, width=int(0.004 * ppm))
    f = ImageFont.truetype(F_BLACK, int(0.022 * ppm))
    tx, ty = px(1.45, -0.045)
    d.text((tx, ty), "MOTUL", font=f, fill=WHITE, anchor="mm")


def plate(out_dir):
    """Front plate, plate coordinates: u across (-0.13..0.13 m, image left = bike's right as seen from the front),
    s along the fork (0..0.30 m, image bottom = 0)."""
    ppm = 3000
    W, H = int(0.26 * ppm), int(0.30 * ppm)
    im = Image.new("RGB", (W, H), RED)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_NUM, int(0.115 * ppm))
    d.text((W / 2, H * 0.47), "114", font=f, fill=WHITE, anchor="mm", stroke_width=9, stroke_fill=BLACK)
    f2 = ImageFont.truetype(F_BLACK, int(0.022 * ppm))
    d.rectangle([W * 0.28, H * 0.06, W * 0.72, H * 0.15], fill=BLACK)
    d.text((W / 2, H * 0.105), "LEATT", font=f2, fill=WHITE, anchor="mm")
    f3 = ImageFont.truetype(F_BOLD, int(0.013 * ppm))
    d.text((W / 2, H * 0.80), "DAMIEN VENTER", font=f3, fill=WHITE, anchor="mm")
    im.save(os.path.join(out_dir, "plate.png"))


def barpad(out_dir):
    ppm = 3000
    W, H = int(0.21 * ppm), int(0.05 * ppm)
    im = Image.new("RGB", (W, H), RED)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_BLACK, int(0.014 * ppm))
    d.text((W / 2, H * 0.30), "RENTHAL", font=f, fill=WHITE, anchor="mm")
    d.text((W / 2, H * 0.70), "RENTHAL", font=f, fill=WHITE, anchor="mm")
    im.save(os.path.join(out_dir, "barpad.png"))


def swingarm_wrap(out_dir):
    """Chrome-black wrap on the swingarm with PSALM 91 (DV photos 2, 5): side projection x -0.04..0.60, z 0.29..0.52."""
    ppm = 2000
    W, H = int(0.64 * ppm), int(0.23 * ppm)
    a = np.zeros((H, W, 3), np.float32)
    g = np.linspace(0, 1, H)[:, None]
    a[:] = (30 + 60 * np.exp(-((g - 0.45) / 0.12) ** 2))[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for side in ("L", "R"):
        pass
    f = ImageFont.truetype(F_BLACK, int(0.024 * ppm))
    im_l = im.copy()
    ImageDraw.Draw(im_l).text((int((0.60 - 0.12) * ppm), int((0.52 - 0.355) * ppm)), "PSALM 91", font=f, fill=WHITE,
                              anchor="mm")
    im_l.save(os.path.join(out_dir, "swingarm_L.png"))
    im_r = im.copy()
    ImageDraw.Draw(im_r).text((int((0.12 + 0.04) * ppm), int((0.52 - 0.355) * ppm)), "PSALM 91", font=f, fill=WHITE,
                              anchor="mm")
    im_r.save(os.path.join(out_dir, "swingarm_R.png"))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for s in ("L", "R"):
        paint_side(s, out)
    maps = {"side": SIDE,
            "seat": paint_top("seat.png", 0.08, 0.79, -0.095, 0.095, 2000, seat_fn, out),
            "fender": paint_top("fender.png", -0.31, 0.11, -0.10, 0.10, 2000, fender_fn, out),
            "front_fender": paint_top("front_fender.png", 1.21, 1.71, -0.095, 0.095, 2000, front_fender_fn, out),
            "plate": dict(u0=-0.13, u1=0.13, s0=0.0, s1=0.30),
            "swingarm": dict(x0=-0.04, x1=0.60, z0=0.29, z1=0.52)}
    plate(out)
    barpad(out)
    swingarm_wrap(out)
    json.dump(maps, open(os.path.join(out, "maps.json"), "w"), indent=1)
    print("livery written to", out)


if __name__ == "__main__":
    main()
