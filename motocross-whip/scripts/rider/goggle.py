"""Damien's goggle and eyes: Leatt Velocity 5.5 Iriz (Pinata Teal frame and strap) with a purple mirror lens, and
his brown eyes behind it. Built by helmet.py (build calls build_goggle and eyes); helmet.py's CLI writes the npz.

Frames: GOGGLE frame = metres, x to the wearer's left, y backwards, z up (the axes of body.py's MB frame), origin
at the midpoint of his eye centres; the goggle is placed on his face by a translation only (the shapes are measured
square to the face). HELMET frame: helmet.py's.

Sources (research/rider-ledger/goggle.md has every number with its source):
  SHAPE     Leatt's MY27 Moto 8.5 kit photos with the Velocity 5.5 on (us.leatt.com moto-8-5-helmet-kit,
            31505_..._Blue_Red_1/2/4_1027000180.jpg, saved in reference/leatt-gear/goggles/) through pinhole cameras
            fitted to the helmet shell's silhouette (fitted in helmet.py's helmet frame): the goggle's front outline
            back-projected onto its front surface, the side profile from the side views; the Pinata Teal ISO view
            and Leatt's exploded view for the facets, vents and nose bridge.
  SCALE     the helmet (its own 45 mm strap scale, helmet.py).
  EYES      MakeHuman's CC0 high-poly eye proxy fitted by its mhclo onto his shaped mesh puts the eyeball (radius
            0.955 x and centre 0.03 x the helper-eye sphere's radius behind its centre) where the lids close round
            it; here it is rebuilt by script on the same sphere, iris and cornea anatomical (iris 11.8 mm, pupil
            3.6 mm in daylight, cornea radius 7.8 mm).
"""
import json
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import helmet as H      # noqa: E402
import mhdata as mh     # noqa: E402

TEXDIR = H.TEXDIR


# ---------------------------------------------------------------- eyes
EYE_R_OVER_HELPER = 0.9554         # MakeHuman eye proxy (CC0 high-poly, mhclo-fitted on his mesh): eyeball radius
EYE_BACK_OVER_HELPER = 0.0317      # ... and its centre behind the helper-eye sphere's centre, both / helper radius
IRIS_R = 0.0059                    # m, iris radius (adult mean 11.7 to 11.8 mm diameter)
PUPIL_R = 0.0018                   # m, pupil radius in daylight (3 to 4 mm)
CORNEA_RC = 0.0078                 # m, anterior corneal radius of curvature (adult mean 7.8 mm)
EYE_THETA_MAX = math.radians(120)  # the cap kept (the rest lies deep in the socket)
EYE_TEX = 512


def helper_sphere(body, side):
    """Centre and radius of MakeHuman's helper-eye sphere on his shaped mesh (MB rest frame)."""
    meta = json.loads(str(body["meta"]))
    base = mh.Base()
    V = mh.to_mb(mh.shape(base, meta["macro"]))
    V[:, 2] -= V[base.group_verts("body"), 2].min()
    P = V[base.group_verts(f"helper-{side}-eye")]
    A = np.c_[2 * P, np.ones(len(P))]
    s = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    return s[:3], float(np.sqrt(s[3] + s[:3] @ s[:3]))


def eye_geometry(body):
    """Eyeball centre and radius per side ('L', 'R'), gaze along -y (ahead)."""
    out = {}
    for s, side in (("L", "l"), ("R", "r")):
        c, r = helper_sphere(body, side)
        out[s] = (c + np.array([0.0, EYE_BACK_OVER_HELPER * r, 0.0]), EYE_R_OVER_HELPER * r)
    return out


EYE_UV_POW = 0.6                   # polar map r = 0.5 (theta / EYE_THETA_MAX) ** 0.6: more texels on the iris


def eye_texture(path, n=EYE_TEX, R=0.0158):
    """Brown eye (Damien), polar map: texel at radius r from the centre -> angle from the gaze axis
    theta = (r / 0.5) ** (1 / EYE_UV_POW) * EYE_THETA_MAX, round it phi. Pupil, iris with radial fibres, an amber
    collarette and a dark limbal ring, sclera off-white with a few faint vessels towards the back. By script."""
    from PIL import Image, ImageDraw
    rng = np.random.default_rng(114)
    u, v = np.meshgrid((np.arange(n) + 0.5) / n * 2 - 1, (np.arange(n) + 0.5) / n * 2 - 1)
    th = np.hypot(u, v) ** (1 / EYE_UV_POW) * EYE_THETA_MAX
    ph = np.arctan2(v, u)
    rho = R * np.sin(np.minimum(th, np.pi / 2))                     # radius in the eye's frontal projection
    k = np.arange(1, 90)
    amp = rng.normal(0, 1, len(k)) / np.sqrt(k)
    pha = rng.uniform(0, 2 * np.pi, len(k))
    fib = np.zeros_like(ph)
    for a, kk, p in zip(amp, k, pha):
        fib += a * np.cos(kk * ph + p)
    fib = fib / np.abs(fib).max()
    t = np.clip((rho - PUPIL_R) / (IRIS_R - PUPIL_R), 0, 1)            # 0 at the pupil edge, 1 at the limbus
    dark = np.array([58, 32, 18.0])                                   # brown iris (sRGB)
    mid = np.array([104, 60, 28.0])
    amber = np.array([150, 98, 44.0])
    iris = dark + (mid - dark) * (0.5 + 0.5 * fib[..., None]) * (1 - 0.6 * t[..., None])
    coll = np.exp(-((t - 0.28) / 0.08) ** 2)[..., None]               # collarette ring
    iris = iris + (amber - iris) * 0.55 * coll * (0.6 + 0.4 * fib[..., None])
    limb = np.clip((t - 0.82) / 0.18, 0, 1)[..., None]
    iris = iris * (1 - 0.55 * limb)
    sclera = np.array([236, 230, 222.0]) * np.ones_like(iris)
    vm = Image.new("L", (n, n), 0)                                    # a few thin, wandering vessels
    dv = ImageDraw.Draw(vm)
    for _ in range(16):
        t_, p_ = math.radians(118), rng.uniform(0, 2 * np.pi)
        pts = []
        while t_ > math.radians(rng.uniform(48, 75)):
            r_ = 0.5 * (t_ / EYE_THETA_MAX) ** EYE_UV_POW
            pts.append(((0.5 + r_ * math.cos(p_)) * n, (0.5 + r_ * math.sin(p_)) * n))
            t_ -= math.radians(3)
            p_ += rng.normal(0, 0.05)
        dv.line(pts, fill=int(rng.uniform(60, 140)), width=1)
    vein = np.array(vm, float) / 255.0
    back = np.clip((th - math.radians(45)) / math.radians(50), 0, 1)
    sclera = sclera + (np.array([200, 120, 110.0]) - sclera) * (vein * 0.5)[..., None]
    sclera = sclera * (1 - 0.15 * back[..., None])
    img = np.where((rho < PUPIL_R)[..., None], np.array([10, 8, 7.0]), iris)
    lim = np.clip((rho - IRIS_R) / 0.0004, 0, 1)[..., None] * (th < np.pi / 2)[..., None] + (th >= np.pi / 2)[..., None]
    img = img * (1 - lim) + sclera * lim
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)


def _frame(gaze):
    g = gaze / np.linalg.norm(gaze)
    a = np.cross(g, [0, 0, 1.0])
    a /= np.linalg.norm(a)
    b = np.cross(a, g)
    return g, a, b


def build_eyes(body, nth=40, nph=64):
    """Eyeballs and corneas, each riding its eye bone (eye.L / eye.R) rigidly."""
    parts = []
    geo = eye_geometry(body)
    for s in ("L", "R"):
        c, R = geo[s]
        g, a, b = _frame(np.array([0.0, -1.0, 0.0]))
        ball = H.Part("eye_ball_" + s, bone="eye." + s)
        ths = np.r_[np.linspace(0, math.asin(IRIS_R / R), 14)[1:], np.linspace(math.asin(IRIS_R / R), EYE_THETA_MAX, nth)[1:]]
        phs = np.linspace(0, 2 * np.pi, nph, endpoint=False)
        # the cornea's bulge: over the iris the surface follows a sphere of radius CORNEA_RC meeting the eyeball
        # at the limbus (a separate refracting dome over a painted iris looked like a glass bead)
        axial = math.sqrt(R * R - IRIS_R * IRIS_R)
        sc = axial - math.sqrt(CORNEA_RC ** 2 - IRIS_R ** 2)

        def radius(th):
            return max(R, sc * math.cos(th) + math.sqrt(max(CORNEA_RC ** 2 - (sc * math.sin(th)) ** 2, 0.0)))
        apex = ball.add((c + g * radius(0.0))[None], [], "eye_ball")
        rings = []
        for th in ths:
            P = c + radius(th) * (np.cos(th) * g + np.sin(th) * (np.cos(phs)[:, None] * a + np.sin(phs)[:, None] * b))
            rings.append(ball.add(P, [], "eye_ball") + np.arange(nph))

        def uvp(th, ph):
            r = (th / EYE_THETA_MAX) ** EYE_UV_POW * 0.5
            return (0.5 + r * math.cos(ph), 0.5 + r * math.sin(ph))
        for j in range(nph):
            k = (j + 1) % nph
            ball.F.append([apex, rings[0][j], rings[0][k]]); ball.M.append("eye_ball")
            ball.UV.append([uvp(0, 0), uvp(ths[0], phs[j]), uvp(ths[0], phs[j] + 2 * np.pi / nph)])
        for i in range(len(ths) - 1):
            for j in range(nph):
                k = (j + 1) % nph
                phk = phs[j] + 2 * np.pi / nph
                ball.F.append([rings[i][j], rings[i + 1][j], rings[i + 1][k], rings[i][k]]); ball.M.append("eye_ball")
                ball.UV.append([uvp(ths[i], phs[j]), uvp(ths[i + 1], phs[j]), uvp(ths[i + 1], phk), uvp(ths[i], phk)])
        parts.append(ball)
    return parts, dict(eye_radius_mm=round(geo["L"][1] * 1000, 2),
                       eye_centres=[np.round(geo[s][0], 4).tolist() for s in ("L", "R")])


# ---------------------------------------------------------------- the goggle's shape (GOGGLE frame, metres)
# The lens front is a cylinder: plan an ellipse y = A (1 - sqrt(1 - (x / a)^2)) (origin at its front centre),
# rulings tilted back by TILT at the top. Points on it are named by (s, z): s the arc length along the plan from
# the centre (+ to his left), z the height. Outlines are closed curves in (s, z) from control points on the left
# half, mirrored for the right. GP holds every fitted number (Leatt's photos: see the ledger, goggle.md).
#
# The Velocity 5.5 frame (round 4: Leatt's goggle-alone photos as calibrated views, fitted jointly with their
# cameras on outlines, creases and landmarks; research/rider-ledger/goggle.md): the lens sits recessed in the
# frame, whose front face stands lip (about 6 mm) proud of it with an inner wall down to the lens; the faces are
# flat with crisp edges: the raised top band with its stepped centre, the thick side pillars (whose outer walls
# carry the outriggers), the deep lower band with chunky cheeks, the beak's legs either side of a wide nose arch.
# Behind the face: a band rising back to the outline edge, the top surface, a step in to the vent row, the outer
# wall back to the foam seat. The face side's opening (the foam's inner edge) is smaller than the lens and rises
# over the nose: through a clear lens one sees the frame's inner face there.
# 15 control points a half (top centre to bottom centre), named in CTRL; the per-point lists in GP (out, open, inner
# and their fillets) follow CTRL. The front face between the lens edge and the outline edge has a crease across it
# (mid ring, at mid_t of the way out, mid_w proud of the straight face): two facets per cross-section, and a
# transverse crease at every control point (straight runs between them, joined by fillets).
# Round 6 (fair by construction, a moulded part): the outlines' offsets and every cross-section value are low-order
# smooth curves along the frame (bspline_half: a uniform cubic B-spline over the half loop, 24 coefficients for the
# outlines, 16 for the fields, mirrored at the centre line), fitted with a bending penalty; round 5's per-sample
# offsets and per-point values let each sample pull the surface on its own and the faces read as crumpled plastic.
CTRL = ("top_c", "step_hi", "step_lo", "fin_root", "top_corner", "side_top", "side_end", "bot_corner", "cheek",
        "cheek_step", "leg_out", "tab_tip", "notch_side", "arch_step", "notch_apex")


def ci(name):
    return CTRL.index(name)


GP = dict(
    a=0.13480, A=0.09390, tilt=0.0,          # lens plan (round 5 fit, kept in round 6; round 4: 137.7, 89.8 mm)
    # frame outer edge (the outline seen from the front): control polygon (the corners)
    out=[(0.0, 0.04489), (0.03851, 0.04150), (0.04566, 0.04091), (0.08819, 0.03407), (0.09441, 0.02973),
         (0.10524, 0.02513), (0.11323, -0.00422), (0.10345, -0.04097), (0.06352, -0.05291), (0.05004, -0.05525),
         (0.03354, -0.05470), (0.02951, -0.05494), (0.01580, -0.05518), (0.00797, -0.04647), (0.0, -0.03102)],
    # the lens's visible edge (the foot of the frame's inner wall, lip deep)
    open=[(0.0, 0.03415), (0.04188, 0.03179), (0.04273, 0.03173), (0.07949, 0.03150), (0.09042, 0.02911),
          (0.10022, 0.01908), (0.10347, -0.00965), (0.09294, -0.03374), (0.05517, -0.04209), (0.04572, -0.04627),
          (0.03065, -0.05070), (0.01903, -0.04168), (0.01085, -0.03193), (0.00794, -0.03220), (0.0, -0.03035)],
    # the face side's opening (frame inner wall, foam inner edge), rising over the bridge of his nose
    inner=[(0.0, 0.02814), (0.04009, 0.03305), (0.04100, 0.03408), (0.08544, 0.03274), (0.09361, 0.02503),
           (0.09492, 0.01517), (0.08997, -0.00039), (0.09085, -0.02743), (0.05791, -0.02800), (0.04233, -0.03199),
           (0.03293, -0.02899), (0.02502, -0.02757), (0.01468, -0.02037), (0.00667, -0.01684), (0.0, -0.01296)],
    # corner fillets at each control point: moulded edges, small (the tabs, the step and the notch pointed;
    # round 5's, kept in round 6)
    fillet_out=[0.00300, 0.00050, 0.00050, 0.00300, 0.00300, 0.00300, 0.00300, 0.00300, 0.00200, 0.00200, 0.00120,
                0.00120, 0.00200, 0.00150, 0.00150],
    fillet_open=[0.00300, 0.00300, 0.00300, 0.00300, 0.00400, 0.00400, 0.00300, 0.00400, 0.00300, 0.00300, 0.00300,
                 0.00300, 0.00300, 0.00300, 0.00400],
    fillet_inner=[0.00500, 0.00500, 0.00500, 0.00600, 0.00600, 0.00600, 0.00500, 0.00600, 0.00600, 0.00600,
                  0.00600, 0.00600, 0.00800, 0.01000, 0.01200],
    # cross-section fields (round 6: the coefficients of a bspline_half over outline_t, the outer edge's arc
    # length from the top centre, 0, to the bottom centre, 1; m): frame depth behind the lens front (to the foam
    # seat), front rim width, the 45 deg chamfer behind it, the depth of the outline edge behind the rim (the
    # front face rises back to it), the depth of the top surface's back edge (the step in to the vent row), and
    # the face's crease (mid_t of the way out, mid_w proud)
    depth=[0.02259, 0.02250, 0.02314, 0.02345, 0.02303, 0.02120, 0.01809, 0.01633, 0.01609, 0.01638, 0.01676,
           0.01656, 0.01380, 0.00893, 0.00250, 0.00200],
    rim=[0.00294, 0.00297, 0.00289, 0.00274, 0.00275, 0.00295, 0.00293, 0.00241, 0.00252, 0.00283, 0.00286,
         0.00287, 0.00301, 0.00303, 0.00298, 0.00290],
    chamfer=[0.00089, 0.00091, 0.00086, 0.00072, 0.00067, 0.00080, 0.00080, 0.00071, 0.00083, 0.00105, 0.00138,
             0.00178, 0.00203, 0.00153, 0.00121, 0.00126],
    band=[0.00084, 0.00267, 0.00456, 0.00488, 0.00499, 0.00948, 0.01172, 0.00960, 0.00889, 0.00827, 0.00574,
          0.00218, 0.00280, 0.00383, 0.00318, 0.00367],
    top=[0.01301, 0.01300, 0.01306, 0.01318, 0.01315, 0.01368, 0.01424, 0.01408, 0.01239, 0.01024, 0.00899,
         0.00834, 0.00730, 0.00558, 0.00453, 0.00440],
    mid_w=[-0.00216, -0.00215, -0.00172, -0.00052, 0.00039, 0.00026, -0.00072, -0.00080, 0.00020, 0.00139, 0.00196,
           0.00181, -0.00008, 0.00001, 0.00037, 0.00076],
    mid_t=[0.6293, 0.5186, 0.4312, 0.4250, 0.3189, 0.3461, 0.5595, 0.5511, 0.3827, 0.2371, 0.3941, 0.5839, 0.5072,
           0.5094, 0.4032, 0.5767],
    # the frame's front face stands this far proud of the lens front (the same kind of field: the top band 9.2 to
    # 9.5 mm, the side pillars and lower corners 6.6 to 6.9 mm, the cheeks and nose 8.5 to 9.3 mm at the corners)
    lip=[0.00905, 0.00951, 0.00963, 0.00873, 0.00804, 0.00660, 0.00660, 0.00660, 0.00660, 0.00660, 0.00778,
         0.00959, 0.00872, 0.00820, 0.00957, 0.00899],
    step=0.00184,           # the vent row's step in
    taper=0.00187,          # the outer wall leans out this much from the step to the back
    # samples per control segment of the left half (fillet_closed), and (round 6) the outer edge's and the lens
    # edge's smooth outward offsets (m): bspline_half coefficients over each polygon's own arc length, fitted on
    # nine photos with a bending penalty and held near 0 at the control points (ledger goggle.md)
    per=[40, 6, 40, 6, 6, 15, 21, 20, 7, 8, 6, 7, 6, 8],
    out_dk=[-0.00011, 0.00023, 0.00038, -0.00018, 0.00010, 0.00182, 0.00105, -0.00023, 0.00003, -0.00001, -0.00045,
            -0.00004, -0.00006, 0.00022, -0.00008, -0.00025, -0.00019, 0.00003, 0.00003, -0.00003, 0.00001,
            0.00002, -0.00002, 0.0],
    open_dk=[-0.00003, 0.00007, 0.00006, 0.0, 0.00001, -0.00010, -0.00024, 0.00005, -0.00001, 0.00018, -0.00044,
             -0.00095, 0.00038, 0.00189, -0.00004, -0.00135, -0.00101, -0.00011, 0.00014, -0.00010, 0.00008,
             -0.00001, -0.00001, 0.00001],
    # the top band's teeth (tooth_drop): |s| in, |s| out, drop at each end (m)
    teeth=[[0.04360, 0.05900, 0.0, 0.00150], [0.05900, 0.07950, 0.00166, 0.00138]],
    # outriggers (outrigger_frames): fitted with the shape (round 5, kept in round 6)
    or_len=0.03040,
    or_back_h=0.05870,
    or_turn=0.44010,
    or_top_in=0.00320,
    or_bot_in=0.00350,
    or_back_dz=0.00060,
    or_front=0.00220,
)
NOSE_S = 0.030                     # |s| inside which the foam leaves the frame's back for the nose bridge
VENT_ROWS = (0.3, 0.7)             # the top vents' slots run between these fractions of the outer wall's depth
# rings round the frame's cross-section: a lens contact, b lip, c rim inner edge, d rim outer edge, e chamfer,
# e2 the front face's crease, f outline edge, f2 top surface back, g step, v1 v2 vent rows, k outer wall back,
# l back face inner edge (the face side's opening), m inner wall at the lens stack's back, n behind the lens's
# visible edge
RING_RIM, RING_CHAMFER, RING_MID, RING_EDGE, RING_TOP = 3, 4, 5, 6, 7
RING_VENT, RING_BACK_OUT, RING_BACK_IN = 9, 11, 12
LENS_T, LENS_GAP, LENS_IN_T = 0.0012, 0.0016, 0.0006     # outer lens, foam spacer gap, inner lens (m)
LENS_GROOVE = 0.003                                     # the lens runs this far under the frame's front rim


class LensSurface:
    def __init__(self, gp=None):
        gp = gp or GP
        self.a, self.A, self.tilt = gp["a"], gp["A"], gp["tilt"]
        x = np.linspace(0, self.a * 0.995, 4000)
        y = self.A * (1 - np.sqrt(1 - (x / self.a) ** 2))
        self.X, self.Y = x, y
        self.S = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]

    def point(self, s, z, off=0.0):
        """Points on the lens front surface (off > 0: in front of it along its normal)."""
        s, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(z, float))
        sg = np.where(s < 0, -1.0, 1.0)
        x = np.interp(np.abs(s), self.S, self.X)
        y = np.interp(np.abs(s), self.S, self.Y)
        dx = np.gradient(self.X)
        dy = np.gradient(self.Y)
        ds = np.hypot(dx, dy)
        tx = np.interp(np.abs(s), self.S, dx / ds)
        ty = np.interp(np.abs(s), self.S, dy / ds)
        T = np.stack([tx, ty * sg, np.zeros_like(tx)], -1)            # plan tangent, d/ds
        tt = math.tan(self.tilt)
        Rl = np.array([0.0, tt, 1.0]) / math.hypot(tt, 1.0)
        N = np.cross(T, Rl)
        N /= np.linalg.norm(N, axis=-1)[..., None]
        P = np.stack([sg * x, y + z * tt, z], -1)
        return P + N * np.asarray(off)[..., None] if np.ndim(off) else P + N * off, N


FILLET = 0.005                      # m, the frame's moulded corners: straight runs between the control points with
                                   # 5 mm fillets (a smooth spline through them read as a soft generic goggle)


def fillet_closed(P, per=12, r=FILLET):
    """Closed polygon through P (k x 2) with each corner rounded (a quadratic Bezier between points r from it on
    either side, r at most 0.4 of the shorter side); per samples per side (one number, or one per side). Returns the
    samples and, for each, the side it lies on and the fraction along it: outlines sampled alike correspond point
    for point."""
    P = np.asarray(P, float)
    k = len(P)
    tin, tout = [], []
    for i in range(k):
        a, b, c = P[(i - 1) % k], P[i], P[(i + 1) % k]
        ri = r[i] if np.ndim(r) else r
        d = min(ri, 0.4 * np.linalg.norm(b - a), 0.4 * np.linalg.norm(c - b))
        tin.append(b + (a - b) / max(np.linalg.norm(a - b), 1e-12) * d)
        tout.append(b + (c - b) / max(np.linalg.norm(c - b), 1e-12) * d)

    def bez(i, t):
        return (1 - t) ** 2 * tin[i] + 2 * (1 - t) * t * P[i] + t * t * tout[i]
    out, seg, frac = [], [], []
    for i in range(k):
        j = (i + 1) % k
        pi = int(per[i]) if np.ndim(per) else int(per)
        n1 = max(min(pi // 4, 3), 1)             # three samples on each half of a corner's fillet
        n2 = pi - 2 * n1
        pts = [bez(i, 0.5 + 0.5 * u / n1) for u in range(n1)]
        pts += [tout[i] + (tin[j] - tout[i]) * u / n2 for u in range(n2)]
        pts += [bez(j, 0.5 * u / n1) for u in range(n1)]
        out += pts
        seg += [i] * pi
        frac += list(np.arange(pi) / pi)
    return np.array(out), np.array(seg), np.array(frac)


def full_loop(half):
    """Half outline (top centre ... bottom centre, s >= 0) -> closed loop: the left half, then the right half
    (mirrored) back up to the top: anticlockwise seen from the front (x left, z up)."""
    h = np.asarray(half, float)
    right = h[1:-1][::-1] * [-1, 1]
    return np.vstack([h, right])


def loop_values(vals):
    v = np.asarray(vals, float)
    return np.r_[v, v[1:-1][::-1]]


def outward2d(C):
    """Unit outward normals of a closed (s, z) loop (anticlockwise seen from the front: s grows to his left)."""
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    n = np.c_[t[:, 1], -t[:, 0]]
    area = 0.5 * np.sum(C[:, 0] * np.roll(C[:, 1], -1) - np.roll(C[:, 0], -1) * C[:, 1])
    return n if area > 0 else -n


def loop_per(gp):
    """Samples per side of the full loop: GP "per" (one per half-loop side, top centre to bottom centre) mirrored,
    else 12 on every side."""
    p = gp.get("per")
    return 12 if p is None else list(p) + list(p)[::-1]


def bspline_half(c, t):
    """A field along half the frame's loop: the uniform cubic B-spline with coefficients c (K of them, evenly
    spaced over t = 0 at the top centre .. 1 at the bottom centre), its coefficients mirrored at both ends so the
    field continues into the other half as its mirror image: C2 all round the loop (round 6)."""
    c = np.asarray(c, float)
    if c.ndim == 0:
        return np.full(np.shape(t), float(c))
    K = len(c)
    ext = np.r_[c[2], c[1], c, c[-2], c[-3]]
    x = np.clip(np.asarray(t, float), 0.0, 1.0) * (K - 1)
    i = np.minimum(np.floor(x).astype(int), K - 2)
    u = x - i
    b0, b3 = (1 - u) ** 3 / 6, u ** 3 / 6
    b1 = (3 * u ** 3 - 6 * u ** 2 + 4) / 6
    b2 = (-3 * u ** 3 + 3 * u ** 2 + 3 * u + 1) / 6
    j = i + 2
    return b0 * ext[j - 1] + b1 * ext[j] + b2 * ext[j + 1] + b3 * ext[j + 2]


def bspline_basis(K, t):
    """The B-spline fields' basis: B (len(t) x K) with bspline_half(c, t) = B @ c."""
    return np.stack([bspline_half(np.eye(K)[k], t) for k in range(K)], -1)


def loop_t(C, nh):
    """Each sample's place along its half of a closed, mirror-symmetric (s, z) loop by arc length: 0 at the top
    centre (sample 0), 1 at the bottom centre (sample nh), back to 0 round the other half."""
    d = np.linalg.norm(np.diff(np.vstack([C, C[:1]]), axis=0), axis=1)
    ell = np.r_[0.0, np.cumsum(d)]
    lh, total = ell[nh], ell[-1]
    ell = ell[:-1]
    return np.where(np.arange(len(C)) <= nh, ell / lh, (total - ell) / (total - lh))


def half_samples(gp, per=None):
    """The bottom centre's sample index on the loop (the left half's sample count)."""
    per = loop_per(gp) if per is None else per
    n = len(gp["out"]) - 1
    return int(np.sum(per[:n])) if np.ndim(per) else int(per) * n


def outline_t(gp=None, per=None):
    """Each loop sample's t (bspline_half) on the outer outline's control polygon with its fillets: the cross-section
    fields run along it."""
    gp = gp or GP
    per = loop_per(gp) if per is None else per
    Cb = fillet_closed(full_loop(gp["out"]), per, loop_values(gp["fillet_out"]))[0]
    return loop_t(Cb, half_samples(gp, per))


def xs_at(gp, key, t):
    """A cross-section field (GP: one value, or the coefficients of bspline_half) at t."""
    return bspline_half(gp[key], t) if np.ndim(gp[key]) else np.full(np.shape(t), float(gp[key]))


def cp_t(gp=None):
    """t of each control point (the middle of its fillet on the outer outline)."""
    gp = gp or GP
    per = loop_per(gp)
    n = len(gp["out"]) - 1
    t = outline_t(gp, per)
    return t[np.r_[0, np.cumsum(per[:n])].astype(int)] if np.ndim(per) else t[np.arange(n + 1) * int(per)]


TOOTH_EASE = 0.0004                 # m, half width of a tooth's step (a moulded step, crisp at 1:1)


def tooth_drop(gp, C):
    """How far the top band's teeth hang below the lens edge at each (s, z) sample (GP "teeth": per tooth the |s| of
    its inner and outer ends and its drop there). Leatt's ISO renders (iso55, pink and white, the same camera): going
    out from the stepped centre the top band's lower edge steps down twice more, each tooth sloping lower outwards,
    and at the last tooth's outer end it steps straight back up (|s| 43.6, 59 and 79.5 mm, back-projected on the
    front face). Round 6: the profile is eased over about 2 TOOTH_EASE at its steps and corners (a Gaussian of
    TOOTH_EASE / 2) instead of jumping between two samples."""
    teeth = gp.get("teeth", [])
    if not teeth:
        return np.zeros(len(C))
    h = 2e-5
    g = np.arange(0.0, 0.14, h)
    prof = np.zeros(len(g))
    for s_in, s_out, d_in, d_out in teeth:
        on = (g >= s_in) & (g < s_out)
        prof = np.where(on, np.maximum(prof, d_in + (d_out - d_in) * (g - s_in) / max(s_out - s_in, 1e-6)), prof)
    sig = 0.5 * TOOTH_EASE / h
    k = np.exp(-0.5 * (np.arange(-int(4 * sig), int(4 * sig) + 1) / sig) ** 2)
    prof = np.convolve(np.pad(prof, len(k) // 2, mode="edge"), k / k.sum(), mode="valid")
    return np.where(C[:, 1] > 0.0, np.interp(np.abs(C[:, 0]), g, prof), 0.0)


def outlines(gp=None, per=None, teeth=True):
    """The three outlines sampled alike (point i of each corresponds): lens edge Co, outer edge Cu, face-side
    opening Ci, (s, z); with each sample's control segment and fraction along it. Each is straight runs between its
    control points joined by fillets; the lens edge and the outer edge then bow off that polygon along its normal
    by a smooth offset (round 6: GP "open_dk", "out_dk", the coefficients of a bspline_half in the polygon's own arc
    length; round 5's one free offset per sample, rounded to 0.1 mm, crumpled the frame at 1:1). The lens edge
    steps down at the top band's teeth (teeth=False: the plain lens edge)."""
    gp = gp or GP
    per = loop_per(gp) if per is None else per
    nh = half_samples(gp, per)
    Co, seg, frac = fillet_closed(full_loop(gp["open"]), per, loop_values(gp["fillet_open"]))
    Cu, _, _ = fillet_closed(full_loop(gp["out"]), per, loop_values(gp["fillet_out"]))
    Ci, _, _ = fillet_closed(full_loop(gp["inner"]), per, loop_values(gp["fillet_inner"]))
    if gp.get("out_dk") is not None:
        Cu = Cu + outward2d(Cu) * bspline_half(gp["out_dk"], loop_t(Cu, nh))[:, None]
    if gp.get("open_dk") is not None:
        Co = Co + outward2d(Co) * bspline_half(gp["open_dk"], loop_t(Co, nh))[:, None]
    if teeth and gp.get("teeth"):
        Co = Co - np.c_[np.zeros(len(Co)), tooth_drop(gp, Co)]
    return Co, Cu, Ci, seg, frac


def frame_rings(gp=None, per=None):
    """The frame as rings (closed loops of 3D points, GOGGLE frame) round its cross-section (see RING_*)."""
    gp = gp or GP
    L = LensSurface(gp)
    Co, Cu, Ci, seg, frac = outlines(gp, per)
    # round 6: every cross-section field is a smooth function of the outer outline's arc length (bspline_half),
    # not a value per control point joined by straight lines (the zigzags between neighbours dented the faces)
    tu = outline_t(gp, per)
    d, rim, ch, bd, top, mt, mw, lip = (xs_at(gp, k, tu) for k in ("depth", "rim", "chamfer", "band", "top", "mid_t",
                                                                   "mid_w", "lip"))
    nu = outward2d(Cu)
    W = np.linalg.norm(Cu - Co, axis=1)
    U = (Cu - Co) / np.maximum(W, 1e-9)[:, None]                   # rim direction: lens edge -> outer edge
    st, r = gp["step"], 0.0004
    bv = xs_at(dict(bevel=gp.get("bevel", 0.0)), "bevel", tu)
    # round 6: at the nose arch's apex the face narrows to 1.0 to 4.6 mm (|s| < 4.5 mm), less than the rim and the
    # chamfer (4.2 mm): there both shrink with it (to 0.85 of the width), so the rings keep their order across the
    # face. Before, they ran past the outer edge and the face folded back: a pinch at the apex in the 1:1 crops
    k = np.minimum(1.0, 0.85 * (W - bv) / np.maximum(rim + ch, 1e-9))
    rim, ch = rim * k, ch * k
    stack = LENS_T + LENS_GAP + LENS_IN_T + 0.0005

    def ring(C, off):
        return L.point(C[:, 0], C[:, 1], off)[0]
    c0 = Co + U * bv[:, None]                                       # the front face's inner edge
    rings = [ring(Co, 0.0003),                                      # a: against the lens front (in the groove)
             ring(c0, lip - r),                                     # b: the inner wall up from the lens (bevel)
             ring(c0 + U * r, lip),                                 # c: front rim, inner edge
             ring(c0 + U * rim[:, None], lip),                      # d: front rim, outer edge
             ring(c0 + U * (rim + ch)[:, None], lip - ch),          # e: 45 deg chamfer
             ring(c0 + U * (rim + ch)[:, None] + (Cu - c0 - U * (rim + ch)[:, None]) * mt[:, None],
                  lip - ch + (ch - bd) * mt + mw),                  # e2: the crease across the front face
             ring(Cu, lip - bd),                                    # f: the band face up to the outline edge
             ring(Cu, lip - top),                                   # f2: the top surface back to the step
             ring(Cu - nu * st, lip - top - 0.0003)]                # g: step in to the vent row
    for f_ in VENT_ROWS:                                            # v1, v2: vent rows on the outer wall
        rings.append(ring(Cu + nu * (gp["taper"] * f_ - st), (lip - top - 0.0003) * (1 - f_) - d * f_))
    rings += [ring(Cu + nu * (gp["taper"] - st), -d),               # k: outer wall back
              ring(Ci, -d),                                         # l: back face inner edge (foam seat)
              ring(Ci, -stack),                                     # m: inner wall at the lens stack's back
              ring(Co, -stack)]                                     # n: behind the lens's visible edge
    return rings, dict(Co=Co, Cu=Cu, Ci=Ci, depth=d, L=L, seg=seg, frac=frac, t=tu)


# top vents: slots in the vent row behind the top band, s ranges on each side (Leatt exploded view and ISO: three
# slots a side either side of the moulded logo)
VENTS_S = [(0.008, 0.024), (0.030, 0.046), (0.052, 0.068)]


def ring_faces(part, rings, mats, uv=None):
    """Quads between consecutive closed rings (the last ring joins the first). mats: per ring gap, a material
    name or a per-segment list."""
    m = len(rings[0])
    ids = [part.add(r, [], "x") + np.arange(m) for r in rings]
    for k in range(len(rings)):
        A_, B_ = ids[k], ids[(k + 1) % len(rings)]
        mk = mats[k]
        for i in range(m):
            j = (i + 1) % m
            part.F.append([A_[i], A_[j], B_[j], B_[i]])
            part.M.append(mk if isinstance(mk, str) else mk[i])
            part.UV.append([(0.0, 0.0)] * 4)
    return ids


def build_frame(gp=None):
    gp = gp or GP
    rings, info = frame_rings(gp)
    Cu = info["Cu"]
    m = len(Cu)
    # vents: segments of the vent row on the top (|s| in a vent range, above the top corners)
    top = Cu[:, 1] > np.max(Cu[:, 1]) - 0.010
    vent = np.array(["goggle_frame"] * m, dtype=object)
    for s0, s1 in VENTS_S:
        sel = top & (np.abs(Cu[:, 0]) >= s0) & (np.abs(Cu[:, 0]) <= s1)
        vent[sel] = "goggle_vent"
    mats = ["goggle_frame"] * len(rings)
    mats[RING_VENT] = list(vent)                 # between v1 and v2
    # the nose bridge behind the lens (back face, inner wall, the plate behind the lens edge): black round the nose
    # ribs (iso55)
    Co = info["Co"]
    for k in (RING_BACK_OUT, RING_BACK_IN, RING_BACK_IN + 1):
        mats[k] = ["goggle_foam" if abs(c[0]) < RIB_BRIDGE_S and c[1] < 0 else "goggle_frame" for c in Co]
    # support rings 0.35 mm either side of every edge: smooth shading then turns only at the edges, and the faces
    # read flat (without them the bezel shaded like a tube)
    R2, M2 = [], []
    K = len(rings)
    for k in range(K):
        A_, B_ = rings[k], rings[(k + 1) % K]
        gap = np.linalg.norm(B_ - A_, axis=1)[:, None]
        f_ = np.clip(0.00035 / np.maximum(gap, 1e-6), 0, 0.3)
        R2 += [A_, A_ + (B_ - A_) * f_, B_ + (A_ - B_) * f_]
        M2 += [mats[k]] * 3
    fr = H.Part("goggle_frame")
    ring_faces(fr, R2, M2)
    return fr, info


# ---------------------------------------------------------------- Leatt's goggle-alone photos as calibrated views
# research/goggle-cameras.json: per photo a camera x = [az, el, roll (deg), d (m), f (px), u0, v0 (px)] in the GOGGLE
# frame (camera at d (sin az cos el, -cos az cos el, sin el) looking at the origin, rolled by roll, principal point
# (W/2 + u0, H/2 + v0), image y down) and the landmarks read off the photo (px): ICON the Leatt icon on the top
# band's front edge (s = 0), NOTCH the top of the nose arch's front edge (s = 0), POST_R / POST_L the heads of the
# tear-off studs (his right / left). Round 4 fitted them jointly with the shape (outline, creases, landmarks).
CAMERAS = os.path.normpath(os.path.join(HERE, "..", "..", "research", "goggle-cameras.json"))


def photo_project(x, P, W, H):
    """Pixels (u, v) of GOGGLE-frame points P in a photo with camera x, and their depth."""
    az, el, roll, d, f, u0, v0 = x
    a, e = math.radians(az), math.radians(el)
    dirn = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
    fwd = -dirn
    right = np.cross(fwd, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    r = math.radians(roll)
    right, up = right * math.cos(r) + up * math.sin(r), up * math.cos(r) - right * math.sin(r)
    q = (np.asarray(P, float) - dirn * d) @ np.vstack([right, up, fwd]).T
    return np.c_[W / 2 + u0 + f * q[:, 0] / q[:, 2], H / 2 + v0 - f * q[:, 1] / q[:, 2]], q[:, 2]


POST_HEAD = 0.0039                  # the tear-off stud's head centre off the lens front (build_posts)


def lip_at(gp, t):
    """How far the frame's front face stands proud of the lens front at t (bspline_half: 0 top centre, 1 bottom
    centre)."""
    return float(xs_at(gp, "lip", t))


def photo_landmarks(gp=None):
    """The model points of the photo landmarks (GOGGLE frame). Round 5: the top and the notch are read off the
    outer outline as built (with its normal offsets), not off the bare control points."""
    gp = gp or GP
    L = LensSurface(gp)
    s_post, z_post = post_sz(gp)
    Cu = outlines(gp)[1]
    c = Cu[np.abs(Cu[:, 0]) < 0.004]
    z_top = np.interp(0.0, *zip(*sorted((p[0], p[1]) for p in c[c[:, 1] > 0])))
    z_notch = np.interp(0.0, *zip(*sorted((p[0], p[1]) for p in c[c[:, 1] < 0])))
    band0, band1 = (float(xs_at(gp, "band", t)) for t in (0.0, 1.0))
    return dict(ICON=L.point(0.0, z_top - 0.002, lip_at(gp, 0.0) - band0)[0],
                NOTCH=L.point(0.0, z_notch, lip_at(gp, 1.0) - band1)[0],
                POST_R=L.point(-s_post, z_post, POST_HEAD)[0], POST_L=L.point(s_post, z_post, POST_HEAD)[0])


FIN_S = (0.090, 0.099)             # the fins at the top band's outer ends: root and tip along the top (|s|)
FIN_H, FIN_T = 0.005, 0.0035       # rise above the top band at the tip, thickness (Leatt ISO, right end: 8 x 5 mm)


def build_fins(gp=None):
    """The small upward fins at the top band's outer ends (Leatt ISO): a wedge rising from the top surface towards
    the end, its tip leaning out; every face separate (crisp, flat shaded)."""
    gp = gp or GP
    L = LensSurface(gp)
    Co, Cu, Ci, seg, frac = outlines(gp)
    left = (Cu[:, 0] > 0.04) & (Cu[:, 1] > 0.0)
    order = np.argsort(Cu[left, 0])
    s_, z_ = Cu[left][order, 0], Cu[left][order, 1]
    tf = np.interp(np.mean(FIN_S), s_, outline_t(gp)[left][order])
    bd, lip = float(xs_at(gp, "band", tf)), lip_at(gp, tf)
    w0, w1 = lip - bd - 0.0008, lip - bd - 0.0008 - FIN_T          # on the top surface, just behind its edge
    fins = H.Part("goggle_fins")
    for sg in (1, -1):
        s0, s1 = FIN_S
        z0, z1 = np.interp(s0, s_, z_), np.interp(s1, s_, z_)

        def P(s, z, w):
            return L.point(sg * s, z, w)[0]
        B0, B1 = P(s0, z0 - 0.0005, w0), P(s0, z0 - 0.0005, w1)
        B2, B3 = P(s1, z1 - 0.0005, w0), P(s1, z1 - 0.0005, w1)
        T0, T1 = P(s1 + 0.0015, z1 + FIN_H, w0 - 0.0008), P(s1 + 0.0015, z1 + FIN_H, w1 + 0.0008)
        faces = [[B0, B2, T0], [B1, T1, B3], [B0, T0, T1, B1], [B2, B3, T1, T0]]
        for fc in faces:
            fc = fc if sg > 0 else fc[::-1]
            fins.add(np.array(fc), [list(range(len(fc)))], "goggle_frame", [[(0.0, 0.0)] * len(fc)])
    return fins


def untangle(P, reach=40):
    """A closed (s, z) loop with the small loops cut out that an offset makes at sharp inward corners: where an edge
    crosses one up to reach edges further on, the vertices between are replaced by the crossing point."""
    P = [np.asarray(p, float) for p in P]
    i = 0
    while i < len(P):
        n = len(P)
        a1, a2 = P[i], P[(i + 1) % n]
        cut = None
        for k in range(min(reach, n - 3), 1, -1):                  # the farthest crossing first (the whole loop)
            b1, b2 = P[(i + k) % n], P[(i + k + 1) % n]
            d = (a2[0] - a1[0]) * (b2[1] - b1[1]) - (a2[1] - a1[1]) * (b2[0] - b1[0])
            if abs(d) < 1e-18:
                continue
            t = ((b1[0] - a1[0]) * (b2[1] - b1[1]) - (b1[1] - a1[1]) * (b2[0] - b1[0])) / d
            u = ((b1[0] - a1[0]) * (a2[1] - a1[1]) - (b1[1] - a1[1]) * (a2[0] - a1[0])) / d
            if 0.0 < t < 1.0 and 0.0 < u < 1.0:
                cut = (k, a1 + t * (a2 - a1))
                break
        if cut is None:
            i += 1
            continue
        k, X = cut
        idx = [(i + j) % n for j in range(1, k + 1)]               # the loop's vertices, replaced by X
        keep = [p for j, p in enumerate(P) if j not in set(idx)]
        at = i + 1 - sum(1 for j in idx if j <= i)
        P = keep[:at] + [X] + keep[at:]
        i = max(at - 1, 0)
    return np.array(P)


def lens_region(gp, grow):
    """Lens outline in (s, z): the opening grown by grow (under the frame's lip). Round 5: the fitted lens window
    has sharp inward corners (the nose arch's steps, the top band's step) where the grown outline crossed itself and
    left see-through wedges in the lens; those loops are cut out."""
    Co = outlines(gp, teeth=False)[0]
    return untangle(Co + outward2d(Co) * grow)


def sheet(L, poly, off, h=0.004):
    """Triangulated region of the lens surface inside poly ((s, z) loop) at offset off: vertices, triangles
    (anticlockwise seen from the front), and the boundary vertex count (the first len(poly))."""
    from scipy.spatial import Delaunay
    lo, hi = poly.min(0), poly.max(0)
    gs, gz = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h * 0.866))
    gs = gs + (np.arange(gs.shape[0])[:, None] % 2) * h / 2
    pts = np.c_[gs.ravel(), gz.ravel()]
    o = H.Profile.__new__(H.Profile)
    o.outline = poly
    keep = H.Profile.inside(o, pts) & (cKDTree(poly).query(pts)[0] > 0.4 * h)
    P2 = np.vstack([poly, pts[keep]])
    T = Delaunay(P2).simplices
    T = T[H.Profile.inside(o, P2[T].mean(1))]
    a, b, c = P2[T[:, 0]], P2[T[:, 1]], P2[T[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    T[cr < 0] = T[cr < 0][:, ::-1]
    # (s, z) anticlockwise with s to his left = clockwise seen from the front (x left): flip to face forward
    T = T[:, ::-1]
    V = L.point(P2[:, 0], P2[:, 1], off(P2) if callable(off) else off)[0]     # off: a depth, or one per (s, z)
    return V, T, len(poly)


def closed_sheet(part, L, poly, off_front, off_back, mat_front, mat_back, mat_edge):
    """A lens sheet as a closed solid: front, back (the same triangulation further back) and the edge strip."""
    Vf, T, nb = sheet(L, poly, off_front)
    Vb = sheet(L, poly, off_back)[0]
    of = part.add(Vf, [list(t) for t in T], mat_front, [[(0.0, 0.0)] * 3 for _ in T])
    ob = part.add(Vb, [list(t[::-1]) for t in T], mat_back, [[(0.0, 0.0)] * 3 for _ in T])
    for i in range(nb):
        j = (i + 1) % nb
        part.F.append([of + j, of + i, ob + i, ob + j]); part.M.append(mat_edge); part.UV.append([(0.0, 0.0)] * 4)
    return of, ob


def build_lens(gp=None):
    """The double lens: the outer (mirror coated on its front) in the frame's groove, the thin inner lens behind it
    on the foam spacer."""
    gp = gp or GP
    L = LensSurface(gp)
    lens = H.Part("goggle_lens")
    poly = lens_region(gp, LENS_GROOVE)
    closed_sheet(lens, L, poly, 0.0, -LENS_T, "goggle_lens_mirror", "goggle_lens_clear", "goggle_lens_clear")
    poly_in = lens_region(gp, LENS_GROOVE - 0.0015)
    closed_sheet(lens, L, poly_in, -(LENS_T + LENS_GAP), -(LENS_T + LENS_GAP + LENS_IN_T),
                 "goggle_lens_clear", "goggle_lens_clear", "goggle_lens_clear")
    return lens


POST_S, POST_Z = 0.0867, -0.0012   # tear-off posts near the lens's ends, at (+-s, z) on the lens: the stud heads
                                   # are landmarks in every goggle-alone photo (round 4: 87.5, -1.5 mm, fitted with
                                   # the shape; round 5: refitted on round 5's lens with its cameras fixed, iso55,
                                   # phy, phr: studs 1.8 mm off at most before, 1.0 after)


def post_sz(gp=None):
    """(s, z) of the tear-off post on his left (the right one mirrored); GP may override it with "post"."""
    p = (gp or GP).get("post")
    return (p[0], p[1]) if p is not None else (POST_S, POST_Z)


def build_posts(gp=None):
    """Bare tear-off posts (Damien runs no tear-offs): a square boss on the lens and a round stud with a head."""
    gp = gp or GP
    L = LensSurface(gp)
    posts = H.Part("goggle_posts")
    sp, zp = post_sz(gp)
    for sg in (1, -1):
        s0 = sg * sp
        P0, N0 = L.point(s0, zp, 0.0)
        P1, _ = L.point(s0 + 0.001, zp, 0.0)
        t = (P1 - P0) / np.linalg.norm(P1 - P0)
        up = np.cross(N0, t)
        up /= np.linalg.norm(up)
        # square boss 4.5 x 4.5 x 1.5 mm
        box = []
        for h, (a, b) in ((0, (-1, -1)), (0, (1, -1)), (0, (1, 1)), (0, (-1, 1)),
                          (1, (-1, -1)), (1, (1, -1)), (1, (1, 1)), (1, (-1, 1))):
            box.append(P0 + t * a * 0.00225 + up * b * 0.00225 + N0 * (0.0015 * h - 0.0002))
        quads = [[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        posts.add(np.array(box), quads, "goggle_post", [[(0.0, 0.0)] * 4] * 6)
        # stud 2.4 mm across, 2.5 mm long, head 3.4 mm
        k = 12
        ang = np.linspace(0, 2 * np.pi, k, endpoint=False)
        rings = []
        for rr, hh in ((0.0012, 0.0013), (0.0012, 0.0033), (0.0017, 0.0036), (0.0017, 0.0042), (0.0008, 0.0045)):
            rings.append(P0 + N0 * hh + rr * (np.cos(ang)[:, None] * t + np.sin(ang)[:, None] * up))
        ids = [posts.add(r, [], "goggle_post") + np.arange(k) for r in rings]
        for a_, b_ in zip(ids[:-1], ids[1:]):
            for i in range(k):
                j = (i + 1) % k
                posts.F.append([a_[i], a_[j], b_[j], b_[i]]); posts.M.append("goggle_post")
                posts.UV.append([(0.0, 0.0)] * 4)
        tip = posts.add((P0 + N0 * 0.0046)[None], [], "goggle_post")
        for i in range(k):
            j = (i + 1) % k
            posts.F.append([ids[-1][i], ids[-1][j], tip]); posts.M.append("goggle_post"); posts.UV.append([(0.0, 0.0)] * 3)
    return posts


OR_LEN, OR_T, OR_BACK_H = 0.030, 0.008, 0.059     # outrigger: length behind the frame, thickness, height at the
                                                 # strap end (Leatt ISO: 1.3 x the 45 mm strap beside it)


OR_TURN = 0.4                      # the outrigger turns out from the side face's backward line by atan(0.4) = 22 deg
                                   # towards the strap (Leatt ISO)


def outrigger_frames(gp=None):
    """Each outrigger's corners (GOGGLE frame): it starts behind the frame's tall side face (its outer face in the
    side face's plane: the pink side face shows ahead of it, Leatt ISO) and runs back to the strap, turned out by
    OR_TURN. Returns {side: (8 x 3 corners, strap end point, outward normal)}."""
    gp = gp or GP
    L = LensSurface(gp)
    out = {}
    s_end = max(p[0] for p in gp["out"])
    o_len, o_back_h, o_turn = (gp.get(k, v) for k, v in (("or_len", OR_LEN), ("or_back_h", OR_BACK_H),
                                                          ("or_turn", OR_TURN)))
    zt = gp["out"][ci("top_corner")][1] - gp.get("or_top_in", 0.003)
    zb = gp["out"][ci("bot_corner")][1] + gp.get("or_bot_in", 0.003)
    zc = 0.5 * (zt + zb)
    zbk = zc + gp.get("or_back_dz", 0.0)                           # the back end's centre height
    d_end = float(xs_at(gp, "depth", cp_t(gp)[ci("side_end")]))
    for sg in (1, -1):
        P0, N0 = L.point(sg * (s_end + gp["taper"] - gp["step"]), zc, -d_end + gp.get("or_front", 0.002))
        Pa = L.point(sg * (s_end - 0.001), zc, 0.0)[0]
        Pb = L.point(sg * s_end, zc, 0.0)[0]
        T = Pb - Pa                                                # round the end (outwards, back)
        T[2] = 0.0
        T /= np.linalg.norm(T)
        back = -np.array([N0[0], N0[1], 0.0])
        back /= np.linalg.norm(back)
        t = back + o_turn * T
        t /= np.linalg.norm(t)
        n = np.cross([0.0, 0.0, 1.0], t)
        n = n if n @ T > 0 else -n                                 # outwards
        C = np.array([P0 + [0, 0, zt - zc], P0 + [0, 0, zb - zc],
                      P0 + t * o_len + [0, 0, zbk - zc - o_back_h / 2], P0 + t * o_len + [0, 0, zbk - zc + o_back_h / 2]])
        box = np.vstack([C, C - n * OR_T])
        out[sg] = (box, P0 + t * (o_len - 0.004) + [0, 0, zbk - zc] - n * OR_T / 2, n)
    return out


OR_GAP = 0.0015            # m, a mounted outrigger's inner face off the shell (it rests on it, strap tension)
OR_BEND = math.tan(math.radians(60))   # steepest outward bend of a mounted outrigger (lift per length)
OR_ANCHOR = 0.010          # m, the strap's end sits this far inside the outrigger's back end (its buckle slot)
OR_NU, OR_NV = 13, 7       # grid of each outrigger face (along x up)


def shell_mount(prof):
    """For the goggle on the helmet: the half width an outrigger point (GOGGLE frame) must clear, i.e. the shell's
    outer surface where the point lies behind the eyeport's edge in the side view (helmet.py's profile), else 0
    (in the eyeport opening nothing is in the way)."""
    def need(Pg):
        Ph = g2h(Pg)
        ins = prof.inside(Ph[:, 1:])
        return np.where(ins, H.shell_hw(prof, Ph[:, 1], Ph[:, 2]), 0.0)
    return need


def outrigger_grids(gp=None, mount=None, nu=OR_NU, nv=OR_NV):
    """Each outrigger's outer and inner faces as (nu x nv x 3) grids (i along it, front to back; j up) and the strap's
    anchor (GOGGLE frame). Free (mount None, as in Leatt's ISO): the flat plate of outrigger_frames. On the helmet
    (mount = shell_mount(prof)): the strap pulls the outriggers onto the shell, as on every goggle worn over a helmet
    (his 07 and 09, Leatt's MY27 kit views: the strap leaves the outrigger and lies on the shell). The free plate
    starts inside the eyeport opening and its back 35 % would sink 22 to 41 mm into the shell, so each row of the
    plate is lifted outwards (x only, the front edge fixed on the frame) to clear the shell by OR_GAP behind the
    eyeport's edge, bending out at most OR_BEND before it reaches the edge and never back in towards its end."""
    out = {}
    for sg, (box, end, n) in outrigger_frames(gp).items():
        u = np.linspace(0.0, 1.0, nu)[:, None, None]
        v = np.linspace(0.0, 1.0, nv)[None, :, None]

        def bil(c):                       # corners: front-top, front-bottom, back-bottom, back-top
            return (1 - u) * ((1 - v) * c[1] + v * c[0]) + u * ((1 - v) * c[2] + v * c[3])
        Go, Gi = bil(box[:4]), bil(box[4:])
        if mount is not None:
            need = mount(Gi.reshape(-1, 3)).reshape(nu, nv)
            req = np.maximum(0.0, np.where(need > 0, need + OR_GAP - np.abs(Gi[..., 0]), 0.0))
            ds = np.linalg.norm(np.diff(Gi[:, nv // 2], axis=0), axis=1)
            s = np.r_[0.0, np.cumsum(ds)]                          # length along the plate
            lift = np.zeros_like(req)
            for i in range(nu):                                    # rise early enough to reach each later need
                ahead = req[i:] - OR_BEND * (s[i:, None] - s[i])
                lift[i] = np.maximum(0.0, ahead.max(0))
            lift = np.minimum(lift, OR_BEND * s[:, None])          # fixed on the frame at its front edge
            lift = np.maximum.accumulate(lift, axis=0)             # bends outwards only, towards the back
            Go = Go.copy()
            Gi = Gi.copy()
            Go[..., 0] += sg * lift
            Gi[..., 0] += sg * lift
        L = np.linalg.norm(Gi[-1, nv // 2] - Gi[0, nv // 2])
        i_a = np.clip(1.0 - OR_ANCHOR / L, 0, 1) * (nu - 1)
        i0 = int(i_a)
        f = i_a - i0
        mid = 0.5 * (Go + Gi)[:, nv // 2]
        anchor = mid[i0] * (1 - f) + mid[min(i0 + 1, nu - 1)] * f
        out[sg] = (Go, Gi, anchor)
    return out


def build_outriggers(gp=None, mount=None):
    """Black outriggers, white vertical LEATT on the outer face (letter tops towards the strap; Leatt's ISO view
    and the Pinata kit photo, right side), one image half per side. mount: see outrigger_grids."""
    o = H.Part("goggle_outriggers")
    for sg, (Go, Gi, anchor) in outrigger_grids(gp, mount).items():
        nu, nv = Go.shape[:2]
        V = np.vstack([Go.reshape(-1, 3), Gi.reshape(-1, 3)])
        O = lambda i, j: i * nv + j                               # noqa: E731
        I = lambda i, j: nu * nv + i * nv + j                     # noqa: E731
        quads, mats, uvs = [], [], []
        h0, h1 = (0.0, 0.5) if sg > 0 else (0.5, 1.0)
        # outer face: texture u = height (h0 bottom .. h1 top) in its image half, v = along (0 front .. 1 back)
        tex = lambda i, j: (h0 + (h1 - h0) * j / (nv - 1), i / (nu - 1))   # noqa: E731
        for i in range(nu - 1):
            for j in range(nv - 1):
                quads.append([O(i, j + 1), O(i, j), O(i + 1, j), O(i + 1, j + 1)])
                uvs.append([tex(i, j + 1), tex(i, j), tex(i + 1, j), tex(i + 1, j + 1)])
                quads.append([I(i + 1, j + 1), I(i + 1, j), I(i, j), I(i, j + 1)])
                uvs.append([(0.5, 0.5)] * 4)
        for i in range(nu - 1):                                   # top and bottom edges
            quads.append([I(i, nv - 1), O(i, nv - 1), O(i + 1, nv - 1), I(i + 1, nv - 1)])
            quads.append([O(i, 0), I(i, 0), I(i + 1, 0), O(i + 1, 0)])
            uvs += [[(0.5, 0.5)] * 4] * 2
        for j in range(nv - 1):                                   # front and back ends
            quads.append([I(0, j + 1), I(0, j), O(0, j), O(0, j + 1)])
            quads.append([O(nu - 1, j + 1), O(nu - 1, j), I(nu - 1, j), I(nu - 1, j + 1)])
            uvs += [[(0.5, 0.5)] * 4] * 2
        if sg < 0:
            quads = [q[::-1] for q in quads]
            uvs = [w[::-1] for w in uvs]
        o.add(V, quads, "goggle_outrigger", uvs)
    return o


# Leatt's slanted LEATT wordmark, the official file (us.leatt.com header logo, Logo_2_NoBG.png: see the gear
# README): the logo on the Velocity 5.5's strap, outriggers and lower frame (Leatt ISO, MY27 kit views, his 07)
WORDMARK = os.path.join(HERE, "..", "..", "reference", "leatt-gear", "leatt-wordmark-slanted_official_leatt-us_1200x300.png")


def wordmark_mask():
    """The wordmark as a boolean mask (rows top down) cropped to its letters, the registered mark dropped."""
    from PIL import Image
    from scipy import ndimage
    a = np.array(Image.open(WORDMARK).convert("RGBA"))[..., 3] > 128
    lab, n = ndimage.label(a)
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.nonzero(sizes > 0.05 * sizes.max())[0])
    ys, xs = np.nonzero(keep)
    return keep[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def stamp_wordmark(im, x0, y0, w, h, colour, mirror=False):
    """Paint the wordmark into PIL image im, box (x0, y0, w, h) in pixels, upright (mirror: flipped left-right)."""
    from PIL import Image
    m = Image.fromarray((wordmark_mask() * 255).astype(np.uint8)).resize((int(round(w)), int(round(h))), Image.LANCZOS)
    if mirror:
        m = m.transpose(Image.FLIP_LEFT_RIGHT)
    im.paste(Image.new("RGB", m.size, colour), (int(round(x0)), int(round(y0))), m)


def wordmark_aspect():
    m = wordmark_mask()
    return m.shape[1] / m.shape[0]


def outrigger_texture(path, w=256, h=512):
    """Image halves (left half: his left outrigger), each u across the outrigger's height (0 bottom .. 1 top within
    the half), v along it (0 at the frame, 1 at the strap). Letter tops towards the strap on both sides (Leatt ISO
    and the Pinata kit photo, right side): on the right it reads bottom to top, on the left top to bottom (the left
    face's (u, v) is mirrored seen from outside, so its half is drawn mirrored and reads right there). The text runs
    0.8 of the outrigger's height at its middle; its letter height keeps the wordmark's own aspect (u spans the
    height, v the OR_LEN length)."""
    from PIL import Image
    im = Image.new("RGB", (2 * w, h), (14, 14, 16))
    h_mid = 0.5 * ((GP["out"][ci("top_corner")][1] - GP["out"][ci("bot_corner")][1] - GP.get("or_top_in", 0.003)
                    - GP.get("or_bot_in", 0.003)) + GP.get("or_back_h", OR_BACK_H))
    L_ = 0.80 * w                                             # text length in px (along u)
    ch = 0.80 * h_mid / wordmark_aspect() / GP.get("or_len", OR_LEN) * h   # letter height in px (along v), true aspect
    stamp_wordmark(im, w + (w - L_) / 2, h - (0.5 * h + ch / 2), L_, ch, (236, 236, 238))
    right = im.crop((w, 0, 2 * w, h))
    im.paste(right.transpose(Image.FLIP_LEFT_RIGHT), (0, 0))         # the left half: the right one mirrored
    im.save(path)


LOGO_S, LOGO_H = 0.053, 0.004      # the lower band's LEATT (his left cheek, MY27 front-iso and left side views):
                                   # centre along the outline (s), letter height (m); its length from the aspect


def build_frame_logo(gp=None, cell=0.0002):
    """The white LEATT on the lower band at his left cheek, as cells of the wordmark mask laid 0.15 mm off the
    band face (between the chamfer and the outline edge), reading left to right seen from the front."""
    gp = gp or GP
    rings, info = frame_rings(gp)
    Cu = info["Cu"]
    sel = np.nonzero((Cu[:, 0] > 0.035) & (Cu[:, 0] < 0.075) & (Cu[:, 1] < -0.03))[0]
    order = sel[np.argsort(Cu[sel, 0])]
    s_ = Cu[order, 0]
    E, E2, F = rings[RING_CHAMFER][order], rings[RING_MID][order], rings[RING_EDGE][order]
    a_, b_ = np.linalg.norm(E2 - E, axis=1), np.linalg.norm(F - E2, axis=1)
    tm_ = a_ / np.maximum(a_ + b_, 1e-9)                            # where the face's crease lies, 0..1

    def P(s, t):
        e, e2, f = (np.stack([np.interp(s, s_, R[:, k]) for k in range(3)], -1) for R in (E, E2, F))
        tm = np.interp(s, s_, tm_)[..., None]
        t = t[..., None]
        # on the two facets either side of the crease, not on the chord across them
        return np.where(t < tm, e + (e2 - e) * t / np.maximum(tm, 1e-6),
                        e2 + (f - e2) * (t - tm) / np.maximum(1 - tm, 1e-6))
    length = LOGO_H * wordmark_aspect()
    band_w = np.linalg.norm(F - E, axis=1).mean()
    nl, nh = int(length / cell), int(LOGO_H / cell)
    from PIL import Image
    m = np.array(Image.fromarray((wordmark_mask() * 255).astype(np.uint8)).resize((nl, nh), Image.LANCZOS)) > 127
    gi, gj = np.meshgrid(np.arange(nl + 1), np.arange(nh + 1), indexing="ij")
    sv = LOGO_S + (gi / nl - 0.5) * length                          # reads + s (his left = the viewer's right)
    tv = 0.5 + (gj / nh - 0.5) * LOGO_H / band_w                    # letter tops (j = 0) towards the lens
    G_ = P(sv.ravel(), tv.ravel()).reshape(nl + 1, nh + 1, 3)
    ds = np.gradient(G_, axis=0)
    dt = np.gradient(G_, axis=1)
    N = np.cross(ds, dt)
    N /= np.linalg.norm(N, axis=-1)[..., None]
    N *= np.where(N[..., 1:2] < 0, 1.0, -1.0)                       # facing forward (-y)
    G_ = G_ + N * 0.00015
    used = np.zeros((nl + 1, nh + 1), bool)
    cells = np.argwhere(m.T)                                        # (i along, j down)
    for i, j in cells:
        used[i:i + 2, j:j + 2] = True
    vid = -np.ones((nl + 1, nh + 1), int)
    vid[used] = np.arange(used.sum())
    quads = [[vid[i, j], vid[i, j + 1], vid[i + 1, j + 1], vid[i + 1, j]] for i, j in cells]
    lg = H.Part("goggle_logo")
    lg.add(G_[used], quads, "goggle_logo", [[(0.0, 0.0)] * 4] * len(quads))
    return lg


NOSE_GUARD_DROP = 0.007            # the flexible nose guard hangs this far under the notch, inside the tabs (ISO)


def build_nose_guard(gp=None):
    """The black flexible nose guard under the nose arch (Leatt exploded view)."""
    gp = gp or GP
    L = LensSurface(gp)
    _, Cu, _, seg, frac = outlines(gp)
    n = len(gp["out"])
    t = ci("notch_side")
    # the arch: from half-way up the left leg's inner side (notch side to arch step), over the apex (the bottom
    # centre) to the mirror point on the right
    nl = 2 * (n - 1)                                   # control points round the full loop
    idx = np.nonzero(((seg == t) & (frac >= 0.5)) | ((seg > t) & (seg < nl - t - 1)) |
                     ((seg == nl - t - 1) & (frac <= 0.5)))[0]
    C = Cu[idx]
    # it hangs deepest under the arch's apex and not at all at its sides (inside the beak's legs)
    zs, za = C[:, 1].min(), C[:, 1].max()
    k = np.clip((C[:, 1] - zs) / max(za - zs, 1e-6), 0.0, 1.0)
    rings = []
    for drop, off in ((0.0, -0.002), (NOSE_GUARD_DROP * 0.6, -0.006), (NOSE_GUARD_DROP, -0.012)):
        P = L.point(C[:, 0], C[:, 1] - drop * k, off)[0]
        rings.append(P)
    g = H.Part("goggle_noseguard")
    m = len(C)
    ids = [g.add(r, [], "goggle_noseguard") + np.arange(m) for r in rings]
    for a_, b_ in zip(ids[:-1], ids[1:]):
        for i in range(m - 1):
            g.F.append([a_[i], a_[i + 1], b_[i + 1], b_[i]]); g.M.append("goggle_noseguard"); g.UV.append([(0.0, 0.0)] * 4)
    return g


# Nose-bridge ribs (round 5): a comb moulded on the frame's nose bridge behind the lens, seen through the lens in
# Leatt's ISO renders (iso55, pink and white colourways) and bare in the exploded view: a centre finger, a finger each
# side and an outer lobe each side holding a closed slot, open slots between, rounded tips; round it the bridge is
# black (iso55: dark between and above the fingers in both colourways). (s, z) are the white ISO's pixels
# back-projected with the round 5 iso55 camera onto the comb's front face (ribs_bp.py), the pattern centred on s = 0
# (a 3.6 mm shift: the centre finger's top read at s -3.6 mm). Its depth is not pinned: the exploded view's closed
# slot agrees in height only 8.5 mm back and never in s (ribs_tri.py), and every slot reads sheared (bottom 7 mm
# further to his left than its top), the mark of a bridge that slopes back from the lens. So the comb is a flat
# front face 0.3 mm in front of the round 4 bridge's nearest point (which keeps his nose clear), its back moulded
# into the bridge; vertical slots.
RIB_PROUD, RIB_SINK = 0.0003, 0.0002           # front: this far in front of the bridge's nearest point; back: into it
RIB_FINGERS = [(0.0, 0.0038, -0.0164), (0.01025, 0.00405, -0.0179)]   # (|s| centre, half width, tip z), mirrored
RIB_LOBE = (0.0167, 0.0290, -0.0187, -0.0215)  # |s| inner and outer edges, top z at the inner and outer edge
RIB_SLOT_Z = (-0.0252, -0.0249)                # open slots' bottoms: inner pair, outer pair
RIB_CLOSED = (0.0217, 0.00125, -0.0291, -0.0225)   # closed slot in each lobe: |s| centre, half width, z bottom, top
RIB_BRIDGE_S = 0.030                           # the bridge behind the lens is black within this |s| (iso55)
RIB_CORNER = 0.0018                            # tip corner radius


def rib_top(s):
    """The comb's top edge z(s) (nan outside it), a function of |s|: tips with rounded corners, slot notches."""
    a = np.abs(np.asarray(s, float))
    z = np.full(a.shape, np.nan)

    def tip(c, hw, zt):
        d = np.abs(a - c) - (hw - RIB_CORNER)
        return np.where(d <= 0, zt, zt - RIB_CORNER + np.sqrt(np.clip(RIB_CORNER ** 2 - d ** 2, 0, None)))
    for c, hw, zt in RIB_FINGERS:
        m = np.abs(a - c) <= hw
        z[m] = tip(c, hw, zt)[m]
    i0, i1, zi, zo = RIB_LOBE
    m = (a >= i0) & (a <= i1)
    zl = zi + (zo - zi) * (a - i0) / (i1 - i0)
    zl = np.where(a - i0 < RIB_CORNER, zl - RIB_CORNER + np.sqrt(np.clip(RIB_CORNER ** 2 - (RIB_CORNER - (a - i0)) ** 2, 0, None)), zl)
    z[m] = zl[m]
    gaps = [(RIB_FINGERS[0][0] + RIB_FINGERS[0][1], RIB_FINGERS[1][0] - RIB_FINGERS[1][1], RIB_SLOT_Z[0]),
            (RIB_FINGERS[1][0] + RIB_FINGERS[1][1], i0, RIB_SLOT_Z[1])]
    for g0, g1, zb in gaps:
        z[(a > g0) & (a < g1)] = zb
    return z


def rib_base(gp):
    """The comb's bottom edge z(s): 4 mm under the lens opening, but not below the nose arch's top (out loop)."""
    Co, Cu = outlines(gp, teeth=False)[:2]
    lo = Co[(Co[:, 1] < 0) & (np.abs(Co[:, 0]) < 0.04)]
    lo = lo[np.argsort(lo[:, 0])]
    arch = Cu[(Cu[:, 1] < 0) & (Cu[:, 1] > -0.045) & (np.abs(Cu[:, 0]) < 0.015)]
    arch = arch[np.argsort(arch[:, 0])]

    def f(s):
        s = np.asarray(s, float)
        za = np.interp(s, arch[:, 0], arch[:, 1], left=-1.0, right=-1.0)
        return np.maximum(np.interp(s, lo[:, 0], lo[:, 1]) - 0.004, za)
    return f


def bridge_depth(gp):
    """Depth behind the lens front (m, > 0) of the first frame surface a ray from the front meets at (s, z) near the
    nose (Moller-Trumbore against the frame's triangles there); the lens stack's back where it meets none."""
    L = LensSurface(gp)
    fr = build_frame(gp)[0]
    V = np.asarray(fr.V)
    T = np.array([[f[0], f[i], f[i + 1]] for f in fr.F for i in range(1, len(f) - 1)])
    c = V[T].mean(1)
    T = T[(np.abs(c[:, 0]) < 0.05) & (c[:, 2] < -0.005) & (c[:, 2] > -0.07)]
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1, e2 = B - A, C - A
    dflt = LENS_T + LENS_GAP + LENS_IN_T + 0.0005

    def f(s, z):
        s, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(z, float))
        O, N = L.point(s.ravel(), z.ravel(), 0.0)
        out = np.full(len(O), dflt)
        for k in range(0, len(O), 200):
            o, d = O[k:k + 200, None], -N[k:k + 200, None]
            p = np.cross(d, e2[None])
            det = (e1[None] * p).sum(-1)
            det = np.where(np.abs(det) < 1e-14, 1e-14, det)
            tv = o - A[None]
            u = (tv * p).sum(-1) / det
            q = np.cross(tv, e1[None])
            v = (d * q).sum(-1) / det
            t = (e2[None] * q).sum(-1) / det
            hit = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0.0005)
            t = np.where(hit, t, np.inf).min(1)
            out[k:k + 200] = np.where(np.isfinite(t), t, dflt)
        return out.reshape(s.shape)
    return f


def rib_clear(L, s, skin_G, depth):
    """Highest z at each s where the comb (its back at depth(s, z) behind the lens front) clears his skin by 0.5 mm:
    the first skin along the lens normal must lie deeper. -inf where no z clears (his nose fills the column)."""
    tree = cKDTree(skin_G)
    zs = np.arange(-0.045, -0.015, 0.0005)
    out = np.full(len(s), np.inf)
    for i, si in enumerate(s):
        P, N = L.point(np.full(len(zs), si), zs, 0.0)
        for j in range(len(zs)):
            idx = tree.query_ball_point(P[j], 0.03)
            if not idx:
                continue
            q = skin_G[idx] - P[j]
            along = -(q @ N[j])
            lat = np.linalg.norm(q + np.outer(along, N[j]), axis=1)
            m = lat < 0.003
            if m.any() and along[m].min() < depth(si, zs[j]) + 0.0005:
                out[i] = zs[j] - 0.0005 if j else -np.inf
                break
    return out


def build_nose_ribs(gp=None, skin_G=None):
    """The nose-bridge comb (frame plastic) and its closed slots. On him (skin_G, GOGGLE frame) the flexible ribs
    give way to his nose: each column of the comb stops 0.5 mm short of his skin, and columns his nose fills are
    left out (the comb bends flat there; behind the mirror lens nothing of it shows)."""
    gp = gp or GP
    L = LensSurface(gp)
    base = rib_base(gp)
    bd = bridge_depth(gp)

    gs, gz = np.meshgrid(np.linspace(-RIB_LOBE[1], RIB_LOBE[1], 25), np.linspace(-0.030, RIB_FINGERS[0][2], 8))
    off_f = -(float(bd(gs, gz).min()) - RIB_PROUD)

    def front(P2):
        return np.full(len(P2), off_f)

    def back(P2):
        return -(bd(P2[:, 0], P2[:, 1]) + RIB_SINK)
    s = np.round(np.arange(-RIB_LOBE[1], RIB_LOBE[1] + 1e-9, 0.00025), 6)
    top = rib_top(s)
    if skin_G is not None:
        top = np.minimum(top, rib_clear(L, s, skin_G, lambda s_, z_: float(bd(s_, z_)) + RIB_SINK))
    ok = np.isfinite(top) & (top > base(s) + 0.0008)
    g = H.Part("goggle_noseribs")
    runs = np.split(np.arange(len(s)), np.nonzero(np.diff(ok.astype(int)))[0] + 1)
    for r in runs:
        if not ok[r[0]] or len(r) < 3:
            continue
        poly = np.vstack([np.c_[s[r], top[r]], np.c_[s[r][::-1], base(s[r][::-1])]])
        # the edge strip dark: the slots read as gaps onto the black bridge, as in iso55
        closed_sheet(g, L, poly, front, back, "goggle_frame", "goggle_frame", "goggle_foam")
    # the closed slots: dark through-cuts drawn on both faces of each lobe that is still there
    c, hw, zb, zt = RIB_CLOSED
    for sg in (-1.0, 1.0):
        ss = sg * np.array([c - hw, c + hw, c + hw, c - hw])
        zz = np.array([zb, zb, zt, zt])
        if not np.all(np.interp(ss, s, np.where(ok, top, -1.0)) > zt + 0.001):
            continue
        dd = bd(ss, zz)
        for off, rev in ((np.full(4, off_f + 0.0001), sg < 0), (-(dd + RIB_SINK + 0.0001), sg > 0)):
            V = L.point(ss, zz, off)[0]
            f = [0, 1, 2, 3] if rev else [3, 2, 1, 0]
            g.add(V, [f], "goggle_noseguard", [[(0.0, 0.0)] * 4])
    return g


# ---------------------------------------------------------------- placement, face foam, assembly
# Where the goggle sits on Leatt's helmet (HELMET frame): its lens front centre at (0, ty, tz), pitched by PITCH
# (top back), fitted with the shape in the four kit photos. On Damien the helmet sits on his head (helmet.py
# fit_on_head) and the goggle keeps this place in it; the foam fills to his face. Round 4 (recessed lens, a shape
# whose height origin the photo fit leaves free): lens front centre 2 mm further back and 4 mm lower than round 3's,
# so the frame's top front sits at y -152 mm and its beak bottom at z -64 mm (side views: -149, -64.6 to -66; the
# test allows 4 mm) and his nose bridge clears the lens (the full -149 put it 3 mm into the lens). Round 5: the
# fitted frame is 101 mm tall at the centre (round 4: 109; the photos fix its shape, not its size: ledger goggle.md,
# "Scale"), 0.2 mm further forward and at round 4's height: centring it on the side views' top and bottom (2.5 mm
# lower) put the lens's lower corners into the shell's eyeport edge and his nose bridge into the frame, so its top
# sits about 3 mm under the side views' and its beak bottom about 5 mm above (the scale question).
PLACE = (-0.1468, -0.004, 5.0)
FOAM_MIN, FOAM_MAX, FOAM_DEFAULT = 0.0015, 0.030, 0.014  # triple-layer foam, compressed against the face
FOAM_W = 0.013                     # foam band width on the frame's back face (round 2's seat, 13 mm at the top)


def g2h(V, pl=None):
    ty, tz, pitch = pl or PLACE
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    Rg = np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
    return np.asarray(V) @ Rg.T + np.array([0.0, ty, tz])


def h2g(V, pl=None):
    ty, tz, pitch = pl or PLACE
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    Rg = np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
    return (np.asarray(V) - np.array([0.0, ty, tz])) @ Rg


def march_to_skin(P, D, tree, step=0.0005, reach=FOAM_MAX + 0.01, tol=0.0015):
    """Distance along D from each P to the first skin point within tol of the ray (nan if none within reach)."""
    out = np.full(len(P), np.nan)
    for t_ in np.arange(0.0, reach, step):
        todo = np.isnan(out)
        if not todo.any():
            break
        d, _ = tree.query(P[todo] + D[todo] * t_)
        hit = d < tol
        idx = np.nonzero(todo)[0][hit]
        out[idx] = t_
    return out


def build_foam(rings, info, skin_G):
    """Face foam from the frame's back face to his face along the lens's inward normal, conforming (compressed to
    0.5 mm off the skin), never thinner than FOAM_MIN; where no skin is in reach (the ends past the temples) it
    keeps FOAM_DEFAULT."""
    L = info["L"]
    Cu, Ci = info["Cu"], info["Ci"]
    f, g = rings[RING_BACK_OUT], rings[RING_BACK_IN]
    # the foam is a FOAM_W band along the face-side opening (the frame's back face beyond it, at the cheeks' outer
    # edge and the beak's tabs, stays bare: the nose channel)
    gap = np.linalg.norm(f - g, axis=1)[:, None]
    f = g + (f - g) * np.minimum(1.0, FOAM_W / np.maximum(gap, 1e-9))
    # over the nose the foam leaves the bridge and runs along the lens opening's edge (the nose sits under the
    # bridge, in the nose guard: Leatt exploded view): its outer edge closes onto its inner edge there
    t = np.clip(1 - np.abs(Cu[:, 0]) / NOSE_S, 0, 1) * (Cu[:, 1] < 0)
    w = (t * t * (3 - 2 * t))[:, None] ** 0.5
    f = f + (g + (f - g) * 0.25 - f) * w
    tree = cKDTree(skin_G)
    out = []
    # five marches across the band (outer edge to inner edge): the face conforms across the cheeks' bulge;
    # a march that misses the skin (the edge past the cheek's curve) takes the band's nearest hit
    rows = [(f + (g - f) * a_, Cu + (Ci - Cu) * a_) for a_ in (0.0, 0.25, 0.5, 0.75, 1.0)]
    Ns = [L.point(C[:, 0], C[:, 1], 0.0)[1] for _, C in rows]
    D = np.array([march_to_skin(R_, -N, tree, tol=0.0025) for (R_, _), N in zip(rows, Ns)])   # his cheek's
    # vertices lie up to 5 mm apart: a 1.5 mm search let rays slip between them
    fill = np.nanmin(np.where(np.isnan(D), np.inf, D), axis=0)
    for (R_, _), N, d in zip(rows, Ns, D):
        d = np.where(np.isnan(d), fill, d)
        d = np.where(np.isfinite(d), d - 0.0005, FOAM_DEFAULT)
        d = np.clip(d, FOAM_MIN, FOAM_MAX)
        for _ in range(4):                                          # round the loop: no steps between samples
            d = np.minimum(d, (np.roll(d, 1) + 2 * d + np.roll(d, -1)) / 4 + 0.0005)
        out.append(R_ - N * d[:, None])
    foam = H.Part("goggle_foam")
    ring_faces(foam, [f] + out + [g], ["goggle_foam"] * (len(out) + 2))
    return foam, (out[0], f)


def build_goggle(body, Rt, prof):
    """The goggle on his head (MB rest frame), riding the head bone: frame, double lens, bare tear-off posts,
    outriggers, nose guard, face foam and the strap; his eyes behind it."""
    R, t = Rt
    fr, info = build_frame()
    rings, _ = frame_rings()
    skin = body["V"][H.head_skin(body, ("head",))]
    skin_G = h2g((skin - t) @ R)
    foam, foam_back = build_foam(rings, info, skin_G)
    mount = shell_mount(prof)                         # on the helmet: outriggers drape over the shell
    parts = [fr, build_fins(), build_frame_logo(), build_lens(), build_posts(), build_outriggers(mount=mount),
             build_nose_guard(), build_nose_ribs(skin_G=skin_G), foam]
    ends = {sg: g2h(a[None])[0] @ R.T + t for sg, (Go, Gi, a) in outrigger_grids(mount=mount).items()}
    for P in parts:
        P.V = g2h(P.V) @ R.T + t
    strap = H.build_strap(Rt, prof, ends)
    eyes, einfo = build_eyes(body)
    L = info["L"]
    ctr = g2h(L.point(0.0, 0.0, 0.0)[0][None])[0] @ R.T + t
    eye = H.head_landmarks(body)["eye"]
    info_out = dict(lens_centre_ahead_of_eye_mm=round(float(eye[1] - ctr[1]) * 1000, 1),
                    lens_centre_above_eye_mm=round(float(ctr[2] - eye[2]) * 1000, 1),
                    foam_mm=[round(float(np.linalg.norm(foam_back[0] - foam_back[1], axis=1).min()) * 1000, 1),
                             round(float(np.linalg.norm(foam_back[0] - foam_back[1], axis=1).max()) * 1000, 1)],
                    frame_width_mm=round(float(np.ptp(g2h(np.vstack(rings))[:, 0])) * 1000, 1),
                    frame_height_mm=round(float(np.ptp(np.vstack(rings)[:, 2])) * 1000, 1), **einfo)
    return parts + [strap] + eyes, info_out


def free_parts(gp=None):
    """The goggle alone as in Leatt's product photos (GOGGLE frame): frame, fins, logo, lens, posts, the free (flat)
    outriggers, nose guard and the foam at its default thickness (no face to press on); for the comparison with
    the goggle-alone photos (goggle_views.py)."""
    fr, info = build_frame(gp)
    rings, _ = frame_rings(gp)
    foam, _ = build_foam(rings, info, np.array([[0.0, 10.0, 0.0]]))
    return [fr, build_fins(gp), build_frame_logo(gp), build_lens(gp), build_posts(gp), build_outriggers(gp, None),
            build_nose_guard(gp), build_nose_ribs(gp), foam]


# ---------------------------------------------------------------- the helmet's brow badge (repainted by script)
# helmet.py's projection put the purple badge on the atlas twice ("LEATT LEATT") with four brow vents: the
# model's brow under the visor stands about 16 mm ahead of the real one, so Leatt's two side views (iso-left,
# iso-right) project it 19 mm apart either way. The badge and its two vents are measured on the shell by casting
# the rays of Leatt's MY27 front-iso-left (white badge, 31505 _1) and Pinata iso-right (purple badge) photos through
# their fitted cameras; each view's outline is centred on its own badge (the depth error shifts the whole outline)
# and the two are averaged; HELMET frame (x, z), m. The brow is then repainted once, centred on x = 0.
BADGE_Z = (0.0765, 0.0930)          # bottom and top of the badge
BADGE_HW = (0.0280, 0.0185)         # half widths at the bottom and the top (a trapezoid, top corners rounded)
BADGE_CORNER = 0.003
BADGE_LOGO = dict(width=0.0346, height=0.0083, zc=0.0848)   # white LEATT: 62 % of the bottom width, 50 % high
BADGE_RGB = (79, 39, 180)           # Pinata iso-right photo, median of the badge
VENT_QUAD = [(-0.0633, 0.0717), (-0.0368, 0.0797), (-0.0313, 0.0912), (-0.0624, 0.0775)]   # his right; mirrored
BROW_BOX = (0.096, 0.064, 0.101)    # |x| and z range repainted (plain brow in Leatt's photos)


def leatt_logo(width, height, cx, cy, shear=0.25):
    """The LEATT logotype (logo_polys) scaled to a box (width x height) centred at (cx, cy), y up, reading +x."""
    polys, lw = H.logo_polys(0.0, 0.0, 1.0, shear)
    sx, sy = width / lw, height
    return [[(cx + (px - lw / 2) * sx, cy + (py - 0.5) * sy) for px, py in p] for p in polys]


def badge_outline(n=8):
    (z0, z1), (w0, w1), r = BADGE_Z, BADGE_HW, BADGE_CORNER
    pts = [(-w0, z0), (w0, z0)]
    k = (w1 - w0) / (z1 - z0)
    # right side up to the corner, rounded corner, top, left corner, left side
    for sgn in (1, -1):
        c = (sgn * (w1 - r), z1 - r)
        arc = np.linspace(0, math.pi / 2, n) if sgn > 0 else np.linspace(math.pi / 2, math.pi, n)
        seg = [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in arc]
        pts += seg
    return np.array(pts)


def paint_brow_badge(path):
    """Repaint the brow of helmet_pinata.png: plain brow white, the two vents (dark mesh, lighter rim), the purple
    badge with one white LEATT. Every texel is coloured from its own 3D point on the shell."""
    from matplotlib.path import Path
    from PIL import Image
    Vo, Fo, prof = H.shell_outer()
    UV, isl = H.atlas_uvs(Vo, Fo)
    N = H.normals(Vo, Fo)
    idx, P, Nn = H.rasterize(UV * H.TEX, Vo[Fo], N[Fo])
    img = np.array(Image.open(path).convert("RGB")).astype(float)
    row, col = H.TEX - 1 - np.clip(idx[:, 1], 0, H.TEX - 1), np.clip(idx[:, 0], 0, H.TEX - 1)
    front = (P[:, 1] < -0.09) & (Nn[:, 1] < 0)
    box = front & (np.abs(P[:, 0]) < BROW_BOX[0]) & (P[:, 2] > BROW_BOX[1]) & (P[:, 2] < BROW_BOX[2])
    ring = front & (np.abs(P[:, 0]) < BROW_BOX[0] + 0.012) & (P[:, 2] > BROW_BOX[1]) & (P[:, 2] < BROW_BOX[2]) & ~box
    base = np.median(img[row[ring], col[ring]], 0) if ring.sum() > 20 else np.array(H.BASE_WHITE, float)
    xz = P[:, [0, 2]]
    col_ = np.tile(base, (len(P), 1))
    for sgn in (1, -1):                                              # vents: mesh, lighter moulded rim
        q = np.array(VENT_QUAD) * [sgn, 1]
        inside = Path(q).contains_points(xz)
        qc = q.mean(0)
        rim = Path(qc + (q - qc) * 1.12).contains_points(xz) & ~inside
        u = (xz[:, 0] + xz[:, 1]) / 0.0016
        v = (xz[:, 0] - xz[:, 1]) / 0.0016
        mesh = (np.abs(u - np.round(u)) < 0.12) | (np.abs(v - np.round(v)) < 0.12)
        col_[inside] = np.where(mesh[inside, None], [92, 92, 98], [26, 26, 30])
        col_[rim] = base * 0.82
    b = Path(badge_outline()).contains_points(xz)
    col_[b] = BADGE_RGB
    lg = BADGE_LOGO
    for poly in leatt_logo(lg["width"], lg["height"], 0.0, lg["zc"]):
        col_[b & Path(np.array(poly)).contains_points(xz)] = (240, 240, 244)
    out = img.copy()
    out[row[box], col[box]] = col_[box]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)
    return dict(brow_texels=int(box.sum()), badge_texels=int((b & box).sum()), base=base.round(0).tolist())


MATERIALS = {
    "eye_ball": dict(image="goggle_eyes_brown.png", rough=0.35, coat=1.0),        # wet: a clear coat over it all
    # red-pink: his 08, 09 (hue 346 deg; frame median his 08: 147/28/49, his 09: 160/10/48); high gloss (round 6):
    # Leatt's iso55 frame highlights have 2.4 px edges, rough 0.05 renders 2.5 px in the same studio light (0.4: 4.0
    # px, read as semi-matte; ledger goggle.md section 8)
    "goggle_frame": dict(rgb=[150, 0, 58], rough=0.05),
    "goggle_logo": dict(rgb=[236, 236, 238], rough=0.4),                   # printed white (MY27 kit views)
    "goggle_vent": dict(rgb=[16, 16, 18], rough=0.95),                      # foam-backed slots
    "goggle_foam": dict(rgb=[40, 40, 44], rough=0.95, sheen=0.6),
    "goggle_noseguard": dict(rgb=[30, 30, 32], rough=0.6),
    "goggle_post": dict(rgb=[20, 20, 22], rough=0.35),
    # gloss black (kit photo; round 6, iso55: Leatt's face reads 23/23/23 with thin crisp edge highlights; rough 0.25
    # under a coat rendered a grey sheen, 46; rough 0.05 bare, 36 and crisp edges, the rest is our studio's backdrop)
    "goggle_outrigger": dict(image="goggle_outrigger.png", rough=0.05),
    # purple mirror (Damien): metallic purple with an interference film, purple square on, gold-orange at grazing
    # angles (his 08, 09); the little light the mirror lets through is tinted dark purple (eyes hidden)
    "goggle_lens_mirror": dict(rgb=[90, 30, 125], metal=0.94, rough=0.03, transmission=1.0,
                               thin_film=dict(thickness_nm=430, ior=1.33)),      # swatches: deep purple square on
    "goggle_lens_clear": dict(rgb=[120, 90, 150], rough=0.02, transmission=1.0),
}
for _k in ("goggle_strap", "goggle_strap_in"):
    MATERIALS[_k] = H.MATERIALS[_k]


if __name__ == "__main__":
    # python3 goggle.py --free OUT.npz: the goggle alone (free_parts) for goggle_views.py
    if len(sys.argv) > 2 and sys.argv[1] == "--free":
        os.makedirs(TEXDIR, exist_ok=True)
        outrigger_texture(os.path.join(TEXDIR, "goggle_outrigger.png"))
        H.write_npz(sys.argv[2], free_parts())
        print("wrote", sys.argv[2])
