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
             "alu_weld": dict(rgb=(176, 176, 180), metal=1.0, rough=0.5),   # duller than the arm (RIGHT: the welds)
             "alu_satin": dict(rgb=(198, 198, 202), metal=1.0, rough=0.36),   # cast ends: no brushing (aniso streaked them)
             "axle_block": dict(rgb=(172, 172, 176), metal=1.0, rough=0.28),  # rr34: as light as the casting, bright edges
             "zinc": dict(rgb=(205, 205, 210), metal=1.0, rough=0.22),        # bright plated adjusters (LEFT, lr34)
             "groove": dict(rgb=(40, 40, 42), metal=1.0, rough=0.6),
             "alu_forged": dict(rgb=(196, 196, 200), metal=1.0, rough=0.3),   # Dirt Rider 09: bright forged rods
             "peg_black": dict(rgb=(24, 24, 26), metal=0.7, rough=0.32),      # detail 475839: black pegs
             "peg_edge": dict(rgb=(150, 150, 154), metal=1.0, rough=0.35),     # their worn tooth tips
             "muffler": dict(rgb=(190, 190, 195), metal=1.0, rough=0.36, aniso=0.5, normal="stock/brushed_n.png",
                             normal_strength=1.0),                     # brushed along the can (RIGHT, rr34, REAR); rough
             #     0.36 (round 3, was 0.26): REAR shows the cap evenly lit, the sharper reflections drew a dark band
             "bore": dict(rgb=(10, 10, 11), metal=0.3, rough=0.7),     # the hollow axle's inside: black in every photo
             "frame_cast": dict(rgb=(200, 200, 204), metal=1.0, rough=0.42, normal="stock/cast_n.png",
                                normal_strength=0.3),                  # the frame's castings: matte, grained (RIGHT, LEFT)
             "steel_dark": dict(rgb=(118, 118, 122), metal=1.0, rough=0.45),  # LEFT: the pivot bolt's head in its recess
             "frame_spar": dict(rgb=(205, 205, 208), metal=1.0, rough=0.32, aniso=0.6, normal="stock/brushed_n.png",
                                normal_strength=0.8),                  # the extruded spars: brushed along their length
             "mc_cast": dict(rgb=(184, 184, 188), metal=1.0, rough=0.5, normal="stock/mc_n.png", normal_strength=1.0),
             #     the master cylinder's casting: grey, coarse grain, cast lettering (RIGHT: lit faces 197, the frame's 186)
             "mc_lid": dict(rgb=(46, 46, 50), metal=0.0, rough=0.3),   # its cap: smoky dark (RIGHT band grey 99, rr34)
             "mc_lens": dict(rgb=(104, 100, 94), metal=0.0, rough=0.06),   # sight window: grey glass (REAR mc6, rr34)
             "mc_ring": dict(rgb=(176, 176, 178), metal=0.0, rough=0.45)}   # the window's light retaining ring
CLASS = {"shock_spring": "black", "peg_black": "black"}
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


def _plate2d(outer, holes, mat, to3d, step, rings, hole_rings=None, hole_step=None, grid_step=None, extra=None):
    """geom.plate2d with its rows of vertices following the holes too (a window's rounded rim needs them as much as
    the outline does: on the bare grid it came out frilled). EXTRA: rows of points (2D) laid along features of the
    faces (a boss's fillet, a rib's crest), kept where they are inside and 0.45 GRID_STEP clear of the others."""
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
    if extra is not None and len(extra):
        E = np.asarray(extra, float)
        ok = inside(loops[0], E) & (tree.query(E)[0] > max(rings) + 0.3 * step)
        for h in loops[1:]:
            ok &= ~inside(h, E)
        E = E[ok]
        if len(R):
            E = E[cKDTree(R).query(E)[0] > 0.45 * step]
        keep = []
        for i in range(len(E)):
            if not keep or np.min(np.hypot(*(E[keep] - E[i]).T)) > 0.3 * step:
                keep.append(i)
        E = E[keep]
        R = np.vstack([R, E]) if len(R) else E
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
    if hasattr(to3d, "batch"):
        T3, B3 = to3d.batch(P)
        top, bot = m.verts(T3), m.verts(B3)
    else:
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


# ---------------------------------------------------------------- frame rear: the cast pivot section (round 3)
# Read on 3x crops of the studio photos with 10 px ticks (scratch r_low3, l_low, l_weld, r_weld, r_fz1, piv2). The
# rear of each side is one casting: the extruded spar's end is a rounded tongue welded into it (a U-shaped TIG bead),
# below it the leg runs down round the pivot boss into a lower section that meets the cradle rail at a second weld.
# Lower section, past the old outline's end (LEFT: front branch from the pivot down to the cradle weld, its bottom
# edge, the rear under the footpeg; RIGHT the same, partly behind the pedal). The left front branch's edge from a 5x
# crop (l_shift): its lit rim 2 to 3 px inside the silhouette, under the shift lever's clamp at about (2185, 1505)
LOW_PX = {"left": [(2232, 1440), (2222, 1450), (2221, 1477), (2216, 1500), (2209, 1516), (2199, 1530), (2183, 1540),
                   (2160, 1545), (2140, 1550), (2124, 1555), (2117, 1597), (2137, 1600), (2193, 1600), (2210, 1596),
                   (2227, 1590), (2260, 1584), (2292, 1578), (2306, 1560), (2306, 1520), (2300, 1500), (2290, 1450)],
          "right": [(1768, 1440), (1785, 1470), (1790, 1505), (1792, 1527), (1817, 1543), (1850, 1550), (1874, 1553),
                    (1884, 1588), (1867, 1590), (1833, 1592), (1800, 1590), (1767, 1586), (1743, 1582), (1710, 1575),
                    (1694, 1566), (1690, 1530), (1696, 1500), (1700, 1450)]}
# RIGHT: the master cylinder's two tabs behind the leg (bosses round the bolts at (1645, 1338) and (1652, 1402), 24 px
# across) and the square pocket between them (floor at u 1665)
TAB_PX = [(1668, 1300), (1655, 1318), (1643, 1325), (1635, 1333), (1634, 1343), (1641, 1351), (1655, 1354),
          (1665, 1357), (1666, 1381), (1652, 1388), (1643, 1391), (1639, 1401), (1642, 1411), (1653, 1415),
          (1668, 1418), (1680, 1420), (1680, 1300)]
TAB_BOLTS_PX = [(1645, 1338), (1652, 1402)]
# the U bead's centre line round the spar's end (top run, the end, the lower run), LEFT and RIGHT; the top run goes on
# along the spar's top edge under the upper mount's ear (l_weld 3x: to (2020, 963); r_weld: from (1993, 960))
TONGUE_PX = {"left": [(2020, 963), (2045, 982), (2070, 1000), (2103, 1022), (2133, 1040), (2167, 1062), (2193, 1083),
                      (2215, 1105), (2228, 1128),
                      (2231, 1148), (2222, 1166), (2203, 1174), (2182, 1168), (2160, 1153), (2127, 1133), (2100, 1114),
                      (2067, 1091), (2043, 1077)],
             "right": [(1993, 960), (1973, 970), (1951, 984),
                       (1930, 999), (1897, 1017), (1867, 1037), (1840, 1057), (1813, 1077), (1790, 1097), (1773, 1120),
                       (1772, 1140), (1780, 1157), (1800, 1167), (1827, 1163), (1853, 1153), (1883, 1137), (1913, 1120),
                       (1945, 1102)]}
Y_MID = Y_PLATE - T_SPAR / 2            # the plate's mid plane: the outline is cast on it, as _frame_outline


def _cast_px(view, pts, y):
    return np.array([_px(view, u, v, "y", y)[[0, 2]] for u, v in pts])


def _side_outline(s):
    """Side outline of one side's frame plate (x, z): the spar and leg of _frame_outline (OUT2, left photo: it fits
    the right photo's leg within 4 px), the footpeg bracket, the lower section from each side's own photo and, on the
    right, the master cylinder's tabs."""
    view = "left" if s > 0 else "right"
    polys = [_frame_outline(), _bracket_outline(), _cast_px(view, LOW_PX[view], s * Y_MID)]
    if s < 0:
        polys.append(_cast_px("right", TAB_PX, -Y_MID))
    return _clean(_union_outline(polys), 0.0015, 0.0012)


def _tongue(s):
    """The U bead's centre line (x, z) round the extruded spar's end, on the spar's outer face."""
    view = "left" if s > 0 else "right"
    P = _cast_px(view, TONGUE_PX[view], s * 0.134)
    return spline(np.column_stack([P[:, 0], np.zeros(len(P)), P[:, 1]]), 80)[:, [0, 2]]


# the pivot's two ends (piv2 crop, intensity rows and columns through the centres):
# RIGHT a nut in a round counterbore: the bore's dark ring from u 1731 to 1773 (42 px, 31.8 mm); the nut's flats
#   at u 1738 and 1766 (28 px, 21.2 mm), its corners up and down at v 1419 and 1451 (24.2 mm: 21 mm across flats);
#   the bolt's end a bright ring 21 px (16 mm) round a black bore 9 px (7 mm)
# LEFT the head in a hexagonal recess: the gap's dark outline with corners fore and aft at u 2226 and 2267.5 (31.4
#   mm) and flats at v 1415 and 1451.5 (27.7 mm); inside it the head's darker face and a black bore 14 px (10.6 mm)
PIV_CB = (0.0159, 0.006)                # counterbore radius, depth (EST: deep enough to take the nut's flange)
PIV_NUT = (0.021, 0.008)                # across flats, thickness
PIV_END = (0.008, 0.0035, 0.0015)       # bolt end radius, its bore radius, standing proud of the nut
PIV_HEX = (0.0277, 0.0035)              # recess across flats, depth
PIV_HEAD = (0.0250, 0.0053)             # head across flats (1.4 mm gap all round: the outline 2 px wide), bore radius
BOSS_R, BOSS_H = 0.034, 0.0015          # the boss round the pivot (round 4; it was 26 mm): its fold, a raised rim, is
#   a C round the pivot cut open by the leg's front edge: RIGHT column 1700 lit from v 1415 to 1440 (40 mm from the
#   nut, chassis4/fr2), row 1420 lit at u 1700..1710; LEFT row 1440 the boss's face lit to u 2296 (36.6 mm from the
#   head) and dropping there; the detail photo 475836 (d836_leg) shows the fold as a crisp edge on the boss's rear
BOSS_RIM = (0.0035, 0.0008)             # the rim's half width and height over the boss's face (EST: the fold's lit band
#                                         is 4 to 6 px wide; the face inside it reads recessed)
TURN = (0.0010, 0.0025, 0.018)          # round 4: the leg's face turns away over the last 18 mm before its edges, 2.5
#   mm at the front (the C round the engine), 1 mm at the rear (a crowned section): the detail photo 475836 (directional
#   light, the leg 208 px = 50 mm wide) rises 125 -> 181 over the first 10 mm from the front edge and is even (200) over
#   the rest (rows 1300, 1500, 1700); no channel along the rim. RIGHT row 1340 brightens 182 -> 200 toward the front
#   edge before its highlight. The old flat face rendered one even grey (f8_right_2)
TAB_BOSS = (0.009, 0.0020)              # RIGHT: the tabs' bosses 24 px across, standing 2 mm (EST) off the tab
TAB_T = 0.0045                          # EST: the tabs' thickness (a lug, not the leg's 26 mm box); the master cylinder
#                                         (brake_pedal) is flattened in front where it passes inboard of them
# LEFT px: the triangular pocket under the pivot between the front branch and the rib that runs down to the footpeg
# (l_pocket: lit rib from (2238, 1457) to (2278, 1505), the pocket's shaded floor inside (2246, 1476) (2253, 1508)
# (2272, 1508)); the right one is behind the pedal and is taken as the mirror image
POCKET_PX = [(2247, 1474), (2252, 1509), (2273, 1509)]
RIB_PX = [(2238, 1457), (2259, 1481), (2279, 1506)]
CAST_STEP = 0.0025


def _smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _seg_dist(P, a, b):
    """Distance from points P (N, 2) to the segment AB."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-18), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def _poly_sdist(poly, step=0.0001):
    """Signed distance to a closed polygon (negative inside), to the polygon resampled every STEP."""
    tree = cKDTree(resample(np.asarray(poly, float), step))

    def g(P):
        P = np.atleast_2d(P)
        d = tree.query(P)[0]
        return np.where(inside(poly, P), -d, d)
    return g


class _Cast:
    """The rear of one side's frame plate as a height field over its side outline: the outer face at _spar_y(x)
    with its edges rounded (7 mm where they face forward, the C round the engine; 4 mm elsewhere: RIGHT and LEFT,
    the front edge's light falls off over 8 to 10 px, the rear edge's highlight is 3 to 4 px), the inner face 26 mm
    behind it, and on the outer face the pivot boss, the footpeg bracket's pad, the master cylinder tabs' bosses and
    chevron ribs (right), the pocket and rib under the pivot."""

    def __init__(self, s):
        self.s = s
        view = "left" if s > 0 else "right"
        self.view = view
        self.o = _side_outline(s)
        o = self.o
        tg = np.roll(o, -1, axis=0) - np.roll(o, 1, axis=0)
        nrm = np.stack([tg[:, 1], -tg[:, 0]], axis=1)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        if inside(o, (o + 0.001 * nrm)[::7]).mean() > 0.5:
            nrm = -nrm                                               # outward
        fine = resample(o, 0.0004)
        self.edge = cKDTree(fine)
        self.edge_r = 0.004 + 0.003 * np.clip(nrm[cKDTree(o).query(fine)[1], 0], 0, 1)
        self.leg_sd = None
        if s < 0:                                                    # the tabs' edges: 1.2 mm (r_mc: crisp lugs)
            self.leg_sd = _poly_sdist(_frame_outline(), 0.0003)
            self.tab_sd = _poly_sdist(_cast_px("right", TAB_PX, -Y_MID), 0.0003)   # only the tabs: not the lower
            fs = (self.leg_sd(fine) > 0.0015) & (self.tab_sd(fine) < 0.002)       # section (audit: it was thin)
            self.edge_r = np.where(fs, 0.0012, self.edge_r)
        self.piv = np.array([PIVOT[0], PIVOT[2]])
        if s > 0:
            a = np.radians(np.arange(0, 360, 60))                     # corners fore and aft
            rc = PIV_HEX[0] / 2 / math.cos(math.pi / 6)
            self.hole = resample(np.stack([self.piv[0] + rc * np.cos(a), self.piv[1] + rc * np.sin(a)], 1), 0.0008)
        else:
            self.hole = circle(PIV_CB[0], 72, *self.piv)
        self.hole_d = cKDTree(resample(self.hole, 0.0001))
        self.tabs = [_cast_px("right", [b], -Y_PLATE)[0] for b in TAB_BOLTS_PX] if s < 0 else []
        pk = _cast_px("left", POCKET_PX, Y_PLATE)
        rib = _cast_px("left", RIB_PX, Y_PLATE)
        self.pocket = _clean(pk, 0.0008, 0.0012)
        self.pocket_sd = _poly_sdist(self.pocket)
        self.rib = rib
        br = _bracket_outline()
        self.pad = br
        self.pad_sd = _poly_sdist(br)
        # the pedal's pivot on the right sits on the pad too (RIGHT px (1709, 1493): its boss's inner face at 0.1414)
        self.pedal = _px("right", 1709.2, 1493.2, "y", -0.150)[[0, 2]] if s < 0 else None
        self.chev = []
        for b in self.tabs:                                          # RIGHT: a ">" of two ribs from each boss into the
            for ang in (28, -28):                                    # leg (r_low3: 15 mm long, 30 deg either side)
                a = math.radians(ang)
                self.chev.append((b + 0.010 * np.array([math.cos(a), math.sin(a)]),
                                  b + 0.022 * np.array([math.cos(a), math.sin(a)])))

    def r_edge(self, P):
        """Distance to the outline and the edge radius there, the radius blended over the outline points within a
        few mm (taken from the nearest point alone it jumped where two edges of different radius are equally near,
        and the rounding stepped: torn white shards in the close-ups)."""
        d, i = self.edge.query(P, k=48)
        w = np.exp(-((d - d[:, :1]) / 0.002) ** 2)
        r = (w * self.edge_r[i]).sum(axis=1) / w.sum(axis=1)
        return d[:, 0], r

    def feat(self, P):
        """Height of the outer face's features above the plane, at points P (N, 2)."""
        P = np.atleast_2d(np.asarray(P, float))
        h = np.zeros(len(P))
        rb = np.linalg.norm(P - self.piv, axis=1)
        # (only broad features here: narrow ridges on the 2.5 mm triangulation came out as torn shards in the
        # close-ups; the ribs are swept beads, _cast_ribs)
        h += BOSS_H * _smoothstep((BOSS_R + 0.003 - rb) / 0.006)
        h += BOSS_RIM[1] * (1 - _smoothstep(np.abs(rb - (BOSS_R - BOSS_RIM[0])) / BOSS_RIM[0]))
        pad = -self.pad_sd(P)
        lift = _smoothstep((pad + 0.004) / 0.008)
        if self.pedal is not None:
            lift = np.maximum(lift, _smoothstep((0.018 - np.linalg.norm(P - self.pedal, axis=1)) / 0.008))
        h += 0.004 * lift
        for b in self.tabs:
            h += TAB_BOSS[1] * _smoothstep((TAB_BOSS[0] + 0.002 - np.linalg.norm(P - b, axis=1)) / 0.004)
        sd = self.pocket_sd(P)
        h -= 0.002 * _smoothstep((0.001 - sd) / 0.005)
        return h

    def extra(self):
        """Rows of vertices along the features (the grid alone frilled them)."""
        rows = []
        for r in (BOSS_R - 2 * BOSS_RIM[0], BOSS_R - 1.4 * BOSS_RIM[0], BOSS_R - BOSS_RIM[0], BOSS_R - 0.6 * BOSS_RIM[0],
                  BOSS_R - 0.0002, BOSS_R + 0.0015, BOSS_R + 0.0035):
            rows.append(resample(circle(r, 8, *self.piv), 0.0012))
        h = self.hole
        c = h.mean(axis=0)
        for r in (0.0024, 0.0040):                                  # round the counterbore or recess
            rows.append(resample(c + (h - c) * (1 + r / np.linalg.norm(h - c, axis=1).mean()), 0.0012))
        for b in self.tabs:
            for r in (TAB_BOSS[0] - 0.002, TAB_BOSS[0], TAB_BOSS[0] + 0.002):
                rows.append(resample(circle(r, 8, *b), 0.0012))
        c = self.pocket.mean(axis=0)
        for k in (-0.004, -0.0015, 0.001):
            q = self.pocket - c
            rr = np.linalg.norm(q, axis=1, keepdims=True)
            rows.append(resample(c + q * (1 + k / rr.mean()), 0.0012))
        return np.vstack(rows)

    def turn(self, P, d, r):
        """How far the leg's outer face turns away near its edges (TURN, more where the edge radius R is the front's):
        not on the spar's end above the U bead, the tabs, the footpeg pad or the pedal's seat (they carry parts)."""
        amp = TURN[0] + (TURN[1] - TURN[0]) * np.clip((r - 0.004) / 0.003, 0, 1)
        t = amp * (1 - _smoothstep(d / TURN[2]))
        t = t * _smoothstep((0.655 - P[:, 1]) / 0.025) * _smoothstep((self.pad_sd(P) - 0.002) / 0.006)
        if self.pedal is not None:
            t = t * _smoothstep((np.linalg.norm(P - self.pedal, axis=1) - 0.020) / 0.008)
        if self.leg_sd is not None:
            t = t * _smoothstep((self.tab_sd(P) - 0.002) / 0.004)
        return t

    def surf(self, P, outer, rim=True):
        """|y| of the outer (OUTER) or inner face at points P (N, 2)."""
        P = np.atleast_2d(np.asarray(P, float))
        d, r = self.r_edge(P)
        k = np.where(d < r, r - np.sqrt(np.maximum(r * r - (r - np.minimum(d, r)) ** 2, 0)), 0.0)
        base = np.array([_spar_y(x) for x in P[:, 0]])
        if outer:
            kh = 0.0
            if rim:
                dh = self.hole_d.query(P)[0]
                rh = 0.0010
                kh = np.where(dh < rh, rh - np.sqrt(np.maximum(rh * rh - (rh - np.minimum(dh, rh)) ** 2, 0)), 0.0)
            return base - k - kh + self.feat(P) - self.turn(P, d, r)
        ri = np.minimum(r, 0.003)
        ki = np.where(d < ri, ri - np.sqrt(np.maximum(ri ** 2 - (ri - np.minimum(d, ri)) ** 2, 0)), 0.0)
        # the lower section's front reaches in round the cradle rail's end (the rail runs 1 to 3 cm inboard)
        wrap = 0.022 * _smoothstep((P[:, 0] - 0.600) / 0.040) * _smoothstep((0.420 - P[:, 1]) / 0.020)
        yi = base - T_SPAR + ki - wrap
        if self.leg_sd is not None:
            # the master cylinder's tabs are lugs 5 mm thick behind the leg (the cylinder's own lugs sit inboard of them)
            tf = _smoothstep((self.leg_sd(P) - 0.0005) / 0.003) * _smoothstep((0.002 - self.tab_sd(P)) / 0.002)
            yi = (1 - tf) * yi + tf * (base - TAB_T + ki)
        return yi

    def y_out(self, P):
        return self.surf(P, True, rim=False)

    def build(self, mat_spar, mat_cast):
        s = self.s
        rings = (0.0006, 0.0018, 0.0032, 0.0048, 0.0066)
        hrings = (0.0003, 0.0008, 0.0014)
        pts_cache = {}
        surf = self.surf

        def to3d(u, v, w):
            key = (round(u, 7), round(v, 7))
            if key not in pts_cache:
                pts_cache[key] = (float(surf(np.array([[u, v]]), True)[0]), float(surf(np.array([[u, v]]), False)[0]))
            yo, yi = pts_cache[key]
            return (u, s * (yo if w > 0 else yi), v)

        def batch(P):
            yo, yi = surf(P, True), surf(P, False)
            return (np.column_stack([P[:, 0], s * yo, P[:, 1]]), np.column_stack([P[:, 0], s * yi, P[:, 1]]))
        to3d.batch = batch
        area = lambda q: float(np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1]))
        hole = self.hole if (area(self.hole) > 0) == (area(self.o) > 0) else self.hole[::-1]
        m = _plate2d(self.o, [hole], mat_cast, to3d, CAST_STEP, rings, hrings, 0.0008, CAST_STEP, self.extra())
        # normals out: the first triangle is on the outer face, the first quad on the outline's rim
        V = np.asarray(m.V)
        tri = next(f for f in m.F if len(f) == 3)
        quad = next(f for f in m.F if len(f) == 4)
        nt = np.cross(V[tri[1]] - V[tri[0]], V[tri[2]] - V[tri[0]])
        nq = np.cross(V[quad[1]] - V[quad[0]], V[quad[2]] - V[quad[0]])
        cq = V[list(quad)].mean(axis=0)[[0, 2]]
        out2 = cq - self.o.mean(axis=0)
        j = int(cKDTree(self.o).query(cq)[1])
        tg = self.o[(j + 1) % len(self.o)] - self.o[j - 1]
        o2 = np.array([tg[1], -tg[0]])
        if not inside(self.o, (cq + 0.0005 * o2 / np.linalg.norm(o2))[None, :])[0]:
            out2 = o2
        else:
            out2 = -o2
        ft = nt[1] * s < 0
        fq = nq[0] * out2[0] + nq[2] * out2[1] < 0
        m.F = [q[::-1] if (ft if len(q) == 3 else fq) else q for q in m.F]
        # the extruded spar's end (inside the U bead's line, closed far forward along the spar) keeps the spar's
        # brushed finish; the rest is the casting
        t = _tongue(s)
        dirn = np.array([1.0, 0.632]) / math.hypot(1.0, 0.632)
        tongue = np.vstack([t[0] + 0.3 * dirn, t, t[-1] + 0.3 * dirn])
        V = np.asarray(m.V)
        C = np.array([V[list(f)][:, [0, 2]].mean(axis=0) for f in m.F])
        # and every face under the bead (6.5 mm of its line): where the bead runs along the plate's top edge the
        # boundary otherwise ran along the rounded edge and the two finishes alternated face by face (a saw tooth)
        sp = inside(tongue, C) | (cKDTree(resample(np.vstack([t, t[::-1]]), 0.0005)).query(C)[0] < 0.0065)
        m.M = [mat_spar if q else mat_cast for q in sp]
        _uv_box(m, 0.08)
        # the spar's brushing runs along it (LEFT, RIGHT: streaks parallel to its edges): UVs along and across it
        for i in np.nonzero(sp)[0]:
            Q = V[list(m.F[i])]
            m.uv[i] = [(float((q[0] * dirn[0] + q[2] * dirn[1]) / BRUSH_TILE),
                        float((-q[0] * dirn[1] + q[2] * dirn[0] + 0.3 * q[1]) / BRUSH_TILE)) for q in Q]
        return m


def _bead(P, N, w, h, pitch=0.0020, sink=0.6, taper=0.004, mat="alu_weld", smooth=False):
    """TIG bead along an open path P (N, 3) lying on a face with outward normals N: _weld's rippled half-buried
    ellipse, its width and height tapering to nothing over TAPER at both ends. SMOOTH: no ripples (a cast rib)."""
    P, N = np.asarray(P, float), np.asarray(N, float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    arc = np.concatenate([[0], np.cumsum(seg)])
    n = max(int(arc[-1] / (pitch / 3)), 4)
    if smooth:
        pitch = 1e9
    a = np.linspace(0, arc[-1], n)
    Q = np.stack([np.interp(a, arc, P[:, k]) for k in range(3)], axis=1)
    Nq = np.stack([np.interp(a, arc, N[:, k]) for k in range(3)], axis=1)
    Nq /= np.linalg.norm(Nq, axis=1, keepdims=True)
    T = np.gradient(Q, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    L = np.cross(Nq, T)
    L /= np.linalg.norm(L, axis=1, keepdims=True)
    phi = np.linspace(0, 2 * math.pi, 12, endpoint=False)
    rings = []
    for i in range(n):
        tp = _smoothstep(min(a[i], arc[-1] - a[i]) / taper) ** 0.5
        e = np.cos(phi)
        q = a[i] / pitch + 0.55 * e ** 2
        ripple = q % 1.0
        jit = (np.sin(np.floor(q) * 12.9898) * 43758.5453) % 1.0
        hh = h * tp * (0.84 + 0.16 * np.sqrt(ripple)) * (0.94 + 0.12 * jit)
        u = np.sin(phi)
        off = np.where(u > 0, u * hh, u * h * sink)
        rings.append(Q[i] + np.outer(off, Nq[i]) + np.outer(e * w / 2 * max(tp, 0.15) * (0.97 + 0.03 * ripple), L[i]))
    m = grid(Mesh(), rings, mat, closed_u=True, cap0=True, cap1=True)
    # outward: the first ring's top point must lie along +N from the path
    V = np.asarray(m.V)
    f = m.F[len(m.F) // 2]
    nn = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
    c = V[list(f)].mean(axis=0)
    j = int(np.argmin(np.linalg.norm(Q - c, axis=1)))
    if np.dot(nn, c - Q[j]) < 0:
        m.F = [q[::-1] for q in m.F]
    return m


def _face_normal(s, x):
    """Outward normal of the plate's outer face at x (the face follows _spar_y in plan)."""
    dfx = (_spar_y(x + 0.001) - _spar_y(x - 0.001)) / 0.002
    n = np.array([-dfx, float(s), 0.0])
    return n / np.linalg.norm(n)


def _frame_welds(m, cast):
    """U bead round the extruded spar's end (LEFT and RIGHT: 8 to 10 mm wide, ripples every 2 mm) and the bead where
    the lower section meets the cradle rail (LEFT px (2136,1556)..(2117,1598), RIGHT (1874,1553)..(1884,1589))."""
    s = cast.s
    t = _tongue(s)
    y = cast.y_out(t)
    P = np.column_stack([t[:, 0], s * y, t[:, 1]])
    N = np.array([_face_normal(s, x) for x in t[:, 0]])
    m.add(_bead(P, N, 0.0100, 0.0024))
    px = [(2136, 1556), (2121, 1580), (2117, 1598)] if s > 0 else [(1874, 1553), (1880, 1572), (1884, 1589)]
    q = _cast_px(cast.view, px, s * Y_PLATE)
    q = spline(np.column_stack([q[:, 0], np.zeros(len(q)), q[:, 1]]), 20)[:, [0, 2]]
    y = cast.y_out(q)
    keep = y > np.array([_spar_y(x) for x in q[:, 0]]) - 0.0035          # on the face, not over the rounded edges
    q, y = q[keep], y[keep]
    m.add(_bead(np.column_stack([q[:, 0], s * y, q[:, 1]]), [_face_normal(s, x) for x in q[:, 0]], 0.0080, 0.0018))


def _pivot_ends(m, cast):
    """RIGHT: the nut in its round counterbore, the bolt's hollow end; LEFT: the head in its hexagonal recess."""
    s = cast.s
    out = s * Y3
    yf = float(cast.y_out(np.array([[PIVOT[0], PIVOT[2] + BOSS_R - 0.004]]))[0])     # the boss's face
    face = PIVOT + s * (yf - 0.0010) * Y3                                            # the rim's rounding ends here
    if s < 0:
        R, dep = PIV_CB
        fl = face - out * (dep - 0.0010)
        # the bore's wall and floor (seen from outside: normals toward the axis and outward)
        m.add(turned(face + out * 0.0002, -out, [(0, R), (dep - 0.0008, R), (dep - 0.0008, 0.0001)], "frame_cast", 72,
                     False, True))
        af, hn = PIV_NUT
        m.add(hexnut(fl, out, af, hn, PIV_END[0] - 0.0002, "steel", phase=math.pi / 6))
        r_end, r_b, pr = PIV_END
        top = fl + out * (hn + pr)
        m.add(turned(fl + out * 0.002, out, [(0, r_end), (hn + pr - 0.0007, r_end), (hn + pr, r_end - 0.0007),
                                             (hn + pr, r_b + 0.0004), (hn + pr - 0.0004, r_b)], "steel", 36, False, False))
        m.add(turned(top - out * 0.0004, -out, [(0, r_b), (0.012, r_b), (0.012, 0.0001)], "bore", 24, False, True))
    else:
        af, dep = PIV_HEX
        fl = face - out * (dep + 0.0025)
        # the recess's six walls down to a dark gap round the head
        m.add(lathe2(face + out * 0.0002, -out, [(0, 1.0, af), (dep + 0.0025, 1.0, af), (dep + 0.0025, 0.0001)], "frame_cast",
                     48, 0.0, False, True))
        haf, r_b = PIV_HEAD
        hh = dep + 0.0025 - 0.0010                                    # head's face 1 mm under the boss's face
        # flat-topped (piv2: the face inside the gap is even to the gap), edges broken 0.4 mm; darker than the frame
        # (grey 95..110 against the casting's 180..230)
        prof = [(0.0, 0.0001), (0.0, 1.0, haf), (hh - 0.0004, 1.0, haf), (hh, 1.0, haf - 0.0008), (hh, r_b + 0.0006),
                (hh - 0.0005, r_b)]
        m.add(lathe2(fl, out, prof, "steel_dark", 48, 0.0, cap0=True, cap1=False))
        m.add(turned(fl + out * (hh - 0.0005), -out, [(0, r_b), (0.012, r_b), (0.012, 0.0001)], "bore", 24, False, True))


def _cast_ribs(m, cast):
    """The casting's narrow ribs as smooth beads on its face: RIGHT, a '>' of two from each tab's boss into the leg
    (r_low3, r_mc: 15 mm long, about 3 mm wide); both sides, the rib down the pocket's upper edge under the pivot
    (l_pocket: lit, about 6 mm wide, from the boss's fillet to the footpeg pad)."""
    s = cast.s
    paths = [np.linspace(a, b, 12) for a, b in cast.chev]
    rb = np.linalg.norm(cast.rib - cast.piv, axis=1)
    rib = cast.rib.copy()
    rib[0] = cast.piv + (rib[0] - cast.piv) * (BOSS_R + 0.004) / rb[0]      # it starts at the boss's fillet
    paths.append(spline(np.column_stack([rib[:, 0], np.zeros(len(rib)), rib[:, 1]]), 20)[:, [0, 2]])
    for q, (w, h) in zip(paths, [(0.0028, 0.0010)] * len(cast.chev) + [(0.0060, 0.0015)]):
        y = cast.y_out(q)
        g = _bead(np.column_stack([q[:, 0], s * y, q[:, 1]]), [_face_normal(s, x) for x in q[:, 0]], w, h, pitch=0.0008,
                  sink=0.8, taper=0.003, mat="frame_cast", smooth=True)
        _uv_box(g, 0.08)
        m.add(g)


def _tab_bolts(m, cast):
    """RIGHT: the master cylinder's two M6 flange bolts on the tabs' bosses (r_mc: bright heads, flange 16 px = 12 mm,
    hexagon 8 mm), their ends in the cylinder's lugs behind."""
    for b in cast.tabs:
        y = float(cast.y_out(b[None, :])[0])
        m.add(hexbolt((b[0], -(y - 0.0003), b[1]), -Y3, 0.008, 0.0055, flange_d=0.012, flange_h=0.0012, mat="zinc", seg=36))


def _uv_box(m, scale):
    """UVs for the plate's isotropic grain: one side projection (x, z) over both faces and every slope, so the tangent
    frame is the same on neighbouring faces (a box projection switched axes on the pocket's and the pad's slopes and
    the normal map turned them into bright shards); the rim walls (normal square to y) take (x + z, y)."""
    V = np.asarray(m.V, float)
    for i, f in enumerate(m.F):
        Q = V[list(f)]
        n = np.cross(Q[1] - Q[0], Q[2] - Q[0])
        if abs(n[1]) > 0.25 * np.linalg.norm(n):
            m.uv[i] = [(float(q[0] / scale), float(q[2] / scale)) for q in Q]
        else:
            m.uv[i] = [(float((q[0] + q[2]) / scale), float(q[1] / scale)) for q in Q]


def _debug_outlines(s):
    view = "left" if s > 0 else "right"
    out = [(_frame_outline(), (0, 200, 255)), (_side_outline(s), (255, 230, 0)),
           (_cast_px(view, LOW_PX[view], s * Y_MID), (255, 0, 255))]
    t = _tongue(s)
    out.append((np.vstack([t, t[::-1]]), (0, 255, 0)))
    if s < 0:
        out.append((_cast_px("right", TAB_PX, -Y_MID), (255, 0, 255)))
    return out


def _union_outline(polys, res=0.0005, sigma=0.0010):
    """Outline of the union of polygons (x, z): rasterised every 0.5 mm, softened by SIGMA (so the joints between the
    traced pieces become cast fillets, not corners) and traced back at the half level."""
    from contourpy import contour_generator
    from scipy.ndimage import gaussian_filter
    A = np.vstack(polys)
    lo, hi = A.min(axis=0) - 0.01, A.max(axis=0) + 0.01
    xs, zs = np.arange(lo[0], hi[0], res), np.arange(lo[1], hi[1], res)
    X, Z = np.meshgrid(xs, zs)
    Q = np.stack([X.ravel(), Z.ravel()], axis=1)
    mask = np.zeros(len(Q), bool)
    for p in polys:
        mask |= inside(p, Q)
    field = gaussian_filter(mask.reshape(X.shape).astype(float), sigma / res)
    lines = contour_generator(x=xs, y=zs, z=field).lines(0.5)
    o = max(lines, key=len)
    if np.allclose(o[0], o[-1]):
        o = o[:-1]
    return o


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
    for s in (1, -1):
        # spar and the cast rear section: one plate over each side's own outline (round 3: _Cast), the U bead round
        # the spar's end, the cradle weld, the pivot's two ends
        cast = _Cast(s)
        m.add(cast.build("frame_spar", "frame_cast"))
        _frame_welds(m, cast)
        _pivot_ends(m, cast)
        _tab_bolts(m, cast)
        _cast_ribs(m, cast)
        # the spar under the shroud, up to the head (EST): 80 mm deep box, the visible part's top edge continued
        xs = np.array([0.74, 0.78, 0.82, 0.86, 0.90, 0.92, 0.94, 0.98, 1.03, 1.058])
        low = np.interp(xs, [0.86, 0.92, 1.058], [0.0, 0.004, 0.004])        # top 8 mm lower under the shroud deck (z 0.961)
        path = np.stack([xs, s * (np.array([_spar_y(x) for x in xs]) - T_SPAR / 2), _spar_top(xs) - 0.047 - low], axis=1)
        m.add(bar(path, 0.0245, np.linspace(0.080, 0.088, len(xs)) - 2 * low, "alu_frame"))
        # gusset between the spar's underside, the head and the down tube (EST)
        m.add(slab(np.array([(1.058, 0.940), (0.992, 0.906), (1.030, 0.850)]), s * 0.0245, 0.005, "alu_frame", r=0.002,
                   step=0.012, to=_xz))
        m.add(turned(PIVOT + s * 0.052 * Y3, s * Y3, [(0, 0.0085), (0.080, 0.0085)], "steel", 14))
        # footpeg bracket (now the casting's raised pad) with the black socket bolt (LEFT px (2228,1562), RIGHT px
        # (1770,1561)) and the hinge boss
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
    k = np.clip((s - S_WF) / (0.482 - S_WF), 0, 1)                   # round 4: the pivot casting steps in to 0.107 just
    #   ahead of the front weld (x 0.452 to 0.465). rr34 (chassis4/mc9): the arm's box ends in a front wall at u 1785
    #   (x 0.443); ahead of it, over the arm's height, only the brake's clevis and lever; REAR (mc8) puts the clevis's
    #   legs at y -0.112 and -0.130 and the push rod at -0.120, and RIGHT the master cylinder's skirt and boot down to z
    #   0.465 there: the casting's outer half is not there (round 2 kept it wide to x 0.499: 0.122 at x 0.48)
    arm = Y_ARM_O[0] + (Y_ARM_O[1] - Y_ARM_O[0]) * np.clip((s - S_WR) / (S_WF - S_WR), 0, 1)
    return np.where(s < S_WF, arm, Y_ARM_O[1] + (0.1070 - Y_ARM_O[1]) * (3 * k ** 2 - 2 * k ** 3))


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


def _weld(s_w, side, w=0.014, h=0.0020, pitch=0.0028, sink=0.6):
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
        hh = h * (0.84 + 0.16 * np.sqrt(ripple)) * (0.94 + 0.12 * jit)  # each ripple's crest, then its steep front
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
        sf = np.concatenate([np.linspace(S_WF, 0.484, 7), np.linspace(0.490, ARM_L - 0.030, 9),
                             np.linspace(ARM_L - 0.026, ARM_L - 0.0112, 6)])   # stops
        #                                                                  short of the pivot bolt (r 8.5): the boss carries it
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
    _hose_clip(m)                                                    # round 3: the brake hose's guide on the right arm
    return m


_HOSE_CACHE = []


def _wheels_hose():
    """Ring centres and radii of detail_wheels.py's brake hose (part rear_brake: the 'cable' tube, 12 points a ring),
    read off its built mesh so that the joint and the clip follow that module's run."""
    if not _HOSE_CACHE:
        import detail_wheels
        m = detail_wheels.PARTS["rear_brake"]()
        V = np.asarray(m.V, float)
        idx = sorted({i for f, mt in zip(m.F, m.M) if mt == "cable" for i in f})
        C = V[idx]
        R = C[:len(C) // 12 * 12].reshape(-1, 12, 3)
        cen = R.mean(axis=1)
        _HOSE_CACHE.append((cen, np.linalg.norm(R - cen[:, None, :], axis=2).mean(axis=1)))
    return _HOSE_CACHE[0]


# the hose's guide clip on the right arm's top (RIGHT 7x crop 1370..1450 x 1428..1480, r_clip; rr34 1595..1630 x
# 1370..1400): a black band 16 px (12 mm) along the hose over its top (u 1392..1408), on a ribbed base 41 px (31 mm)
# long and 12 px (9 mm) tall (u 1384..1425), three ribs along it. Cast with detail_wheels' own photo-to-model map
# (_cal_px): base x 0.281..0.312, band 0.287..0.299. In the photo the hose rides on the base 9 mm over the arm; the
# wheels module lays it 1.2 mm over the arm's top, so the base is two cheeks either side of the hose, the band
# arching over it between them
CLIP_X = (0.281, 0.312, 0.287, 0.299)


def _hose_clip(m):
    cen, rad = _wheels_hose()
    xc = (CLIP_X[0] + CLIP_X[1]) / 2
    k = int(np.argmin(np.abs(cen[:, 0] - xc)))
    t = cen[min(k + 1, len(cen) - 1)] - cen[max(k - 1, 0)]
    t /= np.linalg.norm(t)
    c = cen[k] + t * ((xc - cen[k][0]) / t[0])
    up = np.cross(t, Y3)                                             # square to the hose, in the arm's plane
    up = -up if up[2] < 0 else up
    up /= np.linalg.norm(up)
    hr = float(rad[k])
    base = c - up * (hr + 0.0012)                                    # the arm's top under the hose
    L = CLIP_X[1] - CLIP_X[0]
    Rm = np.column_stack([t, Y3, up])
    top = hr + 0.0012 + 0.0020                                       # cheeks: from the arm's top to 2 mm over the hose's
    #                                                                  axis (the band arches over them)
    for sg in (1, -1):
        yc = c[1] + sg * (hr + 0.0005 + 0.002)
        q = base + up * (top / 2 - 0.0003)
        m.add(box((q[0], yc, q[2]), (L, 0.004, top), "plastic_black", Rm))
        for h in (0.0020, 0.0040, 0.0060):                           # three ribs along the outer faces
            p = base + up * h
            m.add(box((p[0], yc + sg * 0.0022, p[2]), (L - 0.002, 0.0008, 0.0010), "plastic_black", Rm))
    # the band: an arch 1.4 mm thick round the hose's top, 12 mm along it, its feet on the cheeks
    bl = CLIP_X[3] - CLIP_X[2]
    bc = c + t * (((CLIP_X[2] + CLIP_X[3]) / 2 - c[0]) / t[0])
    ang = np.radians(np.linspace(-10, 190, 21))
    r0, r1 = hr + 0.0003, hr + 0.0017
    rings = []
    for s_ in (-bl / 2, -bl / 2 + 0.0006, bl / 2 - 0.0006, bl / 2):
        e = 0.0003 if abs(s_) == bl / 2 else 0.0
        outer = [bc + t * s_ + (Y3 * math.cos(a) + up * math.sin(a)) * (r1 - e) for a in ang]
        inner = [bc + t * s_ + (Y3 * math.cos(a) + up * math.sin(a)) * (r0 + e) for a in ang[::-1]]
        rings.append(np.array(outer + inner))
    g = grid(Mesh(), rings, "plastic_black", cap0=False, cap1=False)
    V = np.asarray(g.V)
    f = g.F[(len(ang) // 2)]                                        # a face on the outer arc's top: normal up
    if np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]]) @ up < 0:
        g.F = [q[::-1] for q in g.F]
    n = len(ang)
    for j, sg in ((0, -1), (len(rings) - 1, 1)):                    # the band's two ends: quads across the arch
        o = j * 2 * n
        for i in range(n - 1):
            q = (o + i, o + i + 1, o + 2 * n - 2 - i, o + 2 * n - 1 - i)
            if np.cross(V[q[1]] - V[q[0]], V[q[2]] - V[q[0]]) @ t * sg < 0:
                q = q[::-1]
            g.face(q, "plastic_black")
    m.add(g)


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
PHOTO_AXLE = {"left": (-0.0007, 0.3343), "right": (0.0002, 0.3377)}   # the photos' axle (see the ledger)


def _photo_px(view, pts, y):
    """Pixels of a part that hangs on the swingarm, cast on its plane y and carried from the photo's arm (axle to
    pivot) onto the model's: (x, z) points."""
    a = np.array(PHOTO_AXLE[view])
    pv = np.array([PIVOT[0], PIVOT[2]])
    e = (pv - a) / np.linalg.norm(pv - a)
    n = np.array([-e[1], e[0]])
    k = ARM_L / float(np.linalg.norm(pv - a))
    out = []
    for u, v in pts:
        q = _px(view, u, v, "y", y)
        d = np.array([q[0], q[2]]) - a
        out.append(_fr(ARM_A, float(d @ e) * k, float(d @ n)))
    return np.array(out)


# chain guide (LEFT px, 7x crop 2730..2920 x 1640..1780; lr34 for the depth order): outer plate, windows, bolts
GUIDE_Y = (0.1050, 0.1080)               # alu plate: inner and outer face (EST 3 mm, outside the chain's 0.0985)
GUIDE_PLATE = [(2743.6, 1648.6), (2747.5, 1645.0), (2753.0, 1644.0), (2760.0, 1646.5), (2777.0, 1653.0), (2783.0, 1656.0),
               (2787.0, 1664.3), (2797.0, 1674.3), (2804.3, 1678.6), (2830.0, 1680.0), (2838.0, 1677.5), (2845.0, 1677.0),
               (2851.0, 1679.0), (2855.7, 1682.9), (2872.9, 1704.3), (2894.3, 1722.9), (2907.0, 1728.6), (2912.5, 1734.5),
               (2912.0, 1747.0), (2905.7, 1755.7), (2887.0, 1758.6), (2844.0, 1759.3), (2830.0, 1754.3), (2798.6, 1742.9),
               (2772.9, 1734.3), (2760.0, 1727.1), (2754.5, 1723.5), (2752.9, 1715.0), (2751.4, 1664.3), (2747.0, 1657.0)]
GUIDE_WIN = [(2770.0, 1682.9), (2779.3, 1682.9), (2792.0, 1694.0), (2805.0, 1707.1), (2806.4, 1728.6), (2802.0, 1733.0),
             (2797.0, 1733.6), (2772.9, 1720.0), (2770.0, 1712.0)]
GUIDE_SLOTW = [(2822.9, 1717.1), (2832.9, 1715.7), (2894.3, 1737.1), (2897.0, 1742.9), (2894.0, 1750.0), (2888.6, 1754.3),
               (2838.6, 1735.7), (2822.9, 1725.7)]
GUIDE_BOLTS = [(2752.1, 1649.3), (2777.1, 1660.0), (2845.0, 1685.0)]   # flange bolts M6 (heads: bright rings 12 mm)
GUIDE_TAB = [(2736.0, 1600.0), (2786.0, 1612.0), (2788.0, 1661.0), (2760.0, 1652.0), (2739.0, 1644.0)]   # front tab
GUIDE_STRUT = [(2846.0, 1624.0), (2860.0, 1628.0), (2852.0, 1683.0), (2840.0, 1683.0)]                 # rear strut


def _clip_below(poly, z):
    """The part of a closed polygon (x, z) under the line Z (Sutherland-Hodgman)."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        if p[1] <= z:
            out.append(p)
        if (p[1] - z) * (q[1] - z) < 0:
            t = (z - p[1]) / (q[1] - p[1])
            out.append(p + t * (q - p))
    return np.array(out)


def chain_guide():
    """Stock chain guide under the left arm (fiche K95CF3200: plate 11, block 10, bolts 18/19, nuts 23): the alu
    plate with its front window and long rear slot, bolted by three M6 flange bolts to two tabs welded under the arm
    (a wide front tab and a narrow rear strut); behind it the black block: an inner wall and two wear rails round the
    lower run (GUIDE_SLOT keeps the model's chain in it), its nose showing ahead of the plate (LEFT u 2743..2751)."""
    m = Mesh()
    yo, yi = GUIDE_Y[1], GUIDE_Y[0]
    plate = _clean(_photo_px("left", GUIDE_PLATE, yo), 0.0015, 0.0012)
    win = _clean(_photo_px("left", GUIDE_WIN, yo), 0.0012, 0.001)
    slw = _clean(_photo_px("left", GUIDE_SLOTW, yo), 0.0012, 0.001)
    m.add(slab2(plate, (yo + yi) / 2, yo - yi, "alu_satin", r=0.0012, step=0.005, holes=[win, slw], to=_xz, r_hole=0.0009))
    # tabs welded under the arm, 4 mm, inboard of the plate; their tops run into the arm's underside
    for pts in (GUIDE_TAB, GUIDE_STRUT):
        o = _photo_px("left", pts, yo)
        top = o[:, 1] > o[:, 1].mean()
        o[top, 1] = [float(_arm_bot(x)) - 0.0003 for x in o[top, 0]]        # welded on: 0.3 mm short of the face
        m.add(slab2(o, yi - 0.0021, 0.0040, "alu_satin", r=0.0012, step=0.005, to=_xz))
    for u, v in GUIDE_BOLTS:
        c = _photo_px("left", [(u, v)], yo)[0]
        m.add(hexbolt((c[0], yo + 0.0001, c[1]), Y3, 0.008, 0.0055, flange_d=0.012, flange_h=0.0012, mat="zinc", seg=36))
        m.add(hexnut((c[0], yi - 0.0042, c[1]), -Y3, 0.010, 0.005, 0.0031, "zinc", seg=24))
        m.add(thread((c[0], yi - 0.0092, c[1]), -Y3, 0.003, 0.001, 0.0012, "zinc", seg=16, per=5))   # 1.2 mm past the nut
    # black block: inner wall (the plate's lower part), wear rails above and below the run, the nose ahead
    x0, z0, slope, half = GUIDE_SLOT
    wall = _clip_below(plate, 0.300)
    m.add(slab(wall, CHAIN_Y - 0.0185, 0.004, "plastic_black", r=0.001, step=0.006, to=_xz))       # outside the slot band
    a = math.atan(slope)
    e, nrm = np.array([math.cos(a), 0.0, math.sin(a)]), np.array([-math.sin(a), 0.0, math.cos(a)])
    for q in (-1, 1):
        c = np.array([0.158, (CHAIN_Y - 0.0165 + yi - 0.0006) / 2, z0 + slope * (0.158 - x0)]) + nrm * q * (half * math.cos(a) + 0.004)
        w1 = (0.1835 - c[0]) / e[0]                                     # front ends at the nose (LEFT u 2743..2751)
        m.add(bar([c + e * w for w in np.linspace(-0.027, w1, 10)], yi - 0.0006 - CHAIN_Y + 0.0165, 0.008, "plastic_black"))
    nose = _photo_px("left", [(2742.5, 1667.0), (2754.0, 1665.0), (2756.0, 1727.0), (2746.0, 1729.0)], yo)   # LEFT dark band
    y0n = CHAIN_Y + 0.0117                                          # the block's outer wall: 1.2 mm outside the chain
    m.add(slab(nose, (y0n + yi - 0.0002) / 2, yi - 0.0002 - y0n, "plastic_black", r=0.0012, step=0.005, to=_xz))
    return m


# ---------------------------------------------------------------- Pro-Link
def _pivot_bolt(c, half_l, half_r, af_head=0.017, af_nut=0.022, r_t=0.007, washer=0.0135, phase=math.pi / 6):
    """Linkage bolt across the bike at C: flange head on the left at |y| HALF_L, washer, U-nut and two threads of
    the end on the right at HALF_R (Dirt Rider 09: big nuts with bright washer faces on the right side)."""
    c = np.asarray(c, float)
    m = Mesh()
    m.add(hexbolt((c[0], half_l + 0.0002, c[2]), Y3, af_head, 0.0095, flange_d=af_head * 1.45, flange_h=0.0018, mat="zinc",
                  seg=36))
    m.add(turned((c[0], -half_r - 0.0002, c[2]), -Y3, [(0, r_t + 0.0002), (0, washer), (0.0025, washer), (0.0025, r_t + 0.0002),
                                                        (0, r_t + 0.0002)], "steel", 32, False, False))       # washer
    m.add(hexnut((c[0], -half_r - 0.0027, c[2]), -Y3, af_nut, 0.011, r_t + 0.0001, "zinc", phase=phase, seg=36))
    m.add(thread((c[0], -half_r - 0.0137, c[2]), -Y3, r_t, 0.0015, 0.004, "zinc", seg=24, per=6))
    return m


def _dogbone(p0, p1, y, mat="alu_forged"):
    """Connecting rod side: two round eyes and an I-section web between them (Dirt Rider 09: flanges along both
    edges, the web recessed between them)."""
    m = Mesh()
    a, b = np.array([p0[0], p0[2]]), np.array([p1[0], p1[2]])
    e = (b - a) / np.linalg.norm(b - a)
    n = np.array([-e[1], e[0]])
    sg = 1 if y > 0 else -1
    for c in (a, b):
        m.add(hollow((c[0], y - 0.0035, c[1]), Y3, 0.0158, 0.0072, 0.007, mat, 36))
    web = np.array([a + e * 0.012 + n * 0.0065, b - e * 0.012 + n * 0.0065, b - e * 0.012 - n * 0.0065, a + e * 0.012 - n * 0.0065])
    m.add(slab(web, y, 0.0048, mat, r=0.0008, step=0.004, to=_xz))
    for q in (1, -1):                                             # flanges (rod 18 mm deep: DR 09, 0.55 of the eye)
        path = [(c[0], y, c[1]) for c in (a + e * 0.010 + n * q * 0.0075, b - e * 0.010 + n * q * 0.0075)]
        path = [np.array(path[0]) + (np.array(path[1]) - np.array(path[0])) * t for t in np.linspace(0, 1, 6)]
        m.add(bar(path, 0.0092, 0.0030, mat))
    return m


def linkage():
    """Cushion arm (on the swingarm at T, shock clevis at A, link at B) and the connecting rods to the frame at F:
    link length B-F 144 mm, T-B 49 mm, T-A 78 mm (LEFT and RIGHT zooms, both sides agree within 6 mm). Dirt Rider 09
    (right side, close): each rod a forged dog-bone with an I-section, the shock's clevis bolt just under it; the
    arm a cast triangle with a recessed face and rims; M14 bolts, U-nuts with washers on the right."""
    m = Mesh()
    T, A, B, F = LINK_T, SHOCK_A, LINK_B, F_LINK
    arm = hull([(T[0], T[2], 0.020), (A[0], A[2], 0.016), (B[0], B[2], 0.017)])
    c = (T + A + B) / 3
    m.add(slab(arm, 0.0, 0.024, "alu_cast", r=0.003, step=0.006, holes=[circle(0.0075, 16, c[0], c[2])], to=_xz))
    m.add(hollow(T - 0.031 * Y3, Y3, 0.020, 0.008, 0.062, "alu_cast", 32))
    m.add(hollow(B - 0.0245 * Y3, Y3, 0.017, 0.007, 0.049, "alu_cast", 28))
    for s in (1, -1):
        m.add(_dogbone(B, F, s * 0.0285))
    m.add(hollow(F - 0.036 * Y3, Y3, 0.015, 0.0072, 0.072, "alu_cast", 28))
    k = (0.497 - B[0]) / (F[0] - B[0])                         # bridge of the rods, ahead of the shock's clevis
    zb = B[2] + k * (F[2] - B[2])
    m.add(bar([(0.497, -0.027, zb), (0.497, 0.0, zb), (0.497, 0.027, zb)], 0.016, 0.018, "alu_forged"))
    m.add(_pivot_bolt(T, 0.042, 0.042))
    m.add(_pivot_bolt(B, 0.0322, 0.0322))
    m.add(_pivot_bolt(F, 0.036 + 0.0075, 0.036 + 0.0075, af_head=0.014, af_nut=0.017, r_t=0.005, washer=0.0105))   # M10:
    #                                                                     clear of the frame's lower cross member
    return m


# ---------------------------------------------------------------- shock
RES_CAP = (0.546, 0.730)                  # RIGHT px (1727, 1096): the reservoir's end cap seen through the frame,
#                                           cast on y -0.075 (Dirt Rider 07-08: a round cap with a bolt in its middle)


def shock():
    """Showa shock on the centre line (fiche K95CF3300), hidden behind the pivot plates and the airbox panel in both
    profiles: lower clevis bolt measured (SHOCK_A), the reservoir's end cap seen through the frame (RES_CAP), the
    bottom cup and clevis in Dirt Rider 09; the rest from the real part's sizes (EST: 481 mm eye to eye, 50 mm body,
    spring 8.25 coils of 12 mm wire, closed and ground ends)."""
    m = Mesh()
    U, A = SHOCK_U, SHOCK_A
    L = float(np.linalg.norm(A - U))
    d = (A - U) / L
    nr = np.array([d[2], 0.0, -d[0]])                          # square to the axis, pointing back and up
    m.add(hollow(U - 0.0155 * Y3, Y3, 0.018, 0.006, 0.031, "alu_cast", 28))
    for s in (1, -1):                                          # the eye's seals
        m.add(hollow(U + s * 0.0152 * Y3, s * Y3, 0.0105, 0.0062, 0.0012, "rubber_black", 20))
    m.add(turned(U, d, [(0.018, 0.015), (0.026, 0.027), (0.036, 0.0275), (0.052, 0.028), (0.068, 0.0285), (0.088, 0.029),
                        (0.092, 0.0265)], "alu_cast", 32))
    m.add(turned(U, d, [(0.092, 0.0265), (0.270, 0.0265), (0.272, 0.012)], "shock_body", 32))
    m.add(thread(U + d * 0.095, d, 0.0275, 0.0015, 0.020, "shock_body", seg=40, per=4))          # the rings' thread
    # lock ring (7) and preload ring (6): castellated, eight notches each
    for s0, s1, ro in ((0.1150, 0.1235, 0.0365), (0.1255, 0.137, 0.0405)):
        ang = np.linspace(0, 2 * math.pi, 64, endpoint=False)
        notch = (np.abs(((ang * 8 / (2 * math.pi)) % 1.0) - 0.5) < 0.12)
        R = frame_z(d)
        cs = np.stack([np.cos(ang), np.sin(ang), np.zeros(64)], axis=1) @ R.T
        rings = []
        for s, rr in ((s0, 0.0277), (s0, ro - 0.0006), (s0 + 0.0006, ro), (s1 - 0.0006, ro), (s1, ro - 0.0006), (s1, 0.0277)):
            rad = np.where(notch & (rr > 0.03), rr - 0.0035, rr)
            rings.append(U + d * s + cs * rad[:, None])
        rings.append(rings[0])
        m.add(_outward(grid(Mesh(), rings, "alu_machined")))
    # spring (fiche 5): closed AND ground ends (round 4): the end turns' wire centres on the seats' faces (the preload
    # ring's at 0.137, the lower seat's at 0.371) and ground flat there, the cut tapering over half a turn
    sp = coil(U + d * 0.1373, U + d * 0.3707, 0.0355, 0.006, 8.25, "shock_spring", seg=12, dead=1.0)
    V = np.asarray(sp.V)
    t = (V - U) @ d
    V = V + np.outer(np.clip(t, 0.1372, 0.3708) - t, d)
    sp.V = list(map(tuple, V))
    m.add(sp)
    m.add(turned(U, d, [(0.268, 0.009), (0.398, 0.009)], "chrome", 16))
    m.add(turned(U, d, [(0.336, 0.009), (0.340, 0.021), (0.366, 0.024), (0.372, 0.022)], "rubber_black", 20))         # bump stop
    # lower seat (25) with its stopper ring (24), the bottom cup (4): Dirt Rider 09, a stepped bright cup with grooves
    m.add(turned(U, d, [(0.371, 0.012), (0.371, 0.0405), (0.3725, 0.0415), (0.3765, 0.0415), (0.378, 0.0395), (0.379, 0.0265),
                        (0.385, 0.0262), (0.3855, 0.0248), (0.3875, 0.0248), (0.388, 0.0262), (0.400, 0.0262),
                        (0.4005, 0.0248), (0.4025, 0.0248), (0.403, 0.0262), (0.408, 0.026), (0.412, 0.022), (0.445, 0.019)],
                 "alu_machined", 40))
    m.add(turned(U, d, [(0.3795, 0.0262), (0.3795, 0.0282), (0.3815, 0.0282), (0.3815, 0.0262)], "steel", 32, False, False))
    for s in (1, -1):                                          # clevis ears astride the cushion arm
        p = U + d * (L - 0.046)
        m.add(slab(hull([(A[0], A[2], 0.016), (p[0], p[2], 0.017)]), s * 0.0168, 0.0085, "alu_machined", r=0.0015, step=0.005,
                   to=_xz))
    m.add(_pivot_bolt(A, 0.021, 0.021, af_head=0.014, af_nut=0.014, r_t=0.0050, washer=0.0095, phase=0.0))   # under the rods
    # rebound adjuster on the clevis (a slotted screw), its S-arrow marking cut in the ear's face (Dirt Rider 09)
    q = U + d * 0.428 - nr * 0.0185
    m.add(turned(q, -nr, [(0, 0.0001), (0, 0.0055), (0.0025, 0.0055), (0.0032, 0.0048), (0.0032, 0.0001)], "steel", 20, True, True))
    m.add(box(q - nr * 0.0033, (0.0095, 0.0010, 0.0012), "bore", R=np.column_stack([np.cross(Y3, nr), Y3, -nr])))
    # round 4: Dirt Rider 09 (cu3_s: its crop 560..1000 x 280..560) shows the rebound scale stamped in the right ear's
    # flat face just under the cup: "S" at the rear, 7 mm tall (25 px against the ear's 110 px, 33 mm), a curved
    # double-headed arrow ahead of it a little higher, and an index line at the front; upright toward the cup;
    # grooves 0.7 mm wide, black, 0.1 mm proud of the face. (In the studio pose the connecting rods pass over them.)
    face = U + d * 0.4565 + np.array([0.0, -0.02080, 0.0])
    to_face = lambda px, py: face - nr * px - d * py                # noqa: E731  (px forward, py up the shock)
    hs, ws = 0.0070, 0.0046
    s_up = [(-0.0060 + ws / 2 * math.cos(q), hs / 4 + hs / 4 * math.sin(q)) for q in np.radians(np.linspace(25, 270, 14))]
    s_lo = [(-0.0060 + ws / 2 * math.cos(q), -hs / 4 + hs / 4 * math.sin(q)) for q in np.radians(np.linspace(90, -155, 14))]
    arc = [(0.0020 + 0.0042 * math.cos(q), 0.0004 + 0.0020 * math.sin(q)) for q in np.radians(np.linspace(20, 160, 14))]
    strokes = [s_up + s_lo[1:], arc, [(0.0085, 0.0030), (0.0085, -0.0035)]]
    for e0, e1 in ((arc[0], arc[1]), (arc[-1], arc[-2])):          # the arrow's heads
        u = np.subtract(e0, e1) / np.linalg.norm(np.subtract(e0, e1))
        w = np.array([-u[1], u[0]])
        strokes.append([tuple(np.add(e0, -0.0015 * u + 0.0011 * w)), e0, tuple(np.add(e0, -0.0015 * u - 0.0011 * w))])
    for stroke in strokes:
        m.add(tube([to_face(px, py) for px, py in stroke], 0.00035, 6, "bore"))
    # reservoir: across the bike to the right of the head, its end cap and the two-stage compression adjuster
    rc = np.array([RES_CAP[0], 0.0, RES_CAP[1]])
    m.add(turned(rc + 0.004 * Y3, -Y3, [(0.0, 0.0001), (0.0, 0.015), (0.004, 0.020), (0.070, 0.020), (0.0705, 0.0185),
                                        (0.071, 0.0001)], "shock_body", 32, True, True))
    m.add(bar([U + d * 0.060, (U + d * 0.060 + rc) / 2 - 0.006 * Y3, rc - 0.010 * Y3], 0.030, 0.030, "alu_cast"))
    m.add(turned(rc - 0.0670 * Y3, -Y3, [(0.0, 0.0001), (0.0, 0.0178), (0.0035, 0.0178), (0.0045, 0.0168), (0.0045, 0.0001)],
                 "alu_machined", 36, True, True))                                      # end cap
    m.add(hollow(rc - 0.0662 * Y3, -Y3, 0.0182, 0.0168, 0.0008, "steel", 36))         # circlip (22)
    m.add(hexbolt(rc - 0.0712 * Y3, -Y3, 0.014, 0.006, mat="alu_machined", seg=36))   # high-speed adjuster, 14 mm
    m.add(turned(rc - 0.0772 * Y3, -Y3, [(0.0, 0.0001), (0.0, 0.0035), (0.0015, 0.0035), (0.0015, 0.0001)], "steel", 16, True, True))
    m.add(box(rc - 0.0786 * Y3, (0.0065, 0.0006, 0.0008), "bore"))                    # low-speed screw's slot
    m.add(_pivot_bolt(U, 0.023, 0.023, af_head=0.014, af_nut=0.019, r_t=0.0055))
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
# muffler (round 2): a straight can of flat facets. RIGHT (OUT2 'muffler', cast at y -0.14): the lower edge is a
# straight line from x 0.029 to 0.301 (z 0.775 to 0.640, within 4 mm of the old table); the top is seen only at the
# rear (LEFT row 878 at col 2950: z 0.893 at x 0..0.024; REAR: the cap's top at 0.901), 109 to 117 mm over that line:
# the can keeps one height to the nose (the old pass bent its top down under the side panel's skin: that bend was the
# kink in the right view; the panel covers the can there, as in the photo). Plan: TOP cols 2640..2840: outer flank -0.194 at x 0.05, -0.180 at x 0.175; REAR: inner
# flank -0.082 (straight lines). The old pass's section table wandered (top line slopes -0.32, -0.67, -0.30, -0.67,
# -1.14), a 20 mm dent was pressed into the inner top for the panel and the section morphed into a circle over the
# can's front 11 cm: those were the lumps.
MUF_LOW = (0.029, 0.775, -0.496)            # z_low = a + b (x - x0)
MUF_H = 0.108                               # LEFT row 878 and REAR (0.901) disagree by 11 mm: the top splits it
MUF_TAPER = 0.18                            # the can's height falls 18 mm per 100 mm, straight, to clear the side panel
#                                             over the nose (audit: 20.8 mm into it at x 0.26..0.32 without; hidden part)
MUF_FACE = -0.008                           # the cap's rear face (at z 0.840, before its lean)
MUF_ROLL = 0.018                            # the cap's pressed edge: an 18 mm roll into its rear face (rr34, REAR)
MUF_NOSE = (0.345, 0.371, 0.0215)          # round 3: the can's lines run to the seam's top (x 0.345); the nose ends at
#                                             the inlet's weld ring (RIGHT u 1490) round the 41 mm pipe (r 20.5 + 1)
MUF_X = list(np.arange(0.012, 0.300, 0.006)) + [0.300]
# end cap seen from behind, an octagon of flat facets (REAR, 2x crop 2100..2330 x 680..920, cast on x 0): top z 0.901
# from y -0.1015 to -0.1658; outer chamfer to (-0.1916, 0.8665); outer side down to z 0.799; lower chamfer to
# (-0.1778, 0.769); bottom z 0.765 to y -0.115; inner corner (-0.095, 0.778), (-0.0868, 0.792); inner side to z 0.880.
# As (a outward, b up) in half-widths about (y -0.139, z 0.833); corners rounded about 5 mm (smoothed; round 3 tried
# 3 samples instead of 6 for crisper corners: the outer top corner then stood 12 mm above LEFT's row 878, so 6 stays)
_SEC = np.array([(-1.0, 0.0), (-1.0, -0.60), (-0.84, -0.81), (-0.46, -1.0), (0.70, -1.0), (1.0, -0.50), (1.0, 0.49),
                 (0.505, 1.0), (-0.718, 1.0), (-1.0, 0.69)])[::-1]
MUF_SEC = smooth_poly(resample(_SEC, 0.05), 6)
OUT_AXIS = np.array([-1.0, 0.0, 0.0])        # square to the cap's upright face (round 3, _cap_x)
OUTLET = np.array([-0.012, -0.138, 0.845])                    # REAR: dark disc centred on px (2205, 787)
MUF_AXIS = np.array([-0.927, 0.0, 0.375])                     # rearward along the can (22 deg: between its two edges)
BRUSH_TILE = 0.08                                             # metres per repeat of the brushed map


def _smin(a, b, k=0.008):
    return -k * math.log(math.exp(-a / k) + math.exp(-b / k))


def _muf(x):
    """z of the can's lower and upper edges, its plan centre and half width at station x (straight lines)."""
    zl = MUF_LOW[1] + MUF_LOW[2] * (x - MUF_LOW[0])
    zt = zl + MUF_H - MUF_TAPER * max(x - 0.013, 0.0)
    yc = -0.138 + (-0.127 + 0.138) * (x + 0.008) / 0.243
    hw = 0.056 + (0.046 - 0.056) * (x + 0.004) / 0.239
    return zl, zt, yc, hw


def _muf_ring(x, grow=0.0, inset=0.0, morph=0.0):
    """Section of the can at station x: the octagon on its two edge lines, grown by GROW (m, outward, the cap and the
    nose stand proud of the can) or rolled in by INSET (the cap's pressed edge). MORPH (0..1): the nose's turn from
    the octagon into the round inlet on the header (round 3: the nose is built per vertex from its slanted seam, the
    cap's face is shaped by _cap_x, so the station itself is square to the can)."""
    zl, zt, yc, hw = _muf(min(max(x, MUF_FACE), MUF_NOSE[0]))
    hh = (zt - zl) / 2
    zm = (zl + zt) / 2
    S = MUF_SEC.copy()
    if morph > 0:
        k = 3 * morph ** 2 - 2 * morph ** 3
        ang = np.arctan2(S[:, 1], S[:, 0])
        S = (1 - k) * S + k * np.stack([np.cos(ang), np.sin(ang)], axis=1)
        hw = (1 - k) * hw + k * MUF_NOSE[2]
        hh = (1 - k) * hh + k * MUF_NOSE[2]
        yc = (1 - k) * yc + k * MUF_INLET[0]
        zm = (1 - k) * zm + k * MUF_INLET[1]
    hw2, hh2 = hw + grow - inset, hh + grow - inset
    z = zm + S[:, 1] * hh2
    return np.stack([np.full(len(S), x), yc - S[:, 0] * hw2, z], axis=1)


# the cap's side profile (RIGHT, the rear-most pixel of each row, cast on y -0.14; scratch r_cap): the face is
# upright at x -0.0072 from z 0.866 to 0.838 (u 983..984), then a knee of about 50 mm radius (x -0.0047 at z 0.820,
# -0.0027 at 0.811, 0.0023 at 0.802) into one straight facet at 45 deg (0.0111, 0.793), (0.0199, 0.784), (0.0309,
# 0.775), (0.0353, 0.770) down to the can's underside (0.0465, 0.765). The round-2 cap leaned 14.5 deg on one line
# (from the cap's seam to its face), 13 mm too far back at the top and with a crease where the roll met the bottom
CAP_X = -0.0072
CAP_KNEE = (0.0428, 0.8318, 0.050)          # the knee's circle: centre x, z and radius, tangent to the face and facet
_KT = (CAP_KNEE[0] - CAP_KNEE[2] * math.sqrt(0.5), CAP_KNEE[1] - CAP_KNEE[2] * math.sqrt(0.5))   # (0.0074, 0.7964)


def _cap_x(z):
    """x of the cap's rear surface at height z (before the roll round its edge)."""
    if z >= CAP_KNEE[1]:
        return CAP_X
    if z >= _KT[1]:
        return CAP_KNEE[0] - math.sqrt(max(CAP_KNEE[2] ** 2 - (z - CAP_KNEE[1]) ** 2, 0.0))
    return _KT[0] + (_KT[1] - z)


# the nose (RIGHT, 3x crop 1340..1580 x 1100..1280, r_nose; cast on the can's outer flank, y -0.17): the can's front
# edge (its two rivets just behind it) runs slanted from (0.3176, 0.6373) at the bottom to (0.3411, 0.6875) where the
# side panel covers it; the pressed nose cone, a darker satin steel, from it to the inlet's weld ring at u 1490 (x
# 0.372); its lower edge almost level (z 0.637 to 0.641), turning up into the pipe at the end. The round-2 seam was
# square to the can at x 0.296, 2 to 4.5 cm behind the photo's
NOSE_SEAM = (0.3176, 0.6373, 0.468)         # x, z at the bottom and dx/dz up the seam (25 deg)
MUF_INLET = (-0.0917, 0.6441)               # the header's axis (y, z) at the nose's end (HEADER, between its last two points)


def _nose_x(z):
    return NOSE_SEAM[0] + NOSE_SEAM[2] * (z - NOSE_SEAM[1])


def _uv_grid(mesh, rings, base=0):
    """UVs for a closed-ring grid built by geom.grid (faces in its order from BASE): u along the can (x), v round the
    section (arc length), both in BRUSH_TILE units, so the brushed lines run along the can."""
    R = [np.asarray(r, float) for r in rings]
    n = len(R[0])
    for k in range(len(R) - 1):
        arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([R[k], R[k][:1]]), axis=0), axis=1))])
        for i in range(n):
            j = i + 1
            u0, u1 = R[k][i, 0] / BRUSH_TILE, R[k + 1][i, 0] / BRUSH_TILE
            u0j, u1j = R[k][j % n, 0] / BRUSH_TILE, R[k + 1][j % n, 0] / BRUSH_TILE
            v0, v1 = arc[i] / BRUSH_TILE, arc[j] / BRUSH_TILE
            mesh.uv[base + k * n + i] = [(u0, v0), (u0j, v1), (u1j, v1), (u1, v0)]


def _can(m):
    """The can, its pressed rear cap (a separate part over the can's end: its front edge on a slanted plane, a 0.6
    mm step to the can), the nose cone with its own step; brushed UVs on all three."""
    n = len(MUF_SEC)
    # the cap's front edge: a plane leaning back at the bottom through the side rivets (set by exhaust()), 6 mm ahead
    a0, b = _CAP_PLANE
    seam_x = lambda z: a0 + b * z + 0.006
    # can: from under the cap to under the nose
    zc = np.array([_muf_ring(0.03)[j, 2] for j in range(n)])
    x0 = max(min(seam_x(float(z)) for z in zc) - 0.006, _KT[0] + 0.004)
    zf = _muf_ring(MUF_NOSE[0])[:, 2]
    xn = np.array([_nose_x(z) for z in zf])                       # the can's front edge, slanted (RIGHT, r_nose)
    xs = [x0] + [x for x in MUF_X if x0 + 0.003 < x < xn.min() - 0.004]
    rings = [_muf_ring(x) for x in xs]
    rings.append(np.array([_muf_ring(xn[j])[j] for j in range(n)]))
    g = grid(Mesh(), rings, "muffler", cap0=True, cap1=True)
    _uv_grid(g, rings)
    m.add(g)
    # cap (round 3): its rear surface follows _cap_x (upright face, 50 mm knee, 45 deg lower facet); the roll round
    # its edge is 18 mm where the cap is long enough and shrinks to 2 mm at the bottom, where the photo's seam meets
    # the lower facet; then the cap's side out to its seam (per vertex) and the 0.6 mm step down to the can
    full = _muf_ring(MUF_FACE, grow=0.0006)
    roll = np.clip([seam_x(float(p[2])) - _cap_x(float(p[2])) - 0.004 for p in full], 0.002, MUF_ROLL)

    def ring_at(inset_of, x_of):
        """Per vertex: the section taken at the vertex's own station (the can's top and bottom lines slope, so the
        cap's sides follow them), its x from the profile; two passes settle x and z together."""
        out = []
        for j in range(n):
            x = MUF_FACE
            for _ in range(3):
                p = _muf_ring(x, grow=0.0006, inset=float(inset_of[j]))[j]
                x = x_of(j, float(p[2]))
            out.append((x, p[1], p[2]))
        return np.array(out)
    B = ring_at(roll, lambda j, z: _cap_x(z))
    c0 = B.mean(axis=0)
    rings = []
    for q in np.linspace(0.08, 1.0, 13)[:-1]:                     # the face: fine enough to carry the knee's curve
        R_ = c0 + (B - c0) * q
        R_[:, 0] = [_cap_x(float(z)) for z in R_[:, 2]]
        rings.append(R_)
    for a in np.radians(np.linspace(0, 90, 7)):
        rings.append(ring_at(roll * (1 - math.sin(a)), lambda j, z, a=a: _cap_x(z) + roll[j] * (1 - math.cos(a))))
    xr = rings[-1][:, 0].copy()
    tail = []
    for t in np.linspace(0, 1, 8)[1:]:
        ring = []
        for j in range(n):
            xj = seam_x(float(_muf_ring(0.03)[j, 2]))
            xx = xr[j] + t * max(xj - xr[j], 0.0005)
            ring.append(_muf_ring(xx, grow=0.0006)[j])
        tail.append(np.array(ring))
    last = tail[-1]
    step = np.array([_muf_ring(p[0])[j] for j, p in enumerate(last)])
    cap_rings = rings + tail + [last + (step - last) * 0.6, step]
    g = grid(Mesh(), cap_rings, "muffler", cap0=True, cap1=False)
    _uv_grid(g, cap_rings, 0)
    nf = 12                                                       # the face: brushed across (REAR: level lines on the
    for f in range(nf * n):                                       # cap's face), a plane map in y and z; the roll keeps
        #                                                           the can's map (the plane map streaked it sideways)
        g.uv[f] = [(-g.V[i][1] / BRUSH_TILE, g.V[i][2] / BRUSH_TILE) for i in g.F[f]]
    for f in range((len(cap_rings) - 1) * n, len(g.F)):           # the centre fan
        g.uv[f] = [(-g.V[i][1] / BRUSH_TILE, g.V[i][2] / BRUSH_TILE) for i in g.F[f]]
    m.add(_outward(g))
    # nose (round 3): a separate pressed cone of satin steel from the can's slanted front edge (0.6 mm under it, the
    # can's edge laps over it) to the inlet's ring round the header, its section turning from the octagon into the
    # pipe's circle with a smoothstep over its front two thirds (r_nose: the lower edge runs level first, then the
    # inlet end meets the pipe tangentially: the photo's rounded front corner)
    nose = []
    for t in np.linspace(0, 1, 13):
        ring = []
        for j in range(n):
            xx = xn[j] - 0.004 + t * (MUF_NOSE[1] - xn[j] + 0.004)
            ring.append(_muf_ring(xx, grow=-0.0006, morph=float(np.clip((t - 0.35) / 0.65, 0, 1)))[j])
        nose.append(np.array(ring))
    g = grid(Mesh(), nose, "header_steel", cap0=False, cap1=True)
    _uv_grid(g, nose, 0)
    m.add(_outward(g))


_CAP_PLANE = (0.0, 0.0)


def brushed_map(path, size=1024, seed=7):
    """Tangent-space normal map of a brushed finish: fine lines along u (the can's length), each a few cm long, of
    random depth; 0.08 m per repeat, so a pixel is 0.08 mm. OpenGL convention."""
    from PIL import Image
    from scipy.ndimage import gaussian_filter, zoom
    rng = np.random.default_rng(seed)
    coarse = rng.standard_normal((size, 48))                       # rows: v; columns: u (stretched 21x along u)
    h = zoom(coarse, (1, size / 48), order=1, mode="grid-wrap")[:, :size]
    scr = rng.random((size,)) < 0.015                              # a few deeper scratches
    h -= 2.5 * scr[:, None] * zoom(rng.random((1, 6)), (1, size / 6), order=1, mode="grid-wrap")[:, :size]
    h = gaussian_filter(h, (0.6, 12.0), mode="wrap")
    dv = np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)
    du = np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)
    k = 0.16                # round 3: was 0.06, a 2 deg spread of the normals across the lines: the brushing did not
    #                         read in a close-up at 30 cm; now about 6 deg (the photos' streaks are clear at 2x)
    nrm = np.stack([-du * k * 0.3, dv * k, np.ones_like(h)], axis=-1)    # image rows run down: +v is up the image
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    Image.fromarray(np.clip((nrm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)).save(path)


def cast_map(path, size=1024, seed=11):
    """Tangent-space normal map of the frame's cast surface: the fine grain of a shot-blasted sand casting (equalised
    crops of RIGHT and LEFT: an even speckle about 0.3 mm across, no direction) over a faint orange peel 1 to 2 mm
    across; 0.08 m per repeat (a pixel is 0.08 mm), as the brushed map. OpenGL convention."""
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(seed)
    g = gaussian_filter(rng.standard_normal((size, size)), 1.8, mode="wrap")
    g /= g.std()
    peel = gaussian_filter(rng.standard_normal((size, size)), 10.0, mode="wrap")
    peel /= peel.std()
    h = g + 0.6 * peel
    dv = np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)
    du = np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)
    k = 0.10
    nrm = np.stack([-du * k, dv * k, np.ones_like(h)], axis=-1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    Image.fromarray(np.clip((nrm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)).save(path)


def _on_can(u, v):
    """Where the right camera's ray through pixel (u, v) meets the can (or, if it passes over the model's can, the
    can's surface nearest to it), and the can's outward normal there."""
    best = None
    for y in np.arange(-0.215, -0.08, 0.0002):
        q = _px("right", u, v, "y", y)
        R = _muf_ring(q[0])
        P2_ = R[:, 1:]
        E = np.roll(P2_, -1, axis=0) - P2_
        t = np.clip(((q[1:] - P2_) * E).sum(1) / np.maximum((E * E).sum(1), 1e-12), 0, 1)
        near = P2_ + E * t[:, None]
        dist = np.linalg.norm(near - q[1:], axis=1)
        i = int(np.argmin(dist))
        hit = inside(P2_, np.array([[q[1], q[2]]]))[0]
        if best is None or (dist[i] < best[0] and y < -0.15) or hit:     # the outer flank: the side the photo sees
            nn = np.array([0.0, E[i, 1], -E[i, 0]])
            nn /= np.linalg.norm(nn)
            if nn[1:] @ (near[i] - P2_.mean(axis=0)) < 0:
                nn = -nn
            best = (dist[i], np.array([q[0], near[i, 0], near[i, 1]]), nn)
        if hit:
            break
    return best[1], best[2]


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
    # blind rivets (RIGHT px): three on the cap's front edge, two on the nose; domed 5.5 mm heads, mandrel holes.
    # The cap's front edge runs on the plane of the three cap rivets, 6 mm ahead of them
    global _CAP_PLANE
    riv = [_on_can(u, v) for u, v in ((1114, 924), (1079, 988), (1054.6, 1041.6), (1430.8, 1181.2), (1408, 1219.8))]
    R3 = np.array([p for p, _ in riv[:3]])
    bb, aa = np.polyfit(R3[:, 2], R3[:, 0], 1)
    _CAP_PLANE = (float(aa), float(bb))
    _can(m)
    # round 3: the three rivets seen from behind (REAR 3x crop, rear_cap: the lower corners of the cap's face at
    # (2142, 870) and (2268, 870), one at the bottom (2205, 898)), on the cap where the rear camera's ray meets it
    V = np.asarray(m.V, float)
    Nv = np.zeros_like(V)
    for f in m.F:
        nf = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
        for i in f:
            Nv[i] += nf
    Nv /= np.maximum(np.linalg.norm(Nv, axis=1, keepdims=True), 1e-12)
    capv = (V[:, 0] < 0.07) & (V[:, 2] > 0.74) & (np.abs(V[:, 1] + 0.139) < 0.07)
    cam = cams.CAMS["rear"]
    for u, v in ((2142, 870), (2268, 870), (2205, 898)):
        d = cam.ray(np.array([u], float), np.array([v], float))[0]
        d /= np.linalg.norm(d)
        w = V - cam.C
        dist = np.linalg.norm(w - np.outer(w @ d, d), axis=1)
        dist[~capv | (Nv @ d > -0.2)] = 1.0
        near = np.nonzero(dist < max(float(dist.min()) * 1.5, 0.0015))[0]
        i = int(near[np.argmin((w @ d)[near])])                     # the first surface along the ray: the cap's
        riv.append((V[i] - Nv[i] * 0.0006, Nv[i]))
    for k, (p, nrm) in enumerate(riv):
        p = p + nrm * 0.0006                                       # on the cap or the nose, which stand 0.6 mm proud
        m.add(turned(p - nrm * 0.0003, nrm, [(0.0, 0.0001), (0.0, 0.00275), (0.0004, 0.0027), (0.0009, 0.0022),
                                              (0.0012, 0.0014), (0.00125, 0.0008), (0.0004, 0.0008), (0.0004, 0.0001)],
                     "steel", 16, True, True))
        m.add(turned(p + nrm * 0.0008, nrm, [(0.0, 0.0001), (0.0, 0.00075)], "bore", 8, True, False))
    # outlet (REAR, 2x crop: lip 54.8 px = 37 mm, a black ring 30.6, the spark arrestor's sleeve 25.8, dark 19.6):
    # rolled lip 4 mm proud of the cap's face, the sleeve's end face 2.5 mm, the gap between them and the bore dark
    a = OUTLET - OUT_AXIS * 0.016
    m.add(turned(a, OUT_AXIS, [(0.0, 0.0168), (0.0, 0.0185), (0.0145, 0.0185), (0.0155, 0.0183), (0.0160, 0.0176),
                               (0.0158, 0.0168), (0.0, 0.0168)], "muffler", 40, False, False))
    m.add(turned(a + OUT_AXIS * 0.0125, OUT_AXIS, [(0.0, 0.0001), (0.0, 0.0167)], "bore", 40, True, False))
    m.add(turned(a + OUT_AXIS * 0.0125, OUT_AXIS, [(0.0, 0.0098), (0.0, 0.0129), (0.0012, 0.0129), (0.0015, 0.0126),
                                                   (0.0015, 0.0101), (0.0012, 0.0098), (0.0, 0.0098)], "steel", 40, False,
                 False))
    # mounts (hidden under the side panel in every photo, EST): two brackets welded on the can's inner flank rise to a
    # tab square to the right subframe rail's underside; a rubber bush (fiche K95CF2700: mounting rubbers) on the tab
    # under the rail, a steel collar through it, an M8 flange bolt up through tab, collar and bush into the rail
    low = _sub_rails(-1)[0][::-1]
    for x in (0.220, 0.255):
        i = int(np.argmin(np.abs(low[:, 0] - x)))
        p0, p1 = low[max(i - 1, 0)], low[min(i + 1, len(low) - 1)]
        tg = np.array([p1[0] - p0[0], p1[2] - p0[2]])
        tg /= np.linalg.norm(tg)
        nd = np.array([tg[1], -tg[0]])
        if nd[1] > 0:
            nd = -nd                                                     # the rail's downward normal (x, z)
        rz = float(np.interp(x, low[:, 0], low[:, 2]))
        ry = float(np.interp(x, low[:, 0], low[:, 1]))
        under = np.array([x, rz]) + nd * 0.0110                          # the rail's underside (22 mm tall rail)
        ax = np.array([-nd[0], 0.0, -nd[1]])                              # up, square to the rail
        bush_top = under + nd * 0.0002
        tab_top = bush_top + nd * 0.008                                  # 8 mm rubber bush
        tab_c = tab_top + nd * 0.0015
        zl, zt, yc, hw = _muf(x)
        yin = yc + hw                                                    # the can's inner flank
        # tab (3 mm) under the bush, across to the strap
        e = np.array([-nd[1], nd[0]])                                    # along the rail
        tab = np.array([tab_c + e * 0.010, tab_c - e * 0.010])
        R = np.column_stack([np.array([e[0], 0.0, e[1]]), Y3, ax])
        ym = ry + 0.004                                                  # inboard on the rail: clear of the panel's lip
        m.add(box((tab_c[0], ym - 0.0005, tab_c[1]), (0.020, 0.012, 0.003), "steel", R))
        # strap: from the can's inner flank (welded) up to the tab's outer end
        strap = np.array([(x - 0.007, (zl + zt) / 2), (x + 0.007, (zl + zt) / 2), (tab_c[0] + 0.007, tab_c[1] - 0.001),
                          (tab_c[0] - 0.007, tab_c[1] - 0.001)])
        m.add(slab(strap, yin + 0.0016, 0.003, "steel", r=0.0008, step=0.005, to=_xz))
        c3 = np.array([bush_top[0], ym, bush_top[1]])
        m.add(turned(c3, -ax, [(0.0, 0.0045), (0.0, 0.0065), (0.0010, 0.0070), (0.0070, 0.0070), (0.0080, 0.0065),
                               (0.0080, 0.0045), (0.0, 0.0045)], "rubber_black", 24, False, False))          # bush
        m.add(turned(c3, -ax, [(0.0, 0.0042), (0.0, 0.0050), (0.0110, 0.0050), (0.0110, 0.0042), (0.0, 0.0042)], "steel", 16,
                     False, False))                                                                     # collar
        head = np.array([tab_c[0], ym, tab_c[1]]) - ax * 0.0016
        m.add(hexbolt(head, -ax, 0.012, 0.0075, flange_d=0.017, flange_h=0.0015, mat="zinc", seg=36))
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
    washer and split pin, return spring. Teeth 4 mm high every 8 mm (LEFT zoom). Black, the teeth's tips worn bright
    (detail 475839 and RIGHT: a dark peg with bright tooth edges); its side rails deep at the root and shallow at the
    tip, a triangle seen from behind (detail 475839: the brace runs from the tip down to the hinge)."""
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
            lo = -0.021 + 0.013 * min(max((o[1] - PEG_Y0 - 0.010) / (PEG_TIP[0] - PEG_Y0 - 0.010), 0.0), 1.0)
            ring = f([(o[0], o[1], lo), (o[0], o[1], tooth[i]), (q[0], q[1], tooth[i]), (q[0], q[1], lo)])
            rings.append(ring[::-1] if s > 0 else ring)
        band = grid(Mesh(), rings + [rings[0]], "peg_black")
        V = np.asarray(band.V)
        for k, fc in enumerate(band.F):                               # the crests of the teeth, worn bright
            c = V[list(fc)].mean(axis=0)
            if np.ptp(V[list(fc)][:, 2]) < 0.0025 and c[2] > PEG_ROOT_Z - 0.003 + (abs(c[1]) - PEG_Y0) * 0.08:
                band.M[k] = "peg_edge"
        m.add(band)
        for ly in (PEG_Y0 + 0.031, PEG_Y0 + 0.062):               # cross bars
            b = Mesh()
            b.verts(f([(x, y, z) for z in (-0.019, -0.006) for x, y in ((-0.025, ly - 0.002), (0.025, ly - 0.002), (0.025, ly + 0.002),
                                                                         (-0.025, ly + 0.002))]))
            for fc in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                b.face(fc if s > 0 else fc[::-1], "peg_black")
            m.add(b)
        # hinge: ears on the peg, pin along x through the frame's boss, washer, split pin, torsion spring
        py, pz = PEG_PIN
        for lx in (-0.020, 0.015):
            m.add(box((PEG[0] + lx, s * (py + 0.0075), pz + 0.002), (0.005, 0.015, 0.018), "peg_black"))
        pin0 = np.array([PEG[0] - 0.031, s * py, pz])
        m.add(turned(pin0, (1, 0, 0), [(0, 0.006), (0.003, 0.006), (0.003, 0.003), (0.060, 0.003)], "bolt", 12))
        m.add(turned(pin0 + (0.054, 0, 0), (1, 0, 0), [(0, 0.006), (0.0015, 0.006)], "bolt", 12))
        m.add(tube([pin0 + (0.0575, 0, -0.007), pin0 + (0.0575, 0, 0.007)], 0.0009, 6, "bolt"))
        m.add(coil(pin0 + (0.0145, 0, 0), pin0 + (0.0235, 0, 0), 0.0040, 0.0009, 5, "steel", seg=6, dead=0, per=14))
        m.add(tube([pin0 + (0.0145, 0, 0.0040), pin0 + (0.0145, s * 0.012, 0.0085)], 0.0009, 6, "steel"))
        m.add(tube([pin0 + (0.0235, 0, 0.0040), pin0 + (0.0235, -s * 0.004, 0.0030)], 0.0009, 6, "steel"))
    return m


# ---------------------------------------------------------------- implicit castings (round 4)
# A casting whose parts run into each other with fillets (the master cylinder's columns, lugs and pads) is written as a
# smooth union of simple solids (signed distance functions, metres, negative inside) and its surface extracted by naive
# surface nets: one vertex per grid cell the surface crosses, at the mean of the crossings on the cell's edges, then
# moved onto the surface by Newton steps along the gradient; one quad per grid edge the surface crosses.
def _sm(a, b, k):
    """Smooth union of two distance fields: a fillet of about K where the two solids meet (polynomial smooth min)."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def _sd_round(d2, dz, re):
    """Solid bounded by a section's distance D2 and an axial distance DZ, the edges between them rounded by RE."""
    w0, w1 = d2 + re, dz + re
    return np.minimum(np.maximum(w0, w1), 0.0) + np.hypot(np.maximum(w0, 0.0), np.maximum(w1, 0.0)) - re


def _sd_rrect(px, py, x, y, rc):
    """2D rounded rectangle over the ranges X, Y, corner radius RC."""
    qx = np.abs(px - (x[0] + x[1]) / 2) - (x[1] - x[0]) / 2 + rc
    qy = np.abs(py - (y[0] + y[1]) / 2) - (y[1] - y[0]) / 2 + rc
    return np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0)) + np.minimum(np.maximum(qx, qy), 0.0) - rc


def _sd_prism(P, x, y, z, rc, re):
    """Upright block over the ranges X, Y, Z: upright edges rounded by RC, top and bottom edges by RE."""
    return _sd_round(_sd_rrect(P[:, 0], P[:, 1], x, y, rc), np.abs(P[:, 2] - (z[0] + z[1]) / 2) - (z[1] - z[0]) / 2, re)


def _sd_cyl(P, a, b, r, re):
    """Cylinder of radius R from A to B, its two rims rounded by RE."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = float(np.linalg.norm(b - a))
    e = (b - a) / L
    q = P - a
    t = q @ e
    return _sd_round(np.linalg.norm(q - t[:, None] * e, axis=1) - r, np.abs(t - L / 2) - L / 2, re)


def _surface_nets(f, lo, hi, h, mat, iters=5):
    """Closed surface f = 0 inside the box LO..HI (f > 0 on its border) on a grid of step H (quads, normals out)."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    n = np.ceil((hi - lo) / h).astype(int) + 1
    ax = [lo[i] + h * np.arange(n[i]) for i in range(3)]
    F = f(np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)).reshape(n)
    ins = F < 0
    offs = np.array([(a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)])
    cin = np.stack([ins[a:a + n[0] - 1, b:b + n[1] - 1, c:c + n[2] - 1] for a, b, c in offs], -1)
    active = cin.any(-1) & ~cin.all(-1)
    I = np.argwhere(active)
    cv = np.stack([F[I[:, 0] + a, I[:, 1] + b, I[:, 2] + c] for a, b, c in offs], 1)
    acc, cnt = np.zeros((len(I), 3)), np.zeros(len(I))
    for ea in range(8):
        for eb in range(ea + 1, 8):
            if np.abs(offs[ea] - offs[eb]).sum() != 1:
                continue
            fa, fb = cv[:, ea], cv[:, eb]
            x = (fa < 0) != (fb < 0)
            t = np.where(x, fa / np.where(x, fa - fb, 1.0), 0.0)
            acc += (offs[ea] + t[:, None] * (offs[eb] - offs[ea])) * x[:, None]
            cnt += x
    V = lo + h * (I + acc / cnt[:, None])
    vid = -np.ones(n - 1, int)
    vid[tuple(I.T)] = np.arange(len(I))
    quads = []
    for axis in range(3):
        u_, v_ = (axis + 1) % 3, (axis + 2) % 3
        s0, s1 = [slice(None)] * 3, [slice(None)] * 3
        s0[axis], s1[axis] = slice(0, -1), slice(1, None)
        a0 = ins[tuple(s0)]
        E = np.argwhere(a0 != ins[tuple(s1)])
        E = E[(E[:, u_] >= 1) & (E[:, v_] >= 1) & (E[:, u_] <= n[u_] - 2) & (E[:, v_] <= n[v_] - 2)]
        out = a0[tuple(E.T)]                                    # inside at the edge's start: the normal points +axis

        def cell(du, dv):
            c = E.copy()
            c[:, u_] -= du
            c[:, v_] -= dv
            return vid[tuple(c.T)]
        q = np.stack([cell(1, 1), cell(0, 1), cell(0, 0), cell(1, 0)], 1)
        quads.append(np.where(out[:, None], q, q[:, ::-1]))
    Q = np.vstack(quads)
    e = 0.1 * h
    for _ in range(iters):                                      # onto the surface (moves capped at half a cell)
        g = np.stack([(f(V + e * np.eye(3)[i]) - f(V - e * np.eye(3)[i])) / (2 * e) for i in range(3)], 1)
        step = f(V)[:, None] * g / np.maximum((g * g).sum(1), 1e-12)[:, None]
        nrm = np.linalg.norm(step, axis=1, keepdims=True)
        V = V - step * np.minimum(1.0, 0.5 * h / np.maximum(nrm, 1e-12))
    m = Mesh()
    m.verts(V)
    for q in Q:
        m.face(q, mat)
    return m


def _uv_cast(m, base, tile, org, regions):
    """UVs for an isotropic cast-grain map on faces BASE.. of M: each face projected on the plane square to its normal's
    largest component, each of the six directions into its own REGIONS offset of the map (so lettering drawn for the
    outer face, region '-y', shows nowhere else). Metres per repeat TILE, origin ORG."""
    V = np.asarray(m.V, float)
    for k in range(base, len(m.F)):
        idx = list(m.F[k])
        P = V[idx]
        nn = np.cross(P[1] - P[0], P[2] - P[0]) + (np.cross(P[2] - P[0], P[3] - P[0]) if len(idx) > 3 else 0)
        a = int(np.argmax(np.abs(nn)))
        key = ("-" if nn[a] < 0 else "+") + "xyz"[a]
        cu, cv_ = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[a]
        du, dv = regions[key]
        m.uv[k] = [((p[cu] - org[cu]) / tile + du, (p[cv_] - org[cv_]) / tile + dv) for p in P]


# ---------------------------------------------------------------- rear brake: pedal, master cylinder, hose
# RIGHT px (3.25x crop 1680..1990 x 1420..1620): the pedal's arm centre line from the pivot over the top of its arc
# and down to the folding tip; its width square to that line (21 mm at the arc, 14 mm at the tip); the tip's pin
PEDAL_LINE = [(1709.2, 1493.2), (1726.2, 1472.3), (1750.8, 1465.5), (1772.3, 1464.6), (1793.8, 1473.8),
              (1812.3, 1493.8), (1840.0, 1512.3), (1870.8, 1523.1), (1901.5, 1530.8), (1926.2, 1532.3),
              (1950.8, 1529.2)]
PEDAL_W = (0.021, 0.021, 0.021, 0.021, 0.0205, 0.020, 0.019, 0.017, 0.015, 0.014, 0.014)

# ---- rear master cylinder (round 4): ONE Nissin casting (fiche K95CF1500 part 2), read on 4x to 8x crops of RIGHT
# (scratch chassis4/mc1, mc2, mc3, mc7), rr34 (mc4, mc9) and REAR (mc6, mc8). x and z: RIGHT cast on y MC_YC; y: REAR
# cast on the feature's own x (the rear photo reads 13 px (10 mm) lower than RIGHT here, as at the footpegs: its rows
# are not used). Ranges are (x), (y), (z) in metres.
MC_YC = -0.1211                              # REAR: the boot cols 2150..2175 (-0.1118..-0.1304), the push rod col 2160
MC_AXIS = ((0.4803, 0.4796), (0.4697, 0.5660))   # the bore (x, z): the boot's centre (RIGHT u 1641) at the skirt's foot
#   (v 1432) and the neck's centre (u 1618..1636) under the banjo (v 1319): 7 deg, the top leaning back
MC_RES = ((0.4408, 0.4606), (-0.1335, -0.1090), (0.5190, 0.5700))   # reservoir column: RIGHT u 1589..1615, its rounded
#   foot v 1373..1378; REAR cols 2147..2180 (an oval column 20 x 24.5 mm: rr34 m1: round, slim)
MC_HEAD = ((0.4335, 0.4610), (-0.1341, -0.1067), (0.5670, 0.5790))  # the cap's seat: RIGHT u 1580..1615 from the step
#   under it at the rear (v 1317) to the cap (v 1302); REAR cols 2144..2181
MC_LID = (0.5790, 0.5852)                    # plate (part 6) and cap (part 4): the dark band v 1302..1296 and its top
MC_SCREWS = ((0.4374, -0.1250), (0.4541, -0.1124))   # cap screws (part 14) at diagonal corners: RIGHT u 1584.5 / 1606.5
#   (the inboard one stands higher: further from the camera), REAR cols 2169 / 2151.5; pan heads 7 mm (RIGHT 9 px)
MC_BORE = (0.4728, 0.0105, 0.4990, 0.5505)  # bore column (x of its upright axis, radius, z): RIGHT front edge u 1645 (v
#   1350..1400), its rear in the valley by the reservoir u 1616..1618 (rr34: two round columns joined by a web), the
#   shoulder from the neck (1636, 1340) to (1645, 1350); its outer side 0.6 mm inside the frame tabs' inner face
#   (Y_PLATE - TAB_T: the lugs seat on the tabs, bolts from outside, fiche part 11)
MC_BLOCK = ((0.4480, 0.4700), (-0.1285, -0.1140), (0.5010, 0.5260))  # the web under the reservoir: RIGHT its rear edge
#   u 1600 (v 1378..1400), the round emblem on it; REAR its lit rear face cols 2158..2173 with two dots; set back
#   from both columns' outer sides (rr34)
MC_LOWER = (0.4784, 0.0105, 0.4890, 0.5060)    # lower column (axis x, radius, z): RIGHT u 1622..1655 with the lug (v 1400..1417)
MC_SKIRT = ((0.4648, 0.4928), (-0.1338, -0.1082), (0.4796, 0.4915))  # its bell foot: RIGHT u 1620..1658, v 1417..1432;
#   REAR cols 2145..2181 (y -0.1081..-0.1349; the outer side kept 1.2 mm in, under the lower tab)
MC_WIN = (0.4370, -0.1238, 0.5370, 0.0105, 0.00865, 0.0072)   # sight window: pad face x (RIGHT u 1584), centre y (REAR
#   ring cols 2155.6..2179), z (RIGHT v 1357, the bump v 1340..1373); pad radius; lit ring 17.3 mm (REAR); lens recess
MC_NECK = 0.00685                            # RIGHT u 1618..1636 under the banjo
MC_LUG = 0.0065                              # EST: lugs 13 mm round on the tabs' bolts (hidden behind the tabs' bosses)
MC_PIN = (1648, 1505)                        # RIGHT: the clevis pin, centre of the clevis's lower part (mc7: u 1638..1660,
#                                              v 1497..1512)
MC_TILE, MC_ORG = 0.128, (0.430, -0.140, 0.475)       # mc_n.png: metres per repeat, origin of the outer face's region
MC_REG = {"-y": (0.0, 0.0), "+y": (0.55, 0.5), "-x": (0.60, 0.0), "+x": (0.80, 0.0), "-z": (0.0, 0.92), "+z": (0.0, 0.92)}


def _mc_sdf(P):
    """The casting as a smooth union (fillets of 1.2 to 2.5 mm, cast): reservoir column and its head, the bore column
    with its lugs, the web, the lower column and its skirt, the neck, the sight window's pad with the lens recess."""
    d = _sd_prism(P, *MC_RES, 0.0095, 0.0040)
    d = _sm(d, _sd_prism(P, *MC_HEAD, 0.0045, 0.0010), 0.0012)
    xb, rb, zb0, zb1 = MC_BORE
    d = _sm(d, _sd_cyl(P, (xb, MC_YC, zb0), (xb, MC_YC, zb1), rb, 0.0050), 0.0015)
    d = _sm(d, _sd_prism(P, *MC_BLOCK, 0.0050, 0.0030), 0.0025)
    xl, rl, zl0, zl1 = MC_LOWER
    d = _sm(d, _sd_cyl(P, (xl, MC_YC, zl0), (xl, MC_YC, zl1), rl, 0.0010), 0.0030)
    d = _sm(d, _sd_prism(P, *MC_SKIRT, 0.0125, 0.0015), 0.0020)
    a0, a1 = (np.array([x, MC_YC, z]) for x, z in MC_AXIS)
    d = _sm(d, _sd_cyl(P, a0 + (a1 - a0) * ((0.535 - a0[2]) / (a1[2] - a0[2])), a1, MC_NECK, 0.0008), 0.0020)
    for (u, v), k in zip(TAB_BOLTS_PX, (0.0025, 0.0015)):          # the upper one's fillet wider: a narrow crevice
        b = _px("right", u, v, "y", -(Y_PLATE - TAB_T))             # under it made non-manifold cells
        d = _sm(d, _sd_cyl(P, (b[0], -0.1319, b[2]), (b[0], -0.1120, b[2]), MC_LUG, 0.0008), k)
    x0, yw, zw, rp, _, rr = MC_WIN
    d = _sm(d, _sd_cyl(P, (x0, yw, zw), (x0 + 0.012, yw, zw), rp, 0.0012), 0.0015)
    return np.maximum(d, -_sd_cyl(P, (x0 - 0.002, yw, zw), (x0 + 0.0015, yw, zw), rr, 0.0))   # the lens's recess


def _rr_ring(x, y, rc, n=6):
    """Counter-clockwise rounded rectangle over the ranges X, Y (corner radius RC, N points a corner)."""
    pts = []
    for cx, cy, a0 in ((x[1] - rc, y[0] + rc, -90), (x[1] - rc, y[1] - rc, 0), (x[0] + rc, y[1] - rc, 90),
                       (x[0] + rc, y[0] + rc, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + rc * math.cos(a), cy + rc * math.sin(a)))
    return np.array(pts)


def _pill(x, y, z, rc, r0, r1, mat, n=6, k=4):
    """Rounded-rectangle box (plan X x Y, corner RC) from Z[0] to Z[1], its bottom edge rounded by R0, its top by R1."""
    q = [math.pi / 2 * i / k for i in range(k + 1)]
    rings = [(z[0] + r0 * (1 - math.cos(a)), r0 * (1 - math.sin(a))) for a in q]
    rings += [(z[1] - r1 * (1 - math.cos(a)), r1 * (1 - math.sin(a))) for a in q[::-1]]
    R = []
    for zz, ins in rings:
        o = _rr_ring((x[0] + ins, x[1] - ins), (y[0] + ins, y[1] - ins), max(rc - ins, 0.0003), n)
        R.append(np.column_stack([o, np.full(len(o), zz)]))
    return _outward(grid(Mesh(), R, mat, cap0=True, cap1=True))


def _pan_screw(c, d, mat="steel", dk=0.0070, k=0.0032, w=0.0009, l=0.0019):
    """JIS cross-recessed pan head (M4: 7 mm head; 3.2 mm tall: RIGHT the heads stand 4 px over the cap) on C along D: a rounded head with the cross
    recess cut through it (the cap's face under it is the recess's floor)."""
    d = np.asarray(d, float) / np.linalg.norm(d)
    R = frame_z(d)
    e1, e2 = R[:, 0], R[:, 1]
    cross = [(w / 2, w / 2), (l, w / 2), (l, -w / 2), (w / 2, -w / 2), (w / 2, -l), (-w / 2, -l), (-w / 2, -w / 2),
             (-l, -w / 2), (-l, w / 2), (-w / 2, w / 2), (-w / 2, l), (w / 2, l)]
    to = lambda u, v, t: np.asarray(c) + u * e1 + v * e2 + t * d          # noqa: E731
    return slab2(circle(dk / 2, 32), k / 2, k, mat, r=0.0009, step=0.0008, holes=[np.array(cross)[::-1]], to=to,
                 mirror=False, r_hole=0.0002)


def mc_map(path, size=1024, seed=5):
    """Normal map of the master cylinder's casting (MC_TILE metres per repeat, 0.125 mm a pixel): a coarse sand-cast
    grain (RIGHT 7x crop: a mottle about 1 mm across over a fine speckle) and the cast marks, placed in the outer face's
    region of the map (MC_REG '-y': u = (x - 0.430) / tile, v = (z - 0.475) / tile): NISSIN raised 0.3 mm along the bore
    column (RIGHT u 1628..1640, v 1348..1378: 6 mm letters reading down, their tops forward), LOWER beside the sight
    window (v 1351..1354, from u 1598: 3 mm letters, kept on the reservoir column's face), the round emblem (RIGHT u 1605..1614, v 1381..1391: an 8 mm ring
    round an N) and the two dots on the web's rear face (REAR: 1.5 mm, 7 mm apart, region '-x')."""
    from PIL import Image, ImageDraw, ImageFont
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(seed)
    g = gaussian_filter(rng.standard_normal((size, size)), 1.5, mode="wrap")
    mot = gaussian_filter(rng.standard_normal((size, size)), 3.0, mode="wrap")
    h = g / g.std() + 0.6 * mot / mot.std()
    h *= 0.016                                                     # mm: the grain's relief (0.035 read as crinkle paint
    #                                                                in the close-up cu1; the photo's grain is finer)
    px = size / (MC_TILE * 1000)                                   # pixels per mm
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    lay = Image.new("L", (size, size), 0)

    def put(text, x, z, cap, rot, length=None):
        f = ImageFont.truetype(font, int(cap * px / 0.72))
        bb = f.getbbox(text)
        im = Image.new("L", (bb[2] + 4, bb[3] + 4), 0)
        ImageDraw.Draw(im).text((2 - bb[0], 2), text, fill=255, font=f)
        if length:
            im = im.resize((int(length * px), im.height))
        im = im.rotate(rot, expand=True)
        cu, cv = (x - MC_ORG[0]) / MC_TILE * size, (1 - (z - MC_ORG[2]) / MC_TILE) * size
        lay.paste(im, (int(cu - im.width / 2), int(cv - im.height / 2)), im)
    put("NISSIN", 0.4766, 0.5310, 6.0, -90, 22.0)
    put("LOWER", 0.4512, 0.5352, 3.0, 0, 12.5)
    put("N", 0.4555, 0.5190, 4.2, 0)
    d = ImageDraw.Draw(lay)
    cu, cv = (0.4555 - MC_ORG[0]) / MC_TILE * size, (1 - (0.5190 - MC_ORG[2]) / MC_TILE) * size
    d.ellipse([cu - 4.0 * px, cv - 4.0 * px, cu + 4.0 * px, cv + 4.0 * px], outline=255, width=int(0.8 * px))
    rel = gaussian_filter(np.asarray(lay, float) / 255.0, 0.12 * px) * 0.30
    for z in (0.5060, 0.5130):                                     # the dots: 0.4 mm dimples on the web's rear face
        cu = ((-0.1245 - MC_ORG[1]) / MC_TILE + MC_REG["-x"][0]) * size
        cv = (1 - ((z - MC_ORG[2]) / MC_TILE + MC_REG["-x"][1])) * size
        yy, xx = np.mgrid[0:size, 0:size]
        rel -= 0.4 * np.exp(-((xx - cu) ** 2 + (yy - cv) ** 2) / (2 * (0.5 * px) ** 2))
    h = h + rel
    dv = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * px / 2      # mm per mm
    du = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * px / 2
    nrm = np.stack([-du, dv, np.ones_like(h)], axis=-1)            # image rows run down: +v is up the image
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    Image.fromarray(np.clip((nrm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)).save(path)


def _master_cylinder(pin):
    """Rear master cylinder (fiche K95CF1500): the one casting (_mc_sdf), the cap stack (plate, cap, two pan screws), the
    sight window's lens and ring, the banjo (washers, black eye, 12 mm bolt) with the hose's bent steel tube rising from
    it, the plain boot, the push rod with its lock nut and the U clevis on the pedal lever's pin (part 10). The hose
    from the tube to detail_wheels.py's run is the loop of fiche part 1: up, forward behind the frame's tabs and down
    inboard of the casting (hidden in every photo but its first bend, RIGHT u 1648..1668, v 1283..1312)."""
    m = Mesh()
    mc = _surface_nets(_mc_sdf, (0.425, -0.145, 0.472), (0.505, -0.098, 0.586), 0.0012, "mc_cast")   # 12k vertices
    _uv_cast(mc, 0, MC_TILE, MC_ORG, MC_REG)
    m.add(mc)
    # cap stack
    m.add(_pill((0.4338, 0.4607), (-0.1338, -0.1070), (MC_HEAD[2][1] - 0.0002, MC_LID[0] + 0.0008), 0.0045, 0.0002, 0.0003,
                "steel", k=1))
    m.add(_pill((0.4340, 0.4605), (-0.1336, -0.1072), (MC_LID[0] + 0.0008, MC_LID[1]), 0.0043, 0.0004, 0.0015, "mc_lid"))
    for sx, sy in MC_SCREWS:
        m.add(_pan_screw((sx, sy, MC_LID[1] - 0.0001), (0.0, 0.0, 1.0)))
    # sight window: the lit ring round the recess, the lens 1.2 mm in, a retaining ring of three arcs on it (REAR mc6)
    x0, yw, zw, _, r_ring, rr = MC_WIN
    m.add(turned((x0 + 0.0004, yw, zw), (-1, 0, 0), [(0, rr + 0.0002), (0.0, r_ring - 0.0003), (0.0005, r_ring),
                                                      (0.0014, r_ring - 0.0004), (0.0014, rr + 0.0004), (0.0, rr + 0.0002)],
                 "alu_satin", 48, False, False))
    m.add(turned((x0 + 0.0015, yw, zw), (-1, 0, 0), [(0, 0.0001), (0, rr - 0.0001), (0.0006, rr - 0.0001), (0.0006, 0.0001)],
                 "mc_lens", 48))
    for k in range(3):
        a0 = math.radians(90 + 120 * k + 14)
        arc = [(math.cos(a), math.sin(a)) for a in np.linspace(a0, a0 + math.radians(92), 12)]
        o = np.array([(5.6e-3 * c, 5.6e-3 * s) for c, s in arc] + [(4.4e-3 * c, 4.4e-3 * s) for c, s in arc[::-1]])
        m.add(slab(o + (yw, zw), x0 + 0.0006, 0.0006, "mc_ring", r=0.0002, step=0.0008,
                   to=lambda u, v, t: (t, u, v), mirror=False))
    # banjo on the neck (fiche 12, 13): washer, black eye 16.4 x 11 mm (RIGHT u 1619..1640, v 1303..1317), washer, bolt
    a0, a1 = (np.array([x, MC_YC, z]) for x, z in MC_AXIS)
    db = (a1 - a0) / np.linalg.norm(a1 - a0)
    m.add(turned(a1, db, [(0, 0.0052), (0, 0.0075), (0.0010, 0.0075), (0.0010, 0.0052), (0, 0.0052)], "zinc", 32, False,
                 False))
    eye = a1 + db * 0.0010
    m.add(turned(eye, db, [(0, 0.0001), (0, 0.0078), (0.0006, 0.0082), (0.0104, 0.0082), (0.0110, 0.0078), (0.0110, 0.0001)],
                 "rubber_black", 32))
    m.add(turned(eye + db * 0.0110, db, [(0, 0.0052), (0, 0.0075), (0.0010, 0.0075), (0.0010, 0.0052), (0, 0.0052)], "zinc",
                 32, False, False))
    m.add(hexbolt(eye + db * 0.0120, db, 0.012, 0.0062, flange_d=0.014, flange_h=0.0010, mat="steel", seg=36))
    ec = eye + db * 0.0055                                          # the eye's centre; its spigot forward, the tube up
    m.add(turned(ec + (0.0070, 0, 0), (1, 0, 0), [(0, 0.0001), (0, 0.0045), (0.0055, 0.0045), (0.0065, 0.0038),
                                                    (0.0065, 0.0001)], "rubber_black", 20))
    tx = 0.4855                                                     # RIGHT u 1645..1651: the bright pipe, 4.7 mm,
    tp = spline([ec + (0.0120, 0, 0), (tx - 0.0010, MC_YC, ec[2] + 0.0006), (tx, MC_YC, ec[2] + 0.0040),
                 (tx, MC_YC, 0.5815)], 16)                          # rising from the eye to v 1300 (z 0.581)
    m.add(tube(tp, 0.00235, 14, "zinc"))
    m.add(turned((tx, MC_YC, 0.5795), (0, 0, 1), [(0, 0.0001), (0, 0.0036), (0.0008, 0.0046), (0.0060, 0.0046),
                                                  (0.0060, 0.0001)], "rubber_black", 20))      # the hose's black sleeve
    # the hose (fiche 1: its top a hook): up off the pipe, over forward and down in front of it (RIGHT: black, u 1648..
    # 1668, v 1283..1312, behind the tabs' top), then down inboard of the casting (hidden, EST) to detail_wheels.py's run
    # end, which it meets end to end inside a crimped sleeve (_wheels_hose, round 3)
    cen, _ = _wheels_hose()
    E = cen[-1]
    dE = (cen[-1] - cen[-2]) / np.linalg.norm(cen[-1] - cen[-2])
    hose = spline([E, E + dE * 0.008, (0.461, -0.0995, 0.517), (0.471, -0.0990, 0.530), (0.484, -0.0995, 0.546),
                   (0.494, -0.1010, 0.562), (0.4970, -0.1035, 0.574), (0.4960, -0.1060, 0.5835), (0.4925, -0.1110, 0.5895),
                   (0.4880, -0.1175, 0.5890), (tx, MC_YC, 0.5855), (tx, MC_YC, 0.5815)], 70)
    m.add(tube(hose, 0.0042, 10, "cable"))
    m.add(turned(E - dE * 0.008, dE, [(0.0, 0.0047), (0.0, 0.0060), (0.003, 0.0062), (0.0045, 0.0057), (0.0065, 0.0057),
                                      (0.008, 0.0062), (0.0095, 0.0057), (0.0115, 0.0057), (0.013, 0.0062),
                                      (0.016, 0.0060), (0.016, 0.0047), (0.0, 0.0047)], "zinc", 24, False, False))
    # boot (fiche 3): a plain black sleeve 18.7 mm (RIGHT u 1629..1653, REAR 18.6 mm) from the skirt to v 1451, its
    # lower end rounded onto the rod
    m.add(turned(a0 + db * 0.0004, -db, [(0, 0.0001), (0, 0.0088), (0.0010, 0.0093), (0.0120, 0.0093), (0.0140, 0.0086),
                                         (0.0152, 0.0064), (0.0156, 0.0040), (0.0156, 0.0001)], "rubber_black", 32))
    # push rod (fiche 8) down to the clevis (mc7: rod u 1640..1647), its lock nut (15) on the clevis's boss (v 1461..1466)
    cx, top = 0.4845, 0.4555                                        # clevis: RIGHT u 1636..1655, its top v 1465
    rod0 = a0 - db * 0.0150
    rod1 = np.array([cx, MC_YC, top])
    m.add(tube([rod0 + db * 0.004, rod1 + (0, 0, -0.003)], 0.0030, 14, "zinc"))
    m.add(hexnut(rod1 + (0, 0, 0.0002), rod0 - rod1, 0.010, 0.0040, 0.0031, "zinc", seg=24))
    m.add(thread(rod1 + (rod0 - rod1) * (0.0042 / np.linalg.norm(rod0 - rod1)), rod0 - rod1, 0.0030, 0.0010,
                 float(np.linalg.norm(rod0 - rod1)) - 0.0062, "zinc"))
    # clevis (fiche 10): seen as rectangular outlines from the side (RIGHT mc7) AND from behind (REAR mc8: legs 18 mm
    # apart over all), a box of 1.6 mm bars: its base round the rod's end, an upper box 14.4 mm long (u 1636..1655, v
    # 1467..1490), a waist, the lower box round the pin set 3 mm forward (u 1638..1660, v 1497..1513), bosses for the pin
    m.add(box((cx, MC_YC, top - 0.0010), (0.0144, 0.0176, 0.0020), "zinc"))
    hb, hy = 0.0016, 0.0088 - 0.0008
    for (xa, xb), (za, zb) in (((0.4773, 0.4917), (0.4365, top - 0.0020)), ((0.4790, 0.4955), (0.4180, 0.4330))):
        for xx in (xa + hb / 2, xb - hb / 2):
            for yy in (-hy, hy):
                m.add(box((xx, MC_YC + yy, (za + zb) / 2), (hb, hb, zb - za), "zinc"))
        for zz in (za + hb / 2, zb - hb / 2):
            for yy in (-hy, hy):
                m.add(box(((xa + xb) / 2, MC_YC + yy, zz), (xb - xa - 0.0002, hb, hb), "zinc"))
            for xx in (xa + hb / 2, xb - hb / 2):
                m.add(box((xx, MC_YC, zz), (hb, 2 * hy - 0.0002, hb), "zinc"))
    for yy in (-hy, hy):                                            # the waist between the two boxes, the pin's bosses
        m.add(box((0.4850, MC_YC + yy, 0.4348), (0.0130, hb, 0.0040), "zinc"))
        m.add(turned((pin[0], MC_YC + yy - 0.0008, pin[2]), Y3, [(0, 0.0030), (0, 0.0040), (hb, 0.0040), (hb, 0.0030),
                                                                  (0, 0.0030)], "zinc", 16, False, False))
    # pin: head inboard, the split pin's eye outboard (RIGHT: a small bright loop at u 1630..1637, v 1503..1515)
    m.add(turned((pin[0], MC_YC + 0.0104, pin[2]), -Y3, [(0, 0.0001), (0, 0.0042), (0.0014, 0.0042), (0.0014, 0.0030),
                                                        (0.0210, 0.0030), (0.0210, 0.0001)], "zinc", 16))
    yo = MC_YC - 0.0098
    m.add(tube([(pin[0] + 0.0040, yo, pin[2] + 0.0007), (pin[0] - 0.0030, yo, pin[2] + 0.0007)], 0.0005, 6, "steel"))
    th = np.linspace(0, 2 * math.pi, 13)
    m.add(tube([(pin[0] - 0.0052 + 0.0022 * math.cos(t), yo, pin[2] - 0.0002 + 0.0022 * math.sin(t)) for t in th],
               0.0005, 6, "steel"))
    return m


def _toe(pin):
    """Folding tip: two side cheeks and a serrated tread between them on a pin through the arm's end (RIGHT px
    1932..1975 x 1508..1537: 32 mm long, 22 mm tall, five teeth; TOP rows 922..955: y -0.161..-0.193)."""
    m = Mesh()
    x0, z0 = pin[0], pin[2]
    prof = [(-0.008, -0.009), (0.024, -0.006), (0.026, 0.004), (0.024, 0.010)]
    for k in range(5):                                            # teeth along the top, rearmost first
        xt = 0.020 - 0.0055 * k
        prof += [(xt, 0.013), (xt - 0.0022, 0.013), (xt - 0.0028, 0.010)]
    prof += [(-0.010, 0.010), (-0.012, 0.000)]
    o = np.array(prof) + (x0, z0)
    for ya, yb in ((-0.1610, -0.1640), (-0.1900, -0.1930)):
        m.add(slab(o, (ya + yb) / 2, abs(yb - ya), "alu_cast", r=0.0008, step=0.004, to=_xz))
    tread = np.array([p for p in prof if p[1] >= 0.010] + [(0.024, 0.006), (-0.010, 0.006)])
    m.add(slab(tread + (x0, z0), -0.1770, 0.0258, "alu_cast", r=0.0008, step=0.004, to=_xz))
    m.add(turned((x0, -0.1595, z0), -Y3, [(0, 0.0045), (0.0012, 0.0045), (0.0015, 0.003), (0.0355, 0.003)], "steel", 16))
    m.add(turned((x0, -0.1938, z0), -Y3, [(0, 0.0032), (0.0012, 0.0032)], "steel", 12))           # retaining washer
    return m


def rear_brake():
    """Rear brake pedal, master cylinder and its fittings (part brake_pedal): the cast arm from the photo's line,
    its round pivot boss on an M8 socket bolt, the folding tip; the rear lever to the push rod's clevis, the rubber
    boot, the cylinder body with its integral reservoir and cap, two mounting bolts, the banjo and the hose's first
    bend (the hose along the swingarm is detail_wheels.py's), the return spring."""
    m = Mesh()
    piv = _px("right", 1709.2, 1493.2, "y", -0.150)                # the boss: round, 25 mm (17 px radius)
    piv[1] = -0.1414                                               # on the footpeg bracket's outer face (0.141)
    m.add(turned(piv, -Y3, [(0, 0.0001), (0, 0.0122), (0.0006, 0.0127), (0.0114, 0.0127), (0.012, 0.0121), (0.012, 0.0001)],
                 "alu_cast", 32))
    head = piv - 0.0121 * Y3                                       # M8 socket cap screw, 13 mm head, 6 mm hex
    m.add(lathe2(head, -Y3, [(0.0, 0.0001), (0.0, 0.0065), (0.0072, 0.0065), (0.0080, 0.0058), (0.0080, 1.0, 0.006),
                             (0.0050, 1.0, 0.006), (0.0047, 0.0001)], "anod_black", 36, cap0=True, cap1=True))
    # arm: cast, 9 mm thick, its width from the photo; its plane moves out 13 mm to the tip (TOP rows 955..975)
    ys = np.linspace(-0.1470, -0.1600, len(PEDAL_LINE))
    pts = np.array([_px("right", u, v, "y", y) for (u, v), y in zip(PEDAL_LINE, ys)])
    pts[:, 1] = ys
    path = spline(pts, 40)
    w = np.interp(np.linspace(0, 1, 40), np.linspace(0, 1, len(PEDAL_W)), PEDAL_W)
    m.add(bar(path, 0.0090, w, "alu_cast"))
    m.add(_toe(pts[-1]))
    # rear lever from the boss to the clevis pin, bending in to the push rod's line (REAR mc8: rod and clevis at y -0.121)
    pin = _px("right", MC_PIN[0], MC_PIN[1], "y", MC_YC)
    lever_mid = (piv + pin) / 2 + (0, 0.002, 0.004)
    lever_mid[1] = -0.1330
    m.add(bar([piv - 0.0065 * Y3, lever_mid, pin + (0.0, 0.0, -0.002)], (0.007, 0.009, 0.0110), (0.024, 0.020, 0.015),
              "alu_cast"))                                          # rr34 m1: a broad flat arm (20 mm) to the clevis
    m.add(_master_cylinder(pin))
    # return spring from the lever's tab down to the bracket's rear edge (RIGHT px (1654,1522) to (1697,1547))
    # (round 3: outside the frame's lower section, which now reaches under it; hooked on the footpeg pad's face)
    sa, sb = _px("right", 1654, 1522, "y", -0.1425), _px("right", 1697.5, 1546.6, "y", -0.1425)
    m.add(coil(sa, sb, 0.0045, 0.0008, 13, "steel", seg=6, dead=0, per=12))
    m.add(tube([sa, (lever_mid[0] - 0.004, -0.1440, lever_mid[2] - 0.006)], 0.0008, 6, "steel"))
    m.add(tube([sb, (0.5425, -0.1420, 0.3895)], 0.0008, 6, "steel"))
    return m


PARTS = {"frame": frame, "subframe": subframe, "swingarm": swingarm, "rear_axle": rear_axle, "chain_guide": chain_guide,
         "linkage": linkage,
         "shock": shock, "exhaust": exhaust, "footpegs": footpegs, "brake_pedal": rear_brake}   # (named "rear_brake" it was
#   replaced by detail_wheels.py's caliper, loaded later: the pedal and master cylinder were missing from the bike)
SMOOTH = {"footpegs": 30, "frame": 42}
BEVEL = {"swingarm": 0.0004,          # its edges are modelled (rounded rims, chamfers); build_bike's 3 mm bevel ate them
         "frame": 0.0001}             # so are the frame's (round 3: the casting's edges and features are modelled; a
#                                       0.5 mm bevel at build_bike's 40 deg limit tore the 1 mm triangles of its fillets)
