"""The CRF250R's plastics as measured 3D surfaces (stock Honda, 2025/2026 bodywork).

Every surface is tied to Honda's studio photos through the calibrated cameras (cams.py):
  side outline   the exact outline in the left or right profile photo (outlines.py); every vertex of a panel lies on
                 the ray through its photo pixel, so the model's side view IS the photo's outline
  plan widths    the red envelope of the top photo, column by column (measure.py)
  sections       the outer silhouette of the front photo (shroud fins) and of the rear photo (side panels)
  number plate   its outline in the front photo, cast onto the plate's inclined, wrapped surface
Cross-check 2026-11-10: shroud half-width 0.199 m from the top photo, 0.201 m from the front photo.

Tags as in parts.py: OUT/OUT2 outlines, TOP/FRONT/REAR photo measurements, EST estimated.
"""
import json
import math
import os

import numpy as np

import cams
from geom import Mesh, grid, inside, plate2d, rounded_rect, smooth_poly

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
def _outline_px(view, pts_mm, smooth=3):
    u, v = cams.linear_to_px(view, np.asarray(pts_mm, float)[:, 0], np.asarray(pts_mm, float)[:, 1])
    return smooth_poly(np.stack([u, v], axis=1), smooth)


def _on_surface(cam, u, v, surf, y0):
    """3D point where the ray through pixel (u, v) meets the surface y = surf(x, z) (fixed-point iteration)."""
    y = y0
    for _ in range(6):
        P = cam.on_plane(u, v, "y", y)[0]
        y = surf(P[0], P[2])
    return cam.on_plane(u, v, "y", y)[0]


def photo_panel(view, outline_mm, surf, thickness, mat, holes_mm=(), step=11.0):
    """Shell whose side view is exactly OUTLINE in the VIEW photo: meshed in the photo's pixel space, every vertex
    put on the surface y = surf(x, z) along its pixel's ray, THICKNESS toward the bike's centre. Holes (vents) are
    cut through. step: mesh size in pixels (about 0.78 mm each)."""
    cam = cams.CAMS[view]
    sgn = 1.0 if view == "left" else -1.0
    outer = _outline_px(view, outline_mm)
    holes = [_outline_px(view, h, 1) for h in holes_mm]
    y0 = sgn * 0.15

    def to3d(u, v, w):                 # plate2d offsets w in [-t/2, t/2]: the outer face (w = t/2) is the surface
        P = _on_surface(cam, u, v, surf, y0)
        return (P[0], P[1] - sgn * (thickness / 2 - w), P[2])
    return plate2d(outer, holes, thickness, mat, to3d, step=step)


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


def _front_edge_table(ref):
    """Smoothed front edge x(z) of an outline (x, z)."""
    zs = np.arange(ref[:, 1].min() + 0.004, ref[:, 1].max() - 0.004, 0.004)
    xs = []
    for z in zs:
        c = [a_[0] + (b_[0] - a_[0]) * (z - a_[1]) / (b_[1] - a_[1]) for a_, b_ in zip(ref, np.roll(ref, -1, axis=0))
             if (a_[1] - z) * (b_[1] - z) <= 0 and a_[1] != b_[1]]
        xs.append(max(c) if c else np.nan)
    xs = np.array(xs)
    ok = np.isfinite(xs)
    zs, xs = zs[ok], _smooth(xs[ok], 5)
    return lambda z: float(np.interp(z, zs, xs))


LIP = 0.012          # FRONT: the leading edge shows as a red rim outside the radiator, 10 mm wide at mid height
WALL_STEP = 0.008    # the inner wall ahead of the skin's edge sits this far in (FRONT: the rim it and the skin's edge
#                      make is 10 to 18 mm wide; the step itself is not measurable: EST)
SHOULDER_H, SHOULDER_IN = 0.038, 0.028      # FRONT: silhouette 0.198 at z 0.899, 0.188 at 0.917, 0.175 at 0.933,
#                                             on the section whose top edge is at 0.937: a rounded shoulder


def _shroud_surface(side, parts=False):
    """y(x, z) of a shroud's outer surface.
    Side face: upright, at the plan envelope of the top photo (TOP). Checked against the front photo through the
    refitted camera: its outer silhouette is 0.200 m off the centre line at z 0.83..0.88 (top photo: 0.199 to 0.202),
    0.193 at z 0.74 and 0.185 at 0.68, which is the plan envelope at the x where the leading edge is at those heights.
    Leading edge: two layers (LEFT and RIGHT photos, zoomed): the outer skin stops 35 to 80 mm short of the front
    edge between z 0.68 and 0.88; ahead of it a recessed inner wall, in shadow in the photos, runs on to the true
    front edge, which is rolled in by LIP (FRONT: red rim outside the black louvres).
    Shoulder: the top 38 mm turns in by 28 mm (FRONT silhouette). Inboard of it the top deck is built separately
    (shroud_decks): it is edge-on in the profile photos."""
    name = "shroud" if side > 0 else "shroud_R"
    view = "left" if side > 0 else "right"
    ref = _true_outline(view, OUT[name], side * 0.19)
    top_edge = _top_edge_table(ref)
    front_edge = _front_edge_table(ref)
    plan = _shroud_plan(side)
    z_lo, z_hi = ref[:, 1].min() + 0.006, ref[:, 1].max() - 0.006

    # edge of the outer skin (outlines.py 'shroud_skin'): ahead of it the surface is the recessed inner wall
    sk = _true_outline(view, OUT["shroud_skin" + ("" if side > 0 else "_R")], side * 0.19)
    sk = sk[np.argsort(sk[:, 1])]
    from scipy.signal import medfilt
    sk_z, sk_x = sk[:, 1], _smooth(medfilt(sk[:, 0], 5), 5)

    def surf(x, z):
        W = plan(x)
        if sk_z[0] <= z <= sk_z[-1] + 0.012:
            W -= WALL_STEP * smoothstep((x - float(np.interp(z, sk_z, sk_x))) / 0.005)
        d = front_edge(min(max(z, z_lo), z_hi)) - x                   # distance behind the leading edge
        if d < LIP:
            W -= LIP * (1.0 - max(d, 0.0) / LIP) ** 2
        sh = (z - (top_edge(x) - SHOULDER_H)) / SHOULDER_H
        if sh > 0:                                                    # none behind x 0.72: the shroud lies on the
            W -= SHOULDER_IN * min(sh, 1.0) ** 2 * smoothstep((x - 0.72) / 0.15)      # frame spar there
        return side * W
    if parts:
        return surf, plan, top_edge, ref
    return surf


# inner edge of the shrouds' top decks (TOP: gap between the two shrouds around the tank and the steering head)
DECK_X = [0.790, 0.854, 0.929, 0.960, 1.060]
DECK_Y = [0.053, 0.055, 0.060, 0.075, 0.092]


def shroud_decks():
    """Top decks of the shrouds: from the rounded shoulder in to the edge at the tank (TOP: red from the plan
    envelope in to the gap around the tank, +-0.053 to 0.060 m beside the filler cap, opening to 0.092 at the
    steering head). Level with the shoulder's top edge, 3 mm lower at the inner edge (edge-on in the profile photos,
    so its height comes from the shroud outline's top edge; cross slope EST)."""
    m = Mesh()
    for side in (1, -1):
        surf, plan, top_edge, ref = _shroud_surface(side, parts=True)
        x1 = min(1.062, float(ref[:, 0].max()) - 0.075)
        rings = []
        for x in np.linspace(0.792, x1, 30):
            zt = top_edge(x)
            y_out = plan(x) - SHOULDER_IN + 0.002
            y_in = min(float(np.interp(x, DECK_X, DECK_Y)), y_out - 0.004)
            rings.append(np.array([(x, side * (y_out + (y_in - y_out) * k), zt - 0.001 - 0.003 * k)
                                   for k in np.linspace(0, 1, 7)]))
        m.add(grid(Mesh(), rings, "plastic_red", closed_u=False))
    return m


def _vent_holes(view, name, min_area=120):
    """Dark openings inside a plastic's outline in the profile photo (shroud vents, side panel air intake)."""
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
    for side, view, name in ((1, "left", "shroud"), (-1, "right", "shroud_R")):
        # no openings are cut: the dark shapes inside the shroud's outline in the photo are the stock decal's navy
        # letters, not vents (cutting them left slits in the render)
        m.add(photo_panel(view, OUT[name], _shroud_surface(side), 0.003, "plastic_red", step=6.0))
    return m


# ---------------------------------------------------------------- side panels
def _panel_surface(side):
    """y(x, z) of a side panel: tucked under the seat's edge at the top, out to the plan envelope of the top photo
    (TOP: left 0.159, right 0.175 where it bulges over the muffler) within 40 mm (EST); the right panel reaches its
    envelope lower down. The rear photo cannot confirm the section: the shrouds, further forward, form its outer
    silhouette at these heights."""
    name = "side_panel" if side > 0 else "side_panel_R"
    view = "left" if side > 0 else "right"
    ref = _true_outline(view, OUT[name], side * 0.14)

    top_edge = _top_edge_table(ref)

    def surf(x, z):
        W = plan_half_width(min(max(x, -0.19), 0.80), side)
        zt = top_edge(x)
        y_top = max(seat_hw(min(max(x, 0.08), 0.80)) + 0.006, 0.050) if x > 0.06 else W * 0.92
        y_top = min(y_top, W)
        t = smoothstep((zt - z) / 0.040)
        if side < 0:
            t *= 0.90 + 0.10 * smoothstep((0.935 - z) / 0.065)
        return side * (y_top + (W - y_top) * t)
    return surf


def side_panels():
    m = Mesh()
    for side, view, name, low in ((1, "left", "side_panel", "lower_panel"), (-1, "right", "side_panel_R", "lower_panel_R")):
        surf = _panel_surface(side)
        holes = _vent_holes(view, name, min_area=200)
        m.add(photo_panel(view, OUT[name], surf, 0.003, "plastic_red", holes_mm=holes))
        for h in holes:                                   # air intake: dark mesh behind the opening
            m.add(photo_panel(view, h, lambda x, z, s=surf, q=side: s(x, z) - q * 0.010, 0.002, "louvre", step=9.0))
        # black textured lower panel (airbox side, mud flap): its own exact outline, on the same surface set in 6 mm
        m.add(photo_panel(view, OUT2[low], lambda x, z, s=surf, q=side: s(x, max(z, 0.76)) - q * 0.006, 0.003,
                          "black_texture"))
    return m


# ---------------------------------------------------------------- lofted parts: seat, fenders
def _line(view, name, y):
    P = _true_outline(view, OUT[name], y)
    o = np.argsort(P[:, 0])
    return P[o]


def seat():
    """Seat: top line from the left photo (its upper silhouette, seen from a camera above it, is the far edge: the
    line is cast onto y = -0.6 x half-width), plan half-width from the top photo (TOP, seat cover mask), flat top with
    25 mm rounded edges, 70 mm deep sides (EST)."""
    xs = np.linspace(0.082, 0.798, 60)
    rings = []
    for x in xs:
        hw = seat_hw(x)
        top_line = _line("left", "seat_top", -0.6 * hw)
        zt = float(np.interp(x, top_line[:, 0], _smooth(top_line[:, 1], 5)))
        depth = 0.070 * sat((0.80 - x) / 0.06 + 0.25) * sat((x - 0.06) / 0.05 + 0.3)
        loop = rounded_rect(2 * hw, max(depth, 0.012), min(0.025, hw * 0.8, depth * 0.45), 6)
        rings.append(np.array([(x, p[0], zt - depth / 2 + p[1]) for p in loop]))
    return grid(Mesh(), rings, "seat", cap0=True, cap1=True)


def _blade(xs, hw_fn, top_fn, edge_fn, crown_fn, mat, plateau=None, n=25):
    """Fender blade lofted along x: centre top line, plan half-width, edge height; each section is crowned across and
    turns down into the edge. plateau(x) -> (half-width, height) of a raised flat centre with a crease, or None."""
    rings = []
    for x in xs:
        hw, zt, ze = hw_fn(x), top_fn(x), edge_fn(x)
        crown = crown_fn(x)
        ring = []
        for u in np.linspace(-1, 1, n):
            y = u * hw
            a = abs(u)
            z = zt - crown * a ** 2.2 - max(zt - crown - ze, 0.0) * smoothstep((a - 0.72) / 0.28)
            if plateau is not None:
                pw, ph = plateau(x)
                if pw > 0:
                    z += ph * (1.0 - smoothstep((abs(y) - pw) / 0.006))
            ring.append((x, y, z))
        rings.append(np.array(ring))
    return grid(Mesh(), rings, mat, closed_u=False)


def rear_fender():
    """Rear fender: centre top line from the left photo, plan half-width from the top photo (TOP), edges down to the
    lower outline of the left photo. (The red seen under it from behind is not the blade: see fender_mounts. Skirts
    on the blade were tried and showed behind the side panel in the profile, where the photo has none.)"""
    top_line = _line("left", "fender_top", 0.0)
    low = _true_outline("left", OUT["rear_fender"], 0.07)
    xs = np.linspace(-0.3005, 0.100, 44)
    hw = lambda x: max(min(plan_half_width(x, 1), 0.098) * sat((x + 0.303) / 0.012 + 0.08), 0.004)
    top = lambda x: float(np.interp(x, top_line[:, 0], _smooth(top_line[:, 1], 5)))

    def edge(x):
        zb = _poly_bottom(low, min(max(x, low[:, 0].min() + 0.004), low[:, 0].max() - 0.004))
        # no cap on the depth: at its root the fender's side is 100 mm deep in the photo (a 75 mm cap left a hole
        # there, with the subframe showing through)
        return top(x) - 0.006 if not np.isfinite(zb) else min(zb, top(x) - 0.006)
    return _blade(xs, hw, top, edge, lambda x: 0.010, "plastic_red")


# front fender plan half-width between the fork legs. FRONT (refitted camera, rows 700..740, right edge of the red:
# the left edge carries the fork tube's red reflection): 0.064 to 0.072 m; the top photo's envelope there is the
# fork guards. From x 1.457 forward the top photo's envelope is the fender itself.
FF_X = [1.215, 1.300, 1.420, 1.457]
FF_HW = [0.062, 0.064, 0.075, 0.080]


def _fender_plan():
    m = TT["x"] > 1.44
    x, w = TT["x"][m], _smooth(0.5 * (TT["left"][m] + TT["right"][m]), 3)
    return lambda q: float(np.interp(q, x, w)) if q > 1.457 else float(np.interp(q, FF_X, FF_HW))


def front_fender():
    """Front fender. Centre top line and lowest line from the left photo, plan half-width from the top photo.
    Section: arched. The widest point (x 1.51, +-0.100 m) shows in the front photo at row 759, which is z 0.858: the
    height of the LOWEST line in the left photo there (0.856), 62 mm under the centre line. So the edges are the low
    line and the centre is the high line all along (FRONT + LEFT + TOP agree to 5 mm). Across: a flat centre that
    carries a raised shield-shaped plateau ending in a point behind the nose (FRONT, TOP; 5 mm high EST), then
    sides sloping down to the edges (profile EST)."""
    top_line = _line("left", "front_fender_top", 0.0)
    bot_line = _line("left", "front_fender_bottom", 0.09)
    # stations every 5 mm, every 1.5 mm over the last 30 mm: the nose narrows fast and showed facets
    xs = np.concatenate([np.linspace(1.218, 1.677, 92), np.linspace(1.6785, 1.7075, 20)])
    hw = _fender_plan()
    top = lambda x: float(np.interp(x, top_line[:, 0], _smooth(top_line[:, 1], 5)))
    edge = lambda x: min(float(np.interp(x, bot_line[:, 0], _smooth(bot_line[:, 1], 5))), top(x) - 0.004)

    def plateau(x):
        if x < 1.30 or x > 1.655:
            return 0.0, 0.0
        return 0.052 * sat((1.655 - x) / 0.13) ** 0.8 * sat((x - 1.30) / 0.05 + 0.4), 0.005
    rings = []
    for x in xs:
        w, zt, ze = hw(x), top(x), edge(x)
        pw, ph = plateau(x)
        ring = []
        for u in np.linspace(-1, 1, 65):
            a_ = abs(u)
            drop = 0.18 * a_ ** 2 + 0.82 * smoothstep((a_ - 0.40) / 0.60)
            z = zt - (zt - ze) * drop
            if pw > 0:
                z += ph * (1.0 - smoothstep((a_ * w - pw) / 0.012)) - ph
            ring.append((x, u * w, z))
        rings.append(np.array(ring))
    return grid(Mesh(), rings, "plastic_red", closed_u=False)


def fender_flap(on_tube, back, t_at_z):
    """The fender's rear flap: the red panel that hangs between the fork legs behind the tyre's top (FRONT: the red
    column under the fender nose, rows 905..1030, with the tyre's knobs in front of it). Half-width 67 mm at z 0.74
    to 58 mm at its lower corners (z 0.667), rounded lower edge down to z 0.650 on the centre line (FRONT). It lies
    on the fork's plane: the left photo shows no red behind the fork leg, only slivers at the tube's edges, so it is
    hidden by the leg. Distance ahead of the tube axis (28 mm) and its top end (z 0.90, under the lower clamp): EST."""
    t0, t1 = t_at_z(0.667), t_at_z(0.900)
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
def number_plate():
    """Front number plate: its outline in the front photo (FRONT) cast onto its surface: a face parallel to the fork
    through the plate's front edge in the left photo (OUT 'number_plate', centre plane), wrapped back 45 mm at
    +-0.12 m (left photo row z 1.00: the plate is 50 mm deep in side view)."""
    side = _true_outline("left", OUT["number_plate"], 0.0)
    zs = np.linspace(1.00, 1.20, 9)
    P = np.asarray(side)
    front = []
    for z in zs:                                            # front edge (largest x) of the side outline per height
        xs_ = []
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            if (a[1] - z) * (b[1] - z) <= 0 and a[1] != b[1]:
                xs_.append(a[0] + (b[0] - a[0]) * (z - a[1]) / (b[1] - a[1]))
        front.append((max(xs_), z))
    front = np.array(front)
    k = np.polyfit(front[:, 1], front[:, 0], 1)             # x = k0 z + k1 on the centre plane
    d = np.array([k[0], 0.0, 1.0]); d /= np.linalg.norm(d)   # up the plate
    back = np.array([-d[2], 0.0, d[0]])                      # perpendicular, pointing back
    p0 = np.array([np.polyval(k, 1.0), 0.0, 1.0])

    def depth(y):
        return 0.045 * sat(abs(y) / 0.12) ** 2.2

    def hit(u, v, extra=0.0):
        t = 0.0
        for _ in range(6):
            o = p0 + back * (t + extra)                      # plane through o with normal 'back'
            r = FRONT.ray(np.array([u]), np.array([v]))[0]
            s = ((o - FRONT.C) @ back) / (r @ back)
            Pw = FRONT.C + s * r
            t = depth(Pw[1])
        return Pw
    # the brake hose crosses the plate's right half in the photo: the left half is mirrored about the centre column
    raw = np.array(MEAS["front_plate_px"])
    uc = 1999.5
    half = raw[raw[:, 0] <= uc]
    # around the plate one way, top to left to bottom: the angle is measured from straight up so it runs 0..pi over
    # the left half without a jump (measured from the +u axis it jumped at the plate's mid height and folded the
    # outline along the centre line: slits showed in the front view)
    half = half[np.argsort(np.arctan2(uc - half[:, 0], 450.0 - half[:, 1]))]
    mirror = np.stack([2 * uc - half[::-1, 0], half[::-1, 1]], axis=1)
    outer = smooth_poly(np.vstack([half, mirror]), 6)      # the mask's edge is ragged where the plate meets the fender
    return plate2d(outer, [], 0.003, "plastic_red", lambda u, v, w: tuple(hit(u, v, 0.0015 - w)), step=10.0)


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
    hides it in the rear photo: width (120 mm at the top to 110 mm) EST."""
    zt = np.array([0.675, 0.643, 0.611, 0.580, 0.549, 0.518, 0.486])
    xr = np.array([0.336, 0.339, 0.342, 0.339, 0.333, 0.326, 0.318])
    rings = []
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
