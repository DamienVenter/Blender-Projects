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
  * parts.PIVOT and parts.PEG are readings on the photo's centre plane. Cast on the planes the parts are on, the
    pivot cap is at z 0.480 (not 0.462) and the peg's teeth at 0.412 to 0.425. The pivot stays on parts.PIVOT here
    (shared datum); the pegs follow the photos and the spec (422 mm).

Normals point out of every solid and parts that only touch a neighbour stop 0.2 to 0.5 mm short of it: the audit
(audit.py) measures clash depth along the normals and counts intersecting faces.
"""
import math

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.spatial import ConvexHull, cKDTree

import cams
from geom import Mesh, bolt, box, circle, frame_z, grid, plate2d, resample, rounded_rect, smooth_poly, tube
from parts import CHAIN_Y, P2, PEG, PIVOT, RA, R_REAR, STEER0, T_BOT_CLAMP, T_TOP_CLAMP, UP

REPLACES = ["frame", "swingarm", "shock", "exhaust", "controls"]
MATERIALS = {"shock_spring": dict(rgb=(28, 28, 30), metal=0.7, rough=0.4)}   # EST: dark behind the plate (LEFT col 2360)
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


def slab(outline, mid, t, mat, r=0.003, step=0.007, holes=(), to=None, mirror=True):
    """Plate cut to OUTLINE (2D) with rounded edges: mid(u, v) is the mid-surface's offset along the normal, T the
    thickness, R the edge radius, to(u, v, w) the map to 3D (MIRROR: it swaps handedness, as (u, v, w) -> (x, w, v)
    does). The side view stays the outline exactly; faces are turned so that every normal points out."""
    o = np.asarray(outline, float)
    r = min(r, 0.4 * t)
    ccw = float(np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])) > 0
    holes = [np.asarray(h, float) if ccw else np.asarray(h, float)[::-1] for h in holes]     # circle() runs counter-clockwise
    dense = np.vstack([resample(o, 0.0015)] + [resample(h, 0.0015) for h in holes])
    tree = cKDTree(dense)
    mid_f = mid if callable(mid) else (lambda u, v: mid)

    def f(u, v, w):
        d = tree.query((u, v))[0]
        k = 0.0 if d >= r else r - math.sqrt(max(r * r - (r - d) ** 2, 0.0))
        half = t / 2 - k
        return to(u, v, mid_f(u, v) + (half if w > 0 else -half))
    m = plate2d(o, holes, 1.0, mat, f, step=step, rings=(0.3 * r, r))
    flip_rim = mirror == ccw
    m.F = [q[::-1] if (mirror if len(q) == 3 else flip_rim) else q for q in m.F]
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
HEAD_LO = STEER0 + (T_BOT_CLAMP + 0.03) * UP
HEAD_L = (T_TOP_CLAMP - 0.02) - (T_BOT_CLAMP + 0.03)
F_LINK = np.array([0.5195, 0.0, 0.369])         # LEFT px (2298,1558), RIGHT px (1702,1557) cast at |y| 0.045
SHOCK_U = np.array([0.585, 0.0, 0.790])         # EST: upper eye; the adjuster seen at RIGHT px (1733,1109) lies beside it
SHOCK_A = np.array([0.448, 0.0, 0.329])         # LEFT px (2386,1607), RIGHT px (1611,1606): lower clevis bolt
LINK_T = np.array([0.385, 0.0, 0.375])          # LEFT px (2469,1552), RIGHT px (1524,1551): arm on the swingarm
LINK_B = np.array([0.382, 0.0, 0.326])          # LEFT px (2471,1617), RIGHT px (1524,1608): arm to link
CROSS_LO = np.array([0.545, 0.0, 0.388])        # EST: lower cross member behind the engine
CROSS_UP = np.array([0.632, 0.0, 0.805])        # EST: upper cross member that carries the shock
PEG_ROOT_Z = 0.4115                             # REAR row 1313 at y 0.14: 0.411; LEFT px (2257,1520): 0.413
PEG_TIP = (0.2475, 0.425)                       # REAR: tips at columns 1673 and 2328, row 1294: y 0.247, z 0.425
PEG_Y0 = 0.152
PEG_PIN = (PEG_Y0 - 0.006, PEG_ROOT_Z - 0.012)   # EST: hinge pin under the peg's root (y, z)


def _spar_y(x):
    """Outer face of the frame in plan: pivot plates measured (TOP, REAR); the spars run in to the head under the
    tank and shrouds, where no photo shows them (EST)."""
    return float(np.interp(x, [0.45, 0.62, 0.72, 0.82, 0.92, 1.00, 1.066], [0.137, 0.137, 0.128, 0.110, 0.084, 0.058, 0.040]))


def _frame_outline():
    """OUT2 'frame' (left photo) cast on the plate's mid plane. The frame is symmetric: the right photo's outline
    has the header, the hanger and the brake pedal fused into it and lacks the plate's rear half (hidden by the
    master cylinder), so both sides use this one; where both are clean they agree within 5 mm."""
    o = P2("frame", Y_PLATE - T_SPAR / 2)
    # the extraction's cut line and the dark ring of the pivot cap left a notch at the pivot: close it
    keep = ~((o[:, 0] > 0.52) & (o[:, 0] < 0.5745) & (o[:, 1] > 0.452) & (o[:, 1] < 0.492))
    return smooth_poly(o[keep], 2)


def _spar_top(x):
    return 0.786 + 0.632 * (x - 0.661)          # OUT2 'frame': top edge through (0.661,0.786) and (0.737,0.834)


def _bracket_outline():
    # footpeg bracket under the pivot plate (LEFT zoom: peg, black bolt and roller hang from it)
    return np.array([(0.535, 0.418), (0.548, 0.446), (0.572, 0.446), (0.592, 0.418), (0.594, 0.374), (0.582, 0.362),
                     (0.552, 0.362), (0.545, 0.385)])


def _sub_rails(s):
    """Subframe rails of side S: hidden under the seat and side panels in every photo (EST), kept under the seat's
    base and inside the side panels of the model; the mounts are measured: LEFT px (2313,1259) on the plate's rear
    edge and (2172,963) on its ear. On the right the lower rail passes outside the exhaust's mid pipe."""
    lower = spline([(0.522, s * 0.1015, 0.600), (0.495, s * 0.1005, 0.640), (0.470, s * 0.093, 0.676), (0.433, s * 0.088, 0.717),
                    (0.378, s * 0.095, 0.760), (0.30, s * 0.094, 0.800), (0.213, s * 0.082, 0.842)], 20)
    upper = spline([(0.612, s * 0.1015, 0.840), (0.590, s * 0.090, 0.856), (0.553, s * 0.070, 0.874), (0.482, s * 0.069, 0.876),
                    (0.409, s * 0.070, 0.882), (0.336, s * 0.070, 0.888), (0.262, s * 0.069, 0.894), (0.213, s * 0.068, 0.897)], 20)
    return lower, upper


def frame():
    m = Mesh()
    # steering head: tube with its two bearing cups (parts.py: between the clamps)
    L = HEAD_L
    m.add(turned(HEAD_LO, UP, [(-0.004, 0.026), (-0.004, 0.0335), (0.012, 0.0335), (0.016, 0.0305), (L - 0.016, 0.0305),
                               (L - 0.012, 0.0335), (L + 0.004, 0.0335), (L + 0.004, 0.026)], "alu_frame", 28))
    o = _frame_outline()
    br = _bracket_outline()
    for s in (1, -1):
        # spar and pivot plate: the photo outline, 26 mm deep with rounded edges, on the spar's path in plan
        m.add(slab(o, lambda x, z, s=s: s * (_spar_y(x) - T_SPAR / 2), T_SPAR, "alu_frame", r=0.005, step=0.009, to=_xz))
        # the spar under the shroud, up to the head (EST): 80 mm deep box, the visible part's top edge continued
        xs = np.array([0.74, 0.82, 0.90, 0.98, 1.035, 1.066])
        path = np.stack([xs, s * (np.array([_spar_y(x) for x in xs]) - T_SPAR / 2), _spar_top(xs) - 0.047], axis=1)
        m.add(bar(path, 0.0245, np.linspace(0.080, 0.088, len(xs)), "alu_frame"))
        # gusset between the spar's underside, the head and the down tube (EST)
        m.add(slab(np.array([(1.058, 0.940), (0.955, 0.888), (1.012, 0.800)]), s * 0.0245, 0.005, "alu_frame", r=0.002,
                   step=0.012, to=_xz))
        # pivot: boss on the plate (the plate's own front edge there is the extraction's cut line), pad, bolt
        m.add(slab(circle(0.040, 40, PIVOT[0], PIVOT[2]), s * (Y_PLATE - T_SPAR / 2 + 0.0004), T_SPAR + 0.0008, "alu_frame",
                   r=0.005, step=0.009, to=_xz))
        m.add(turned(PIVOT + s * (Y_PLATE - 0.0005) * Y3, s * Y3, [(0, 0.030), (0.003, 0.0285), (0.004, 0.022)], "alu_frame", 28))
        m.add(turned(PIVOT + s * 0.052 * Y3, s * Y3, [(0, 0.0085), (0.086, 0.0085)], "steel", 14))
        # footpeg bracket with the black socket bolt (LEFT px (2228,1562), RIGHT px (1770,1561)) and the hinge boss
        m.add(slab(br, s * 0.130, 0.022, "alu_cast", r=0.003, step=0.007, to=_xz))
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
    dt = spline([(1.078, 0, 0.952), (1.050, 0, 0.870), (1.020, 0, 0.775), (0.990, 0, 0.690), (0.962, 0, 0.625), (0.938, 0, 0.576),
                 (0.9145, 0, 0.452)], 18)
    m.add(bar(dt, 0.044, np.linspace(0.042, 0.030, len(dt)), "alu_frame"))
    # cross members between the plates (EST) and the lower chain roller (LEFT px (2298,1558))
    m.add(tube([CROSS_LO - 0.121 * Y3, CROSS_LO + 0.121 * Y3], 0.013, 16, "alu_frame"))
    m.add(tube([CROSS_UP - 0.115 * Y3, CROSS_UP + 0.115 * Y3], 0.015, 16, "alu_frame"))
    ro = np.array([0.521, CHAIN_Y, 0.376])
    m.add(slab(hull([(ro[0], ro[2], 0.011), (CROSS_LO[0], CROSS_LO[2], 0.012)]), CHAIN_Y - 0.0155, 0.007, "alu_frame", r=0.002,
               step=0.005, to=_xz))
    m.add(turned(ro - 0.012 * Y3, Y3, [(0, 0.008), (0.0005, 0.016), (0.004, 0.017), (0.008, 0.015), (0.014, 0.015), (0.018, 0.017),
                                      (0.0215, 0.016), (0.022, 0.008)], "plastic_black", 24))
    m.add(bolt(ro + 0.0098 * Y3, Y3, af=0.010, head_h=0.006, flange_d=0.018))
    return m


def subframe():
    m = Mesh()
    for s in (1, -1):
        lower, upper = _sub_rails(s)
        m.add(bar(lower, 0.018, 0.022, "alu_frame"))
        m.add(bar(upper, 0.018, 0.022, "alu_frame"))
        m.add(bar([lower[-1], upper[-1]], 0.016, 0.018, "alu_frame"))                  # tail strut
        # lug on the frame's ear, 0.2 mm inside the plate's inner face (the lower rail starts under the plate)
        m.add(slab(hull([(0.624, 0.833, 0.012), (0.603, 0.846, 0.010)]), s * 0.1068, 0.008, "alu_frame", r=0.002, step=0.005,
                   to=_xz))
    lo_l, up_l = _sub_rails(1)
    for p, r in ((up_l[-1], 0.009), (lo_l[-1], 0.008)):                                 # cross tubes at the tail
        m.add(tube([(p[0], -p[1], p[2]), (p[0], p[1], p[2])], r, 12, "alu_frame"))
    return m


# ---------------------------------------------------------------- swingarm
def _arm_top(x):
    """Top edge: OUT2 'swingarm' (0.052,0.369)-(0.446,0.482) and 'swingarm_R' (0.054,0.373)-(0.431,0.484)."""
    return 0.371 + 0.2906 * (np.asarray(x, float) - 0.053)


def _arm_bot(x):
    """Lower edge: OUT2 'swingarm_R' (0.059,0.337)-(0.332,0.380), then parallel to the top to (0.468,0.421)."""
    return np.interp(x, [-0.04, 0.059, 0.332, 0.468], [0.3215, 0.337, 0.380, 0.421])


def _arm_yo(x):
    """Outer face in plan: REAR rows 1480..1560 (cols 1811 and 2190: 0.129 at the axle and unchanged up the arm);
    in between the frame plates at the pivot (EST 0.110, the plates' inner faces are at 0.111)."""
    return np.interp(x, [-0.04, 0.30, 0.50, 0.56], [0.129, 0.129, 0.110, 0.109])


def _arm_w(x):
    return np.interp(x, [-0.04, 0.06, 0.25, 0.50], [0.031, 0.031, 0.038, 0.040])    # REAR: 0.098..0.129 at the axle


def swingarm():
    m = Mesh()
    sec = resample(rounded_rect(1.0, 1.0, 0.16, 3), 0.118)
    xs = np.unique(np.concatenate([np.linspace(0.052, 0.468, 12), [0.379, 0.400, 0.421, 0.50, 0.53, 0.548]]))
    for s in (1, -1):
        mat = "swing_L" if s > 0 else "swing_R"
        rings = []
        for x in xs:
            zt, zb = float(_arm_top(x)), float(_arm_bot(x))
            if x > 0.468:                                    # forged front end closing on the pivot tube
                k = (x - 0.468) / (0.548 - 0.468)
                zt = (1 - k) * float(_arm_top(0.468)) + k * (PIVOT[2] + 0.0265)
                zb = (1 - k) * 0.421 + k * (PIVOT[2] - 0.0265)
            w = float(_arm_w(x))
            yc = float(_arm_yo(x)) - w / 2
            ring = np.stack([np.full(len(sec), x), s * (yc + sec[:, 0] * w), (zt + zb) / 2 + sec[:, 1] * (zt - zb)], 1)
            rings.append(ring if s > 0 else ring[::-1])
        m.add(grid(Mesh(), rings, mat, cap0=True, cap1=True))
        m.add(hollow(PIVOT + s * 0.056 * Y3, s * Y3, 0.0265, 0.0105, 0.054, "alu_swingarm", 24))
        # machined end with the axle slot (LEFT px 2913..3022 x 1584..1663; OUT2 rear end x 0.052, z 0.300..0.371)
        end = np.array([(0.062, 0.3745), (-0.022, 0.3500), (-0.033, 0.3405), (-0.036, 0.3264), (-0.031, 0.309), (-0.012, 0.3005),
                        (0.062, 0.3000)])
        m.add(slab(end, s * (0.129 - 0.0155), 0.031, "alu_machined", r=0.003, step=0.007, to=_xz))
        # axle plate with its index marks, reference mark on the arm, adjuster bolt and lock nut
        m.add(slab(rounded_rect(0.046, 0.038, 0.004) + RA[[0, 2]], s * 0.1308, 0.004, "alu_machined", r=0.001, step=0.006, to=_xz))
        for k in range(-2, 3):
            m.add(box((RA[0] + 0.006 * k, s * 0.1328, RA[2] + 0.0155), (0.0011, 0.0006, 0.005 if k else 0.007), "anod_black"))
        m.add(box((RA[0], s * 0.1290, RA[2] + 0.0235), (0.0012, 0.0006, 0.006), "anod_black"))
        m.add(bolt((-0.0357, s * 0.1135, RA[2]), (-1, 0, 0), af=0.012, head_h=0.005, flange_d=0.014))
        m.add(turned((-0.0357, s * 0.1135, RA[2]), (-1, 0, 0), [(0, 0.004), (0.014, 0.004)], "bolt", 10))
        m.add(bolt((-0.0497, s * 0.1135, RA[2]), (-1, 0, 0), af=0.012, head_h=0.006, flange_d=0.013))
        # lug for the cushion arm under the cross member (OUT2 'swingarm_R' hangs to z 0.354 at x 0.33..0.39)
        m.add(slab(hull([(LINK_T[0], LINK_T[2], 0.017), (0.374, 0.414, 0.006), (0.410, 0.414, 0.006)]), s * 0.0375, 0.009,
                   "alu_swingarm", r=0.002, step=0.005, to=_xz))
    # axle ends: hollow head on the left, flanged nut on the right (REAR row 1540: -0.139 on the right, 0.129 left)
    m.add(turned(RA + 0.1326 * Y3, Y3, [(0, 0.008), (0, 0.018), (0.0025, 0.018), (0.0035, 0.0165), (0.0035, 0.008), (0, 0.008)],
                 "steel", 24, False, False))
    m.add(turned(RA + 0.1331 * Y3, Y3, [(0, 0.0082)], "anod_black", 16, True, False))
    m.add(bolt(RA - 0.1326 * Y3, -Y3, af=0.027, head_h=0.008, flange_d=0.037, mat="steel"))
    m.add(hollow(RA - 0.1326 * Y3, -Y3, 0.0115, 0.007, 0.0105, "steel", 18))
    # cross member behind the shock (EST: between the shock's spring seat and the tyre), ending in the arms' walls
    zc = (float(_arm_top(0.40)) + float(_arm_bot(0.40))) / 2
    yi = float(_arm_yo(0.40)) - float(_arm_w(0.40)) + 0.002
    m.add(bar([(0.400, -yi, zc), (0.400, 0.0, zc), (0.400, yi, zc)], 0.042, 0.056, "alu_swingarm"))
    # chain slider: black strip under and over the left arm's front and round the pivot
    # (LEFT zoom: top px 2332..2625, bottom px 2310..2454)
    lowr = [(x, float(_arm_bot(min(x, 0.468))) + max(x - 0.468, 0) * 0.175 - 0.0035) for x in np.linspace(0.41, 0.54, 6)]
    arc = [(PIVOT[0] + 0.0305 * math.cos(a), PIVOT[2] + 0.0305 * math.sin(a)) for a in np.radians(np.arange(-75, 76, 15))]
    topr = [(x, min(float(_arm_top(x)), float(_arm_top(0.468)) + (PIVOT[2] + 0.0265 - float(_arm_top(0.468))) *
                    max(x - 0.468, 0) / 0.08) + 0.0035) for x in np.linspace(0.54, 0.28, 12)]
    sl = np.array([(x, CHAIN_Y, z) for x, z in lowr + arc + topr])
    hs = np.full(len(sl), 0.006)
    hs[-3:] = (0.008, 0.011, 0.011)                           # thicker rub block at the strip's rear end
    m.add(bar(sl, 0.024, hs, "plastic_black"))
    return m


def chain_guide():
    """Chain guide under the left arm: two aluminium plates hung 0.3 mm under the arm, tied by two bolts with their
    spacers, and the two wear blocks the chain runs between (LEFT px 2735..2834 x 1624..1752: x 0.107..0.185,
    z 0.229..0.328). Centred on parts.CHAIN_Y."""
    m = Mesh()

    def zt(x):
        return float(_arm_bot(x)) - 0.0003
    ties = ((0.192, zt(0.196) - 0.0085), (0.122, zt(0.122) - 0.0085))
    gp = np.array([(0.196, ties[0][1]), (0.196, zt(0.196)), (0.112, zt(0.112)), (0.100, 0.300), (0.103, 0.240), (0.120, 0.226),
                   (0.184, 0.243), (0.196, 0.275)])
    for dy in (-0.0185, 0.0185):
        m.add(slab(gp, CHAIN_Y + dy, 0.003, "alu_machined", r=0.001, step=0.007, holes=[circle(0.011, 20, 0.150, 0.312)], to=_xz))
    for x, z in ties:
        m.add(tube([(x, CHAIN_Y - 0.0205, z), (x, CHAIN_Y + 0.0205, z)], 0.004, 10, "bolt"))
        m.add(bolt((x, CHAIN_Y + 0.0198, z), Y3, af=0.010, head_h=0.005))
        m.add(bolt((x, CHAIN_Y - 0.0198, z), -Y3, af=0.010, head_h=0.005))
    a = math.radians(19.0)                                    # the lower chain run's slope there
    e = np.array([math.cos(a), 0.0, math.sin(a)])
    for dz in (-0.017, 0.017):
        c = np.array([0.158, CHAIN_Y, 0.2585 + dz])
        m.add(bar([c + e * q for q in np.linspace(-0.033, 0.033, 9)], 0.0336, 0.010, "plastic_black"))
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
WELDS = ((0.913, -0.146, 0.545), (0.690, -0.124, 0.624))      # RIGHT px (2213,1344) and (1916,1240)
CLAMPS = ((0.635, -0.116, 0.626), (0.376, -0.128, 0.6435))    # RIGHT px (1844,1238) and (1500,1223)
HEADER = [
    PORT,
    (0.9146, 0.000, 0.6101),  # 12 mm along PORT_DIR
    (0.9200, -0.012, 0.6085), # EST: hard right in the 30 mm between the head and the down tube (hidden by the radiator)
    (0.9235, -0.031, 0.605),  # EST
    (0.936, -0.050, 0.598),   # EST
    (0.957, -0.061, 0.588),   # RIGHT px (2274,1277): the pipe comes out from behind the radiator, front edge x 0.985
    (0.967, -0.064, 0.568),
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
    (0.585, -0.088, 0.627),   # EST: behind the right pivot plate (its inner face is at -0.111)
    (0.530, -0.068, 0.626),   # EST: between the subframe's lower rail and the shock's spring
    (0.470, -0.072, 0.628),   # EST
    (0.420, -0.100, 0.636),   # EST
    (0.376, -0.128, 0.6435),  # RIGHT px (1500,1223): clamp at the muffler's inlet
    (0.352, -0.127, 0.649),   # into the muffler's nose
]
# muffler: lower edge and rear face from OUT2 'muffler' (right photo, cast at y -0.14); top edge seen at the rear only
# (0.893 at x 0..0.024), then hidden by the side panel: it is run 3 mm above the panel's edge in the photo
# ((0.152,0.844) (0.224,0.805) (0.267,0.746)), the lowest line the photo allows, EST; nose at the rivets seen at
# RIGHT px (1431,1181) and (1408,1220)
MUF_LOW = ([-0.008, -0.0065, -0.004, 0.0, 0.008, 0.018, 0.029, 0.07, 0.113, 0.195, 0.245, 0.301, 0.350],
           [0.818, 0.813, 0.811, 0.806, 0.797, 0.787, 0.775, 0.757, 0.731, 0.688, 0.664, 0.640, 0.628])
MUF_TOP = ([-0.008, -0.0065, -0.004, 0.0, 0.008, 0.018, 0.029, 0.152, 0.224, 0.267, 0.350],
           [0.886, 0.8905, 0.893, 0.8945, 0.8935, 0.890, 0.8865, 0.847, 0.808, 0.750, 0.672])
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
    yc = float(np.interp(x, [-0.008, MUF_CONE[0], MUF_CONE[1]], [-0.138, -0.127, -0.127]))
    hw = float(np.interp(x, [-0.008, -0.0065, -0.004, MUF_CONE[0], MUF_CONE[1]], [0.050, 0.054, 0.056, 0.046, 0.023]))
    return zl, zt, yc, hw


def _muf_ring(x):
    zl, zt, yc, hw = _muf(x)
    k = min(max((x - MUF_CONE[0]) / (MUF_CONE[1] - MUF_CONE[0]), 0.0), 1.0)    # the cone turns the section into a circle
    ang = np.arctan2(MUF_SEC[:, 1], MUF_SEC[:, 0])
    S = (1 - k) * MUF_SEC + k * np.stack([np.cos(ang), np.sin(ang)], axis=1)
    return np.stack([np.full(len(S), x), yc - S[:, 0] * hw, (zl + zt) / 2 + S[:, 1] * (zt - zl) / 2], axis=1)


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
    # flange at the port with its two nuts
    c, d, r = np.array(PORT), np.array(PORT_DIR) / np.linalg.norm(PORT_DIR), rr[0]
    m.add(turned(c, d, [(0.0, 0.033), (0.006, 0.033), (0.006, r)], "steel", 6))
    side = np.cross(d, [0, 0, 1.0])
    side /= np.linalg.norm(side)
    for q in (-1, 1):
        m.add(bolt(c + d * 0.0058 + side * q * 0.0265, d, af=0.010, head_h=0.006, flange_d=0.012))
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
    # mounts: two straps from the can's inner top edge to the underside of the right subframe rail, bolted
    # (hidden by the side panel, EST)
    low = _sub_rails(-1)[0][::-1]
    for x in (0.220, 0.255):
        ry, rz = float(np.interp(x, low[:, 0], low[:, 1])), float(np.interp(x, low[:, 0], low[:, 2]))
        zl, zt, yc, hw = _muf(x)
        k = min(max((x - MUF_CONE[0]) / (MUF_CONE[1] - MUF_CONE[0]), 0.0), 1.0)
        fy, fz = yc + 0.5 * hw, zt - (0.006 + 0.03 * k)
        zr = rz - 0.011 - 0.0065                                 # strap 4 mm thick, just under the sloping rail
        m.add(bar([(x, fy, fz), (x, fy + 0.3 * (ry - fy), fz + 0.75 * (zr - fz)), (x, ry - 0.006, zr), (x, ry + 0.006, zr)],
                  0.012, 0.004, "steel"))
        m.add(bolt((x, ry, zr - 0.0018), (0, 0, -1), af=0.010, head_h=0.005))
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


PARTS = {"frame": frame, "subframe": subframe, "swingarm": swingarm, "chain_guide": chain_guide, "linkage": linkage,
         "shock": shock, "exhaust": exhaust, "footpegs": footpegs, "rear_brake": rear_brake}
SMOOTH = {"footpegs": 30}
