"""Wheels, tyres, final drive and rear brake caliper of the stock CRF250R (plugin of parts.py: see the comment above
parts.plugins). Parts: front_wheel and rear_wheel (each one mesh built in place about its axle, so it can spin),
drive (chain, countershaft sprocket, chain rollers) and rear_brake (caliper, bracket, hose).

Every number carries its source:
  SPEC   research/crf250r-2026.md, or the standard the part is made to (#520 chain, rim contour, Honda bolt circles)
  LEFT / RIGHT / FRONT / REAR   Honda studio photo through cams.py, with rows, columns or the polar scan used
  EST    the real part's usual size where no photo shows it
Angles are in the wheel's side view: 0 = forward (+x), 90 = up, as the wheel stands in Honda's photos.
"""
import functools
import math

import numpy as np

from geom import Mesh, bolt, box, circle, grid, inside, lathe, resample, slot, smooth_poly, tube
from parts import CHAIN_Y, CS, FA, P520, R_FRONT, R_REAR, RA, chain_top, sprocket_r

REPLACES = ["front_wheel", "rear_wheel", "drive"]
FRONT_END = {"front_wheel"}
SMOOTH = {"front_wheel": 32, "rear_wheel": 32, "drive": 32, "rear_brake": 35}
IN = 0.0254

# ---------------------------------------------------------------- measured and specified dimensions
FRONT = dict(
    R=R_FRONT, pitches=41,          # LEFT / RIGHT circle through the knob tips: r 359.3; LEFT: 41 pitches
    root=0.3470,                    # LEFT / RIGHT front arc: the groove floor between the knobs at r 346.5..347.5
    knob=0.012,                     # tips less root: 12.3 mm
    rb=21 * IN / 2, hw=1.60 * IN / 2,   # SPEC rim 21 x 1.60: bead seat radius, half width between the flanges
    hf=0.011,                       # SPEC WM contour flange height (EST 11 mm)
    r_in=0.256,                     # LEFT / RIGHT radial scan about the axle: white ends at r 252..256 mm
    width=0.0885,                   # FRONT rows 1900..2000: 137 px = 88 to 89 mm at the shoulder knobs' depth
)
REAR = dict(
    R=R_REAR, pitches=46,           # LEFT / RIGHT circle through the knob tips: r 334.3; LEFT: 46 pitches
    root=0.3180,                    # LEFT / RIGHT rear arc: the groove floor at r 317..319 (314 at the lowest)
    knob=0.0165,                    # tips less root: 16.3 mm
    rb=19 * IN / 2, hw=1.85 * IN / 2,   # SPEC rim 19 x 1.85
    hf=0.0105,                      # SPEC WM contour flange height (EST)
    r_in=0.229,                     # LEFT / RIGHT radial scan: white ends at r 224..228 mm
    width=0.0915,                   # REAR rows 1750..1975: 139 px = 90 to 92 mm
)
# carcass half sections (y, r - r_crown), crown centre to bead. Shapes EST (MX tyre on a narrow rim), widths fitted
# to the FRONT / REAR photo rows above through the cameras (test_detail_wheels.py checks the silhouettes).
# FRONT rows 2000..2040 (the tread seen from the front where it meets the ground): half width 24 mm 8 mm above the
# lowest point, 35 mm at 21 mm, 44 mm at 34 mm: the knob tips lie on a circle of about 42 mm, the carcass on one of
# about 31 mm. REAR rows 1980..2000: a flatter crown (half width 33 mm 8 mm up).
FRONT_SECTION = [(0.0, 0.0), (0.0121, -0.0019), (0.0228, -0.0073), (0.0307, -0.0155), (0.0349, -0.0230),
                 (0.0361, -0.0310), (0.0356, -0.0420), (0.0336, -0.0520)]
REAR_SECTION = [(0.0, 0.0), (0.0127, -0.0010), (0.0245, -0.0055), (0.0322, -0.014), (0.0358, -0.026), (0.0367, -0.037),
                (0.0345, -0.048)]
# tread rows: (phase in pitches, t0, t1 = arc length from the crown centre along the carcass, block length along the
# tread, height at t0, height at t1, skew = how far the outer end leads the inner end; both sides unless t0 < 0).
# FRONT photo: centre pairs with a V between them, intermediates half a pitch on, shoulder knobs between the rows
# (zig-zag silhouette, two shoulder knobs per pitch in the LEFT photo). Block sizes EST from those photos.
FRONT_ROWS = [(0.00, 0.0012, 0.0150, 0.015, 0.012, 0.012, 0.006),
              (0.50, 0.0185, 0.0300, 0.017, 0.0118, 0.0110, -0.008),
              (0.25, 0.0340, 0.0470, 0.018, 0.0105, 0.0090, 0.004),
              (0.75, 0.0355, 0.0500, 0.015, 0.0100, 0.0088, -0.004)]
# REAR photo rows 1500..1560: one row of four blocks across the tread per pitch (shoulder 17 mm, two centre blocks
# 22 mm each, shoulder). LEFT / RIGHT rear arc: one bump per pitch (harmonic 46, none at 92), 24 mm long 10 mm below
# the tips, the groove floor in view between rows 15 mm down: nothing stands on the crown between the rows. Small
# shoulder knobs half a pitch on (EST). The 3-pitch variation of Honda's profile is not resolved: every pitch alike.
REAR_ROWS = [(0.00, 0.0015, 0.0235, 0.0205, 0.0165, 0.0160, 0.003),
             (0.00, 0.0270, 0.0480, 0.0205, 0.0155, 0.0105, 0.002),
             (0.50, 0.0330, 0.0480, 0.0150, 0.0140, 0.0110, -0.002)]
# where the first row stands, in pitches (LEFT and RIGHT edge scans agree: front tips at 3.35 deg, rear 4.4 / 5.35)
FRONT_PHASE, REAR_PHASE = 3.35 / (360 / 41), 4.9 / (360 / 46)
# spokes: LEFT and RIGHT ring scans at four radii, fitted through the cameras (three-cross, 60 deg): front hub holes
# on r 41 mm, first hole at 18.5 deg (residual 0.9 deg rms in both photos); rear first hole at 10.5..11 deg (fit
# poor, 2.7 deg rms: the rear's hole circle stays EST)
FRONT_HUB_R, FRONT_SPOKE0 = 0.041, math.radians(18.5)
REAR_HUB_R, REAR_SPOKE0 = 0.046, math.radians(10.75)

SPOKES = 36                         # SPEC front 36 (RevZilla listing); rear 36 EST, as every 19 in MX rim of this size
SPOKE_R = 0.0019                    # EST 3.8 mm spokes
DISC_F = dict(r=0.130, y=0.062, t=0.003)    # SPEC 260 mm; y EST (FRONT cols 2078..2108: guard and disc, y 53..74 mm)
DISC_R = dict(r=0.120, y=-0.070, t=0.004)   # SPEC 240 mm; REAR cols 2102..2107, rows 1450..1700: y -68..-72 mm
DISC_F_DEEP = math.radians(-20.0)   # RIGHT polar scan r 126: deep scallops at -98, -59, -21, 18 deg (every 40),
                                    # shallow ones half way: 18 scallops
DISC_R_FLAT = math.radians(86.0)    # RIGHT polar scan r 110..115: four wide scallops at 86 + 90 k deg, 28 small ones
DISC_R_BOLT_R = 0.071               # RIGHT: three bolts on a circle of 92 px (top, rear, bottom)
DISC_F_BOLT_R = 0.054               # EST (hidden by the guard and the fork lug): six M6 bolts
SPROCKET_BOLT_R = 0.0765            # SPEC Honda 153 mm bolt circle; LEFT: bolts 99..101 px from the centre
SPROCKET_BORE_R = 0.0625            # SPEC Honda 125 mm centre hole
SPROCKET_BOLT0 = math.radians(85.4)     # LEFT: bolts at 85 and 145 deg (zoomed crop, cols 2970 / 3059)
SPROCKET_T = 0.0058                 # SPEC #520 sprocket tooth width (chain inner width 6.35)
ROLLER_R = 0.00508                  # SPEC #520 roller 10.16 mm
SEAT_R = 0.00525                    # roller seat with running clearance
TIP_H = 0.0042                      # EST tooth tip above the pitch circle
ARM_FACE = 0.0935                   # REAR cols 1833..1858 at the axle row: the swingarm's inner faces at +-93 to 95 mm
CAL_ANG = math.radians(65.0)        # RIGHT cols 1050..1120, rows 1480..1517: caliper 65 deg above forward, r 105 mm
SEG_RIM = 144


# ---------------------------------------------------------------- small builders
def _piece(m, V, faces, mat):
    """Add a star-shaped piece: every face turned so that its normal points away from the piece's centre."""
    V = np.asarray(V, float)
    c = V.mean(axis=0)
    o = m.verts(V)
    for f in faces:
        P = V[list(f)]
        if np.cross(P[1] - P[0], P[2] - P[0]) @ (P.mean(axis=0) - c) < 0:
            f = f[::-1]
        m.face([o + i for i in f], mat)


def _compact(m):
    """Drop vertices no face uses (carcass grid points under the tread blocks): a lone vertex is a loose piece."""
    used = np.zeros(len(m.V), bool)
    for f in m.F:
        used[list(f)] = True
    if not used.all():
        new = np.cumsum(used) - 1
        m.V = [v for v, u in zip(m.V, used) if u]
        m.F = [tuple(int(new[i]) for i in f) for f in m.F]
    return m


def _ring(r0, r1, y0, y1, mat, seg=32):
    """Ring of rectangular section about the axle, y0 < y1 (faces outward)."""
    return lathe([(r0, y1), (r1, y1), (r1, y0), (r0, y0)], seg, mat, closed=True)


def _ccw(L):
    L = np.asarray(L, float)
    area = np.sum(L[:, 0] * np.roll(L[:, 1], -1) - np.roll(L[:, 0], -1) * L[:, 1])
    return L if area > 0 else L[::-1]


def _plate(outer, holes, y, thick, mat, step, origin=(0.0, 0.0)):
    """Flat plate in the wheel's plane: outline and holes are (x, z) loops about ORIGIN, used point for point (no
    resampling: tooth forms and small holes keep their shape), plus an interior grid; thickness along y about Y."""
    from scipy.spatial import Delaunay, cKDTree
    outer = _ccw(outer)
    hs = [_ccw(h) for h in holes]
    loops = [outer] + hs
    B = np.vstack(loops)
    lo, hi = outer.min(axis=0), outer.max(axis=0)
    gx, gz = np.meshgrid(np.arange(lo[0] + step / 2, hi[0], step), np.arange(lo[1] + step / 2, hi[1], step))
    G = np.stack([gx.ravel(), gz.ravel()], axis=1)
    ok = inside(outer, G)
    for h in hs:
        ok &= ~inside(h, G)
    G = G[ok]
    if len(G):
        G = G[cKDTree(B).query(G)[0] > 0.6 * step]
    P = np.vstack([B, G])
    tri = Delaunay(P).simplices
    c = P[tri].mean(axis=1)
    keep = inside(outer, c)
    for h in hs:
        keep &= ~inside(h, c)
    tri = tri[keep]
    a, b, cc = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    area = (b[:, 0] - a[:, 0]) * (cc[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (cc[:, 0] - a[:, 0])
    tri = tri[abs(area) > 1e-10]
    area = area[abs(area) > 1e-10]
    tri[area < 0] = tri[area < 0][:, ::-1]
    m = Mesh()
    X, Z = P[:, 0] + origin[0], P[:, 1] + origin[1]
    lo_ = m.verts(np.stack([X, np.full(len(P), y - thick / 2), Z], axis=1))      # ccw in (x, z) faces -y
    hi_ = m.verts(np.stack([X, np.full(len(P), y + thick / 2), Z], axis=1))
    for i, j, k in tri:
        m.face((lo_ + i, lo_ + j, lo_ + k), mat)
        m.face((hi_ + i, hi_ + k, hi_ + j), mat)
    o = 0
    for n, L in enumerate(loops):
        for i in range(len(L)):
            j = (i + 1) % len(L)
            f = (lo_ + o + i, hi_ + o + i, hi_ + o + j, lo_ + o + j)
            m.face(f if n == 0 else f[::-1], mat)
        o += len(L)
    return m


def _pilots(r, a0, n):
    """Bolt holes of a bolted joint (3.8 mm, under the bolt heads and nuts)."""
    return [circle(0.0019, 16, *_pol(r, a0 + k * 2 * math.pi / n)) for k in range(n)]


def _pol(r, a):
    return np.stack([np.asarray(r) * np.cos(a), np.asarray(r) * np.sin(a)], axis=-1)


def _round(poly, step=0.0035, k=3):
    return smooth_poly(resample(np.asarray(poly, float), step), k)


def _lobes(n, r_valley, r_lobe, half_deg, a0, step_deg=3.0):
    """Outline of a hub's bolt flange: n lobes of radius r_lobe at a0 + k 360 / n on a circle r_valley."""
    a = np.radians(np.arange(0, 360, step_deg))
    d = (a - a0 + math.pi / n) % (2 * math.pi / n) - math.pi / n
    w = np.where(abs(d) < math.radians(half_deg), 0.5 * (1 + np.cos(math.pi * d / math.radians(half_deg))), 0.0)
    return _pol(r_valley + (r_lobe - r_valley) * w, a)


def _at(mesh, c):
    return mesh.transform(None, c)


# ---------------------------------------------------------------- tyres
class Section:
    """Half cross-section of a carcass, (y, r) by arc length t from the crown centre down to the bead."""

    def __init__(self, spec, ctrl):
        from scipy.interpolate import CubicSpline
        rc = spec["R"] - spec["knob"]
        rb, hw, hf = spec["rb"], spec["hw"], spec["hf"]
        c = [(y, rc + dr) for y, dr in ctrl]
        c += [(hw + 0.0085, rb + 0.017), (hw + 0.0035, rb + hf + 0.0006), (hw, rb + 0.006), (hw - 0.0008, rb)]
        c = np.array(c)
        s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))])
        P = CubicSpline(s, c, bc_type=((1, (1.0, 0.0)), (2, (0.0, 0.0))))(np.linspace(0, s[-1], 600))
        self.P = P
        self.t = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        d = np.gradient(P, axis=0)
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        self.N = np.stack([-d[:, 1], d[:, 0]], axis=1)           # outward normal (y, r)
        self.length = float(self.t[-1])

    def at(self, t, h=0.0):
        """(y, r) at arc length t (t < 0: the other side of the crown), lifted h along the surface normal."""
        a = abs(t)
        y = np.interp(a, self.t, self.P[:, 0]) + h * np.interp(a, self.t, self.N[:, 0])
        r = np.interp(a, self.t, self.P[:, 1]) + h * np.interp(a, self.t, self.N[:, 1])
        return (y if t >= 0 else -y), r

    def lift(self, t, h, lean):
        """(y, r) arrays: the carcass at arc lengths t (>= 0) lifted h along a direction between the radial one
        (lean 0: walls in the wheel's radial plane) and the surface normal (lean 1). Knobs are moulded leaning out
        less than the carcass turns: the shoulder knobs nearly along the normal, the inner ones nearer radial."""
        t = np.asarray(t, float)
        ny, nr = np.interp(t, self.t, self.N[:, 0]), np.interp(t, self.t, self.N[:, 1])
        dy, dr = lean * ny, lean * nr + (1 - lean)
        k = np.hypot(dy, dr)
        return (np.interp(t, self.t, self.P[:, 0]) + h * dy / k, np.interp(t, self.t, self.P[:, 1]) + h * dr / k)


def tyre(spec, ctrl, rows, phase0=0.0, per=8):
    """Knobby tyre as one mesh. The carcass is a grid: PER columns per knob pitch round the wheel, and section
    samples that include every block's edges. Each tread block is raised from the grid cells under it, its walls
    starting on the carcass's own vertices (nothing sunk in, nothing loose), its top standing on the carcass normal:
    L long, inset 1.4 mm, the outer end leading by SKEW."""
    sec = Section(spec, ctrl)
    n = spec["pitches"]
    na = per * n
    edges = sorted({round(t, 5) for row in rows for t in row[1:3]})
    end = max(edges) + 0.004
    ts = {0.0} | set(edges)
    for t in list(np.linspace(0.0, end, int(end / 0.0045) + 1)) + list(np.linspace(end, sec.length, 8)[1:]):
        if all(abs(t - e) > 0.0018 for e in edges):
            ts.add(round(float(t), 5))
    ts = sorted(ts)
    T = ts[::-1] + [-t for t in ts[1:]]                          # +y bead, crown, -y bead
    col = {t: j for j, t in enumerate(T)}
    a0 = 2 * math.pi * phase0 / n
    ang = a0 + 2 * math.pi * np.arange(na) / na
    C = np.empty((len(T), na, 3))
    for j, t in enumerate(T):
        y, r = sec.at(t)
        C[j] = np.stack([r * np.cos(ang), np.full(na, y), r * np.sin(ang)], axis=1)
    m = Mesh()
    m.verts(C.reshape(-1, 3))
    raised = set()
    blocks = []
    for k in range(n):
        for phase, t0, t1, length, h0, h1, skew in rows:
            r_mid = sec.at(0.5 * (t0 + t1))[1]
            ni = max(2, int(round((length + 0.0044) / (2 * math.pi * r_mid / na))))
            i0 = int(round((k + phase) * per - ni / 2))
            ac = a0 + 2 * math.pi * (i0 + ni / 2) / na
            for side in (1, -1):
                j0, j1 = (col[t1], col[t0]) if side > 0 else (col[-t0], col[-t1])
                top = np.empty((j1 - j0 + 1, ni + 1, 3))
                for jj in range(j1 - j0 + 1):
                    v = (abs(T[j0 + jj]) - t0) / (t1 - t0)
                    y, r = sec.at(side * (t0 + 0.0014 + v * (t1 - t0 - 0.0028)), h0 + v * (h1 - h0))
                    aa = ac + skew * (v - 0.5) / r + (np.arange(ni + 1) / ni - 0.5) * length / r
                    top[jj] = np.stack([r * np.cos(aa), np.full(ni + 1, y), r * np.sin(aa)], axis=1)
                raised |= {((i0 + ii) % na, j) for ii in range(ni) for j in range(j0, j1)}
                blocks.append((i0, ni, j0, j1, top))
    for j in range(len(T) - 1):
        for i in range(na):
            if (i, j) not in raised:
                i2 = (i + 1) % na
                m.face((j * na + i, j * na + i2, (j + 1) * na + i2, (j + 1) * na + i), "rubber")
    for i0, ni, j0, j1, top in blocks:
        nj = j1 - j0
        o = m.verts(top.reshape(-1, 3))
        base = lambda ii, jj: (j0 + jj) * na + (i0 + ii) % na
        tp = lambda ii, jj: o + jj * (ni + 1) + ii
        pos = lambda idx: top.reshape(-1, 3)[idx - o] if idx >= o else C.reshape(-1, 3)[idx]
        centre = 0.5 * (top.mean(axis=(0, 1)) + C[j0:j1 + 1, [(i0 + ii) % na for ii in range(ni + 1)]].mean(axis=(0, 1)))
        faces = [(tp(ii, jj), tp(ii + 1, jj), tp(ii + 1, jj + 1), tp(ii, jj + 1)) for ii in range(ni) for jj in range(nj)]
        for ii in range(ni):
            for jj in (0, nj):
                faces.append((base(ii, jj), base(ii + 1, jj), tp(ii + 1, jj), tp(ii, jj)))
        for jj in range(nj):
            for ii in (0, ni):
                faces.append((base(ii, jj), base(ii, jj + 1), tp(ii, jj + 1), tp(ii, jj)))
        for f in faces:
            P = np.array([pos(i) for i in f])
            if np.cross(P[1] - P[0], P[2] - P[0]) @ (P.mean(axis=0) - centre) < 0:
                f = f[::-1]
            m.face(f, "rubber")
    return m, na, a0, len(T)


# ---------------------------------------------------------------- tread blocks (shaped knobs on a whole carcass)
# A knob is built in its own plan coordinates: s along the tread in the direction of travel (+ = the leading edge,
# the one that meets the ground first), t across = arc length of the carcass section from the crown centre line
# (always >= 0 in the plan; the -y side is mirrored), z = height above the carcass. Walls have a moulding draft,
# the plan's corners are rounded, the top edge has a quarter-round, the foot a small flare (the fillet at the
# root) sunk 0.8 mm into the carcass, which is a whole grid under every knob (nothing hangs, nothing has holes).
def _fillet(poly, r, n=3):
    """Round the corners of a closed polygon with radius about R (quadratic arcs, N points each)."""
    P = np.asarray(poly, float)
    out = []
    for i in range(len(P)):
        a, b, c = P[i - 1], P[i], P[(i + 1) % len(P)]
        u, v = a - b, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        u, v = u / lu, v / lv
        ang = math.acos(float(np.clip(u @ v, -1, 1)))
        d = min(r / max(math.tan(ang / 2), 1e-3), 0.45 * lu, 0.45 * lv)
        p0, p1 = b + u * d, b + v * d
        for w in np.linspace(0, 1, n):
            out.append((1 - w) ** 2 * p0 + 2 * (1 - w) * w * b + w ** 2 * p1)
    return np.array(out)


def _mitre(poly, d):
    """Offset a closed counter-clockwise polygon by D (scalar or per vertex; > 0 outward), mitred corners."""
    P = np.asarray(poly, float)
    e = np.roll(P, -1, 0) - P
    e /= np.linalg.norm(e, axis=1, keepdims=True)
    n = np.stack([e[:, 1], -e[:, 0]], axis=1)                    # outward normal of the edge i -> i + 1
    m = n + np.roll(n, 1, 0)
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    k = 1.0 / np.clip((m * n).sum(axis=1), 0.45, None)
    return P + np.asarray(d, float).reshape(-1, 1) * m * k[:, None]


def _cap(loop, step):
    """Triangles over a simple closed loop (its points first) with an interior grid, for knob tops."""
    from scipy.spatial import Delaunay, cKDTree
    loop = np.asarray(loop, float)
    lo, hi = loop.min(axis=0), loop.max(axis=0)
    gx, gz = np.meshgrid(np.arange(lo[0] + step / 2, hi[0], step), np.arange(lo[1] + step / 2, hi[1], step))
    G = np.stack([gx.ravel(), gz.ravel()], axis=1)
    G = G[inside(loop, G)] if len(G) else G
    if len(G):
        G = G[cKDTree(loop).query(G)[0] > 0.55 * step]
    P = np.vstack([loop, G])
    tri = Delaunay(P).simplices
    tri = tri[inside(loop, P[tri].mean(axis=1))]
    a, b, c = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    tri = tri[abs(area) > 1e-12]
    area = area[abs(area) > 1e-12]
    tri[area < 0] = tri[area < 0][:, ::-1]
    return P, tri


class Knob:
    """Maps a knob's plan (s, t, z) to the wheel frame: centred at wheel angle A, on side SIDE (+1: +y), leaning
    LEAN (Section.lift). The wheel turns forward: seen from +y the top moves to +x, so the leading edge is at the
    smaller angle."""

    def __init__(self, sec, a, side, lean):
        self.sec, self.a, self.side, self.lean = sec, a, side, lean

    def __call__(self, s, t, z):
        s, t, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(t, float), np.asarray(z, float))
        y, r = self.sec.lift(t, z, self.lean)
        rc = np.interp(t, self.sec.t, self.sec.P[:, 1])
        ang = self.a - s / rc
        return np.stack([r * np.cos(ang), self.side * y, r * np.sin(ang)], axis=-1)


ROUND = 0.0009          # EST top edge quarter-round of a moulded knob (0.5 to 1 mm, MICRO.md)
FLARE = 0.0010          # EST root fillet seen as a flare at the foot


def _knob(m, xf, plan, h_of, draft, mat="rubber", base=None, top=True, wall_mat=None, top_mat=None, step=0.0032):
    """One knob: PLAN (s, t) counter-clockwise at the root; H_OF(s, t) its height. BASE: start the walls at this
    height (no root flare; a knob stacked on another one); TOP False: a flat top without the round (a floor seen
    only in a slit). WALL_MAT(i): material of the wall from plan vertex i to i + 1 (below the round). Returns the
    top's boundary in 3D and in plan (for spews)."""
    plan = _ccw(plan)
    h = np.array([h_of(s, t) for s, t in plan])
    td = math.tan(draft)
    if base is None:
        lv = [(np.full(len(h), -0.0008), FLARE), (np.zeros(len(h)), 0.5 * FLARE), (np.full(len(h), 0.0015), None)]
    else:
        lv = [(np.full(len(h), base), None)]
    if top:
        lv += [(h - ROUND, None), (h - 0.293 * ROUND, -0.293 * ROUND), (h, -ROUND)]
    else:
        lv += [(h, None)]
    rings = []
    for z, extra in lv:
        off = -np.maximum(z, 0.0) * td + (0.0 if extra is None else extra)
        Q = _mitre(plan, off)
        rings.append((Q, z))
    o = len(m.V)
    for Q, z in rings:
        m.verts(xf(Q[:, 0], Q[:, 1], z))
    n = len(plan)
    faces = []
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            mat_i = wall_mat(i) if (wall_mat and k < len(rings) - (3 if top else 1)) else mat
            faces.append(((o + k * n + i, o + k * n + j, o + (k + 1) * n + j, o + (k + 1) * n + i), mat_i))
    Qt, zt = rings[-1]
    P2, tri = _cap(Qt, step)
    extra_pts = P2[n:]
    ot = o + (len(rings) - 1) * n
    oe = m.verts(xf(extra_pts[:, 0], extra_pts[:, 1], [h_of(s, t) for s, t in extra_pts])) if len(extra_pts) else 0
    for tr in tri:
        faces.append((tuple(ot + i if i < n else oe + i - n for i in tr), top_mat or mat))
    # winding: the top faces the way the knob stands (from the carcass out)
    tr0 = faces[-1][0]
    A, B, C = (np.asarray(m.V[i]) for i in tr0)
    s0, t0 = P2[tri[-1]].mean(axis=0)
    up = xf(s0, t0, float(h_of(s0, t0)) + 0.001) - xf(s0, t0, float(h_of(s0, t0)))
    flip = np.cross(B - A, C - A) @ up < 0
    for f, mt in faces:
        m.face(f[::-1] if flip else f, mt)
    return xf(Qt[:, 0], Qt[:, 1], zt), Qt


def _spew(m, p, d, length, rng):
    """A mould vent hair: rubber whisker 0.45 mm thick, LENGTH long, from P along D, slightly bent."""
    d = d / np.linalg.norm(d)
    side = np.cross(d, rng.normal(size=3))
    side /= np.linalg.norm(side)
    path = [p - d * 0.0004, p + d * length * 0.5 + side * length * 0.06, p + d * length]
    m.add(tube(path, [0.00024, 0.00022, 0.00016], 3, "tyre_spew"))


# ---------------------------------------------------------------- rims, spokes, valve, rim lock
def rim_profile(spec):
    """Closed section (r, y) of the rim: well, bead seats, flanges with rolled lips (D.I.D DirtStar, WM contour)."""
    rb, hw, hf, ri = spec["rb"], spec["hw"], spec["hf"], spec["r_in"]
    lip = 0.0045                                                 # EST flange lip thickness
    half = [(ri, 0.0), (ri, 0.45 * hw), (ri + 0.0035, 0.80 * hw), (rb - 0.004, hw + lip - 0.0012),
            (rb + hf - 0.0025, hw + lip), (rb + hf - 0.0006, hw + lip - 0.0008), (rb + hf, hw + lip / 2),
            (rb + hf - 0.0008, hw + 0.0006), (rb + hf - 0.003, hw), (rb, hw), (rb - 0.0006, 0.60 * hw),
            (ri + 0.0050, 0.40 * hw), (ri + 0.0035, 0.20 * hw)]
    return half + [(ri + 0.0035, 0.0)] + [(r, -y) for r, y in half[:0:-1]]


def spoke_lines(spec, r_hub, y_left, y_right, flange_t=0.006, phase=0.0):
    """36 spokes laced three-cross: 18 per flange, alternately on the outer and the inner face of the flange, each to
    the rim hole 60 deg on (leading) or back (trailing). Returns (hub point, rim point, flange y, face sign)."""
    out = []
    per = SPOKES // 2
    for s, yf in ((1, y_left), (-1, y_right)):
        for i in range(per):
            ah = phase + 2 * math.pi * (i + (0.0 if s > 0 else 0.5)) / per
            ar = ah + (1 if i % 2 == 0 else -1) * math.pi / 3
            e = s * (1 if i % 2 == 0 else -1)                    # which face of the flange the spoke lies on
            p0 = np.array([r_hub * math.cos(ah), yf + e * (flange_t / 2 + SPOKE_R), r_hub * math.sin(ah)])
            p1 = np.array([spec["r_in"] * math.cos(ar), s * 0.004, spec["r_in"] * math.sin(ar)])
            out.append((p0, p1, yf, e))
    return out


def _rim(m, spec, na, a0, n_t):
    """Rim on the tyre's own columns (M holds the tyre, its bead rings first and last): the beads are joined to the
    rim's seats by a hidden strip, so tyre and rim are one mesh. Returns the rim's first vertex."""
    prof = rim_profile(spec)
    ang = a0 + 2 * math.pi * np.arange(na) / na
    off = len(m.V)
    for r, y in prof:
        m.verts(np.stack([r * np.cos(ang), np.full(na, y), r * np.sin(ang)], axis=1))
    for p in range(len(prof)):
        p2 = (p + 1) % len(prof)
        for i in range(na):
            i2 = (i + 1) % na
            m.face((off + p * na + i, off + p * na + i2, off + p2 * na + i2, off + p2 * na + i), "rim")
    for ring_t, ring_r in ((0, 9), (n_t - 1, 17)):               # profile points 9 and 17: the two bead seats
        for i in range(na):
            i2 = (i + 1) % na
            m.face((ring_t * na + i, ring_t * na + i2, off + ring_r * na + i2, off + ring_r * na + i), "rubber")
    return off


def _hub(m, prof, mats, phase, seg=72):
    """Hub, seals and collars as one lathe (72 columns from PHASE: a vertex at every spoke hole)."""
    off = len(m.V)
    a = phase + 2 * math.pi * np.arange(seg) / seg
    grid(m, [np.stack([r * np.cos(a), np.full(seg, y), r * np.sin(a)], axis=1) for r, y in prof], "hub", mats=mats)
    return off


def _spokes(m, spec, r_hub, y_left, y_right, phase, flange_t=0.006):
    """Each spoke is one piece: head, elbow through the flange, spoke, nipple (flats, then the seat 3 mm into the
    rim's wall)."""
    for p0, p1, yf, e in spoke_lines(spec, r_hub, y_left, y_right, flange_t, phase):
        dn = (p1 - p0) / np.linalg.norm(p1 - p0)
        ey = np.array([0.0, e, 0.0])
        q = np.array([p0[0], yf - e * flange_t / 2, p0[2]])
        path = [q - 0.0018 * ey, q - 0.00005 * ey, q, p0, p1 - dn * 0.0151, p1 - dn * 0.0150, p1 - dn * 0.0050,
                p1 - dn * 0.0049, p1 + dn * 0.003]
        m.add(tube(path, [0.0034, 0.0034, SPOKE_R, SPOKE_R, SPOKE_R, 0.0031, 0.0031, 0.0040, 0.0040], 6, "spoke"))


def _stem(m, spec, ang, lock):
    """Valve stem with its nut and cap, or a rim lock's stud with washer and nut, through the rim well toward the hub."""
    e = np.array([math.cos(ang), 0.0, math.sin(ang)])
    if lock:
        d = [0.003, 0.0005, 0.00045, -0.002, -0.00205, -0.009, -0.00905, -0.017]
        rad = [0.004, 0.004, 0.011, 0.011, 0.0075, 0.0075, 0.004, 0.004]
    else:
        d = [0.003, 0.0005, 0.00045, -0.004, -0.00405, -0.024, -0.02405, -0.034]
        rad = [0.0042, 0.0042, 0.007, 0.007, 0.0042, 0.0042, 0.0048, 0.0048]
    m.add(tube([e * (spec["r_in"] + x) for x in d], rad, 8, "steel"))


# ---------------------------------------------------------------- discs
def front_disc_r(a):
    """Outer radius of the front disc: 18 scallops, alternately deep and shallow (RIGHT polar scan at r 126 mm:
    runs 9..14 deg wide every 40 deg, short runs half way between them)."""
    s = (np.asarray(a, float) - DISC_F_DEEP) * 18 / (2 * math.pi)
    k = np.round(s)
    depth = np.where(k % 2 == 0, 0.0085, 0.0050)
    return DISC_F["r"] - depth * np.clip(1 - ((s - k) / 0.42) ** 2, 0, None) ** 1.5


def front_disc():
    a = np.radians(np.arange(0, 360, 1.25))
    holes = [circle(0.042, 48)] + _pilots(DISC_F_BOLT_R, DISC_F_DEEP + math.pi / 6, 6)
    for k in range(6):                                           # six swept windows between six arms (RIGHT crop;
        aw = DISC_F_DEEP + k * math.pi / 3                       # their exact outline is hidden by the spokes: EST)
        lo = [(0.068, aw + math.radians(d - 6)) for d in np.linspace(-21, 21, 9)]
        hi = [(0.100, aw + math.radians(d + 6)) for d in np.linspace(23, -23, 9)]
        holes.append(_round([_pol(r, t) for r, t in lo + hi]))
    for k in range(18):                                          # one hole in each lobe, one under each scallop
        a1 = DISC_F_DEEP + (k + 0.5) * math.pi / 9
        a2 = DISC_F_DEEP + k * math.pi / 9
        holes.append(circle(0.00325, 8, *_pol(0.1185, a1)))
        holes.append(circle(0.00275, 8, *_pol(0.1095, a2)))
    m = _plate(_pol(front_disc_r(a), a), holes, DISC_F["y"], DISC_F["t"], "disc", 0.007)
    for k in range(6):
        x, z = _pol(DISC_F_BOLT_R, DISC_F_DEEP + (k + 0.5) * math.pi / 3)
        m.add(bolt((x, DISC_F["y"] + DISC_F["t"] / 2, z), (0, 1, 0), af=0.010, head_h=0.0045, flange_d=0.014,
                   mat="steel"))
    return m


def rear_disc_r(a):
    """Outer radius of the rear disc: four wide scallops over the four bolts and 28 small ones (RIGHT polar scan:
    edge harmonics 4 and 28; at r 110 the wide ones are 19 deg wide, at r 115 28 deg)."""
    a = np.asarray(a, float)
    r = DISC_R["r"] - 0.0015 * (1 - np.cos(28 * (a - DISC_R_FLAT)))
    for k in range(4):
        d = (a - DISC_R_FLAT - k * math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
        r = r - 0.0150 * np.exp(-(d / math.radians(12.0)) ** 2)
    return r


def rear_disc_r_in(a):
    """Inner edge: a rounded square, flats at the four bolts (RIGHT crop; white fraction 0 at r 86 mm)."""
    d = (np.asarray(a, float) - DISC_R_FLAT + math.pi / 4) % (math.pi / 2) - math.pi / 4
    return np.minimum(0.088, 0.064 / np.cos(d))


def rear_disc():
    a = np.radians(np.arange(0, 360, 1.25))
    ai = np.radians(np.arange(0, 360, 3.0))
    holes = [_pol(rear_disc_r_in(ai), ai)] + _pilots(DISC_R_BOLT_R, DISC_R_FLAT, 4)
    for j in range(28):                                          # RIGHT scan: holes at r 94, 103 and 111 mm
        for r, da in ((0.1115, 0.0), (0.1030, 4.3), (0.0945, 8.6)):
            ah = DISC_R_FLAT + j * 2 * math.pi / 28 + math.radians(da)
            if rear_disc_r(ah) - r > 0.0065 and r - rear_disc_r_in(ah) > 0.0065:
                holes.append(circle(0.003, 8, *_pol(r, ah)))
    m = _plate(_pol(rear_disc_r(a), a), holes, DISC_R["y"], DISC_R["t"], "disc", 0.007)
    for k in range(4):
        x, z = _pol(DISC_R_BOLT_R, DISC_R_FLAT + k * math.pi / 2)
        m.add(bolt((x, DISC_R["y"] - DISC_R["t"] / 2, z), (0, -1, 0), af=0.010, head_h=0.005, flange_d=0.015,
                   mat="steel"))
    return m


# ---------------------------------------------------------------- sprockets and chain
def sprocket_outline(n, phase):
    """Tooth outline (x, z) of an n-tooth #520 sprocket: a roller seat on the pitch circle at phase + k 360 / n,
    flanks leaving the seat 20 deg off the radius, tips TIP_H above the pitch circle."""
    rp = sprocket_r(n)
    pts = []
    for k in range(n):
        phi = phase + 2 * math.pi * k / n
        er = np.array([math.cos(phi), math.sin(phi)])
        et = np.array([-er[1], er[0]])
        for al in np.radians(np.linspace(-70, 70, 9)):
            pts.append(rp * er + SEAT_R * (-math.cos(al) * er + math.sin(al) * et))
        for da in (-0.001, 0.001):
            pts.append(_pol(rp + TIP_H, phi + math.pi / n + da / (rp + TIP_H)))
    return np.array(pts)


def rear_sprocket(phase):
    """50 teeth, aluminium. LEFT photo: six bolts, between them windows with a rounded top (polar scan: 31 deg wide
    at r 88, 25 at r 96, closed by r 106) and three 7 mm holes at r 73; a slot outside every bolt (r 102..113)."""
    holes = [circle(SPROCKET_BORE_R, 72)] + _pilots(SPROCKET_BOLT_R, SPROCKET_BOLT0, 6)
    for k in range(6):
        ab = SPROCKET_BOLT0 + k * math.pi / 3
        am = ab + math.pi / 6
        win = [(0.080, d) for d in np.linspace(-15.5, 15.5, 9)]
        win += [(0.088, 15.5), (0.096, 12.5), (0.102, 7.0), (0.1055, 2.0), (0.1055, -2.0), (0.102, -7.0),
                (0.096, -12.5), (0.088, -15.5)]
        holes.append(_round([_pol(r, am + math.radians(d)) for r, d in win]))
        holes.append(resample(slot(_pol(0.106, ab), ab + math.pi / 2, 0.026, 0.009), 0.0035))
        for d in (-10.5, 0.0, 10.5):
            holes.append(circle(0.0035, 10, *_pol(0.073, am + math.radians(d))))
    return _plate(sprocket_outline(50, phase), holes, CHAIN_Y, SPROCKET_T, "sprocket", 0.006)


BOTTOM_RUN = ((0.604, 0.428), (0.171, 0.270))       # LEFT: the bottom run is straight between these two points
GUIDE_PT = BOTTOM_RUN[1]                            # its rear end, at the chain guide
LOWER_ROLLER = (0.522, 0.375)       # LEFT pixel (2297, 1557) cast on the chain's plane: the frame's lower roller
                                    # (detail_chassis.py), just under the bottom run


@functools.lru_cache(maxsize=None)
def chain_path():
    """Pin centres (x, z) of the #520 chain along the path the LEFT photo shows: round the 50-tooth sprocket, the
    top run along parts.chain_top (over the swingarm's slider), round the 13-tooth sprocket, onto the bottom run's
    straight (BOTTOM_RUN: it passes 3.7 mm inside the 13T's pitch circle, so the chain reaches its front end by
    the tangent from there) and from GUIDE_PT onto the 50-tooth sprocket. Pins on the sprockets sit in the tooth seats, exactly one
    pitch apart. The loop is 112.9 pitches long and a chain has an even number of links: 112, the links of the two
    free runs made longer by the same STRETCH to close it (the 13T's seats are turned so that both runs come out
    whole). The chain meets and leaves both sprockets from outside (first seat at or before the tangent point).
    Returns pins, both sprockets' seat phases, the bottom-run pins and STRETCH."""
    c1, c2 = np.array([CS[0], CS[2]]), np.array([RA[0], RA[2]])
    rf, rr = sprocket_r(13), sprocket_r(50)
    p1, g = np.array(BOTTOM_RUN[0]), np.array(BOTTOM_RUN[1])
    dr, df = 2 * math.pi / 50, 2 * math.pi / 13
    th_a = math.atan2(1.0, -float(chain_top(0.30) - chain_top(0.20)) / 0.10)          # the top run leaves the 50T
    th_arr = math.atan2(1.0, -float(chain_top(CS[0] - 0.010) - chain_top(CS[0] - 0.020)) / 0.010)     # meets the 13T

    def low(c, r, q):                                            # where the tangent from Q touches, underneath
        d = q - c
        phi, al = math.atan2(d[1], d[0]), math.acos(r / float(np.linalg.norm(d)))
        return min((phi + al, phi - al), key=math.sin)

    def on_r(th):
        return c2 + rr * np.array([math.cos(th), math.sin(th)])

    def on_f(th):
        return c1 + rf * np.array([math.cos(th), math.sin(th)])

    def length(P):
        return float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())

    kr = math.ceil(((low(c2, rr, g) - th_a) % (2 * math.pi)) / dr - 1e-9)                # 50T seats in use: 0 .. kr
    wrap_f = (th_arr - low(c1, rf, p1)) % (2 * math.pi)

    def lay(delta, kf):
        th_f = low(c1, rf, p1) - delta                               # the 13T's last seated pin, DELTA past the tangent
        a, b = on_r(th_a), on_f(th_f + kf * df)
        xs = np.linspace(a[0] + 0.10, b[0] - 0.010, 80)
        return (np.vstack([a, np.stack([xs, chain_top(xs)], axis=1), b]),
                np.vstack([on_f(th_f), p1, g, on_r(th_a + kr * dr)]), th_f + kf * df)

    best = None
    for kf in (math.ceil(wrap_f / df), math.ceil(wrap_f / df) - 1):
        for n_top in range(38, 44):
            for n_bot in range(36, 42):
                if (n_top + n_bot + kf + kr) % 2:
                    continue

                def uneven(dl):
                    top, bot, _ = lay(dl, kf)
                    return length(top) / n_top - length(bot) / n_bot

                lo, hi = -0.35, 0.9
                if uneven(lo) * uneven(hi) > 0:
                    continue
                for _ in range(45):
                    mid = 0.5 * (lo + hi)
                    if uneven(mid) < 0:
                        lo = mid
                    else:
                        hi = mid
                delta = 0.5 * (lo + hi)
                link = length(lay(delta, kf)[0]) / n_top
                clean = -0.02 <= delta <= kf * df - wrap_f + 0.02
                cand = (not clean, abs(link / P520 - 1), link / P520 - 1, delta, kf, n_top, n_bot)
                if best is None or cand < best:
                    best = cand
    _, _, stretch, delta, kf, n_top, n_bot = best
    top, bot, th_b = lay(delta, kf)

    def spaced(P, n):
        d = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        w = np.linspace(0, d[-1], n + 1)
        return np.stack([np.interp(w, d, P[:, 0]), np.interp(w, d, P[:, 1])], axis=1)

    top_p, bot_p = spaced(top, n_top), spaced(bot, n_bot)
    pins = list(top_p) + [on_f(th_b - k * df) for k in range(1, kf + 1)] + list(bot_p[1:])
    pins += [on_r(th_a + k * dr) for k in range(kr - 1, 0, -1)]
    return np.array(pins), th_a, th_b, bot_p, stretch


CHAIN_LEVELS = (-0.0087, -0.00725, -0.00525, -0.005175, -0.003175, -0.0031, 0.0031, 0.003175, 0.005175, 0.00525,
                0.00725, 0.0087)                                # SPEC #520: pin ends, outer and inner plates, roller
PIN_R = 0.0026                                                  # SPEC #520 pin 5.2 mm


def _chain(m, pins, y):
    """The chain as one connected mesh: every pin is a spool (riveted pin with its roller), and every plate's faces
    are meshed round the pins' own vertices, so the links hang together as on the real chain."""
    from scipy.spatial import Delaunay
    n = len(pins)
    a = np.linspace(0, 2 * math.pi, 8, endpoint=False)
    cs, sn = np.cos(a), np.sin(a)
    ring = {}
    for k, (x, z) in enumerate(pins):
        for li, dy in enumerate(CHAIN_LEVELS):
            r = ROLLER_R if li in (5, 6) else PIN_R
            ring[k, li] = m.verts(np.stack([x + r * cs, np.full(8, y + dy), z + r * sn], axis=1))
        for li in range(len(CHAIN_LEVELS) - 1):
            lo, hi = ring[k, li], ring[k, li + 1]
            for j in range(8):
                j2 = (j + 1) % 8
                m.face((lo + j, hi + j, hi + j2, lo + j2), "steel")
        c0, c1 = m.verts([(x, y + CHAIN_LEVELS[0], z)]), m.verts([(x, y + CHAIN_LEVELS[-1], z)])
        for j in range(8):
            j2 = (j + 1) % 8
            m.face((ring[k, 0] + j, ring[k, 0] + j2, c0), "steel")
            m.face((ring[k, 11] + j2, ring[k, 11] + j, c1), "steel")
    for k in range(n):
        k2 = (k + 1) % n
        p, q = pins[k], pins[k2]
        d = q - p
        length = float(np.linalg.norm(d))
        ex = d / length
        ez = np.array([-ex[1], ex[0]])
        hr = 0.0073 if k % 2 == 0 else 0.0065                   # inner plates are the taller ones
        loc = [(length / 2 + hr * math.cos(t), hr * math.sin(t)) for t in np.radians((-90, -45, 0, 45, 90))]
        loc.append((0.0, 0.80 * hr))
        loc += [(-length / 2 + hr * math.cos(t), hr * math.sin(t)) for t in np.radians((90, 135, 180, 225, 270))]
        loc.append((0.0, -0.80 * hr))
        loc = np.array(loc)
        out = (p + q) / 2 + loc[:, :1] * ex + loc[:, 1:] * ez
        pts = np.vstack([out, p + PIN_R * np.stack([cs, sn], axis=1), q + PIN_R * np.stack([cs, sn], axis=1)])
        tri = Delaunay(pts).simplices
        keep = inside(out, pts[tri].mean(axis=1)) & ~np.all((tri >= 12) & (tri < 20), axis=1) & ~np.all(tri >= 20, axis=1)
        tri = tri[keep]
        u, v, w = pts[tri[:, 0]], pts[tri[:, 1]], pts[tri[:, 2]]
        flip = (v[:, 0] - u[:, 0]) * (w[:, 1] - u[:, 1]) - (v[:, 1] - u[:, 1]) * (w[:, 0] - u[:, 0]) < 0
        tri[flip] = tri[flip][:, ::-1]                           # counter-clockwise in (x, z): facing -y
        for la, lb in (((3, 4), (7, 8)) if k % 2 == 0 else ((1, 2), (9, 10))):
            idx = []
            for lev in (la, lb):
                o = m.verts([(x, y + CHAIN_LEVELS[lev], z) for x, z in out])
                idx.append(lambda i, o=o, lev=lev: o + i if i < 12 else (ring[k, lev] + i - 12 if i < 20 else ring[k2, lev] + i - 20))
            for t in tri:
                m.face([idx[0](i) for i in t], "chain")
                m.face([idx[1](i) for i in t[::-1]], "chain")
            for i in range(12):
                i2 = (i + 1) % 12
                m.face((idx[0](i), idx[1](i), idx[1](i2), idx[0](i2)), "chain")


def _chain_roller(m, x, z, r, w=0.024, boss=0.012):
    """Rubber chain roller on the frame's left side, with its collar toward the frame and its flange bolt."""
    y = CHAIN_Y
    m.add(_at(lathe([(0.006, w / 2), (r - 0.003, w / 2), (r, w / 2 - 0.003), (r, -w / 2 + 0.003), (r - 0.003, -w / 2),
                     (0.006, -w / 2)], 24, "rubber_black"), (x, y, z)))
    m.add(tube([(x, y - w / 2 - boss, z), (x, y - w / 2, z)], 0.008, 20, "alu_cast"))
    m.add(tube([(x, y - w / 2, z), (x, y + w / 2, z)], 0.0062, 12, "steel", cap0=False))
    m.add(bolt((x, y + w / 2, z), (0, 1, 0), af=0.012, head_h=0.006, flange_d=0.020, mat="steel"))


def drive():
    """#520 chain of real links (inner and outer plates, rollers, riveted pins; SPEC sizes), the 13-tooth
    countershaft sprocket with washer and bolt, and the two chain rollers on the frame."""
    m = Mesh()
    pins, _, th_b, bottom, _ = chain_path()
    y = CHAIN_Y
    _chain(m, pins, y)
    c = (CS[0], 0.0, CS[2])
    m.add(_plate(sprocket_outline(13, th_b), [circle(0.0103, 24)], y, SPROCKET_T, "steel", 0.006, (CS[0], CS[2])))
    m.add(_at(_ring(0.0103, 0.0185, y - 0.0085, y - SPROCKET_T / 2, "steel", 24), c))       # sprocket's shoulder
    m.add(tube([(CS[0], y - 0.0085, CS[2]), (CS[0], y + 0.0045, CS[2])], 0.0104, 16, "steel"))   # shaft end
    m.add(_at(_ring(0.0045, 0.0145, y + 0.0045, y + 0.0070, "steel", 24), c))               # washer
    m.add(bolt((CS[0], y + 0.0070, CS[2]), (0, 1, 0), af=0.012, head_h=0.006, mat="steel"))
    # The lower chain roller (LEFT pixel (2297, 1557): LOWER_ROLLER, just under the bottom run) is part of the frame
    # in detail_chassis.py, on its bracket; a second one here would stand in the same place. The upper roller is
    # this module's: EST, clear above the top run behind the pivot.
    xu = 0.455
    _chain_roller(m, xu, float(chain_top(xu)) + 0.0073 + 0.017 + 0.005, 0.017)
    return m


# ---------------------------------------------------------------- wheels
def _flange(rh, yf):
    return [(rh - 0.008, yf + 0.003), (rh, yf + 0.003), (rh + 0.006, yf + 0.003), (rh + 0.006, yf - 0.003),
            (rh, yf - 0.003), (rh - 0.008, yf - 0.003)]


def _wheel(spec, ctrl, rows, tread_phase, prof, mats, rh, yl, yr, spoke0, stems):
    """Tyre and rim (one mesh: the beads sit on the rim's seats), hub with seals and collars, spokes, valve, rim lock."""
    m, na, a0, n_t = tyre(spec, ctrl, rows, tread_phase)
    _rim(m, spec, na, a0, n_t)
    _hub(m, prof, mats, spoke0)
    _spokes(m, spec, rh, yl, yr, spoke0)
    for ang, lock in stems:
        _stem(m, spec, math.radians(ang), lock)
    return m


def front_wheel():
    """Front wheel about the front axle. Hub EST (hidden by the disc guard and the fork lugs in every photo): 36-hole
    flanges on the fitted hole circle, six-lug disc flange, seals and collars; disc on the left."""
    yl, yr, rh = 0.0305, -0.0365, FRONT_HUB_R
    yc = DISC_F["y"] - DISC_F["t"] / 2 - 0.006                   # the disc flange: 6 mm, behind the disc
    prof = [(0.0104, 0.0725), (0.0155, 0.0725), (0.0155, 0.0668), (0.022, 0.0668), (0.022, 0.066), (0.024, 0.066),
            (0.026, 0.064), (0.026, yc), (0.026, 0.046), (0.030, 0.040)] + _flange(rh, yl) + [
            (0.024, 0.016), (0.021, 0.006), (0.021, -0.012), (0.025, -0.026)] + _flange(rh, yr) + [
            (0.028, -0.046), (0.025, -0.050), (0.024, -0.056), (0.022, -0.056), (0.022, -0.0568), (0.0155, -0.0568),
            (0.0155, -0.0705), (0.0104, -0.0705)]                 # collars to +72.5 / -70.5: the fork lugs clamp outside
    mats = ["steel", "steel", "rubber_black", "rubber_black"] + ["hub"] * (len(prof) - 9) + [
        "rubber_black", "rubber_black", "steel", "steel"]
    m = _wheel(FRONT, FRONT_SECTION, FRONT_ROWS, FRONT_PHASE, prof, mats, rh, yl, yr, FRONT_SPOKE0,
               ((245.0, False), (65.0, True)))
    b0 = DISC_F_DEEP + math.pi / 6
    m.add(_plate(_lobes(6, 0.040, 0.063, 20.0, b0), [circle(0.0255, 48)] + _pilots(DISC_F_BOLT_R, b0, 6), yc + 0.003,
                 0.006, "hub", 0.008))
    m.add(front_disc())
    return _at(m, FA)


def rear_wheel():
    """Rear wheel about the rear axle: sprocket on the left on the chain line, disc on the right."""
    ys = CHAIN_Y
    y_end = min(ys + 0.006, ARM_FACE - 0.0011)                   # LEFT: the hub's end shows inside the sprocket;
                                                                 # its seal stops 0.3 mm from the swingarm
    back = ys - SPROCKET_T / 2 - 0.012                           # REAR cols 1895..1915: sprocket nuts 16..29 mm inboard
    yl, yr, rh = min(0.046, ys - 0.046), -0.040, REAR_HUB_R
    if y_end + 0.0008 < ARM_FACE - 0.001:                        # left collar, up to the swingarm's inner face
        prof, mats = [(0.0125, ARM_FACE), (0.0175, ARM_FACE), (0.0175, y_end + 0.0008)], ["steel", "steel"]
    else:
        prof, mats = [(0.0128, y_end + 0.0008)], []
    prof += [(0.024, y_end + 0.0008), (0.024, y_end), (0.028, y_end), (0.031, y_end - 0.003), (0.056, y_end - 0.004),
             (0.0605, y_end - 0.006), (0.0605, back), (0.0605, back - 0.001), (0.050, back - 0.010),
             (0.044, yl + 0.012)] + _flange(rh, yl) + [(0.030, 0.018), (0.029, -0.010), (0.034, -0.030)] + _flange(rh, yr)
    prof += [(0.044, -0.050), (0.056, -0.058), (0.058, -0.060), (0.058, -0.0745), (0.054, -0.077), (0.031, -0.076),
             (0.028, -0.079), (0.024, -0.079), (0.024, -0.0798), (0.0175, -0.0798), (0.0175, -0.0855),
             (0.0125, -0.0855)]                                  # right collar, up to the caliper bracket
    mats += ["rubber_black", "rubber_black"]
    mats += ["hub"] * (len(prof) - 1 - len(mats) - 4) + ["rubber_black", "rubber_black", "steel", "steel"]
    m = _wheel(REAR, REAR_SECTION, REAR_ROWS, REAR_PHASE, prof, mats, rh, yl, yr, REAR_SPOKE0,
               ((115.0, False), (295.0, True)))
    m.add(_plate(_lobes(6, 0.066, 0.0875, 16.0, SPROCKET_BOLT0),
                 [circle(0.059, 72)] + _pilots(SPROCKET_BOLT_R, SPROCKET_BOLT0, 6), back + 0.006, 0.012, "hub", 0.008))
    m.add(rear_sprocket(chain_path()[1]))
    for k in range(6):
        x, z = _pol(SPROCKET_BOLT_R, SPROCKET_BOLT0 + k * math.pi / 3)
        m.add(bolt((x, ys + SPROCKET_T / 2, z), (0, 1, 0), af=0.014, head_h=0.0045, mat="steel", kind="cap"))
        m.add(bolt((x, back, z), (0, -1, 0), af=0.012, head_h=0.008, mat="steel"))
    yd = DISC_R["y"] + DISC_R["t"] / 2
    m.add(_plate(_lobes(4, 0.060, 0.080, 14.0, DISC_R_FLAT), [circle(0.0565, 48)] + _pilots(DISC_R_BOLT_R, DISC_R_FLAT, 4),
                 yd + 0.004, 0.008, "hub", 0.008))
    m.add(rear_disc())
    return _at(m, RA)


# ---------------------------------------------------------------- rear brake
def rear_brake():
    """Rear caliper (single piston, floating; RIGHT and REAR photos for its place, shapes EST), its bracket on the
    axle between the hub collar and the swingarm, pads, slide pins, bleed nipple, banjo and hose."""
    m = Mesh()
    er = np.array([math.cos(CAL_ANG), 0.0, math.sin(CAL_ANG)])
    et = np.array([-math.sin(CAL_ANG), 0.0, math.cos(CAL_ANG)])
    R = np.column_stack([et, [0.0, 1.0, 0.0], er])               # local axes: along the disc, y, radial

    def P(t, y, r):
        return RA + t * et + r * er + np.array([0.0, y, 0.0])

    yb0, yb1 = -ARM_FACE, -0.0858                                # bracket: one plate on the axle, 7.7 mm, with a
    tips = [sg * 0.043 * et + 0.121 * er for sg in (-1, 1)]      # window for the piston housing
    win = 0.106 * er
    m.add(_plate(_hull([(0.0, 0.0, 0.026)] + [(t[0], t[2], 0.012) for t in tips], 24),
                 [circle(0.0135, 20), circle(0.022, 24, win[0], win[2])], (yb0 + yb1) / 2, yb1 - yb0, "alu_cast",
                 0.010, (RA[0], RA[2])))
    for sg in (-1, 1):
        m.add(tube([P(sg * 0.043, yb1, 0.121), P(sg * 0.043, -0.066, 0.121)], 0.005, 10, "steel"))        # slide pin
        m.add(tube([P(sg * 0.043, yb1 + 0.0002, 0.121), P(sg * 0.043, -0.079, 0.121)], 0.0075, 12, "rubber_black",
                   cap0=False))
        m.add(bolt(P(sg * 0.043, yb0, 0.121), (0, -1, 0), af=0.012, head_h=0.005, mat="steel"))
    m.add(box(P(0, -0.070, 0.128), (0.100, 0.024, 0.009), "caliper", R))             # bridge over the disc's edge
    m.add(tube([P(0, -0.080, 0.104), P(0, -0.112, 0.104)], 0.0175, 20, "caliper"))   # piston housing (outboard)
    m.add(box(P(0, -0.092, 0.1175), (0.032, 0.026, 0.012), "caliper", R))
    m.add(box(P(0, -0.0575, 0.111), (0.040, 0.005, 0.034), "caliper", R))            # inboard finger
    for y0, y1, mat in ((-0.0768, -0.0723, "anod_black"), (-0.0798, -0.0768, "steel"),
                        (-0.0677, -0.0632, "anod_black"), (-0.0632, -0.0602, "steel")):      # pads, 0.3 mm off the disc
        m.add(box(P(0, (y0 + y1) / 2, 0.108), (0.044, abs(y1 - y0), 0.022), mat, R))
    d = 0.87 * er - 0.5 * et                                     # bleed nipple with its cap
    b0 = P(-0.008, -0.100, 0.119)
    m.add(tube([b0, b0 + 0.014 * d], 0.003, 8, "steel"))
    m.add(tube([b0 + 0.012 * d, b0 + 0.019 * d], 0.0042, 8, "rubber_black"))
    m.add(tube([P(0, -0.112, 0.104), P(0, -0.1175, 0.104)], 0.008, 12, "steel"))     # banjo
    m.add(bolt(P(0, -0.1175, 0.104), (0, -1, 0), af=0.012, head_h=0.005, mat="steel"))
    from scipy.interpolate import CubicSpline
    s0 = P(0, -0.115, 0.104)                                     # hose: RIGHT rows 1490..1500, level above the arm
    way = np.array([s0, s0 + (0.030, -0.002, 0.008), (0.140, -0.116, 0.436), (0.220, -0.110, 0.440),
                    (0.360, -0.098, 0.470), (0.440, -0.090, 0.490), (0.470, -0.086, 0.515)])       # onward EST
    m.add(tube(CubicSpline(np.arange(len(way)), way)(np.linspace(0, len(way) - 1, 40)), 0.0042, 8, "cable"))
    return m


def _hull(circles, n=20):
    """Convex outline (x, z) round circles (x, z, r)."""
    from scipy.spatial import ConvexHull
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    pts = np.vstack([np.stack([x + r * np.cos(a), z + r * np.sin(a)], axis=1) for x, z, r in circles])
    return pts[ConvexHull(pts).vertices]


PARTS = {name: (lambda fn=fn: _compact(fn())) for name, fn in
         (("front_wheel", front_wheel), ("rear_wheel", rear_wheel), ("drive", drive), ("rear_brake", rear_brake))}
