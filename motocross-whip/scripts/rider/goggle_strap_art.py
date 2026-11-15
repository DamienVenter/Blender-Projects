"""The goggle strap's and adjuster slides' textures (round 9, decision 45), drawn by script. goggle.py's MATERIALS
use them; `python3 goggle_strap_art.py` (or goggle.py --free) writes them into textures/rider.

  PRINT   his Pinata Teal strap's tie-dye, sampled from Leatt's goggle ISO 8026000150 (a CGI render in even light,
          reference/leatt-gear/goggles): per column of the strap the median colour in five bands across (the white
          LEATT and the backdrop left out); each column's distance along the strap from where it leaves the
          outrigger, from the LEATT's own scale (its letters 0.67 of the strap's height, the official wordmark's
          aspect 3.99: 120 mm long) with the perspective taken from the strap's height per column; smoothed over
          4 mm. That is his strap's right side from the outrigger back 150 mm; the left side is the same from its
          own end; past the ISO's view, its last colour (teal-green) to the back.
  WEAVE   Leatt's woven elastic at 1:1 in the MY27 back view (0.214 mm/px along the strap, 0.207 across): knit
          loops about 0.65 x 0.45 mm (the grain is 3 x 2 px), a jacquard repeat of 1.9 mm along (autocorrelation
          peak at 9 px), the albedo spread 15 to 24 % of the mean (luminance sd in the blue body); the woven
          selvedges 5.2 mm (25 of the strap's 217 px at both edges), a diagonal rib (scratch weave_acf.py).
  LOGO    the white LEATT is a raised silicone print (its walls show in the Pinata kit iso-right): 0.8 mm proud.
  SLIDES  the details moulded on the slides' top faces (MY27 back view at 1:1): the left slide's centre bar with
          an embossed LEATT, the right slide's grip tab with Leatt's triangle and a field of dimples.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

REF = os.path.join(HERE, "..", "..", "reference", "leatt-gear", "goggles")
ISO = os.path.join(REF, "goggle-velocity55-iriz_pinatateal-purple78_iso_leatt-us_8026000150_1920.jpg")
ISO_BG = (236.0, 236.0, 236.0)             # Leatt's backdrop
ISO_X_EDGE, ISO_X_FAR = 826, 224           # px: the strap leaves the outrigger's back edge; the last full column
ISO_ROWS = (700, 1150)

STRAP_LEN_UV = 0.645       # m: the built strap's centre line (round 8: 618.8 mm; round 9's hinged outriggers put
                           # its ends 13 mm further forward: 645.0) on the shell; u = s / s_total. The printed
                           # face's centre line, 3.3 mm out, is 648.4 mm (0.5 % longer: the weave tile reads 19.1)
TEX_W, TEX_H = 4096, 384   # texels: 6.6 per mm along, 8.5 across
W_MM = 45.0
ANCHOR_MM = 10.0           # the strap's end lies this far inside the outrigger's back end (goggle.OR_ANCHOR)
PRINT_SIGMA_MM = 4.0
LEATT_H = 0.67             # the ISO's letters: 177 of the strap's 265 px

LOOP_ALONG, LOOP_ACROSS = 0.655, 0.45      # mm (0.65 measured; 29 to the tile)
JACQUARD = 1.9                             # mm
# the weave as a detail tile (round 9): 19 mm along (29 loops, 10 jacquard repeats) by the strap's full width, at 24
# texels a mm, repeated along the strap; at the print's 6.6 texels a mm the renders' grain was 1.5 px wide at 1:1
# against the photo's 0.9 (autocorrelation half widths, scratch acfcmp.py)
TILE_MM = 19.0
TILE_PX_MM = 24.0
MOTTLE_MY27 = 0.75                         # round 9's body albedo spread (sd / mean of the factor); the MY27 back
                                           # photo's 1:1 crops read 0.25 (body) and 0.56 (selvedges) in sRGB luminance
                                           # at the high pass (sd over a 4 px blur); the renders read about half the
                                           # factor's
# Round 10 (decision 48): his strap is the Pinata, so its grain comes from the Pinata kit iso-right (scratch grain.py
# over the strap alone, 1:1: 0.125 to 0.147), the pitch from MY27. Round 9's factor (sd 0.62, 0.15 to 2.2, fibre flecks
# 0.1 mm) put 40 % of the brightest print's texels above an albedo of 1 and read as glitter, brightest on the teal end;
# its loop lattice put rows 0.45 mm apart, 2 px in the Pinata view (Nyquist): moire lines. Both photos' power spectra
# (scratch psd2d.py) show two families of diagonal waves instead: MY27 back 3.48 px (0.745 mm) at 68 and 109 deg to the
# strap (20.5 deg either side of across), the Pinata 2.9 to 3.9 px at 44 and 136 deg (the view foreshortens the strap).
# His tile is those two waves (a crosshatch whose crossings are the pores), nothing finer: band-limited by construction.
WAVE_MM = 0.745            # the waves' period (MY27 back photo, 0.214 mm/px)
WAVE_ALONG = 9             # whole periods of each wave along the 19 mm tile: sin(angle) = 9 * 0.745 / 19, 20.7 deg
                           # from across (measured 20.5)
WAVE_JITTER = (1.0, 0.8)   # rad, mm: the waves' phase wanders by 1 rad over about 0.8 mm (a woven elastic is not a
                           # lattice); the amplitude by 25 % over the same
MOTTLE = 0.35              # the albedo factor's sd over the crosshatch (calibrated: the ledger goggle.md section 12)
ALB_CLIP = (0.35, 1.3)
ALB_CAP = 0.9              # the strap's albedo (linear, per channel) after the weave: no fabric reflects more
# the shader fades the tile by the pixel's footprint on the strap (mm, the view distance times the camera's pixel
# angle over the square root of the view's cosine): the crosshatch (red, green) from full at FADE_FINE[0] to none at
# FADE_FINE[1] (3 to 1.7 px a period), the coarse relief (blue: the loops' clusters, about 1 mm) over FADE_COARSE.
# Cycles has no mip-maps: at whip distance (2.7 mm a pixel) the strap shows the print and its normal map only
FADE_FINE = (0.25, 0.45)
FADE_COARSE = (0.5, 1.0)
FLECK = (0.35, 2.2)                        # the selvedges: a dark ground (0.45) and light flecks on the knit's loop
                                           # tops (+1.5 per sd above the mean), normalised to a mean of 1
SELVEDGE_MM = 5.2
PEBBLE_MM, PEBBLE_W = 0.3, 0.8            # the knit's loops clump in about 1 mm clusters (the photo's 4 to 5 px
                                           # grain): the relief's
EDGE_LOOP = (0.50, 0.38)                   # mm: the selvedges' finer knit (light flecks on navy in the photo)
RIB_MM = TILE_MM / 18 / math.sqrt(2)      # the selvedges' faint diagonal rib: 0.746 mm pitch (18 to the tile)
LOOP_H, RIB_H, LOGO_H = 0.18, 0.10, 0.8    # mm: relief heights for the normal map
EDGE_ROUND_MM = 0.35


def _gauss(a, sig):
    from scipy import ndimage
    return ndimage.gaussian_filter(a, sig)


def iso_print(step=2, bands=5):
    """The ISO's strap: distance d (mm from the outrigger's back edge) per sampled column, the colour per band (top
    band first; nan where the band is all LEATT), and the LEATT's d range."""
    from PIL import Image
    a = np.asarray(Image.open(ISO).convert("RGB")).astype(float)
    xs = np.arange(ISO_X_EDGE, ISO_X_FAR - 1, -1)
    y0s, y1s = [], []
    for x in xs:
        col = a[ISO_ROWS[0]:ISO_ROWS[1], x - 1:x + 2].mean(1)
        ys = np.nonzero(np.linalg.norm(col - ISO_BG, axis=1) > 25)[0]
        y0s.append(ISO_ROWS[0] + ys.min())
        y1s.append(ISO_ROWS[0] + ys.max())
    y0s, y1s = np.array(y0s, float), np.array(y1s, float)
    h = y1s - y0s
    # the LEATT: white columns within the strap
    nwhite = []
    for x, y0, y1 in zip(xs, y0s, y1s):
        seg = a[int(y0) + 4:int(y1) - 3, x]
        nwhite.append(int(((seg.min(1) > 205) & (np.ptp(seg, 1) < 35)).sum()))
    nwhite = np.array(nwhite)
    wx = xs[nwhite > 8]
    xa, xb = wx.min(), wx.max()
    # along scale per column: K * h / 45 px per mm, K from the LEATT's length (letters LEATT_H of the strap)
    import goggle as G
    L_leatt = LEATT_H * W_MM * G.wordmark_aspect()
    inside = (xs >= xa) & (xs <= xb)
    K = float(np.sum(W_MM / h[inside])) / L_leatt
    d = np.r_[0.0, np.cumsum(W_MM / (K * 0.5 * (h[1:] + h[:-1])))]       # xs descend: d grows away from it
    d_leatt = (float(np.interp(xb, xs[::-1], d[::-1])), float(np.interp(xa, xs[::-1], d[::-1])))
    cols = np.full((len(xs), bands, 3), np.nan)
    for k, (x, y0, y1) in enumerate(zip(xs, y0s, y1s)):
        if k % step:
            continue
        for b in range(bands):
            f0, f1 = (b + 0.12) / bands, (b + 0.88) / bands
            seg = a[int(y0 + f0 * (y1 - y0)):int(y0 + f1 * (y1 - y0)), x - 2:x + 3].reshape(-1, 3)
            sat = np.ptp(seg, 1)
            seg = seg[(sat > 40) & ~((seg.min(1) > 200) & (sat < 40))]
            if len(seg) >= 6:
                cols[k, b] = np.median(seg, 0)
    keep = np.isfinite(cols[:, :, 0]).any(1)
    return d[keep], cols[keep], d_leatt, dict(K=K, leatt_px=(int(xa), int(xb)), h_px=(float(h[0]), float(h[-1])))


def print_field(dg):
    """The print's colour at distances dg (mm from where the strap leaves the outrigger) for the five bands (top
    first): the ISO's samples filled across the LEATT along each band, smoothed, held past the ISO's view."""
    d, cols, d_leatt, info = iso_print()
    out = np.zeros((len(dg), cols.shape[1], 3))
    for b in range(cols.shape[1]):
        ok = np.isfinite(cols[:, b, 0])
        for c in range(3):
            out[:, b, c] = np.interp(dg, d[ok], cols[ok, b, c])
    step = dg[1] - dg[0]
    for b in range(out.shape[1]):
        for c in range(3):
            out[:, b, c] = _gauss(out[:, b, c], PRINT_SIGMA_MM / step)
    return out, d_leatt, info


def _gauss_wrap(a, sig):
    """Gaussian blur, periodic along (axis 1: the tile repeats along the strap), reflected across."""
    from scipy import ndimage
    a = ndimage.gaussian_filter1d(a, sig[1] if np.ndim(sig) else sig, axis=1, mode="wrap")
    return ndimage.gaussian_filter1d(a, sig[0] if np.ndim(sig) else sig, axis=0, mode="reflect")


def weave_height(nx, ny, mm_x, mm_y, seed=7, loop=None, spread=0.65, fibre=0.25):
    """Knit loops (texels nx along, ny across; mm per texel mm_x, mm_y; periodic along when nx * mm_x is a whole
    number of loops): impulses on a staggered lattice with random strength (1 +- spread), an elliptical blob each;
    the 1.9 mm jacquard repeat along; fine fibre noise (weight fibre). Zero mean, about unit sd; rows top down.
    loop: (along, across) mm, default the body's."""
    rng = np.random.default_rng(seed)
    imp = np.zeros((ny, nx))
    la, lc = loop if loop else (LOOP_ALONG, LOOP_ACROSS)
    sp = spread
    pa, pc = la / mm_x, lc / mm_y                                # texels
    js = np.arange(int(ny / pc) + 2)
    for j in js:
        y = j * pc + rng.uniform(-0.12, 0.12) * pc                  # knit loops sit irregularly
        off = 0.5 * pa * (j % 2)
        xs_ = np.arange(off, nx - 1e-6, pa)
        xs_ = xs_ + rng.uniform(-0.15, 0.15, len(xs_)) * pa
        yi = int(round(y))
        if 0 <= yi < ny:
            xi = np.round(xs_).astype(int) % nx
            np.add.at(imp[yi], xi, rng.uniform(1.0 - sp, 1.0 + sp, len(xi)))
    hgt = _gauss_wrap(imp, (0.25 * pc, 0.235 * pa))              # each loop a blob a quarter of its pitch wide
    X = (np.arange(nx) + 0.5) * mm_x
    hgt = hgt * (1.0 + 0.15 * np.cos(2 * math.pi * X / JACQUARD))[None, :]
    if fibre:
        hgt = hgt + fibre * _gauss_wrap(rng.normal(size=(ny, nx)), 0.6 * pa / 4.3) * hgt.std() / 0.3
    hgt = (hgt - hgt.mean()) / hgt.std()
    return hgt


def rib_height(nx, ny, mm_x, mm_y, seed=11):
    rng = np.random.default_rng(seed)
    X = (np.arange(nx) + 0.5)[None, :] * mm_x
    Y = (np.arange(ny) + 0.5)[:, None] * mm_y
    r = np.cos(2 * math.pi * (X + Y) / (RIB_MM * math.sqrt(2)))
    r = np.sign(r) * np.abs(r) ** 0.6                                     # flat-topped ribs
    r = r + 0.35 * _gauss_wrap(rng.normal(size=(ny, nx)), 0.7 * 0.15 / mm_x)
    return (r - r.mean()) / r.std()


def normal_map(Hmm, mm_x, mm_y):
    """Tangent-space normals (OpenGL: +x along u, +y along v, i.e. up the image) from heights in mm, rows top
    down."""
    gx = np.gradient(Hmm, mm_x, axis=1)
    gy = -np.gradient(Hmm, mm_y, axis=0)                                 # rows run down, v up
    n = np.stack([-gx, -gy, np.ones_like(Hmm)], -1)
    n /= np.linalg.norm(n, axis=-1)[..., None]
    return np.clip((n * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)


def wordmark_box(nx, ny, x0, y0, w, h, mirror=False):
    """The official wordmark as a float mask (0..1) in an ny x nx image, box (x0, y0, w, h) in texels."""
    from PIL import Image
    import goggle as G
    m = Image.fromarray((G.wordmark_mask() * 255).astype(np.uint8)).resize((int(round(w)), int(round(h))),
                                                                          Image.LANCZOS)
    if mirror:
        m = m.transpose(Image.FLIP_LEFT_RIGHT)
    out = np.zeros((ny, nx))
    xa, ya = int(round(x0)), int(round(y0))
    mm = np.asarray(m, float) / 255.0
    ys, xs = slice(max(ya, 0), min(ya + mm.shape[0], ny)), slice(max(xa, 0), min(xa + mm.shape[1], nx))
    out[ys, xs] = mm[ys.start - ya:ys.stop - ya, xs.start - xa:xs.stop - xa]
    return out


def crosshatch(nx, ny, mm_x, mm_y, seed=5):
    """His strap's weave (round 10): two families of waves WAVE_MM apart, WAVE_ALONG whole periods along the tile
    (periodic), mirrored about the across direction, their phase and amplitude wandering over about a mm. Zero mean,
    unit sd; rows top down. Returns the two waves' sum (the crosshatch, its troughs' crossings the pores) and the
    first wave alone (the selvedges' diagonal rib)."""
    rng = np.random.default_rng(seed)
    X = (np.arange(nx) + 0.5)[None, :] * mm_x
    Y = (np.arange(ny) + 0.5)[:, None] * mm_y
    fa = WAVE_ALONG / TILE_MM                                           # cycles a mm along
    fc = math.sqrt(1.0 / WAVE_MM ** 2 - fa ** 2)                         # ... and across
    sig = (WAVE_JITTER[1] / mm_y, WAVE_JITTER[1] / mm_x)

    def smooth():
        n = _gauss_wrap(rng.normal(size=(ny, nx)), sig)
        return n / n.std()
    w1 = (1 + 0.25 * smooth()) * np.cos(2 * math.pi * (fa * X + fc * Y) + WAVE_JITTER[0] * smooth())
    w2 = (1 + 0.25 * smooth()) * np.cos(2 * math.pi * (-fa * X + fc * Y) + WAVE_JITTER[0] * smooth())
    h = w1 + w2
    return (h - h.mean()) / h.std(), (w1 - w1.mean()) / w1.std()


def weave_fields(style="pinata"):
    """The tile's fine relief (mm), coarse relief (mm), albedo factor, rows top down (see weave_tile), and (mm_x,
    mm_y)."""
    nx, ny = int(round(TILE_MM * TILE_PX_MM)), int(round(W_MM * TILE_PX_MM))
    mm_x, mm_y = TILE_MM / nx, W_MM / ny
    Y = (np.arange(ny) + 0.5) * mm_y                                    # mm from the top edge
    e = np.minimum(Y, W_MM - Y)                                         # mm from the nearer edge
    sel = np.clip((SELVEDGE_MM + 0.2 - e) / 0.4, 0, 1)[:, None]         # 1 in the selvedge, 0.4 mm blend
    rng = np.random.default_rng(3)
    fleck = _gauss_wrap(rng.normal(size=(ny, nx)), 0.09 / mm_x)         # fibre to fibre, 0.1 mm
    fleck /= fleck.std()
    pebble = _gauss_wrap(rng.normal(size=(ny, nx)), PEBBLE_MM / mm_x)  # the loops' clusters (the photo's pebbly grain)
    pebble /= pebble.std()
    hgt = LOOP_H * (1 - sel) + RIB_H * sel
    if style == "my27":
        # round 9's MY27 jacquard (the back-view comparisons only): loops 0.655 x 0.45 mm, fibre flecks in the body,
        # the selvedges' light flecks on a dark ground; up to 2.2 times the print
        wv = weave_height(nx, ny, mm_x, mm_y)
        rb = 0.7 * weave_height(nx, ny, mm_x, mm_y, seed=17, loop=EDGE_LOOP) + \
            0.3 * rib_height(nx, ny, mm_x, mm_y)
        rb /= rb.std()
        wh = (wv + PEBBLE_W * pebble) / math.sqrt(1 + PEBBLE_W ** 2)    # in the relief only: as albedo it read as
        Hmm = hgt * (wh * (1 - sel) + rb * sel)                         # dark blotches the photo does not show
        body = 1 + MOTTLE_MY27 * (0.8 * wv + 0.6 * fleck)
        edge = FLECK[0] + FLECK[1] * np.clip(0.8 * rb + 0.6 * fleck, 0, None)
        edge /= edge.mean()
        alb = np.clip(body * (1 - sel) + edge * sel, 0.15, ALB_MAX)
        Hc = _gauss_wrap(Hmm, (PEBBLE_MM / mm_y, PEBBLE_MM / mm_x))
        return Hmm - Hc, Hc, alb, (mm_x, mm_y)
    # his Pinata (round 10): a sublimation print, one colour through the yarn: the albedo follows the crosshatch only
    # (dark pores where its troughs cross), bounded; the selvedges a single diagonal rib of the same period; the
    # loops' clusters in the coarse relief only
    ch, rib = crosshatch(nx, ny, mm_x, mm_y)
    tex = ch * (1 - sel) + rib * sel
    alb = np.clip(1 + MOTTLE * tex, *ALB_CLIP)
    alb /= alb.mean()
    return hgt * tex, hgt * PEBBLE_W * pebble, alb, (mm_x, mm_y)


def weave_tile(outdir, name="goggle_strap_weave.png", style="pinata"):
    """The weave as a detail tile, TILE_MM along (periodic) by the strap's width, TILE_PX_MM texels a mm, rows top
    down (v 1 at the top edge): red the fine relief (0.5 + mm / WEAVE_RANGE_MM: his crosshatch), green the albedo
    factor / ALB_MAX (its pores), blue the coarse relief (the loops' clusters, as red). The shader fades red and green
    by the pixel's footprint over FADE_FINE, blue over FADE_COARSE (detail_nodes). style "my27": round 9's jacquard
    with the selvedges' light flecks on their dark ground, for the MY27 back-view comparisons (written to a scratch
    folder, not textures/rider)."""
    from PIL import Image
    Hf, Hc, alb, _ = weave_fields(style)
    R = np.clip(0.5 + Hf / WEAVE_RANGE_MM, 0, 1)
    B = np.clip(0.5 + Hc / WEAVE_RANGE_MM, 0, 1)
    rgb = np.stack([R, alb / ALB_MAX, B], -1)
    Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(outdir, name),
                                                                            optimize=True)
    return dict(relief_mm=[round(float(Hf.min()), 3), round(float(Hf.max()), 3)],
                coarse_mm=[round(float(Hc.min()), 3), round(float(Hc.max()), 3)],
                albedo=[round(float(alb.min()), 3), round(float(alb.max()), 3)],
                clipped=round(float(np.mean((R <= 0) | (R >= 1) | (B <= 0) | (B >= 1))), 4))


ALB_MAX = 2.2              # the tile's green: the albedo factor / ALB_MAX
WEAVE_RANGE_MM = 1.4       # the tile's red: 0.5 + relief / WEAVE_RANGE_MM (the bump distance)


def strap_textures(outdir, colour="goggle_strap_print.jpg", normal="goggle_strap_print_n.png",
                   mask="goggle_strap_mask.png", body=None, edge=None, logo=True):
    """The strap's print (colour; the weave's own light and dark are in the tile, weave_tile) and its large relief
    (normal: the selvedges' woven seam, the edges' round-over, the raised LEATT) over its whole length, u = s /
    s_total (left end 0), v across (bottom edge 0); mask: where the weave tile applies (the fabric, not the silicone
    letters). body/edge: plain colours instead of the Pinata print (the MY27 Blue/Red comparison: blue body, navy
    selvedges, no LEATT)."""
    from PIL import Image
    nx, ny = TEX_W, TEX_H
    L = STRAP_LEN_UV * 1000.0
    mm_x, mm_y = L / nx, W_MM / ny
    u = (np.arange(nx) + 0.5) / nx
    d_end = np.minimum(u, 1 - u) * L                                    # mm from the nearer strap end
    dg = np.clip(d_end - ANCHOR_MM, 0, None)                            # from where it leaves the outrigger
    v = 1 - (np.arange(ny) + 0.5) / ny                                  # rows top down: v 1 at the top edge
    Y = (1 - v) * W_MM                                                  # mm from the top edge
    if body is None:
        grid = np.arange(0.0, L / 2 + 1, 1.0)
        F, d_leatt, info = print_field(grid)                            # (n, 5, 3), top band first
        bc = (np.arange(F.shape[1]) + 0.5) / F.shape[1]                 # band centres, from the top (fraction)
        frac = np.clip(Y / W_MM, bc[0], bc[-1])
        Fi = np.stack([np.stack([np.interp(dg, grid, F[:, b, c]) for c in range(3)], -1) for b in range(F.shape[1])],
                      0)                                                # (5, nx, 3)
        # linear across the bands
        bi = np.clip(np.searchsorted(bc, frac) - 1, 0, len(bc) - 2)
        t = ((frac - bc[bi]) / (bc[bi + 1] - bc[bi]))[:, None, None]
        img = Fi[bi] * (1 - t) + Fi[bi + 1] * t                          # (ny, nx, 3)
    else:
        d_leatt, info = None, {}
        img = np.tile(np.asarray(body, float), (ny, nx, 1))
    e = np.minimum(Y, W_MM - Y)                                         # mm from the nearer edge
    sel = np.clip((SELVEDGE_MM + 0.2 - e) / 0.4, 0, 1)[:, None]
    Hmm = np.zeros((ny, nx))
    Hmm = Hmm - 0.04 * np.exp(-((e - SELVEDGE_MM) / 0.15) ** 2)[:, None]   # the woven seam where the edge starts
    Hmm = Hmm - 0.5 * np.clip(1 - e / EDGE_ROUND_MM, 0, 1)[:, None] ** 2    # the edge's round-over
    if edge is not None:
        img = img * (1 - sel[..., None]) + np.asarray(edge, float) * sel[..., None]
    fabric = np.ones((ny, nx))
    if logo and d_leatt is not None:
        # the white LEATT, raised: on each side reading from outside (L away from the goggle on the right side,
        # towards it on the left), letters LEATT_H of the strap, its d range from the ISO
        import goggle as G
        lh = LEATT_H * ny
        lw = lh * G.wordmark_aspect()
        x_right = nx * (1 - (d_leatt[0] + ANCHOR_MM) / L) - lw            # right side: the TT nearest the goggle
        x_left = nx * (d_leatt[0] + ANCHOR_MM) / L                       # left side: the L nearest the goggle
        y0 = (ny - lh) / 2
        mask_ = np.maximum(wordmark_box(nx, ny, x_right, y0, lw, lh), wordmark_box(nx, ny, x_left, y0, lw, lh))
        soft = _gauss(mask_, 0.25 / mm_y)
        Hmm = Hmm * (1 - soft) + LOGO_H * soft
        white = np.array([238.0, 238.0, 240.0])
        img = img * (1 - mask_[..., None]) + white * mask_[..., None]
        fabric = 1 - mask_
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(outdir, colour), quality=92)
    Image.fromarray(normal_map(Hmm, mm_x, mm_y)).save(os.path.join(outdir, normal), optimize=True)
    if mask:
        Image.fromarray(np.clip(fabric * 255 + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(outdir, mask),
                                                                                    optimize=True)
    return dict(d_leatt_mm=None if d_leatt is None else [round(x, 1) for x in d_leatt], **info)


PX_ANGLE_DRIVER = "sw / (lens * rx * pct / 100)"     # rad a pixel: the scene camera's (sensor fit horizontal or auto)


def px_angle_node(nt):
    """A Value node holding the scene camera's angle per pixel (rad), driven (a simple expression: no Python needed
    at render time) by the camera's lens and sensor and the render's width, so it follows a camera that zooms."""
    import bpy
    v = nt.nodes.new("ShaderNodeValue")
    v.name = v.label = "px_angle"
    sc = bpy.context.scene
    cam = sc.camera.data if sc.camera and sc.camera.type == "CAMERA" else None
    v.outputs[0].default_value = (cam.sensor_width / (cam.lens * sc.render.resolution_x *
                                                       sc.render.resolution_percentage / 100.0)) if cam else 36.0 / (50.0 * 3840)
    drv = v.outputs[0].driver_add("default_value").driver
    drv.type = "SCRIPTED"
    for name, path in (("sw", "camera.data.sensor_width"), ("lens", "camera.data.lens"),
                       ("rx", "render.resolution_x"), ("pct", "render.resolution_percentage")):
        var = drv.variables.new()
        var.name, var.type = name, "SINGLE_PROP"
        var.targets[0].id_type = "SCENE"
        var.targets[0].id = sc
        var.targets[0].data_path = path
    drv.expression = PX_ANGLE_DRIVER
    return v


def footprint_fades(nt):
    """Node outputs (fine, coarse): 1 where the weave's crosshatch (the loops' clusters) is resolved, 0 where the
    pixel's footprint on the strap is too big for it (FADE_FINE, FADE_COARSE, mm). Footprint: the view distance times
    the pixel's angle, over the square root of the cosine between the view and the normal (floor 0.2)."""
    cd, geo = nt.nodes.new("ShaderNodeCameraData"), nt.nodes.new("ShaderNodeNewGeometry")
    pa = px_angle_node(nt)
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    nt.links.new(cd.outputs["View Distance"], m1.inputs[0])
    nt.links.new(pa.outputs[0], m1.inputs[1])
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Incoming"], dot.inputs[0])
    nt.links.new(geo.outputs["Normal"], dot.inputs[1])
    ab, fl, sq, fp = (nt.nodes.new("ShaderNodeMath") for _ in range(4))
    ab.operation, fl.operation, sq.operation, fp.operation = "ABSOLUTE", "MAXIMUM", "SQRT", "DIVIDE"
    fl.inputs[1].default_value = 0.2
    nt.links.new(dot.outputs["Value"], ab.inputs[0])
    nt.links.new(ab.outputs[0], fl.inputs[0])
    nt.links.new(fl.outputs[0], sq.inputs[0])
    nt.links.new(m1.outputs[0], fp.inputs[0])
    nt.links.new(sq.outputs[0], fp.inputs[1])
    out = []
    for lo, hi in (FADE_FINE, FADE_COARSE):
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.clamp = True
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = lo / 1000.0, hi / 1000.0
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
        nt.links.new(fp.outputs[0], mr.inputs["Value"])
        out.append(mr.outputs["Result"])
    return out


def detail_nodes(nt, p, spec, texdir, base=None, normal=None):
    """Shader nodes for a material's weave tile (spec["detail"]: image, repeat (u, v), mask): the tile's
    albedo factor multiplies the base colour where the mask is white, its relief bumps the normal (after the
    material's own normal map). base, normal: the sockets feeding the Principled's Base Color and Normal (or None).
    Round 10: both fade by the pixel's footprint (footprint_fades: the fine crosshatch in red and green, the coarse
    relief in blue), the albedo is capped at ALB_CAP and the relief is kept off the silicone LEATT (the mask).
    Used by goggle_views.py and build_rider.py (Blender only)."""
    d = spec["detail"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (d["repeat"][0], d["repeat"][1], 1.0)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage")
    import bpy
    t.image = bpy.data.images.load(os.path.join(texdir, d["image"]))
    t.image.colorspace_settings.name = "Non-Color"
    t.interpolation = "Cubic"
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    sp = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(t.outputs["Color"], sp.inputs["Color"])
    wf, wc = footprint_fades(nt)
    # albedo factor 1 + wf (green * ALB_MAX - 1); height 0.5 + wf (red - 0.5) + wc (blue - 0.5)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY_ADD"
    mul.inputs[1].default_value, mul.inputs[2].default_value = ALB_MAX, -1.0
    nt.links.new(sp.outputs["Green"], mul.inputs[0])
    af = nt.nodes.new("ShaderNodeMath")
    af.operation = "MULTIPLY_ADD"
    af.inputs[2].default_value = 1.0
    nt.links.new(mul.outputs[0], af.inputs[0])
    nt.links.new(wf, af.inputs[1])
    hs = []
    for ch, w in (("Red", wf), ("Blue", wc)):
        c = nt.nodes.new("ShaderNodeMath")
        c.operation = "SUBTRACT"
        c.inputs[1].default_value = 0.5
        nt.links.new(sp.outputs[ch], c.inputs[0])
        m = nt.nodes.new("ShaderNodeMath")
        m.operation = "MULTIPLY"
        nt.links.new(c.outputs[0], m.inputs[0])
        nt.links.new(w, m.inputs[1])
        hs.append(m)
    hsum = nt.nodes.new("ShaderNodeMath")
    hsum.operation = "ADD"
    nt.links.new(hs[0].outputs[0], hsum.inputs[0])
    nt.links.new(hs[1].outputs[0], hsum.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mk = None
    if d.get("mask"):
        mk = nt.nodes.new("ShaderNodeTexImage")
        mk.image = bpy.data.images.load(os.path.join(texdir, d["mask"]))
        mk.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mk.outputs["Color"], mix.inputs["Factor"])
    else:
        mix.inputs["Factor"].default_value = 1.0
    if base is not None:
        nt.links.new(base, mix.inputs["A"])
    else:
        mix.inputs["A"].default_value = p.inputs["Base Color"].default_value
    nt.links.new(af.outputs[0], mix.inputs["B"])
    # round 10: no channel above ALB_CAP (round 9's factor up to 2.2 times the print made albedos above 1: glitter)
    cap = nt.nodes.new("ShaderNodeVectorMath")
    cap.operation = "MINIMUM"
    cap.inputs[1].default_value = (ALB_CAP, ALB_CAP, ALB_CAP)
    nt.links.new(mix.outputs["Result"], cap.inputs[0])
    nt.links.new(cap.outputs["Vector"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Distance"].default_value = WEAVE_RANGE_MM / 1000.0
    bp.inputs["Strength"].default_value = d.get("bump_strength", 1.0)
    if mk is not None:                             # round 10: the knit's relief only on the fabric, not the silicone LEATT
        bs = nt.nodes.new("ShaderNodeMath")
        bs.operation = "MULTIPLY"
        bs.inputs[1].default_value = d.get("bump_strength", 1.0)
        nt.links.new(mk.outputs["Color"], bs.inputs[0])
        nt.links.new(bs.outputs[0], bp.inputs["Strength"])
    nt.links.new(hsum.outputs[0], bp.inputs["Height"])
    if normal is not None:
        nt.links.new(normal, bp.inputs["Normal"])
    nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])


# ---------------------------------------------------------------- the slides' moulded details
SLIDE_TEX = (1024, 704)          # px: two halves (left slide, right slide), each 40 x 56 mm of the slide's (a, b)
SLIDE_TEX_MM = (40.0, 56.0)


def slide_uv(a, b, right):
    """Texture coordinates of slide-local (a along the strap, b across; m) on the left or right half."""
    u = (a * 1000.0 + SLIDE_TEX_MM[0] / 2) / SLIDE_TEX_MM[0]
    return 0.5 * (u + (1.0 if right else 0.0)), (b * 1000.0 + SLIDE_TEX_MM[1] / 2) / SLIDE_TEX_MM[1]


def slide_texture(outdir, name="goggle_slide_n.png", leatt=None, tab=None):
    """The slides' details as a normal map: leatt = (a_c, b_c, length, height) of the left slide's embossed LEATT
    (reading along +b, letter tops towards -a); tab = dict(tri=[(a, b) x 3], groove=b, dots=[(a, b)...], r) of the
    right slide's grip (mm). Raised 0.25 mm (letters, the triangle's rim), dimples 0.25 mm deep."""
    from PIL import Image
    nx, ny = SLIDE_TEX
    half = nx // 2
    mm_x, mm_y = SLIDE_TEX_MM[0] / half, SLIDE_TEX_MM[1] / ny
    Hmm = np.zeros((ny, nx))
    A = ((np.arange(half) + 0.5) * mm_x - SLIDE_TEX_MM[0] / 2)[None, :]
    B = (SLIDE_TEX_MM[1] / 2 - (np.arange(ny) + 0.5) * mm_y)[:, None]       # rows top down: b up
    if leatt is not None:
        ac, bc, ln, ht = leatt
        import goggle as G
        from PIL import Image as I_
        m = G.wordmark_mask()
        mi = I_.fromarray((m * 255).astype(np.uint8)).rotate(90, expand=True)   # reads upwards, tops to the left
        w_px, h_px = int(round(ht / mm_x)), int(round(ln / mm_y))
        mi = np.asarray(mi.resize((w_px, h_px), I_.LANCZOS), float) / 255.0
        x0 = int(round((ac - ht / 2 + SLIDE_TEX_MM[0] / 2) / mm_x))
        y0 = int(round((SLIDE_TEX_MM[1] / 2 - bc - ln / 2) / mm_y))
        Hmm[y0:y0 + h_px, x0:x0 + w_px] = np.maximum(Hmm[y0:y0 + h_px, x0:x0 + w_px], 0.25 * mi)
    if tab is not None:
        R = np.zeros((ny, half))
        from matplotlib.path import Path
        P = np.c_[np.broadcast_to(A, (ny, half)).ravel(), np.broadcast_to(B, (ny, half)).ravel()]
        tri = np.asarray(tab["tri"], float)
        c = tri.mean(0)
        outer = Path(tri).contains_points(P).reshape(ny, half)
        inner = Path(c + (tri - c) * tab.get("rim", 0.62)).contains_points(P).reshape(ny, half)
        R += 0.25 * (outer & ~inner) - 0.08 * inner
        R -= 0.12 * np.exp(-((B - tab["groove"]) / 0.3) ** 2) * ((A > tab["a_range"][0]) & (A < tab["a_range"][1]))
        for (da, db) in tab["dots"]:
            R -= 0.25 * np.exp(-(((A - da) ** 2 + (B - db) ** 2) / (tab["r"] ** 2)) ** 1.5)
        Hmm[:, half:] += _gauss(R, 0.6)
    if leatt is not None:
        Hmm[:, :half] = _gauss(Hmm[:, :half], 0.6)
    Image.fromarray(normal_map(Hmm, mm_x, mm_y)).save(os.path.join(outdir, name), optimize=True)


if __name__ == "__main__":
    import goggle as G
    os.makedirs(G.TEXDIR, exist_ok=True)
    print(G.write_strap_textures())
