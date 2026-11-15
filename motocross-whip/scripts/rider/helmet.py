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
  ART       the Pinata Teal print, the brow badge included, redrawn flat by helmet_art.py (traced in Leatt's four
            Pinata photos through PRINT_CAMS, the cameras solved with all the photos, research/helmet-ba.json;
            logos from Leatt's own files): no studio light in the texture.
            The paint is that print under a gloss clear coat (MATERIALS["helmet_paint"]).
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
# Joint front fit phase 2 (decision 51): the chin bar refitted through the solved side cameras (research/
# helmet-ba.json: Royal_Left, MY27 left and right; scratch chinfit.py, chinapply.py). Each traced point of the chin
# front (the centre plane's rim) and of the lower edge (the near side's free edge) moved along its normal by the three
# photos' mean offset between their silhouette and the model's: the chin front 2.3 to 5.6 mm back and down (it stood
# 4 to 6 mm forward of all three photos, its top edge high; 1.8 to 2.5 mm at the mouthpiece's step, where the
# cameras spread most), tapered to nothing at its corner with the lower edge; the chin bar's top (FACE_PORT's first
# seven points) follows the junction's 4 mm, tapered to nothing at its seventh; the lower edge 1 to 2.5 mm up from u
# 510 to 865, tapered to nothing at u 1022. Behind that the side photos put the lower edge 2 to 3 mm higher still,
# but the back views' outline at z = -130 mm holds it (the outline test): left for the next solve.
LOWER_EDGE = [
    (1497, 1414), (1458, 1422), (1419, 1432), (1380, 1437), (1340, 1440), (1300, 1443), (1260, 1446),
    (1220, 1449), (1181, 1452), (1141, 1455), (1101, 1459), (1061, 1463), (1022, 1471), (982.5, 1475.4),
    (942.0, 1480.9), (902.7, 1485.6), (863.4, 1490.7), (823.5, 1498.7), (784.6, 1506.6), (745.7, 1515.1), (705.8, 1522.6),
    (666.9, 1531.1), (628.2, 1538.9), (589.5, 1546.4), (549.8, 1553.3), (509.9, 1560.6), (471, 1569), (432, 1578),
    (393, 1585), (353, 1591), (314, 1596), (294, 1598)]
CHIN_FRONT = [
    (294, 1598), (275.1, 1587.3), (268.8, 1572.5), (270.5, 1547.6), (271.1, 1514.3), (269.4, 1482.2), (264.8, 1451.0),
    (260.4, 1419.5), (258.6, 1388.7), (259.4, 1358.3), (258.2, 1328.9), (245.7, 1296.8), (232.7, 1268.4), (224.4, 1241.4),
    (225.8, 1231.6), (236.0, 1221.7), (252.2, 1204.9), (273.2, 1181.0), (294.0, 1158.6), (314.6, 1138.5), (340.4, 1125.6),
    (368.3, 1115.9), (382.2, 1113.4)]
FACE_PORT = [                    # chin bar top, the port's side edge (inner edge of the trim), brow edge
    (382.2, 1113.4), (389.5, 1123.9), (398.8, 1134.3), (412.1, 1138.7), (442.4, 1144.1), (473.7, 1144.6), (505, 1144),
    (536, 1146), (566, 1135), (592, 1116), (621, 1104), (652, 1096), (683, 1090), (708, 1071),
    (726, 1045), (735, 1015), (740, 983), (742, 951), (744, 919), (746, 887), (750, 860),
    (746, 842), (731, 835), (704, 819), (676, 806), (649, 788), (625, 768), (597, 752),
    (569, 738), (548, 724), (539, 703)]
# Round 2: in the side photo the port's notch is bounded by the cheek pads, which fill the opening ahead of the
# shell's edge; the shell's own edge (the rubber trim's inner edge) shows in Leatt's Pinata iso-left photo (no
# goggle). Its rear part, picked on that photo (px): chin bar top (816, 1131) to (1163, 1120), side edge (1186, 1090)
# to (1192, 800), brow edge (1158, 795) to (950, 770). Joint front fit (decision 47): cast onto the shell through the
# solved iso-left camera (helmet.PRINT_CAMS, research/helmet-ba.json; round 2's single-photo camera, CAMS, put the
# edge 16 to 18 mm too far back: through the solved camera it landed 75 to 80 px behind the photo's edge). Helmet
# frame (y, z), m. FACE_PORT keeps its centre parts (the chin bar top's first seven points, the brow edge from
# its 26th).
PORT_REAR = [(-0.1421, -0.0620), (-0.1319, -0.0657), (-0.1214, -0.0692), (-0.1109, -0.0715), (-0.1000, -0.0727),
             (-0.0886, -0.0722), (-0.0793, -0.0694), (-0.0744, -0.0631), (-0.0721, -0.0520), (-0.0700, -0.0362),
             (-0.0677, -0.0203), (-0.0660, -0.0045), (-0.0651, 0.0022), (-0.0723, 0.0045), (-0.0828, 0.0073),
             (-0.0895, 0.0129), (-0.1000, 0.0208), (-0.1086, 0.0259)]
PORT_KEEP = (7, 25)                # FACE_PORT points kept: [:7] (chin bar top) and [25:] (brow edge)
# The port the build uses. "iso" (decision 47): the cut edge above, 16 to 23 mm behind the side photo's notch, with
# the cheek pads in the opening ahead of it. "side": FACE_PORT as traced at Royal_Left's notch (rounds 1 to 4).
PORT = "iso"


def port_outline(kind=None):
    """The face port's edge in the helmet frame (y, z): FACE_PORT, or ("iso") its centre parts round the iso-left
    rear part."""
    P = px2h(FACE_PORT)
    if (kind or PORT) == "side":
        return P
    return np.vstack([P[:PORT_KEEP[0]], PORT_REAR, P[PORT_KEEP[1]:]])


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


RIM_FINE = 0.00025                 # m, rim sampling for the width field's distances (fair surface, see below)
RIM_LAM = (3e-8, 5e-9)             # smoothing spline weights, crown and chin rims (largest departures 0.43, 0.25 mm)


def fair_curve(P, lam):
    """A C2 curve through traced points (smoothing splines in x and y over the chord length): a polyline through
    the 1 px tracing has a corner at every point, and the width field's distance to the rim carried those corners
    into the shell as ridges near the centre line (helmet round 2)."""
    from scipy.interpolate import make_smoothing_spline
    P = np.asarray(P, float)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    sy, sz = make_smoothing_spline(s, P[:, 0], lam=lam), make_smoothing_spline(s, P[:, 1], lam=lam)
    t = np.linspace(0, s[-1], int(s[-1] / 0.0002) + 2)
    C = np.c_[sy(t), sz(t)]
    C[0], C[-1] = P[0], P[-1]                      # the ends stay where the free edges meet them
    return C


class Profile:
    """The side outline in the helmet frame: two rims (crown and back; chin front) and the free edges."""

    def __init__(self, step=0.003, port=None):
        self.port_kind = port or PORT
        crown = np.vstack([CROWN_UNDER_VISOR, CROWN_BACK])
        # the width field measures distances to the rims sampled every 0.25 mm: with the 3 mm outline samples the
        # nearest-sample distance scalloped by up to 0.6 mm at 2 mm from the rim (x ~ sqrt(d) there), which stood
        # as ridges 20 mm either side of the centre line on main's crown back (normal turn 229 /m)
        crown_c = fair_curve(px2h(crown), RIM_LAM[0])
        chin_c = fair_curve(px2h(CHIN_FRONT), RIM_LAM[1])
        self.rim_crown = resample_open(crown_c, step)
        self.lower = resample_open(smooth_open(px2h(LOWER_EDGE), 2), step)
        self.rim_chin = resample_open(chin_c, step)
        self.fine_crown = resample_open(crown_c, RIM_FINE)
        self.fine_chin = resample_open(chin_c, RIM_FINE)
        self.ftree_crown = cKDTree(self.fine_crown)
        self.ftree_chin = cKDTree(self.fine_chin)
        self.port = resample_open(smooth_open(port_outline(self.port_kind), 2), step)
        # closed domain outline, counter-clockwise in (y, z)? order: brow -> crown -> back -> lower -> chin -> port
        self.outline = np.vstack([self.rim_crown, self.lower[1:], self.rim_chin[1:], self.port[1:-1]])
        self.tree_crown = cKDTree(self.rim_crown)
        self.tree_chin = cKDTree(self.rim_chin)
        # the same without the port cut (closed by the chord across the face): the smoothing's domain, so the
        # surface does not depend on where the port is cut and is not pulled in beside its edge
        self.outline_uncut = np.vstack([self.rim_crown, self.lower[1:], self.rim_chin[1:]])
        o = self.outline
        self.area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])

    def inside(self, P, uncut=False):
        o = self.outline_uncut if uncut else self.outline
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
# Half width by height (back view) and plan factor by y (top view). Round 1 fitted them with L_CROWN and P_CROWN to
# Leatt's back and top views through hand-fitted cameras (residuals 1.6 mm back, 2.3 mm top) and evened out the
# fit's dip at z = 0 by hand. Round 3 (decision 46) refitted W_Z between z = -0.13 and +0.06 m (knots every 10 mm)
# and Q_Y's knots at y 0 to 0.12 to the shell's outline through the bundle adjustment's cameras (helmet_ba.py,
# research/helmet-ba.json) in Pinata back, V25 white back and Pinata top: least squares on the outline vertices'
# offsets binned by z (back views) and y (top view), a smoothness penalty on W's second differences. Before: the
# back views' outline 2.3 to 3.5 mm inside the model at z -0.03 to +0.02 (a waist: the shell narrows above its
# shoulder) and 2.5 to 3.4 mm outside it at z -0.06 to -0.04 (the shoulder, a moulded corner where the lower shell
# flares out) and at z -0.13 to -0.11; Pinata and V25 agree within 0.5 mm, MY27 shows the same with its strap on.
# After: every 10 mm bin within 1.0 mm in the three views (rms 0.43 mm). The shoulder is a sharp corner on Leatt's
# shell; the 10 mm smoothing below rounds it (about 1 mm left either side of it).
W_Z = np.array([[-0.20, 0.1115], [-0.16, 0.1155], [-0.13, 0.1221], [-0.12, 0.1234], [-0.11, 0.1247],
                [-0.10, 0.1256], [-0.09, 0.1265], [-0.08, 0.1285], [-0.07, 0.1322], [-0.06, 0.1358],
                [-0.05, 0.1368], [-0.04, 0.1344], [-0.03, 0.1313], [-0.02, 0.1297], [-0.01, 0.1287],
                [0.00, 0.1270], [0.01, 0.1254], [0.02, 0.1265], [0.03, 0.1296], [0.04, 0.1320], [0.05, 0.1321],
                [0.06, 0.1314], [0.08, 0.1322], [0.12, 0.1342], [0.16, 0.1362]])
Q_Y = np.array([[-0.30, 0.9126], [-0.04, 0.9126], [0.00, 0.9753], [0.04, 0.9469], [0.08, 0.9673],
                [0.12, 1.0198], [0.16, 1.1211]])


def falloff(t, p):
    t = np.clip(t, 0.0, 1.0)
    return (1.0 - (1.0 - t) ** p) ** (1.0 / p)


L_BROW, P_BROW = 0.075, 2.0         # the brow and forehead are broad and flat with rounded corners (iso views)
Y_BROW = (-0.10, 0.00)             # the crown rim blends from the brow's roundness to the crown's over this y range
SMOOTH_SIGMA = 0.010               # m, Gaussian smoothing of the width field away from the rims (no creases)


def crown_shape(y):
    """Roundness length and power of the crown rim at y (brow in front, crown and back behind)."""
    k = np.clip((np.asarray(y, float) - Y_BROW[0]) / (Y_BROW[1] - Y_BROW[0]), 0, 1)
    k = k * k * k * (k * (6 * k - 15) + 10)
    return L_BROW + (L_CROWN - L_BROW) * k, P_BROW + (P_CROWN - P_BROW) * k


def falloff_at(f, L, p):
    """The distance from a rim at which falloff(d / L, p) reaches f (the inverse of falloff)."""
    return L * (1.0 - (1.0 - f ** p) ** (1.0 / p))


def rim_dist(tree, C, P):
    """Distance from points to a finely sampled rim polyline (to its segments, not its samples), the index of the
    nearest sample and the foot point on the polyline."""
    d, i = tree.query(P)
    best, foot = d.copy(), C[i].copy()
    for j0 in (i - 1, i):
        j = np.clip(j0, 0, len(C) - 2)
        A, AB = C[j], C[j + 1] - C[j]
        t = np.clip(np.sum((P - A) * AB, 1) / np.sum(AB * AB, 1), 0, 1)
        Q = A + AB * t[:, None]
        dq = np.linalg.norm(P - Q, axis=1)
        near = dq < best
        best = np.where(near, dq, best)
        foot[near] = Q[near]
    return best, i, foot


# W_Z and Q_Y were read with straight lines between their knots: the width's slope jumped at every knot (z every
# 40 mm, y at 0.00 to 0.16), which banded the reflections on the back. A C2 smoothing spline over the straight-line
# table sampled every 1 mm rounds each knot and keeps the straight runs (largest departure 0.30 mm of width for
# W_Z, 0.35 mm for Q_Y). A spline through the knots alone rang in Q_Y's long flat run (y -0.30 to -0.04): 9 % low
# at y -0.10, the chin bar's rear corner 6 mm narrow.
TABLE_LAM = (1e-7, 1e-7)


def _table(T, lam):
    from scipy.interpolate import make_smoothing_spline
    v = np.arange(T[0, 0], T[-1, 0] + 1e-9, 0.001)
    sp = make_smoothing_spline(v, np.interp(v, T[:, 0], T[:, 1]), lam=lam)
    lo, hi = T[0, 0], T[-1, 0]
    return lambda x: sp(np.clip(x, lo, hi))


_W_OF_Z = _table(W_Z, TABLE_LAM[0])
_Q_OF_Y = _table(Q_Y, TABLE_LAM[1])


def raw_width(prof, Y, Z):
    """The width field before smoothing: back view width x plan factor x the two rims' roundness."""
    P = np.c_[Y, Z]
    dc, _, foot = rim_dist(prof.ftree_crown, prof.fine_crown, P)
    dh = rim_dist(prof.ftree_chin, prof.fine_chin, P)[0]
    # the roundness at the foot point on the rim: read at the nearest 0.25 mm sample it stepped at every sample
    # (up to 0.04 mm of width at the brow, where it blends from the brow's to the crown's), a staircase under the
    # 3 mm mesh that hid the surface's own normal from the shading test (round 3)
    Lc, Pc = crown_shape(foot[:, 0])
    w = _W_OF_Z(Z) * _Q_OF_Y(Y)
    return w * falloff(dc / Lc, Pc) * falloff(dh / L_CHIN, P_CHIN), np.minimum(dc, dh)


SMOOTH_H = 0.002                    # m, grid of the smoothed field


def smoothed_width(prof):
    """The width field smoothed on a fixed 2 mm grid (Gaussian, normalised over the domain) and read back by a
    bicubic spline: the same at any point whatever points ask (main averaged over the query points themselves,
    so the graded rings near the rims weighted the average unevenly). Kept on the profile."""
    from scipy import ndimage
    from scipy.interpolate import RectBivariateSpline
    if getattr(prof, "_smooth", None) is None:
        lo, hi = prof.outline.min(0) - 0.03, prof.outline.max(0) + 0.03
        gy = np.arange(lo[0], hi[0] + SMOOTH_H, SMOOTH_H)
        gz = np.arange(lo[1], hi[1] + SMOOTH_H, SMOOTH_H)
        YY, ZZ = np.meshgrid(gy, gz, indexing="ij")
        P = np.c_[YY.ravel(), ZZ.ravel()]
        X = raw_width(prof, P[:, 0], P[:, 1])[0].reshape(YY.shape)
        # the uncut domain: normalised over the cut one, the Gaussian pulled the chin bar's rear corner 6 mm in
        # beside the port (the field widens towards the edge)
        M = prof.inside(P, uncut=True).reshape(YY.shape).astype(float)
        s = SMOOTH_SIGMA / SMOOTH_H
        num = ndimage.gaussian_filter(X * M, s, mode="constant")
        den = ndimage.gaussian_filter(M, s, mode="constant")
        Xs = np.where(den > 1e-3, num / np.maximum(den, 1e-3), X)
        prof._smooth = RectBivariateSpline(gy, gz, Xs, kx=3, ky=3)
    return prof._smooth


def half_width(prof, Y, Z, smooth=True):
    """Half width x of the outer surface over the profile domain (both halves are +-x)."""
    Y, Z = np.asarray(Y, float), np.asarray(Z, float)
    X, d = raw_width(prof, Y, Z)
    if not smooth:
        return X
    # the nearest-rim distance has creases where the nearest rim point jumps: smoothed away from the rims, blended
    # in over 8 to 28 mm with a C2 step
    Xs = smoothed_width(prof).ev(Y, Z)
    k = np.clip((d - 0.008) / 0.020, 0, 1)
    return X + (Xs - X) * k * k * k * (k * (6 * k - 15) + 10)


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


# The crown rim is the centre line, where the half width x = W falloff(d / L) rises as the square root of the
# distance d from the rim: 3 mm of x across the crown is 0.04 mm of d. Main graded its crown rings by the brow's
# roundness all round and thinned them against the 3 mm outline samples, so the first point kept off the centre
# line stood 7 or 14 mm out by turns: one strip of fan triangles across the crown, its vertex normals 3 to 8 deg
# off the surface's, a ladder of clear-coat reflections along the print's stem (helmet round 3, Leatt's top view).
# Now a band of rows at equal steps of x, each row the rim's own samples moved along the rim's normals by the
# crown's local roundness: a structured grid (quads between straight columns, Delaunay at any scale of d), as fine
# across the crown as along it. Rings at the local roundness beyond it.
BAND_DF, BAND_N = 0.025, 20        # the band's rows: x steps of 2.5 % of the half width (3.1 to 3.4 mm), to 50 %
RING_DF = 1.0 / 28                 # the crown rings beyond it: steps of 3.6 % (4.5 mm), to 11/14 as before
BAND_CLEAR = 0.0012                # m, band points this close to another free edge (port, lower edge) are left out
BAND_SQUEEZE = 0.6                 # a column stops where its row spacing falls below this share of the rim's (the
                                   # crown's tight turn down to the back, 15 mm radius, focuses the normals)
BAND_NEAR = 0.0025                 # m (3D), other points this close to a band point are left out


def crown_frame(prof):
    """The crown rim's samples, their unit normals into the domain and the roundness there."""
    rim = prof.rim_crown
    t = np.gradient(rim, axis=0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    n = np.c_[-t[:, 1], t[:, 0]]
    if prof.area < 0:
        n = -n
    L, p = crown_shape(rim[:, 0])
    return rim, n, L, p


def crown_band(prof):
    """The band's points along the crown rim, rows of increasing distance (row k at x steps of k BAND_DF); each
    column stops where the rows close up (before the normals of a tight turn cross)."""
    rim, n, L, p = crown_frame(prof)
    B = np.stack([rim + n * falloff_at(k * BAND_DF, L, p)[:, None] for k in range(1, BAND_N + 1)])
    gap = np.linalg.norm(np.diff(B, axis=1), axis=2) / np.linalg.norm(np.diff(rim, axis=0), axis=1)
    tight = np.zeros(B.shape[:2], bool)
    tight[:, :-1] |= gap < BAND_SQUEEZE
    tight[:, 1:] |= gap < BAND_SQUEEZE
    tight = np.logical_or.accumulate(tight, axis=0)
    B = B[~tight]
    others = np.vstack([prof.lower, prof.rim_chin, prof.port])
    return B[prof.inside(B) & (cKDTree(others).query(B)[0] > BAND_CLEAR)]


def domain_points(prof, h=0.005, nring=14):
    """Points of the profile domain: the outline itself, the crown band, rings graded towards the rims, an
    interior grid."""
    rim, n, L, p = crown_frame(prof)
    f_band = BAND_N * BAND_DF
    pts = []
    for f in f_band + RING_DF * np.arange(1, 40):
        if f > (nring - 3) / nring + 1e-9:
            break
        d = falloff_at(f, L, p)
        pts.append(resample_open(rim + n * d[:, None], max(0.003, min(h, float(np.median(d)) * 0.9))))
    t = np.gradient(prof.rim_chin, axis=0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    nc = np.c_[-t[:, 1], t[:, 0]]
    if prof.area < 0:
        nc = -nc
    for d in ring_offsets(L_CHIN, P_CHIN, nring)[:-3]:
        pts.append(resample_open(prof.rim_chin + nc * d, max(0.003, min(h, d * 0.9))))
    lo, hi = prof.outline.min(0), prof.outline.max(0)
    gy, gz = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h * 0.866))
    gy = gy + (np.arange(gy.shape[0])[:, None] % 2) * h / 2
    pts.append(np.c_[gy.ravel(), gz.ravel()])
    Q = np.vstack(pts)
    # inside, nothing closer than 1.2 mm to the outline, clear of the band (3D) and of the rings it replaces
    keep = prof.inside(Q) & (cKDTree(prof.outline).query(Q)[0] > 0.0012)
    band = crown_band(prof)
    Q = Q[keep]
    B3 = np.c_[half_width(prof, band[:, 0], band[:, 1]), band]
    Q3 = np.c_[half_width(prof, Q[:, 0], Q[:, 1]), Q]
    keep = cKDTree(B3).query(Q3)[0] > BAND_NEAR
    P = np.vstack([prof.outline, band, Q[keep]])
    n_fix = len(prof.outline) + len(band)
    # thin out points closer than a local spacing (greedy, rings first; the outline and the band stay)
    tree = cKDTree(P)
    alive = np.ones(len(P), bool)
    dc = np.minimum(prof.tree_crown.query(P)[0], prof.tree_chin.query(P)[0])
    rad = np.clip(dc * 0.35, 0.0008, h * 0.6)
    for i in range(n_fix, len(P)):
        if not alive[i]:
            continue
        for j in tree.query_ball_point(P[i], rad[i]):
            if j > i and j >= n_fix:
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
T_MIN_PORT = {"side": 0.018, "iso": 0.014}  # 14 mm with the iso port: its lower rear corner reaches 10 to 15 mm
                                   # lower, over his cheeks (the cheek pads fill it); 18 mm put 4 cheek vertices inside
# The helmet on his head from the liner build-up (joint front fit, decision 47; main placed it by two rules: the
# port's top edge 40 mm above his eyes and his forehead at least 32 mm behind the brow, the rest even all round).
# Leatt Technical File 172 r01 (section 8, in the Moto 8.5 kit document): shell M/L 260 x 350 x 300 mm, EPS 256 x
# 287 x 270 (W x L x H). The table's outer rows read reversed (XS/S 268 x 361 x 309 is the largest, against the weights
# XS/S 1250 to XL/XXL 1430 g, section 7.10); M/L, the middle row, is the same either way. The EPS's length less his
# head's (fore to back, head_landmarks) is the EPS and comfort liner's build-up, shared front and back; the shell's
# wall is our brow-to-back 288.8 mm less the EPS's 287 (0.9 mm a side). The crown takes the same build-up (EST: an
# even EPS over the cap; the file gives no crown figure). Pitch, fore-aft and height are fitted so the shell stands
# that far off his crown, forehead and back; the sides follow from the shell's width (more there: the cheek pads,
# 25 to 40 mm by size in Leatt's spares, and the EPS's flare fill it). Checked: the port's top edge above his eyes
# (ECE 22.06 6.15, upward visual clearance 7 deg at least: the file's test report passes it).
EPS_LENGTH = 0.287                 # m, TF 172 M/L
SHELL_WALL = 0.0009                # m, brow to back: our 288.8 mm against the EPS's 287
UP_CLEARANCE_MIN = 7.0             # deg, ECE 22.06 6.15.3.2


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


def build_up(L):
    """m, the shell's stand-off from his head at the crown, forehead and back (EPS, comfort liner and the wall)."""
    return (EPS_LENGTH - (L["back"][1] - L["fore"][1])) / 2 + SHELL_WALL


def fit_on_head(body, Vo, Fo, prof):
    """Place the helmet on his head from the liner build-up (decision 47): pitch, fore-aft and height so the shell
    stands build_up() off his crown, forehead and back (nearest distances to the outer surface), centred across.
    Returns R, t (p_MB = R p_H + t) and the gaps, the brow's place and the upward clearance from his eyes."""
    from scipy.optimize import least_squares
    L = head_landmarks(body)
    C = np.vstack([Vo, Vo[Fo].mean(1)])
    tree = cKDTree(C)
    b = brow_point(prof)
    T = build_up(L)

    def place(th, dy, dz):
        R = rot_x(th)
        return R, np.array([0.0, L["eye"][1] + dy, L["eye"][2] + dz]) - R @ b

    def gaps(p, keys=("top", "fore", "back")):
        R, t = place(*p)
        return np.array([tree.query((L[k] - t) @ R)[0] for k in keys])

    best = None                                   # coarse grid, then least squares on the three stand-offs
    for th in np.radians(np.arange(0.0, 30.01, 1.0)):
        for dy in np.arange(-0.090, -0.0399, 0.002):
            for dz in np.arange(0.010, 0.0701, 0.002):
                c = np.sum((gaps((th, dy, dz)) - T) ** 2)
                if best is None or c < best[0]:
                    best = (c, (th, dy, dz))
    p = least_squares(lambda p: (gaps(p) - T) * 1000, best[1], diff_step=1e-3, x_scale=[0.02, 0.002, 0.002]).x
    R, t = place(*p)
    g = dict(zip(("top", "back", "left", "right", "fore"), gaps(p, ("top", "back", "left", "right", "fore"))))
    brow = R @ b + t
    up = math.degrees(math.atan2(brow[2] - L["eye"][2], L["eye"][1] - brow[1]))
    return R, t, dict(pitch_deg=round(math.degrees(p[0]), 2), brow_ahead_of_eye_mm=round(-p[1] * 1000, 1),
                      brow_above_eye_mm=round(p[2] * 1000, 1), build_up_mm=round(T * 1000, 1),
                      up_clearance_deg=round(up, 1), gaps_mm={k: round(float(v) * 1000, 1) for k, v in g.items()})


def shell_solid(Vo, Fo, skin_H):
    """Outer surface, inner (comfort liner) surface and the rolled edges joining them, in the helmet frame.
    skin_H: his head and neck skin in the helmet frame. The liner surface lies GAP off the skin where the skin is
    near (pads) and T_MAX inside the shell elsewhere, never thinner than T_MIN. Returns the inner surface, the
    thickness and the rim strips (one per free edge: face port, lower edge) as lists of rings."""
    n = len(Vo)
    N = normals(Vo, Fo)
    d = cKDTree(skin_H).query(Vo)[0]
    t_min = T_MIN_PORT.get(PORT, T_MIN)
    t = np.clip(d - GAP, t_min, T_MAX)
    t = np.minimum(smooth_field(Fo, n, t, 12), np.maximum(d - GAP, t_min))
    Vi = Vo - N * t[:, None]
    strips = []
    for loop in boundary_loops(Fo):
        O, I = Vo[loop], Vi[loop]
        tang = np.roll(O, -1, 0) - np.roll(O, 1, 0)
        tang /= np.linalg.norm(tang, axis=1)[:, None]
        out = np.cross(tang, N[loop])                      # in the surface, away from it (winding order)
        out /= np.linalg.norm(out, axis=1)[:, None]
        # the wall's bow on the port's sides (out along y); the chin bar's top and the brow keep the lip only: there
        # the goggle's lens sits close above the chin bar (a 10 mm bow all round put its lower corners in the trim)
        side = (np.abs(out[:, 1]) / np.maximum(np.linalg.norm(out[:, 1:], axis=1), 1e-9)) ** 2
        rings = []
        for k, sv in enumerate(np.linspace(0, 1, RIM_RINGS)):
            bulge = RIM_A * side * np.sin(np.pi * sv) + RIM_B * np.sin(np.pi * min(sv * 3, 1)) * (sv < 0.34)
            rings.append(O + (I - O) * sv + out * bulge[:, None])
        strips.append((loop, rings))
    return Vi, t, strips


RIM_R = 0.004                      # m, the rubber trim's lip beyond the cut edge (goggle.STRAP_EDGE's margin)
# Joint front fit, phase 2 (decision 51): the port's trim rolls inward from the crest. Leatt's iso photos show the
# rolled band 9 to 14 mm wide (iso-left 1160 to 1197 px and more, iso-right 710 to 760 px); ours, a 4 mm bow on a
# 2.4 mm lip, read 4.4 to 7.7 mm through the solved iso-left camera (median 6.2). The wall now bows 10 mm into the
# opening at mid depth on a 3 mm lip, on the port's sides: 4.9 to 13.0 mm (median 11.0; the low end at the brow's
# corner), his skin still 2.1 mm off it (scratch trimw.py)
RIM_A = 0.010                      # m, the trim's wall bowed into the opening at mid depth
RIM_B = 0.003                      # m, its lip at the crest
RIM_RINGS = 9                      # rings across the trim, crest to liner


# ---------------------------------------------------------------- visor
# Royal_Left pixels: top line (centre line) and lower edge (the visor's side edge seen from the side), tip at u 220,
# rear end on the crown at u 1135 (its rear edge runs down to the side corner at u 1075, v 662). Round 4: behind that
# corner the low line runs on at its height (main rose to the crown, v 540 and 380, for a rear edge straight across):
# the grid then lies over the shell to the tongue's end and VISOR_REAR cuts the rear edge from it.
# Joint front fit, phase 2 (decision 51): through the solved Royal camera (research/helmet-ba.json) the top line
# stood 10 to 15 px (2.5 to 3.7 mm) above Leatt's and the side silhouette 22 px (the arch's near shoulder, lifted by
# the perspective). Fitted to the top silhouette in Royal and MY27 left together (scratch fitvisor.py): the top line
# 15 px lower at the tip, fading to 0 at u 1000, and VISOR_ARCH 0.7 (was 1.3): Royal mean -2.9 px, rms 3.8 (was
# -21.6, 22.3), the tip +0.2 (was -19.0); MY27 left +0.7, rms 2.2 (was -17.3, 18.0). Round 4's table: v 334, 323,
# 322 ... from the tip.
VISOR_TOP = [(220, 349.0), (257, 337.3), (297, 335.5), (337, 334.8), (407, 332.4), (487, 331.9), (567, 331.3),
             (647, 332.8), (726, 334.3), (806, 337.7), (886, 342.2), (966, 347.7), (1045, 352), (1100, 356),
             (1135, 360)]
VISOR_LOW = [(220, 349.0), (277, 377), (346, 416), (416, 454), (487, 491), (558, 528), (610, 600), (660, 660),
             (720, 712), (760, 722), (900, 692), (1000, 675), (1075, 662), (1135, 662)]
# plan half width of the visor (Pinata Teal top view, 0.247 mm/px), by Royal_Left u
# Round 4 (decision 50): the half widths ahead of u 912 measured against Leatt's top photo through the solved top
# camera (research/helmet-ba.json; its outline: the photo's mask, the visor's edge row by row): main's visor stood
# 10 to 18 mm too wide over its first 15 mm (Leatt's tip is pointed in plan), 1.5 to 5 mm along its sides and 5 to
# 10 mm at its wings (y -103 to -61 mm). Behind u 912 the visor lies on the shell and its rear edge is VISOR_REAR's
# (round 4: the half width stays 50 mm to the rear end, where main's 0 gathered the rear row into one point).
VISOR_PLAN = [(220, 0.0), (236, 0.018), (251, 0.030), (279, 0.055), (311, 0.0695), (347, 0.0732), (403, 0.0775),
              (460, 0.0819), (516, 0.0864), (573, 0.0913), (629, 0.0967), (685, 0.0978), (742, 0.0995),
              (798, 0.1079), (854, 0.1136), (912, 0.1199), (1000, 0.090), (1075, 0.050), (1135, 0.050)]
VISOR_T = 0.0035                   # m, visor thickness (moulded ABS)
VISOR_ARCH = 0.7                   # the arch's fall from the centre line to the side edge: (1 - cos) ** VISOR_ARCH
VISOR_GAP = 0.0075                 # m, top surface off the shell where it lies over it (underside 4 mm clear)
# the wings' edges come down to the shell (round 4): Leatt's top photo has its outline 5 to 10 mm inside main's wings,
# which stood the full gap off the shell to their edges; over the outer fifth of the arch the gap falls to the
# visor's thickness plus 1 mm
VISOR_EDGE_GAP = 0.0045
# the visor's rear edge in plan (round 4, decision 50): |x| and y, m, y from the tongue's rear end (Royal's u 1135).
# Leatt's top photo at 3x: a tongue over the crown's centre (straight to |x| 22 mm, round to 30), the edge then
# running forward along the crown (steeply to |x| 46 mm, 22 mm ahead, then gently) to a corner 37.5 mm ahead at |x|
# 90 mm, ahead of the vents, and back up the wing to |x| 113 mm, 15 mm ahead (y -6.2 mm: Royal's corner at u 1075).
# Main's rear edge ran straight across at the tongue's end. Both sides traced, cast through the solved top camera
# (research/helmet-ba.json) onto the shell offset by VISOR_GAP, mirrored and averaged (the sides agree within 1.3 mm
# but at the corner, 4 mm); y is taken from the tongue because the top photo puts the crown 10 to 12 mm ahead of the
# side views (helmet.md 7).
VISOR_REAR = [(0.0, 0.0), (0.022, 0.0), (0.026, -0.0005), (0.028, -0.0010), (0.030, -0.0022), (0.032, -0.0043),
              (0.036, -0.0099), (0.040, -0.0157), (0.044, -0.0207), (0.046, -0.0218), (0.050, -0.0230),
              (0.062, -0.0269), (0.074, -0.0309), (0.086, -0.0353), (0.0905, -0.0375), (0.095, -0.0328),
              (0.101, -0.0269), (0.107, -0.0210), (0.113, -0.0149), (0.200, -0.0149)]
VISOR_REAR_FROM = -0.06            # m, stations ahead of this y keep their place (the rear edge's corner: y -28.8)
VISOR_FINE = 8                     # the finer grid's columns per column


def grid_at(F, c, t):
    """Points of a grid surface F (rows, columns, 3) at fractional column c and row t (bilinear)."""
    nr, nc, _ = F.shape
    c0 = np.clip(np.floor(c).astype(int), 0, nc - 2)
    t0 = np.clip(np.floor(t).astype(int), 0, nr - 2)
    a, b = (c - c0)[:, None], (t - t0)[:, None]
    return ((1 - a) * (1 - b) * F[t0, c0] + a * (1 - b) * F[t0, c0 + 1] + (1 - a) * b * F[t0 + 1, c0]
            + a * b * F[t0 + 1, c0 + 1])


def visor_rear_edge(F, nphi, y_end):
    """The visor's grid (nphi columns) from a finer one F whose rear stations run straight across: ahead of
    VISOR_REAR_FROM its own columns; behind it a band whose last row lies on VISOR_REAR. Where each fine column first
    crosses the rear edge gives the edge; every column then runs from its place on the station at VISOR_REAR_FROM to
    the edge's point at the same share of its length (sliding each column to its own crossing sheared the band into
    folded quads where the columns run nearly along the edge's steep part)."""
    rear = np.array(VISOR_REAR)
    nr, nf, _ = F.shape
    step = (nf - 1) // (nphi - 1)
    i0 = int(np.searchsorted(F[:, nf // 2, 1], VISOR_REAR_FROM))
    te = np.full(nf, nr - 1.0)
    for k in range(nf):
        g = F[:, k, 1] - (y_end + np.interp(np.abs(F[:, k, 0]), rear[:, 0], rear[:, 1]))
        h = np.nonzero(g[i0:] > 1e-9)[0]
        if len(h):
            m = i0 + h[0]
            te[k] = (m - 1) + g[m - 1] / (g[m - 1] - g[m])
    ce = np.arange(nf, dtype=float)

    def share(P):
        c = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        return c / c[-1]

    fe = share(grid_at(F, ce, te))
    cj = np.arange(nphi) * step
    f = share(F[i0])[cj]
    c_end, t_end = np.interp(f, fe, ce), np.interp(f, fe, te)
    r = np.linspace(0.0, 1.0, nr - i0)[:, None]
    C = (1 - r) * cj[None, :] + r * c_end[None, :]
    T = (1 - r) * i0 + r * t_end[None, :]
    G = F[:, ::step].copy()
    G[i0:] = grid_at(F, C.ravel(), T.ravel()).reshape(nr - i0, nphi, 3)
    return G


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
    nf = VISOR_FINE * (nphi - 1) + 1                   # the rear edge is found on a finer grid (visor_rear_edge)
    phi = np.linspace(-1, 1, nf)
    G = np.zeros((len(us), nf, 3))
    for i, (y, z0, z1, ai) in enumerate(zip(ys, zt, zl, a)):
        c = 1 - np.cos(phi * np.pi / 2)
        z = z0 - (z0 - z1) * c ** VISOR_ARCH
        x = ai * np.sin(phi * np.pi / 2)
        G[i] = np.c_[x, np.full(nf, y), z]
    # lie over the shell where the shell is under it: never closer than VISOR_GAP
    flat = G.reshape(-1, 3)
    ins = prof.inside(flat[:, 1:])
    hw = np.zeros(len(flat))
    hw[ins] = shell_hw(prof, flat[ins, 1], flat[ins, 2])
    side = np.sign(flat[:, 0]) + (flat[:, 0] == 0)
    k = np.clip((np.tile(np.abs(phi), len(us)) - 0.8) / 0.2, 0, 1)
    gap = VISOR_GAP - (VISOR_GAP - VISOR_EDGE_GAP) * k * k * (3 - 2 * k)
    need = ins & (np.abs(flat[:, 0]) < hw + gap)
    flat[need, 0] = side[need] * (hw[need] + gap[need])
    return visor_rear_edge(flat.reshape(G.shape), nphi, ys[-1])


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
    import helmet_detail                              # moulded vents away from the front (round 3, decision 46)
    parts.append(helmet_detail.build(Vo, Fo))
    if PAINT:                                         # the old projection of Leatt's photos (lighting baked in)
        Vt, Ft, Nt, UVt = visor.top
        info["paint"] = paint_atlas([(Vo, Fo, normals(Vo, Fo), uv_o), (Vt, Ft, Nt, UVt)],
                                    os.path.join(TEXDIR, "helmet_pinata.png"))
    elif ART or not os.path.exists(os.path.join(TEXDIR, "helmet_pinata.png")):
        import helmet_art                             # flat print redrawn by script (brow badge included)
        helmet_art.draw(os.path.join(TEXDIR, "helmet_pinata.png"), log=lambda *a: None)
    for P in parts:                                   # faces without art: any UV (their materials have no image)
        P.UV = [u if u is not None else [(0.0, 0.0)] * len(f) for u, f in zip(P.UV, P.F)]
    for P in parts:
        P.V = P.V @ R.T + tr
    info.update(shell_thickness_mm=[round(float(thick.min()) * 1000, 1), round(float(thick.max()) * 1000, 1)])
    import goggle as G                                # the goggle and his eyes (goggle.py)
    gparts, ginfo = G.build_goggle(body, (R, tr), prof)
    info.update(ginfo)
    return parts + gparts, info, (R, tr)


# ---------------------------------------------------------------- graphics: Leatt's Pinata Teal photos and cameras
# (helmet_art.py traces the print through them; paint_atlas below is the old projection, kept for comparison)
REF = os.path.normpath(os.path.join(HERE, "..", "..", "reference", "leatt-gear", "helmet"))
PHOTOS = dict(isoleft="helmet85-kit_pinatateal_iso-left_leatt-us_1026000250_1920.png",
              isoright="helmet85-kit_pinatateal_iso-right-with-goggle_leatt-us_1026000250_1920.png",
              back="helmet85-kit_pinatateal_back_leatt-us_1026000250_1920.png",
              top="helmet85-kit_pinatateal_top_leatt-us_1026000250_1920.png")
# Pinhole cameras of Leatt's four Pinata Teal views in the helmet frame, fitted to the shell and visor outline
# (chamfer distance both ways, half resolution, Powell then Nelder-Mead): azimuth from the front towards his left
# and elevation of the camera (deg), roll (deg), distance (m), focal length (px), aim offset (m) from CAM_CTR.
CAM_CTR = np.array([0.0, -0.03, 0.0])
# The back camera was refitted on 2026-11-13 with the print's centre line as a second term (outline chamfer + 0.25 x
# rms offset of the shell's x = 0 line from photo x 965.5, where the stripe's stem and the DOT print stand): the
# outline-only fit had settled 6.9 deg yawed and 4.9 deg rolled (centre line 25 to 125 px off, the back LEATT 16 mm
# off centre); the refit is straight behind and upright, outline chamfer 9.0 px against 11.2 (half res).
# The iso cameras put the shell's centre line 66 px (iso-left) and 79 px (iso-right) beside the brow badge's centre,
# about 14 and 17 mm: fitting iso-left to the badge costs 4.7 px of outline (az 62 -> 52 deg) and leaves the badge
# 27 px low, so the error is the shell's estimated front (brow, chin), not the camera; they are kept.
CAMS = dict(isoleft=[62.0789, 3.9144, -7.4058, 1.4021, 5653.2658, -0.0307, -0.0032, -0.0334],
            back=[179.7402, 11.1849, 0.0388, 1.1854, 5620.7099, 0.0004, 0.0194, 0.0024],
            top=[3.0441, 87.254, 0.2669, 1.4571, 5624.0378, 0.0002, -0.0141, -0.0449],
            isoright=[-59.1663, 8.6293, 8.1332, 1.8892, 7721.6883, 0.0325, 0.0004, -0.0393])
# The print's cameras (helmet round 4, decision 50): the four Pinata views as solved together with Leatt's other
# photos of the shell (helmet_ba.py, research/helmet-ba.json: shared landmarks and outlines). CAMS above, each fitted
# alone to its own outline, put the crown print 20 to 30 mm ahead of where the other views see it (round 3); they stay
# as helmet_ba's start values. cam_from and cam_project take either kind.
BA_JSON = os.path.normpath(os.path.join(HERE, "..", "..", "research", "helmet-ba.json"))
PRINT_CAMS = {k[4:]: dict(C=np.array(c["C"]), R=np.array(c["R"]), f=float(c["f"]))
              for k, c in json.load(open(BA_JSON))["cameras"].items() if k.startswith("pin_")}
# the goggle and its strap cover the right side in Leatt's iso-right view: not the helmet's art (hand-drawn, px)
ISORIGHT_GOGGLE = [(215, 630), (560, 610), (800, 700), (1430, 700), (1470, 1000), (1440, 1260), (800, 1240),
                   (770, 1040), (560, 960), (215, 930)]
TEX = 4096                         # 4.3 texels per mm: small print (EMERGENCY USE ONLY, MX-26) stays legible
PAINT = False                      # True: the old projected atlas (paint_atlas), kept only for comparison
ART = False                        # True: redraw the flat print (helmet_art.draw) even if the texture exists
ATLAS_K = 4300.0                   # texels per metre (UVs = texels / TEX: the same layout as the 2048 atlas)
BASE_WHITE = (226, 229, 235)


def cam_from(x):
    """(centre, rotation rows right/up/forward, focal px) of a camera: a solved one (dict C, R, f; principal point
    960, 960) or CAMS' parameters."""
    if isinstance(x, dict):
        return x["C"], x["R"], x["f"]
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


# atlas islands: (name, origin u, v in texels, axes): side views by (y, z), top by (x, y), back/front by (x, z).
# Joint front fit (decision 47): the visor's faces each in the island of its normal's largest component, as the
# shell's: the top by (x, y) in V, the steep wings by (y, z) in VL and VR, the faces turned forward (its tip, the
# wings' front edges) or back by (x, z) in VF and VB. In the one top projection their texels stretched up to 97 times
# (1 / |n_z|): the side LEATT and the print on the wing came out in horizontal steps (Royal 1:1, sheet 10).
ISLANDS = {k: (2 * u, 2 * v) for k, (u, v) in
           dict(L=(0, 0), R=(820, 0), T=(0, 700), B=(600, 700), F=(1200, 700), V=(0, 1500), VL=(580, 1450),
                VR=(1150, 1450), VF=(580, 1700), VB=(1200, 1700)).items()}


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
    elif name in ("VL", "VR"):
        u, v = ((y + 0.225) if name == "VL" else (0.012 - y)) * k, (z - 0.04) * k
    elif name in ("VF", "VB"):
        u, v = ((x + 0.13) if name == "VF" else (0.13 - x)) * k, (z - 0.04) * k
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
    """Face-corner UVs (0..1) for an outer surface, each face in the island of its normal (visor: V, VL, VR, VF, VB;
    a quad's normal from its diagonals: the visor's tip has quads whose first three corners nearly meet)."""
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    if visor:
        if F.shape[1] == 4:
            fn = np.cross(V[F[:, 2]] - V[F[:, 0]], V[F[:, 3]] - V[F[:, 1]])
        fn = fn * np.sign(fn[:, 2].sum())                     # outward (up) whatever the grid's winding
        a = np.abs(fn)
        isl = np.where((a[:, 0] >= a[:, 2]) & (a[:, 0] >= a[:, 1]), np.where(fn[:, 0] > 0, "VL", "VR"),
                       np.where(a[:, 1] > a[:, 2], np.where(fn[:, 1] < 0, "VF", "VB"), "V"))
    else:
        isl = face_island(fn)
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


# ---------------------------------------------------------------- goggle strap (the goggle itself: goggle.py)
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
    from PIL import Image
    s = np.abs(np.linspace(-1, 1, w))                      # 1 at the outriggers, 0 at the back centre
    stops = [(0.0, (40, 190, 160)), (0.30, (60, 175, 175)), (0.48, (110, 60, 170)), (0.62, (170, 30, 150)),
             (0.76, (225, 40, 120)), (0.88, (245, 120, 60)), (1.0, (250, 200, 60))]
    t = 1 - s
    cols = np.array([np.interp(1 - t, [p for p, _ in stops], [c[k] for _, c in stops]) for k in range(3)]).T
    img = np.repeat(cols[None, :, :], h, axis=0)
    yy = np.linspace(0, 1, h)[:, None]
    img = img * (0.92 + 0.08 * np.cos(yy * 9.0 + np.linspace(0, 40, w)[None, :] * 0.2))[..., None]   # sheen bands
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    # Leatt's official slanted wordmark (goggle.WORDMARK; Leatt ISO, his 07), letter height 0.70 of the strap
    import goggle as G
    ch = 0.70 * h
    lw = ch * G.wordmark_aspect()
    for side in (0, 1):
        # side 1 (right side) is read from outside going towards its outrigger: same direction along the strap
        start = 0.07 * w if side == 0 else 0.93 * w - lw
        G.stamp_wordmark(im, start, h * 0.5 - ch / 2, lw, ch, (250, 250, 250))
    im.save(path)


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
    """hide_body: the skin under the helmet; helmet_shell__frame: the helmet frame's placement on him (4x4,
    p_MB = F p_H), so views fitted in the helmet frame (his-photo-cameras.json, head_closeups.py) ride the shell."""
    R, t = Rt
    F = np.eye(4)
    F[:3, :3], F[:3, 3] = R, t
    return dict(hide_body=hidden_skin(body, Rt), helmet_shell__frame=F)


MATERIALS = {
    # Pinata Teal art under a gloss clear coat. The print/coat interface (n about 1.5 both sides) reflects almost
    # nothing, so the base has no specular of its own (spec 0; Blender 5.2 does not cancel it under a coat: a base at
    # rough 0.22 added a soft satin glow round the highlight, coat test of 2026-11-13). The one reflection is the coat:
    # IOR 1.5 (4 % at normal incidence), rough 0.03 (Leatt's studio photos show the softboxes with crisp edges).
    "helmet_paint": dict(image="helmet_pinata.png", rough=0.5, spec=0.0, coat=1.0, coat_rough=0.03),
    "helmet_trim": dict(rgb=[18, 18, 20], rough=0.65),
    # the moulded detail (helmet_detail.py): the crown vents' insert and lattice are white plastic, satin (Leatt's top
    # photo, de-lit: rim 202 206 214, bars 209 213 219); the rear slots' surround and the rear lower pieces are the
    # shell's own white under its clear coat (the print's white ink, helmet_art.json, and helmet_paint's coat)
    "helmet_vent_insert": dict(rgb=[205, 209, 216], rough=0.35),
    "helmet_moulded": dict(rgb=[226, 229, 235], rough=0.5, spec=0.0, coat=1.0, coat_rough=0.03),
    # the rear slots' wire mesh (round 4): near black in Leatt's back photos, its wires seen by their faint glints
    # (Pinata back at 3x: the exhaust slot's mesh barely shows, the lower slot's dark grey on black)
    "helmet_vent_mesh": dict(rgb=[36, 37, 40], rough=0.4),
    "helmet_liner": dict(rgb=[34, 34, 38], rough=0.9, sheen=0.4),
    "visor_under": dict(rgb=[214, 217, 222], rough=0.45),
    "goggle_strap": dict(rough=0.7, sheen=0.3, image="goggle_strap.png"),
    "goggle_strap_in": dict(rgb=[24, 24, 26], rough=0.8),
}


def write_npz(path, parts, extra=None):
    import goggle as G
    allm = {**MATERIALS, **G.MATERIALS}
    mats = sorted({m for P in parts for m in P.M})
    out = dict(names=np.array([P.name for P in parts]), mats=np.array(mats),
               materials=json.dumps({m: allm[m] for m in mats}))
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
    ART = True                                        # the CLI always redraws the art (deterministic)
    os.makedirs(TEXDIR, exist_ok=True)
    import goggle as G
    strap_texture(os.path.join(TEXDIR, "goggle_strap.png"))
    G.outrigger_texture(os.path.join(TEXDIR, "goggle_outrigger.png"))
    G.eye_texture(os.path.join(TEXDIR, "goggle_eyes_brown.png"))
    parts, info, Rt = build(body)                     # the brow badge is part of the art (helmet_art)
    write_npz(sys.argv[2], parts, extras(body, parts, Rt))
    print(json.dumps(info), sum(len(P.V) for P in parts), "vertices")
