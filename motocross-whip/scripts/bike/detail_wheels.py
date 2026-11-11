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
MATERIALS = {"tyre": dict(rgb=(15, 15, 16), rough=0.72),        # studio photos: lit knob faces show a dull sheen
             "tyre_spew": dict(rgb=(15, 15, 16), rough=0.72),
             # black anodised aluminium: the anodic film is a dielectric, so its gloss is plain (not metallic) and
             # the printed strip and the bare rim look alike except for the print
             "rim": dict(rgb=(12, 12, 13), metal=0.0, rough=0.40),
             "rim_print_r": dict(image="stock/rim_rear.png", metal=0.0, rough=0.40),
             "rim_print_f": dict(image="stock/rim_front.png", metal=0.0, rough=0.40),
             "nipple": dict(rgb=(198, 198, 202), metal=1.0, rough=0.22),           # DR13: bright plated nipples
             # rear hub (see _hub_ribs): the LEFT photo's end, recessed in the sprocket, reads 96..102; the RIGHT
             # photo's open end reads about 160 (pair p_disc1): one cast finish between, lit as the photos are
             "hub_cast": dict(rgb=(124, 126, 130), metal=0.6, rough=0.58),
             "hub_machined": dict(rgb=(176, 178, 182), metal=1.0, rough=0.3),     # its turned sprocket spigot
             # LEFT pair p_spr1: the bare aluminium sprocket reads 150..157 in the photo, the old 170 rendered white
             "sprocket": dict(rgb=(150, 152, 156), metal=1.0, rough=0.48),
             # chain (LEFT pair p_spr1, 475832): plain grey steel plates and pins, not the dark grey of before
             "chain": dict(rgb=(128, 129, 133), metal=1.0, rough=0.42),
             "chain_pin": dict(rgb=(150, 151, 155), metal=1.0, rough=0.35),
             # rear caliper (RIGHT photo: body 56..66, piston housing's end 100..110, swingarm 175, disc 160)
             "caliper_r": dict(rgb=(86, 87, 91), metal=0.8, rough=0.36),
             "caliper_face": dict(rgb=(100, 102, 106), metal=1.0, rough=0.38),
             "bracket_r": dict(rgb=(84, 80, 82), metal=0.8, rough=0.5),      # REAR: the arm darker than the swingarm
             "brake_pad": dict(rgb=(42, 40, 38), metal=0.3, rough=0.8),      # sintered lining
             "pad_ear": dict(rgb=(150, 118, 84), metal=1.0, rough=0.4),      # REAR / rr34: bronze ears on the pad pin
             "brass": dict(rgb=(176, 136, 82), metal=1.0, rough=0.35)}       # banjo sealing washers
CLASS = {"tyre": "black", "tyre_spew": "black", "rim_print_r": "black", "rim_print_f": "black"}
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
# where the first row stands, in pitches (LEFT and RIGHT edge scans agree: front tips at 3.35 deg, rear 4.4 / 5.35)
FRONT_PHASE, REAR_PHASE = 3.35 / (360 / 41), 4.9 / (360 / 46)
# spokes: LEFT and RIGHT ring scans at four radii, fitted through the cameras (three-cross, 60 deg): front hub holes
# on r 41 mm, first hole at 18.5 deg (residual 0.9 deg rms in both photos); rear first hole at 10.5..11 deg (fit
# poor, 2.7 deg rms: the rear's hole circle stays EST)
FRONT_HUB_R, FRONT_SPOKE0 = 0.041, math.radians(18.5)
REAR_HUB_R, REAR_SPOKE0 = 0.046, math.radians(9.0)
# 2026-11-11: the rims' inner ring unwrapped in both side photos (unwrap.py, r_in - 9..20 mm, plane y 0): the
# front's nipples fit a 36 comb (phase 8.3 deg, rms 1.5 deg), the rear's do NOT (36: vector strength 0.16 and 0.04)
# but a 32 comb does (0.58 and 0.43; 17 nipples over 179 deg in the clear arc of the LEFT photo, 19 over 200 in the
# RIGHT): the rear wheel has 32 spokes, its rim holes at 9.0 deg + k 11.25 (both photos)

SPOKES = {"front": 36, "rear": 32}  # front SPEC 36 (RevZilla listing) and counted; rear counted (above)
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


def _plate(outer, holes, y, thick, mat, step, origin=(0.0, 0.0), chamfer=0.0, chamfered=()):
    """Flat plate in the wheel's plane: outline and holes are (x, z) loops about ORIGIN, used point for point (no
    resampling: tooth forms and small holes keep their shape), plus an interior grid; thickness along y about Y.
    CHAMFER: the holes numbered in CHAMFERED (0 = the first hole) get a 45 deg chamfer that wide on both faces."""
    from scipy.spatial import Delaunay, cKDTree
    outer = _ccw(outer)
    hs0 = [_ccw(h) for h in holes]
    hs = [_mitre(h, chamfer) if (chamfer and i in chamfered) else h for i, h in enumerate(hs0)]
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
        if n > 0 and chamfer and (n - 1) in chamfered:          # face edge -> the hole's own size -> face edge
            H = hs0[n - 1] + np.asarray(origin)
            r1 = m.verts(np.stack([H[:, 0], np.full(len(H), y - thick / 2 + chamfer), H[:, 1]], axis=1))
            r2 = m.verts(np.stack([H[:, 0], np.full(len(H), y + thick / 2 - chamfer), H[:, 1]], axis=1))
            rings = [lo_ + o, r1, r2, hi_ + o]
        else:
            rings = [lo_ + o, hi_ + o]
        for a_, b_ in zip(rings, rings[1:]):
            for i in range(len(L)):
                j = (i + 1) % len(L)
                f = (a_ + i, b_ + i, b_ + j, a_ + j)
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


# ---------------------------------------------------------------- tread blocks (shaped knobs on a whole carcass)
# A knob is built in its own plan coordinates: s along the tread in the direction of travel (+ = the leading edge,
# the one that meets the ground first), t across = arc length of the carcass section from the crown centre line
# (always >= 0 in the plan; the -y side is mirrored), z = height above the carcass. Walls have a moulding draft,
# the plan's corners are rounded, the top edge has a quarter-round, the foot a small flare (the fillet at the
# root) sunk 0.8 mm into the carcass, which is a whole grid under every knob (nothing hangs, nothing has holes).
def _fillet(poly, r, n=3):
    """Round the corners of a closed polygon with radius about R (one, or one per corner; quadratic arcs, N points
    each)."""
    P = np.asarray(poly, float)
    rr = np.broadcast_to(np.asarray(r, float), (len(P),))
    out = []
    for i in range(len(P)):
        r = rr[i]
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


def _rect(s0, s1, t0, t1, r, n=3):
    """Counter-clockwise rectangle in plan with rounded corners, R one radius or four (s0t0, s1t0, s1t1, s0t1)."""
    return _fillet([(s0, t0), (s1, t0), (s1, t1), (s0, t1)], r, n)


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


def _knob(m, xf, plan, h_of, draft, mat="tyre", base=None, top=True, wall_mat=None, top_mat=None, step=0.0032,
          rnd=ROUND, base_draft=None):
    """One knob: PLAN (s, t) counter-clockwise at the root; H_OF(s, t) its height; DRAFT one angle or one per plan
    vertex. BASE: start the walls at this height (no root flare: a knob stacked on another one, whose walls it
    continues with BASE_DRAFT); TOP False: a flat top without the round (a floor seen only in a slit). WALL_MAT(i):
    material of the wall from plan vertex i to i + 1 (below the round). RND: radius of the top edge's round.
    Returns the top's boundary in 3D and in plan (for spews)."""
    plan = _ccw(plan)
    h = np.array([h_of(s, t) for s, t in plan])
    td = np.broadcast_to(np.tan(np.asarray(draft, float)), (len(plan),))
    zb = 0.0 if base is None else base
    tb = td if base_draft is None else np.full(len(plan), math.tan(base_draft))
    if base is None:
        z3 = np.minimum(0.0015, 0.5 * (h - rnd))
        lv = [(np.full(len(h), -0.0008), FLARE), (np.zeros(len(h)), 0.5 * FLARE), (z3, None)]
    else:
        lv = [(np.full(len(h), base), None)]
    if top:
        lv += [(h - rnd, None), (h - 0.293 * rnd, -0.293 * rnd), (h, -rnd)]
    else:
        lv += [(h, None)]
    rings = []
    for z, extra in lv:
        zz = np.maximum(z, 0.0)
        off = -(tb * np.minimum(zz, zb) + td * np.maximum(zz - zb, 0.0)) + (0.0 if extra is None else extra)
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
        tm = top_mat(*P2[tr].mean(axis=0)) if callable(top_mat) else (top_mat or mat)
        faces.append((tuple(ot + i if i < n else oe + i - n for i in tr), tm))
    # winding: the top faces the way the knob stands (from the carcass out)
    tr0 = faces[-1][0]
    A, B, C = (np.asarray(m.V[i]) for i in tr0)
    s0, t0 = P2[tri[-1]].mean(axis=0)
    up = xf(s0, t0, float(h_of(s0, t0)) + 0.001) - xf(s0, t0, float(h_of(s0, t0)))
    flip = np.cross(B - A, C - A) @ up < 0
    for f, mt in faces:
        m.face(f[::-1] if flip else f, mt)
    return xf(Qt[:, 0], Qt[:, 1], zt), Qt


def carcass(sec, n, phase0, per, t_end):
    """The carcass as one grid, bead (+y) to bead (-y): PER columns per pitch, section rows every 3 mm over the
    tread (to T_END), then the sidewall down to the bead. Returns mesh, columns, first angle, rows."""
    na = per * n
    ts = set(np.round(np.linspace(0.0, t_end, int(t_end / 0.003) + 1), 5))
    ts |= set(np.round(np.linspace(t_end, sec.length, 9)[1:], 5))
    ts = sorted(ts)
    T = ts[::-1] + [-t for t in ts[1:]]
    a0 = 2 * math.pi * phase0 / n
    ang = a0 + 2 * math.pi * np.arange(na) / na
    m = Mesh()
    for t in T:
        y, r = sec.at(t)
        m.verts(np.stack([r * np.cos(ang), np.full(na, y), r * np.sin(ang)], axis=1))
    for j in range(len(T) - 1):
        mat = "tyre"
        for i in range(na):
            i2 = (i + 1) % na
            m.face((j * na + i, j * na + i2, (j + 1) * na + i2, (j + 1) * na + i), mat)
    return m, na, a0, len(T)


def _spew(m, p, d, length, rng):
    """A mould vent hair: rubber whisker 0.45 mm thick, LENGTH long, from P along D, slightly bent."""
    d = d / np.linalg.norm(d)
    side = np.cross(d, rng.normal(size=3))
    side /= np.linalg.norm(side)
    path = [p - d * 0.0004, p + d * length * 0.5 + side * length * 0.06, p + d * length]
    m.add(tube(path, [0.00024, 0.00022, 0.00016], 3, "tyre_spew"))


def _spews_at(m, P3, up, idx, rng, p=0.8, lo=0.0025, hi=0.0050):
    """Spews at the top boundary points IDX of a knob (P3: its top boundary in 3D), leaning out and up."""
    c = P3.mean(axis=0)
    for i in idx:
        if rng.random() > p:
            continue
        out = P3[i] - c
        out -= (out @ up) * up
        d = 0.75 * out / np.linalg.norm(out) + 0.65 * up + 0.3 * rng.normal(size=3)
        _spew(m, P3[i] - 0.0002 * up, d, rng.uniform(lo, hi), rng)


# Rear: Pirelli Scorpion MX32 Mid Soft 100/90-19 (SPEC), as Honda's studio photos show it. One row per pitch, 46
# pitches (LEFT / RIGHT polar scans of the outline: tall plateaus every 7.8 deg, 4.2 deg wide at r 334; between them
# a low plateau at r 321.5 half a pitch on). Per row (REAR rows 1580..1680 cols 1925..2075, LEFT cols 3250..3400
# rows 1480..1680 zoomed, lr34, DR13 and 475832):
#   centre knob across the crown, 44 px = 28 mm at the top (REAR), split along the centre line by a V slit that runs
#     its whole length (REAR: a dark wedge down the leading wall of every centre knob, 5 mm wide at the top, about
#     1.5 at its floor) but only part way down (475832: the two halves join below it)
#   an intermediate knob each side in the same row, its outer-leading corner cut off at a slant (REAR: the slanted
#     edge at the top-outer corner of both; Pirelli's flat view of the tread). Its trailing wall spans y 15..34 mm
#     (REAR cols 1947..1977); seen side-on (LEFT zoom) its outer face is the lit square inside the outline
#   half a pitch on: a shoulder knob each side, y 26..45.5 mm (REAR cols 1929..1959); plain tapered block with a vent
#     hair at each top corner (DR13: no notch or step on the stock tyre's shoulder knobs, unlike Pirelli's renders)
#   a low pad under each row joining its three in-row knobs: in the REAR photo and in Pirelli's views the floor
#     shows a faint arc between rows, longest at the centre (EST 1.2 mm high)
# Heights: the LEFT outline (edge.py: the last dark column per row, photo against model, cols 3200..3420) has flat
#   plateaus at the centre knobs' tips (r 334.3, y = 0); a knob nearer the camera (y > 0) at the back of the wheel
#   lands 0.28 px further out per mm of y, 1.28 px per mm of radius. Nothing passes the centre tips, so the
#   intermediates' tops fall away to R - 9 mm at their outer end (tip envelope ENV), and the low plateau (col 3365:
#   the shoulders' inner top corner, at y 37) puts that corner at r 317.5.
# The red centre line of 475832 (an outdoor press bike) is not on the studio bike (REAR, lr34: none): left off.
# Lengths along the tread: LEFT zoom of one pitch side-on (cols 3300..3400, rows 1500..1620): the in-row knob's lit
#   outer face is 25 px = 19.5 mm long, the whole row 29 px = 22 mm, the shoulder's face 25 px; the rest EST.
REAR_TREAD = dict(
    env=0.0090,                                     # tip envelope: R - env (t / 31.5 mm)^2
    centre=dict(s=0.0110, t=0.0150, slit_z=0.0090, slit_t=0.0002, draft=4.0, slit_draft=7.5),
    inter=dict(t0=0.0165, t1=0.0315, s=0.0095, cut=(0.0065, 0.0055), lean=0.3, draft=5.0),
    shoulder=dict(t0=0.0280, t1=0.0470, s=0.0080, r0=0.3175, h1=0.0120, lean=0.85, draft=5.0),
    pad=dict(t=0.0300, s0=0.0120, s1=0.0045, h=0.0012, draft=35.0))


def _signed(xc):
    """A Knob map that takes signed t (a knob across the crown centre line)."""
    def f(s, t, z):
        s, t, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(t, float), np.asarray(z, float))
        P = xc(s, abs(t), z)
        P[..., 1] *= np.where(t < 0, -1.0, 1.0)
        return P
    return f


def rear_tread(m, sec, n, a0, spec, seed=19):
    """Every knob of the rear tyre on the carcass grid already in M."""
    q = REAR_TREAD
    rng = np.random.default_rng(seed)
    rc = lambda t: float(np.interp(abs(t), sec.t, sec.P[:, 1]))
    r_env = lambda t: spec["R"] - q["env"] * (t / 0.0315) ** 2

    def h_to(t, r_top, lean):                       # height along the lean direction that reaches radius R_TOP
        y0, r0 = sec.lift(abs(t), 0.0, lean)
        y1, r1 = sec.lift(abs(t), 0.01, lean)
        return float((r_top - r0) / ((r1 - r0) / 0.01))

    for k in range(n):
        a = a0 + 2 * math.pi * k / n
        xc = _signed(Knob(sec, a, 1, 0.0))
        # row pad: lens-shaped, longest at the centre line
        p = q["pad"]
        tt = np.linspace(-p["t"], p["t"], 13)
        sh = p["s0"] + p["s1"] * (1 - (tt / p["t"]) ** 2)
        pad = np.vstack([np.stack([-sh, tt], 1)[::-1], np.stack([sh, tt], 1)])
        _knob(m, xc, _fillet(pad, 0.004, 3), lambda s, t: p["h"], math.radians(p["draft"]), mat="tyre", rnd=0.0006)
        # centre knob: a body up to the slit's floor, and two halves above it that share its walls' line
        c = q["centre"]
        hc = lambda s, t: r_env(t) - rc(t)
        body = _rect(-c["s"], c["s"], -c["t"], c["t"], 0.0015)
        _knob(m, xc, body, lambda s, t: c["slit_z"], math.radians(c["draft"]), mat="tyre", top=False, step=0.002)
        for sg in (1, -1):
            t0, t1 = sorted((sg * c["slit_t"], sg * c["t"]))
            r_in, r_out = 0.0003, 0.0015                         # slit corners nearly sharp, outer ones rounded
            half = _rect(-c["s"], c["s"], t0, t1, (r_in, r_in, r_out, r_out) if sg > 0 else (r_out, r_out, r_in, r_in))
            dr = np.where(abs(half[:, 1]) < c["slit_t"] + 0.0005, math.radians(c["slit_draft"]), math.radians(c["draft"]))
            # the slit's walls stand on the body's top edge: start them from the body's own outline there
            P3, Qt = _knob(m, xc, half, hc, dr, mat="tyre", base=c["slit_z"], base_draft=math.radians(c["draft"]))
            up = xc(0.0, sg * 0.007, hc(0, 0.007) + 0.001) - xc(0.0, sg * 0.007, hc(0, 0.007))
            far = [i for i in range(len(Qt)) if abs(Qt[i][1]) > c["t"] - 0.004]
            _spews_at(m, P3, up / np.linalg.norm(up), far[::2], rng, 0.5)
        # intermediate and shoulder knobs, both sides
        for side in (1, -1):
            g = q["inter"]
            plan = [(-g["s"], g["t0"]), (g["s"], g["t0"]), (g["s"], g["t1"] - g["cut"][0]),
                    (g["s"] - g["cut"][1], g["t1"]), (-g["s"], g["t1"])]
            hf = lambda s, t, g=g: h_to(t, r_env(t), g["lean"])
            xi = Knob(sec, a, side, g["lean"])
            P3, Qt = _knob(m, xi, _fillet(plan, 0.0015), hf, math.radians(g["draft"]), mat="tyre")
            tm = 0.5 * (g["t0"] + g["t1"])
            up = xi(0.0, tm, hf(0, tm) + 0.001) - xi(0.0, tm, hf(0, tm))
            _spews_at(m, P3, up / np.linalg.norm(up), range(1, len(Qt), 3), rng, 0.55)
            g = q["shoulder"]
            h0 = h_to(g["t0"], g["r0"], g["lean"])
            hf = lambda s, t, g=g, h0=h0: h0 + (g["h1"] - h0) * (t - g["t0"]) / (g["t1"] - g["t0"])
            xs = Knob(sec, a + math.pi / n, side, g["lean"])
            plan = _rect(-g["s"], g["s"], g["t0"], g["t1"], 0.0012)
            P3, Qt = _knob(m, xs, plan, hf, math.radians(g["draft"]), mat="tyre")
            up = xs(0.0, g["t1"] - 0.004, 0.02) - xs(0.0, g["t1"] - 0.004, 0.0)
            _spews_at(m, P3, up / np.linalg.norm(up), range(1, len(Qt), 3), rng, 0.8)
            for s0 in (-0.5 * g["s"], 0.5 * g["s"]):                       # vents on the outer face (475832)
                if rng.random() < 0.6:
                    z = 0.6 * hf(s0, g["t1"])
                    pnt = xs(s0, g["t1"] - z * math.tan(math.radians(g["draft"])) - 0.0002, z)
                    o = xs(s0, g["t1"] + 0.003, z) - xs(s0, g["t1"], z)
                    _spew(m, pnt, o / np.linalg.norm(o) + 0.3 * rng.normal(size=3), rng.uniform(0.003, 0.005), rng)


# ---------------------------------------------------------------- tyre sidewall: raised marks
# Moulded marks stand 0.8 mm proud of the sidewall (EST, they cast a shadow at 30 cm: geometry, MICRO.md). Text is
# DejaVu Sans Bold Oblique (bundled with matplotlib, so the build is the same everywhere), the nearest free face to
# Pirelli's heavy italic. Every mark reads clockwise seen from its own side, tops outward (LEFT and RIGHT photos
# unwrapped about the rear axle, unwrap.py: the left wall's text reads with the angle growing, the right wall's with
# it falling).
MARK_H = 0.0008
MARK_SINK = 0.0003


def _text_polys(text, cap, span=None):
    """Glyph outlines of TEXT (u along the baseline from 0, v up) with cap height CAP; stretched along u to SPAN."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), text, size=1.0, prop=FontProperties(family="DejaVu Sans", weight="bold", style="oblique"))
    k = cap / 0.729                                              # DejaVu Sans: cap height 0.729 em
    polys = [np.asarray(p, float)[:-1] * k for p in tp.to_polygons() if len(p) > 3]
    lo = min(p[:, 0].min() for p in polys)
    hi = max(p[:, 0].max() for p in polys)
    sx = 1.0 if span is None else span / (hi - lo)
    return [np.stack([(p[:, 0] - lo) * sx, p[:, 1]], axis=1) for p in polys], (hi - lo) * sx


def _frame_polys(u0, u1, v0, v1, w):
    """A rectangular border W wide (outer loop and inner hole)."""
    o = np.array([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    i = np.array([(u0 + w, v0 + w), (u0 + w, v1 - w), (u1 - w, v1 - w), (u1 - w, v0 + w)])
    return [o, i]


def _raised(m, polys, xf, mat="tyre", step=0.0003):
    """Polygons (even-odd fill: outlines and their holes) raised MARK_H from a surface. XF(u, v, z) -> 3D."""
    from matplotlib.path import Path
    from scipy.spatial import Delaunay
    loops = [resample(np.vstack([p, p[:1]]), step)[:-1] if len(p) > 2 else p for p in polys]
    loops = [lp for lp in loops if len(lp) >= 3]
    paths = [Path(lp) for lp in loops]

    def filled(pts):
        return sum(pa.contains_points(pts).astype(int) for pa in paths) % 2 == 1

    P = np.vstack(loops)
    tri = Delaunay(P).simplices
    tri = tri[filled(P[tri].mean(axis=1))]
    a, b, c = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    tri = tri[abs(area) > 1e-14]
    area = area[abs(area) > 1e-14]
    tri[area < 0] = tri[area < 0][:, ::-1]
    top = m.verts(xf(P[:, 0], P[:, 1], MARK_H))
    bot = m.verts(xf(P[:, 0], P[:, 1], -MARK_SINK))
    o = 0
    up = xf(P[0, 0], P[0, 1], 0.001) - xf(P[0, 0], P[0, 1], 0.0)
    A, B, C = (xf(P[i, 0], P[i, 1], MARK_H) for i in tri[0]) if len(tri) else (None, None, None)
    flip = len(tri) and np.cross(B - A, C - A) @ up < 0
    for t in tri:
        m.face(tuple(top + i for i in (t[::-1] if flip else t)), mat)
    for lp in loops:
        n = len(lp)
        e = np.roll(lp, -1, axis=0) - lp
        mid = lp + 0.5 * e
        nrm = np.stack([e[:, 1], -e[:, 0]], axis=1)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
        out_right = ~filled(mid + nrm * 1e-5)                     # the fill lies left of the edge
        for i in range(n):
            j = (i + 1) % n
            f = (bot + o + i, bot + o + j, top + o + j, top + o + i)
            m.face(f if out_right[i] != bool(flip) else f[::-1], mat)
        o += n


def _sidewall_y(sec):
    """y of the sidewall (outer surface) against radius, below the shoulder."""
    i0 = int(np.searchsorted(sec.t, 0.058))
    r, y = sec.P[i0:, 1][::-1], sec.P[i0:, 0][::-1]
    return lambda rho: np.interp(rho, r, y)


def _arc_map(ysw, side, a_c, r_b, u_mid, sense):
    """(u, v, z) of a mark -> wheel frame: u along the baseline (radius R_B) centred on wheel angle A_C, v outward,
    z off the sidewall; SENSE +1: u grows with the wheel angle."""
    def f(u, v, z):
        u, v, z = np.broadcast_arrays(np.asarray(u, float), np.asarray(v, float), np.asarray(z, float))
        rho = r_b + v
        a = a_c + sense * (u - u_mid) / r_b
        return np.stack([rho * np.cos(a), side * (ysw(rho) + z), rho * np.sin(a)], axis=-1)
    return f


def _emblem(cap):
    """Pirelli's Scorpion emblem (DR13, at the shoulder: a scorpion seen from above, about 16 mm across), as raised
    strokes: body, curled tail, two claws, eight legs. Returns polygons in (u, v) about (0, 0); overlapping strokes
    are separate pieces (each raised on its own)."""
    s = cap / 16.0
    pieces = [circle(2.2 * s, 14, 0, 0) * [1.0, 1.5]]                                   # body
    for x, y, r in [(0, 3.6, 1.5), (0.6, 5.6, 1.3), (1.8, 7.0, 1.1), (3.2, 7.4, 0.9), (4.2, 6.6, 0.8)]:
        pieces.append(circle(r * s, 10, x * s, y * s))                                # tail segments, curling
    for sg in (1, -1):
        for k in range(4):                                                            # legs, fanned out
            b = math.radians(35 - 25 * k)
            p0 = np.array([sg * 1.6 * s, (1.2 - 1.0 * k) * s])
            p1 = p0 + 4.0 * s * np.array([sg * math.cos(b), math.sin(b)])
            pieces.append(slot((p0 + p1) / 2, math.atan2(*(p1 - p0)[::-1]), float(np.linalg.norm(p1 - p0)), 0.7 * s, 4))
        c0 = np.array([sg * 1.4 * s, -2.6 * s])                                       # claw: arm and pincer
        c1 = c0 + np.array([sg * 2.5, -2.5]) * s
        pieces.append(slot((c0 + c1) / 2, math.atan2(*(c1 - c0)[::-1]), float(np.linalg.norm(c1 - c0)), 0.9 * s, 4))
        pieces.append(circle(1.2 * s, 10, *(c1 + np.array([sg * 0.6, -0.8]) * s)))
    return pieces


# Rear wall layout (degrees along the reading direction from the emblem). LEFT photo, sidewall unwrapped beside the
# model's (uwcmp.py, plane y 0.036): SCORPION MX32 84..160 deg, caps 16 mm on a baseline at r 266.5; the size code
# 272..337.5 deg, caps 11.5 mm at r 259. RIGHT unwrap: SCORPION MX from 95 deg down to 27, a small box at 138..148.
# The emblem stands just before SCORPION (DR13; RIGHT 97 deg, LEFT 78 by the same offset). The rest follows
# Pirelli's own layout (web/pirelli-mx32ms-wheel-side): MID SOFT in a box after MX32, the big PIRELLI word, the
# size code, the small PIRELLI box 45 deg before the emblem: places EST from that picture.
REAR_WALL = dict(emblem=(78.0, 97.0), items=[
    ("box", "PIRELLI", -49.0, -40.0, 0.2655, 0.0055),
    ("emblem", None, 0.0, None, 0.2745, 0.016),
    ("text", "SCORPION  MX32", 6.0, 82.0, 0.2665, 0.016),
    ("box", "MID SOFT", 88.0, 102.0, 0.2665, 0.0065),
    ("logo", "PIRELLI", 115.0, 150.0, 0.2640, 0.015),
    ("text", "100/90-19  57M  NHS", 194.0, 259.5, 0.2590, 0.0115),
    ("arrow", None, 265.0, 277.0, 0.2635, 0.008)])


def sidewall(m, sec, spec, side, layout):
    """Raised marks on one sidewall (SIDE +1: left), the rim line and the vent hairs of the wall."""
    ysw = _sidewall_y(sec)
    a_e = math.radians(layout["emblem"][0 if side > 0 else 1])
    sense = 1 if side > 0 else -1
    for kind, txt, d0, d1, r_b, cap in layout["items"]:
        if kind == "emblem":
            xf = _arc_map(ysw, side, a_e + sense * math.radians(d0), r_b, 0.0, sense)
            for pc in _emblem(cap):
                _raised(m, [pc], xf, step=0.0005)
            continue
        a0, a1 = a_e + sense * math.radians(d0), a_e + sense * math.radians(d1)
        span = abs(a1 - a0) * r_b
        a_c = 0.5 * (a0 + a1)
        if kind == "arrow":
            L, w = span, cap
            poly = np.array([(0, 0.35 * w), (0.62 * L, 0.35 * w), (0.62 * L, 0.0), (L, 0.5 * w), (0.62 * L, w),
                             (0.62 * L, 0.65 * w), (0, 0.65 * w)])
            if side < 0:                                         # the arrow points the way the wheel turns
                poly = poly * [-1, 1] + [L, 0]
            _raised(m, [poly], _arc_map(ysw, side, a_c, r_b, L / 2, sense), step=0.0006)
            continue
        polys, w = _text_polys(txt, cap, span if kind == "text" else None)
        if kind in ("box", "logo"):
            pad = 0.35 * cap
            if kind == "logo":                                   # Pirelli's long P: its top runs over the word
                polys.append(np.array([(0.45 * cap, 0.86 * cap), (w, 0.86 * cap), (w - 0.03 * cap, cap),
                                       (0.45 * cap, cap)]))
            polys += _frame_polys(-pad, w + pad, -pad, cap + pad, 0.12 * cap if kind == "box" else 0.07 * cap)
        _raised(m, polys, _arc_map(ysw, side, a_c, r_b, w / 2, sense), step=float(np.clip(cap / 36, 0.00025, 0.0006)))
    # rim line: a rib 1.2 mm wide, 0.6 mm proud, 4 mm above the rim flange (EST: every tyre has one, DR13 shows it
    # as the fine bright line just above the rim)
    r_l = spec["rb"] + spec["hf"] + 0.004
    prof = [(r_l - 0.0006, ysw(r_l - 0.0006) - 0.0003), (r_l - 0.0005, ysw(r_l - 0.0005) + 0.0006),
            (r_l + 0.0005, ysw(r_l + 0.0005) + 0.0006), (r_l + 0.0006, ysw(r_l + 0.0006) - 0.0003)]
    rib = lathe([(r, side * y) for r, y in prof], 288, "tyre")
    if side < 0:
        rib.F = [f[::-1] for f in rib.F]
    m.add(rib)
    # vent hairs of the sidewall mould: one a pitch, just under the shoulder knobs (DR13: a row of short dark
    # whiskers there), leaning out and away from the rim
    rng = np.random.default_rng(23 if side > 0 else 29)
    n = spec["pitches"]
    for k in range(n):
        a = 2 * math.pi * (k + 0.25) / n + rng.normal() * 0.01
        rho = 0.2885 if spec is REAR else 0.3160
        p = np.array([rho * math.cos(a), side * (ysw(rho) - 0.0002), rho * math.sin(a)])
        d = np.array([0.6 * math.cos(a), side * 0.8, 0.6 * math.sin(a)]) + 0.25 * rng.normal(size=3)
        _spew(m, p, d, rng.uniform(0.0025, 0.004), rng)


# Front: Pirelli Scorpion MX32 Mid Soft 80/100-21 (SPEC). 41 rows (LEFT / RIGHT polar scans about the front axle,
# scan_front: tall plateaus at r 359 every 8.78 deg, 3.8 deg wide; low plateaus at r 354 half a pitch on; floor
# 347..348). Per row (FRONT photo rows 1380..1560, cols 1930..2070 zoomed; 1.6 px a mm there):
#   a centre knob split by a V slit like the rear's: cols 1969..2030 = 38 mm across at the top, the gap 6 px =
#     3.7 mm; its trailing edge rises 2.5 mm toward the slit (the halves point backward, Pirelli's arrow knobs)
#   a shoulder knob each side in the same row: cols 1930..1952 = y 30..44 mm, 17.5 mm long
#   half a pitch on: an intermediate knob each side, an arrowhead pointing out (corners fore, aft and out, a V notch
#     in its inner side: the dark notch inside each in the FRONT zoom; Pirelli's arrow knobs): 36 px = 22 mm long,
#     y 17..40 mm (FRONT pair p_ff2: the first try at 18 mm and y 17..36 stood smaller and further in than the photo's)
# Heights from the outline as for the rear (edge.py on LEFT and RIGHT: tall plateaus 2 to 3 px outside the photo's
#   in both, low plateaus within 2 px); the rest EST.
FRONT_TREAD = dict(
    env=0.0110,                                     # tip envelope: R - env (t / 31.5 mm)^2 (LEFT outline)
    centre=dict(s=0.0110, t=0.0200, v=0.0025, slit_z=0.0060, slit_t=0.0004, draft=4.0, slit_draft=7.5),
    shoulder=dict(t0=0.0300, t1=0.0450, s=0.0085, h0=0.0120, h1=0.0105, lean=0.85, draft=5.0),
    inter=dict(t0=0.0165, t1=0.0400, s=0.0110, cut=0.0050, r0=0.3480, lean=0.5, draft=5.0))


def front_tread(m, sec, n, a0, spec, seed=21):
    """Every knob of the front tyre on the carcass grid already in M."""
    q = FRONT_TREAD
    rng = np.random.default_rng(seed)
    rc = lambda t: float(np.interp(abs(t), sec.t, sec.P[:, 1]))
    r_env = lambda t: spec["R"] - q["env"] * (t / 0.0315) ** 2

    def h_to(t, r_top, lean):
        y0, r0 = sec.lift(abs(t), 0.0, lean)
        y1, r1 = sec.lift(abs(t), 0.01, lean)
        return float((r_top - r0) / ((r1 - r0) / 0.01))

    for k in range(n):
        a = a0 + 2 * math.pi * k / n
        xc = _signed(Knob(sec, a, 1, 0.0))
        c = q["centre"]
        hc = lambda s, t: r_env(t) - rc(t)
        body = _fillet([(-c["s"], -c["t"]), (c["s"], -c["t"]), (c["s"], c["t"]), (-c["s"], c["t"]),
                        (-c["s"] - c["v"], 0.0)], 0.0015)
        _knob(m, xc, body, lambda s, t: c["slit_z"], math.radians(c["draft"]), top=False, step=0.002)
        for sg in (1, -1):
            ts, to = sg * c["slit_t"], sg * c["t"]
            # the half's slit edge runs from the V's point to the leading edge; rounded outer corners only
            half = [(-c["s"] - c["v"] * (1 - c["slit_t"] / c["t"]), ts), (c["s"], ts), (c["s"], to), (-c["s"], to)]
            half = _ccw(half)                                   # sg < 0: reversed, the slit corners last
            half = _fillet(half, (0.0003, 0.0003, 0.0015, 0.0015) if sg > 0 else (0.0015, 0.0015, 0.0003, 0.0003))
            dr = np.where(abs(half[:, 1]) < c["slit_t"] + 0.0005, math.radians(c["slit_draft"]), math.radians(c["draft"]))
            P3, Qt = _knob(m, xc, half, hc, dr, base=c["slit_z"], base_draft=math.radians(c["draft"]))
            up = xc(0.0, sg * 0.01, hc(0, 0.01) + 0.001) - xc(0.0, sg * 0.01, hc(0, 0.01))
            far = [i for i in range(len(Qt)) if abs(Qt[i][1]) > c["t"] - 0.004]
            _spews_at(m, P3, up / np.linalg.norm(up), far[::2], rng, 0.5)
        for side in (1, -1):
            g = q["shoulder"]
            hf = lambda s, t, g=g: g["h0"] + (g["h1"] - g["h0"]) * (t - g["t0"]) / (g["t1"] - g["t0"])
            xs = Knob(sec, a, side, g["lean"])
            P3, Qt = _knob(m, xs, _rect(-g["s"], g["s"], g["t0"], g["t1"], 0.0012), hf, math.radians(g["draft"]))
            up = xs(0.0, g["t1"] - 0.004, 0.02) - xs(0.0, g["t1"] - 0.004, 0.0)
            _spews_at(m, P3, up / np.linalg.norm(up), range(1, len(Qt), 3), rng, 0.8)
            g = q["inter"]
            tm = 0.5 * (g["t0"] + g["t1"])
            plan = [(0.0, g["t1"]), (-g["s"], tm), (-0.5 * g["s"], g["t0"]), (0.0, g["t0"] + g["cut"]),
                    (0.5 * g["s"], g["t0"]), (g["s"], tm)]                   # arrowhead pointing out
            h0 = h_to(tm, g["r0"], g["lean"])
            hf = lambda s, t, g=g, h0=h0: h0
            xi = Knob(sec, a + math.pi / n, side, g["lean"])
            P3, Qt = _knob(m, xi, _fillet(_ccw(plan), 0.0014), hf, math.radians(g["draft"]))
            up = xi(0.0, tm, h0 + 0.001) - xi(0.0, tm, h0)
            _spews_at(m, P3, up / np.linalg.norm(up), range(1, len(Qt), 3), rng, 0.6)


def front_tyre():
    """Front tyre: carcass grid, the shaped knobs and the sidewall marks."""
    sec = Section(FRONT, FRONT_SECTION)
    m, na, a0, n_t = carcass(sec, FRONT["pitches"], FRONT_PHASE, 8, 0.050)
    front_tread(m, sec, FRONT["pitches"], a0, FRONT)
    for side in (1, -1):
        sidewall(m, sec, FRONT, side, FRONT_WALL)
    return m, na, a0, n_t


# Front wall layout (as REAR_WALL). LEFT unwrap about the front axle (plane y 0.036): a small box at 24..37 deg,
# SCORPION MX32 from about 70 deg to 155 (the fork leg hides 113..130), the size code "80/100-21 M/C 51M MST" (SPEC
# service description: research/crf250r-2026.md, OM) 267..340 deg, caps 12.5 mm at r 293. RIGHT unwrap: the
# small box 142..152 deg, SCORPION MX32 107 down to 17 deg. 475831 shows "80/100-21" large beside the rim.
FRONT_WALL = dict(emblem=(64.0, 105.0), items=[
    ("box", "PIRELLI", -41.0, -30.0, 0.2960, 0.0055),
    ("emblem", None, 0.0, None, 0.3050, 0.016),
    ("text", "SCORPION  MX32", 5.0, 92.0, 0.2905, 0.017),
    ("box", "MID SOFT", 97.0, 110.0, 0.2960, 0.0065),
    ("logo", "PIRELLI", 122.0, 155.0, 0.2930, 0.015),
    ("text", "80/100-21  M/C  51M  MST", 203.0, 276.0, 0.2930, 0.0125),
    ("arrow", None, 282.0, 293.0, 0.2960, 0.008)])


# ---------------------------------------------------------------- rims, spokes, valve, rim lock
def rim_profile(spec):
    """Closed section (r, y) of the rim (D.I.D DirtStar): a flat inner face carrying the nipples, a flat side band
    (where the decals are) 3.5 mm outside the bead seats, a rounded flange lip, the bead seats on the WM contour and
    the drop-centre well. Points 3 -> 4 are the +y side band, 22 -> 23 the -y one; 9 and 17 the bead seats."""
    rb, hw, hf, ri = spec["rb"], spec["hw"], spec["hf"], spec["r_in"]
    ys = hw + RIM_FLANGE_T                                       # the side band's plane
    half = [(ri, 0.0), (ri, ys - 0.0025), (ri + 0.0007, ys - 0.0007), (ri + 0.0025, ys),
            (rb + hf - 0.0035, ys + 0.0003), (rb + hf - 0.0012, ys + 0.0001), (rb + hf, ys - 0.0018),
            (rb + hf - 0.0010, ys - 0.0034), (rb + hf - 0.0030, hw + 0.0002), (rb, hw), (rb - 0.0006, 0.60 * hw),
            (ri + 0.0060, 0.40 * hw), (ri + 0.0045, 0.20 * hw)]
    return half + [(ri + 0.0045, 0.0)] + [(r, -y) for r, y in half[:0:-1]]


RIM_FLANGE_T = 0.0035   # EST flange 3.5 mm thick: the rim 54 mm wide over the bands at the rear (19 x 1.85), 48 front
# Decals (DR13, studio unwraps of both side photos): white "D.I.D" and "DirtStar" once on each side of each rim,
# reading clockwise seen from that side, tops toward the tyre, at 258..282 deg (rear) and 260..282 (front) in both
# side photos; letters 10 mm (DR13: the D.I.D letters 45 px against nipples 27 px across 6 mm flats), D.I.D 29 mm
# long, DirtStar 73 mm. The dark print "D.I.D JAPAN 76-08 10" and the size (475831: black on black, beside the
# spoke holes) EST 95 deg further on.
RIM_DECAL = {"rear": 258.0, "front": 260.0}
RIM_TEX = dict(L=0.400, H=0.025)                 # texture strip: 400 x 25 mm, 4096 x 256 px (10.24 px a mm)
RIM_DECAL_LEN = 0.117                            # D.I.D and DirtStar end to end on the strip


def rim_texture(which, out):
    """Paint the rim strip texture (stock/rim_<which>.png): the rim's black, white decals, dark print."""
    import os
    import matplotlib
    from PIL import Image, ImageDraw, ImageFont
    W, H = 4096, 256
    k = W / (RIM_TEX["L"] * 1000)                                # px a mm
    ttf = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    serif = lambda mm: ImageFont.truetype(os.path.join(ttf, "DejaVuSerif-Bold.ttf"), int(mm * k / 0.73))
    obl = lambda mm: ImageFont.truetype(os.path.join(ttf, "DejaVuSans-BoldOblique.ttf"), int(mm * k / 0.73))
    sans = lambda mm: ImageFont.truetype(os.path.join(ttf, "DejaVuSans-Bold.ttf"), int(mm * k / 0.73))
    im = Image.new("RGB", (W, H), (12, 12, 13))
    d = ImageDraw.Draw(im)
    base = H / 2 + 6 * k                         # letters 12 mm, centred on the band (LEFT pair: 70 % of the band)
    x = 4 * k
    # D.I.D: compact block letters (LEFT pair p_rim1: 2.7 times as long as tall): drawn, then squeezed to 78 %
    w0 = int(d.textlength("D.I.D", font=serif(12))) + 4
    tile = Image.new("RGB", (w0, H), (12, 12, 13))
    ImageDraw.Draw(tile).text((2, base), "D.I.D", font=serif(12), fill=(236, 236, 232), anchor="ls")
    tile = tile.resize((int(w0 * 0.78), H), Image.LANCZOS)
    im.paste(tile, (int(x), 0))
    x += tile.width + 9 * k
    for ch, mm in (("D", 11), ("I", 8.5), ("R", 8.5), ("T", 8.5), ("S", 11), ("T", 8.5), ("A", 8.5), ("R", 8.5)):
        f = obl(mm)
        d.text((x, base), ch, font=f, fill=(12, 12, 13), anchor="ls", stroke_width=max(2, int(0.45 * k)),
               stroke_fill=(236, 236, 232))
        if ch == "A":                                            # the star in the A of STAR
            cx, cy, rr = x + 0.42 * d.textlength("A", font=f), base - 2.6 * k, 1.6 * k
            pts = [(cx + (rr if i % 2 == 0 else 0.42 * rr) * math.sin(i * math.pi / 5),
                    cy - (rr if i % 2 == 0 else 0.42 * rr) * math.cos(i * math.pi / 5)) for i in range(10)]
            d.polygon(pts, fill=(236, 236, 232))
        x += d.textlength(ch, font=f) + 0.4 * k
    size = "19X1.85" if which == "rear" else "21X1.60"
    d.text((200 * k, H / 2 + 2.5 * k), "D.I.D  JAPAN     76 - 08  10 -       %s" % size, font=sans(5),
           fill=(44, 44, 47), anchor="ls")
    im.save(out)
    return out


def spoke_lines(spec, r_hub, y_left, y_right, flange_t=0.006, phase=0.0):
    """Spokes laced three-cross: SPOKES[wheel] / 2 per flange, alternately on the outer and the inner face of the
    flange, each to the rim hole 3 x 720 / n deg on (leading) or back (trailing). Returns (hub point, rim point,
    flange y, face sign)."""
    n = SPOKES["rear" if spec is REAR else "front"]
    per = n // 2
    cross = 3 * 4 * math.pi / n
    out = []
    for s, yf in ((1, y_left), (-1, y_right)):
        for i in range(per):
            ah = phase + 2 * math.pi * (i + (0.0 if s > 0 else 0.5)) / per
            ar = ah + (1 if i % 2 == 0 else -1) * cross
            e = s * (1 if i % 2 == 0 else -1)                    # which face of the flange the spoke lies on
            p0 = np.array([r_hub * math.cos(ah), yf + e * (flange_t / 2 + SPOKE_R), r_hub * math.sin(ah)])
            p1 = np.array([spec["r_in"] * math.cos(ar), s * 0.004, spec["r_in"] * math.sin(ar)])
            out.append((p0, p1, yf, e))
    return out


def _rim(m, spec, na, a0, n_t, which):
    """Rim on the tyre's own columns (M holds the tyre, its bead rings first and last): the beads are joined to the
    rim's seats by a hidden strip, so tyre and rim are one mesh. The side bands carry the printed strip (rim_print_*
    material, its own UVs) where the decals are. Returns the rim's first vertex."""
    prof = rim_profile(spec)
    ang = a0 + 2 * math.pi * np.arange(na) / na
    off = len(m.V)
    for r, y in prof:
        m.verts(np.stack([r * np.cos(ang), np.full(na, y), r * np.sin(ang)], axis=1))
    L, Ht = RIM_TEX["L"], RIM_TEX["H"]
    rm = 0.5 * (prof[3][0] + prof[4][0])                         # the band's middle radius
    a_dec = math.radians(RIM_DECAL[which])
    for p in range(len(prof)):
        p2 = (p + 1) % len(prof)
        band = {3: 1, 22: -1}.get(p)
        for i in range(na):
            i2 = (i + 1) % na
            f = (off + p * na + i, off + p * na + i2, off + p2 * na + i2, off + p2 * na + i)
            mat = "rim"
            if band:
                # arc length along the reading direction (clockwise seen from the band's side) from the decal start
                a_s = a_dec if band > 0 else a_dec + RIM_DECAL_LEN / rm       # the right side reads back down
                aa = [ang[i], ang[i] + 2 * math.pi / na]
                s = [band * (((aa[q] - a_s + math.pi) % (2 * math.pi)) - math.pi) * rm for q in (0, 1, 1, 0)]
                if -0.002 < min(s) and max(s) < L - 0.002 and max(s) - min(s) < 0.02:
                    mat = "rim_print_" + which[0]
                    rr = [prof[p][0], prof[p][0], prof[p2][0], prof[p2][0]]
                    # v grows outward: the letters' tops face the tyre (LEFT pair: upside down at the bottom)
                    m.uv[len(m.F)] = [(sj / L, 0.5 + (rj - rm) / Ht) for sj, rj in zip(s, rr)]
            m.face(f, mat)
    for ring_t, ring_r in ((0, 9), (n_t - 1, 17)):               # profile points 9 and 17: the two bead seats
        for i in range(na):
            i2 = (i + 1) % na
            m.face((ring_t * na + i, ring_t * na + i2, off + ring_r * na + i2, off + ring_r * na + i), "tyre")
    return off


def _hub(m, prof, mats, phase, seg=72):
    """Hub, seals and collars as one lathe (72 columns from PHASE: a vertex at every spoke hole)."""
    off = len(m.V)
    a = phase + 2 * math.pi * np.arange(seg) / seg
    grid(m, [np.stack([r * np.cos(a), np.full(seg, y), r * np.sin(a)], axis=1) for r, y in prof], "hub", mats=mats)
    return off


# Nipples (DR13: silver, about 13 mm showing below the rim's inner face, a round shank then hex flats with a
# chamfered end where the spoke goes in; each sits in a small raised eyelet on the rim's inner face; a few mm of
# rolled thread show on the spoke beyond it). Sizes EST from DR13 against the 6 mm flats.
NIPPLE = dict(shank_r=0.0028, shank=0.0040, hex_af=0.0060, hex=0.0085, thread=0.0030, eyelet_r=0.0042)
# (DR13 close-up beside the model's: the round collar is a third of the nipple, the hex flats the rest)


def _spokes(m, spec, r_hub, y_left, y_right, phase, flange_t=0.006):
    """Each spoke: its head on the far face of the flange, a rounded J-bend through the flange, the spoke, a few mm
    of rolled thread; then the nipple (round shank, hex flats, chamfer) with its eyelet on the rim."""
    q = NIPPLE
    for p0, p1, yf, e in spoke_lines(spec, r_hub, y_left, y_right, flange_t, phase):
        dn = (p1 - p0) / np.linalg.norm(p1 - p0)
        ey = np.array([0.0, e, 0.0])
        h = np.array([p0[0], yf - e * flange_t / 2, p0[2]])      # under the head
        bend = (ey + dn) / np.linalg.norm(ey + dn)
        tip = p1 - dn * (q["shank"] + q["hex"] + 0.0010)          # where the spoke enters the nipple
        path = [h - 0.0019 * ey, h - 0.0018 * ey, h - 0.0002 * ey, h, p0 - 0.0012 * ey, p0 + 0.0016 * bend,
                p0 + 0.0045 * dn, tip - dn * (q["thread"] + 0.0002)]
        rad = [0.0026, 0.0033, 0.0033, SPOKE_R, SPOKE_R, SPOKE_R, SPOKE_R, SPOKE_R]
        m.add(tube(path, rad, 8, "spoke"))
        th = [tip - dn * (q["thread"] + 0.0002 - k * 0.0004) for k in range(9)]   # rolled thread, 0.8 mm pitch
        m.add(tube(th, [SPOKE_R * (1.04 if k % 2 else 0.97) for k in range(9)], 8, "spoke", cap0=False))
        hx = q["hex_af"] / 2 / math.cos(math.pi / 6)
        m.add(tube([tip + dn * 0.0002, tip + dn * 0.0010, tip + dn * (0.0010 + q["hex"]),
                    tip + dn * (0.0012 + q["hex"])], [0.0024, hx * 0.92, hx, hx * 0.94], 6, "nipple"))
        m.add(tube([tip + dn * (0.0010 + q["hex"]), p1 + dn * 0.003], q["shank_r"], 12, "nipple"))
        er = np.array([p1[0], 0.0, p1[2]]) / np.hypot(p1[0], p1[2])  # the rim's radial direction at the hole
        m.add(lathe_at(p1, -er, [(0.0029, -0.0006), (0.0029, 0.0006), (q["eyelet_r"], 0.0006),
                                 (q["eyelet_r"] + 0.0006, 0.0), (q["eyelet_r"] + 0.0008, -0.0006)], 12, "rim"))


def lathe_at(c, axis, prof, seg, mat):
    """A small solid of revolution: PROF (radius, height along AXIS) about point C."""
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    hlp = np.array([0.0, 1.0, 0.0]) if abs(a[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(a, hlp)
    u /= np.linalg.norm(u)
    v = np.cross(a, u)
    ang = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    rings = [np.array([c + a * z + r * (math.cos(t) * u + math.sin(t) * v) for t in ang]) for r, z in prof]
    return grid(Mesh(), rings, mat)


def _stem(m, spec, ang, lock):
    """Valve (LEFT / RIGHT unwraps of the rims' inner ring: a black stem with a domed cap) or rim lock (a grey
    threaded stud; DR13: hex nut on a washer, the thread showing past the nut), through the rim toward the hub."""
    e = np.array([math.cos(ang), 0.0, math.sin(ang)])
    r0 = spec["r_in"]
    P = lambda d: e * (r0 + d)
    if lock:                                                     # M8 stud, washer 16 mm, 12 mm hex nut, EST
        m.add(tube([P(0.003), P(-0.0012)], 0.008, 16, "steel"))                         # washer
        m.add(bolt(P(-0.0012), -e, af=0.012, head_h=0.0065, flange_d=0.0150, mat="steel"))
        th = [P(-0.0070 - k * 0.000625) for k in range(17)]                             # 10 mm of M8 x 1.25 thread
        m.add(tube(th, [0.0040 if k % 2 == 0 else 0.0035 for k in range(17)], 10, "steel", cap0=False))
        m.add(tube([P(-0.0070 - 16 * 0.000625), P(-0.0175)], [0.0035, 0.0028], 10, "steel"))
    else:                                                        # TR4 valve: knurled nut, stem, black cap, EST
        m.add(tube([P(0.003), P(-0.0005)], 0.0042, 10, "steel"))
        m.add(tube([P(-0.0005), P(-0.0045)], 0.0058, 18, "steel"))                      # nut
        m.add(tube([P(-0.0045), P(-0.0100)], 0.0039, 12, "steel"))                      # threaded stem
        cap = [P(-0.0100), P(-0.0102), P(-0.0190), P(-0.0205), P(-0.0212)]
        m.add(tube(cap, [0.0040, 0.0044, 0.0044, 0.0036, 0.0020], 14, "rubber_black"))


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
    """Outer radius of the rear wave disc (RIGHT photo unwrapped about the disc's own centre on its plane,
    disc_polar_c / disc_edge, then disc_fit against the model): eight petals 45 deg apart, each a flat arc at r 120
    for 21 deg (SPEC 240 mm), a steep drop over 4.5 deg to r 109.5, 6 deg flat at the bottom and a ramp back over
    13.5 deg. Petals start at 63.5 + 45 k deg: the drops then fall at 84, 129, 174, 219, 264, 309 deg, the photo's
    at 131, 172, 222, 263, 313 (the first hidden by the caliper)."""
    a = np.asarray(a, float)
    d = np.degrees((a - math.radians(DISC_R_PETAL0)) % (math.pi / 4))
    r0, dep = DISC_R["r"], 0.0105
    drop = np.clip((d - 21.0) / 4.5, 0, 1)
    ramp = np.clip((d - 31.5) / 13.5, 0, 1)
    s = np.where(d < 21.0, 0.0, np.where(d < 25.5, 0.5 - 0.5 * np.cos(math.pi * drop),
                                         np.where(d < 31.5, 1.0, (1 - ramp) ** 1.2)))
    return r0 - dep * s


def rear_disc_r_in(a):
    """Inner edge: the braking band's inner edge at r 89.5 between the bolts, and at each of the four bolts an arm
    down to the bolt's boss (RIGHT unwrap: arms 15 deg wide at r 80, 30 deg where they leave the band; the bosses
    8 mm round the bolts on r 72)."""
    d = np.degrees((np.asarray(a, float) - DISC_R_FLAT + math.pi / 4) % (math.pi / 2) - math.pi / 4)
    w = np.clip((np.abs(d) - 9.0) / 9.0, 0, 1)                  # 0 on the arm, 1 on the band
    return 0.0630 + (0.0895 - 0.0630) * (0.5 - 0.5 * np.cos(math.pi * w))


DISC_R_PETAL0 = 63.5    # deg, the first petal's plateau start (above)


def rear_disc():
    a = np.radians(np.arange(0, 360, 1.25))
    ai = np.radians(np.arange(0, 360, 1.0))
    holes = [_pol(rear_disc_r_in(ai), ai)] + _pilots(DISC_R_BOLT_R, DISC_R_FLAT, 4)
    for j in range(28):                                          # RIGHT scan: holes at r 94, 103 and 111 mm
        for r, da in ((0.1115, 0.0), (0.1030, 4.3), (0.0945, 8.6)):
            ah = DISC_R_FLAT + j * 2 * math.pi / 28 + math.radians(da)
            if rear_disc_r(ah) - r > 0.0065 and r - rear_disc_r_in(ah) > 0.0065:
                holes.append(circle(0.003, 12, *_pol(r, ah)))
    m = _plate(_pol(rear_disc_r(a), a), holes, DISC_R["y"], DISC_R["t"], "disc", 0.007, chamfer=0.0004,
               chamfered=range(5, len(holes) - 1))               # drilled holes: a small chamfer each face
    for k in range(4):                                           # RIGHT unwrap: round socket heads on the bosses
        x, z = _pol(DISC_R_BOLT_R, DISC_R_FLAT + k * math.pi / 2)
        m.add(bolt((x, DISC_R["y"] - DISC_R["t"] / 2, z), (0, -1, 0), af=0.0125, head_h=0.005, mat="steel",
                   kind="cap"))
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
    """50 teeth (SPEC), aluminium, a truss of straight struts: LEFT photo unwrapped about the axle on the sprocket's
    plane (spr_polar: angle x radius). Six bolts on bosses (SPEC 153 mm circle, LEFT at 85 + k 60 deg); between the
    bolts a big window like a triangle standing on the bore ring (A: from r 74, 38 deg wide, to a rounded top at
    r 96, 20 deg wide); above each bolt a smaller one hanging from the tooth ring (B: 25 deg wide at r 108.5, 11 deg
    at its rounded bottom, r 90.5). Radii corrected for the photo's sprocket centre, which the bolt heads put 6.4 mm
    from the model's axle (circle fit: x -2.9, z +5.7 mm on the sprocket plane). Teeth chamfered on both faces (ANSI
    #520 tooth form: the top 3 mm of each tooth tapers to 55 % of its width)."""
    holes = [circle(SPROCKET_BORE_R, 72)] + _pilots(SPROCKET_BOLT_R, SPROCKET_BOLT0, 6)
    for k in range(6):
        ab = SPROCKET_BOLT0 + k * math.pi / 3
        am = ab + math.pi / 6
        a_win = [(0.0740, am + math.radians(d)) for d in (-19.0, 19.0)] + \
                [(0.0960, am + math.radians(d)) for d in (10.0, -10.0)]
        holes.append(_window(a_win, (0.005, 0.005, 0.007, 0.007)))
        b_win = [(0.0905, ab + math.radians(d)) for d in (-5.5, 5.5)] + \
                [(0.1085, ab + math.radians(d)) for d in (12.5, -12.5)]
        holes.append(_window(b_win, (0.0045, 0.0045, 0.004, 0.004)))
    m = _plate(sprocket_outline(50, phase), holes, CHAIN_Y, SPROCKET_T, "sprocket", 0.005, chamfer=0.0007,
               chamfered=range(7, 19))                          # the twelve windows (LEFT: a bright edge round each)
    rp = sprocket_r(50)
    V = np.asarray(m.V)
    r = np.hypot(V[:, 0], V[:, 2])
    f = np.clip(1.0 - 0.45 * (r - (rp + TIP_H - 0.003)) / 0.003, 0.55, 1.0)       # tooth chamfers
    V[:, 1] = CHAIN_Y + (V[:, 1] - CHAIN_Y) * f
    m.V = list(map(tuple, V))
    return m


def _window(corners, radii, n=4):
    """A window of a plate: corners (r, angle) in order round it, joined along arcs of constant radius where two
    corners share a radius and by straight lines otherwise, then rounded with RADII."""
    P = []
    for (r0, a0), (r1, a1) in zip(corners, corners[1:] + corners[:1]):
        if abs(r0 - r1) < 1e-9:
            for t in np.linspace(0, 1, 8, endpoint=False):
                P.append(_pol(r0, a0 + (a1 - a0) * t))
        else:
            P.append(_pol(r0, a0))
    P = _fillet(np.array(P), [radii[[i for i, (r, a) in enumerate(corners) if np.allclose(_pol(r, a), p)][0]]
                                 if any(np.allclose(_pol(r, a), p) for r, a in corners) else 0.0002 for p in P], n)
    return resample(np.vstack([P, P[:1]]), 0.002)[:-1]


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
# Plates (LEFT pair p_spr1 zoomed, 475832): grey steel, figure-of-eight: round ends about the pins and a smooth waist;
# the pins' riveted ends show as rings with a dark centre (the peening dimple). #520 plate height 15 mm, waist 12 mm
# (ANSI / D.I.D tables: 15.0 and about 0.8 of it); inner and outer plates alike (the photo shows no step).
PLATE_HR, PLATE_WAIST = 0.0075, 0.80
PIN_SEG = 10


def _plate_outline(length, hr):
    """Figure-of-eight outline of a link plate, centred, along x: two end arcs and smooth waists."""
    out = []
    for sx, a0 in ((1, -90.0), (-1, 90.0)):
        for t in np.radians(np.linspace(a0, a0 + 180.0, 9)):
            out.append((sx * length / 2 + hr * math.cos(t), hr * math.sin(t)))
        top = 1 if sx > 0 else -1                               # the waist after this arc (top after the front end)
        for f in (0.25, 0.5, 0.75):
            w = hr * (1 - (1 - PLATE_WAIST) * math.sin(math.pi * f))
            out.append((sx * length / 2 * (1 - 2 * f), top * w))
    return np.array(out)


def _chain(m, pins, y):
    """The chain as one connected mesh: every pin is a spool (riveted pin with its roller, a dimpled head at each
    end), and every plate's faces are meshed round the pins' own vertices, so the links hang together as on the
    real chain."""
    from scipy.spatial import Delaunay
    n = len(pins)
    a = np.linspace(0, 2 * math.pi, PIN_SEG, endpoint=False)
    cs, sn = np.cos(a), np.sin(a)
    ring = {}
    nl = len(CHAIN_LEVELS)
    for k, (x, z) in enumerate(pins):
        for li, dy in enumerate(CHAIN_LEVELS):
            r = ROLLER_R if li in (5, 6) else PIN_R
            ring[k, li] = m.verts(np.stack([x + r * cs, np.full(PIN_SEG, y + dy), z + r * sn], axis=1))
        for li in range(nl - 1):
            lo, hi = ring[k, li], ring[k, li + 1]
            for j in range(PIN_SEG):
                j2 = (j + 1) % PIN_SEG
                m.face((lo + j, hi + j, hi + j2, lo + j2), "chain_pin")
        for end, sg in ((0, -1), (nl - 1, 1)):                  # riveted head: a rim, then a dimple
            yy = y + CHAIN_LEVELS[end]
            rim = m.verts(np.stack([x + 0.65 * PIN_R * cs, np.full(PIN_SEG, yy + sg * 0.00025), z + 0.65 * PIN_R * sn], 1))
            c0 = m.verts([(x, yy - sg * 0.0003, z)])
            for j in range(PIN_SEG):
                j2 = (j + 1) % PIN_SEG
                f = (ring[k, end] + j, ring[k, end] + j2, rim + j2, rim + j)
                m.face(f if sg < 0 else f[::-1], "chain_pin")
                t = (rim + j, rim + j2, c0)
                m.face(t if sg < 0 else t[::-1], "chain_pin")
    for k in range(n):
        k2 = (k + 1) % n
        p, q = pins[k], pins[k2]
        d = q - p
        length = float(np.linalg.norm(d))
        ex = d / length
        ez = np.array([-ex[1], ex[0]])
        loc = _plate_outline(length, PLATE_HR)
        no = len(loc)
        out = (p + q) / 2 + loc[:, :1] * ex + loc[:, 1:] * ez
        pts = np.vstack([out, p + PIN_R * np.stack([cs, sn], axis=1), q + PIN_R * np.stack([cs, sn], axis=1)])
        tri = Delaunay(pts).simplices
        r1 = (tri >= no) & (tri < no + PIN_SEG)
        r2 = tri >= no + PIN_SEG
        keep = inside(out, pts[tri].mean(axis=1)) & ~np.all(r1, axis=1) & ~np.all(r2, axis=1)
        tri = tri[keep]
        u, v, w = pts[tri[:, 0]], pts[tri[:, 1]], pts[tri[:, 2]]
        flip = (v[:, 0] - u[:, 0]) * (w[:, 1] - u[:, 1]) - (v[:, 1] - u[:, 1]) * (w[:, 0] - u[:, 0]) < 0
        tri[flip] = tri[flip][:, ::-1]                           # counter-clockwise in (x, z): facing -y
        for la, lb in (((3, 4), (7, 8)) if k % 2 == 0 else ((1, 2), (9, 10))):
            idx = []
            for lev in (la, lb):
                o = m.verts([(xx, y + CHAIN_LEVELS[lev], zz) for xx, zz in out])
                idx.append(lambda i, o=o, lev=lev: o + i if i < no else (ring[k, lev] + i - no if i < no + PIN_SEG
                                                                         else ring[k2, lev] + i - no - PIN_SEG))
            for t in tri:
                m.face([idx[0](i) for i in t], "chain")
                m.face([idx[1](i) for i in t[::-1]], "chain")
            for i in range(no):
                i2 = (i + 1) % no
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


def rear_tyre():
    """Rear tyre: carcass grid with the red centre line, and the shaped knobs."""
    sec = Section(REAR, REAR_SECTION)
    m, na, a0, n_t = carcass(sec, REAR["pitches"], REAR_PHASE, 8, 0.054)
    rear_tread(m, sec, REAR["pitches"], a0, REAR)
    for side in (1, -1):
        sidewall(m, sec, REAR, side, REAR_WALL)
    return m, na, a0, n_t


def _wheel(spec, ctrl, rows, tread_phase, prof, mats, rh, yl, yr, spoke0, stems, tyre_fn):
    """Tyre and rim (one mesh: the beads sit on the rim's seats), hub with seals and collars, spokes, valve, rim lock."""
    m, na, a0, n_t = tyre_fn()
    _rim(m, spec, na, a0, n_t, "rear" if spec is REAR else "front")
    _hub(m, prof, mats, spoke0, 2 * SPOKES["rear" if spec is REAR else "front"])
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
    m = _wheel(FRONT, FRONT_SECTION, None, FRONT_PHASE, prof, mats, rh, yl, yr, FRONT_SPOKE0,
               ((53.8, False), (252.5, True)), front_tyre)       # valve, rim lock: unwraps (above)
    b0 = DISC_F_DEEP + math.pi / 6
    m.add(_plate(_lobes(6, 0.040, 0.063, 20.0, b0), [circle(0.0255, 48)] + _pilots(DISC_F_BOLT_R, b0, 6), yc + 0.003,
                 0.006, "hub", 0.008))
    m.add(front_disc())
    return _at(m, FA)


# Rear hub (LEFT photo, sprocket plane unwrapped and rectified: spr_plan / spr_overlay): a dark grey casting, RGB
# 96 / 99 / 102 in the photo where the bare aluminium sprocket reads 150 / 153 / 157 (r 40..56 mm, 180..300 deg);
# its sprocket-side end, seen through the sprocket's bore, carries twelve tear-shaped radial ribs (r 36..54 mm).
def _hub_ribs(m, y_face, n=12, side=1):
    """Radial ribs on the hub's sprocket-side end face (plane y = Y_FACE, facing +y), between r 36 and 54 mm."""
    for k in range(n):
        a = SPROCKET_BOLT0 + (k + 0.5) * 2 * math.pi / n

        def xf(s, t, z, a=a):
            s, t, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(t, float), np.asarray(z, float))
            ang = a + s / t
            return np.stack([t * np.cos(ang), y_face + side * z, t * np.sin(ang)], axis=-1)

        # tear-shaped, 8 mm across at the outer end, low and soft: the photo's ribs are subtle bumps of the casting
        # (coordinator's whole-wheel pair: 2.6 mm ribs with crisp edges read as bright marks on a dark disc)
        plan = [(-0.0018, 0.0360), (0.0018, 0.0360), (0.0042, 0.0490), (0.0, 0.0545), (-0.0042, 0.0490)]
        _knob(m, xf, _fillet(plan, 0.0020), lambda s, t: 0.0013, math.radians(40.0), mat="hub_cast", rnd=0.0010)


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
    mats += ["hub_cast"] * (len(prof) - 1 - len(mats) - 4) + ["rubber_black", "rubber_black", "steel", "steel"]
    i_ring = [i for i in range(len(prof) - 1) if prof[i][0] >= 0.0559 and prof[i + 1][0] >= 0.0559 and
              prof[i][1] > back - 0.0005][:2]
    for i in i_ring:                                            # the turned ring round the end face and the spigot
        mats[i] = "hub_machined"                                # (LEFT: a lighter annulus inside the sprocket bore)
    m = _wheel(REAR, REAR_SECTION, None, REAR_PHASE, prof, mats, rh, yl, yr, REAR_SPOKE0,
               ((84.8, False), (308.2, True)), rear_tyre)        # valve, rim lock: unwraps (above)
    m.add(_plate(_lobes(6, 0.066, 0.0875, 16.0, SPROCKET_BOLT0),
                 [circle(0.059, 72)] + _pilots(SPROCKET_BOLT_R, SPROCKET_BOLT0, 6), back + 0.006, 0.012, "hub_cast",
                 0.008))
    _hub_ribs(m, 0.5 * (y_end - 0.003 + y_end - 0.004))
    _hub_ribs(m, -0.0765, side=-1)                              # RIGHT pair p_disc1: the disc side has them too
    m.add(rear_sprocket(chain_path()[1]))
    for k in range(6):
        x, z = _pol(SPROCKET_BOLT_R, SPROCKET_BOLT0 + k * math.pi / 3)
        m.add(bolt((x, ys + SPROCKET_T / 2, z), (0, 1, 0), af=0.014, head_h=0.0045, mat="steel", kind="cap"))
        m.add(bolt((x, back, z), (0, -1, 0), af=0.012, head_h=0.008, mat="steel"))
    yd = DISC_R["y"] + DISC_R["t"] / 2
    m.add(_plate(_lobes(4, 0.060, 0.080, 14.0, DISC_R_FLAT), [circle(0.0565, 48)] + _pilots(DISC_R_BOLT_R, DISC_R_FLAT, 4),
                 yd + 0.004, 0.008, "hub_cast", 0.008))
    m.add(rear_disc())
    return _at(m, RA)


# ---------------------------------------------------------------- rear brake
# Nissin single-piston floating caliper, its bracket on the axle, guard and hose (fiche K95CF1700: bracket 7 with the
# pad retainer 4, caliper 6, pads 1, pad pin 8 under its plug, bleed screw 11 and cap 12, slide pin 5 with the boot 16
# in the bracket, the bracket's pin in the boot 15, guard 10 on two bolts 17).
# Places: RIGHT photo, 7x crop 1044..1192 x 1462..1560 (gz_r2) and its neighbours; each pixel cast on the plane of
# its feature (y from the REAR photo, 1.435 px a mm about the disc, which reads u 2100.7..2106.4 for y -0.068..-0.072)
# and carried from the photo's hub to the model's: the RIGHT disc bolt circle puts the photo's hub 8.4 mm above
# parts.RA (ledger 10), and the parts turn about the swingarm pivot onto RA as the swingarm does in detail_chassis.
# Shapes the photos do not show (the bracket behind the swingarm, the inboard finger) are EST, kept clear of the
# swingarm (detail_chassis), the disc and the hub.
CAL_PX = dict(                      # RIGHT (u, v), plane y
    piston=((1115.0, 1519.0), -0.1100),     # housing end: lower arc (1097, 1540) .. (1115, 1545.5) .. (1133, 1537): r 26.6 px
    pin_a=((1160.8, 1524.2), -0.1180),      # slide pin 5: black socket head in a 23 mm round end (30 px)
    pin_b=((1086.7, 1550.0), -0.1180),      # bracket pin and boot 15: 17 px round; REAR u 2141..2180 (y -0.096..-0.123)
    pad_pin=((1105.0, 1484.0), -0.1060),    # plug 8's hex (11 px); REAR: the pin across the top, v 1360..1369, u 2081..2161
    bleed0=((1128.0, 1483.0), -0.0990),     # bleed screw 11 at its boss ...
    bleed1=((1136.0, 1472.0), -0.1060),     # ... and the end of its cap 12 (the dark block 1127..1142 x 1468..1480)
    banjo=((1155.0, 1497.0), -0.1070),      # banjo eye under the guard's lower bar, the hose leaving it forward
    g_top=((1176.7, 1475.8), -0.1220),      # guard bolts 17: top-right boss (21 px round) ...
    g_low=((1063.3, 1530.8), -0.1220),      # ... and the lower-left one (18 px)
)
# guard 10 (black): a slim triangular frame over the piston (RIGHT pair p_cal1: the hook at the front end, the top
# bar, the boss of the top bolt, the lower bar down to the bottom corner; bars 5 to 7 px), a lug out to its lower
# bolt; two windows either side of a strut (rr34 crop 1290..1440 x 1410..1540: the piston behind the left one, the
# body behind the right one). rr34 also shows its front end folding in toward the wheel round the banjo to the top
# bolt (GUARD_FOLD)
GUARD_PX = [(1051.0, 1495.0), (1056.0, 1489.5), (1072.5, 1488.6), (1101.4, 1490.3), (1113.5, 1490.0), (1135.0, 1484.0),
            (1154.6, 1477.0), (1166.0, 1468.0), (1176.0, 1464.5), (1185.0, 1467.0), (1189.0, 1475.0), (1186.0, 1484.5),
            (1169.0, 1494.6), (1154.6, 1503.0), (1135.0, 1514.0), (1113.5, 1528.5), (1101.4, 1535.7), (1095.0, 1538.5),
            (1086.0, 1537.5), (1075.0, 1537.0), (1066.0, 1540.0), (1057.0, 1537.0), (1054.0, 1529.0), (1058.0, 1522.5),
            (1065.0, 1518.0), (1060.4, 1506.7)]
GUARD_WIN_PX = [[(1059.5, 1498.5), (1076.0, 1497.5), (1078.0, 1504.0), (1071.0, 1515.0), (1066.0, 1511.0)],
                [(1086.0, 1497.5), (1113.0, 1497.5), (1135.0, 1492.5), (1151.0, 1487.5), (1153.0, 1489.5), (1125.0, 1512.0),
                 (1103.0, 1527.0), (1096.0, 1527.0), (1088.0, 1512.0)]]
GUARD_FOLD = (0.112, 0.126, 0.0060)  # x about RA where the fold starts and ends, how far in (EST from rr34)
GUARD_Y = (-0.1310, -0.1180)        # REAR pair p_calb3: a black box from the body out to u 2195 (y -0.133): a deep
                                    # frame (rr34: its bars show deep side walls), 13 mm from the banjo bolt out
# the hose: RIGHT 6x crop 1170..1340 x 1460..1520 (gz_hose2): the black sleeve u 1185..1210 (11 mm across), then the
# 9 mm hose rising onto the swingarm's top (gz_hose: 2.4x crop 1150..1620 x 1330..1530); plane y -0.110
HOSE_PX = [(1210.0, 1497.5), (1250.0, 1494.0), (1300.0, 1488.0), (1330.0, 1484.0), (1360.0, 1481.0), (1460.0, 1452.0)]
HOSE_R = 0.0045                     # RIGHT: 11 px across at u 1250 (8.6 mm)
HOSE_END = (0.452, -0.100, 0.505)   # meets the brake_pedal part's hose (detail_chassis.py) on its bend, not
                                    # beside it (audit: the two ends overlapped 2.8 mm)
PHOTO_HUB = (-0.0004, 0.0084)       # RIGHT: the disc's bolt circle about parts.RA (ledger 10)
# swingarm top under the hose (detail_chassis's arm, ray cast on the built part at y -0.100..-0.125, flat across):
# z above the axle line at x; the hose keeps its radius + 1 mm over it
ARM_TOP = ((0.05, 0.07, 0.10, 0.14, 0.18, 0.20, 0.23, 0.26, 0.30, 0.34, 0.38, 0.42, 0.45),
           (0.0444, 0.0506, 0.0596, 0.0723, 0.0850, 0.0911, 0.0998, 0.1083, 0.1194, 0.1309, 0.1423, 0.1532, 0.1599))


def _cal_px(u, v, y):
    """RIGHT pixel cast on the plane y -> (x, z) about parts.RA: the photo's hub carried onto the model's by a turn
    about the swingarm pivot (and the small rest as a shift)."""
    import cams
    from parts import PIVOT
    P = np.asarray(cams.CAMS["right"].on_plane(np.array([u], float), np.array([v], float), "y", np.array([y], float)))[0]
    pv = np.array([PIVOT[0], PIVOT[2]])
    a0 = np.array([RA[0], RA[2]])
    ap = a0 + np.array(PHOTO_HUB)
    th = math.atan2(*(a0 - pv)[::-1]) - math.atan2(*(ap - pv)[::-1])
    Rm = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    fw = lambda q: pv + Rm @ (q - pv)
    return fw(np.array([P[0], P[2]])) + (a0 - fw(ap)) - a0


@functools.lru_cache(maxsize=None)
def caliper_points():
    """The caliper's measured places, (x, z) about RA (CAL_PX)."""
    return {k: tuple(_cal_px(u, v, y)) for k, ((u, v), y) in CAL_PX.items()}


def _slab(outline, y0, y1, r, mat, step=0.003, holes=(), origin=(0.0, 0.0), n=3):
    """Cast or moulded plate between the planes y0 < y1 with every edge rounded to R (quarter rounds of N steps):
    OUTLINE and HOLES are (x, z) loops about ORIGIN (resampled and smoothed here)."""
    loops = [_ccw(_round(outline, 0.0012, 2))] + [_ccw(_round(h, 0.0010, 2))[::-1] for h in holes]   # holes cw
    m = Mesh()
    ox, oz = origin
    rings = []
    for L in loops:
        hole = L is not loops[0]
        prof = [(r * (1 - math.sin(t)), y1 - r * (1 - math.cos(t))) for t in np.linspace(0, math.pi / 2, n + 1)]
        prof += [(r * (1 - math.cos(t)), y0 + r - r * math.sin(t)) for t in np.linspace(0, math.pi / 2, n + 1)]
        rs = []
        for ins, y in prof:                                      # INS: inset from the outline into the material
            if ins <= 0:                                          # _mitre offsets a ccw loop, + outward
                P = L
            else:
                P = _mitre(L[::-1], ins)[::-1] if hole else _mitre(L, -ins)
            rs.append(m.verts(np.stack([P[:, 0] + ox, np.full(len(P), y), P[:, 1] + oz], axis=1)))
        for a_, b_ in zip(rs, rs[1:]):
            for i in range(len(L)):
                j = (i + 1) % len(L)
                m.face((a_ + i, a_ + j, b_ + j, b_ + i), mat)
        rings.append(rs)
    # caps on the inset loops
    from scipy.spatial import Delaunay, cKDTree
    out_in = np.array([[m.V[rings[0][0] + i][0] - ox, m.V[rings[0][0] + i][2] - oz] for i in range(len(loops[0]))])
    hol_in = [np.array([[m.V[rs[0] + i][0] - ox, m.V[rs[0] + i][2] - oz] for i in range(len(L))])
              for rs, L in zip(rings[1:], loops[1:])]
    B = np.vstack([out_in] + hol_in)
    lo, hi = out_in.min(axis=0), out_in.max(axis=0)
    gx, gz = np.meshgrid(np.arange(lo[0] + step / 2, hi[0], step), np.arange(lo[1] + step / 2, hi[1], step))
    G = np.stack([gx.ravel(), gz.ravel()], axis=1)
    ok = inside(out_in, G)
    for h in hol_in:
        ok &= ~inside(h, G)
    G = G[ok]
    if len(G):
        G = G[cKDTree(B).query(G)[0] > 0.6 * step]
    P = np.vstack([B, G])
    tri = Delaunay(_off_hull(P)).simplices
    c = P[tri].mean(axis=1)
    keep = inside(out_in, c)
    for h in hol_in:
        keep &= ~inside(h, c)
    tri = tri[keep]
    a, b, cc = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    area = (b[:, 0] - a[:, 0]) * (cc[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (cc[:, 0] - a[:, 0])
    tri, area = tri[abs(area) > 1e-13], area[abs(area) > 1e-13]
    tri[area < 0] = tri[area < 0][:, ::-1]                      # ccw in (x, z): faces -y
    nb = len(B)
    ends = [rs[0] for rs in rings], [rs[-1] for rs in rings]     # first rings: y1 face, last rings: y0 face
    for face_y, starts, flip in ((y1, ends[0], True), (y0, ends[1], False)):
        idx = np.concatenate([np.arange(len(L)) + s for L, s in zip(loops, starts)])
        g0 = m.verts(np.stack([G[:, 0] + ox, np.full(len(G), face_y), G[:, 1] + oz], axis=1)) if len(G) else 0
        vid = np.concatenate([idx, g0 + np.arange(len(G))]) if len(G) else idx
        for t in tri:
            f = tuple(int(vid[k]) for k in t)
            m.face(f[::-1] if flip else f, mat)
    assert nb == len(idx)
    return m


def _off_hull(P):
    """Points for Delaunay: those lying ON an edge of the convex hull (straight runs of an outline) moved 2 microns
    inward, so that Qhull joins them to the inside instead of leaving a flat triangle along the edge (a hole in the
    cap once it is dropped)."""
    from scipy.spatial import ConvexHull
    h = ConvexHull(P)
    Q = P.copy()
    c = P.mean(axis=0)
    for eq in h.equations:                                       # n . p + d = 0 on the hull's edge lines
        d = P @ eq[:2] + eq[2]
        on = (abs(d) < 1e-9)
        on[h.vertices] = False
        Q[on] -= 2e-6 * eq[:2]                                   # inward
    return Q


def _arc_band(r0, r1, a0, a1, rc=0.004):
    """(x, z) outline of a band between radii r0 < r1 from angle a0 to a1 (rad), corners rounded RC."""
    n = max(4, int(abs(a1 - a0) * r1 / 0.003))
    a = np.linspace(a0, a1, n)
    P = np.vstack([_pol(r1, a), _pol(r0, a[::-1])])
    return _round_corners(P, rc)


def _round_corners(P, rc):
    """Light corner rounding of a fine outline: a smoothed resample (corners of about RC)."""
    return smooth_poly(resample(P, rc / 3), 3)


def _turned(c, axis, prof, seg, mat):
    """Closed solid of revolution about point C along AXIS: PROF (radius > 0, distance along AXIS), both ends capped,
    faces turned outward."""
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    hlp = np.array([0.0, 1.0, 0.0]) if abs(a[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(a, hlp)
    u /= np.linalg.norm(u)
    v = np.cross(a, u)
    ang = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    c = np.asarray(c, float)
    rings = [np.array([c + a * z + r * (math.cos(t) * u + math.sin(t) * v) for t in ang]) for r, z in prof]
    m = grid(Mesh(), rings, mat, cap0=True, cap1=True)
    V = np.asarray(m.V)
    vol = sum(np.dot(V[f[0]], np.cross(V[f[1]], V[f[2]])) + (np.dot(V[f[0]], np.cross(V[f[2]], V[f[3]]))
                                                             if len(f) == 4 else 0.0) for f in m.F)
    if vol < 0:
        m.F = [tuple(f[::-1]) for f in m.F]
    return m


def _ribbed(m, c, axis, r, r_rib, y0, y1, n_rib, mat):
    """Rubber boot along AXIS from distance y0 to y1 off C: N_RIB rounded ribs."""
    zs = np.linspace(y0, y1, 4 * n_rib + 1)
    rad = [r + (r_rib - r) * 0.5 * (1 - math.cos(2 * math.pi * k / 4)) for k in range(len(zs))]
    m.add(_turned(c, axis, list(zip(rad, zs)), 20, mat))


def rear_brake():
    """Rear caliper, bracket, pads, pins, bleeder, banjo, hose and guard (see CAL_PX)."""
    m = Mesh()
    C = {k: np.array(v) for k, v in caliper_points().items()}
    o = (RA[0], RA[2])
    Y = np.array([0.0, 1.0, 0.0])
    P3 = lambda q, y: np.array([RA[0] + q[0], y, RA[2] + q[1]])
    pc, pa, pb, pp = C["piston"], C["pin_a"], C["pin_b"], C["pad_pin"]
    bj, g_t, g_l = C["banjo"], C["g_top"], C["g_low"]
    ang_p = math.atan2(pc[1], pc[0])                             # the piston's angle about the axle (47 deg)
    # --- pads (1): steel backing with an ear on the pad pin (REAR: bronze ears above the caliper at u 2085..2089 and
    #     2114..2119), sintered lining 0.5 mm off the disc's faces; 46 mm long, r 97..119.5 (EST, inside the band)
    ac = ang_p + math.radians(1.5)
    band = _arc_band(0.0970, 0.1195, ac - math.radians(12.5), ac + math.radians(12.5), 0.004)
    yd0, yd1 = DISC_R["y"] - DISC_R["t"] / 2, DISC_R["y"] + DISC_R["t"] / 2
    for s, (yl0, yl1, yb0, yb1) in ((1, (yd1 + 0.0005, yd1 + 0.0060, yd1 + 0.0060, yd1 + 0.0100)),
                                     (-1, (yd0 - 0.0060, yd0 - 0.0005, yd0 - 0.0100, yd0 - 0.0060))):
        m.add(_slab(_mitre(band, -0.0010), min(yl0, yl1), max(yl0, yl1), 0.0006, "brake_pad", origin=o))
        m.add(_slab(band, yb0, yb1, 0.0005, "steel", origin=o))
        m.add(_slab(_hull([(pp[0], pp[1], 0.0055), (pp[0] - 0.006, pp[1] - 0.011, 0.004),
                           (pp[0] + 0.008, pp[1] - 0.009, 0.004)], 24), yb0 + 0.0003, yb1 - 0.0003, 0.0005,
                    "pad_ear", origin=o))
    # --- caliper body (6), dark cast aluminium (RIGHT: 56..66 where the swingarm reads 175)
    yo0 = yd0 - 0.0100 - 0.0002                                  # its inner face behind the outboard pad's backing
    main = _hull([(pc[0], pc[1], 0.0215), (pp[0], pp[1], 0.0070), (C["bleed0"][0], C["bleed0"][1], 0.0070),
                  (bj[0], bj[1], 0.0090)], 24)
    m.add(_slab(main, -0.1040, yo0, 0.0020, "caliper_r", origin=o))
    wing = _hull([(pc[0], pc[1], 0.0205), (pa[0], pa[1], 0.0115), (pb[0], pb[1], 0.0080), (g_l[0], g_l[1], 0.0065)], 24)
    m.add(_slab(wing, -0.1060, -0.0955, 0.0015, "caliper_r", origin=o))
    m.add(_slab(_hull([(bj[0], bj[1], 0.0080), (g_t[0], g_t[1], 0.0065)], 20), -0.1040, -0.0960, 0.0015, "caliper_r",
                origin=o))                                       # lug for the guard's top bolt
    # bridge over the disc's edge, ahead of the pad pin (rr34: the pin lies open across the top behind it)
    br = _arc_band(0.1215, 0.1350, math.radians(33.0), math.atan2(pp[1], pp[0]) - math.radians(4.8), 0.004)
    m.add(_slab(br, yo0 + 0.0010, yd1 + 0.0195, 0.0020, "caliper_r", origin=o))
    # inboard finger (EST shape): behind the inboard pad, up to an ear on the pad pin
    fin = _hull([(q[0], q[1], 0.0) for q in _arc_band(0.0960, 0.1220, ac - math.radians(14.0), ac + math.radians(14.0))]
                + [(pp[0], pp[1], 0.0065)], 40)
    m.add(_slab(fin, yd1 + 0.0145, yd1 + 0.0198, 0.0015, "caliper_r", origin=o))
    # piston housing: round, its end face turned (RIGHT: the face reads 100..110, the body 56..66)
    m.add(_turned(P3(pc, 0.0), Y, [(0.0205, -0.1100), (0.0205, yo0 + 0.0005)], 40, "caliper_r"))
    m.add(_turned(P3(pc, 0.0), Y, [(0.0170, -0.1124), (0.0195, -0.1117), (0.0204, -0.1101)], 40, "caliper_face"))
    # --- bracket (7): a slim cast arm from the axle (between the hub's collar and the swingarm's inner face) up behind
    #     the swingarm to the bracket pin and the slide pin's bore (REAR: a darker arm at u 2116..2136 between the disc
    #     and the arm, v 1430..1514); 7.7 mm plate, its outline EST round the measured pins
    yb = (-0.0935, -0.0858)
    bo = [(0.0, -0.021), (0.015, -0.0145), (0.021, -0.003), (0.034, 0.018), (0.055, 0.036), (0.075, 0.042),
          (0.093, 0.048), (pa[0] - 0.0076, pa[1] - 0.0157), (pa[0], pa[1] - 0.0100), (pa[0] + 0.0094, pa[1] - 0.0057),
          (pa[0] + 0.0099, pa[1] + 0.0053), (pa[0] + 0.0014, pa[1] + 0.0100), (pa[0] - 0.0076, pa[1] + 0.0053),
          (pa[0] - 0.0136, pa[1] - 0.0057), (0.088, 0.061), (0.075, 0.0555), (pb[0] + 0.0090, pb[1] - 0.0047),
          (pb[0] + 0.0050, pb[1] + 0.0073), (pb[0] - 0.0020, pb[1] + 0.0085), (pb[0] - 0.0085, pb[1] - 0.0030),
          (0.038, 0.044), (0.022, 0.026), (0.010, 0.0195), (-0.006, 0.020), (-0.019, 0.009), (-0.021, -0.006),
          (-0.013, -0.017)]
    m.add(_slab(np.array(bo), yb[0], yb[1], 0.0015, "bracket_r", holes=[circle(0.0135, 40)], origin=o))
    # REAR pair p_calb3: away from the axle the arm is deeper, its inboard face at u 2115 (y -0.079): a rib inboard
    # of the plate from 32 mm out (clear of the hub's collar; 2 mm off the disc bolts' heads at y -0.077)
    rib = [q for q in bo if np.hypot(*q) > 0.032]
    m.add(_slab(_fillet(_ccw(np.array(rib)), 0.004, 4), -0.0860, -0.0790, 0.0015, "bracket_r", origin=o))
    # pad retainer (4) is inside the caliper: not seen. Slide pin (5): screwed into the body's front boss, its boot
    # (16) between body and bracket; the bracket's pin in the rear boss under its ribbed boot (15)
    m.add(_turned(P3(pa, 0.0), Y, [(0.0115, -0.0955), (0.0115, -0.1110), (0.0100, -0.1125)], 32, "caliper_r"))
    m.add(bolt(P3(pa, -0.1125), (0, -1, 0), af=0.0135, head_h=0.0055, mat="anod_black", kind="cap"))
    _ribbed(m, P3(pa, 0.0), -Y, 0.0075, 0.0088, 0.0937, 0.0953, 1, "rubber_black")
    m.add(tube([P3(pb, yb[0] + 0.0002), P3(pb, -0.1150)], 0.0042, 16, "steel"))
    m.add(_turned(P3(pb, 0.0), Y, [(0.0080, -0.0956), (0.0080, -0.1140)], 28,
                   "caliper_r"))
    _ribbed(m, P3(pb, 0.0), -Y, 0.0068, 0.0076, 0.1140, 0.1222, 3, "rubber_black")
    # --- pad pin (8) across the top, from the finger's ear to the outboard boss, under its hex plug
    m.add(tube([P3(pp, yd1 + 0.0150), P3(pp, -0.1000)], 0.0025, 16, "steel"))
    m.add(_turned(P3(pp, 0.0), Y, [(0.0032, yd1 + 0.0150), (0.0032, yd1 + 0.0128)], 16, "steel"))
    m.add(bolt(P3(pp, -0.1040), (0, -1, 0), af=0.010, head_h=0.0050, flange_d=0.0125, mat="steel"))
    # --- bleed screw (11) and its rubber cap (12), up and outward from the body's top
    b0 = P3(C["bleed0"], -0.0990)
    b1 = P3(C["bleed1"], -0.1060)
    db = (b1 - b0) / np.linalg.norm(b1 - b0)
    m.add(bolt(b0, db, af=0.008, head_h=0.0045, flange_d=0.0095, mat="steel"))
    m.add(tube([b0 + 0.004 * db, b0 + 0.0075 * db], 0.0026, 12, "steel"))
    m.add(_turned(b0, db, [(0.0036, 0.0068), (0.0042, 0.0080), (0.0042, 0.0140), (0.0034, 0.0152)], 16, "rubber_black"))
    # --- banjo on the body's face, its bolt along y, two sealing washers; the hose leaves it forward
    yf = -0.1040
    for y0_, y1_, r_, mat in ((yf, yf - 0.0012, 0.0072, "brass"), (yf - 0.0012, yf - 0.0102, 0.0078, "steel"),
                              (yf - 0.0102, yf - 0.0114, 0.0072, "brass")):
        m.add(_turned(P3(bj, 0.0), Y, [(r_, y0_), (r_, y1_)], 24, mat))
    m.add(bolt(P3(bj, yf - 0.0114), (0, -1, 0), af=0.012, head_h=0.0024, flange_d=0.0140, mat="steel"))
    yh = yf - 0.0057
    e = np.array([1.0, 0.0, 0.0])
    s0 = P3(bj, yh) + 0.0070 * e
    m.add(tube([s0, s0 + 0.0040 * e], 0.0042, 14, "steel"))                       # neck of the banjo
    # RIGHT gz_hose2: a black clamp ring on the banjo's neck (u 1160..1172), then the black crimped sleeve to u 1210
    m.add(tube([s0 + 0.0030 * e, s0 + 0.0040 * e, s0 + 0.0110 * e, s0 + 0.0120 * e], [0.0050, 0.0058, 0.0058, 0.0050],
               20, "anod_black"))
    sl = [s0 + 0.0120 * e, s0 + 0.0130 * e, s0 + 0.0200 * e, s0 + 0.0210 * e, s0 + 0.0220 * e, s0 + 0.0300 * e,
          s0 + 0.0370 * e, s0 + 0.0390 * e]                                       # sleeve, two grooves
    m.add(tube(sl, [0.0048, 0.0054, 0.0054, 0.0049, 0.0054, 0.0054, 0.0054, 0.0047], 20, "rubber_black"))
    from scipy.interpolate import CubicSpline
    hp_ = [_cal_px(u, v, -0.110) for u, v in HOSE_PX]
    way = [s0 + 0.0380 * e]
    for q in hp_:
        z_min = float(np.interp(q[0], *ARM_TOP)) + HOSE_R + 0.0010
        way.append(np.array([RA[0] + q[0], -0.110, RA[2] + max(q[1], z_min)]))
    for x in (0.385,):                                          # onward along the arm's top, EST
        way.append(np.array([x, -0.104, RA[2] + float(np.interp(x, *ARM_TOP)) + HOSE_R + 0.0025]))
    # into the pedal part's hose at its bend (round 2's joint): that hose comes down from the master cylinder's
    # banjo to HOSE_END and runs on 20 mm forward past it (detail_chassis), so the two overlap there (reported)
    way += [np.array([0.425, -0.098, 0.488]), np.array(HOSE_END)]
    way = np.array(way)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(way, axis=0), axis=1))])
    t = np.linspace(0, s[-1], 70)
    path = CubicSpline(s, way)(t)
    on_arm = (path[:, 0] > RA[0] + 0.15) & (path[:, 0] < 0.43)     # lying on the arm: never into it (spline sag)
    z_arm = RA[2] + np.interp(path[:, 0] - RA[0], *ARM_TOP) + HOSE_R + 0.0012
    path[on_arm, 2] = np.maximum(path[on_arm, 2], z_arm[on_arm])
    rad = HOSE_R - (HOSE_R - 0.0042) * np.clip((t - (s[-1] - 0.07)) / 0.05, 0, 1)   # the pedal part's 4.2 mm hose
    m.add(tube(path, rad, 12, "cable"))
    _caliper_guard(m, C)
    return m


def _caliper_guard(m, C):
    """Guard 10 over the caliper's outer face (GUARD_PX cast on its plane), black, two windows, its front end folded
    in toward the wheel (GUARD_FOLD), on two black socket bolts (17) whose bosses stand off the body."""
    yg = 0.5 * (GUARD_Y[0] + GUARD_Y[1])
    outer = np.array([_cal_px(u, v, yg) for u, v in GUARD_PX])
    wins = [np.array([_cal_px(u, v, yg) for u, v in w]) for w in GUARD_WIN_PX]
    wins = [_fillet(_ccw(w), 0.0015, 3) for w in wins]
    g = _slab(_fillet(_ccw(outer), 0.0010, 2), GUARD_Y[0], GUARD_Y[1], 0.0008, "plastic_black", holes=wins,
              origin=(RA[0], RA[2]), step=0.002)
    x0, x1, dy = GUARD_FOLD
    fold = lambda x: dy * (0.5 - 0.5 * np.cos(math.pi * np.clip((x - RA[0] - x0) / (x1 - x0), 0, 1)))
    V = np.asarray(g.V)
    V[:, 1] += fold(V[:, 0])
    g.V = [tuple(v) for v in V]
    m.add(g)
    for k, y_in in (("g_top", -0.1040), ("g_low", -0.1060)):
        q = C[k]
        c = np.array([RA[0] + q[0], 0.0, RA[2] + q[1]])
        f = float(fold(c[0]))
        m.add(_turned(c, (0, 1, 0), [(0.0068, GUARD_Y[0] + f + 0.0004), (0.0075, GUARD_Y[0] + f + 0.0012),
                                     (0.0075, y_in - 0.0002)], 28, "plastic_black"))
        m.add(bolt(c + np.array([0.0, GUARD_Y[0] + f, 0.0]), (0, -1, 0), af=0.0100, head_h=0.0050, mat="anod_black",
                   kind="cap"))


def _hull(circles, n=20):
    """Convex outline (x, z) round circles (x, z, r)."""
    from scipy.spatial import ConvexHull
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    pts = np.vstack([np.stack([x + r * np.cos(a), z + r * np.sin(a)], axis=1) for x, z, r in circles])
    return pts[ConvexHull(pts).vertices]


if __name__ == "__main__":                       # python3 detail_wheels.py: repaint the rim strips
    import os
    for w in ("rear", "front"):
        print(rim_texture(w, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "textures", "stock",
                                          "rim_%s.png" % w)))

PARTS = {name: (lambda fn=fn: _compact(fn())) for name, fn in
         (("front_wheel", front_wheel), ("rear_wheel", rear_wheel), ("drive", drive), ("rear_brake", rear_brake))}
