"""Damien's boots: Leatt Moto 6.5, White (US 10), both feet, built by script on his body.

python3 boots.py BODY.npz OUT.npz        (BODY.npz from body.py; writes the gear npz that build_rider.py loads)

Sources (every number is also in research/rider-ledger/boots.md):
  Product: research/rider-gear-leatt.md section 6; Leatt's twelve studio views in reference/leatt-gear/boots/
    (02 outer side and 03 inner side are the RIGHT boot; 05 back pair; 06 soles, the right boot on the image's left).
  Size: his foot on body.npz (heel to longest toe, 277 mm) against Leatt's boot chart
    (reference/leatt-gear/sizing/leatt-size-chart_boots.jpg: US 9 = 27.5 cm, US 10 = 29.0 cm): US 10.
  Sole length: chart foot 290 mm + 19 mm toe room (Gaerne's fit rule, foot at least 3/4 in shorter than the insole)
    + heel wall 8 mm + toe wall, cap and welt 13 mm = 330 mm, toe cap tip to heel. Every other dimension is Leatt's
    photo 02 scaled by that length (1154 px: 0.286 mm/px); the other views are scaled to the same boot height.
Frames: the boot is built in its own frame (u to the toe, v up from the sole's ground line, w to the outer side,
metres) as the RIGHT boot, then put on his right foot in body.py's MB frame (x left, -y forward, z up) and mirrored
(x -> -x) onto the left foot with every logo set back to read.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bike"))
import geom as G  # noqa: E402  (the bike's mesh toolkit)

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, "..", ".."))
REF = os.path.join(PROJ, "reference", "leatt-gear", "boots")
TEXDIR = os.path.join(PROJ, "textures", "rider")


def ref(k):
    names = {"01": "pair-front-34", "02": "outer-side-buckles", "03": "inner-side-calf-panel", "04": "front",
             "05": "back-pair", "06": "soles", "07": "detail-toe-box-6.5-toe-cap",
             "08": "detail-top-slidelock-badge-shin-plate", "09": "detail-buckles-ankle-logo",
             "10": "detail-heel-ankle-logo-welt", "11": "detail-rear-spine-buckles", "12": "detail-top-gaiter-liner"}
    return os.path.join(REF, f"boot65_white_{k}-{names[k]}_leatt-us_3025400140_1920.jpg")


# ---------------------------------------------------------------- size (Leatt chart, his foot)
CHART_CM = {7: 25.5, 8: 26.5, 9: 27.5, 10: 29.0, 11: 29.5, 12: 30.5, 13: 31.5}   # Leatt boot chart, foot length
TOE_ROOM = 0.019             # Gaerne fit rule: the foot sits at least 3/4 in shorter than the insole
HEEL_WALL = 0.008            # heel counter 3 mm TPU + 5 mm padding and liner (EST, behind his heel)
TOE_WALL = 0.013             # toe box wall and liner 6 mm + toe cap 3 mm + welt lip 4 mm (EST, photo 07)

# ---------------------------------------------------------------- photo calibrations (pixels, read on grid crops)
# side views: heel = back of the sole at the welt, toe = tip of the toe cap, ground = bottom of the heel block,
# top = top of the gaiter; d = +1 when the toe points to the image's right.
P02 = dict(heel_x=443.0, toe_x=1597.0, ground_y=1702.0, top_y=217.0, d=1)     # outer side, right boot
P03 = dict(heel_x=1467.0, toe_x=312.0, ground_y=1704.0, top_y=216.0, d=-1)    # inner side, right boot


def foot_length(body):
    """Heel to longest toe of his right foot along -y (body.py MB frame), and the heel's y."""
    V = body["V"]
    f = V[(V[:, 0] < -0.1) & (V[:, 2] < 0.12)]
    return f[:, 1].max() - f[:, 1].min(), f[:, 1].max()


def choose_size(L):
    for us, cm in sorted(CHART_CM.items()):
        if L * 100 <= cm + 1e-9:
            return us
    return max(CHART_CM)


def sole_length(us):
    return CHART_CM[us] / 100 + TOE_ROOM + HEEL_WALL + TOE_WALL


# ---------------------------------------------------------------- silhouettes from Leatt's photos
def photo_mask(path, tcol=7.0, tgrad=1.5):
    """Boot pixels: everything not connected to the border through flat background grey (236) pixels."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    g = ndi.gaussian_filter(a.mean(2), 1.2)
    G = np.hypot(ndi.sobel(g, 0), ndi.sobel(g, 1)) / 8
    cand = (np.abs(a - 236.0).max(2) <= tcol) & (G < tgrad)
    lab, n = ndi.label(cand)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = ndi.binary_dilation(np.isin(lab, border[border > 0]), iterations=1)
    m = ndi.binary_opening(~bg, iterations=2)
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[1:] = sizes > 0.05 * sizes.max()
    return a, ndi.binary_fill_holes(keep[lab])


class Side:
    """A side photo calibrated to the boot frame: (u, v) metres <-> pixels."""

    def __init__(self, P, L):
        self.P = P
        self.s = L / abs(P["toe_x"] - P["heel_x"])          # metres per pixel

    def px(self, u, v):
        return self.P["heel_x"] + self.P["d"] * np.asarray(u) / self.s, self.P["ground_y"] - np.asarray(v) / self.s

    def uv(self, x, y):
        return self.P["d"] * (np.asarray(x) - self.P["heel_x"]) * self.s, (self.P["ground_y"] - np.asarray(y)) * self.s


GRID = 0.001                              # side-silhouette raster, 1 mm
U0, U1, V0, V1 = -0.02, 0.36, -0.005, 0.45


HEEL_BAND = (0.055, 0.170)               # v range where photo 02's heel cup is blown out to the background grey


def side_mask(L):
    """The boot's side outline as a 1 mm raster M[v, u] (v from 0 up, u from U0), from photo 02. Its white heel cup
    is clipped to the background's exact grey (236, 236, 236) between v 55 and 170 mm: there each row is filled back
    to photo 03's back edge (mirrored, same calibration). Cleaned by a 3 mm closing and a 2 mm opening."""
    us = np.arange(U0, U1, GRID)
    vs = np.arange(0.0, (P02["ground_y"] - P02["top_y"]) * Side(P02, L).s, GRID)
    UU, VV = np.meshgrid(us, vs)
    hits = []
    for k, P in (("02", P02), ("03", P03)):
        _, m = photo_mask(ref(k))
        x, y = Side(P, L).px(UU, VV)
        xi, yi = np.clip(np.round(x).astype(int), 0, m.shape[1] - 1), np.clip(np.round(y).astype(int), 0,
                                                                                m.shape[0] - 1)
        hits.append(m[yi, xi])
    M = hits[0].copy()
    for i in np.nonzero((vs >= HEEL_BAND[0]) & (vs <= HEEL_BAND[1]))[0]:
        r2, r3 = np.nonzero(hits[0][i])[0], np.nonzero(hits[1][i])[0]
        if len(r2) and len(r3) and r3[0] < r2[0]:
            M[i, r3[0]:r2[0]] = True
    M = ndi.binary_closing(M, structure=disk(3))
    M = ndi.binary_opening(M, structure=disk(2))
    M = ndi.binary_fill_holes(M)
    lab, n = ndi.label(M)
    M = lab == (np.argmax(ndi.sum(M, lab, range(1, n + 1))) + 1)
    return us, vs, M


def robust_spline(x, y, knot_step, out_sign, iters=6, tol=0.0015):
    """Least-squares cubic B-spline through (x, y) with interior knots every knot_step, refitted with the points
    that stand OUT of the fit (out_sign * residual > tol: buckles, strap ends, plates on the photo's outline)
    weighted down, so the curve follows the shell's own line."""
    from scipy.interpolate import make_lsq_spline
    ok = np.isfinite(y)
    x, y = x[ok], y[ok]
    t_in = np.arange(x[0] + knot_step, x[-1] - knot_step / 2, knot_step)
    t = np.concatenate([[x[0]] * 4, t_in, [x[-1]] * 4])
    w = np.ones_like(y)
    for _ in range(iters):
        s = make_lsq_spline(x, y, t, k=3, w=w)
        r = out_sign * (y - s(x))
        w = np.where(r > tol, np.exp(-((r - tol) / 0.002) ** 2), 1.0)
    return s


def base_outline(us, vs, M, L):
    """The shell's own side outline: the photo outline's back line, the shaft's front line and the foot's top line
    each a robust smooth spline (knots every 40, 40 and 25 mm), so buckles, strap ends, the spine and plates (built
    as parts) are not in the shell. The heel and toe ends are the photo's. Returns a raster like M."""
    ub, uf = row_edges(us, M)
    s_b = robust_spline(vs, ub, 0.04, -1)
    v_j = 0.13
    sel = vs >= v_j
    s_f = robust_spline(vs[sel], uf[sel], 0.04, +1)
    first = np.cumprod(M[10:], axis=0).astype(bool)                # each column's first run up from v = 10 mm
    vt = np.where(first.any(0), vs[10 + first.sum(0) - 1], np.nan)
    u_j = float(s_f(v_j))
    selu = (us >= u_j - 0.02) & np.isfinite(vt) & (us <= L - 0.01)
    s_t = robust_spline(us[selu], vt[selu], 0.025, +1)
    B = np.zeros_like(M)
    ubs = s_b(vs)
    for i, v in enumerate(vs):
        if v >= v_j:
            front = s_f(v)
        else:
            uu = us[(us >= u_j) & (us <= L - 0.01)]
            above = uu[s_t(uu) >= v]
            front = above.max() if len(above) else u_j
            front = max(front, uf[i] if v < 0.04 else front)        # the toe's end: the photo's
        B[i] = (us >= ubs[i]) & (us <= front)
    B &= M | ndi.binary_dilation(M, structure=disk(6))
    return B


def row_edges(us, M):
    """Back and front edge of each row of a side raster (nan where empty)."""
    any_ = M.any(1)
    ub = np.where(any_, us[np.argmax(M, 1)], np.nan)
    uf = np.where(any_, us[M.shape[1] - 1 - np.argmax(M[:, ::-1], 1)], np.nan)
    return ub, uf


def surface_nets(f, origin, h, iters=6):
    """Quad mesh of the zero level of the sampled field f[i, j, k] (inside < 0), one vertex per crossing cell at the
    mean of its edge crossings, then moved onto the level by Newton steps on the trilinear field. Faces point out."""
    s = f < 0
    nx, ny, nz = f.shape
    cid = -np.ones((nx - 1, ny - 1, nz - 1), int)
    acc = np.zeros((nx - 1, ny - 1, nz - 1, 3))
    cnt = np.zeros((nx - 1, ny - 1, nz - 1))
    # edge crossings along each axis, accumulated into the four cells sharing the edge
    for ax in range(3):
        sl0 = [slice(None)] * 3
        sl1 = [slice(None)] * 3
        sl0[ax] = slice(0, -1)
        sl1[ax] = slice(1, None)
        f0, f1 = f[tuple(sl0)], f[tuple(sl1)]
        e = (f0 < 0) != (f1 < 0)
        idx = np.argwhere(e)
        t = f0[e] / (f0[e] - f1[e])
        p = idx.astype(float)
        p[:, ax] += t
        others = [a for a in range(3) if a != ax]
        for da in (0, -1):
            for db in (0, -1):
                c = idx.copy()
                c[:, others[0]] += da
                c[:, others[1]] += db
                ok = (c >= 0).all(1) & (c[:, 0] < nx - 1) & (c[:, 1] < ny - 1) & (c[:, 2] < nz - 1)
                np.add.at(acc, (c[ok, 0], c[ok, 1], c[ok, 2]), p[ok])
                np.add.at(cnt, (c[ok, 0], c[ok, 1], c[ok, 2]), 1)
    act = cnt > 0
    cid[act] = np.arange(act.sum())
    P = acc[act] / cnt[act][:, None]
    quads = []
    for ax in range(3):
        sl0 = [slice(None)] * 3
        sl1 = [slice(None)] * 3
        sl0[ax] = slice(0, -1)
        sl1[ax] = slice(1, None)
        e = s[tuple(sl0)] != s[tuple(sl1)]
        idx = np.argwhere(e)
        inside_first = s[tuple(sl0)][e]
        o = [a for a in range(3) if a != ax]
        keep = (idx[:, o[0]] >= 1) & (idx[:, o[1]] >= 1) & (idx[:, o[0]] < f.shape[o[0]] - 1) & \
            (idx[:, o[1]] < f.shape[o[1]] - 1) & (idx[:, ax] < f.shape[ax] - 1)
        idx, inside_first = idx[keep], inside_first[keep]
        corners = []
        for da, db in ((-1, -1), (0, -1), (0, 0), (-1, 0)):
            c = idx.copy()
            c[:, o[0]] += da
            c[:, o[1]] += db
            corners.append(cid[c[:, 0], c[:, 1], c[:, 2]])
        q = np.stack(corners, 1)
        # orientation: normal along +ax when the inside is first (lower index)
        flip = inside_first if ax != 1 else ~inside_first
        q[flip] = q[flip][:, ::-1]
        quads.append(q)
    Q = np.concatenate(quads)
    # Newton steps onto the zero level
    for _ in range(iters):
        val, g = trilinear(f, P)
        gn = (g * g).sum(1) + 1e-12
        step = (val / gn)[:, None] * g
        step = np.clip(step, -0.5, 0.5)
        P = P - step
    return origin + P * h, Q


def trilinear(f, P):
    """Value and gradient (per voxel) of f at fractional voxel coordinates P (n, 3)."""
    i = np.clip(np.floor(P).astype(int), 0, np.array(f.shape) - 2)
    t = P - i
    c = lambda a, b, d: f[i[:, 0] + a, i[:, 1] + b, i[:, 2] + d]
    c000, c100, c010, c110 = c(0, 0, 0), c(1, 0, 0), c(0, 1, 0), c(1, 1, 0)
    c001, c101, c011, c111 = c(0, 0, 1), c(1, 0, 1), c(0, 1, 1), c(1, 1, 1)
    x, y, z = t[:, 0], t[:, 1], t[:, 2]
    c00 = c000 * (1 - x) + c100 * x
    c10 = c010 * (1 - x) + c110 * x
    c01 = c001 * (1 - x) + c101 * x
    c11 = c011 * (1 - x) + c111 * x
    c0 = c00 * (1 - y) + c10 * y
    c1 = c01 * (1 - y) + c11 * y
    val = c0 * (1 - z) + c1 * z
    gx = ((c100 - c000) * (1 - y) + (c110 - c010) * y) * (1 - z) + ((c101 - c001) * (1 - y) + (c111 - c011) * y) * z
    gy = (c10 - c00) * (1 - z) + (c11 - c01) * z
    gz = c1 - c0
    return val, np.stack([gx, gy, gz], 1)


# ---------------------------------------------------------------- the boot on his foot
V_FOOT = 0.027          # footbed under his heel, 27 mm above the ground line: welt top at the heel 23 mm in photo
                        # 02 (y 1622) + insole 4 mm (EST)
V_BALL = 0.020          # footbed under the ball of his foot (u = 217 mm): welt top 18 mm (02, y 1640) + 2 mm.
                        # The boot's 7 mm heel drop pitches it 2.0 deg toe-down against his flat rest foot
U_BALL = 0.217          # his ball (metatarsal heads) at 72 % of the foot from the heel
U_HEEL = 0.017          # his heel's back at u = 17 mm: the upper's heel 9 mm in front of the sole's (02) + HEEL_WALL
CLEAR = 0.008           # shell outer surface at least 8 mm outside his skin when built (shell 3 + foam and liner 5)
CLEAR_SOLE = 0.004      # at his foot's widest (the ball, at the welt): 3 mm upper + 1 mm liner, a snug lasted fit
CLEAR_CALF = 0.004      # over the calf (v above 260 mm): 3 mm TPU + 1 mm liner pressed by the calf. Leatt's photo 05
                        # shows the boot empty and closed; his calf (127 mm wide) opens the shaft's panels
SHAFT_FRONT_V = 0.150   # below this the shin's front line is carried straight down (the instep starts in front)


class Fit:
    """His right foot and leg in the right boot's frame, the profiles from Leatt's photos, the size."""

    def __init__(self, body):
        self.body = body
        self.foot, self.y_heel = foot_length(body)
        self.us_size = choose_size(self.foot)
        self.L = sole_length(self.us_size)
        self.s02 = Side(P02, self.L).s
        self.H = (P02["ground_y"] - P02["top_y"]) * self.s02
        V = body["V"]
        heel = V[(V[:, 0] < -0.1) & (V[:, 2] < 0.05) & (V[:, 1] > 0.0)]
        self.x_hc = 0.5 * (heel[:, 0].min() + heel[:, 0].max())
        # yaw: his ball's centre onto the outsole's centre at the ball (photo 06; the boot's last curves outward)
        ball = V[(V[:, 0] < -0.06) & (V[:, 2] < 0.03) & (np.abs(self.y_heel - V[:, 1] - (U_BALL - U_HEEL)) < 0.006)]
        c_his = self.x_hc - 0.5 * (ball[:, 0].min() + ball[:, 0].max())
        u_p, w_out_p, w_in_p, _ = plan_outline(self.L)
        c_sole = np.interp(U_BALL, u_p, 0.5 * (w_out_p + w_in_p))
        self.yaw = np.arctan2(c_sole - c_his, U_BALL - U_HEEL)

    PITCH = np.arctan2(V_FOOT - V_BALL, U_BALL - U_HEEL)

    def to_boot(self, P):
        """MB points of his right foot and leg -> the boot frame (u, v, w): his heel's back and centre on the boot's
        heel (U_HEEL, w 0), yawed by YAW about it (his heel-ball line on the sole's), pitched by PITCH (heel drop)."""
        P = np.asarray(P, float)
        a = self.y_heel - P[..., 1]                                     # along his foot from the heel
        b = P[..., 2]                                                   # up from his sole
        w = self.x_hc - P[..., 0]                                       # to his right foot's outer side
        cy, sy = np.cos(self.yaw), np.sin(self.yaw)
        a, w = cy * a - sy * w, sy * a + cy * w
        c, s = np.cos(self.PITCH), np.sin(self.PITCH)
        return np.stack([U_HEEL + c * a + s * b, V_FOOT - s * a + c * b, w], -1)

    def to_body(self, Q):
        Q = np.asarray(Q, float)
        du, dv = Q[..., 0] - U_HEEL, Q[..., 1] - V_FOOT
        c, s = np.cos(self.PITCH), np.sin(self.PITCH)
        a, b = c * du - s * dv, s * du + c * dv
        cy, sy = np.cos(self.yaw), np.sin(self.yaw)
        a, w = cy * a + sy * Q[..., 2], -sy * a + cy * Q[..., 2]
        return np.stack([self.x_hc - w, self.y_heel - a, b], -1)

    def leg_extents(self, vs):
        """His right leg's (u_min, u_max, w_min, w_max) in the boot frame at each height v (exact slices)."""
        V = self.body["V"]
        T = tris_of(self.body["F"], self.body["FS"])
        right = T[(V[T][:, :, 0] < -0.06).all(1)]
        Q = self.to_boot(V)[:, [0, 2, 1]]                              # slice planes v = const
        out = []
        for v in vs:
            s = slice_z(Q, right, v)
            if len(s) == 0:
                out.append([np.nan] * 4)
                continue
            q = s.reshape(-1, 3)
            out.append([q[:, 0].min(), q[:, 0].max(), q[:, 1].min(), q[:, 1].max()])
        return np.array(out)

    def foot_extents(self, us, vmax=0.20):
        """His right foot's top v and w range at each u (vertices within 4 mm), boot frame."""
        V = self.body["V"]
        q = self.to_boot(V[V[:, 0] < -0.06])
        q = q[q[:, 1] < vmax]
        out = []
        for u in us:
            s = q[np.abs(q[:, 0] - u) < 0.004]
            out.append([s[:, 1].max(), s[:, 2].min(), s[:, 2].max()] if len(s) else [np.nan] * 3)
        return np.array(out)


def shell_sections(fit):
    """The shell's numbers from Leatt's photos, opened where his leg or foot needs clearance around it:
    the side outline M (1 mm raster over us_m, vs; photo 02), grown by his leg (CLEAR) and foot tops;
    shaft half-width hws and centre wcs per mm of height (photo 05's clean inner edge about its centre line, the
    section centred on his leg); foot half-width hwf and centre wcf per mm of length us (photo 06's outsole less
    the welt, held over the last 30 mm so the toe is rounded once)."""
    us_m, vs, M = side_mask(fit.L)
    M = base_outline(us_m, vs, M, fit.L)
    leg = fit.leg_extents(vs)
    above = vs > V_FOOT + 0.06                                     # the leg above the ankle bones
    lu0, lu1, lw0, lw1 = [np.where(above, leg[:, i], np.nan) for i in range(4)]
    grow = lambda a: ndi.maximum_filter1d(np.nan_to_num(a, nan=-1.0), 15)
    a0, a1 = -grow(-(lu0 - CLEAR)), grow(lu1 + CLEAR)
    for i in np.nonzero(above & np.isfinite(lu0))[0]:
        M[i] |= (us_m >= a0[i]) & (us_m <= a1[i])
    vb, wi, wo = back_profile(fit.H, fit.L)
    c_photo = -0.045 * np.clip(vs - 0.10, 0, None)                 # 05's centre line: 0 at the heel, -13.5 mm at the top
    hws = c_photo - np.interp(vs, vb, ndi.gaussian_filter1d(wi, 40))
    wcs = 0.5 * (lw0 + lw1)
    ok = np.isfinite(wcs)
    wcs = np.interp(vs, vs[ok], ndi.gaussian_filter1d(wcs[ok], 20))
    clear = np.interp(vs, [0.20, 0.26], [CLEAR, CLEAR_CALF])       # the calf opens the worn shaft's panels
    need = np.where(ok, np.maximum(lw1 - wcs, wcs - lw0) + clear, 0)
    hws = ndi.gaussian_filter1d(np.maximum(hws, ndi.maximum_filter1d(np.nan_to_num(need), 61)), 25)
    # foot
    u_p, w_out_p, w_in_p, _ = plan_outline(fit.L)
    us = np.arange(U0, fit.L + 0.004, GRID)
    uh = np.minimum(us, fit.L - 0.030)
    w0 = np.interp(uh, u_p, w_in_p) + WELT_OUT
    w1 = np.interp(uh, u_p, w_out_p) - WELT_OUT
    ft = fit.foot_extents(us)
    fok = np.isfinite(ft[:, 0])
    w0 = np.where(fok, np.minimum(w0, np.nan_to_num(ft[:, 1]) - CLEAR_SOLE), w0)
    w1 = np.where(fok, np.maximum(w1, np.nan_to_num(ft[:, 2]) + CLEAR_SOLE), w1)
    w0, w1 = ndi.gaussian_filter1d(w0, 12.0, mode="nearest"), ndi.gaussian_filter1d(w1, 12.0, mode="nearest")
    # the upper stays inside the welt (a lasted upper tucks under the foot; the welt stands out of it)
    w0 = np.maximum(w0, np.interp(uh, u_p, w_in_p) + 0.0015)
    w1 = np.minimum(w1, np.interp(uh, u_p, w_out_p) - 0.0015)
    foot_top = ndi.gaussian_filter1d(np.where(fok, np.nan_to_num(ft[:, 0]) + CLEAR, 0.0), 6.0)
    ftm = np.interp(us_m, us, foot_top)
    M |= (vs[:, None] <= ftm[None, :]) & (ftm[None, :] > 0.03)
    M = ndi.binary_closing(M, structure=disk(4))
    return dict(M=M, us_m=us_m, vs=vs, hws=hws, wcs=wcs, us=us, hwf=0.5 * (w1 - w0), wcf=0.5 * (w0 + w1),
                u_plan=u_p, w_out_plan=w_out_p, w_in_plan=w_in_p)


# the white shell's top edge and the gaiter's top (photo 02 outer, 03 inner: first white below the black gaiter)
TOP_U = [0.0, 0.01, 0.03, 0.06, 0.09, 0.13, 0.17, 0.20]
SHELL_TOP_OUT = [0.360, 0.367, 0.375, 0.393, 0.396, 0.378, 0.372, 0.370]
SHELL_TOP_IN = [0.385, 0.388, 0.392, 0.405, 0.409, 0.405, 0.392, 0.388]
GAITER_TOP = [0.405, 0.418, 0.423, 0.420, 0.415, 0.406, 0.398, 0.395]


WELT_OUT = 0.005        # the welt and outsole stand 5 mm out from the upper (photos 02, 10)
H_VOX = 0.0025          # shell field voxel
BASE_OPEN = 12          # mm: protrusions of the photo outline narrower than 24 mm are parts, not the shell
BASE_SMOOTH = 0.004     # m: the core outline is the photo's smoothed over 4 mm
R_FOOT = 0.022          # the foot's top and toe round over 22 mm from the side outline (EST, photos 01, 07)
P_SHAFT = 2.4           # the shaft's sections: superellipses spanning the outline's depth and the shaft's width
V_FOOT_TOP, V_SHAFT = 0.08, 0.17    # the foot's numbers below the first, the shaft's above the second, blended


# the outsole's black top and the welt above it, along the sole (photo 02 grid crops: black top at y 1628 at the heel,
# 1650 under the arch and the ball, 1640 at x 1400, 1620 at the toe; the white roped welt 6.5 mm above it)
SOLE_TOP_U = [0.0, 0.06, 0.12, 0.17, 0.24, 0.274, 0.31, 0.33]
SOLE_TOP_V = [0.0212, 0.0200, 0.0155, 0.0143, 0.0143, 0.0177, 0.0220, 0.0240]
WELT_H = 0.0065


def sole_top(u):
    return np.interp(u, SOLE_TOP_U, SOLE_TOP_V)


def welt_top(u):
    """Bottom of the white upper (top of the welt) along the sole."""
    return sole_top(u) + WELT_H


def smin(a, b, k):
    hh = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * hh - k * hh * (1 - hh)


def smax(a, b, k):
    return -smin(-a, -b, k)


class SidePlane:
    """Fields on the side plane (u, v), 1 mm raster: signed distance e to the outline (positive inside; the outline
    is extended past its top and bottom, which are cut separately), and the half-width, centre, rounding radius and
    exponent of the sections at each point."""

    def __init__(self, sec):
        self.h = h = GRID
        M, us, vs = sec["M"], sec["us_m"], sec["vs"]
        # the base shell: the outline without what stands proud of it (buckles, strap ends, plates, the spine;
        # built as their own parts): opened by 8 mm, closed by 4 mm
        M = ndi.binary_closing(M, structure=disk(4))
        pad = 40
        self.u = us
        self.v = v = np.concatenate([vs[0] - h * np.arange(pad, 0, -1), vs, vs[-1] + h * np.arange(1, pad + 1)])
        m = np.concatenate([np.repeat(M[2:3], pad, 0), M, np.repeat(M[-60:-59], pad, 0)])
        top = np.searchsorted(v, vs[-1] - 0.060)
        m[top:] = m[top]                                            # the gaiter's slanted top: cut separately
        e = (ndi.distance_transform_edt(m) - ndi.distance_transform_edt(~m)) * h
        e = ndi.gaussian_filter(e, BASE_SMOOTH / h)                # a smooth core outline (no creases)
        es = ndi.gaussian_filter(e, 0.012 / h)                     # the interior smoother still
        self.e = es + (e - es) * np.exp(-(e / 0.006) ** 2)
        t = np.clip((v - V_FOOT_TOP) / (V_SHAFT - V_FOOT_TOP), 0, 1)
        beta = (t * t * (3 - 2 * t))[:, None]
        hwf = np.interp(us, sec["us"], sec["hwf"])[None, :]
        wcf = np.interp(us, sec["us"], sec["wcf"])[None, :]
        hws = np.interp(v, vs, sec["hws"])[:, None]
        wcs = np.interp(v, vs, sec["wcs"])[:, None]
        self.hw = (1 - beta) * hwf + beta * hws
        self.wc = (1 - beta) * wcf + beta * wcs
        R_row = np.maximum(ndi.maximum_filter1d(self.e.max(1), 41), 0.01)[:, None]   # shaft: elliptic sections
        self.R = (1 - beta) * R_FOOT + beta * R_row + 0 * hwf
        self.p = (1 - beta) * 2.0 + beta * P_SHAFT + 0 * hwf

    def sample(self, name, uu, vv):
        a = getattr(self, name)
        return ndi.map_coordinates(a, [(vv - self.v[0]) / self.h, (uu - self.u[0]) / self.h], order=1,
                                   mode="nearest")


def shell_field(sec, h=H_VOX, top="shell"):
    """Signed distance (m, negative inside) on a voxel grid of the white shell (top = "shell": cut at its white
    top edge) or of its outline volume up to the gaiter's top (top = "gaiter"): every point (u, v) inside the side
    outline carries the half-width there, rounded toward the outline over R (superellipse of exponent p); the
    top cut with a 3 mm round, the bottom at the welt."""
    sp = SidePlane(sec)
    u = np.arange(U0 - 0.012, 0.345, h)
    v = np.arange(0.0, sec["vs"][-1] + 3 * h, h)
    w = np.arange(-0.13, 0.11, h)
    UU, VV = np.meshgrid(u, v, indexing="ij")
    e = sp.sample("e", UU, VV)[:, :, None]
    hw = sp.sample("hw", UU, VV)[:, :, None]
    wc = sp.sample("wc", UU, VV)[:, :, None]
    R = sp.sample("R", UU, VV)[:, :, None]
    p = sp.sample("p", UU, VV)[:, :, None]
    W = w[None, None, :]
    x = np.clip(1 - e / R, 0, None)                                 # 0 deep inside, 1 on the outline, > 1 outside
    G = (x ** p + np.abs((W - wc) / hw) ** p) ** (1 / p)
    d = (G - 1) * np.minimum(R, hw)
    if top == "shell":
        s = np.clip(0.5 + 0.5 * (W - wc) / hw, 0, 1)
        s = s * s * (3 - 2 * s)                                     # 0 on the inner side, 1 on the outer
        vt = (1 - s) * np.interp(u, TOP_U, SHELL_TOP_IN)[:, None, None] + \
            s * np.interp(u, TOP_U, SHELL_TOP_OUT)[:, None, None]
    else:
        vt = np.interp(u, TOP_U, GAITER_TOP)[:, None, None]
    d = smax(d, VV[:, :, None] - vt, 0.003)
    bot = welt_top(u)[:, None, None]
    d = np.maximum(d, (bot - 0.004) - VV[:, :, None])
    return ndi.gaussian_filter(d, 0.6), np.array([u[0], v[0], w[0]])


def disk(r):
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


# back view 05 (right boot = the right one; image right = its outer side) and soles 06 (right boot = the left one,
# toe up; image left = its outer side). Calibrated to the side view: 05 by the boot's height (ground 1742, gaiter
# top 215), 06 by the sole length (toe cap tip 275, heel 1555); w = 0 at the heel's centre in the sole view (x 663),
# and 05's full-width centre at the bottom (x 1256, the forefoot) on the sole view's forefoot centre (x 621.5).
P05 = dict(ground_y=1742.0, top_y=215.0, xc=1256.0)
P06 = dict(toe_y=275.0, heel_y=1555.0, xc_heel=663.0, xc_ff=621.5)


def runmin(a, n):
    return ndi.maximum_filter1d(ndi.minimum_filter1d(a, n, mode="nearest"), n, mode="nearest")


def back_profile(H, L):
    """Shaft edges from photo 05: v (m, increasing) -> w of the inner and outer edge of the shell. The buckles'
    bumps on the outer edge are taken off by an opening of the edge profile (window 150 px; a buckle is 60 to 120
    px tall)."""
    _, m = photo_mask(ref("05"))
    s5 = H / (P05["ground_y"] - P05["top_y"])
    s6 = L / (P06["heel_y"] - P06["toe_y"])
    w_ff = (P06["xc_heel"] - P06["xc_ff"]) * s6                        # forefoot centre, outer of the heel's
    ys = np.arange(int(P05["top_y"]) + 10, int(P05["ground_y"]) - 5)
    xl, xr = [], []
    for y in ys:
        r = np.nonzero(m[y, 950:])[0] + 950
        run = np.split(r, np.nonzero(np.diff(r) > 1)[0] + 1)[0]
        xl.append(run[0])
        xr.append(run[-1])
    xl = ndi.median_filter(np.array(xl, float), 9, mode="nearest")
    xr = runmin(np.array(xr, float), 150)
    v = (P05["ground_y"] - ys) * s5
    return v[::-1], ((xl - P05["xc"]) * s5 + w_ff)[::-1], ((xr - P05["xc"]) * s5 + w_ff)[::-1]


def tris_of(F, FS):
    starts = np.concatenate([[0], np.cumsum(FS)[:-1]])
    return np.array([[F[s], F[s + i], F[s + i + 1]] for s, n in zip(starts, FS) for i in range(1, n - 1)])


def slice_z(V, T, z):
    """Segments where the triangle mesh (V, T) crosses the plane z: (n, 2, 3)."""
    d = V[T, 2] - z
    s = np.sign(d)
    cross = (s.min(1) < 0) & (s.max(1) > 0)
    segs = []
    for t, dd in zip(T[cross], d[cross]):
        p = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if (dd[i] < 0) != (dd[j] < 0):
                a = dd[i] / (dd[i] - dd[j])
                p.append(V[t[i]] + a * (V[t[j]] - V[t[i]]))
        if len(p) == 2:
            segs.append(p)
    return np.array(segs)


def plan_outline(L):
    """Outsole outline from photo 06: u (m) -> (w_outer, w_inner) of the dark rubber, the toe cap continuing it."""
    a, m = photo_mask(ref("06"))
    lum = a.mean(2)
    dark = ndi.binary_fill_holes(ndi.binary_closing(lum < 110, iterations=3))
    s6 = L / (P06["heel_y"] - P06["toe_y"])
    ys = np.arange(int(P06["toe_y"]), int(P06["heel_y"]) + 1)
    lo, hi = [], []
    for y in ys:
        d = np.nonzero(dark[y, :950])[0]
        r = np.nonzero(m[y, :950])[0]
        q = d if len(d) > 20 else r
        lo.append(q.min() if len(q) else np.nan)
        hi.append(q.max() if len(q) else np.nan)
    lo, hi = np.array(lo, float), np.array(hi, float)
    # the outer edge is crossed by the buckles and the white upper between y 1030 and 1300: robust envelope
    lo = ndi.median_filter(np.nan_to_num(lo, nan=np.nanmax(lo)), 61, mode="nearest")
    hi = ndi.median_filter(np.nan_to_num(hi, nan=np.nanmin(hi)), 31, mode="nearest")
    u = (P06["heel_y"] - ys) * s6
    w_out = (P06["xc_heel"] - lo) * s6
    w_in = (P06["xc_heel"] - hi) * s6
    return u[::-1], ndi.gaussian_filter1d(w_out[::-1], 6), ndi.gaussian_filter1d(w_in[::-1], 6), s6


# ---------------------------------------------------------------- component 1: sole, welt, toe cap
P06L = dict(toe_y=266.0, heel_y=1547.0, xc_heel=1284.0)   # the LEFT sole in photo 06 (right blob), same reading
LUG_DEPTH = 0.0035      # tread: the base between the lugs 3.5 mm above the lug faces (EST: photo 02's sole edge)
ARCH_LIFT = 0.0015      # the waist under the arch clears the ground by 1.5 mm (photo 02, y 1697 against 1702)
SOLE_EDGE_R = 0.0025    # the outsole's bottom edge rounded over 2.5 mm (photos 02, 10)


def sole_loop(L, step=0.002):
    """The outsole's outline (u, w) as a closed loop."""
    u, wo, wi, _ = plan_outline(L)
    k = slice(None, None, 4)
    loop = np.vstack([np.stack([u[k], wi[k]], 1), np.stack([u[k][::-1], wo[k][::-1]], 1)])
    return G.smooth_poly(G.resample(loop, step), 6)


def tread_raster():
    """Lug faces (1) against the recessed base (0) under the sole, from the moulding's fine texture in photo 06
    (lugs, the footpeg zone and the logos are textured; the base between them is smooth), in photo 06's pixels."""
    a = np.asarray(Image.open(ref("06")).convert("L")).astype(float)
    hp = a - ndi.gaussian_filter(a, 3)
    en = np.sqrt(ndi.gaussian_filter(hp ** 2, 4))
    lug = ndi.binary_opening(ndi.binary_closing(en > 9.0, iterations=2), iterations=2)
    return ndi.gaussian_filter(lug.astype(float), 2.0)


def to_px06(P, L, u, w):
    s6 = L / (P["heel_y"] - P["toe_y"])
    return P["xc_heel"] - np.asarray(w) / s6, P["heel_y"] - np.asarray(u) / s6


def build_sole(L, side="R"):
    """Outsole: the photo 06 outline extruded from the tread up to the black's top (SOLE_TOP), the bottom a height
    field of the Leatt lug pattern traced from photo 06 (lug faces on the ground line, the base LUG_DEPTH up,
    the waist ARCH_LIFT up), its edge rounded. Bottom faces carry UVs into the photo's sole (texture per side)."""
    from scipy.spatial import cKDTree
    loop = sole_loop(L, 0.0015)
    lug = tread_raster()
    tree = cKDTree(loop)

    def h_bottom(u, w):
        x, y = to_px06(P06, L, u, w)                               # the lug pattern of the right sole
        f = ndi.map_coordinates(lug, [[y], [x]], order=1)[0]
        d = tree.query([u, w])[0]
        edge = SOLE_EDGE_R * max(0.0, 1 - d / SOLE_EDGE_R) ** 2
        arch = ARCH_LIFT * np.exp(-((u - 0.135) / 0.03) ** 2)
        return max(LUG_DEPTH * (1 - f), edge) + arch + toe_spring(u)

    def to3d(u, w, t):
        return (u, sole_top(u) if t > 0 else h_bottom(u, w), w)

    m = G.plate2d(loop, [], 1.0, "boot_tread", to3d, step=0.0016, side_mat="boot_sole",
                  rings=(0.0006, 0.0015, 0.0028))
    V = np.asarray(m.V)
    tex = "boot_tread_" + side
    for i, f in enumerate(m.F):
        if m.M[i] != "boot_tread":
            continue
        if all(V[j][1] > 0.009 for j in f):                         # the top faces: plain rubber under the upper
            m.M[i] = "boot_sole"
        else:
            m.M[i] = tex
            m.uv[i] = [tread_uv(V[j][0], V[j][2], L, side) for j in f]
    return m


TREAD_BOX = {"R": (360, 240, 880, 1600), "L": (1040, 230, 1560, 1590)}   # crops of photo 06 for the textures


def tread_uv(u, w, L, side):
    if side == "R":
        x, y = to_px06(P06, L, u, w)
    else:                                                           # the left sole: its outer side to the image's right
        x, y = to_px06(P06L, L, u, -w)
    x0, y0, x1, y1 = TREAD_BOX[side]
    return (float((x - x0) / (x1 - x0)), float(1 - (y - y0) / (y1 - y0)))


def write_tread_textures(out_dir):
    """Black rubber albedo and a normal map of the moulding for each sole, from photo 06 (Leatt's own soles: the
    left boot's is its own, so its LEATT reads right)."""
    a = np.asarray(Image.open(ref("06")).convert("L")).astype(float)
    for side, (x0, y0, x1, y1) in TREAD_BOX.items():
        c = a[y0:y1, x0:x1]
        alb = np.clip(18 + (c - 20) * 0.45, 12, 60)                 # sRGB 12..60: black rubber, moulding visible
        alb[c > 150] = 30                                           # the toe cap and the background: plain rubber
        Image.fromarray(alb.astype(np.uint8)).convert("RGB").save(os.path.join(out_dir, f"boot_tread_{side}.png"))
        hgt = ndi.gaussian_filter(np.minimum(c, 120), 1.0)
        gy, gx = np.gradient(hgt)
        n = np.stack([-gx * 0.02, gy * 0.02, np.ones_like(gx)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(
            os.path.join(out_dir, f"boot_tread_{side}_n.png"))


def offset_loop(loop, d):
    """Closed loop moved by d along its outward normal."""
    t = np.roll(loop, -1, 0) - np.roll(loop, 1, 0)
    n = np.stack([t[:, 1], -t[:, 0]], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    if G.inside(loop, (loop + 0.001 * n)[::7]).mean() > 0.5:
        n = -n
    return loop + d * n


def ellipsoid(a, b, c, nu=8, nv=5):
    """A UV ellipsoid (semi-axes along u, v, w): vertices and faces."""
    th = np.linspace(0, np.pi, nv + 1)[1:-1]
    ph = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    P = [[0, b, 0]]
    for t in th:
        for p in ph:
            P.append([a * np.sin(t) * np.cos(p), b * np.cos(t), c * np.sin(t) * np.sin(p)])
    P.append([0, -b, 0])
    F = [(0, 1 + (i + 1) % nu, 1 + i) for i in range(nu)]
    for r in range(len(th) - 1):
        for i in range(nu):
            a0, a1 = 1 + r * nu + i, 1 + r * nu + (i + 1) % nu
            F.append((a0, a1, a1 + nu, a0 + nu))
    last = len(P) - 1
    base = 1 + (len(th) - 1) * nu
    F += [(base + i, last, base + (i + 1) % nu) for i in range(nu)]
    return np.array(P), F


def mesh_of(V, F, mat):
    m = G.Mesh()
    o = m.verts(V)
    for f in F:
        m.face([o + i for i in f], mat)
    return m


def build_welt(L):
    """The white welt band under the upper's edge (6.5 mm, standing WELT_OUT out) and the roped stitch on it."""
    loop = sole_loop(L, 0.002)
    inner = offset_loop(loop, -(WELT_OUT + 0.004))
    outer = offset_loop(loop, -0.0003)
    m = G.plate2d(outer, [inner], 1.0, "boot_welt",
                  lambda u, w, t: (u, welt_top(u) if t > 0 else sole_top(u), w), step=0.004)
    # the stitch: a twisted cord of slanted beads 2.5 mm in from the welt's edge, every 2.4 mm (photo 10)
    path = G.resample(offset_loop(loop, -0.0022), 0.0024)
    t = np.roll(path, -1, 0) - np.roll(path, 1, 0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    bv, bf = ellipsoid(0.0034, 0.0014, 0.0017, 6, 4)
    for p, d in zip(path, t):
        if p[0] > L - 0.014:
            continue                                                # under the toe cap
        a = np.arctan2(d[1], d[0]) + np.radians(35)                 # each turn of the cord slants 35 deg
        R = np.array([[np.cos(a), 0, -np.sin(a)], [0, 1, 0], [np.sin(a), 0, np.cos(a)]])
        c = np.array([p[0], welt_top(p[0]) + 0.0008, p[1]])
        m.add(mesh_of(bv @ R.T + c, bf, "boot_stitch"))
    return m


# the toe spring: the sole's bottom rises toward the toe (photo 02: y 1690 at x 1350, 1680 at 1450, 1660 at 1500,
# 1640 at 1550 against the ground line 1702)
TOE_SPRING_U = [0.24, 0.26, 0.288, 0.302, 0.317, 0.335]
TOE_SPRING_V = [0.0, 0.0034, 0.0063, 0.0120, 0.0177, 0.0215]


def toe_spring(u):
    return np.interp(u, TOE_SPRING_U, TOE_SPRING_V)


class ShellSDF:
    """Trilinear lookup of the shell's field: f(u, v, w) in metres (negative inside)."""

    def __init__(self, f, origin, h):
        self.f, self.o, self.h = f, np.asarray(origin), h

    def __call__(self, P):
        P = np.atleast_2d(P)
        val, _ = trilinear(self.f, (P - self.o) / self.h)
        return val

    def grad(self, P):
        P = np.atleast_2d(P)
        _, g = trilinear(self.f, (P - self.o) / self.h)
        return g / np.linalg.norm(g, axis=1, keepdims=True)

    def project(self, P, off=0.0, iters=8):
        """Points moved along the field's gradient onto the level `off` (m outside the surface)."""
        P = np.atleast_2d(P).astype(float).copy()
        for _ in range(iters):
            P -= ((self(P) - off)[:, None]) * self.grad(P)
        return P


CAP_T = 0.0018          # Zamak toe cap 1.8 mm thick (EST, photo 07's edge)
CAP_BACK = 0.017        # it wraps the last 17 mm of the sole at the sides (photo 02: from x 1555, u 318 mm)
CAP_TOP_C, CAP_TOP_S = 0.038, 0.030   # its top edge: 36 mm above the ground at the tip, 29 mm at the sides (02, 07)
CAP_SCREWS_TOP = [(-0.45, 0.027), (0.45, 0.027)]          # (position along the wrap -1..1, height): photo 07
CAP_SCREWS_BOT = [(0.322, 0.021), (0.322, 0.006), (0.322, -0.0095)]   # (u, w) under the toe: photo 06, x 580/640/700


def build_toecap(L, sdf):
    """The silver toe cap: a band wrapping the toe from the sole's bottom edge to its top edge, 1.8 mm thick, laid
    on the sole, welt and shell (projected onto the shell's field 0.4 mm out), a flange under the sole's toe and
    five Phillips screws (two on the wrap, three under: photos 06, 07). UVs: (position along the wrap, height)."""
    loop = sole_loop(L, 0.0012)
    front = loop[loop[:, 0] > L - CAP_BACK]
    order = np.argsort(np.arctan2(front[:, 1], front[:, 0] - (L - 0.05)))
    arc = G.resample(front[order], 0.002)
    arc = arc[np.argsort(np.arctan2(arc[:, 1], arc[:, 0] - (L - 0.05)))]
    ns = len(arc)
    s = np.linspace(-1, 1, ns)
    t2 = np.gradient(arc, axis=0)
    nrm = np.stack([t2[:, 1], -t2[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    if (nrm[:, 0] < 0).mean() > 0.5:
        nrm = -nrm
    nv = 10
    rows_in = []
    for k in range(nv + 1):
        f = k / nv
        top = CAP_TOP_C - (CAP_TOP_C - CAP_TOP_S) * s ** 2
        bot = toe_spring(arc[:, 0]) - 0.0008
        v = bot + f * (top - bot)
        n3 = np.stack([nrm[:, 0], np.zeros(ns), nrm[:, 1]], 1)
        base = np.stack([arc[:, 0], v, arc[:, 1]], 1)
        # march in from 15 mm outside along the plan normal to the first point on the shell (0.4 mm out of it);
        # below the shell (welt and sole) the cap lies 0.6 mm out of the sole's outline
        steps = np.arange(0.015, -0.030, -0.0005)
        cand = base[:, None, :] + steps[None, :, None] * n3[:, None, :]
        hit = sdf(cand.reshape(-1, 3)).reshape(ns, len(steps)) < 0.0004
        first = np.where(hit.any(1), np.argmax(hit, 1), -1)
        p = base + 0.0006 * n3
        ok = (first >= 0) & (v > sole_top(arc[:, 0]) + WELT_H - 0.002)
        q = cand[np.arange(ns), np.maximum(first, 0)]
        p[ok] = np.where((np.einsum("ij,ij->i", q - base, n3) > 0.0006)[:, None], q, p)[ok]
        rows_in.append(p)
    rows_in = ndi.gaussian_filter1d(ndi.gaussian_filter1d(np.array(rows_in), 1.2, axis=0, mode="nearest"), 1.5,
                                    axis=1, mode="nearest")
    # outward normals of the inner surface by finite differences, the outer surface CAP_T out
    du = np.gradient(rows_in, axis=1)
    dv = np.gradient(rows_in, axis=0)
    n3 = np.cross(du, dv)
    n3 /= np.linalg.norm(n3, axis=2, keepdims=True)
    if (n3[..., 0] * 1 > 0).mean() < 0.5:
        n3 = -n3
    rows_out = rows_in + CAP_T * n3
    m = G.Mesh()
    oi = m.verts(rows_in.reshape(-1, 3))
    oo = m.verts(rows_out.reshape(-1, 3))
    idx = lambda o, k, i: o + k * ns + i
    for k in range(nv):
        for i in range(ns - 1):
            q = (idx(oo, k, i), idx(oo, k, i + 1), idx(oo, k + 1, i + 1), idx(oo, k + 1, i))
            m.face(q, "boot_cap")
            m.uv[len(m.F) - 1] = [(s[i] * 0.5 + 0.5, k / nv), (s[i + 1] * 0.5 + 0.5, k / nv),
                                  (s[i + 1] * 0.5 + 0.5, (k + 1) / nv), (s[i] * 0.5 + 0.5, (k + 1) / nv)]
            m.face((idx(oi, k, i), idx(oi, k + 1, i), idx(oi, k + 1, i + 1), idx(oi, k, i + 1)), "boot_cap")
            m.uv[len(m.F) - 1] = [(0.0, 0.0)] * 4
    for i in range(ns - 1):                                         # bottom and top edges
        for k, rev in ((0, False), (nv, True)):
            f = (idx(oi, k, i), idx(oi, k, i + 1), idx(oo, k, i + 1), idx(oo, k, i))
            m.face(f[::-1] if rev else f, "boot_cap")
            m.uv[len(m.F) - 1] = [(0.0, 0.0)] * 4
    for i, rev in ((0, False), (ns - 1, True)):                     # the two ends
        for k in range(nv):
            f = (idx(oi, k, i), idx(oo, k, i), idx(oo, k + 1, i), idx(oi, k + 1, i))
            m.face(f[::-1] if rev else f, "boot_cap")
            m.uv[len(m.F) - 1] = [(0.0, 0.0)] * 4
    # flange under the toe, on the sole's sprung bottom
    fl = loop[loop[:, 0] > L - 0.024]
    fl = fl[np.argsort(np.arctan2(fl[:, 1], fl[:, 0] - (L - 0.05)))]
    back = np.stack([np.full(9, L - 0.024), np.linspace(fl[-1, 1], fl[0, 1], 9)], 1)
    back[:, 0] += 0.004 * np.sin(np.linspace(0, np.pi, 9))          # the plate's back edge bows forward (06)
    outline = G.smooth_poly(G.resample(np.vstack([fl, back[1:-1]]), 0.0015), 2)
    m.add(G.plate2d(outline, [], CAP_T, "boot_cap",
                    lambda u, w, t: (u, toe_spring(u) - 0.0004 + (t + CAP_T / 2), w), step=0.003))
    for u, w in CAP_SCREWS_BOT:
        m.add(screw_head(np.array([u, toe_spring(u) - 0.0004, w]), np.array([0, -1.0, 0]), 0.0050))
    for sp, v in CAP_SCREWS_TOP:
        i = int(round((sp * 0.5 + 0.5) * (ns - 1)))
        k = int(round(nv * 0.7))
        m.add(screw_head(rows_out[k, i], n3[k, i], 0.0048))
    return m


def screw_head(c, n, d, mat="boot_screw"):
    """A pan-head Phillips screw: a low dome of diameter d on the surface at c facing n, with a cross recess."""
    R = G.frame_z(n)
    prof = [(0.0, 0.0012), (0.25, 0.00118), (0.5, 0.0011), (0.75, 0.0009), (0.92, 0.0006), (1.0, 0.0002),
            (1.0, -0.0004)]
    m = G.Mesh()
    seg = 16
    rings = []
    for r, z in prof:
        a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
        rr = r * d / 2
        ring = np.stack([rr * np.cos(a), rr * np.sin(a), np.full(seg, z)], 1)
        # the cross recess: points near the arms pressed down
        arm = np.minimum(np.abs(ring[:, 0]), np.abs(ring[:, 1])) < 0.00045
        ring[arm & (rr < d * 0.3), 2] -= 0.0006
        rings.append(ring @ R.T + c)
    G.grid(m, rings[1:][::-1], mat, cap0=True, cap1=True)         # outer ring first: faces point out
    return m


# ---------------------------------------------------------------- materials (sRGB starting values from the photos)
MATERIALS = {
    "boot_white": {"rgb": [236, 239, 242], "rough": 0.38, "coat": 0.15},     # TPU shell, cool white (01, 02)
    "boot_sole": {"rgb": [30, 30, 32], "rough": 0.78},                       # outsole rubber (02, 06)
    "boot_tread_R": {"image": "boot_tread_R.png", "normal": "boot_tread_R_n.png", "rough": 0.82},
    "boot_tread_L": {"image": "boot_tread_L.png", "normal": "boot_tread_L_n.png", "rough": 0.82},
    "boot_welt": {"rgb": [226, 227, 224], "rough": 0.55},                    # white welt (10)
    "boot_stitch": {"rgb": [236, 234, 226], "rough": 0.85, "sheen": 0.4},    # thick white welt cord (10)
    "boot_cap": {"rgb": [205, 206, 210], "rough": 0.28, "metal": 1.0},       # Zamak toe cap (07)
    "boot_screw": {"rgb": [190, 190, 196], "rough": 0.3, "metal": 1.0},
}


# ---------------------------------------------------------------- assembly
class Build:
    """Everything for one pair: the fit on his body, the shell field, the parts of the right boot in its frame."""

    def __init__(self, body):
        self.fit = Fit(body)
        self.sec = shell_sections(self.fit)
        self.field, self.origin = shell_field(self.sec)
        self.sdf = ShellSDF(self.field, self.origin, H_VOX)
        self.parts = {}

    def shell(self):
        P, Q = surface_nets(self.field, self.origin, H_VOX)
        m = G.Mesh()
        m.verts(P)
        for q in Q:
            m.face(tuple(int(i) for i in q), "boot_white")
        return m

    def build(self):
        L = self.fit.L
        self.parts["shell"] = self.shell()
        self.parts["sole"] = {"R": build_sole(L, "R"), "L": build_sole(L, "L")}
        self.parts["welt"] = build_welt(L)
        self.parts["toecap"] = build_toecap(L, self.sdf)
        return self


def mesh_arrays(m):
    V = np.asarray(m.V, float)
    FS = np.array([len(f) for f in m.F])
    F = np.concatenate([np.asarray(f) for f in m.F])
    UV = None
    if m.uv:
        UV = np.concatenate([np.asarray(m.uv.get(i, [(0.0, 0.0)] * len(f)), float) for i, f in enumerate(m.F)])
    return V, F, FS, list(m.M), UV


def weights(fit, Q, bones):
    """Skin weights of boot points Q (boot frame): the foot shell rides foot.R, the shaft lowerleg02.R, blended over
    the Dual Axis hinge at his ankle (25 mm below to 35 mm above it, and only behind the instep's front)."""
    names = list(bones)
    ib, ifoot = names.index("lowerleg02.R"), names.index("foot.R")
    a = fit.to_boot(np.asarray(fit.body["heads"][ifoot]))
    t = np.clip((Q[:, 1] - (a[1] - 0.025)) / 0.06, 0, 1)
    t = t * t * (3 - 2 * t)
    front = np.clip((Q[:, 0] - (a[0] + 0.05)) / 0.05, 0, 1)
    ws = t * (1 - front)
    ws = np.where(ws < 1e-3, 0.0, np.where(ws > 1 - 1e-3, 1.0, ws))
    return ib, ifoot, ws


def assemble(build, out_npz):
    """Both boots into the gear npz of build_rider.py: the right boot placed on his right foot, the left its mirror."""
    fit = build.fit
    bones = [str(b) for b in fit.body["bones"]]
    out = {"names": [], "mats": list(MATERIALS)}
    for side in ("R", "L"):
        for name, part in build.parts.items():
            m = part[side] if isinstance(part, dict) else part
            V, F, FS, M, UV = mesh_arrays(m)
            P = fit.to_body(V)
            ib, ifoot, ws = weights(fit, V, bones)
            if side == "L":
                P[:, 0] = -P[:, 0]                                  # mirror; faces reversed to keep them outward
                starts = np.concatenate([[0], np.cumsum(FS)[:-1]])
                F = np.concatenate([F[s:s + n][::-1] for s, n in zip(starts, FS)])
                if UV is not None:
                    UV = np.concatenate([UV[s:s + n][::-1] for s, n in zip(starts, FS)])
                ib, ifoot = bones.index("lowerleg02.L"), bones.index("foot.L")
            pn = f"boot{side}_{name}"
            out["names"].append(pn)
            out[pn + "__V"] = P
            out[pn + "__F"] = F
            out[pn + "__FS"] = FS
            out[pn + "__M"] = np.array([out["mats"].index(x) for x in M])
            if UV is not None:
                out[pn + "__UV"] = UV
            n = len(P)
            vi = np.arange(n)
            keep_s, keep_f = ws > 1e-4, ws < 1 - 1e-4
            out[pn + "__wv"] = np.concatenate([vi[keep_s], vi[keep_f]])
            out[pn + "__wb"] = np.concatenate([np.full(keep_s.sum(), ib), np.full(keep_f.sum(), ifoot)])
            out[pn + "__ww"] = np.concatenate([ws[keep_s], 1 - ws[keep_f]])
            if name == "sole":
                out[pn + "__smooth"] = np.array(0)                  # moulded rubber: flat facets, crisp lugs
    out["names"] = np.array(out["names"])
    out["mats"] = np.array(out["mats"])
    out["materials"] = json.dumps(MATERIALS)
    meta = dict(size_us=fit.us_size, foot_length=fit.foot, sole_length=fit.L, boot_height=fit.H,
                mm_per_px_02=fit.s02 * 1000, pitch_deg=float(np.degrees(fit.PITCH)))
    out["meta"] = json.dumps(meta)
    np.savez_compressed(out_npz, **out)
    return out


def skin_clearance(build, vmax=None):
    """Depth (m) of each of his right leg's skin vertices inside the shell's outer surface, rest pose (positive =
    inside), for the vertices the boot covers (below the shell's top edge); with their boot-frame positions."""
    fit = build.fit
    V = fit.body["V"]
    idx = np.nonzero(V[:, 0] < -0.06)[0]
    Q = fit.to_boot(V[idx])
    top = np.minimum(np.interp(Q[:, 0], TOP_U, SHELL_TOP_OUT), np.interp(Q[:, 0], TOP_U, SHELL_TOP_IN))
    sel = Q[:, 1] < (top - 0.01 if vmax is None else vmax)
    lo = build.origin
    hi = lo + (np.array(build.field.shape) - 1) * H_VOX
    sel &= (Q >= lo).all(1) & (Q <= hi).all(1)
    idx, Q = idx[sel], Q[sel]
    depth = -build.sdf(Q)
    # below the upper's bottom edge the foot is on the footbed, inside the welt: depth to the outsole's outline
    low = Q[:, 1] < welt_top(Q[:, 0])
    if low.any():
        from scipy.spatial import cKDTree
        loop = sole_loop(build.fit.L, 0.001)
        d = cKDTree(loop).query(Q[low][:, [0, 2]])[0]
        d = np.where(G.inside(loop, Q[low][:, [0, 2]]), d, -d)
        depth[low] = np.maximum(depth[low], d)
    return idx, Q, depth


def main(body_path, out_npz):
    body = dict(np.load(body_path))
    write_tread_textures(TEXDIR)
    b = Build(body).build()
    out = assemble(b, out_npz)
    nv = sum(len(out[n + "__V"]) for n in out["names"])
    print(json.loads(out["meta"]), "vertices", nv)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
