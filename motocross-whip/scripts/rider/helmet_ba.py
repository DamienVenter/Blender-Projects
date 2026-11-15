"""Bundle adjustment of Leatt's Moto 8.5 photos (helmet round 3, decision 46; round 4, decision 50): all twelve cameras
and the shared 3D landmarks solved together with the shell's outlines, in the HELMET frame (metres, x to the wearer's
left, y back, z up).

usage: python3 helmet_ba.py [OUT.json]      (default research/helmet-ba.json; about 4 minutes on one core)

Photos (reference/leatt-gear): Pinata Teal iso-left, iso-right, back, top (helmet/, 1920 px); V25 Royal left (the
side view the profile was traced from) and back (helmet/); V25 white iso-left and back (helmet/); MY27 kit
front-iso-left, left, right, back (goggles/, the Velocity 5.5 on the 8.5). The same shell in all of them (Leatt makes
the 8.5 in one shell size for M/L; the DOT label on the back reads M).

Gauge: the model shell. Its scale is Royal_Left's (helmet.px2h: y = (u - 1100) S, z = -(v - 900) S at x = 0,
S = 0.2484 mm/px from the strap width) and every camera, Royal_Left included (round 4: it was held looking exactly
along -x; free, it turns 1.6 to 2.6 deg), is placed on the shell by the outlines and the landmarks held on its
surface. The shell is mirror symmetric: a landmark pair (L on the wearer's left, R on his right) is one point
(x, y, z) and its mirror (-x, y, z); a centre landmark is (0, y, z).

Cameras: pinhole, square pixels, no distortion (Leatt's product photos are long-lens studio shots), principal point
fixed (image centre; MY27 at goggle round 8's), free rotation, centre and focal length. Initial values: helmet.CAMS
(Pinata), goggle round 8's MY27 cameras carried to this frame, the Pinata ones for V25.

Landmarks: photo px read by eye on 1:1 crops (helmet5 crop sheets) and refined to sub-pixel where the feature allows:
  disc  Otsu dark (or bright) disc centroid (visor screws, emergency release tabs, DOT "O")
  blob  colour blob centroid (brow badge, rear 360 badge)
  mesh  lattice centroid by local contrast (crown mesh vents)
  eye   read by eye at 3x (vent slots, print corners), sigma 2.5 to 6 px
  line  an edge across the image: only the offset normal to the edge is measured (the visor's rear edge)
sigma is the 1-sigma reading error in px, divided by the cosine of the view's incidence on the shell (foreshorten).
Residuals are weighted by 1/sigma: three soft-l1 robust rounds (scale 2 sigma), then plain least squares; the
covariance of the solution is (J'J)^-1 scaled by the reduced chi-square when that exceeds 1. The landmarks away from
the front are held on the model shell (SURFACE_LMS), the two on the centre line on the traced profile.

Outlines: see OUTLINE_* below. The solve then measures the shell: Outline.offsets_mm gives each outline vertex's
distance from the photo's outline through the solved cameras (helmet round 3 rebuilt W_Z, Q_Y from them).
"""
import json
import math
import os
import sys

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = os.environ.get("HELMET_SCRIPTS", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import helmet as H  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
REF = os.path.join(ROOT, "reference", "leatt-gear")
BA_JSON = os.path.join(ROOT, "research", "helmet-ba.json")

PHOTOS = {
    "pin_isoleft": "helmet/" + H.PHOTOS["isoleft"],
    "pin_isoright": "helmet/" + H.PHOTOS["isoright"],
    "pin_back": "helmet/" + H.PHOTOS["back"],
    "pin_top": "helmet/" + H.PHOTOS["top"],
    "royal_left": "helmet/helmet85_royal-v25_left_leatt-us_1025100220_1920.png",
    "royal_back": "helmet/helmet85_royal-v25_back_leatt-us_1025100220_1920.png",
    "v25w_isoleft": "helmet/helmet85_white-v25_iso-left_leatt-us_1025100260.jpg",
    "v25w_back": "helmet/helmet85_white-v25_back_leatt-us_1025100260.jpg",
    "my27_isoleft": "goggles/velocity55-on-helmet85-kit-my27_bluered_1-front-iso-left_leatt-us_1027000180_1920.jpg",
    "my27_left": "goggles/velocity55-on-helmet85-kit-my27_bluered_2-left-side_leatt-us_1027000180_1920.jpg",
    "my27_right": "goggles/velocity55-on-helmet85-kit-my27_bluered_3-right-side_leatt-us_1027000180_1920.jpg",
    "my27_back": "goggles/velocity55-on-helmet85-kit-my27_bluered_4-back_leatt-us_1027000180_1920.jpg",
}
W = 1920

# goggle round 8's MY27 cameras (goggle frame "PL7": the helmet frame shifted by (0, -0.1468, -0.004) m and pitched
# 5 deg): az, el, roll (deg), d (m), f (px), principal point offset (px) about their target
MY27 = {
    "isoleft": ([43.88918440738743, 3.271251222956865, 1.4114696488312501, 1.6, 6877.8191552093285,
                 10.163102668794025, -19.987836096979414]),
    "left": ([96.25221577830708, -3.0811578904917933, -3.3871494605261847, 1.6, 6025.609860794244,
              33.743802850531765, -29.262833371694022]),
    "right": ([-95.9963298610849, -3.139492601822695, 1.7862755868405797, 1.6, 6241.882641485473,
               18.623638922480893, -35.20232556957784]),
    "back": ([179.95579731625958, 15.909592609927742, 0.10916150145976686, 1.6, 6619.02054779141,
              7.802556316372393, 49.550828563119516]),
}
MY27_TARGET = np.array([0.0, 0.10803634806459077, -0.01103549444587415])
PL7 = (-0.1468, -0.004, 5.0)

# ------------------------------------------------------------------------------------------------ the landmarks
# name: (kind, {view: (u, v, sigma[, "line" normal angle deg])}); kind "C" centre (x = 0), "L"/"R" a mirrored pair
# whose L observations see the wearer's left one and R observations his right one. Back views: image left = wearer's
# left; top view: image right = wearer's left.
PAIRS = {
    # the round screw on the shell's side below the eye port (dark disc), sigma 1.5 px
    "side_screw": {
        "L": {"pin_isoleft": (1353.5, 1108.3, 1.5), "royal_left": (953.9, 1174.4, 1.5),
              "v25w_isoleft": (1244.1, 1117.7, 1.5), "my27_isoleft": (1461.0, 1126.9, 1.5),
              "my27_left": (1035.5, 1100.2, 1.5)},
        "R": {"pin_isoright": (540.2, 1103.8, 1.5), "my27_right": (929.0, 1103.0, 1.5)}},
    # emergency release tab on the lower cheek (dark disc)
    "release_tab": {
        "L": {"pin_isoleft": (1179.4, 1410.1, 2.0), "royal_left": (729.9, 1461.6, 2.0),
              "v25w_isoleft": (1069.4, 1417.8, 2.0), "my27_isoleft": (1261.2, 1447.2, 3.0),
              "my27_left": (891.9, 1381.4, 2.0)},
        # the dark discs read on the right side (pin_isoright 545.9, 1335.1; my27_right 933.5, 1338.3) sit 25 to 35 mm
        # from the mirror of the left one in every solution: another feature, left out
        "R": {}},
    # rear exhaust slot in the back band (dark slot centroid)
    "rear_slot": {
        "L": {"pin_back": (764.5, 748.2, 2.5), "v25w_back": (753.2, 704.9, 2.5), "my27_back": (802.5, 684.6, 4.0),
              "royal_back": (755.0, 714.0, 2.5)},
        "R": {"pin_back": (1153.4, 748.9, 2.5), "v25w_back": (1152.3, 710.7, 2.5), "my27_back": (1159.1, 674.5, 4.0),
              "royal_back": (1160.0, 712.0, 2.5)}},
    # (the side views show a small mesh slot under the rear ledge, Royal_Left 1561, 556 and MY27 left: as the rear slot
    # it sits 52 to 57 px (14 mm) above where the five back views put it; another opening, left out)
    # crown mesh vent (lattice centroid). Round 4: the side views' readings are the centroid of the vent's outline
    # (Royal_Left: the light-grey vent segmented on the navy shell; the others: the mean of its four corners read at
    # 3x); round 3 had read its front end in four of them (MY27 left 76 px, Royal 27 px, iso-left 25 px ahead)
    "crown_vent": {
        "L": {"pin_top": (1208.4, 674.1, 3.0), "pin_back": (669.1, 573.0, 3.0), "v25w_back": (661.2, 533.7, 4.0),
              "my27_back": (691.7, 506.0, 3.0), "royal_left": (1272.4, 453.1, 4.0), "my27_left": (1236.0, 370.0, 4.0),
              "pin_isoleft": (1363.0, 332.7, 4.0), "v25w_isoleft": (1302.7, 347.7, 4.0),
              "royal_back": (658.0, 532.0, 3.0)},
        "R": {"pin_top": (721.0, 671.5, 3.0), "pin_back": (1244.5, 569.3, 3.0), "v25w_back": (1263.2, 541.0, 4.0),
              "my27_back": (1260.2, 508.0, 3.0), "my27_right": (704.2, 352.3, 4.0),
              "pin_isoright": (565.3, 307.5, 4.0), "royal_back": (1252.0, 528.0, 3.0)}},
    # upper side exhaust vent behind the visor (dark slot centroid)
    "side_vent": {
        "L": {"pin_isoleft": (1484.5, 452.2, 4.0), "royal_left": (1316.1, 568.0, 4.0),
              "v25w_isoleft": (1399.3, 463.9, 4.0), "my27_isoleft": (1514.4, 455.8, 4.0),
              "my27_left": (1269.5, 463.2, 4.0), "pin_top": (1334.2, 645.2, 3.0)},
        "R": {"pin_isoright": (438.2, 427.3, 4.0), "my27_right": (660.8, 451.7, 4.0), "pin_top": (588.3, 643.2, 3.0)}},
    # lower rear vent (dark slot centroid)
    "low_vent": {
        "L": {"royal_left": (1445.5, 1227.6, 4.0), "v25w_isoleft": (1609.1, 1057.3, 4.0),
              "v25w_back": (456.0, 1435.9, 4.0), "my27_back": (515.7, 1332.1, 4.0), "royal_back": (472.0, 1465.0, 4.0)},
        "R": {"my27_right": (426.0, 1100.0, 8.0), "v25w_back": (1434.2, 1444.2, 4.0),
              "my27_back": (1427.5, 1330.4, 4.0), "royal_back": (1455.0, 1460.0, 4.0)}},
    # the grey triangle badge on the shell beside the eye port, above the goggle strap (light triangle centroid)
    "eyeport_triangle": {
        "L": {"pin_isoleft": (1070.1, 724.1, 3.0), "royal_left": (718.2, 767.7, 2.0),
              "v25w_isoleft": (950.2, 776.8, 2.0), "my27_isoleft": (1227.6, 700.2, 2.0),
              "my27_left": (744.4, 739.5, 2.0)},
        "R": {"pin_isoright": (816.5, 727.6, 2.0), "my27_right": (1212.5, 724.3, 2.0)}},
    # the chin bar's side vent (lattice centroid)
    "chin_vent": {
        "L": {"royal_left": (439.4, 1416.4, 4.0), "v25w_isoleft": (729.0, 1450.3, 4.0),
              "my27_isoleft": (896.6, 1465.3, 6.0), "my27_left": (590.2, 1392.7, 4.0)},
        "R": {"my27_right": (1406.4, 1391.7, 4.0)}},
    # (the Pinata stem's corners, pin_top 984, 598 / 948, 600 and pin_back 963, 548 / 993, 541, are print that is not
    # mirror symmetric in the photos: 10 to 22 px off any symmetric solution; left out)
}
CENTRES = {
    # rear "360 Turbine" badge (blue blob centroid)
    # (V25 white's badge, v25w_back 999.4, 582.7, sits 58 px right of its DOT print, about 11 mm off the centre line:
    # a sticker placed differently on that kit; left out)
    "rear_badge": {"pin_back": (960.1, 632.3, 2.0), "pin_top": (961.2, 426.9, 2.0), "my27_back": (983.6, 566.3, 2.0),
                   "royal_back": (963.0, 581.0, 2.0)},
    # the "O" of the DOT print on the back (dark ring centroid)
    "dot_o": {"pin_back": (965.6, 1583.2, 1.5), "v25w_back": (940.9, 1563.0, 1.5), "my27_back": (978.6, 1467.0, 1.5),
              "royal_back": (965.0, 1568.0, 2.0)},
    # brow badge plate (purple blob; MY27: white plate)
    "brow_badge": {"pin_isoleft": (632.9, 534.5, 3.0), "pin_isoright": (1276.0, 540.1, 3.0),
                   "my27_isoleft": (698.6, 498.5, 4.0)},
    # the visor's tip on the centre line: its frontmost point in the side views and the top view (read at 2x). The
    # only landmark at the top view's front: without it the solve stretched that view 185 px (45 mm) past Leatt's tip
    # (round 4, first run). The visor's angle is adjustable and MY27's tip sits 20 to 28 px lower than Royal's: there
    # only the offset along the length (u) counts
    "visor_tip": {"royal_left": (216.0, 336.5, 2.0), "pin_top": (960.0, 1711.0, 2.0),
                  "my27_left": (226.0, 425.0, 3.0, 0.0), "my27_right": (1748.5, 376.0, 3.0, 0.0)},
    # the visor's rear edge across the crown (a line: only the offset across it counts)
    "visor_rear_edge": {"pin_top": (960.0, 792.0, 3.0, 90.0), "pin_back": (960.0, 447.0, 3.0, 90.0)},
}
# the art view of each landmark: where the model's print or part was placed from (for "model now")
ART_VIEW = {"eyeport_triangle": "pin_isoleft", "chin_vent": "royal_left", "side_screw": "pin_isoleft", "release_tab": "pin_isoleft", "rear_slot": "pin_back",
            "crown_vent": "pin_top", "side_vent": "pin_isoleft", "low_vent": "royal_left",
            "rear_badge": "pin_back", "dot_o": "pin_back", "brow_badge": "pin_isoleft",
            "visor_rear_edge": "pin_top", "visor_tip": "royal_left"}


# ------------------------------------------------------------------------------------------------ cameras
def basis(az, el, roll):
    a, e = math.radians(az), math.radians(el)
    dirn = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
    fwd = -dirn
    right = np.cross(fwd, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    r = math.radians(roll)
    right, up = right * math.cos(r) + up * math.sin(r), up * math.cos(r) - right * math.sin(r)
    return dirn, np.vstack([right, up, fwd])


def old_camera(view):
    """helmet.CAMS (the Pinata views each fitted alone to its own outline: the solve's start) as a camera dict."""
    C, Rm, f = H.cam_from(H.CAMS[view[4:]])
    return dict(R=Rm, C=C, f=f, cx=960.0, cy=960.0)


def initial_cameras():
    cams = {"pin_" + k: old_camera("pin_" + k) for k in ("isoleft", "isoright", "back", "top")}
    ty, tz, pitch = PL7
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    Rg = np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
    for k, x in MY27.items():
        dirn, Rm = basis(*x[:3])
        Cg = dirn * x[3] + MY27_TARGET
        cams["my27_" + k] = dict(R=Rm @ Rg.T, C=Rg @ Cg + np.array([0.0, ty, tz]), f=x[4], cx=960.0 + x[5],
                                 cy=960.0 + x[6])
    cams["v25w_isoleft"] = dict(cams["pin_isoleft"])
    cams["v25w_back"] = dict(cams["pin_back"])
    cams["royal_left"] = royal(1.5)
    # Royal_Back: straight behind, 10 deg up (the other back views solve to 8 to 11 deg), 1.6 m, 0.226 mm/px
    dirn, Rm = basis(180.0, 10.0, 0.0)
    cams["royal_back"] = dict(R=Rm, C=dirn * 1.6 + np.array([0.0, 0.02, 0.0]), f=7080.0, cx=960.0, cy=960.0)
    return cams


VIEWS = ["royal_left", "pin_isoleft", "pin_isoright", "pin_back", "pin_top", "v25w_isoleft", "v25w_back",
         "my27_isoleft", "my27_left", "my27_right", "my27_back", "royal_back"]
ROYAL_R = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [-1.0, 0.0, 0.0]])


def royal(D):
    """Royal_Left as the gauge camera (looking exactly along -x at distance D): the start of its solve."""
    return dict(R=ROYAL_R, C=np.array([D, (960 - H.U0) * H.S, -(960 - H.V0) * H.S]), f=D / H.S, cx=960.0, cy=960.0)


def project(cam, X):
    q = (np.atleast_2d(X) - cam["C"]) @ cam["R"].T
    return np.c_[cam["cx"] + cam["f"] * q[:, 0] / q[:, 2], cam["cy"] - cam["f"] * q[:, 1] / q[:, 2]]


def ray(cam, u, v):
    d = np.array([(u - cam["cx"]) / cam["f"], -(v - cam["cy"]) / cam["f"], 1.0]) @ cam["R"]
    return d / np.linalg.norm(d)


# ------------------------------------------------------------------------------------------------ observations
def observations():
    """Rows: (landmark, side, view, u, v, sigma, normal or None)."""
    rows = []
    for n, sides in PAIRS.items():
        for side, obs in sides.items():
            for v, o in obs.items():
                rows.append((n, side, v, o[0], o[1], o[2], None if len(o) < 4 else o[3]))
    for n, obs in CENTRES.items():
        for v, o in obs.items():
            rows.append((n, "C", v, o[0], o[1], o[2], None if len(o) < 4 else o[3]))
    return rows


ROWS = observations()
LMS = list(PAIRS) + list(CENTRES)
FREE = list(VIEWS)

# The silhouette Royal_Left traces is the shell's centre-plane profile behind the visor (helmet.CROWN_BACK, LOWER_EDGE;
# the rearmost and topmost points of a symmetric shell are on its centre plane): print on the centre line lies on it.
# These landmarks get a residual = their signed distance from that traced profile / PROFILE_SIGMA (the trace's +-3 px).
# Round 4: not the rear badge. Held on the profile it cost 63 to 77 px in the top view (round 3's 43 px rms); free, its
# four readings agree within 4 px 7 to 16 mm inside the profile. The top view sees the disc almost round (axes 0.89)
# and the back views at 0.6: it sits on a slope about 30 deg from level, ahead of the rear ledge, where the side
# silhouette (the ledge and the crown vents' raised pods either side) stands behind and above the centre line.
PROFILE_LMS = ("dot_o",)
PROFILE_SIGMA = 0.00075
_PROF = np.asarray(H.px2h(np.array(H.CROWN_BACK + H.LOWER_EDGE[1:], float)))


def profile_offset(y, z):
    """Signed distance (m, + outside) of (y, z) from the traced back profile."""
    A, B = _PROF[:-1], _PROF[1:]
    t = B - A
    L2 = (t * t).sum(1)
    P = np.array([y, z])
    w = np.clip(((P - A) * t).sum(1) / L2, 0, 1)
    Q = A + w[:, None] * t
    k = np.argmin(((P - Q) ** 2).sum(1))
    n = np.array([-t[k, 1], t[k, 0]]) / math.sqrt(L2[k])
    return float((P - Q[k]) @ n)


# ------------------------------------------------------------------------------------------------ the photos' outlines
def photo_mask(view):
    """The helmet's silhouette in a photo: Leatt's PNGs carry an alpha matte; the JPGs (plain studio background) are
    cut where the colour is more than 14 levels from the border's median, opened once; the largest piece, holes
    filled. The MY27 masks include the goggle strap and the floor shadow (left out below)."""
    from PIL import Image
    from scipy import ndimage
    im = Image.open(os.path.join(REF, PHOTOS[view]))
    if im.mode == "RGBA":
        m = np.asarray(im)[..., 3] > 128
    else:
        a = np.asarray(im.convert("RGB"), float)
        border = np.r_[a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)]
        m = np.sqrt(((a - np.median(border, 0)) ** 2).sum(-1)) > 14
        m = ndimage.binary_opening(m, iterations=1)
    lab, _ = ndimage.label(m)
    return ndimage.binary_fill_holes(lab == np.bincount(lab.ravel())[1:].argmax() + 1)


_SDF = {}


def sdf(view):
    """Signed distance (px, + outside) to the photo's silhouette."""
    if view not in _SDF:
        from scipy import ndimage
        m = photo_mask(view)
        _SDF[view] = (ndimage.distance_transform_edt(~m) - ndimage.distance_transform_edt(m)).astype(np.float32)
    return _SDF[view]


def sample(F, uv):
    from scipy import ndimage
    return ndimage.map_coordinates(F, [uv[:, 1], uv[:, 0]], order=1, mode="nearest")


# ------------------------------------------------------------------------------------------------ the model
def model_mesh():
    """The model now: shell outer surface and visor top as triangles (V, F), the shell's vertices and normals."""
    Vo, Fo, prof = H.shell_outer()
    G = H.visor_surface(prof)
    nr, nc, _ = G.shape
    Q = np.array(H.grid_faces(nr, nc)) + len(Vo)
    F = np.vstack([Fo, Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
    return np.vstack([Vo, G.reshape(-1, 3)]), F, Vo, H.normals(Vo, Fo)


def raycast(V, F, C, d):
    """Nearest hit of the ray C + t d (t > 0) on the triangles, or None."""
    v0 = V[F[:, 0]]
    e1, e2 = V[F[:, 1]] - v0, V[F[:, 2]] - v0
    p = np.cross(d, e2)
    det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    t0 = C - v0
    u = (t0 * p).sum(1) * inv
    q = np.cross(t0, e1)
    v = (q @ d) * inv
    t = (e2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return None if not hit.any() else C + np.min(np.where(hit, t, np.inf)) * d


# Shell outlines (decision 46: "landmarks plus silhouettes"). Each view's outline vertices of the model shell (edges
# between a face turned to the camera and one turned away, on the projected outline) must lie on the photo's outline:
# residual = the photo silhouette's signed distance at their projection / OUTLINE_SIGMA, OUTLINE_N per view evenly
# round the outline. Left out: the iso views (their outlines are mostly the brow, chin and visor: 13 to 15 px off
# before phase B rebuilds the front, and with them in the solve the iso readings went 20 to 30 px off), the visor (its wings stand 8 to 12 mm outside Leatt's outline in the top and back
# views: phase B), the shell's front (y < -0.10 m: brow, port and chin, rebuilt in phase B), the goggle and its strap
# where a photo shows them (MY27 rows, Pinata iso-right's goggle polygon), the MY27 floor shadow (z < -0.11 m) and
# (round 3) Royal_Left (then the gauge camera; round 4 frees it, its outline in: 1.7 to 2.4 px). The vertices are
# chosen at the current cameras, three rounds. Tried first (2026-11-15): the side views' traced profile only, with
# the cameras from the landmarks alone; the top and back cameras then put the shell's outline 11 to 18 mm off
# Leatt's (the landmarks of the back group float in depth), so the outlines are in the solve.
OUTLINE_SIGMA = 3.0        # px: the outline vertices' own spacing (3 to 5 mm) and the photo mask's edge
OUTLINE_N = 40
OUTLINE_ROUNDS = 3
FRONT_Y = -0.10
STRAP_ROWS = {"my27_left": (540, 880), "my27_right": (540, 880), "my27_back": (860, 1140)}
OUTLINE_VIEWS = ["pin_back", "pin_top", "v25w_back", "my27_left", "my27_right", "my27_back", "royal_left", "royal_back"]


class Outline:
    def __init__(self, V, F, n_shell):
        self.V, self.F, self.n_shell = V, F, n_shell
        E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
        fid = np.tile(np.arange(len(F)), 3)
        Es = np.sort(E, 1)
        key = Es[:, 0] * (len(V) + 1) + Es[:, 1]
        o = np.argsort(key)
        self.ES, self.EF, self.EK = Es[o], fid[o], key[o]
        self.FC = V[F].mean(1)
        self.FN = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
        from scipy.spatial import cKDTree
        self.Vs = V[:n_shell]
        self.Ns = H.normals(self.Vs, F[(F < n_shell).all(1)])
        self.tree = cKDTree(self.Vs)

    def vertices(self, cam, view, nmax=OUTLINE_N):
        """The shell's outline vertices seen from cam (indices), with the left-out parts removed."""
        from PIL import Image, ImageDraw
        from scipy import ndimage
        V, F = self.V, self.F
        face = np.sign(((cam["C"] - self.FC) * self.FN).sum(1))
        a = np.nonzero(self.EK[1:] == self.EK[:-1])[0]
        idx = np.unique(self.ES[a[face[self.EF[a]] != face[self.EF[a + 1]]]].ravel())
        uv = project(cam, V)
        im = Image.new("L", (W // 2, W // 2), 0)
        d = ImageDraw.Draw(im)
        for f in F:
            d.polygon([tuple(uv[i] / 2) for i in f], fill=255)
        m = np.asarray(im) > 0
        dist = ndimage.distance_transform_edt(~(m & ~ndimage.binary_erosion(m)))
        q = uv[idx] / 2
        ok = (q[:, 0] > 0) & (q[:, 0] < W // 2 - 1) & (q[:, 1] > 0) & (q[:, 1] < W // 2 - 1)
        ok[ok] = dist[q[ok, 1].astype(int), q[ok, 0].astype(int)] < 1.5
        ok &= (V[idx, 1] > FRONT_Y) & (idx < self.n_shell)
        if view in STRAP_ROWS:
            ok &= ~((uv[idx, 1] > STRAP_ROWS[view][0]) & (uv[idx, 1] < STRAP_ROWS[view][1]))
        if view == "royal_left":            # the crown ahead of y 30 mm: under Leatt's visor (it reaches y 21 mm)
            ok &= V[idx, 1] > 0.03
        if view.startswith("my27"):
            ok &= V[idx, 2] > -0.11
        if view == "pin_isoright":
            from matplotlib.path import Path
            ok &= ~Path(np.array(H.ISORIGHT_GOGGLE, float)).contains_points(uv[idx])
        idx = idx[ok]
        if len(idx) > nmax:
            c = uv[idx].mean(0)
            ang = np.arctan2(uv[idx, 1] - c[1], uv[idx, 0] - c[0])
            idx = idx[np.argsort(ang)][np.linspace(0, len(idx) - 1, nmax).astype(int)]
        return idx

    def offsets_mm(self, cam, view):
        """Each outline vertex's position against the photo's outline (mm at its depth; + = the model lies outside
        the photo's silhouette, too wide or too long there): (vertices, offsets)."""
        idx = self.vertices(cam, view, nmax=10 ** 9)
        P = self.V[idx]
        depth = (P - cam["C"]) @ cam["R"][2]
        return P, sample(sdf(view), project(cam, P)) * depth / cam["f"] * 1000


# Landmarks on the measured shell (away from the front) lie on its surface: residual = signed distance from the model
# shell / SURFACE_SIGMA. Without it (first run, 2026-11-15) the outlines fixed each camera's scale but not its distance
# (a long-lens camera's outline barely changes with distance at fixed scale), and the back group's points settled 16 to
# 29 mm inside the shell. The front's landmarks (brow badge, eye port, chin, release tab, side screw) stay free: the
# front is rebuilt in phase B from them.
# Round 4: not the rear badge (the traced profile, which the shell's centre line follows, is not its surface there:
# PROFILE_LMS); measured free from its five views, it is reported against the shell.
SURFACE_LMS = ("rear_slot", "crown_vent", "side_vent", "low_vent", "dot_o")
SURFACE_SIGMA = 0.0015

LOGF_SIGMA = 0.25          # prior on each camera's log focal length (and so its distance) about its start: 25 %
ROBUST = 2.0               # soft-l1 loss scale in sigma units: a misread point or a stray outline cannot drag a camera


class Problem:
    def __init__(self, cams0, pts0, outline=None):
        self.cams0, self.outline, self.sidx = cams0, outline, {}
        self.p_index, k = {}, 0
        for v in FREE:
            self.p_index[v] = k
            k += 7
        for n in LMS:
            self.p_index[n] = k
            k += 3 if n in PAIRS else 2
        self.n = k
        x = np.zeros(k)
        for v in FREE:
            x[self.p_index[v] + 3:self.p_index[v] + 6] = cams0[v]["C"]
            x[self.p_index[v] + 6] = math.log(cams0[v]["f"])
        for n in LMS:
            i = self.p_index[n]
            x[i:i + (3 if n in PAIRS else 2)] = pts0[n] if n in PAIRS else pts0[n][1:]
        self.x0 = x

    def cam(self, x, v):
        i = self.p_index[v]
        c0 = self.cams0[v]
        R = Rotation.from_rotvec(x[i:i + 3]).as_matrix() @ c0["R"]
        return dict(R=R, C=x[i + 3:i + 6], f=math.exp(x[i + 6]), cx=c0["cx"], cy=c0["cy"])

    def point(self, x, n, side):
        i = self.p_index[n]
        if n in CENTRES:
            return np.array([0.0, x[i], x[i + 1]])
        p = x[i:i + 3].copy()
        if side == "R":
            p[0] = -p[0]
        return p

    def residuals(self, x, rows=None, per_row=False):
        rows = ROWS if rows is None else rows
        cams = {v: self.cam(x, v) for v in VIEWS}
        out = []
        for n, side, v, u, vv, s, nrm in rows:
            uv = project(cams[v], self.point(x, n, side))[0] - (u, vv)
            if nrm is None:
                out.append(uv / s)
            else:
                a = math.radians(nrm)
                out.append(np.array([np.dot(uv, (math.cos(a), math.sin(a))) / s]))
        return out if per_row else np.concatenate(out)

    def profile(self, x):
        return np.array([profile_offset(*self.point(x, n, "L")[1:]) / PROFILE_SIGMA for n in PROFILE_LMS])

    def outlines(self, x, per_view=False):
        out = []
        for v in OUTLINE_VIEWS:
            idx = self.sidx.get(v, np.zeros(0, int))
            out.append(sample(sdf(v), project(self.cam(x, v), self.outline.V[idx])) / OUTLINE_SIGMA if len(idx)
                       else np.zeros(0))
        return out if per_view else np.concatenate(out)

    def surface(self, x):
        if self.outline is None:
            return np.zeros(0)
        P = np.array([self.point(x, n, "L") for n in SURFACE_LMS])
        j = self.outline.tree.query(P)[1]
        return np.sum((P - self.outline.Vs[j]) * self.outline.Ns[j], 1) / SURFACE_SIGMA

    def priors(self, x):
        return np.array([(x[self.p_index[v] + 6] - self.x0[self.p_index[v] + 6]) / LOGF_SIGMA for v in FREE])

    def all(self, x):
        return np.concatenate([self.residuals(x), self.profile(x), self.outlines(x), self.surface(x), self.priors(x)])

    def choose_outlines(self, x):
        self.sidx = {v: self.outline.vertices(self.cam(x, v), v) for v in OUTLINE_VIEWS}


def initial_points(cams, mesh):
    """Each landmark's start: the ray of its art view's start camera through the photo point, cast onto the model
    (shell and visor); the visor's rear edge starts on the visor's top at its rear end."""
    V, F = mesh[:2]
    pts = {}
    for n in LMS:
        av = ART_VIEW[n]
        o = (PAIRS[n]["L"] if n in PAIRS else CENTRES[n]).get(av)
        p = None
        if o is not None and len(o) == 3:
            p = raycast(V, F, cams[av]["C"], ray(cams[av], o[0], o[1]))
        if p is None:
            p = np.array([0.0, 0.0087, 0.13])
        p[0] = 0.0 if n in CENTRES else abs(p[0])
        pts[n] = p
    return pts


FORE_MIN = 0.25
FORE_LMS = SURFACE_LMS + ("side_screw", "release_tab", "eyeport_triangle", "chin_vent", "brow_badge")


def foreshorten(cams, pts, mesh, log=print):
    """A reading's sigma / cos(incidence) (the view direction against the model shell's normal at the landmark's
    start point, at least FORE_MIN): a feature seen at a grazing angle is foreshortened and, recessed or raised, its
    visible centroid shifts by its depth or height (the crown vents from behind: cos 0.13 to 0.15). Changes ROWS."""
    from scipy.spatial import cKDTree
    Vo, N = mesh[2], mesh[3]
    tree = cKDTree(Vo)
    for k, (n, side, v, u, vv, s, nrm) in enumerate(ROWS):
        if n not in FORE_LMS:
            continue
        p = pts[n].copy()
        if side == "R":
            p[0] = -p[0]
        d = p - cams[v]["C"]
        cs = abs(float(N[tree.query(p)[1]] @ (d / np.linalg.norm(d))))
        ROWS[k] = (n, side, v, u, vv, s / max(cs, FORE_MIN), nrm)


def solve(log=print):
    cams0 = initial_cameras()
    mesh = model_mesh()
    pts0 = initial_points(cams0, mesh)
    foreshorten(cams0, pts0, mesh)
    pb = Problem(cams0, pts0, Outline(mesh[0], mesh[1], len(mesh[2])))
    x = pb.x0.copy()
    r = None
    for it in range(OUTLINE_ROUNDS):
        pb.choose_outlines(x)
        r = least_squares(pb.all, x, method="trf", loss="soft_l1", f_scale=ROBUST, x_scale="jac", max_nfev=200)
        x = r.x
        s = pb.outlines(x) * OUTLINE_SIGMA
        log("round %d: landmarks rms %.2f sigma, outlines rms %.2f px (median |.| %.2f px), %s" % (
            it, np.sqrt(np.mean(pb.residuals(x) ** 2)), np.sqrt(np.mean(s ** 2)), np.median(np.abs(s)), r.message))
    # then plain least squares (the constraints that hold the landmarks on the shell act in full), for the covariance
    r = least_squares(pb.all, x, method="trf", x_scale="jac", max_nfev=300)
    s = pb.outlines(r.x) * OUTLINE_SIGMA
    log("final (least squares): landmarks rms %.2f sigma, outlines rms %.2f px, %s" % (
        np.sqrt(np.mean(pb.residuals(r.x) ** 2)), np.sqrt(np.mean(s ** 2)), r.message))
    return pb, r, mesh


def model_now(mesh, cams):
    """Where the model's own feature sits: the ray of the art view's solved camera (the print is traced through
    them, helmet.PRINT_CAMS, round 4) through the photo point, cast onto the model now."""
    V, F = mesh[:2]
    out = {}
    for nm in LMS:
        av = ART_VIEW[nm]
        o = (PAIRS[nm]["L"] if nm in PAIRS else CENTRES[nm]).get(av)
        if o is None or len(o) > 3:
            out[nm] = None
            continue
        c = cams[av]
        out[nm] = raycast(V, F, c["C"], ray(c, o[0], o[1]))
    return out


def solved_cameras(path=BA_JSON):
    """The solved cameras of a solution file (default research/helmet-ba.json) as dicts: C, R, f, cx, cy."""
    ba = json.load(open(path))
    return {v: dict(C=np.array(c["C"]), R=np.array(c["R"]), f=c["f"], cx=c["cx"], cy=c["cy"])
            for v, c in ba["cameras"].items()}


BAND_VIEWS = ("pin_back", "v25w_back", "my27_back", "pin_top")


def outline_bands(cams=None, views=BAND_VIEWS):
    """The current shell's outline against each photo's through the solved cameras (mm, + = the model outside the
    photo's silhouette), the median per band: back views by height (10 mm bands, z -140 to +60 mm), the top view by
    length (20 mm bands, y -20 to +160 mm). Bands with fewer than 3 outline vertices are left out."""
    cams = cams or solved_cameras()
    V, F, Vo, _ = model_mesh()
    O = Outline(V, F, len(Vo))
    out = {}
    for v in views:
        P, off = O.offsets_mm(cams[v], v)
        key, lo, w, n = (P[:, 1], -0.02, 0.02, 9) if v == "pin_top" else (P[:, 2], -0.14, 0.01, 20)
        out[v] = {}
        for k in range(n):
            b = lo + k * w
            sel = (key >= b) & (key < b + w)
            if sel.sum() >= 3:
                out[v][round(b * 1000)] = float(np.median(off[sel]))
    return out


def main():
    pb, r, mesh = solve()
    x = r.x
    res = pb.residuals(x, per_row=True)
    J = r.jac
    rr = pb.all(x)
    m, n = len(rr), pb.n
    chi2 = float(np.sum(rr ** 2))
    dof = m - n
    s2 = max(1.0, chi2 / max(dof, 1))
    cov = np.linalg.pinv(J.T @ J) * s2
    sil = pb.outlines(x, per_view=True)
    print("residuals %d (landmark photo coordinates %d in %d readings, profile %d, outline points %d, surface %d, "
          "priors %d), "
          "unknowns %d, chi2 %.1f, reduced %.2f" % (m, len(pb.residuals(x)), len(ROWS), len(PROFILE_LMS),
                                                    sum(len(s) for s in sil), len(SURFACE_LMS), len(pb.priors(x)), n, chi2,
                                                    chi2 / dof))
    fwd = pb.cam(x, "royal_left")["R"][2]
    print("Royal_Left looks %.2f deg forward of -x (camera behind the side), %.2f deg up" % (
        math.degrees(math.atan2(-fwd[1], -fwd[0])), math.degrees(math.asin(fwd[2]))))
    print("profile offsets mm", dict(zip(PROFILE_LMS, np.round(pb.profile(x) * PROFILE_SIGMA * 1000, 2))))
    print("surface offsets mm", dict(zip(SURFACE_LMS, np.round(pb.surface(x) * SURFACE_SIGMA * 1000, 2))))
    out = dict(frame="HELMET: metres, x to the wearer's left, y back, z up (helmet.py)",
               method="bundle adjustment: landmarks, the centre-line profile, shell outlines (helmet_ba.py)",
               reduced_chi2=chi2 / dof, cameras={}, landmarks={}, observations=[list(o) for o in ROWS])
    cams = {v: pb.cam(x, v) for v in VIEWS}
    for v in VIEWS:
        c = cams[v]
        e = [res[k] * ROWS[k][5] for k in range(len(ROWS)) if ROWS[k][2] == v]
        px = np.concatenate(e) if e else np.zeros(0)
        rms = float(np.sqrt(np.mean(px ** 2))) if len(px) else float("nan")
        d = float(-(c["C"] @ c["R"][2]))
        mmpx = d / c["f"] * 1000
        so = sil[OUTLINE_VIEWS.index(v)] * OUTLINE_SIGMA if v in OUTLINE_VIEWS else np.zeros(0)
        orms = float(np.sqrt(np.mean(so ** 2))) if len(so) else float("nan")
        out["cameras"][v] = dict(photo=PHOTOS[v], C=c["C"].tolist(), R=c["R"].tolist(), f=c["f"], cx=c["cx"],
                                 cy=c["cy"], W=W, H=W, landmark_rms_px=rms, n_landmark_readings=len(e),
                                 outline_rms_px=orms, n_outline_points=len(so), depth_of_origin=d,
                                 mm_per_px_at_origin=mmpx)
        print("%-13s landmarks rms %5.2f px (%2d)  outline rms %5.2f px (%3d)  f %6.0f  depth %.2f m  %.3f mm/px" % (
            v, rms, len(e), orms, len(so), c["f"], d, mmpx))
    now = model_now(mesh, cams)
    Vo, NV = mesh[2], mesh[3]
    print("%-16s %-22s %-17s %-22s %-22s %s" % ("landmark", "measured mm", "sigma mm", "model now mm", "difference mm",
                                               "off the shell mm"))
    for nm in LMS:
        i = pb.p_index[nm]
        k = 3 if nm in PAIRS else 2
        sd = np.sqrt(np.diag(cov)[i:i + k])
        p = pb.point(x, nm, "L" if nm in PAIRS else "C")
        sig = sd if nm in PAIRS else np.r_[0.0, sd]
        j = np.argmin(((Vo - p) ** 2).sum(1))
        off = float((p - Vo[j]) @ NV[j])
        M = now[nm]
        rows = [(ROWS[j][1], ROWS[j][2], (res[j] * ROWS[j][5]).round(1).tolist()) for j in range(len(ROWS))
                if ROWS[j][0] == nm]
        out["landmarks"][nm] = dict(kind="pair (L given; R = mirror)" if nm in PAIRS else "centre", X=p.tolist(),
                                    sigma=sig.tolist(), model_now=None if M is None else M.tolist(),
                                    off_shell=off, residuals_px=rows)
        f = lambda a: "(%s)" % ", ".join("%.0f" % (q * 1000) for q in a)  # noqa: E731
        print("%-16s %-22s %-17s %-22s %-22s %+.1f" % (nm, f(p), f(sig), f(M) if M is not None else "-",
                                                      f(p - M) if M is not None else "-", off * 1000))
    for nm in LMS:
        print("   %-16s %s" % (nm, out["landmarks"][nm]["residuals_px"]))
    path = sys.argv[1] if len(sys.argv) > 1 else BA_JSON
    json.dump(out, open(path, "w"), indent=1)
    print("written", path)


if __name__ == "__main__":
    main()
