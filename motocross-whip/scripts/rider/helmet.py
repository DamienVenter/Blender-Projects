"""Damien's helmet and goggle: Leatt Moto 8.5 Composite (V26 kit, Pinata Teal) and Velocity 5.5 Iriz goggle.

python3 helmet.py BODY.npz OUT.npz          (body.py writes BODY.npz; OUT.npz is a gear file for build_rider.py)

Everything is built here in the HELMET frame (metres, x to the wearer's left, y backwards, z up: the axes of body.py's
MB frame) and placed on his head by one rigid transform found from his head mesh (fit_on_head). The parts ride the
"head" bone rigidly.

Sources (research/rider-ledger/helmet.md has every number with its source):
  PROFILE   the shell's side outline traced from Leatt's near-orthographic left view of the same 8.5 shell
            (V25 "Royal", 1025100220: Leatt_Helmet_Moto_8.5_Royal_Left_1025100220.png on us.leatt.com, product
            helmet-kit-moto-8-5-composite-with-5-5-goggle-sale), in its pixels (u right = backwards, v down).
  SCALE     the 45 mm goggle strap (Leatt Velocity 5.5 spec) measured in Leatt's MY27 side and back views of the
            same shell with the goggle on (31509_Helmet_Kit_Moto_8.5_White_2/_3_1027000260.jpg), the left view
            registered onto that side view by a similarity fit (residual 18 px), camera taken 1.5 m away.
  WIDTHS    back-view half widths (Royal_Back, scaled the same way) and the plan (Pinata Teal top view).
"""
import json
import math
import os
import sys

import numpy as np
from scipy.spatial import Delaunay, cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.normpath(os.path.join(HERE, "..", "..", "textures", "rider"))

# ---------------------------------------------------------------- scale and profile (Leatt Royal_Left pixels)
STRAP = 0.045                      # m, Velocity 5.5 strap width (Leatt feature list)
STRAP_PX_MY27_SIDE = 186.7         # strap width across its run in the MY27 side view (194 px tall at 15.8 deg)
ROYAL_TO_MY27 = 0.9481             # similarity fit of the Royal_Left outline onto the MY27 side view
PERSPECTIVE = 1.087                # strap on the side surface 0.13 m nearer a camera 1.5 m away than the centre plane
S = STRAP / STRAP_PX_MY27_SIDE * ROYAL_TO_MY27 * PERSPECTIVE      # m per Royal_Left pixel = 0.248 mm
U0, V0 = 1100.0, 900.0             # helmet-frame origin in Royal_Left pixels (near the ear)

# Traced outline, Royal_Left pixels, in order round the shell (front at small u). RIM stretches are on the
# centre plane (the surface's two halves meet there); FREE stretches are cut edges (lower edge, face port).
CROWN_UNDER_VISOR = [            # shell crown hidden under the visor: estimated (visor stands 0 mm off the crown at
    (539, 703), (533, 660), (533, 615), (540, 572), (556, 530),   # u 1135, 13 mm at u 886, 21 mm at u 726)
    (582, 490), (620, 455), (668, 430), (725, 413), (800, 399), (886, 390), (966, 384), (1045, 379), (1124, 377)]
CROWN_BACK = [
    (1194, 380), (1218, 385), (1241, 389), (1265, 395), (1288, 400), (1311, 405), (1335, 412), (1358, 418),
    (1381, 424), (1404, 430), (1427, 436), (1450, 442), (1473, 450), (1496, 457), (1519, 464), (1542, 471),
    (1562, 484), (1577, 503), (1584, 524), (1581, 547), (1580, 571), (1588, 593), (1597, 615), (1606, 637),
    (1615, 659), (1624, 681), (1633, 703), (1641, 726), (1649, 748), (1655, 771), (1662, 794), (1668, 817),
    (1674, 841), (1679, 864), (1683, 888), (1688, 911), (1691, 935), (1695, 959), (1697, 982), (1699, 1006),
    (1699, 1030), (1696, 1054), (1689, 1076), (1681, 1098), (1674, 1121), (1670, 1144), (1668, 1168),
    (1665, 1192), (1658, 1214), (1649, 1235), (1637, 1256), (1625, 1276), (1613, 1297), (1602, 1319),
    (1589, 1336), (1573, 1354), (1557, 1372), (1540, 1389), (1522, 1404), (1497, 1414)]
LOWER_EDGE = [
    (1497, 1414), (1458, 1422), (1419, 1432), (1380, 1437), (1340, 1440), (1300, 1443), (1260, 1446),
    (1220, 1449), (1181, 1452), (1141, 1455), (1101, 1459), (1061, 1463), (1022, 1471), (983, 1478),
    (943, 1486), (904, 1493), (865, 1500), (825, 1507), (786, 1514), (747, 1522), (707, 1529), (668, 1537),
    (629, 1544), (590, 1550), (550, 1555), (510, 1561), (471, 1569), (432, 1578), (393, 1585), (353, 1591),
    (314, 1596), (294, 1598)]
CHIN_FRONT = [
    (294, 1598), (272, 1593), (257, 1578), (252, 1550), (249, 1516), (247, 1484), (244, 1453), (241, 1421),
    (239, 1389), (240, 1357), (243, 1330), (236, 1300), (224, 1272), (213, 1245), (210, 1228), (221, 1210),
    (238, 1192), (259, 1168), (281, 1145), (305, 1124), (334, 1110), (364, 1100), (378, 1098)]
FACE_PORT = [                    # chin bar top, the port's side edge (inner edge of the trim), brow edge
    (378, 1098), (386, 1111), (396, 1124), (410, 1131), (441, 1139), (473, 1142), (505, 1144), (536, 1146),
    (566, 1135), (592, 1116), (621, 1104), (652, 1096), (683, 1090), (708, 1071), (726, 1045), (735, 1015),
    (740, 983), (742, 951), (744, 919), (746, 887), (750, 860), (746, 842), (731, 835), (704, 819), (676, 806),
    (649, 788), (625, 768), (597, 752), (569, 738), (548, 724), (539, 703)]


def px2h(P):
    """Royal_Left pixels -> helmet frame (y, z) in metres."""
    P = np.asarray(P, float)
    return np.c_[(P[:, 0] - U0) * S, -(P[:, 1] - V0) * S]


def resample_open(P, step):
    P = np.asarray(P, float)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    t = np.linspace(0, s[-1], max(int(round(s[-1] / step)), 2) + 1)
    return np.c_[np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])]


def smooth_open(P, k=2):
    """Moving average that keeps the end points (removes 1 px tracing steps)."""
    P = np.array(P, float)
    for _ in range(k):
        Q = P.copy()
        Q[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4
        P = Q
    return P


class Profile:
    """The side outline in the helmet frame: two rims (crown and back; chin front) and the free edges."""

    def __init__(self, step=0.003):
        crown = np.vstack([CROWN_UNDER_VISOR, CROWN_BACK])
        self.rim_crown = resample_open(smooth_open(px2h(crown), 3), step)
        self.lower = resample_open(smooth_open(px2h(LOWER_EDGE), 2), step)
        self.rim_chin = resample_open(smooth_open(px2h(CHIN_FRONT), 2), step)
        self.port = resample_open(smooth_open(px2h(FACE_PORT), 2), step)
        # closed domain outline, counter-clockwise in (y, z)? order: brow -> crown -> back -> lower -> chin -> port
        self.outline = np.vstack([self.rim_crown, self.lower[1:], self.rim_chin[1:], self.port[1:-1]])
        self.tree_crown = cKDTree(self.rim_crown)
        self.tree_chin = cKDTree(self.rim_chin)
        o = self.outline
        self.area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])

    def inside(self, P):
        o = self.outline
        x, y = P[:, 0], P[:, 1]
        res = np.zeros(len(P), bool)
        j = len(o) - 1
        for i in range(len(o)):
            xi, yi = o[i]
            xj, yj = o[j]
            res ^= ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
            j = i
        return res


# ---------------------------------------------------------------- half width over the profile
L_CROWN, P_CROWN = 0.1239, 1.933  # roundness of the crown and back (m, superellipse power): fitted with W_Z, Q_Y
L_CHIN, P_CHIN = 0.140, 1.25       # the chin bar narrows to a blunt V in plan (Pinata iso-left camera fit)
# Half width by height (back view) and plan factor by y (top view), fitted together with L_CROWN and P_CROWN to
# Leatt's back view (Royal_Back, camera 13.5 deg above, 0.2046 mm/px) and top view (Pinata Teal top, 0.247
# mm/px) by least squares with a smoothness penalty: residuals 7.7 px (1.6 mm) back, 9.3 px (2.3 mm) top. The
# fit's 7 % dip at z = 0 (a 1.5 % waist in the back photo, rows 880 to 960) is evened out by hand to 0.1300.
W_Z = np.array([[-0.20, 0.1115], [-0.16, 0.1155], [-0.12, 0.1197], [-0.08, 0.1287], [-0.04, 0.1347],
                [0.00, 0.1300], [0.04, 0.1304], [0.08, 0.1322], [0.12, 0.1342], [0.16, 0.1362]])
Q_Y = np.array([[-0.30, 0.9126], [-0.04, 0.9126], [0.00, 0.9755], [0.04, 0.9413], [0.08, 0.9447],
                [0.12, 1.0228], [0.16, 1.1211]])


def falloff(t, p):
    t = np.clip(t, 0.0, 1.0)
    return (1.0 - (1.0 - t) ** p) ** (1.0 / p)


L_BROW, P_BROW = 0.075, 2.0         # the brow and forehead are broad and flat with rounded corners (iso views)
Y_BROW = (-0.10, 0.00)             # the crown rim blends from the brow's roundness to the crown's over this y range
SMOOTH_SIGMA = 0.010               # m, Gaussian smoothing of the width field away from the rims (no creases)


def rim_shape(prof):
    """Roundness length and power at each crown rim sample (brow in front, crown and back behind)."""
    y = prof.rim_crown[:, 0]
    k = np.clip((y - Y_BROW[0]) / (Y_BROW[1] - Y_BROW[0]), 0, 1)
    k = k * k * (3 - 2 * k)
    return L_BROW + (L_CROWN - L_BROW) * k, P_BROW + (P_CROWN - P_BROW) * k


def half_width(prof, Y, Z, smooth=True):
    """Half width x of the outer surface over the profile domain (both halves are +-x)."""
    P = np.c_[Y, Z]
    dc, ic = prof.tree_crown.query(P)
    dh = prof.tree_chin.query(P)[0]
    Lc, Pc = rim_shape(prof)
    w = np.interp(Z, W_Z[:, 0], W_Z[:, 1]) * np.interp(Y, Q_Y[:, 0], Q_Y[:, 1])
    X = w * falloff(dc / Lc[ic], Pc[ic]) * falloff(dh / L_CHIN, P_CHIN)
    if not smooth:
        return X
    # the nearest-rim distance has creases where the nearest rim point jumps: average them out away from the rims
    d = np.minimum(dc, dh)
    tree = cKDTree(P)
    far = np.nonzero(d > 0.008)[0]
    Xs = X.copy()
    for i, nb in zip(far, tree.query_ball_point(P[far], 2.5 * SMOOTH_SIGMA)):
        nb = np.asarray(nb)
        wts = np.exp(-np.sum((P[nb] - P[i]) ** 2, 1) / (2 * SMOOTH_SIGMA ** 2))
        Xs[i] = np.sum(wts * X[nb]) / np.sum(wts)
    k = np.clip((d - 0.008) / 0.020, 0, 1)
    return X + (Xs - X) * k * k * (3 - 2 * k)


_SHELL_HW = {}


def shell_hw(prof, Y, Z):
    """The built shell's own half width (smoothed field, interpolated over its domain points) for parts that lie
    on it (visor, strap); outside the domain 0."""
    from scipy.interpolate import LinearNDInterpolator
    key = id(prof)
    if key not in _SHELL_HW:
        P = domain_points(prof)
        _SHELL_HW[key] = LinearNDInterpolator(P, half_width(prof, P[:, 0], P[:, 1]), fill_value=0.0)
    return np.nan_to_num(_SHELL_HW[key](np.c_[Y, Z]))


def ring_offsets(L, p, n):
    """Distances from a rim where the falloff rises in equal steps (even spacing across the 3D surface)."""
    s = np.arange(1, n + 1) / n
    return L * (1.0 - (1.0 - s ** p) ** (1.0 / p))


def domain_points(prof, h=0.005, nring=14):
    """Points of the profile domain: the outline itself, rings graded towards the rims, an interior grid."""
    pts = [prof.outline]
    for rim, L, p in ((prof.rim_crown, L_BROW, P_BROW), (prof.rim_chin, L_CHIN, P_CHIN)):
        t = np.gradient(rim, axis=0)
        t /= np.linalg.norm(t, axis=1)[:, None]
        n = np.c_[-t[:, 1], t[:, 0]]
        if prof.area < 0:
            n = -n
        for d in ring_offsets(L, p, nring)[:-3]:
            step = max(0.003, min(h, d * 0.9))
            r = resample_open(rim + n * d, step)
            pts.append(r)
    lo, hi = prof.outline.min(0), prof.outline.max(0)
    gy, gz = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h * 0.866))
    gy = gy + (np.arange(gy.shape[0])[:, None] % 2) * h / 2
    pts.append(np.c_[gy.ravel(), gz.ravel()])
    P = np.vstack(pts)
    n_out = len(prof.outline)
    keep = np.ones(len(P), bool)
    keep[n_out:] = prof.inside(P[n_out:])
    # nothing closer than 1.2 mm to the outline (other than the outline itself)
    d_out = cKDTree(prof.outline).query(P)[0]
    keep[n_out:] &= d_out[n_out:] > 0.0012
    P = P[keep]
    # thin out points closer than a local spacing (greedy, rings first)
    tree = cKDTree(P)
    alive = np.ones(len(P), bool)
    dc = np.minimum(prof.tree_crown.query(P)[0], prof.tree_chin.query(P)[0])
    rad = np.clip(dc * 0.35, 0.0008, h * 0.6)
    for i in range(n_out, len(P)):
        if not alive[i]:
            continue
        for j in tree.query_ball_point(P[i], rad[i]):
            if j > i and j >= n_out:
                alive[j] = False
    return P[alive]


def mesh_domain(prof, P):
    tri = Delaunay(P).simplices
    c = P[tri].mean(1)
    tri = tri[prof.inside(c)]
    # orientation: counter-clockwise in (y, z)
    a, b, cc = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (cc[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (cc[:, 0] - a[:, 0])
    tri[cr < 0] = tri[cr < 0][:, ::-1]
    return tri[np.abs(cr) > 1e-9]                   # slivers along nearly straight outline corners


def shell_outer(prof=None):
    """Outer surface of the shell, both halves, one vertex on the centre plane for each rim point."""
    prof = prof or Profile()
    P = domain_points(prof)
    T = mesh_domain(prof, P)
    X = half_width(prof, P[:, 0], P[:, 1])
    rim_mask = np.minimum(prof.tree_crown.query(P)[0], prof.tree_chin.query(P)[0]) < 1e-7
    X[rim_mask] = 0.0
    n = len(P)
    VL = np.c_[X, P]                                       # left half (x > 0)
    VR = np.c_[-X, P]
    # right half reuses the rim vertices
    idx_r = np.arange(n) + n
    idx_r[rim_mask] = np.nonzero(rim_mask)[0]
    V = np.vstack([VL, VR])
    # left half seen from +x: (y, z) counter-clockwise -> normal +x when ordered (y, z) ccw. Check below.
    FL = T.copy()
    FR = idx_r[T][:, ::-1]
    F = np.vstack([FL, FR])
    used = np.unique(F)
    remap = -np.ones(len(V), int)
    remap[used] = np.arange(len(used))
    return V[used], remap[F], prof


def normals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, F[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1), 1e-12)[:, None]


# ---------------------------------------------------------------- parts, rims, inner surface
class Part:
    """Vertices, triangles/quads, a material name per face, optional face-corner UVs."""

    def __init__(self, name, bone="head"):
        self.name, self.bone = name, bone
        self.V = np.zeros((0, 3))
        self.F, self.M, self.UV = [], [], []

    def add(self, V, F, mat, uv=None):
        o = len(self.V)
        self.V = np.vstack([self.V, V])
        for k, f in enumerate(F):
            self.F.append([int(i) + o for i in f])
            self.M.append(mat if isinstance(mat, str) else mat[k])
            self.UV.append(None if uv is None else uv[k])
        return o


def boundary_loops(F):
    """Closed loops of edges used by one face only, as vertex lists in the faces' winding order."""
    cnt = {}
    for f in F:
        for a, b in zip(f, np.roll(f, -1)):
            k = (min(a, b), max(a, b))
            cnt[k] = cnt.get(k, 0) + 1
    nxt = {}
    for f in F:
        for a, b in zip(f, np.roll(f, -1)):
            if cnt[(min(a, b), max(a, b))] == 1:
                nxt[int(a)] = int(b)
    loops, seen = [], set()
    for s in nxt:
        if s in seen:
            continue
        loop, v = [], s
        while v not in seen:
            seen.add(v)
            loop.append(v)
            v = nxt[v]
        loops.append(np.array(loop))
    return loops


def smooth_field(F, n, val, it=10, keep=None):
    """Laplacian smoothing of a per-vertex scalar over the mesh's edges."""
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E = np.vstack([E, E[:, ::-1]])
    deg = np.bincount(E[:, 0], minlength=n).astype(float)
    v = val.copy()
    for _ in range(it):
        acc = np.bincount(E[:, 0], weights=v[E[:, 1]], minlength=n)
        v = 0.5 * v + 0.5 * acc / np.maximum(deg, 1)
        if keep is not None:
            v[keep] = val[keep]
    return v


# ---------------------------------------------------------------- his head size and Leatt's chart
SIZES = [("XS", 0.53, 0.54), ("S", 0.55, 0.56), ("M", 0.57, 0.58), ("L", 0.59, 0.60), ("XL", 0.61, 0.62),
         ("XXL", 0.63, 0.64)]          # Leatt helmet moto size chart, head circumference (m)


def head_circumference(body):
    """Tape round his head above the brows and over the back of the skull: the largest convex girth of the
    skin over planes through the head between the brows and the crown, tilted -10 to +10 deg (front low)."""
    from scipy.spatial import ConvexHull
    V, FS, F = body["V"], body["FS"], body["F"]
    starts = np.concatenate([[0], np.cumsum(FS)[:-1]])
    tri = np.array([[F[s0], F[s0 + i], F[s0 + i + 1]] for s0, n in zip(starts, FS) for i in range(1, n - 1)])
    names = list(body["bones"])
    eye = body["heads"][names.index("eye.L")]
    best = 0.0
    for z0 in np.arange(eye[2] + 0.015, eye[2] + 0.05, 0.0025):
        for tilt in np.radians(np.arange(-10, 10.1, 2)):
            n = np.array([0.0, math.sin(tilt), math.cos(tilt)])
            sd = (V - np.array([0.0, eye[1], z0])) @ n
            pts = []
            for i, j in ((0, 1), (1, 2), (2, 0)):
                si, sj = sd[tri[:, i]], sd[tri[:, j]]
                m = si * sj < 0
                tt = si[m] / (si[m] - sj[m])
                pts.append(V[tri[m, i]] + (V[tri[m, j]] - V[tri[m, i]]) * tt[:, None])
            P = np.concatenate(pts)
            P = P[np.abs(P[:, 0]) < 0.12]
            P = P[P[:, 2] > eye[2] - 0.03]
            if np.ptp(P[:, 0]) > 0.165:                 # the plane caught the ears: not a head girth
                continue
            e1 = np.array([1.0, 0, 0]); e2 = np.cross(n, e1)
            best = max(best, ConvexHull(np.c_[P @ e1, P @ e2]).area)
    return best


def size_for(circ):
    """Leatt size for a head girth: the size whose range holds it, else the nearest range (ties: larger)."""
    d = [(max(lo - circ, circ - hi, 0.0), -i, name) for i, (name, lo, hi) in enumerate(SIZES)]
    return min(d)[2]


# ---------------------------------------------------------------- his head and the fit
GAP = 0.002                        # m between his skin and the comfort liner's surface (pads touch the head)
T_MIN, T_MAX = 0.018, 0.040        # m, shell + EPS + pads at their thinnest (chin bar) and fullest (crown)
EYE_TO_BROW = 0.040                # m, face port's top edge above his eye centres (goggle centred on them)
FORE_MIN = 0.032                   # m, the brow (outer) at least this far ahead of his forehead


def head_skin(body, bones=("head", "jaw", "neck03", "neck02", "neck01")):
    """Skin vertices mostly carried by the head, jaw and neck (rest frame) and those of the head alone."""
    names = list(body["bones"])
    V = body["V"]
    tot = np.zeros(len(V))
    for b in bones:
        bi = names.index(b)
        sel = body["w_bone"] == bi
        np.add.at(tot, body["w_vert"][sel], body["w_val"][sel])
    for b in [n for n in names if n.startswith(("eye", "special", "tongue", "jaw", "levator", "orbicularis",
                                                    "oris", "temporalis", "risorius", "nose", "cheek"))]:
        bi = names.index(b)
        sel = body["w_bone"] == bi
        np.add.at(tot, body["w_vert"][sel], body["w_val"][sel])
    return np.nonzero(tot > 0.5)[0]


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def brow_point(prof):
    """Centre-line end of the face port's top edge (helmet frame)."""
    p = prof.port[-1]
    return np.array([0.0, p[0], p[1]])


def head_landmarks(body):
    """His head's landmarks (rest frame): eye centres' midpoint, vertex (top), back, sides, forehead."""
    names = list(body["bones"])
    eye = 0.5 * (body["heads"][names.index("eye.L")] + body["heads"][names.index("eye.R")])
    Hd = body["V"][head_skin(body, ("head",))]
    sk = Hd[Hd[:, 2] > eye[2] + 0.03]
    fore = Hd[(Hd[:, 2] > eye[2] + 0.025) & (np.abs(Hd[:, 0]) < 0.01)]
    return dict(eye=eye, top=Hd[np.argmax(Hd[:, 2])], back=sk[np.argmax(sk[:, 1])], left=sk[np.argmax(sk[:, 0])],
                right=sk[np.argmin(sk[:, 0])], fore=fore[np.argmin(fore[:, 1])])


def fit_on_head(body, Vo, Fo, prof):
    """Place the helmet on his head: the face port's top edge EYE_TO_BROW above his eye centres on the centre
    line (the goggle then sits centred on his eyes in the port); pitch and fore-aft shift chosen so the shell
    stands off his skull evenly at the top, back and sides (equal EPS and padding all round) with the forehead
    at least FORE_MIN behind the brow. Returns R, t (p_MB = R p_H + t) and the gaps."""
    L = head_landmarks(body)
    C = np.vstack([Vo, Vo[Fo].mean(1)])
    tree = cKDTree(C)
    b = brow_point(prof)

    def place(th, dy):
        R = rot_x(th)
        return R, np.array([0.0, L["eye"][1] + dy, L["eye"][2] + EYE_TO_BROW]) - R @ b

    def gaps(th, dy):
        R, t = place(th, dy)
        return {k: tree.query((L[k] - t) @ R)[0] for k in ("top", "back", "left", "right", "fore")}

    best = None
    for th in np.radians(np.arange(0.0, 25.01, 0.5)):
        for dy in np.arange(-0.070, -0.0199, 0.001):
            g = gaps(th, dy)
            ring = np.array([g["top"], g["back"], g["left"], g["right"]])
            cost = ring.std() + 10 * max(0.0, FORE_MIN - g["fore"])
            if best is None or cost < best[0]:
                best = (cost, th, dy, g)
    R, t = place(best[1], best[2])
    return R, t, dict(pitch_deg=round(math.degrees(best[1]), 2), brow_ahead_of_eye_mm=round(-best[2] * 1000, 1),
                      gaps_mm={k: round(float(v) * 1000, 1) for k, v in best[3].items()})


def shell_solid(Vo, Fo, skin_H):
    """Outer surface, inner (comfort liner) surface and the rolled edges joining them, in the helmet frame.
    skin_H: his head and neck skin in the helmet frame. The liner surface lies GAP off the skin where the skin is
    near (pads) and T_MAX inside the shell elsewhere, never thinner than T_MIN. Returns the inner surface, the
    thickness and the rim strips (one per free edge: face port, lower edge) as lists of rings."""
    n = len(Vo)
    N = normals(Vo, Fo)
    d = cKDTree(skin_H).query(Vo)[0]
    t = np.clip(d - GAP, T_MIN, T_MAX)
    t = np.minimum(smooth_field(Fo, n, t, 12), np.maximum(d - GAP, T_MIN))
    Vi = Vo - N * t[:, None]
    strips = []
    for loop in boundary_loops(Fo):
        O, I = Vo[loop], Vi[loop]
        tang = np.roll(O, -1, 0) - np.roll(O, 1, 0)
        tang /= np.linalg.norm(tang, axis=1)[:, None]
        out = np.cross(tang, N[loop])                      # in the surface, away from it (winding order)
        out /= np.linalg.norm(out, axis=1)[:, None]
        rings = []
        for k, sv in enumerate(np.linspace(0, 1, 6)):
            bulge = RIM_R * np.sin(np.pi * sv) + RIM_R * 0.6 * np.sin(np.pi * min(sv * 3, 1)) * (sv < 0.34)
            rings.append(O + (I - O) * sv + out * bulge[..., None] if np.ndim(bulge) else O + (I - O) * sv + out * bulge)
        strips.append((loop, rings))
    return Vi, t, strips


RIM_R = 0.004                      # m, the rubber trim's roll beyond the cut edge


# ---------------------------------------------------------------- visor
# Royal_Left pixels: top line (centre line) and lower edge (the visor's side edge seen from the side), tip at u 220,
# rear end on the crown at u 1135 (its rear edge runs down to the side corner at u 1075, v 662).
VISOR_TOP = [(220, 334), (257, 323), (297, 322), (337, 322), (407, 321), (487, 322), (567, 323), (647, 326),
             (726, 329), (806, 334), (886, 340), (966, 347), (1045, 352), (1100, 356), (1135, 360)]      # rear end raised 3 mm: sits on the crown
VISOR_LOW = [(220, 334), (277, 377), (346, 416), (416, 454), (487, 491), (558, 528), (610, 600), (660, 660),
             (720, 712), (760, 722), (900, 692), (1000, 675), (1075, 662), (1110, 540), (1135, 380)]
# plan half width of the visor (Pinata Teal top view, 0.247 mm/px), by Royal_Left u
VISOR_PLAN = [(220, 0.0), (236, 0.0356), (276, 0.0652), (315, 0.0745), (395, 0.0800), (474, 0.0860),
              (554, 0.0921), (634, 0.0988), (713, 0.1058), (793, 0.1162), (872, 0.1212), (912, 0.1225),
              (1000, 0.090), (1075, 0.050), (1135, 0.0)]      # behind u 912 the visor lies on the shell
VISOR_T = 0.0035                   # m, visor thickness (moulded ABS)
VISOR_GAP = 0.0075                 # m, top surface off the shell where it lies over it (underside 4 mm clear)


def visor_surface(prof, nu=56, nphi=41):
    """Top surface of the visor as a grid (stations from the tip back to the rear, arch across)."""
    top = px2h(VISOR_TOP)
    low = px2h(VISOR_LOW)
    plan = np.array(VISOR_PLAN, float)
    us = np.r_[np.linspace(220, 330, 12), np.linspace(330, 1135, nu - 12)[1:]]
    ys = (us - U0) * S
    zt = np.interp(ys, top[:, 0], top[:, 1])
    zl = np.interp(ys, low[:, 0], low[:, 1])
    a = np.interp(us, plan[:, 0], plan[:, 1])
    phi = np.linspace(-1, 1, nphi)
    G = np.zeros((len(us), nphi, 3))
    for i, (y, z0, z1, ai) in enumerate(zip(ys, zt, zl, a)):
        c = 1 - np.cos(phi * np.pi / 2)
        z = z0 - (z0 - z1) * c ** 1.3
        x = ai * np.sin(phi * np.pi / 2)
        G[i] = np.c_[x, np.full(nphi, y), z]
    # lie over the shell where the shell is under it: never closer than VISOR_GAP
    flat = G.reshape(-1, 3)
    ins = prof.inside(flat[:, 1:])
    hw = np.zeros(len(flat))
    hw[ins] = shell_hw(prof, flat[ins, 1], flat[ins, 2])
    side = np.sign(flat[:, 0]) + (flat[:, 0] == 0)
    need = ins & (np.abs(flat[:, 0]) < hw + VISOR_GAP)
    flat[need, 0] = side[need] * (hw[need] + VISOR_GAP)
    return flat.reshape(G.shape)


def grid_faces(nr, nc, off=0, flip=False):
    F = []
    for i in range(nr - 1):
        for j in range(nc - 1):
            q = [off + i * nc + j, off + i * nc + j + 1, off + (i + 1) * nc + j + 1, off + (i + 1) * nc + j]
            F.append(q[::-1] if flip else q)
    return F


def thicken_grid(G, t, mat_top, mat_under, mat_edge, part):
    """A grid surface made solid: top, underside offset by t along its normals, edge strips all round."""
    nr, nc, _ = G.shape
    V = G.reshape(-1, 3)
    Ft = np.array(grid_faces(nr, nc))
    tris = np.vstack([Ft[:, [0, 1, 2]], Ft[:, [0, 2, 3]]])
    N = normals(V, tris)
    # top faces point up/out: orient by the centre of the grid
    c = V.mean(0)
    flip = np.mean(np.sum(N * (V - c), 1)) < 0
    if flip:
        N = -N
    Vu = V - N * t
    Ftop = np.array(grid_faces(nr, nc, 0, flip))
    uv_top = atlas_uvs(V, Ftop, visor=True)[0] if mat_top == "helmet_paint" else None
    o1 = part.add(V, Ftop, mat_top, None if uv_top is None else list(uv_top))
    part.top = (V, Ftop, N, uv_top)
    o2 = part.add(Vu, grid_faces(nr, nc, 0, not flip), mat_under)
    ring = ([(0, j) for j in range(nc)] + [(i, nc - 1) for i in range(1, nr)] +
            [(nr - 1, j) for j in range(nc - 2, -1, -1)] + [(i, 0) for i in range(nr - 2, 0, -1)])
    idx = [i * nc + j for i, j in ring]
    F = []
    for k in range(len(idx)):
        a, b = idx[k], idx[(k + 1) % len(idx)]
        q = [o1 + a, o1 + b, o2 + b, o2 + a]
        F.append(q if not flip else q[::-1])
    part.add(np.zeros((0, 3)), [], mat_edge)
    for f in F:
        part.F.append(f); part.M.append(mat_edge); part.UV.append(None)
    return o1


def build(body):
    Vo, Fo, prof = shell_outer()
    R, tr, info = fit_on_head(body, Vo, Fo, prof)
    skin = body["V"][head_skin(body)]
    skin_H = (skin - tr) @ R
    Vi, thick, strips = shell_solid(Vo, Fo, skin_H)
    shell = Part("helmet_shell")
    uv_o = atlas_uvs(Vo, Fo)[0]
    shell.add(Vo, Fo, "helmet_paint", list(uv_o))
    o_in = shell.add(Vi, Fo[:, ::-1], "helmet_liner")
    for loop, rings in strips:
        m = len(loop)
        ids = [loop] + [shell.add(r, [], "helmet_trim") + np.arange(m) for r in rings[1:-1]] + [o_in + loop]
        F = []
        for k in range(len(ids) - 1):
            for i in range(m):
                j = (i + 1) % m
                F.append([ids[k][i], ids[k + 1][i], ids[k + 1][j], ids[k][j]])
        o = len(shell.V)
        for f in F:
            shell.F.append(f); shell.M.append("helmet_trim"); shell.UV.append(None)
    visor = Part("helmet_visor")
    thicken_grid(visor_surface(prof), VISOR_T, "helmet_paint", "visor_under", "visor_under", visor)
    parts = [shell, visor]
    if PAINT or not os.path.exists(os.path.join(TEXDIR, "helmet_pinata.png")):
        Vt, Ft, Nt, UVt = visor.top
        info["paint"] = paint_atlas([(Vo, Fo, normals(Vo, Fo), uv_o), (Vt, Ft, Nt, UVt)],
                                    os.path.join(TEXDIR, "helmet_pinata.png"))
    for P in parts:                                   # faces without art: any UV (their materials have no image)
        P.UV = [u if u is not None else [(0.0, 0.0)] * len(f) for u, f in zip(P.UV, P.F)]
    for P in parts:
        P.V = P.V @ R.T + tr
    info.update(shell_thickness_mm=[round(float(thick.min()) * 1000, 1), round(float(thick.max()) * 1000, 1)])
    gparts, ginfo = build_goggle(body, (R, tr), prof)
    info.update(ginfo)
    return parts + gparts, info, (R, tr)


# ---------------------------------------------------------------- graphics: Leatt's Pinata Teal art, projected
REF = os.path.normpath(os.path.join(HERE, "..", "..", "reference", "leatt-gear", "helmet"))
PHOTOS = dict(isoleft="helmet85-kit_pinatateal_iso-left_leatt-us_1026000250_1920.png",
              isoright="helmet85-kit_pinatateal_iso-right-with-goggle_leatt-us_1026000250_1920.png",
              back="helmet85-kit_pinatateal_back_leatt-us_1026000250_1920.png",
              top="helmet85-kit_pinatateal_top_leatt-us_1026000250_1920.png")
# Pinhole cameras of Leatt's four Pinata Teal views in the helmet frame, fitted to the shell and visor outline
# (chamfer distance both ways, half resolution, Powell then Nelder-Mead): azimuth from the front towards his left
# and elevation of the camera (deg), roll (deg), distance (m), focal length (px), aim offset (m) from CAM_CTR.
CAM_CTR = np.array([0.0, -0.03, 0.0])
CAMS = dict(isoleft=[62.0789, 3.9144, -7.4058, 1.4021, 5653.2658, -0.0307, -0.0032, -0.0334],
            back=[186.6286, 10.703, -4.8924, 1.2116, 5632.7324, -0.0011, 0.0102, 0.002],
            top=[3.0441, 87.254, 0.2669, 1.4571, 5624.0378, 0.0002, -0.0141, -0.0449],
            isoright=[-59.1663, 8.6293, 8.1332, 1.8892, 7721.6883, 0.0325, 0.0004, -0.0393])
# the goggle and its strap cover the right side in Leatt's iso-right view: not the helmet's art (hand-drawn, px)
ISORIGHT_GOGGLE = [(215, 630), (560, 610), (800, 700), (1430, 700), (1470, 1000), (1440, 1260), (800, 1240),
                   (770, 1040), (560, 960), (215, 930)]
TEX = 2048
PAINT = False
ATLAS_K = 2150.0                   # texels per metre (2.15 px/mm)
BASE_WHITE = (226, 229, 235)


def cam_from(x):
    az, el, roll, d, f, tx, ty, tz = x
    a, e = math.radians(az), math.radians(el)
    dirn = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
    C = CAM_CTR + np.array([tx, ty, tz]) + dirn * d
    fwd = -dirn
    up0 = np.array([0, 0, 1.0]) if abs(e) < math.radians(80) else np.array([0, 1.0, 0])
    right = np.cross(fwd, up0); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    r = math.radians(roll)
    right, up = right * math.cos(r) + up * math.sin(r), up * math.cos(r) - right * math.sin(r)
    return C, np.vstack([right, up, fwd]), f


def cam_project(x, Q):
    C, Rm, f = cam_from(x)
    q = (Q - C) @ Rm.T
    return np.c_[960 + f * q[:, 0] / q[:, 2], 960 - f * q[:, 1] / q[:, 2]], q[:, 2]


# atlas islands: (name, origin u, v in texels, axes): side views by (y, z), top by (x, y), back/front by (x, z)
ISLANDS = dict(L=(0, 0), R=(820, 0), T=(0, 700), B=(600, 700), F=(1200, 700), V=(0, 1500))


def island_uv(name, P):
    """Texel coordinates of helmet-frame points in an island (u right, v up, origin at the island's corner)."""
    k = ATLAS_K
    ou, ov = ISLANDS[name]
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    if name == "L":
        u, v = (y + 0.225) * k, (z + 0.18) * k
    elif name == "R":
        u, v = (0.16 - y) * k, (z + 0.18) * k
    elif name == "T":
        u, v = (x + 0.14) * k, (0.16 - y) * k
    elif name in ("B", "F"):
        u, v = ((0.14 - x) if name == "B" else (x + 0.14)) * k, (z + 0.18) * k
    else:
        u, v = (x + 0.13) * k, (0.02 - y) * k
    return np.c_[ou + u, ov + v]


def face_island(N):
    ax, ay, az = np.abs(N).T
    isl = np.where((ax >= ay) & (ax >= az), np.where(N[:, 0] > 0, "L", "R"),
                   np.where(az >= ay, np.where(N[:, 2] > 0, "T", np.where(N[:, 0] > 0, "L", "R")),
                            np.where(N[:, 1] > 0, "B", "F")))
    return isl


def atlas_uvs(V, F, visor=False):
    """Face-corner UVs (0..1) for an outer surface, each face in the island of its normal (visor: V)."""
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    isl = np.full(len(F), "V") if visor else face_island(fn)
    UV = np.zeros((len(F), F.shape[1], 2))
    for name in np.unique(isl):
        m = isl == name
        P = V[F[m]].reshape(-1, 3)
        UV[m] = island_uv(name, P).reshape(m.sum(), F.shape[1], 2)
    return UV / TEX, isl


def rasterize(UV, P3, N3):
    """Texel centres covered by each triangle (UV in texels), with the interpolated 3D point and normal."""
    tex_idx, pts, nrm = [], [], []
    for (a, b, c), (pa, pb, pc), (na, nb, nc) in zip(UV, P3, N3):
        lo = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        hi = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
        q = np.c_[gx.ravel(), gy.ravel()] + 0.5
        T = np.array([b - a, c - a]).T
        det = np.linalg.det(T)
        if abs(det) < 1e-9:
            continue
        l = np.linalg.solve(T, (q - a).T).T
        w = np.c_[1 - l.sum(1), l]
        ok = (w >= -0.02).all(1)
        if not ok.any():
            continue
        w = w[ok]
        tex_idx.append(np.c_[gx.ravel()[ok], gy.ravel()[ok]])
        pts.append(w @ np.array([pa, pb, pc]))
        nrm.append(w @ np.array([na, nb, nc]))
    return np.vstack(tex_idx), np.vstack(pts), np.vstack(nrm)


def paint_atlas(surfaces, out_path):
    """Leatt's photos projected onto the outer surfaces: every texel takes the views that see it, weighted by how
    squarely they see it (cos^4), visible by a depth test, inside the photo's matte and (iso-right) not behind the
    goggle. Texels no view sees take the mirror point's colour (the art is symmetric), then the base white."""
    from PIL import Image, ImageDraw
    allidx, allP, allN = [], [], []
    for V, F, N, UV in surfaces:
        T = F if F.shape[1] == 3 else np.vstack([F[:, [0, 1, 2]], F[:, [0, 2, 3]]])
        UVt = UV if F.shape[1] == 3 else np.vstack([UV[:, [0, 1, 2]], UV[:, [0, 2, 3]]])
        idx, P, Nn = rasterize(UVt * TEX, V[T], N[T])
        allidx.append(idx); allP.append(P); allN.append(Nn)
    idx, P, Nn = np.vstack(allidx), np.vstack(allP), np.vstack(allN)
    Nn /= np.linalg.norm(Nn, axis=1)[:, None]
    acc = np.zeros((len(P), 3)); wsum = np.zeros(len(P))
    acc_m = np.zeros((len(P), 3)); wsum_m = np.zeros(len(P))
    for view, x in CAMS.items():
        if x is None:
            continue
        img = np.array(Image.open(os.path.join(REF, PHOTOS[view])).convert("RGBA")).astype(float)
        if view == "isoright":
            m = Image.new("L", (1920, 1920), 0)
            ImageDraw.Draw(m).polygon(ISORIGHT_GOGGLE, fill=255)
            img[np.array(m) > 0, 3] = 0
        C, Rm, f = cam_from(x)
        for mirror in (False, True):
            Q = P * ([-1, 1, 1] if mirror else 1)
            Nq = Nn * ([-1, 1, 1] if mirror else 1)
            uv, depth = cam_project(x, Q)
            # depth buffer from the surfaces themselves, 4 px cells
            cell = np.floor(uv / 4).astype(int)
            okc = (cell >= 0).all(1) & (cell < 480).all(1)
            zb = np.full((480, 480), np.inf)
            np.minimum.at(zb, (cell[okc, 1], cell[okc, 0]), depth[okc])
            vis = np.zeros(len(P), bool)
            vis[okc] = depth[okc] <= zb[cell[okc, 1], cell[okc, 0]] + 0.004
            view_dir = (C - Q) / np.linalg.norm(C - Q, axis=1)[:, None]
            cosv = np.clip(np.sum(Nq * view_dir, 1), 0, 1)
            ui = np.clip(np.round(uv).astype(int), 0, 1919)
            px = img[ui[:, 1], ui[:, 0]]
            w = cosv ** 4 * vis * (px[:, 3] > 200) * (cosv > 0.15)
            if mirror:
                acc_m += w[:, None] * px[:, :3]; wsum_m += w
            else:
                acc += w[:, None] * px[:, :3]; wsum += w
    col = np.tile(np.array(BASE_WHITE, float), (len(P), 1))
    has_m = wsum_m > 1e-4
    col[has_m] = acc_m[has_m] / wsum_m[has_m, None]
    has = wsum > 0.02
    col[has] = acc[has] / wsum[has, None]
    out = np.zeros((TEX, TEX, 3)); cnt = np.zeros((TEX, TEX))
    ii = np.clip(idx, 0, TEX - 1)
    np.add.at(out, (TEX - 1 - ii[:, 1], ii[:, 0]), col)
    np.add.at(cnt, (TEX - 1 - ii[:, 1], ii[:, 0]), 1)
    filled = cnt > 0
    out[filled] /= cnt[filled, None]
    # bleed the islands' edges by a few texels so filtering never reaches the empty atlas
    from scipy import ndimage
    for _ in range(4):
        grown = ndimage.grey_dilation(np.where(filled[..., None], out, 0), size=(3, 3, 1))
        out = np.where(filled[..., None], out, grown)
        filled = ndimage.binary_dilation(filled)
    out[~filled] = BASE_WHITE
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(out_path)
    return dict(texels=int(len(P)), seen=float(has.mean()), mirrored=float((~has & has_m).mean()))


# ---------------------------------------------------------------- goggle: Leatt Velocity 5.5 Iriz, Pinata Teal
G_HALF_W = 0.094                   # m, frame half width (fills the port at eye height, outriggers just outside it)
G_TOP, G_BOT = 0.035, -0.057       # m, frame top and bottom at the sides, from his eye centres (94 mm: MY27 side
                                   # view with the goggle on, 386 px x 0.241 mm/px = 93 mm; fills the port as in 09)
G_NOSE, G_NOSE_W = 0.030, 0.042   # m, the nose cut-out: rise of the bottom edge at the centre, half width
G_RIM = (0.008, 0.009, 0.010)      # m, frame rim width at the top, sides and bottom (Leatt goggle iso)
G_DEPTH, G_FOAM = 0.020, 0.014     # m, frame depth behind the lens; triple-layer face foam (compressed)
G_PLAN = (0.115, 0.075)            # m, lens plan: ellipse half axes (170 deg WideVision wrap, 36 mm back at the ends)
STRAP_W, STRAP_T = 0.045, 0.002    # m, strap width (Leatt) and thickness
# strap centre line on the shell, Royal_Left px: its front point from Leatt's MY27 side view (goggle on) mapped
# through the registration; it runs back 5 deg down in the helmet frame (13 deg up in his rest frame) as on his
# photo 07, lower than Leatt's product shot (7 deg up)
STRAP_LINE = [(1071, 918), (1615, 966)]


def logo_polys(x0=0.0, y0=0.0, h=1.0, shear=0.25):
    """The LEATT logotype as polygons (cap height h, italic shear): L, E (detached middle arm), A without its bar,
    TT under one top bar. Units of h; y up."""
    L = [[(0, 0), (0.75, 0), (0.75, 0.22), (0.22, 0.22), (0.22, 1), (0, 1)]]
    E = [[(0, 0), (0.75, 0), (0.75, 0.22), (0.22, 0.22), (0.22, 0.78), (0.75, 0.78), (0.75, 1), (0, 1)],
         [(0.30, 0.39), (0.70, 0.39), (0.70, 0.61), (0.30, 0.61)]]
    A = [[(0, 0), (0.25, 0), (0.5, 0.66), (0.75, 0), (1.0, 0), (0.62, 1), (0.38, 1)]]
    TT = [[(0, 0.78), (1.62, 0.78), (1.62, 1), (0, 1)], [(0.29, 0), (0.51, 0), (0.51, 0.78), (0.29, 0.78)],
          [(1.11, 0), (1.33, 0), (1.33, 0.78), (1.11, 0.78)]]
    out, x = [], 0.0
    for glyph, w in ((L, 0.75), (E, 0.75), (A, 1.0), (TT, 1.62)):
        for poly in glyph:
            out.append([(x0 + (x + px + shear * py) * h, y0 + py * h) for px, py in poly])
        x += w + 0.14
    return out, (x - 0.14 + shear) * h


def strap_texture(path, w=2048, h=160):
    """Strap print: iridescent gradient (orange-yellow at the goggle, magenta, purple, teal-green round the back;
    Leatt goggle iso and Damien's 07, 09) with a large white LEATT on each side reading along the strap from the
    left outrigger (so it reads correctly on both sides from outside)."""
    from PIL import Image, ImageDraw
    s = np.abs(np.linspace(-1, 1, w))                      # 1 at the outriggers, 0 at the back centre
    stops = [(0.0, (40, 190, 160)), (0.30, (60, 175, 175)), (0.48, (110, 60, 170)), (0.62, (170, 30, 150)),
             (0.76, (225, 40, 120)), (0.88, (245, 120, 60)), (1.0, (250, 200, 60))]
    t = 1 - s
    cols = np.array([np.interp(1 - t, [p for p, _ in stops], [c[k] for _, c in stops]) for k in range(3)]).T
    img = np.repeat(cols[None, :, :], h, axis=0)
    yy = np.linspace(0, 1, h)[:, None]
    img = img * (0.92 + 0.08 * np.cos(yy * 9.0 + np.linspace(0, 40, w)[None, :] * 0.2))[..., None]   # sheen bands
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    ch = 0.72 * h
    for side in (0, 1):
        polys, lw = logo_polys(0, 0, ch)
        start = 0.06 * w if side == 0 else w - 0.06 * w - (0.5 * w - 0.06 * w) + 0.5 * w - lw - 0.0 * w
        start = 0.07 * w if side == 0 else 0.93 * w - lw
        # side 1 (right side) is read from outside going towards its outrigger: same direction along the strap
        for poly in polys:
            d.polygon([(start + px, h * 0.5 + ch / 2 - py) for px, py in poly], fill=(250, 250, 250))
    im.save(path)


def outrigger_texture(path, w=256, h=512):
    """Black outriggers with the vertical white LEATT, letter tops towards the frame on both sides (Pinata
    iso-right: reads top to bottom on the right side). Left half of the image: the left outrigger (text turned
    anticlockwise), right half: the right one (clockwise); front of each at the image's outer edge."""
    from PIL import Image, ImageDraw
    band = Image.new("RGB", (h, w), (16, 16, 18))
    d = ImageDraw.Draw(band)
    ch = 0.5 * w
    polys, lw = logo_polys(0, 0, ch)
    x0 = (h - lw) / 2
    for poly in polys:
        d.polygon([(x0 + px, w / 2 + ch / 2 - py) for px, py in poly], fill=(245, 245, 245))
    im = Image.new("RGB", (2 * w, h))
    im.paste(band.rotate(90, expand=True), (0, 0))
    im.paste(band.rotate(-90, expand=True), (w, 0))
    im.save(path)


def goggle_outline(z_e, inset=(0.0, 0.0, 0.0), n=96):
    """Front outline (x, z) of the frame, closed, starting at the top centre going towards +x. inset: (top, side,
    bottom) in metres for the lens opening."""
    it, isd, ib = inset
    W = G_HALF_W - isd
    out = []
    for k in range(n):
        th = 2 * np.pi * k / n
        c, s_ = np.sin(th), np.cos(th)                    # x-ish, z-ish
        x = W * np.sign(c) * abs(c) ** 0.35
        top = z_e + G_TOP - it - 0.014 * (x / G_HALF_W) ** 2      # follows the port's brow edge
        bot = z_e + G_BOT + ib
        tt = abs(x) / G_NOSE_W
        bot = bot + (G_NOSE + 0.6 * ib) * ((1 - tt * tt) ** 2 if tt < 1 else 0.0)
        zc, zh = 0.5 * (top + bot), 0.5 * (top - bot)
        z = zc + zh * np.sign(s_) * abs(s_) ** 0.35
        out.append((x, z))
    return np.array(out)


def lens_y(x, y_c):
    a, b = G_PLAN
    return y_c + b * (1 - np.sqrt(np.clip(1 - (x / a) ** 2, 0, 1)))


def ring_quads(rings, part, mat, closed=True):
    m = len(rings[0])
    ids = [part.add(r, [], mat) + np.arange(m) for r in rings]
    for k in range(len(ids) - (0 if closed else 1)):
        A_, B_ = ids[k], ids[(k + 1) % len(ids)]
        for i in range(m):
            j = (i + 1) % m
            part.F.append([A_[i], A_[j], B_[j], B_[i]]); part.M.append(mat); part.UV.append(None)
    return ids


def build_goggle(body, Rt, prof):
    """The goggle in the rest frame (MB): frame, double lens, face foam conforming to his face, outriggers,
    bare tear-off posts, and the strap round the helmet's back."""
    R, t = Rt
    L = head_landmarks(body)
    z_e = L["eye"][2]
    skin = body["V"][head_skin(body, ("head",))]
    front = skin[skin[:, 1] < L["eye"][1] + 0.02]
    tree = cKDTree(front[:, [0, 2]])

    def face_y(x, z):
        out = []
        for xi, zi in zip(np.atleast_1d(x), np.atleast_1d(z)):
            nb = tree.query_ball_point([xi, zi], 0.008)
            out.append(front[nb, 1].min() if nb else np.nan)
        return np.array(out)

    oo = goggle_outline(z_e)
    ii = goggle_outline(z_e, G_RIM)
    # foam back on his face, the frame's back the foam's depth in front of it, the lens the frame's depth in front
    fy = face_y(oo[:, 0] * 0.97, oo[:, 1])
    fy = np.where(np.isnan(fy), np.nanmax(fy), fy)
    lens_back = np.min(fy - (G_FOAM + G_DEPTH) - (lens_y(oo[:, 0], 0.0)))
    y_c = lens_back
    gog = Part("goggle_frame")
    yo, yi = lens_y(oo[:, 0], y_c), lens_y(ii[:, 0], y_c)
    fr = [np.c_[oo[:, 0], yo - 0.002, oo[:, 1]], np.c_[ii[:, 0], yi - 0.002, ii[:, 1]],
          np.c_[ii[:, 0], yi + G_DEPTH, ii[:, 1]], np.c_[oo[:, 0], yo + G_DEPTH, oo[:, 1]]]
    ring_quads(fr, gog, "goggle_frame")
    # face foam: frame back to his face, conforming
    fo = goggle_outline(z_e, (-0.001, -0.001, -0.001))
    fi = goggle_outline(z_e, tuple(r + 0.004 for r in G_RIM))
    yb_o = np.maximum(face_y(fo[:, 0] * 0.97, fo[:, 1]), lens_y(fo[:, 0], y_c) + G_DEPTH + 0.004) - 0.001
    yb_i = np.maximum(face_y(fi[:, 0] * 0.97, fi[:, 1]), lens_y(fi[:, 0], y_c) + G_DEPTH + 0.004) - 0.001
    yb_o = np.where(np.isnan(yb_o), lens_y(fo[:, 0], y_c) + G_DEPTH + G_FOAM, yb_o)
    yb_i = np.where(np.isnan(yb_i), lens_y(fi[:, 0], y_c) + G_DEPTH + G_FOAM, yb_i)
    foam = Part("goggle_foam")
    ring_quads([np.c_[fo[:, 0], lens_y(fo[:, 0], y_c) + G_DEPTH - 0.001, fo[:, 1]],
                np.c_[fi[:, 0], lens_y(fi[:, 0], y_c) + G_DEPTH - 0.001, fi[:, 1]],
                np.c_[fi[:, 0], yb_i, fi[:, 1]], np.c_[fo[:, 0], yb_o, fo[:, 1]]], foam, "goggle_foam")
    # lens: two sheets 2 mm apart, 3 mm larger than the opening (edges in the frame's groove)
    lo = goggle_outline(z_e, tuple(r - 0.003 for r in G_RIM), n=96)
    from scipy.spatial import Delaunay as _D
    gx, gz = np.meshgrid(np.linspace(lo[:, 0].min(), lo[:, 0].max(), 40), np.linspace(lo[:, 1].min(), lo[:, 1].max(), 14))
    pts = np.vstack([lo, np.c_[gx.ravel(), gz.ravel()]])
    o = Profile.__new__(Profile)
    o.outline = lo
    keep = np.r_[np.ones(len(lo), bool), Profile.inside(o, pts[len(lo):]) &
                 (cKDTree(lo).query(pts[len(lo):])[0] > 0.003)]
    pts = pts[keep]
    T = _D(pts).simplices
    T = T[Profile.inside(o, pts[T].mean(1))]
    lens = Part("goggle_lens")
    for dy, flip in ((0.0, False), (0.002, True)):
        V = np.c_[pts[:, 0], lens_y(pts[:, 0], y_c) + 0.004 + dy, pts[:, 1]]
        lens.add(V, T[:, ::-1] if not flip else T, "goggle_lens")
    # outriggers (both sides) and bare tear-off posts
    parts_ = [gog, foam, lens]
    orig = Part("goggle_outriggers")
    posts = Part("goggle_posts")
    ends = {}
    for sgn in (1, -1):
        x0 = sgn * G_HALF_W
        y0 = lens_y(G_HALF_W, y_c)
        P0 = np.array([x0 - sgn * 0.004, y0 + 0.002, z_e - 0.002])
        P1 = np.array([x0 + sgn * 0.010, y0 + 0.042, z_e - 0.002])
        d = (P1 - P0) / np.linalg.norm(P1 - P0)
        nrm = np.cross(d, [0, 0, 1.0]) * sgn
        nrm /= np.linalg.norm(nrm)
        box = []
        for (u, hz, off) in ((0, 1, 0), (1, 1, 0), (1, -1, 0), (0, -1, 0), (0, 1, 1), (1, 1, 1), (1, -1, 1), (0, -1, 1)):
            box.append(P0 + (P1 - P0) * u + np.array([0, 0, 0.025 * hz]) + nrm * (0.007 * off - 0.0035))
        box = np.array(box)
        quads = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]
        if sgn < 0:
            quads = [q[::-1] for q in quads]
        uv = [None] * 6
        outer = 1                                           # the face with offset +1 is the outer face
        uvq = [(0, 1), (1, 1), (1, 0), (0, 0)]
        uvs = [[(0.5, 0.5)] * 4 for _ in quads]
        # outer face corners (front bottom, back bottom, back top, front top); image halves per side
        if sgn > 0:
            uvs[1] = [(0.0, 0.0), (0.5, 0.0), (0.5, 1.0), (0.0, 1.0)]
        else:
            uvs[1] = [(1.0, 1.0), (0.5, 1.0), (0.5, 0.0), (1.0, 0.0)]     # front top, back top, back bottom, front bottom
        orig.add(box, quads, "goggle_outrigger", uvs)
        ends[sgn] = P1 + nrm * 0.0035
        c = np.array([sgn * 0.083, lens_y(0.083, y_c) - 0.003, z_e + 0.006])
        cyl = []
        for k in range(10):
            a_ = 2 * np.pi * k / 10
            cyl.append(c + np.array([0.0025 * np.cos(a_), 0, 0.0025 * np.sin(a_)]))
        cyl = np.array(cyl)
        ring_quads([cyl, cyl + [0, -0.004, 0]], posts, "goggle_post")
    parts_ += [orig, posts]
    parts_.append(build_strap(Rt, prof, ends))
    return parts_, dict(lens_centre_ahead_of_eye_mm=round(float(L["eye"][1] - y_c) * 1000, 1))


def build_strap(Rt, prof, ends, n=160):
    """Strap round the helmet's back: from each outrigger's rear end onto the shell, along the line traced from
    Leatt's MY27 side view, across the back. Width across the band, laid on the shell (2.5 mm off it)."""
    R, t = Rt
    L0, L1 = px2h(STRAP_LINE)
    end_H = {k: R.T @ (v - t) for k, v in ends.items()}
    ys = np.linspace(0, 1, n)
    rows = []
    for sgn in (1, -1):
        e = end_H[sgn]
        y_back = prof.rim_crown[np.argmin(np.abs(prof.rim_crown[:, 1] - L1[1]) + (prof.rim_crown[:, 0] < 0) * 9), 0]
        Y = e[1] + (y_back - e[1]) * ys
        Z = np.interp(Y, [e[1], L0[0], L1[0], y_back + 0.01], [e[2], L0[1], L1[1], L1[1] + (y_back - L1[0]) * 0.12])
        X = np.zeros(n)
        ins = prof.inside(np.c_[Y, Z])
        X[ins] = shell_hw(prof, Y[ins], Z[ins])
        X = X + 0.004
        k = np.clip((Y - e[1]) / 0.04, 0, 1)
        X = np.maximum(X, abs(e[0]) * (1 - k))
        X[-1] = 0.0
        Y[-1] = Y[-1] + 0.004
        rows.append(np.c_[sgn * X, Y, Z])
    path = np.vstack([rows[0], rows[1][::-1][1:]])         # left outrigger -> back -> right outrigger
    tg = np.gradient(path, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None]
    w = np.cross(tg, np.c_[np.sign(path[:, 0]), np.zeros(len(path)), np.zeros(len(path))] + [0, 1e-9, 0])
    up = np.array([0, 0, 1.0])
    w = up - tg * (tg @ up)[:, None]
    w /= np.linalg.norm(w, axis=1)[:, None]
    lo_, hi_ = path - w * STRAP_W / 2, path + w * STRAP_W / 2
    # keep both edges on the outside of the shell
    for E_ in (lo_, hi_):
        ins = prof.inside(E_[:, 1:])
        hw = np.zeros(len(E_))
        hw[ins] = shell_hw(prof, E_[ins, 1], E_[ins, 2]) + 0.004
        need = np.abs(E_[:, 0]) < hw
        E_[need, 0] = np.sign(path[need, 0] + 1e-9) * hw[need]
    strap = Part("goggle_strap")
    m = len(path)
    outn = np.c_[path[:, 0], path[:, 1] - 0.0, np.zeros(m)]          # outwards in plan from the shell's centre
    outn /= np.linalg.norm(outn, axis=1)[:, None]
    rings = [lo_, hi_, hi_ - outn * STRAP_T * 0 + (hi_ - path) * 0, lo_]
    s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    s_ /= s_[-1]
    o1 = strap.add(lo_, [], "goggle_strap")
    o2 = strap.add(hi_, [], "goggle_strap")
    inner_lo = lo_ - (lo_ - np.c_[np.zeros(m), lo_[:, 1:]]) * 0 - outn * STRAP_T
    inner_hi = hi_ - outn * STRAP_T
    o3 = strap.add(inner_hi, [], "goggle_strap_in")
    o4 = strap.add(inner_lo, [], "goggle_strap_in")
    for i in range(m - 1):
        j = i + 1
        uv = [(s_[i], 0.0), (s_[j], 0.0), (s_[j], 1.0), (s_[i], 1.0)]
        strap.F.append([o1 + i, o1 + j, o2 + j, o2 + i]); strap.M.append("goggle_strap"); strap.UV.append(uv)
        for a_, b_, mat in ((o2, o3, "goggle_strap_in"), (o3, o4, "goggle_strap_in"), (o4, o1, "goggle_strap_in")):
            strap.F.append([a_ + i, a_ + j, b_ + j, b_ + i]); strap.M.append(mat); strap.UV.append([(0.5, 0.5)] * 4)
    # the band was built in the helmet frame: to the rest frame
    strap.V = strap.V @ R.T + t
    strap.frame = "MB"
    return strap


def hidden_skin(body, Rt, prof=None):
    """His scalp and the skin the shell covers completely (hide_body): head skin inside the shell, more than
    40 mm above its lower edge and more than 30 mm behind the face port's side edge, so nothing that can be seen
    through the port or from below is hidden."""
    prof = prof or Profile()
    R, t = Rt
    idx = head_skin(body)
    q = (body["V"][idx] - t) @ R
    ins = prof.inside(q[:, 1:])
    hw = np.zeros(len(q))
    hw[ins] = half_width(prof, q[ins, 1], q[ins, 2], smooth=False)
    low = np.interp(q[:, 1], prof.lower[::-1, 0], prof.lower[::-1, 1])
    port_back = prof.port[:, 0].max()
    keep = ins & (np.abs(q[:, 0]) < hw - 0.005) & (q[:, 2] > low + 0.040) & (q[:, 1] > port_back + 0.030)
    return idx[keep]


def extras(body, parts, Rt):
    return dict(hide_body=hidden_skin(body, Rt))


MATERIALS = {
    "helmet_paint": dict(image="helmet_pinata.png", rough=0.22, coat=1.0),       # Pinata Teal art, gloss clear
    "helmet_trim": dict(rgb=[18, 18, 20], rough=0.65),
    "helmet_liner": dict(rgb=[34, 34, 38], rough=0.9, sheen=0.4),
    "visor_under": dict(rgb=[214, 217, 222], rough=0.45),
    "goggle_frame": dict(rgb=[196, 28, 78], rough=0.35, coat=0.3),         # raspberry pink (his photos 07, 09)
    "goggle_foam": dict(rgb=[46, 46, 50], rough=0.95, sheen=0.6),
    "goggle_lens": dict(rgb=[214, 190, 226], rough=0.02, transmission=1.0,  # Iriz Purple, 78 % VLT
                        thin_film=dict(thickness_nm=520, ior=1.6)),         # (thin film: not read by build_rider yet)
    "goggle_post": dict(rgb=[22, 22, 24], rough=0.4),
    "goggle_outrigger": dict(rough=0.45, image="goggle_outrigger.png"),
    "goggle_strap": dict(rough=0.7, sheen=0.3, image="goggle_strap.png"),
    "goggle_strap_in": dict(rgb=[24, 24, 26], rough=0.8),
}


def write_npz(path, parts, extra=None):
    mats = sorted({m for P in parts for m in P.M})
    out = dict(names=np.array([P.name for P in parts]), mats=np.array(mats),
               materials=json.dumps({m: MATERIALS[m] for m in mats}))
    for P in parts:
        FS = np.array([len(f) for f in P.F])
        out[P.name + "__V"] = P.V.astype(np.float64)
        out[P.name + "__F"] = np.concatenate([np.asarray(f) for f in P.F]).astype(np.int64)
        out[P.name + "__FS"] = FS
        out[P.name + "__M"] = np.array([mats.index(m) for m in P.M])
        out[P.name + "__bone"] = np.array(P.bone)
        if all(u is not None for u in P.UV):
            out[P.name + "__UV"] = np.concatenate([np.asarray(u, float) for u in P.UV])
    if extra:
        out.update(extra)
    np.savez_compressed(path, **out)


if __name__ == "__main__":
    body = np.load(sys.argv[1])
    PAINT = "--paint" in sys.argv
    os.makedirs(TEXDIR, exist_ok=True)
    strap_texture(os.path.join(TEXDIR, "goggle_strap.png"))
    outrigger_texture(os.path.join(TEXDIR, "goggle_outrigger.png"))
    parts, info, Rt = build(body)
    write_npz(sys.argv[2], parts, extras(body, parts, Rt))
    print(json.dumps(info), sum(len(P.V) for P in parts), "vertices")
