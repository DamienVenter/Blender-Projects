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
T_BAR = 0.980                                         # bar centre: pad top z 1.2095 (FRONT cols 1980, 2115), pad 60 tall
F_BAR = F_STEER + 0.003                               # TOP rows 1045, 1180: pad centred on x 0.988
YC = 0.152                                            # TOP rows 1270..1360: the bar is straight across out to here
R_GRIP = 0.0155
# The bar ends sit on cams.BAR_END: both side photos, the rear photo and the top photo agree on it.
_TXZ = (cams.BAR_END[0], cams.BAR_END[2])
_C0X = float((TUBE0 + F_BAR * FWD + T_BAR * UP)[0])
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


class _Side:
    """Grip frame of one side: p(a, f, u) is a metres inboard of the bar end along the grip, f ahead, u up."""

    def __init__(self, side):
        self.side = side
        self.T = TIP * [1, side, 1]
        self.d = np.array([-math.sin(SWEEP), side * math.cos(SWEEP), 0.0])      # along the grip, outwards
        self.f = np.array([math.cos(SWEEP), side * math.sin(SWEEP), 0.0])       # ahead of the grip

    def p(self, a, f=0.0, u=0.0):
        return self.T - a * self.d + f * self.f + u * Z


def bar_path():
    """Centre line of the left half of the Fatbar, clamp to bar end. TOP: straight across to y 0.15, then swept
    back in one line to the bar end (bar centre x 0.980 at y 0.168, 0.969 at 0.207, 0.9165 at 0.404). FRONT cols
    2205..2340: it rises between y 0.085 and 0.235 (centre z 1.189 at y 0.153, 1.199 at 0.186) and is level beyond."""
    c0 = fk(F_BAR, 0, T_BAR)
    k, w = math.tan(SWEEP), 0.020                                  # w: softness of the plan bend (EST)
    q = (c0[0] - TIP[0]) / k
    yc = TIP[1] - (q - w * w / (4 * q))
    ys = np.append(np.arange(0.0, TIP[1] - 0.004, 0.008), TIP[1])
    v = ys - yc
    x = c0[0] - k * (v + np.sqrt(v * v + w * w)) / 2
    s = np.clip((ys - 0.085) / 0.150, 0, 1)
    z = c0[2] + (TIP[2] - c0[2]) * s * s * (3 - 2 * s)
    return np.stack([x, ys, z], axis=1)


def _block(s, a0, a1, wf, wu, mat, cf=0.0, cu=0.0, r=0.006, ch=0.0015):
    """Block clamped on the grip section from a0 to a1, wf deep and wu tall, centred (cf, cu) off the bar axis."""
    return slab(rounded_rect(wf, wu, r, 4), a0, a1, mat, lambda p, q, h: s.p(h, cf + p, cu + q), ch)


def _lever(s, pts):
    """Forged lever blade through grip-frame points (a, f, u), ball end. FRONT: ball at |y| 0.389, z 1.18;
    TOP rows 685..865 and 1405..1540: blade 52 mm ahead of the grip at |y| 0.265, 70 at 0.345, 95 at the ball
    (offsets kept relative to the grip)."""
    q = spline([s.p(*p) for p in pts], 26)
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
    rr = np.interp(abs(sel[:, 1]), [0.085, 0.19], [0.0143, 0.0111])
    pts = np.vstack([sel - (rr + 0.003)[:, None] * Z, [s.p(a0 + 0.012, f * 0.5, u), s.p(a0 - 0.002, f, u)]])
    return sweep(pts, 0.0025, "cable", 8)


def bars():
    """Renthal Fatbar (28.6 mm in the holders, 22.2 mm at the controls), holders with their bolts, bar pad, grips,
    left: mode / traction / stop switch and clutch perch, lever and adjuster; right: throttle housing with its two
    cable elbows, start button, front master cylinder with reservoir, lever and banjo."""
    m = Mesh()
    left = bar_path()
    path = np.vstack([(left * [1, -1, 1])[::-1][:-1], left])
    path[-1] -= 0.003 * unit(path[-1] - path[-2])                           # bar ends 3 mm inside the grips' ends
    path[0] -= 0.003 * unit(path[0] - path[1])
    rr = np.interp(abs(path[:, 1]), [0.085, 0.19], [0.0143, 0.0111])        # SPEC diameters; taper over the rise
    m.add(tube(path, rr, 24, "bar_black"))
    # ---- holders: rubber cushion on the top clamp, post, cradle, cap with two bolts (EST sizes)
    cradle = rounded_rect(0.060, 0.026, 0.009, 4)
    for side in (-1, 1):
        yh = side * HOLDER_Y
        m.add(cyl(fk(F_BAR, yh, T_UP[1]), fk(F_BAR, yh, T_UP[1] + 0.006), 0.017, "rubber_black", 24, 0.001))
        lev = [(T_UP[1] + 0.006, 0.52), (T_UP[1] + 0.022, 0.52), (T_BAR - 0.016, 1.0), (T_BAR - 0.0003, 1.0)]
        rings = [np.array([fk(F_BAR + p[0] * k, yh + p[1], t) for p in cradle]) for t, k in lev]
        m.add(_outward(grid(Mesh(), rings, "alu_cast", cap0=True, cap1=True)))
        lev = [(T_BAR + 0.0003, 1.0, 1.0), (T_BAR + 0.0185, 1.0, 1.0), (T_BAR + 0.0215, 0.94, 0.86)]
        rings = [np.array([fk(F_BAR + p[0] * k, yh + p[1] * ky, t) for p in cradle]) for t, k, ky in lev]
        m.add(_outward(grid(Mesh(), rings, "alu_cast", cap0=True, cap1=True)))
        for df in (-0.0205, 0.0205):
            m.add(bolt(fk(F_BAR + df, yh, T_BAR + 0.0215), UP, af=0.010, flange_d=0.013))
    # ---- bar pad: FRONT "RENTHAL" face y -0.088..0.092, top z 1.214; TOP rows 1045, 1180: x 0.958..1.015
    c0 = fk(F_BAR, 0, T_BAR) + np.array([0.001, 0, 0.0045])
    sec = rounded_rect(0.056, 0.060, 0.017, 6)
    rings = [np.array([c0 + np.array([p[0] * k, yy, p[1] * k]) for p in sec])
             for yy, k in ((-0.095, 0.80), (-0.088, 1.0), (0.088, 1.0), (0.095, 0.80))]
    bore = []                                                      # the bar leaves the pad through a bore at each end
    for ring in (rings[0], rings[-1]):
        j = int(np.argmin(np.abs(path[:, 1] - ring[0][1])))
        d = (ring - path[j]) * [1, 0, 1]
        bore.append(path[j] * [1, 0, 1] + [0, ring[0][1], 0]
                    + (rr[j] + 0.0004) * d / np.linalg.norm(d, axis=1, keepdims=True))
    m.add(_outward(grid(Mesh(), [bore[0]] + rings + [bore[1]], "barpad")))
    # ---- both grips: FRONT flange at |y| 0.3115 (102 mm of y), 31 mm across; DET 475829
    grip = [(R_GRIP, 0.0), (0.0165, 0.003), (0.0158, 0.009), (0.0155, 0.094), (0.0165, 0.0985), (0.0225, 0.0995),
            (0.0225, 0.1035), (0.0165, 0.105), (0.0140, 0.106), (0.0114, 0.1063)]      # closes onto the bar
    L, R = _Side(1), _Side(-1)
    for s in (L, R):
        m.add(rev(s.T, -s.d, grip, "grip", 24, cap0=True))
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
        b0, q0 = R.p(0.156, ge, 0.029), throttle_paths()[k][0]     # the boot stops 0.3 mm short of the cable's end
        m.add(cyl(b0, q0 - 0.0003 * unit(q0 - b0), 0.0048, "rubber_black", 10))
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
    s = _Side(1)
    return s.p(0.188, 0.036, -0.002), unit(-s.d + 0.25 * s.f)


THROTTLE_F = (-0.005, 0.005)                          # the two cables leave side by side over the bar, EST


def _throttle_start(k):
    return _Side(-1).p(0.168, THROTTLE_F[k], 0.029)


def _hose_start():
    return _Side(-1).p(0.2365, 0.054, -0.019)


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
    """Clutch cable, perch adjuster to the engine: through the plate's loop, over the left fork cap, between the
    left tube and the head, down the left of the steering head (LEFT by eye: (0.996, 1.10) to (1.019, 1.04), with
    the in-line adjuster), then under the tank's left edge to the upper end of the engine module's own cable
    (CLUTCH_JOIN), or all the way to detail_engine.CLUTCH_ARM_END once that exists."""
    a0, ad = _clutch_adjuster()
    arm = _engine("CLUTCH_ARM_END")
    w = unit(np.array([0.815, 0.074, 0.795]) - CLUTCH_JOIN)
    route = _engine("CLUTCH_CABLE")                      # the engine module's own route, from CLUTCH_JOIN to its last guide
    tail = [CLUTCH_JOIN + 0.0025 * w] if arm is None or route is None else [CLUTCH_JOIN] + [tuple(p) for p in route[1:]] + [arm]
    pts = [a0 + 0.0463 * ad, (1.045, 0.160, 1.205), (1.058, 0.118, 1.190), fk(0.030, 0.090, 0.957),
           fk(0.036, 0.062, 0.925), fk(0.034, 0.056, 0.880), fk(0.006, 0.052, 0.858), fk(-0.038, 0.052, 0.853),
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
    sd = _Side(-1)
    pts = [sd.p(0.168, 0.0, 0.029), sd.p(0.200, 0.0, 0.030), sd.p(0.236, 0.004, 0.030),
           (1.035, -0.150, 1.238), (1.060, -0.100, 1.230), (1.066, -0.060, 1.2195), (1.066, 0.000, 1.206),
           (1.060, 0.055, 1.203), (1.048, 0.112, 1.199), (1.022, 0.108, 1.164), (0.989, 0.100, 1.144),
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


PARTS = {"fork": fork, "clamps": clamps, "bars": bars, "front_brake": front_brake, "disc_guard": disc_guard,
         "cables": cables}
REPLACES = ["fork", "clamps", "bars", "cables", "disc_guard"]
FRONT_END = ["fork", "clamps", "bars", "front_brake", "disc_guard"]
MATERIALS = {"btn_red": dict(rgb=(200, 22, 26), rough=0.4), "btn_blue": dict(rgb=(24, 70, 190), rough=0.4),
             "btn_green": dict(rgb=(20, 140, 60), rough=0.4)}
CLASS = {"btn_red": "black", "btn_blue": "black", "btn_green": "black"}
SMOOTH = {"fork": 40, "clamps": 40, "bars": 40, "front_brake": 40, "disc_guard": 40, "cables": 60}
