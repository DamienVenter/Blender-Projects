"""Engine, cooling and fuel in detail (plugin of parts.py; replaces its engine, radiators and tank).

Sources of the numbers (tags in the comments):
  LEFT / RIGHT   Honda's profile photos, read on gridded crops (pxgrid.py left 1560 900 2280 1670 and
                 right 1720 900 2440 1670, 1500 px wide): crop (X, Y) -> photo pixel u = u0 + 0.48 X, v = 900 + 0.48 Y,
                 then cams.CAMS[view].on_plane at the part's lateral position. _L and _R do this.
  LEFT/RIGHT cols  rowscan.py class runs along photo columns (head cover edges)
  FRONT / TOP    rowscan.py runs of the front and top photos
  SPEC           research/crf250r-2026.md
  MODEL          the neighbouring parts as built (frame of detail_chassis.py, drive of detail_wheels.py, shroud decks,
                 seat): the engine's estimated widths and hidden parts yield to them, 2 mm clear
  EST            not visible in any photo: the real part's usual size
Lateral positions of everything on the engine are EST (no photo shows the engine's width): cases +-78 mm, covers to
+131 / -129 mm, kept inside the frame's plates (inner faces at +-111 mm).
Parts that touch a neighbour stop 0.3 mm short of it; hoses slide over their spigots without touching them.
"""
import math

import numpy as np
from scipy.spatial import cKDTree

import cams
import detail_chassis as chassis
import plastics
from geom import Mesh, bolt, box, grid, inside, plate2d, resample, rot_z, rounded_rect, smooth_poly, tube
from parts import BACK, CS, PIVOT, STEER0, T_TOP_CLAMP, UP, chain_top

REPLACES = ["engine", "radiators", "tank"]


# ------------------------------------------------------------------ photo readings -> world
def _L(X, Y, y):
    return cams.CAMS["left"].on_plane(1560 + 0.48 * X, 900 + 0.48 * Y, "y", y)[0]


def _R(X, Y, y):
    return cams.CAMS["right"].on_plane(1720 + 0.48 * X, 900 + 0.48 * Y, "y", y)[0]


def _xz(fn, pts, y):
    return np.array([fn(X, Y, y)[[0, 2]] for X, Y in pts])


def _p(fn, X, Y, y):
    """World point of a crop reading, on the plane y."""
    q = fn(X, Y, y)
    return np.array([q[0], y, q[2]])


# ------------------------------------------------------------------ small mesh helpers
def turned(c, axis, prof, mat, seg=24, cap0=True, cap1=True):
    """Lathe about AXIS through C: prof = [(radius, height along the axis), ...]."""
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    h = np.array([0.0, 0.0, 1.0]) if abs(a[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(h, a)
    u /= np.linalg.norm(u)
    v = np.cross(a, u)
    ang = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    c = np.asarray(c, float)
    rings = [c + a * z + r * (np.outer(np.cos(ang), u) + np.outer(np.sin(ang), v)) for r, z in prof]
    return grid(Mesh(), rings, mat, cap0=cap0, cap1=cap1)


def rcyl(c, axis, R, H, mat, rr=0.003, seg=28, sink=0.003, n=4):
    """Boss or cap: a cylinder standing H along AXIS from C (sunk SINK into what it stands on), top edge rounded RR,
    its top face in rings 6 mm apart."""
    rr = min(rr, 0.9 * R, 0.9 * H)
    prof = [(R, -sink), (R, H - rr)]
    for k in range(1, n + 1):
        t = k / n * math.pi / 2
        prof.append((R - rr + rr * math.cos(t), H - rr + rr * math.sin(t)))
    r = R - rr
    while r > 0.007:
        r -= 0.006
        prof.append((max(r, 0.002), H))
    return turned(c, axis, prof, mat, seg)


def _smooth(poly, step=0.004, k=5):
    return smooth_poly(resample(np.asarray(poly, float), step), k)


def _inset(P, d):
    t = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)
    n = np.stack([-t[:, 1], t[:, 0]], axis=1)
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return P + d * (n if area > 0 else -n)


def slab(poly, y0, y1, mat, rr=0.003, step=0.005, k=5):
    """Casting with a convex side outline (x, z) between y0 and y1, its edges rounded RR; faces meshed in rings."""
    P = _smooth(poly, step, k)
    s = 1.0 if y1 > y0 else -1.0
    c = P.mean(axis=0)

    def ring(Q, y):
        return np.column_stack([Q[:, 0], np.full(len(Q), y), Q[:, 1]])
    inner = _inset(P, rr)
    nl = max(int(np.abs(inner - c).max() / 0.007), 1)
    fs = [(i + 1) / (nl + 1) for i in range(nl)]
    rings = [ring(c + (inner - c) * f, y0) for f in fs]
    rings += [ring(inner, y0), ring(_inset(P, 0.3 * rr), y0 + s * 0.3 * rr)]
    ny = max(int((abs(y1 - y0) - 2 * rr) / 0.007), 1)
    rings += [ring(P, y) for y in np.linspace(y0 + s * rr, y1 - s * rr, ny + 1)]
    rings += [ring(_inset(P, 0.3 * rr), y1 - s * 0.3 * rr), ring(inner, y1)]
    rings += [ring(c + (inner - c) * f, y1) for f in fs[::-1]]
    return grid(Mesh(), rings, mat, cap0=True, cap1=True)


def dome(outline, y0, side, wall, height, rr, mat, step=0.006, back=0.003, hfn=None):
    """Cast cover: side outline (x, z) standing on the plane y0, an upright wall WALL high, then a shoulder of radius
    RR up to HEIGHT (a function of the distance to the outline, so the shoulder follows the edge exactly).
    hfn(x, z): the face's height where it is not uniform (the wall follows)."""
    O = _smooth(outline, 0.004, 4)
    tree = cKDTree(resample(O, 0.0004))
    sh = height - wall

    def to3d(u, v, w):
        if w < 0:
            return (u, y0 - side * back, v)
        t = min(tree.query((u, v))[0] / rr, 1.0)
        H = height if hfn is None else hfn(u, v)
        return (u, y0 + side * (H - sh + sh * math.sqrt(1.0 - (1.0 - t) ** 2)), v)
    return plate2d(O, [], 1.0, mat, to3d, step=step, rings=(0.12 * rr, 0.35 * rr, 0.65 * rr, rr))


def flat(outline, y0, y1, mat, holes=(), step=0.006):
    yc, t = (y0 + y1) / 2, abs(y1 - y0)
    return plate2d(np.asarray(outline, float), [np.asarray(h, float) for h in holes], t, mat,
                   lambda u, v, w: (u, yc + w, v), step=step)


def hose(pts, r, mat, seg=12, n=None, caps=(False, False)):
    """Tube along the polyline PTS, its corners rounded (no spline: it stays where the points put it). Ends that sit
    over a spigot are left open."""
    P = np.asarray(pts, float)
    t = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    n = n or max(int(t[-1] / 0.006), 6)
    Q = np.stack([np.interp(np.linspace(0, t[-1], n), t, P[:, i]) for i in range(3)], axis=1)
    for _ in range(3):
        Q[1:-1] = (Q[:-2] + 2 * Q[1:-1] + Q[2:]) / 4
    return tube(Q, r, seg, mat, cap0=caps[0], cap1=caps[1])


def rbox(size, r, mat, R=None, t=None, n=3):
    """Box (d, w, h) with the four edges along w rounded R and its ends chamfered, in rings 7 mm apart along w."""
    d, w, h = size
    loop = rounded_rect(d, h, r, n)
    c = min(0.6 * r, w / 4)
    k = 1.0 - 1.2 * c / max(min(d, h), 1e-6)
    ws = np.linspace(-w / 2 + c, w / 2 - c, max(int(w / 0.007), 1) + 1)
    rings = [np.column_stack([loop[:, 0] * s, np.full(len(loop), ww), loop[:, 1] * s])
             for ww, s in [(-w / 2, k)] + [(q, 1.0) for q in ws] + [(w / 2, k)]]
    return grid(Mesh(), rings, mat, cap0=True, cap1=True).transform(R, t)


def sbox(center, size, mat, R, axis, step=0.006):
    """Box in sections STEP apart along its local AXIS."""
    d = np.asarray(size, float) / 2
    o = [i for i in range(3) if i != axis]
    rings = []
    for t in np.linspace(-d[axis], d[axis], max(int(size[axis] / step), 1) + 1):
        loop = np.zeros((4, 3))
        for j, (a, b) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            loop[j, o[0]], loop[j, o[1]], loop[j, axis] = a * d[o[0]], b * d[o[1]], t
        rings.append(loop @ np.asarray(R, float).T + np.asarray(center, float))
    return grid(Mesh(), rings, mat, cap0=True, cap1=True)


def oriented(m):
    """Wind the faces of every piece outward: audit.py measures how deep a clash goes along the face normals, and
    viewers cull back faces. Faces joined by an edge are made consistent, then the piece is turned so that its volume
    about its own centroid is positive."""
    V = np.asarray(m.V, float)
    # geom.plate2d leaves zero-area triangles between collinear points of a straight edge: drop them first
    keep = [i for i, f in enumerate(m.F)
            if max(np.linalg.norm(np.cross(V[f[k]] - V[f[0]], V[f[k + 1]] - V[f[0]])) for k in range(1, len(f) - 1)) > 1e-12]
    m.F, m.M = [m.F[i] for i in keep], [m.M[i] for i in keep]
    F = m.F
    emap = {}
    for fi, f in enumerate(F):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            emap.setdefault((a, b) if a < b else (b, a), []).append((fi, a < b))
    nb = [[] for _ in F]
    for lst in emap.values():
        if len(lst) == 2:
            (f1, d1), (f2, d2) = lst
            nb[f1].append((f2, d1 == d2))
            nb[f2].append((f1, d1 == d2))
    flip = [False] * len(F)
    seen = [False] * len(F)
    for s in range(len(F)):
        if seen[s]:
            continue
        comp, i = [s], 0
        seen[s] = True
        while i < len(comp):
            f = comp[i]
            i += 1
            for g, same in nb[f]:
                if not seen[g]:
                    seen[g] = True
                    flip[g] = flip[f] ^ same
                    comp.append(g)
        c = V[sorted({v for f in comp for v in F[f]})].mean(axis=0)
        vol = 0.0
        for f in comp:
            p = V[list(F[f])] - c
            v = sum(float(p[0] @ np.cross(p[k], p[k + 1])) for k in range(1, len(p) - 1))
            vol += -v if flip[f] else v
        if vol < 0:
            for f in comp:
                flip[f] = not flip[f]
    m.F = [tuple(f[::-1]) if fl else f for f, fl in zip(F, flip)]
    return m


YP, YM = np.array([0.0, 1.0, 0.0]), np.array([0.0, -1.0, 0.0])

# ------------------------------------------------------------------ the frame beside the engine (MODEL)
T_FR = chassis.T_SPAR
FRAME_OUT = chassis._frame_outline()       # the plate's side outline (x, z); 26 mm deep, inner face at frame_in(x)
_FRAME_EDGE = cKDTree(resample(FRAME_OUT, 0.002))
_BRACKET = chassis._bracket_outline()
PIVOT_BOSS_R = 0.026                       # detail_chassis.frame: the boss round the pivot on the plate
# detail_chassis.frame's cradle rail: a bar 22 mm wide and 24 mm deep swept with geom.tube through these 30 stations
# (copied: the path is not exported there)
RAIL = chassis.spline([(0.922, 0.012, 0.490), (0.9145, 0.022, 0.452), (0.905, 0.038, 0.415), (0.880, 0.056, 0.392),
                       (0.831, 0.066, 0.382), (0.776, 0.070, 0.3555), (0.735, 0.073, 0.355), (0.690, 0.076, 0.355),
                       (0.620, 0.092, 0.358), (0.585, 0.112, 0.368)], 30)
RAIL_W, RAIL_H = 0.011, 0.012


def _bar_frame(P):
    """Section axes of geom.tube along P: sideways and across (the bar's faces lie along them)."""
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    n0 = np.cross(T[0], [0, 0, 1.0]) if abs(T[0][2]) < 0.95 else np.cross(T[0], [1.0, 0, 0])
    N = [n0 / np.linalg.norm(n0)]
    for i in range(1, len(P)):
        v = N[-1] - (N[-1] @ T[i]) * T[i]
        N.append(v / np.linalg.norm(v))
    N = np.array(N)
    return N, np.cross(T, N)


_RN, _RB = _bar_frame(RAIL)
RAIL_LAT = _RN * np.sign(_RN[:, 1:2])      # outward on the left rail
RAIL_DN = _RB * -np.sign(_RB[:, 2:3])      # downward
_RTOP = RAIL - RAIL_H * RAIL_DN            # middle of the bar's top face
_RO, _RT = np.argsort(RAIL[:, 0]), np.argsort(_RTOP[:, 0])


def frame_in(x):
    """Inner face (|y|) of the frame's plate at x."""
    return chassis._spar_y(x) - T_FR


def under_frame(x, z, margin=0.002):
    """True where the frame's plate (photo outline, pivot boss, footpeg bracket) stands beside the point (x, z)."""
    q = np.array([[x, z]])
    return bool(math.hypot(x - PIVOT[0], z - PIVOT[2]) < PIVOT_BOSS_R + margin or inside(FRAME_OUT, q)[0]
                or inside(_BRACKET, q)[0] or _FRAME_EDGE.query((x, z))[0] < margin)


def frame_gap(x, z):
    """Distance in the side view from a point ahead of the frame's plate to its outline and pivot boss."""
    return min(float(_FRAME_EDGE.query((x, z))[0]), math.hypot(x - PIVOT[0], z - PIVOT[2]) - PIVOT_BOSS_R)


def rail_at(x):
    """(y of the rail's axis, z of its axis, z of its top face) at x."""
    return (float(np.interp(x, RAIL[_RO, 0], RAIL[_RO, 1])), float(np.interp(x, RAIL[_RO, 0], RAIL[_RO, 2])),
            float(np.interp(x, _RTOP[_RT, 0], _RTOP[_RT, 2])))


def rail_top(x, y):
    """z of the rail's top face at x under the lateral position |y| (the face leans a little with the bar's roll)."""
    q = _RTOP + RAIL_LAT * (abs(y) - RAIL[:, 1:2])
    o = np.argsort(q[:, 0])
    return float(np.interp(x, q[o, 0], q[o, 2]))


def above_rail(xz, gap=0.006):
    """Side outline (x, z) lifted where it would dip onto the cradle rail (MODEL: the frame is measured)."""
    xz = np.array(xz, float)
    for q in xz:
        if 0.62 < q[0] < 0.90:
            q[1] = max(q[1], rail_at(q[0])[2] + gap)
    return xz


# ------------------------------------------------------------------ engine layout
YL, YR = 0.078, -0.078                     # EST: gasket faces of the left and right crankcase covers
CRANK = _L(897, 1167, 0.125)               # LEFT: hex-socket cap on the crankshaft's end (px 1990.6, 1460.2)
O = CRANK[[0, 2]]
LEAN = math.radians(14.0)                  # LEFT/RIGHT cols: head cover edges slope 15 deg; the head sits centred
#                                            on a 14 deg axis through the crank (SPEC says 9 deg: see the report)
AX, PP = np.array([math.sin(LEAN), math.cos(LEAN)]), np.array([math.cos(LEAN), -math.sin(LEAN)])
AX3, PP3 = np.array([AX[0], 0.0, AX[1]]), np.array([PP[0], 0.0, PP[1]])
BORE, TB_BORE = 0.079, 0.044               # SPEC


def _hs(q):
    """(height along the cylinder axis, offset toward the front) of a world point (x, y, z) or (x, z)."""
    q = np.asarray(q, float)
    d = (q[[0, 2]] if len(q) == 3 else q) - O
    return float(d @ AX), float(d @ PP)


def _a(h, s, y=None):
    q = O + h * AX + s * PP
    return q if y is None else np.array([q[0], y, q[1]])


H_BASE = _hs(_L(850, 930, 0.07))[0]                                       # LEFT: cylinder foot
H_HEAD = _hs(_L(850, 735, 0.07))[0]                                       # LEFT: cylinder / head joint
H_COVER = _hs(cams.CAMS["left"].on_plane(1920.0, 1137.0, "y", 0.07)[0])[0]   # LEFT cols 1880..1980: cover's lower edge
H_TOP = H_COVER + 0.052                                                   # LEFT cols: black to +0.061 with the cap
S_RB = _hs(_L(975, 925, 0.07))[1]                                         # LEFT: rear edges, foot to cover
S_RC = _hs(_L(965, 800, 0.07))[1]
S_RV = _hs(_L(930, 420, 0.07))[1]
S_FH = _hs(_R(960, 600, -0.06))[1]                                        # RIGHT: head's front edge
S_FV = _hs(_R(960, 440, -0.06))[1]                                        # RIGHT: cover's front edge
S_FC = S_FH - 0.012                                                       # EST: cylinder front (behind the hoses)
CYL_Y, HEAD_Y, COVER_Y = (-0.058, 0.068), (-0.062, 0.070), (-0.064, 0.072)   # EST: bore 79 + jackets; chain left
H_PORT = H_HEAD + 0.40 * (H_COVER - H_HEAD)                               # EST: exhaust port height on the head
# Mating face of the exhaust port (centre) and the header's direction. MODEL: the frame's down tube stands 30 mm
# ahead of the head on the centre line, so the port leaves 30 mm to its right and its stub is 30 mm long:
# detail_chassis.py's header starts here (its first ring: HEADER[0]). The stub's face stops 0.3 mm short of this
# point; the pipe's end stands in the stub's bore.
PORT = np.array([0.9125, -0.030, 0.6106])
PORT_DIR = np.array([0.970, 0.0, -0.242]) / math.hypot(0.970, 0.242)

L_COVER = [(790, 950), (850, 925), (905, 890), (960, 875), (995, 830), (1060, 818), (1150, 822), (1178, 850),
           (1170, 890), (1140, 910), (1132, 1000), (1128, 1085), (1100, 1125), (1092, 1180), (1065, 1250),
           (1040, 1300), (1000, 1335), (945, 1378), (880, 1372), (800, 1335), (745, 1270), (705, 1190), (698, 1120),
           (702, 1050), (730, 990)]                                       # LEFT: left crankcase cover
L_COVER_BOLTS = [(1007, 843), (1147, 843), (810, 955), (718, 1052), (712, 1127), (787, 1300), (940, 1362),
                 (1072, 1125)]                                            # LEFT: 8 bolts counted
L_CASE_BOLTS = [(693, 962), (625, 1128)]                                  # LEFT: case bolts ahead of the cover
R_COVER = [(185, 905), (235, 855), (300, 832), (400, 812), (470, 845), (560, 890), (625, 935), (700, 945),
           (770, 940), (850, 975), (905, 1040), (915, 1110), (880, 1185), (830, 1225), (800, 1260), (795, 1320),
           (760, 1345), (690, 1345), (600, 1362), (480, 1350), (370, 1305), (260, 1262), (185, 1185), (150, 1110),
           (160, 1010)]                                                   # RIGHT: right crankcase cover
CLUTCH_BOLTS = [(400, 828), (228, 893), (590, 943), (170, 1112), (562, 1212), (372, 1282)]   # RIGHT: 6 counted
PUMP_BOLTS = [(765, 968), (900, 1055), (700, 1132), (840, 1190)]          # RIGHT: 4 counted
FILTER_BOLTS = [(625, 1222), (782, 1252)]                                 # RIGHT: 2 counted
R_COVER_BOLTS = [(765, 1325), (590, 1360)]                                # RIGHT: seen under the header pipe
CASE = [(650, 935), (600, 940), (578, 965), (585, 1000), (592, 1060), (600, 1120), (625, 1180), (665, 1250),
        (710, 1310), (760, 1350), (830, 1378), (930, 1390), (1050, 1392), (1150, 1385), (1250, 1370), (1320, 1330),
        (1345, 1260), (1345, 1100), (1330, 1010), (1290, 950), (1230, 900), (1180, 860), (1100, 835), (1000, 838),
        (985, 925)]                                                       # LEFT: crankcase (rear and deck EST)
# MODEL: the 13T sprocket and the chain of detail_wheels.py run in a pocket of the left half
POCKET_R = 0.047                           # chain on the sprocket reaches 41.7 mm from the shaft; 5 mm clear
POCKET_Y = CS[1] - 0.020 - 0.0003          # the drive's shaft end starts 20 mm inboard of the chain line
CHAIN_HALF = 0.0105                        # MODEL: half width of the chain over its pins
SHIFT = np.array([0.609, 0.0, 0.403])      # EST: shift shaft, under the chain's lower run and ahead of the peg bracket
SHIFT_TIP = _L(1020, 1305, 0.16)           # LEFT: the folding tip, end-on


def case_face(x, z, left):
    """Half width of the crankcase at (x, z): 78 mm (EST), less where the frame's cradle rails pass under its flanks
    and, on the left, in the pocket of the sprocket and of the two chain runs (MODEL)."""
    H = 0.078
    if 0.60 < x < 0.90:
        yr, zr, top = rail_at(x)
        lim, z0 = yr - RAIL_W - 0.0035, top + 0.003
        if z < z0 + 0.009:
            t = max((z - z0) / 0.009, 0.0)
            H = min(H, lim + (H - lim) * t * t * (3 - 2 * t))
    if left:
        d = math.hypot(x - CS[0], z - CS[2]) - POCKET_R
        if x < CS[0]:                      # top run (parts.chain_top) and lower run (LEFT: from (0.604, 0.428))
            d = min(d, abs(z - float(chain_top(x))) - 0.014, abs(z - (0.428 + 0.3649 * (x - 0.604))) - 0.014)
        t = min(max(d / 0.006, 0.0), 1.0)
        H = min(H, POCKET_Y + (0.078 - POCKET_Y) * t * t * (3 - 2 * t))
    return H


def _cases(m):
    out = _xz(_L, CASE, YL)
    for side in (1, -1):                                   # two halves, split on the centre line
        m.add(dome(out, 0.0, side, 0.072, 0.078, 0.006, "engine_case", step=0.005, back=0.001,
                   hfn=lambda u, v, s=side: case_face(u, v, s > 0)))
    # front mount: lug between the two hanger plates, which sit on the down tube's sides (LEFT 605, 968)
    e1 = _L(605, 968, 0.03)
    m.add(rcyl((e1[0], -0.0222, e1[2]), YP, 0.014, 0.0444, "engine_case", sink=0.0))
    fb = [_L(520, 885, 0.03), _L(530, 955, 0.03)]          # LEFT: the plate's two bolts on the frame's tabs
    rear = _xz(_L, [(545, 868), (625, 950), (628, 985), (600, 1000), (520, 985)], 0.03)
    plate = np.vstack([[(0.938, rear[0, 1] + 0.004)], rear, [(0.938, rear[-1, 1] - 0.002)]])
    for side in (1, -1):                                   # MODEL: the down tube is 44 mm wide: 0.3 mm from its side
        m.add(flat(plate, side * 0.0223, side * 0.0283, "alu_cast", step=0.005))
        ax = YP * side
        m.add(bolt((e1[0], side * 0.0283, e1[2]), ax, af=0.012))                   # M10 head / nut
        for q in fb:
            m.add(bolt((q[0], side * 0.0283, q[2]), ax, af=0.010))                 # M8
    # lower mount: through bolt, and a tab on each side standing on the cradle rail (LEFT 826, 1345 = RIGHT 670, 1350)
    m2 = _L(826, 1345, 0.085)
    yi = rail_at(m2[0])[0] - RAIL_W - 0.004                # the boss ends inside the rails; a slim sleeve passes over
    m.add(rcyl((m2[0], -yi, m2[2]), YP, 0.013, 2 * yi, "engine_case", sink=0.0))
    m.add(hose([(m2[0], -0.0785, m2[2]), (m2[0], 0.0785, m2[2])], 0.0072, "steel", seg=12, n=28, caps=(True, True)))
    foot = [(x, max(rail_top(x, 0.0725), rail_top(x, 0.0785)) + 0.0006) for x in np.linspace(m2[0] - 0.016, m2[0] + 0.016, 5)]
    lug = np.array(foot + [(m2[0] + 0.011, m2[2] + 0.012), (m2[0] - 0.011, m2[2] + 0.012)])
    for side in (1, -1):
        m.add(flat(lug, side * 0.0725, side * 0.0785, "alu_cast", step=0.004))
        m.add(bolt((m2[0], side * 0.0785, m2[2]), YP * side, af=0.012, flange_d=0.0135))   # plain hex: clears the rail
    # drain bolt under the cases beside the seam (EST position; M12 on its boss)
    zb = _L(930, 1390, YL)[2] + 0.004                      # the smoothed outline sits a little inside the reading
    m.add(rcyl((O[0] + 0.020, 0.006, zb + 0.004), (0, 0, -1), 0.011, 0.009, "engine_case", rr=0.002, sink=0.0))
    m.add(bolt((O[0] + 0.020, 0.006, zb - 0.005), (0, 0, -1), af=0.012))
    # round boss on the left half ahead of the cover (LEFT 693, 1175) and the case bolts beside the cover
    q = _L(693, 1175, YL)
    m.add(rcyl((q[0], YL + 0.0005, q[2]), YP, 0.016, 0.008, "engine_case", rr=0.004, sink=0.0))
    for X, Y in L_CASE_BOLTS:
        q = _L(X, Y, YL)
        m.add(rcyl((q[0], YL, q[2]), YP, 0.008, 0.004, "engine_case", rr=0.001))
        m.add(bolt((q[0], YL + 0.004, q[2]), YP))
    # shift shaft boss at the lower rear corner
    m.add(rcyl((SHIFT[0], 0.030, SHIFT[2]), YP, 0.012, 0.056, "engine_case", sink=0.0))


GUARD_Y = (CS[1] + CHAIN_HALF + 0.0025, CS[1] + CHAIN_HALF + 0.006)       # MODEL: 2.5 mm outside the chain
ARM_END = _p(_L, 1222, 905, 0.116)         # LEFT 1222, 905: end of the clutch release arm
CABLE_HOLD = _p(_L, 1160, 890, 0.114) + np.array([0.0, 0.0, 0.0035])   # LEFT 1150..1160, 890: the cable's last guide, 4 mm over the arm (EST lift)
_NIP = ARM_END + np.array([0.0, 0.0, 0.009])               # the nipple stands on the arm's end (r 4.2 mm)
CLUTCH_ARM_END = _NIP + 0.0054 * (CABLE_HOLD - _NIP) / np.linalg.norm(CABLE_HOLD - _NIP)   # the clutch cable ends here, 1.2 mm off the nipple, coming from CABLE_HOLD


# Route of the clutch cable on the engine (EST), from the tank's left edge (detail_front.py's CLUTCH_JOIN) to
# CABLE_HOLD: down the left of the head ahead of the hanger, outside the temperature sender, back along the top
# edge of the left cover over the idle gear's boss, then down over the cover's bolt. Checked clear of this module's
# parts as a 3 mm cable splined through these points and on to CLUTCH_ARM_END.
CLUTCH_CABLE = [(0.790, 0.074, 0.800), (0.768, 0.080, 0.770), (0.753, 0.090, 0.720), (0.748, 0.093, 0.667),
                (0.746, 0.096, 0.630), (0.736, 0.103, 0.598), (0.708, 0.109, 0.587), (0.684, 0.1170, 0.582),
                (0.6715, 0.1215, 0.5745), (0.6660, 0.1185, 0.5640), tuple(CABLE_HOLD)]


def _left_cover(m):
    m.add(dome(above_rail(_xz(_L, L_COVER, 0.10)), YL, 1, 0.022, 0.030, 0.008, "engine_cover"))   # face at y 0.108
    m.add(rcyl((O[0], 0.106, O[1]), YP, 0.058, 0.020, "engine_cover", rr=0.012, seg=56, sink=0.0, n=6))
    #        ^ generator bulge: LEFT radius 150 crop px = 56..58 mm about the crank
    m.add(turned((O[0], 0.126, O[1]), YP, [(0.0206, -0.001), (0.0206, 0.004), (0.0188, 0.0055), (0.0125, 0.0055),
                                           (0.0065, 0.0055), (0.0058, 0.0015)], "alu_machined", 32))   # crank cap
    for (X, Y), r, h in (((1095, 870), 0.0135, 0.012), ((1030, 955), 0.009, 0.008)):       # LEFT: idle gear bosses
        q = _L(X, Y, 0.11)
        m.add(rcyl((q[0], 0.106, q[2]), YP, r, h, "engine_cover", rr=0.004))
    q = _L(770, 1195, 0.11)                                                               # LEFT: boss + 12 mm bolt
    m.add(rcyl((q[0], 0.104, q[2]), YP, 0.014, 0.008, "engine_cover", rr=0.003))
    m.add(bolt((q[0], 0.112, q[2]), YP, af=0.012))
    for X, Y in L_COVER_BOLTS:
        q = _L(X, Y, 0.11)
        m.add(rcyl((q[0], YL, q[2]), YP, 0.008, 0.032, "engine_cover", rr=0.0015, sink=0.0))
        m.add(bolt((q[0], YL + 0.032, q[2]), YP))
    # clutch release shaft in its boss, arm on top, cable nipple (LEFT 1095..1107, 920..1085; arm to 1222, 905)
    b0, b1 = _p(_L, 1095, 1085, 0.110), _p(_L, 1107, 920, 0.110)
    m.add(hose([b0, b1], 0.0085, "engine_cover", seg=16, caps=(True, True)))
    top, end = _p(_L, 1107, 913, 0.110), ARM_END
    m.add(tube([b1 - (b1 - b0) * 0.02, top + (top - b0) * 0.03], 0.005, 12, "steel"))
    m.add(hose([top, end], [(0.0075, 0.0025)] * 8, "steel", seg=12, n=8, caps=(True, True)))   # flat lever
    m.add(rcyl(_NIP - np.array([0, 0, 0.007]), (0, 0, 1), 0.0042, 0.012, "steel", rr=0.001, seg=12, sink=0.0))
    # (the cable of detail_front.py passes CABLE_HOLD 1.5 mm over the cover and runs on over the arm to the nipple)
    # countershaft sprocket guard (black plastic, two openings) outside the chain, on two stand-offs clear of it
    g = _xz(_L, [(1135, 962), (1200, 940), (1290, 950), (1368, 978), (1372, 1040), (1340, 1075), (1300, 1085),
                 (1250, 1075), (1200, 1090), (1160, 1120), (1135, 1100), (1125, 1020)], 0.103)
    holes = [_xz(_L, [(1218, 992), (1280, 992), (1250, 1040)], 0.103),
             _xz(_L, [(1300, 1005), (1348, 1012), (1318, 1050)], 0.103)]
    m.add(flat(_smooth(g, 0.004, 2), GUARD_Y[0], GUARD_Y[1], "plastic_black", [_smooth(h, 0.003, 2) for h in holes],
               0.005))
    for X, Y in ((1200, 958), (1285, 968)):
        q = _L(X, Y, 0.10)
        y0 = case_face(q[0], q[2], True)
        m.add(rcyl((q[0], y0, q[2]), YP, 0.006, GUARD_Y[0] - y0 + 0.001, "engine_case", rr=0.001, seg=12, sink=0.002))
        m.add(bolt((q[0], GUARD_Y[1], q[2]), YP, head_h=0.004))


def _shift(m):
    s, tip = SHIFT, SHIFT_TIP
    m.add(hose([(s[0], 0.082, s[2]), (s[0], 0.150, s[2])], 0.0065, "steel", seg=12, caps=(True, True)))
    m.add(rcyl((s[0], 0.134, s[2]), YP, 0.011, 0.014, "steel", rr=0.002, seg=20, sink=0.0))            # clamp
    m.add(bolt((s[0] - 0.006, 0.141, s[2] + 0.010), (0, 0, 1), af=0.008))                              # pinch bolt
    arm = [(s[0], 0.141, s[2]), (s[0] + 0.040, 0.142, s[2] + 0.001), (tip[0] - 0.022, 0.142, tip[2] + 0.001),
           (tip[0] - 0.004, 0.142, tip[2])]
    m.add(hose(arm, [(0.0045, 0.008)] * 20, "steel", seg=12, n=20, caps=(True, True)))
    m.add(rcyl((tip[0] - 0.004, 0.137, tip[2]), YP, 0.007, 0.012, "steel", rr=0.002, seg=16, sink=0.0))  # hinge
    m.add(turned((tip[0], 0.139, tip[2]), YP, [(0.0072, 0.0), (0.0078, 0.004), (0.0072, 0.008), (0.0078, 0.014),
                                                (0.0072, 0.020), (0.0078, 0.028), (0.0072, 0.036),
                                                (0.0075, 0.046), (0.0055, 0.048), (0.0030, 0.046)], "steel", 16))


YRF = YR - 0.027                           # right cover's face (EST): 2 mm inside the frame plate's inner face
_CL = _R(395, 1065, -0.12)                 # RIGHT: clutch cover's centre, radius 215 crop px = 79 mm;
CLUTCH_R = min(0.079, frame_gap(_CL[0], _CL[2]) - 0.002)   # MODEL: never closer than 2 mm to the frame's plate
PUMP_PIPE = np.array([_p(_R, 815, 1085, -0.119), _p(_R, 812, 1000, -0.115), _p(_R, 825, 930, -0.105),
                      _p(_R, 850, 890, -0.097)])


PUMP_DIR = (PUMP_PIPE[3] - PUMP_PIPE[2]) / np.linalg.norm(PUMP_PIPE[3] - PUMP_PIPE[2])


def _right_cover(m):
    m.add(dome(above_rail(_xz(_R, R_COVER, -0.10)), YR, -1, 0.019, 0.027, 0.008, "engine_cover"))   # face at -0.105
    yb = YRF + 0.002
    c = _R(395, 1065, -0.12)                               # RIGHT: clutch cover
    m.add(rcyl((c[0], yb, c[2]), YM, CLUTCH_R, 0.026, "engine_cover", rr=0.014, seg=72, sink=0.0, n=6))
    m.add(rcyl((c[0], yb - 0.026, c[2]), YM, 0.047, 0.0014, "engine_cover", rr=0.0008, seg=72, sink=0.002, n=2))
    #        ^ the cover's raised centre panel (EST height)
    for X, Y in CLUTCH_BOLTS:                              # ears; the one beside the frame's pivot boss stays low
        q = _R(X, Y, -0.12)
        low = under_frame(q[0], q[2], 0.012)
        h = 0.0008 if low else 0.012
        m.add(rcyl((q[0], yb, q[2]), YM, 0.009, h, "engine_cover", rr=0.002, seg=16))
        m.add(bolt((q[0], yb - h, q[2]), YM, head_h=0.0045 if low else 0.0055))
    c = _R(800, 1085, -0.12)                               # RIGHT: water pump cover, 4 bolts
    m.add(rcyl((c[0], yb, c[2]), YM, 0.034, 0.018, "engine_cover", rr=0.008, seg=40, sink=0.0))
    for X, Y in PUMP_BOLTS:
        q = _R(X, Y, -0.12)
        m.add(rcyl((q[0], yb + 0.002, q[2]), YM, 0.008, 0.010, "engine_cover", rr=0.002, seg=16))
        m.add(bolt((q[0], yb - 0.008, q[2]), YM))
    m.add(hose(PUMP_PIPE, 0.0105, "engine_cover", seg=14, caps=(True, True)))   # RIGHT: cast pipe up from the pump
    m.add(rcyl(PUMP_PIPE[-1] - 0.004 * PUMP_DIR, PUMP_DIR, 0.0118, 0.004, "engine_cover", rr=0.001, seg=14, sink=0.0))
    c = _R(695, 1250, -0.12)                               # RIGHT: oil filter cover, 2 bolts
    m.add(rcyl((c[0], yb, c[2]), YM, 0.022, 0.008, "engine_cover", rr=0.004, seg=32))
    m.add(rcyl((c[0], yb - 0.008, c[2]), YM, 0.007, 0.003, "engine_cover", rr=0.001, seg=16, sink=0.001))
    for X, Y in FILTER_BOLTS:
        q = _R(X, Y, -0.12)
        m.add(rcyl((q[0], yb + 0.002, q[2]), YM, 0.007, 0.007, "engine_cover", rr=0.0015, seg=14))
        m.add(bolt((q[0], yb - 0.005, q[2]), YM))
    for X, Y in R_COVER_BOLTS:
        q = _R(X, Y, -0.12)
        q[2] = max(q[2], rail_at(q[0])[2] + 0.013)         # the boss stays above the cradle rail
        m.add(rcyl((q[0], YR, q[2]), YM, 0.008, 0.029, "engine_cover", rr=0.0015, sink=0.0))
        m.add(bolt((q[0], YR - 0.029, q[2]), YM))
    # oil filler cap on its boss, ahead of the clutch cover (RIGHT 680, 880..930)
    af = np.array([0.0, -0.6, 0.8])
    c = _p(_R, 680, 922, -0.097)
    m.add(rcyl(c - 0.030 * af, af, 0.012, 0.032, "engine_cover", rr=0.002, seg=20, sink=0.0))
    m.add(turned(c + 0.002 * af, af, [(0.0145, 0.0), (0.0145, 0.007), (0.012, 0.009), (0.0085, 0.009),
                                      (0.0085, 0.015), (0.0065, 0.016)], "plastic_black", 20))


def _hanger(m, fn, side, outline, head, bolts):
    """Head hanger of one side: plate seated on the inner face of the frame's plate (0.4 mm off it), the head's lug
    and boss out to it, bolt heads outside where the frame does not cover them, nuts inside where it does."""
    hp = _smooth(_xz(fn, outline, side * 0.095), 0.004, 2)
    m.add(plate2d(hp, [], 0.006, "alu_cast", lambda u, v, w: (u, side * (frame_in(u) - 0.0034 + w), v), step=0.005))
    ax = YP * side

    def stud(q, af):
        yo = frame_in(q[0]) - 0.0004
        if under_frame(q[0], q[2], 0.010):
            m.add(bolt((q[0], side * (yo - 0.006), q[2]), -ax, af=af))
        else:
            m.add(bolt((q[0], side * yo, q[2]), ax, af=af))
    q = fn(head[0], head[1], side * 0.08)
    y0 = abs(HEAD_Y[1] if side > 0 else HEAD_Y[0]) - 0.010
    m.add(rcyl((q[0], side * y0, q[2]), ax, 0.013, frame_in(q[0]) - 0.006 - y0, "engine_case", rr=0.002, sink=0.0))
    m.add(hose([(q[0], side * 0.074, q[2]), (q[0] + 0.022 * PP[0], side * 0.066, q[2] + 0.022 * PP[1])], 0.009,
               "engine_case", seg=12, caps=(True, True)))   # the lug that carries the boss on the head
    stud(q, 0.012)
    for X, Y in bolts:
        stud(fn(X, Y, side * 0.09), 0.010)


JOINT = _p(_L, 745, 700, 0.082)            # LEFT: water joint on the head (to the left radiator's top)
JOINT_DIR = np.array([0.93, 0.12, 0.34]) / np.linalg.norm([0.93, 0.12, 0.34])    # LEFT: toward the clamp at 690, 680
JOINT2 = _a(H_BASE + 0.030, S_FC - 0.016, 0.082)    # LEFT 610, 850: the fat hose from the left radiator ends on the
J2_DIR = _p(_L, 580, 780, 0.093) - JOINT2           # cylinder's left flank (spigot along the hose seen at 580, 780)
J2_DIR = J2_DIR / np.linalg.norm(J2_DIR)
BLEED0 = _a(H_TOP - 0.004, S_RV + 0.060, -0.045)    # RIGHT 757, 318: air bleed spigot on the head cover


def _top_end(m):
    cyl = [_a(H_BASE - 0.004, S_RB), _a(H_BASE - 0.004, S_FC), _a(H_HEAD, S_FC), _a(H_HEAD, S_RC)]
    head = [_a(H_HEAD, S_RC - 0.004), _a(H_HEAD, S_FH), _a(H_COVER, S_FH), _a(H_COVER, S_RV)]
    cover = [_a(H_COVER, S_RV), _a(H_COVER, S_FV), _a(H_TOP, S_FV - 0.008), _a(H_TOP, S_RV + 0.010)]
    m.add(slab(cyl, CYL_Y[0], CYL_Y[1], "engine_case", rr=0.005, k=3))
    m.add(slab(head, HEAD_Y[0], HEAD_Y[1], "engine_case", rr=0.004, k=3))
    m.add(slab(cover, COVER_Y[0], COVER_Y[1], "engine_black", rr=0.008, k=4))
    # the joints: gasket flanges standing 2 mm proud (base of the cylinder and of the head)
    for h, y, s0, s1 in ((H_BASE, CYL_Y, S_RB, S_FC), (H_HEAD, HEAD_Y, S_RC - 0.004, S_FH)):
        fl = [_a(h - 0.003, s0 - 0.002), _a(h - 0.003, s1 + 0.002), _a(h + 0.006, s1 + 0.002), _a(h + 0.006, s0 - 0.002)]
        m.add(slab(fl, y[0] - 0.002, y[1] + 0.002, "engine_case", rr=0.0015, step=0.004, k=1))
    # cylinder bolts (EST positions: the four corners of the cylinder foot)
    for s in (S_RB + 0.012, S_FC - 0.012):
        for y in (CYL_Y[0], CYL_Y[1]):
            sg = float(np.sign(y))
            q = _a(H_BASE + 0.016, s, y)
            m.add(rcyl(q, YP * sg, 0.007, 0.004, "engine_case", rr=0.001, seg=12))
            m.add(bolt(q + np.array([0, sg * 0.004, 0]), YP * sg))
    # cover bolts and the plug cap on top of the black cover (the smoothed top sits a little under H_TOP)
    for s, y in ((S_RV + 0.030, 0.034), (S_FV - 0.030, 0.034), (S_RV + 0.030, -0.034), (S_FV - 0.030, -0.034)):
        m.add(rcyl(_a(H_TOP - 0.004, s, y), AX3, 0.008, 0.005, "engine_black", rr=0.001, seg=14, sink=0.002))
        m.add(bolt(_a(H_TOP + 0.001, s, y), AX3, af=0.010))
    m.add(turned(_a(H_TOP - 0.008, 0.5 * (S_RV + S_FV), 0.0), AX3,
                 [(0.015, 0.0), (0.015, 0.004), (0.015, 0.008), (0.015, 0.012), (0.015, 0.016), (0.012, 0.020),
                  (0.006, 0.022)], "plastic_black", 20))
    m.add(rcyl(BLEED0, AX3, 0.004, 0.012, "steel", rr=0.001, seg=10, sink=0.002))            # air bleed spigot
    # right face: the two half-moon cam plugs across the cover joint and a bolt (RIGHT 835, 520; 640, 480; 708, 540)
    for (X, Y), r in (((835, 520), 0.032), ((640, 480), 0.020)):
        q = _R(X, Y, -0.064)
        m.add(rcyl((q[0], COVER_Y[0] + 0.002, q[2]), YM, r, 0.005, "engine_case", rr=0.002, seg=40))
    q = _R(708, 540, -0.064)
    m.add(bolt((q[0], HEAD_Y[0], q[2]), YM))
    # left face: cam chain tunnel bolt (LEFT 790, 530), temperature sender (LEFT 905, 600), the two water joints
    # with their spigots (LEFT 745, 700, bolt 775, 668; LEFT 610, 850)
    q = _L(790, 530, 0.07)
    m.add(bolt((q[0], HEAD_Y[1] - 0.0005, q[2]), YP, af=0.010))
    q = _L(905, 600, 0.07)
    m.add(rcyl((q[0], HEAD_Y[1], q[2]), YP, 0.007, 0.014, "steel", rr=0.002, seg=6))
    m.add(rcyl((JOINT[0], HEAD_Y[1] - 0.004, JOINT[2]), YP, 0.015, 0.018, "engine_cover", rr=0.004, seg=24, sink=0.0))
    m.add(hose([JOINT, JOINT + 0.030 * JOINT_DIR], 0.0095, "engine_cover", seg=14, caps=(True, True)))
    q = _L(775, 668, 0.08)
    m.add(bolt((q[0], HEAD_Y[1] + 0.014, q[2]), YP))
    m.add(rcyl((JOINT2[0], CYL_Y[1] - 0.004, JOINT2[2]), YP, 0.015, 0.020, "engine_cover", rr=0.004, seg=24, sink=0.0))
    m.add(hose([JOINT2, JOINT2 + 0.026 * J2_DIR], 0.0105, "engine_cover", seg=14, caps=(True, True)))
    # exhaust port: stub out of the head's front face to the mating face, bored for the pipe's end (51 mm for a
    # 38 mm pipe that leaves 22 deg to the right); two lugs with their studs and nuts above and below the pipe
    b = _a(H_PORT, S_FH, PORT[1])
    hb = float((PORT - b) @ PORT_DIR) + 0.004 - 0.0003
    m.add(turned(b - 0.004 * PORT_DIR, PORT_DIR,
                 [(0.0305, 0.0), (0.0305, 0.006), (0.0283, 0.009), (0.0283, hb - 0.010), (0.0283, hb - 0.0012),
                  (0.0273, hb), (0.0255, hb), (0.0255, hb - 0.006), (0.0255, hb - 0.012), (0.012, hb - 0.012)],
                 "engine_case", 32))
    face = PORT - 0.0003 * PORT_DIR
    for sg in (-1, 1):
        c = face + sg * 0.0375 * AX3
        m.add(rcyl(c - 0.007 * PORT_DIR, PORT_DIR, 0.0105, 0.007, "engine_case", rr=0.0015, seg=20, sink=0.0))
        m.add(hose([c - 0.007 * PORT_DIR - sg * 0.012 * AX3, c - 0.007 * PORT_DIR], [(0.0085, 0.0035)] * 6, "engine_case",
                   seg=10, n=6, caps=(True, True)))          # web from the stub to the lug
        m.add(bolt(c, PORT_DIR, af=0.010))
        m.add(rcyl(c + 0.0055 * PORT_DIR, PORT_DIR, 0.003, 0.004, "steel", rr=0.0008, seg=10, sink=0.001))   # stud's end
    # head hangers: LEFT and RIGHT outlines and bolts
    _hanger(m, _L, 1, [(975, 372), (1060, 400), (1145, 505), (1145, 560), (1060, 600), (1015, 690), (958, 690),
                       (950, 620), (968, 480)], (985, 652), [(1015, 430), (1088, 490), (1125, 535)])
    _hanger(m, _R, -1, [(520, 400), (505, 640), (462, 640), (440, 560), (380, 510), (380, 470), (450, 420)],
            (492, 612), [(485, 430), (408, 490)])


STARTER = _L(1088, 818, 0.05)              # LEFT: black barrel behind the cylinder, top at crop Y 750..770
TB0 = _a(H_HEAD + 0.80 * (H_COVER - H_HEAD), S_RV + 0.004, 0.0)    # intake port on the head's rear face (EST)
TB_DIR = np.array([-math.cos(math.radians(50)), 0.0, math.sin(math.radians(50))])   # EST: downdraft 50 deg
TB_UP = np.array([math.sin(math.radians(50)), 0.0, math.cos(math.radians(50))])
TB_R = TB_BORE / 2 + 0.008
TB_MID = TB0 + 0.062 * TB_DIR
THROTTLE_DRUM = TB_MID + np.array([0.0, -TB_R - 0.008, 0.019])   # highest point of the throttle drum (right of the body): the two throttle cables end lying on it


def _intake_and_electrics(m):
    # starter motor: black barrel across the cases behind the cylinder, silver flange at its left end
    sx, sz = STARTER[0], STARTER[2]
    prof = [(0.020, 0.0), (0.024, 0.004)] + [(0.024, 0.004 + 0.008 * k) for k in range(1, 13)] \
        + [(0.020, 0.106), (0.009, 0.108)]
    m.add(turned((sx, -0.050, sz), YP, prof, "engine_black", 28))
    m.add(rcyl((sx, 0.040, sz), YP, 0.026, 0.006, "engine_cover", rr=0.001, sink=0.0))
    # intake: rubber insulator, throttle body (SPEC bore 44), boot toward the airbox, cut 11 mm short of the frame's
    # upper cross member (MODEL), which lies on the intake's axis
    p1, p2, ro = TB0 + 0.030 * TB_DIR, TB0 + 0.100 * TB_DIR, TB_R
    m.add(turned(TB0 - 0.004 * TB_DIR, TB_DIR, [(ro + 0.003, 0.0), (ro + 0.003, 0.010), (ro, 0.013), (ro, 0.034)],
                 "rubber_black", 28))
    m.add(turned(p1, TB_DIR, [(ro - 0.001, 0.0), (ro + 0.002, 0.003)] + [(ro + 0.002, 0.003 + 0.0061 * k)
                                                                         for k in range(1, 11)]
                 + [(ro - 0.001, 0.070)], "alu_cast", 28))
    m.add(turned(p2 - 0.004 * TB_DIR, TB_DIR, [(ro + 0.004, 0.0), (ro + 0.004, 0.006), (ro + 0.004, 0.012),
                                               (ro + 0.001, 0.016), (ro + 0.002, 0.026), (ro + 0.0035, 0.034),
                                               (ro + 0.001, 0.036)], "rubber_black", 28))
    for d in (0.004, 0.012):                               # band clamps on the insulator and the boot
        m.add(turned(p1 + (d - 0.012) * TB_DIR, TB_DIR, [(ro + 0.0042, 0.0), (ro + 0.0042, 0.006)], "steel", 28,
                     cap0=False, cap1=False))
        m.add(turned(p2 + (d - 0.006) * TB_DIR, TB_DIR, [(ro + 0.0052, 0.0), (ro + 0.0052, 0.006)], "steel", 28,
                     cap0=False, cap1=False))
    mid = TB_MID
    m.add(rcyl(mid + np.array([0, -ro, 0]), YM, 0.019, 0.016, "plastic_black", rr=0.003, seg=24))    # throttle drum
    m.add(rbox((0.030, 0.014, 0.022), 0.004, "plastic_black", None, mid + np.array([0, ro + 0.005, 0])))  # sensor
    # fast idle knob (yellow, LEFT 960, 340) on its stem
    kn = _p(_L, 960, 340, 0.052)
    m.add(hose([mid + np.array([0, ro - 0.002, 0.004]), kn], 0.0025, "steel", seg=8, caps=(True, True)))
    m.add(turned(kn, YP, [(0.004, -0.002), (0.0065, 0.0), (0.0065, 0.008), (0.005, 0.010)], "idle_knob", 8))
    # injector on the body's top with its fuel joint; fuel hose up to the tank's outlet spigot
    inj = TB0 + 0.040 * TB_DIR + (ro - 0.004) * TB_UP
    idir = (TB_UP + 0.5 * TB_DIR) / np.linalg.norm(TB_UP + 0.5 * TB_DIR)
    m.add(turned(inj, idir, [(0.0085, 0.0), (0.0085, 0.008), (0.0085, 0.022), (0.0105, 0.024), (0.0105, 0.030),
                             (0.0105, 0.036), (0.007, 0.038)], "plastic_black", 16))
    rail = inj + 0.032 * idir
    m.add(rbox((0.016, 0.034, 0.012), 0.003, "alu_cast", None, rail + np.array([0, 0.010, 0])))       # fuel rail
    m.add(bolt(rail + np.array([0, 0.022, 0.006]), (0, 0, 1)))
    m.add(hose([rail + np.array([0, 0.024, 0]), rail + np.array([0.012, 0.040, 0.012]),
                FUEL_OUT - np.array([0.03, 0, 0.026]), FUEL_OUT - np.array([0, 0, 0.014]),
                FUEL_OUT + np.array([0, 0, 0.0105])], 0.0055, "rubber_black", seg=10))   # slides over the spigot
    # head cover breather to the airbox boot (EST route)
    b0 = _a(H_TOP - 0.004, S_RV + 0.022, 0.040)
    m.add(rcyl(b0, AX3, 0.006, 0.012, "plastic_black", rr=0.001, seg=12, sink=0.002))
    be = TB0 + 0.122 * TB_DIR
    m.add(hose([b0 + 0.008 * AX3, b0 + 0.024 * AX3 + 0.012 * TB_DIR, TB0 + 0.100 * TB_DIR + np.array([0, 0.046, 0.026]),
                be + np.array([0, ro + 0.004, 0.003])], 0.006, "rubber_black", seg=10))
    # black ribbed electrics box behind the cylinder on the left (LEFT outline), ribs along its length
    out = _xz(_L, [(1055, 612), (1185, 532), (1215, 542), (1395, 792), (1398, 832), (1282, 872), (1240, 862),
                   (1045, 642)], 0.07)
    m.add(dome(out, 0.052, 1, 0.024, 0.030, 0.006, "plastic_black", step=0.006))
    a0, a1 = _L(1120, 600, 0.07)[[0, 2]], _L(1320, 840, 0.07)[[0, 2]]
    el = (a1 - a0) / np.linalg.norm(a1 - a0)
    es = np.array([-el[1], el[0]])
    Rb = np.column_stack([[el[0], 0, el[1]], [0, 1, 0], [es[0], 0, es[1]]])
    c0 = 0.5 * (a0 + a1)
    for k in range(-2, 3):
        cc = c0 + es * 0.0085 * k
        m.add(sbox((cc[0], 0.082, cc[1]), (0.105, 0.003, 0.0035), "plastic_black", Rb, 0))
    m.add(hose([(out[-1, 0] - 0.012, 0.058, out[-1, 1] + 0.008), (sx - 0.002, 0.050, sz + 0.022)], 0.005,
               "plastic_black", seg=8, caps=(True, True)))   # its stay down to the starter (EST)


def _skid(m):
    """Black skid plate: a U channel round both cradle rails, 2.5 mm clear of them in their own section planes
    (MODEL), from below the down tube's foot (LEFT: front tip at z 0.44) to x 0.665 (LEFT: rear end at 0.67). Walls
    3 mm; the base is 13 mm deep: the belly's lowest outline in both side photos is 346..348 mm above the ground at
    the rail (test_bike.py), 15.5 mm under the rail's lower edge."""
    th = 0.003
    aw, eb, nt = RAIL_W + 0.0025 + th, RAIL_H + 0.0025, -(RAIL_H - 0.004)
    e = RAIL_H + 0.0155
    sec = [(aw, nt), (aw, e - 0.010), (aw - 0.010, e)]                       # outer: wall, chamfer, bottom
    sin = [(aw - th - 0.004, eb), (aw - th, eb - 0.004), (aw - th, nt)]      # inner, bottom to wall
    rings = []
    for i in np.flatnonzero((RAIL[:, 2] < 0.425) & (RAIL[:, 0] > 0.665)):
        left = lambda a, nn, i=i: RAIL[i] + RAIL_LAT[i] * a + RAIL_DN[i] * nn
        right = lambda a, nn, i=i: left(a, nn) * np.array([1.0, -1.0, 1.0])
        rings.append(np.array([left(*q) for q in sec] + [right(*q) for q in sec[::-1]]
                              + [right(*q) for q in sin[::-1]] + [left(*q) for q in sin]))
    o = len(m.V)
    grid(m, rings, "plastic_black")
    for kk in (0, len(rings) - 1):                          # close the two ends of the channel's wall
        b = o + 12 * kk
        for i in range(5):
            m.face((b + i, b + i + 1, b + 10 - i, b + 11 - i), "plastic_black")


def engine():
    m = Mesh()
    _cases(m)
    _left_cover(m)
    _shift(m)
    _right_cover(m)
    _top_end(m)
    _intake_and_electrics(m)
    _skid(m)
    return oriented(m)


# ------------------------------------------------------------------ radiators
RAD_LEAN = math.radians(22.0)              # LEFT: grille's front face from (0.986, 0.659) to (1.027, 0.760)
RAD0 = np.array([0.949, 0.0, 0.668])       # LEFT / RIGHT: lower tank at x 0.91..0.96, z 0.645..0.667; core above it
RAD_D = 0.030                              # EST core depth
RAD_H = 0.228                              # MODEL: top tank 8 mm under the shroud decks (z 0.93 at x 1.06). The front
#                                            photo's black reaches z 0.95 (rows 610..1030): the decks, not the core
RAD_IN = 0.074                             # EST inner edge (the fork tubes hide it in the front photo)
E_H = np.array([math.sin(RAD_LEAN), 0.0, math.cos(RAD_LEAN)])
E_D = np.array([math.cos(RAD_LEAN), 0.0, -math.sin(RAD_LEAN)])
RF = np.column_stack([E_D, [0.0, 1.0, 0.0], E_H])          # local (depth forward, width, height) -> world


def _rad_out():
    """Outer edge per side: 8 mm inside the shroud's plan envelope wherever the shroud covers the radiator."""
    out = {}
    for side in (1, -1):
        plan = plastics._shroud_plan(side)
        zs = np.linspace(0.70, 0.92, 12)
        xr = RAD0[0] + (zs - RAD0[2]) * math.tan(RAD_LEAN) - 0.5 * RAD_D / math.cos(RAD_LEAN)
        out[side] = min(float(plan(float(x))) for x in xr) - 0.008
    return out


RAD_OUT = _rad_out()


def _rw(d, w, h):
    return RAD0 + RF @ np.array([d, w, h])


NECK = _rw(-0.002, -(RAD_IN + 0.030), RAD_H + 0.022)       # EST: filler neck on the right radiator's top tank
STUB = {s: np.array([0.9015, s * 0.100, 0.652]) for s in (1, -1)}   # LEFT 500, 620 / RIGHT 1000, 620: hose clamps


def radiators():
    m = Mesh()
    for side in (1, -1):
        y0, y1 = RAD_IN, RAD_OUT[side] - 0.003
        W, yc = y1 - y0, side * (y0 + y1) / 2
        # core: 28 rows, black; side plates; aluminium tanks top and bottom (the lower one shows bare in profile)
        rings = []
        for k in range(57):
            dd = RAD_D / 2 - (0.0016 if k % 2 else 0.0)
            hh = RAD_H * k / 56
            rings.append(np.array([_rw(-dd, yc - W / 2 + 0.003, hh), _rw(dd, yc - W / 2 + 0.003, hh),
                                   _rw(dd, yc + W / 2 - 0.003, hh), _rw(-dd, yc + W / 2 - 0.003, hh)]))
        grid(m, rings, "radiator", cap0=True, cap1=True)
        for yy, cut in ((yc - side * (W / 2 - 0.0015), 0.0), (yc + side * (W / 2 - 0.0015), 0.014)):
            # (the outer plate starts 14 mm up: the shroud's lower tip curls in under it)
            m.add(sbox(_rw(0, yy, RAD_H / 2 + cut / 2), (RAD_D + 0.004, 0.003, RAD_H + 0.004 - cut), "alu_cast", RF, 2))
        m.add(rbox((RAD_D + 0.006, W - 0.014, 0.022), 0.007, "alu_cast", RF, _rw(0, yc - side * 0.007, -0.010)))
        m.add(rbox((RAD_D + 0.006, W, 0.024), 0.008, "alu_cast", RF, _rw(0, yc, RAD_H + 0.011)))
        for z in (0.724, 0.850):                           # FRONT rows 745 and 915: lugs for the shroud's bolts
            hh = (z - RAD0[2]) / math.cos(RAD_LEAN)
            m.add(rcyl(_rw(0.004, side * (y1 - 0.001), hh), YP * side, 0.007, 0.004, "rubber_black", rr=0.001,
                       seg=14, sink=0.001))
        # outlet stub of the lower tank with its hose clamp; strap to the side of the frame's down tube (MODEL:
        # 44 mm wide there; the strap stops 0.5 mm short)
        m.add(hose([_rw(-0.012, side * 0.100, -0.010), STUB[side] + np.array([0.012, 0, 0.002]), STUB[side]],
                   0.0115, "alu_cast", seg=14, caps=(True, True)))
        m.add(hose([(0.951, side * (RAD_IN + 0.004), 0.656), (0.968, side * 0.0245, 0.648)], [(0.009, 0.002)] * 8,
                   "alu_cast", seg=8, n=8, caps=(True, True)))
        m.add(bolt((0.966, side * 0.031, 0.650), (0, 0, 1)))
        # grille: black frame with six upright slats turned 32 deg outward
        g0, g1, gh0, gh1 = RAD_D / 2 + 0.002, RAD_D / 2 + 0.024, -0.021, RAD_H + 0.006
        gd, gc = g1 - g0, (g0 + g1) / 2
        for hh in (gh0 + 0.002, gh1 - 0.002):
            m.add(sbox(_rw(gc, yc, hh), (gd, W, 0.004), "louvre", RF, 1, 0.004))
        for yy in (yc - W / 2 + 0.0015, yc + W / 2 - 0.0015):
            m.add(sbox(_rw(gc, yy, (gh0 + gh1) / 2), (gd, 0.003, gh1 - gh0), "louvre", RF, 2))
        for k in range(6):
            yy = yc + (k - 2.5) * (W - 0.012) / 6
            m.add(sbox(_rw(gc, yy, (gh0 + gh1) / 2), (gd + 0.002, 0.0016, gh1 - gh0 - 0.002), "louvre",
                       RF @ rot_z(side * math.radians(32)), 2, 0.012))
        # the grille's outer wing closes the gap to the shroud's inside (FRONT rows: black out to 0.189): it stops
        # 8 mm short of the plan envelope and fades out under the shroud's rounded top
        plan = plastics._shroud_plan(side)
        ring = []
        for hh in np.linspace(0.040, 0.250, 26):
            f = _rw(g1, 0.0, hh)
            t = min((f[2] - 0.700) / 0.025, (0.905 - f[2]) / 0.045, 1.0)
            tip = y1 + max(t, 0.0) * max(float(plan(float(f[0]))) - 0.008 - y1, 0.0)
            ring.append(np.array([_rw(g0 + 0.004, side * (y1 - 0.0015), hh), _rw(g1, side * (tip - 0.0015), hh),
                                  _rw(g1, side * tip, hh), _rw(g0 + 0.004, side * y1, hh)]))
        grid(m, ring, "louvre", cap0=True, cap1=True)
    # filler neck and cap (right radiator), EST
    m.add(turned(NECK - 0.004 * E_H, E_H, [(0.016, 0.0), (0.016, 0.004), (0.016, 0.008), (0.016, 0.012),
                                           (0.0215, 0.012), (0.0215, 0.016), (0.0215, 0.020), (0.019, 0.022),
                                           (0.013, 0.0225), (0.007, 0.0225)], "alu_machined", 28))
    for a in (0.0, math.pi):
        m.add(box(NECK + 0.014 * E_H + 0.022 * (math.cos(a) * E_D), (0.008, 0.008, 0.006), "alu_machined", RF))
    # upper inlet of the left radiator and the hose from the head's water joint (LEFT 690, 680 .. 540, 330)
    inl = _rw(-0.016, 0.105, RAD_H + 0.011)
    m.add(hose([inl + np.array([0.004, 0, 0]), inl - np.array([0.030, 0, 0.004])], 0.0095, "alu_cast", seg=14,
               caps=(True, True)))
    h1 = [JOINT + 0.027 * JOINT_DIR, JOINT + 0.050 * JOINT_DIR, _p(_L, 640, 600, 0.092), _p(_L, 590, 480, 0.095),
          _p(_L, 560, 400, 0.097), _p(_L, 535, 320, 0.100), inl - np.array([0.050, 0, 0.014]),
          inl - np.array([0.012, 0, 0.002])]
    m.add(hose(h1, 0.0115, "rubber_black", seg=14))
    for q, d in ((JOINT + 0.031 * JOINT_DIR, JOINT_DIR), (inl - np.array([0.020, 0, 0.003]), np.array([1.0, 0, 0.1]))):
        m.add(turned(q, d, [(0.0128, -0.004), (0.0128, 0.004)], "steel", 16, cap0=False, cap1=False))
    # lower hoses: left radiator down the cylinder's left flank to its water joint (LEFT 540, 700 .. 610, 850),
    # right radiator to the pump pipe (RIGHT 880, 760 .. 990, 628). Both slide over their spigots.
    top = PUMP_PIPE[-1]
    h2 = [STUB[1] + np.array([0.010, 0, 0.001]), _p(_L, 540, 700, 0.096), JOINT2 + 0.058 * J2_DIR,
          JOINT2 + 0.023 * J2_DIR]
    m.add(hose(h2, 0.0135, "rubber_black", seg=14))
    h3 = [STUB[-1] + np.array([0.010, 0, 0.001]), _p(_R, 935, 680, -0.100), _p(_R, 880, 760, -0.099),
          top + 0.022 * PUMP_DIR, top - 0.002 * PUMP_DIR]
    m.add(hose(h3, 0.0135, "rubber_black", seg=14))
    for s in (1, -1):
        m.add(turned(STUB[s] + np.array([0.003, 0, 0]), (1, 0, 0.05), [(0.015, -0.004), (0.015, 0.004)], "steel", 16,
                     cap0=False, cap1=False))
    m.add(turned(JOINT2 + 0.027 * J2_DIR, J2_DIR, [(0.015, -0.004), (0.015, 0.004)], "steel", 16, cap0=False, cap1=False))
    # air bleed from the head cover's spigot to the filler neck (RIGHT 757..900, 300: thin black pipe over the cover)
    m.add(hose([BLEED0 + 0.006 * AX3, BLEED0 + 0.024 * AX3, _p(_R, 800, 290, -0.052), _p(_R, 900, 296, -0.056),
                (0.930, -0.076, 0.800), (0.990, -0.090, 0.870), NECK + np.array([-0.034, 0.0, -0.014]),
                NECK + np.array([-0.015, 0, 0.002])], 0.0058, "rubber_black", seg=10))
    # overflow tube: from the neck, behind the down tube under the throttle cables (MODEL) to the left, down behind the
    # cradle (LEFT 480, 660 .. 560, 1190) to the skid plate (LEFT and RIGHT: clear tube at x 0.817)
    of = [NECK + np.array([0.0, 0.015, 0.003]), NECK + np.array([-0.012, 0.030, -0.010]), (1.014, -0.064, 0.880),
          (0.992, -0.052, 0.800), (0.962, -0.018, 0.760), (0.950, 0.030, 0.740), (0.925, 0.062, 0.660),
          (0.897, 0.064, 0.540), (0.880, 0.050, 0.445), (0.862, 0.030, 0.410), (0.838, 0.008, 0.384),
          (0.822, 0.000, 0.371)]
    m.add(hose(of, 0.004, "tube_clear", seg=8, caps=(True, True)))
    return oriented(m)


# ------------------------------------------------------------------ fuel tank
CAP = cams.CAMS["top"].on_plane(1854.0, 1120.0, "z", 1.04)[0]      # TOP: filler cap centre (x 0.883)
TANK_GAP = 0.056                                                    # TOP cols 1840..1920: titanium +-0.053..0.056
TANK_PLATEAU = 0.050                       # the raised top between the shroud decks (MODEL: their edges at 0.053+)
# MODEL: detail_chassis.frame's spar under the shroud: a bar 24.5 mm wide and 80..88 mm deep swept with geom.tube
# through these stations, its top 8 mm lower ahead of x 0.92 (copied: the path is not exported there;
# test_detail_engine.py checks the tank against the frame's mesh itself)
SPAR_X = np.array([0.74, 0.78, 0.82, 0.86, 0.90, 0.92, 0.94, 0.98, 1.03, 1.058])
_SLOW = np.interp(SPAR_X, [0.86, 0.92, 1.058], [0.0, 0.004, 0.004])
_SP = np.stack([SPAR_X, np.array([chassis._spar_y(x) for x in SPAR_X]) - T_FR / 2,
                chassis._spar_top(SPAR_X) - 0.047 - _SLOW], axis=1)
_SN, _SB = _bar_frame(_SP)
_SN, _SB = _SN * np.sign(_SN[:, 1:2]), _SB * np.sign(_SB[:, 2:3])          # outward, upward
_SH = (np.linspace(0.080, 0.088, len(SPAR_X)) - 2 * _SLOW)[:, None] / 2
_SPAR_IN = [_SP - 0.01225 * _SN + k * _SH * _SB for k in (-1, 1)]          # edges of the bar's inner face
_SPAR_TOP = [_SP + _SH * _SB + k * 0.01225 * _SN for k in (-1, 1)]         # edges of its top face


def _spar(x):
    """(inner face |y|, top z) of the frame beside and under the tank at x: the hidden spar bar and, behind x 0.816,
    the visible plate as well."""
    yin = min(float(np.interp(x, e[np.argsort(e[:, 0]), 0], e[np.argsort(e[:, 0]), 1])) for e in _SPAR_IN)
    top = max(float(np.interp(x, e[np.argsort(e[:, 0]), 0], e[np.argsort(e[:, 0]), 2])) for e in _SPAR_TOP)
    if x <= 0.816:
        yin, top = min(yin, frame_in(x)), max(top, float(chassis._spar_top(x)))
    return yin, top


def tank_section(x):
    """(lobe half-width, half-width, lobe bottom, underside, shoulder, top, plateau half-width) at x.
    The top plateau is what shows between the shroud decks (TOP); the shoulders beside it stay 8 mm under the decks,
    the side panels' tips and the seat's nose (MODEL); underneath it is a saddle: the body stays 2.5 mm inside the
    frame's spars, or 3 mm above them where it reaches over, and a lobe hangs below, clear of the head cover (EST)."""
    zt = float(np.interp(x, [0.745, 0.77, 0.795, 0.82, 0.88, 0.96, 0.975], [0.909, 0.928, 0.961, 0.997, 1.022, 1.015, 1.003]))
    zs = min(zt - 0.004, float(np.interp(x, [0.745, 0.78, 0.82, 0.86, 0.888, 0.90, 0.94, 0.975],
                                         [0.915, 0.950, 0.978, 0.984, 0.984, 0.958, 0.946, 0.938])))
    hw = float(np.interp(x, [0.745, 0.80, 0.85, 0.895, 0.918, 0.95, 0.975], [0.060, 0.086, 0.100, 0.098, 0.052, 0.040, 0.030]))
    yin, top = _spar(x)
    zu = float(np.interp(x, [0.745, 0.80, 0.92, 0.975], [0.890, 0.867, 0.867, 0.900]))
    if hw > yin - 0.0025:                                  # the body would reach over the frame:
        if zs - (top + 0.003) >= 0.006:
            zu = max(zu, top + 0.003)                      # rest 3 mm above it,
        else:
            hw = yin - 0.0025                              # or, with no room up there, stay between the spars
    zu = min(zu, zs - 0.006)
    # MODEL: detail_front.py's clutch cable runs under the tank's left edge at y 0.074: the lobe stops at 0.066
    b = min(yin - 0.003, float(np.interp(x, [0.745, 0.80], [0.055, 0.066])), hw - 0.006)
    zl = float(np.interp(x, [0.745, 0.77, 0.80, 0.92, 0.945, 0.96, 0.975], [0.860, 0.825, 0.806, 0.806, 0.860, 0.915, 0.928]))
    return b, hw, min(zl, zu - 0.002), zu, zs, zt, min(TANK_PLATEAU, hw - 0.004)


def _arc(c, r, a0, a1, n=4):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(1, n + 1)]


def _line(p, q, n):
    return [(p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n) for k in range(1, n + 1)]


def _tank_ring(x):
    b, hw, zl, zu, zs, zt, yp = tank_section(x)
    lo = 0.0004
    rb = max(min(0.016, 0.45 * b, 0.45 * (zu - zl)), lo)
    rc = max(min(0.008, 0.45 * (zu - zl), 0.4 * (hw - b)), lo)
    rd = max(min(0.010, 0.4 * (zs - zu), 0.4 * (hw - b)), lo)
    re = max(min(0.016, 0.5 * (zs - zu), 0.4 * (hw - yp)), lo)
    rf = max(min(0.008, 0.4 * (zt - zs), 0.4 * (hw - yp)), lo)
    rg = max(min(0.014, 0.5 * (zt - zs), 0.4 * yp), lo)
    half = [(0.0, zl)] + _line((0.0, zl), (b - rb, zl), 3) + _arc((b - rb, zl + rb), rb, -90, 0)
    half += _line(half[-1], (b, zu - rc), 3) + _arc((b + rc, zu - rc), rc, 180, 90)
    half += _line(half[-1], (hw - rd, zu), 3) + _arc((hw - rd, zu + rd), rd, -90, 0)
    half += _line(half[-1], (hw, zs - re), 2) + _arc((hw - re, zs - re), re, 0, 90)
    half += _line(half[-1], (yp + rf, zs), 4) + _arc((yp + rf, zs + rf), rf, 270, 180)
    half += _line(half[-1], (yp, zt - rg), 2) + _arc((yp - rg, zt - rg), rg, 0, 90)
    half += _line(half[-1], (0.0, zt), 5)
    ring = half + [(-y, z) for y, z in half[-2:0:-1]]
    return np.array([(x, y, z) for y, z in ring])


TANK_X = np.linspace(0.745, 0.975, 36)
FUEL_OUT = np.array([0.800, 0.030, tank_section(0.800)[2] - 0.012])   # EST: tip of the outlet spigot under the lobe


def tank_hull():
    return grid(Mesh(), [_tank_ring(x) for x in TANK_X], "tank_ti", cap0=True, cap1=True)


def tank():
    m = tank_hull()
    zc = tank_section(CAP[0])[5]
    c = np.array([CAP[0], 0.0, zc])
    m.add(rcyl(c, (0, 0, 1), 0.029, 0.007, "tank_ti", rr=0.002, seg=36))                  # filler neck
    m.add(rcyl(FUEL_OUT + np.array([0, 0, 0.014]), (0, 0, -1), 0.004, 0.014, "alu_machined", rr=0.001, seg=10,
               sink=0.0))                                                                 # fuel outlet spigot
    # black cap with seven lobes (TOP: 37 mm at the lobes), vent nipple and breather hose to the steering stem
    ang = np.linspace(0, 2 * math.pi, 70, endpoint=False)
    rl = 0.0345 * (1 + 0.07 * np.cos(7 * ang))
    rings = [np.column_stack([c[0] + k * rl * np.cos(ang), k * rl * np.sin(ang), np.full(70, c[2] + z)])
             for k, z in ((0.80, 0.005), (0.97, 0.005), (1.0, 0.008), (1.0, 0.016), (1.0, 0.024), (0.93, 0.0275),
                          (0.70, 0.0285), (0.45, 0.0285), (0.20, 0.0285))]
    grid(m, rings, "plastic_black", cap0=True, cap1=True)
    top = c + np.array([0, 0, 0.0285])
    m.add(rcyl(top, (0, 0, 1), 0.0055, 0.007, "plastic_black", rr=0.001, seg=12, sink=0.001))
    # MODEL: the bar mount sits on the stem, so the hose ends 0.5 mm off the top clamp's rear face, under the bar
    end = STEER0 + (T_TOP_CLAMP + 0.015) * UP + 0.0234 * BACK - 0.008 * UP
    path = [top + np.array([0, 0, 0.005]), top + np.array([0.008, 0, 0.014]), top + np.array([0.030, 0, 0.026]),
            end + 0.030 * BACK - 0.012 * UP, end]
    m.add(hose(path, 0.004, "rubber_black", seg=10, caps=(True, True)))
    return oriented(m)


PARTS = {"engine": engine, "radiators": radiators, "tank": tank}
MATERIALS = {"tube_clear": dict(rgb=(205, 205, 196), rough=0.25),
             "idle_knob": dict(rgb=(214, 188, 40), rough=0.5)}
CLASS = {}
BEVEL = {"engine": 0.0}                    # edges are rounded in the mesh; a bevel modifier would eat the bolts
SMOOTH = {"engine": 38, "radiators": 38, "tank": 50}
