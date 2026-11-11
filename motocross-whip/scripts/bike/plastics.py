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


def smoothstep_arr(x):
    x = np.clip(x, 0.0, 1.0)
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


# Seat plan: the cover's outermost line (its hem) in the TOP photo, half-widths in px about row SEAT_ROW, read at 4x
# on a 10 px grid (nose, tail) and by a scan of the matte cover (g > 38, out from the centre row) checked on the
# same zoom (middle). Nose: a straight front edge at u 1967.5 from row 1060 to 1185, corners at (1971, 1054) and
# (1990, 1049 / 1200). Middle: u 2140 rows 1035.5 / 1213.5, u 2200 1029.5 / 1219.5, u 2260..2620 1024 / 1223.5.
# Tail: u 2690 1031.5 / 1214.5, 2700 1036.5 / 1210.5, 2720 1043.5 / 1200.5, 2730 1058.5 / 1190.5, 2740 1072.5 /
# 1176.5, 2750 1097.5 / 1152.5, a rounded point at u 2757.5. Centre row: the nose's corners and the two "HONDA"
# prints (rows 1028..1036 and 1212..1220 at u 2500) are symmetric about 1124.5.
# (The table of 2026-11-10 put the top's edge at 0.088 and the hem 14 mm further out: 13 mm a side too wide, and
# the nose ran to a 15 mm point where the photo has a blunt front 112 mm wide.)
SEAT_ROW = 1124.5
SEAT_PLAN_PX = [(1967.5, 62.5), (1969.0, 67.0), (1972.0, 71.0), (1980.0, 74.0), (1990.0, 75.5), (2040.0, 80.5),
                (2090.0, 84.5), (2140.0, 89.0), (2170.0, 92.5), (2200.0, 95.0), (2230.0, 97.5), (2260.0, 99.5),
                (2620.0, 99.0), (2650.0, 97.0), (2675.0, 94.0), (2690.0, 91.5), (2700.0, 87.0), (2710.0, 83.0),
                (2720.0, 78.0), (2730.0, 66.0), (2740.0, 52.0), (2750.0, 27.5), (2755.0, 16.0), (2757.5, 0.0)]


@functools.lru_cache(maxsize=None)
def _seat_plan():
    """The seat's plan outline (TOP): x of each table column (on the plane z 0.96, the hem's mean height; the top
    camera is 12.5 m above it, so 50 mm of height moves a point 0.2 mm) and its half-width."""
    t = np.array(SEAT_PLAN_PX, float)
    n = len(t)
    c = TOP.on_plane(t[:, 0], np.full(n, SEAT_ROW), "z", 0.96)
    lt = TOP.on_plane(t[:, 0], SEAT_ROW + t[:, 1], "z", 0.96)
    rt = TOP.on_plane(t[:, 0], SEAT_ROW - t[:, 1], "z", 0.96)
    x, hw = c[:, 0], (lt[:, 1] - rt[:, 1]) / 2
    o = np.argsort(x)
    return x[o], hw[o]


def seat_hem_hw(x):
    """Half-width of the seat's hem (its outermost line in plan) at x (0 beyond the seat's ends)."""
    xs, hw = _seat_plan()
    return float(np.interp(x, xs, hw, left=0.0, right=0.0))


def seat_hw(x):
    """Half-width of the seat's flat top (kept for callers of the first passes): the hem less 35 mm of skirt lean
    and shoulder (the shoulder has fallen 1.3 mm there, SEAT_SHOULDER), at least 30 mm."""
    return max(seat_hem_hw(x) - 0.035, 0.03)


@functools.lru_cache(maxsize=None)
def seat_outline(step=0.004):
    """The hem's plan outline as a closed curve (x, y), counter-clockwise from the nose's front centre, sampled every
    STEP (4 mm: see SEAT_RINGS_MM) and smoothed over 2 mm (the table's corners stay; the tail's point is rounded to
    about 8 mm, as in the photo)."""
    from scipy.ndimage import gaussian_filter1d
    xs, hw = _seat_plan()
    left = np.stack([xs[::-1], hw[::-1]], axis=1)                  # nose to tail tip, y > 0
    right = (left[::-1] * np.array([1.0, -1.0]))[1:]               # tail tip to nose, y < 0
    P = resample(np.vstack([[[xs[-1], 0.0]], left, right]), step / 3.0)
    k = 0.002 / (step / 3.0)
    P = np.stack([gaussian_filter1d(P[:, 0], k, mode="wrap"), gaussian_filter1d(P[:, 1], k, mode="wrap")], axis=1)
    return resample(P, step)


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


def smooth_pieces(px, corners, knot=40.0, step=4.5):
    """A traced outline as a few smooth pieces. px: the traced closed curve (photo pixels). corners: (u, v, radius)
    in order round the curve, the outline's corners as read in the photo (radius 0: sharp; otherwise the corner is
    rounded to about that radius, in px; a fourth value True: the trace from this corner to the next is not the
    plastic's edge, draw a straight line). Between two corners the traced points are fitted with a cubic B-spline
    whose knots are KNOT px apart, so the curve cannot wiggle on a shorter scale than about 1.5 knots (45 mm), and
    with a robust loss, so that a notch where a cable or a bracket crosses the plastic's edge is bridged instead of
    followed. Returns the closed curve sampled every STEP px and the index of each corner in it (corner 0 first)."""
    from scipy.interpolate import make_lsq_spline
    from scipy.ndimage import gaussian_filter1d
    from scipy.spatial import cKDTree
    D = resample(px, 1.0)
    C = np.array([c[:2] for c in corners], float)
    idx = cKDTree(D).query(C)[1]
    if (np.diff(np.concatenate([idx, idx[:1]])) % len(D)).sum() != len(D):    # listed against the curve's direction
        D = D[::-1]
        idx = len(D) - 1 - idx
    out, at = [], []
    for k in range(len(C)):
        i, j = int(idx[k]), int(idx[(k + 1) % len(C)])
        seg = D[i:j + 1] if j > i else np.vstack([D[i:], D[:j + 1]])
        seg = np.vstack([C[k], seg[2:-2], C[(k + 1) % len(C)]])               # a piece starts and ends ON its corners
        s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(seg, axis=0), axis=1))])
        ok = np.concatenate([[True], np.diff(s) > 1e-6])
        seg, s = seg[ok], s[ok]
        q = np.linspace(0.0, s[-1], max(int(round(s[-1] / step)), 2) + 1)[:-1]
        at.append(sum(len(o) for o in out))
        if s[-1] < 15.0 or len(seg) < 8 or (len(corners[k]) > 3 and corners[k][3]):
            out.append(seg[0] + (seg[-1] - seg[0]) * (q / s[-1])[:, None])
            continue
        t = np.concatenate([[0.0] * 4, np.linspace(0.0, s[-1], max(int(s[-1] // knot), 1) + 1)[1:-1], [s[-1]] * 4])
        w = np.ones(len(s))
        for _ in range(5):
            w[0] = w[-1] = 1e3
            spl = make_lsq_spline(s, seg, t, k=3, w=w)
            w = 1.0 / (1.0 + (np.linalg.norm(spl(s) - seg, axis=1) / 2.5) ** 2)
        out.append(spl(q))
    P = np.vstack(out)
    n = len(P)
    for c, a in zip(corners, at):
        r = c[2]
        if r > 0:
            Ps = np.stack([gaussian_filter1d(P[:, 0], 0.8 * r / step, mode="wrap"),
                           gaussian_filter1d(P[:, 1], 0.8 * r / step, mode="wrap")], axis=1)
            d = np.abs((np.arange(n) - a + n // 2) % n - n // 2) * step
            P = P + np.exp(-0.5 * (d / (1.5 * r)) ** 2)[:, None] * (Ps - P)
    return P, at


def conforming_mesh(outer, rings=(), rows=(), step=9.0):
    """Triangles over the closed curve OUTER (2D) that keep its points exactly as given: rows of vertices parallel
    to the boundary at the distances RINGS inside it (for a rim that rolls), the points of ROWS as given (creases,
    pocket rims), a staggered grid of STEP elsewhere, Delaunay. Every edge of the boundary must come out as an edge
    of the triangulation (otherwise the outline would be notched or webbed): checked, and an error if not.
    Returns (points, triangles, number of boundary points); the boundary points come first, in order."""
    from scipy.spatial import Delaunay, cKDTree
    B = np.asarray(outer, float)
    nb = len(B)
    btree = cKDTree(_dense(B, closed=True)[:-1])
    t = np.roll(B, -1, axis=0) - np.roll(B, 1, axis=0)
    n = np.stack([t[:, 1], -t[:, 0]], axis=1)
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    if inside(B, (B + 1.0 * n)[::3]).mean() < 0.5:                 # normals point into the shape
        n = -n
    sp = float(np.median(np.linalg.norm(np.diff(B, axis=0), axis=1)))
    pts, d0 = [B], 0.0
    for d in rings:
        Q = B + d * n
        Q = Q[inside(B, Q) & (btree.query(Q)[0] > 0.93 * d)]       # not folded over at a corner or across a thin tip
        if len(Q):
            Q = Q[cKDTree(np.vstack(pts)).query(Q)[0] > 0.7 * (d - d0)]
        keep = []
        for p in Q:                                                # thinned where a hollow bend crowds the row
            if not keep or np.hypot(*(p - keep[-1])) > 0.6 * sp:
                keep.append(p)
        if keep:
            pts.append(np.array(keep))
        d0 = d
    reach = (max(rings) if len(rings) else 0.0)
    feats = []
    for R in rows:                                                 # earlier rows win where two come close
        R = np.asarray(R, float)
        R = R[inside(B, R)]
        if len(R):
            R = R[btree.query(R)[0] > reach + 2.0]
        if len(R) and feats:
            R = R[cKDTree(np.vstack(feats)).query(R)[0] > 2.2]
        if len(R):
            feats.append(R)
    pts += feats
    feat = np.vstack(pts[1:]) if len(pts) > 1 else np.zeros((0, 2))
    lo, hi = B.min(axis=0), B.max(axis=0)
    G = []
    for j, v in enumerate(np.arange(lo[1], hi[1], step * 0.866)):
        us = np.arange(lo[0] + (0.5 * step if j % 2 else 0.0), hi[0], step)
        G.append(np.stack([us, np.full(len(us), v)], axis=1))
    G = np.vstack(G)
    G = G[inside(B, G)]
    G = G[btree.query(G)[0] > reach + 0.6 * step]
    if len(feat) and len(G):
        G = G[cKDTree(feat).query(G)[0] > 0.6 * step]
    P = np.vstack(pts + [G])
    tri = Delaunay(P).simplices
    tri = tri[inside(B, P[tri].mean(axis=1))]
    a, b, c = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    area = 0.5 * ((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0]))
    tri = tri[np.abs(area) > 1e-9]
    edges = {tuple(sorted(e)) for f in tri for e in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0]))}
    missing = [i for i in range(nb) if (min(i, (i + 1) % nb), max(i, (i + 1) % nb)) not in edges]
    if missing:
        raise RuntimeError("boundary edges missing from the mesh at %s" % [tuple(P[i].round(1)) for i in missing[:6]])
    return P, tri, nb


def shell(P, tri, nb, to3d, thickness, sgn, mat):
    """A shell from a conforming mesh: outer face on the surface (to3d(u, v) -> 3D), inner face THICKNESS further
    toward the centre plane (sgn: +1 left, -1 right), a rim round the boundary. Faces wound so that every normal
    points out of the plastic. Returns the mesh and the outer face's points (in the order of P)."""
    X = np.array([to3d(u, v) for u, v in P])
    m = Mesh()
    top = m.verts(X)
    bot = m.verts(X - np.array([0.0, sgn * thickness, 0.0]))
    third = {}
    for a, b, c in tri:
        if np.cross(X[b] - X[a], X[c] - X[a])[1] * sgn < 0:
            b, c = c, b
        m.face((top + a, top + b, top + c), mat)
        m.face((bot + a, bot + c, bot + b), mat)
        for p, q, r in ((a, b, c), (b, c, a), (c, a, b)):
            third[(min(p, q), max(p, q))] = r
    for i in range(nb):
        j = (i + 1) % nb
        k = third[(min(i, j), max(i, j))]
        f = (top + i, top + j, bot + j, bot + i)
        if np.cross(X[j] - X[i], np.array([0.0, -sgn, 0.0])) @ (X[k] - X[i]) > 0:    # pointing at the panel: turn
            f = f[::-1]
        m.face(f, mat)
    return m, X


# Both shrouds are described once, in LEFT photo pixels, and built through each side's own camera (the right photo is
# the left one mirrored about column 1999.5: _mpx). Checked on both photos, 2026-11-10: the skin's leading and bottom
# edges (first bright-red pixel of 31 rows, last of 13 columns) are the same within 1 px, the traced outlines within
# 1 px (median) and 2.7 px (90 %); they differ where a cable (u 1676..1687) or the fork tube (wall apex) hides the
# edge on one side. The plastic is symmetric; the plan widths are each side's own (TOP).
#
# Corners of the traced outline (LEFT, read at 4x to 7x zoom): A the skin's top front corner; B1, B2 foot and top of
# the 25 px step where the bolt plate beside the tank starts (TOP: its front edge at x 0.93); D, E the blunt rear
# end under the seat; F0, F the round lower tip of the skin and its lowest point; G the inner wall's lower tip; H
# the wall's apex, where its leading edge meets the fork tube's rear edge (the wall runs on behind the tube, unseen;
# the trace's 12 px hook down the tube from there is not in the right photo: left out). Between F and G the trace
# follows the radiator's grey bracket in and out (outlines.py closes the louvre gap there): a straight line.
SHROUD_CORNERS = [(1531, 848, 0), (1775, 773, 0), (1772, 748, 0), (2197, 886, 6), (2203, 915, 6), (1786, 1157, 8),
                  (1765, 1186, 6, True), (1684, 1201, 3), (1475, 967, 0)]
# The outer skin's own edge. LEFT rows 850..1150: first bright-red pixel (r > 200) behind the shadowed wall, every
# 30 rows; then its bottom edge, columns 1690..1765: last bright-red row (under it the louvres and the bracket).
SKIN_FRONT_PX = [(1530, 850), (1535, 880), (1548, 910), (1561, 940), (1574, 970), (1589, 1000), (1608, 1030),
                 (1628, 1060), (1648, 1090), (1668, 1120), (1691, 1150)]
SKIN_BOTTOM_PX = [(1690, 1150), (1706, 1159), (1722, 1168), (1738, 1176), (1754, 1185), (1765, 1186)]
# The crease between the upright side face and the top face ("roof"). Behind the vents it is a brightness step in
# the LEFT photo: columns 1800..2012, rows 845, 821, 813, 803, 798 (steps of +20 to +42 in r+g; at 6x it leaves the
# vent pocket's top rear corner, (1799, 840)). Along the pocket's top it is the pocket's rim (rows 848 to 840).
# Ahead of the vents nothing marks it (the shoulder is round there): placed where the roof below gives the FRONT
# photo's silhouette (see ROOF_R), 29 px under the top edge at column 1600.
CREASE_PX = [(1531, 877), (1600, 854), (1660, 847), (1721, 845), (1760, 845), (1800, 843), (1860, 822), (1920, 812),
             (1980, 803), (2012, 798)]
# Roof: above the crease the surface leans in at 45 deg, with a fillet of radius ROOF_R at the crease: lean =
# hh^2 / (hh + r), hh = height above the crease + r. That one rule against the other photos (model values printed
# from the built surface, 2026-11-10):
#   FRONT, section whose top edge is at z 0.937: the silhouette leans 0 / 10 / 23 mm at z 0.899 / 0.917 / 0.933.
#          Model at column 1600 (x 1.053, r 15 mm): 0 / 10 / 24.5, and 26 at its top edge (z 0.934)
#   FRONT, upper silhouette further back: 0.150 off the centre line at z 0.950, 0.128 at 0.963.
#          Model at x 0.965: 0.151 at 0.950, top edge 0.135 at 0.961
#   TOP, inner edge of the blade ahead of the vents: 0.147 at x 0.98, 0.116 at 0.932. Model: 0.144 at 0.987, 0.120
#          at 0.925 (foot of the step)
#   TOP, outer edge of the bolt plate at x 0.928: 0.100. Model (top of the step): 0.102
# Behind the vents the crease is crisp in the photo (r 1.5 mm, EST: a moulded edge).
ROOF_R = (0.015, 0.0015)
ROOF_R_U = (1660.0, 1820.0)      # columns over which the fillet tightens (across the vent pocket)
# Rims. Every free edge turns in over its last 8 mm (rows of vertices parallel to the edge carry it):
LIP = 0.012          # the wall's leading edge. FRONT: a red rim outside the radiator, 10 mm wide at mid height
SKIN_LIP = 0.003     # the skin's own edge over the wall (EST: it lands on the wall, WALL_STEP minus the 3 mm shell)
TOP_LIP = 0.006      # the blade's inner top edge. TOP: the blade is 35 mm wide in plan at x 1.05 where the roof
#                      leans 26 mm
EDGE_LIP = 0.0025    # lower and rear edges (EST: a moulded panel's turned edge)
TAIL_U = 2140.0      # behind this column the tail lies flat on the side panel: no lip (it cut 2.6 mm into the panel)
RIM_W = 0.008
RINGS_PX = (2.0, 4.5, 7.5, 11.0)
WALL_STEP = 0.006    # the inner wall sits this far inside the skin (FRONT: the rim it and the skin's edge make is
#                      10 to 18 mm wide; the step itself is not measurable: EST). With its 1.5 mm shell it stays
#                      outside the radiator grille's wing, which detail_engine puts 8 mm inside the plan envelope:
#                      8 mm deep (and 12 mm at the lower tip, to open the louvre gap of the photo) ran 6 mm into it
WALL_T = 0.0015
WALL_TUCK = 12.0     # px of wall under the skin's edge
# The vent pocket behind the "CRF" decal (LEFT, 6x): a recess with a rounded rim. Its rear wall runs down from
# (1811, 887) by (1825, 973) to a tip at (1767, 1100); its front edge is a straight line up to (1722, 850). In the
# photo its top rim is the crease itself (rows 848 to 840); here it is 14 px lower, so that the rim and the crease
# each keep their own rows of vertices (6 px apart they made one wavy ridge). The two outlets in it are open to the
# radiator's louvres on the bike; here the pocket has a floor (a dark part inside the shroud's outline is what the
# intruder test forbids, and the outline closes them). Depth and wall width EST.
POCKET_PX = [(1726, 861), (1760, 857), (1797, 854), (1811, 890), (1822, 937), (1825, 973), (1807, 1028), (1770, 1100),
             (1764, 1100), (1757.6, 1060), (1744.1, 975), (1735.4, 920)]
POCKET_DEPTH = 0.007
POCKET_WALL = 5.0    # px
# Bolt plate (deck) beside the tank. TOP: red from the roof's top edge in to the gap around the tank, 0.053 to 0.060
# off the centre line, from the plate's front edge (x 0.93) back under the seat's nose.
DECK_X = [0.790, 0.854, 0.929, 0.960]
DECK_Y = [0.053, 0.055, 0.060, 0.075]
DECK_END_U = 1950.0  # LEFT column where the plate ends under the seat's nose (x 0.792). (Run on back to u 2120 to fill
#                      the red strip the top photo shows beside the seat's nose, it ran 3 to 4 mm into the side panels'
#                      noses and the shrouds' skins and cost the rear view 1.6 points of red: left as it was)
DECK_DROP = 0.003    # the plate's inner edge lies this much lower than its outer edge (EST)


@functools.lru_cache(maxsize=None)
def _shroud_px():
    """A shroud in LEFT photo pixels: outline in smooth pieces, the skin's and the wall's boundaries with the lip of
    each boundary point, the crease, the pocket."""
    from types import SimpleNamespace
    from scipy.interpolate import CubicSpline
    from scipy.ndimage import gaussian_filter1d
    from scipy.spatial import cKDTree
    raw = np.stack(cams.linear_to_px("left", *np.asarray(OUT["shroud"], float).T), axis=1)
    P, at = smooth_pieces(raw, SHROUD_CORNERS)
    A, B1, B2, D, E, F0, F, G, H = at
    assert A == 0
    step = 4.5
    # the skin's own edge: A down the leading edge to its bottom corner, along the bottom to F
    fr, bt = np.array(SKIN_FRONT_PX, float), np.array(SKIN_BOTTOM_PX, float)
    cf, cb = np.polyfit((fr[:, 1] - 1000.0) / 100.0, fr[:, 0], 4), np.polyfit((bt[:, 0] - 1725.0) / 40.0, bt[:, 1], 2)
    front = lambda v: np.polyval(cf, (np.asarray(v, float) - 1000.0) / 100.0)
    bottom = lambda u: np.polyval(cb, (np.asarray(u, float) - 1725.0) / 40.0)
    vk = 1151.0
    for _ in range(8):                                             # the corner: where the two fitted edges meet
        uk = float(front(vk))
        vk = float(bottom(uk))
    v1 = np.arange(P[A, 1], vk, 1.0)
    u2 = np.arange(uk, P[F, 0], 1.0)
    edge = np.vstack([P[A:A + 1], np.stack([front(v1), v1], axis=1)[3:], [[uk, vk]],
                      np.stack([u2, bottom(u2)], axis=1)[1:-2], P[F:F + 1]])
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(edge, axis=0), axis=1))])
    q = np.linspace(0.0, s[-1], int(round(s[-1] / step)) + 1)
    edge = np.stack([np.interp(q, s, edge[:, 0]), np.interp(q, s, edge[:, 1])], axis=1)
    k2 = int(np.argmin(np.hypot(edge[:, 0] - uk, edge[:, 1] - vk)))
    sm = np.stack([gaussian_filter1d(edge[:, 0], 0.9, mode="nearest"), gaussian_filter1d(edge[:, 1], 0.9, mode="nearest")], 1)
    wk = np.exp(-0.5 * ((np.arange(len(edge)) - k2) / 2.0) ** 2)[:, None]
    wk[0] = wk[-1] = 0.0
    edge = edge + wk * (sm - edge)                                 # the bottom corner rounded to about 4 px
    skin = np.vstack([P[A:F], edge[::-1][:-1]])
    # lips along the skin's boundary: none where the bolt plate carries the skin on (B1 over the step to the plate's end)
    n_top = F - A
    deck_end = B2 + int(np.argmin(np.abs(P[B2:D, 0] - DECK_END_U)))
    lip = np.full(len(skin), EDGE_LIP)
    lip[A:B1] = TOP_LIP
    lip[n_top:] = SKIN_LIP
    lip = gaussian_filter1d(lip, 2.0, mode="wrap")
    i = np.arange(len(skin))
    lip *= np.clip(np.maximum(B1 - i, i - deck_end) / 6.0, 0.0, 1.0)
    lip *= np.clip((TAIL_U - skin[:, 0]) / 30.0, 0.0, 1.0)
    # the wall: everything in the outline ahead of and under the skin's edge, and WALL_TUCK px under the edge itself
    t = np.gradient(edge, axis=0)
    nrm = np.stack([t[:, 1], -t[:, 0]], axis=1) / np.linalg.norm(t, axis=1)[:, None]
    if inside(skin, (edge + 3.0 * nrm)[2:-2:3]).mean() < 0.5:
        nrm = -nrm
    tuck = edge + WALL_TUCK * nrm
    tuck = tuck[inside(skin, tuck) & (cKDTree(_dense(edge)).query(tuck)[0] > 0.95 * WALL_TUCK)
                & (cKDTree(_dense(P, closed=True)).query(tuck)[0] > 8.0)]
    a3, f3 = A + 3, F - 3                                           # the tuck's ends, on the outline
    tk = np.vstack([P[a3], tuck, P[f3]])
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(tk, axis=0), axis=1))])
    q = np.linspace(0.0, s[-1], int(round(s[-1] / step)) + 1)
    tk = np.stack([np.interp(q, s, tk[:, 0]), np.interp(q, s, tk[:, 1])], axis=1)
    wall = np.vstack([P[f3:], P[A:a3], tk[:-1]])
    wlip = np.zeros(len(wall))
    g, h = G - f3, H - f3
    wlip[:g] = EDGE_LIP
    wlip[g:h] = LIP
    wlip[h:len(P) - f3] = EDGE_LIP
    wlip = gaussian_filter1d(wlip, 2.0, mode="wrap")
    wlip[len(P) - f3 + 3:] = 0.0
    # crease: a smooth curve through the readings, straight on beyond them
    cr = np.array(CREASE_PX, float)
    cs = CubicSpline(cr[:, 0], cr[:, 1], bc_type="natural")
    s0, s1 = float(cs(cr[0, 0], 1)), float(cs(cr[-1, 0], 1))

    def crease(u):
        if u < cr[0, 0]:
            return cr[0, 1] + s0 * (u - cr[0, 0])
        if u > cr[-1, 0]:
            return cr[-1, 1] + s1 * (u - cr[-1, 0])
        return float(cs(u))
    # pocket rim: a closed smooth curve through its points
    pk = np.array(POCKET_PX, float)
    pk = np.vstack([pk, pk[:1]])
    ps = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pk, axis=0), axis=1))])
    pc = CubicSpline(ps, pk, bc_type="periodic")
    pocket = pc(np.linspace(0.0, ps[-1], int(round(ps[-1] / 4.0)), endpoint=False))
    return SimpleNamespace(outline=P, at=at, skin=skin, lip=lip, wall=wall, wlip=wlip, edge=edge, crease=crease,
                           crease_u=(float(P[A, 0]) + 30.0, float(cr[-1, 0]) + 30.0), pocket=pocket,
                           top=(B2, deck_end))


def _offset_loop(loop, d):
    """A closed curve moved by d along its normals (positive: inward)."""
    t = np.roll(loop, -1, axis=0) - np.roll(loop, 1, axis=0)
    n = np.stack([t[:, 1], -t[:, 0]], axis=1) / np.linalg.norm(t, axis=1)[:, None]
    if inside(loop, (loop + 1.0 * n)[::3]).mean() < 0.5:
        n = -n
    return loop + d * n


@functools.lru_cache(maxsize=None)
def _shroud(side):
    """A shroud's two shells as conforming meshes in its own photo's pixels, with their surfaces.
    Side face: upright, at the plan envelope of the top photo (TOP). Checked against the front photo through the
    refitted camera: its outer silhouette is 0.200 m off the centre line at z 0.83..0.88 (top photo: 0.199 to 0.202),
    0.193 at z 0.74 and 0.185 at 0.68, which is the plan envelope at the x where the leading edge is at those heights.
    Roof: above the crease (CREASE_PX, ROOF_R). Two layers (LEFT and RIGHT photos, zoomed): the outer skin stops 35 to
    80 mm short of the front edge; under it a separate inner wall, in shadow in the photos, runs on to the true front
    edge, whose rim is rolled in by LIP. Every height is a smooth function of the pixel with those few parameters;
    only the rims' last 8 mm depend on the distance to the boundary, and they are carried by rows of vertices
    parallel to it."""
    from types import SimpleNamespace
    from scipy.spatial import cKDTree
    S = _shroud_px()
    view = "left" if side > 0 else "right"
    cam = cams.CAMS[view]
    plan = _shroud_plan(side)
    mir = (lambda u: u) if side > 0 else (lambda u: 3999.0 - u)    # this side's photo column <-> LEFT column

    def roof(u, v):
        h = (S.crease(u) - v) * MPP
        r = ROOF_R[0] + (ROOF_R[1] - ROOF_R[0]) * smoothstep((u - ROOF_R_U[0]) / (ROOF_R_U[1] - ROOF_R_U[0]))
        hh = h + r
        return hh * hh / (hh + r) if hh > 0 else 0.0

    def rim(boundary, lips):
        k = 12
        f = np.linspace(0.0, 1.0, k, endpoint=False)[None, :, None]
        nxt, ln = np.roll(boundary, -1, axis=0), np.roll(lips, -1)
        tree = cKDTree((boundary[:, None, :] + (nxt - boundary)[:, None, :] * f).reshape(-1, 2))
        amp = (lips[:, None] + (ln - lips)[:, None] * f[0, :, 0]).ravel()

        def fn(u, v):
            d, i = tree.query((u, v))
            d *= MPP
            return amp[i] * (1.0 - d / RIM_W) ** 2 if d < RIM_W else 0.0
        return fn
    rim_skin, rim_wall = rim(S.skin, S.lip), rim(S.wall, S.wlip)
    ptree = cKDTree(_dense(S.pocket, closed=True))

    def pocket(u, v):
        if not (1715.0 < u < 1832.0 and 845.0 < v < 1106.0) or not inside(S.pocket, np.array([[u, v]]))[0]:
            return 0.0
        return POCKET_DEPTH * smoothstep(ptree.query((u, v))[0] / POCKET_WALL)

    def off_skin(u, v):                                # metres inside the plan envelope, at a LEFT photo pixel
        return roof(u, v) + rim_skin(u, v) + pocket(u, v)

    def off_wall(u, v):
        return WALL_STEP + roof(u, v) + rim_wall(u, v)

    def point(off, u, v):                              # 3D point of a surface at a pixel of THIS side's photo
        o = off(mir(u), v)
        return _on_surface(cam, u, v, lambda x, z: side * (plan(x) - o), side * 0.15)
    # rows of vertices on the crease and either side of it; on the pocket's rim, just outside it, and on the foot of
    # its wall and just inside that
    us = np.arange(S.crease_u[0], S.crease_u[1], 4.5)
    cv = np.array([S.crease(u) for u in us])

    def ring(d):                                       # the pocket's rim moved in by d px (not folded at its tip)
        Q = _offset_loop(S.pocket, d)
        return Q[ptree.query(Q)[0] > 0.9 * abs(d)]
    rows = [S.pocket, ring(POCKET_WALL), ring(-2.5), ring(POCKET_WALL + 2.5)]
    rows += [np.stack([us, cv + d], axis=1) for d in (0.0, -2.5, 3.0, -6.0)]
    out = SimpleNamespace(view=view, cam=cam, plan=plan, mir=mir, px=S, off_skin=off_skin, off_wall=off_wall,
                          off_roof=roof, point=point)
    for name, poly, r in (("skin", S.skin, rows), ("wall", S.wall, rows[4:])):
        P, tri, nb = conforming_mesh(poly, rings=RINGS_PX, rows=r, step=9.0)
        P = P.copy()
        P[:, 0] = mir(P[:, 0])
        setattr(out, name, (P, tri, nb))
    return out


def shroud_roof(side, under=0.0):
    """For photo_panel: a shroud's side face and roof without rims or pocket, defined beyond its outline too, or the
    surface UNDER metres inside it."""
    S = _shroud(side)
    return lambda u, v: (lambda x, z, o=S.off_roof(S.mir(u), v) + under: side * (S.plan(x) - o))


def shroud_point(side, u, v):
    """3D point of a shroud's outer skin at a pixel of its profile photo."""
    S = _shroud(side)
    return S.point(S.off_skin, u, v)


@functools.lru_cache(maxsize=None)
def _shroud_shells(side):
    S = _shroud(side)
    skin, X = shell(*S.skin, lambda u, v: S.point(S.off_skin, u, v), 0.003, side, "plastic_red")
    wall, _ = shell(*S.wall, lambda u, v: S.point(S.off_wall, u, v), WALL_T, side, "plastic_red")
    b2, end = S.px.top
    return skin.add(wall), X[b2:end + 1]


def _deck(side):
    """The bolt plate's rows: from each point of the skin's top edge (the roof's own vertices) in to the tank."""
    edge = _shroud_shells(side)[1]
    rows = []
    for p in edge:
        y_in = min(float(np.interp(p[0], DECK_X, DECK_Y)), abs(p[1]) - 0.004)
        k = np.linspace(0.0, 1.0, 9)
        rows.append(np.stack([np.full(9, p[0]), side * (abs(p[1]) + (y_in - abs(p[1])) * k), p[2] - DECK_DROP * k * k],
                             axis=1))
    return rows


def deck_point(side, x, y):
    """Point on a shroud's bolt plate at (x, |y|)."""
    rows = _deck(side)
    o = np.argsort([r[0, 0] for r in rows])
    xs = np.array([rows[i][0, 0] for i in o])
    y_out = float(np.interp(x, xs, [abs(rows[i][0, 1]) for i in o]))
    y_in = float(np.interp(x, xs, [abs(rows[i][-1, 1]) for i in o]))
    zt = float(np.interp(x, xs, [rows[i][0, 2] for i in o]))
    return np.array([x, side * abs(y), zt - DECK_DROP * sat((y_out - abs(y)) / (y_out - y_in)) ** 2])


def shroud_decks():
    """The bolt plates beside the tank (TOP): from the roof's top edge in to the edge at the tank. Each plate's
    outer edge IS the row of vertices along the skin's top edge, so the roof and the plate are one skin: no slit and
    no overlap. Edge-on in the profile photos, so its height is the outline's top edge; the 3 mm fall inward is EST.
    Ahead of the plate (x > 0.93) the shroud's top is open, as in the top photo (the radiator's cap shows there)."""
    m = Mesh()
    for side in (1, -1):
        g = grid(Mesh(), _deck(side), "plastic_red", closed_u=False)
        V = np.asarray(g.V)
        a, b, c = (V[list(g.F[0])[i]] for i in range(3))
        if np.cross(b - a, c - a)[2] < 0:                          # normals up: the 3 mm of plastic is underneath
            g.F = [f[::-1] for f in g.F]
        m.add(g)
    return m


def shrouds():
    m = Mesh()
    for side in (1, -1):
        m.add(_shroud_shells(side)[0])
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


# ---------------------------------------------------------------- side panels
PANEL_H = 0.100      # the face reaches the plan envelope this far under the seam (LEFT: the panel is 93 to 139 mm
#                      tall; TOP: evenly lit from the seam out to the envelope, so one even lean; distribution EST)
# Width of the bead along the panel's top edge, under the seam with the seat. LEFT: a bright band 8 px wide at
# columns 2300..2540 (zoomed), a bright line 19 to 23 px under the seam at 2580..2820 (steps of +30 / -30).
BEAD_U, BEAD_PX = [2300, 2540, 2600, 2820], [8, 8, 19, 21]
# The seam between the seat's skirt and the side panel: SEAM_PX, the seat's hem line (SEAT_HEM_PX).

# The panel's tail (round 3, 2026-11-11). Read per column of the LEFT photo (the RIGHT photo, mirrored, gives the same
# rows within 3 px wherever the can does not cover them), classing each pixel of the glossy red as dark (g < 45: the
# plain red, (238, 22, 35)), light (g > 88: a reflection, (245, 95, 100)) or medium, every 5 px from u 2760 to 2965.
# Down each column under the seat's hem or the fender's dark crease line: a light facet (A, from u 2805: under the
# hem it is the bead), a dark line with a light line 2 to 4 px under it (the crease, lr34: "one crisp crease and a
# highlight line along it"), a dark face (B, dying out at u 2895), a light band (C, from u 2750 back), a dark band
# (D: the face turning in under the fold C/D), then the red ends. Toward the tail A, the crease, C and D converge on
# one point at (2949, 805); behind D's outer edge (u 2895..2945, rows 818..862) lies the fender's flank, medium red
# (g 65..75) as it is behind the panel (u 2960). The traced tail of rounds 1 and 2 ran on over that flank to an
# upright rear edge at u 2946 and stood 35 to 55 mm out from it: the "wedge" of the lr34 review.
# Top edge (A's top, under the fender's dark crease line, from u 2852; ahead of that it tucks under the seat's hem, 3.5
# to 6 px over A's top at u 2830..2850, and runs on the hem's line to u 2836):
PANEL_TAIL_TOP_PX = [(2836, 792.5), (2844, 791.5), (2852, 790.3), (2860, 789.5), (2870, 787.5), (2880, 786.5),
                     (2890, 784.5), (2900, 786.5), (2910, 790.5), (2920, 792.5), (2930, 795.5), (2940, 797.5),
                     (2946, 800.5)]
PANEL_TIP_PX = (2949.0, 805.0)
# Crease: the boundary of the dark line and the light line under it (ahead of u 2810 it is the bead's line, 21 px
# under the hem):
PANEL_CREASE_PX = [(2780, 836.0), (2800, 833.0), (2820, 832.0), (2830, 830.5), (2840, 829.5), (2850, 827.5),
                   (2860, 825.5), (2870, 823.5), (2880, 821.5), (2890, 818.5), (2900, 817.5), (2910, 815.5),
                   (2920, 813.5), (2930, 811.5), (2940, 810.0)]
# Fold (the face's widest line, where it turns in: C's lower edge). Ahead of u 2760 the photo's face is one even red
# down to the black part (no C band): the round 2 ridge's two points, as estimated then, carry it on.
PANEL_FOLD_PX = [(2640, 968.0), (2700, 938.0), (2760, 916.0), (2780, 913.5), (2800, 903.5), (2810, 898.5),
                 (2820, 894.5), (2830, 890.5), (2840, 887.5), (2850, 884.5), (2860, 880.5), (2870, 872.5),
                 (2880, 861.5), (2890, 848.5), (2900, 834.5), (2910, 821.0), (2920, 818.5), (2930, 816.0),
                 (2940, 813.5)]
# Lower edge over the can, each side from its own photo (left-photo columns for both). The last row of the red, its
# rounded edge's highlight included (r > 200, r - g > 110): left 956.5 / 933.5 / 904.5 / 891.5 at u 2760 / 2800 /
# 2850 / 2870, right 958.5 / 936.5 / 908.5 / 894.5 (the coordinator's check of the RIGHT view: the panel covered the
# can's top there by 20 to 27 px; the traced outline ran 10 px under the red on the left and 25 px on the right:
# test_bike's see-through check, which trusts that trace, finds 2.9 cm2 of background over the can at RIGHT u
# 1222..1252, rows 958..982, where the photo shows the can).
# Left, behind u 2840: under the red the left photo shows the far side's can pink-grey ((180, 116, 118)), rows to
# 912 at u 2850 and 903 at 2900; round 2 read it as the plastic seen through the can (the coordinator's see-through
# check, and the traced fender outline, take it as red) and ran the tail on behind it there: kept, its corner rounded
# up into D's seam (round 2's upright free edge at u 2946 crumpled the close-ups). Against it: the can's bolt head at
# (2853, 915) shows, and nothing on the near side can be in front of it. Right: the can is in front of the panel, so
# its edge is hidden; the mirrored left edge lies 2 to 4 px above the visible red-to-silver edge: the panel ends
# there (the coordinator's request).
PANEL_LOW_PX = {
    1: [(2690, 997.5), (2700, 991.5), (2710, 985.5), (2720, 979.5), (2730, 973.5), (2740, 967.5), (2750, 962.0),
        (2760, 956.5), (2770, 950.5), (2780, 944.5), (2790, 938.5), (2800, 933.5), (2810, 927.5), (2820, 921.5),
        (2830, 916.0), (2840, 913.0), (2850, 912.0), (2860, 911.0), (2870, 909.5), (2880, 906.0), (2888, 899.0),
        (2894, 887.0)],
    -1: [(2690, 997.5), (2700, 991.5), (2710, 986.5), (2720, 980.5), (2730, 975.5), (2740, 969.5), (2750, 964.5),
         (2760, 958.5), (2770, 953.5), (2780, 947.5), (2790, 941.5), (2800, 936.5), (2810, 930.5), (2820, 925.5),
         (2830, 919.5), (2840, 914.5), (2850, 908.5), (2860, 902.5), (2870, 894.5), (2880, 885.5), (2890, 876.5)]}
# D's outer edge on the fender's flank (the seam), up to the tip (LEFT; RIGHT 843.5 / 832.5 / 821.5 at 2920..2940):
PANEL_SEAM_TAIL_PX = [(2900, 862.0), (2910, 852.5), (2920, 841.5), (2930, 830.5), (2940, 818.5), (2946, 810.0)]
# The panel's top edge in plan (TOP, the dark seam line outside the fender's flank, left side; x on z 0.965): it stays
# 0.094 to 0.098 out from x 0.08 to 0.17 (the seat's hem, narrowing to its tail, is 0.078 at x 0.128: between the two
# TOP shows the fender's flank, dark) and comes out to 0.101 at x 0.039. Smoothed:
PANEL_SEAM_Y = [(0.035, 0.1015), (0.048, 0.1004), (0.066, 0.0986), (0.083, 0.0968), (0.100, 0.0957), (0.120, 0.0952),
                (0.140, 0.0960), (0.170, 0.0975)]
# The crease in plan (TOP, the light facet A's outer edge, left side; x on z 0.945): half-width at x
PANEL_CREASE_Y = [(0.035, 0.1050), (0.039, 0.1086), (0.048, 0.1112), (0.057, 0.1121), (0.066, 0.1139),
                  (0.075, 0.1139), (0.092, 0.1130), (0.110, 0.1112), (0.128, 0.1104), (0.146, 0.1095),
                  (0.155, 0.1086), (0.173, 0.1077)]
# The fold's half-width is the plan envelope (width(x)): TOP, the outer edge of the dark band outside the crease,
# 0.1535 / 0.1454 / 0.1347 / 0.1222 / 0.1168 at x 0.128 / 0.083 / 0.066 / 0.048 / 0.039, within 3 mm of it. In lr34
# the fold, cast at that width from its LEFT rows, lands on the photo's light-to-dark edge (2600, 767), (2558, 810).
PANEL_TUCK = 0.010   # the free lower edge lies this far inside the fold (EST: D, dark, 15 to 40 px tall in LEFT)


def _union(px, poly):
    """The union of two closed pixel outlines, as one closed curve (rasterised at half pixels, contoured, resampled
    every 3 px and smoothed over 0.7 px)."""
    from PIL import Image, ImageDraw
    import contourpy
    from scipy.ndimage import gaussian_filter1d
    S = 2
    allp = np.vstack([px, poly])
    lo = np.floor(allp.min(axis=0)) - 4
    n = np.ceil((allp.max(axis=0) - lo + 4) * S).astype(int)
    im = Image.new("L", (int(n[0]), int(n[1])), 0)
    d = ImageDraw.Draw(im)
    for Q in (px, poly):
        d.polygon([(float((a - lo[0]) * S), float((b - lo[1]) * S)) for a, b in Q], fill=1)
    c = max(contourpy.contour_generator(z=(np.asarray(im) > 0).astype(float)).lines(0.5), key=len)
    P = resample(c[:-1] / S + lo, 3.0)
    return np.stack([gaussian_filter1d(P[:, 0], 0.7, mode="wrap"), gaussian_filter1d(P[:, 1], 0.7, mode="wrap")], axis=1)


@functools.lru_cache(maxsize=None)
def _panel(side):
    """A side panel's outline and surface. Section, top to bottom: the top edge sits at the seam under the seat's
    hem (TOP: the hem is the seat's outermost line, seat_hem_hw) and tucks under it over a bead; from the bead's crease the
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
    # over the can the trace runs 10 (left) to 25 px (right) under the photo's red: cut at PANEL_LOW_PX, then the
    # tail (PANEL_TAIL_TOP_PX, the tip, PANEL_SEAM_TAIL_PX, PANEL_LOW_PX) takes over from u 2836 (the trace's top
    # behind that is the hem's line, 4 px over the tail's edge: a notch at the hand-drawn cut, u 2845)
    low = np.array(PANEL_LOW_PX[1 if side > 0 else -1], float)
    px = _cut(px, lambda uu, vv: (left_u(np.asarray(uu, float)) < 2836.0)
              & ((left_u(np.asarray(uu, float)) < low[0, 0] - 2.0)
                 | (vv <= np.interp(left_u(np.asarray(uu, float)), low[:, 0], low[:, 1]))))
    hem_2800 = float(np.interp(2800.0, sm[:, 0], sm[:, 1]))
    tail = np.vstack([[(2800.0, hem_2800 + 1.0)], [q for q in SEAM_PX if 2800 < q[0] < 2830], PANEL_TAIL_TOP_PX,
                      [PANEL_TIP_PX], np.array(PANEL_SEAM_TAIL_PX)[::-1],
                      low[low[:, 0] >= 2800][::-1]])
    if side < 0:
        tail[:, 0] = 3999.0 - tail[:, 0]
    px = _union(px, tail)
    E = Edges(view, px)
    run = _longest_run(E.top)                          # the seam: the long top-facing stretch of the outline
    # the rest of the outline (front and lower edges ahead of the can) is the trace, ragged by 1 to 3 px against the
    # black part: smoothed over 12 px more (the seam is the measured SEAM_PX, and behind u 2686 every edge is
    # measured: they stay)
    from scipy.ndimage import gaussian_filter1d
    w = np.ones(len(px))
    w[run] = 0.0
    w[np.array([left_u(a_) for a_ in px[:, 0]]) > 2686.0] = 0.0
    w = np.clip(gaussian_filter1d(w, 3.0, mode="wrap") * 2.0 - 1.0, 0.0, 1.0)
    ps = np.stack([gaussian_filter1d(px[:, 0], 4.0, mode="wrap"), gaussian_filter1d(px[:, 1], 4.0, mode="wrap")], 1)
    px = px + w[:, None] * (ps - px)
    E = Edges(view, px)
    run = _longest_run(E.top)
    seam = px[run]
    bead = lambda u: float(np.interp(left_u(u), BEAD_U, BEAD_PX))
    cl = seam - E.n[run] * np.array([bead(u) for u in seam[:, 0]])[:, None]
    cl = np.stack([_gauss(cl[:, 0], 3.0), _gauss(cl[:, 1], 3.0)], axis=1)[6:-6]
    clu = np.array([left_u(u) for u in cl[:, 0]])
    cl = cl[(clu > 2080.0) & (clu < 2772.0)]           # not along the steep edge under the seat's nose; behind u 2780
    kt = np.array(PANEL_CREASE_PX, float)              # the tail's crease (measured)
    cl = np.vstack([cl, _mpx(view, kt), _mpx(view, [PANEL_TIP_PX])])
    rg = np.array(PANEL_FOLD_PX, float)
    shroud_w = _shroud_plan(side)
    # The section is a function of the column and of the height under the panel's top edge only (it was a function
    # of the distance to the traced outline and of the outline's height per 6 px column, smoothed over 18 px: each
    # wiggle of the trace became a dent; close-ups showed the face lumpy). Top edge: the seam (SEAM_PX) to u 2826,
    # then the tail's upper edge (PANEL_TAIL_TOP_PX). Height of the panel per column: smoothed over 40 px.
    tp = np.array([q for q in SEAM_PX if q[0] <= 2826] + PANEL_TAIL_TOP_PX + [PANEL_TIP_PX], float)
    top_v = lambda ul: float(np.interp(ul, tp[:, 0], tp[:, 1]))
    def _sm(t, sig=0.8):
        # a measured line, read to 0.5 px at 10 to 20 px steps: a smoothing spline through it (a straight-line
        # interpolation has a kink at every reading, and the face's lean, set by the rows, followed each kink)
        from scipy.interpolate import UnivariateSpline
        t = np.asarray(t, float)
        sp = UnivariateSpline(t[:, 0], t[:, 1], k=3, s=len(t) * sig ** 2)
        q = np.arange(t[0, 0], t[-1, 0] + 0.01, 2.0)
        return np.column_stack([q, sp(q)])
    kt_, rg_ = _sm(np.vstack([kt, [PANEL_TIP_PX]])), _sm(np.vstack([rg, [PANEL_TIP_PX]]))
    low_s = _sm(low, 0.4)
    seam_s = _sm(np.vstack(([low[-1:]] if low[-1, 0] < 2895 else []) + [PANEL_SEAM_TAIL_PX, [PANEL_TIP_PX]]), 0.4)
    tp = np.vstack([tp[tp[:, 0] < 2780], _sm(tp[tp[:, 0] >= 2780])])
    crease_v = lambda ul: float(np.interp(ul, kt_[:, 0], kt_[:, 1]))
    fold_v = lambda ul: float(np.interp(ul, rg_[:, 0], rg_[:, 1]))
    def edge_v(ul):
        # the free lower edge to its last column, then D's seam on the fender's flank (the left one meets it with a
        # short free rear edge at u 2900: two pieces)
        if ul <= low[-1, 0]:
            return float(np.interp(ul, low_s[:, 0], low_s[:, 1]))
        return float(np.interp(ul, seam_s[:, 0], seam_s[:, 1]))
    cy = np.array(PANEL_CREASE_Y, float)
    sy_ = np.array(PANEL_SEAM_Y, float)
    pl_ = np.array([(left_u(a_), b_) for a_, b_ in px])
    ub = np.arange(pl_[:, 0].min(), pl_[:, 0].max() + 4.0, 4.0)
    hgt = np.array([pl_[np.abs(pl_[:, 0] - q) < 4.0, 1].max() - top_v(q) if (np.abs(pl_[:, 0] - q) < 4.0).any()
                    else 60.0 for q in ub])
    hgt = _gauss(np.clip(hgt, 25.0, None), 10.0)
    # plan envelope (TOP), smoothed over 40 mm. Behind x 0.12 it is the tails' (TOP, the red outside the fender's
    # seam per column: out to 0.148 / 0.139 / 0.134 / 0.120 / 0.113 / 0.107 at x 0.087 / 0.074 / 0.060 / 0.047 /
    # 0.040 / 0.033, the point at x 0.027), smoothed over 10 mm only
    tx_ = TT["x"]
    tw_ = _gauss(_PLAN[1 if side > 0 else -1], 8.0)
    fx, fhw = _fender_lines()[:2]

    tw3 = _gauss(_PLAN[1 if side > 0 else -1], 2.0)         # behind x 0.12 less smoothed: the tails taper in plan

    def width(x):
        W = float(np.interp(min(max(x, -0.19), 0.80), tx_, tw_))
        W += (float(np.interp(x, tx_, tw3)) - W) * smoothstep((0.14 - x) / 0.03)
        return max(W, float(np.interp(x, fx, fhw)) + 0.0035)

    def surf(u, v):
        ul = left_u(u)
        T = top_v(ul)
        d = max(v - T, 0.0)                                # px under the panel's top edge
        db = bead(u)
        reach = min(PANEL_H / MPP, 0.92 * float(np.interp(ul, ub, hgt)))
        F = fold_v(ul)
        if ul > rg[0, 0]:                                  # the face is at its widest on the fold
            reach += (min(reach, max(F - T, 25.0)) - reach) * smoothstep((ul - rg[0, 0]) / 60.0)
        K, Ed = crease_v(ul), edge_v(ul)
        # the tail's own section (PANEL_TAIL_TOP_PX ..): from u 2790, in full from 2830
        wt = smoothstep((ul - 2790.0) / 40.0)
        # under the fold the face turns in (D) to the lower edge, from u 2730 (where the photo's band C begins); on
        # the fender's flank (u 2890 on) D's edge is the seam with the flank
        wd = smoothstep((ul - 2730.0) / 50.0) if v > F else 0.0
        on_flank = smoothstep((ul - 2840.0) / 60.0)

        def f(x, z):
            W = width(x)
            ys = min(max(seat_hem_hw(min(max(x, 0.09), 0.78)), 0.064), W - 0.004)
            if x < 0.105:                                  # the tail's top edge laps over the fender's lip
                lap = fender_outer_y(x, z) + 0.0060      # (ahead of x 0.105 it tucks under the seat's hem)
                ys = ys + (max(lap, ys) - ys) * smoothstep((0.105 - x) / 0.02)
            y = ys + (W - ys) * (1.0 - (1.0 - sat(d / reach)) ** 1.3)
            if d < db:
                y -= 0.55 * (db - d) * MPP * smoothstep((x - 0.03) / 0.06)
            if wt > 0.0:
                # facet A from the top edge out to the crease (TOP: PANEL_CREASE_Y), the face out to the fold (the
                # plan envelope), convex as the panel's face ahead. The top edge: TOP's seam (PANEL_SEAM_Y), but at
                # most 0.8 mm clear of the fender's lip with its 3 mm shell (5 to 12 mm out, it stood as a ledge over
                # the lip in the lr34 close-up; the photo's facet runs on from the lip) (a function of x only: as a function of
                # each vertex's height over the lip's roll, with the old tuck under the seat's hem ahead of x 0.105
                # blended in, it came out jagged: the wrinkle at x 0.085..0.125 of round 2)
                yk = min(float(np.interp(x, cy[:, 0], cy[:, 1])), W - 0.002)
                yf = float(np.interp(x, fx, fhw))          # the fender's lip
                y0 = max(min(float(np.interp(x, sy_[:, 0], sy_[:, 1])), yf + 0.0038), yf + 0.0035)
                if v <= K:
                    yt = y0 + (yk - y0) * sat((v - T) / max(K - T, 1.0))
                else:
                    yt = yk + (W - yk) * (1.0 - (1.0 - sat((v - K) / max(F - K, 1.0))) ** 1.3)
                y += wt * (yt - y)
            if wd > 0.0:
                # (a function of x only: through the fender's lip roll and under its lower edge, as a function of
                # each vertex's height, it crumpled the lower tail in the close-ups)
                yf = float(np.interp(x, fx, fhw)) + 0.0035
                ye = (W - PANEL_TUCK) + (yf - (W - PANEL_TUCK)) * on_flank
                s = sat((v - F) / max(Ed - 1.0 - F, 1.0))   # on the edge's own row 1 px early (the outline is
                #                                          resampled and smoothed by 0.7 px)
                y -= wd * (W - ye) * s ** 1.5
            if x > 0.585:                                  # the panel's nose lies 5 mm inside the shroud's tail
                y = min(y, shroud_w(x) - 0.005 * smoothstep((x - 0.585) / 0.015))
            if x < 0.125 and (v > F or wt < 1.0):          # never inside the fender: clear of its face by the
                y = max(y, fender_outer_y(x, z) + 0.0035)  # panel's 3 mm shell and 0.5 mm
            return side * y
        return f
    # extra rows of vertices through the tail, where four lines meet within a few px and the face turns 40 mm in 20
    # px: between the crease and the fold, under the fold, and along the lower edge (on a 9 px mesh it came out
    # jagged in the close-ups)
    uq = np.arange(2784.0, 2944.0, 4.0)
    rows = [(lambda q: crease_v(q) + 0.5 * (fold_v(q) - crease_v(q))), (lambda q: fold_v(q) + 4.0),
            (lambda q: fold_v(q) + 0.5 * (edge_v(q) - fold_v(q))), (lambda q: edge_v(q) - 4.0),
            (lambda q: top_v(q) + 0.5 * (crease_v(q) - top_v(q)))]
    tail_lines = [_mpx(view, np.column_stack([uq, [r(q) for q in uq]])) for r in rows]
    return SimpleNamespace(view=view, px=px, E=E, width=width, surf=surf, seam=seam, crease=cl, extra=extra,
                           tail_lines=tail_lines,
                           ridge=_mpx(view, rg))


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
                          lines=[Pn.crease, Pn.ridge] + Pn.tail_lines, line_step=5.0))
        for piece in Pn.extra:
            # the red triangle under the seat's nose, between the seat and the shroud's traced top edge: outlines.py
            # hands it to the side panel (its hand-drawn seam), but it is the shroud's roof running on under the
            # seat. On the panel's own surface it stood 6 to 9 mm clear of everything as a fin (audit: floating); on
            # the roof itself it lay in the skin where the two traces overlap (audit: 3 mm). So: 6 mm under the
            # roof, below the skin's 3 mm shell and its turned edge. Its upper part is the seat's nose (LEFT, 6x: the
            # cover's hem runs from (1964, 758) down to (1980, 780) across it, SEAT_HEM_PX; it stood 9 mm proud of
            # the remodelled nose as a fin): only the part under the hem, and ahead of the nose, is kept.
            hm = np.array(SEAT_HEM_PX, float)
            ul = (lambda uu: uu) if side > 0 else (lambda uu: 3999.0 - uu)
            keep = lambda uu, vv: (ul(uu) < hm[0, 0] - 2.0) | (vv > np.interp(ul(uu), hm[:, 0], hm[:, 1]) + 2.0)
            for part in _cut(piece, keep, every=True):
                if len(part) >= 8:
                    m.add(photo_panel(view, part, shroud_roof(side, 0.006), 0.003, "plastic_red", step=9.0))
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
            # the filter's screen behind it: a dark green diamond mesh (detail 475833, u 2350..2650, v 600..800 at 4x:
            # strands on two diagonals about 11 px, 2 mm, apart, lit (18, 63, 5), in the shadow (8, 35, 2)),
            # detail_plastics.INTAKE_MESH, laid on x and z
            sc = photo_panel(view, hin, back, 0.002, "intake_mesh", step=9.0)
            V = np.asarray(sc.V)
            for fi, f in enumerate(sc.F):
                sc.uv[fi] = [(float(-side * V[i, 0] / 0.016), float(V[i, 2] / 0.016)) for i in f]
            m.add(sc)
        # black textured lower panel (airbox side): its own exact outline, 6 mm inside the red panel's envelope.
        # Its moulded Y ribs are a normal map (detail_plastics.SIDE_COVER) laid on x and z, the tile 34.2 x 29.6 mm
        # (two lattice steps each way), u running backward on the left and forward on the right
        # the panel bolt sits in a round pocket (detail 475833, 0.186 mm/px from the bolt's 8 mm hex: the dark recess
        # 160 px, 30 mm across; depth 8 mm EST): a hole in the black part, a wall and a floor behind it
        bc = _mpx(view, [PANEL_BOLT_PX])[0]
        lsurf = lambda u, v, q=side: (lambda x, z: q * (Pn.width(x) - 0.006))
        pr = POCKET_R / MPP
        ang = np.linspace(0.0, 2 * math.pi, 33)[:-1]
        hole = np.stack([bc[0] + pr * np.cos(ang), bc[1] + pr * np.sin(ang)], axis=1)
        lp = photo_panel(view, clean_outline(view, OUT2[low], sigma=4.0), lsurf, 0.003, "black_texture",
                         holes_px=[hole])
        rim = np.array([_on_surface(cam, u, v, lsurf(u, v), side * 0.15) for u, v in hole])
        rings = [rim]
        for k_ in (0.3, 0.7, 1.0):                         # the wall, rounded into the floor
            rr = rim - np.array([0.0, side * POCKET_D * k_, 0.0])
            cen = rr.mean(axis=0)
            rings.append(cen + (rr - cen) * (1.0 - 0.12 * k_ ** 4))
        pk = grid(Mesh(), rings, "plastic_black", closed_u=True, cap1=True)
        if side < 0:
            pk.F = [f[::-1] for f in pk.F]
        m.add(pk)
        V = np.asarray(lp.V)
        tw, th = 0.0342, 0.0342 * math.sqrt(3) / 2
        for fi, f in enumerate(lp.F):
            lp.uv[fi] = [(float(-side * V[i, 0] / tw), float(V[i, 2] / th)) for i in f]     # (u, v, n) right-handed
        m.add(lp)
    return m


PANEL_BOLT_PX = (2426.0, 1136.0)   # LEFT: the side panel's bolt in its black lower part (detail_plastics.panel_bolts)
POCKET_R, POCKET_D = 0.015, 0.008  # its pocket's radius and depth


# ---------------------------------------------------------------- lofted parts: seat, fenders
def _line(view, name, y):
    P = _true_outline(view, OUT[name], y)
    o = np.argsort(P[:, 0])
    return P[o]


TAIL_X0 = 0.20       # the red wall under the tail (detail_plastics.tail_under): EST, hidden in the other photos
TAIL_TOP_ROW = 606   # REAR: its top edge


@functools.lru_cache(maxsize=None)
def _tank_tree():
    import importlib
    from scipy.spatial import cKDTree
    import parts
    fn = parts.tank
    for name in parts.PLUGINS:                              # the tank a merged module builds, if one does
        if name != "detail_plastics" and os.path.exists(os.path.join(HERE, name + ".py")):
            fn = getattr(importlib.import_module(name), "PARTS", {}).get("tank", fn)
    V = np.asarray(fn().V)
    return cKDTree(V[:, :2]), V[:, 2]


@functools.lru_cache(maxsize=None)
def _subframe_tree():
    import importlib
    from scipy.spatial import cKDTree
    import parts
    for name in parts.PLUGINS:                              # the subframe a merged module builds, if one does
        if name != "detail_plastics" and os.path.exists(os.path.join(HERE, name + ".py")):
            fn = getattr(importlib.import_module(name), "PARTS", {}).get("subframe")
            if fn is not None:
                V = np.asarray(fn().V)
                return cKDTree(V[:, :2]), V[:, 2]
    return None


def _subframe_z(x, y):
    """Top of the subframe within 12 mm of (x, y) (-1: none there): the seat's base rests on its rails."""
    t = _subframe_tree()
    if t is None:
        return -1.0
    i = t[0].query_ball_point((x, y), 0.012)
    return float(t[1][i].max()) if len(i) else -1.0


def _tank_z(x, y):
    """Top of the tank within 10 mm of (x, y), so the seat's nose stays clear of it (-1: no tank there)."""
    tree, z = _tank_tree()
    i = tree.query_ball_point((x, y), 0.010)
    return float(z[i].max()) if len(i) else -1.0


# The hem (the cover's rounded lower edge): the dark seam line under it, per column the centre of the darkest run of
# r + g within 16 px of a first reading (half-depth edges, 3 columns averaged), every 20 px from u 1966 to 2846 in the
# LEFT photo. The RIGHT photo at mirrored columns gives the same rows within 0.5 px all along. Over the seat bolt's
# pocket (u 2160..2190, rows 855..883) the line is the pocket's: interpolated across. The V at u 2266 (row 904.5) is
# the cover's lowest corner, over the joint of the shroud's tail and the side panel. Nose and tail ends read at 6x on
# a 10 px grid: (1964, 758) the nose's front, (2856, 779) and (2866, 768) the tail's tip. This line is also the side
# panels' top edge (SEAM_PX).
SEAT_HEM_PX = [(1964, 758.0), (1966, 759.5), (1986, 783.0), (2006, 796.0), (2026, 804.5), (2046, 813.5), (2066, 821.5),
               (2086, 828.5), (2106, 836.5), (2126, 844.0), (2146, 851.5), (2226, 881.0), (2246, 888.0), (2266, 904.5),
               (2286, 900.5), (2306, 898.0), (2326, 894.5), (2346, 891.0), (2366, 888.0), (2386, 885.0), (2406, 882.0),
               (2426, 879.0), (2446, 875.5), (2466, 872.0), (2486, 869.0), (2506, 866.0), (2526, 863.0), (2546, 860.0),
               (2566, 857.0), (2586, 854.0), (2606, 851.0), (2626, 848.0), (2646, 844.0), (2666, 841.0), (2686, 838.0),
               (2706, 835.0), (2726, 831.5), (2746, 828.0), (2766, 824.5), (2786, 818.0), (2806, 809.5), (2826, 799.0),
               (2846, 786.0), (2856, 779.0), (2866, 768.0)]
SEAM_PX = SEAT_HEM_PX
# The top line: the seat's upper silhouette in the LEFT photo, the first non-white row of each column (sub-pixel, where
# the darkest channel crosses half-way from the white background (255) to the cover 3 px in), every 4 px from u 1958 to 2866. It
# lies 1.5 to 2 px above the traced line OUT 'seat_top' (a mask contour); the RIGHT photo (mirrored columns) gives the
# same rows within 1 px (peak 732 at u 2005..2020 = left 1979..1994, dip 787 at 1690..1735 = left 2264..2309, tail
# 755 at 1150..1165 = left 2834..2849). Used between the nose's and the tail's own rounding (LEFT, 6x: the nose's
# top at (1985, 731) rounds over to its front at (1962, 746); the tail's top at (2850, 755.5) to its tip at (2866,
# 762)): those are the shoulder's, at both ends (SEAT_END_L).
SEAT_TOP_U = (1986.0, 2846.0)
SEAT_END_L = (0.025, 0.020)     # the shoulder's length at the nose's front and at the tail's end: LEFT, the nose
#                                 falls 3 mm in its last 20 mm then 12 mm to its front (u 1985..1962), the tail 5 mm
#                                 in its last 16 px (12.5 mm, u 2850..2866)
SEAT_SHOULDER = 0.021  # D: the top falls D to the skirt over its shoulder (seat_cover_z). REAR rows 514..562, the nose
#                      seen from behind (0.775 mm/px at x 0.76): half-widths 34 / 52 / 60 / 65.5 / 71.5 / 74.5 / 76.5 /
#                      79.5 / 81.5 / 83.5 / 85 / 85.5 / 87 px every 4 rows under the top. Projected model vertices with
#                      D 21 mm and power 2.5 (sides plus nose): rms 2.9 px (power 4: 5.7, power 3: 3.5; D 26: 2.4).
#                      LEFT: the "HONDA" print's top edge is 21 mm under the silhouette (u 2500), where the skirt
#                      starts. TOP: the cover's light band ends 69 mm out at u 2300, where this shoulder is at 29 deg
SEAT_POWER = 2.5
SEAT_LEAN = math.radians(12.0)   # the skirt leans out toward the hem: the "HONDA" print, 43 px (34 mm) tall in the
#                      LEFT photo (u 2475..2515), is 8 px (7 mm) deep in the TOP photo (rows 1028..1036, 1212..1220)
SEAT_NOSE_LEAN = math.radians(3.0)   # LEFT, 6x: the nose's front is upright within 2 px over its lower 10 px (EST 3)
HEM_R = 0.0012       # the hem's rounded edge (LEFT, 6x: a light line 1 to 2 px over the dark seam: EST 1.2 mm)
HEM_LIFT = 0.0025    # the hem's outer point above the dark seam line's centre (the line is the shadow under the hem
#                      and the gap to the panel, 8 px = 6 mm: SEAM_PX)
TUCK = (0.004, 0.002)  # the cover turns under the base this far in from the hem and this far up (EST, hidden: it
#                      clears the side panel's top edge, which stands under the hem, by 1.5 mm or more)
SEAT_RINGS_MM = (0.5, 1.2, 2.2, 3.5, 5.2, 7.4, 10.0, 13.2, 17.0, 21.5, 26.5, 32.0, 38.0, 45.0)
# rows of vertices parallel to the hem (mm in from it), the hem itself sampled every 4 mm: compare.raster draws a
# triangle under 2 px (3.6 mm in the top view) as one pixel, so with 3 mm samples and 22 rows 19 % of the cover
# fell through as dots in the top view's score (the base showed between them)


@functools.lru_cache(maxsize=None)
def _seat_lines():
    """The seat's hem height z(x) and top-line height z(x), each cast on the plane it lies on: the hem on the near
    side's hem (y = its half-width), the top line on the far side, 25 mm out (from the camera, 1.13 m up and 4.7 m
    away, the ray grazes the top's shoulder where its slope is 0.032: 25 mm out, 0.2 mm under the centre line)."""
    hem = []
    for cam, sg in ((LEFT, 1.0), (RIGHT, -1.0)):                # each side through its own photo's camera
        h = np.array(SEAT_HEM_PX, float)
        if sg < 0:
            h[:, 0] = 3999.0 - h[:, 0]
        W = np.array([cam.on_plane(np.array([u]), np.array([v]), "y", 0.0)[0] for u, v in h])
        for _ in range(3):                                     # on the hem's own plane
            W = np.array([cam.on_plane(np.array([u]), np.array([v]), "y", sg * max(seat_hem_hw(w[0]), 0.02))[0]
                          for (u, v), w in zip(h, W)])
        o = np.argsort(W[:, 0])
        hem.append((W[o, 0], W[o, 2] + HEM_LIFT))
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(HERE, "..", "..", "reference", "crf250r-2026", cams.FILES["left"]))
                   .convert("RGB").crop((1950, 650, 2880, 900))).astype(float).min(axis=2)
    raw = []
    for u in np.arange(SEAT_TOP_U[0], SEAT_TOP_U[1] + 1.0, 4.0):
        col = a[:, int(u) - 1950]
        i = int(np.argmax(col < 235.0))
        lvl = 0.5 * (col[max(i - 4, 0)] + col[i + 3])
        k = max(i - 1, 0) + float(np.clip((col[max(i - 1, 0)] - lvl) / max(col[max(i - 1, 0)] - col[i], 1e-6), 0, 1))
        raw.append((u, 650.0 + k))
    raw = np.array(raw)
    T = np.array([LEFT.on_plane(np.array([u]), np.array([v]), "y", -0.025)[0] for u, v in raw])
    o = np.argsort(T[:, 0])
    tx, tz = T[o, 0], _gauss(T[o, 2], 2.0)
    return hem, tx, tz


def seat_top_z(x, y=0.0):
    """Height of the seat's centre line at x (the shoulder's fall to the sides is seat_cover_z's)."""
    hem, tx, tz = _seat_lines()
    return float(np.interp(x, tx, tz))


def seat_hem_z(x, y=None):
    """Height of the hem's outer point at x on the side of y (None: the higher side). The two sides' cameras put the
    same photo rows (the photos agree within 0.5 px) at heights 2.5 mm apart in the middle (right higher): each side
    follows its own photo, so each side panel's top edge stays under its own side of the hem."""
    hem, tx, tz = _seat_lines()
    zl, zr = (float(np.interp(x, hx, hz)) for hx, hz in hem)
    if y is None:
        return max(zl, zr)
    return zr + (zl - zr) * smoothstep(0.5 + y / 0.04)


@functools.lru_cache(maxsize=None)
def _seat_sections():
    """Per point of the hem's outline: inward normal, hem height, skirt lean and the section's widths. Section
    (inward distance w from the hem): the skirt rises from the hem leaning in at LEAN to w_s, D under the top; from
    there the top's shoulder (seat_cover_z) rises to the centre line, L in on the sides (the half-width 25 and 40 mm
    in from the ends)."""
    B = seat_outline()
    t = np.roll(B, -1, axis=0) - np.roll(B, 1, axis=0)
    nin = np.stack([-t[:, 1], t[:, 0]], axis=1)                 # counter-clockwise: left of the direction is inward
    nin /= np.linalg.norm(nin, axis=1)[:, None]
    a = SEAT_LEAN - (SEAT_LEAN - SEAT_NOSE_LEAN) * np.maximum(-nin[:, 0], 0.0) ** 2
    zb = np.array([seat_hem_z(p[0], p[1]) for p in B])
    zt = np.array([seat_top_z(p[0]) for p in B])
    zb = np.minimum(zb, zt - 0.008)                             # the tail's tip: 8 mm thick at least (LEFT: the tip
    #                                                             is 8 px tall at u 2866, rows 762..770)
    D = np.minimum(SEAT_SHOULDER, 0.75 * (zt - zb))
    ws = (zt - D - zb) * np.tan(a)
    xs = _seat_plan()[0]
    L = np.array([seat_hem_hw(min(max(p[0], xs[0] + 0.04), xs[-1] - 0.025)) for p in B]) - ws
    i0, i1 = int(np.argmax(B[:, 0])), int(np.argmin(B[:, 0]))       # the nose's front, the tail's end
    from types import SimpleNamespace
    return SimpleNamespace(B=B, nin=nin, a=a, zb=zb, zt=zt, D=D, ws=ws, L=L, ws_end=(ws[i0], ws[i1]))


def seat_cover_z(P2):
    """Heights of the cover at plan points P2 (n, 2). In the skirt (closer to the hem than w_s) the height rises
    evenly from the hem. Above it the top falls D (1 - (1 - qs^4)(1 - qf^4)(1 - qt^4)) under the centre line, qs
    from the distance to the side hem across (L the half-width), qf and qt from the distances to the nose's front
    and the tail's end (SEAT_END_L): the shoulders of the sides and the ends add up at the nose's corners, which come
    out round as the rear photo has them (REAR rows 514..534: the nose's top is within 1.2 mm of its peak for only
    26 mm either side of the centre line). D, w_s and the hem height are the nearest hem points' (averaged over
    those within 8 mm of the nearest, so they blend where the nearest jumps from a side to the front)."""
    from scipy.spatial import cKDTree
    S = _seat_sections()
    B = S.B
    P2 = np.asarray(P2, float)
    d = cKDTree(_dense(B, sub=12, closed=True)[:-1]).query(P2)[0]
    dk, jk = cKDTree(B).query(P2, k=24)
    wt = np.exp(-((dk - dk[:, :1]) / 0.008) ** 2)
    wt /= wt.sum(axis=1, keepdims=True)
    par = {k: (getattr(S, k)[jk] * wt).sum(axis=1) for k in ("zb", "zt", "D", "ws")}
    x, y = P2[:, 0], np.abs(P2[:, 1])
    xs = _seat_plan()[0]
    zc = np.array([seat_top_z(q) for q in x])
    hw = np.array([seat_hem_hw(q) for q in x])
    Ls = np.array([seat_hem_hw(min(max(q, xs[0] + 0.04), xs[-1] - 0.025)) for q in x]) - par["ws"]
    qs = np.clip(1.0 - (hw - y - par["ws"]) / Ls, 0.0, 1.0)
    qf = np.clip(1.0 - (xs[-1] - x - S.ws_end[0]) / SEAT_END_L[0], 0.0, 1.0)
    qt = np.clip(1.0 - (x - xs[0] - S.ws_end[1]) / SEAT_END_L[1], 0.0, 1.0)
    p = SEAT_POWER
    drop = par["D"] * (1.0 - (1.0 - qs ** p) * (1.0 - qf ** p) * (1.0 - qt ** p))
    skirt = par["zb"] + (par["zt"] - par["D"] - par["zb"]) * d / np.maximum(par["ws"], 1e-6)
    return np.where(d < par["ws"], skirt, zc - drop)


SEAT_UV_TILE = 0.064  # metres of cover per repeat of its grain texture (detail_plastics.SEAT_GRAIN)


def _box_uv(V, f, tile=SEAT_UV_TILE):
    """Corner UVs of a face by the axis its normal is closest to (top: x, y; sides: x, z; ends: y, z), u turned so
    that (u, v, normal) is right-handed: on a mirrored UV frame a normal map's bumps read as dents."""
    P = V[list(f)]
    nr = np.cross(P[1] - P[0], P[2] - P[0])
    k = int(np.argmax(np.abs(nr)))
    a, b = {2: (0, 1), 1: (0, 2), 0: (1, 2)}[k]
    sg = {2: 1.0, 1: -1.0, 0: 1.0}[k] * (1.0 if nr[k] > 0 else -1.0)
    return [(float(sg * p[a] / tile), float(p[b] / tile)) for p in P]


def seat():
    """Seat: cover (foam shape) and base, built on the hem's plan outline (seat_outline, TOP).
    Every point of the cover is placed by its distance w from the hem in plan (exact rows of vertices at
    SEAT_RINGS_MM carry the skirt and the shoulder): the skirt rises from the hem leaning in at SEAT_LEAN, the top
    falls to it over the measured shoulder (SEAT_SHOULDER), all round the seat, so the blunt nose and the rounded tail
    get the same edge as the sides. Profile: hem and top lines of the LEFT photo (SEAT_HEM_PX, OUT 'seat_top').
    Under the hem the cover's edge is rounded (HEM_R) and turns in under the black base, which closes the seat 4 mm
    above the hem, clear of the tank at the nose and of the red wall under the tail."""
    S = _seat_sections()
    B = S.B
    nb = len(B)
    from scipy.spatial import cKDTree
    P2, tri, nb2 = conforming_mesh(B * 1000.0, rings=SEAT_RINGS_MM, step=7.0)
    assert nb2 == nb
    P2 = P2 / 1000.0
    X = np.column_stack([P2, seat_cover_z(P2)])
    X[:nb, 2] = S.zb
    m = Mesh()
    top = m.verts(X)
    for f in tri:
        a, b, c = (int(q) for q in f)
        if np.cross(X[b] - X[a], X[c] - X[a])[2] < 0:
            b, c = c, b
        m.face((top + a, top + b, top + c), "seat")
    # the hem's rounded edge and the tuck under the base: (inward w, height above the hem's outer point)
    rb = HEM_R
    sec = [(rb * (1 - math.cos(q)), -rb * math.sin(q)) for q in np.radians([30.0, 60.0, 90.0, 120.0])]
    sec += [(2.6 * rb, -0.45 * rb), TUCK]
    rings = [X[:nb]] + [np.column_stack([B + w * S.nin, S.zb + dz]) for w, dz in sec]
    # where the seat is thin (the tail's point: 8 mm) the tuck would reach the cover's top: keep it 1.5 mm under it
    cz = seat_cover_z(rings[-1][:, :2])
    rings[-1][:, 2] = np.minimum(rings[-1][:, 2], cz - 0.0015)
    # base: the tuck's end ring, then 4 mm further in at the base's height, then flat
    z_wall = float(REAR.on_plane(np.array([2000.0]), np.array([float(TAIL_TOP_ROW)]), "x", TAIL_X0)[0][2])

    def z_base(x, y):
        z = max(seat_hem_z(x) + 0.004, _tank_z(x, y) + 0.0005, _subframe_z(x, y) + 0.0005,
                (z_wall + 0.003) * smoothstep((0.30 - x) / 0.04))
        return max(min(z, seat_top_z(x, y) - 0.010), seat_hem_z(x) + 0.001)
    BT = rings[-1][:, :2]
    Pb, trib, nbb = conforming_mesh(BT * 1000.0, rings=(4.0,), step=12.0)
    Pb = Pb / 1000.0
    Zb = np.array([z_base(p[0], p[1]) for p in Pb])
    Zb = np.minimum(Zb, seat_cover_z(Pb) - 0.003)          # never through the cover (the tail's thin point)
    Zb[:nbb] = rings[-1][:, 2]
    base = m.verts(np.column_stack([Pb, Zb]))
    VB = np.column_stack([Pb, Zb])
    for f in trib:
        a, b, c = (int(q) for q in f)
        if np.cross(VB[b] - VB[a], VB[c] - VB[a])[2] > 0:       # normals down
            b, c = c, b
        m.face((base + a, base + b, base + c), "plastic_black")
    idx = [top + np.arange(nb)] + [m.verts(r) for r in rings[1:-1]] + [base + np.arange(nb)]
    idx = [np.asarray(k) if np.ndim(k) else k + np.arange(nb) for k in idx]
    for k in range(len(idx) - 1):
        for i in range(nb):
            q = (i + 1) % nb
            # going round counter-clockwise, from the outer ring to the inner: normals point out and down
            m.face((int(idx[k][i]), int(idx[k + 1][i]), int(idx[k + 1][q]), int(idx[k][q])), "seat")
    V = np.asarray(m.V)
    for fi, (f, mat) in enumerate(zip(m.F, m.M)):
        if mat == "seat":
            m.uv[fi] = _box_uv(V, f)
    seat.sections = S
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


# Rear fender (micro-detail pass, 2026-11-11).
# Plan: half-width in TOP photo px about row 1124.5, the red against the floor, the chain and the label (a scan per
# column, checked at 3x on a 10 px grid). Its edges at the root are the dark seams to the side panels' tails (rows
# 1022 / 1227 at u 2720). It tapers straight to a shoulder at u 3128 (63 px), then an arrow point at u 3188.5 (the
# half angle 47 deg; the tip and the shoulder rounded about 4 px).
FENDER_PLAN_PX = [(2720, 103.0), (2740, 102.0), (2760, 101.0), (2780, 100.0), (2800, 99.5), (2820, 97.5), (2840, 95.5),
                  (2860, 93.5), (2880, 92.0), (2900, 90.0), (2920, 87.5), (2950, 84.0), (3000, 78.5), (3050, 73.0),
                  (3100, 67.0), (3110, 65.5), (3128, 63.0), (3140, 57.0), (3150, 47.0), (3160, 36.0), (3170, 25.0),
                  (3180, 14.0), (3186, 6.0), (3188.5, 0.0)]
# The side photos put the tip at x -0.290 (LEFT u 3353) and -0.287 (RIGHT u 646), the top photo at -0.305: the mean
# is used (the plan's x is stretched by up to 8.3 mm toward the tip; the seat, where they agree within 3 to 7 mm, is
# not moved).
FENDER_TIP_SHIFT = 0.0083
# Profile (LEFT, first and last non-white row of each column against the white floor, 10 px steps): the top line
# from just behind the seat's tip to the tip's upper corner; the near flank's lower edge from where it leaves the
# muffler (u 2960) to the tip's lower corner (the tip's end slants: top corner u 3340, lower u 3353).
FENDER_TOP_PX = [(2880, 774), (2900, 770.5), (2920, 770), (2940, 768), (2950, 767), (2970, 765), (3000, 763),
                 (3030, 760.5), (3050, 759), (3080, 757), (3100, 755), (3130, 753), (3150, 752), (3180, 750),
                 (3200, 748), (3230, 746), (3250, 745), (3300, 743), (3320, 742), (3340, 740.5)]
FENDER_LOW_PX = [(2960, 847), (2980, 839), (3000, 831), (3020, 824), (3050, 816), (3080, 809), (3100, 804),
                 (3130, 797), (3150, 793), (3180, 786), (3200, 782), (3230, 776), (3250, 773), (3280, 767),
                 (3300, 764), (3320, 759), (3340, 754), (3353, 751)]
# Section, from the TOP photo's bands across the blade at u 3000 (half-width 78.5 px, centre row 1124.5): a lit deck
# to 30 px out, a bright crease band 30..45 px (0.38..0.57), a dark facet to 62 px (0.79), a light strip to the edge
# (the lip rolling over into the flank); the same bands converge on the point. LEFT: under the top line a lit band
# 15 to 23 px deep (the facet and lip seen from the side), then the dark crease line and the flank.
FENDER_A1, FENDER_A2 = 0.50, 0.80   # deck edge (the crease band's middle) and facet end, fractions of the half-width
FENDER_CROWN = 0.003                # the deck's fall to its edge (EST)
FENDER_FACET = 0.008                # the facet's drop (LEFT: the lit band under the top line, less the lip: EST)
FENDER_FLARE = math.radians(8.0)    # the flank leans out toward its lower edge (REAR: the end-on outline widens
#                                     downward, rows 600..637 from 115 to 134 px: EST from that)


@functools.lru_cache(maxsize=None)
def _fender_lines():
    """The rear fender's plan half-width hw(x), top-line height zt(x) and the near flank's lower edge ze(x)."""
    t = np.array(FENDER_PLAN_PX, float)
    c = TOP.on_plane(t[:, 0], np.full(len(t), 1124.5), "z", 0.98)
    lt = TOP.on_plane(t[:, 0], 1124.5 + t[:, 1], "z", 0.98)
    rt = TOP.on_plane(t[:, 0], 1124.5 - t[:, 1], "z", 0.98)
    x = c[:, 0] + FENDER_TIP_SHIFT * smoothstep_arr(-c[:, 0] / 0.305)
    hw = (lt[:, 1] - rt[:, 1]) / 2
    o = np.argsort(x)
    px, phw = x[o], hw[o]
    T = np.array([LEFT.on_plane(np.array([u]), np.array([v]), "y", 0.0)[0] for u, v in FENDER_TOP_PX])
    E = []
    for u, v in FENDER_LOW_PX:                                  # on the near flank's own plane
        q = LEFT.on_plane(np.array([u]), np.array([v]), "y", 0.08)[0]
        for _ in range(3):
            q = LEFT.on_plane(np.array([u]), np.array([v]), "y", max(float(np.interp(q[0], px, phw)), 0.005))[0]
        E.append(q)
    E = np.array(E)
    return px, phw, T[np.argsort(T[:, 0])][:, [0, 2]], E[np.argsort(E[:, 0])][:, [0, 2]]


@functools.lru_cache(maxsize=None)
def _fender_top_edge():
    """The fender's top line zt(x) and the near flank's lower edge ze(x): the photo's, carried on at their slopes
    ahead of where the photo shows them (under the seat's tail, behind the muffler and the panels' tails)."""
    px, phw, T, E = _fender_lines()
    sl_t = (T[-1, 1] - T[-4, 1]) / (T[-1, 0] - T[-4, 0])
    sl_e = (E[-1, 1] - E[-5, 1]) / (E[-1, 0] - E[-5, 0])

    def top(x):
        return float(np.interp(x, T[:, 0], T[:, 1])) if x <= T[-1, 0] else T[-1, 1] + sl_t * (x - T[-1, 0])

    def edge(x):
        z = float(np.interp(x, E[:, 0], E[:, 1])) if x <= E[-1, 0] else E[-1, 1] + sl_e * (x - E[-1, 0])
        return max(z, 0.86)
    return top, edge


def _fender_half(x, w):
    """Half section (y >= 0, z) of the fender at x with half-width w, from the centre out: deck, eased facet, lip,
    flank."""
    top, edge = _fender_top_edge()
    zt, ze = top(x), edge(x)
    hgt = max(zt - ze, 0.004)
    fade = sat(w / 0.035)                                 # the creases die out into the point
    # toward the root the facet and the lip are shallower: LEFT, the crease line is 23 px under the top line at
    # u 3100 (x -0.09) but 15 px at u 2890 (x 0.06), and the panel's tail meets the lip 11 px under it at u 2846
    kr = smoothstep((x + 0.02) / 0.08)
    c1, c2 = FENDER_CROWN * fade, min(FENDER_FACET * fade * (1.0 - 0.4 * kr), 0.35 * hgt)
    r = max(min((1.0 - FENDER_A2) * w, 0.45 * (hgt - c1 - c2), 0.010 - 0.007 * kr), 0.0005)
    flank = max(hgt - c1 - c2 - r, 0.0)
    # the lip's outer face (the flank's top); at the root, under the side panels' tails, the flank is upright
    wl = w - flank * math.tan(FENDER_FLARE) * smoothstep(-x / 0.06)
    half = [(a * FENDER_A1 * (wl - r), zt - c1 * a * a) for a in np.linspace(0.0, 1.0, 8)]
    for s_ in np.linspace(0.0, 1.0, 6)[1:]:
        q = s_ * s_ * (3.0 - 2.0 * s_) * 0.6 + 0.4 * s_     # eased out of the crease
        half.append((FENDER_A1 * (wl - r) + s_ * (wl - r - FENDER_A1 * (wl - r)), zt - c1 - c2 * q))
    for th in np.linspace(0.0, math.pi / 2, 6)[1:]:       # the lip rolls over into the flank
        half.append((wl - r + r * math.sin(th), zt - c1 - c2 - r * (1.0 - math.cos(th))))
    for s_ in np.linspace(0.0, 1.0, 5)[1:]:
        half.append((wl + s_ * (w - wl), zt - c1 - c2 - r - s_ * flank))
    return np.array(half)


def fender_outer_y(x, z):
    """How far out the fender's outer surface is at x and height z (its table width, before it narrows between the
    side panels): what the panels' tails lap over."""
    px, phw = _fender_lines()[:2]
    h = _fender_half(x, max(float(np.interp(x, px, phw)), 0.0006))
    k = int(np.argmax(h[:, 0] >= h[:, 0].max() * 0.75))   # from the facet's end down the lip and flank
    q = h[k:]
    return float(np.interp(z, q[::-1, 1], q[::-1, 0])) if z <= q[0, 1] else float(q[0, 0])


def rear_fender():
    """Rear fender: plan from the top photo (FENDER_PLAN_PX: a straight taper and an arrow point), top line and the
    near flank's lower edge from the left photo (FENDER_TOP_PX, FENDER_LOW_PX). Section (_fender_half): a crowned
    deck, a facet from the crease, a lip rolling over into a flank that leans out a little to its lower edge.
    Root: the blade runs on under the seat's tail to the red wall under it (x 0.195: detail_plastics.tail_under,
    which is this moulding's front leg), between the side panels, the seat's tail resting on it (2 mm under the
    seat's underside: LEFT, the top line leaves the seat's tip 6 px under it, row 774 against 768); its lower edge
    carries on down at the photo's slope, hidden by the muffler and the side panels' tails, which lap over it.
    Rings run left to right, so Blender's 3 mm shell lies under the measured top."""
    px, phw, T, E = _fender_lines()
    x_tip, x_root = float(px[0]), 0.195
    xs = np.concatenate([np.linspace(x_tip, x_tip + 0.06, 31)[:-1], np.linspace(x_tip + 0.06, 0.055, 54)[:-1],
                         np.linspace(0.055, 0.105, 26)[:-1], np.linspace(0.105, x_root, 18)])   # 2 mm round the seat's tail
    # ahead of the side panels' rear edges (x 0.112) it runs on between their top edges (which tuck in under the
    # seat's hem over a bead: 70 to 80 mm out), 0.5 mm inside them, to the wall under the tail
    Vp = np.asarray(side_panels().V)
    Vp = Vp[(Vp[:, 0] > 0.080) & (Vp[:, 2] > 0.88)]
    pin_x = np.arange(0.084, 0.200, 0.004)
    pin = np.array([np.abs(Vp[np.abs(Vp[:, 0] - q) < 0.006, 1]).min() if (np.abs(Vp[:, 0] - q) < 0.006).any() else 0.2
                    for q in pin_x]) - 0.0005

    def hw(x):
        w = float(np.interp(x, px, phw))
        return w + (min(w, float(np.interp(x, pin_x, pin))) - w) * smoothstep((x - 0.084) / 0.010)
    rings = []
    for x in xs:
        half = _fender_half(x, max(hw(x), 0.0006))
        ring = np.vstack([half[::-1] * [1, 1], half[1:] * [-1, 1]])     # left (y > 0) to right
        ring = np.column_stack([np.full(len(ring), x), ring[:, 0], ring[:, 1]])
        if x > 0.05:                                      # the seat's tail rests on it: 2 mm under the seat
            zu = seat_under_z(ring[:, :2])
            # (2 mm: 0.5 mm under the seat's underside at the vertices, the blade's coarser faces cut through the
            # hem's rounded edge between them)
            ring[:, 2] = np.where(np.isfinite(zu), np.minimum(ring[:, 2], zu - 0.002), ring[:, 2])
        rings.append(ring)
    return grid(Mesh(), rings, "plastic_red", closed_u=False)


@functools.lru_cache(maxsize=None)
def _seat_under():
    """The seat's underside (base, tuck and hem) as a linear interpolator over plan points."""
    from scipy.interpolate import LinearNDInterpolator
    m = seat()
    V = np.asarray(m.V)
    idx = set()
    for f, mat in zip(m.F, m.M):
        P = V[list(f)]
        if mat != "seat" or np.cross(P[1] - P[0], P[2] - P[0])[2] < 0:
            idx.update(f)
    U = V[sorted(idx)]
    U = U[U[:, 2] < np.array([seat_top_z(x) for x in U[:, 0]]) - 0.004]      # not the cover's top
    return LinearNDInterpolator(U[:, :2], U[:, 2])


def seat_under_z(P2):
    """Height of the seat's underside over plan points P2 (n, 2); nan outside the seat."""
    return _seat_under()(np.asarray(P2, float))


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
    # Rings run left to right, so Blender's 3 mm shell lies UNDER this surface: the measured top line is the fender's
    # top, and the bosses of the lower clamp's fender nose (detail_front), which stop 0.3 mm under the inner skin,
    # meet it. (Right to left, the shell lay above the surface: measured from every vertex the fender was 3.8 mm
    # from the bosses.)
    U = np.concatenate([-A[::-1], A[1:]])[::-1]
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
    for z in (0.735, 0.715, 0.700, 0.688):                  # up to where the mudguard is at its full width
        # 0.3 mm in front of the mudguard's front face (its plate is 3 mm thick about its mid-surface)
        rings.append(np.array([(MUD_X + 0.15 * (z - z0) - 0.010 * (1.0 - min(abs(u) * 0.060 / 0.084, 1.0) ** 2) + 0.0018
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
