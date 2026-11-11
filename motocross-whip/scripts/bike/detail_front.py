"""Front end in detail (plugin of parts.py): Showa 49 mm fork, triple clamps, Renthal Fatbar, hand controls, front
brake, disc cover, and the cables and hoses that leave the handlebar.

Frame: metres, x forward, y left, z up, axle-line frame of parts.py. Most of it is written in the FORK frame
fk(f, y, t): f ahead of the plane of the two tube axes, y left, t up the tubes from the axle's height (parts.on_tube).
The hand controls are written in a GRIP frame per side (_Side.p): a inboard of the bar end along the grip, f ahead of
it, u up.

Sources, tagged on every number: SPEC (research/crf250r-2026.md), LEFT / RIGHT / FRONT / TOP (Honda's studio photos
through cams.CAMS; rows, columns or the scan that gave it), DET (Honda's detail photos 475829, 475830, 475831, 475835:
what the part looks like, no dimensions), EST (real part's usual size, not visible in any photo).
Scans (scratch, reproducible with rowscan.py): class runs across the left tube at t 0.33..0.96 ("across"), along its
axis ("axis"), front photo rows 600..1020 on the tubes' plane ("front"), bar black per column of the front photo and
per row of the top photo ("bars_front", "bars_top"), the hose's black over the plate rows 230..610 ("hose").
"""
import math

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.spatial import ConvexHull

import cams
import parts as P
from geom import Mesh, bolt, box, circle, grid, plate2d, rounded_rect, tube
from parts import AXLE_LEAD, BACK, CLAMP_OFFSET, FA, FORK_HALF, TUBE0, UP

Y = np.array([0.0, 1.0, 0.0])
Z = np.array([0.0, 0.0, 1.0])
FWD = -BACK
RF = np.column_stack([FWD, Y, UP])                    # fork frame as a rotation (box sizes: f, y, t)
F_STEER = -CLAMP_OFFSET                               # the steering axis in the fork frame (f)

# ---------------------------------------------------------------- measured levels (t along the tubes)
T_SEAL = 0.354                                        # LEFT axis: dust seal black 0.348..0.354, gold above
T_LO = (0.662, 0.716)                                 # FRONT rows 630, 660 silver, 600 and 690 gold; LEFT axis 0.652..
T_UP = (0.884, 0.928)                                 # LEFT + RIGHT axis: silver 0.884..0.928
T_TUBE_TOP = 0.933                                    # LEFT axis: tube stands 5 mm proud of the top clamp (DET 475835)
R_BOSS_LO = 0.0325                                    # FRONT rows 630, 660: lower clamp out to |y| 0.130..0.132
R_BOSS_UP = 0.0305                                    # EST (5 mm wall): yields to the number plate, whose wing comes
#   within 31.1 mm of the tube axis ahead and outboard of the top clamp (plastics, measured)
FACE_LO = T_LO[1] - 0.001                             # lower clamp's upper face, along the steering axis
FACE_UP = T_UP[1] - 0.015                             # top clamp's underside: bridge 15 mm thick between the bosses, EST
STEM_R = 0.0145                                       # EST: the stem is the only part inside the frame's head tube
FENDER_T = 0.003                                      # build_bike.py solidifies the fender 3 mm inwards
R_INNER = 0.0245                                      # SPEC: 49 mm inner tubes
T_BAR = 0.968                                         # bar centre, EST: the holders' caps and bolts reach 27 mm above
#   it and must stay under the bar pad's measured top (PAD_T)
F_BAR = F_STEER + 0.003                               # TOP rows 1045, 1180: pad centred on x 0.988
YC = 0.152                                            # TOP rows 1270..1360: the bar is straight across out to here
R_GRIP = 0.0158                                       # where the end lip's rounded rim reaches furthest out
# The bar ends sit on cams.BAR_END: both side photos, the rear photo and the top photo agree on it.
_TXZ = (cams.BAR_END[0], cams.BAR_END[2])
_C0X = float((TUBE0 + F_BAR * FWD + T_BAR * UP)[0])
UPSWEEP = math.radians(1.85)                          # the grips rise outwards: FRONT top edge falls 4.5 mm from a 8 to
#   104, REAR top 4.6 and bottom 1.7 (axis 3.1 mm over 96 mm with the grip's 2.8 mm taper taken out; component 1)
SWEEP = 0.25                                          # plan angle of the grips: from the corner at YC to the bar end
for _ in range(4):                                    # (TOP rows 685..1585 give 0.288 = 16 deg to the photo's bar end)
    SWEEP = math.atan((_C0X - _TXZ[0]) / (cams.BAR_END[1] - R_GRIP * math.sin(SWEEP) - YC))
TIP = np.array([_TXZ[0], cams.BAR_END[1] - R_GRIP * math.sin(SWEEP), _TXZ[1]])    # grip end centre: the end face is
#   swept back, so its outer rim, not its centre, makes the 827 mm overall width (SPEC)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def _outward(m):
    """Wind a closed piece so that its normals point outwards (signed volume): the audit's depth test and the
    bar pad's lettering both read the normals."""
    v = np.asarray(m.V, float)
    v = v - v.mean(axis=0)
    vol = 0.0
    for f in m.F:
        q = v[list(f)]
        for i in range(1, len(f) - 1):
            vol += float(q[0] @ np.cross(q[i], q[i + 1]))
    if vol < 0:
        m.F = [tuple(reversed(f)) for f in m.F]
    return m


def fk(f, y, t):
    """Fork frame to bike frame."""
    return TUBE0 + f * FWD + y * Y + t * UP


# Bar pad, in the fork frame: it leans with the steering axis and its section is the same along its length.
PAD_F = (-0.0545, 0.0315)     # rear face: LEFT rows 505..560 and RIGHT rows 510..560 on the end plane y +-0.106, the
#   cap's rear edge stays 53..57 mm behind the tubes' plane from t 0.947 to 0.995 (so the lean is the fork's, RAKE);
#   front face: the mirror of it about the top face's centre, and TOP u 1662..1684 (second line of lettering)
PAD_T = (0.945, 1.001)        # underside: LEFT / RIGHT axis scans (cap black from t 0.946), corners at 0.947, REAR col
#   2000 (red down to row 345, 0.941); top: FRONT cols 1960..2040 (rows 250..258, z 1.208..1.203) with TOP u 1708
PAD_SHOULDER = (0.0185, 0.013)                        # rounded shoulders, deep and high: TOP emblem band u 1708..1762,
#   lettering bands u 1684..1708 and 1762..1775, rear edge u 1775 (x 0.951); REAR col 2000 lettering rows 276..294
PAD_Y = (0.0875, 0.106)       # red body, and with the grey end caps: TOP cols 1712..1744 (red v 1025..1225, dark to
#   1001 and 1244), REAR rows 290..310 (red u 1890..2109, dark caps outside)
PAD_HALF = ((PAD_F[1] - PAD_F[0]) / 2, (PAD_T[1] - PAD_T[0]) / 2)        # 86 mm fore-aft, 56 mm tall
PAD_C = fk((PAD_F[0] + PAD_F[1]) / 2, 0, (PAD_T[0] + PAD_T[1]) / 2)      # its centre (axle-line frame)
PAD_TILT = P.RAKE                                     # lean back, radians


def pad_section():
    """The pad's section (f, t), counter-clockwise from the front lower corner."""
    (f0, f1), (t0, t1), (a, b) = PAD_F, PAD_T, PAD_SHOULDER
    ph = np.linspace(0, math.pi / 2, 7)
    front = [(f1 - a + a * math.cos(q), t1 - b + b * math.sin(q)) for q in ph]
    rear = [(f0 + a - a * math.cos(q), t1 - b + b * math.sin(q)) for q in ph[::-1]]
    return np.array([(f1 - 0.003, t0), (f1, t0 + 0.003)] + front + rear + [(f0, t0 + 0.003), (f0 + 0.003, t0)])




def fyz(f, y, z):
    """Point f ahead of the tubes' plane at lateral y and height z (front-photo readings)."""
    return fk(f, y, (z - TUBE0[2] - f * FWD[2]) / UP[2])


def rev(o, axis, prof, mat, seg=24, cap0=False, cap1=False, ref=None, arc=None, solid=False):
    """Profile [(radius, height)] turned about AXIS through O: a full turn, or the ARC (a0, a1) measured from REF
    towards axis x REF. solid: the profile is a closed loop (outer wall then inner wall, same number of points)."""
    a = unit(axis)
    if ref is None:
        ref = Z if abs(a[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = unit(ref - (ref @ a) * a)
    v = np.cross(a, u)
    ang = np.linspace(0, 2 * math.pi, seg, endpoint=False) if arc is None else np.linspace(arc[0], arc[1], seg)
    ring = np.outer(np.cos(ang), u) + np.outer(np.sin(ang), v)
    rings = [np.asarray(o, float) + a * h + r * ring for r, h in prof]
    if solid:
        rings.append(rings[0])
    m = grid(Mesh(), rings, mat, closed_u=arc is None, cap0=cap0, cap1=cap1)
    if solid and arc is not None:                     # close the two ends of the arc
        k = len(prof)
        for col, flip in ((0, False), (seg - 1, True)):
            for i in range(k // 2 - 1):
                q = (i * seg + col, (i + 1) * seg + col, (k - 2 - i) * seg + col, (k - 1 - i) * seg + col)
                m.face(q[::-1] if flip else q, mat)
    return _outward(m) if (arc is None or solid) else m


def cyl(p0, p1, r, mat, seg=20, ch=0.0):
    """Capped cylinder from p0 to p1, edges chamfered by ch."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ln = np.linalg.norm(p1 - p0)
    prof = [(r - ch, 0.0), (r, ch), (r, ln - ch), (r - ch, ln)] if ch > 0 else [(r, 0.0), (r, ln)]
    return rev(p0, p1 - p0, prof, mat, seg, cap0=True, cap1=True)


def ball(c, r, mat, seg=14):
    lat = np.linspace(0.3, math.pi - 0.3, 7)
    return rev(c, Z, [(r * math.sin(a), -r * math.cos(a)) for a in lat], mat, seg, cap0=True, cap1=True)


def slab(outline, h0, h1, mat, to3d, ch=0.0015):
    """Outline (n, 2) extruded from h0 to h1 through to3d(p, q, h), edges chamfered (outline star-shaped)."""
    o = np.asarray(outline, float)
    c = o.mean(axis=0)
    ins = c + (o - c) * (1.0 - ch / np.linalg.norm(o - c, axis=1).mean())
    lev = [(ins, h0), (o, h0 + ch), (o, h1 - ch), (ins, h1)] if ch > 0 else [(o, h0), (o, h1)]
    rings = [np.array([to3d(p[0], p[1], h) for p in loop]) for loop, h in lev]
    return _outward(grid(Mesh(), rings, mat, cap0=True, cap1=True))


def spline(pts, n):
    q = np.asarray(pts, float)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))])
    return CubicSpline(s, q)(np.linspace(0, s[-1], n))


def sweep(pts, r, mat, seg=10, n=None):
    q = np.asarray(pts, float)
    if n is None:
        n = max(8, int(np.linalg.norm(np.diff(q, axis=0), axis=1).sum() / 0.007))
    return tube(spline(q, n), r, seg, mat)


def loop_from_half(half):
    """Closed outline from its y >= 0 half ((f, y), front centre round to rear centre), corners cut twice."""
    h = np.asarray(half, float)
    full = np.vstack([h, h[-2:0:-1] * [1, -1]])
    for _ in range(2):
        nxt = np.roll(full, -1, axis=0)
        full = np.stack([0.75 * full + 0.25 * nxt, 0.25 * full + 0.75 * nxt], axis=1).reshape(-1, 2)
    return full


# ================================================================ fork
def fork():
    """Showa 49 mm coil-spring fork: gold outer tubes, chrome inner tubes, dust seals, caps with adjuster and bleed
    screw, cast axle lugs with pinch bolts (and the caliper ears on the left), axle with its nut."""
    m = Mesh()
    lug = "fork_lug"
    for side in (-1, 1):
        y = side * FORK_HALF
        o = fk(0, y, 0)
        # outer tube. LEFT across: 51 mm at t 0.50..0.76, 58 mm seal housing with two grooves at 0.36..0.385 (EST length:
        # it ends under the fork guard's neck, which is 27.5 mm inside from t 0.40);
        # FRONT rows 690..990: 46..48 mm (y 74..120); the brief's 48..53. 53 mm inside the lower clamp is EST.
        prof = [(0.0262, T_SEAL), (0.0290, 0.357), (0.0290, 0.3625), (0.0279, 0.364), (0.0279, 0.367),
                (0.0290, 0.3685), (0.0290, 0.3745), (0.0279, 0.376), (0.0279, 0.379), (0.0290, 0.3805),
                (0.0290, 0.385), (0.0252, 0.393), (0.0250, 0.397), (0.0250, 0.600), (0.0265, 0.650), (0.0265, 0.725),
                (0.0255, 0.760), (0.0255, T_TUBE_TOP - 0.0015), (0.0243, T_TUBE_TOP)]
        m.add(rev(o, UP, prof, "fork_gold", 40, cap1=True))
        # dust seal (LEFT axis: black 0.348..0.354) and inner tube (LEFT axis: bright metal 0.292..0.346)
        m.add(rev(o, UP, [(R_INNER + 0.0003, 0.3425), (0.0262, 0.345), (0.0270, 0.351), (0.0262, T_SEAL + 0.001)],
                  "rubber_black", 32))
        m.add(rev(o, UP, [(R_INNER, 0.066), (R_INNER, 0.400)], "chrome", 32))
        # fork cap (DET 475835: black cap in the tube's mouth), compression adjuster and bleed screw (EST sizes)
        m.add(rev(o, UP, [(0.0222, T_TUBE_TOP - 0.001), (0.0222, 0.9365), (0.0205, 0.938)], "anod_black", 28,
                  cap1=True))
        m.add(bolt(fk(0, y, 0.938), UP, af=0.014, head_h=0.004, flange_d=0.019, mat="alu_machined"))
        m.add(cyl(fk(0, y, 0.942), fk(0, y, 0.9432), 0.0038, "steel", 12))
        m.add(box(fk(0, y, 0.9434), (0.0066, 0.0011, 0.0006), "rubber_black", RF))            # screwdriver slot
        m.add(bolt(fk(0.013, y, 0.938), UP, af=0.0052, head_h=0.0022, mat="steel", kind="cap"))    # air bleed
        # (the socket's top is a collar for the fork guard's foot: the guard starts at t 0.053, LEFT axis red from
        # 0.056; its inboard wall is 28.0 mm from the tube axis inside, audit; the collar is 27.7)
        # axle lug: socket round the foot of the inner tube, web to the axle boss 39.6 mm ahead (parts.AXLE_LEAD),
        # chin under the axle with a slit and two pinch bolts from the front (EST layout; DET 475831 for the look)
        m.add(rev(o, UP, [(0.020, -0.022), (0.0285, -0.017), (0.031, -0.008), (0.031, 0.036), (0.0277, 0.040),
                          (0.0277, 0.064), (0.0262, 0.070), (R_INNER + 0.0002, 0.072)], lug, 32, cap0=True))
        pts = np.vstack([circle(0.025, 24, AXLE_LEAD, 0.0), [(-0.020, -0.020), (-0.026, 0.036), (0.026, 0.040), (AXLE_LEAD + 0.004, -0.0386),
                         (AXLE_LEAD - 0.012, -0.038), (AXLE_LEAD + 0.020, -0.038), (AXLE_LEAD + 0.020, -0.022)]])
        hull = pts[ConvexHull(pts).vertices]
        m.add(slab(hull, 0.078, 0.122, lug, lambda f, t, h, s=side: fk(f, s * h, t), ch=0.002))
        m.add(cyl(FA + side * 0.074 * Y, FA + side * 0.126 * Y, 0.024, lug, 28, 0.002))
        m.add(box(fk(AXLE_LEAD + 0.004, side * 0.100, -0.0295), (0.0016, 0.0446, 0.018), "rubber_black", RF))
        for dy in (-0.012, 0.012):
            m.add(bolt(fk(AXLE_LEAD + 0.020, side * 0.100 + dy, -0.030), FWD, af=0.010, flange_d=0.013))
    # caliper ears on the left lug (DET 475831: two bolts behind the leg), webs into the socket
    for f, t in CAL_EARS:
        m.add(cyl(fk(f, 0.083, t), fk(f, 0.105, t), 0.009, lug, 20, 0.0015))
        m.add(box(fk(f + 0.006, 0.094, t), (0.012, 0.022, 0.016), lug, RF))
    # axle (EST 20 mm), head on the right, nut on the left (DET 475831: hex in the centre of the disc cover)
    m.add(cyl(FA - 0.126 * Y, FA + 0.126 * Y, 0.010, "steel", 20))
    m.add(bolt(FA - 0.126 * Y, -Y, af=0.027, head_h=0.006, mat="steel", kind="cap"))
    m.add(bolt(FA + 0.126 * Y, Y, af=0.022, head_h=0.010, flange_d=0.032, mat="steel"))
    return m


CAL_EARS = ((-0.036, 0.036), (-0.040, -0.006))         # (f, t) of the caliper bracket bolts on the left lug, EST


# ================================================================ triple clamps
_FENDER = []


def _fender_skin(x, y, default=0.962):
    """Height of the front fender's outer surface at (x, y): the mesh of the fender in use (the plastics plugin's
    if it replaces it), linear between its vertices, so the bosses follow the fender."""
    try:
        if not _FENDER:
            from scipy.interpolate import LinearNDInterpolator
            fn = P.plastics.front_fender
            try:
                import detail_plastics
                fn = detail_plastics.PARTS.get("front_fender", fn)
            except Exception:
                pass
            v = np.asarray(fn().V, float)
            v = v[(v[:, 0] < 1.30) & (np.abs(v[:, 1]) < 0.065)]
            _FENDER.append(LinearNDInterpolator(v[:, :2], v[:, 2]))
        z = float(_FENDER[0](x, y))
        return z if np.isfinite(z) else default
    except Exception:
        return default


def _pinch(m, t0, t1, mat):
    """Rear pinch lug of a clamp boss with its slit and two bolts, both sides. LEFT (1516, 880): a flange bolt
    faces out at t 0.668, 31 mm behind the tube axis (lower clamp); the top clamp's are EST (the two bolt heads
    seen ahead of the top clamp at t 0.893 and 0.910 leave no room behind the number plate for a lug)."""
    tc, h = (t0 + t1) / 2, t1 - t0 - 0.004
    for side in (-1, 1):
        m.add(box(fk(-0.0375, side * FORK_HALF, tc), (0.019, 0.030, h), mat, RF))
        m.add(box(fk(-0.0375, side * FORK_HALF, tc), (0.0196, 0.0016, h + 0.0006), "rubber_black", RF))
        for t in (t0 + 0.012, t1 - 0.012):
            m.add(bolt(fk(-0.0375, side * (FORK_HALF + 0.015), t), side * Y, af=0.010, flange_d=0.014))


def _boss(side, tt, r, r_in, mat):
    """Clamp boss as a ring round the tube: the tube runs through its bore untouched."""
    ch = 0.002
    prof = [(r_in, tt[0]), (r - ch, tt[0]), (r, tt[0] + ch), (r, tt[1] - ch), (r - ch, tt[1]), (r_in, tt[1])]
    return rev(fk(0, side * FORK_HALF, 0), UP, prof, mat, 48, solid=True)


def _bridge(front, rear, r_mid):
    """Outline (f, y) of a clamp's bridge from its y >= 0 half: front edge, a notch that follows the middle of the
    boss's wall round the tube, rear edge."""
    notch = [(r_mid * math.cos(a), FORK_HALF + r_mid * math.sin(a))
             for a in np.radians([-50, -70, -90, -110, -130, -150])]
    return loop_from_half(front + notch + rear)


def clamps():
    """Lower clamp (cast, with the fender bosses and the fender nose), top clamp (machined, stem nut), steering
    stem."""
    m = Mesh()
    cast, mach = "alu_cast", "alu_machined"
    # (rear edge EST: it yields to the frame's down tube, 22 mm behind the steering axis at s 0.70)
    # ---- lower clamp: bosses FRONT rows 630..660 (|y| 0.073..0.131), LEFT across t 0.66..0.69 (36 mm ahead of the
    # axis, 55 mm behind it at the stem)
    for side in (-1, 1):
        m.add(_boss(side, T_LO, R_BOSS_LO, 0.0269, cast))
    low = _bridge([(0.024, 0.0), (0.025, 0.040), (0.024, 0.064)],
                  [(-0.036, 0.062), (-0.041, 0.040), (-0.0425, 0.015), (-0.0425, 0.0)], (0.0269 + R_BOSS_LO) / 2)
    m.add(slab(low, T_LO[0] + 0.006, FACE_LO, cast, fk, ch=0.002))
    _pinch(m, T_LO[0], T_LO[1], cast)
    m.add(cyl(fk(F_STEER, 0, T_LO[0] - 0.006), fk(F_STEER, 0, T_LO[0] + 0.008), 0.018, cast, 28, 0.002))  # stem foot
    for f, yb in ((0.010, 0.036), (-0.034, 0.034)):                # fender bosses under the clamp (EST positions)
        for side in (-1, 1):
            m.add(cyl(fk(f, side * yb, T_LO[0] - 0.002), fk(f, side * yb, T_LO[0] + 0.008), 0.0085, cast, 16, 0.001))
    # fender nose: two arms run forward under the number plate's lower edge (t 0.684) to bosses that stop 0.3 mm under the
    # fender's inner skin at x 1.236 (the fender of plastics.py starts at x 1.218 with its top at z 0.968)
    sec = rounded_rect(2.0, 1.2, 0.35, 3)
    for side in (-1, 1):
        yb, xb = side * 0.024, 1.236
        ring = [(0.0, 0.0)] + [(0.0075 * math.cos(a), 0.0075 * math.sin(a))
                               for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
        zb = min(_fender_skin(xb + dx, yb + dy) for dx, dy in ring) - FENDER_T - 0.0003     # 0.3 mm short of the skin
        skin = min(_fender_skin(x, yb + dy) for x in (1.221, 1.229, 1.240) for dy in (-0.007, 0.007))
        e = np.array([xb, yb, skin - 0.0105])                        # the arm stays 3 mm under the inner skin
        a = fk(0.078, yb, 0.670)
        m.add(tube([fk(0.016, yb, 0.670), fk(0.050, yb, 0.670), a, e + 0.007 * unit(e - a)], 0.0075, len(sec), cast,
                   section=sec))
        m.add(cyl(e - 0.003 * Z, [xb, yb, zb], 0.0075, cast, 16, 0.001))
    # ---- top clamp: LEFT / RIGHT axis silver t 0.884..0.928
    for side in (-1, 1):
        m.add(_boss(side, T_UP, R_BOSS_UP, 0.0259, mach))
    top = _bridge([(0.017, 0.0), (0.017, 0.045), (0.016, 0.066)],
                  [(-0.036, 0.066), (-0.054, 0.048), (-0.062, 0.020), (-0.063, 0.0)], (0.0259 + R_BOSS_UP) / 2)
    m.add(slab(top, FACE_UP, T_UP[1] - 0.0005, mach, fk, ch=0.002))
    _pinch(m, T_UP[0], T_UP[1], mach)
    # ---- stem: the only part between the two faces within the head tube's radius; nut and washer (EST 30 mm)
    m.add(cyl(fk(F_STEER, 0, T_LO[0] - 0.0055), fk(F_STEER, 0, T_UP[1] + 0.011), STEM_R, "steel", 24, 0.001))
    m.add(bolt(fk(F_STEER, 0, T_UP[1]), UP, af=0.030, head_h=0.008, flange_d=0.040, mat="steel"))
    for side in (-1, 1):                                           # nuts of the bar holders' studs
        m.add(bolt(fk(F_BAR, side * HOLDER_Y, FACE_UP), -UP, af=0.012, head_h=0.007, mat="steel"))
    return m


# ================================================================ handlebar and hand controls
HOLDER_Y = 0.046                                      # EST: bar holders 92 mm apart
CTRL_SHIFT = (0.017, 0.019)   # left and right controls moved inboard to clear the grips' flanges (TOP: switch housing
#   from a 122, throttle housing from a 122 on the right); each control is measured again in its own component


class _Side:
    """Grip frame of one side: p(a, f, u) is a metres inboard of the bar end along the grip, f ahead, u up.
    shift: added to every a (the hand controls moved inboard when the grips grew to their measured length; each
    control is placed again from the photos in its own component)."""

    def __init__(self, side, shift=0.0):
        self.side = side
        self.shift = shift
        self.T = TIP * [1, side, 1]
        dh = np.array([-math.sin(SWEEP), side * math.cos(SWEEP), 0.0])
        self.d = math.cos(UPSWEEP) * dh + math.sin(UPSWEEP) * Z                # along the grip, outwards (and up)
        self.f = np.array([math.cos(SWEEP), side * math.sin(SWEEP), 0.0])       # ahead of the grip
        self.u = -math.sin(UPSWEEP) * dh + math.cos(UPSWEEP) * Z               # up, square to the grip

    def p(self, a, f=0.0, u=0.0):
        return self.T - (a + self.shift) * self.d + f * self.f + u * self.u


# ================================================================ grips (Honda stock, 53165 / 53140 group)
# Anatomy and sources: research/detail-ledger/front.md, component 1. a is measured inboard from the end face (mm in
# the comments, metres in the code). TOPv = top studio photo, silhouette cast on the plane z = BAR_END z (gripscan.py,
# 0.78 mm a pixel); FRONTv / REARv = edge scans of the end photos on the grip's own plane; DET829 / DET830 / DR05 /
# DR06 = detail photos (counts, proportions, which features are grooves and which ribs).
G_TIP = (0.0150, 0.0141)      # outside diameter over the diamond tips 30.0 mm at a 8 and 28.2 mm at a 110: FRONTv top
#   edge falls 4.5 mm and REARv's bottom 1.7 mm over that run (so 2.8 mm of taper, the rest is the bar's upsweep),
#   TOPv widths 28.6 -> 27.0 (left) and 29.6 -> 28.6 (right) under a threshold that reads about 0.4 mm narrow
G_DEPTH = 0.00055             # pyramid height, EST: DR06 shows sharp pyramids about a third as tall as they are wide
G_PITCH = 0.00125             # half the pyramid diagonal along the axis: DET829 2D FFT of zone 2, both diagonal
#   families repeat every 20.4 px along the axis where zone 2 (46 mm) spans 380 px -> 2.47 mm a diagonal
G_ROUND = 36                  # pyramids round the grip: 2.47 mm round a 29 mm grip -> 36.9; 36 keeps the square
#   diamonds of DR06 (2.6 mm round, 2.5 along)
G_RINGS = (0.0279, 0.0738)    # full rings, centres: mean of TOPv silhouette notches (28.5, 74.5 left; 29.5, 75 right),
#   TOPv dark lines on the grip's top (27.3, 73.0; 26.3, 72.0) and FRONTv / REARv dark lines (25.8..31.8, 70.3..78.8;
#   axprof.py). A groove round the palm side with a bright bead in it (DR06, DR05); a rib across the waffle side
#   (DET829, DET830: they stand below the bottom edge there)
G_ZONES = ((0.0080, 0.0267), (0.0291, 0.0726), (0.0750, 0.1120))    # diamond fields between the end collar, the two
#   ring grooves and the flange's fillet; the pattern starts after a smooth collar behind the end lip (DET829 crop)
G_GROOVE = 0.0024             # groove width over the field edges, EST from DR06 (bead 1.3 mm, walls either side)
G_FLOOR = 0.0016              # groove floor below the tips; TOPv dips 1.5..2.5 mm at the rings
G_BEAD = (0.0005, 0.0010)     # bead radius and its top below the tips, EST: it catches the light in DR05 / DR06
G_PARTIAL = (0.0510, 0.0975)  # ribs across the waffle side between the full rings: FRONTv dark lines at a 51.0 and
#   97.3 (right grip), DR05 48.9 and 98, DET829 about 53 and 104, TOPv front-edge step at 97 (left) and 98 (right)
G_LONG = tuple(math.radians(t) for t in (20, 205, 336))   # ribs along the grip (deg from the front, up positive):
#   FRONTv shows two lines on the front face, +20 and -24 deg (33 % and 71 % down the grip), diamond panels between
#   them; lf34 (calibrated, candidate lines drawn, riblines.py) about +28. Behind, one line only, low: DET830 71 %
#   down from behind (about 200 deg), DET829 from behind and below (about 236), DR06 none on the upper rear (a second
#   rear rib at 158 deg was tried and showed in the DR06 / DET829 close-ups where the photos have none).
#   They run from the end collar to the last partial rib (DR05)
G_BAND = (math.radians(205), math.radians(336))    # smooth band under the grip between the lower ribs (DET829: no
#   diamonds below the line near the bottom; FRONTv: the face below -24 deg reads smooth and dark)
G_RIB = (0.0013, 0.0010, 0.0003)    # rib width at the root and at the top, top above the tips: DET829 / DET830 ribs
#   across the smooth band stand 5..10 px (0.5..0.9 mm) below the bottom edge (the band lies 0.75 mm under the tips)
G_LIP = 0.01675               # end lip radius (33.5 mm): FRONTv 34.9 at a 4, REARv 34.2, TOPv 32.5..34.0 at a 2..5
G_FLANGE = (0.1190, 0.1220, 0.0290)     # flange disc a0, a1 and radius: TOPv widest at a 118..121 (both), its front-
#   rear extent 57.7 mm (left, threshold reads narrow); lf34 pair: flange 82 px tall over a body of 40 (model 76 at
#   28 mm); DET829 and DR05 flange twice the body's height next to it
G_COLLAR = (0.0156, 0.1256)   # collar behind the flange (DR05 "688" moulded on it) and where the grip ends on the bar,
#   EST: the switch housing starts at a 122..126 in TOPv and wraps it
G_THROTTLE_R = 0.0130         # throttle tube under the right grip, EST (a 1.2 mm grip wall on a 26 mm pipe)


def g_tip(a):
    """Radius over the diamond tips at a (linear taper, constant over the end collar)."""
    k = (min(max(a, 0.008), 0.110) - 0.008) / 0.102
    return G_TIP[0] + (G_TIP[1] - G_TIP[0]) * k


def _rows():
    """Rings of the grip body from the end face to the bar: (a, kind, data). kind 'r': a plain ring of radius data;
    'p': a pattern row (data = row parity). Pattern rows sit on each field's own pitch so both its edges are rows."""
    out = []
    # end face: recessed disc, raised rim, rolled lip, step down to the smooth collar (DET829 crop of the end cap)
    for r, a in ((0.0110, 0.0006), (0.0118, 0.00035), (0.0126, 0.00005), (0.0135, 0.0), (0.01525, 0.0),
                 (0.0158, 0.00005), (0.01625, 0.0004), (0.0166, 0.0009), (G_LIP, 0.0015), (G_LIP, 0.0028),
                 (0.0165, 0.0036), (0.0160, 0.0042), (0.0153, 0.0046), (0.0150, 0.0050)):
        out.append((a, "r", r))
    out.append((0.0074, "r", g_tip(0.0074) - G_DEPTH))
    edges = []
    for z, (a0, a1) in enumerate(G_ZONES):
        n = int(round((a1 - a0) / G_PITCH))
        for i in range(n + 1):
            out.append((a0 + (a1 - a0) * i / n, "p", i % 2))
        if z < len(G_RINGS):                                # ring groove after this field
            c, w = G_RINGS[z], G_GROOVE / 2
            fl, bead = G_FLOOR, G_BEAD
            for a, dr in ((c - w + 0.00015, -G_DEPTH - 0.00015), (c - w + 0.0003, -fl), (c - bead[0] - 0.0001, -fl),
                          (c - bead[0] * 0.7, -bead[1] - bead[0] * 0.3), (c - bead[0] * 0.35, -bead[1] - 0.00006),
                          (c, -bead[1]), (c + bead[0] * 0.35, -bead[1] - 0.00006),
                          (c + bead[0] * 0.7, -bead[1] - bead[0] * 0.3), (c + bead[0] + 0.0001, -fl),
                          (c + w - 0.0003, -fl), (c + w - 0.00015, -G_DEPTH - 0.00015)):
                out.append((a, "b" if abs(a - c) < bead[0] * 0.8 else "r", g_tip(a) + dr))
    # fillet from the field into the flange, the flange with its rounded rim, the collar (DET829, DR05, DR06)
    a0, a1, rf = G_FLANGE
    for r, a in ((g_tip(0.1123) - G_DEPTH, 0.1123), (0.0145, 0.1142), (0.0154, 0.1158), (0.0168, 0.1172),
                 (0.0186, 0.1183), (0.0210, 0.1189), (0.0235, a0), (rf - 0.0008, a0 + 0.0002),
                 (rf - 0.0002, a0 + 0.0008), (rf, a0 + 0.0015), (rf - 0.0002, a1 - 0.0008), (rf - 0.0008, a1 - 0.0002),
                 (0.0250, a1), (0.0175, a1), (G_COLLAR[0] + 0.0004, a1 + 0.0003), (G_COLLAR[0], a1 + 0.0008),
                 (G_COLLAR[0], G_COLLAR[1] - 0.0006), (G_COLLAR[0] - 0.0006, G_COLLAR[1])):
        out.append((a, "r", r))
    return out


def grip(s, right=False):
    """Honda stock grip on one side (s: _Side): a closed rubber body from the end face to the bar (or the throttle
    tube), its diamond fields as true pyramids (36 round, 2.5 mm diagonal), two ring grooves with beads, the end lip,
    flange and collar; the underside's waffle ribs (two along it, the rings and two partial ribs across) on top."""
    mat = "grip_rubber"
    n = 2 * G_ROUND
    th = np.arange(n) * 2 * math.pi / n
    cs, sn = np.cos(th), np.sin(th)
    band = (th > G_BAND[0] + 0.01) & (th < G_BAND[1] - 0.01)
    rows = _rows()
    rows.append((G_COLLAR[1] + 0.0001, "r", G_THROTTLE_R if right else 0.0114))      # onto the pipe / the bar
    m = Mesh()
    base = []
    for a, kind, q in rows:
        if kind == "p":
            r = np.where((np.arange(n) + q) % 2 == 0, g_tip(a), g_tip(a) - G_DEPTH)
            r = np.where(band, g_tip(a) - G_DEPTH - 0.0002, r)        # the smooth band under the grip
        else:
            r = np.full(n, q)
        base.append(m.verts([s.p(a, ri * c, ri * si) for ri, c, si in zip(r, cs, sn)]))
    for k in range(len(rows) - 1):
        b0, b1 = base[k], base[k + 1]
        pat = rows[k][1] == "p" and rows[k + 1][1] == "p"
        fm = "grip_bead" if rows[k][1] == "b" and rows[k + 1][1] == "b" else mat
        for i in range(n):
            j = (i + 1) % n
            q = (b0 + i, b0 + j, b1 + j, b1 + i)
            if not pat:
                m.face(q, fm)
            elif (i + rows[k][2]) % 2 == 0:                  # corner i of row k is a tip: split along the valleys
                m.face((q[0], q[1], q[3]), mat)
                m.face((q[1], q[2], q[3]), mat)
            else:
                m.face((q[0], q[1], q[2]), mat)
                m.face((q[0], q[2], q[3]), mat)
    c = m.verts([s.p(rows[0][0])])                           # end face centre, recessed with its ring
    for i in range(n):
        m.face((base[0] + (i + 1) % n, base[0] + i, c), mat)
    m = _outward_open(m, s)
    # ---- underside waffle: ribs along at G_LONG, across at the rings and the partial ribs
    w0, w1, hgt = G_RIB
    lo = -G_FLOOR - 0.0003                                   # root below the groove floor, inside the body

    sec = [(-w0 / 2, lo), (-w0 / 2, -G_DEPTH), (-w1 / 2, hgt - 0.0003), (-w1 / 2 + 0.0002, hgt),
           (w1 / 2 - 0.0002, hgt), (w1 / 2, hgt - 0.0003), (w0 / 2, -G_DEPTH), (w0 / 2, lo)]    # (across, radial)
    for z, (a0, a1) in enumerate(G_ZONES):                   # ribs along, from the end collar to the fillet
        aa = (a0 + 0.0006 if z == 0 else G_RINGS[z - 1], G_PARTIAL[1] if z == 2 else G_RINGS[z])
        for t in G_LONG:
            e_r, e_t = np.array([math.cos(t), math.sin(t)]), np.array([-math.sin(t), math.cos(t)])
            rings = [np.array([s.p(a, *((g_tip(a) + dr) * e_r + dt * e_t)) for dt, dr in sec])
                     for a in np.linspace(aa[0], aa[1], 3)]
            m.add(_outward(grid(Mesh(), rings, mat, cap0=True, cap1=True)))
    for c in list(G_RINGS) + list(G_PARTIAL):                # ribs across: partials over the whole lower arc (FRONTv,
        prof = [(dt, dr) for dt, dr in sec]                  # lf34, rr34), the rings' beads rise into ribs only
        t0, t1 = (G_LONG[1], G_LONG[0] + 2 * math.pi) if c in G_PARTIAL else G_BAND   # across the smooth band
        tt = np.linspace(t0 - 0.046, t1 + 0.046, 48 if c in G_PARTIAL else 30)      # over the long ribs' width
        rings = [np.array([s.p(c + da, *((g_tip(c) + dr) * np.array([math.cos(t), math.sin(t)])))
                           for da, dr in prof]) for t in tt]
        m.add(_outward(grid(Mesh(), rings, mat, cap0=True, cap1=True)))
    # ---- mould parting line across the flange's outboard face, front and rear (DET829: a fine line at mid-height),
    # 0.4 mm wide, 0.12 mm proud of the flat face
    for t in (0.0, math.pi):
        e, e_t = np.array([math.cos(t), math.sin(t)]), np.array([-math.sin(t), math.cos(t)])
        loop = [(0.0003, -0.0002), (0.0003, 0.0002), (-0.00012, 0.0002), (-0.00012, -0.0002)]
        rings = [np.array([s.p(G_FLANGE[0] + da, *(r0 * e + dt * e_t)) for da, dt in loop])
                 for r0 in (0.0220, G_FLANGE[2] - 0.0010)]
        m.add(_outward(grid(Mesh(), rings, mat, cap0=True, cap1=True)))
    return m


def _outward_open(m, s):
    """Wind the grip body so its normals point away from the grip's axis (checked on the widest ring)."""
    v = np.asarray(m.V, float)
    for f in m.F[:200]:
        q = v[list(f)]
        nrm = np.cross(q[1] - q[0], q[2] - q[0])
        c = q.mean(axis=0) - s.T
        radial = c - (c @ s.d) * s.d
        if np.linalg.norm(nrm) > 1e-12 and np.linalg.norm(radial) > 0.008:
            if nrm @ radial < 0:
                m.F = [tuple(reversed(f)) for f in m.F]
            break
    return m


def bar_path():
    """Centre line of the left half of the Fatbar, clamp to bar end. TOP: straight across to y 0.15, then swept
    back in one line to the bar end (bar centre x 0.980 at y 0.168, 0.969 at 0.207, 0.9165 at 0.404). FRONT cols
    2205..2340: it rises between y 0.075 and 0.225 (centre z 1.189 at y 0.153, 1.199 at 0.186); beyond it follows
    the grips' axis (UPSWEEP)."""
    c0 = fk(F_BAR, 0, T_BAR)
    k, w = math.tan(SWEEP), 0.020                                  # w: softness of the plan bend (EST)
    q = (c0[0] - TIP[0]) / k
    yc = TIP[1] - (q - w * w / (4 * q))
    ys = np.append(np.arange(0.0, TIP[1] - 0.004, 0.008), TIP[1])
    v = ys - yc
    x = c0[0] - k * (v + np.sqrt(v * v + w * w)) / 2
    m_ = math.tan(UPSWEEP) / math.cos(SWEEP)                                  # slope of the grips' axis in y
    zl = TIP[2] - (TIP[1] - ys) * m_                                       # the grips' axis, run inwards
    y1, y2 = RISE
    h = y2 - y1
    t = np.clip((ys - y1) / h, 0, 1)                                       # cubic Hermite: level at y1, on the
    z2 = TIP[2] - (TIP[1] - y2) * m_                                       # grips' axis with its slope at y2
    zr = c0[2] * (2 * t ** 3 - 3 * t ** 2 + 1) + z2 * (3 * t ** 2 - 2 * t ** 3) + m_ * h * (t ** 3 - t ** 2)
    z = np.where(ys >= y2, zl, zr)
    return np.stack([x, ys, z], axis=1)


RISE = (0.075, 0.185)         # the bar rises from the clamps and meets the grips' axis (with its upsweep) at y 0.185:
#   FRONT centre z 1.189 at y 0.153 and 1.199 at 0.186 (cols 2205..2340, earlier pass); the grips' axis is at 1.1993
#   there, so the end section is one straight 1.85 deg line from the rise to the bar end


BAR_R = (0.0143, 0.0111)      # SPEC: Renthal Fatbar, 28.6 mm in the clamps, 22.2 mm at the controls
BAR_TAPER = (0.150, 0.185)    # |y| where the taper starts and ends: TOP crops (rul_top_L / _R) and DR05, the bar is
#   thick out to the cable tie (TOP a 250..255 left, 280 right) and thin from the perch's clamp inwards; d835 the same
BAR_KNURL = (0.020, 0.074)    # knurled clamping zone each side of the centre (under the pad, hidden in every photo):
#   Renthal knurls the 28.6 mm section where the holders can sit (four positions over 26 mm, SPEC), EST extent
KNURL_PITCH = 0.0010          # knurl diamond pitch, EST (a fine straight-diamond knurl)


def bar_r(y):
    """Fatbar radius at lateral y: 28.6 mm, a smooth taper, 22.2 mm."""
    k = np.clip((np.abs(y) - BAR_TAPER[0]) / (BAR_TAPER[1] - BAR_TAPER[0]), 0, 1)
    return BAR_R[0] + (BAR_R[1] - BAR_R[0]) * k * k * (3 - 2 * k)


def knurl_map(path, n=256, tiles=8):
    """Tangent-space normal map (OpenGL, +Y up) of a straight diamond knurl: TILES pitches across N pixels, the
    pyramids' faces at 30 deg."""
    from PIL import Image
    t = (np.arange(n) + 0.5) / n * tiles
    u, v = np.meshgrid(t, t)
    a, b = (u + v) % 1.0 - 0.5, (u - v) % 1.0 - 0.5                      # distance to the two groove families
    gx = -(np.sign(a) + np.sign(b))                                      # gradient of -(|a| + |b|)
    gy = -(np.sign(a) - np.sign(b))
    k = math.tan(math.radians(30)) / 2
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(gx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    img = np.stack([nx / ln, ny / ln, nz / ln], axis=2) * 0.5 + 0.5
    Image.fromarray((img[::-1] * 255).round().astype(np.uint8)).save(path)       # row 0 is the top (v = 1)


def _block(s, a0, a1, wf, wu, mat, cf=0.0, cu=0.0, r=0.006, ch=0.0015):
    """Block clamped on the grip section from a0 to a1, wf deep and wu tall, centred (cf, cu) off the bar axis."""
    return slab(rounded_rect(wf, wu, r, 4), a0, a1, mat, lambda p, q, h: s.p(h, cf + p, cu + q), ch)


def _lever(s, pts):
    """Forged lever blade through grip-frame points (a, f, u), ball end. FRONT: ball at |y| 0.389, z 1.18;
    TOP rows 685..865 and 1405..1540: blade 52 mm ahead of the grip at |y| 0.265, 70 at 0.345, 95 at the ball
    (offsets kept relative to the grip)."""
    q = spline([s.p(a - s.shift * (1 - min(1.0, max(0.0, (a - 0.06) / 0.10))), f, u) for a, f, u in pts], 26)
    k = np.linspace(0, 1, len(q))
    rad = np.stack([np.interp(k, [0, 0.25, 1], [0.0060, 0.0042, 0.0036]),
                    np.interp(k, [0, 0.25, 1], [0.0080, 0.0068, 0.0052])], axis=1)
    m = tube(q, rad, 12, "lever")
    m.add(ball(q[-1], 0.0085, "lever"))
    return m


def _wire(s, a0, f, u):
    """Switch lead: from a housing along the underside of the bar into the bar pad."""
    side = s.side
    path = bar_path() * [1, side, 1]
    y0 = abs(s.p(a0)[1])
    sel = path[(abs(path[:, 1]) > 0.070) & (abs(path[:, 1]) < y0 - 0.02)]
    rr = bar_r(sel[:, 1])
    pts = np.vstack([sel - (rr + 0.003)[:, None] * Z, [s.p(a0 + 0.012, f * 0.5, u), s.p(a0 - 0.002, f, u)]])
    return sweep(pts, 0.0025, "cable", 8)


def _bar(path):
    """The Fatbar: plain black tube, its knurled clamping zones (own material with a knurl normal map, UVs in knurl
    pitches), the open ends with a 1.6 mm wall and a black plastic plug pressed in (both hidden by the closed grips)."""
    from scipy.interpolate import interp1d
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    marks = sorted(set([0.0, float(s[-1])] + [float(np.interp(y, path[:, 1], s)) for y in
                   (-BAR_TAPER[1], -BAR_TAPER[0], -BAR_KNURL[1], -BAR_KNURL[0], BAR_KNURL[0], BAR_KNURL[1],
                    BAR_TAPER[0], BAR_TAPER[1])]))
    ss = []                     # rows every 2 mm in the knurl zones and the taper, 6 mm elsewhere, on the zone edges
    for s0, s1 in zip(marks[:-1], marks[1:]):
        mid = abs(float(np.interp((s0 + s1) / 2, s, path[:, 1])))
        step = 0.002 if (BAR_KNURL[0] < mid < BAR_KNURL[1] or BAR_TAPER[0] < mid < BAR_TAPER[1]) else 0.006
        k = max(1, int(math.ceil((s1 - s0) / step)))
        ss += list(np.linspace(s0, s1, k + 1)[:-1])
    ss = np.array(ss + [float(s[-1])])
    P = interp1d(s, path, axis=0)(ss)
    seg = 32
    m = tube(P, bar_r(P[:, 1]), seg, "bar_black", cap0=False, cap1=False)
    circ = 2 * math.pi * BAR_R[0]
    for k in range(len(P) - 1):
        if BAR_KNURL[0] < abs(0.5 * (P[k, 1] + P[k + 1, 1])) < BAR_KNURL[1]:
            for i in range(seg):
                fi = k * seg + i
                m.M[fi] = "bar_knurl"
                u0, u1 = i * circ / seg / KNURL_PITCH / 8, (i + 1) * circ / seg / KNURL_PITCH / 8
                v0, v1 = ss[k] / KNURL_PITCH / 8, ss[k + 1] / KNURL_PITCH / 8
                m.uv[fi] = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    for end, nxt in ((P[0], P[1]), (P[-1], P[-2])):      # open ends: wall, bore, plug 1 mm inside
        ax = unit(end - nxt)
        ri = BAR_R[1] - 0.0016
        m.add(rev(end, -ax, [(BAR_R[1], 0.0), (ri + 0.0003, 0.0), (ri, 0.0003), (ri, 0.006)], "bar_black", seg))
        m.add(rev(end - 0.001 * ax, -ax, [(ri + 0.0001, 0.0), (ri + 0.0001, 0.0045), (0.0, 0.0045)], "plastic_black",
                  seg, cap0=True))
    return m


def bars():
    """Renthal Fatbar (28.6 mm in the holders, 22.2 mm at the controls), holders with their bolts, bar pad, grips,
    left: mode / traction / stop switch and clutch perch, lever and adjuster; right: throttle housing with its two
    cable elbows, start button, front master cylinder with reservoir, lever and banjo."""
    m = Mesh()
    left = bar_path()
    path = np.vstack([(left * [1, -1, 1])[::-1][:-1], left])
    path[-1] -= 0.003 * unit(path[-1] - path[-2])                           # bar ends 3 mm inside the grips' ends
    path[0] -= 0.003 * unit(path[0] - path[1])
    m.add(_bar(path))
    # ---- holders: rubber cushion on the top clamp, post, cradle, cap with two bolts (EST sizes)
    cradle = rounded_rect(0.060, 0.026, 0.009, 4)
    for side in (-1, 1):
        yh = side * HOLDER_Y
        m.add(cyl(fk(F_BAR, yh, T_UP[1]), fk(F_BAR, yh, T_UP[1] + 0.006), 0.017, "rubber_black", 24, 0.001))
        lev = [(T_UP[1] + 0.006, 0.52), (T_UP[1] + 0.012, 0.52), (T_BAR - 0.016, 1.0), (T_BAR - 0.0003, 1.0)]
        rings = [np.array([fk(F_BAR + p[0] * k, yh + p[1], t) for p in cradle]) for t, k in lev]
        m.add(_outward(grid(Mesh(), rings, "alu_cast", cap0=True, cap1=True)))
        lev = [(T_BAR + 0.0003, 1.0, 1.0), (T_BAR + 0.0185, 1.0, 1.0), (T_BAR + 0.0215, 0.94, 0.86)]
        rings = [np.array([fk(F_BAR + p[0] * k, yh + p[1] * ky, t) for p in cradle]) for t, k, ky in lev]
        m.add(_outward(grid(Mesh(), rings, "alu_cast", cap0=True, cap1=True)))
        for df in (-0.0205, 0.0205):
            m.add(bolt(fk(F_BAR + df, yh, T_BAR + 0.0215), UP, af=0.010, flange_d=0.013))
    # ---- bar pad (PAD_F, PAD_T, PAD_Y): red body, dark grey end caps, the bar leaving through a bore in each cap.
    # It sits over the holders and hides them and their bolts (DET 475835)
    sec = pad_section()
    cs = sec.mean(axis=0)
    ring = lambda yy, k=1.0: np.array([fk(q[0], yy, q[1]) for q in cs + (sec - cs) * k])
    y0, y1 = PAD_Y
    rings = [ring(-y1, 0.96), ring(-y1 + 0.002), ring(-y0), ring(y0), ring(y1 - 0.002), ring(y1, 0.96)]
    bore = []
    for r_ in (rings[0], rings[-1]):
        j = int(np.argmin(np.abs(path[:, 1] - r_[0][1])))
        d = (r_ - path[j]) * [1, 0, 1]
        bore.append(path[j] * [1, 0, 1] + [0, r_[0][1], 0]
                    + (bar_r(path[j, 1]) + 0.0004) * d / np.linalg.norm(d, axis=1, keepdims=True))
    m.add(_outward(grid(Mesh(), [bore[0]] + rings + [bore[1]], "barpad",
                        mats=["barpad", "pad_cap", "pad_cap", "barpad", "pad_cap", "pad_cap", "barpad"])))
    # ---- hand controls (the grips are their own part, grips())
    L, R = _Side(1, CTRL_SHIFT[0]), _Side(-1, CTRL_SHIFT[1])
    # ---- left: switch cluster (DET 475829: blue, red and green buttons facing the rider) and its lead
    m.add(_block(L, 0.109, 0.131, 0.034, 0.040, "plastic_black", cf=-0.002, cu=0.003, r=0.008))
    for a, u, mat in ((0.114, 0.012, "btn_blue"), (0.126, 0.012, "btn_red"), (0.120, -0.004, "btn_green")):
        m.add(cyl(L.p(a, -0.0185, u), L.p(a, -0.0212, u), 0.0042, mat, 12, 0.0006))
    m.add(_wire(L, 0.131, -0.004, -0.014))
    # ---- left: clutch perch (FRONT col 2340: black, z 1.188..1.243 at y 0.253), pivot, lever, cable adjuster
    m.add(_block(L, 0.150, 0.168, 0.036, 0.048, "anod_black", r=0.012))
    for u in (-0.0165, 0.0165):
        m.add(bolt(L.p(0.159, -0.018, u), -L.f, af=0.008))
    arm = [(0.150, 0.012), (0.170, 0.012), (0.188, 0.026), (0.190, 0.040), (0.180, 0.048), (0.162, 0.046),
           (0.150, 0.034)]
    m.add(slab(arm, -0.012, 0.008, "anod_black", L.p))
    m.add(bolt(L.p(0.178, 0.036, 0.008), Z, af=0.010))
    m.add(bolt(L.p(0.178, 0.036, -0.012), -Z, af=0.010, head_h=0.006))
    m.add(_lever(L, [(0.178, 0.036, -0.002), (0.165, 0.050, -0.005), (0.130, 0.060, -0.009), (0.087, 0.070, -0.014),
                     (0.062, 0.084, -0.018), (0.0495, 0.095, -0.021)]))
    a0, ad = _clutch_adjuster()
    m.add(cyl(a0, a0 + 0.007 * ad, 0.009, "anod_black", 16, 0.001))
    m.add(cyl(a0 + 0.007 * ad, a0 + 0.022 * ad, 0.0055, "steel", 12))
    m.add(rev(a0 + 0.022 * ad, ad, [(0.0062, 0.0), (0.0058, 0.008), (0.0042, 0.024)], "rubber_black", 12, cap1=True))
    # ---- right: throttle housing (FRONT col 1620: black z 1.185..1.247 at y -0.283; DET 475830) and elbows
    m.add(_block(R, 0.107, 0.138, 0.040, 0.044, "plastic_black", cf=0.002, cu=0.002, r=0.012))
    m.add(cyl(R.p(0.107), R.p(0.121), 0.0245, "plastic_black", 24, 0.003))
    for k in (0, 1):
        g, ge = 0.004 + 0.008 * k, THROTTLE_F[k]
        m.add(sweep([R.p(0.124, g, 0.016), R.p(0.127, g, 0.0245), R.p(0.137, (g + ge) / 2, 0.028),
                     R.p(0.156, ge, 0.029)], 0.0032, "steel", 8))
        b0, tp = R.p(0.156, ge, 0.029), throttle_paths()[k]        # the boot stops 0.3 mm short of the cable's end
        ax = unit(tp[0] - b0)                                      # (whose first ring is square to the cable)
        gap = 0.0003 + 0.0035 * math.sqrt(max(0.0, 1.0 - float(unit(tp[1] - tp[0]) @ ax) ** 2))
        m.add(cyl(b0, tp[0] - gap * ax, 0.0048, "rubber_black", 10))
    # ---- right: start button and its lead
    m.add(_block(R, 0.143, 0.159, 0.028, 0.032, "plastic_black", cf=-0.004, cu=-0.004, r=0.006))
    m.add(cyl(R.p(0.151, -0.018, -0.002), R.p(0.151, -0.0206, -0.002), 0.005, "anod_black", 12, 0.0006))
    m.add(_wire(R, 0.159, -0.006, -0.014))
    # ---- right: Nissin master cylinder (FRONT cols 1676..1752: grey, z 1.183..1.243; TOP rows 865, 910: x 0.975..1.02)
    cast = "alu_cast"
    m.add(_block(R, 0.170, 0.186, 0.034, 0.046, cast, r=0.011))
    for u in (-0.016, 0.016):
        m.add(bolt(R.p(0.178, -0.017, u), -R.f, af=0.008))
    m.add(_block(R, 0.170, 0.186, 0.020, 0.024, cast, cf=0.022, cu=-0.006))
    m.add(cyl(R.p(0.164, 0.030, -0.008), R.p(0.232, 0.030, -0.008), 0.0125, cast, 20, 0.002))        # barrel
    m.add(slab(rounded_rect(0.058, 0.042, 0.008, 4), -0.004, 0.0305, cast,
               lambda p, q, h: R.p(0.201 + p, 0.036 + q, h)))                                         # reservoir
    m.add(slab(rounded_rect(0.061, 0.045, 0.009, 4), 0.0305, 0.034, cast,
               lambda p, q, h: R.p(0.201 + p, 0.036 + q, h), ch=0.001))                               # lid
    for da, df in ((0.022, -0.013), (-0.022, 0.013)):
        m.add(bolt(R.p(0.201 + da, 0.036 + df, 0.034), Z, af=0.0055, head_h=0.0018, mat="steel", kind="cap"))
    m.add(cyl(R.p(0.201, 0.0152, 0.010), R.p(0.201, 0.0138, 0.010), 0.006, "rubber_black", 14))       # sight glass
    arm = [(0.160, 0.030), (0.186, 0.030), (0.190, 0.050), (0.180, 0.058), (0.164, 0.054)]
    m.add(slab(arm, -0.012, 0.004, cast, R.p))
    m.add(bolt(R.p(0.176, 0.046, 0.004), Z, af=0.010))
    m.add(bolt(R.p(0.176, 0.046, -0.012), -Z, af=0.010, head_h=0.006))
    m.add(_lever(R, [(0.176, 0.046, -0.004), (0.163, 0.054, -0.006), (0.130, 0.061, -0.009), (0.087, 0.070, -0.014),
                     (0.062, 0.084, -0.018), (0.0495, 0.095, -0.021)]))
    # banjo on the inboard end of the barrel (FRONT: hose leaves at y -0.19, z 1.18) and the steel pipe stub
    m.add(cyl(R.p(0.232, 0.030, -0.008), R.p(0.241, 0.030, -0.008), 0.0085, "steel", 16, 0.001))
    m.add(bolt(R.p(0.241, 0.030, -0.008), -R.d, af=0.012, head_h=0.006, flange_d=0.015))
    m.add(cyl(R.p(0.2365, 0.034, -0.009), _hose_start() + 0.0008 * unit(_hose_start() - R.p(0.2365, 0.034, -0.009)),
              0.0040, "steel", 10))
    return m


def _clutch_adjuster():
    s = _Side(1, CTRL_SHIFT[0])
    return s.p(0.188, 0.036, -0.002), unit(-s.d + 0.25 * s.f)


THROTTLE_F = (-0.005, 0.005)                          # the two cables leave side by side over the bar, EST


def _throttle_start(k):
    return _Side(-1, CTRL_SHIFT[1]).p(0.168, THROTTLE_F[k], 0.029)


def _hose_start():
    return _Side(-1, CTRL_SHIFT[1]).p(0.2365, 0.054, -0.019)


# ================================================================ front brake
CAL_C = FA + np.array([-0.120, 0.0, 0.004])           # LEFT: caliper box u 1174..1252, v 1550..1654 (by eye, 10 mm)
E_Q = unit((CAL_C - FA) * [1, 0, 1])                  # radial, away from the axle (rearwards)
E_W = np.cross(Y, E_Q)                                # along the disc's rim, upwards


def cal(q, w, y):
    return CAL_C + q * E_Q + w * E_W + y * Y


def _banjo():
    return cal(0.0515, -0.012, 0.088)


def hose_path():
    """Front brake hose, master cylinder to caliper. FRONT ("hose" scan): crosses the centre line at z 1.193, over
    the plate's left half to y 0.089 at z 1.064, then straight down at y 0.088..0.090 to the guide on the fork
    guard (rows 1014..1054, y 0.097..0.108), inboard of the leg below it (y 0.047 at z 0.53). LEFT across: 64 to
    75 mm ahead of the tube axis at t 0.42..0.76. LEFT by eye (10 mm): the loop behind the leg down to the banjo."""
    b = _banjo()
    pts = [_hose_start(), fyz(0.078, -0.170, 1.208), fyz(0.088, -0.125, 1.224), fyz(0.090, -0.085, 1.222),
           fyz(0.088, -0.030, 1.208), fyz(0.086, 0.000, 1.193), fyz(0.084, 0.028, 1.1785), fyz(0.082, 0.0535, 1.150),
           fyz(0.080, 0.0685, 1.1215), fyz(0.078, 0.079, 1.0925), fyz(0.075, 0.0885, 1.064), fyz(0.072, 0.0895, 1.028),
           fk(0.072, 0.088, 0.740), fk(0.072, 0.088, 0.670), fk(0.070, 0.089, 0.550), fk(0.068, 0.092, 0.440),
           fk(0.066, 0.096, 0.385), fk(0.064, 0.080, 0.340), fk(0.062, 0.062, 0.300), fk(0.050, 0.052, 0.265),
           fk(0.020, 0.051, 0.235), fk(-0.020, 0.054, 0.213), (1.2964, 0.065, 0.4457), (1.2887, 0.078, 0.3958),
           b + 0.028 * E_W, b + 0.010 * E_W]
    return spline(pts, 230)


def front_brake():
    """Brake hose with its sleeve and two guides, Nissin two-piston caliper (30 and 27 mm, SPEC) on its bracket
    behind the left leg, pads, slide pins, bleed nipple, banjo."""
    m = Mesh()
    q = hose_path()
    m.add(tube(q, 0.0045, 10, "cable"))
    t = (q - TUBE0) @ UP
    sl = q[(t > 0.725) & (t < 0.82) & (q[:, 1] > 0.08)]              # FRONT rows 530..610: black 8 mm wide (sleeve)
    m.add(tube(sl, 0.0062, 10, "rubber_black"))
    # guide under the lower clamp (FRONT rows 610..640, LEFT (1445, 815)): stay off the left boss, rubber grommet
    m.add(box(fk(0.0475, 0.090, 0.670), (0.036, 0.003, 0.012), "steel", RF))
    m.add(cyl(fk(0.072, 0.088, 0.661), fk(0.072, 0.088, 0.679), 0.0085, "rubber_black", 16, 0.0015))
    # guide on the fork guard (FRONT rows 1014..1054; LEFT bolts (1244, 1170) and (1236, 1189))
    m.add(box(fk(0.0585, 0.108, 0.384), (0.003, 0.030, 0.026), "steel", RF))
    for tb in (0.376, 0.392):
        m.add(bolt(fk(0.060, 0.114, tb), FWD, af=0.008))
    m.add(cyl(fk(0.066, 0.096, 0.372), fk(0.066, 0.096, 0.396), 0.0085, "rubber_black", 16, 0.0015))
    # ---- caliper (DET 475831). Disc at y 0.0605..0.0635 out to r 0.130 (wheel): pads either side, bridge beyond
    c = "caliper"
    m.add(slab(rounded_rect(0.052, 0.082, 0.014, 5), 0.071, 0.099, c, lambda p, w, h: cal(0.005 + p, w, h), 0.002))
    for w, r in ((0.0195, 0.0195), (-0.0195, 0.0180)):               # 30 and 27 mm pistons
        m.add(cyl(cal(-0.004, w, 0.097), cal(-0.004, w, 0.106), r, c, 24, 0.003))
    m.add(slab(rounded_rect(0.016, 0.070, 0.005, 3), 0.046, 0.099, c, lambda p, w, h: cal(0.022 + p, w, h)))
    m.add(slab(rounded_rect(0.050, 0.060, 0.010, 4), 0.046, 0.055, c, lambda p, w, h: cal(0.006 + p, w, h)))
    for y0, y1 in ((0.0645, 0.0712), (0.0548, 0.0595)):              # pads
        m.add(slab(rounded_rect(0.034, 0.054, 0.006, 3), y0, y1, "anod_black", lambda p, w, h: cal(-0.011 + p, w, h),
                   0.0005))
    # bracket: plate from the lug's two ears to the slide pins above and below the body
    pins = [cal(0.004, 0.049, 0.0), cal(0.004, -0.049, 0.0)]
    ears = [fk(f, 0.0, t) for f, t in CAL_EARS]
    pts = np.vstack([circle(0.009, 16, p[0], p[2]) for p in ears] + [circle(0.009, 16, p[0], p[2]) for p in pins])
    hull = pts[ConvexHull(pts).vertices]
    m.add(slab(hull, 0.0745, 0.0825, c, lambda x, z, h: np.array([x, h, z]), 0.001))
    for p in ears:
        m.add(bolt([p[0], 0.105, p[2]], Y, af=0.010, flange_d=0.016))
    for p in pins:
        m.add(cyl([p[0], 0.0825, p[2]], [p[0], 0.099, p[2]], 0.0065, "rubber_black", 14, 0.001))
        m.add(bolt([p[0], 0.099, p[2]], Y, af=0.010, head_h=0.004, flange_d=0.011))
    nb = unit(0.9 * E_W + 0.3 * E_Q)                                 # bleed nipple with its rubber cap
    p0 = cal(0.020, 0.040, 0.090)
    m.add(bolt(p0, nb, af=0.008, head_h=0.004, flange_d=0.009, mat="steel"))
    m.add(cyl(p0 + 0.004 * nb, p0 + 0.011 * nb, 0.0028, "steel", 10))
    m.add(cyl(p0 + 0.008 * nb, p0 + 0.015 * nb, 0.0042, "rubber_black", 10, 0.0008))
    # banjo on the body's rear, hose entering from above through a steel stub
    b = _banjo()
    m.add(cyl(cal(0.029, -0.012, 0.088), cal(0.047, -0.012, 0.088), 0.008, c, 14, 0.001))
    m.add(cyl(cal(0.047, -0.012, 0.088), cal(0.056, -0.012, 0.088), 0.0085, "steel", 16, 0.001))
    m.add(bolt(cal(0.056, -0.012, 0.088), E_Q, af=0.012, head_h=0.006, flange_d=0.015))
    m.add(cyl(b, b + 0.024 * E_W, 0.0040, "steel", 10))
    return m


# ================================================================ disc cover
def disc_guard():
    """Black plastic cover outside the front disc (DET 475831, LEFT u 960..1110, v 1440..1600): a plate just outside
    the disc with a honeycomb window in its upper front, solid below, a fin towards the rear under the caliper, a
    hub that steps out over the axle lug to the axle nut. Open where the fork leg and the caliper are. Outline in
    axle-centred fork coordinates (g ahead, t up the fork); radii and the window's extent are EST."""
    m = Mesh()
    yp, r0, rh = 0.0865, 0.143, 0.060
    a_top = math.atan2(math.sqrt(r0 ** 2 - 0.006 ** 2), 0.006)       # edge 6 mm ahead of the fork guard's front
    a_fin = math.radians(-161.75)                                    # 135 deg below the horizontal, behind
    out = [(r0 * math.cos(a), r0 * math.sin(a)) for a in np.linspace(a_top, a_fin + math.radians(16), 64)]
    out.append((0.160 * math.cos(a_fin + math.radians(5)), 0.160 * math.sin(a_fin + math.radians(5))))   # fin tip
    out.append((0.096 * math.cos(a_fin), 0.096 * math.sin(a_fin)))
    a_in = math.atan2(-0.030, -math.sqrt(rh ** 2 - 0.030 ** 2))      # inner edge 8 mm under the lug's socket
    out += [(rh * math.cos(a), rh * math.sin(a)) for a in np.linspace(a_in, math.radians(80), 40)]
    holes = []
    pitch, rhex = 0.0135, 0.0052
    for i in range(-2, 14):
        for j in range(0, 14):
            g, t = i * pitch + (pitch / 2 if j % 2 else 0.0), j * pitch * 0.866
            if rh + 0.012 < math.hypot(g, t) < r0 - 0.012 and g > 0.026 and t > 0.012:
                holes.append(circle(rhex, 6, g, t))
    m.add(_outward(plate2d(np.array(out), holes, 0.003, "plastic_black",
                  lambda g, t, w: FA + g * FWD + t * UP + (yp + w) * Y, step=0.009)))
    arc = lambda a0, a1: (-math.radians(a1), -math.radians(a0))      # fork angles to rev's (which runs clockwise)
    # hub: cone from the plate out over the lug, face round the axle nut (3 mm wall)
    hub = [(rh, yp + 0.0015), (0.050, 0.127), (0.046, 0.1315), (0.041, 0.1335), (0.0135, 0.1335),
           (0.0135, 0.1305), (0.0395, 0.1305), (0.0435, 0.129), (0.047, 0.125), (rh - 0.003, yp - 0.0015)]
    m.add(rev(FA, Y, hub, "plastic_black", 56, ref=FWD, arc=arc(-135, 80), solid=True))
    # rim lip towards the wheel, rib on the solid part
    lip = [(r0 - 0.0005, yp + 0.0015), (r0 + 0.0025, yp + 0.0005), (r0 + 0.0025, 0.0765), (r0 + 0.0005, 0.0755),
           (r0 + 0.0005, yp - 0.0015), (r0 - 0.0005, yp - 0.0015)]
    m.add(rev(FA, Y, lip, "plastic_black", 72, ref=FWD,
              arc=arc(math.degrees(a_fin) + 16, math.degrees(a_top)), solid=True))
    rib = [(0.104, yp + 0.0014), (0.1025, yp + 0.0034), (0.0985, yp + 0.0034), (0.097, yp + 0.0014)]
    m.add(rev(FA, Y, rib, "plastic_black", 48, ref=FWD, arc=arc(-150, 2)))
    for a in (35, -75):                                              # screws on the hub face (DET: two visible)
        c = FA + 0.028 * (math.cos(math.radians(a)) * FWD + math.sin(math.radians(a)) * UP) + 0.1335 * Y
        m.add(bolt(c, Y, af=0.008))
    return m


# ================================================================ cables that run on to the frame
CLUTCH_JOIN = np.array([0.790, 0.074, 0.800])         # upper end of the cable that detail_engine draws up from the
#   clutch release arm on the LEFT crankcase cover. Its route down to the arm is detail_engine.CLUTCH_CABLE

def _engine(name):
    """A cable anchor of the engine module; None until it defines one (CLUTCH_ARM_END, THROTTLE_DRUM)."""
    try:
        import detail_engine
        v = getattr(detail_engine, name, None)
        return None if v is None else np.asarray(v, float)
    except Exception:
        return None


def throttle_end():
    """Where the throttle cables end: on top of the drum on the right of the throttle body (detail_engine: centre
    TB0 + 0.062 TB_DIR, 38 mm right of the bore's axis, radius 19 mm), lying on it 0.3 mm clear."""
    drum = _engine("THROTTLE_DRUM")
    if drum is not None:
        return drum + np.array([0.0, 0.0, 0.0038])
    try:
        import detail_engine as de
        mid = de.TB0 + 0.062 * de.TB_DIR
        return np.array([mid[0], -(de.TB_BORE / 2 + 0.016), mid[2] + 0.019 + 0.0038])
    except Exception:
        return np.array([0.7047, -0.038, 0.7618])


def clutch_path():
    """Clutch cable, perch adjuster to the engine: past the plate's left corner, across the front of the pad's left end (FRONT row 270: black at y 0.080..0.089,
    z 1.193), down behind the plate, between the
    left tube and the head, down the left of the steering head (LEFT by eye: (0.996, 1.10) to (1.019, 1.04), with
    the in-line adjuster), then under the tank's left edge to the upper end of the engine module's own cable
    (CLUTCH_JOIN), or all the way to detail_engine.CLUTCH_ARM_END once that exists."""
    a0, ad = _clutch_adjuster()
    arm = _engine("CLUTCH_ARM_END")
    w = unit(np.array([0.815, 0.074, 0.795]) - CLUTCH_JOIN)
    route = _engine("CLUTCH_CABLE")                      # the engine module's own route, from CLUTCH_JOIN to its last guide
    tail = [CLUTCH_JOIN + 0.0025 * w] if arm is None or route is None else [CLUTCH_JOIN] + [tuple(p) for p in route[1:]] + [arm]
    pts = [a0 + 0.0466 * ad, a0 + 0.062 * ad, a0 + 0.085 * ad,            # leaves along the adjuster
           (1.058, 0.118, 1.190), fk(0.041, 0.095, 0.972),
           fk(0.042, 0.072, 0.968), fk(0.043, 0.060, 0.945), fk(0.040, 0.057, 0.915), fk(0.034, 0.056, 0.880), fk(0.006, 0.052, 0.858), fk(-0.038, 0.052, 0.853),
           fk(-0.054, 0.054, 0.800), fk(-0.056, 0.056, 0.740), (1.030, 0.057, 0.904), (0.991, 0.062, 0.875),
           (0.951, 0.068, 0.849), (0.909, 0.075, 0.824), (0.866, 0.077, 0.801), (0.815, 0.074, 0.795)] + tail
    return spline(pts, 190)


def throttle_paths():
    """The two throttle cables, housing elbows to the drum. FRONT (bars_front, refitted camera): a cable crosses
    over the front of the bar pad from the throttle side, z 1.241 at y -0.18 falling to 1.200 at y 0.086, into
    the cable loop on the plate's left; then under the bar, down behind the steering head ahead of the tank and
    back under the tank to the drum. They leave the elbows along the bar, behind the master cylinder's reservoir
    (FRONT col 1710: nothing black above or ahead of the reservoir). One centre line; the pair rides either side
    of it on a frame carried along the path (always square to it, so the cables stay 7.6 mm apart), turned
    evenly along the way so that they arrive side by side across the drum."""
    end = throttle_end()
    sd = _Side(-1, CTRL_SHIFT[1])
    pts = [sd.p(0.168, 0.0, 0.029), sd.p(0.200, 0.0, 0.030), sd.p(0.236, 0.004, 0.030),
           (1.035, -0.150, 1.238), (1.060, -0.100, 1.230), (1.066, -0.060, 1.2195), (1.066, 0.000, 1.206),
           (1.060, 0.055, 1.203), (1.048, 0.118, 1.199), (1.022, 0.118, 1.164), (0.989, 0.118, 1.134),
           (0.978, 0.105, 1.108),                     # round the pad's left end and under its rear lower corner
           (0.974, 0.062, 1.101), (0.983, 0.038, 1.039), (0.995, 0.014, 0.974), (0.995, 0.003, 0.907),
           (0.996, -0.006, 0.840), (0.953, -0.019, 0.805), (0.902, -0.028, 0.784), (0.845, -0.031, 0.783),
           (0.789, -0.035, 0.781), end + np.array([0.030, 0.0, 0.004]), end]
    c = spline(pts, 260)
    t = np.gradient(c, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    n = [unit(sd.f - (sd.f @ t[0]) * t[0])]                         # the elbows sit one ahead of the other
    for i in range(1, len(c)):
        n.append(unit(n[-1] - (n[-1] @ t[i]) * t[i]))
    n = np.array(n)
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))])
    bn = np.cross(t[-1], n[-1])
    turn = min((math.atan2(sgn * (Y @ bn), sgn * (Y @ n[-1])) for sgn in (1, -1)), key=abs)
    ang = turn * arc / arc[-1]
    n = np.cos(ang)[:, None] * n + np.sin(ang)[:, None] * np.cross(t, n)
    g = np.interp(arc, [0.0, 0.06], [THROTTLE_F[1], 0.0038])[:, None]
    return [c - g * n, c + g * n]


def cables():
    """Clutch cable and the two throttle cables: they start on the bar's fittings and end on the engine, so they
    do not turn with the steering. Below the steering head their control points were pushed away from the nearest
    surface of the merged model (frame, tank, radiators, engine) until the paths cleared it by 10 mm or more."""
    m = Mesh()
    q = clutch_path()
    m.add(tube(q, 0.0040, 8, "cable"))
    i = int(np.argmin(np.linalg.norm(q - fk(-0.054, 0.054, 0.800), axis=1)))
    d = unit(q[i + 1] - q[i - 1])
    m.add(cyl(q[i] - 0.016 * d, q[i] + 0.016 * d, 0.0058, "steel", 12, 0.001))          # in-line adjuster
    m.add(cyl(q[i] + 0.016 * d, q[i] + 0.030 * d, 0.0052, "rubber_black", 10, 0.001))
    for q in throttle_paths():
        m.add(tube(q, 0.0035, 8, "cable"))
    return m


def grips():
    """Both grips (the right one on the throttle tube)."""
    m = Mesh()
    m.add(grip(_Side(1)))
    m.add(grip(_Side(-1), right=True))
    return m


PARTS = {"fork": fork, "clamps": clamps, "bars": bars, "grips": grips, "front_brake": front_brake,
         "disc_guard": disc_guard, "cables": cables}
REPLACES = ["fork", "clamps", "bars", "cables", "disc_guard"]
FRONT_END = ["fork", "clamps", "bars", "grips", "front_brake", "disc_guard"]
MATERIALS = {"bar_knurl": dict(rgb=(20, 20, 22), metal=0.6, rough=0.45, normal="stock/bar_knurl_n.png",
                           normal_strength=0.8),        # the Fatbar's clamping zones (BAR_KNURL)
             "btn_red": dict(rgb=(200, 22, 26), rough=0.4), "btn_blue": dict(rgb=(24, 70, 190), rough=0.4),
             "btn_green": dict(rgb=(20, 140, 60), rough=0.4), "pad_cap": dict(rgb=(58, 58, 62), rough=0.65),
             "grip_rubber": dict(rgb=(24, 24, 26), rough=0.55, bump=0.12),      # satin black rubber (DR06, DET829)
             "grip_bead": dict(rgb=(26, 26, 28), rough=0.22)}       # the rings' beads shine as thin lines (DR05, DR06)
CLASS = {"bar_knurl": "black", "btn_red": "black", "btn_blue": "black", "btn_green": "black", "pad_cap": "black", "grip_rubber": "black",
         "grip_bead": "black"}
SMOOTH = {"fork": 40, "clamps": 40, "bars": 40, "grips": 40, "front_brake": 40, "disc_guard": 40, "cables": 60}
# bar pad's texture: "RENTHAL" on its front and rear faces, each read from its own side (FRONT and REAR photos)
UV = {"barpad": dict(centre=[float(PAD_C[0]), float(PAD_C[2])], half=list(PAD_HALF), y_half=PAD_Y[1],
                     tilt=float(PAD_TILT))}


if __name__ == "__main__":
    import os
    knurl_map(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "textures", "stock",
                           "bar_knurl_n.png"))
