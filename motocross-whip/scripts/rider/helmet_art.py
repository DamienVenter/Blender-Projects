"""The Pinata Teal graphics of Damien's Leatt Moto 8.5, redrawn as flat print in the shell's UV atlas.

python3 helmet_art.py trace     (once, needs Leatt's photos: writes helmet_art.json, helmet_art_field.png and
                                 helmet_art_stripe.png)
python3 helmet_art.py draw      (writes textures/rider/helmet_pinata.png from those two files; helmet.py calls it)

Why: projecting Leatt's studio photos onto the shell (helmet.paint_atlas) carried their lighting into the texture
(white reflections, soft studio shading, doubled edges where two views disagree), so the shell rendered glassy and
smeared. Here the photos are only used to MEASURE the print, never copied into the texture:

trace  1. every atlas texel is a point on the shell (helmet.atlas_uvs, rasterize); its DESIGN POINT is the same point
          on his left half (|x|, y, z): the Pinata art is mirror-symmetric (Leatt iso-left against iso-right), words
          excepted (drawn afterwards, reading right on each side)
       2. each design point is looked up in the views that see it (Leatt's four Pinata photos through the cameras
          solved with Leatt's other photos, helmet.PRINT_CAMS; the right side's photo mirrored); ONE view owns each
          texel (the most square-on one, smoothed; round the rear lower pieces the back view, BACK_ZONE), so no two
          misregistered views are blended
       3. lighting out: the studio shading of each view is fitted on the white base as a smooth function of the
          shell's normal (second-order spherical harmonics, robust) and divided out; studio reflections (pixels
          brighter than any print, and the hand-marked reflections in HIGHLIGHTS) are cut and filled from their
          own print region
       4. the de-lit colours are classed into the print's inks (white, black, purple, magenta, iridescent, teal),
          the class maps smoothed (1 mm) and vectorised (contours at half level, simplified): polygons per island
       5. inside each coloured region the colour is a smooth field (normalised Gaussian within the region, so edges
          between inks stay crisp); a region whose field barely varies is one flat ink (median)
draw   polygons filled with their ink, coloured regions with their fitted field (helmet_art_field.png), then the
       words and logos from Leatt's own files (helmet.py and goggle.py document them), the brow badge, the vents.
Everything is in the HELMET frame of helmet.py (metres, x his left, y backwards, z up).
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import helmet as H          # noqa: E402

DATA = os.path.join(HERE, "helmet_art.json")
FIELD = os.path.join(HERE, "helmet_art_field.png")
TRACE_TEX = 2048                    # texels of the tracing atlas (2.15 px/mm, the photos give 4 to 5 px/mm)


# ---------------------------------------------------------------- the atlas as points on the shell
_CUT = {}                           # the shell's mouth cut in its own parameters (helmet.shell_outer), for mouth_ink


def surfaces():
    """Outer shell and visor top: (V, F, N, UV) in the helmet frame, UV 0..1 (helmet.atlas_uvs)."""
    Vo, Fo, prof = H.shell_outer()
    _CUT["mouth"] = prof.mouth_poly
    uv_o = H.atlas_uvs(Vo, Fo)[0]
    G = H.visor_surface(prof)
    nr, nc, _ = G.shape
    V = G.reshape(-1, 3)
    Ft = np.array(H.grid_faces(nr, nc))
    tris = np.vstack([Ft[:, [0, 1, 2]], Ft[:, [0, 2, 3]]])
    N = H.normals(V, tris)
    flip = np.mean(np.sum(N * (V - V.mean(0)), 1)) < 0
    if flip:
        N = -N
    Ftop = np.array(H.grid_faces(nr, nc, 0, flip))
    uv_v = H.atlas_uvs(V, Ftop, visor=True)[0]
    return [(Vo, Fo, H.normals(Vo, Fo), uv_o), (V, Ftop, N, uv_v)]


def texels(tex):
    """Every covered texel of a tex x tex atlas: (row, col), its point and unit normal on the shell, and which
    surface (0 shell, 1 visor)."""
    rows, cols, P, N, S = [], [], [], [], []
    for k, (V, F, Nv, UV) in enumerate(surfaces()):
        T = F if F.shape[1] == 3 else np.vstack([F[:, [0, 1, 2]], F[:, [0, 2, 3]]])
        UVt = UV if F.shape[1] == 3 else np.vstack([UV[:, [0, 1, 2]], UV[:, [0, 2, 3]]])
        idx, p, n = H.rasterize(UVt * tex, V[T], Nv[T])
        ok = (idx >= 0).all(1) & (idx < tex).all(1)
        rows.append(tex - 1 - idx[ok, 1]); cols.append(idx[ok, 0]); P.append(p[ok]); N.append(n[ok])
        S.append(np.full(ok.sum(), k))
    rows, cols, P, N, S = map(np.concatenate, (rows, cols, P, N, S))
    N /= np.linalg.norm(N, axis=1)[:, None]
    # one entry per texel (triangles share edge texels): keep the first
    key = rows * tex + cols
    _, first = np.unique(key, return_index=True)
    return rows[first], cols[first], P[first], N[first], S[first]


# ---------------------------------------------------------------- the photos
PHOTO_FILES = H.PHOTOS


def load_photo(view):
    from PIL import Image
    return np.array(Image.open(os.path.join(H.REF, PHOTO_FILES[view])).convert("RGBA")).astype(np.float32)


def bilinear(img, uv):
    """Sample an H x W x C image at pixel coordinates uv (x right, y down; pixel centres at integers)."""
    h, w = img.shape[:2]
    x = np.clip(uv[:, 0], 0, w - 1.001)
    y = np.clip(uv[:, 1], 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    a, b = img[y0, x0], img[y0, x0 + 1]
    c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def srgb_to_lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(np.asarray(c, float), 0, None)
    return 255.0 * np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def view_lookup(view, P, N, all_P):
    """Where each point lands in a view's photo (px), whether the view sees it (depth test against all_P, the
    whole outer surface), and how squarely (cos of the angle between the normal and the ray)."""
    x = H.PRINT_CAMS[view]
    C, Rm, f = H.cam_from(x)
    uv, depth = H.cam_project(x, P)
    uva, da = H.cam_project(x, all_P)
    cell = 3.0
    n = int(1920 / cell) + 1
    ca = np.floor(uva / cell).astype(int)
    ok = (ca >= 0).all(1) & (ca < n).all(1)
    zb = np.full((n, n), np.inf)
    np.minimum.at(zb, (ca[ok, 1], ca[ok, 0]), da[ok])
    c = np.floor(uv / cell).astype(int)
    okc = (c >= 0).all(1) & (c < n).all(1)
    vis = np.zeros(len(P), bool)
    vis[okc] = depth[okc] <= zb[c[okc, 1], c[okc, 0]] + 0.004
    d = (C - P) / np.linalg.norm(C - P, axis=1)[:, None]
    cos = np.sum(N * d, 1)
    return uv, vis, cos


# ---------------------------------------------------------------- trace: measure the print in the photos
VIEWS = [(v, m) for v in ("isoleft", "isoright", "back", "top") for m in (0, 1)]   # m = 1: the mirror point
# Which view owns a texel: the most square-on (cos^2), times these preferences. The sides take Leatt's iso-left
# (no goggle in it; his right side is its mirror image), the iso-right only where nothing else sees; the top, back,
# front and visor take each point from its own side (words and centre-line art stay whole) before a mirror point.
VIEW_PREF = dict(isoleft=1.0, isoright=0.6, back=1.0, top=1.0)
MIRROR_PREF = dict(side=1.0, other=0.45)
# On the visor's top the top view comes first: it sees the visor square-on (4 px per mm), and through the model's
# visor, whose slope is not the real one's, the iso views put its chevrons 10 to 25 mm off the top view's (drawn
# from that photo, VISOR_CHEVRONS): two columns of them before. The iso views keep what the top view sees at a
# glancing angle only.
VISOR_PREF = dict(isoleft=0.1, isoright=0.1, back=0.1, top=1.0)
# Studio reflections on coloured print that the automatic test (photo brighter than the view's white, or a
# washed-out pink) misses: hand-marked on each photo (px), the texels under them are taken from another view or
# filled from their own print region.
HIGHLIGHTS = {}                     # none needed so far: the automatic test and FORCE cover Leatt's four photos
# Parts of a photo that show something else where the fitted camera puts the shell: in the back view everything
# above the rear lip is the visor seen from behind (its LEATT band, its two vents), not the crown.
# The turbine disc in the back view is a copy of the one drawn from the top view, landing about 20 mm lower on the
# shell (the back camera fits worst at the crown): left out too. In the top view everything beyond the rear
# spoiler's edge (the back band, its arrows, the stripe's end, all seen edge-on) is left to the back view: the
# shell has no spoiler, and the top camera laid them across the crown as a streak.
NOT_SHELL = {"back": [[(0, 0), (1920, 0), (1920, 620), (1560, 560), (1340, 455), (1050, 440), (850, 440),
                       (560, 455), (360, 560), (0, 620)],
                      [(870, 585), (1030, 585), (1030, 690), (870, 690)]],
             "top": [[(0, 0), (1920, 0), (1920, 540), (1420, 500), (1280, 450), (1160, 400), (1040, 378),
                      (880, 378), (760, 400), (640, 450), (500, 500), (0, 540)]]}
WHITE = (226, 229, 235)            # the white base's ink (helmet.BASE_WHITE): every view's white is scaled to it
# The unpainted black plastic parts: their moulded texture (the grip panel's triangles, the chin vent's mesh, the
# eye port's trim) catches the studio light in grey and white streaks that are no print. Hand-marked on Leatt's
# iso-left photo (px, 1920 x 1920), applied to each texel's design point (so his right side gets the mirror):
# every shell texel inside is that ink. The moulded LEATT on the chin cap is black on black (no print). The chin
# vent's ink comes from the mouthpiece's rim in 3D instead (mouth_ink).
FORCE = {"isoleft": [
    ("black", [(470, 577), (700, 577), (783, 590), (883, 602), (992, 619), (1100, 644), (1160, 655), (1350, 697),
               (1347, 735), (1331, 816), (1316, 897), (1300, 954), (1287, 1010), (1275, 1047), (1262, 1085),
               (1256, 1097), (1175, 1122), (1100, 1150), (950, 1140), (950, 760), (700, 740), (470, 720)]),  # port trim, grip panel
    ("black", [(385, 1180), (430, 1118), (480, 1098), (650, 1098), (650, 1192), (545, 1188), (400, 1182)]),     # chin cap
    # round 5 (decision 56): the crown's side vent is geometry (helmet_detail.crown_side_vents): its slot and the
    # shading round it are no print (main traced them as two black blobs, px 1440 to 1495, 369 to 496)
    ("white", [(1425, 355), (1535, 355), (1535, 520), (1425, 520)]),
],
    # The centre stripe's end on the back (back photo px): teal both sides of the purple stem (x 941 to 987) down
    # to the spoiler's foot (y 722). The top view places the turbine on the shell about 40 mm above where the back
    # view does, so the shell carries more of the stripe's end than the photo shows: it is teal and stem all the
    # way (no second purple field, no hole where the back view's disc was left out). Only the region is set; the
    # colours are the fitted fields of the teal and the stem round it.
    "back": [
    ("iridescent", [(850, 440), (1060, 440), (1060, 722), (850, 722)]),
    ("purple", [(941, 440), (987, 440), (988, 728), (944, 728)]),
]}
# The same for the visor's top (top photo px, his left; his right gets the mirror): from just inside its chevron
# column out to its edge it is white print only. The photo shows the visor's moulded detail there in shading (the
# crease along the chevrons, the shadow under its raised side, the side vent's recess lit pale blue), which the
# model's plain visor does not have; the chevrons and the visor's LEATT are drawn over it (VISOR_CHEVRONS, ELEMENTS).
FORCE_VISOR = {"top": [("white", [(1230, 960), (1480, 960), (1480, 1560), (1230, 1560)])]}
# The print round the rear lower pieces comes from the back view (round 4, decision 50). The shell turns there from
# the back to the side and every camera sees it at a grazing angle (cosine 0.13 to 0.43); the iso-left view, owning
# it by its larger cosine, laid the white piece's edge out as a spike over the black beside it (back photo px 500 to
# 540, 1495 to 1520), its camera having no outline of its own there. Inside this zone (back photo px, his left; his
# right takes the mirror) the back view owns every texel it sees at a cosine over BACK_ZONE_COS, the others weigh
# 0.02 of their own.
BACK_ZONE = [(425, 1395), (555, 1395), (565, 1645), (425, 1645)]
BACK_ZONE_COS = 0.1


def design_points(P, N):
    """The same point on his left half (the art is mirror-symmetric) and its normal."""
    s = np.where(P[:, 0] < 0, -1.0, 1.0)
    return P * np.c_[s, np.ones((len(P), 2))], N * np.c_[s, np.ones((len(P), 2))]


def sh9(n):
    x, y, z = n.T
    return np.c_[np.ones_like(x), x, y, z, x * y, y * z, x * z, x * x - y * y, 3 * z * z - 1]


def to_img(tex, r, c, v, fill=0.0):
    out = np.full((tex, tex) + np.shape(v)[1:], fill, np.float32)
    out[r, c] = v
    return out


def norm_blur(val, w, sigma):
    """Normalised Gaussian: the weighted average of val (H x W [x C]) with weights w, and the weight density."""
    from scipy import ndimage
    den = ndimage.gaussian_filter(w.astype(np.float32), sigma)
    if val.ndim == 2:
        return ndimage.gaussian_filter(val * w, sigma) / np.maximum(den, 1e-6), den
    num = np.stack([ndimage.gaussian_filter(val[..., k] * w, sigma) for k in range(val.shape[2])], -1)
    return num / np.maximum(den, 1e-6)[..., None], den


def hue_sat(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = np.maximum(mx - mn, 1e-6)
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == R, ((G - B) / d) % 6, np.where(mx == G, (B - R) / d + 2, (R - G) / d + 4)) * 60
    return h, (mx - mn) / np.maximum(mx, 1e-6)


def sample_views(tex):
    """Every texel looked up in every (view, mirror): photo colour, alpha, visible, cos, photo px."""
    from PIL import Image, ImageDraw
    r, c, P, N, S = texels(tex)
    out = dict(r=r, c=c, P=P, N=N, S=S)
    for view in PHOTO_FILES:
        img = load_photo(view)
        if view == "isoright":                        # the goggle covers the right side there
            m = Image.new("L", (1920, 1920), 0)
            ImageDraw.Draw(m).polygon(H.ISORIGHT_GOGGLE, fill=255)
            img[np.array(m) > 0, 3] = 0
        for poly in NOT_SHELL.get(view, []):
            m = Image.new("L", (1920, 1920), 0)
            ImageDraw.Draw(m).polygon(poly, fill=255)
            img[np.array(m) > 0, 3] = 0
        hm = Image.new("L", (1920, 1920), 0)
        for poly in HIGHLIGHTS.get(view, []):
            ImageDraw.Draw(hm).polygon([tuple(p) for p in poly], fill=255)
        hm = np.array(hm) > 0
        for mir in (0, 1):                            # 0: the texel's own point, 1: its mirror point
            sg = np.array([-1.0, 1, 1]) if mir else np.ones(3)
            uv, vis, cos = view_lookup(view, P * sg, N * sg, P)
            px = bilinear(img, uv)
            ui = np.clip(np.round(uv).astype(int), 0, 1919)
            k = f"{view}{mir}"
            out[k + "_rgb"], out[k + "_a"] = px[:, :3], px[:, 3]
            out[k + "_vis"], out[k + "_cos"], out[k + "_n"] = vis, cos, N * sg
            out[k + "_hand"] = hm[ui[:, 1], ui[:, 0]]
    return out


def back_zone(P, N, S):
    """Shell texels whose design point lies in BACK_ZONE, seen in the back view."""
    from matplotlib.path import Path
    Pd, Nd = design_points(P, N)
    uv, vis, cos = view_lookup("back", Pd, Nd, P)
    return Path(BACK_ZONE).contains_points(uv) & vis & (cos > 0.0) & (S == 0)


# The chin's mouthpiece (phase 2, decision 51): its moulding covers the shell inside its rim (helmet_detail.mouth_rim_xz,
# traced through the two solved cameras that see the chin's outline within 5 mm). The Pinata iso-left camera, which
# owns the chin's front, puts Leatt's black 10 to 15 mm off there (its chin outline stands 13 mm inside Leatt's): its
# black ran past the rim as teeth, a FORCE polygon in its px could not hold it. Inside the rim the shell is black, in
# a band MOUTH_RING round it white (the paint folding in at the rim). The same for the chin bar's side vents
# (helmet_detail.SIDE_VENT_YZ, on the chin's sides): black inside, white in a band SIDE_RING round them. Round 5
# (decision 56): inside the rim means inside the shell's cut in its own parameters (y, z: helmet.shell_outer's
# mouth_poly, the faces pushed back behind the mouthpiece); by the front-plane outline, texels on the chin bar's side
# behind the rim's top corner fell inside it and hung a black flag 2 mm out of the rim (iso-left at 2.4x).
MOUTH_RING = 0.008
SIDE_RING = 0.005
# The chin cap's lower edge across the chin's front (x, z in mm): the dark moulding over the chin bar's top meets the
# white paint there (Pinata iso-right at 1.5x with a grid, cast through its solved camera; Leatt's black from the
# iso-left view, 10 to 15 mm off at the chin, hung below it as teeth). Ahead of y CHIN_CAP_Y and inside |x| 48 mm:
# black above the line, white below it down to the mouthpiece's rim (beside the rim's top corners, |x| over 40 mm,
# only down to z -82 mm: the upper side slots' print below that stays).
CHIN_CAP = [(0.0, -68.0), (13.0, -68.0), (25.0, -69.0), (34.0, -70.3), (48.5, -74.0)]
CHIN_CAP_Y = -0.185
# Along the chin bar's sides (|x| over 40 mm, y -205 to -150 mm) the same edge as (y, z) mm, from the same photo;
# white for CHIN_CAP_BAND under it (the upper side slots' print lies 7 to 10 mm under it there)
CHIN_CAP_SIDE = [(-205.0, -72.5), (-200.0, -74.0), (-185.1, -81.0), (-170.5, -81.9), (-153.7, -82.2)]
CHIN_CAP_BAND = 0.005


def mouth_ink(P, S, out):
    """The mouthpiece's ink on the shell's texels (index into INKS, in place): black inside the rim, white in the
    band round it, on the chin's front (y < -0.12 m); the same round the chin bar's side vents; the chin cap black
    above its lower edge (CHIN_CAP, CHIN_CAP_SIDE) and the paint white below it."""
    import helmet_detail as D
    from matplotlib.path import Path
    from scipy.spatial import cKDTree
    rim = D.mouth_rim_xz()
    xz = P[:, [0, 2]]
    cap = np.asarray(CHIN_CAP) / 1000.0
    ax = np.abs(P[:, 0])
    zc = np.interp(ax, cap[:, 0], cap[:, 1])
    face = (S == 0) & (P[:, 1] < CHIN_CAP_Y) & (ax < cap[-1, 0])
    out[face & (P[:, 2] > zc + 0.001)] = INKS.index("black")
    out[face & (P[:, 2] < zc - 0.001) & ((ax < 0.040) | (P[:, 2] > -0.082))] = INKS.index("white")
    cs = np.asarray(CHIN_CAP_SIDE) / 1000.0
    zs = np.interp(P[:, 1], cs[:, 0], cs[:, 1])
    flank = (S == 0) & (ax > 0.040) & (P[:, 1] > cs[0, 0]) & (P[:, 1] < cs[-1, 0])
    out[flank & (P[:, 2] > zs + 0.001)] = INKS.index("black")
    out[flank & (P[:, 2] < zs - 0.001) & (P[:, 2] > zs - CHIN_CAP_BAND)] = INKS.index("white")
    front = (S == 0) & (P[:, 1] < -0.12)
    cut = _CUT.get("mouth")
    inside = (Path(rim).contains_points(xz) if cut is None else Path(cut).contains_points(P[:, 1:])) & front
    near = cKDTree(rim).query(xz)[0] < MOUTH_RING
    out[front & near & ~inside] = INKS.index("white")
    out[inside] = INKS.index("black")
    sv = D.resample_loop(np.asarray(D.SIDE_VENT_YZ, float) / 1000.0, 0.0005)
    yz = P[:, [1, 2]]
    side = (S == 0) & (np.abs(P[:, 0]) > 0.035) & (P[:, 1] < -0.12)
    inside = Path(sv).contains_points(yz) & side
    near = cKDTree(sv).query(yz)[0] < SIDE_RING
    out[side & near & ~inside] = INKS.index("white")
    out[inside] = INKS.index("black")
    return out


def force_labels(P, N, S):
    """The ink FORCE (shell) and FORCE_VISOR (visor's top) put on each texel (index into INKS), -1 where none: the
    texel's design point is looked up in the marked view and must be seen there. The visor's wings: white."""
    from PIL import Image, ImageDraw
    Pd, Nd = design_points(P, N)
    out = np.full(len(P), -1)
    for surf, table in ((0, FORCE), (1, FORCE_VISOR)):
        for view, marks in table.items():
            uv, vis, cos = view_lookup(view, Pd, Nd, P)
            ui = np.clip(np.round(uv).astype(int), 0, 1919)
            for ink, poly in marks:
                m = Image.new("L", (1920, 1920), 0)
                ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
                inside = (np.array(m) > 0)[ui[:, 1], ui[:, 0]] & vis & (cos > 0.0) & (S == surf)
                out[inside] = INKS.index(ink)
    # the visor's steep wings (its side islands, helmet.atlas_uvs) are white print in Leatt's Pinata photos, its
    # LEATT drawn over them from the file. The iso views laid the visor's rear edge line there (the model's rear
    # corner stands 7 mm off Leatt's: the photo's grey edge line and the shell's blue beyond it fell on the wing) as
    # thin grey marks and two small blue slivers (joint front fit, decision 47)
    a = np.abs(N)
    out[(S == 1) & (a[:, 0] >= a[:, 2]) & (a[:, 0] >= a[:, 1])] = INKS.index("white")
    return mouth_ink(P, S, out)


def labels(t):
    """The ink of each texel: its de-lit colour's class, or the hand-marked one."""
    lab = classify(t["alb"])
    f = t.get("force")
    return np.where(f >= 0, f, lab) if f is not None else lab


def highlight_flags(rgb, white_level):
    """Studio reflections in a photo: brighter than the view's white print, or a washed-out pink (a reflection
    over magenta, purple or red ink: the inks' least channel is near 0)."""
    h, s = hue_sat(rgb)
    bright = rgb.min(1) > white_level + 18
    pink = ((h > 280) | (h < 20)) & (s > 0.10) & (s < 0.55) & (rgb.max(1) > 140)
    return bright | pink


def trace(tex=TRACE_TEX, log=print):
    """Measure the print: ownership, de-lit colours, inks, region maps and fields (atlas images, tex x tex)."""
    from scipy import ndimage
    d = sample_views(tex)
    r, c = d["r"], d["c"]
    n = len(r)
    force = force_labels(d["P"], d["N"], d["S"])
    zone = back_zone(d["P"], d["N"], d["S"])
    keys = [f"{v}{m}" for v, m in VIEWS]
    W_lin = srgb_to_lin(np.array(WHITE, float))
    cov = to_img(tex, r, c, np.ones(n)) > 0
    weights, alb, hl_all = [], [], []
    for k in keys:
        rgb, a, vis, cos = d[k + "_rgb"], d[k + "_a"], d[k + "_vis"], d[k + "_cos"]
        ok = vis & (a > 200) & (cos > 0.25)
        own_ok, zp = ok, np.where(zone, 0.02, 1.0)     # who may own a texel (BACK_ZONE: the back view)
        if k.startswith("back"):
            own_ok, zp = ok | (zone & vis & (a > 200) & (cos > BACK_ZONE_COS)), 1.0
        whiteish = ok & (rgb.max(1) - rgb.min(1) < 20) & (rgb.min(1) > 100) & (force < 0)
        level = np.percentile(rgb[whiteish].min(1), 90) if whiteish.sum() > 500 else 200.0
        hl = own_ok & (highlight_flags(rgb, level) | d[k + "_hand"])
        # studio shading: second-order SH of the normal fitted to the white print (robust: reflections are
        # positive outliers), then corrected locally by the measured white around each texel
        lin = srgb_to_lin(rgb)
        Bm = sh9(d[k + "_n"])
        white = whiteish & ~hl
        shade = np.zeros((n, 3))
        if white.sum() > 500:
            for ch in range(3):
                sel = white.copy()
                for _ in range(6):
                    cf = np.linalg.lstsq(Bm[sel], lin[sel, ch], rcond=None)[0]
                    res = lin[:, ch] - Bm @ cf
                    sd = np.median(np.abs(res[sel])) * 1.48 + 1e-4
                    sel = white & (res < 1.5 * sd) & (res > -3 * sd)
                shade[:, ch] = np.maximum(Bm @ cf, 0.02)
            ratio = to_img(tex, r, c, (lin / shade).mean(1))
            wimg = to_img(tex, r, c, white.astype(float))
            loc, den = norm_blur(ratio, wimg, 12.0)
            loc2, _ = norm_blur(ratio, wimg, 40.0)
            corr = np.where(den > 0.05, loc, loc2)[r, c]
            corr = np.clip(np.nan_to_num(corr, nan=1.0), 0.6, 1.6)
            shade *= corr[:, None]
        else:
            shade[:] = 1.0
        alb.append(lin_to_srgb(lin / shade * W_lin))
        # brighter than the white base once de-lit is no print (white is the lightest ink): a reflection, or the
        # shading fit extrapolated to a face turned away from the light (the iso-left view on his rear lower side,
        # facing down, gave magenta over 255, drawn as a saturated pink glow); that view does not own the texel
        over = own_ok & (alb[-1].max(1) > 255.0)
        hl = hl | over
        hl_all.append(hl)
        side = np.isin(H.face_island(d["N"]), ["L", "R"]) & (d["S"] == 0)
        mp = 1.0 if k.endswith("0") else np.where(side, MIRROR_PREF["side"], MIRROR_PREF["other"])
        vp = np.where(d["S"] == 1, VISOR_PREF[k[:-1]], 1.0)
        w = np.clip(cos, 0, 1) ** 2 * own_ok * VIEW_PREF[k[:-1]] * mp * vp * zp
        sm, _ = norm_blur(to_img(tex, r, c, w), cov, 6.0)
        weights.append(np.where(w > 0, sm[r, c], 0.0) * ~hl)
        log(k, "white level", round(float(level), 1), "reflections", int(hl.sum()), "of them over white once de-lit",
            int(over.sum()), "seen", int(ok.sum()))
    weights = np.array(weights)
    own = np.argmax(weights, 0)
    known = weights.max(0) > 0
    alb = np.array(alb)[own, np.arange(n)]
    # a texel no view owns, with an owned one within 3 mm on the shell, takes that one's owner and colour: on the
    # crown's rippled back slope the faces turned to the back are seen by no view (the back photo shows the visor
    # there, NOT_SHELL) while their neighbours turned up are seen from the top; left unseen they were white dashes
    # across the stripe
    from scipy.spatial import cKDTree
    for s in np.unique(d["S"]):
        a, b = np.nonzero(known & (d["S"] == s))[0], np.nonzero(~known & (d["S"] == s))[0]
        if len(a) and len(b):
            dist, j = cKDTree(d["P"][a]).query(d["P"][b], distance_upper_bound=0.003)
            hit = np.isfinite(dist)
            own[b[hit]], alb[b[hit]] = own[a[j[hit]]], alb[a[j[hit]]]
            known[b[hit]] = True
    log("owned by view", {keys[i]: int(((own == i) & known).sum()) for i in range(len(keys))},
        "unknown", int((~known).sum()), "hand-marked", int((force >= 0).sum()))
    return dict(d=d, own=np.where(known, own, -1), alb=alb, keys=keys, force=force)


INKS = ["black", "white", "purple", "magenta", "iridescent"]
K, WH, PU, MA, IR = range(5)
FIELD_INKS = (PU, MA, IR)           # inks whose colour is a fitted field (design gradients); the rest are flat
PALE_TEAL_DEFICIT = 14.0            # de-lit red this far below the mean of green and blue: pale teal, not white


def classify(alb):
    """Ink of each de-lit colour: black, white, purple, magenta, else iridescent (teal, green, yellow, orange,
    red, the pale teal of the back band)."""
    h, s = hue_sat(alb)
    lab = np.full(len(alb), IR)
    lab[(h >= 250) & (h < 295)] = PU
    lab[(h >= 295) & (h < 338)] = MA
    grey = alb.max(1) - alb.min(1) < 32
    # the pale teal of the back band (the hexagon round the back icon) is grey by spread but short of red: the white
    # base has red 6 below the mean of green and blue (BASE_WHITE), its texels median 5.7, 95 % under 12.5. The sky
    # blue studio reflections on the visor are short of red too but bluer (green minus blue median -12.7 there,
    # -1.7 on the back's pale teal)
    teal = ((alb[:, 1] + alb[:, 2]) / 2 - alb[:, 0] > PALE_TEAL_DEFICIT) & (alb[:, 1] - alb[:, 2] > -7.0)
    lab[grey & (alb.min(1) > 120) & ~teal] = WH
    lab[(alb.max(1) < 55) | (grey & (alb.max(1) < 135))] = K
    return lab


SPECK_MM2 = 3.0                     # ink islands smaller than this are glints or dust, not print (the small
                                    # print, the words and labels, is drawn from files, not traced)


def despeckle(reg, probs, cov, tex):
    """Ink islands under SPECK_MM2 that do not touch an atlas island's edge (there a shape may simply continue
    on the next island) take the ink round them; reg and probs are changed in place."""
    from scipy import ndimage
    mm = 1000.0 / (H.ATLAS_K * tex / 4096.0)
    nmin = SPECK_MM2 / mm ** 2
    edge = cov & ~ndimage.binary_erosion(cov)
    bad = np.zeros_like(cov)
    for k in range(len(INKS)):
        lab, n = ndimage.label(reg == k, structure=np.ones((3, 3)))
        if n == 0:
            continue
        ids = np.arange(1, n + 1)
        size = ndimage.sum(np.ones_like(lab), lab, ids)
        touch = ndimage.maximum(edge, lab, ids) > 0
        small = np.r_[False, (size < nmin) & ~touch]
        bad |= small[lab]
    idx = ndimage.distance_transform_edt(bad | ~cov, return_distances=False, return_indices=True)
    new = reg[idx[0], idx[1]]
    reg[bad] = new[bad]
    probs[:, bad] = 0.0
    for k in range(len(INKS)):
        probs[k][bad & (new == k)] = 1.0
    return int(bad.sum())


EXCLUDE_WEIGHT = 0.3                # an erased texel's own-ink probability is scaled by this (it is still taken
                                    # where nothing else is near, so a word's edge over plain white stays white)


def regions(t, tex=TRACE_TEX, sig_lab=2.2, sig_field=3.0, erased=None, exclude=None):
    """Ink regions (smoothed one-hot, argmax) and the colour field of each field ink, as tex x tex images. Texels
    under the drawn elements (erased) are filled from the print round them, preferring inks other than the
    element's own (exclude, erase_mask)."""
    from scipy import ndimage
    d, own, alb = t["d"], t["own"], t["alb"]
    r, c = d["r"], d["c"]
    cov = to_img(tex, r, c, np.ones(len(r))) > 0
    lab = labels(t)
    seen = (own >= 0) | (t["force"] >= 0)
    known = seen & ~(erased if erased is not None else False)
    probs = []
    kimg = to_img(tex, r, c, known.astype(float))
    far = ndimage.gaussian_filter(to_img(tex, r, c, seen.astype(float)), sig_lab) < 0.2
    for k in range(len(INKS)):
        oh = to_img(tex, r, c, ((lab == k) & known).astype(float))
        p1, den = norm_blur(oh, kimg, sig_lab)
        p2, den2 = norm_blur(oh, kimg, 12.0)
        p3, _ = norm_blur(oh, kimg, 40.0)
        probs.append(np.where(den > 0.2, p1, np.where(den2 > 0.05, p2, p3)))
    probs = np.array(probs)
    if exclude is not None:
        ex = to_img(tex, r, c, exclude, -1)
        for k in range(len(INKS)):
            probs[k][ex == k] *= EXCLUDE_WEIGHT
    probs[:, far] = 0.0                               # nothing seen near: the plain white base (under the visor)
    probs[WH, far] = 1.0
    reg = np.where(cov, np.argmax(probs, 0), -1)
    despeckle(reg, probs, cov, tex)
    aimg = to_img(tex, r, c, alb)
    # a hand-marked texel sets the region, never the colour: the fields are fitted only from texels a view owns
    # whose own colour is that ink. (A hand-marked texel no view owns has no measured colour: the stripe's end on the
    # back, masked in the back view and seen by the top view only at a glancing angle, fed its garbage into the teal
    # field as a pure white glow.)
    owned = (own >= 0) & ~(erased if erased is not None else False)
    cls = classify(alb)
    fields = {}
    for k in FIELD_INKS:
        src = to_img(tex, r, c, ((cls == k) & owned).astype(float)) * (reg == k)
        f1, den = norm_blur(aimg, src, sig_field)
        f2, den2 = norm_blur(aimg, src, 15.0)
        f3, _ = norm_blur(aimg, src, 60.0)
        fields[k] = np.where((den > 0.05)[..., None], f1, np.where((den2 > 0.01)[..., None], f2, f3))
    return reg, probs, fields


# ---------------------------------------------------------------- vectorise the ink regions
def simplify(P, tol):
    """Douglas-Peucker on a closed loop (first point not repeated)."""
    n = len(P)
    if n < 8:
        return P
    i0 = 0
    i1 = int(np.argmax(np.linalg.norm(P - P[0], axis=1)))
    keep = np.zeros(n, bool)
    keep[[i0, i1]] = True
    stack = [(i0, i1), (i1, n)]
    Pc = np.vstack([P, P[:1]])
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        A, B = Pc[a], Pc[b]
        seg = Pc[a + 1:b]
        ab = B - A
        L = np.linalg.norm(ab)
        dist = np.abs(ab[0] * (seg[:, 1] - A[1]) - ab[1] * (seg[:, 0] - A[0])) / L if L > 1e-9 else \
            np.linalg.norm(seg - A, axis=1)
        k = int(np.argmax(dist))
        if dist[k] > tol:
            m = a + 1 + k
            keep[m % n] = True
            stack += [(a, m), (m, b)]
    return P[keep]


def vectorise(probs, cov, tol=0.8):
    """Each ink's region as polygons (outer loop, holes) in atlas UV units: filled contours of the ink's
    probability minus the best other ink's, at 0, simplified (tol texels)."""
    import contourpy
    tex = probs.shape[1]
    out = {}
    for k in range(len(INKS)):
        others = np.max(np.delete(probs, k, axis=0), axis=0)
        z = np.where(cov, probs[k] - others, -1.0).astype(np.float64)
        z = np.pad(z, 1, constant_values=-1.0)
        gen = contourpy.contour_generator(z=z, fill_type="OuterOffset")
        polys = []
        pts, offs = gen.filled(0.0, 10.0)
        for P, of in zip(pts, offs):
            loops = [P[of[i]:of[i + 1] - 1] for i in range(len(of) - 1)]   # contourpy closes loops: drop repeat
            loops = [simplify(L, tol) for L in loops]
            loops = [L for L in loops if len(L) >= 3]
            if not loops or abs(poly_area(loops[0])) < 4.0:              # specks under 4 texels
                continue
            # (x, y) = (column, row) of the padded image -> UV (u right, v up)
            polys.append([np.round(np.c_[(L[:, 0] - 0.5) / tex, 1.0 - (L[:, 1] - 0.5) / tex], 6).tolist()
                          for L in loops])
        out[INKS[k]] = polys
    return out


def poly_area(L):
    x, y = L[:, 0], L[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def raster_polys(polys, tex, ss=2):
    """Coverage (0..1) of polygons (outer + holes, UV units) on a tex x tex atlas, supersampled ss x ss."""
    from PIL import Image, ImageDraw
    n = tex * ss
    im = Image.new("L", (n, n), 0)
    dr = ImageDraw.Draw(im)
    order = sorted(polys, key=lambda p: -abs(poly_area(np.asarray(p[0]))))
    for p in order:
        for j, L in enumerate(p):
            L = np.asarray(L)
            xy = np.c_[L[:, 0] * n, (1.0 - L[:, 1]) * n]
            dr.polygon([tuple(q) for q in xy], fill=255 if j == 0 else 0)
    a = np.asarray(im, np.float32).reshape(tex, ss, tex, ss).mean((1, 3)) / 255.0
    return a


FIELD_RES = 1024                    # texels per side of each ink's field (0.93 mm: the fields are 1.4 mm smooth)


def save_trace(t, reg, probs, fields, tex=TRACE_TEX, log=print, extra=None):
    """helmet_art.json (ink colours, polygons) and helmet_art_field.png (the field inks' colour fields, side by
    side, extended past their regions so the polygons never sample a neighbour)."""
    from PIL import Image
    from scipy import ndimage
    d = t["d"]
    cov = to_img(tex, d["r"], d["c"], np.ones(len(d["r"]))) > 0
    aimg = to_img(tex, d["r"], d["c"], t["alb"])
    known = to_img(tex, d["r"], d["c"], (t["own"] >= 0).astype(float)) > 0
    lab = to_img(tex, d["r"], d["c"], classify(t["alb"]).astype(float), -1)
    inks = {}
    for k, name in enumerate(INKS):
        core = ndimage.binary_erosion(reg == k, iterations=3) & known & (lab == k)
        inks[name] = np.median(aimg[core], 0).round(1).tolist() if core.sum() > 50 else [128.0] * 3
    inks["white"] = list(WHITE)
    polys = vectorise(probs, cov)
    data = dict(trace_tex=tex, inks=inks, field_inks=[INKS[k] for k in FIELD_INKS], polygons=polys, **(extra or {}))
    json.dump(data, open(DATA, "w"), separators=(",", ":"))
    s = tex // FIELD_RES
    panel = []
    for k in FIELD_INKS:
        f = fields[k].reshape(FIELD_RES, s, FIELD_RES, s, 3).mean((1, 3))
        panel.append(np.clip(f, 0, 255))
    Image.fromarray(np.hstack(panel).round().astype(np.uint8)).save(FIELD, optimize=True)
    log("inks", inks, "polygons", {k: len(v) for k, v in polys.items()})
    return data


def draw(out_path=None, tex=None, log=print):
    """The atlas from the traced print (helmet_art.json, helmet_art_field.png) plus the drawn elements."""
    from PIL import Image
    from scipy import ndimage
    tex = tex or H.TEX
    out_path = out_path or os.path.join(H.TEXDIR, "helmet_pinata.png")
    data = json.load(open(DATA))
    fimg = np.asarray(Image.open(FIELD).convert("RGB"), np.float32)
    covs = {name: raster_polys(data["polygons"][name], tex) for name in INKS}
    tot = sum(covs.values())
    out = np.zeros((tex, tex, 3), np.float32)
    uu, vv = np.meshgrid((np.arange(tex) + 0.5) / tex, (np.arange(tex) + 0.5) / tex)
    for name, cv in covs.items():
        if name in data["field_inks"]:
            j = data["field_inks"].index(name)
            fx = np.clip(uu * FIELD_RES - 0.5, 0, FIELD_RES - 1) + j * FIELD_RES
            fy = vv * FIELD_RES - 0.5
            col = np.stack([ndimage.map_coordinates(fimg[..., ch], [fy, fx], order=1, mode="nearest")
                            for ch in range(3)], -1)
        else:
            col = np.array(data["inks"][name], np.float32)[None, None]
        out += cv[..., None] * col
    # where the polygons only partly cover a texel (an island's edge: the trace is coarser) their own colour is
    # used, and a texel no polygon reaches takes the nearest polygon's colour: never a white fill (no seams)
    have = tot > 0.5
    out /= np.maximum(tot, 1e-6)[..., None]
    idx = ndimage.distance_transform_edt(~have, return_distances=False, return_indices=True)
    out = np.where(have[..., None], out, out[idx[0], idx[1]])
    tx = texels(tex)
    # an island's edge and its small fragments (a rippled slope's faces alternate between two islands) take the
    # colour of the nearest island interior on the SHELL: the regions and fields are smooth in the atlas, so there
    # they would mix in whatever lies next to them in the atlas (thin light lines on the crown's back before)
    from scipy.spatial import cKDTree
    cov = np.zeros((tex, tex), bool)
    cov[tx[0], tx[1]] = True
    lab, n = ndimage.label(cov, np.ones((3, 3)))
    big = np.r_[False, ndimage.sum(cov, lab, range(1, n + 1)) > 3000 * (tex / 4096.0) ** 2]    # over 160 mm^2
    inner = (ndimage.binary_erosion(cov, iterations=max(2, tex // 1024)) & big[lab])[tx[0], tx[1]]
    for s in np.unique(tx[4]):
        a, b = np.nonzero((tx[4] == s) & inner)[0], np.nonzero((tx[4] == s) & ~inner)[0]
        if len(a) and len(b):
            j = cKDTree(tx[2][a]).query(tx[2][b])[1]
            out[tx[0][b], tx[1][b]] = out[tx[0][a[j]], tx[1][a[j]]]
    # the 3D inks (mouth_ink: the chin cap's edge, the mouthpiece's and the side vents' rims) once more on the texels
    # themselves: the chin bar's top front lies in thin atlas slivers (its faces alternate between two islands, 2 to
    # 5 texels wide), where the fill above took the cap's black from over its edge and hung it 7 mm below it (phase 2)
    f = mouth_ink(tx[2], tx[4], np.full(len(tx[2]), -1))
    for k in np.unique(f[f >= 0]):
        m = f == k
        out[tx[0][m], tx[1][m]] = np.asarray(data["inks"][INKS[k]], np.float32)
    art = draw_elements(out, tex, data, log, tx)
    # bleed: every texel off the islands takes the colour of the nearest island texel, so the renderer's texture
    # filtering at an island's edge never reads the fill (no seams where the islands meet on the shell)
    cov = np.zeros((tex, tex), bool)
    cov[tx[0], tx[1]] = True
    idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    art = art[idx[0], idx[1]]
    Image.fromarray(np.clip(art, 0, 255).round().astype(np.uint8)).save(out_path, optimize=True)
    log("drew", out_path)
    return out_path


# ---------------------------------------------------------------- elements: Leatt's logos, the labels, the badges
# Drawn over the traced print, each texel coloured from its own point on the shell (no atlas seams), in a frame
# placed on the shell: origin o, reading direction u, up v, normal n; the frame's coordinates follow the surface
# (arc length: asin of the offset times the local curvature, cu along u, cv along v), and a similarity maps the
# element's image (px, rows down) into them. A mirrored copy on his right side uses o' = M o, n' = M n, u' = -M u
# (M: x -> -x), so words read the right way on both sides and logos are never mirror images.
REFDIR = os.path.normpath(os.path.join(HERE, "..", "..", "reference", "leatt-gear"))
WORDMARK = os.path.join(REFDIR, "leatt-wordmark-slanted_official_leatt-us_1200x300.png")      # us.leatt.com logo
ICON = os.path.join(REFDIR, "leatt-icon-triangle_official-favicon_leatt-us_100x100.png")       # us.leatt.com favicon
FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",          # package fonts-dejavu-core
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"]
FIT_TEX = 4096                      # texels for the element fits (0.23 mm)
MX = np.array([-1.0, 1.0, 1.0])

# Colours of the printed labels: Leatt's photos, the ink against the helmet's white beside it (linear ratio) times
# the white ink (scratch measure_cols.py; chin and emergency label iso-left, turbine top view, size label back)
NAVY = (46, 28, 117)                # chin lettering
LABEL_BLACK = (13, 7, 11)           # emergency label
LABEL_RED = (197, 0, 0)             # its pull tab
TURBINE_BLUE = (3, 116, 200)        # the 360 Turbine disc
STICKER_WHITE = (245, 244, 241)     # the size sticker: brighter than the paint's white (photo 215 against 183)


def font(px):
    from PIL import ImageFont
    for f in FONTS:
        if os.path.exists(f):
            return ImageFont.truetype(f, max(int(px), 1))
    raise FileNotFoundError("no bold sans font: install fonts-dejavu-core")


def wordmark_mask():
    """Leatt's slanted wordmark as a 0..1 mask (rows down) cropped to its letters, the registered mark dropped
    (alpha over 128, parts over 5 % of the largest: the same reading as goggle.wordmark_mask)."""
    from PIL import Image
    from scipy import ndimage
    a = np.asarray(Image.open(WORDMARK).convert("RGBA"))[..., 3].astype(np.float32) / 255.0
    lab, n = ndimage.label(a > 0.5)
    sizes = ndimage.sum(a > 0.5, lab, range(1, n + 1))
    keep = ndimage.binary_dilation(np.isin(lab, 1 + np.nonzero(sizes > 0.05 * sizes.max())[0]), iterations=2)
    a = a * keep
    ys, xs = np.nonzero(a > 0.5)
    return np.ascontiguousarray(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1])


def icon_mask(up=8):
    """Leatt's three-piece triangle (the site's favicon, 100 px: the icon printed on the helmet; the older
    one-piece logo is not it), upsampled x up and re-thresholded: straight edges, round corners."""
    from PIL import Image
    from scipy import ndimage
    a = np.asarray(Image.open(ICON).convert("RGBA"))[..., 3].astype(np.float32) / 255.0
    lab, n = ndimage.label(a > 0.5)
    sizes = ndimage.sum(a > 0.5, lab, range(1, n + 1))
    keep = ndimage.binary_dilation(np.isin(lab, 1 + np.nonzero(sizes > 500)[0]), iterations=2)
    a = ndimage.zoom(a * keep, up, order=3)
    a = ndimage.gaussian_filter(np.where(a > 0.5, 1.0, 0.0), up * 0.35)
    ys, xs = np.nonzero(a > 0.5)
    return np.ascontiguousarray(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1])


def mask_keypoints(m):
    """Two ink points of a mask: bottom-left of its lowest row, top-right of its top row (px)."""
    ys, xs = np.nonzero(m > 0.5)
    b, t = ys.max(), ys.min()
    return np.array([[xs[ys == b].min(), b], [xs[ys == t].max(), t]], float)


def text_line(txt, cap, track=0.0, adv=None, cw=None):
    """A line of capitals as a 0..1 mask: cap height `cap` px, baseline at 1.15 cap, height 1.3 cap. Natural
    spacing plus `track` x cap between letters, or spaced lettering: `adv` px per character, each glyph at most
    `cw` px wide (squeezed)."""
    from PIL import Image, ImageDraw
    B = 200
    f = font(B / 0.729)                                    # DejaVu Sans Bold capitals: 0.729 em

    def glyph(ch):
        g = Image.new("L", (5 * B, 3 * B), 0)
        ImageDraw.Draw(g).text((B, B // 2), ch, font=f, fill=255)
        return g
    _, top, _, bot = glyph("H").getbbox()
    capB = bot - top
    k = cap / capB
    y0, hB = top - 0.15 * capB, 1.3 * capB
    Hh = int(round(1.3 * cap))
    parts, x = [], 0.0
    for ch in txt:
        step = adv if adv else (f.getlength(ch) + track * capB) * k
        if ch != " ":
            g = glyph(ch)
            bb = g.getbbox()
            g = g.crop((bb[0], int(round(y0)), bb[2], int(round(y0 + hB))))
            w = max(1, int(round((bb[2] - bb[0]) * k)))
            if cw and w > cw:
                w = int(round(cw))
            g = np.asarray(g.resize((w, Hh), Image.LANCZOS), np.float32) / 255.0
            parts.append((g, x + (adv - w) / 2 if adv else x + (bb[0] - B) * k))
        x += step
    W = int(math.ceil(max([l + g.shape[1] for g, l in parts] + [x]))) + 2
    out = np.zeros((Hh, W), np.float32)
    for g, l in parts:
        i = int(round(l))
        out[:, i:i + g.shape[1]] = np.maximum(out[:, i:i + g.shape[1]], g)
    return np.clip(out, 0, 1)


def shear(m, deg):
    """Italic: a mask sheared so its tops lean right by deg."""
    from PIL import Image
    t = math.tan(math.radians(deg))
    h, w = m.shape
    im = Image.fromarray((m * 255).astype(np.uint8))
    im = im.transform((w + int(math.ceil(t * h)), h), Image.AFFINE, (1, t, -t * h, 0, 1, 0), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


class Canvas:
    """An RGBA decal drawn in millimetres (res px per mm), premultiplied (colour times alpha)."""
    def __init__(self, w_mm, h_mm, res=24.0):
        self.res = res
        self.a = np.zeros((int(round(h_mm * res)), int(round(w_mm * res)), 4), np.float32)

    def paint(self, m, rgb, x_mm, y_mm):
        """Colour rgb through a 0..1 mask whose top-left lands at (x, y) mm."""
        h, w = self.a.shape[:2]
        x, y = int(round(x_mm * self.res)), int(round(y_mm * self.res))
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + m.shape[1], w), min(y + m.shape[0], h)
        if x1 <= x0 or y1 <= y0:
            return
        mm = m[y0 - y:y1 - y, x0 - x:x1 - x][..., None]
        src = np.concatenate([np.asarray(rgb, np.float32) / 255.0 * np.ones(3), [1.0]])
        self.a[y0:y1, x0:x1] = self.a[y0:y1, x0:x1] * (1 - mm) + src * mm

    def knock(self, m, x_mm, y_mm):
        """Clear the decal through a 0..1 mask (a knock-out: the surface under it shows)."""
        h, w = self.a.shape[:2]
        x, y = int(round(x_mm * self.res)), int(round(y_mm * self.res))
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + m.shape[1], w), min(y + m.shape[0], h)
        self.a[y0:y1, x0:x1] *= 1 - m[y0 - y:y1 - y, x0 - x:x1 - x][..., None]

    def shape(self, draw_fn):
        """A 0..1 mask of the canvas size from PIL drawing commands in mm (draw_fn(draw, s), s = px per mm),
        drawn at 4x and reduced (smooth edges)."""
        from PIL import Image, ImageDraw
        h, w = self.a.shape[:2]
        im = Image.new("L", (w * 4, h * 4), 0)
        draw_fn(ImageDraw.Draw(im), self.res * 4)
        return np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255.0

    def text(self, txt, rgb, x_mm, y_mm, cap_mm, width_mm=None, slant=0.0, **kw):
        """A line of capitals, its cap top-left at (x, y) mm, optionally stretched to width_mm."""
        from PIL import Image
        m = text_line(txt, cap_mm * self.res, **kw)
        ys, xs = np.nonzero(m > 0.3)
        m = m[:, xs.min():xs.max() + 1]
        if width_mm:
            m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize(
                (int(round(width_mm * self.res)), m.shape[0]), Image.LANCZOS), np.float32) / 255.0
        if slant:
            m = shear(m, slant)
        self.paint(m, rgb, x_mm, y_mm - 0.15 * cap_mm)
        return m.shape[1] / self.res

    def rgba(self):
        return self.a


def decal_emergency():
    """The emergency release label under each cheek (Leatt iso-left, 1164-1347 x 1340-1440 px): a black label,
    a red pull tab with a white arrow at its front end, two lines of white capitals. Size from the photo through
    the fitted camera (helmet_art.json frames: 46 mm between the ends' midpoints); proportions from the photo."""
    L, Hh = 46.0, 8.6
    cv = Canvas(L, Hh)
    r = 0.9
    cv.paint(cv.shape(lambda d, s: d.rounded_rectangle([0, 0, L * s - 1, Hh * s - 1], r * s, fill=255)), LABEL_BLACK, 0, 0)
    cv.paint(cv.shape(lambda d, s: (d.rounded_rectangle([0, 0, 8.0 * s, Hh * s - 1], r * s, fill=255),
                                    d.rectangle([4 * s, 0, 8.0 * s, Hh * s - 1], fill=255))), LABEL_RED, 0, 0)
    cx, cy = 4.0, Hh / 2 + 0.2
    cv.paint(cv.shape(lambda d, s: (d.rectangle([(cx - 2.3) * s, (cy - 2.6) * s, (cx + 2.3) * s, (cy - 1.9) * s], fill=255),
                                    d.polygon([((cx - 2.3) * s, (cy - 1.3) * s), ((cx + 2.3) * s, (cy - 1.3) * s),
                                               (cx * s, (cy + 2.6) * s)], fill=255))), (245, 245, 245), 0, 0)
    cv.text("EMERGENCY USE ONLY", (238, 238, 238), 9.4, 1.0, 3.3, width_mm=35.2)
    cv.text("PULL RED TAB & REMOVE CHEEK PAD", (205, 205, 208), 9.6, 5.5, 1.75, width_mm=34.6)
    a = cv.rgba()
    h, w = a.shape[:2]
    return a, np.array([[0.0, (h - 1) / 2], [w - 1.0, (h - 1) / 2]])


def decal_chin():
    """The chin's lettering (Leatt iso-left 695-865 x 1325-1415 px): three left-aligned lines of spaced, condensed
    italic capitals in navy, "MX.26", "MOTO RACE SPEC", "LEATT DEVELOPED". Key points: bottom-left of the M of
    MOTO, bottom-right of the C of SPEC (photo 701,1394 and 864,1340)."""
    cap, pitch, adv, slant = 3.4, 4.9, 3.15, 16.0     # mm, from the photo: 13 px letters, 19 px lines, 12 px cells
    lines = ["MX.26", "MOTO RACE SPEC", "LEATT DEVELOPED"]
    cv = Canvas(15 * adv + 4, 3 * pitch + 1)
    for i, txt in enumerate(lines):
        m = text_line(txt, cap * cv.res, adv=adv * cv.res, cw=0.62 * cap * cv.res)
        cv.paint(shear(m, slant), NAVY, 0.3 + (2 - i) * pitch * math.tan(math.radians(slant)), 0.3 + i * pitch - 0.15 * cap)
    a = cv.rgba()
    # key points from the drawn ink of line 2, just above its baseline
    y_base = (0.3 + pitch + cap) * cv.res
    band = a[int(y_base - 0.25 * cap * cv.res):int(y_base), :, 3].max(0)
    xs = np.nonzero(band > 0.5)[0]
    return a, np.array([[xs.min(), y_base], [xs.max(), y_base]], float)


LAYOUT_MM = 0.25                    # mm per photo px of the back labels' layout (the frame or projection sets size)
DOT_ORIGIN = (915.0, 1540.0)        # back view px of the DOT print's layout origin
SIZE_ORIGIN = (1020.0, 1562.3)      # and of the size sticker's


def decal_dot():
    """The DOT certification printed white on the black lower back (Leatt back view, 915-1017 x 1540-1620 px):
    a white bar with the wordmark knocked out, MOTO 8.5, DOT, FMVSS No. 218, CERTIFIED, an underline. Laid out in
    the photo's pixels (0.25 mm each, scaled on the shell by the frame). Key points: top-left of the bar, right end
    of the underline."""
    s = LAYOUT_MM
    X, Y = DOT_ORIGIN
    cv = Canvas(103 * s, 81 * s)
    W = WHITE
    bar = cv.shape(lambda d, q: d.rectangle([(918.6 - X) * s * q, (1540.6 - Y) * s * q, (1017.1 - X) * s * q,
                                             (1552.0 - Y) * s * q], fill=255))
    cv.paint(bar, W, 0, 0)
    wm = wordmark_mask()
    from PIL import Image
    ww = (988.6 - 945.7) * s * cv.res
    wmi = np.asarray(Image.fromarray((wm * 255).astype(np.uint8)).resize(
        (int(round(ww)), int(round(ww * wm.shape[0] / wm.shape[1]))), Image.LANCZOS), np.float32) / 255.0
    cv.knock(wmi, (945.7 - X) * s, (1542.9 - Y) * s)  # the wordmark knocked out of the bar (black shows)
    for txt, x0, x1, y0, y1 in (("MOTO 8.5", 942.9, 991.4, 1554.3, 1562.3), ("DOT", 918.6, 1014.3, 1564.3, 1598.6),
                                ("FMVSS No. 218", 922.9, 1007.1, 1600.9, 1608.0), ("CERTIFIED", 934.3, 994.3, 1609.4, 1617.1)):
        cv.text(txt, W, (x0 - X) * s, (y0 - Y) * s, (y1 - y0) * s, width_mm=(x1 - x0) * s)
    cv.paint(cv.shape(lambda d, q: d.rectangle([(915.7 - X) * s * q, (1618.0 - Y) * s * q, (1012.9 - X) * s * q,
                                                (1619.7 - Y) * s * q], fill=255)), W, 0, 0)
    q = cv.res * s
    return cv.rgba(), np.array([[(918.6 - X) * q, (1540.6 - Y) * q], [(1012.9 - X) * q, (1619.7 - Y) * q]])


def decal_size():
    """The size sticker beside it (Leatt back view, 1020-1116 x 1562-1621 px, reading M 57-58cm, 1305g±50g,
    ECE 22.06): white, rounded, black capitals. Printed with HIS size, L 59-60 cm (Leatt's size chart, his 59.2 cm
    head: research/rider-ledger/helmet.md); the weight line is the photographed one (same shell assumed). Key
    points: its bottom-left and top-right corners."""
    s = LAYOUT_MM
    X, Y = SIZE_ORIGIN
    w, h = 95.7 * s, 58.3 * s
    cv = Canvas(w, h)
    cv.paint(cv.shape(lambda d, q: d.rounded_rectangle([0, 0, w * q - 1, h * q - 1], 1.4 * q, fill=255)), STICKER_WHITE, 0, 0)
    k = (20, 20, 22)
    for txt, x0, x1, y0, y1 in (("L", 1062.0, 1081.0, 1567.0, 1585.7), ("59-60cm", 1048.0, 1096.0, 1594.3, 1599.0),
                                ("1305g±50g", 1041.4, 1102.9, 1601.0, 1607.0), ("ECE 22.06", 1031.4, 1108.6, 1608.6, 1615.4)):
        cv.text(txt, k, (x0 - X) * s, (y0 - Y) * s, (y1 - y0) * s, width_mm=(x1 - x0) * s)
    a = cv.rgba()
    hh, ww = a.shape[:2]
    return a, np.array([[0.0, hh - 1.0], [ww - 1.0, 0.0]])


def decal_turbine():
    """Leatt's 360 Turbine badge on the top-back (Leatt top view 922-1006 x 384-463 px, back view 916-1016 px):
    a blue disc, a black ring of six arcs with arrow gaps, "360°" and "TURBINE" in black. Key points: the ends of
    its horizontal diameter (reading direction)."""
    D = 21.0                                           # mm, placeholder: the frame sets the true size from the photo
    cv = Canvas(D, D)
    R = D / 2
    cv.paint(cv.shape(lambda d, q: d.ellipse([0, 0, D * q - 1, D * q - 1], fill=255)), TURBINE_BLUE, 0, 0)

    def ring(d, q):
        for i in range(6):
            a0 = i * 60 + 12
            d.pieslice([(R - 0.80 * R) * q, (R - 0.80 * R) * q, (R + 0.80 * R) * q, (R + 0.80 * R) * q],
                       a0, a0 + 44, fill=255)
        d.ellipse([(R - 0.62 * R) * q, (R - 0.62 * R) * q, (R + 0.62 * R) * q, (R + 0.62 * R) * q], fill=0)
    cv.paint(cv.shape(ring), (0, 0, 0), 0, 0)
    cv.text("360°", (0, 0, 0), R - 0.48 * R, R - 0.40 * R, 0.42 * R, width_mm=0.96 * R)
    cv.text("TURBINE", (0, 0, 0), R - 0.42 * R, R + 0.14 * R, 0.17 * R, width_mm=0.84 * R)
    a = cv.rgba()
    h, w = a.shape[:2]
    return a, np.array([[0.0, (h - 1) / 2], [w - 1.0, (h - 1) / 2]])


# The visor's chevrons: seven black V's in a column along each side of the visor's top (Leatt top photo, seen
# square-on at about 4 px per mm). Traced like the rest they came out ragged (the trace's 2.15 texels per mm, views
# mixed over the visor, its slope unlike the real one's), so they are vectorised from that photo instead: each
# chevron's outline is the ink at half its contrast against the white round it (sub-pixel contour, Douglas-Peucker
# 0.6 px), projected through the top camera onto the visor like the back labels. Each side from its own column (his
# left: the image's right). Kept: ink components (under 90 on white) of 1200 to 2000 px, the chevrons (1415 to 1556
# px); left out: the visor's LEATT (1049 px, drawn from the file), the shadows under the visor's side (about 350 px)
# and the vents (over 4000 px). Leatt's art is mirror-symmetric, but through the solved top camera (helmet round 4)
# the mirror of one column's cast lands 14 px (3.5 mm) from the other column in the photo, and on the visor's sloping
# side the two casts lie 5 mm from mirror places (the camera and the visor's height at its tip, not the art). So each
# column's outline is moved in the photo half way to the mirror of the other's cast (about 7 px each): the two sit at
# mirror places, each within 2 mm of its own photo place.
VISOR_CHEVRONS = dict(view="top", y=(950, 1540), cols={"visor_chevrons": (1220, 1480), "visor_chevrons_R": (440, 700)},
                      dark=90.0, area=(1200, 2000), tol=0.6, q=4.0, erase_grow=0.003)


def chevron_polys():
    """{frame name: [outline (k x 2, photo px, x right, y down), ...] front last} of the visor's chevrons."""
    import contourpy
    from scipy import ndimage
    v = VISOR_CHEVRONS
    ph = load_photo(v["view"])
    a = ph[..., 3:] / 255.0
    L = (ph[..., :3] * a + 255.0 * (1 - a)).mean(-1)            # the photo on white
    y0, y1 = v["y"]
    out = {}
    for name, (x0, x1) in v["cols"].items():
        sub = L[y0:y1, x0:x1]
        ink = sub < v["dark"]
        lab, n = ndimage.label(ink)
        area = ndimage.sum(ink, lab, range(1, n + 1))
        polys = []
        for k in [i + 1 for i, s in enumerate(area) if v["area"][0] <= s <= v["area"][1]]:
            m = lab == k
            ring = ndimage.binary_dilation(m, iterations=7) & ~ndimage.binary_dilation(m, iterations=3) & ~ink
            white, black = np.median(sub[ring]), np.median(sub[ndimage.binary_erosion(m, iterations=2)])
            alpha = np.clip((white - sub) / (white - black), 0, 1) * ndimage.binary_dilation(m, iterations=3)
            z = np.pad(ndimage.gaussian_filter(alpha, 0.6), 1).astype(np.float64)
            line = max(contourpy.contour_generator(z=z, line_type="Separate").lines(0.5), key=len)[:-1]
            polys.append(np.round(simplify(line, v["tol"]) + [x0 - 1, y0 - 1], 2))
        out[name] = sorted(polys, key=lambda p: p[:, 1].mean())
    return out


def poly_art(fr):
    """Premultiplied RGBA (0..1) of an element given as outlines in a photo's px (a projected frame's polys), q art
    px per photo px, 2 x 2 supersampled."""
    from PIL import Image, ImageDraw
    pj = fr["proj"]
    q, ss = pj["q"], 2
    w, h = pj["size"]
    im = Image.new("L", (int(round(w * q)) * ss, int(round(h * q)) * ss), 0)
    d = ImageDraw.Draw(im)
    for P in fr["polys"]:
        a = (np.asarray(P) - np.asarray(pj["origin"])) * q            # art px (pixel centres at integers)
        d.polygon([tuple(p) for p in (a + 0.5) * ss - 0.5], fill=255)
    m = np.asarray(im, np.float32) / 255.0
    m = m.reshape(m.shape[0] // ss, ss, m.shape[1] // ss, ss).mean((1, 3))
    return np.dstack([m, m, m, m])


def frame_art(fr):
    """(art image, cache key) of a frame: its polygons or its art file."""
    if "polys" in fr:
        return poly_art(fr), fr["name"]
    return art_image(fr["art"])[0], fr["art"]


def art_image(art):
    """(premultiplied RGBA 0..1 image, key points px) of an element's art."""
    if art == "wordmark":
        m = wordmark_mask()
    elif art == "icon":
        m = icon_mask()
    elif art.startswith("glyph:"):
        m = text_line(art[6:], 120)
        ys, xs = np.nonzero(m > 0.3)
        m = m[:, xs.min():xs.max() + 1]
        return np.dstack([m, m, m, m]), np.array([[0.0, 0.0], [1.0, 0.0]])
    else:
        return dict(emergency=decal_emergency, chin=decal_chin, dot=decal_dot, size=decal_size,
                    turbine=decal_turbine)[art]()
    return np.dstack([m, m, m, m]), mask_keypoints(m)


# The elements. fit: Leatt's file laid over its ink in a photo (region of interest px, ink test, rotation guess
# deg), first in the photo, then on the shell through the fitted camera; picks: two photo points (px) that the
# art's key points land on, then (refine) the art's ink part fitted on the shell like a file. ink: white / black
# (the traced inks), trace (the de-lit colour under it), or the art's own colours. surface 1 = the visor's top.
# Not here: the big raised LEATT on the side in the iso-right photo is on the goggle's strap (woven, over the shell).
# Not here either: the LEATT knocked out of the visor's band is traced from the top photo (seen square-on, 4 px per
# mm). The file laid on the visor's surface fits it badly (IoU 0.49, 0.50 with a free aspect: the visor's slope
# differs from the real one's along its length), and drawn that way it ate the band's strips between the letters.
ELEMENTS = [
    dict(name="back_leatt", art="wordmark", ink="white", free_aspect=True,
         fit=dict(view="back", roi=(540, 1250, 1400, 1480), test="white", ang=0)),
    dict(name="visor_side_leatt", art="wordmark", ink="black", surface=1, mirror=True,
         fit=dict(view="isoleft", roi=(1130, 415, 1265, 480), test="black", ang=0)),
    dict(name="side_icon", art="icon", ink="white", mirror=True,
         fit=dict(view="isoleft", roi=(930, 1240, 1200, 1495), test="white_cc", ang=6)),
    dict(name="back_icon", art="icon", ink="trace",
         fit=dict(view="back", roi=(820, 920, 1100, 1100), test="teal", ang=0)),
    dict(name="emergency", art="emergency", mirror=True,
         picks=dict(view="isoleft", px=[(1164.4, 1418.8), (1345.0, 1353.8)])),
    dict(name="chin_text", art="chin", mirror=True,
         picks=dict(view="isoleft", px=[(701.1, 1394.4), (864.4, 1339.6)])),
    # the back labels sit where the shell turns under (foreshortened in the photo, laid out in its pixels): they
    # are projected through the back camera onto the shell (proj: the photo px of their layout's origin)
    dict(name="dot_label", art="dot", proj=dict(view="back", origin=DOT_ORIGIN)),
    dict(name="size_label", art="size", proj=dict(view="back", origin=SIZE_ORIGIN)),
    dict(name="turbine", art="turbine",
         picks=dict(view="top", px=[(1006.0, 423.0), (922.5, 423.0)])),
    dict(name="visor_chevrons", art="polys", ink="black", surface=1, chevrons=VISOR_CHEVRONS),
]
# "EIGHT POINT FIVE" along the top of each side band, small black capitals, one letter per cell (spaces included).
# It reads from the front up on his left (Leatt iso-left: E I G H T P O I N T F I seen, V E hidden) and from the back
# down on his right (iso-right: all of it). Letter centres (px, None: a space or unseen) and their height there.
EIGHT = dict(text="EIGHT POINT FIVE", cap_px=10.5, ink="black",
             left=dict(view="isoleft", px=[(1340.0, 667.5), (1362.5, 652.5), (1380.0, 640.0), (1395.0, 622.5),
                                           (1417.5, 607.5), None, (1473.3, 578.3), (1491.7, 565.0), (1510.0, 552.7),
                                           (1526.0, 540.0), (1540.0, 526.7), None, (1565.0, 504.0), (1576.0, 493.3),
                                           None, None]),
             right=dict(view="isoright", px=[(323.6, 448.4), (330.0, 459.6), (337.6, 471.6), (347.0, 485.0),
                                             (358.0, 497.6), None, (382.0, 522.4), (397.6, 536.0), (413.6, 549.6),
                                             (430.4, 563.6), (449.6, 577.6), None, (486.6, 606.6), (507.4, 622.4),
                                             (529.6, 638.4), (552.4, 656.0)]))


def ink_test(rgba, test):
    """Ink pixels of a photo crop (bool) and the pixels a fit may compare (bool: on the helmet)."""
    from scipy import ndimage
    rgb = rgba[..., :3]
    h, s = hue_sat(rgb)
    every = rgba[..., 3] > 200
    if test == "white":
        return (rgb.min(-1) > 150) & (s < 0.2) & every, every
    if test == "black":
        return (rgb.max(-1) < 90) & every, every
    if test == "teal":
        return (h > 150) & (h < 200) & (s > 0.35) & every, every
    if test == "white_cc":                     # white parts that do not reach the crop's edge (inside colour)
        white = (rgb.min(-1) > 140) & (s < 0.25) & every
        lab, n = ndimage.label(white)
        edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])
        return white & ~np.isin(lab, edge[edge > 0]), every
    raise ValueError(test)


def fit_photo(view, roi, test, ang0, m):
    """Similarity (mask px -> photo px, 2 x 3) that best lays the mask over the ink in a region of a photo (soft
    IoU: an angle and scale grid round the guess, then Nelder-Mead), and its IoU."""
    from scipy import ndimage, optimize
    img = load_photo(view)
    x0, y0, x1, y1 = roi
    T, within = ink_test(img[y0:y1, x0:x1], test)
    T = ndimage.gaussian_filter(T.astype(np.float32), 0.7)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    mh, mw = m.shape
    ys, xs = np.nonzero(T > 0.5)
    cx, cy = xs.mean() + x0, ys.mean() + y0
    ext = max(np.ptp(xs), np.ptp(ys))

    def M_of(q):
        sc, th, tx, ty = q
        c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
        return np.array([[sc * c, -sc * s_, tx], [sc * s_, sc * c, ty]])

    def score(q):
        A_ = np.linalg.inv(np.vstack([M_of(q), [0, 0, 1]]))
        mx = A_[0, 0] * xx + A_[0, 1] * yy + A_[0, 2]
        my = A_[1, 0] * xx + A_[1, 1] * yy + A_[1, 2]
        v = ndimage.map_coordinates(m, [my, mx], order=1, cval=0.0) * within
        return -np.minimum(v, T).sum() / max(np.maximum(v, T).sum(), 1.0)

    best = None
    for th in np.arange(ang0 - 40, ang0 + 41, 4.0):
        c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
        diag = max(abs(mw * c) + abs(mh * s_), abs(mw * s_) + abs(mh * c))
        for f in (0.8, 0.9, 1.0, 1.1):
            sc = ext / max(diag, 1) * f
            tx = cx - sc * (c * mw / 2 - s_ * mh / 2)
            ty = cy - sc * (s_ * mw / 2 + c * mh / 2)
            v = score([sc, th, tx, ty])
            if best is None or v < best[0]:
                best = (v, [sc, th, tx, ty])
    res = optimize.minimize(score, best[1], method="Nelder-Mead", options=dict(xatol=0.02, fatol=1e-6, maxiter=1500))
    return M_of(res.x), -res.fun


def photo_to_shell(P, N, view, pts, all_P):
    """Points of the shell under photo pixels of a view: the nearest visible point's (P, N subsets)."""
    from scipy.spatial import cKDTree
    uv, vis, cos = view_lookup(view, P, N, all_P)
    ok = vis & (cos > 0.05)
    i = cKDTree(uv[ok]).query(np.asarray(pts, float))[1]
    return P[ok][i], N[ok][i]


def frame_at(P, N, A, B):
    """A frame on the shell between two surface points: o the surface point nearest their midpoint, n the mean
    normal round it, u along A -> B in the tangent plane, v = n x u, cu and cv the curvatures along u and v
    (least squares of the normal offset over the element's area)."""
    mid = 0.5 * (A + B)
    i = np.argmin(np.linalg.norm(P - mid, axis=1))
    o = P[i]
    near = np.linalg.norm(P - o, axis=1) < 0.012
    n = N[near].mean(0)
    n /= np.linalg.norm(n)
    u = (B - A) - n * ((B - A) @ n)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    rad = max(0.6 * np.linalg.norm(B - A), 0.015)
    q = P - o
    sel = (np.linalg.norm(q, axis=1) < rad) & (N @ n > 0.3)
    U, V, D = q[sel] @ u, q[sel] @ v, q[sel] @ n
    cf = np.linalg.lstsq(np.c_[U * U, V * V, U * V, np.ones_like(U)], D, rcond=None)[0]
    cu, cv = float(np.clip(-2 * cf[0], -30, 30)), float(np.clip(-2 * cf[1], -30, 30))
    return dict(o=o.tolist(), u=u.tolist(), v=v.tolist(), n=n.tolist(), cu=cu, cv=cv)


def surface_uv(fr, P, N, depth=0.05):
    """Frame coordinates (m, along the surface) of shell points; NaN off the element's face."""
    o, u, v, n = (np.asarray(fr[k], float) for k in ("o", "u", "v", "n"))
    q = P - o
    U, V, D = q @ u, q @ v, q @ n

    def arc(x, c):
        return x if abs(c) < 1e-6 else np.arcsin(np.clip(x * c, -1, 1)) / c
    out = np.c_[arc(U, fr["cu"]), arc(V, fr["cv"])]
    out[(np.abs(D) > depth) | (N @ n < 0.25)] = np.nan
    return out


def frame_px(fr, P, N):
    """Image px (x right, y down) of the element's art at shell points; NaN off its face."""
    if "proj" in fr:                                  # projected through a photo's camera
        pj = fr["proj"]
        x = H.PRINT_CAMS[pj["view"]]
        C, _, _ = H.cam_from(x)
        uv, _ = H.cam_project(x, P)
        px = (uv - np.asarray(pj.get("shift", (0.0, 0.0))) - np.asarray(pj["origin"])) * pj["q"]
        bad = (np.linalg.norm(P - np.asarray(fr["o"]), axis=1) > pj["radius"]) | (np.sum(N * (C - P), 1) <= 0)
        px[bad] = np.nan
        return px
    w = surface_uv(fr, P, N)
    a, b, tx, ty = fr["sim"]
    z = (w[:, 0] - tx + 1j * (w[:, 1] - ty)) / complex(a, b)
    return np.c_[z.real, -z.imag / fr.get("aspect", 1.0)]


def px_size(fr):
    """Metres per px of an element's art on the shell (about, for a projected one)."""
    if "proj" in fr:
        return fr["proj"].get("mpp", LAYOUT_MM / 1000.0) / fr["proj"]["q"]
    return abs(complex(*fr["sim"][:2]))


def set_sim(fr, kp, A2, B2):
    """The similarity taking the art's key points (px, rows down) to two frame points (m)."""
    k0, k1 = complex(kp[0][0], -kp[0][1]), complex(kp[1][0], -kp[1][1])
    za, zb = complex(*A2), complex(*B2)
    rot = (zb - za) / (k1 - k0)
    t = za - rot * k0
    fr["sim"] = [rot.real, rot.imag, t.real, t.imag]
    return fr


def mirror_frame(fr):
    o, u, n = (np.asarray(fr[k], float) for k in ("o", "u", "n"))
    n2, u2 = n * MX, -(u * MX)
    return dict(fr, name=fr["name"] + "_R", o=(o * MX).tolist(), u=u2.tolist(), n=n2.tolist(),
                v=np.cross(n2, u2).tolist())


# A fit with a free aspect stays near the photo's own fit: scale within 0.82 to 1.22, turn within 20 deg, the
# centre within 25 mm, the aspect within 0.74 to 1.35. Unbounded, the back LEATT's fit through the refitted back
# camera ran off to 254 mm wide and 2.3 in aspect, over the white bands round the black panel. (Fixed-aspect fits
# are left free: the visor side LEATT needs its scale cut by a fifth from a poor start, IoU 0.29 to 0.60.)
MAX_LOG_SCALE, MAX_TURN, MAX_SHIFT_MM, MAX_LOG_ASPECT = 0.2, math.radians(20.0), 25.0, 0.3


def refine_on_shell(fr, m, view, roi, test, P, N, all_P, log=print, free_aspect=False):
    """Refine a frame's similarity: the art laid on the shell, seen through the view's fitted camera, against the
    ink in the photo (soft IoU over the shell points the view sees square enough). Coarse to fine: a grid of turns
    and scales with both blurred 3 mm, then Nelder-Mead at 3, 1.5, 0.6 mm and sharp. free_aspect: the art's
    height may also scale against its length (a wordmark printed stretched: measured, logged)."""
    from scipy import ndimage, optimize
    img = load_photo(view)
    x0, y0, x1, y1 = roi
    T0, within = ink_test(img[y0:y1, x0:x1], test)
    o = np.asarray(fr["o"])
    a, b, tx, ty = fr["sim"]
    size = abs(complex(a, b)) * max(m.shape)
    near = np.linalg.norm(P - o, axis=1) < 0.7 * size + 0.01
    Pn, Nn = P[near], N[near]
    uv, vis, cos = view_lookup(view, Pn, Nn, all_P)
    inside = (uv[:, 0] >= x0) & (uv[:, 0] < x1 - 1) & (uv[:, 1] >= y0) & (uv[:, 1] < y1 - 1)
    w = surface_uv(fr, Pn, Nn)
    ok = vis & (cos > 0.2) & inside & ~np.isnan(w[:, 0])
    uv, w = uv[ok], w[ok]
    w_in = ndimage.map_coordinates(within.astype(np.float32), [uv[:, 1] - y0, uv[:, 0] - x0], order=0) > 0.5
    # photo px per mm round the element (for the blur levels)
    x = H.PRINT_CAMS[view]
    u_ = np.asarray(fr["u"])
    q2, _ = H.cam_project(x, np.array([o, o + 0.001 * u_]))
    ppm = max(np.linalg.norm(q2[1] - q2[0]), 0.5)
    zw = w[:, 0] + 1j * w[:, 1]
    rot0, t0 = complex(a, b), complex(tx, ty)
    ys, xs = np.nonzero(m > 0.5)
    zc = complex(xs.mean(), -ys.mean())               # turn and scale about the art's centre
    tc0 = rot0 * zc + t0
    k = 5 if free_aspect else 4

    def sim(p):
        rot = rot0 * np.exp(p[0] + 1j * p[1])
        asp = math.exp(p[4]) if len(p) > 4 else 1.0
        tc = tc0 + 0.001 * complex(p[2], p[3])
        return rot, tc - rot * complex(zc.real, zc.imag * asp), asp

    def level(sig_mm):
        Tb = ndimage.gaussian_filter(T0.astype(np.float32), max(0.7, sig_mm * ppm))
        tv = ndimage.map_coordinates(Tb, [uv[:, 1] - y0, uv[:, 0] - x0], order=1)
        mb = ndimage.gaussian_filter(m, sig_mm * 0.001 / abs(rot0)) if sig_mm > 0 else m

        def score(p):
            if len(p) > 4 and (abs(p[4]) > MAX_LOG_ASPECT or abs(p[0]) > MAX_LOG_SCALE or
                               abs(p[1]) > MAX_TURN or abs(complex(p[2], p[3])) > MAX_SHIFT_MM):
                return 0.0                                   # a refinement of the photo's fit, not a new search
            rot, t, asp = sim(p)
            z = (zw - t) / rot
            mv = ndimage.map_coordinates(mb, [-z.imag / asp, z.real], order=1, cval=0.0) * w_in
            return -np.minimum(mv, tv).sum() / max(np.maximum(mv, tv).sum(), 1.0)
        return score
    sharp = level(0.0)
    s0 = sharp(np.zeros(k))
    score = level(3.0)
    best = (score(np.zeros(k)), np.zeros(k))
    for th in np.radians(np.arange(-40, 41, 4)):
        for ls in np.arange(-0.25, 0.26, 0.05):
            q = np.zeros(k); q[0], q[1] = ls, th
            v = score(q)
            if v < best[0]:
                best = (v, q)
    p = best[1]
    for sig, step in ((3.0, 1.5), (1.5, 0.8), (0.6, 0.4), (0.0, 0.2)):
        score = level(sig)
        simplex = p + np.vstack([np.zeros(k), np.diag([0.02, 0.02, step, step, 0.02][:k])])
        p = optimize.minimize(score, p, method="Nelder-Mead",
                              options=dict(xatol=1e-4, fatol=1e-6, maxiter=3000, initial_simplex=simplex)).x
    rot, t, asp = sim(p)
    fr["sim"] = [rot.real, rot.imag, t.real, t.imag]
    fr["aspect"] = round(asp, 4)
    fr["iou"] = round(float(-sharp(p)), 3)
    log(fr["name"], "IoU on the shell", round(-s0, 3), "->", fr["iou"], "points", int(ok.sum()), "aspect", fr["aspect"])
    return fr


def element_frames(log=print):
    """Every element's frame(s) on the shell (and the mirrored ones), measured in Leatt's photos."""
    r, c, P, N, S = texels(FIT_TEX)
    all_P = P[::3]
    frames = []
    for e in ELEMENTS:
        surf = e.get("surface", 0)
        Ps, Ns = P[S == surf], N[S == surf]
        if "chevrons" in e:                           # outlines from a photo, projected through its camera
            v = e["chevrons"]
            cast = {}
            for name, polys in chevron_polys().items():
                allp = np.vstack(polys)
                ctr = (allp.min(0) + allp.max(0)) / 2
                cs = [p.mean(0) for p in polys]
                cast[name] = (polys, ctr) + tuple(photo_to_shell(Ps, Ns, v["view"], [
                    ctr, ctr - [0, 10], ctr + [0, 10], cs[0], cs[-1]], all_P)[0])
            for name, (polys, ctr, o, a_, b_, f_, l_) in cast.items():
                other = cast[name[:-2] if name.endswith("_R") else name + "_R"][2]
                uv, _ = H.cam_project(H.PRINT_CAMS[v["view"]], ((o + MX * other) / 2)[None])
                shift = uv[0] - ctr                       # photo px: half way to the mirror of the other column
                o = photo_to_shell(Ps, Ns, v["view"], [ctr + shift], all_P)[0][0]
                allp = np.vstack(polys)
                mpp = float(np.linalg.norm(b_ - a_) / 20.0)
                pad = v["erase_grow"] / mpp + 3.0             # the art reaches past the erase margin (px)
                lo, hi = allp.min(0) - pad, allp.max(0) + pad
                size = hi - lo
                frames.append(dict(name=name, art="polys", ink=e["ink"], surface=surf, o=o.tolist(),
                                   proj=dict(view=v["view"], origin=lo.round(2).tolist(), size=size.round(2).tolist(),
                                             q=v["q"], mpp=mpp, radius=0.6 * float(np.hypot(*size)) * mpp + 0.01,
                                             shift=shift.round(2).tolist()),
                                   erase_grow=v["erase_grow"], polys=[p.tolist() for p in polys]))
                ext = np.array([np.ptp(p, 0) for p in polys]) * mpp * 1000
                log(name, len(polys), "chevrons from the photo, centre mm", (o * 1000).round(1).tolist(),
                    "column mm", round(float(np.linalg.norm(l_ - f_) * 1000), 1), "each about",
                    ext.mean(0).round(1).tolist(), "mm (photo px x, y), mm per px", round(mpp * 1000, 3),
                    "moved px", shift.round(1).tolist())
            continue
        img, kp = art_image(e["art"])
        if "proj" in e:
            pj = e["proj"]
            q = 24.0 * LAYOUT_MM                          # decal px per photo px (Canvas res 24 px/mm)
            h, w = img.shape[:2]
            ctr = np.asarray(pj["origin"]) + np.array([w, h]) / q / 2
            (o, _), _ = photo_to_shell(Ps, Ns, pj["view"], [ctr, ctr], all_P)
            fr = dict(name=e["name"], art=e["art"], ink=e.get("ink"), surface=surf, o=o.tolist(),
                      proj=dict(view=pj["view"], origin=list(pj["origin"]), q=q, radius=0.04))
            corners, _ = photo_to_shell(Ps, Ns, pj["view"], [pj["origin"], np.asarray(pj["origin"]) + [w / q, 0],
                                                              np.asarray(pj["origin"]) + [0, h / q]], all_P)
            log(e["name"], "projected, centre mm", (o * 1000).round(1).tolist(), "width mm",
                round(float(np.linalg.norm(corners[1] - corners[0]) * 1000), 1), "height mm",
                round(float(np.linalg.norm(corners[2] - corners[0]) * 1000), 1))
            frames.append(fr)
            continue
        if "fit" in e:
            f = e["fit"]
            M, iou = fit_photo(f["view"], f["roi"], f["test"], f["ang"], img[..., 3])
            px = (M @ np.c_[kp, np.ones(2)].T).T
            log(e["name"], "photo fit IoU", round(float(iou), 3), "key points px", px.round(1).tolist())
            view = f["view"]
        else:
            view, px = e["picks"]["view"], np.asarray(e["picks"]["px"], float)
        (A, B), _ = photo_to_shell(Ps, Ns, view, px, all_P)
        fr = frame_at(Ps, Ns, A, B)
        wa, wb = surface_uv(fr, np.array([A, B]), np.array([fr["n"], fr["n"]]))
        fr.update(name=e["name"], art=e["art"], ink=e.get("ink"), surface=surf)
        set_sim(fr, kp, wa, wb)
        if "fit" in e or "refine" in e:
            f = e.get("fit") or e["refine"]
            m = img[..., 3]
            if f["test"] == "white" and "refine" in e:          # the decal's white part (its print or sticker)
                m = np.where(img[..., :3].mean(-1) > 0.6 * np.maximum(m, 1e-3), m, 0.0)
            refine_on_shell(fr, np.ascontiguousarray(m, np.float32), view, f["roi"], f["test"], Ps, Ns, all_P, log,
                            e.get("free_aspect", False))
        rot = complex(*fr["sim"][:2])
        h, w = img.shape[:2]
        log(e["name"], "centre mm", (np.asarray(fr["o"]) * 1000).round(1).tolist(),
            "size mm", round(abs(rot) * w * 1000, 1), "x", round(abs(rot) * h * fr.get("aspect", 1.0) * 1000, 1),
            "turn deg", round(math.degrees(math.atan2(rot.imag, rot.real)), 1))
        frames.append(fr)
        if e.get("mirror"):
            frames.append(mirror_frame(fr))
    frames += eight_frames(P[S == 0], N[S == 0], all_P, log)
    return frames


def eight_frames(P, N, all_P, log=print):
    """EIGHT POINT FIVE: one smooth curve on his left side (cubic in the cell index) through the letters' centres
    seen in both iso views (his right side's mirrored: its cell i is the left's cell n - 1 - i, the text running the
    other way), points more than 3 mm off dropped; one frame per letter, height from the iso-right photo through the
    camera. His right side is the mirrored curve read the other way."""
    e = EIGHT
    n_cells = len(e["text"])
    pts, cells = [], []
    for side in ("left", "right"):
        sd = e[side]
        idx = [i for i, p in enumerate(sd["px"]) if p is not None]
        Q, _ = photo_to_shell(P, N, sd["view"], [sd["px"][i] for i in idx], all_P)
        if side == "right":
            Q, idx = Q * MX, [n_cells - 1 - i for i in idx]
        pts.append(Q); cells += idx
    Q, t = np.vstack(pts), np.array(cells, float)
    keep = np.ones(len(t), bool)
    for _ in range(4):
        coef = np.polyfit(t[keep], Q[keep], 3)
        fit = np.array([np.polyval(coef[:, k], t) for k in range(3)]).T
        res = np.linalg.norm(fit - Q, axis=1)
        keep = res < max(0.003, 2.5 * np.median(res))
    tt = np.arange(n_cells, dtype=float)
    C = np.array([np.polyval(coef[:, k], tt) for k in range(3)]).T
    dC = np.array([np.polyval(np.polyder(coef[:, k]), tt) for k in range(3)]).T
    # letter height: the photo's letter length over the camera's px per metre across the curve (his right side)
    x = H.PRINT_CAMS[e["right"]["view"]]
    hs = []
    for i in range(n_cells):
        if e["right"]["px"][n_cells - 1 - i] is None:
            continue
        j = np.argmin(np.linalg.norm(P - C[i] * MX, axis=1))
        n = N[j]
        d = -(dC[i] * MX)
        u = d - n * (d @ n); u /= np.linalg.norm(u)
        v = np.cross(n, u)
        a_, _ = H.cam_project(x, np.array([P[j] - 0.001 * v, P[j] + 0.001 * v]))
        hs.append(e["cap_px"] / np.linalg.norm(a_[1] - a_[0]) * 0.002)
    cap = float(np.median(hs))
    log("eight point five: points kept", int(keep.sum()), "of", len(keep), "residual mm",
        round(float(res[keep].max() * 1000), 2), "cell pitch mm",
        round(float(np.median(np.linalg.norm(np.diff(C, axis=0), axis=1)) * 1000), 2), "cap height mm", round(cap * 1000, 2))
    frames = []
    for i, ch in enumerate(e["text"]):
        if ch == " ":
            continue
        img, _ = art_image("glyph:" + ch)
        hpx = img.shape[0] / 1.3                     # cap height in the glyph image
        for side in ("L", "R"):
            if side == "L":
                pt, d = C[i], dC[i]
            else:                                     # mirrored curve, read the other way
                k = n_cells - 1 - i
                pt, d = C[k] * MX, -(dC[k] * MX)
            j = np.argmin(np.linalg.norm(P - pt, axis=1))
            o, n = P[j], N[j]
            u = d - n * (d @ n); u /= np.linalg.norm(u)
            fr = dict(name=f"eight{i}{side}", art="glyph:" + ch, ink=e["ink"], surface=0, o=o.tolist(), u=u.tolist(),
                      v=np.cross(n, u).tolist(), n=n.tolist(), cu=0.0, cv=0.0)
            rot = cap / hpx
            zc = complex(img.shape[1] / 2, -0.65 * hpx)      # the middle of the capitals on the curve
            fr["sim"] = [rot, 0.0, -(rot * zc).real, -(rot * zc).imag]
            frames.append(fr)
    return frames


def element_colours(t, frames):
    """Colour of the elements drawn in the traced colour under them (the back icon's teal): median de-lit colour of
    the traced texels well inside the art."""
    d = t["d"]
    out = {}
    for fr in frames:
        if fr.get("ink") != "trace":
            continue
        img, _ = art_image(fr["art"])
        px = frame_px(fr, d["P"], d["N"])
        ok = ~np.isnan(px[:, 0]) & (d["S"] == fr["surface"])
        from scipy import ndimage
        core = ndimage.binary_erosion(img[..., 3] > 0.5, iterations=max(2, int(0.08 * min(img.shape[:2]))))
        a = np.zeros(len(px))
        a[ok] = ndimage.map_coordinates(core.astype(np.float32), [px[ok, 1], px[ok, 0]], order=0)
        sel = (a > 0.5) & (t["own"] >= 0)
        out[fr["name"]] = np.median(t["alb"][sel], 0).round(1).tolist() if sel.sum() > 20 else [30.0, 160.0, 140.0]
    return out


def erase_mask(frames, P, N, S, grow=0.0012, rgb=None):
    """Shell points under any element (grown by `grow` m): the traced copies there are not used. Also the ink each
    such point should not be filled with (the element's own; rgb: element_colours), -1 for none: a white word
    knocked out of a coloured band is filled with the band, so the photo's copy of the word, a little off the drawn
    one, never shows beside it."""
    from scipy import ndimage
    out = np.zeros(len(P), bool)
    excl = np.full(len(P), -1)
    cache = {}
    for fr in frames:
        img, key = frame_art(fr) if "polys" in fr or fr["art"] not in cache else (None, fr["art"])
        if img is not None:
            cache[key] = img[..., 3] > 0.3
        m = cache[key]
        g = fr.get("erase_grow", grow) / px_size(fr)
        m = ndimage.distance_transform_edt(~m) <= g
        sel = S == fr["surface"]
        px = frame_px(fr, P[sel], N[sel])
        ok = ~np.isnan(px[:, 0])
        v = np.zeros(sel.sum())
        v[ok] = ndimage.map_coordinates(m.astype(np.float32), [px[ok, 1], px[ok, 0]], order=0, cval=0.0)
        idx = np.nonzero(sel)[0][v > 0.5]
        out[idx] = True
        e = own_ink(fr, rgb)
        if e >= 0:
            excl[idx] = e
    return out, excl


def own_ink(fr, rgb=None):
    """The traced ink an element is printed in (white, black, or the traced colour's class), -1 for a decal."""
    ink = fr.get("ink")
    if ink in ("white", "black"):
        return INKS.index(ink)
    if ink == "trace" and rgb:
        return int(classify(np.array([rgb[fr["name"][:-2] if fr["name"].endswith("_R") else fr["name"]]]))[0])
    return -1


# The brow badge and vents as goggle.py measured them (its paint_brow_badge drew them over the old projected
# atlas; one source of numbers): badge z range, half widths bottom and top, corner radius, the white LEATT's width
# and centre height (its height here from the file's aspect), the badge purple, the vent quad (his right, mirrored),
# and the plain brow round them.
import goggle as G          # noqa: E402
BADGE_Z, BADGE_HW, BADGE_CORNER = G.BADGE_Z, G.BADGE_HW, G.BADGE_CORNER
BADGE_LOGO = dict(width=G.BADGE_LOGO["width"], zc=G.BADGE_LOGO["zc"])
BADGE_RGB, VENT_QUAD, BROW_BOX = G.BADGE_RGB, G.VENT_QUAD, G.BROW_BOX


def brow_zone(P, N):
    return (P[:, 1] < -0.09) & (N[:, 1] < 0) & (np.abs(P[:, 0]) < BROW_BOX[0]) & (P[:, 2] > BROW_BOX[1]) & \
        (P[:, 2] < BROW_BOX[2])


def badge_outline(n=8):
    (z0, z1), (w0, w1), r = BADGE_Z, BADGE_HW, BADGE_CORNER
    pts = [(-w0, z0), (w0, z0)]
    for sgn in (1, -1):
        c = (sgn * (w1 - r), z1 - r)
        arc = np.linspace(0, math.pi / 2, n) if sgn > 0 else np.linspace(math.pi / 2, math.pi, n)
        pts += [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in arc]
    return np.array(pts)


def draw_brow(P, N, col):
    """The brow: plain white, the two vents (dark mesh in a moulded rim), the purple badge, Leatt's wordmark."""
    from matplotlib.path import Path
    from scipy import ndimage
    z = brow_zone(P, N)
    if not z.any():
        return
    xz = P[z][:, [0, 2]]
    c = np.tile(np.array(WHITE, np.float32), (len(xz), 1))
    for sgn in (1, -1):
        q = np.array(VENT_QUAD) * [sgn, 1]
        ins = Path(q).contains_points(xz)
        qc = q.mean(0)
        rim = Path(qc + (q - qc) * 1.12).contains_points(xz) & ~ins
        uu = (xz[:, 0] + xz[:, 1]) / 0.0016
        vv = (xz[:, 0] - xz[:, 1]) / 0.0016
        mesh = (np.abs(uu - np.round(uu)) < 0.12) | (np.abs(vv - np.round(vv)) < 0.12)
        c[ins] = np.where(mesh[ins, None], [92, 92, 98], [26, 26, 30])
        c[rim] = np.array(WHITE) * 0.82
    b = Path(badge_outline()).contains_points(xz)
    c[b] = BADGE_RGB
    m = wordmark_mask()
    w = BADGE_LOGO["width"]; h = w * m.shape[0] / m.shape[1]
    mx = (xz[:, 0] + w / 2) / w * (m.shape[1] - 1)
    my = (BADGE_LOGO["zc"] + h / 2 - xz[:, 1]) / h * (m.shape[0] - 1)
    a = ndimage.map_coordinates(m, [my, mx], order=1, cval=0.0) * b
    c = c * (1 - a[:, None]) + a[:, None] * np.array([240, 240, 244.0])
    col[z] = c


# The crown's centre stripe (round 3), from the top photo at 1:1 (px): the teal block either side of the purple
# stem below the turbine, and the chevron: its sides straight (the teal's outer edges, x 871.7 and 1059.2), its
# top two diagonals from the stem (950 / 983.3 at y 595) to the sides (y 728.3), a white step notch at its lower
# left (in at y 861.7 to x 915.4 at y 887.5, down to y 945) and its lower edge a diagonal down to the right, parallel
# to the italic LEATT below (to 1059.2, 1028.8). It is not mirror-symmetric, so the trace (every texel read at its
# point on his left half) drew it symmetric and blobby, split where the top and back views meet. Here each shell
# or visor texel is looked up at its own place in the top view (helmet.PRINT_CAMS["top"]), and inside the outlines it
# takes a smooth colour field measured in the photo (helmet_art_stripe.png: the photo de-lit by the white either
# side of the stripe, a white level linear in y, 212 at y 450 to 229 at y 1050; normalised Gaussian 5 px inside
# each outline, 3 px in from its edge, the moulded ridge's reflection rows left out). Round them a white margin
# (25 px, 6 mm) clears what the trace left outside. The turbine disc is stamped over the stem's top afterwards.
STRIPE = dict(view="top", box=(830, 430, 1100, 1060), cos=0.15, sigma=5.0, ridge=(780, 818),
              white_cols=[(822, 856), (1075, 1110)],
              white=[(846, 440), (1085, 440), (1085, 1040), (1050, 1056), (890, 960), (890, 894), (846, 868)],
              teal=[(871.7, 440), (1059.2, 440), (1059.2, 728.3), (871.7, 728.3)],
              purple=[(950.0, 440), (983.3, 440), (983.3, 595.0), (1059.2, 728.3), (1059.2, 1028.8),
                      (1054.4, 1031.9), (915.4, 945.0), (915.4, 887.5), (871.7, 861.7), (871.7, 728.3),
                      (950.0, 595.0)])
STRIPE_FIELD = os.path.join(HERE, "helmet_art_stripe.png")


def stripe_field(log=print):
    """Trace: the stripe's colour fields in STRIPE's box of the top photo (teal left half, purple right half of
    helmet_art_stripe.png, sRGB)."""
    from PIL import Image
    from matplotlib.path import Path
    from scipy import ndimage
    s = STRIPE
    ph = load_photo(s["view"])
    a = ph[..., 3:] / 255.0
    rgb = ph[..., :3] * a + 255.0 * (1 - a)
    x0, y0, x1, y1 = s["box"]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    pts = np.c_[xx.ravel() + 0.5, yy.ravel() + 0.5]
    sub = rgb[y0:y1, x0:x1].reshape(-1, 3)
    ridge = (pts[:, 1] >= s["ridge"][0]) & (pts[:, 1] <= s["ridge"][1])
    wm = np.zeros(len(pts), bool)
    for c0, c1 in s["white_cols"]:
        wm |= (pts[:, 0] >= c0) & (pts[:, 0] < c1)
    wm &= (sub.min(1) > 150) & ~ridge
    A = np.c_[np.ones(len(pts)), pts[:, 1] / 1000.0]
    level = A @ np.linalg.lstsq(A[wm], srgb_to_lin(sub[wm]), rcond=None)[0]
    shape = (y1 - y0, x1 - x0)
    alb = (srgb_to_lin(sub) / level * srgb_to_lin(np.array(WHITE, float))).reshape(shape + (3,))
    halves = []
    for name, excl in (("teal", "purple"), ("purple", None)):
        m = Path(s[name]).contains_points(pts)
        if excl:
            m &= ~Path(s[excl]).contains_points(pts)
        m = ndimage.binary_erosion(m.reshape(shape), iterations=3) & ~ridge.reshape(shape)
        f, den = norm_blur(alb, m.astype(np.float32), s["sigma"])
        far, _ = norm_blur(alb, m.astype(np.float32), 4 * s["sigma"])
        halves.append(lin_to_srgb(np.where((den > 0.05)[..., None], f, far)))
    Image.fromarray(np.clip(np.hstack(halves), 0, 255).round().astype(np.uint8)).save(STRIPE_FIELD, optimize=True)
    log("stripe field", STRIPE_FIELD)


def stripe_lookup(P, N):
    """Each point's place in the stripe's view (px) and whether it shows there squarely enough (depth test
    against the points given: the shell and the visor's top)."""
    uv, vis, cos = view_lookup(STRIPE["view"], P, N, P)
    return uv, vis & (cos > STRIPE["cos"])


def draw_stripe(P, N, col, white):
    """The centre stripe at its own place on the shell and the visor's top (no mirror): the white margin, then the
    teal and the purple outlines in their fields."""
    from PIL import Image
    from matplotlib.path import Path
    from scipy import ndimage
    s = STRIPE
    fimg = np.asarray(Image.open(STRIPE_FIELD).convert("RGB"), np.float32)
    x0, y0, x1, y1 = s["box"]
    w = x1 - x0
    sel = np.nonzero(P[:, 2] > 0.05)[0]
    uv, ok = stripe_lookup(P[sel], N[sel])
    col[sel[Path(s["white"]).contains_points(uv) & ok]] = white
    for j, name in enumerate(("teal", "purple")):
        ins = Path(s[name]).contains_points(uv) & ok
        q = uv[ins] - [x0, y0] - 0.5
        qx = np.clip(q[:, 0], 0, w - 1) + j * w
        qy = np.clip(q[:, 1], 0, y1 - y0 - 1)
        col[sel[ins]] = np.stack([ndimage.map_coordinates(fimg[..., k], [qy, qx], order=1) for k in range(3)], -1)


# The crown's two vents: a white moulded insert with a triangle lattice over the dark opening. Round 3 (decision 46)
# builds the insert and the lattice as geometry (helmet_detail.py, through the same top camera); the print keeps
# the insert's colour under them and the opening dark (no painted bars: they would double the built ones). Leatt's top
# photo px, the vent on his right (image left); his left gets the mirror.
# Round 4 (decision 50), traced again at 5x (helmet round 4 ledger): the opening is a parallelogram whose sides run
# along the lattice's two bar directions, its corners rounded; the insert is a thin, even surround round it.
#   opening  the convex hull of the dark holes (darker than 60, opened by 3 px) fitted with four lines: top -23,
#            right 94, bottom -21, left 100 deg; corners rounded 6 px (the hull stands 2 to 4.6 px inside the
#            lines' corners)
#   rim      7 to 9 px wide all round at 5x (its outer edge: the thin dark gap on the shell): 8 px
#   lattice  fitted to the photo's brightness in the opening as a triangle lattice: a 24.1 px at -21 deg, b 24.2 px
#            at 98.5 deg, 119.5 deg apart (a + b 24.3 px at 39 deg): near-equilateral cells, bars along a, b and
#            a + b, 21 px apart (main: a right-angled grid with bars along the vent's long axis)
CROWN_VENT = dict(view="top", opening=[(700.9, 618.4), (764.3, 591.3), (756.7, 712.5), (678.8, 742.1)],
                  corner=6.0, rim=8.0, origin=(725.9, 643.5), a=(22.46, -8.61), b=(-3.57, 23.95))


def _grow_quad(q, d):
    """A convex quadrilateral's corners with every side moved d px outwards (parallel)."""
    q = np.asarray(q, float)
    c = q.mean(0)
    lines = []
    for i in range(4):
        a, b = q[i], q[(i + 1) % 4]
        t = (b - a) / np.linalg.norm(b - a)
        n = np.array([t[1], -t[0]])
        n = n if (a - c) @ n > 0 else -n
        lines.append((n, n @ a + d))
    return np.array([np.linalg.solve(np.array([lines[i - 1][0], lines[i][0]]), [lines[i - 1][1], lines[i][1]])
                     for i in range(4)])


CROWN_VENT["insert"] = np.round(_grow_quad(CROWN_VENT["opening"], CROWN_VENT["rim"]), 1).tolist()


def round_quad(q, r, n=8):
    """A convex polygon with its corners rounded to radius r (px): arcs tangent to both sides, n points each."""
    q = np.asarray(q, float)
    out = []
    m = len(q)
    for i in range(m):
        a, b, c = q[i - 1], q[i], q[(i + 1) % m]
        u, v = (a - b) / np.linalg.norm(a - b), (c - b) / np.linalg.norm(c - b)
        ang = math.acos(np.clip(u @ v, -1, 1))
        d = r / math.tan(ang / 2)
        p0, p1 = b + u * d, b + v * d
        bis = (u + v) / np.linalg.norm(u + v)
        ctr = b + bis * r / math.sin(ang / 2)
        a0, a1 = math.atan2(*(p0 - ctr)[::-1]), math.atan2(*(p1 - ctr)[::-1])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for t in np.linspace(0, 1, n):
            out.append(ctr + r * np.array([math.cos(a0 + da * t), math.sin(a0 + da * t)]))
    return np.array(out)


def vent_outline(kind):
    """The crown vent's opening or insert outline (top photo px, rounded): the insert's corners are the opening's
    grown by the rim (radius corner + rim), so the surround is even."""
    v = CROWN_VENT
    if kind == "opening":
        return round_quad(v["opening"], v["corner"])
    return round_quad(v["insert"], v["corner"] + v["rim"])

VENT_BAR_RGB = (209, 213, 219)      # top photo, bars de-lit (now built: helmet.MATERIALS helmet_vent_insert)
VENT_RIM_RGB = (202, 206, 214)      # the insert's moulded rim, same measure
VENT_HOLE_RGB = (24, 23, 25)        # the opening (photo: 0 0 0): the print's black ink, one black in the print


def draw_crown_vents(P, N, S, col):
    from matplotlib.path import Path
    v = CROWN_VENT
    sel = np.nonzero((S == 0) & (P[:, 2] > 0.05) & (N[:, 2] > 0.3))[0]
    for sg in (np.ones(3), MX):
        Q, Nq = P[sel] * sg, N[sel] * sg
        uv, vis, cos = view_lookup(v["view"], Q, Nq, Q)
        ok = vis & (cos > 0.2)
        ins = Path(vent_outline("insert")).contains_points(uv) & ok
        op = Path(vent_outline("opening")).contains_points(uv) & ok
        c = col[sel]
        c[ins] = VENT_RIM_RGB
        c[op] = VENT_HOLE_RGB
        col[sel] = c


def stamp(col, P, N, fr, img, rgb, texel):
    """Composite an element's art (premultiplied RGBA) over texel colours: rgb None = the art's own colours. The
    art is pre-blurred to the texel's footprint (no aliasing of fine strokes)."""
    from scipy import ndimage
    o = np.asarray(fr["o"])
    rot = px_size(fr)
    h, w = img.shape[:2]
    rad = fr["proj"]["radius"] if "proj" in fr else rot * math.hypot(w, h * fr.get("aspect", 1.0)) * 0.75 + 0.003
    near = np.nonzero(np.linalg.norm(P - o, axis=1) < rad)[0]
    px = frame_px(fr, P[near], N[near])
    ok = ~np.isnan(px[:, 0]) & (px[:, 0] > -2) & (px[:, 0] < w + 1) & (px[:, 1] > -2) & (px[:, 1] < h + 1)
    if not ok.any():
        return 0
    idx, q = near[ok], px[ok]
    sig = 0.45 * texel / rot
    if sig > 0.5:
        img = np.stack([ndimage.gaussian_filter(img[..., k], sig) for k in range(4)], -1)
    a = ndimage.map_coordinates(img[..., 3], [q[:, 1], q[:, 0]], order=1, cval=0.0)
    if rgb is None:
        c = np.stack([ndimage.map_coordinates(img[..., k], [q[:, 1], q[:, 0]], order=1, cval=0.0)
                      for k in range(3)], -1) * 255.0
    else:
        c = a[:, None] * np.asarray(rgb, np.float32)[None]
    col[idx] = col[idx] * (1 - a[:, None]) + c
    return int((a > 0.5).sum())


def element_rgb(fr, data):
    ink = fr.get("ink")
    if ink in ("white", "black"):
        return data["inks"][ink]
    if ink == "trace":
        return data["element_rgb"][fr["name"][:-2] if fr["name"].endswith("_R") else fr["name"]]
    return None


def draw_elements(art, tex, data, log=print, tx=None):
    """The brow, Leatt's logos (their own files), the labels: each texel coloured from its own point on the shell,
    so the elements run across the atlas's island edges without a seam. tx: texels(tex), if already made."""
    r, c, P, N, S = tx if tx is not None else texels(tex)
    col = art[r, c].astype(np.float32)
    draw_brow(P, N, col)
    draw_crown_vents(P, N, S, col)
    draw_stripe(P, N, col, np.asarray(data["inks"]["white"], np.float32))
    texel = 1.0 / (H.ATLAS_K * tex / 4096.0)
    cache = {}
    for fr in data.get("frames", []):
        key = fr["name"] if "polys" in fr else fr["art"]
        if key not in cache:
            cache[key] = frame_art(fr)[0]
        sel = np.nonzero(S == fr["surface"])[0]
        sub = col[sel]
        n = stamp(sub, P[sel], N[sel], fr, cache[key], element_rgb(fr, data), texel)
        col[sel] = sub
        if not fr["name"].startswith("eight"):
            log(fr["name"], "texels", n)
    art[r, c] = col
    return art


if __name__ == "__main__":
    if sys.argv[1] == "trace":
        t = trace()
        frames = element_frames()
        d = t["d"]
        rgb = element_colours(t, frames)
        erased, exclude = erase_mask(frames, d["P"], d["N"], d["S"], rgb=rgb)
        print("erased texels (elements redrawn from files)", int(erased.sum()))
        reg, probs, fields = regions(t, erased=erased, exclude=exclude)
        save_trace(t, reg, probs, fields, extra=dict(frames=frames, element_rgb=rgb))
        stripe_field()
    elif sys.argv[1] == "draw":
        draw(sys.argv[2] if len(sys.argv) > 2 else None)
