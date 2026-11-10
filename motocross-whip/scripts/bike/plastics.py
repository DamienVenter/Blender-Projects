"""The CRF250R's plastics as measured 3D surfaces (stock Honda, 2025/2026 bodywork).

Every surface is tied to Honda's studio photos through the calibrated cameras (cams.py):
  side outline   the exact outline in the left or right profile photo (outlines.py); every vertex of a panel lies on
                 the ray through its photo pixel, so the model's side view IS the photo's outline
  plan widths    the red envelope of the top photo, column by column (measure.py)
  sections       the outer silhouette of the front photo (shroud fins) and of the rear photo (side panels)
  number plate   its outline in the front photo, cast onto the plate's inclined, folded surface
  creases        brightness steps in the photos (rows and columns quoted at each one), built as changes of the
                 surface's angle along rows of vertices (plate_lines)
Cross-check 2026-11-10: shroud half-width 0.199 m from the top photo, 0.201 m from the front photo.

Tags as in parts.py: OUT/OUT2 outlines, TOP/FRONT/REAR photo measurements, EST estimated.
"""
import functools
import json
import math
import os

import numpy as np

import cams
from geom import Mesh, bolt, grid, inside, plate2d, resample, rounded_rect, smooth_poly

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "research")
OUT = json.load(open(os.path.join(RES, "bike-outlines.json")))
OUT2 = json.load(open(os.path.join(RES, "bike-outlines2.json")))
MEAS = json.load(open(os.path.join(RES, "bike-plastics.json")))
TOP, FRONT, REAR, LEFT, RIGHT = (cams.CAMS[k] for k in ("top", "front", "rear", "left", "right"))


def sat(x):
    return min(max(x, 0.0), 1.0)


def smoothstep(x):
    x = sat(x)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- plan tables from the top photo
def _top_tables():
    xs, yl, yr, sl, sr, gl, gr = [], [], [], [], [], [], []
    for e in MEAS["top"]:
        u = e["u"]
        x = TOP.on_plane(u, 1123, "z", 0.90)[0][0]
        a, b = (TOP.on_plane(u, v, "z", 0.88)[0][1] for v in e["red"])        # v_min = right side (y < 0)
        xs.append(x); yr.append(-a); yl.append(b)
        if "seat" in e:
            a, b = (TOP.on_plane(u, v, "z", 0.97)[0][1] for v in e["seat"])
            sr.append(-a); sl.append(b)
        else:
            sr.append(np.nan); sl.append(np.nan)
        if "gap" in e:
            a, b = (TOP.on_plane(u, v, "z", 1.0)[0][1] for v in e["gap"])
            gr.append(-a); gl.append(b)
        else:
            gr.append(np.nan); gl.append(np.nan)
    o = np.argsort(xs)
    return {k: np.array(v)[o] for k, v in dict(x=xs, left=yl, right=yr, seat_l=sl, seat_r=sr, gap_l=gl, gap_r=gr).items()}


TT = _top_tables()


def _smooth(a, n=5):
    k = np.ones(n) / n
    return np.convolve(np.pad(a, n // 2, mode="edge"), k, mode="valid")


_PLAN = {1: _smooth(TT["left"], 9), -1: _smooth(TT["right"], 9)}


def plan_half_width(x, side):
    """Half-width (m, positive) of the red bodywork's plan envelope at x on the given side (+1 left, -1 right): TOP."""
    return float(np.interp(x, TT["x"], _PLAN[1 if side > 0 else -1]))


def _top_edge_table(ref):
    """Smoothed upper edge z(x) of an outline (x, z), as an interpolation function."""
    xs = np.arange(ref[:, 0].min() + 0.004, ref[:, 0].max() - 0.004, 0.004)
    zs = np.array([_poly_top(ref, x) for x in xs])
    ok = np.isfinite(zs)
    xs, zs = xs[ok], _smooth(zs[ok], 7)
    return lambda x: float(np.interp(x, xs, zs))


# seat plan half-width (TOP, seat cover mask; the readings ahead of x 0.76 pick up shroud highlights and are replaced
# by the seat's visible rounded nose)
SEAT_X = [0.080, 0.100, 0.180, 0.250, 0.330, 0.400, 0.480, 0.550, 0.630, 0.700, 0.750, 0.780, 0.800]
SEAT_HW = [0.040, 0.060, 0.086, 0.088, 0.088, 0.088, 0.088, 0.087, 0.079, 0.075, 0.062, 0.042, 0.015]


def seat_hw(x):
    return float(np.interp(x, SEAT_X, SEAT_HW))


# ---------------------------------------------------------------- panels seen through a profile photo
MPP = (4.7 - 0.17) / 6075.0          # metres per photo pixel at the panels' distance from the side cameras


def clean_outline(view, pts_mm, sigma=5.0, step=3.0):
    """A traced outline (bike-outlines.json, mm) as a closed curve in photo pixels: evenly resampled every STEP px and
    smoothed along its length with a Gaussian of SIGMA px (5 px = 4 mm). The traced outlines carry pixel steps and
    mask noise of 1 to 3 px; fed straight into the panels they tore every rolled edge and wrinkled the surfaces
    (close-up renders, 2026-11-10). Corners tighter than about 4 mm are rounded to that."""
    from scipy.ndimage import gaussian_filter1d
    from geom import resample
    u, v = cams.linear_to_px(view, np.asarray(pts_mm, float)[:, 0], np.asarray(pts_mm, float)[:, 1])
    P = resample(np.stack([u, v], axis=1), step)
    k = sigma / step
    return np.stack([gaussian_filter1d(P[:, 0], k, mode="wrap"), gaussian_filter1d(P[:, 1], k, mode="wrap")], axis=1)


class Edges:
    """Which way each point of a cleaned outline faces, and distances from any pixel to the outline's front-facing
    and top-facing parts. Rolled edges and shoulders are functions of these DISTANCES, so they are zero exactly on
    the outline and smooth along it (as functions of a separately smoothed edge table they zig-zagged)."""

    def __init__(self, view, px):
        from scipy.spatial import cKDTree
        t = np.roll(px, -1, axis=0) - np.roll(px, 1, axis=0)
        n = np.stack([t[:, 1], -t[:, 0]], axis=1)
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]
        if inside(px, (px + 3.0 * n)[::7]).mean() > 0.5:          # make the normals point out of the shape
            n = -n
        fwd = -1.0 if view == "left" else 1.0                     # the bike's front is at the left of the left photo
        self.px, self.n = px, n
        self.front = n[:, 0] * fwd > 0.5
        self.top = n[:, 1] < -0.6
        # distances are taken to the edge sampled every 0.25 px: against the outline's own points (3 px apart) the
        # distance of a vertex ON the edge wandered between 0 and 1.5 px and the rolled edges came out scalloped
        k = np.linspace(0.0, 1.0, 12, endpoint=False)[None, :, None]
        dense = (px[:, None, :] + (np.roll(px, -1, axis=0) - px)[:, None, :] * k).reshape(-1, 2)
        self._front = cKDTree(dense[np.repeat(self.front | np.roll(self.front, -1), 12)])
        self._top = cKDTree(dense[np.repeat(self.top | np.roll(self.top, -1), 12)])

    def d_front(self, u, v):
        return float(self._front.query((u, v))[0]) * MPP

    def d_top(self, u, v):
        return float(self._top.query((u, v))[0]) * MPP


def _on_surface(cam, u, v, f, y0):
    """3D point where the ray through pixel (u, v) meets the surface y = f(x, z) (fixed-point iteration)."""
    y = y0
    for _ in range(6):
        P = cam.on_plane(u, v, "y", y)[0]
        y = f(P[0], P[2])
    return cam.on_plane(u, v, "y", y)[0]


def _poly_top(poly, x):
    """Highest z of a closed polygon (x, z) at abscissa x."""
    P = np.asarray(poly, float)
    zs = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]:
            zs.append(a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    return max(zs) if zs else float("nan")


def _poly_bottom(poly, x):
    P = np.asarray(poly, float)
    zs = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]:
            zs.append(a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    return min(zs) if zs else float("nan")


def _true_outline(view, pts_mm, y):
    u, v = cams.linear_to_px(view, np.asarray(pts_mm, float)[:, 0], np.asarray(pts_mm, float)[:, 1])
    return cams.CAMS[view].on_plane(u, v, "y", y)[:, [0, 2]]



# ---------------------------------------------------------------- meshing with feature lines
def _dense(poly, sub=12, closed=False):
    """A polyline sampled SUB times per segment (for exact distances to it)."""
    P = np.asarray(poly, float)
    Q = np.vstack([P, P[:1]]) if closed else P
    k = np.linspace(0.0, 1.0, sub, endpoint=False)[None, :, None]
    D = (Q[:-1, None, :] + (Q[1:] - Q[:-1])[:, None, :] * k).reshape(-1, 2)
    return np.vstack([D, Q[-1:]])


def _mpx(view, pts):
    """Pixels measured in the LEFT photo, for the given profile photo. The two photos mirror each other about column
    1999.5 at equal rows (shroud bolts at u 1702 and 2297, seat bolts at 2172 and 1827, all on the same rows)."""
    P = np.array(pts, float)
    if view == "right":
        P[:, 0] = 3999.0 - P[:, 0]
    return P


def plate_lines(outer, holes, thickness, mat, to3d, step, rings=(), lines=(), line_step=None, single=False):
    """geom.plate2d with feature lines: rows of vertices along LINES (polylines in the plate's 2D space), so a
    surface can change angle exactly on a crease or drop into a pocket with a clean edge. line_step: spacing of the
    vertices along the lines. single: one surface only (no thickness, for parts solidified in Blender)."""
    from scipy.spatial import Delaunay, cKDTree
    loops = [resample(outer, step * 0.7)] + [resample(h, step * 0.5) for h in holes]
    B = np.vstack(loops)
    btree = cKDTree(B)
    ls = line_step or 0.6 * step

    def ok_inside(Q):
        ok = inside(loops[0], Q)
        for h in loops[1:]:
            ok &= ~inside(h, Q)
        return ok
    Ls = []
    for ln in lines:
        ln = np.asarray(ln, float)
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(ln, axis=0), axis=1))])
        t = np.linspace(0, s[-1], max(int(s[-1] / ls), 2) + 1)
        Q = np.stack([np.interp(t, s, ln[:, 0]), np.interp(t, s, ln[:, 1])], axis=1)
        Q = Q[ok_inside(Q) & (btree.query(Q)[0] > 0.6 * ls)]
        if len(Ls) and len(Q):
            Q = Q[cKDTree(np.vstack(Ls)).query(Q)[0] > 0.5 * ls]
        if len(Q):
            Ls.append(Q)
    Lp = np.vstack(Ls) if Ls else np.zeros((0, 2))
    ltree = cKDTree(Lp) if len(Lp) else None
    rows = []
    if len(rings):
        L = loops[0]
        t = np.roll(L, -1, axis=0) - np.roll(L, 1, axis=0)
        n = np.stack([t[:, 1], -t[:, 0]], axis=1)
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        if inside(L, (L + 0.3 * step * n)[::5]).mean() < 0.5:        # make the normals point into the shape
            n = -n
        for d in rings:
            Q = L + d * n
            Q = Q[ok_inside(Q) & (btree.query(Q)[0] > 0.8 * d)]      # not across a thin tip or a concave corner
            if ltree is not None and len(Q):
                Q = Q[ltree.query(Q)[0] > 0.8 * ls]
            if len(rows) and len(Q):
                Q = Q[cKDTree(np.vstack(rows)).query(Q)[0] > 0.45 * step]
            if len(Q) > 1:
                keep = [0]
                for i in range(1, len(Q)):
                    if np.hypot(*(Q[i] - Q[keep[-1]])) > 0.45 * step:
                        keep.append(i)
                Q = Q[keep]
            if len(Q):
                rows.append(Q)
    R = np.vstack(rows) if rows else np.zeros((0, 2))
    lo, hi = loops[0].min(axis=0), loops[0].max(axis=0)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0], step), np.arange(lo[1], hi[1], step))
    G = np.stack([gx.ravel(), gy.ravel()], axis=1)
    G = G[ok_inside(G)]
    if len(G):
        G = G[btree.query(G)[0] > (0.45 * step if not len(rings) else max(rings) + 0.5 * step)]
    if ltree is not None and len(G):
        G = G[ltree.query(G)[0] > max(0.5 * step, ls)]
    P = np.vstack([B, Lp, R, G])
    tri = Delaunay(P).simplices
    tri = tri[ok_inside(P[tri].mean(axis=1))]
    m = Mesh()
    if single:
        top = m.verts([to3d(u, v, 0.0) for u, v in P])
        for a, b, cc in tri:
            m.face((top + a, top + b, top + cc), mat)
        return m
    top = m.verts([to3d(u, v, thickness / 2) for u, v in P])
    bot = m.verts([to3d(u, v, -thickness / 2) for u, v in P])
    for a, b, cc in tri:
        m.face((top + a, top + b, top + cc), mat)
        m.face((bot + a, bot + cc, bot + b), mat)
    o = 0
    for k, L in enumerate(loops):
        n = len(L)
        for i in range(n):
            j = (i + 1) % n
            f = (top + o + i, bot + o + i, bot + o + j, top + o + j)
            m.face(f if k == 0 else f[::-1], mat)
        o += n
    return m


def photo_panel(view, outer_px, surf, thickness, mat, holes_px=(), step=11.0, rings=(), lines=(), line_step=None):
    """Shell whose side view is exactly OUTER_PX (closed curve, photo pixels) in the VIEW photo: meshed in the
    photo's pixel space, every vertex put on the surface along its pixel's ray, THICKNESS toward the bike's centre.
    surf(u, v) returns the function y = f(x, z) to use at that pixel (so a surface can depend on where the pixel is
    in the outline). Holes are cut through. step: mesh size in pixels (about 0.78 mm each). rings: rows of vertices
    parallel to the outline; lines: rows of vertices along creases and pocket edges (photo pixels)."""
    cam = cams.CAMS[view]
    sgn = 1.0 if view == "left" else -1.0
    y0 = sgn * 0.15
    hit = {}

    def to3d(u, v, w):                 # offsets w in [-t/2, t/2]: the outer face (w = t/2) is the surface
        key = (round(float(u), 3), round(float(v), 3))
        if key not in hit:
            hit[key] = _on_surface(cam, u, v, surf(u, v), y0)
        P = hit[key]
        return (P[0], P[1] - sgn * (thickness / 2 - w), P[2])
    return plate_lines(outer_px, list(holes_px), thickness, mat, to3d, step, rings=rings, lines=lines,
                       line_step=line_step)


def _cut(px, keep, every=False):
    """The part of a closed pixel outline where keep(u, v) holds, as a closed curve (rasterised at half pixels,
    contoured, resampled every 3 px and smoothed over 2 px). every: all the pieces, largest first."""
    from PIL import Image, ImageDraw
    import contourpy
    from scipy.ndimage import gaussian_filter1d
    S = 2
    lo = np.floor(px.min(axis=0)) - 4
    n = np.ceil((px.max(axis=0) - lo + 4) * S).astype(int)
    im = Image.new("L", (int(n[0]), int(n[1])), 0)
    ImageDraw.Draw(im).polygon([(float((a - lo[0]) * S), float((b - lo[1]) * S)) for a, b in px], fill=1)
    uu, vv = np.meshgrid(lo[0] + np.arange(n[0]) / S, lo[1] + np.arange(n[1]) / S)
    m = (np.asarray(im) > 0) & keep(uu, vv)
    out = []
    for c in sorted(contourpy.contour_generator(z=m.astype(float)).lines(0.5), key=len, reverse=True):
        if len(c) < 60 * S and out:                        # crumbs (the largest piece is always kept)
            continue
        P = resample(c[:-1] / S + lo, 3.0)
        out.append(np.stack([gaussian_filter1d(P[:, 0], 0.7, mode="wrap"),
                             gaussian_filter1d(P[:, 1], 0.7, mode="wrap")], axis=1))
    return out if every else out[0]


def _gauss(a, sigma):
    from scipy.ndimage import gaussian_filter1d
    return gaussian_filter1d(np.asarray(a, float), sigma, mode="nearest")


def _longest_run(mask, gap=8):
    """Indices of the longest run of True in a circular mask (gaps of up to GAP samples are bridged)."""
    n = len(mask)
    m = np.concatenate([mask, mask]).copy()
    idx = np.where(m)[0]
    for a, b in zip(idx[:-1], idx[1:]):
        if 1 < b - a <= gap:
            m[a:b] = True
    best, i = (0, 0), 0
    while i < 2 * n:
        if m[i]:
            j = i
            while j < 2 * n and m[j]:
                j += 1
            if j - i > best[1] - best[0]:
                best = (i, j)
            i = j
        else:
            i += 1
    return np.arange(best[0], min(best[1], best[0] + n)) % n


# ---------------------------------------------------------------- shrouds
def _shroud_plan(side):
    """Half-width of a shroud's side face along x (TOP): a smooth curve through the top photo's red envelope from
    x 0.60 to 1.09. The handlebar and cables cross the shroud in that photo and cut the envelope short around x 0.96
    and 0.98, so the curve is fitted with a robust loss and those columns do not pull it in."""
    from scipy.optimize import least_squares
    m = (TT["x"] > 0.60) & (TT["x"] < 1.093)
    x, w = TT["x"][m], TT["left" if side > 0 else "right"][m]
    sol = least_squares(lambda c: np.polyval(c, x - 0.85) - w, np.polyfit(x - 0.85, w, 4), loss="soft_l1", f_scale=0.002)
    return lambda q: float(np.polyval(sol.x, min(max(q, 0.60), 1.093) - 0.85))


LIP = 0.012          # FRONT: the leading edge shows as a red rim outside the radiator, 10 mm wide at mid height
SKIN_LIP = 0.005     # roll of the outer skin's own edge where it stops short over the inner wall (EST)
WALL_STEP = 0.008    # the inner wall ahead of the skin's edge sits this far in (FRONT: the rim it and the skin's edge
#                      make is 10 to 18 mm wide; the step itself is not measurable: EST)
WALL_TIP = 0.004     # and this much deeper at the lower tip, where the radiator's louvres show in the gap between
#                      the two layers (LEFT rows 1070..1170, u 1630..1690; depth EST: 12 mm put the wall inside
#                      parts.radiators, whose outer face is at 0.177)
SHOULDER_H, SHOULDER_IN = 0.038, 0.028      # FRONT: silhouette 0.198 at z 0.899, 0.188 at 0.917, 0.175 at 0.933,
#                                             on the section whose top edge is at 0.937: a flat facet (the three
#                                             readings are on one line), 38 mm tall, leaning in 28 mm
# The shoulder's lower crease behind the vents. LEFT columns 1800..1980: the surface is brighter below a line through
# rows 845, 821, 813, 803 (steps of +20 to +42 in r+g), 100 to 63 px under the top edge. Ahead of the vents the
# facet is the 38 mm of the front photo.
SHOULDER_PX = [(1800, 845), (1860, 821), (1920, 813), (1980, 803), (2012, 798)]
# The two air outlets behind the "CRF" decal. LEFT rows 900..1060: dark from u 1729..1767 (row 900), 1735..1774
# (940), 1742..1778 (980), 1747..1787 (1020), 1754..1783 (1060); column 1740: rows 861..948; a red bar between them
# at rows 949..977. Built as pockets, not holes: the real ones are open to the radiator's black louvres, and a dark
# part inside the shroud's outline is what the intruder test forbids.
VENTS_PX = [[(1731, 864), (1760, 864), (1770, 945), (1741, 948)],
            [(1745, 978), (1775, 975), (1785, 1040), (1772, 1092), (1764, 1092), (1752, 1035)]]
VENT_DEPTH = 0.010   # EST
# 1: the first pass's shroud: one surface, stepped in at the skin's edge, hollow shoulder 38 mm under the top edge.
# 2: skin and inner wall as two shells with the gap between them, the shoulder's measured crease behind the vents
#    and the two vent pockets. Close-up renders of 2 (2026-11-10) showed a saw-toothed leading edge, spikes along
#    the top edge and ragged pockets, not yet traced to their cause: 1 is built until 2 is clean.
SHROUD_LAYERS = 1


@functools.lru_cache(maxsize=None)
def _shroud(side):
    """A shroud's outline, its two layers and their surfaces.
    Side face: upright, at the plan envelope of the top photo (TOP). Checked against the front photo through the
    refitted camera: its outer silhouette is 0.200 m off the centre line at z 0.83..0.88 (top photo: 0.199 to 0.202),
    0.193 at z 0.74 and 0.185 at 0.68, which is the plan envelope at the x where the leading edge is at those heights.
    Two layers (LEFT and RIGHT photos, zoomed): the outer skin stops 35 to 80 mm short of the front edge between
    z 0.68 and 0.88; under it a separate inner wall, in shadow in the photos, runs on to the true front edge, which
    is rolled in by LIP (FRONT: red rim outside the black louvres). The wall lies WALL_STEP inside the skin, more at
    the lower tip, and tucks 11 mm under the skin's edge.
    Shoulder: a flat facet leaning in from a crease to the top edge (FRONT, LEFT). Inboard of it the top deck is
    built separately (shroud_decks)."""
    from types import SimpleNamespace
    from scipy.signal import medfilt
    from scipy.spatial import cKDTree
    name = "shroud" if side > 0 else "shroud_R"
    view = "left" if side > 0 else "right"
    fwd = -1.0 if view == "left" else 1.0
    px = clean_outline(view, OUT[name])
    E = Edges(view, px)
    plan = _shroud_plan(side)
    # edge of the outer skin (outlines.py 'shroud_skin') as a column per row of the photo; beyond its ends the line
    # curves forward and runs out through the leading edge
    sk = np.asarray(OUT["shroud_skin" + ("" if side > 0 else "_R")], float)
    su, sv = cams.linear_to_px(view, sk[:, 0], sk[:, 1])
    o = np.argsort(sv)
    sv, su = sv[o], _gauss(medfilt(su[o], 5), 3.0)
    sv_all, su_all = sv, su
    # the traced line's ends can run along the rows (it follows the decal's edge there): keep the part that runs
    # down the shroud (on the right side the stray end put a wedge of inner wall 150 px behind the leading edge)
    g = np.abs(np.gradient(su, sv))
    i0, i1 = 0, len(sv)
    while i0 < i1 - 12 and g[i0:i0 + 3].max() > 1.5:
        i0 += 1
    while i1 > i0 + 12 and g[i1 - 3:i1].max() > 1.5:
        i1 -= 1
    sv, su = sv[i0:i1], su[i0:i1]

    def skin_u(v):
        # beyond the line's ends: straight on along the rows, curving forward (extrapolated along its end slope,
        # which is nearly along the rows at the top, the line ran 150 px back into the skin and cut a wedge out)
        v = np.asarray(v, float)
        u = np.interp(v, sv, su)
        u = np.where(v < sv[0], su[0] + fwd * 0.035 * (sv[0] - v) ** 2, u)
        return np.where(v > sv[-1], su[-1] + fwd * 0.035 * (v - sv[-1]) ** 2, u)

    def ahead(u, v):                                   # px ahead of the skin's edge
        return fwd * (np.asarray(u, float) - skin_u(v))
    if SHROUD_LAYERS == 2:
        skin_px = _cut(px, lambda uu, vv: ahead(uu, vv) <= 0.0)
        wall_px = _cut(px, lambda uu, vv: (ahead(uu, vv) > -14.0) & (vv > sv[0] - 70.0) & (vv < sv[-1] + 70.0))
    else:
        skin_px, wall_px = px, None
    vd = np.arange(sv[0] - 70.0, sv[-1] + 70.0, 0.5)
    etree = cKDTree(np.stack([skin_u(vd), vd], axis=1))     # the skin's own edge, densely
    # shoulder crease: 38 mm under the top edge ahead of the vents, the measured line behind them
    top = px[E.top]
    ub = np.arange(px[:, 0].min(), px[:, 0].max() + 6.0, 6.0)
    tv = np.array([top[np.abs(top[:, 0] - q) < 6.0, 1].min() if (np.abs(top[:, 0] - q) < 6.0).any() else np.nan
                   for q in ub])
    ok = np.isfinite(tv)
    ub, tv = ub[ok], _gauss(tv[ok], 2.0)
    ul = ub if view == "left" else 3999.0 - ub
    sp = np.array(SHOULDER_PX, float)
    w = np.clip((ul - 1760.0) / 40.0, 0.0, 1.0)
    cv = _gauss((1 - w) * (tv + SHOULDER_H / MPP) + w * np.interp(ul, sp[:, 0], sp[:, 1]), 1.5)
    ok = ul <= sp[-1, 0]
    cr = np.stack([ub[ok], cv[ok]], axis=1)
    cr = cr[np.argsort(cr[:, 0])]
    ctree = cKDTree(_dense(cr))

    def inset(u):                                      # how far the shoulder leans in at the top edge, column u
        if SHROUD_LAYERS == 1:
            return SHOULDER_IN
        if u < cr[0, 0] or u > cr[-1, 0]:
            return 0.0
        band = float(np.interp(u, cr[:, 0], cr[:, 1]) - np.interp(u, ub, tv))
        return min(SHOULDER_IN, 0.74 * max(band, 0.0) * MPP)

    def shoulder(u, v):
        if SHROUD_LAYERS == 1:
            dt = E.d_top(u, v)
            return SHOULDER_IN * (1.0 - dt / SHOULDER_H) ** 2 if dt < SHOULDER_H else 0.0
        if u < cr[0, 0] or u > cr[-1, 0] or v >= float(np.interp(u, cr[:, 0], cr[:, 1])):
            return 0.0
        dc, dt = ctree.query((u, v))[0], E.d_top(u, v) / MPP
        t = dc / max(dc + dt, 1e-6)
        # ahead of the vents the facet is flat (FRONT); behind them, where it is up to 100 px tall, only the crease
        # line is measured: most of the lean is put near the top edge (EST; a flat facet there cut into the top of
        # parts.radiators at y 0.177), with a 10 deg change of angle left on the crease
        # (and ahead of the vents a mix of 0.35 flat and 0.65 hollow: against FRONT it gives 23 / 9 / 0 mm where the
        # photo has 25 / 12 / 2; the flat facet that fits best, 25 / 13 / 0, cuts the top corner of parts.radiators)
        # Close-ups of a flat facet with the deck on top of it showed a torn top edge, so ahead of the vents the
        # section is the first pass's hollow one (t squared: 22 / 6 / 0 mm), with the crease kept only behind them.
        k = 0.3 * sat((dc + dt - SHOULDER_H / MPP) / 30.0)
        return inset(u) * (k * t + (1.0 - k) * t * t)
    vents = [_mpx(view, p) for p in VENTS_PX]
    vtree = [cKDTree(_dense(p, closed=True)) for p in vents]

    def pocket(u, v):
        for p, tr in zip(vents if SHROUD_LAYERS == 2 else (), vtree):
            if p[:, 0].min() < u < p[:, 0].max() and p[:, 1].min() < v < p[:, 1].max() \
                    and inside(p, np.array([[u, v]]))[0]:
                return VENT_DEPTH * smoothstep(tr.query((u, v))[0] / 3.0)
        return 0.0

    def surf_skin(u, v):
        # rolls: LIP toward the shroud's true leading edge, SKIN_LIP toward the skin's own edge; both are functions
        # of the distance to a smooth curve (a roll switched by zones along the edge came out frilled)
        df, wall = E.d_front(u, v), 0.0
        lip = LIP * (1.0 - df / LIP) ** 2 if df < LIP else 0.0
        if SHROUD_LAYERS == 2:
            de = float(etree.query((u, v))[0]) * MPP
            if de < SKIN_LIP:
                lip = max(lip, SKIN_LIP * (1.0 - de / SKIN_LIP) ** 2)
        else:                                                         # one stepped surface (the first pass)
            a = fwd * (u - float(np.interp(v, sv_all, su_all))) * MPP
            wall = WALL_STEP * smoothstep(a / 0.005 + 0.5) * smoothstep((v - sv_all[0]) / 25.0) \
                * smoothstep((sv_all[-1] + 20.0 - v) / 25.0)
        sh, pk = shoulder(u, v), pocket(u, v)

        def f(x, z):                                                  # no shoulder behind x 0.72: the shroud lies
            return side * (plan(x) - wall - lip - sh * smoothstep((x - 0.72) / 0.15) - pk)  # on the frame spar there
        return f

    def surf_wall(u, v):
        df = E.d_front(u, v)
        lip = LIP * (1.0 - df / LIP) ** 2 if df < LIP else 0.0
        depth = WALL_STEP + WALL_TIP * smoothstep((v - (sv[-1] - 220.0)) / 220.0)
        sh = shoulder(u, v)

        def f(x, z):
            return side * (plan(x) - depth - lip - sh * smoothstep((x - 0.72) / 0.15))
        return f
    return SimpleNamespace(view=view, px=px, E=E, plan=plan, skin_px=skin_px, wall_px=wall_px, surf=surf_skin,
                           surf_wall=surf_wall, crease=cr, vents=vents, inset=inset)


def shroud_point(side, u, v):
    """3D point of a shroud's outer skin at a pixel of its profile photo."""
    S = _shroud(side)
    return _on_surface(cams.CAMS[S.view], u, v, S.surf(u, v), side * 0.15)


# inner edge of the shrouds' top decks (TOP: gap between the two shrouds around the tank and the steering head)
DECK_X = [0.790, 0.854, 0.929, 0.960, 1.060]
DECK_Y = [0.053, 0.055, 0.060, 0.075, 0.092]


@functools.lru_cache(maxsize=None)
def _deck(side):
    S = _shroud(side)
    cam = cams.CAMS[S.view]
    top = S.px[S.E.top]
    T = cam.on_plane(top[:, 0], top[:, 1], "y", side * 0.17)
    o = np.argsort(T[:, 0])
    tx, tz = T[o, 0], _gauss(T[o, 2], 4.0)
    xs = np.linspace(0.792, min(1.062, float(tx.max()) - 0.075), 40)

    def edges(x):
        zt = float(np.interp(x, tx, tz))
        u = float(cam.project(np.array([[x, side * 0.17, zt]]))[0][0])
        y_out = S.plan(x) - S.inset(u) * smoothstep((x - 0.72) / 0.15) + 0.002
        return zt, y_out, min(float(np.interp(x, DECK_X, DECK_Y)), y_out - 0.004)
    return xs, edges


def deck_point(side, x, y):
    """Point on a shroud's top deck at (x, |y|)."""
    zt, y_out, y_in = _deck(side)[1](x)
    return np.array([x, side * abs(y), zt - 0.001 - 0.003 * sat((y_out - abs(y)) / (y_out - y_in))])


def shroud_decks():
    """Top decks of the shrouds: from the shoulder's top edge in to the edge at the tank (TOP: red from the plan
    envelope in to the gap around the tank, +-0.053 to 0.060 m beside the filler cap, opening to 0.092 at the
    steering head). Level with the shoulder's top edge, 3 mm lower at the inner edge (edge-on in the profile photos,
    so its height comes from the shroud outline's top edge; cross slope EST)."""
    m = Mesh()
    for side in (1, -1):
        xs, edges = _deck(side)
        rings = []
        for x in xs:
            zt, y_out, y_in = edges(x)
            rings.append(np.array([(x, side * (y_out + (y_in - y_out) * k), zt - 0.001 - 0.003 * k)
                                   for k in np.linspace(0, 1, 9)]))
        m.add(grid(Mesh(), rings, "plastic_red", closed_u=False))
    return m


def _vent_holes(view, name, min_area=120):
    """Dark openings inside a plastic's outline in the profile photo (the side panel's air intake)."""
    from scipy import ndimage
    import contourpy
    import segment
    cls, bp, im, X, Z = segment.classify(view)
    poly = np.asarray(OUT[name], float)
    pts = np.stack([X.ravel(), Z.ravel()], axis=1)
    lo, hi = poly.min(axis=0), poly.max(axis=0)
    box = (pts[:, 0] > lo[0]) & (pts[:, 0] < hi[0]) & (pts[:, 1] > lo[1]) & (pts[:, 1] < hi[1])
    ins = np.zeros(len(pts), bool)
    ins[box] = inside(poly, pts[box])
    ins = ndimage.binary_erosion(ins.reshape(X.shape), iterations=7)
    dark = ins & np.isin(cls, (2, 3))
    dark = ndimage.binary_opening(dark, iterations=1)
    lab, n = ndimage.label(dark)
    holes = []
    for k in range(1, n + 1):
        m = lab == k
        if m.sum() < min_area:
            continue
        m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=2))
        c = max(contourpy.contour_generator(z=m.astype(float)).lines(0.5), key=len)
        P = []
        for col, row in c[::3]:
            i, j = min(int(row), X.shape[0] - 1), min(int(col), X.shape[1] - 1)
            P.append((float(X[i, j]), float(Z[i, j])))
        if len(P) >= 6:
            holes.append(np.array(P))
    return holes


def shrouds():
    m = Mesh()
    for side in (1, -1):
        S = _shroud(side)
        lines = [S.crease] if SHROUD_LAYERS == 2 else []
        for p in S.vents if SHROUD_LAYERS == 2 else ():    # pocket edge and a row 3.5 px inside it (the pocket's wall)
            q = _inset_convex(p, 3.5)
            lines += [np.vstack([p, p[:1]]), np.vstack([q, q[:1]])]
        # rows of vertices along the outline through the rolled edge (16 px) and the shoulder (50 px)
        m.add(photo_panel(S.view, S.skin_px, S.surf, 0.003, "plastic_red", step=7.0,
                          rings=(2.5, 5.5, 9, 13, 18, 24, 31, 39, 48), lines=lines, line_step=4.0))
        if S.wall_px is not None:
            m.add(photo_panel(S.view, S.wall_px, S.surf_wall, 0.0025, "plastic_red", step=7.0,
                              rings=(2.5, 5.5, 9, 13)))
    return m


def _inset_convex(p, d):
    """A convex polygon moved in by d on every side (so a pocket's wall is the same width all round)."""
    P = np.asarray(p, float)
    c = P.mean(axis=0)
    edges = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        t = (b - a) / np.linalg.norm(b - a)
        n = np.array([-t[1], t[0]])
        edges.append((a + (n if n @ (c - a) > 0 else -n) * d, t))
    out = []
    for i in range(len(P)):
        (a1, t1), (a2, t2) = edges[i - 1], edges[i]
        out.append(a1 + t1 * np.linalg.solve(np.stack([t1, -t2], axis=1), a2 - a1)[0])
    return np.array(out)


# ---------------------------------------------------------------- side panels
SEAM_OUT = 0.014     # TOP columns 2400..2700: the panel's top bead shows as a bright line 10 to 18 px outside the edge
#                      of the seat cover: the seat's skirt leans out that far down to the seam
PANEL_H = 0.100      # the face reaches the plan envelope this far under the seam (LEFT: the panel is 93 to 139 mm
#                      tall; TOP: evenly lit from the seam out to the envelope, so one even lean; distribution EST)
# Width of the bead along the panel's top edge, under the seam with the seat. LEFT: a bright band 8 px wide at
# columns 2300..2540 (zoomed), a bright line 19 to 23 px under the seam at 2580..2820 (steps of +30 / -30).
BEAD_U, BEAD_PX = [2300, 2540, 2600, 2820], [8, 8, 19, 21]
# Ridge across the panel's tail. LEFT: bright band at rows 904..917 (column 2760), 859..895 (2820), 830..862 (2880);
# below it the face turns in toward the muffler (angle EST: 19 deg, at most 10 mm).
RIDGE_PX = [(2640, 968), (2700, 938), (2760, 910), (2820, 877), (2880, 846)]
# The seam between the seat's skirt and the side panel: a dark line 8 px wide. LEFT, per column the rows of its two
# edges (steps of -85..-167 and +50..+141 in r+g): 2040: 806/815, 2100: 830/838, 2220: 875/883, 2280: 894/907,
# 2340: 888/896, 2400: 879/887, 2460: 869/877, 2520: 860/868, 2580: 850/859, 2640: 841/849, 2700: 831/840,
# 2760: 821/829; column 2160 is the seat bolt's pocket (rows 855..883). Both ends EST from the neighbouring slope.
SEAM_PX = [(1988, 784), (2000, 790), (2040, 810), (2100, 834), (2160, 857), (2220, 879), (2280, 900), (2340, 892),
           (2400, 883), (2460, 873), (2520, 864), (2580, 855), (2640, 845), (2700, 836), (2760, 825), (2820, 812),
           (2862, 803)]


@functools.lru_cache(maxsize=None)
def _panel(side):
    """A side panel's outline and surface. Section, top to bottom: the top edge sits at the seam with the seat's
    skirt (TOP: SEAM_OUT outside the seat cover's edge) and tucks under it over a bead; from the bead's crease the
    face leans out evenly to the plan envelope of the top photo (TOP: left 0.159, right 0.175 where it bulges over
    the muffler; REAR rows 694..778: the lit face of the left panel ends 213 px left of the centre column, 0.151 m);
    under the ridge across its tail it turns in again. The rear photo's outer silhouette cannot confirm more: the
    shrouds, further forward, form it at these heights."""
    from types import SimpleNamespace
    from scipy.spatial import cKDTree
    name = "side_panel" if side > 0 else "side_panel_R"
    view = "left" if side > 0 else "right"
    left_u = (lambda u: u) if view == "left" else (lambda u: 3999.0 - u)
    sm = np.array(SEAM_PX, float)

    def above_seam(uu, vv):
        ul = left_u(np.asarray(uu, float))
        return (ul > sm[0, 0]) & (ul < sm[-1, 0]) & (vv <= np.interp(ul, sm[:, 0], sm[:, 1]))
    # the traced outline 'side_panel' takes in the seat's skirt (it was split from the seat along the foam's edge,
    # not along the seam): the panel is the part under the seam
    # (the piece ahead of the seam's front end, under the seat's nose, comes out separate: 'extra')
    px, *extra = _cut(clean_outline(view, OUT[name]), lambda uu, vv: ~above_seam(uu, vv), every=True)
    E = Edges(view, px)
    run = _longest_run(E.top)                          # the seam: the long top-facing stretch of the outline
    seam = px[run]
    stree = cKDTree(_dense(seam))
    bead = lambda u: float(np.interp(left_u(u), BEAD_U, BEAD_PX))
    cl = seam - E.n[run] * np.array([bead(u) for u in seam[:, 0]])[:, None]
    cl = np.stack([_gauss(cl[:, 0], 3.0), _gauss(cl[:, 1], 3.0)], axis=1)[6:-6]
    cl = cl[np.array([left_u(u) for u in cl[:, 0]]) > 2080.0]       # not along the steep edge under the seat's nose
    rg = np.array(RIDGE_PX, float)
    shroud_w = _shroud_plan(side)
    # the panel's height per column: where it is lower than PANEL_H the face reaches the envelope at its lower edge,
    # and at the ridge where there is one (the top photo's envelope is the panel's widest line)
    ub = np.arange(px[:, 0].min(), px[:, 0].max() + 6.0, 6.0)
    hgt = np.array([np.ptp(px[np.abs(px[:, 0] - q) < 6.0, 1]) if (np.abs(px[:, 0] - q) < 6.0).any() else 60.0 for q in ub])
    hgt = _gauss(hgt, 3.0)

    def width(x):
        return plan_half_width(min(max(x, -0.19), 0.80), side)

    def surf(u, v):
        d = float(stree.query((u, v))[0])
        db, ul = bead(u), left_u(u)
        reach = max(min(PANEL_H / MPP, 0.92 * float(np.interp(u, ub, hgt))), 25.0)
        if ul > rg[0, 0]:                                  # the face is at its widest on the ridge and upright below
            rv = float(np.interp(ul, rg[:, 0], rg[:, 1]))
            reach += (min(reach, max(rv - float(np.interp(ul, sm[:, 0], sm[:, 1])), 25.0)) - reach) \
                * smoothstep((ul - rg[0, 0]) / 60.0)

        def f(x, z):
            W = width(x)
            ys = min(max(seat_hw(min(max(x, 0.08), 0.80)) + SEAM_OUT, 0.064), W - 0.004)
            y = ys + (W - ys) * (1.0 - (1.0 - sat(d / reach)) ** 1.3)
            if d < db:
                y -= 0.55 * (db - d) * MPP
            if x > 0.585:                                  # the panel's nose lies 5 mm inside the shroud's tail
                y = min(y, shroud_w(x) - 0.005 * smoothstep((x - 0.585) / 0.015))
            return side * y
        return f
    return SimpleNamespace(view=view, px=px, E=E, width=width, surf=surf, seam=seam, crease=cl, extra=extra,
                           ridge=_mpx(view, RIDGE_PX))


def panel_point(side, u, v, inset=0.0):
    """3D point of a side panel's face (or of a surface INSET inside its envelope) at a pixel of its photo."""
    Pn = _panel(side)
    f = Pn.surf(u, v) if not inset else (lambda x, z: side * (Pn.width(x) - inset))
    return _on_surface(cams.CAMS[Pn.view], u, v, f, side * 0.15)


def side_panels():
    m = Mesh()
    for side, low in ((1, "lower_panel"), (-1, "lower_panel_R")):
        Pn = _panel(side)
        view, cam = Pn.view, cams.CAMS[Pn.view]
        name = "side_panel" if side > 0 else "side_panel_R"
        holes = [clean_outline(view, h, sigma=7.0) for h in _vent_holes(view, name, min_area=200)]
        m.add(photo_panel(view, Pn.px, Pn.surf, 0.003, "plastic_red", holes_px=holes, step=9.0, rings=(2.5, 5.0),
                          lines=[Pn.crease, Pn.ridge], line_step=5.0))
        for piece in Pn.extra:
            m.add(photo_panel(view, piece, Pn.surf, 0.003, "plastic_red", step=9.0))
        for h in holes:
            # air intake: the opening's edge turns in 16 mm (LEFT, zoomed: a lighter lip 8 px wide above the
            # opening; depth EST) onto a dark panel (the photo shows the filter's dark green behind it)
            c = h.mean(axis=0)
            hin = c + (h - c) * 0.92
            back = lambda u, v, q=side: (lambda x, z, f=Pn.surf(u, v): f(x, z) - q * 0.016)
            hr = resample(h, 4.5)                          # the panel's own vertices round the opening (step / 2)
            r0 = np.array([_on_surface(cam, u, v, Pn.surf(u, v), side * 0.15) for u, v in hr])
            r1 = np.array([_on_surface(cam, u, v, back(u, v), side * 0.15) for u, v in c + (hr - c) * 0.92])
            m.add(grid(Mesh(), [r0, r1], "plastic_red", closed_u=True))
            m.add(photo_panel(view, hin, back, 0.002, "louvre", step=9.0))
        # black textured lower panel (airbox side): its own exact outline, 6 mm inside the red panel's envelope
        m.add(photo_panel(view, clean_outline(view, OUT2[low], sigma=4.0),
                          lambda u, v, q=side: (lambda x, z: q * (Pn.width(x) - 0.006)), 0.003, "black_texture"))
    return m


# ---------------------------------------------------------------- lofted parts: seat, fenders
def _line(view, name, y):
    P = _true_outline(view, OUT[name], y)
    o = np.argsort(P[:, 0])
    return P[o]


SEAT_R = 0.028       # radius of the foam's edge. LEFT columns 2220..2820: the top's far edge shows 11 to 13 px under
#                      the silhouette; TOP: the "HONDA" on the skirt, 13 mm tall in profile, is 12 mm deep in plan
TAIL_X0 = 0.20       # the red wall under the tail (detail_plastics.tail_under): EST, hidden in the other photos
TAIL_TOP_ROW = 606   # REAR: its top edge


def _tank_top():
    """Top of the tank along x (parts.tank, a shared estimate), so the seat's nose stays clear of it."""
    import parts
    V = np.asarray(parts.tank().V)
    xs = np.unique(np.round(V[:, 0], 4))
    return xs, np.array([V[np.abs(V[:, 0] - x) < 2e-4, 2].max() for x in xs])


def seat():
    """Seat: cover, foam shape and base.
    Top line from the left photo (its upper silhouette, seen from a camera above it, is the far edge: the line is
    cast onto y = -0.6 x half-width); plan half-width of the cover's top from the top photo (TOP, seat cover mask).
    Section: a top crowned by 2 mm, the foam's edge radius SEAT_R, then the skirt leaning out SEAM_OUT down to the
    seam with the side panel, which is that panel's top edge in each profile photo (LEFT: the dark seam runs from
    row 810 at column 2040 down to 900 at 2280 and back up to 812 at 2820; the "HONDA" is printed on the skirt).
    The cover stops 3 mm above the panel; the black base shows in that gap (the dark seam line of the photos) and
    closes the underside. The base is raised over the red wall under the tail, and over the tank at the nose."""
    seams = []
    for side in (1, -1):
        Pn = _panel(side)
        W = cams.CAMS[Pn.view].on_plane(Pn.seam[:, 0], Pn.seam[:, 1], "y", side * 0.10)
        o = np.argsort(W[:, 0])
        seams.append((W[o, 0], _gauss(W[o, 2], 2.0)))
    tx, tz = _tank_top()
    z_wall = float(REAR.on_plane(np.array([2000.0]), np.array([float(TAIL_TOP_ROW)]), "x", TAIL_X0)[0][2])
    cover, base = [], []
    for x in np.linspace(0.082, 0.798, 72):
        hw = seat_hw(x)
        top_line = _line("left", "seat_top", -0.6 * hw)
        zt = float(np.interp(x, top_line[:, 0], _smooth(top_line[:, 1], 5)))
        out = SEAM_OUT * sat(hw / 0.07)
        ends = sat((x - 0.082) / 0.05 + 0.25) * sat((0.798 - x) / 0.06 + 0.2)       # the skirt shortens at both ends
        over_tank = float(np.interp(x, tx, tz)) + 0.004 if tx[0] <= x <= tx[-1] else -1.0
        # the skirts follow the photo's seam also beside the tank (parts.tank is wider there than the seat's nose:
        # only the base between them is lifted over it)
        zb = [min(max(float(np.interp(x, sx, sz)) - 0.002, zt - 0.012 - 0.105 * ends), zt - 0.012) for sx, sz in seams]

        def half(zb_):
            r = min(SEAT_R, 0.75 * hw, 0.8 * (zt - zb_))
            yt = max(hw - 0.85 * r, 0.0)
            pts = [(yt * q, zt - 0.002 * q * q) for q in np.linspace(0, 1, 6)]
            for a in np.linspace(0, math.radians(80), 9)[1:]:
                pts.append((yt + r * math.sin(a), zt - 0.002 - r * (1 - math.cos(a))))
            y1, z1 = pts[-1]
            for q in np.linspace(0, 1, 5)[1:]:
                pts.append((y1 + (max(hw + out, y1) - y1) * q, z1 + (zb_ - z1) * q))
            return pts
        L, Rr = half(zb[0]), half(zb[1])
        cover.append([(x, y, z) for y, z in L[::-1]] + [(x, -y, z) for y, z in Rr[1:]])
        # base: recessed 4 mm above the skirt's lower edge and 6 mm inside the cover everywhere, so it shows from
        # nowhere outside (a base flush with the skirt showed as a black band along the seam and came through the
        # foam's edge over the tail)
        zu = max(max(zb) + 0.004, over_tank, (z_wall + 0.003) * smoothstep((0.30 - x) / 0.04))
        zu = min(zu, zt - 0.010)
        inner = lambda pts, z: max(float(np.interp(z, [p[1] for p in pts[::-1]], [p[0] for p in pts[::-1]])) - 0.006, 0.0)
        base.append([(x, -max(Rr[-1][0] - 0.006, 0.0), min(zb[1] + 0.004, zu)), (x, -inner(Rr, zu), zu),
                     (x, -0.5 * inner(Rr, zu), zu), (x, 0.0, zu), (x, 0.5 * inner(L, zu), zu), (x, inner(L, zu), zu),
                     (x, max(L[-1][0] - 0.006, 0.0), min(zb[0] + 0.004, zu))])
    m = grid(Mesh(), [np.array(r) for r in cover], "seat", closed_u=False)
    grid(m, [np.array(r) for r in base], "plastic_black", closed_u=False)
    for k, rev in ((0, True), (-1, False)):                # closed ends
        loop = np.array(cover[k] + base[k])
        o = m.verts(np.vstack([loop, loop.mean(axis=0)[None]]))
        for i in range(len(loop)):
            tri = (o + i, o + (i + 1) % len(loop), o + len(loop))
            m.face(tri[::-1] if rev else tri, "seat")
    return m


def _blade(xs, hw_fn, top_fn, edge_fn, mat, a1=0.68, a2=0.94, c1=0.004, c2=0.011):
    """Fender blade lofted along x: centre top line, plan half-width, edge height. Section: a deck crowned by c1 out
    to a1 of the half-width, a facet dropping c2 to a2, then the flank down to the edge: two creases a side."""
    A = np.concatenate([np.linspace(0, a1, 7), np.linspace(a1, a2, 5)[1:], np.linspace(a2, 1.0, 5)[1:]])
    U = np.concatenate([-A[::-1], A[1:]])
    rings = []
    for x in xs:
        hw, zt, ze = hw_fn(x), top_fn(x), edge_fn(x)
        k = sat(hw / 0.03)                                  # the facets fade out at the tip
        ring = []
        for u in U:
            a = abs(u)
            if a <= a1:
                z = zt - c1 * (a / a1) ** 2
            elif a <= a2:
                z = zt - c1 - c2 * k * (a - a1) / (a2 - a1)
            else:
                z = zt - c1 - c2 * k
                z -= max(z - ze, 0.0) * (a - a2) / (1.0 - a2)
            ring.append((x, u * hw, z))
        rings.append(np.array(ring))
    return grid(Mesh(), rings, mat, closed_u=False)


def rear_fender():
    """Rear fender: centre top line from the left photo, plan half-width from the top photo (TOP), edges down to the
    lower outline of the left photo. The lines are smoothed over 30 mm and the tip is closed round (raw, the tip
    was torn).
    Section: deck, facet, flank. TOP columns 2950..3050: bright crease lines 45 to 52 px either side of the centre
    line where the half-width is 72 to 83 px: the deck ends at 0.68 of the half-width. LEFT columns 3000..3180: a
    lit band 15 to 19 px (11 to 14 mm) under the top edge, then a dark line and the flank: the facet drops 11 mm,
    the flank is nearly upright (REAR: lit edges 133 px either side of the centre column, rows 596..736).
    (The red seen under it from behind is not the blade: see detail_plastics.tail_under. Skirts on the blade were
    tried and showed behind the side panel in the profile, where the photo has none.)"""
    top_line = _line("left", "fender_top", 0.0)
    low = _true_outline("left", OUT["rear_fender"], 0.07)
    x_tip = -0.3005
    # the blade runs 20 mm under the side panel's rear edge (x 0.10 to 0.113): no gap at the root
    xs = np.concatenate([np.linspace(x_tip, x_tip + 0.03, 16)[:-1], np.linspace(x_tip + 0.03, 0.120, 63)])
    tx = np.linspace(-0.30, 0.120, 85)
    tz = _gauss(np.interp(tx, top_line[:, 0], top_line[:, 1]), 6.0)                 # 5 mm samples
    bz = np.array([_poly_bottom(low, min(max(x, low[:, 0].min() + 0.004), low[:, 0].max() - 0.004)) for x in tx])
    from scipy.signal import medfilt
    # median first: the half-transparent muffler behind the root tints the mask's lower edge and makes it dip
    bz = _gauss(medfilt(np.where(np.isfinite(bz), bz, tz - 0.006), 9), 6.0)
    # behind x 0 the blade is at most 98 mm either side; ahead of it the root flares out with the plan envelope to
    # meet the side panels (TOP: 0.089 at x 0.015, 0.145 at 0.08)
    pw = _gauss([min(plan_half_width(x, 1), 0.098 + 0.07 * smoothstep(x / 0.06)) for x in tx], 4.0)
    top = lambda x: float(np.interp(x, tx, tz))
    edge = lambda x: min(float(np.interp(x, tx, bz)), top(x) - 0.005)

    def hw(x):                                              # rounded tip: a half ellipse over the last 25 mm
        w = float(np.interp(x, tx, pw))
        d = (x - x_tip) / 0.025
        return max(w * math.sqrt(max(1.0 - (1.0 - d) ** 2, 0.0)) if d < 1.0 else w, 0.0008)
    return _blade(xs, hw, top, edge, "plastic_red")


# front fender plan half-width between the fork legs. FRONT (refitted camera, rows 700..740, right edge of the red:
# the left edge carries the fork tube's red reflection): 0.064 to 0.072 m; the top photo's envelope there is the
# fork guards. From x 1.457 forward the top photo's envelope is the fender itself.
FF_X = [1.215, 1.300, 1.420, 1.457]
FF_HW = [0.062, 0.064, 0.075, 0.080]
X_NOSE = 1.7075
FF_A1, FF_A2 = 0.70, 0.88      # creases of the section. TOP column 1125 (x 1.535): crease lines 74 px either side of
#                                the centre line, half-width 105 px: 0.70. LEFT columns 1140..1280: under the top
#                                edge a band to 17 px, a lit facet to 46..63 px, the flank to the edge at 78..95 px:
#                                the deck takes 21 % of the drop, the facet 38 %, the flank 41 % (a2 EST)


def _fender_plan():
    m = TT["x"] > 1.44
    x, w = TT["x"][m], _gauss(0.5 * (TT["left"][m] + TT["right"][m]), 2.5)

    def hw(q):
        w_ = float(np.interp(q, x, w)) if q > 1.457 else float(np.interp(q, FF_X, FF_HW))
        d = (X_NOSE - q) / 0.030                             # rounded nose: a half ellipse over the last 30 mm
        return max(w_ * math.sqrt(max(1.0 - (1.0 - d) ** 2, 0.0)) if d < 1.0 else w_, 0.0008)
    return hw


@functools.lru_cache(maxsize=None)
def _ff():
    """Front fender section z(x, a) with a = |y| / half-width. Centre top line and lowest line from the left photo,
    plan half-width from the top photo. Section: arched. The widest point (x 1.51, +-0.100 m) shows in the front
    photo at row 759, which is z 0.858: the height of the LOWEST line in the left photo there (0.856), 62 mm under
    the centre line. So the edges are the low line and the centre is the high line all along (FRONT + LEFT + TOP
    agree to 5 mm). Across: a crowned deck that carries a raised shield-shaped plateau ending in a point behind the
    nose (FRONT, TOP; 5 mm high EST), a facet and a flank with creases between them (FF_A1, FF_A2).
    Behind x 1.262 the fork leg hides the fender's lower edge in the left photo: there it keeps dropping at the
    slope it has where it disappears (29 mm in 47 mm, left photo) into the flap between the fork legs."""
    top_line = _line("left", "front_fender_top", 0.0)
    bot_line = _line("left", "front_fender_bottom", 0.09)
    hw = _fender_plan()
    tx = np.linspace(1.215, X_NOSE, 100)
    tz = _gauss(np.interp(tx, top_line[:, 0], top_line[:, 1]), 4.0)
    bz = np.interp(tx, bot_line[:, 0], bot_line[:, 1])
    k = int(np.searchsorted(tx, 1.262))
    bz[:k] = bz[k] - 0.6 * (tx[k] - tx[:k])
    bz = _gauss(bz, 4.0)
    top = lambda x: float(np.interp(x, tx, tz))
    edge = lambda x: min(float(np.interp(x, tx, bz)), top(x) - 0.004)

    def plateau(x):
        if x < 1.30 or x > 1.655:
            return 0.0, 0.0
        # the height fades to nothing at both ends with the width (a full-height plateau that stopped dead left a
        # 5 mm step right across the nose)
        return (0.052 * sat((1.655 - x) / 0.13) ** 0.8 * sat((x - 1.30) / 0.05 + 0.4),
                0.005 * smoothstep((1.655 - x) / 0.035) * smoothstep((x - 1.30) / 0.035))

    def z(x, a):
        w, zt, ze = hw(x), top(x), edge(x)
        if a <= FF_A1:
            q = a / FF_A1
            drop = 0.21 * (0.25 * q + 0.75 * q * q)
        elif a <= FF_A2:
            drop = 0.21 + 0.38 * (a - FF_A1) / (FF_A2 - FF_A1)
        else:
            drop = 0.59 + 0.41 * (a - FF_A2) / (1.0 - FF_A2)
        zz = zt - (zt - ze) * drop
        pw, ph = plateau(x)
        if pw > 0:
            zz += ph * (1.0 - smoothstep((a * w - pw) / 0.012)) - ph
        return zz
    return hw, z


def front_fender_z(x, y):
    """Height of the front fender's surface at (x, y)."""
    hw, z = _ff()
    x = min(max(x, 1.219), X_NOSE - 0.002)
    return z(x, min(abs(y) / hw(x), 1.0))


def front_fender():
    hw, z = _ff()
    # stations every 5 mm, every 1.5 mm over the last 30 mm: the nose narrows fast
    xs = np.concatenate([np.linspace(1.218, 1.677, 92), np.linspace(1.6785, X_NOSE, 20)])
    A = np.concatenate([np.linspace(0, FF_A1, 18), np.linspace(FF_A1, FF_A2, 7)[1:], np.linspace(FF_A2, 1.0, 6)[1:]])
    U = np.concatenate([-A[::-1], A[1:]])
    rings = [np.array([(x, u * hw(x), z(x, abs(u))) for u in U]) for x in xs]
    return grid(Mesh(), rings, "plastic_red", closed_u=False)


def fender_flap(on_tube, back, t_at_z):
    """The fender's rear flap: the red panel that hangs between the fork legs behind the tyre's top (FRONT: the red
    column under the fender nose, rows 905..1030, with the tyre's knobs in front of it). Half-width 67 mm at z 0.74
    to 58 mm at its lower corners (z 0.667), rounded lower edge down to z 0.650 on the centre line (FRONT). It lies
    on the fork's plane: the left photo shows no red behind the fork leg, only slivers at the tube's edges, so it is
    hidden by the leg. Distance ahead of the tube axis (28 mm): EST. Its top end meets the fender's mounting pad
    under the lower clamp (detail_plastics.fender_pad: 9 mm under the clamp's underside, which is 22.5 mm under the
    clamp's centre at z 0.925)."""
    t0, t1 = t_at_z(0.667), t_at_z(0.925) - 0.0225 - 0.0095
    rings = []
    for t in np.linspace(t0 - 0.020, t1, 22):
        w = float(np.interp(t, [t0, t_at_z(0.741), t1], [0.058, 0.067, 0.070]))
        ring = []
        for u in np.linspace(-1, 1, 15):
            # rounded lower edge: below the corners the blade narrows to the centre line
            tt = max(t, t0 - 0.020 * math.sqrt(max(1.0 - u * u, 0.0)))
            P = on_tube(tt) - back * (0.028 - 0.018 * abs(u) ** 2.5)
            ring.append((P[0], u * w, P[2]))
        rings.append(np.array(ring))
    return grid(Mesh(), rings, "plastic_red", closed_u=False)


# ---------------------------------------------------------------- number plate
# Edge of the plate's centre panel, px either side of column 2000 per row (FRONT: a step of +91..+99 in r+g on the
# left at u 1890 (row 320) .. 1953 (row 560); the mirrored step on the right, -52..-107, within 4 px of it on every
# row the hose does not cross). The centre panel is the lighter face; the wings fold back from these two lines.
PLATE_ROWS = [320, 335, 350, 365, 380, 395, 410, 425, 440, 455, 470, 485, 500, 515, 530, 545, 560]
PLATE_HALF = [110, 103, 96, 89, 83, 76, 72, 67, 64, 61, 59, 57, 55, 53, 51, 49, 47]
PLATE_POCKET = (2000.0, 346.0, 13.0, 8.0)   # FRONT: dark oval u 1987..2013, v 338..354: the recessed mounting bolt
PLATE_SLOT = (1963.0, 2038.0, 572.0, 586.0)  # FRONT: dark slot under the centre panel


@functools.lru_cache(maxsize=None)
def _plate():
    """The plate's surface: a centre panel parallel to the fork through the plate's front edge in the left photo
    (OUT 'number_plate', centre plane), wings folded back from the measured crease lines to 45 mm at +-0.141 m (left
    photo row z 1.00: the plate is 50 mm deep in side view), a pocket for the mounting bolt and a slot (depths EST)."""
    from types import SimpleNamespace
    side = np.asarray(_true_outline("left", OUT["number_plate"], 0.0))
    front = []
    for z in np.linspace(1.00, 1.20, 9):                    # front edge (largest x) of the side outline per height
        xs_ = []
        for i in range(len(side)):
            a, b = side[i], side[(i + 1) % len(side)]
            if (a[1] - z) * (b[1] - z) <= 0 and a[1] != b[1]:
                xs_.append(a[0] + (b[0] - a[0]) * (z - a[1]) / (b[1] - a[1]))
        front.append((max(xs_), z))
    front = np.array(front)
    k = np.polyfit(front[:, 1], front[:, 0], 1)             # x = k0 z + k1 on the centre plane
    d = np.array([k[0], 0.0, 1.0]); d /= np.linalg.norm(d)   # up the plate
    back = np.array([-d[2], 0.0, d[0]])                      # perpendicular, pointing back
    p0 = np.array([np.polyval(k, 1.0), 0.0, 1.0])
    mpp = (FRONT.C[0] - p0[0]) / FRONT.f                     # metres per px at the plate

    def depth(y, u, v):
        wc = float(np.interp(v, PLATE_ROWS, PLATE_HALF)) * mpp
        s = sat((abs(y) - wc) / (0.141 - wc))
        t = 0.045 * (0.75 * s + 0.25 * s * s)
        uc, vc, a, b = PLATE_POCKET
        e = math.hypot((u - uc) / a, (v - vc) / b)
        if e < 1.0:
            t += 0.008 * smoothstep((1.0 - e) * b / 2.5)
        u0, u1, v0, v1 = PLATE_SLOT
        din = min(u - u0, u1 - u, v - v0, v1 - v)
        if din > 0:
            t += 0.010 * smoothstep(din / 2.5)
        return t

    def hit(u, v, extra=0.0):
        t = 0.0
        for _ in range(6):
            o = p0 + back * (t + extra)                      # plane through o with normal 'back'
            r = FRONT.ray(np.array([u]), np.array([v]))[0]
            s = ((o - FRONT.C) @ back) / (r @ back)
            Pw = FRONT.C + s * r
            t = depth(Pw[1], u, v)
        return Pw
    return SimpleNamespace(hit=hit, back=back, up=d, mpp=mpp)


def number_plate():
    """Front number plate: its outline in the front photo (FRONT) cast onto its surface (_plate).
    Outline: the photo's own, both halves. The brake hose crosses the right half (the bike's left), so below row 352
    that half is the left one mirrored: the two agree within 2 px on every row the hose does not cross (half-widths
    194 / 193 px at row 335, 161 / 160 at 530, 139 / 137 at 560). Above it they differ: the left corner is cut off
    (edge at u 1838 on row 305, 1806 on row 335) while the right one is square (2189 to 2193) and the red runs on
    above the plate's top edge beside the bar pad (measure.py 'front_plate_rt')."""
    Pl = _plate()
    raw = np.array(MEAS["front_plate_px"])
    uc = 1999.5
    half = raw[raw[:, 0] <= uc]
    # around the plate one way, top to left to bottom: the angle is measured from straight up so it runs 0..pi over
    # the left half without a jump (measured from the +u axis it jumped at the plate's mid height and folded the
    # outline along the centre line: slits showed in the front view)
    half = half[np.argsort(np.arctan2(uc - half[:, 0], 450.0 - half[:, 1]))]
    mirror = np.stack([2 * uc - half[::-1, 0], half[::-1, 1]], axis=1)       # bottom, up the right edge, top
    rt = MEAS.get("front_plate_rt")
    if rt:
        # (row, right edge) from the plate's top edge (the left half's top row) down to 351. Above that row the red
        # runs on to row 224 beside the bar pad (u 2124..2186): not identified as plate, not built
        e = np.array(rt["edge"], float)
        e = e[e[:, 0] > half[:, 1].min() + 1.0]
        i1 = int(np.argmax(mirror[:, 1] < e[-1, 0] + 2))
        up = e[::-1][:, ::-1]
        after = np.where((np.arange(len(mirror)) > i1) & (mirror[:, 0] < up[-1, 0] - 5.0)
                         & (mirror[:, 1] < half[:, 1].min() + 8.0))[0]
        i2 = int(after[0]) if len(after) else len(mirror)
        mirror = np.vstack([mirror[:i1], up, mirror[i2:]])
    outer = smooth_poly(np.vstack([half, mirror]), 6)      # the mask's edge is ragged where the plate meets the fender
    rows = np.arange(302.0, 566.0, 6.0)
    hw = np.interp(rows, PLATE_ROWS, PLATE_HALF)
    lines = [np.stack([2000.0 - hw, rows], axis=1), np.stack([2000.0 + hw, rows], axis=1)]
    ang = np.linspace(0, 2 * math.pi, 25)
    ucp, vcp, a, b = PLATE_POCKET
    for s in (1.0, 0.62):
        lines.append(np.stack([ucp + a * s * np.cos(ang), vcp + b * s * np.sin(ang)], axis=1))
    u0, u1, v0, v1 = PLATE_SLOT
    for q in (0.0, 3.5):
        lines.append(np.array([(u0 + q, v0 + q), (u1 - q, v0 + q), (u1 - q, v1 - q), (u0 + q, v1 - q), (u0 + q, v0 + q)]))
    m = plate_lines(outer, [], 0.003, "plastic_red", lambda u, v, w: tuple(Pl.hit(u, v, 0.0015 - w)), 10.0,
                    lines=lines, line_step=3.5)
    # the mounting bolt at the bottom of its pocket (8 mm head: SPEC body fasteners)
    m.add(bolt(Pl.hit(ucp, vcp) - Pl.back * 0.0003, -Pl.back, af=0.008, head_h=0.004, flange_d=0.011))
    return m


MUD_X = 0.335        # LEFT: the mud flap's rear face is at x 0.339 where it leaves the airbox (z 0.643)


def inner_mudguard():
    """Black panel behind the airbox, above the rear tyre (the black arch under the fender in the rear photo).
    REAR (refitted camera, dark region on the centre line): arched top at row 726, then 117 px either side of the
    centre line from row 800 to 985 and a rounded lower edge at row 1000. Cast at x 0.335, where the left photo
    shows the mud flap leaving the airbox: +-84 mm wide, z 0.867 down to 0.669. Above row 800 its corners are hidden
    by the red walls under the fender (fender_mounts), so it is drawn full width there. Lean (top 30 mm further
    forward) and the 10 mm bulge toward the tyre are EST."""
    rows = np.array([726, 734, 748, 770, 800, 850, 950, 985, 1000])
    half = np.array([0, 60, 95, 117, 117, 117, 117, 108, 78])
    P = REAR.on_plane(np.full(len(rows), 2000.0), rows.astype(float), "x", MUD_X)
    zs = P[:, 2]
    hw = half * ((MUD_X - REAR.C[0]) / REAR.f)
    outer = np.array([(w, z) for w, z in zip(hw, zs)] + [(-w, z) for w, z in zip(hw[::-1], zs[::-1])][:-1])
    outer = smooth_poly(outer, 2)
    z0 = float(zs.min())

    def to3d(y, z, w):
        x = MUD_X + 0.15 * (z - z0) - 0.010 * (1.0 - min(abs(y) / 0.084, 1.0) ** 2)
        return (x - w, y, z)
    return plate2d(outer, [], 0.003, "plastic_black", to3d, step=0.012)


def mud_flap():
    """Mud flap hanging from the airbox in front of the rear tyre. LEFT photo (dark strip, rows 1200..1400, on the
    centre plane): rear face at x 0.339 (z 0.643), 0.342 (0.611), 0.339 (0.580), 0.333 (0.549), 0.326 (0.518),
    0.318 (0.486), 22 to 27 mm deep in side view: a sheet whose edges curl forward. Lower end z 0.485. The rear tyre
    hides it in the rear photo: width (120 mm at the top to 110 mm) EST. Its top 25 mm laps onto the front face of
    the inner mudguard's lower edge, as one moulding with it (EST: the joint is hidden)."""
    zt = np.array([0.675, 0.643, 0.611, 0.580, 0.549, 0.518, 0.486])
    xr = np.array([0.336, 0.339, 0.342, 0.339, 0.333, 0.326, 0.318])
    z0 = float(REAR.on_plane(np.array([2000.0]), np.array([1000.0]), "x", MUD_X)[0][2])      # mudguard's lower edge
    rings = []
    for z in (0.700, 0.688):
        rings.append(np.array([(MUD_X + 0.15 * (z - z0) - 0.010 * (1.0 - min(abs(u) * 0.060 / 0.084, 1.0) ** 2) + 0.004
                                + 0.007 * abs(u) ** 2.2, u * 0.060, z) for u in np.linspace(-1, 1, 13)]))
    for z in np.linspace(0.675, 0.485, 20):
        x = float(np.interp(-z, -zt, xr))
        w = 0.060 - 0.005 * sat((0.675 - z) / 0.19)
        rings.append(np.array([(x + 0.023 * abs(u) ** 2.2, u * w, z - 0.006 * (1 - abs(u)) * sat((0.50 - z) / 0.015))
                               for u in np.linspace(-1, 1, 13)]))
    return grid(Mesh(), rings, "plastic_black", closed_u=False)


def fender_mounts():
    """Red walls under the rear fender, facing back, either side of the mudguard's arch, each with a mounting bolt
    (REAR rows 610..795: red from 210 px left of the centre line to 134 px right of it, where the muffler and the
    right side panel begin; arch cut out from the measured dark region). Cast from the rear photo onto an upright
    plane at x 0.20 (EST: hidden behind the side panels and seat in the other photos, and ahead of the fender's
    blade so nothing shows under it in the profile)."""
    # outline in rear-photo pixels, clockwise from the top left; the arch is the mudguard's dark outline
    px = [(1790, 612), (2134, 612), (2134, 730), (2127, 742), (2111, 760), (2100, 780), (2100, 795), (2079, 795),
          (2066, 780), (2056, 760), (2040, 740), (2020, 729), (2000, 726), (1980, 729), (1959, 740), (1940, 760),
          (1924, 780), (1908, 795), (1790, 795)]
    px = np.array(px, float)
    X0 = 0.20

    def to3d(u, v, w):
        P = REAR.on_plane(np.array([u]), np.array([v]), "x", X0)[0]
        return (P[0] - w, P[1], P[2])
    m = plate2d(smooth_poly(px, 1), [], 0.004, "plastic_red", to3d, step=14.0)
    for u, v in ((1895, 767), (2112, 776)):                 # bolt heads with their washers (REAR)
        c = REAR.on_plane(np.array([float(u)]), np.array([float(v)]), "x", X0 - 0.003)[0]
        from geom import tube
        m.add(tube([c, c - np.array([0.004, 0, 0])], 0.011, 16, "alu_machined"))
        m.add(tube([c - np.array([0.004, 0, 0]), c - np.array([0.009, 0, 0])], 0.0065, 6, "steel"))
    return m
