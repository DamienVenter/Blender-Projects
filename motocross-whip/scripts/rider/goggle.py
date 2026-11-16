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
  SCALE     the helmet (its own 45 mm strap scale, helmet.py); round 8: x 1.02 on it (PLACE), the most his face
            and the eyeport take (ledger section 10).
  STRAP     round 8: laid on the shell by build_strap (its height from his photo 07 and Leatt's Pinata kit
            photo, the slides from Leatt's MY27 back view).
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
# Round 7 (crisp and faceted, Leatt's white ISO at 1:1): the cross-section is three flat facets meeting in sharp
# creases, an inner wall (leaning out from the lens edge by "bevel": the lit top face of the lower band's foot), the
# front face (rim wide, flat), an outer facet leaning back to the outline edge (the top band's lighter top plane);
# the chamfer is only the outer crease's land and the mid ring lies on the outer facet (mid_w 0: no bulge). Every
# designed crease is shaded over CREASE_R either side, the width its highlight and shading step have in the photos.
# Round 6 (fair by construction, a moulded part): the outlines' offsets and every cross-section value are low-order
# smooth curves along the frame (bspline_half: a uniform cubic B-spline over the half loop, 24 coefficients for the
# outlines, 16 for the fields, mirrored at the centre line), fitted with a bending penalty; round 5's per-sample
# offsets and per-point values let each sample pull the surface on its own and the faces read as crumpled plastic.
CTRL = ("top_c", "step_hi", "step_lo", "fin_root", "top_corner", "side_top", "side_end", "bot_corner", "cheek",
        "cheek_step", "leg_out", "tab_tip", "notch_side", "arch_step", "notch_apex")


def ci(name):
    return CTRL.index(name)


GP = dict(
    a=0.13480, A=0.09390, tilt=0.0,          # lens plan (round 5 fit, kept since; round 4: 137.7, 89.8 mm)
    # frame outer edge (the outline seen from the front): control polygon (the corners). Round 7: the pillar's side_top,
    # side_end and bot_corner are collinear (one straight pillar); side_end sits at the lens edge's pillar corner's
    # height (z -17.13 mm, was -3.75), so the rings' rulings between the two edges run across the pillar, not up it
    # (the outline is the same to 60 um; the crease and chamfer wobbled 0.5 mm and failed the fairness test)
    out=[(0.0, 0.04394), (0.03950, 0.04056), (0.04495, 0.04135), (0.08844, 0.03407), (0.09272, 0.02977),
         (0.11247, 0.02380), (0.10827, -0.01713), (0.10588, -0.04047), (0.06294, -0.05308), (0.04993, -0.05515),
         (0.03280, -0.05465), (0.03101, -0.05542), (0.01250, -0.05019), (0.00260, -0.03785), (0.0, -0.03785)],
    # the lens's visible edge (the foot of the frame's inner wall, lip deep)
    open=[(0.0, 0.03508), (0.04177, 0.03248), (0.04230, 0.03232), (0.07923, 0.03156), (0.08977, 0.02874),
          (0.09986, 0.01868), (0.09986, -0.01713), (0.09430, -0.03279), (0.05716, -0.04098), (0.04860, -0.04590),
          (0.02838, -0.04954), (0.01850, -0.04125), (0.01411, -0.03073), (0.00670, -0.03291), (0.0, -0.03025)],
    # the face side's opening (frame inner wall, foam inner edge), rising over the bridge of his nose
    inner=[(0.0, 0.02761), (0.04014, 0.03231), (0.04100, 0.03409), (0.08607, 0.03256), (0.09364, 0.02506),
           (0.09548, 0.01486), (0.08955, 0.00042), (0.08982, -0.02606), (0.05510, -0.02633), (0.04300, -0.03185),
           (0.03364, -0.02758), (0.02517, -0.02659), (0.01529, -0.02062), (0.00611, -0.01904), (0.0, -0.01474)],
    # corner fillets at each control point: moulded edges, small (the tabs and the step pointed; round 7:
    # the nose arch's round top and feet fitted; a control point that does not turn gets a token fillet)
    fillet_out=[0.00300, 0.00050, 0.00050, 0.00300, 0.00300, 0.00300, 0.00300, 0.00300, 0.00200, 0.00200, 0.00120,
                0.00120, 0.00218, 0.00240, 0.00040],
    fillet_open=[0.00300, 0.00300, 0.00300, 0.00300, 0.00400, 0.00400, 0.00300, 0.00400, 0.00300, 0.00300, 0.00300,
                 0.00300, 0.00300, 0.00300, 0.00400],
    fillet_inner=[0.00500, 0.00500, 0.00500, 0.00600, 0.00600, 0.00600, 0.00500, 0.00600, 0.00600, 0.00600,
                  0.00600, 0.00600, 0.00800, 0.01000, 0.01200],
    # cross-section fields (round 6: the coefficients of a bspline_half over outline_t, the outer edge's arc
    # length from the top centre, 0, to the bottom centre, 1; m). Round 7 section (Leatt at 1:1): the inner wall
    # leans out by bevel from the lens edge (the lit "foot" beside the nose), a wide flat front face (rim), a
    # crisp crease with a 0.1 mm land (chamfer), the outer facet leaning back by band to the outline edge (the
    # lighter top plane), the top surface back to top, the frame's depth behind the lens front (the foam seat)
    depth=[0.01962, 0.01954, 0.02008, 0.02104, 0.02140, 0.02010, 0.01735, 0.01507, 0.01560, 0.01755, 0.01831,
           0.01653, 0.01231, 0.00728, 0.00327, 0.00212],
    rim=[0.00653, 0.00655, 0.00653, 0.00645, 0.00602, 0.00544, 0.00507, 0.00494, 0.00497, 0.00495, 0.00482,
         0.00478, 0.00503, 0.00545, 0.00578, 0.00586],
    chamfer=0.00010,
    bevel=[0.0, 0.0, 0.0, 0.00015, 0.00109, 0.00207, 0.00274, 0.00317, 0.00287, 0.00139, 0.00008, 0.0, 0.0,
           0.00016, 0.00071, 0.00084],
    band=[0.00195, 0.00253, 0.00393, 0.00488, 0.00553, 0.00580, 0.00567, 0.00591, 0.00651, 0.00669, 0.00535,
          0.00288, 0.00169, 0.00134, 0.00048, 0.00030],
    top=[0.01354, 0.01361, 0.01386, 0.01415, 0.01442, 0.01435, 0.01389, 0.01332, 0.01244, 0.01117, 0.00970,
         0.00814, 0.00659, 0.00532, 0.00458, 0.00441],
    mid_w=0.0,
    mid_t=0.5,
    # the frame's front face stands this far proud of the lens front (the same kind of field; round 7: the top
    # band 9 to 11 mm, the side pillars 3 to 5 mm with the post heads showing in front, the lower band 7 to 8)
    lip=[0.00906, 0.00963, 0.01129, 0.01033, 0.00619, 0.00325, 0.00396, 0.00471, 0.00419, 0.00361, 0.00515,
         0.00765, 0.00789, 0.00718, 0.00743, 0.00785],
    step=0.00167,           # the vent row's step in
    taper=0.00211,          # the outer wall leans out this much from the step to the back
    # samples per control segment of the left half (fillet_closed), and (round 6) the outer edge's and the lens
    # edge's smooth outward offsets (m): bspline_half coefficients over each polygon's own arc length, fitted on
    # nine photos with a bending penalty and held near 0 at the control points (ledger goggle.md)
    per=[40, 6, 40, 6, 6, 22, 14, 20, 7, 8, 6, 7, 6, 8],
    out_dk=[0.00010, -0.00023, -0.00041, -0.00009, 0.00015, 0.00149, 0.00067, -0.00012, 0.00002, -0.00001, 0.0,
            -0.00001, 0.00001, -0.00003, 0.00007, -0.00030, -0.00036, -0.00012, 0.00013, -0.00009, -0.00004,
            0.00018, -0.00008, 0.00017],
    open_dk=[-0.00003, 0.00006, 0.00004, -0.00005, 0.00001, 0.00013, -0.00016, 0.00003, 0.0, 0.00001, -0.00001,
             0.00002, -0.00004, 0.00012, -0.00007, -0.00039, -0.00018, 0.00002, 0.00003, -0.00008, 0.00004,
             -0.00001, 0.00001, -0.00001],
    # the top band's teeth (tooth_drop): |s| in, |s| out, drop at each end (m)
    # round 13 (decision 57, item 4): the teeth read through three views jointly (scratch saw13.py, sawfit13b.py: the
    # white ISO and the Pinata ISO through the iso55 camera, the yellow studio photo phy through its own). Per view the
    # frame colour's lowest row per column against our edge with no teeth and with a 1 mm drop, by the edge's |s|,
    # less a line through its read beyond the vents (|s| 41 to 43 and 81 to 85); the median of the three, fitted with
    # linear ramps between the steps (residual rms 0.10 mm; the views scatter about the median by rms 0.42). They
    # agree on steps down at 48.5 and 61.5 (phy 60) and up at 58.5, and on no drop at 79 to 80 (round 6's 1.5 mm step
    # at 79.5 was not there). The second tooth's fall back to the band (its slanted end face) ends where they disagree:
    # the white ISO by 75, iso55 77, phy 78; built to the median, 77.5. Below 47 they disagree (0.4 to 1.8 mm).
    teeth=[[0.04850, 0.05850, 0.00027, 0.00182], [0.05850, 0.06150, 0.00051, 0.00136],
           [0.06150, 0.07150, 0.00196, 0.00298], [0.07150, 0.07750, 0.00298, 0.0]],
    # outriggers (outrigger_frames): fitted with the shape (round 5, kept; round 7 checked the far one in phr: ledger)
    # round 10 (item 2): the plate tapers. Its edges are lines from Leatt's near plate in iso55 and phr (back-projected
    # onto it at 1:1, scratch plcmp.py): top 28.5 mm at the hinge to 23.8 at the back, bottom -38.9 to -31.3, the back
    # bottom between iso55's (-29.9), phr's (-32.5) and phw's (-33.5); the top's slope between iso55 and phr (0.20
    # to 0.23) and phw (where a steeper one stands above Leatt's). Its front corners cut back to round 9's (26.6,
    # -37.0 mm: OR_FRONT_CUT), where the frame hides them in the front photos, its back corners chamfered (OR_CHAMFER).
    # Round 9: or_back_h 0.0587, or_top_in 0.0032, or_bot_in 0.0035, or_back_dz 0.0006 (a 63.5 by 58.7 mm plate).
    # Round 12 (item 2): with the hinge OR_HINGE_IN inboard and OR_HINGE_BACK back (the plate 27 mm long), the taper
    # refitted on the same edges (scratch plfit12.py: Leatt's near plate back-projected onto the plate's own plane,
    # turned 6.25 deg in iso55 and 6.0 in phr so its back edge stays; phr weighted 1.5, as the two views disagree on
    # the bottom edge by 2.6 mm): edge rms top / bottom iso55 0.60 / 1.59 mm (round 10 1.08 / 1.52), phr 0.32 / 1.02
    # (0.53 / 1.00). Round 10: or_back_h 0.0551, or_top_in 0.0013, or_bot_in 0.0016, or_back_dz 0.00145 (63.5 by
    # 50.1 mm); now 64.7 by 50.5.
    or_len=0.03040,
    or_back_h=0.05554,
    or_turn=0.44010,
    or_top_in=0.00050,
    or_bot_in=0.00128,
    or_back_dz=0.00140,
    or_front=0.00220,
    # round 7: the nose guard (build_nose_guard, NG_KEYS), fitted with the shape on the photos' silhouettes; the sweep
    # then set on the finished frame (10.2 to 3 mm: swept back 10 mm its far side left the backdrop showing inside the
    # arch in phr, phy and phw, where Leatt's guard fills it; the fit views' outline p90s 0.1 to 0.4 mm better)
    ng=[-0.03750, -0.05464, 0.00850, 0.01738, 0.00300, -0.00100, 0.00159, 0.00300, 0.00250],
)
NOSE_S = 0.030                    # |s| inside which the foam leaves the frame's back for the nose bridge
VENT_ROWS = (0.3, 0.7)             # the top vents' slots run between these fractions of the outer wall's depth
# rings round the frame's cross-section: a lens contact, b lip, c rim inner edge, d rim outer edge, e chamfer,
# e2 the front face's crease, f outline edge, f2 top surface back, g step, v1 v2 vent rows, k outer wall back,
# l back face inner edge (the face side's opening), m inner wall at the lens stack's back, n behind the lens's
# visible edge
RING_RIM, RING_CHAMFER, RING_MID, RING_EDGE, RING_TOP = 3, 4, 5, 6, 7
RING_VENT, RING_BACK_OUT, RING_BACK_IN = 9, 11, 12
LENS_T, LENS_GAP, LENS_IN_T = 0.0012, 0.0016, 0.0006     # outer lens, foam spacer gap, inner lens (m)
LENS_GROOVE = 0.003                                     # the lens runs this far under the frame's front rim
# round 7: the frame's moulded creases (Leatt's white ISO 39278 and iso55 at 1:1, 0.177 mm per px: across every
# designed crease the shading steps in 1.2 to 2.4 px, 10 to 90 %, against 0.8 to 1.5 px for the silhouettes' own
# blur; phw and phr read alike, 0.8 to 2.5 px; ledger goggle.md section 9): each crease turns its shading over
# CREASE_R either side (support rings), the inner crease has a land of that size and the top crease a land of
# GP["chamfer"] (0.1 mm). Round 6 rolled them over 0.35 mm (3 to 4 px) and a 45 deg chamfer: the soft, inflated look.
CREASE_R = 0.00010
# the probes (probe.py, 10 to 90 % of the shading step across each crease, px at 1:1): view, photo point, measured
# width, the rings either side of the turn (the top crease is the rim's outer edge d and the land e behind it, one
# line at 1:1; the lens edge is the front face's inner edge c). test_goggle checks the built rings against them.
# Each photo's own blur is its silhouette's width (wiso 0.9 at the top, x 1250, and 0.8 at the pillar, y 880;
# iso55 1.3 and 1.5 at the top, x 1250 and 1150). phw and phr read alike but their cameras are less sure at that
# scale, so they stay out of the test.
CREASE_PROBES = [
    ("wiso", 1250, 731.5, 2.2, (3, 4)),      # the top band's upper crease
    ("wiso", 1150, 744.5, 2.1, (3, 4)),
    ("wiso", 1250, 767.5, 2.0, (2, 2)),      # the top band's lens edge
    ("iso55", 1250, 728.5, 1.9, (3, 4)),
    ("iso55", 1150, 740.0, 1.2, (3, 4)),
    ("iso55", 1250, 765.0, 1.3, (2, 2)),
    ("iso55", 1150, 771.0, 1.6, (2, 2)),
]
CREASE_BLUR = dict(wiso=0.85, iso55=1.4)


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
    either side, r at most 0.45 of the shorter side); per samples per side (one number, or one per side). Returns the
    samples and, for each, the side it lies on and the fraction along it: outlines sampled alike correspond point
    for point."""
    P = np.asarray(P, float)
    k = len(P)
    # round 7: a control point that does not turn the outline (under 3 degrees: the nose arch's apex between its
    # mirrored flat top, a straight pillar's middle) gets only a token fillet (0.04 of its sides, a straight run), and
    # its neighbours may use 0.95 of the shared side (the arch's round top, about 4 mm radius under a 3.4 mm flat,
    # Leatt's front photos; ledger goggle.md section 9)
    e = np.roll(P, -1, 0) - P
    e /= np.maximum(np.linalg.norm(e, axis=1), 1e-12)[:, None]
    flat = np.einsum("ij,ij->i", np.roll(e, 1, 0), e) > np.cos(np.radians(3.0))
    tin, tout = [], []
    for i in range(k):
        a, b, c = P[(i - 1) % k], P[i], P[(i + 1) % k]
        ri = 0.04 * min(np.linalg.norm(b - a), np.linalg.norm(c - b)) if flat[i] else (r[i] if np.ndim(r) else r)
        fa, fc = (0.95 if flat[(i - 1) % k] else 0.45), (0.95 if flat[(i + 1) % k] else 0.45)
        d = min(ri, fa * np.linalg.norm(b - a), fc * np.linalg.norm(c - b))
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
    return loop_t(apply_snaps(Cb, tooth_snaps(gp, per)), half_samples(gp, per))   # round 14: the teeth's samples


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
TOOTH_SNAP = 0.0005                 # m, round 14 (item 5): a loop sample this far either side of each tooth step


def tooth_steps(gp):
    """The |s| (m) where the teeth's drop jumps: a tooth's start or end against the next tooth's, or the band's 0."""
    teeth = sorted(gp.get("teeth", []))
    out = set()
    for s_in, s_out, d_in, d_out in teeth:
        before = next((t[3] for t in teeth if abs(t[1] - s_in) < 1e-9), 0.0)
        if abs(d_in - before) > 1e-5:
            out.add(s_in)
        if not any(abs(t[0] - s_out) < 1e-9 for t in teeth) and abs(d_out) > 1e-5:
            out.add(s_out)
    return sorted(out)


def tooth_snaps(gp, per):
    """Round 14 (item 5): moves for the loops' samples (fillet_closed's, sampled alike) that put a top band sample
    TOOTH_SNAP either side of each tooth step (tooth_steps), both sides of the goggle: [(k, a, b, w)], sample k to
    a + (b - a) w between its neighbours a and b on the same side of the loop's polygon, in order. Sampled every 1 mm
    a step ran over 2 mm: the white ISO read 48.5 mm's over 11 px and more, Leatt's over 6 (scratch step14b.py)."""
    steps = tooth_steps(gp)
    if not steps:
        return []
    Co, seg, _ = fillet_closed(full_loop(gp["open"]), per, loop_values(gp["fillet_open"]))
    x, n = Co[:, 0].copy(), len(Co)
    used, moves = set(), []
    for s0 in steps:
        for sg in (1.0, -1.0):
            for target in (sg * (s0 - TOOTH_SNAP), sg * (s0 + TOOTH_SNAP)):
                for k in np.argsort(np.abs(x - target)):
                    k = int(k)
                    a, b = (k - 1) % n, (k + 1) % n
                    if (k in used or Co[k, 1] <= 0.0 or seg[a] != seg[k] or seg[b] != seg[k]
                            or not min(x[a], x[b]) < target < max(x[a], x[b])):
                        continue
                    w = (target - x[a]) / (x[b] - x[a])
                    moves.append((k, a, b, float(w)))
                    x[k] = target
                    used.add(k)
                    break
    return moves


def apply_snaps(C, moves):
    """A loop (or its fractions) with tooth_snaps' moves applied in order."""
    C = np.array(C, float)
    for k, a, b, w in moves:
        C[k] = C[a] + (C[b] - C[a]) * w
    return C


def tooth_drop(gp, C):
    """How far the top band's teeth hang below the lens edge at each (s, z) sample (GP "teeth": per tooth the |s| of
    its inner and outer ends and its drop there). Leatt's ISO renders (iso55, pink and white, the same camera): going
    out from the stepped centre the top band's lower edge steps down twice more, each tooth sloping lower outwards,
    and at the last tooth's outer end it steps straight back up (|s| 43.6, 59 and 79.5 mm, back-projected on the
    front face). Round 6: the profile is eased over about 2 TOOTH_EASE at its steps and corners (a Gaussian of
    TOOTH_EASE / 2) instead of jumping between two samples. Round 13: read through three views jointly (GP "teeth"):
    steps at 48.5, 58.5 (up) and 61.5, the last tooth's end face sloping back to the band by 77.5."""
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
    steps down at the top band's teeth (teeth=False: the plain lens edge, sampled as with them). Round 14: a sample of
    each loop TOOTH_SNAP either side of each step (tooth_snaps)."""
    gp = gp or GP
    per = loop_per(gp) if per is None else per
    nh = half_samples(gp, per)
    Co, seg, frac = fillet_closed(full_loop(gp["open"]), per, loop_values(gp["fillet_open"]))
    Cu, _, _ = fillet_closed(full_loop(gp["out"]), per, loop_values(gp["fillet_out"]))
    Ci, _, _ = fillet_closed(full_loop(gp["inner"]), per, loop_values(gp["fillet_inner"]))
    mv = tooth_snaps(gp, per)                  # round 14 (item 5): a sample either side of each tooth step, every loop
    Co, Cu, Ci, frac = (apply_snaps(C, mv) for C in (Co, Cu, Ci, frac))
    if gp.get("out_dk") is not None:
        Cu = Cu + outward2d(Cu) * bspline_half(gp["out_dk"], loop_t(Cu, nh))[:, None]
    if gp.get("open_dk") is not None:
        Co = Co + outward2d(Co) * bspline_half(gp["open_dk"], loop_t(Co, nh))[:, None]
    if teeth and gp.get("teeth"):
        Co = Co - np.c_[np.zeros(len(Co)), tooth_drop(gp, Co)]
    return Co, Cu, Ci, seg, frac


# Round 7: the raised tab on the top band (it carries the Leatt icon): behind the front face's top crease the top
# surface stands TAB_H higher for |s| < TAB_S, ramping over TAB_RAMP at each end. The top silhouette steps up there in
# four photos: at s -32.0 (iso55, +11 px), -32.0 (phy, +6 px), -29.9 (phw, +6 px), and the white ISO (+9 to 10 px at
# 0.177 mm per px, 1.6 to 1.8 mm); its far end reads at +22.7 to +38.8 (phr, phw, phy: the step faces away, so it
# is mirrored from the near end). Ledger goggle.md section 9.
TAB_S, TAB_RAMP, TAB_H = 0.0310, 0.0020, 0.0017


def tab_rise(Cu, nu):
    """How far the tab lifts each outer outline point (along its outward normal): on the top band only."""
    a = np.abs(Cu[:, 0])
    x = np.clip((TAB_S + 0.5 * TAB_RAMP - a) / TAB_RAMP, 0.0, 1.0)
    return TAB_H * x * x * (3.0 - 2.0 * x) * ((Cu[:, 1] > 0.0) & (nu[:, 1] > 0.7))


def frame_rings(gp=None, per=None, notch=False):
    """The frame as rings (closed loops of 3D points, GOGGLE frame) round its cross-section (see RING_*). notch: the
    worn build's nose (nose_back)."""
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
    st, r = gp["step"], CREASE_R
    bv = xs_at(dict(bevel=gp.get("bevel", 0.0)), "bevel", tu)
    bv = np.minimum(bv, 0.5 * W)                                    # the inner wall leaves room for the front face
    # round 6: at the nose arch's apex the face narrows to 1.0 to 4.6 mm (|s| < 4.5 mm), less than the rim and the
    # chamfer (4.2 mm): there both shrink with it (to 0.85 of the width), so the rings keep their order across the
    # face. Before, they ran past the outer edge and the face folded back: a pinch at the apex in the 1:1 crops
    k = np.minimum(1.0, 0.85 * (W - bv) / np.maximum(rim + ch, 1e-9))
    rim, ch = rim * k, ch * k
    # round 12: the side section (SIDE_*): on the pillars the wall stands nearly upright from the lens's curled-back
    # end to the front face, its foot moved out under the face (c0 stays)
    foot, bv_side = side_foot(gp, Co, Cu, tu)
    Co_fit, Co = Co, Co + foot
    bv, back = bv_side, lens_back(Co[:, 0], Co[:, 1])
    Ci, dl, dm, dn = nose_back(Co, Ci, d, notch)                    # round 11: the bridge behind the comb
    dm = dm + lens_back(Ci[:, 0], Ci[:, 1])           # round 12: the plate behind the lens stays behind the curled lens

    def ring(C, off):
        return L.point(C[:, 0], C[:, 1], off)[0]
    Cu = Cu + nu * tab_rise(Cu, nu)[:, None]                        # round 7: the raised tab behind the top crease
    c0 = Co + U * bv[:, None]                                       # the front face's inner edge
    # round 7: the top crease's land drops at 45 deg only where the outer facet behind it falls back that steeply or
    # more; where that facet is nearly flat (the lower band and the nose arch, band under 1 mm) the land lies on it,
    # so the crease does not draw a dark line across a face Leatt's shows plain (the 1:1 crop of the arch)
    run = np.linalg.norm(Cu - c0 - U * rim[:, None], axis=1)
    drop = ch * np.minimum(1.0, bd / np.maximum(run, 1e-6))
    fw = r / np.hypot(bv, lip + back)                               # round 7: b on the (leaning) inner wall, r short
    rings = [ring(Co, 0.0003 - back),                               # a: against the lens front (in the groove)
             ring(c0 - U * (bv * fw)[:, None], lip - (lip + back) * fw),  # b: the inner wall up from the lens (bevel)
             ring(c0 + U * r, lip),                                 # c: front rim, inner edge
             ring(c0 + U * rim[:, None], lip),                      # d: front rim, outer edge
             ring(c0 + U * (rim + ch)[:, None], lip - drop),        # e: the crease's land
             ring(c0 + U * (rim + ch)[:, None] + (Cu - c0 - U * (rim + ch)[:, None]) * mt[:, None],
                  lip - drop + (drop - bd) * mt + mw),              # e2: the crease across the front face
             ring(Cu, lip - bd),                                    # f: the band face up to the outline edge
             ring(Cu, lip - top),                                   # f2: the top surface back to the step
             ring(Cu - nu * st, lip - top - 0.0003)]                # g: step in to the vent row
    for f_ in VENT_ROWS:                                            # v1, v2: vent rows on the outer wall
        rings.append(ring(Cu + nu * (gp["taper"] * f_ - st), (lip - top - 0.0003) * (1 - f_) - d * f_))
    rings += [ring(Cu + nu * (gp["taper"] - st), -d),               # k: outer wall back
              ring(Ci, -dl),                                        # l: back face inner edge (foam seat)
              ring(Ci, -dm),                                        # m: inner wall at the plate behind the lens
              ring(Co, -dn - back)]                                 # n: behind the lens's visible edge
    return rings, dict(Co=Co, Co_fit=Co_fit, Cu=Cu, Ci=Ci, depth=d, L=L, seg=seg, frac=frac, t=tu, back=back)


# top vents: slots in the vent row behind the top band, s ranges on each side (Leatt exploded view and ISO: three
# slots a side either side of the moulded logo)
VENTS_S = [(0.008, 0.024), (0.030, 0.046), (0.052, 0.068)]
# round 10 (decision 48, item 3): the black chassis round the lens's side edges (build_frame): ring gaps a (the
# bevel up from the lens front), b, l, m (the inner wall and the plate behind the lens) and n (the lens's seat),
# where the lens edge's |s| reaches CHASSIS_S; two clip slots a side in gap a (z ranges of the lens edge, m).
# Measured in Leatt's white ISO through the iso55 camera (the same render as his Pinata ISO; the band is black in
# every colourway): per-row luminance across the band, slots y 835 to 903 and 1025 to 1094 px (near black inside,
# L 1 to 3 against the face's 18 to 23), mapped through gap a's middle to lens edge z 19.4 to 6.5 and -15.9 to
# -28.5 mm; across, x 1673 to 1696 px, which is gap a's whole width (t -0.08 to 1.03 at row 1040). The post sits
# between them. Each slot is a pocket CHASSIS_SLOT_D deep into the moulding (square to gap a's face), its mouth
# CHASSIS_SLOT_T of the way across the gap (a thin chassis frame left either side), its floor near black.
CHASSIS_S = 0.085
CHASSIS_SLOTS = [(0.0065, 0.0194), (-0.0285, -0.0159)]
CHASSIS_SLOT_T = (0.47, 0.97)   # round 12: up the taller side wall (SIDE_*): x 1671 to 1694 px in iso55 (round 10 0.12, 0.92)
CHASSIS_SLOT_D = 0.0015
CHASSIS_RINGS = (0, 1, 12, 13, 14)
# Round 11 (decision 49, item 4): the strap clip's tab inside each slot. Leatt's white ISO at 6x (column x 1680): a grey
# block, L 32 to 35 against the face's 19 and the slot's 0 to 2, at the slot's end away from the post, 16 px long in
# the top slot (y 836 to 851) and 13 in the bottom one (1080 to 1093), at 0.19 mm a px (round 10's slot rows against
# their lens edge z), over the lens side 0.68 of the slot's width (x 1672 to 1689 of 1672 to 1697); the Pinata ISO
# shows the same tabs (L 24 to 36), lit over their whole length. Their depth does not show: 0.5 mm below the mouth
# the slot's end hid all but 5 to 6 px of them in iso55 (and their end wall caught the top light, L 50 to 127), so the
# top is 0.2 mm below the mouth.
# Round 12 (decision 53, item 3): the side section. Leatt's ISO (iso55) shows his lens's far end at x 1656 to 1658 px
# (rows 820 to 1100) and the band from there to 1703; ours ended at 1667 to 1673 and the band (gap a) ran to 1696,
# so his band was 46 px to our 24 and our lens's last 20 mm, nearly edge on there, covered the rest. The same in phr
# (his lens to 1597 to 1600, ours 1612) and phy (1628, ours 1647). Through the cameras a point 1 mm further back along
# the lens normal moves 5.3 px (iso55), 3.9 (phr) and 4.6 (phy) there, and 1 mm along the lens surface 0.15 to 0.5:
# all three views put his lens's end 3 to 4 mm behind ours, a moulded lens curling back into the frame's sides, with
# the wall from it to the front face 7 to 8 mm tall. On the near side his frame colour runs to the lens (iso55 face
# 921 to 983 px, the lens from 984; ours 920 to 981, then our black wall 982 to 993): his wall does not lean out
# (seen from iso55 a wall on the near pillar shows only when it leans out more than 17 deg; ours leaned 32 to 37).
# Built: the lens's ends curl back to SIDE_LENS_BACK behind the lens surface (lens_back; saturated before the
# pillar, so its straight run lies at one depth: from 85 to 99.5 mm the far end stayed at 1662 to 1667 px), from |s|
# 60 mm along the bands' edges (over 75 to 97 the lower band's lens edge rippled 45 um and turned 2.4 deg a sample,
# test_round6_frame_is_fair's bounds 10 um and 1 deg) and from 75 mm over the pillar's height (from 60 there the lens
# at s 72 to 95 mm lay at 81 to 87 deg to the iso55 view and mirrored the black wall beside it: dark from 1645 px),
# the posts at |s| 86.7 mm standing on the curled lens (post_frame), and on the pillars (SIDE_S) the wall's lean
# SIDE_BEVEL at most, its foot moved out under the face (the face's inner edge c0 stays), the lenses' hidden edges
# where they were (lens_region). Now: the lens's far end 1656 to 1659 px in iso55, 1601 to 1603 in phr, 1633 to 1634
# in phy (main 1671 to 1674, 1612 to 1614, 1647); its colour runs to 1654 to 1657 in iso55 rows 870 to 1060 (Leatt
# 1657 to 1658; 1648 at rows 840 and 1090, where the curl eases to the bands') and to 1590 to 1593 in phr (Leatt 1593
# to 1596); the pillar wall 6.9 mm tall, leaning 9 to 10.5 deg (main 4.7 mm, 32 to 37), no wall px on the near side
# in iso55 (main 9 to 12: its lens from 982 to 984 px, as Leatt's). A face 1.3 mm prouder there for his far
# silhouette (1703 px against our 1692 to 1696 in iso55) moved the front views' outline p90 0.8 to 1.1 mm the wrong
# way (phw 5.75 to 6.58 mm): not built, the far silhouette stays 7 to 11 px short.
SIDE_S = (0.085, 0.0995)
SIDE_LENS_S = (0.060, 0.099)
SIDE_LENS_BACK = 0.0030
SIDE_LENS_MID = 0.075
SIDE_LENS_Z = ((-0.030, -0.015), (0.012, 0.025))    # m: the pillar's height (start of the late curl), eased from
                                                    # the bands' edges (lower z -32 to -40.5, upper 30)
SIDE_BEVEL = 0.0012
SIDE_GROOVE_MIN = 0.0006


def side_w(s):
    """Round 12: 0 to 1 over the lens's |s| SIDE_S (smootherstep): where the side section applies."""
    x = np.clip((np.abs(s) - SIDE_S[0]) / (SIDE_S[1] - SIDE_S[0]), 0.0, 1.0)
    return x * x * x * (x * (6.0 * x - 15.0) + 10.0)


def side_foot(gp, Co, Cu, tu):
    """Round 12: on the pillars (SIDE_S) the wall's lean comes down to SIDE_BEVEL with its foot, the lens edge, moved
    out under the face: the move per lens edge sample (s, z) and the bevel left. frame_rings and lens_region (the
    lenses run their groove depth under the frame from the moved edge) share it."""
    W = np.linalg.norm(Cu - Co, axis=1)
    U = (Cu - Co) / np.maximum(W, 1e-9)[:, None]
    bv = np.minimum(xs_at(dict(bevel=gp.get("bevel", 0.0)), "bevel", tu), 0.5 * W)
    bv_side = bv + (np.minimum(bv, SIDE_BEVEL) - bv) * side_w(Co[:, 0])
    return U * (bv - bv_side)[:, None], bv_side


def _smoother(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (x * (6.0 * x - 15.0) + 10.0)


def lens_back(s, z):
    """Round 12: how far the lens lies behind the lens surface at (s, z): its ends curl back, SIDE_LENS_BACK from
    |s| SIDE_LENS_S[1] on (smootherstep: the pillar's straight run all at one depth). The curl starts at
    SIDE_LENS_S[0] along the bands' edges (the lower band's edge stays fair: over 75 to 97 mm it rippled 45 um), and
    at SIDE_LENS_MID over the pillar's height (SIDE_LENS_Z), so the lens turns away late, as Leatt's: started at 60
    mm there, the lens from s 72 to 95 mm lay at 81 to 87 deg to the iso55 view, mirrored the black wall beside it and
    read dark from x 1645 px (Leatt's lens colour runs to 1654, ours from 75 mm to 1651)."""
    zl, zh = SIDE_LENS_Z
    w = _smoother((np.asarray(z) - zl[0]) / (zl[1] - zl[0])) * _smoother((zh[1] - np.asarray(z)) / (zh[1] - zh[0]))
    a = SIDE_LENS_S[0] + (SIDE_LENS_MID - SIDE_LENS_S[0]) * w
    return SIDE_LENS_BACK * _smoother((np.abs(s) - a) / (SIDE_LENS_S[1] - a))


CHASSIS_CLIP_LEN = (0.0030, 0.0024)          # m along the lens edge, per slot (CHASSIS_SLOTS' order)
CHASSIS_CLIP_W = 0.68
CHASSIS_CLIP_H = 0.0013                      # m up from the slot's floor (CHASSIS_SLOT_D deep)


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


def build_frame(gp=None, notch=False):
    gp = gp or GP
    rings, info = frame_rings(gp, notch=notch)
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
        mats[k] = ["goggle_bridge" if abs(c[0]) < RIB_BRIDGE_S and c[1] < 0 else "goggle_frame" for c in Co]
    # round 10: round the lens's side edges the frame is the black chassis that carries the plates (Leatt's ISO in
    # every colourway, the white, black and Pinata alike: a black band from the lens's far edge to the silhouette
    # with two clip slots above and below the post; phr and phy show it the plates' colour, the strap through its
    # slots): the lens's seat, the bevel in front of it and the inner wall behind it, where the lens edge's s is
    # past CHASSIS_S. The coloured shell keeps the front rim, the crease and the outer wall.
    side = np.abs(Co[:, 0]) >= CHASSIS_S
    for k in CHASSIS_RINGS:
        mats[k] = ["goggle_chassis" if side[i] else (mats[k][i] if not isinstance(mats[k], str) else mats[k])
                   for i in range(len(Co))]
    # support rings CREASE_R either side of every edge: smooth shading then turns only at the edges, and the faces
    # read flat (without them the bezel shaded like a tube; round 6's 0.35 mm rolled each crease over 3 to 4 px at
    # 1:1, Leatt's turn in 1.3 to 2.4 px). Gap a also gets the clip slots' mouth edges (CHASSIS_SLOT_T): strip 2.
    R2, M2 = [], []
    K = len(rings)
    for k in range(K):
        A_, B_ = rings[k], rings[(k + 1) % K]
        gap = np.linalg.norm(B_ - A_, axis=1)[:, None]
        f_ = np.clip(CREASE_R / np.maximum(gap, 1e-6), 0, 0.3)
        mid = [A_ + (B_ - A_) * t for t in CHASSIS_SLOT_T] if k == 0 else []
        R2 += [A_, A_ + (B_ - A_) * f_] + mid + [B_ + (A_ - B_) * f_]
        M2 += [mats[k]] * (3 + len(mid))
    fr = H.Part("goggle_frame")
    ring_faces(fr, R2, M2)
    chassis_slots(fr, R2[2], R2[3], rings, Co, side, info["L"])
    return fr, info


def chassis_slots(fr, X0, X1, rings, Co, side, L):
    """Round 10: the clip slots in the chassis band (CHASSIS_SLOTS): the faces of gap a's strip between X0 and X1
    (the slot's mouth edges) over each slot's run of segments are cut out and a pocket CHASSIS_SLOT_D deep put in
    their place: the floor and side walls in goggle_slot (no specular: they stand for the slot's dark inside, which
    Leatt's shows at L 1 to 3; as glossy chassis the shallow pocket read 41 to 54, brighter than the face's 36) and
    the end walls in goggle_chassis (Leatt's top slot shows its end lit). Each face of the pocket has its own
    vertices, so its edges shade sharp. Faces of strip 2 are 2 m + i (ring_faces' order)."""
    m = len(Co)
    cen = np.mean(rings, axis=0)                          # the cross-section's centre per segment: into the moulding
    cut, add = set(), []
    for (z0, z1), clip in zip(CHASSIS_SLOTS, CHASSIS_CLIP_LEN):
        inn = side & (Co[:, 1] >= z0) & (Co[:, 1] <= z1)
        for sgn in (1, -1):
            v = np.nonzero(inn & (np.sign(Co[:, 0]) == sgn))[0]
            if len(v) < 2:
                continue
            v = v[np.argsort(v)]
            if np.any(np.diff(v) != 1):                   # the run wraps the loop's start: never at the sides
                raise ValueError("chassis slot run is not contiguous")
            T = X0[(v + 1) % m] - X0[(v - 1) % m]
            N = np.cross(T, X1[v] - X0[v])
            N *= np.sign(np.sum(N * (cen[v] - 0.5 * (X0[v] + X1[v])), axis=1))[:, None]
            N /= np.linalg.norm(N, axis=1)[:, None]
            # square to the face the floor's inner edge ran 0.17 mm into the lens's groove; parallel to the lens its
            # outer edge came within 0.24 mm of the front rim's face: half its part along the lens normal is taken
            # off (the floor then 0.20 mm or more above the lens front, 0.66 mm or more inside the moulding)
            NL = L.point(Co[v, 0], Co[v, 1], 0.0)[1]
            N -= 0.5 * NL * np.sum(N * NL, axis=1)[:, None]
            N /= np.linalg.norm(N, axis=1)[:, None]
            Q0, Q1 = X0[v] + N * CHASSIS_SLOT_D, X1[v] + N * CHASSIS_SLOT_D
            cut |= {2 * m + i for i in v[:-1]}
            add += [(X0[v], Q0, "goggle_slot"), (Q0, Q1, "goggle_slot"), (Q1, X1[v], "goggle_slot")]
            for j, flip in ((0, False), (-1, True)):
                q = [X0[v[j]], Q0[j], Q1[j], X1[v[j]]]
                fr.F.append(list(fr.add(np.array(q[::-1] if flip else q), [], "x") + np.arange(4)))
                fr.M.append("goggle_chassis")
                fr.UV.append([(0.0, 0.0)] * 4)
            # round 11: the clip's tab at the slot's end away from the post (the top slot's top, the bottom one's
            # bottom), clip long from the end wall: a closed block of its own, 0.05 to 0.1 mm clear of the pocket's
            # end wall, side wall and floor (a solid of its own for the overlap test). Its ends are interpolated
            # along the run: the segments lie 1.1 to 1.8 mm apart here, and whole segments made it 1.2 mm long (6 px
            # in iso55 against Leatt's 13 to 16)
            o = np.argsort(-Co[v, 1]) if z0 > 0 else np.argsort(Co[v, 1])
            A0, A1, NN = X0[v][o], X1[v][o], N[o]
            sl = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(A0, axis=0), axis=1))]
            st = np.r_[0.0001, sl[(sl > 0.0001) & (sl < clip)], clip]
            A0, A1, NN = (np.stack([np.interp(st, sl, P[:, c]) for c in range(3)], 1) for P in (A0, A1, NN))
            NN /= np.linalg.norm(NN, axis=1)[:, None]
            u0 = 0.00005 / np.linalg.norm(A1 - A0, axis=1)
            rails = np.stack([A0 + (A1 - A0) * u[:, None] + NN * d for u, d in (
                (u0, CHASSIS_SLOT_D - CHASSIS_CLIP_H), (np.full_like(u0, CHASSIS_CLIP_W), CHASSIS_SLOT_D - CHASSIS_CLIP_H),
                (np.full_like(u0, CHASSIS_CLIP_W), CHASSIS_SLOT_D - 0.00005), (u0, CHASSIS_SLOT_D - 0.00005))])
            b, n = fr.add(rails.reshape(-1, 3), [], "x"), len(st)
            for r in range(4):
                r2 = (r + 1) % 4
                for i in range(n - 1):
                    fr.F.append([b + r * n + i, b + r * n + i + 1, b + r2 * n + i + 1, b + r2 * n + i])
            fr.F += [[b + r * n for r in range(4)], [b + r * n + n - 1 for r in range(3, -1, -1)]]
            fr.M += ["goggle_clip"] * (4 * (n - 1) + 2)
            fr.UV += [[(0.0, 0.0)] * 4] * (4 * (n - 1) + 2)
    keep = [i for i in range(len(fr.F)) if i not in cut]
    fr.F, fr.M, fr.UV = [fr.F[i] for i in keep], [fr.M[i] for i in keep], [fr.UV[i] for i in keep]
    for A_, B_, mat in add:                               # each wall a strip of its own vertices along the run
        a, b = fr.add(A_, [], "x"), fr.add(B_, [], "x")
        n = len(A_)
        for i in range(n - 1):
            fr.F.append([a + i, a + i + 1, b + i + 1, b + i])
            fr.M.append(mat)
            fr.UV.append([(0.0, 0.0)] * 4)


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
    # round 7: the nose arch's ears, the top corners of its legs on the front face's inner edge (ring c at the lens
    # edge's notch_side control point, both sides)
    rings, info = frame_rings(gp)
    per = loop_per(gp)
    i_ear = int(np.sum(per[:ci("notch_side")])) if np.ndim(per) else int(per) * ci("notch_side")
    ear_l, ear_r = rings[2][i_ear], rings[2][len(rings[2]) - i_ear]
    # and its feet: where each leg meets the lower band's bottom edge (the outline edge, ring f, at the outer
    # outline's notch_side control point)
    foot_l, foot_r = rings[RING_EDGE][i_ear], rings[RING_EDGE][len(rings[RING_EDGE]) - i_ear]
    return dict(ICON=L.point(0.0, z_top + TAB_H - 0.002, lip_at(gp, 0.0) - band0)[0],     # on the tab (round 7)
                NOTCH=L.point(0.0, z_notch, lip_at(gp, 1.0) - band1)[0],
                POST_R=_post_head(L, -s_post, z_post), POST_L=_post_head(L, s_post, z_post),
                EAR_R=ear_r, EAR_L=ear_l, FOOT_R=foot_r, FOOT_L=foot_l)


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
    Co, Cu = outlines(gp, teeth=False)[:2]
    # round 12: from the frame's lens edge, moved out on the pillars, its hidden edge where it was (at least
    # SIDE_GROOVE_MIN under the frame): grown the full groove from the moved edge it reached 1.85 mm further out, into
    # the plate's inner face (0.9 mm, the plate turned straight back)
    foot = side_foot(gp, Co, Cu, outline_t(gp))[0]
    g = np.broadcast_to(np.asarray(grow, float), (len(Co),))
    g = np.maximum(g - np.linalg.norm(foot, axis=1), np.minimum(g, SIDE_GROOVE_MIN))
    Co = Co + foot
    return despike(untangle(Co + outward2d(Co) * g[:, None]))   # round 11: grow per sample too


def despike(P, max_turn=150.0):
    """Round 11: the closed loop P without spikes: points where it turns back by more than max_turn deg (the grown
    lens outline at the nose arch's inner corner went 0.37 mm out and back, an open seam in the lens)."""
    P = np.asarray(P)
    while True:
        u, v = P - np.roll(P, 1, 0), np.roll(P, -1, 0) - P
        c = (u * v).sum(1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-18)
        bad = np.nonzero(c < np.cos(np.radians(max_turn)))[0]
        if not len(bad):
            return P
        P = np.delete(P, bad[:1], 0)


def _tri_grid(lo, hi, h):
    gs, gz = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h * 0.866))
    gs = gs + (np.arange(gs.shape[0])[:, None] % 2) * h / 2
    return np.c_[gs.ravel(), gz.ravel()]


def sheet(L, poly, off, h=0.004, fine=None):
    """Triangulated region of the lens surface inside poly ((s, z) loop) at offset off: vertices, triangles
    (anticlockwise seen from the front), and the boundary vertex count (the first len(poly)). fine (s0, hf): a grid
    hf apart where |s| > s0 (round 12: the lens's curled-back ends)."""
    from scipy.spatial import Delaunay
    lo, hi = poly.min(0), poly.max(0)
    pts = _tri_grid(lo, hi, h)
    if fine is not None:
        pf = _tri_grid(lo, hi, fine[1])
        pts = np.vstack([pts[np.abs(pts[:, 0]) < fine[0] - 0.5 * h], pf[np.abs(pf[:, 0]) >= fine[0]]])
        h = fine[1]                                     # the outline clearance below: the fine spacing's
    o = H.Profile.__new__(H.Profile)
    o.outline = poly
    # round 11: grid points kept 0.4 h off the outline's edges, not only its points, and a triangle on three outline
    # points kept when its corners, taken in the outline's order, turn the outline's way (the centroid test is not
    # reliable on Delaunay's slivers along a gently concave run: the comb had 100 open edges, the outer lens 6); the
    # sheets are now closed solids
    A_, B_ = poly, np.roll(poly, -1, 0)
    E_ = B_ - A_
    dseg = np.full(len(pts), np.inf)
    for k in range(0, len(A_), 64):
        a, e = A_[k:k + 64], E_[k:k + 64]
        u = np.clip(((pts[:, None] - a[None]) * e[None]).sum(-1) / np.maximum((e * e).sum(-1), 1e-18)[None], 0, 1)
        dseg = np.minimum(dseg, np.linalg.norm(pts[:, None] - a[None] - u[..., None] * e[None], axis=-1).min(1))
    keep = H.Profile.inside(o, pts) & (dseg > 0.4 * h)
    P2 = np.vstack([poly, pts[keep]])
    T = Delaunay(P2).simplices
    nb = len(poly)
    ins = H.Profile.inside(o, P2[T].mean(1))
    Ts = np.sort(T, axis=1)
    bnd = Ts[:, 2] < nb
    if bnd.any():
        area = np.sum(poly[:, 0] * B_[:, 1] - B_[:, 0] * poly[:, 1])
        a, b, c = poly[Ts[bnd, 0]], poly[Ts[bnd, 1]], poly[Ts[bnd, 2]]
        cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
        ins[bnd] = cr * area > 0
        # on a straight run (the comb's densified sides) the slivers' turn is rounding noise: those are kept or
        # dropped while that mends the sheet's edges (each outline edge used once, every other edge twice or not)
        flat = np.nonzero(bnd)[0][np.abs(cr) < 1e-6 * np.maximum(
            np.linalg.norm(c - a, axis=1), np.linalg.norm(b - a, axis=1)) ** 2]
        if len(flat):
            key = (np.sort(np.stack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1), axis=2) @ [len(P2), 1])
            outl = set((np.minimum(np.arange(nb), (np.arange(nb) + 1) % nb) * len(P2)
                        + np.maximum(np.arange(nb), (np.arange(nb) + 1) % nb)).tolist())

            def faults(keep):
                u, n = np.unique(key[keep].ravel(), return_counts=True)
                ob = np.array([k in outl for k in u.tolist()], bool)
                return int(np.sum(np.where(ob, np.abs(n - 1), n % 2))) + len(outl) - int(ob.sum())
            best = faults(ins)
            for _ in range(3):
                for i in flat:
                    ins[i] = ~ins[i]
                    f_ = faults(ins)
                    if f_ < best:
                        best = f_
                    else:
                        ins[i] = ~ins[i]
    T = T[ins]
    a, b, c = P2[T[:, 0]], P2[T[:, 1]], P2[T[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    T[cr < 0] = T[cr < 0][:, ::-1]
    # (s, z) anticlockwise with s to his left = clockwise seen from the front (x left): flip to face forward
    T = T[:, ::-1]
    V = L.point(P2[:, 0], P2[:, 1], off(P2) if callable(off) else off)[0]     # off: a depth, or one per (s, z)
    return V, T, len(poly)


def closed_sheet(part, L, poly, off_front, off_back, mat_front, mat_back, mat_edge, h=0.004, fine=None):
    """A lens sheet as a closed solid: front, back (the same triangulation further back) and the edge strip. h: the
    inner grid's spacing (fine: see sheet)."""
    Vf, T, nb = sheet(L, poly, off_front, h, fine)
    Vb = sheet(L, poly, off_back, h, fine)[0]
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
    fine = (SIDE_LENS_S[0] - 0.004, 0.0015)             # round 12: the curled-back ends, 1.5 mm apart

    def at(d):
        return lambda P: d - lens_back(P[:, 0], P[:, 1])
    closed_sheet(lens, L, poly, at(0.0), at(-LENS_T), "goggle_lens_mirror", "goggle_lens_clear",
                 "goggle_lens_clear", fine=fine)
    poly_in = lens_region(gp, inner_grow(gp))
    closed_sheet(lens, L, poly_in, at(-(LENS_T + LENS_GAP)), at(-(LENS_T + LENS_GAP + LENS_IN_T)),
                 "goggle_lens_clear", "goggle_lens_clear", "goggle_lens_clear", fine=fine)
    return lens


POST_S, POST_Z = 0.0867, -0.0012   # tear-off posts near the lens's ends, at (+-s, z) on the lens: the stud heads
                                   # are landmarks in every goggle-alone photo (round 4: 87.5, -1.5 mm, fitted with
                                   # the shape; round 5: refitted on round 5's lens with its cameras fixed, iso55,
                                   # phy, phr: studs 1.8 mm off at most before, 1.0 after)


def post_sz(gp=None):
    """(s, z) of the tear-off post on his left (the right one mirrored); GP may override it with "post"."""
    p = (gp or GP).get("post")
    return (p[0], p[1]) if p is not None else (POST_S, POST_Z)


def _post_head(L, s0, zp):
    """The stud's head centre: POST_HEAD off the lens surface (the landmark fitted in every goggle-alone photo; round
    12 keeps it there while the lens under it curls back: the stud stands longer from its base)."""
    P, N = L.point(s0, zp, 0.0)
    return P + N * POST_HEAD


def post_frame(L, s0, zp):
    """The tear-off post's base on the lens at (s0, zp): point, normal, along s, up. Round 12: on the lens as built
    (lens_back: its ends curl back)."""
    def pt(s, z):
        return L.point(s, z, -lens_back(s, z))[0]
    P0 = pt(s0, zp)
    t = pt(s0 + 0.0005, zp) - pt(s0 - 0.0005, zp)
    t /= np.linalg.norm(t)
    up = pt(s0, zp + 0.0005) - pt(s0, zp - 0.0005)
    N0 = np.cross(t, up)
    N0 *= np.sign(N0 @ L.point(s0, zp, 0.0)[1]) / np.linalg.norm(N0)
    up = np.cross(N0, t)
    return P0, N0, t, up / np.linalg.norm(up)


def build_posts(gp=None):
    """Bare tear-off posts (Damien runs no tear-offs): a square boss on the lens and a round stud with a head."""
    gp = gp or GP
    L = LensSurface(gp)
    posts = H.Part("goggle_posts")
    sp, zp = post_sz(gp)
    for sg in (1, -1):
        P0, N0, t, up = post_frame(L, sg * sp, zp)
        # square boss 4.5 x 4.5 x 1.5 mm
        box = []
        for h, (a, b) in ((0, (-1, -1)), (0, (1, -1)), (0, (1, 1)), (0, (-1, 1)),
                          (1, (-1, -1)), (1, (1, -1)), (1, (1, 1)), (1, (-1, 1))):
            box.append(P0 + t * a * 0.00225 + up * b * 0.00225 + N0 * (0.0015 * h - 0.0002))
        quads = [[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        posts.add(np.array(box), quads, "goggle_post", [[(0.0, 0.0)] * 4] * 6)
        # stud 2.4 mm across, 2.5 mm long, head 3.4 mm. Round 12: from the base on the curled lens to the head at its
        # landmark (_post_head), the stem longer by the curl there
        ax = _post_head(L, sg * sp, zp) - P0
        ext = np.linalg.norm(ax) - POST_HEAD
        N0 = ax / np.linalg.norm(ax)
        t = t - N0 * (t @ N0)
        t /= np.linalg.norm(t)
        up = np.cross(N0, t)
        k = 12
        ang = np.linspace(0, 2 * np.pi, k, endpoint=False)
        rings = []
        for rr, hh in ((0.0012, 0.0013), (0.0012, 0.0033), (0.0017, 0.0036), (0.0017, 0.0042), (0.0008, 0.0045)):
            hh += ext if hh > 0.002 else 0.0
            rings.append(P0 + N0 * hh + rr * (np.cos(ang)[:, None] * t + np.sin(ang)[:, None] * up))
        ids = [posts.add(r, [], "goggle_post") + np.arange(k) for r in rings]
        for a_, b_ in zip(ids[:-1], ids[1:]):
            for i in range(k):
                j = (i + 1) % k
                posts.F.append([a_[i], a_[j], b_[j], b_[i]]); posts.M.append("goggle_post")
                posts.UV.append([(0.0, 0.0)] * 4)
        tip = posts.add((P0 + N0 * (0.0046 + ext))[None], [], "goggle_post")
        for i in range(k):
            j = (i + 1) % k
            posts.F.append([ids[-1][i], ids[-1][j], tip]); posts.M.append("goggle_post"); posts.UV.append([(0.0, 0.0)] * 3)
    return posts


OR_LEN, OR_T, OR_BACK_H = 0.030, 0.005, 0.059     # outrigger: length behind the frame, thickness, height at the
                                                 # strap end (Leatt ISO: 1.3 x the 45 mm strap beside it); round 8:
                                                 # 5 mm thick (rounds 1 to 7: 8), its back edge in the Pinata kit photo
                                                 # 10 px at 4.5 px/mm seen at 0.53: 4.2 mm (ledger section 10)


OR_TURN = 0.4                      # the outrigger turns out from the side face's backward line by atan(0.4) = 22 deg
                                   # towards the strap (Leatt ISO)
# round 9 (decision 45): each outrigger hinges on the frame's widest point (x 103.8, y 28.4 mm at mid height), as a
# plate that pivots on the frame would: in iso55 and phr Leatt's far plate stands out beyond the far pillar, which a
# plate starting where round 8's did (7.4 mm inside that point and 17 mm behind it) cannot do at any angle (ledger
# section 10). Its outer face's front edge on the hinge: with the inner one there, the plate stood 5 mm beyond the
# frame's side in Leatt's front photos at any turn (outline p90 1.3 to 1.4 mm became 3.6 to 3.9). OR_LEN long (Leatt
# ISO), it swings freely: each Leatt photo lays the strap its own way, so each free view has its own turn (the error
# table fits it per photo and side: ledger section 11); worn, the strap pulls it in until it rests on the shell.
OR_HINGE = True
# Round 12 (decision 53, item 2): the hinge OR_HINGE_IN inboard of that point and OR_HINGE_BACK behind it, inside the
# frame's side face, the plate shortened by as much (its back end, the strap's exit, stays). Leatt's frame side
# covers the plate's front: in iso55 (free) his pink side face starts at 920 px and ours at 950 (the plate outboard of
# the side face, which curves in from x 103.8 mm at the hinge to 93 to 97 behind it); in the Pinata iso-right (worn)
# his plate shows 762 to 840 px and his pink side 845 to 918, ours 760 to 889 over the frame's side (whose back edge
# projects at 845, as his). A comparison render with the goggle placed as on his empty helmet (12.6 mm lower, 3.5 mm
# back: the pink frames' best overlay) showed our plate wider still (745 to 870): shape, not place. Scanned (scratch
# orvis12.py, hingescan12.py; each plate turned so that its back edge stays where it is): inboard 3 mm hides the front
# to 920 / 934 / 952 px in iso55 (rows 880 / 980 / 1080) and 992 to 1018 in phr (Leatt about 1000), 6 mm to 918 to
# 944, more hides no more; the far plates stand as far beyond the frame as before (iso55 6 to 10 px, phr 36 to 40)
# at 64 and 76.5 deg. 3 mm back: from the widest point the plate's 5 mm crossed the lens's edge (x 97.1 mm at y 28.8,
# back to y 30.7) by 0.6 mm. Worn, the plate turns out 0 to 18.75 deg to rest on the shell (round 11: 10.75; 4 mm
# inboard needs 20.75). Round 13: rigid, 20.25 deg on phase 2's shell (outrigger_grids).
# Round 14 (decision 60, item 1): the pivot 4.84 mm inboard of that point and 4.36 mm AHEAD of it (OR_HINGE_BACK
# negative), the plate 31.1 mm from it to its back end (OR_LEN 26.8 behind the widest point): the joint fit of the C
# in the four far views and the near plate seen from outside (below, CAR_ON_PLATE). Round 12: 3 mm in, 3 mm back, 27.
OR_HINGE_IN = 0.00484
OR_HINGE_BACK = -0.00436
OR_LEN = 0.02678
OR_HINGE_LEN = OR_LEN - OR_HINGE_BACK   # m, hinge to the back end. 46 mm (to round 8's back end) showed the plate 197 px
                                   # wide between strap and frame in the Pinata iso-right (Leatt 69, round 8 157); 30
                                   # mm shows 115, and the strap fits his 07 at 4.2 mm rms (round 8 4.5)
OR_FREE_TURN = {1: 56.0, -1: 13.7}  # deg out from straight back, free, or {side: deg}: the far plate of the Pinata
                                   # goggle ISO (iso55, his SKU; IoU 0.972 against 0.968 at 0 to 40 deg); phr's is 65.
                                   # Round 12: 55 and 65 from the widest point; from the hinge OR_HINGE_IN inboard and
                                   # OR_HINGE_BACK back the same back edges need 64 and 76.5 (hingescan12.py).
                                   # Round 14: far 56.0 and near 13.7, solved with the C on the plate (CAR_ON_PLATE)
                                   # in iso55 (the far plate: the white ISO 55.9, phr 65.2, the Forge front 54.4;
                                   # the near plate one turn for iso55 and phr: at its stop, CAR_STOP_TURN, the C's
                                   # inner bar against the frame's side; round 12 read it at 6.0 to 6.25)

# Round 13 (decision 57, item 1): the strap carrier. In every Leatt front photo the piece beyond the frame's far end
# has the plates' colour (navy on the Blue and Royal ISO renders, red on the Forge Grey Rose, black on the rest): a C,
# its outer bar with two windows at the chassis slots' heights (the strap seen through them: teal in the Pinata ISO's
# lower window), its arms reaching in to the lens's end at the top and bottom with the strap seen in the gap between
# (phr, Forge front), a clear post on its outer edge at mid height (phr, Forge front; the ISO renders on white show
# none). In the ISO renders (iso55, his Pinata; the white ISO) it is seen face on where our frame's end face (ring 0 to
# 1, black, its slots round 12's stand-in for the windows) is: 1658 to 1703 px, the frame's end projecting 1658 to
# 1696. A C square to the plate on a pivot behind the frame's end (the rigid L: scratch isofit13.py, pose13.py) fits
# both ISO renders' C and near plate but stands behind the frame's front corner there (y 31 to 37 mm against the
# corner's 25 to 28): it rendered as a 10 px strip at 1690 to 1700 (scratch c1), and no pose of a rigid L puts the far
# C in front of the corner without the near plate covering the near frame's pink side (918 to 951 in iso55, Leatt's
# pink there). So the carrier is fixed on the frame's end, flat, in front of its end face (the strap between), and the
# plate swings on round 12's hinge behind it. Fitted through the ISO renders (scratch carmeas13.py, on the meshes):
# outer edge 1700 to 1705 / 1698 to 1701 px (Leatt 1703 / 1701), the windows rows 837 to 906 and 1025 to 1091 (830 to
# 900, 1025 to 1092), the bar 7.2 mm (38 px), the windows 0.17 to 0.83 across it, the inner end 1.1 mm inboard of the
# lens's end (the lens hides it: 1656 px). Not fitted: Leatt's Royal (phr) shows its C 13 mm wide, 1625 to 1677 px,
# standing 3 mm beyond the frame's end (1612) with the plate hidden behind it; ours reaches 1633. iso55 and phr cannot
# both hold: the two cameras see the far end from nearly the same side (a point moved so that iso55 sees no change
# moves 0.5 px a mm in phr), so his Royal's carrier and the Pinata CAD's differ. The Forge front (frg) agrees with
# phr. The back views (phyb) show it as a loop the strap wraps round; ours is a solid plate there (not built).
CAR = True
CAR_OFF = 0.0025                    # m, the C's back face off the frame's end face (the strap, STRAP_T, between)
CAR_T = 0.002                       # m, its wall
CAR_E = 0.0072                      # m, its outer edge along the end face from ring 0 (iso55 1703 px at the stand-off)
CAR_W = 0.0083                      # m, outer edge to inner end
CAR_BAR = 0.0072                    # m, the outer bar (the gap: the rest)
CAR_WIN = (0.17, 0.83)              # the windows across the bar from its outer edge, at CHASSIS_SLOTS' heights
CAR_ARM = 0.0045                    # m, its arms' height (top and bottom), Forge front 20 px of 330
CAR_CUT = (0.0020, 0.0223, -0.0298)  # m, its outer corners cut: along it, and the heights where the cuts meet the
                                    # outer edge (top, bottom). iso55 at 4x 1690,800 to 1700,822 px and 1700,1098 to
                                    # 1690,1122 (10 px at 5.26 a mm; rows 822 and 1098 at 5.32 a mm from the windows'),
                                    # the white ISO the same within 3 px
CAR_Z = (-0.0347, 0.0264)           # m, its bottom and top (GOGGLE z): iso55 rows 1124 and 800 at 5.32 px a mm from
                                    # the windows' (the white ISO 1125 and 797). Our frame's end face leans forwards
                                    # below its middle (5.6 mm ahead at the lower window's foot, z -29) and rounds
                                    # forwards above z 18 (7.7 mm at the top); below z -32 its front-outer corner turns
                                    # forwards into the lower band (9 mm ahead at -33.5, 14 at -34.5). The carrier is
                                    # flat (Leatt's bar reads one tone, 43, top to bottom), CAR_OFF in front of the
                                    # most the frame comes forwards over the windows' heights (car_frame "b0"; a mm
                                    # along its normal moves it 0.7 px out in iso55, 0.1 in phr), and runs up and
                                    # down as far as it clears the frame's corners by CAR_CLEAR: its top at 26.4, its
                                    # bottom at -32.3 (iso55 row 1113, Leatt's 1124: 2.4 mm short). Bowed with the
                                    # frame instead, its face tilted down 28 deg below the lower window and mirrored
                                    # the studio's low light (white, 250, against Leatt's 45)
CAR_CLEAR = 0.0003                  # m, the carrier's back face off the frame's corners at its top and bottom
CAR_POST = (0.0035, 0.0009, 0.0013)  # m, the clear post on the bar's outer edge, along it: length, stem, head radii

# Round 14 (decision 60, item 1): the C rides on the plate and swings with its turn. A C fixed on the frame cannot
# hold iso55 and phr at once (one C, one shared turn: 8.1 px rms against Leatt's lens post, phr 10 to 13 px off;
# scratch fitc14b.py). One C on the plate, the plate turned its own way in each photo (its strap lays it), fits the
# four front views together: the C's inner and outer front edges, its windows' inner edge, the silhouette beyond it
# and, in phr and the Forge front, the post's base and tip, 20 observations, each against the photo's lens post
# (the Forge front's camera spreads the two posts 12 % wide: scaled by them), 11 unknowns (scratch fitc14e.py with
# the plate as built, fitc14f.py): 1.41 px rms, at most 3.3 (the cameras' landmark rms 4.4 to 4.5), the turns 67.4
# (iso55), 67.3 (the white ISO), 79.3 (phr), 64.1 (the Forge front), round 12's hinge kept (the far views alone do
# not fix the pivot: any over x 92 to 106, y 23 to 38 mm fits at 1.1 to 2.2 px). Built so, the NEAR plate (iso55,
# phr, the Forge front: seen from outside, straight back) showed the C standing 2.4 mm proud of the plate, the front
# 14 mm open to the backdrop and the print on 13 mm, where Leatt's near plate is one flat printed face from its back
# edge (iso55 830, phr 930.5 px at mid height) to a front edge (909, 986) where a dark groove runs to the frame's
# rim, the print over 0.09 to 0.92 of it (scratch near14.py, rowprof14.py). Fitted jointly, the far views' 20
# observations and the near plate's back and front edges in iso55 and phr (24; scratch fitc14n2.py), the C's outer
# corner the front edge of a flat outer face that runs back to the plate's end, one near turn: the pivot slides
# along a valley (free, it runs inside the frame to x 85 mm); on the frame's side (pivgrid14.sh) round 12's hinge
# fits at 2.57 px rms (phr's E2 7 px off), the widest point 1.80 (4.8), x 97 y 28 1.50 (3.8, on the lens's edge),
# x 99 y 24 1.15 (3.1) with the near plate at 8.7 deg, where its C's inner bar stands 2.5 mm inside the frame's side
# (bounded at 15.5 deg, 1.2 mm; at 25 deg, the C refitted, still 1.2 mm: scratch fitc14n3.py, clear14.py). So the fit
# keeps the near C out of the frame and the face foam (scratch fitc14n4.py: the C's solid, its bar CAR_T thick, the
# windows open, sampled every 0.5 by 0.8 mm and looked up in the frame's signed distance, sdf14.py, each point
# deeper than -0.3 mm a residual of 4 px a mm), the near turn free: at x 99 y 24, 1.25 px rms, 3.6 at most (the
# Forge front's inner edge; the cameras' landmark rms 4.4 to 4.5), the near C 0.29 mm clear. Built, 4.8 mm inside
# the widest point and 4.4 ahead of it, the plate 31.1 mm long. Its far turns 56.0 (iso55), 55.9 (the white ISO),
# 65.2 (phr), 54.4 (the Forge front); the near 13.7, where the C's inner bar meets the frame's back rim (the built
# meshes, clear14.py: 16 points inside at 13.0 deg, 91 at 12, none from 13.7). phyb (no landmarks) is not fitted.
# From the plate's outer face front edge (the hinge): the C's front face's inner end CAR_Q along the plate and out
# (inboard: negative), the face turned CAR_PSI from square to the plate, CAR_PLATE_W across to its outer corner (0.2
# mm proud of the plate's face: the plate's front edge, OR_PLATE_FRONT), two windows over CAR_PLATE_WIN in from that
# corner (phr: 2 px of bar outside them), no gap (phr's bar runs whole from its inner edge, 1627 px, to the
# windows). The clear post stands on the plate's outer face CAR_POST_AT behind the C's front and out square to the
# plate (phr 1665 to 1700 px, the Forge front 1702 to 1735: base 2.7 mm, head 4.5 mm across, 12 px and 20 px in
# phr). Leatt's CAD (iso55, his SKU; the white ISO) has none, nor do his Pinata kit photos or
# the 2022 back photo (phyb: nothing beyond the bar, where ours stood 39 px out): built only for the Royal and the
# Forge photos (goggle.py --free ... post); his goggle, worn and free, has none.
CAR_ON_PLATE = True
CAR_TURNS = {"iso55": 55.99, "wiso": 55.88, "phr": 65.16, "frg": 54.38}   # deg, each photo's far plate (solved)
CAR_NEAR_TURN = 13.7                # deg, the near plate in iso55 and phr (solved: at its stop)
CAR_STOP_TURN = 13.7                # deg, the least turn of a plate: below it its C's inner bar runs into the frame's
                                    # back rim (z 13 to 23 mm, 0.3 mm deep at 13.0 deg). The free near plate rests on
                                    # it; worn, the plate turns out from it until it clears the shell
CAR_Q = (0.018221, -0.007988)       # m
CAR_PSI = 18.29                      # deg
CAR_PLATE_W = 0.008702              # m
CAR_PLATE_WIN = (0.0006, 0.005403)  # m in from the outer corner
CAR_POST_AT = 0.008439              # m along the plate behind the C's outer front corner
CAR_POST_PLATE = (0.00927, 0.00135, 0.00225)  # m: length from the plate's face (through the C's corner),
                                    # stem and head radii
# The C's windows' heights (GOGGLE z): Leatt's rows (iso55 830/900 and 1025/1092, the white ISO 832/903 and
# 1027/1092) back-projected onto the C's front face at each view's turn (scratch winz14.py: 7.72/21.08,
# -28.90/-16.12; 6.98/20.51, -29.03/-16.65 mm), the mean. On the frame's end (round 13) they took the chassis slots'
# (CHASSIS_SLOTS: 6.5/19.4, -28.5/-15.9), which on the plate puts the upper window 10 px low in iso55. His C's top
# and bottom back-project to 26.8/27.2 and -35.0/-35.3 mm (CAR_Z: 26.4, -34.7)
CAR_WIN_Z = [(0.0074, 0.0208), (-0.0290, -0.0164)]
# The outrigger's front, from the hinge to the C, is open but for an arm at the top and the bottom (phr: the
# background between them at rows 837 to 867 and 1060 to 1087, the strap at mid height, 1611 to 1627 px; the Forge
# front the same; phyb from behind: the arms, the frame's clips between them). Built: the printed plate starts
# OR_PLATE_FRONT along it from the hinge, so it runs from the C back to the strap (round 14's joint fit: from the
# C's outer corner); the arms CAR_ARM tall across the plate's thickness from CAR_ARM_FROM along it (the frame's side
# face is there: the hinge's knuckle not built) into the C. Behind the windows' outer part
# (beyond the strap's cut end, CAR_STRAP) a wall in the C's shade (Leatt's iso55: grey, 1683 to 1693 px, in the
# lower window; without it the studio's backdrop showed through).
OR_PLATE_FRONT = CAR_Q[0] - CAR_PLATE_W * math.sin(math.radians(CAR_PSI))   # 15.49 mm: the C's outer corner
OR_FACE_OUT = CAR_Q[1] + CAR_PLATE_W * math.cos(math.radians(CAR_PSI))      # 0.27 mm: the plate's outer face off the
# hinge, through the C's outer corner, as the joint fit has it (the near plate seen from outside and the far one's
# silhouette run flush from the corner to the back end; through the hinge, iso55's far edge stood 1 px inboard)
CAR_ARM_FROM = 0.0040


def plate_len(gp=None):
    """Round 14: the printed plate's length, from its front edge (OR_PLATE_FRONT along it from the hinge with the C on
    it, else the hinge) to its back end."""
    return (gp or GP).get("or_hinge_len", OR_HINGE_LEN) - (OR_PLATE_FRONT if CAR and CAR_ON_PLATE else 0.0)


def outrigger_frames(gp=None, turn=None):
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
    # the frame's depth at the outrigger's centre height on the pillar (round 7; before, at side_end, which then
    # moved down the straight pillar: GP's outline note)
    Cu, seg = (outlines(gp)[k] for k in (1, 3))
    m = (Cu[:, 0] > 0) & np.isin(seg, (ci("side_top"), ci("side_end")))
    o = np.argsort(Cu[m, 1])
    d_end = float(xs_at(gp, "depth", np.interp(zc, Cu[m, 1][o], outline_t(gp)[m][o])))
    if gp.get("or_hinge", 1.0 if OR_HINGE else 0.0):
        return hinged_frames(gp, zt, zb, zc, zbk, o_back_h, gp.get("or_free_turn", OR_FREE_TURN) if turn is None
                             else turn)
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


def hinge_points(gp=None, zc=None):
    """Each side's hinge: the frame's widest point (GOGGLE frame) within 4 mm of the outriggers' centre height."""
    R_ = np.vstack(frame_rings(gp)[0])
    out = {}
    for sg in (1, -1):
        m = (sg * R_[:, 0] > 0) & ((np.abs(R_[:, 2] - zc) < 0.004) if zc is not None else True)
        i = np.argmax(sg * R_[m, 0])
        out[sg] = R_[m][i]
    return out


def hinged_frames(gp, zt, zb, zc, zbk, o_back_h, turn_deg, length=None):
    """Round 9: outrigger_frames for plates hinged on the frame's widest point: the outer face's front edge a vertical
    line through the hinge (x, y), so that seen from the front the plate hides behind the frame's side (Leatt's front
    photos: nothing beyond the frame's widest point on the far side), the plate running back turned out by turn_deg
    (a number, or {side: deg})."""
    length = length or plate_len(gp)
    front = gp.get("or_hinge_len", OR_HINGE_LEN) - length                # round 14: the plate starts in the C
    hinges = hinge_points(gp, zc)
    h_in = gp.get("or_hinge_in", OR_HINGE_IN)
    h_back = gp.get("or_hinge_back", OR_HINGE_BACK)
    out = {}
    for sg in (1, -1):
        a = math.radians(turn_deg[sg] if isinstance(turn_deg, dict) else turn_deg)
        t = np.array([sg * math.sin(a), math.cos(a), 0.0])
        n = np.array([sg * math.cos(a), -math.sin(a), 0.0])       # outwards, square to the plate
        Hp = np.array([hinges[sg][0] - sg * h_in, hinges[sg][1] + h_back, zc])
        P0 = Hp + t * front                                         # the outer face's front edge
        if front > 0:                                               # round 14: through the C's outer corner
            P0 = P0 + n * OR_FACE_OUT
        if front > 0:                                               # round 14: in the C, as tall as the C
            zt, zb = CAR_Z[1], CAR_Z[0]
        C = np.array([P0 + [0, 0, zt - zc], P0 + [0, 0, zb - zc],
                      P0 + t * length + [0, 0, zbk - zc - o_back_h / 2], P0 + t * length + [0, 0, zbk - zc + o_back_h / 2]])
        box = np.vstack([C, C - n * OR_T])
        out[sg] = (box, P0 + t * (length - 0.004) + [0, 0, zbk - zc] - n * OR_T / 2, n)
    return out


OR_GAP = 0.0015            # m, a mounted outrigger's inner face off the shell (it rests on it, strap tension)
WORN_TURN = {}             # round 9: the worn plates' turns (deg), set by outrigger_grids(mount=...)
OR_BEND = math.tan(math.radians(60))   # steepest outward bend of a mounted outrigger (lift per length)
OR_ANCHOR = 0.010          # m, the strap's end sits this far inside the outrigger's back end (its buckle slot)
OR_NU, OR_NV = 13, 7       # grid of each outrigger face (along x up)
OR_CHAMFER = (0.002, 0.003)   # m, round 10: the plate's back corners cut at 45 deg (top, bottom): Leatt's near plate
                              # in iso55 and phr at 1:1, the back edge's top and bottom 1 to 1.5 mm in from the
                              # taper's lines over its last 2 to 3 mm (ledger section 12)
OR_FRONT_CUT = (0.0019, 0.0019)   # m, round 10: the front corners cut at 45 deg (top, bottom) back to round 9's,
                                  # where the frame hides them in Leatt's front photos (with GP's or_top_in, or_bot_in:
                                  # the taper's lines raised them 1.9 mm, and phw, ink and frg then saw them)


def or_u(nu=OR_NU, length=None):
    """The outrigger grid's columns along the plate (0 at its front edge, 1 at its back end): even, plus a column
    where each corner's cut starts (round 10), so that the cuts run straight."""
    length = length or plate_len()
    cuts = sorted({1.0 - c / length for c in OR_CHAMFER if c > 0} | {c / length for c in OR_FRONT_CUT if c > 0})
    u = np.linspace(0.0, 1.0, nu - len(cuts))
    keep = [x for x in u if all(abs(x - c) * length > 0.0005 for c in cuts)]
    return np.array(sorted(keep + cuts))


def shell_mount(prof):
    """For the goggle on the helmet: the half width an outrigger point (GOGGLE frame) must clear, i.e. the shell's
    outer surface where the point lies behind the eyeport's edge in the side view (helmet.py's profile), else 0
    (in the eyeport opening nothing is in the way)."""
    def need(Pg):
        Ph = g2h(Pg)
        ins = prof.inside(Ph[:, 1:])
        return np.where(ins, H.shell_hw(prof, Ph[:, 1], Ph[:, 2]) / _place(None)[3], 0.0)   # GOGGLE units
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
    hinged = (gp or GP).get("or_hinge", 1.0 if OR_HINGE else 0.0)
    length = plate_len(gp) if hinged else (gp or GP).get("or_len", OR_LEN)
    uu = or_u(nu, length)
    nu = len(uu)
    u = uu[:, None, None]
    v = np.linspace(0.0, 1.0, nv)[None, :, None]
    run = ((1.0 - uu) * length)[:, None]                  # m from each column to the back end
    cut_t, cut_b = (np.maximum(0.0, c - run) + np.maximum(0.0, cf - uu[:, None] * length)
                    for c, cf in zip(OR_CHAMFER, OR_FRONT_CUT))

    def bil(c):                           # corners: front-top, front-bottom, back-bottom, back-top
        top = (1 - u) * c[0] + u * c[3]
        bot = (1 - u) * c[1] + u * c[2]
        top[..., 2] -= cut_t              # round 10: the back corners chamfered (OR_CHAMFER)
        bot[..., 2] += cut_b
        return (1 - v) * bot + v * top
    frames = outrigger_frames(gp)
    rows = {}
    if hinged:
        # round 9: each row of the plate a straight line from the hinge, turned out by its own angle: free, all
        # OR_FREE_TURN (a flat plate); worn, the strap pulls the plate in until it rests on the shell (OR_GAP off it).
        # Round 13 (decision 57, item 2): the plate turns as one, by the largest turn any row needs (the shell's side
        # widens upwards: its top back corner meets it first). Rounds 9 to 12 twisted it (the turn growing from the
        # bottom row's need, 0, to the top's, 20.25 on phase 2's shell), and its back edge then leaned right going
        # down through Leatt's Pinata iso-right camera (+3.3 px a 100 rows over rows 860 to 980, the render's strap
        # edge 767 to 788) where Leatt's leans left (-10.8: 764 to 751, scratch edge13.py on the photo). Rigid, it
        # leans -6.5 at any turn. Placed as on his empty helmet (12.6 mm lower, 3.5 mm back) the plate meets no shell
        # (turn 0) and its back edge stands at 760 / 752 px (Leatt 764 / 751; at 20.25 deg 740 / 733). His 07 and 09
        # see the plate at 0.4 to 0.5 px a mm: twist and rigid differ there by 1 to 2 px, under the cameras' landmark
        # rms (2.2 and 8 px; scratch lean13c.py)
        def row(sg, a, j):
            box = outrigger_frames(gp, turn={1: a, -1: a})[sg][0]
            return bil(box[:4])[:, j], bil(box[4:])[:, j]
        free_t = (gp or GP).get("or_free_turn", OR_FREE_TURN)         # deg, or {side: deg} (each photo's strap
        turns = {sg: np.full(nv, float(free_t[sg] if isinstance(free_t, dict) else free_t))   # swings them its own way)
                 for sg in (1, -1)}
        if mount is not None:
            for sg in (1, -1):
                req = np.zeros(nv)
                a0 = CAR_STOP_TURN if CAR_ON_PLATE else 0.0       # round 14: never inside the C's stop
                for j in range(nv):
                    for a in np.arange(a0, 90.0, 0.25):
                        Gi_ = row(sg, a, j)[1]
                        need = mount(Gi_)
                        if not np.any((need > 0) & (np.abs(Gi_[:, 0]) < need + OR_GAP)):
                            break
                    req[j] = a
                turns[sg] = np.full(nv, float(req.max()))
            WORN_TURN.clear()
            WORN_TURN.update({sg: (round(float(t[0]), 2), round(float(t[-1]), 2)) for sg, t in turns.items()})
        for sg in (1, -1):
            rr = [row(sg, turns[sg][j], j) for j in range(nv)]
            rows[sg] = (np.stack([r[0] for r in rr], 1), np.stack([r[1] for r in rr], 1))
    for sg, (box, end, n) in frames.items():
        Go, Gi = rows[sg] if hinged else (bil(box[:4]), bil(box[4:]))
        if mount is not None and not hinged:
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
        i_a = float(np.interp(np.clip(1.0 - OR_ANCHOR / L, 0, 1), uu, np.arange(nu)))
        i0 = int(i_a)
        f = i_a - i0
        mid = 0.5 * (Go + Gi)[:, nv // 2]
        anchor = mid[i0] * (1 - f) + mid[min(i0 + 1, nu - 1)] * f
        out[sg] = (Go, Gi, anchor)
    return out


def build_outriggers(gp=None, mount=None, post=False):
    """Black outriggers, white vertical LEATT on the outer face (letter tops towards the strap; Leatt's ISO view
    and the Pinata kit photo, right side), one image half per side. mount: see outrigger_grids. Round 13: and the
    strap carriers (carrier_mesh)."""
    o = H.Part("goggle_outriggers")
    grids = outrigger_grids(gp, mount)
    for sg, (Go, Gi, anchor) in grids.items():
        nu, nv = Go.shape[:2]
        run = np.linalg.norm(Go[:, 0, :2] - Go[0, 0, :2], axis=1)    # the grid's columns along it (or_u)
        uu = run / run[-1]
        V = np.vstack([Go.reshape(-1, 3), Gi.reshape(-1, 3)])
        O = lambda i, j: i * nv + j                               # noqa: E731
        I = lambda i, j: nu * nv + i * nv + j                     # noqa: E731
        quads, mats, uvs = [], [], []
        h0, h1 = (0.0, 0.5) if sg > 0 else (0.5, 1.0)
        # outer face: texture u = height (h0 bottom .. h1 top) in its image half, v = along (0 front .. 1 back; the
        # grid's own columns, round 10)
        tex = lambda i, j: (h0 + (h1 - h0) * j / (nv - 1), float(uu[i]))   # noqa: E731
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
    if CAR:                                       # round 13: each with its strap carrier (round 14: on its plate)
        for sg in (1, -1):
            carrier_mesh(o, sg, car_frame_plate(grids[sg][0], sg, post) if CAR_ON_PLATE else car_frame(gp))
    return o


def car_frame(gp=None):
    """Round 13: the carrier's frame on side +1 (GOGGLE frame; side -1 mirrored): ring 0 (the lens's end) at the
    outriggers' centre height, c along the frame's end face out to ring 1 (plan), nrm its front normal, the
    outriggers' bottom and top heights."""
    gp = gp or GP
    zt = gp["out"][ci("top_corner")][1] - gp.get("or_top_in", 0.003)
    zb = gp["out"][ci("bot_corner")][1] + gp.get("or_bot_in", 0.003)
    zc = 0.5 * (zt + zb)
    rings, info = frame_rings(gp)
    Co = info["Co"]
    far = np.nonzero(Co[:, 0] > 0.07)[0]
    i = far[np.argmin(np.abs(Co[far, 1] - zc))]
    R0, R1 = rings[0][i].copy(), rings[1][i].copy()
    c = R1 - R0
    c[2] = 0.0
    c /= np.linalg.norm(c)
    nrm = np.array([c[1], -c[0], 0.0])
    nrm = -nrm if nrm[1] > 0 else nrm                          # forwards
    # the bow: at each height, how far the frame's front surface comes forwards (along nrm) of its end face at zc
    # over the carrier's width (and 1 mm either side): the frame rings' crossings of that height (each ring a
    # polyline over the stations), never back
    lo, hi = CAR_E - CAR_W - 0.001, CAR_E + 0.001
    zg = np.arange(CAR_Z[0] - 0.001, CAR_Z[1] + 0.0011, 0.0005)
    bow = np.zeros(len(zg))
    for r in rings:
        r = np.asarray(r)
        for i0 in far:
            if i0 + 1 not in far:
                continue
            A, B = r[i0], r[i0 + 1]
            if A[2] == B[2]:
                continue
            t = (zg - A[2]) / (B[2] - A[2])
            k = (t >= 0) & (t <= 1)
            X = A[None] * (1 - t[k, None]) + B[None] * t[k, None]
            e, d = (X - R0) @ c, (X - R0) @ nrm
            ok = (e > lo) & (e < hi)
            np.maximum.at(bow, np.nonzero(k)[0][ok], d[ok])
    # flat: it stands off by the most the frame comes forwards over the windows' heights (and 0.5 mm), and runs up and
    # down from there while the frame stays CAR_CLEAR behind its back face
    lo_w, hi_w = min(min(s) for s in car_slots()) - 0.0005, max(max(s) for s in car_slots()) + 0.0005
    b0 = float(bow[(zg >= lo_w) & (zg <= hi_w)].max())
    clear = bow <= b0 + CAR_OFF - CAR_CLEAR
    k0 = int(np.argmin(np.abs(zg - zc)))
    kb, kt = k0, k0
    while kb > 0 and clear[kb - 1]:
        kb -= 1
    while kt < len(zg) - 1 and clear[kt + 1]:
        kt += 1
    zb, zt = max(CAR_Z[0], float(zg[kb])), min(CAR_Z[1], float(zg[kt]))
    return dict(R0=R0, c=c, nrm=nrm, zb=zb, zt=zt, zc=zc, b0=b0, bow=(zg, bow))


def car_frame_plate(Go, sg, post=True):
    """Round 14: side sg's C on its plate (CAR_ON_PLATE), as car_frame's keys in side +1's coordinates (car_point
    mirrors): from the plate's outer face grid Go (outrigger_grids), its front edge at mid height (the hinge) and its
    direction there; the windows, width and post (or None) the C's own."""
    nv = Go.shape[1]
    m = np.array([sg, 1.0, 1.0])
    A, B = Go[0, nv // 2] * m, Go[-1, nv // 2] * m
    t = (B - A)[:2] / np.linalg.norm((B - A)[:2])
    n = np.array([t[1], -t[0]])                                # outwards (side +1)
    Hh = A[:2] - t * (OR_HINGE_LEN - plate_len()) - n * OR_FACE_OUT   # the hinge (pivot)
    ps = math.radians(CAR_PSI)
    E1 = Hh + CAR_Q[0] * t + CAR_Q[1] * n
    c = n * math.cos(ps) - t * math.sin(ps)                    # along its front face, out
    nrm = -(t * math.cos(ps) + n * math.sin(ps))               # its front normal
    E2 = E1 + c * CAR_PLATE_W
    R0 = E2 - c * CAR_E - nrm * (CAR_OFF + CAR_T)              # car_point(u 0, layer 0) is E2
    zc = float(A[2])
    pb = Hh + t * (float((E2 - Hh) @ t) + CAR_POST_AT) + n * OR_FACE_OUT   # on the plate's outer face
    return dict(R0=np.r_[R0, zc], c=np.r_[c, 0.0], nrm=np.r_[nrm, 0.0], zb=CAR_Z[0], zt=CAR_Z[1], zc=zc, b0=0.0,
                w=CAR_PLATE_W, bar=CAR_PLATE_W, win=CAR_PLATE_WIN, t=t, n=n, H=Hh, E1=E1, E2=E2,
                post=(np.r_[pb, zc], np.r_[n, 0.0], CAR_POST_PLATE) if post else None)


def car_bow(F, z):
    """The carrier's stand-off (m along nrm, beyond CAR_OFF) of the frame's end face at zc: flat, F["b0"]."""
    return F["b0"]


def car_point(sg, F, u, z, layer):
    """A point of side sg's carrier: u in from its outer edge, height z, layer 0 its front face, 1 its back."""
    X = F["R0"] + F["c"] * (CAR_E - u) + F["nrm"] * (car_bow(F, z) + CAR_OFF + CAR_T * (1.0 - layer))
    X[2] = z
    X[0] *= sg
    return X


def car_slots():
    """The carrier's two windows' heights (GOGGLE z): the chassis slots' (CHASSIS_SLOTS); round 14, on the plate,
    Leatt's (CAR_WIN_Z)."""
    return [tuple(sorted(z)) for z in (CAR_WIN_Z if CAR_ON_PLATE else CHASSIS_SLOTS)]


def _split(V, faces):
    """(V, faces) with each face given its own vertices: renders shade every face smooth, so a solid's hard edges
    need their vertices apart (the solid stays closed by position)."""
    V = np.asarray(V)
    out = np.vstack([V[f] for f in faces])
    k = np.cumsum([0] + [len(f) for f in faces])
    return out, [list(range(k[i], k[i + 1])) for i in range(len(faces))]


def _outward(V, faces):
    """faces turned so that the closed solid (V, faces) has its normals outwards (positive signed volume)."""
    V = np.asarray(V)
    vol = 0.0
    for f in faces:
        for k in range(1, len(f) - 1):
            vol += np.linalg.det(np.array([V[f[0]], V[f[k]], V[f[k + 1]]]))
    return faces if vol > 0 else [f[::-1] for f in faces]


def carrier_mesh(o, sg, F):
    """Round 13: side sg's strap carrier (CAR_*) added to part o: a C in front of the frame's end face, its outer bar
    CAR_BAR wide with two windows (car_slots), its arms reaching in to the lens's end at the top and bottom, its outer
    corners cut at 45 deg; a closed solid CAR_T thick (cells of a (u, z) grid, side walls where a solid cell meets an
    open one); and the clear post on the bar's outer edge at mid height, along the C."""
    zb, zt = F["zb"], F["zt"]
    slots = car_slots()
    bar, wid = F.get("bar", CAR_BAR), F.get("w", CAR_W)        # round 14: the C on the plate has its own
    w0, w1 = F.get("win") or tuple(CAR_BAR * f for f in CAR_WIN)
    cu = CAR_CUT[0]
    czt, czb = max(0.0, zt - CAR_CUT[1]), max(0.0, CAR_CUT[2] - zb)   # each cut's height
    U = sorted({0.0, w0, w1, bar, wid, cu})
    Zs = {zb, zb + CAR_ARM, zb + czb, zt - czt, zt - CAR_ARM, zt} | {z for sl in slots for z in sl}
    Zs = sorted(Zs | set(np.linspace(zb, zt, 28).tolist()))
    Zs = [z for k, z in enumerate(Zs) if k == 0 or z - Zs[k - 1] > 2e-4]

    def solid(i, k):
        uc, zc_ = 0.5 * (U[i] + U[i + 1]), 0.5 * (Zs[k] + Zs[k + 1])
        if w0 < uc < w1 and any(lo < zc_ < hi for lo, hi in slots):
            return False
        return not (uc > bar and zb + CAR_ARM < zc_ < zt - CAR_ARM)
    ids, V = {}, []

    def vid(i, k, layer):
        u, z = U[i], Zs[k]
        if u < cu:                                             # the outer corners' cuts: grid points there move onto
            z = min(max(z, zb + czb * (1 - u / cu)), zt - czt * (1 - u / cu))   # the cut (one vertex per position)
        key = (round(u * 1e7), round(z * 1e7), layer)
        if key not in ids:
            ids[key] = len(V)
            V.append(car_point(sg, F, u, z, layer))
        return ids[key]
    quads, mq = [], []
    nU, nZ = len(U) - 1, len(Zs) - 1
    PLATE, WALL = "goggle_outrigger", "goggle_slot"            # the walls round the windows and the gap: in their own
    for i in range(nU):                                        # shade (Leatt's iso55 windows 0 to 7 to their edges)
        for k in range(nZ):
            if not solid(i, k):
                continue
            quads.append([vid(i, k + 1, 0), vid(i + 1, k + 1, 0), vid(i + 1, k, 0), vid(i, k, 0)])   # front
            quads.append([vid(i, k, 1), vid(i + 1, k, 1), vid(i + 1, k + 1, 1), vid(i, k + 1, 1)])   # back
            mq += [PLATE, PLATE]
            if i == 0 or not solid(i - 1, k):                  # outer side
                quads.append([vid(i, k, 0), vid(i, k, 1), vid(i, k + 1, 1), vid(i, k + 1, 0)])
                mq.append(PLATE if i == 0 else WALL)
            if i == nU - 1 or not solid(i + 1, k):             # inner side
                quads.append([vid(i + 1, k, 0), vid(i + 1, k + 1, 0), vid(i + 1, k + 1, 1), vid(i + 1, k, 1)])
                mq.append(PLATE if i == nU - 1 else WALL)
            if k == 0 or not solid(i, k - 1):                  # below
                quads.append([vid(i, k, 0), vid(i + 1, k, 0), vid(i + 1, k, 1), vid(i, k, 1)])
                mq.append(PLATE if k == 0 else WALL)
            if k == nZ - 1 or not solid(i, k + 1):             # above
                quads.append([vid(i, k + 1, 0), vid(i, k + 1, 1), vid(i + 1, k + 1, 1), vid(i + 1, k + 1, 0)])
                mq.append(PLATE if k == nZ - 1 else WALL)
    faces, mats = [], []
    for q, m_ in zip(quads, mq):                               # cut corners: collapsed edges out, quads to triangles
        f = [v for k_, v in enumerate(q) if v != q[k_ - 1]]
        if len(set(f)) >= 3:
            faces.append(f)
            mats.append(m_)
    V, faces = _split(V, _outward(V, faces))
    o.add(V, faces, mats, [[(0.5, 0.5)] * len(f) for f in faces])
    if "H" in F:                                               # round 14: the arms, hinge to C, top and bottom
        m_ = np.array([sg, 1.0, 1.0])
        a1 = float((F["E1"] - F["H"]) @ F["t"]) + 0.0005       # into the C's front face at its inner end
        for z0, z1 in ((zb, zb + CAR_ARM), (zt - CAR_ARM, zt)):
            box = [np.r_[F["H"] + F["t"] * a + F["n"] * (b + OR_FACE_OUT), z] * m_ for z in (z0, z1)
                   for b in (-OR_T, 0.0)
                   for a in (CAR_ARM_FROM, a1)]
            quads = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
            Vb, Fb = _split(box, _outward(box, quads))
            o.add(Vb, Fb, "goggle_outrigger", [[(0.5, 0.5)] * 4] * 6)
    # the clear post: out of the bar's outer edge at mid height, along the C (phr 1662 to 1695 px, Forge front 1700
    # to 1725), a stem and a round head. Round 14: on the plate (F["post"]: base, direction, size), or none (None)
    zc = F["zc"]
    up = np.array([0.0, 0.0, 1.0])
    if "post" in F and F["post"] is None:
        return
    if "post" in F:
        m_ = np.array([sg, 1.0, 1.0])
        base, n, (ln, r0, r1) = F["post"][0] * m_, F["post"][1] * m_, F["post"][2]
    else:
        n = F["c"] * np.array([sg, 1.0, 1.0])
        base = car_point(sg, F, 0.0, zc, 0.5)
        ln, r0, r1 = CAR_POST
    t = np.cross(up, n)
    k = 10
    ang = np.linspace(0, 2 * np.pi, k, endpoint=False)
    rings = []
    for rr, hh in ((r0, -0.0005), (r0, ln - r1), (r1, ln - r1 * 0.7), (r1, ln), (r0 * 0.6, ln + r1 * 0.5)):
        rings.append(base + n * hh + rr * (np.cos(ang)[:, None] * t + np.sin(ang)[:, None] * up))
    Pp = np.vstack(rings + [base[None] - n * 0.0005, (base + n * (ln + r1 * 0.75))[None]])
    Fp = []
    for r in range(len(rings) - 1):
        for i in range(k):
            j = (i + 1) % k
            Fp.append([r * k + i, r * k + j, (r + 1) * k + j, (r + 1) * k + i])
    c0, c1 = len(rings) * k, len(rings) * k + 1
    for i in range(k):
        j = (i + 1) % k
        Fp.append([j, i, c0])
        Fp.append([(len(rings) - 1) * k + i, (len(rings) - 1) * k + j, c1])
    Fp = _outward(Pp, Fp)
    o.add(Pp, Fp, "goggle_post_clear", [[(0.0, 0.0)] * len(f) for f in Fp])


CAR_STRAP = (-0.0264, 0.0135, 0.0048)   # m: the strap's end behind the carrier, its bottom and top (z) and its cut
                                        # end in from the carrier's outer edge. Leatt's iso55 at 4x: the windows show
                                        # the strap dark (lum 3 to 30) with the chassis grey above it in the upper
                                        # window (rows 825 to 848 px: its top edge 13.5 mm) and below it in the lower
                                        # (from 1080: -26.4), its cut end a column of teal dots in the lower window
                                        # only (1679 to 1683 px, rows 1040 to 1076), the chassis grey beyond it (1683
                                        # to 1693). At 4.2 mm in ours showed at 1676 to 1681 (the strap 8 mm behind
                                        # the C's face): 3.4 puts it at Leatt's. Round 14, the C on the plate (the
                                        # strap 1.2 to 2.5 mm behind its face): at 3.4 it showed at 1689 (the white
                                        # ISO 1687), at 4.8 1683 (1681; scratch teal14.py)
CAR_STRAP_TEAL = 0.0008                 # m, the print's teal along the cut end (the rest of the face the strap's back)
CAR_STRAP_TEAL_Z = -0.0185              # m, ... up to this height (Leatt's rows 1040 to 1076: z -18.9 to -25.7 mm)


def build_strap_ends(gp=None, mount=None):
    """Round 13: the strap's ends threaded behind the carriers (Leatt's front photos see them through the windows and
    the gap: teal in the Pinata ISO's lower window, the strap in phr's and the Forge front's gap): a strip of strap
    (STRAP_T thick) between each carrier and the frame's end face, from the carrier's inner end to its cut end
    (CAR_STRAP), in the carrier's shade (goggle_strap_shade) but for the print's teal along the cut end in the lower
    window's rows (goggle_strap_teal)."""
    part = H.Part("goggle_strap_end")
    if not CAR:
        return part
    grids = outrigger_grids(gp, mount) if CAR_ON_PLATE else None   # round 14: behind the C on each plate
    ds = [(CAR_OFF + STRAP_T) / 2, (CAR_OFF - STRAP_T) / 2]          # front, back
    zs = np.array(sorted(set(np.linspace(CAR_STRAP[0], CAR_STRAP[1], 17).round(6)) | {CAR_STRAP_TEAL_Z}))
    nz = len(zs)
    for sg in (1, -1):
        F = car_frame_plate(grids[sg][0], sg) if CAR_ON_PLATE else car_frame(gp)
        es = [CAR_E - F.get("w", CAR_W) + 0.0003, CAR_E - CAR_STRAP[2] - CAR_STRAP_TEAL, CAR_E - CAR_STRAP[2]]
        V, idx = [], {}
        for a_, d in enumerate(ds):
            for b_, e in enumerate(es):
                for c_, z in enumerate(zs):
                    X = F["R0"] + F["c"] * e + F["nrm"] * (car_bow(F, z) + d)
                    X[2] = z
                    X[0] *= sg
                    idx[a_, b_, c_] = len(V)
                    V.append(X)
        q = lambda *k: [idx[t] for t in k]                     # noqa: E731
        faces, mats = [], []
        for c_ in range(nz - 1):
            teal = "goggle_strap_teal" if zs[c_ + 1] <= CAR_STRAP_TEAL_Z + 1e-9 else "goggle_strap_shade"   # its rows
            for b_ in range(2):
                faces += [q((0, b_, c_), (0, b_ + 1, c_), (0, b_ + 1, c_ + 1), (0, b_, c_ + 1)),    # front
                          q((1, b_, c_), (1, b_, c_ + 1), (1, b_ + 1, c_ + 1), (1, b_ + 1, c_))]    # back
                mats += [teal if b_ else "goggle_strap_shade", "goggle_strap_shade"]
            faces += [q((0, 0, c_), (0, 0, c_ + 1), (1, 0, c_ + 1), (1, 0, c_)),                   # inner end
                      q((0, 2, c_), (1, 2, c_), (1, 2, c_ + 1), (0, 2, c_ + 1))]                   # the cut end
            mats += ["goggle_strap_shade", teal]
        for b_ in range(2):
            faces += [q((0, b_, 0), (1, b_, 0), (1, b_ + 1, 0), (0, b_ + 1, 0)),                   # bottom
                      q((0, b_, nz - 1), (0, b_ + 1, nz - 1), (1, b_ + 1, nz - 1), (1, b_, nz - 1))]   # top
            mats += ["goggle_strap_shade"] * 2
        V, faces = _split(V, _outward(V, faces))
        part.add(V, faces, mats, [[(0.5, 0.5)] * len(f) for f in faces])
        if CAR_ON_PLATE:                          # round 14: the wall behind the windows' outer part, the C's shade
            e0, e1 = CAR_E - CAR_STRAP[2] + 0.0002, CAR_E - 0.0002
            z0, z1 = min(min(sl) for sl in car_slots()) - 0.001, max(max(sl) for sl in car_slots()) + 0.001
            box = []
            for z in (z0, z1):
                for d in (ds[1] - 0.0002, ds[1] - 0.0007):
                    for e in (e0, e1):
                        X = F["R0"] + F["c"] * e + F["nrm"] * (car_bow(F, z) + d)
                        X[2] = z
                        X[0] *= sg
                        box.append(X)
            quads = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
            Vb, Fb = _split(box, _outward(box, quads))
            part.add(Vb, Fb, "goggle_slot", [[(0.5, 0.5)] * 4] * 6)
    return part


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
    # round 14: on the plate as built (plate_len: from the C back), the letters at most 0.83 of its length (Leatt's
    # near plate in iso55, his SKU: the print over 0.09 to 0.92 of the face, 837 to 903 px of 830 to 909 at mid
    # height; scratch rowprof14.py)
    plen = plate_len() if (GP.get("or_hinge", 1.0 if OR_HINGE else 0.0)) else GP.get("or_len", OR_LEN)
    ch_m = min(0.80 * h_mid / wordmark_aspect(), 0.83 * plen)                # letter height, m
    L_ = ch_m * wordmark_aspect() / h_mid * w                               # text length in px (along u)
    ch = ch_m / plen * h                                                     # letter height in px (along v)
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


# Round 7: the nose guard as Leatt's photos show it (phy, phr: dark textured rubber filling the arch and hanging below
# it; the exploded view: a faceted nose cover, a clip loop on top). Its bottom edge back-projects to z -55.1 to -56.1
# in phy and phr (either depth guess), 34 to 35 mm wide there (the s values carry the depth's bias, the width does
# not); iso55 (from above) sees it only inside the arch, so it sits well behind the lower band. Ledger goggle.md
# section 9.
# GP["ng"]: [top z, bottom z, half width at the top, at the bottom, bottom corner radius, ridge offset from the lens
# front at the top (behind the frame's nose bridge) and at the bottom, how far the sides sweep back at the outer edges,
# rubber thickness]
NG_KEYS = ("top_z", "bot_z", "hw_top", "hw_bot", "corner", "front_top", "front_bot", "sweep", "thick")


def guard_clear(L, S, Z, skin_G, back):
    """How far (m, along the lens normal) each nose guard point (S, Z; back sheet at back behind the lens front) must
    come forward so the back clears his skin by 0.5 mm: the first skin along the normal within 2.5 mm."""
    tree = cKDTree(skin_G)
    P, N = L.point(S.ravel(), Z.ravel(), 0.0)
    push = np.zeros(len(P))
    for j in range(len(P)):
        idx = tree.query_ball_point(P[j], 0.04)
        if not idx:
            continue
        q = skin_G[idx] - P[j]
        along = -(q @ N[j])
        m = np.linalg.norm(q + np.outer(along, N[j]), axis=1) < 0.0025
        if m.any():
            push[j] = max(0.0, -along[m].min() + 0.0005 - back.ravel()[j])
    return push.reshape(S.shape)


def build_nose_guard(gp=None, skin_G=None):
    """The black flexible nose guard filling the nose arch and hanging below it (round 7, Leatt's phy, phr and the
    exploded view): a closed rubber shell, a rounded nose ridge whose sides sweep back, rounded bottom corners. On
    him (skin_G, GOGGLE frame) the rubber gives way to his nose: where its back would cut his skin it comes forward
    (the top corners, beside the bridge of his nose, by up to 7 mm)."""
    gp = gp or GP
    L = LensSurface(gp)
    ng = dict(zip(NG_KEYS, gp.get("ng", GP["ng"])))
    nu, nv = 25, 16
    v = np.linspace(0.0, 1.0, nv)
    z = ng["top_z"] + (ng["bot_z"] - ng["top_z"]) * v
    hw = ng["hw_top"] + (ng["hw_bot"] - ng["hw_top"]) * v
    c = ng["corner"]
    dz = np.clip((ng["bot_z"] + c - z) / c, 0.0, 1.0)     # the rounded bottom corners pull the sides in
    hw = hw - c * (1.0 - np.sqrt(np.clip(1.0 - dz ** 2, 0.0, 1.0)))
    u = np.linspace(-1.0, 1.0, nu)
    S = u[None, :] * hw[:, None]
    Z = np.repeat(z[:, None], nu, 1)
    W = (ng["front_top"] + (ng["front_bot"] - ng["front_top"]) * v)[:, None] - ng["sweep"] * u[None, :] ** 2
    if skin_G is not None:
        push = guard_clear(L, S, Z, skin_G, W - ng["thick"])
        sm = push.copy()                                            # eased into the rubber round it (one pass)
        sm[1:-1, 1:-1] = (push[1:-1, 1:-1] * 4 + push[:-2, 1:-1] + push[2:, 1:-1] + push[1:-1, :-2] +
                          push[1:-1, 2:]) / 8
        W = W + np.maximum(push, sm)
    g = H.Part("goggle_noseguard")
    sheets = []
    for off in (0.0, -ng["thick"]):
        P = L.point(S.ravel(), Z.ravel(), (W + off).ravel())[0]
        sheets.append(g.add(P, [], "goggle_noseguard"))
    vid = [o + np.arange(nu * nv).reshape(nv, nu) for o in sheets]
    q = [(0.0, 0.0)] * 4
    for i in range(nv - 1):
        for j in range(nu - 1):
            f = [vid[0][i, j], vid[0][i + 1, j], vid[0][i + 1, j + 1], vid[0][i, j + 1]]
            g.F.append(f); g.M.append("goggle_noseguard"); g.UV.append(q)
            g.F.append([vid[1][i, j], vid[1][i, j + 1], vid[1][i + 1, j + 1], vid[1][i + 1, j]])
            g.M.append("goggle_noseguard"); g.UV.append(q)
    ring = [(0, j) for j in range(nu)] + [(i, nu - 1) for i in range(1, nv)] + \
           [(nv - 1, j) for j in range(nu - 2, -1, -1)] + [(i, 0) for i in range(nv - 2, 0, -1)]
    for k in range(len(ring)):
        a_, b_ = ring[k], ring[(k + 1) % len(ring)]
        g.F.append([vid[0][a_], vid[0][b_], vid[1][b_], vid[1][a_]]); g.M.append("goggle_noseguard"); g.UV.append(q)
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
RIB_SINK = 0.0002                              # its back this far into the bridge (round 5's RIB_PROUD: see round 11)
RIB_BRIDGE_S = 0.030                           # the bridge behind the lens is black within this |s| (iso55)
# Round 10 (decision 48, item 4): seven tongues (an outer lobe, two fingers a side and the centre finger), the
# slots between them leaning outward, where rounds 5 to 9 had five upright tongues and a closed slot in each lobe
# (ledger goggle.md section 9, "Not matched", and section 12). Leatt's gaps back-projected onto the comb's front
# face (scratch combbp.py; phr and iso55, four gaps each) all lean the same way on both sides (ds/dz -0.08 to
# -1.30): a common shear plus an outward fan. Seen from his right a shear is depth (a point 1 mm deeper reads 0.75
# to 1.15 mm further to his right in phr, 0.94 to 1.45 mm in iso55): the tongues lean back towards his nose, about
# 0.40 mm a mm above z -29 mm, where the two views and the centre finger's two sides agree (combfit.py). That lean
# is not built: the frame's nose bridge lies 0.3 mm behind the comb's front (bridge_depth), so tips 5 mm deeper
# would sink behind it. The gaps are placed where that depth puts them (each view centred on s = 0 by the centre
# finger's pair, 3.8 and 2.1 mm, the cameras' calibration at the nose, as round 5's 3.6 mm). RIB_GAPS, from the
# centre out: the |s| and z of the centre of the gap's round bottom, its inner and outer sides' outward lean (ds/dz)
# and its width (the bottom's diameter). The two inner gaps have parallel sides (the two views' leans 0.15 to 0.27
# and 0.64 to 0.73). The outer one is a wedge open at its top (phr at 3x): the finger's outer side nearly upright
# (0.18: px 1333,1023 to 1348,1060), the lobe's inner side leaning 0.81 to the lobe's lower top corner.
RIB_GAPS = [(0.0039, -0.0246, 0.20, 0.20, 0.0024), (0.0130, -0.0250, 0.67, 0.67, 0.0024),
            (0.0254, -0.0284, 0.18, 0.81, 0.0012)]
# RIB_TOPS: per finger from the centre out, its top's z at its inner and outer corner; RIB_LOBE_TOP: the lobe's top
# corner z and then its top's (|s|, z) points out to its outer corner (|s| RIB_OUTER), down to the base there.
# phr's near side tops (combbp.py; depth hardly moves z, 0.02 mm a mm): -16.4; -16.6 to -17.1; -18.5 to -20.2;
# the lobe -23.5 to -23.9 at |s| 30 to 33, then falling to -28.5 at 41 (its outer end in the photo's crop).
RIB_TOPS = [(-0.0164, -0.0164), (-0.0167, -0.0171), (-0.0185, -0.0202)]
RIB_LOBE_TOP = (-0.0235, [(0.0330, -0.0239), (0.0410, -0.0286)])
RIB_OUTER = RIB_LOBE_TOP[1][-1][0]
RIB_CORNER = 0.0024                            # tip corner radius (Leatt's: about a third of a finger's width)
# Round 11 (decision 49, items 1 and 5): parts inside parts. Rounds 5 to 10 put the comb's flat front 0.3 mm in front
# of the frame's nose bridge, 2.2 mm behind the lens front: between the outer lens and the inner one at the centre and
# 0.3 mm into the inner lens (2.8 to 3.4 mm) further out. The bridge itself was folded: at the nose the frame's back
# face (2.1 to 3.3 mm deep, the fitted depth) lay in front of its plate behind the lens stack (3.9 mm), so the frame
# closed round the inner lens's edge there (overlap.py: the inner lens 1.5 mm inside the frame, the nose foam 0.9 mm
# inside the inner lens). Leatt's exploded view (no lens) shows the slotted surface at the nose starting at the lens's
# seat and sweeping back towards the face: the comb stands behind the whole lens stack. So its front is RIB_LENS_CLEAR
# behind the inner lens's back and leans back as Leatt's tongues do (RIB_LEAN: round 10's 0.40 mm a mm above z -29 mm,
# phr and iso55, combfit.py; the knee rounded), and the frame's bridge stands behind it (nose_back): its plate where
# the comb's back sinks RIB_SINK in, its back face BRIDGE_T behind that, both following the lean (item 5: the bridge
# moved back by the lean Leatt's photos show, up to 7 mm at the face opening's top).
# On him there is no room for that bridge over his nose ridge at the goggle's place (PLACE, decision 47's): his skin
# lies 3.2 mm behind the lens front at s 0, z -34 mm, 3.5 at the window's bottom edge and 4.7 at z -28 (skinsurf.py,
# ray casts on his mesh), where the lens stack, the comb and a plate need 5.8 mm. The worn build (notch) opens the
# face opening down to the window over his nose ridge (|s| under NOSE_NOTCH[0], eased back by NOSE_NOTCH[1]) and keeps
# the band there at its fitted depth; the comb's tongues stand free there and give way to his nose (rib_clear). The
# goggle alone keeps Leatt's bridge. Where the band is no deeper than the inner lens's back (the nose) the inner lens
# stops INNER_NOSE inside the window instead of running into the groove (inner_grow).
STACK_BACK = LENS_T + LENS_GAP + LENS_IN_T     # m, the inner lens's back behind the lens front (3.4 mm)
RIB_LENS_CLEAR = 0.00015                       # the comb's front this far behind it
RIB_T = 0.0010                                 # the comb's thickness where nothing stands behind it
RIB_LEAN = (0.40, -0.029, 0.0015)              # depth per height above z -29 mm; the knee's softness (softplus), m
BRIDGE_T = 0.0012                              # the bridge's thickness behind the comb (plate to back face)
BRIDGE_ZONE = (0.060, 0.008)                   # |s| where the plate eases back to the lens stack's, and over how much
NOSE_NOTCH = (0.008, 0.014)                    # worn: no bridge inside the first |s| (lens edge), eased by the second
# Joint front fit (decision 47): with the helmet on his head from the liner build-up and the goggle back on his face
# (PLACE) his nose ridge lies 8.6 mm behind the lens front at s 0 (z -31 mm; 9.2 at z -34), more than the 5.8 mm the
# lens stack, the comb and the plate need: the worn frame keeps Leatt's bridge (WORN_NOTCH False). True: round 11's.
WORN_NOTCH = False
INNER_NOSE = -0.0003                           # the inner lens's edge where the band is too thin: inside the window


def rib_depth(z):
    """The comb's front depth behind the lens front (m, > 0) at height z: RIB_LENS_CLEAR behind the inner lens's back,
    leaning back above RIB_LEAN's knee (a softplus: C-infinity, so the frame's rings that follow it stay fair)."""
    k, z0, e = RIB_LEAN
    return STACK_BACK + RIB_LENS_CLEAR + k * e * np.logaddexp(0.0, (np.asarray(z, float) - z0) / e)


def _smooth01(a):
    a = np.clip(a, 0.0, 1.0)
    return a * a * (3 - 2 * a)


def nose_back(Co, Ci, d, notch=False):
    """Round 11: the frame's back rings (frame_rings' l, m and n) round the nose, per outline sample: the face
    opening and the depths of l (the back face's inner edge), m (the plate's top, at the face opening) and n (the
    plate's bottom, at the lens edge). On the lower band the plate stands where the comb's back sinks RIB_SINK into it
    (rib_depth + RIB_T - RIB_SINK at the ring's height), easing back to the lens stack's 3.9 mm by BRIDGE_ZONE, and
    the back face's inner edge at least BRIDGE_T behind it (a smooth max with the fitted depth d). notch (worn): over
    his nose ridge the face opening comes down to the lens edge and the rings keep the band's fitted depth."""
    stack = STACK_BACK + 0.0005
    s, low = np.abs(Co[:, 0]), Co[:, 1] < 0
    zone = 0.5 * (1 - np.tanh((s - BRIDGE_ZONE[0]) / BRIDGE_ZONE[1])) * low
    if notch:
        wn = _smooth01((NOSE_NOTCH[1] - s) / (NOSE_NOTCH[1] - NOSE_NOTCH[0])) * low
        Ci = Ci + (Co - Ci) * wn[:, None]

    def plate(z):
        return rib_depth(z) + RIB_T - RIB_SINK
    dn = stack + zone * (plate(Co[:, 1]) - stack)
    dm = stack + zone * (plate(Ci[:, 1]) - stack)
    g = dm + BRIDGE_T - d
    dl = d + zone * 0.5 * (g + np.sqrt(g * g + 0.0005 ** 2))
    if notch:
        wd = _smooth01((NOSE_NOTCH[0] - s) / 0.003) * low                # the notch's sides: 3 mm, where Ci is Co
        # in the notch l, m and n stand on the lens edge's wall 0.1 mm apart (coincident rings fold the mesh)
        dl, dm, dn = (v + (d - k * 0.0001 - v) * wd for v, k in ((dl, 0), (dm, 1), (dn, 2)))
    return Ci, dl, dm, dn


def inner_grow(gp):
    """Round 11: how far the inner lens runs under the frame per lens-edge sample: LENS_GROOVE less 1.5 mm where the
    band is deep enough to hold it (3.9 mm and more), INNER_NOSE (inside the window) where the band is no deeper than
    the inner lens's back (the nose), smoothly between."""
    d = xs_at(gp, "depth", outline_t(gp))
    return INNER_NOSE + (LENS_GROOVE - 0.0015 - INNER_NOSE) * _smooth01((d - STACK_BACK) / 0.0005)


def rib_fillet(P, corners, r, n=6):
    """The closed (s, z) loop P with each vertex index in corners replaced by an arc of radius r tangent to both
    edges (its tangent run capped at 0.45 of the shorter edge)."""
    out = []
    for i in range(len(P)):
        if i not in corners:
            out.append(P[i])
            continue
        p, a, b = P[i], P[i - 1], P[(i + 1) % len(P)]
        u, v = (a - p) / np.linalg.norm(a - p), (b - p) / np.linalg.norm(b - p)
        th = np.arccos(np.clip(u @ v, -1.0, 1.0))
        d = min(r / np.tan(th / 2), 0.45 * min(np.linalg.norm(a - p), np.linalg.norm(b - p)))
        rr = d * np.tan(th / 2)
        c = p + (u + v) / np.linalg.norm(u + v) * rr / np.sin(th / 2)
        p0, p1 = p + u * d - c, p + v * d - c
        a0, a1 = np.arctan2(p0[1], p0[0]), np.arctan2(p1[1], p1[0])
        da = (a1 - a0 + np.pi) % (2 * np.pi) - np.pi
        out += [c + rr * np.array([np.cos(a0 + da * k / n), np.sin(a0 + da * k / n)]) for k in range(n + 1)]
    return np.array(out)


def rib_side(g, sgn):
    """A gap's side line s(z): sgn -1 its inner side, +1 its outer (g one of RIB_GAPS, |s| > 0), tangent to its
    round bottom."""
    sb, zb, qi, qo, w = g
    q = qi if sgn < 0 else qo
    return lambda z: sb + q * (z - zb) + sgn * 0.5 * w * np.hypot(1.0, q)


def rib_outline(gp, step=0.00025, bd=None):
    """The comb's outline, a closed (s, z) loop, and the indices of its corners to round: the seven tongues' tops,
    the leaning slots between them with round bottoms, the lobes' outer sides and the base (rib_base) under them.
    bd: the frame's bridge_depth (the goggle alone's by default)."""
    base = rib_base(gp, bd)
    right, corners = [], []
    for k, (zt0, zt1) in enumerate(RIB_TOPS):
        if k > 0:                                  # the finger's inner corner on the last gap's outer side
            corners.append(len(right))
            right.append([rib_side(RIB_GAPS[k - 1], +1)(zt0), zt0])
        corners.append(len(right))                 # its outer corner
        right.append([rib_side(RIB_GAPS[k], -1)(zt1), zt1])
        sb, zb, qi, qo, w = RIB_GAPS[k]            # the gap's round bottom, from its inner side to its outer
        for th in np.linspace(np.arctan2(qi, -1.0), np.arctan2(-qo, 1.0) + 2 * np.pi, 9):
            right.append([sb + 0.5 * w * np.cos(th), zb + 0.5 * w * np.sin(th)])
    zl, pts = RIB_LOBE_TOP
    corners += list(range(len(right), len(right) + 1 + len(pts)))
    right.append([rib_side(RIB_GAPS[-1], +1)(zl), zl])
    right += [list(p) for p in pts]
    sb_ = np.arange(RIB_OUTER, -1e-9, -step)
    right = np.vstack([right, np.c_[sb_, base(sb_)]])
    left = right[::-1].copy()
    left[:, 0] *= -1
    loop = np.vstack([right, left[1:]])            # clockwise seen from the front (s to his left), as round 5's
    m = len(right)
    return loop, sorted(set(corners) | {2 * m - 2 - c for c in corners})


def rib_base(gp, bd=None):
    """The comb's bottom edge z(s): 4 mm under the lens opening, but not below the nose arch's top (out loop). Round
    11: and only as far down as the band holds it (its back, RIB_T behind its front, 0.2 mm inside the band's back
    face, bd's first surface there); where the band is too thin from the lens edge down (the worn build's notch) it
    stops 0.4 mm above the lens edge, clear of the face foam under it."""
    Co, Cu = outlines(gp, teeth=False)[:2]
    lo = Co[(Co[:, 1] < 0) & (np.abs(Co[:, 0]) < 0.05)]
    lo = lo[np.argsort(lo[:, 0])]
    arch = Cu[(Cu[:, 1] < 0) & (Cu[:, 1] > -0.045) & (np.abs(Cu[:, 0]) < 0.015)]
    arch = arch[np.argsort(arch[:, 0])]
    bd = bd or bridge_depth(gp)
    sg = np.arange(-0.0005, RIB_OUTER + 0.001, 0.0005)
    zc = np.interp(sg, lo[:, 0], lo[:, 1])
    z0 = np.maximum(zc - 0.004, np.interp(sg, arch[:, 0], arch[:, 1], left=-1.0, right=-1.0))
    dz = np.arange(0.00025, 0.004 + 1e-9, 0.00025)
    Z = zc[None] - dz[:, None]
    ok = bd(np.broadcast_to(sg, Z.shape), Z) >= rib_depth(Z) + RIB_T + 0.0002
    run = np.cumprod(ok, axis=0).sum(0)                               # samples held from the lens edge down
    zb = np.where(run > 0, np.maximum(zc - dz[np.maximum(run - 1, 0)], z0), zc + 0.0004)

    def f(s):
        return np.interp(np.abs(np.asarray(s, float)), sg, zb)
    return f


def bridge_depth(gp, notch=False, plate=False):
    """Depth behind the lens front (m, > 0) of the first frame surface a ray from the front meets at (s, z) near the
    nose (Moller-Trumbore against the frame's triangles there; the worn build's frame with notch); round 11: inf where
    it meets none; plate: the plate behind the lens only (frame_rings' m to n), the surface the comb's back is moulded
    into (on the full frame a ray just past the plate's top edge met the back face behind it, 1.2 mm deeper)."""
    L = LensSurface(gp)
    if plate:
        rings = frame_rings(gp, notch=notch)[0]
        V = np.vstack([rings[RING_BACK_IN + 1], rings[RING_BACK_IN + 2]])
        m = len(rings[0])
        i = np.arange(m)
        j = (i + 1) % m
        T = np.r_[np.c_[i, j, m + j], np.c_[i, m + j, m + i]]
    else:
        fr = build_frame(gp, notch)[0]
        V = np.asarray(fr.V)
        T = np.array([[f[0], f[i], f[i + 1]] for f in fr.F for i in range(1, len(f) - 1)])
    c = V[T].mean(1)
    T = T[(np.abs(c[:, 0]) < 0.05) & (c[:, 2] < -0.005) & (c[:, 2] > -0.07)]
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1, e2 = B - A, C - A
    nrm = np.cross(e1, e2)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1), 1e-30)[:, None]
    dflt = np.inf

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
            # round 11: not the walls along the rays (the bridge's top edge face), met at a graze
            hit = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0.0005) & (np.abs((nrm[None] * d).sum(-1)) > 0.25)
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


# Round 11, merged on helmet round 3 (its shell moves the goggle 3.9 mm down his face, his nose 3.2 mm further back
# behind the lens): the comb's tongue at |s| 8 mm now stands whole beside the worn notch, and there the plate it is
# moulded into lies up to 0.8 mm shallower than its nominal depth: the frame's ring samples either side of the notch's
# side (s 6.72 and 9.58 mm) interpolate a corner of plate from the ramp's 3.6 mm to the nominal 4.42 mm. Where that
# corner stood less than 0.3 mm behind the comb's back sinking point the back stayed RIB_T behind the front (0.3 mm
# into the plate), and where it held, the back jumped by up to 0.38 mm at the plate's top edge, smeared 0.35 mm into
# the plate by the comb's 1 mm sheet grid. So the comb is held wherever the plate stands RIB_T_MIN (less RIB_SINK)
# behind its front, and the free back eases towards the held one near the plate: by the plate's deficit below its
# nominal depth, less RIB_EASE[1] per unit distance from it (a cone dilation on a RIB_EASE[0] grid). Where the plate is
# at its nominal depth (the goggle alone, and the worn bridge away from the notch) the deficit is nought: no change.
RIB_T_MIN = 0.0003                             # the comb's least thickness where the plate holds it
RIB_EASE = (0.00025, 0.30)                     # m grid; the ease's fall per unit distance from the held plate


def rib_front(gp, bd=None):
    """Round 11: the comb's front and back depths behind the lens front (m, > 0) as functions of (s, z). The front
    is rib_depth (behind the inner lens, leaning back). In the lens window the back sinks RIB_SINK into the frame's
    plate behind the lens where that stands behind (bd: bridge_depth with plate), and lies RIB_T behind the front where
    nothing does (the worn build's notch, the face opening), eased towards the plate near its edge where the plate
    lies shallower than its nominal depth (RIB_EASE); in the band under the window (the comb's root) RIB_T behind the
    front, inside the band."""
    from matplotlib.path import Path
    from scipy.interpolate import RegularGridInterpolator
    bd = bd or bridge_depth(gp, plate=True)
    win = Path(outlines(gp, teeth=False)[0])

    def front(s, z):
        s, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(z, float))
        return rib_depth(z)

    def held_back(s, z):
        f, b = front(s, z), bd(s, z)
        inw = win.contains_points(np.c_[s.ravel(), z.ravel()]).reshape(s.shape)
        return f, b, inw & np.isfinite(b) & (b > f + RIB_T_MIN - RIB_SINK)

    h, k = RIB_EASE                                 # the deficit (nominal less held back), cone-dilated on a grid
    sg = np.arange(-RIB_OUTER - 0.004, RIB_OUTER + 0.004 + 1e-9, h)
    zg = np.arange(-0.042, -0.012 + 1e-9, h)
    S, Z = np.meshgrid(sg, zg, indexing="ij")
    f, b, held = held_back(S, Z)
    dfc = np.where(held, np.maximum(f + RIB_T - (b + RIB_SINK), 0.0), 0.0)
    r = int(np.ceil((RIB_T - RIB_T_MIN) / k / h))   # the largest deficit (the held test's) runs out there
    pad = np.pad(dfc, r)
    D = dfc.copy()
    for i in range(-r, r + 1):
        for j in range(-r, r + 1):
            dist = math.hypot(i, j) * h
            if 0 < dist <= r * h:
                D = np.maximum(D, pad[r + i:r + i + len(sg), r + j:r + j + len(zg)] - k * dist)
    ease = RegularGridInterpolator((sg, zg), D, bounds_error=False, fill_value=0.0)

    def back(s, z):
        s, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(z, float))
        f, b, held = held_back(s, z)
        e = ease(np.c_[s.ravel(), z.ravel()]).reshape(s.shape)
        return np.where(held, b + RIB_SINK, f + RIB_T - e)
    return front, back


def build_nose_ribs(gp=None, skin_G=None):
    """The nose-bridge comb (frame plastic). On him (skin_G, GOGGLE frame) the flexible tongues give way to his
    nose: the comb is cut 0.5 mm short of his skin (rib_clear per column of s; the cut outline is the level line of
    the comb's signed distance and the clearance), and parts his nose fills are left out (the comb bends flat
    there; behind the mirror lens nothing of it shows)."""
    gp = gp or GP
    L = LensSurface(gp)
    notch = WORN_NOTCH and skin_G is not None                        # round 11: on him, the worn frame's (its notch)
    fr_, bk_ = rib_front(gp, bridge_depth(gp, notch, plate=True))

    def front(P2):
        return -fr_(P2[:, 0], P2[:, 1])

    def back(P2):
        return -bk_(P2[:, 0], P2[:, 1])
    loop, corners = rib_outline(gp, bd=bridge_depth(gp, notch))
    polys = [rib_dense(rib_fillet(loop, corners, RIB_CORNER))]
    if skin_G is not None:
        s = np.round(np.arange(-RIB_OUTER, RIB_OUTER + 1e-9, 0.00025), 6)
        clear = rib_clear(L, s, skin_G, lambda s_, z_: float(bk_(s_, z_)))
        # round 11: no repeated points and no edge over 0.25 mm (a 21 mm straight side left an open seam)
        polys = [rib_dense(despike(p[np.r_[True, np.linalg.norm(np.diff(p, axis=0), axis=1) > 1e-9]]))
                 for p in rib_cut(polys[0], s, clear)]
    g = H.Part("goggle_noseribs")
    for poly in polys:
        # round 11: one moulding in one satin finish (goggle_comb), its side walls too: the grey round the tongues in
        # phr is the bridge behind them, not the tongues' sides. A 1 mm inner grid (4 mm triangles sagged 0.2 mm off
        # the bridge they are moulded into)
        closed_sheet(g, L, poly, front, back, "goggle_comb", "goggle_comb", "goggle_comb", h=0.001)
    return g


def rib_cut(poly, s, clear, h=0.0001):
    """The parts of the (s, z) loop poly under clear(s) (rib_clear's columns), as loops: the zero level line of
    min(signed distance to poly, clear - z) on an h grid (contourpy). Parts under 0.8 mm across are dropped."""
    import contourpy
    from matplotlib.path import Path
    lo, hi = poly.min(0) - 0.001, poly.max(0) + 0.001
    S, Z = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h))
    P = np.c_[S.ravel(), Z.ravel()]
    A, B = poly, np.roll(poly, -1, 0)
    d = np.full(len(P), np.inf)
    for k in range(0, len(A), 64):
        a, e = A[k:k + 64], B[k:k + 64] - A[k:k + 64]
        t = np.clip(((P[:, None] - a[None]) * e[None]).sum(-1) / np.maximum((e * e).sum(-1), 1e-18)[None], 0, 1)
        d = np.minimum(d, np.linalg.norm(P[:, None] - a[None] - t[..., None] * e[None], axis=-1).min(1))
    d = np.where(Path(poly).contains_points(P), d, -d)
    c = np.interp(P[:, 0], s, np.where(np.isfinite(clear), clear, np.where(clear > 0, 1.0, -1.0)))
    F = np.minimum(d, c - P[:, 1]).reshape(S.shape)
    lines = contourpy.contour_generator(S, Z, F).lines(0.0)
    out = []
    for ln in lines:
        ln = ln[:-1]
        if len(ln) > 8 and np.ptp(ln[:, 0]) > 0.0008 and np.ptp(ln[:, 1]) > 0.0008:
            area = np.sum(ln[:, 0] * np.roll(ln[:, 1], -1) - np.roll(ln[:, 0], -1) * ln[:, 1])
            out.append(ln[::-1] if area > 0 else ln)          # clockwise, as rib_outline's
    return out


def rib_dense(P, h=0.00025):
    """The closed loop P with no edge longer than h: sheet's Delaunay then keeps to the outline along the slots'
    long straight sides."""
    out = []
    for a, b in zip(P, np.roll(P, -1, 0)):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / h)))
        out += [a + (b - a) * k / n for k in range(n)]
    return np.array(out)


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
# Round 8 (decision 43): a uniform scale, the fourth number, about the GOGGLE origin (the lens front). The goggle-alone
# photos fix the shape, not the size (section 7, "Scale"). On the helmet, at the helmet's own scale (the 45 mm strap
# in Leatt's MY27 side view, helmet.py, confirmed by his bike's 1483 mm wheelbase in his 07), Leatt's MY27 right view
# reads the frame 3.9 mm taller than round 7's 100 mm and Leatt's Pinata Teal iso-right (his helmet and goggle) 1 to
# 6 mm taller; the goggle-alone photos' 45 mm strap reads ours 0 to 6 % too large; his own photos (2.3 mm a pixel)
# cannot tell. His face and the eyeport decide: x 1.02 is the largest that keeps his nose bridge off the frame and
# the lens out of the eyeport's edge, with the goggle 0.5 mm higher (x 1.03 touches his skin, x 1.04 puts the lens
# into the shell at any fore-aft place). Not moved fore-aft: the kit views' 8 to 9 mm are an empty helmet (no face
# pushing the goggle forward) and back from here his nose bridge meets the frame. Ledger goggle.md section 10.
# Joint front fit (decision 47): the helmet now sits on his head from the liner build-up (helmet.fit_on_head), 4.6 mm
# further forward of his eyes along the goggle's axis and 2.7 mm higher than round 11's (lens centre 60.8 mm ahead of
# his eye centres against 56.2). The goggle rides his face, not the shell: moved back by those 4.6 mm, the lens
# centre is 56.2 mm ahead of his eyes again and the foam meets his face (it stood at least 8 mm off it). Not raised:
# Leatt's MY27 side views have its beak bottom at -64.6 to -66 mm (here -64) and Leatt's Pinata iso-right through
# the solved camera has the goggle lower still. Back 4.6 mm also brings the frame's top front to Leatt's side views'
# -149 mm (round 5: -152). His nose ridge then lies 8.6 to 9.2 mm behind the lens front at s 0, z -31 to -34 mm
# (ray casts along the lens normal on his mesh; main: 6.4 at z -34), where the lens stack, the comb and a plate need
# 5.8 mm.
PLACE = (-0.1422, -0.0035, 5.0, 1.02)
FOAM_MIN, FOAM_MAX, FOAM_DEFAULT = 0.0015, 0.030, 0.014  # triple-layer foam, compressed against the face
FOAM_W = 0.013                     # foam band width on the frame's back face (round 2's seat, 13 mm at the top)


def _place(pl):
    pl = tuple(pl or PLACE)
    return pl + (1.0,) * (4 - len(pl))                            # (ty, tz, pitch[, scale]); round 7's had no scale


def g2h(V, pl=None):
    ty, tz, pitch, k = _place(pl)
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    Rg = np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
    return k * np.asarray(V) @ Rg.T + np.array([0.0, ty, tz])


def h2g(V, pl=None):
    ty, tz, pitch, k = _place(pl)
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    Rg = np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
    return (np.asarray(V) - np.array([0.0, ty, tz])) @ Rg / k


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


# ---------------------------------------------------------------- the strap on the shell (round 8, decision 43)
# helmet.py's strap (rounds 1 to 7) was one ruled band whose chord across its width sagged into the convex shell (the
# shell came 1.5 to 1.9 mm through it at x +-45 mm) and ran about 23 mm lower at the back than Leatt's. Here it is
# laid on the shell: its centre line where a plane cuts the shell, each cross-section walked across the surface (45 mm
# along the shell, not a chord), every layer offset along the shell's normal: the silicone band on the shell, the
# fabric on it. Sources: research/rider-ledger/goggle.md section 10.
STRAP_W, STRAP_T = H.STRAP_W, H.STRAP_T     # 45 mm (Leatt features), 2 mm (woven elastic, helmet.py)
SIL_W, SIL_H = 0.005, 0.0006                # the silicone anti-slip band inside: 5 mm (Leatt features), 0.6 mm (est.)
STRAP_CLEAR = 0.0007                        # the silicone's face off the shell: it rests on it (the test asks 0.5 mm)
# the centre line's plane, HELMET frame: through (y, z) and rising towards the back by the angle (deg). Fitted on his
# gear first (scratch strapfit2: the strap's edges picked in his photo 07, near side-on, and in Leatt's Pinata Teal
# iso-right of his helmet, goggle and strap): centre z -13.5 mm at y -58 behind the outrigger, rising 3 deg; rms
# 4.5 and 0.3 mm there. Leatt's MY27 kit views (an empty helmet, a stylist's strap) want it 6 to 10 deg steeper and
# its back about 22 mm higher (ledger section 10). Joint front fit (decision 47): refitted through his photos'
# fitted cameras (research/his-photo-cameras.json, landmarks rms 2.6 px in 07) and Leatt's solved iso-right
# (helmet.PRINT_CAMS), the same picks (scratch planescan.py): at (-13.5 mm, +3 deg) the strap stood 37 mm above his
# 07's on average (rms 39.1, his 09 25.9, Pinata 8.9 mm), over the chevron panel where his photo shows it below the
# panel's lower stripe. Now centre z -25 mm at y -58, falling 12 deg towards the back: rms his 07 5.6 mm (mean -0.1),
# his 09 12.1 (its camera 8.3 px rms, 16 mm), Pinata 3.8
STRAP_PLANE = (-0.058, -0.025, -12.0)
STRAP_LAND = 0.020                          # m: the strap leaves the outrigger's slot and lands on the shell
# Joint front fit (decision 47): with the eyeport's cut edge where Leatt's iso photos show it (helmet.PORT "iso", 16 to
# 23 mm behind the side photo's notch) the outriggers' back ends stand ahead of the edge, as in Leatt's Pinata
# iso-right (the plate's back end 65 px ahead of the trim's crest there), and the strap crosses the trim to land on
# the shell. It lands where its whole width lies on the shell, STRAP_EDGE behind the edge (the rubber trim's roll,
# helmet.RIM_R, and a millimetre): landing at the edge itself folded the cross-section's walk onto the edge (the band
# 22 mm wide and 2.5 mm tall over four stations, a wedge in the iso-right render).
STRAP_EDGE = H.RIM_R + 0.001
STRAP_ACROSS = np.r_[-22.5, -20, -17.5, -15, -12.5, -10, -7.5, -5, -2.5, 0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20,
                     22.5] / 1000.0         # m across the strap (bottom edge to top edge); +-2.5: the silicone band
# the adjuster slides (round 9, decision 45): flat moulded frames, as Leatt's MY27 back view shows them at 1:1 (round
# 8's scale: 0.204 mm/px across the strap there; the strap turned 18 deg out of the image plane, so 0.214 mm/px along
# it and 0.207 across) and Leatt's 5.5 back photos of other colourways for the parts (ledger section 11). Slide
# coordinates (mm in the comments, m in the code): a along the strap (towards the right outrigger: image right in the
# back view), b across it (up), from the frame's centre.
SLIDE_X = 0.0410                            # centres at x +-41 mm (round 8: bodies 402 px apart)
SLIDE_L, SLIDE_H = 0.022, 0.052             # the frame outside: 103 to 105 x 247 px
SLIDE_R = 0.0018                            # its outer corners' radius (8 px)
SLIDE_RAIL = 0.0038                         # top and bottom rails, beside the strap's edges: b 22.2 to 26 (the strap's
                                            # edge at 22.5; 15 to 17 px show above it)
SLIDE_BAR = 0.0036                          # the right slide's end bars (17 px)
SLIDE_CBAR = (-0.0035, 0.0018)              # the left slide's centre bar (x 772 to 797 px), the embossed LEATT on it
SLIDE_T = 0.0022                            # moulded plastic, flat
SLIDE_CBAR_T = 0.0040                       # the left centre bar stands over the tail (the tail passes under it): its
                                            # wall catches the light, the tail beside it lies in its shadow (x 797 px)
SLIDE_EDGE = 0.0006                         # its edges' round (the soft highlight along every bar)
SLIDE_GAP = 0.0001                          # it rests on the strap
# the right slide's grip tab on its outer bar (x 1240 to 1280 px, y 885 to 1010): sloped top, Leatt's triangle at the
# top, a field of dimples below a groove (mm)
TAB_POLY = [(7.6, 20.0), (15.0, 19.0), (18.7, 11.5), (18.7, -3.8), (16.6, -6.2), (7.6, -6.2)]
TAB_R = 0.0012
TAB_TRI = [(10.2, 9.6), (18.2, 9.6), (13.6, 18.6)]          # the triangle (x 1238 to 1278, y 890 to 935 px)
TAB_GROOVE = 8.4
TAB_DOTS = [(9.8 + 2.1 * i + (1.05 if j % 2 else 0.0), 6.6 - 2.07 * j) for j in range(6) for i in range(4)
            if 9.8 + 2.1 * i + (1.05 if j % 2 else 0.0) < 18.0]  # 10 px pitch, rows staggered
SLIDE_LEATT = (-0.85, -2.3, 14.0, 3.0)      # mm: the left centre bar's LEATT, centre (a, b), length (b), letter height
# the strap's tail: from the left slide, where it comes up out of the slot beside the centre bar (x 800 px), doubled
# over the strap to the right slide; there a crease (x 1115 px, the 'line' of the brief: Leatt's is a soft fold, not a
# step) and two folds round the slide's left end bar and centre bar (x 1115 to 1170, 1170 to 1228 px), standing about
# a strap's thickness above the tail, rounded at the strap's edges; into the slot beside the outer bar
TAIL_START = 0.0021                         # a on the left slide
TAIL_FOLD = 0.0016                          # the tail comes up out of the slot over this length (a quarter round)
ROLLS = ((-0.0166, -0.0048), (-0.0048, 0.0076))   # a on the right slide
ROLL_H = 0.0030                             # the folds stand this far above the tail
ROLL_K = 2.0                                # their cross-section a parabola: the photo's folds brighten steadily
                                            # across (93 to 154 of 255, lit from his right), where an ellipse's flat
                                            # top rendered flat
ROLL_END = 0.0020                           # rounded over this width at the strap's edges
CREASE_W, CREASE_DEPTH = 0.0004, 0.75       # the crease and the gap between the folds: dark lines 2 to 4 px wide (0.4
                                            # to 0.8 mm), the fabric's top pressed down to a quarter of its thickness
TAIL_ACROSS = np.r_[-22.5, -22.2, -21.8, -21.2, -20.5, -19.5, -17.5, -15, -12.5, -10, -7.5, -5, -2.5, 0, 2.5, 5, 7.5,
                    10, 12.5, 15, 17.5, 19.5, 20.5, 21.2, 21.8, 22.2, 22.5] / 1000.0


def tri_closest(P, A, B, C):
    """Closest points to P on the triangles (A, B, C), all n x 3, and their barycentric weights (Ericson, Real-Time
    Collision Detection 5.1.5, vectorised; regions assigned in reverse order of precedence)."""
    ab, ac = B - A, C - A
    ap, bp, cp = P - A, P - B, P - C
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    den = va + vb + vc
    den = np.where(np.abs(den) < 1e-30, 1e-30, den)
    v, w = vb / den, vc / den
    bary = np.c_[1 - v - w, v, w]
    z = np.zeros(len(P))

    def edge(m, t, cols):
        t = np.where(m, t, 0.0)
        e = np.c_[z, z, z]
        e[:, cols[0]], e[:, cols[1]] = 1 - t, t
        bary[m] = e[m]
    m = (va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0)
    edge(m, (d4 - d3) / np.where(m, (d4 - d3) + (d5 - d6), 1.0), (1, 2))
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    edge(m, d2 / np.where(m, d2 - d6, 1.0), (0, 2))
    bary[(d6 >= 0) & (d5 <= d6)] = [0, 0, 1]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    edge(m, d1 / np.where(m, d1 - d3, 1.0), (0, 1))
    bary[(d3 >= 0) & (d4 <= d3)] = [0, 1, 0]
    bary[(d1 <= 0) & (d2 <= 0)] = [1, 0, 0]
    return bary[:, :1] * A + bary[:, 1:2] * B + bary[:, 2:] * C, bary


def triangulate(F):
    return np.array([[f[0], f[j], f[j + 1]] for f in F for j in range(1, len(f) - 1)])


class Surface:
    """A triangle mesh with outward faces, for laying parts on it: closest points, signed distances (positive
    outside) and smooth normals; the k triangles with the nearest centroids are tested exactly."""

    def __init__(self, V, F, k=24):
        self.V, self.F = np.asarray(V, float), triangulate(F) if len(F) and len(F[0]) != 3 else np.asarray(F)
        self.A, self.B, self.C = (self.V[self.F[:, i]] for i in range(3))
        fn = np.cross(self.B - self.A, self.C - self.A)
        self.fn = fn / np.maximum(np.linalg.norm(fn, axis=1), 1e-30)[:, None]
        self.N = H.normals(self.V, self.F)
        self.tree = cKDTree((self.A + self.B + self.C) / 3)
        self.k = min(k, len(self.F))

    def closest(self, P):
        P = np.atleast_2d(P)
        _, idx = self.tree.query(P, k=self.k)
        n, k = idx.shape
        T = idx.ravel()
        PP = np.repeat(P, k, axis=0)
        Q, bary = tri_closest(PP, self.A[T], self.B[T], self.C[T])
        d2 = ((PP - Q) ** 2).sum(1).reshape(n, k)
        sel = np.arange(n) * k + d2.argmin(1)
        Q, bary, tri = Q[sel], bary[sel], T[sel]
        nrm = (bary[:, :, None] * self.N[self.F[tri]]).sum(1)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1), 1e-30)[:, None]
        sd = np.sqrt(d2.min(1)) * np.sign(((P - Q) * self.fn[tri]).sum(1) + 1e-15)
        return Q, nrm, sd

    def ray_out(self, O, D, t0=0.0, t1=0.35, it=32):
        """Where rays from inside (O) along D first leave through the surface (bisection on the signed distance)."""
        lo, hi = np.full(len(D), t0), np.full(len(D), t1)
        for _ in range(it):
            mid = 0.5 * (lo + hi)
            out = self.closest(O + D * mid[:, None])[2] > 0
            hi, lo = np.where(out, mid, hi), np.where(out, lo, mid)
        return O + D * hi[:, None]


def strap_layout(surf, ends, plane=STRAP_PLANE, land=STRAP_LAND, step=0.0025):
    """The strap's stations from the left outrigger round the back to the right one (HELMET frame): base points
    (n x m x 3, m = STRAP_ACROSS), their normals, the centre line's arc length (m) and how many stations at each end
    hang free (from the outrigger's slot to the landing). ends: {side: (anchor, up, back)} of each outrigger's slot.
    On the shell the base points are on its surface; in the free span they are the band's surface under the
    silicone's height, blended from the slot (the band centred on the anchor, across its up) to the landing."""
    y0, z0, rise = plane
    a = math.radians(rise)
    yp = np.array([0.0, math.cos(a), math.sin(a)])                # in the plane, towards the back
    npl = np.array([0.0, -math.sin(a), math.cos(a)])              # its normal (up)
    A = np.array([0.0, 0.010, z0 + math.tan(a) * (0.010 - y0)])   # the plane's point inside the helmet at y 10 mm
    xh = np.array([1.0, 0.0, 0.0])
    Fe = np.sort(np.vstack([surf.F[:, [0, 1]], surf.F[:, [1, 2]], surf.F[:, [2, 0]]]), axis=1)
    eu, ec = np.unique(Fe, axis=0, return_counts=True)
    edge = surf.V[np.unique(eu[ec == 1])]                         # the shell's free edges (eyeport, lower edge)
    sides = {}
    for sg in (1, -1):
        E, up, back = ends[sg]
        e = E - A
        phi_a = math.atan2(sg * (e @ xh), e @ yp)                 # the anchor's angle from the back (0) round
        zeta_a = e @ npl                                          # its height off the plane
        phi = np.linspace(0.0, phi_a, 600)
        k = np.clip(phi / phi_a, 0, 1)
        blend = np.clip((k - 0.55) / 0.40, 0, 1)
        zeta = zeta_a * blend * blend * (3 - 2 * blend)           # the centre line rises/falls to the slot's height
        Dr = np.cos(phi)[:, None] * yp + sg * np.sin(phi)[:, None] * xh
        S = surf.ray_out(A + zeta[:, None] * npl, Dr)
        s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]
        d_anchor = np.linalg.norm(S - E, axis=1)
        T_ = np.gradient(S, axis=0)
        T_ /= np.linalg.norm(T_, axis=1)[:, None]
        rel = edge[None] - S[:, None]                             # the edge loop's points round each station
        along = np.abs(np.einsum("nkj,nj->nk", rel, T_))
        across = np.abs(rel @ npl)
        depth = np.abs(np.einsum("nkj,nj->nk", rel, surf.closest(S)[1]))
        clear = ~np.any((along < STRAP_EDGE) & (across < STRAP_W / 2 + STRAP_EDGE) & (depth < 0.02), axis=1)
        ok = (d_anchor > land) & np.logical_and.accumulate(clear)  # far enough from the slot, its width on the shell
        i_land = int(np.nonzero(ok)[0].max())                     # (all the way from the back)
        sides[sg] = (S[:i_land + 1], s[:i_land + 1], E, up, back)
    # centre line on the shell, left landing -> back -> right landing, resampled every `step`
    SL, SR = sides[1][0][::-1], sides[-1][0][1:]
    S = np.vstack([SL, SR])
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]
    n = max(int(round(s[-1] / step)), 8)
    su = np.linspace(0, s[-1], n + 1)
    C = np.c_[[np.interp(su, s, S[:, i]) for i in range(3)]].T
    C, nC, _ = surf.closest(C)
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    # walk across the surface from the centre, up and down, 1.25 mm a step, keeping the stations at STRAP_ACROSS
    m = len(STRAP_ACROSS)
    base = np.zeros((len(C), m, 3))
    nrm = np.zeros((len(C), m, 3))
    j0 = int(np.argmin(np.abs(STRAP_ACROSS)))
    base[:, j0], nrm[:, j0] = C, nC
    h = 0.00125
    for sgn in (1, -1):
        p, nn = C.copy(), nC.copy()
        targets = {int(round(abs(w) / h)): j for j, w in enumerate(STRAP_ACROSS) if np.sign(w) == sgn}
        for it in range(1, max(targets) + 1):
            Wd = np.cross(nn, T)
            Wd /= np.linalg.norm(Wd, axis=1)[:, None]
            Wd *= np.sign((Wd @ npl) + 1e-12)[:, None] * sgn
            p, nn, _ = surf.closest(p + Wd * h)
            if it in targets:
                base[:, targets[it]], nrm[:, targets[it]] = p, nn
    # the free spans: from the slot (band centred on the anchor, across `up`, its face normal) to each landing
    off = STRAP_CLEAR + SIL_H + STRAP_T / 2                       # the band's mid-thickness above its base
    spans = []
    for sg, i_end in ((1, 0), (-1, len(C) - 1)):
        _, _, E, up, back = sides[sg]
        L = base[i_end]
        nL = nrm[i_end]
        nE = np.cross(up, back) * sg
        nE /= np.linalg.norm(nE)
        nE *= np.sign(nE @ nL[j0])
        bE = E[None] + STRAP_ACROSS[:, None] * up[None] - nE[None] * off
        d = np.linalg.norm(L[j0] - E)
        k = max(int(round(d / step)), 2)
        u = np.linspace(0.0, 1.0, k + 1)[:-1]
        uu = (u * u * (3 - 2 * u))[:, None, None]
        B = bE[None] * (1 - uu) + L[None] * uu
        Nn = nE[None, None] * (1 - uu) + nL[None] * uu
        Nn /= np.linalg.norm(Nn, axis=2)[..., None]
        # never into the shell: lift any base point under the shell's surface back onto it
        flat = B.reshape(-1, 3)
        Q, nq, sd = surf.closest(flat)
        flat = np.where((sd < 0)[:, None], Q, flat)
        B = flat.reshape(B.shape)
        spans.append((B, Nn, k))
    (BL, NL, kL), (BR, NR, kR) = spans
    base = np.concatenate([BL, base, BR[::-1]])
    nrm = np.concatenate([NL, nrm, NR[::-1]])
    mid = base[:, j0] + nrm[:, j0] * off
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(mid, axis=0), axis=1))]
    return base, nrm, s, (kL, kR)


def _grid_faces(part, G, mat, uv=None, flip=False):
    """Quads over a (n x m x 3) grid: i along, j across; uv (n x m x 2) or None."""
    n, m = G.shape[:2]
    o = len(part.V)
    part.V = np.vstack([part.V, G.reshape(-1, 3)])
    for i in range(n - 1):
        for j in range(m - 1):
            q = [o + i * m + j, o + (i + 1) * m + j, o + (i + 1) * m + j + 1, o + i * m + j + 1]
            u = None if uv is None else [tuple(uv[i, j]), tuple(uv[i + 1, j]), tuple(uv[i + 1, j + 1]),
                                         tuple(uv[i, j + 1])]
            if flip:
                q, u = q[::-1], (None if u is None else u[::-1])
            part.F.append(q)
            part.M.append(mat)
            part.UV.append(u if u is not None else [(0.5, 0.5)] * 4)


def _band(part, base, nrm, h0, h1, mat_out, mat_in, uv=None, ends=True):
    """A layer from h0 to h1 above the base points along their normals: outer face (uv), inner face, both rims and
    (ends) both end caps."""
    lo, hi = base + nrm * h0, base + nrm * h1
    _grid_faces(part, hi, mat_out, uv)
    _grid_faces(part, lo, mat_in, None, flip=True)
    for j, flip in ((0, False), (-1, True)):                      # bottom and top rims
        _grid_faces(part, np.stack([lo[:, j], hi[:, j]], axis=1), mat_in, None, flip=flip)
    if ends:
        for i, flip in ((0, False), (-1, True)):
            _grid_faces(part, np.stack([lo[i], hi[i]], axis=0), mat_in, None, flip=flip)


def strap_map(base, nrm, s, sq, bq, hq):
    """Points on the strap's coordinates, vectorised: arc length sq (m), across bq (m; beyond the edges continued
    along each edge's own direction), height hq above the base along the interpolated normal."""
    sq, bq, hq = (np.broadcast_to(np.asarray(x, float), np.broadcast(sq, bq, hq).shape).ravel() for x in (sq, bq, hq))
    i = np.clip(np.searchsorted(s, sq) - 1, 0, len(s) - 2)
    f = ((sq - s[i]) / np.maximum(s[i + 1] - s[i], 1e-12))[:, None, None]
    B = base[i] * (1 - f) + base[i + 1] * f                               # n x m x 3
    N = nrm[i] * (1 - f) + nrm[i + 1] * f
    A = STRAP_ACROSS
    bc = np.clip(bq, A[0], A[-1])
    j = np.clip(np.searchsorted(A, bc) - 1, 0, len(A) - 2)
    g = ((bc - A[j]) / (A[j + 1] - A[j]))[:, None]
    r = np.arange(len(sq))
    b = B[r, j] * (1 - g) + B[r, j + 1] * g
    nn = N[r, j] * (1 - g) + N[r, j + 1] * g
    nn /= np.linalg.norm(nn, axis=1)[:, None]
    up = B[:, -1] - B[:, -2]
    dn = B[:, 0] - B[:, 1]
    e = np.where((bq >= 0)[:, None], up, dn)
    e /= np.linalg.norm(e, axis=1)[:, None]
    b = b + e * (np.abs(bq) - np.abs(bc))[:, None]
    return b + nn * hq[:, None]


def _rounded_outline(core, rho, per_arc=5, seg=0.0015):
    """The boundary of a convex polygon (or a segment) grown by rho, counter-clockwise in (a, b): an arc of per_arc
    points at each corner, the straight runs cut every `seg` (the same count for every rho)."""
    core = np.asarray(core, float)
    k = len(core)
    out = []
    for i in range(k):
        c, cp, cn = core[i], core[i - 1], core[(i + 1) % k]
        e0, e1 = c - cp, cn - c
        n0 = np.array([e0[1], -e0[0]]) / np.linalg.norm(e0)
        n1 = np.array([e1[1], -e1[0]]) / np.linalg.norm(e1)
        p0 = math.atan2(n0[1], n0[0])
        sw = (math.atan2(n1[1], n1[0]) - p0) % (2 * math.pi)
        if sw > math.pi + 1e-9:                     # a segment's ends sweep exactly pi
            sw = math.pi
        for t in np.linspace(0.0, 1.0, per_arc):
            out.append(c + rho * np.array([math.cos(p0 + t * sw), math.sin(p0 + t * sw)]))
        m = max(int(math.ceil(np.linalg.norm(e1) / seg)), 1)
        for t in np.arange(1, m) / m:                # the straight run to the next corner's arc
            out.append(c + rho * n1 + t * e1)
    return np.array(out)


def _rect_core(a0, a1, b0, b1, outer_top, r_out, rs, n=4):
    """The core (to be grown by rs) of the rectangle a0..a1 x b0..b1 whose two outer corners (the b1 side if
    outer_top, else the b0 side) are rounded by r_out and the other two by rs: counter-clockwise."""
    pts = []
    for (ca, cb), (t0, t1), outer in (((a0, b0), (180, 270), not outer_top), ((a1, b0), (270, 360), not outer_top),
                                      ((a1, b1), (0, 90), outer_top), ((a0, b1), (90, 180), outer_top)):
        r = r_out if outer else rs
        cx = ca + (r if ca == a0 else -r)
        cy = cb + (r if cb == b0 else -r)
        rc = r - rs
        if rc < 1e-6:
            pts.append((cx, cy))
            continue
        for t in np.radians(np.linspace(t0, t1, n)):
            pts.append((cx + rc * math.cos(t), cy + rc * math.sin(t)))
    return pts


def _slab(part, mapper, core, R, h0, T, mat, uvf, re=SLIDE_EDGE, grid=0.0015):
    """A moulded plate: the convex core grown by R (rounded corners), from h0 up T, its top edge rounded by re
    (a wall, then a quarter round to the flat top). mapper(a, b, h) -> points; uvf(a, b) -> (u, v) or None."""
    from scipy.spatial import Delaunay
    from matplotlib.path import Path
    prof = [(R, h0), (R, h0 + T - re)]
    prof += [(R - re + re * math.cos(t), h0 + T - re + re * math.sin(t)) for t in np.radians([30, 60])]
    prof += [(R - re, h0 + T)]
    rings = [_rounded_outline(core, r_) for r_, _ in prof]
    n = len(rings[0])
    o = len(part.V)
    Vab, Vh = [], []
    for ring, (_, h) in zip(rings, prof):
        Vab.append(ring)
        Vh.append(np.full(n, h))

    def cap(ring, up):
        lo, hi = ring.min(0), ring.max(0)
        ga, gb = np.meshgrid(np.arange(lo[0] + grid / 2, hi[0], grid), np.arange(lo[1] + grid / 2, hi[1], grid))
        G_ = np.c_[ga.ravel(), gb.ravel()]
        if len(G_):
            A_, B_ = ring, np.roll(ring, -1, axis=0)                    # distance to the ring's edges
            d_ = B_ - A_
            tt = np.clip(((G_[:, None] - A_[None]) * d_[None]).sum(2) / (d_ * d_).sum(1)[None], 0, 1)
            dist = np.linalg.norm(G_[:, None] - (A_[None] + tt[..., None] * d_[None]), axis=2).min(1)
            G_ = G_[Path(ring).contains_points(G_) & (dist > 0.5 * grid)]
        P = np.vstack([ring, G_])
        tri = Delaunay(P).simplices
        e1_, e2_ = P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]]
        ar = e1_[:, 0] * e2_[:, 1] - e1_[:, 1] * e2_[:, 0]                # twice the signed area
        tri, ar = tri[np.abs(ar) > 1e-14], ar[np.abs(ar) > 1e-14]
        flip = (ar < 0) if up else (ar > 0)
        tri[flip] = tri[flip][:, ::-1]
        assert len(np.unique(tri[tri < len(ring)])) == len(ring), "a ring point left out of the cap"
        return P, tri
    base_idx = n * len(prof)
    Pt, Tt = cap(rings[-1], True)
    Pb, Tb = cap(rings[0], False)
    ab = np.vstack(Vab + [Pt[n:], Pb[n:]])
    hh = np.concatenate(Vh + [np.full(len(Pt) - n, prof[-1][1]), np.full(len(Pb) - n, prof[0][1])])
    part.V = np.vstack([part.V, mapper(ab[:, 0], ab[:, 1], hh)])
    top0, bot0 = base_idx, base_idx + len(Pt) - n

    def gid(k, ring_i):                               # ring k's point i, or a cap's own interior point
        return o + k * n + ring_i

    def add(f):
        part.F.append(f)
        part.M.append(mat)
        part.UV.append([uvf(*ab[q - o]) for q in f] if uvf else [(0.5, 0.5)] * len(f))
    for k in range(len(prof) - 1):                    # walls and the round, outwards
        for i in range(n):
            j = (i + 1) % n
            add([gid(k, i), gid(k, j), gid(k + 1, j), gid(k + 1, i)])
    K = len(prof) - 1
    for t in Tt:
        add([gid(K, q) if q < n else o + top0 + q - n for q in t])
    for t in Tb:
        add([gid(0, q) if q < n else o + bot0 + q - n for q in t])


def slide_parts(base, nrm, s, x_c, right, h0):
    """One adjuster slide at x_c (m, HELMET frame) on the strap: rails above and below the strap, the right slide's
    end bars and outer bar with its grip tab, the left slide's centre bar (its end bars lie under the strap and the
    tail: not seen, not built). Every bar a flat moulded plate with rounded corners and soft edges, bent to the
    strap's curve (22 mm along a 95 mm radius is 0.6 mm of sag; 52 mm across, 2.3 mm). Returns the part and the
    slide's centre (arc length)."""
    import goggle_strap_art as SA
    mid = base[:, len(STRAP_ACROSS) // 2]
    k = np.argmin(np.abs(mid[:, 0] - x_c) + 10 * (mid[:, 1] < 0.05))
    s_c = s[k]
    part = H.Part("goggle_slides")
    mapper = lambda a, b, h: strap_map(base, nrm, s, s_c + a, b, h)          # noqa: E731
    uvf = lambda a, b: SA.slide_uv(a, b, right)                            # noqa: E731
    hl, hh = SLIDE_L / 2, SLIDE_H / 2
    R = SLIDE_R
    rs = SLIDE_EDGE + 0.00005
    for sg in (1, -1):                                                     # rails: full length, the frame's outer
        b0, b1 = sorted((sg * (hh - SLIDE_RAIL), sg * hh))                 # corners round (SLIDE_R), the inner ones
        core = _rect_core(-hl, hl, b0, b1, sg > 0, SLIDE_R, rs)            # square where the end bars go on
        _slab(part, mapper, core, rs, h0, SLIDE_T, "goggle_slide", uvf)
    bars = []
    if right:
        bars += [(-hl, -hl + SLIDE_BAR), (-0.0018, 0.0018), (hl - SLIDE_BAR, hl)]
    else:
        bars += [SLIDE_CBAR]
    rb = 0.0008
    for a0, a1 in bars:                                                   # across, rail to rail
        b0, b1 = -hh + 0.5 * SLIDE_RAIL, hh - 0.5 * SLIDE_RAIL
        core = [(a0 + rb, b0), (a1 - rb, b0), (a1 - rb, b1), (a0 + rb, b1)]
        _slab(part, mapper, core, rb, h0, SLIDE_T if right else SLIDE_CBAR_T, "goggle_slide", uvf)
    if right:                                                             # the grip tab, on the outer bar
        poly = np.asarray(TAB_POLY) / 1000.0
        c = poly.mean(0)
        core = c + (poly - c) * (1 - TAB_R / np.linalg.norm(poly - c, axis=1))[:, None]
        _slab(part, mapper, core, TAB_R, h0, SLIDE_T, "goggle_slide", uvf)
    return part, s_c


def build_tail(base, nrm, s, sL, sR, h0, uv_of):
    """The strap's tail doubled over it between the slides (goggle_strap_band faces): from TAIL_START on the left
    slide (coming up out of its slot over TAIL_FOLD) to the right slide's outer bar, the crease and the two folds
    there (ROLLS), rounded at the strap's edges."""
    a0, a1 = sL + TAIL_START, sR + ROLLS[1][1]
    creases = np.array([sR + ROLLS[0][0], sR + ROLLS[0][1]])
    S = np.r_[np.arange(a0, a1, 0.0025), a0 + TAIL_FOLD * np.linspace(0, 1, 7),
              np.arange(sR + ROLLS[0][0] - 0.002, a1, 0.0004), a1]
    for c_ in creases:                                                         # fine through the creases
        S = np.r_[S, c_ + np.linspace(-0.0012, 0.0012, 25)]
    S = np.unique(S)
    S = S[(S >= a0) & (S <= a1)]
    x = np.clip((S - a0) / TAIL_FOLD, 0, 1)
    th = np.maximum(0.0004, STRAP_T * np.sqrt(1 - (1 - x) ** 2))              # the quarter round out of the slot
    dc = np.abs(S[:, None] - creases[None]).min(1)
    th = th * (1 - CREASE_DEPTH * np.exp(-(dc / CREASE_W) ** 2))
    bump = np.zeros(len(S))
    for r0, r1 in ROLLS:
        x = np.clip((S - (sR + r0)) / (r1 - r0), 0, 1)
        bump += ROLL_H * np.clip(1 - np.abs(2 * x - 1) ** ROLL_K, 0, 1)
    Bq = TAIL_ACROSS
    e = (np.abs(Bq) - (STRAP_W / 2 - ROLL_END)) / ROLL_END
    fall = np.where(e > 0, np.sqrt(np.clip(1 - e ** 2, 0, 1)), 1.0)          # the folds' rounded ends
    SS, BB = np.meshgrid(S, Bq, indexing="ij")
    top = h0 + th[:, None] + bump[:, None] * fall[None, :]
    lo = strap_map(base, nrm, s, SS, BB, np.full(SS.shape, h0)).reshape(len(S), len(Bq), 3)
    hi = strap_map(base, nrm, s, SS, BB, top).reshape(len(S), len(Bq), 3)
    # u along the fabric, not along the strap beneath: up out of the slot and over the rolls the face runs up to 4
    # times as far as the base (the weave stretched on their flanks); the tail's own centre line sets its u
    c = hi[:, int(np.argmin(np.abs(Bq)))]
    fab = a0 + np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    uv = uv_of(np.broadcast_to(fab[:, None], SS.shape), BB)
    return lo, hi, uv


def rims(part, lo, hi, uv, mat, sides=True):
    """The band's side faces (both edges, unless not sides) and both end caps, outwards; uv: the edge texels of
    the print."""
    n, m = lo.shape[:2]
    for j, flip in ((0, False), (m - 1, True)) if sides else ():
        G_ = np.stack([lo[:, j], hi[:, j]], axis=1)
        u_ = np.stack([uv[:, j], uv[:, j] + [0, 0.004 if j == 0 else -0.004]], axis=1)
        _grid_faces(part, G_, mat, u_, flip=flip)
    for i, flip in ((0, False), (n - 1, True)):
        G_ = np.stack([lo[i], hi[i]], axis=0)
        u_ = np.stack([uv[i], uv[i] + [0.0004, 0]], axis=0)
        _grid_faces(part, G_, mat, u_, flip=flip)


def selvedges(lo, hi, uv, mat):
    """The strap's woven side faces (goggle_strap): vertices in four rows, outer bottom edge, outer top edge, inner
    top edge, inner bottom edge (one per station, as helmet.py's strap, so each outer row pair is the strap's width
    apart: test_helmet's width check reads them so); faces outwards, uv on the print's edge texels (the navy
    selvedges). The end caps are rims(sides=False) on the band."""
    n = len(lo)
    part = H.Part("goggle_strap")
    part.V = np.vstack([hi[:, 0], hi[:, -1], lo[:, -1], lo[:, 0]])
    W = hi[:, -1] - hi[:, 0]
    dv = np.array([0.0, 0.004])

    def add(f, out, u):
        P = part.V[f]
        if np.cross(P[1] - P[0], P[2] - P[0]) @ out < 0:
            f, u = f[::-1], u[::-1]
        part.F.append(list(f))
        part.M.append(mat)
        part.UV.append([tuple(x) for x in u])
    e0, e1 = uv[:, 0], uv[:, -1]
    for i in range(n - 1):
        add([0 * n + i, 0 * n + i + 1, 3 * n + i + 1, 3 * n + i], -W[i], [e0[i], e0[i + 1], e0[i + 1] + dv, e0[i] + dv])
        add([1 * n + i, 1 * n + i + 1, 2 * n + i + 1, 2 * n + i], W[i], [e1[i], e1[i + 1], e1[i + 1] - dv, e1[i] - dv])
    return part


# Round 11 (decision 49, item 3): the strap's white LEATT. In the Pinata kit iso-right at 8x (scratch pin_T_8x.png) its
# letters are a layer standing on the fabric: crisp edges, a lit wall 2 to 3 px wide along the T's lower edges, a dark
# line where the wall meets the fabric, the fabric's weave stopping at it. Rounds 9 and 10 painted it into the print
# (6.6 texels a mm along, 8.5 across) with a 0.8 mm relief in the normal map blurred over 0.25 mm: flat and soft-edged
# at 4x. Now it is geometry on the band: the official wordmark's outline (its alpha at level 0.5, sub-pixel), a flat
# top STRAP_LOGO_T above the fabric's face and square walls, sunk STRAP_LOGO_SINK into the fabric. Its place is the
# ISO's (goggle_strap_art.leatt_boxes); the print had also stretched it 1.34 times along (texels 0.157 mm along,
# 0.117 across): 162 mm long instead of Leatt's 120.
STRAP_LOGO_T = 0.0005                       # m: the layer's thickness (wall 2 to 3 px at 0.18 mm a px, seen 40 deg)
STRAP_LOGO_SINK = 0.0001                    # m: its walls start this far inside the fabric (no gap on the curve)
STRAP_LOGO_STEP = 0.0002                    # m: outline points at most this far apart; the top face's inner grid 0.6 mm


def wordmark_loops(min_area=0.002):
    """The official wordmark's outlines in letter heights (x from the cropped mark's left, y down from its top, as
    wordmark_mask: the same crop, the registered mark dropped): contours of its alpha at 0.5, loops under min_area
    (letter heights squared: antialiasing specks) dropped."""
    import contourpy
    from PIL import Image
    from scipy import ndimage
    a = np.array(Image.open(WORDMARK).convert("RGBA"))[..., 3].astype(float) / 255.0
    m = a > 128 / 255.0
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.nonzero(sizes > 0.05 * sizes.max())[0])
    ys, xs = np.nonzero(keep)
    a = a * ndimage.binary_dilation(keep, iterations=2)
    c = np.pad(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 2)
    h = ys.max() - ys.min() + 1
    loops = []
    for ln in contourpy.contour_generator(z=c, line_type="Separate").lines(0.5):
        P = (np.asarray(ln, float) - 2.0) / h                      # (col, row) in letter heights, pixel centres
        P = P[:-1] if np.allclose(P[0], P[-1]) else P
        area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
        if len(P) > 3 and abs(area) > min_area:
            loops.append(P)
    return loops


def _resample_loop(P, step):
    """A closed loop with points at most step apart (its own points kept: corners stay sharp)."""
    out = []
    for a, b in zip(P, np.roll(P, -1, axis=0)):
        k = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        out.append(a + (b - a) * (np.arange(k) / k)[:, None])
    return np.vstack(out)


def strap_logo(part, base, nrm, s, h_face, boxes, mat="goggle_strap_logo"):
    """The raised LEATTs on the band (part): boxes [(S0, B_top, height)] in the strap's (s, across) metres, the
    wordmark's top-left there, letters height tall; base, nrm on the (s x STRAP_ACROSS) grid; h_face the fabric's face
    above base. Per wordmark: the top (Delaunay over the outline points and an inner grid, triangles kept whose
    centroid and edge midpoints lie inside), then the walls, each with its own vertices (sharp edges under smooth
    shading). Returns the outline loops in (S, B) for the checks."""
    from matplotlib.path import Path
    from scipy.interpolate import RegularGridInterpolator
    from scipy.spatial import Delaunay, cKDTree
    gB = RegularGridInterpolator((s, STRAP_ACROSS), base)
    gN = RegularGridInterpolator((s, STRAP_ACROSS), nrm)

    def lift(Q, t):
        Nq = gN(Q)
        Nq /= np.linalg.norm(Nq, axis=1)[:, None]
        return gB(Q) + Nq * (h_face + t)

    def inside(Q, loops2):
        r = np.zeros(len(Q), bool)
        for L2 in loops2:
            r ^= Path(L2).contains_points(Q)
        return r
    out = []
    for S0, Btop, lh in boxes:
        loops2 = [_resample_loop(np.c_[S0 + P[:, 0] * lh, Btop - P[:, 1] * lh], STRAP_LOGO_STEP)
                  for P in wordmark_loops()]
        out.append(loops2)
        bp = np.vstack(loops2)
        lo, hi = bp.min(0), bp.max(0)
        g = 0.0006
        gx, gy = np.meshgrid(np.arange(lo[0] + g / 2, hi[0], g), np.arange(lo[1] + g / 2, hi[1], g))
        G2 = np.c_[gx.ravel(), gy.ravel()]
        G2 = G2[inside(G2, loops2)]
        segs = np.vstack([np.c_[L2, np.roll(L2, -1, axis=0)] for L2 in loops2])
        # inner points at least 0.3 mm from every outline segment
        d = np.full(len(G2), np.inf)
        for i0 in range(0, len(segs), 2000):
            A, Bv = segs[i0:i0 + 2000, :2], segs[i0:i0 + 2000, 2:]
            AB = Bv - A
            tt = np.clip(((G2[:, None] - A[None]) * AB[None]).sum(-1) / np.maximum((AB * AB).sum(-1), 1e-18), 0, 1)
            d = np.minimum(d, np.linalg.norm(G2[:, None] - (A[None] + tt[..., None] * AB[None]), axis=-1).min(1))
        G2 = G2[d > 0.0003]
        pts = np.vstack([bp, G2])
        tri = Delaunay(pts).simplices
        T = pts[tri]
        ok = inside(T.mean(1), loops2)
        for a_, b_ in ((0, 1), (1, 2), (2, 0)):          # each edge's midpoint, nudged off the outline it may lie on
            ok &= inside(0.45 * (T[:, a_] + T[:, b_]) + 0.1 * T.mean(1), loops2)
        tri = tri[ok]
        V = lift(pts, STRAP_LOGO_T)
        nm = np.cross(V[tri[:, 1]] - V[tri[:, 0]], V[tri[:, 2]] - V[tri[:, 0]])
        Nc = gN(pts[tri].mean(1))
        tri[(nm * Nc).sum(1) < 0] = tri[(nm * Nc).sum(1) < 0][:, ::-1]
        part.add(V, tri.tolist(), mat, [[(0.5, 0.5)] * 3] * len(tri))
        for L2 in loops2:
            n = len(L2)
            Vt, Vb = lift(L2, STRAP_LOGO_T), lift(L2, -STRAP_LOGO_SINK)
            # outward: the side of the outline away from the letter
            e = np.roll(L2, -1, axis=0) - L2
            rgt = np.c_[e[:, 1], -e[:, 0]] / np.maximum(np.linalg.norm(e, axis=1), 1e-12)[:, None]
            k = int(np.argmax(np.linalg.norm(e, axis=1)))
            mid = 0.5 * (L2[k] + L2[(k + 1) % n])
            sgn = -1.0 if inside((mid + rgt[k] * 1e-5)[None], loops2)[0] else 1.0
            o = len(part.V)
            i = np.arange(n)
            j = (i + 1) % n
            q = np.c_[o + i, o + j, o + n + j, o + n + i]
            fn = np.cross(Vt[j] - Vt[i], Vb[i] - Vt[i])
            mids = 0.5 * (L2 + L2[j])
            outv = lift(mids + sgn * rgt * 1e-4, STRAP_LOGO_T) - lift(mids, STRAP_LOGO_T)
            q[(fn * outv).sum(1) < 0] = q[(fn * outv).sum(1) < 0][:, ::-1]
            part.add(np.vstack([Vt, Vb]), [], mat)
            part.F += q.tolist()
            part.M += [mat] * n
            part.UV += [[(0.5, 0.5)] * 4] * n
    return out


def build_strap(Rt, prof, ends, surf=None):
    """The strap on the shell, in the MB rest frame: goggle_strap_band (the printed woven fabric, its inner face,
    the silicone band inside, the ends and the tail doubled between the slides), goggle_strap (its side faces) and
    goggle_slides (the two adjusters). ends: {side: (anchor, up, back)} of the outriggers' slots in the HELMET
    frame."""
    R, t = Rt
    if surf is None:
        Vo, Fo, _ = H.shell_outer(prof)
        surf = Surface(Vo, Fo)
    base, nrm, s, (kL, kR) = strap_layout(surf, ends)
    band = H.Part("goggle_strap_band")
    h_in = STRAP_CLEAR + SIL_H
    W0 = STRAP_ACROSS[0]
    import goggle_strap_art as SA

    def uv_of(S_, B_):
        # round 12: the print's u in true mm from each end (goggle_strap_art.strap_u), whatever length it is built to
        return np.stack([SA.strap_u(S_, s[-1]), (B_ - W0) / STRAP_W], axis=-1)
    uv = uv_of(*np.meshgrid(s, STRAP_ACROSS, indexing="ij"))
    lo, hi = base + nrm * h_in, base + nrm * (h_in + STRAP_T)
    _grid_faces(band, hi, "goggle_strap", uv)
    # round 11: the raised LEATTs, where the print has them (goggle_strap_art.leatt_boxes: mm on the print's u)
    Lp = SA.STRAP_LEN_UV * 1000.0
    sg = np.linspace(0.0, s[-1], 2001)
    logo_boxes = [(float(np.interp(x0 / Lp, SA.strap_u(sg, s[-1]), sg)), W0 + (1.0 - y0 / SA.W_MM) * STRAP_W,
                   lh / 1000.0) for x0, y0, lh in SA.leatt_boxes()]
    strap_logo(band, base, nrm, s, h_in + STRAP_T, logo_boxes)
    _grid_faces(band, lo, "goggle_strap_in", None, flip=True)
    strap = selvedges(lo, hi, uv, "goggle_strap_rim")
    rims(band, lo, hi, uv, "goggle_strap_rim", sides=False)               # the ends, in the outriggers
    jj = np.nonzero(np.abs(STRAP_ACROSS) <= SIL_W / 2 + 1e-9)[0]
    _band(band, base[:, jj], nrm[:, jj], STRAP_CLEAR, h_in, "goggle_silicone", "goggle_silicone", ends=True)
    slides = H.Part("goggle_slides")
    sc = []
    h_slide = h_in + STRAP_T + SLIDE_GAP
    for x_c, right in ((SLIDE_X, False), (-SLIDE_X, True)):
        p, s_c = slide_parts(base, nrm, s, x_c, right, h_slide)
        o = len(slides.V)
        slides.V = np.vstack([slides.V, p.V])
        slides.F += [[i + o for i in f] for f in p.F]
        slides.M += p.M
        slides.UV += p.UV
        sc.append(s_c)
    sL, sR = min(sc), max(sc)                     # the right slide (x < 0) is the later one along s
    tlo, thi, tuv = build_tail(base, nrm, s, sL, sR, h_in + STRAP_T + SLIDE_GAP, uv_of)
    _grid_faces(band, thi, "goggle_strap", tuv)
    _grid_faces(band, tlo, "goggle_strap_in", None, flip=True)
    rims(band, tlo, thi, tuv, "goggle_strap_rim")
    for P in (band, strap, slides):
        P.V = P.V @ R.T + t
        P.frame = "MB"
    info = dict(length_mm=round(float(s[-1]) * 1000, 1), free_stations=(kL, kR),
                slides_s_mm=[round(v * 1000, 1) for v in sc])
    return [band, strap, slides], info, (base, nrm, s)


def build_goggle(body, Rt, prof):
    """The goggle on his head (MB rest frame), riding the head bone: frame, double lens, bare tear-off posts,
    outriggers, nose guard, face foam and the strap; his eyes behind it."""
    R, t = Rt
    fr, info = build_frame(notch=WORN_NOTCH)           # round 11: no bridge over his nose ridge (nose_back)
    rings, _ = frame_rings(notch=WORN_NOTCH)
    skin = body["V"][H.head_skin(body, ("head",))]
    skin_G = h2g((skin - t) @ R)
    foam, foam_back = build_foam(rings, info, skin_G)
    mount = shell_mount(prof)                         # on the helmet: outriggers drape over the shell
    parts = [fr, build_fins(), build_frame_logo(), build_lens(), build_posts(), build_outriggers(mount=mount),
             build_strap_ends(mount=mount), build_nose_guard(skin_G=skin_G), build_nose_ribs(skin_G=skin_G), foam]
    strap, sinfo, _ = build_strap(Rt, prof, strap_ends(mount))
    for P in parts:
        P.V = g2h(P.V) @ R.T + t
    eyes, einfo = build_eyes(body)
    L = info["L"]
    ctr = g2h(L.point(0.0, 0.0, 0.0)[0][None])[0] @ R.T + t
    eye = H.head_landmarks(body)["eye"]
    info_out = dict(lens_centre_ahead_of_eye_mm=round(float(eye[1] - ctr[1]) * 1000, 1),
                    lens_centre_above_eye_mm=round(float(ctr[2] - eye[2]) * 1000, 1),
                    foam_mm=[round(float(np.linalg.norm(foam_back[0] - foam_back[1], axis=1).min()) * 1000, 1),
                             round(float(np.linalg.norm(foam_back[0] - foam_back[1], axis=1).max()) * 1000, 1)],
                    frame_width_mm=round(float(np.ptp(g2h(np.vstack(rings))[:, 0])) * 1000, 1),
                    frame_height_mm=round(float(np.ptp(np.vstack(rings)[:, 2]) * _place(None)[3]) * 1000, 1),
                    strap=sinfo, **einfo)
    return parts + strap + eyes, info_out


def strap_ends(mount):
    """Each outrigger's strap slot in the HELMET frame: the anchor (OR_ANCHOR inside its back end, mid height and
    thickness), the direction up its back end and the direction back along it."""
    ends = {}
    for sg, (Go, Gi, a) in outrigger_grids(mount=mount).items():
        nv = Go.shape[1]
        mid = 0.5 * (Go + Gi)
        # round 12: up the plate where the anchor is (the twisted plate's cross-section there; round 13's rigid plate
        # is the same up its length), not up its back edge:
        # with the hinge inside the frame the worn twist reaches 18.75 deg at the top row, and the back edge then leans
        # 3.7 deg more than the plate at the anchor, which put the strap's top corner through the plate's outer face
        i = int(np.argmin(np.linalg.norm(mid[:, nv // 2] - a, axis=1)))
        up = g2h(Go[i, -1][None])[0] - g2h(Go[i, 0][None])[0]
        back = g2h(mid[-1, nv // 2][None])[0] - g2h(mid[-4, nv // 2][None])[0]
        ends[sg] = (g2h(a[None])[0], up / np.linalg.norm(up), back / np.linalg.norm(back))
    return ends


def free_parts(gp=None, post=False):
    """The goggle alone as in Leatt's product photos (GOGGLE frame): frame, fins, logo, lens, posts, the free (flat)
    outriggers, nose guard and the foam at its default thickness (no face to press on); for the comparison with
    the goggle-alone photos (goggle_views.py)."""
    fr, info = build_frame(gp)
    rings, _ = frame_rings(gp)
    foam, _ = build_foam(rings, info, np.array([[0.0, 10.0, 0.0]]))
    return [fr, build_fins(gp), build_frame_logo(gp), build_lens(gp), build_posts(gp), build_outriggers(gp, None, post),
            build_strap_ends(gp), build_nose_guard(gp), build_nose_ribs(gp), foam]


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
    # round 11: the comb behind the lens, the frame's colour in a moulded satin finish. Leaning back 22 deg (RIB_LEAN)
    # its faces look up at the studio's top light, and at the frame's rough 0.05 they mirrored it: 3,222 white px in
    # the phr tongue zone (round 10, upright: 1,159). Leatt's tongues show none in phr or iso55, only a soft lighter
    # top (phr: L p95 / p50 1.22 on the tongues). Rough 0.45 left no white px but a pink sheen (tongues L p50 171);
    # rough 0.7 with spec 0.2 renders 126, Leatt's 99 (the rest is our studio's brighter top light)
    "goggle_comb": dict(rgb=[150, 0, 58], rough=0.7, spec=0.2),
    "goggle_logo": dict(rgb=[236, 236, 238], rough=0.4),                   # printed white (MY27 kit views)
    "goggle_vent": dict(rgb=[16, 16, 18], rough=0.95),                      # foam-backed slots
    # round 10: the black inner moulding. Round 11: its face read 37 in iso55 (band x 1676..1692, y 960..1000, L p50)
    # against Leatt's white ISO 19 (23 above the slots, 10 below); spec 0.15 renders 29, 0.05 26, 0.1 at rgb 8 20.4.
    # Round 12: the side section's taller wall (SIDE_*) turns its normal up through the studio key's mirror direction
    # on the lower far pillar (normal z 0.33 to 0.40 at y 1036 to 1068 px in iso55): at spec 0.1 a white patch, L 228
    # (Leatt's 17); rough 0.35 spec 0.05 renders 89, spec 0.02 69, spec 0 16: a matte moulding, rgb 10 for the tone
    "goggle_chassis": dict(rgb=[10, 10, 10], rough=0.5, spec=0.0),
    "goggle_slot": dict(rgb=[3, 3, 4], rough=0.9, spec=0.0),                # round 10: inside the clip slots
    # round 11: the clip's tab in a slot (CHASSIS_CLIP_*): Leatt's white ISO 33 to 35 (top slot), 32 (bottom); at 30/30/32
    # spec 0.2 ours read 54 to 65 and 81 to 87, at this 37 and 58 (the bottom tab faces the studio's top light)
    "goggle_clip": dict(rgb=[14, 14, 15], rough=0.6, spec=0.1),
                                                                            # (the plates' black and gloss)
    # round 12 (item 4): the rim above the near tongues in phr is mostly the face foam's top seen past the comb (part
    # buffer; the bridge only between the tongues): at sheen 0.6 its upper roll glowed at grazing view, the rim L p50
    # 138 (Leatt 87), its roll 150 to 200; sheen 0.2 renders 120, sheen 0 96 (polyurethane foam is matte).
    # Round 13 (item 5): its Fresnel specular at that grazing view, spec 0.1 (default 0.5): rim L p50 97 to 86 (Leatt
    # 87), its peak 99 to 94 (Leatt 93) with the run's top pixel left out on both sides (scratch rim13.py): round 12's
    # peak 160 was mostly that pixel, the rim's edge blended with our white backdrop (Leatt's is teal, left out)
    "goggle_foam": dict(rgb=[40, 40, 44], rough=0.95, sheen=0.0, spec=0.1),
    # round 11: the bridge round the comb (grey in phr and the exploded view's slotted surface): a moulding, satin, no
    # foam sheen
    "goggle_bridge": dict(rgb=[40, 40, 44], rough=0.6),
    "goggle_noseguard": dict(rgb=[30, 30, 32], rough=0.6),
    "goggle_post": dict(rgb=[20, 20, 22], rough=0.35),
    # round 13: the carrier's clear post (phr and the Forge front: a clear knob on the C's outer edge, the red behind
    # it seen through; the ISO renders on white show none beyond the C). Round 14: on the plate (CAR_POST_PLATE)
    "goggle_post_clear": dict(rgb=[235, 235, 238], rough=0.05, transmission=1.0),
    # gloss black (kit photo; round 6, iso55: Leatt's face reads 23/23/23 with thin crisp edge highlights; rough 0.25
    # under a coat rendered a grey sheen, 46; rough 0.05 bare, 36 and crisp edges, the rest is our studio's backdrop)
    "goggle_outrigger": dict(image="goggle_outrigger.png", rough=0.05),
    # purple mirror (Damien): metallic purple with an interference film, purple square on, gold-orange at grazing
    # angles (his 08, 09); the little light the mirror lets through is tinted dark purple (eyes hidden)
    "goggle_lens_mirror": dict(rgb=[90, 30, 125], metal=0.94, rough=0.03, transmission=1.0,
                               thin_film=dict(thickness_nm=430, ior=1.33)),      # swatches: deep purple square on
    "goggle_lens_clear": dict(rgb=[120, 90, 150], rough=0.02, transmission=1.0),
}
MATERIALS["goggle_strap_in"] = H.MATERIALS["goggle_strap_in"]
# round 9: Leatt's woven elastic (goggle_strap_art.py): the Pinata print from Leatt's goggle ISO with the weave's
# albedo, the knit loops and selvedge ribs as a normal map at their measured scale, the white LEATT a raised print;
# a faint satin sheen and a low gloss: the MY27 back view's fabric reads deep and saturated (body 12/108/190, its
# dark loops at a quarter of that), where sheen 0.35 and the default gloss glazed it grey (104/142/195 for an albedo
# of 4/80/165). The band's side faces take the print's edge colour (no normal map: their UVs run along the edge).
MATERIALS["goggle_strap"] = dict(image="goggle_strap_print.jpg", normal="goggle_strap_print_n.png", rough=0.85,
                                 sheen=0.12, spec=0.25,
                                 detail=dict(image="goggle_strap_weave.png", mask="goggle_strap_mask.png",
                                             repeat=(0.6512 * 1000.0 / 19.0, 1.0),   # SA.STRAP_LEN_UV / SA.TILE_MM
                                             bump_strength=0.35))
# round 13: the strap's end behind the carrier (build_strap_ends) in the carrier's shade. Leatt's iso55 windows read
# the strap p50 4 to 6 (rows 870 to 900 and 1035 to 1085), its cut end's teal 22/42/40 (median; peak 61/90/85). Our
# studio's 1 m lights reach into the gap behind the C: in the strap's back colour (rgb 24) it rendered 64 to 66, the
# print's teal (110/158/136) 125/205/170 and rgb 16/46/42 32/63/59; so a near black and a dark teal
MATERIALS["goggle_strap_shade"] = dict(rgb=[3, 3, 4], rough=0.9, spec=0.0)
MATERIALS["goggle_strap_teal"] = dict(rgb=[11, 31, 28], rough=0.9, spec=0.1)
MATERIALS["goggle_strap_rim"] = dict(image="goggle_strap_print.jpg", rough=0.85, sheen=0.12, spec=0.25)
# round 11: the raised LEATT on the strap (goggle.strap_logo), an off-white rubber. Leatt's Pinata kit iso-right reads
# its top 226/222/219 (T bar, px 625..655, 835..848) with a lit 1 to 2 px lip at its lower edge; ours at the print's
# 236 clipped to 254 there (no edge could show), at 160 rendered 178: 1.27 times the albedo in linear, so 203/199/197
MATERIALS["goggle_strap_logo"] = dict(rgb=[203, 199, 197], rough=0.45)
# the silicone band inside the strap (translucent grey rubber, never seen worn)
MATERIALS["goggle_silicone"] = dict(rgb=[150, 150, 152], rough=0.5)
# the adjuster slides: moulded in a colour of the strap's design in Leatt's 5.5 back photos (strap base: Forge
# white, Fuel teal, Neon Yellow cyan; edge: MY27 Blue/Red and Royal navy; accent or black on others: ledger section
# 11). No photo shows the Pinata Teal's; by the brief's rule (Forge: the strap's base there; MY27: its edges, and
# the Pinata strap has no edge colour) the print's teal-green at the slides: the median of goggle_strap_print.jpg's
# middle band over the u the slides cover (0.41 to 0.45 and 0.55 to 0.60 on the built strap; top band 123/165/145,
# bottom 91/151/125). Satin; the moulded LEATT, triangle and dimples as a normal map.
MATERIALS["goggle_slide"] = dict(rgb=[112, 159, 138], rough=0.55, spec=0.35, normal="goggle_slide_n.png")


def write_strap_textures(outdir=None):
    """The strap's print, its weave tile and the slides' details (goggle_strap_art.py) into textures/rider."""
    import goggle_strap_art as SA
    outdir = outdir or TEXDIR
    assert abs(MATERIALS["goggle_strap"]["detail"]["repeat"][0] - SA.STRAP_LEN_UV * 1000.0 / SA.TILE_MM) < 1e-9
    info = SA.strap_textures(outdir)
    info.update(weave=SA.weave_tile(outdir))
    mm = 1.0
    SA.slide_texture(outdir, leatt=SLIDE_LEATT,
                     tab=dict(tri=TAB_TRI, groove=TAB_GROOVE, dots=TAB_DOTS, r=0.38 * mm, rim=0.62,
                              a_range=(8.6, 18.4)))
    return info

if __name__ == "__main__":
    # python3 goggle.py --free OUT.npz [TURN | TURN/TURN] [post]: the goggle alone (free_parts) for goggle_views.py,
    # its outriggers turned TURN deg out from straight back (side +1 / side -1; default OR_FREE_TURN); post: with the
    # clear posts on the plates (round 14: the Royal and the Forge photos show them, his goggle has none)
    if len(sys.argv) > 2 and sys.argv[1] == "--free":
        if len(sys.argv) > 3 and sys.argv[3] != "post":
            t_ = [float(a) for a in sys.argv[3].split("/")]
            OR_FREE_TURN = {1: t_[0], -1: t_[-1]}
        os.makedirs(TEXDIR, exist_ok=True)
        outrigger_texture(os.path.join(TEXDIR, "goggle_outrigger.png"))
        write_strap_textures()
        H.write_npz(sys.argv[2], free_parts(post="post" in sys.argv[3:]))
        print("wrote", sys.argv[2])
