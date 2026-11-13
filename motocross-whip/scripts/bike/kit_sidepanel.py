"""Damien's rear side panel graphics (decision 37): both sides' artwork drawn by script, element by element, as on his
real panels (photos 02 and 03 of 2026-11-10, 06 and 07 of 2026-11-12; every element, number and source in
research/detail-ledger/side-panels.md).

python3 kit_sidepanel.py KIT_DIR        writes KIT_DIR/art/sidepanel_L.png and sidepanel_R.png

The artwork keeps the size (2752 x 1536) and template crop of kit.json's side panel entries, so kit_canvas.py maps it
unchanged: left art px (x, y) = template px ((x / K) + 1832, (y / K) + 516 - 27), K = 2752 / 1364, front at the
left. The right side's crop is the left's mirrored (kit.json "mirror_of"), so the right art is the left's geometry
with x -> 2752 - x.

Layers, back to front:
  zones   silver flake at the front (red ink over it lets the flake through), glossy black laminate along the top
          edge and round the number, red glitter at the bottom with black splatter rising into the number's bottom
          edge and red splatter over the silver; on the right side the zones' geometry is mirrored, their flake
          and splatter drawn afresh
  marks   the hole round the panel bolt, the panel's red plastic showing round the intake opening
  words   114 (the front plate's glyphs, Damien's kit), PSALM 91, the official LEATT logo, his name logo
          (the plate's DAMIEN VENTER); traced to vector outlines and filled at 3x supersampling. On the right side
          each sits at the mirrored place and slant but reads normally (its source is not mirrored): the right
          panel is in none of Damien's photos (ledger; question for Damien).
"""
import functools
import os
import sys

import contourpy
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(HERE, "..", ".."))
KIT = os.path.join(PROJECT, "textures", "damien-v1")
LEATT_LOGO = os.path.join(PROJECT, "reference", "leatt-gear",
                          "leatt-logo-red-with-icon_official_leatt-us_1200x848.png")
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"

W, H = 2752, 1536                    # artwork px (kit.json side_panels crop 1364 x 712 + pad 27, x 2.0176)
SS = 3                               # supersampling of vector shapes

# colours (ledger, element table): photos 02/03 (shade), plate.png (white), the official logo file (Leatt red)
BLACK = (13, 13, 15)
WHITE = (247, 247, 245)
# silver flake vinyl (photo 02, shade): a dark base packed with bright flakes; its brightness at 10/35/50/65/90
# percent of the area. Calibrated in linear light through 02's render (ledger "silver flake"): photo 02 has
# p10/p50/p90 = 0.20/0.60/0.98 of the 114's white
SILVER_Q = (8, 11, 18, 70, 250)
SILVER_TINT = (0.99, 1.0, 1.03)
FLAKE = 5                            # px, 1.45 mm (photo 02: speckles about 1.5 photo px)
INK = 0.45                           # red ink over the flake lets the flake through (photo 02: LEATT, splatter)
RED = (198, 22, 30)
PLASTIC_RED = (208, 10, 22)          # kit_canvas.RED: the plastic itself, round the intake opening
LEATT_RED = (233, 0, 41)

# the panel in left art px (template of bike v6, side_panels: tools in the ledger)
INTAKE = [(1745, 520), (1745, 529), (1732, 549), (1715, 565), (1486, 706), (1470, 712), (1453, 712), (1425, 702),
          (1277, 642), (1246, 624), (1248, 614), (1257, 606), (1302, 592), (1412, 572), (1497, 557), (1593, 540),
          (1677, 528), (1732, 520)]
TOP_EDGE = [(800, 470), (900, 516), (1000, 522), (1100, 504), (1200, 486), (1300, 471), (1400, 454), (1500, 437),
            (1600, 421), (1700, 405), (1800, 389), (1900, 371), (2000, 354), (2100, 338), (2200, 319),
            (2300, 286), (2400, 231), (2500, 215), (2600, 223)]
BOLT, HOLE_R = (1346, 1129), 46      # the panel bolt; the decal's hole round it (photo 07: 80 px across)
RIM = 10                             # red plastic left round the intake opening (photos 02, 07)

# measured on photo 07 (affine fit to the panel's corners, 2.2 px rms) unless noted; ledger rows
CUT = [(760, 1100), (1000, 1080), (1150, 1058), (1260, 1040), (1480, 986), (1830, 868), (2064, 774),
       (2120, 900), (2200, 1600)]                                # the number's bottom edge = the red zone's top;
SPLAT_X1 = 2100                      # behind the number the cut drops down cover B's rear edge (black above)
RED_FRONT = [(1225, 975), (1108, 1232)]  # the red zone starts at the black front piece's rear edge (02, 07)
FRONT = [(1262, 1040), (1252, 660), (1246, 624)]                 # the first 1's front edge: silver ahead of it
BAND = 16                            # black below PSALM 91's baseline
BAND_X0 = 990                        # where the black band along the top edge starts (photo 02)
PSALM = dict(text="PSALM 91", x0=1061, x1=1627, y0=623, slope=-0.165, cap=92, margin=18)
NUMBER = [[0.6818, 0.0157, 1066.05], [-0.1061, 0.6176, 170.85]]  # plate.png px -> art px (5 glyph corners)
NUMBER_LINE = 9                      # black keyline round the number
NUMBER_GAP = 6                       # black between the intake's red rim and the number
LEATT = dict(scale=0.314, src=(138, 632), at=(948, 877))         # logo file px: the L's foot -> art
LEATT_LINE = 3                       # the thin light edge round the red logo (photos 03, 07)
NAME = dict(src=(587, 1591), x0=1461, x1=1821, at=(1461, 1172), slope=-0.22)   # plate px: the logo's foot
NAME_LINE = 5


# ---- vector outlines -----------------------------------------------------------------------------------------------

def simplify(P, tol):
    """Douglas-Peucker on an open polyline (N x 2)."""
    keep = np.zeros(len(P), bool)
    keep[[0, -1]] = True
    stack = [(0, len(P) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = P[i], P[j]
        ab = b - a
        n = np.hypot(*ab)
        q = P[i + 1:j] - a
        d = np.abs(ab[0] * q[:, 1] - ab[1] * q[:, 0]) / n if n > 0 else np.hypot(q[:, 0], q[:, 1])
        k = int(np.argmax(d))
        if d[k] > tol:
            keep[i + 1 + k] = True
            stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return P[keep]


def trace(alpha, tol=0.6, smooth=0.8):
    """The outlines (closed rings, source px) of a coverage mask at half coverage."""
    z = ndi.gaussian_filter(np.pad(alpha.astype(float), 2), smooth)
    rings = []
    for line in contourpy.contour_generator(z=z).lines(0.5):
        if len(line) < 8:
            continue
        j = int(np.argmax(((line - line[0]) ** 2).sum(1)))           # split a closed ring for Douglas-Peucker
        r = np.vstack([simplify(line[:j + 1], tol)[:-1], simplify(line[j:], tol)[:-1]])
        rings.append(r - 2.0)
    return rings


def fill(rings, M, shape=(H, W)):
    """Coverage (0..1, art px) of rings (source px) placed by the 2 x 3 affine M; even-odd, SS x SS samples."""
    M = np.asarray(M, float)
    pts = [r @ M[:, :2].T + M[:, 2] for r in rings]
    if not pts:
        return np.zeros(shape, np.float32)
    allp = np.vstack(pts)
    x0, y0 = np.maximum(np.floor(allp.min(0)).astype(int) - 2, 0)
    x1, y1 = np.minimum(np.ceil(allp.max(0)).astype(int) + 3, (shape[1], shape[0]))
    out = np.zeros(shape, np.float32)
    if x1 <= x0 or y1 <= y0:
        return out
    acc = np.zeros(((y1 - y0) * SS, (x1 - x0) * SS), bool)
    for p in pts:
        im = Image.new("1", (acc.shape[1], acc.shape[0]), 0)
        q = (p - (x0, y0)) * SS
        ImageDraw.Draw(im).polygon([tuple(v) for v in q], fill=1)
        acc ^= np.asarray(im, bool)
    out[y0:y1, x0:x1] = acc.reshape(y1 - y0, SS, x1 - x0, SS).mean((1, 3))
    return out


def poly(P, shape=(H, W)):
    """Coverage of one polygon given in art px."""
    return fill([np.asarray(P, float)], [[1, 0, 0], [0, 1, 0]], shape)


def outline(alpha, width):
    """Coverage of alpha grown by width px (a keyline round it)."""
    d = ndi.distance_transform_edt(alpha < 0.5)
    return np.maximum(alpha, np.clip(width + 0.5 - d, 0, 1)).astype(np.float32)


# ---- sources -------------------------------------------------------------------------------------------------------

def _plate():
    return np.asarray(Image.open(os.path.join(KIT, "art", "plate.png")).convert("RGB")).astype(np.int16)


@functools.lru_cache(None)
def number_rings():
    """114 from Damien's front plate artwork (art/plate.png, his approved kit): the three white glyphs, with the
    black keylines between them, as outlines in plate px."""
    a = _plate()
    win = np.zeros(a.shape[:2], bool)
    win[600:1480, 220:1540] = True
    alpha = np.clip((a.min(-1) - 90) / 110.0, 0, 1) * win
    lab, n = ndi.label(alpha > 0.5)
    sz = ndi.sum(alpha > 0.5, lab, range(1, n + 1))
    keep = np.isin(lab, np.argsort(sz)[::-1][:3] + 1)
    alpha = alpha * ndi.binary_dilation(keep, iterations=2)
    return trace(alpha)


@functools.lru_cache(None)
def name_rings():
    """Damien's name logo from the plate artwork: the signature DAMIEN and the italic VENTER (white only)."""
    a = _plate()
    win = np.zeros(a.shape[:2], bool)
    win[1440:1600, 520:1220] = True
    alpha = np.clip((a.min(-1) - 90) / 110.0, 0, 1) * win
    lab, n = ndi.label(alpha > 0.5)
    sz = ndi.sum(alpha > 0.5, lab, range(1, n + 1))
    keep = np.isin(lab, np.nonzero(sz >= 30)[0] + 1)
    return trace(alpha * ndi.binary_dilation(keep, iterations=2))


@functools.lru_cache(None)
def leatt_rings():
    """The official Leatt logo (wordmark and triangle icon) from Leatt's own file, by its alpha."""
    im = Image.open(LEATT_LOGO).convert("RGBA")
    return trace(np.asarray(im)[..., 3] / 255.0)


@functools.lru_cache(None)
def text_rings(text):
    """Words in Inter Display Black, traced at 400 px; returns rings and (left, baseline, right, cap top)."""
    f = ImageFont.truetype(FONT, 400)
    l, t, r, b = f.getbbox(text)
    im = Image.new("L", (r + 40, b + 40), 0)
    ImageDraw.Draw(im).text((20, 20), text, font=f, fill=255)
    cap = f.getbbox(text[0])
    return trace(np.asarray(im) / 255.0), (20 + l, 20 + cap[3], 20 + r, 20 + cap[1])


# ---- placements (source px -> left art px) ---------------------------------------------------------------------------

def top_edge(x):
    P = np.array(TOP_EDGE, float)
    return np.interp(x, P[:, 0], P[:, 1])


def placements():
    """The 2 x 3 affines that put each lettering element on the left panel."""
    out = {"number": np.array(NUMBER, float)}
    _, (l, base, r, top) = text_rings(PSALM["text"])
    sx = (PSALM["x1"] - PSALM["x0"]) / (r - l)
    sy = PSALM["cap"] / (base - top)
    y0 = PSALM["y0"]
    # keep the cap line PSALM["margin"] px under the model's top edge (the seat skirt) all along the words
    for x in (PSALM["x0"], PSALM["x1"]):
        y0 = max(y0, top_edge(x) + PSALM["margin"] + PSALM["cap"] - PSALM["slope"] * (x - PSALM["x0"]))
    # vertical shear along the edge: x' = x0 + sx (x - l); y' = y0 + slope (x' - x0) + sy (y - base)
    out["psalm"] = np.array([[sx, 0, PSALM["x0"] - sx * l],
                             [PSALM["slope"] * sx, sy, y0 - PSALM["slope"] * sx * l - sy * base]])
    s = LEATT["scale"]
    out["leatt"] = np.array([[s, 0, LEATT["at"][0] - s * LEATT["src"][0]],
                             [0, s, LEATT["at"][1] - s * LEATT["src"][1]]])
    s = (NAME["x1"] - NAME["x0"]) / (1154 - 587)                      # plate name logo x 587..1154
    k = NAME["slope"]
    out["name"] = np.array([[s, 0, NAME["at"][0] - s * NAME["src"][0]],
                            [k * s, s, NAME["at"][1] - k * s * NAME["src"][0] - s * NAME["src"][1]]])
    return out


def mirror_place(M, rings):
    """Right side: the element at the mirrored place and slant, its source unmirrored so it reads normally.
    M_right = F M F_src, F: x -> W - x (art), F_src: the source mirrored about its own centre."""
    allp = np.vstack(rings)
    c = (allp[:, 0].min() + allp[:, 0].max()) / 2
    F = np.array([[-1, 0, W], [0, 1, 0], [0, 0, 1]], float)
    Fs = np.array([[-1, 0, 2 * c], [0, 1, 0], [0, 0, 1]], float)
    M3 = np.vstack([M, [0, 0, 1]])
    return (F @ M3 @ Fs)[:2]


# ---- procedural surfaces --------------------------------------------------------------------------------------------

def noise(rng, scale, shape=(H, W)):
    """Smooth value noise (0..1) with features about scale px."""
    small = rng.random((shape[0] // scale + 4, shape[1] // scale + 4))
    z = ndi.zoom(small, scale, order=3, mode="nearest")[:shape[0], :shape[1]]
    return np.clip(z, 0, 1).astype(np.float32)


def fbm(rng, scales, shape=(H, W)):
    tot, acc = 0.0, np.zeros(shape, np.float32)
    for s in scales:
        acc += noise(rng, s, shape) * s ** 0.6
        tot += s ** 0.6
    return acc / tot


def glitter(rng, base, mottle, sparkle, flake):
    """Metal-flake laminate: base colour mottled by flakes about flake px across (3 to 4 px, about 1 mm: 2 texels of
    the side map), a few bright flakes."""
    n = noise(rng, flake)
    m = np.clip((n - 0.5) * 2.6, -1, 1)[..., None] * np.asarray(mottle, np.float32)
    out = np.asarray(base, np.float32) + m
    bright = noise(rng, 3) > 0.83
    out[bright] = out[bright] * 0.4 + np.asarray(sparkle, np.float32) * 0.6
    return out


def flake(rng):
    """Silver metal-flake vinyl as photo 02 shows it in shade: a dark base packed with bright flakes. Smooth noise
    (flakes about FLAKE px, a finer grain on top) mapped through the measured brightness quantiles SILVER_Q.
    Returns the colour and the flake brightness 0..1 (for the red ink printed over it)."""
    n = noise(rng, FLAKE) + 0.35 * noise(rng, 2)
    qn = np.percentile(n[::7, ::7], [0, 10, 35, 50, 65, 90, 100])
    L = np.interp(n, qn, [SILVER_Q[0] * 0.5, *SILVER_Q, min(255, SILVER_Q[-1] + 15)]).astype(np.float32)
    return L[..., None] * np.asarray(SILVER_TINT, np.float32), L / 255.0


def laminate(rng):
    """Glossy black laminate with the faint dark red grunge print seen above the number (photos 02, 06)."""
    out = np.empty((H, W, 3), np.float32)
    out[:] = BLACK
    g = fbm(rng, (90, 30, 10))
    a = np.clip((g - 0.56) * 4.0, 0, 1) * 0.30
    out += a[..., None] * (np.array((72, 14, 16), np.float32) - BLACK)
    return out + (noise(rng, 2)[..., None] - 0.5) * 3


def cut_y(x, cut):
    P = np.array(cut, float)
    o = np.argsort(P[:, 0])
    return np.interp(x, P[o, 0], P[o, 1])


def splatter(rng, cut, n, below, spread, rmax, toward=None, shape=(H, W)):
    """Paint splatter along the cut line: n drops, their distance from the line exponential (spread px), on its
    lower (below=True) or upper side; big drops get small satellites. toward: an x the drops crowd toward (half
    of them within a third of the line's length of it) instead of spreading evenly. Coverage 0..1."""
    xs = np.array(cut, float)[:, 0]
    im = Image.new("L", (shape[1] * SS, shape[0] * SS), 0)
    d = ImageDraw.Draw(im)
    lo, hi = max(xs.min(), 0), min(xs.max(), shape[1])
    for _ in range(n):
        if toward is None:
            x = rng.uniform(lo, hi)
        else:
            x = toward - np.sign(toward - (lo + hi) / 2) * abs(rng.normal(0, (hi - lo) / 2))
            if not lo <= x <= hi:
                continue
        dist = rng.exponential(spread)
        y = cut_y(x, cut) + (dist if below else -dist)
        r = min(1.6 + 3.2 * rng.pareto(2.2), rmax)
        e = rng.uniform(0.7, 1.4)
        d.ellipse([(x - r * e) * SS, (y - r / e) * SS, (x + r * e) * SS, (y + r / e) * SS], fill=255)
        if r > 7:
            for _ in range(rng.integers(2, 7)):
                a, rr = rng.uniform(0, 2 * np.pi), r * rng.uniform(1.3, 2.6)
                q = rng.uniform(0.8, 2.4)
                cx, cy = x + rr * np.cos(a), y + rr * np.sin(a)
                d.ellipse([(cx - q) * SS, (cy - q) * SS, (cx + q) * SS, (cy + q) * SS], fill=255)
    a = np.asarray(im, np.float32) / 255.0
    return a.reshape(shape[0], SS, shape[1], SS).mean((1, 3))


# ---- the panel ------------------------------------------------------------------------------------------------------

def mx(P, side):
    """A left-art point list on the given side (the right side's crop is the left's mirrored)."""
    return [(W - x, y) if side == "right" else (x, y) for x, y in P]


def zones(side, rng):
    """Coverage of the black laminate and of the red zone, and the cut line, on this side."""
    cut = mx(CUT, side)
    c, r = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    xl = W - c if side == "right" else c                                 # left-art x of every pixel
    # black: the band along the top edge from BAND_X0 back, and everything behind the first 1's front edge, down
    # to the cut line
    _, (l, base, rr, top) = text_rings(PSALM["text"])
    M = placements()["psalm"]
    xb = np.arange(BAND_X0, W + 60, 20.0)
    band = np.c_[xb, (M[1, 0] * ((xb - M[0, 2]) / M[0, 0]) + M[1, 1] * base + M[1, 2]) + BAND]
    band = band[band[:, 0] < FRONT[-1][0]]
    P = [(BAND_X0, -60), (W + 60, -60), (W + 60, cut_y(W + 60, CUT))]
    P += [p for p in sorted(CUT, key=lambda q: -q[0]) if p[0] > FRONT[0][0]] + list(FRONT)
    P += [tuple(p) for p in band[::-1]]
    black = poly(mx(P, side))
    # red: below the cut line and behind the black front piece, its edges ragged
    ragged = (fbm(rng, (70, 26, 9)) - 0.5) * 2 * 20
    red = np.clip(r - cut_y(xl, CUT) + ragged + 0.5, 0, 1)
    (ax, ay), (bx, by) = RED_FRONT
    fx = ax + (r - ay) * (bx - ax) / (by - ay)
    behind = np.clip(xl - fx + (fbm(rng, (50, 18, 7)) - 0.5) * 2 * 16 + 0.5, 0, 1)
    return black, (red * behind).astype(np.float32), behind.astype(np.float32), cut


def build(side):
    """The side panel artwork (H x W x 3 uint8) for side 'left' or 'right'."""
    rng = np.random.default_rng(114 if side == "left" else 91)
    black, red, behind, cut = zones(side, rng)
    silver_l, s = flake(rng)
    red_l = glitter(rng, RED, (30, 10, 11), (255, 120, 120), 3)
    black_l = laminate(rng)
    # splatter: black drops into the red under the number, red drops over the silver and the black above it, and a
    # spray of red over the front (photo 07: round the LEATT logo and the intake's front tip)
    line = [p for p in CUT if p[0] <= SPLAT_X1]
    sb = splatter(rng, mx(line, side), 5200, True, 42, 11) * behind
    sr = splatter(rng, mx(line, side), 2600, False, 46, 9)
    front = mx([(820, 780), (1250, 700)], side)
    near = mx([(1250, 0)], side)[0][0]
    sf = (splatter(rng, front, 260, True, 90, 8, toward=near) +
          splatter(rng, front, 120, False, 50, 7, toward=near))
    keep = np.clip(red - sb, 0, 1)
    bk = np.maximum(black, sb)
    spl = np.clip(sr + sf * (1 - black), 0, 1)
    out = silver_l * (1 - bk[..., None]) + black_l * bk[..., None]
    out = out * (1 - keep[..., None]) + red_l * keep[..., None]
    # red ink on the silver: the flake shows through (dark base darker red, bright flakes full red)
    shade = (1 - (1 - bk) * (1 - keep) * INK * (1 - s))[..., None]
    out = out * (1 - spl[..., None]) + red_l * shade * spl[..., None]

    def put(alpha, colour):
        nonlocal out
        out = out * (1 - alpha[..., None]) + np.asarray(colour, np.float32) * alpha[..., None]

    # the hole round the panel bolt: the dark recess shows through
    bx, by = mx([BOLT], side)[0]
    t = np.linspace(0, 2 * np.pi, 96, endpoint=False)
    put(poly(np.c_[bx + HOLE_R * np.cos(t), by + HOLE_R * np.sin(t)]), (8, 8, 9))
    # the intake opening: black inside (the foam), the red plastic round it, black between that and the number
    intake = poly(mx(INTAKE, side))
    din = ndi.distance_transform_edt(intake < 0.5)
    rim = np.clip(RIM + 0.5 - din, 0, 1)
    keep_out = np.clip(RIM + NUMBER_GAP + 0.5 - din, 0, 1)
    # lettering
    P = placements()
    rings = {"number": number_rings(), "psalm": text_rings(PSALM["text"])[0], "leatt": leatt_rings(),
             "name": name_rings()}
    place = {k: (mirror_place(P[k], rings[k]) if side == "right" else P[k]) for k in rings}
    num = fill(rings["number"], place["number"])
    c, r = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    under = np.clip(cut_y(c, cut) - NUMBER_LINE - r + 0.5, 0, 1)                # the number stops at the red
    psalm = fill(rings["psalm"], place["psalm"])
    # and under the band of PSALM 91 as far back as the intake (the 4 rises behind the intake, photos 02, 06, 07)
    xl = W - c if side == "right" else c
    Mp = P["psalm"]
    _, (_, base, _, _) = text_rings(PSALM["text"])
    band_y = Mp[1, 0] * (xl - Mp[0, 2]) / Mp[0, 0] + Mp[1, 1] * base + Mp[1, 2] + BAND
    band = np.clip(band_y + NUMBER_GAP - r + 0.5, 0, 1) * np.clip(INTAKE[0][0] + 15 - xl, 0, 1)
    clear = np.maximum(np.maximum(keep_out, outline(psalm, 14)), band)
    num = num * under * (1 - clear)
    put(np.clip(outline(num, NUMBER_LINE) * (1 - keep_out), 0, 1), BLACK)
    put(num, WHITE)
    put(psalm, WHITE)
    leatt = fill(rings["leatt"], place["leatt"])
    put(outline(leatt, LEATT_LINE), WHITE)
    put(leatt, np.asarray(LEATT_RED, np.float32) * shade)
    name = fill(rings["name"], place["name"])
    put(outline(name, NAME_LINE), BLACK)
    put(name, WHITE)
    put(np.maximum(rim - intake, 0), PLASTIC_RED)
    put(intake, (6, 6, 7))
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def main(kdir=KIT):
    for side, f in (("left", "sidepanel_L.png"), ("right", "sidepanel_R.png")):
        a = build(side)
        os.makedirs(os.path.join(kdir, "art"), exist_ok=True)
        Image.fromarray(a).save(os.path.join(kdir, "art", f), optimize=True)
        print(side, f, a.shape)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else KIT)
