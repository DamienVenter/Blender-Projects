"""Chassis detail (plugin of parts.py): frame and subframe, swingarm, chain guide, Pro-Link, shock, exhaust, footpegs
and the rear brake controls of the stock 2026 CRF250R.

Every number is tagged with its source:
  SPEC   research/crf250r-2026.md
  LEFT / RIGHT / FRONT / REAR / TOP   Honda's studio photo, with the pixel (u, v), row or column it was read at;
         pixels become metres through the calibrated cameras (cams.py): `_px(view, u, v, axis, value)`
  OUT2   outline extracted from the photos' material map (research/bike-outlines2.json)
  EST    not visible in any photo: size of the real part or a clearance, estimated

Things the photos settle (2026-11-10):
  * Pro-Link: the three bolts of the cushion arm and the link's frame bolt are seen from both sides (LEFT px
    (2469,1552) (2386,1607) (2471,1617) (2298,1558); RIGHT px (1524,1551) (1611,1606) (1524,1608) (1702,1557)).
    The shock's clevis bolt shows through a hole in the one-piece link.
  * The muffler's side outline (OUT2, right photo) is cut by the side panel: its top edge is only seen at the rear
    (z 0.893 for x 0..0.024; left photo row 878 at column 2950). The rear photo gives the end cap (rows 710..890:
    y -0.082..-0.195) and the outlet (dark disc centred on pixel (2205, 787): y -0.138, z 0.845).
  * The header leaves the head hidden by the radiator, comes down in front of the engine on the right of the down
    tube (front edge x 0.989 in the left photo), turns back at z 0.46 and climbs along the right side. No springs
    show at its joints in the right photo: two welds and two clamps.
  * The rear master cylinder carries its reservoir on top (one casting in the right photo): there is no separate
    reservoir hose on this bike, only the pressure hose to the caliper along the swingarm.
  * parts.PEG is a reading on the photo's centre plane. Cast on the plane they are on, the peg's teeth are at
    z 0.40 to 0.42: the pegs follow the photos and the spec (422 mm). parts.PIVOT is the pivot cap cast on its plane.

Normals point out of every solid and parts that only touch a neighbour stop 0.2 to 0.5 mm short of it: the audit
(audit.py) measures clash depth along the normals and counts intersecting faces.
"""
import math

import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.spatial import ConvexHull, cKDTree

import cams
from geom import Mesh, bolt, box, circle, frame_z, grid, inside, plate2d, resample, rounded_rect, smooth_poly, tube
from parts import CHAIN_Y, P2, PEG, PIVOT, RA, R_REAR, STEER0, UP, chain_top

REPLACES = ["frame", "swingarm", "shock", "exhaust", "controls"]
MATERIALS = {"shock_spring": dict(rgb=(28, 28, 30), metal=0.7, rough=0.4),   # EST: dark behind the plate (LEFT col 2360)
             "alu_weld": dict(rgb=(186, 186, 190), metal=1.0, rough=0.42),
             "alu_satin": dict(rgb=(198, 198, 202), metal=1.0, rough=0.36),   # cast ends: no brushing (aniso streaked them)
             "axle_block": dict(rgb=(172, 172, 176), metal=1.0, rough=0.28),  # rr34: as light as the casting, bright edges
             "zinc": dict(rgb=(205, 205, 210), metal=1.0, rough=0.22),        # bright plated adjusters (LEFT, lr34)
             "groove": dict(rgb=(40, 40, 42), metal=1.0, rough=0.6),
             "bore": dict(rgb=(10, 10, 11), metal=0.3, rough=0.7)}            # the hollow axle's inside: black in every photo
CLASS = {"shock_spring": "black"}
Y3 = np.array([0.0, 1.0, 0.0])


# ---------------------------------------------------------------- helpers
def _px(view, u, v, axis, val):
    """3D point seen at pixel (u, v) of a studio photo, on the plane AXIS = VAL."""
    return cams.CAMS[view].on_plane(np.array([float(u)]), np.array([float(v)]), axis, val)[0]


def spline(pts, n):
    P = np.asarray(pts, float)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    return CubicSpline(s, P)(np.linspace(0, s[-1], n))


def turned(a, d, prof, mat, seg=20, cap0=True, cap1=True):
    """Lathe about any axis: rings of radius r at distance s from A along D, for (s, r) in PROF."""
    a, d = np.asarray(a, float), np.asarray(d, float)
    d = d / np.linalg.norm(d)
    ang = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    c = np.stack([np.cos(ang), np.sin(ang), np.zeros(seg)], axis=1) @ frame_z(d).T
    return grid(Mesh(), [a + d * s + c * r for s, r in prof], mat, cap0=cap0, cap1=cap1)


def hollow(a, d, r_out, r_in, h, mat, seg=20):
    """Tube with a bore (bosses, eyes, the outlet): closed all round, open through the middle."""
    return turned(a, d, [(0, r_in), (0, r_out), (h, r_out), (h, r_in), (0, r_in)], mat, seg, False, False)


def bar(path, w, h, mat, cap0=True, cap1=True):
    """Rounded rectangular section W (sideways) x H swept along PATH; W and H may vary along it."""
    P = np.asarray(path, float)
    sec = rounded_rect(1.0, 1.0, 0.22, 3)
    wh = np.stack([np.broadcast_to(np.asarray(w, float), (len(P),)), np.broadcast_to(np.asarray(h, float), (len(P),))], 1)
    return tube(P, wh, len(sec), mat, cap0, cap1, section=sec)


def _edge_dist(loops):
    """Exact distance from a 2D point to the nearest edge of closed polygons. (Taken to sample points of the outline
    it was up to 0.75 mm off, and the quarter-round edge is steep there: the rim's height changed from vertex to
    vertex and the plates' edges came out serrated.)"""
    A = np.vstack(loops)
    AB = np.vstack([np.roll(q, -1, axis=0) for q in loops]) - A
    L2 = np.maximum((AB * AB).sum(axis=1), 1e-18)

    def f(u, v):
        ap = np.array([u, v]) - A
        d = ap - AB * np.clip((ap * AB).sum(axis=1) / L2, 0.0, 1.0)[:, None]
        return math.sqrt(float((d * d).sum(axis=1).min()))
    return f


def slab(outline, mid, t, mat, r=0.003, step=0.007, holes=(), to=None, mirror=True, fine=False):
    """Plate cut to OUTLINE (2D) with rounded edges: mid(u, v) is the mid-surface's offset along the normal, T the
    thickness, R the edge radius, to(u, v, w) the map to 3D (MIRROR: it swaps handedness, as (u, v, w) -> (x, w, v)
    does). The side view stays the outline exactly; faces are turned so that every normal points out.
    FINE: three rows of vertices follow the outline through the quarter-round edge (at 0.2, 0.6 and 1.0 R), with
    the grid fine enough for plate2d to keep every one of them; without it plate2d thins the second row wherever
    the rows are closer than 0.45 STEP and the rounding turns into irregular facets (the frame's crumpled look)."""
    o = np.asarray(outline, float)
    r = min(r, 0.4 * t)
    ccw = float(np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])) > 0
    holes = [np.asarray(h, float) if ccw else np.asarray(h, float)[::-1] for h in holes]     # circle() runs counter-clockwise
    dist = _edge_dist([o] + holes)
    rings = (0.3 * r, r)
    if fine:
        step, rings = min(step, 0.85 * r), (0.2 * r, 0.6 * r, r)
    mid_f = mid if callable(mid) else (lambda u, v: mid)

    def f(u, v, w):
        d = dist(u, v)
        k = 0.0 if d >= r else r - math.sqrt(max(r * r - (r - d) ** 2, 0.0))
        half = t / 2 - k
        return to(u, v, mid_f(u, v) + (half if w > 0 else -half))
    m = plate2d(o, holes, 1.0, mat, f, step=step, rings=rings)
    flip_rim = mirror == ccw
    m.F = [q[::-1] if (mirror if len(q) == 3 else flip_rim) else q for q in m.F]
    return m


def _plate2d(outer, holes, mat, to3d, step, rings, hole_rings=None, hole_step=None, grid_step=None):
    """geom.plate2d with its rows of vertices following the holes too (a window's rounded rim needs them as much as
    the outline does: on the bare grid it came out frilled)."""
    from scipy.spatial import Delaunay
    hst = step if hole_step is None else hole_step
    loops = [resample(outer, step * 0.7)] + [resample(h, hst * 0.7) for h in holes]
    B = np.vstack(loops)
    tree = cKDTree(B)
    rows = []
    for k, L in enumerate(loops):
        stp = step if k == 0 else hst
        t = np.roll(L, -1, axis=0) - np.roll(L, 1, axis=0)
        n = np.stack([t[:, 1], -t[:, 0]], axis=1)
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        probe = inside(L, (L + 0.3 * step * n)[::5]).mean() > 0.5
        if (k == 0) != probe:                                      # into the material: inward on the outline, out of holes
            n = -n
        for d in (rings if k == 0 or hole_rings is None else hole_rings):
            Q = L + d * n
            ok = inside(loops[0], Q) & (tree.query(Q)[0] > 0.8 * d)
            for h in loops[1:]:
                ok &= ~inside(h, Q)
            Q = Q[ok]
            if rows and len(Q):
                Q = Q[cKDTree(np.vstack(rows)).query(Q)[0] > 0.45 * stp]
            if len(Q) > 1:
                keep = [0]
                for i in range(1, len(Q)):
                    if np.hypot(*(Q[i] - Q[keep[-1]])) > 0.45 * stp:
                        keep.append(i)
                Q = Q[keep]
            if len(Q):
                rows.append(Q)
    R = np.vstack(rows) if rows else np.zeros((0, 2))
    lo, hi = loops[0].min(axis=0), loops[0].max(axis=0)
    gs = step if grid_step is None else max(grid_step, step)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0], gs), np.arange(lo[1], hi[1], gs))
    G = np.stack([gx.ravel(), gy.ravel()], axis=1)
    ok = inside(loops[0], G)
    for h in loops[1:]:
        ok &= ~inside(h, G)
    G = G[ok]
    if len(G):
        G = G[tree.query(G)[0] > max(rings) + 0.5 * gs]
        if len(R):
            G = G[cKDTree(R).query(G)[0] > 0.45 * gs]
    P = np.vstack([B, R, G])
    tri = Delaunay(P).simplices
    c = P[tri].mean(axis=1)
    keep = inside(loops[0], c)
    for h in loops[1:]:
        keep &= ~inside(h, c)
    tri = tri[keep]
    m = Mesh()
    top = m.verts([to3d(u, v, 0.5) for u, v in P])
    bot = m.verts([to3d(u, v, -0.5) for u, v in P])
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


def slab2(outline, mid, t, mat, r=0.002, step=0.004, holes=(), to=None, mirror=True, r_hole=None):
    """slab() with rows of vertices at 0.2, 0.6 and 1.0 R inside the outline AND round every hole (rounded rims on
    windows and bores as clean as on the outline). R_HOLE: the holes' own edge radius (a crisp window in a soft
    casting)."""
    o = np.asarray(outline, float)
    r = min(r, 0.4 * t)
    rh = r if r_hole is None else min(r_hole, 0.4 * t)
    ccw = float(np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])) > 0
    hs = []
    for h in holes:
        h = np.asarray(h, float)
        hc = float(np.sum(h[:, 0] * np.roll(h[:, 1], -1) - np.roll(h[:, 0], -1) * h[:, 1])) > 0
        hs.append(h if hc == ccw else h[::-1])
    dist_o = _edge_dist([o])
    dist_h = _edge_dist(hs) if hs else (lambda u, v: 1.0)
    gstep, step = step, min(step, 0.85 * r)
    mid_f = mid if callable(mid) else (lambda u, v: mid)

    def rnd(d, rr):
        return 0.0 if d >= rr else rr - math.sqrt(max(rr * rr - (rr - d) ** 2, 0.0))

    def f(u, v, w):
        k = max(rnd(dist_o(u, v), r), rnd(dist_h(u, v), rh))
        half = t / 2 - k
        return to(u, v, mid_f(u, v) + (half if w > 0 else -half))
    m = _plate2d(o, hs, mat, f, step, (0.2 * r, 0.6 * r, r), (0.2 * rh, 0.6 * rh, rh), min(step, 0.85 * rh), gstep)
    flip_rim = mirror == ccw
    m.F = [q[::-1] if (mirror if len(q) == 3 else flip_rim) else q for q in m.F]
    return m


def _outward(m):
    """Turn every face of a closed mesh round if its signed volume is negative (normals pointing in)."""
    V = np.asarray(m.V, float)
    vol = 0.0
    for f in m.F:
        a = V[f[0]]
        for i in range(1, len(f) - 1):
            vol += float(np.dot(a, np.cross(V[f[i]], V[f[i + 1]])))
    if vol < 0:
        m.F = [f[::-1] for f in m.F]
    return m


def _xz(u, v, w):
    return (u, w, v)


def hull(circles, n=18):
    """Convex outline around circles (cx, cz, r): lugs, links and brackets between bolt bosses."""
    P = np.vstack([circle(r, n, cx, cz) for cx, cz, r in circles])
    return P[ConvexHull(P).vertices]


def coil(a, b, r, wire, turns, mat, seg=8, dead=0.75, per=26):
    """Coil spring from A to B: mean radius R, wire radius WIRE, TURNS in all, of which DEAD closed at each end."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = np.linalg.norm(b - a)
    d = (b - a) / L
    R = frame_z(d)
    th = np.linspace(0, turns, int(turns * per) + 1)
    pe = wire * 2.05
    act = (L - 2 * dead * pe) / (turns - 2 * dead)
    h = np.where(th < dead, th * pe, np.where(th > turns - dead, L - (turns - th) * pe, dead * pe + (th - dead) * act))
    pts = [a + d * hh + R @ np.array([r * math.cos(2 * math.pi * q), r * math.sin(2 * math.pi * q), 0.0]) for q, hh in zip(th, h)]
    return tube(pts, wire, seg, mat)


def _rings(c, d, prof, seg, phase=0.0):
    """Rings of a lathe about axis D through C. PROF: (s, r) for a circle, (s, r, af) for a circle clipped by a hexagon
    AF across flats (r large: the plain hexagon; r between AF/2 and the corners: a 30 deg chamfer's cut). Corners of
    the hexagon at PHASE + k 60 deg from the frame's first axis, so SEG must be a multiple of 6."""
    c, d = np.asarray(c, float), np.asarray(d, float)
    d = d / np.linalg.norm(d)
    R = frame_z(d)
    ang = phase + np.linspace(0, 2 * math.pi, seg, endpoint=False)
    cs = np.stack([np.cos(ang), np.sin(ang), np.zeros(seg)], axis=1) @ R.T
    out = []
    for p in prof:
        s, r = p[0], p[1]
        rr = np.full(seg, float(r))
        if len(p) > 2 and p[2]:
            hx = p[2] / 2 / np.cos(((ang - phase) % (math.pi / 3)) - math.pi / 6)
            rr = np.minimum(rr, hx)
        out.append(c + d * s + cs * rr[:, None])
    return out


def lathe2(c, d, prof, mat, seg=48, phase=0.0, cap0=False, cap1=False):
    """Lathe with hexagon rings (see _rings). Profile clockwise in the (s right, r up) plane: normals point out."""
    return grid(Mesh(), _rings(c, d, prof, seg, phase), mat, cap0=cap0, cap1=cap1)


def _chamfer_rings(af, s0, s1, sign, face_r=None, n=4):
    """Rings of a 30 deg chamfer that cuts a hexagon's corners from a face at S0 toward S1 (direction SIGN)."""
    r0 = face_r if face_r is not None else af / 2
    reach = (af / 2 / math.cos(math.pi / 6) - r0) / math.tan(math.radians(60))
    return [(s0 + sign * reach * k / n, r0 + reach * k / n * math.tan(math.radians(60)), af) for k in range(n + 1)]


def hexnut(c, d, af, h, bore, mat="steel", phase=0.0, ch0=True, ch1=True, seg=48):
    """Hexagon nut AF across flats, H thick, from C along D, with 30 deg chamfers on both faces (bearing-face circle
    = AF) and its bore. ISO 4032 shape."""
    lo = _chamfer_rings(af, 0.0, h, 1) if ch0 else [(0.0, 1.0, af)]
    hi = _chamfer_rings(af, h, 0.0, -1)[::-1] if ch1 else [(h, 1.0, af)]
    prof = [(0.0, bore)] + lo + hi + [(h, bore), (0.0, bore)]
    return lathe2(c, d, prof, mat, seg, phase)


def hexbolt(c, d, af, h, flange_d=None, flange_h=0.0, mat="bolt", phase=0.0, seg=48):
    """Flange bolt head (Honda: 8 mm heads on M6, 10 on M8, 12 on M10, 14 on M12) standing on C along D: a round
    flange with a rounded rim, the hexagon above it with its top chamfered (30 deg) and a dished top face."""
    prof = []
    if flange_d:
        rf, ft = flange_d / 2, max(flange_h, 0.0008)
        prof += [(0.0, 0.0001), (0.0, rf - 0.0003), (0.0002, rf), (ft - 0.0002, rf), (ft, rf - 0.0004)]
        base = ft
    else:
        prof += [(0.0, 0.0001)]
        base = 0.0
    prof += [(base, 1.0, af)] + _chamfer_rings(af, h, base, -1)[::-1] + [(h, af * 0.40), (h - 0.0003, af * 0.30),
                                                                       (h - 0.0003, 0.0001)]
    return lathe2(c, d, prof, mat, seg, phase, cap0=True, cap1=True)


def thread(c, d, r_maj, pitch, length, mat="bolt", seg=24, per=6, depth=None):
    """Threaded shank (ISO metric: 60 deg flanks, depth 0.54 P) from C along D: a helical ridge, closed at both ends."""
    c, d = np.asarray(c, float), np.asarray(d, float)
    d = d / np.linalg.norm(d)
    R = frame_z(d)
    depth = 0.54 * pitch if depth is None else depth
    ang = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    cs = np.stack([np.cos(ang), np.sin(ang), np.zeros(seg)], axis=1) @ R.T
    n = max(int(length / pitch * per), 2)
    rings = []
    for s in np.linspace(0, length, n + 1):
        ph = (s / pitch - ang / (2 * math.pi)) % 1.0
        tri = 1 - np.abs(2 * ph - 1)                                   # 0 at the root, 1 at the crest
        rr = r_maj - depth + depth * np.clip(1.25 * tri - 0.125, 0, 1)  # flat crest and root, as rolled threads
        rings.append(c + d * s + cs * rr[:, None])
    return grid(Mesh(), rings, mat, cap0=True, cap1=True)


def through(c, half, af, head=-1, mat="bolt", seat=-0.0004):
    """Bolt across the bike at C: head on side HEAD (-1 right), flanged nut and thread end on the other, each on the
    face at |y| = HALF (SEAT: sunk 0.4 mm into its own part, or held 0.2 mm off another part's face)."""
    c = np.asarray(c, float)
    m = Mesh()
    h = af * 0.6
    for s in (1, -1):
        p = np.array([c[0], s * (half + seat), c[2]])
        m.add(bolt(p, (0, s, 0), af=af, head_h=h if s == head else h * 1.15, mat=mat))
        if s != head:
            m.add(turned(p, (0, s, 0), [(0, af * 0.3), (h * 1.15 + 0.003, af * 0.3)], mat, 10))
    return m


# ---------------------------------------------------------------- frame
T_SPAR = 0.026            # TOP col 2150 (left plate 0.112..0.132) and col 2200 (right 0.110..0.142)
Y_PLATE = 0.137           # outer face of the pivot plates: TOP cols 2150/2200, REAR row 1360 col 1813 (0.141)
# head tube along the steering axis (t from STEER0, as in detail_front.py): from 1 mm above the lower clamp's top face
# (its T_LO[1] 0.716) to 1 mm under the top clamp's bridge (T_UP[1] - 0.015 = 0.913). Stem r 14.5, seals r 26.
HEAD_T = (0.717, 0.912)
HEAD_LO = STEER0 + HEAD_T[0] * UP
HEAD_L = HEAD_T[1] - HEAD_T[0]
STEM_BORE = 0.019
R_PIV = 0.0175            # pivot boss: the chain's top run passes 30 mm above the axis (parts.chain_top), slider 3.5 mm
F_LINK = np.array([0.5195, 0.0, 0.369])         # LEFT px (2298,1558), RIGHT px (1702,1557) cast at |y| 0.045
SHOCK_U = np.array([0.585, 0.0, 0.790])         # EST: upper eye; the adjuster seen at RIGHT px (1733,1109) lies beside it
SHOCK_A = np.array([0.448, 0.0, 0.329])         # LEFT px (2386,1607), RIGHT px (1611,1606): lower clevis bolt
LINK_T = np.array([0.385, 0.0, 0.375])          # LEFT px (2469,1552), RIGHT px (1524,1551): arm on the swingarm
LINK_B = np.array([0.382, 0.0, 0.326])          # LEFT px (2471,1617), RIGHT px (1524,1608): arm to link
CROSS_LO = np.array([0.545, 0.0, 0.380])        # EST: lower cross member behind the engine, 6 mm under the lower chain run
CROSS_UP = np.array([0.632, 0.0, 0.805])        # EST: upper cross member that carries the shock
PEG_ROOT_Z = 0.4065                             # top of the teeth at the root. REAR row 1313 at y 0.14: 0.401; LEFT px
# (2257,1520): 0.413; SPEC footpeg height 422 on the ground: 0.405. The mean of the two photos
PEG_TIP = (0.2475, 0.420)                       # REAR: tips at columns 1673 and 2328, row 1294: y 0.248, z 0.416; LEFT:
# the teeth's top edge at rows 1522..1530 gives 0.423
PEG_Y0 = 0.152
PEG_PIN = (PEG_Y0 - 0.006, PEG_ROOT_Z - 0.012)   # EST: hinge pin under the peg's root (y, z)


_SPAR = PchipInterpolator([0.45, 0.62, 0.74, 0.82, 0.86, 0.90, 0.94, 0.98, 1.03, 1.066],
                          [0.137, 0.137, 0.113, 0.120, 0.127, 0.122, 0.080, 0.062, 0.050, 0.040])


def _spar_y(x):
    """Outer face of the frame in plan, one smooth curve (a polyline put a crease across the spar at every knot):
    pivot plates measured (TOP, REAR); the spars run in to the head under the tank and shrouds, where no photo
    shows them (EST): 4 mm inside the shroud's skin (0.118 at x 0.74, 0.136 at 0.82), outside the tank (0.072 at
    x 0.78, 0.099 at 0.86, 0.048 at 0.94), under the shroud deck at x 0.94."""
    return float(_SPAR(min(max(x, 0.45), 1.066)))


def _clean(o, step=0.00235, sigma=0.0039):
    """plastics.clean_outline for an outline in metres: resampled evenly every 3 px (2.35 mm) and smoothed along the
    closed curve with a Gaussian of 5 px (3.9 mm). The traced outline's pixel steps serrated the plates' edges."""
    from scipy.ndimage import gaussian_filter1d
    P = resample(o, step)
    k = sigma / step
    return np.stack([gaussian_filter1d(P[:, 0], k, mode="wrap"), gaussian_filter1d(P[:, 1], k, mode="wrap")], axis=1)


def _frame_outline():
    """OUT2 'frame' (left photo) cast on the plate's mid plane and cleaned. The frame is symmetric: the right photo's
    outline has the header, the hanger and the brake pedal fused into it and lacks the plate's rear half (hidden by
    the master cylinder), so both sides use this one; where both are clean they agree within 5 mm.
    Three stretches of the traced outline are not the frame's own edge and are replaced:
    the notch of the extraction's cut line at the pivot cap; the footpeg standing in front of the plate's foot
    (hidden behind the bracket); and, ahead of x 0.705, the shroud's rear tip lying over the spar: there the spar
    is carried on as the box it is (top edge continued, 94 mm deep at x 0.81) and ends under the shroud."""
    o = P2("frame", Y_PLATE - T_SPAR / 2)
    br = _bracket_outline()
    keep = ~((o[:, 0] > 0.52) & (o[:, 0] < 0.5745) & (o[:, 1] > 0.452) & (o[:, 1] < 0.492))
    keep &= ~inside(br.mean(axis=0) + 0.85 * (br - br.mean(axis=0)), o)
    keep &= o[:, 0] < 0.705
    o = o[keep]
    gap = np.linalg.norm(np.roll(o, -1, axis=0) - o, axis=1)
    gap[o[:, 0] < 0.66] = 0.0
    j = int(np.argmax(gap))                                   # where the spar's front was cut away
    end = np.array([(0.810, float(_spar_top(0.810)) - 0.094), (0.810, float(_spar_top(0.810)))])
    if o[j, 1] > o[(j + 1) % len(o), 1]:
        end = end[::-1]
    return _clean(np.vstack([o[:j + 1], end, o[j + 1:]]))


def _spar_top(x):
    return 0.786 + 0.632 * (x - 0.661)          # OUT2 'frame': top edge through (0.661,0.786) and (0.737,0.834)


def _bracket_outline():
    # footpeg bracket under the pivot plate (LEFT zoom: peg, black bolt and roller hang from it)
    return np.array([(0.535, 0.418), (0.548, 0.446), (0.572, 0.446), (0.592, 0.418), (0.594, 0.374), (0.582, 0.362),
                     (0.552, 0.362), (0.545, 0.385)])


def _sub_rails(s):
    """Subframe rails of side S: hidden under the seat and side panels in every photo (EST), kept under the seat's
    base and inside the side panels of the model; the mounts are measured: LEFT px (2313,1259) on the plate's rear
    edge and (2172,963) on its ear. The airbox panel's inner skin (0.084..0.105) runs between the plates and the
    rails: the rails stay 4 mm inside it; the lower rail hangs on a bracket that reaches the plate under the panel's
    lower edge, the upper mount is the lug on the ear alone. On the right the exhaust passes under the lower rail."""
    lower = spline([(0.522, s * 0.081, 0.652), (0.495, s * 0.082, 0.672), (0.470, s * 0.083, 0.690), (0.433, s * 0.086, 0.722),
                    (0.378, s * 0.093, 0.762), (0.30, s * 0.094, 0.800), (0.213, s * 0.082, 0.842)], 20)
    upper = spline([(0.615, s * 0.070, 0.838), (0.585, s * 0.070, 0.858), (0.553, s * 0.070, 0.872), (0.482, s * 0.069, 0.876),
                    (0.409, s * 0.070, 0.882), (0.336, s * 0.070, 0.888), (0.262, s * 0.069, 0.894), (0.213, s * 0.068, 0.897)], 20)
    return lower, upper


def frame():
    m = Mesh()
    # steering head: tube with its two bearing cups (parts.py: between the clamps)
    L = HEAD_L
    m.add(turned(HEAD_LO, UP, [(0.0035, STEM_BORE), (0.0035, 0.027), (0.0, 0.027), (0.0, 0.0335), (0.016, 0.0335), (0.020, 0.0305),
                               (L - 0.020, 0.0305), (L - 0.016, 0.0335), (L, 0.0335), (L, 0.027), (L - 0.003, 0.027),
                               (L - 0.003, STEM_BORE), (0.0035, STEM_BORE)], "alu_frame", 28, False, False))
    o = _frame_outline()
    br = _bracket_outline()
    # weld bead across the spar where the extrusion meets the cast pivot plate (EST: 5 mm wide, at x 0.69)
    q = np.array([0.690, 0.757]) + np.outer(np.arange(-0.075, 0.0751, 0.0015), [-0.534, 0.845])
    ins = inside(o, q)
    i0 = len(q) // 2
    lo = i0 - int(np.argmin(ins[i0::-1]))
    hi = i0 + int(np.argmin(ins[i0:]))
    weld = q[lo + 3:hi - 2]
    for s in (1, -1):
        # spar and pivot plate: the photo outline, 26 mm deep with rounded edges, on the spar's path in plan
        m.add(slab(o, lambda x, z, s=s: s * (_spar_y(x) - T_SPAR / 2), T_SPAR, "alu_frame", r=0.005, step=0.009, to=_xz, fine=True))
        m.add(tube([(x, s * (_spar_y(x) + 0.0001), z) for x, z in weld], [(0.0012, 0.0030)] * len(weld), 10, "alu_frame"))
        # the spar under the shroud, up to the head (EST): 80 mm deep box, the visible part's top edge continued
        xs = np.array([0.74, 0.78, 0.82, 0.86, 0.90, 0.92, 0.94, 0.98, 1.03, 1.058])
        low = np.interp(xs, [0.86, 0.92, 1.058], [0.0, 0.004, 0.004])        # top 8 mm lower under the shroud deck (z 0.961)
        path = np.stack([xs, s * (np.array([_spar_y(x) for x in xs]) - T_SPAR / 2), _spar_top(xs) - 0.047 - low], axis=1)
        m.add(bar(path, 0.0245, np.linspace(0.080, 0.088, len(xs)) - 2 * low, "alu_frame"))
        # gusset between the spar's underside, the head and the down tube (EST)
        m.add(slab(np.array([(1.058, 0.940), (0.992, 0.906), (1.030, 0.850)]), s * 0.0245, 0.005, "alu_frame", r=0.002,
                   step=0.012, to=_xz))
        # pivot: boss on the plate (the plate's own front edge there is the extraction's cut line), pad, bolt
        m.add(slab(circle(0.026, 30, PIVOT[0], PIVOT[2]), s * (Y_PLATE - T_SPAR / 2 + 0.0004), T_SPAR + 0.0008, "alu_frame",
                   r=0.005, step=0.009, to=_xz, fine=True))
        m.add(turned(PIVOT + s * (Y_PLATE - 0.0005) * Y3, s * Y3, [(0, 0.025), (0.003, 0.0235), (0.004, 0.019)], "alu_frame", 28))
        m.add(turned(PIVOT + s * 0.052 * Y3, s * Y3, [(0, 0.0085), (0.086, 0.0085)], "steel", 14))
        # footpeg bracket with the black socket bolt (LEFT px (2228,1562), RIGHT px (1770,1561)) and the hinge boss
        m.add(slab(br, s * 0.130, 0.022, "alu_cast", r=0.003, step=0.007, to=_xz, fine=True))
        m.add(bolt((0.5765, s * 0.1407, 0.380), (0, s, 0), af=0.016, head_h=0.007, mat="anod_black", kind="cap"))
        m.add(hollow((PEG[0] - 0.006, s * PEG_PIN[0], PEG_PIN[1]), (1, 0, 0), 0.0058, 0.0038, 0.018, "alu_cast", 14))
        # cradle rail from the down tube's foot under the engine to the bracket (OUT2 'cradle' cast at the rail's own y: lower edge z 0.343;
        # LEFT cols 2077 and 2168: rows 1585..1597, the skid plate wraps it below)
        rail = spline([(0.922, s * 0.012, 0.490), (0.9145, s * 0.022, 0.452), (0.905, s * 0.038, 0.415), (0.880, s * 0.056, 0.392),
                       (0.831, s * 0.066, 0.382), (0.776, s * 0.070, 0.3555), (0.735, s * 0.073, 0.355), (0.690, s * 0.076, 0.355),
                       (0.620, s * 0.092, 0.358), (0.585, s * 0.112, 0.368)], 30)
        m.add(bar(rail, 0.022, 0.024, "alu_frame"))
        # (engine hangers, mounts and the skid plate belong to detail_engine.py)
        # lugs: link (under the lower cross member) and shock (under the upper one)
        m.add(slab(hull([(F_LINK[0], F_LINK[2], 0.013), (CROSS_LO[0], CROSS_LO[2], 0.013)]), s * 0.040, 0.007, "alu_frame",
                   r=0.002, step=0.005, to=_xz))
        m.add(slab(hull([(SHOCK_U[0], SHOCK_U[2], 0.016), (CROSS_UP[0], CROSS_UP[2], 0.016)]), s * 0.0195, 0.007, "alu_frame",
                   r=0.002, step=0.006, to=_xz))
        # subframe mounts: boss on the plate's ear and the two bolts (LEFT px (2172,963), (2313,1259))
        m.add(slab(circle(0.013, 20, 0.624, 0.833), s * (Y_PLATE - T_SPAR / 2 + 0.0004), T_SPAR + 0.0008, "alu_frame", r=0.003,
                   step=0.006, to=_xz))
        m.add(bolt((0.624, s * (Y_PLATE + 0.0002), 0.833), (0, s, 0), af=0.012, head_h=0.007))
        m.add(bolt((0.524, s * (Y_PLATE - 0.0003), 0.607), (0, s, 0), af=0.012, head_h=0.007))
    # pivot bolt: recessed head on the left, flanged nut on the right (LEFT px (2245,1433), RIGHT px (1751,1431))
    m.add(bolt(PIVOT + (Y_PLATE + 0.0033) * Y3, Y3, af=0.024, head_h=0.007, flange_d=0.036, mat="steel"))
    m.add(bolt(PIVOT - (Y_PLATE + 0.0033) * Y3, -Y3, af=0.022, head_h=0.010, flange_d=0.032, mat="steel"))
    m.add(turned(PIVOT - (Y_PLATE + 0.0033) * Y3, -Y3, [(0, 0.0075), (0.013, 0.0075)], "steel", 12))
    # down tube: its front and rear edges in the left photo (rows 1280..1440: x 0.954..0.923 down to 0.925..0.904)
    dt = spline([(1.056, 0, 0.945), (1.040, 0, 0.870), (1.015, 0, 0.775), (0.990, 0, 0.690), (0.962, 0, 0.625), (0.938, 0, 0.576),
                 (0.9145, 0, 0.452)], 18)
    m.add(bar(dt, 0.044, np.linspace(0.042, 0.030, len(dt)), "alu_frame"))
    # cross members between the plates (EST) and the lower chain roller (LEFT px (2298,1558))
    m.add(tube([CROSS_LO - 0.121 * Y3, CROSS_LO + 0.121 * Y3], 0.013, 16, "alu_frame"))
    m.add(tube([CROSS_UP - 0.115 * Y3, CROSS_UP + 0.115 * Y3], 0.015, 16, "alu_frame"))
    # roller r 12.5 (LEFT zoom: 32..34 px across), 1.7 mm under the lower run; its lug stands inboard of the chain
    ro = np.array([0.521, CHAIN_Y, 0.376])
    m.add(slab(hull([(ro[0], ro[2], 0.009), (CROSS_LO[0], CROSS_LO[2], 0.012)]), CHAIN_Y - 0.0165, 0.007, "alu_frame", r=0.002,
               step=0.005, to=_xz))
    m.add(turned(ro - 0.013 * Y3, Y3, [(0, 0.006), (0.0025, 0.006), (0.0025, 0.0115), (0.0035, 0.0125), (0.007, 0.0125), (0.009, 0.011),
                                      (0.017, 0.011), (0.019, 0.0125), (0.0225, 0.0125), (0.0235, 0.0115), (0.0235, 0.005)],
                 "plastic_black", 24))
    m.add(bolt(ro + 0.0103 * Y3, Y3, af=0.010, head_h=0.006, flange_d=0.016))
    return m


def subframe():
    m = Mesh()
    for s in (1, -1):
        lower, upper = _sub_rails(s)
        m.add(bar(lower, 0.018, 0.022, "alu_frame"))
        m.add(bar(upper, 0.018, 0.022, "alu_frame"))
        m.add(bar([lower[-1], upper[-1]], 0.016, 0.018, "alu_frame"))                  # tail strut
        # bracket of the lower mount: 3 mm leg between the pipe and the panel, foot to the plate under the panel's edge
        m.add(slab(np.array([(0.513, 0.597), (0.529, 0.597), (0.529, 0.655), (0.513, 0.655)]), s * 0.0885, 0.003, "alu_frame",
                   r=0.001, step=0.006, to=_xz))
        m.add(bar([(0.521, s * 0.090, 0.603), (0.521, s * 0.100, 0.603), (0.521, s * 0.1105, 0.603)], 0.014, 0.012, "alu_frame"))
        # lug on the frame's ear, 0.2 mm inside the plate's inner face (the lower rail starts under the plate)
        m.add(slab(hull([(0.624, 0.833, 0.012), (0.603, 0.846, 0.010)]), s * 0.1058, 0.008, "alu_frame", r=0.002, step=0.005,
                   to=_xz))
    lo_l, up_l = _sub_rails(1)
    for p, r in ((up_l[-1], 0.009), (lo_l[-1], 0.008)):                                 # cross tubes at the tail
        m.add(tube([(p[0], -p[1], p[2]), (p[0], p[1], p[2])], r, 12, "alu_frame"))
    return m


# ---------------------------------------------------------------- swingarm (micro pass 2026-11-11)
# The arm's own frame: s from the rear axle toward the pivot, t square to it (up). The photos' axle lies 8 mm above
# parts.RA (LEFT: the 50T sprocket's bolt circle, five bolts fitted to 0.3 px, and the axle's bore both cast to
# z 0.3343; RIGHT: bore 0.3377), so every swingarm shape is measured relative to the photo's own axle-to-pivot line
# and built on the model's (RA to PIVOT): the arm keeps its shape and turns 0.8 deg with the model.
ARM_A = math.atan2(PIVOT[2] - RA[2], PIVOT[0] - RA[0])
ARM_L = float(math.hypot(PIVOT[2] - RA[2], PIVOT[0] - RA[0]))
ARM_E = np.array([math.cos(ARM_A), 0.0, math.sin(ARM_A)])
ARM_N = np.array([-math.sin(ARM_A), 0.0, math.cos(ARM_A)])
SLOT_A = ARM_A - math.radians(0.97)     # LEFT: the slot's rails and the block's edges fit best at 13.5 deg (edge contrast
#                                         over 6..16 deg), the photo's axle-to-pivot line lies at 14.47 deg
S_WR, S_WF = 0.050, 0.468               # welds of the extruded arm: LEFT s 0.046..0.061, RIGHT 0.039..0.050 (rear);
#                                         LEFT 0.461..0.482, RIGHT 0.453..0.475 (front)
# arm's top and bottom edges (t, m): the bright run of the side face in both photos (armscan, 28 stations), plus
# 1 mm for the rounded edge; LEFT's bottom is hidden by the slider from s 0.42 on, RIGHT gives it there
_T_TOP = PchipInterpolator([0.050, 0.08, 0.12, 0.16, 0.20, 0.26, 0.32, 0.40, 0.468],
                           [0.0293, 0.0304, 0.0315, 0.0332, 0.0349, 0.0360, 0.0364, 0.0374, 0.0375])
_T_BOT = PchipInterpolator([0.050, 0.08, 0.12, 0.16, 0.20, 0.26, 0.30, 0.40, 0.468],
                           [-0.0304, -0.0314, -0.0330, -0.0350, -0.0368, -0.0390, -0.0396, -0.0386, -0.0386])
ARM_R = 0.004                           # LEFT: the top edge's highlight is 3 to 4 px wide (EST radius)
Y_ARM_O = (0.129, 0.127)                # outer face at the rear and front welds: REAR cols 1811 and 2190 at the axle;
#                                         the 2 mm taper forward EST (the top photo has the arms under the panels)
W_ARM = 0.031                           # REAR: 0.098..0.129
# rear casting and axle block, in the slot's frame (f along the slot, n square to it, from the axle's centre), read on
# intensity profiles through the axle at 13.5 deg in LEFT (0.7545 mm/px) and RIGHT (0.751); where the two sides differ
# the mean is used and both are written down
Y_END_O = 0.1280                        # REAR row 1545: light edge at cols 1810..1813 (left) and 2182..2184 (right)
Y_END_I = 0.0937                        # 0.2 mm off the wheel's collar (detail_wheels.ARM_FACE 0.0935)
Y_BLK_O = 0.1258                        # REAR: the block's lit edge at col 2182.5 (y -0.1252), the nut from col 2184
Y_LEDGE = 0.1260                        # the window's ledge, 2 mm under the face (lr34, rr34: the window's walls show)
Y_POCKET = 0.1125                       # EST: floor of the adjuster's pocket (lit grey in LEFT and RIGHT)
Y_ADJ = 0.1205                          # lr34, rr34: the lock nut's outer corner just under the casting's face
ADJ = (0.004, 0.00125, 0.012, 0.007)    # adjuster M8 x 1.25 (LEFT: thread 10 px tall, 7.5 mm; RIGHT 8 px), its lock
#                                         nut 12 mm across flats, 7 mm thick (Honda M8 nuts; LEFT 10 px long)
CAST_REAR = -0.0294                     # rear end: LEFT -40.5 px, RIGHT -37.5 px
CAST_TOP = (0.0282, 0.060)              # n = a + b f: LEFT +37 px at f 0 (+38.5 at 35 px, +40.5 at 60 px), RIGHT +39
CAST_BOT = (-0.0252, -0.049)            # LEFT -34 px (-35.5, -37), RIGHT -31.5: the casting stands 1.5 mm high of the axle
CAST_CORNER = 0.011                     # LEFT: the end 4 px shorter at n 14 px than at n 0
N0 = 0.0008                             # centre of the window, slot and block: LEFT window +27.5 / -26.5 px, RIGHT
#                                         pocket +29 / -24 px; the head and its flats are on the axle's centre
WIN = (-0.0226, 0.0410, 0.0203)         # window in the face: rear end (LEFT -31.5, RIGHT -28.5 px), front wall (53, 57),
#                                         half height (LEFT 27 px, RIGHT 26.5)
SLOT_H = 0.0189                         # the slot proper under the ledge, 0.2 mm round the block
POCKET_F = 0.0191                       # the pocket's floor runs up to the block (LEFT, RIGHT: no gap ahead of it)
REAR_R = 0.048                          # the slot's rear end is an arc: LEFT the gap behind the square block is a
#                                         crescent, 4 mm on the slot's line, closing at the block's corners
BLK = (0.01865, 0.0187)                 # block 37.3 x 37.4 mm: LEFT edges at -24.5 and +25 px along it
HEAD_R, HEAD_FLAT, HEAD_T = 0.0179, 0.0153, 0.0045   # LEFT: 47.5 px round, 40.5 px across the flats; REAR: to 0.1303
HEAD_BORE = 0.00905                     # LEFT: dark disc 24 px
R_AXLE = 0.011                          # Honda U-nut 22 mm (90305-KZ4-J20) on the M22 x 1.5 end
AXLE_BORE = 0.00665                     # RIGHT: dark disc 17.7 px
NUT_AF, NUT_H, NUT_COLLAR = 0.032, 0.0089, (0.0145, 0.0041)   # 32 mm (M22 nut kits); RIGHT 44.5 px across flats;
#                                         REAR cols 2184..2197 hex, 2197..2203 collar, 2203..2205 the axle's end
MARKS = (9, 0.002, 0.0032, 0.0020)      # index marks: count, pitch, long, short (LEFT: 16 mm rows centred on the axle,
#                                         top row centred 24.4 mm, bottom 21.5 mm from it)


def _fr(a, f, n):
    """(x, z) of the point F along and N across the direction at angle A, about the rear axle."""
    f, n = np.asarray(f, float), np.asarray(n, float)
    return np.stack([RA[0] + f * math.cos(a) - n * math.sin(a), RA[2] + f * math.sin(a) + n * math.cos(a)], axis=-1)


def _slot_xz(P):
    P = np.asarray(P, float)
    return _fr(SLOT_A, P[:, 0], P[:, 1])


def _rr(f0, f1, n0, n1, r0, r1, k=6):
    """Rounded rectangle (counter-clockwise) with corner radius R0 at the F0 end and R1 at the F1 end."""
    pts = []
    for cf, cn, r, a0 in ((f1 - r1, n1 - r1, r1, 0), (f0 + r0, n1 - r0, r0, 90), (f0 + r0, n0 + r0, r0, 180),
                          (f1 - r1, n0 + r1, r1, 270)):
        for j in range(k + 1):
            a = math.radians(a0 + 90 * j / k)
            pts.append((cf + r * math.cos(a), cn + r * math.sin(a)))
    return np.array(pts)


def _t_top(s):
    s = np.asarray(s, float)
    return np.where(s < S_WF, _T_TOP(np.clip(s, S_WR, S_WF)), _front_t(s, float(_T_TOP(S_WF)), R_PIV))


def _t_bot(s):
    s = np.asarray(s, float)
    return np.where(s < S_WF, _T_BOT(np.clip(s, S_WR, S_WF)), -_front_t(s, -float(_T_BOT(S_WF)), R_PIV))


def _front_t(s, t0, t1):
    """Pivot casting: from the arm's edge at the front weld round onto the pivot boss (EST: behind the frame plate
    and the slider in both photos; a quarter ellipse)."""
    k = np.clip((s - S_WF) / (ARM_L - S_WF), 0.0, 1.0)
    return t1 + (t0 - t1) * np.sqrt(np.clip(1 - k ** 2.2, 0, 1))


def _edge_z(x, tf):
    """z of an arm edge t = tf(s) at the given x (model frame)."""
    x = np.asarray(x, float)
    s = (x - RA[0]) / math.cos(ARM_A)
    for _ in range(4):
        s = (x - RA[0] + tf(s) * math.sin(ARM_A)) / math.cos(ARM_A)
    return RA[2] + s * math.sin(ARM_A) + tf(s) * math.cos(ARM_A)


def _arm_top(x):
    """Top edge of the arm at x (the photo line, on the model's axle-to-pivot line)."""
    return _edge_z(x, _t_top)


def _arm_bot(x):
    return _edge_z(x, _t_bot)


def _arm_zt(x):
    """Top of the arm: the photo line, kept 13.5 mm under the chain's top run where the chain closes on it."""
    return float(min(_arm_top(x), chain_top(x) - 0.0135))


def _arm_zb(x):
    return float(_arm_bot(x))


def _arm_yo(s):
    """Outer face in plan: straight arm, then the pivot casting closes in to the boss inside the frame plates (their
    inner faces at 0.111 from x 0.50)."""
    s = np.asarray(s, float)
    k = np.clip((s - S_WF) / (0.505 - S_WF), 0, 1)                    # inside 0.110 wherever the ring reaches x 0.499
    arm = Y_ARM_O[0] + (Y_ARM_O[1] - Y_ARM_O[0]) * np.clip((s - S_WR) / (S_WF - S_WR), 0, 1)
    return np.where(s < S_WF, arm, Y_ARM_O[1] + (0.1100 - Y_ARM_O[1]) * (3 * k ** 2 - 2 * k ** 3))


def _arm_yi(s):
    s = np.asarray(s, float)
    k = np.clip((s - S_WF) / (ARM_L - 0.012 - S_WF), 0, 1)
    return np.where(s < S_WF, _arm_yo(s) - W_ARM, Y_ARM_O[1] - W_ARM + (0.058 - Y_ARM_O[1] + W_ARM) * (3 * k ** 2 - 2 * k ** 3))


def slider_top(x):
    """Upper face of the chain slider: 6.5 mm over the arm, then 9 mm under the chain's centre line from x 0.44 on."""
    return float(_arm_top(x)) + 0.0065 if x < 0.44 else float(chain_top(x)) - 0.009


def _arm_section(s, side, n=6):
    """Ring of the arm (or pivot casting) at S: rounded rectangle in (y, t), counter-clockwise seen from the front."""
    yo, yi = float(_arm_yo(s)), float(_arm_yi(s))
    tt, tb = float(_t_top(s)), float(_t_bot(s))
    p = ARM_E * s + RA
    z_top = p[2] + tt * ARM_N[2]
    lim = float(chain_top(p[0] - tt * math.sin(ARM_A))) - 0.0135          # under the slider and the chain's top run
    if z_top > lim:
        tt -= (z_top - lim) / ARM_N[2]
    r = min(ARM_R, (yo - yi) / 2 - 1e-4, (tt - tb) / 2 - 1e-4)
    sec = rounded_rect(yo - yi, tt - tb, r, n)
    ya = (yo + yi) / 2 + sec[:, 0]
    tb_ = (tt + tb) / 2 + sec[:, 1]
    P = p[None, :] + tb_[:, None] * ARM_N[None, :] + (side * ya)[:, None] * Y3[None, :]
    return P if side > 0 else P[::-1]


def _weld(s_w, side, w=0.015, h=0.0028, pitch=0.0028, sink=0.6):
    """TIG bead round the arm's section at S_W: a half-buried ellipse W wide, H high, with crescent ripples every
    PITCH (the stacked look of a pulsed weld: LEFT u 2903..2923 and RIGHT u 1060..1085, 15 to 19 mm across the
    corner; lr34: about 12 ripples across the arm's 31 mm top, of uneven height)."""
    ring = _arm_section(s_w, side, 6)
    ring = np.vstack([ring, ring[:1]])
    seg = np.linalg.norm(np.diff(ring, axis=0), axis=1)
    arc = np.concatenate([[0], np.cumsum(seg)])
    m_n = int(arc[-1] / (pitch / 4))
    a = np.linspace(0, arc[-1], m_n, endpoint=False)
    P = np.stack([np.interp(a, arc, ring[:, k]) for k in range(3)], axis=1)
    T = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = np.cross(ARM_E, T) * side                                     # outward, in the section's plane
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    # outward check: from the section's centre
    cen = P.mean(axis=0)
    if np.mean(np.sum((P - cen) * N, axis=1)) < 0:
        N = -N
    phi = np.linspace(0, 2 * math.pi, 14, endpoint=False)
    rings = []
    for i in range(m_n):
        e = np.cos(phi)
        q = a[i] / pitch + 0.55 * e ** 2
        ripple = q % 1.0
        jit = (np.sin(np.floor(q) * 12.9898) * 43758.5453) % 1.0        # uneven ripples, as laid by hand
        hh = h * (0.62 + 0.38 * np.sqrt(ripple)) * (0.94 + 0.12 * jit)  # each ripple's crest, then its steep front
        u = np.sin(phi)
        off = np.where(u > 0, u * hh, u * h * sink)
        rings.append(P[i] + np.outer(off, N[i]) + np.outer(e * w / 2 * (0.97 + 0.03 * ripple), ARM_E))
    rings.append(rings[0])
    return _outward(grid(Mesh(), rings, "alu_weld", closed_u=True))


def _cast_outline():
    """Rear casting in the side's plane (x, z): the U end round the slot from the photo's lines, the front cut square
    to the arm under the weld, its edges blended onto the arm's over the last 20 mm."""
    c_top = lambda f: CAST_TOP[0] + CAST_TOP[1] * f
    c_bot = lambda f: CAST_BOT[0] + CAST_BOT[1] * f
    fr, cc = CAST_REAR + CAST_CORNER, CAST_CORNER
    pts = [(fr + cc * math.cos(a), c_bot(fr) + cc + cc * math.sin(a)) for a in np.radians(np.linspace(270, 180, 9))]
    pts += [(fr + cc * math.cos(a), c_top(fr) - cc + cc * math.sin(a)) for a in np.radians(np.linspace(180, 90, 9))[1:]]
    rear = _slot_xz(np.array(pts))                                    # up the U end
    d = SLOT_A - ARM_A
    cd, sd = math.cos(d), math.sin(d)

    def edge(fn, tf):
        out = []
        for f in np.linspace(fr + 0.002, S_WR + 0.003, 30):
            n = fn(f)
            s_l, t_l = f * cd - n * sd, f * sd + n * cd                 # the slot's frame into the arm's
            k = float(np.clip((s_l - 0.030) / (S_WR - 0.030), 0, 1))
            k = 3 * k ** 2 - 2 * k ** 3
            out.append(_fr(ARM_A, s_l, (1 - k) * t_l + k * float(tf(s_l))))
        return np.array(out)
    return np.vstack([rear, edge(c_top, _t_top), edge(c_bot, _t_bot)[::-1]])


def _ribs(m, side):
    """Index marks above and below the window, every 2 mm, long and short in turn (lr34, rr34; dark lines in LEFT and
    RIGHT): cut lines, drawn as their dark floor 0.02 mm proud of the face (a 0.7 mm groove is not worth its mesh)."""
    count, pitch, lng, sht = MARKS
    for k in range(count):
        f = (k - (count - 1) / 2) * pitch
        ln = lng if k % 2 == 0 else sht
        for sg in (1, -1):
            n0 = N0 + sg * (WIN[2] + 0.0010)
            nc = n0 + sg * ln / 2
            c = _fr(SLOT_A, f, nc)
            R = np.array([[math.cos(SLOT_A), 0, -math.sin(SLOT_A)], [0, 1, 0], [math.sin(SLOT_A), 0, math.cos(SLOT_A)]])
            m.add(box((c[0], side * (Y_END_O - 0.00008), c[1]), (0.0007, 0.0003, ln), "groove", R))


def swingarm():
    m = Mesh()
    for s in (1, -1):
        mat = "swing_L" if s > 0 else "swing_R"
        # extruded arm between its two welds, then the pivot casting onto the boss
        ss = np.unique(np.concatenate([np.linspace(S_WR - 0.002, S_WF + 0.002, 34), [0.06, 0.07]]))
        m.add(grid(Mesh(), [_arm_section(q, s) for q in ss], mat, cap0=True, cap1=True))
        sf = np.concatenate([np.linspace(S_WF, ARM_L - 0.030, 12), np.linspace(ARM_L - 0.026, ARM_L - 0.006, 6)])
        m.add(grid(Mesh(), [_arm_section(q, s) for q in sf], "alu_cast", cap0=True, cap1=True))
        m.add(_weld(S_WR + 0.0005, s))
        m.add(_weld(S_WF - 0.0005, s))
        m.add(hollow(PIVOT + s * 0.056 * Y3, s * Y3, R_PIV, 0.0105, 0.054, "alu_cast", 32))
        # rear casting: the U end with its window, the boss on its inner face, the adjuster's pocket floor
        o = _cast_outline()
        win = _slot_xz(_window())
        yc0 = Y_END_O - W_ARM - 0.0005                                  # 1 mm inside the arm's inner face
        m.add(slab2(o, s * (yc0 + Y_END_O) / 2, Y_END_O - yc0, "alu_satin", r=0.0015, step=0.004, holes=[win], to=_xz,
                    r_hole=0.0006))
        boss = _slot_xz(_rr(CAST_REAR + 0.0025, 0.026, CAST_BOT[0] + 0.0035, CAST_TOP[0] - 0.0035, 0.009, 0.006))
        slot = _slot_xz(_arc_rr(WIN[0], POCKET_F, SLOT_H, 0.0005))
        yb0, yb1 = Y_END_I, Y_END_O - W_ARM
        m.add(slab(boss, s * (yb0 + yb1 + 0.0006) / 2, yb1 + 0.0006 - yb0, "alu_satin", r=0.0015, step=0.004, holes=[slot],
                   to=_xz))
        floor = _slot_xz(_window(inset=0.0001, f0=POCKET_F + 0.0001))
        for sg in (1, -1):                                       # ledges round the slot, 2 mm under the face
            f_led = WIN[0] + REAR_R - math.sqrt(REAR_R ** 2 - WIN[2] ** 2) + 0.0003     # inside the window's arc
            led = _slot_xz(_rr(f_led, POCKET_F, SLOT_H, WIN[2] - 0.0001, 0.0003, 0.0003) * (1, sg) + (0, N0))
            m.add(slab(led[::sg], s * (Y_LEDGE + Y_POCKET) / 2, Y_LEDGE - Y_POCKET, "alu_satin", r=0.0004, step=0.003, to=_xz))
        yf0 = Y_END_O - W_ARM - 0.0004
        m.add(slab(floor, s * (yf0 + Y_POCKET) / 2, Y_POCKET - yf0, "alu_cast", r=0.0008, step=0.004, to=_xz))
        _ribs(m, s)
        # lug for the cushion arm under the cross member (OUT2 'swingarm_R' hangs to z 0.354 at x 0.33..0.39)
        m.add(slab(hull([(LINK_T[0], LINK_T[2], 0.017), (0.374, 0.414, 0.006), (0.410, 0.414, 0.006)]), s * 0.0375, 0.009,
                   "alu_satin", r=0.002, step=0.005, to=_xz))
    # cross member behind the shock (EST: between the shock's spring seat and the tyre), ending in the arms' walls
    zc = (float(_arm_top(0.40)) + float(_arm_bot(0.40))) / 2
    yi = float(_arm_yi((0.40 - RA[0]) / math.cos(ARM_A))) + 0.002
    m.add(bar([(0.400, -yi, zc), (0.400, 0.0, zc), (0.400, yi, zc)], 0.042, 0.056, "alu_satin"))
    # chain slider (black): strip A on the arm's top and over the pivot boss, its upper face slider_top(x); strip B
    # under the arm and round the boss's front, 3 mm thick there (the 13T sprocket's teeth pass 5 mm from the boss)
    xa = np.concatenate([np.linspace(0.28, 0.44, 7), np.linspace(0.458, 0.590, 12)])
    ha = np.interp(xa, [0.28, 0.44, 0.468, 0.548, 0.560, 0.590], [0.006, 0.006, 0.0045, 0.0045, 0.0035, 0.003])
    za = np.array([slider_top(x) for x in xa]) - ha / 2
    m.add(bar(np.stack([xa, np.full(len(xa), CHAIN_Y), za], axis=1), 0.022, ha, "plastic_black"))
    lowr = [(x, _arm_zb(x) - 0.003) for x in np.linspace(0.41, 0.545, 6)]
    arc = [(PIVOT[0] + (R_PIV + 0.0015) * math.cos(a), PIVOT[2] + (R_PIV + 0.0015) * math.sin(a))
           for a in np.radians(np.arange(-90, 61, 15))]
    sb = np.array([(x, CHAIN_Y, z) for x, z in lowr + arc])
    m.add(bar(sb, 0.022, np.concatenate([np.full(len(lowr), 0.006), np.full(len(arc), 0.003)]), "plastic_black"))
    return m


def _arc_rr(f0, f1, h, rf, rc=0.002, k=8, n0=N0):
    """Slot outline (counter-clockwise): its rear end an arc of radius REAR_R with its apex at F0, met by the top and
    bottom edges (+-H about N0) in corners of RC; front corners RF at F1."""
    pts = [(f1 - rf + rf * math.cos(a), n0 + h - rf + rf * math.sin(a)) for a in np.radians(np.linspace(0, 90, k))]
    fc = f0 + REAR_R
    lim = math.asin(h / REAR_R)
    for a in np.linspace(math.pi - lim, math.pi + lim, 2 * k + 1):
        pts.append((fc + REAR_R * math.cos(a), n0 + REAR_R * math.sin(a)))
    pts += [(f1 - rf + rf * math.cos(a), n0 - h + rf + rf * math.sin(a)) for a in np.radians(np.linspace(270, 360, k))]
    return np.array(pts)


def _window(inset=0.0, f0=None):
    """Window in the casting's face (slot frame): its rear end the slot's arc, 6.5 mm corners at the front wall.
    F0: only the part ahead of F0 (the pocket's floor)."""
    h = WIN[2] - inset
    if f0 is None:
        return _arc_rr(WIN[0] + inset, WIN[1] - inset, h, 0.0065 - inset)
    return _rr(f0, WIN[1] - inset, N0 - h, N0 + h, 0.0004, 0.0065 - inset)


def _head_outline(n=40):
    """The axle's head in the slot's frame: a round flange with two flats along the slot (they keep it square in
    the block)."""
    lim = math.asin(HEAD_FLAT / HEAD_R)
    pts = []
    for a0, a1 in ((-lim, lim), (math.pi - lim, math.pi + lim)):
        for a in np.linspace(a0, a1, n // 2):
            pts.append((HEAD_R * math.cos(a), HEAD_R * math.sin(a)))
    return np.array(pts)


def rear_axle():
    """Rear axle with its head (left), U-nut (right), the two square axle blocks in the swingarm's slots and the chain
    adjusters (lock nut against the window's front wall, the bolt's dog point on the block)."""
    m = Mesh()
    c = np.array([RA[0], 0.0, RA[2]])
    # shaft: one hollow piece from under the head to the threaded end (hidden in the hub, collars and blocks)
    ye = -(Y_BLK_O + 0.0001 + NUT_H + NUT_COLLAR[1])                       # the collar's top
    L = Y_BLK_O - ye + 0.0001
    hb, ab = HEAD_BORE + 0.0001, AXLE_BORE + 0.0001
    m.add(turned(c + Y_BLK_O * Y3, -Y3, [(0, hb), (0, R_AXLE), (L, R_AXLE), (L, ab), (0.030, ab), (0.030, hb), (0, hb)], "steel", 32,
                 False, False))
    for s in (1, -1):
        # block: 37 mm square, 0.2 mm clear of the slot; raised rails top and bottom hold the head's flats
        blk = _slot_xz(_rr(-BLK[0], BLK[0], N0 - BLK[1], N0 + BLK[1], 0.0015, 0.0015))
        yb0 = Y_END_I + 0.0001
        m.add(slab2(blk, s * (yb0 + Y_BLK_O) / 2, Y_BLK_O - yb0, "axle_block", r=0.0006, step=0.004,
                    holes=[circle(R_AXLE + 0.0002, 32, RA[0], RA[2])], to=_xz))
        for sg in (1, -1):
            rail = _slot_xz(_rr(-BLK[0] + 0.001, BLK[0] - 0.001, 0.0161, 0.0183, 0.0004, 0.0004) * (1, sg) + (0, N0))
            m.add(slab(rail[::sg], s * (Y_BLK_O + 0.00035), 0.0009, "axle_block", r=0.0003, step=0.003, to=_xz))
            if s > 0:                                             # LEFT: bright tabs at the rails' rear ends
                tab = _slot_xz(_rr(-BLK[0] + 0.0002, -0.0108, 0.0161, 0.0185, 0.0004, 0.0006) * (1, sg) + (0, N0))
                m.add(slab(tab[::sg], s * (Y_BLK_O + 0.00075), 0.0017, "alu_machined", r=0.0006, step=0.003, to=_xz))
        # chain adjuster: lock nut (M6, 10 mm) against the window's front wall, thread, dog point on the block
        P = lambda f: np.array([_fr(SLOT_A, f, N0)[0], s * Y_ADJ, _fr(SLOT_A, f, N0)[1]])
        fdir = np.array([math.cos(SLOT_A), 0.0, math.sin(SLOT_A)])
        r_t, pt, af, nh = ADJ
        m.add(hexnut(P(WIN[1] - nh - 0.0001), fdir, af, nh, r_t + 0.0001, "zinc", phase=math.pi / 6))
        m.add(thread(P(BLK[0] + 0.0036), fdir, r_t, pt, WIN[1] - nh - 0.0002 - BLK[0] - 0.0036 + 0.003, "zinc", seg=20, per=5))
        m.add(turned(P(BLK[0] + 0.0002), fdir, [(0, 0.0024), (0.0006, 0.0030), (0.0036, 0.0030), (0.0037, r_t - 0.0006)], "zinc",
                     16, True, False))                            # dog point on the block
    # head (left): flange with flats, its deep bore (dark at the bottom)
    hd = _slot_xz(_head_outline())
    m.add(slab2(hd, Y_BLK_O + 0.0001 + HEAD_T / 2, HEAD_T, "steel", r=0.0006, step=0.003,
                holes=[circle(HEAD_BORE, 40, RA[0], RA[2])], to=_xz))
    top = Y_BLK_O + 0.0001 + HEAD_T
    m.add(turned(c + top * Y3, -Y3, [(0.030, 0.0001), (0.030, HEAD_BORE), (0.006, HEAD_BORE)], "bore", 40, True, False))
    m.add(turned(c + top * Y3, -Y3, [(0.006, HEAD_BORE), (0.0, HEAD_BORE)], "steel", 40, False, False))   # lr34: its mouth lit
    # U-nut (right): 32 mm hexagon with both faces chamfered, the round locking collar, the axle's threaded end
    y0 = -(Y_BLK_O + 0.0001)
    m.add(hexnut(c + y0 * Y3, -Y3, NUT_AF, NUT_H, R_AXLE + 0.0001, "steel", phase=math.pi / 6, seg=48))
    cr, ch = NUT_COLLAR
    m.add(turned(c + (y0 - NUT_H) * Y3, -Y3, [(0.0, R_AXLE + 0.0001), (0.0, cr - 0.0004), (0.0003, cr), (ch - 0.0008, cr),
                                             (ch, cr - 0.0009), (ch, 0.0121), (ch - 0.0006, R_AXLE + 0.0001),
                                             (0.0, R_AXLE + 0.0001)], "steel", 48, False, False))
    m.add(turned(c + (ye - 0.0001) * Y3, -Y3, [(0.0, R_AXLE - 0.0006), (0.0008, R_AXLE - 0.0006), (0.0016, R_AXLE - 0.0014),
                                              (0.0016, AXLE_BORE + 0.0008), (0.0008, AXLE_BORE), (-0.001, AXLE_BORE)], "steel", 40,
                 False, False))
    m.add(turned(c + (ye - 0.0001) * Y3, -Y3, [(-0.030, 0.0001), (-0.030, AXLE_BORE), (-0.001, AXLE_BORE)], "bore", 40, True,
                 False))
    return m


GUIDE_SLOT = (0.150, 0.2554, 0.39, 0.0165)      # x, z of the slot's centre line, its slope, half its height


def chain_guide():
    """Chain guide under the left arm: two aluminium plates hung 0.3 mm under the arm, tied by two bolts with their
    spacers ahead of the 50T sprocket's teeth (r 0.131), and two wear blocks 33 mm apart round the lower run (LEFT px
    2735..2834 x 1624..1752: x 0.107..0.185, z 0.229..0.328). The slot takes the chain (15 mm tall, 21 wide) wherever
    it runs between the photo's straight line to (0.171, 0.270) and the tangent onto the sprocket."""
    m = Mesh()

    def zt(x):
        return float(_arm_bot(x)) - 0.0003
    ties = ((0.192, zt(0.196) - 0.0085), (0.142, zt(0.142) - 0.0085))
    gp = np.array([(0.196, ties[0][1]), (0.196, zt(0.196)), (0.112, zt(0.112)), (0.100, 0.300), (0.103, 0.232), (0.120, 0.212),
                   (0.188, 0.238), (0.196, 0.270)])
    for dy in (-0.0185, 0.0185):
        m.add(slab(gp, CHAIN_Y + dy, 0.003, "alu_machined", r=0.001, step=0.007, holes=[circle(0.011, 20, 0.150, 0.318)], to=_xz))
    for x, z in ties:
        m.add(tube([(x, CHAIN_Y - 0.0205, z), (x, CHAIN_Y + 0.0205, z)], 0.004, 10, "bolt"))
        m.add(bolt((x, CHAIN_Y + 0.0198, z), Y3, af=0.010, head_h=0.005))
        m.add(bolt((x, CHAIN_Y - 0.0198, z), -Y3, af=0.010, head_h=0.005))
    x0, z0, slope, half = GUIDE_SLOT
    a = math.atan(slope)
    e, nrm = np.array([math.cos(a), 0.0, math.sin(a)]), np.array([-math.sin(a), 0.0, math.cos(a)])
    for q in (-1, 1):
        c = np.array([0.158, CHAIN_Y, z0 + slope * (0.158 - x0)]) + nrm * q * (half * math.cos(a) + 0.004)
        m.add(bar([c + e * w for w in np.linspace(-0.027, 0.035, 9)], 0.0336, 0.008, "plastic_black"))
    return m


# ---------------------------------------------------------------- Pro-Link
def linkage():
    """Cushion arm (on the swingarm at T, shock clevis at A, link at B) and the one-piece link to the frame at F:
    link length B-F 144 mm, T-B 49 mm, T-A 78 mm (LEFT and RIGHT zooms, both sides agree within 6 mm). The link
    passes the shock's clevis bolt, which shows through a hole in each of its sides (RIGHT px (1611,1606))."""
    m = Mesh()
    T, A, B, F = LINK_T, SHOCK_A, LINK_B, F_LINK
    arm = hull([(T[0], T[2], 0.020), (A[0], A[2], 0.016), (B[0], B[2], 0.017)])
    c = (T + A + B) / 3
    m.add(slab(arm, 0.0, 0.024, "alu_cast", r=0.003, step=0.006, holes=[circle(0.0075, 16, c[0], c[2])], to=_xz))
    m.add(hollow(T - 0.031 * Y3, Y3, 0.020, 0.008, 0.062, "alu_cast", 24))
    m.add(hollow(B - 0.0245 * Y3, Y3, 0.017, 0.007, 0.049, "alu_cast", 22))
    for s in (1, -1):
        m.add(slab(hull([(B[0], B[2], 0.016), (A[0], A[2], 0.019), (F[0], F[2], 0.015)]), s * 0.0285, 0.007, "alu_cast", r=0.002,
                   step=0.006, holes=[circle(0.014, 20, A[0], A[2])], to=_xz))
    m.add(hollow(F - 0.036 * Y3, Y3, 0.015, 0.007, 0.072, "alu_cast", 22))
    k = (0.497 - B[0]) / (F[0] - B[0])                         # bridge of the link, ahead of the shock's clevis
    zb = B[2] + k * (F[2] - B[2])
    m.add(bar([(0.497, -0.027, zb), (0.497, 0.0, zb), (0.497, 0.027, zb)], 0.016, 0.018, "alu_cast"))
    m.add(through(T, 0.042, 0.017, seat=0.0002))
    m.add(through(B, 0.032, 0.014))
    m.add(through(F, 0.0435, 0.014, seat=0.0002))
    return m


# ---------------------------------------------------------------- shock
def shock():
    """Showa shock on the centre line, hidden behind the pivot plates and the airbox panel in both profiles: lower
    clevis bolt measured (SHOCK_A), compression adjuster seen through the frame in the right photo (px (1733,1109)),
    the rest from the real part's sizes (EST: 481 mm eye to eye, 50 mm body, spring 8.25 coils of 12 mm wire)."""
    m = Mesh()
    U, A = SHOCK_U, SHOCK_A
    L = float(np.linalg.norm(A - U))
    d = (A - U) / L
    nr = np.array([d[2], 0.0, -d[0]])                          # square to the axis, pointing back and up
    m.add(hollow(U - 0.0155 * Y3, Y3, 0.018, 0.006, 0.031, "alu_cast", 22))
    m.add(turned(U, d, [(0.018, 0.015), (0.026, 0.027), (0.036, 0.0275), (0.052, 0.028), (0.068, 0.0285), (0.088, 0.029),
                        (0.092, 0.0265)], "alu_cast", 32))
    m.add(turned(U, d, [(0.092, 0.0265), (0.270, 0.0265), (0.272, 0.012)], "shock_body", 24))
    m.add(turned(U, d, [(0.115, 0.027), (0.115, 0.0375), (0.125, 0.0375), (0.125, 0.027)], "alu_machined", 12))      # lock ring
    m.add(turned(U, d, [(0.1255, 0.027), (0.1255, 0.041), (0.137, 0.041), (0.137, 0.0355), (0.137, 0.030)], "alu_machined", 24))
    m.add(coil(U + d * 0.143, U + d * 0.366, 0.0355, 0.006, 8.25, "shock_spring", seg=10))
    m.add(turned(U, d, [(0.372, 0.030), (0.372, 0.0355), (0.372, 0.041), (0.381, 0.041), (0.381, 0.019), (0.445, 0.019)],
                 "alu_cast", 24))
    m.add(turned(U, d, [(0.268, 0.008), (0.400, 0.008)], "chrome", 14))
    m.add(turned(U, d, [(0.336, 0.009), (0.340, 0.021), (0.366, 0.024), (0.372, 0.022)], "rubber_black", 18))         # bump stop
    for s in (1, -1):                                          # clevis ears astride the cushion arm
        p = U + d * (L - 0.046)
        m.add(slab(hull([(A[0], A[2], 0.016), (p[0], p[2], 0.017)]), s * 0.0168, 0.0085, "alu_cast", r=0.002, step=0.005, to=_xz))
    m.add(through(A, 0.021, 0.014))
    m.add(turned(U + d * 0.428 - nr * 0.0185, -nr, [(0, 0.006), (0.004, 0.006), (0.004, 0.003), (0.006, 0.003)], "alu_machined", 12))
    # piggyback reservoir behind the body on the right, its bridge, the compression adjuster facing right
    rc = U + nr * 0.062 - 0.020 * Y3
    m.add(turned(rc, d, [(0.020, 0.012), (0.023, 0.024), (0.029, 0.0265), (0.040, 0.0265), (0.052, 0.0265), (0.064, 0.0265),
                         (0.147, 0.0265), (0.153, 0.024), (0.155, 0.010)], "shock_body", 32))
    e = (rc - U) / np.linalg.norm(rc - U)
    m.add(bar([U + d * 0.052 + e * 0.027, (U + rc) / 2 + d * 0.052, rc + d * 0.052 - e * 0.0245], 0.040, 0.034, "alu_cast"))
    ca = U + d * 0.073 + nr * 0.0146 - 0.0245 * Y3
    m.add(bolt(ca, -Y3, af=0.017, head_h=0.006, flange_d=0.026, mat="alu_machined"))
    m.add(turned(ca - 0.0058 * Y3, -Y3, [(0, 0.006), (0.002, 0.006)], "bolt", 10))
    m.add(through(U, 0.023, 0.014, seat=0.0002))
    return m


# ---------------------------------------------------------------- exhaust
PORT = (0.903, 0.0, 0.613)                                    # exhaust port flange face of detail_engine.py (coordinator)
PORT_DIR = (0.970, 0.0, -0.242)                               # its outward direction
PORT_Y = -0.030                                               # the hidden first 60 mm start right of it: elbow 3 mm off the down tube
WELDS = ((0.913, -0.146, 0.545), (0.690, -0.124, 0.624))      # RIGHT px (2213,1344) and (1916,1240)
CLAMPS = ((0.635, -0.116, 0.626), (0.380, -0.090, 0.6425))    # RIGHT px (1844,1238) and (1500,1223)
HEADER = [
    (0.9125, PORT_Y, 0.6106),   # 10 mm off the engine's flange face and right of its centre: the flange (its part) reaches
                                # x 0.909 at y -0.038, and the down tube stands 30 mm ahead of the port
    (0.9185, -0.0325, 0.6090),  # EST (hidden by the radiator)
    (0.9245, -0.0395, 0.6065),  # EST
    (0.934, -0.0535, 0.601),  # EST
    (0.950, -0.0625, 0.592),  # EST
    (0.9625, -0.065, 0.578),  # RIGHT px (2274,1277): the pipe comes out from behind the radiator
    (0.968, -0.066, 0.560),
    (0.970, -0.068, 0.523),   # RIGHT px (2287,1356); LEFT px (1699,1400): front edge x 0.989; FRONT row 1260 cols 1913..1939
    (0.964, -0.086, 0.480),
    (0.948, -0.112, 0.462),   # RIGHT px (2277,1436): bottom of the bend, outer edge row 1460; LEFT row 1445
    (0.930, -0.138, 0.488),
    (0.913, -0.146, 0.545),   # RIGHT px (2213,1344): weld; FRONT row 1140 col 1784: outer edge y -0.164
    (0.873, -0.151, 0.568),   # TOP col 1870 row 937: outer edge -0.171
    (0.832, -0.143, 0.590),   # RIGHT px (2104,1287); TOP col 1950 row 954: outer edge -0.155 at x 0.80
    (0.757, -0.124, 0.607),   # RIGHT px (2005,1262); TOP col 2000 row 969: outer edge -0.141
    (0.690, -0.124, 0.624),   # RIGHT px (1916,1240): weld; TOP col 2050 row 966: -0.144
    (0.635, -0.116, 0.626),   # RIGHT px (1844,1238): clamp; TOP col 2100 row 975: -0.136
    (0.585, -0.086, 0.626),   # EST: behind the right pivot plate (its inner face is at -0.111)
    (0.530, -0.0645, 0.616),  # EST: between the subframe's bracket (y -0.087) and the shock's spring (r 41.5)
    (0.470, -0.068, 0.613),   # EST: under the subframe's lower rail
    (0.440, -0.074, 0.620),   # EST: 4 mm inside the airbox panel's skin (0.102 at x 0.45, 0.113 at 0.39, 0.123 at 0.36)
    (0.410, -0.081, 0.632),   # EST
    (0.380, -0.090, 0.6425),  # RIGHT px (1500,1223): clamp at the muffler's inlet
    (0.352, -0.096, 0.648),   # into the muffler's nose
]
# muffler: lower edge and rear face from OUT2 'muffler' (right photo, cast at y -0.14); top edge seen at the rear only
# (0.893 at x 0..0.024; a seam rivet at RIGHT px (1114,924): z 0.862 at x 0.095), then hidden: it is kept 4 mm under
# the right side panel of the model (outer skin's edge 0.815 - 1.3 (x - 0.21); inner lip 0.848 at x 0.12, 0.833 at
# 0.15, 0.804 at 0.21, over the can's inner half: _muf_drop), EST. From x 0.30 the can is inside the skin; nose at the rivets seen at
# RIGHT px (1431,1181) and (1408,1220)
MUF_LOW = ([-0.008, -0.0065, -0.004, 0.0, 0.008, 0.018, 0.029, 0.07, 0.113, 0.195, 0.245, 0.301, 0.350],
           [0.818, 0.813, 0.811, 0.806, 0.797, 0.787, 0.775, 0.757, 0.731, 0.688, 0.664, 0.640, 0.628])
MUF_TOP = ([-0.008, -0.0065, -0.004, 0.0, 0.008, 0.018, 0.029, 0.120, 0.150, 0.180, 0.210, 0.224, 0.267, 0.300, 0.350],
           [0.886, 0.8905, 0.893, 0.8945, 0.8935, 0.890, 0.8865, 0.857, 0.837, 0.828, 0.808, 0.792, 0.736, 0.706, 0.668])
MUF_X = [-0.008, -0.0065, -0.004, 0.0, 0.004, 0.008, 0.013, 0.018, 0.0235, 0.029] + list(np.arange(0.036, 0.345, 0.007)) + [0.350]
MUF_CONE = (0.235, 0.350)
# end cap seen from behind (REAR rows 710..890 at x 0: z 0.896 y -0.099..-0.157; 0.869: -0.087..-0.181;
# 0.828: -0.086..-0.195; 0.801: -0.082..-0.190; 0.774: -0.082..-0.180), as (a outward, b up) in half-widths
_SEC = np.array([(-1.0, 0.0), (-0.98, -0.55), (-0.90, -0.85), (-0.65, -1.0), (0.30, -1.0), (0.66, -0.88), (0.90, -0.55),
                 (1.0, -0.12), (0.93, 0.30), (0.74, 0.60), (0.48, 0.86), (0.25, 1.0), (-0.62, 1.0), (-0.86, 0.80), (-0.96, 0.45)])[::-1]
MUF_SEC = smooth_poly(resample(_SEC, 0.17), 1)
OUTLET = np.array([-0.012, -0.138, 0.845])                    # REAR: dark disc centred on px (2205, 787)
MUF_AXIS = np.array([-0.927, 0.0, 0.375])                     # rearward along the can (22 deg: between its two edges)


def _muf(x):
    zl, zt = float(np.interp(x, *MUF_LOW)), float(np.interp(x, *MUF_TOP))
    # plan: TOP cols 2640..2840: outer flank -0.194 at x 0.05, -0.180 at x 0.175; REAR: inner flank -0.082
    yc = float(np.interp(x, [-0.008, MUF_CONE[0], MUF_CONE[1]], [-0.138, -0.127, -0.096]))
    hw = float(np.interp(x, [-0.008, -0.0065, -0.004, MUF_CONE[0], MUF_CONE[1]], [0.050, 0.054, 0.056, 0.046, 0.023]))
    return zl, zt, yc, hw


def _muf_drop(x):
    """How far the can's inner top corner sits below its outer one, under the side panel's inner wall."""
    return float(np.interp(x, [0.09, 0.115, 0.215, 0.235], [0.0, 0.020, 0.020, 0.0]))


def _muf_ring(x):
    zl, zt, yc, hw = _muf(x)
    k = min(max((x - MUF_CONE[0]) / (MUF_CONE[1] - MUF_CONE[0]), 0.0), 1.0)    # the cone turns the section into a circle
    ang = np.arctan2(MUF_SEC[:, 1], MUF_SEC[:, 0])
    S = (1 - k) * MUF_SEC + k * np.stack([np.cos(ang), np.sin(ang)], axis=1)
    z = (zl + zt) / 2 + S[:, 1] * (zt - zl) / 2 - _muf_drop(x) * np.clip((0.3 - S[:, 0]) / 1.3, 0, 1) * np.clip(S[:, 1], 0, None)
    return np.stack([np.full(len(S), x), yc - S[:, 0] * hw, z], axis=1)


def _muf_side(x, z):
    """y of the muffler's outer flank at (x, z)."""
    R = _muf_ring(x)
    near = R[np.abs(R[:, 2] - z) < 0.012]
    return float(near[:, 1].min()) if len(near) else float(R[:, 1].min())


def _clamp(c, d, r):
    m = turned(c - d * 0.007, d, [(0, r + 0.0004), (0.001, r + 0.003), (0.013, r + 0.003), (0.014, r + 0.0004)], "steel", 20,
               False, False)
    lug = c + np.array([0.0, 0.0, -(r + 0.007)])
    m.add(box(lug, (0.014, 0.009, 0.012), "steel"))
    m.add(bolt(lug - 0.0043 * Y3, -Y3, af=0.008, head_h=0.004))
    return m


def exhaust():
    m = Mesh()
    hp = spline(HEADER, 200)
    ig = int(np.argmin(np.linalg.norm(hp - np.array(WELDS[1]), axis=1)))
    rr = np.where(np.arange(len(hp)) < ig, 0.019, 0.0205)       # RIGHT: 37 mm before the weld at x 0.69, 41 after
    rr[ig - 1:ig + 1] = (0.0195, 0.020)
    m.add(tube(hp, rr, 18, "header_steel"))
    tan = np.gradient(hp, axis=0)
    tan /= np.linalg.norm(tan, axis=1, keepdims=True)

    def at(p):
        i = int(np.argmin(np.linalg.norm(hp - np.asarray(p, float), axis=1)))
        return hp[i], tan[i], rr[i]
    for w in WELDS:                                             # the two welds seen in the right photo
        c, d, r = at(w)
        m.add(turned(c - d * 0.003, d, [(0, r), (0.0015, r + 0.0016), (0.0045, r + 0.0016), (0.006, r)], "header_steel", 18, False,
                     False))
    for w in CLAMPS:
        m.add(_clamp(*at(w)))
    # muffler body; the flat end cap is closed ring by ring
    R0 = _muf_ring(MUF_X[0])
    c0 = R0.mean(axis=0)
    m.add(grid(Mesh(), [c0 + (R0 - c0) * q for q in (0.25, 0.5, 0.75)] + [_muf_ring(x) for x in MUF_X], "muffler", cap0=True,
               cap1=True))
    # outlet: tube parallel to the can, dark inside
    a = OUTLET - MUF_AXIS * 0.016
    m.add(hollow(a, MUF_AXIS, 0.0225, 0.0175, 0.016, "muffler", 28))
    m.add(turned(a + MUF_AXIS * 0.0125, MUF_AXIS, [(0, 0.0178)], "muffler_cap", 20, False, True))
    # rivets of the end cap's seam and of the nose (RIGHT px), on the outer flank
    for u, v in ((1114, 924), (1079, 988), (1054.6, 1041.6), (1430.8, 1181.2), (1408, 1219.8)):
        y = -0.19
        for _ in range(3):
            p = _px("right", u, v, "y", y)
            y = _muf_side(p[0], p[2])
        m.add(bolt((p[0], y + 0.0004, p[2]), -Y3, af=0.007, head_h=0.002, mat="steel", kind="cap"))
    # mounts: two straps from the can's inner flank up to the underside of the right subframe rail, inboard of the
    # side panel's lip (y -0.090), each with a bolt (hidden, EST)
    low = _sub_rails(-1)[0][::-1]
    for x in (0.220, 0.255):
        rz = float(np.interp(x, low[:, 0], low[:, 2]))
        zl, zt, yc, hw = _muf(x)
        z1 = rz - 0.0122 - 0.0034                                # 0.5 mm under the sloping rail's lowest point there
        strap = np.array([(x - 0.006, (zl + zt) / 2), (x + 0.006, (zl + zt) / 2), (x + 0.006, z1), (x - 0.006, z1)])
        m.add(slab(strap, yc + hw - 0.0025, 0.004, "steel", r=0.001, step=0.005, to=_xz))
        m.add(bolt((x, yc + hw - 0.0007, z1 - 0.007), Y3, af=0.008, head_h=0.004))
    return m


# ---------------------------------------------------------------- footpegs
def _peg_frame(s):
    """Map from the peg's own coordinates (lx fore-aft, ly along the peg from the bike's centre, lz up from the tooth
    tips) to the bike: the peg rises 8 deg to its tip (REAR: root top z 0.411, tip 0.425)."""
    sn = (PEG_TIP[1] - PEG_ROOT_Z) / (PEG_TIP[0] - PEG_Y0)
    cs = math.sqrt(1 - sn * sn)

    def f(P):
        P = np.atleast_2d(np.asarray(P, float))
        dy = P[:, 1] - PEG_Y0
        return np.stack([PEG[0] + P[:, 0], s * (PEG_Y0 + dy * cs - P[:, 2] * sn), PEG_ROOT_Z + dy * sn + P[:, 2] * cs], axis=1)
    return f


def _peg_loop():
    w, y0, y1, rt, rr = 0.054, PEG_Y0, PEG_TIP[0], 0.024, 0.006       # LEFT zoom: 52..55 mm fore-aft
    pts = []
    for cx, cy, r, a0 in ((w / 2 - rt, y1 - rt, rt, 0), (-w / 2 + rt, y1 - rt, rt, 90), (-w / 2 + rr, y0 + rr, rr, 180),
                          (w / 2 - rr, y0 + rr, rr, 270)):
        for k in range(7):
            a = math.radians(a0 + 15 * k)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return resample(np.array(pts), 0.002)


def footpegs():
    """Cage pegs: a toothed band 4.5 mm thick round the outline (TOP: open cells), two cross bars, hinge pin with
    washer and split pin, return spring. Teeth 4 mm high every 8 mm (LEFT zoom)."""
    m = Mesh()
    loop = _peg_loop()
    n = len(loop)
    tg = np.roll(loop, -1, axis=0) - np.roll(loop, 1, axis=0)
    tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    inward = np.stack([-tg[:, 1], tg[:, 0]], axis=1)
    sarc = np.arange(n) * 0.002
    tooth = -0.004 + 0.004 * (1 - np.abs(2 * ((sarc / 0.008) % 1.0) - 1))
    for s in (1, -1):
        f = _peg_frame(s)
        rings = []
        for i in range(n):
            o, q = loop[i], loop[i] + 0.0045 * inward[i]
            ring = f([(o[0], o[1], -0.021), (o[0], o[1], tooth[i]), (q[0], q[1], tooth[i]), (q[0], q[1], -0.021)])
            rings.append(ring[::-1] if s > 0 else ring)
        m.add(grid(Mesh(), rings + [rings[0]], "steel"))
        for ly in (PEG_Y0 + 0.031, PEG_Y0 + 0.062):               # cross bars
            b = Mesh()
            b.verts(f([(x, y, z) for z in (-0.019, -0.006) for x, y in ((-0.025, ly - 0.002), (0.025, ly - 0.002), (0.025, ly + 0.002),
                                                                         (-0.025, ly + 0.002))]))
            for fc in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                b.face(fc if s > 0 else fc[::-1], "steel")
            m.add(b)
        # hinge: ears on the peg, pin along x through the frame's boss, washer, split pin, torsion spring
        py, pz = PEG_PIN
        for lx in (-0.020, 0.015):
            m.add(box((PEG[0] + lx, s * (py + 0.0075), pz + 0.002), (0.005, 0.015, 0.018), "steel"))
        pin0 = np.array([PEG[0] - 0.031, s * py, pz])
        m.add(turned(pin0, (1, 0, 0), [(0, 0.006), (0.003, 0.006), (0.003, 0.003), (0.060, 0.003)], "bolt", 12))
        m.add(turned(pin0 + (0.054, 0, 0), (1, 0, 0), [(0, 0.006), (0.0015, 0.006)], "bolt", 12))
        m.add(tube([pin0 + (0.0575, 0, -0.007), pin0 + (0.0575, 0, 0.007)], 0.0009, 6, "bolt"))
        m.add(coil(pin0 + (0.0145, 0, 0), pin0 + (0.0235, 0, 0), 0.0040, 0.0009, 5, "steel", seg=6, dead=0, per=14))
        m.add(tube([pin0 + (0.0145, 0, 0.0040), pin0 + (0.0145, s * 0.012, 0.0085)], 0.0009, 6, "steel"))
        m.add(tube([pin0 + (0.0235, 0, 0.0040), pin0 + (0.0235, -s * 0.004, 0.0030)], 0.0009, 6, "steel"))
    return m


# ---------------------------------------------------------------- rear brake: pedal, master cylinder, hose
def rear_brake():
    m = Mesh()
    piv = _px("right", 1706, 1493, "y", -0.143)                 # RIGHT zoom: pedal pivot bolt
    piv[1] = -(Y_PLATE + 0.0002)
    m.add(turned(piv, -Y3, [(0, 0.014), (0.0125, 0.013)], "alu_cast", 20))
    m.add(bolt(piv - 0.0122 * Y3, -Y3, af=0.017, head_h=0.006, mat="steel", kind="cap"))
    # arm: cast boomerang under the pivot nut and over the clutch cover's lower edge to the toe piece
    # (RIGHT zoom, middle of the arm; TOP: tip at px (2045,932), arm from row 955 to row 975)
    arm = [piv - 0.0065 * Y3] + [_px("right", u, v, "y", y) for u, v, y in
                                 ((1720, 1478, -0.1445), (1734.7, 1468, -0.1455), (1755.4, 1466, -0.147), (1796.7, 1478.3, -0.150),
                                  (1838, 1507.2, -0.154), (1862.9, 1530, -0.157), (1915, 1541, -0.160), (1944, 1545, -0.161))]
    ap = spline(arm, 26)
    m.add(bar(ap, 0.009, np.linspace(0.024, 0.013, len(ap)), "alu_cast"))
    tip = ap[-1]
    # toe piece: ribbed block across the arm's end (TOP rows 922..955: y -0.161..-0.193)
    tp = [(0.001, -0.005), (0.015, -0.005), (0.015, 0.004)]
    for k in range(4):
        tp += [(0.0125 - 0.0055 * k, 0.007), (0.0098 - 0.0055 * k, 0.004)]
    tp += [(-0.007, 0.004), (-0.007, -0.005)]
    m.add(slab(np.array(tp) + (tip[0], tip[2]), -0.1775, 0.032, "steel", r=0.0012, step=0.004, to=_xz))
    # rear lever to the master cylinder's clevis (RIGHT px (1635,1505)), push rod, boot, body with the reservoir on
    # top (RIGHT px 1623..1652 x 1370..1445, top at px (1600,1295)), two bolts into the plate's rear edge
    pin = _px("right", 1635.5, 1505, "y", -0.129)
    lever_mid = (piv + pin) / 2 + (0, -0.003, 0.004)
    m.add(bar([piv - 0.0065 * Y3, lever_mid, pin], 0.007, (0.022, 0.016, 0.014), "alu_cast"))
    m.add(box(pin + (0, 0, 0.004), (0.011, 0.013, 0.020), "steel"))
    m.add(bolt(pin - 0.0063 * Y3, -Y3, af=0.008, head_h=0.004))
    a0, a1 = np.array([0.4765, -0.128, 0.468]), np.array([0.4525, -0.128, 0.585])
    d = (a1 - a0) / np.linalg.norm(a1 - a0)
    m.add(tube([pin + (0, 0.001, 0.008), a0 + d * 0.004], 0.003, 8, "steel"))
    m.add(turned(a0, d, [(0.0, 0.006), (0.004, 0.0095), (0.020, 0.0095), (0.022, 0.006)], "rubber_black", 14))
    m.add(turned(a0, d, [(0.021, 0.0125), (0.076, 0.0125), (0.079, 0.0165), (0.112, 0.0165)], "alu_cast", 18))
    m.add(turned(a0, d, [(0.112, 0.0175), (0.1185, 0.0175), (0.1195, 0.015)], "plastic_black", 18))
    for sb in (0.032, 0.066):                                   # mounting ears, 0.2 mm off the plate's face
        b = a0 + d * sb
        ear = np.array([(0.519, b[2] + 0.008), (b[0] - 0.006, b[2] + 0.008), (b[0] - 0.006, b[2] - 0.008), (0.519, b[2] - 0.008)])
        m.add(slab(ear, -(Y_PLATE + 0.0027), 0.005, "alu_cast", r=0.001, step=0.005, to=_xz))
        m.add(bolt((0.509, -(Y_PLATE + 0.0049), b[2]), -Y3, af=0.010, head_h=0.005))
    # pressure hose: banjo on the body, along the right arm in two clips (RIGHT px (1404,1466)), up to the caliper
    bj = a0 + d * 0.030 + np.array([-0.0122, 0, 0])
    m.add(bolt(bj, (-1, 0, 0.15), af=0.012, head_h=0.006))
    hose = spline([bj + (-0.004, 0, 0), (0.440, -0.118, 0.497), (0.400, -0.110, float(_arm_top(0.40)) + 0.014),
                   (0.297, -0.108, float(_arm_top(0.297)) + 0.0125), (0.200, -0.108, float(_arm_top(0.20)) + 0.012),
                   (0.130, -0.105, float(_arm_top(0.13)) + 0.016), (0.092, -0.100, 0.436)], 40)
    m.add(tube(hose, 0.0042, 8, "rubber_black"))
    m.add(turned(hose[-1], (0, -1, 0), [(-0.003, 0.0065), (0.003, 0.0065)], "bolt", 12))
    hd = np.gradient(hose, axis=0)
    for x in (0.297, 0.170):
        i = int(np.argmin(np.abs(hose[:, 0] - x)))
        hpnt, tg = hose[i], hd[i] / np.linalg.norm(hd[i])
        m.add(hollow(hpnt - tg * 0.006, tg, 0.0075, 0.0044, 0.012, "plastic_black", 12))
        z0, z1 = float(_arm_top(hpnt[0])) + 0.0012, hpnt[2] - 0.0065
        m.add(box((hpnt[0], hpnt[1], (z0 + z1) / 2), (0.006, 0.010, z1 - z0), "plastic_black"))
    # return spring from the lever's tab down to the bracket's rear edge (RIGHT px (1654,1522) to (1697,1547))
    sa, sb = _px("right", 1654, 1522, "y", -0.131), _px("right", 1697.5, 1546.6, "y", -0.131)
    m.add(coil(sa, sb, 0.0045, 0.0008, 13, "steel", seg=6, dead=0, per=12))
    m.add(tube([sa, (lever_mid[0] - 0.004, -0.131, lever_mid[2] - 0.006)], 0.0008, 6, "steel"))
    m.add(tube([sb, (0.5425, -0.131, 0.3895)], 0.0008, 6, "steel"))
    return m


PARTS = {"frame": frame, "subframe": subframe, "swingarm": swingarm, "rear_axle": rear_axle, "chain_guide": chain_guide,
         "linkage": linkage,
         "shock": shock, "exhaust": exhaust, "footpegs": footpegs, "brake_pedal": rear_brake}   # (named "rear_brake" it was
#   replaced by detail_wheels.py's caliper, loaded later: the pedal and master cylinder were missing from the bike)
SMOOTH = {"footpegs": 30, "frame": 42}
BEVEL = {"swingarm": 0.0004}          # its edges are modelled (rounded rims, chamfers); build_bike's 3 mm bevel ate them
