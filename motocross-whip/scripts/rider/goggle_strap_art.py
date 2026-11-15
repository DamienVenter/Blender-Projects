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
MOTTLE = 0.75                              # the body's albedo spread (sd / mean of the factor); the MY27 back photo's
                                           # 1:1 crops read 0.25 (body) and 0.56 (selvedges) in sRGB luminance at the
                                           # high pass (sd over a 4 px blur); the renders read about half the factor's
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


def weave_height(nx, ny, mm_x, mm_y, seed=7, loop=None):
    """Knit loops (texels nx along, ny across; mm per texel mm_x, mm_y; periodic along when nx * mm_x is a whole
    number of loops): impulses on a staggered lattice with random strength, an elliptical blob each; the 1.9 mm
    jacquard repeat along; fine fibre noise. Zero mean, about unit sd; rows top down. loop: (along, across) mm,
    default the body's."""
    rng = np.random.default_rng(seed)
    imp = np.zeros((ny, nx))
    la, lc = loop if loop else (LOOP_ALONG, LOOP_ACROSS)
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
            np.add.at(imp[yi], xi, rng.uniform(0.35, 1.65, len(xi)))
    hgt = _gauss_wrap(imp, (0.25 * pc, 0.235 * pa))              # each loop a blob a quarter of its pitch wide
    X = (np.arange(nx) + 0.5) * mm_x
    hgt = hgt * (1.0 + 0.15 * np.cos(2 * math.pi * X / JACQUARD))[None, :]
    hgt = hgt + 0.25 * _gauss_wrap(rng.normal(size=(ny, nx)), 0.6 * pa / 4.3) * hgt.std() / 0.3
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


def weave_tile(outdir, name="goggle_strap_weave.png"):
    """The weave as a detail tile, TILE_MM along (periodic) by the strap's width, TILE_PX_MM texels a mm, rows top
    down (v 1 at the top edge): red the relief (0.5 + mm / WEAVE_RANGE_MM), green the albedo factor / ALB_MAX (the
    knit's light loop tops and dark gaps, and the selvedges' light flecks on their dark ground)."""
    from PIL import Image
    nx, ny = int(round(TILE_MM * TILE_PX_MM)), int(round(W_MM * TILE_PX_MM))
    mm_x, mm_y = TILE_MM / nx, W_MM / ny
    Y = (np.arange(ny) + 0.5) * mm_y                                    # mm from the top edge
    wv = weave_height(nx, ny, mm_x, mm_y)
    rb = 0.7 * weave_height(nx, ny, mm_x, mm_y, seed=17, loop=EDGE_LOOP) + 0.3 * rib_height(nx, ny, mm_x, mm_y)
    rb /= rb.std()
    e = np.minimum(Y, W_MM - Y)                                         # mm from the nearer edge
    sel = np.clip((SELVEDGE_MM + 0.2 - e) / 0.4, 0, 1)[:, None]         # 1 in the selvedge, 0.4 mm blend
    tex = wv * (1 - sel) + rb * sel
    Hmm = (LOOP_H * (1 - sel) + RIB_H * sel) * tex
    rng = np.random.default_rng(3)
    fleck = _gauss_wrap(rng.normal(size=(ny, nx)), 0.09 / mm_x)         # fibre to fibre, 0.1 mm
    fleck /= fleck.std()
    pebble = _gauss_wrap(rng.normal(size=(ny, nx)), PEBBLE_MM / mm_x)  # the loops' clusters (the photo's pebbly grain)
    pebble /= pebble.std()
    wh = (wv + PEBBLE_W * pebble) / math.sqrt(1 + PEBBLE_W ** 2)        # in the relief only: as albedo it read as
    Hmm = (LOOP_H * (1 - sel) + RIB_H * sel) * (wh * (1 - sel) + rb * sel)  # dark blotches the photo does not show
    body = 1 + MOTTLE * (0.8 * wv + 0.6 * fleck)
    ef = 0.8 * rb + 0.6 * fleck
    edge = FLECK[0] + FLECK[1] * np.clip(ef, 0, None)
    edge /= edge.mean()
    alb = np.clip(body * (1 - sel) + edge * sel, 0.15, ALB_MAX)
    R = np.clip(0.5 + Hmm / WEAVE_RANGE_MM, 0, 1)
    rgb = np.stack([R, alb / ALB_MAX, np.zeros_like(R)], -1)
    Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(outdir, name),
                                                                            optimize=True)
    return dict(relief_mm=[round(float(Hmm.min()), 3), round(float(Hmm.max()), 3)],
                clipped=round(float(np.mean((R <= 0) | (R >= 1))), 4))


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


def detail_nodes(nt, p, spec, texdir, base=None, normal=None):
    """Shader nodes for a material's weave tile (spec["detail"]: image, repeat (u, v), mask): the tile's
    albedo factor multiplies the base colour where the mask is white, its relief bumps the normal (after the
    material's own normal map). base, normal: the sockets feeding the Principled's Base Color and Normal (or None).
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
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = ALB_MAX
    nt.links.new(sp.outputs["Green"], mul.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
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
    nt.links.new(mul.outputs[0], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Distance"].default_value = WEAVE_RANGE_MM / 1000.0
    bp.inputs["Strength"].default_value = d.get("bump_strength", 1.0)
    nt.links.new(sp.outputs["Red"], bp.inputs["Height"])
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
