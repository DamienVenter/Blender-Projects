"""Damien's 2026 Honda CRF250R, part by part, as meshes in the bike frame (metres; x forward, y left, z up; origin
on the ground under the rear axle). Plain Python (numpy/scipy): run it to write the parts file, which
build_bike.py turns into Blender objects. Every number has a source:
  SPEC  research/crf250r-2026.md (Honda spec sheets: wheelbase, rake, trail, rims, tyres, discs, fork, sprockets)
  BP    research/bike-blueprint.json (Honda studio profile photo, calibrated: axles, tyre outer diameters)
  OUT   research/bike-outlines.json (plastics traced from that photo)
  GRID  positions read off the millimetre-gridded blueprint crops (scripts/bike/gridview.py)
  TOP   widths read off the gridded studio top photo (scripts/bike/topview.py)
  DV    Damien's own photos (reference/damien-bike-2026-11-10): his parts and colours
  EST   estimated (hidden or not yet measured); to verify on his bike

python3 parts.py OUT.npz
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geom import (Mesh, box, circle, frame_z, grid, lathe, loft_sections, panel, plate2d, prism,  # noqa: E402
                  rot_x, rot_y, rot_z, rounded_rect, slot, smooth_poly, tube)

RES = os.path.join(HERE, "..", "..", "research")
BP = json.load(open(os.path.join(RES, "bike-blueprint.json")))["left"]
OUT = json.load(open(os.path.join(RES, "bike-outlines.json")))
MM = 0.001

# ---------------------------------------------------------------- geometry of the chassis
WHEELBASE = 1.483                                   # SPEC
R_REAR = BP["rear_tyre_od_mm"] / 2 * MM             # BP: 0.3264 (knob tips)
R_FRONT = BP["front_tyre_od_mm"] / 2 * MM           # BP: 0.3506
# The parts are built in the AXLE-LINE frame of the blueprint (both axles at z = R_REAR, the frame every outline
# and grid reading is in). build_bike.py then tilts the whole bike nose-up by GROUND_PITCH about the rear axle so
# both tyres stand on the ground (the front tyre is bigger).
RA = np.array([0.0, 0.0, R_REAR])                   # rear axle
FA = np.array([WHEELBASE, 0.0, R_REAR])             # front axle (axle-line frame)
GROUND_PITCH = math.atan2(R_FRONT - R_REAR, WHEELBASE)        # about 0.93 deg
RAKE = math.radians(28.4) - GROUND_PITCH            # SPEC: 28 deg 24 min to the ground (EU, AU, South Africa)
UP = np.array([-math.sin(RAKE), 0.0, math.cos(RAKE)])         # fork / steering axis, pointing up
BACK = np.array([-math.cos(RAKE), 0.0, -math.sin(RAKE)])      # perpendicular to it, pointing back
AXLE_LEAD = 0.015                                   # EST: axle ahead of the fork tube axis (leading-axle lug)
CLAMP_OFFSET = 0.022                                # SPEC (aftermarket source, L): triple clamp offset
TUBE0 = FA + AXLE_LEAD * BACK                       # fork tube axis passes here (axle height)
STEER0 = TUBE0 + CLAMP_OFFSET * BACK                # steering axis passes here
FORK_HALF = 0.093                                   # TOP: fork tube centres at +-93 mm


def on_tube(t, y=0.0):
    """Point on the fork tube axis t metres above the axle (along UP), at lateral position y."""
    return TUBE0 + t * UP + np.array([0, y, 0])


def t_at_z(z):
    return (z - TUBE0[2]) / UP[2]


T_BOT_CLAMP = t_at_z(0.925)                         # GRID: lower clamp at z 0.90..0.96
T_TOP_CLAMP = t_at_z(1.140)                         # GRID: top clamp at z 1.13..1.15
PIVOT = np.array([0.563, 0.0, 0.462])               # GRID: swingarm pivot bolt; pivot to axle 0.579 (SPEC 585.2)
PEG = np.array([0.556, 0.0, 0.378])                 # GRID: footpeg (centre of the toothed platform)
CS = np.array([0.633, 0.098, 0.451])                # GRID: countershaft (13T) sprocket; y EST
CHAIN_Y = 0.098                                     # EST: chain line (left side)
P520 = 0.015875                                     # SPEC: #520 chain pitch


def sprocket_r(n):
    return P520 / (2 * math.sin(math.pi / n))


# ---------------------------------------------------------------- wheels
def tyre_profile(r_bead, r_crown, half_w):
    """Carcass section (r, y), bead to bead over the crown."""
    pts = []
    for a in np.linspace(-1, 1, 25):
        y = half_w * math.sin(a * math.pi / 2) * 1.0
        # rounded section: full width at about 55 % of the section height
        r = r_bead + (r_crown - r_bead) * (math.cos(a * math.pi / 2) ** 0.55)
        pts.append((r, y * (0.62 + 0.38 * math.cos(a * math.pi / 2) ** 0.3)))
    pts[0] = (r_bead, -half_w * 0.55)
    pts[-1] = (r_bead, half_w * 0.55)
    return pts


def tyre(name, r_out, rim_d_in, section_w, rows, centre_y):
    """Knobby tyre: carcass by lathe plus blocks in a two-row repeating pattern (Pirelli Scorpion MX32 style:
    centre pairs alternating with a centre single, intermediate and shoulder knobs). Knob height 13 mm EST."""
    knob_h = 0.013
    r_bead = rim_d_in * 0.0254 / 2 + 0.002
    r_crown = r_out - knob_h
    hw = section_w / 2
    prof = tyre_profile(r_bead, r_crown, hw)
    m = lathe(prof, 96, "rubber")
    pr = np.array(prof)

    def surf(y):
        """Carcass point (r) and the section's normal angle at lateral position y (upper half)."""
        upper = pr[np.argsort(pr[:, 1])]
        r = float(np.interp(y, upper[:, 1], upper[:, 0]))
        dy = 0.002
        r1 = float(np.interp(y + dy, upper[:, 1], upper[:, 0]))
        slope = (r1 - r) / dy
        return r, math.atan(-slope)

    for k in range(rows):
        a = 2 * math.pi * k / rows
        if k % 2 == 0:
            ys = [-0.42, 0.42, -0.88, 0.88]          # centre pair, shoulders (fraction of half width)
        else:
            ys = [0.0, -0.68, 0.68]                   # centre single, intermediates
        for fy in ys:
            y = fy * hw
            r, tilt = surf(y)
            w_lat = 0.011 if abs(fy) > 0.8 else 0.013
            w_circ = 0.017 if abs(fy) < 0.5 else 0.014
            kb = box((0, 0, 0), (w_circ, w_lat, knob_h + 0.004), "rubber")
            kb.transform(rot_x(-tilt))
            kb.transform(None, (0, y, r + knob_h / 2 - 0.002))
            # around the wheel: the wheel's spin axis is y; position angle a in the x-z plane
            c, s = math.cos(a), math.sin(a)
            R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
            kb.transform(R)
            m.add(kb)
    m.transform(None, (0, centre_y, 0))
    return m


def rim(bead_d_in, width_in, mat="rim"):
    rb = bead_d_in * 0.0254 / 2
    hw = width_in * 0.0254 / 2
    prof = [(rb - 0.006, -hw + 0.006), (rb - 0.004, -hw - 0.001), (rb + 0.009, -hw - 0.002), (rb + 0.010, -hw + 0.002),
            (rb + 0.001, -hw + 0.004), (rb - 0.001, -hw * 0.45), (rb - 0.009, -hw * 0.3), (rb - 0.009, hw * 0.3),
            (rb - 0.001, hw * 0.45), (rb + 0.001, hw - 0.004), (rb + 0.010, hw - 0.002), (rb + 0.009, hw + 0.002),
            (rb - 0.004, hw + 0.001), (rb - 0.006, hw - 0.006), (rb - 0.016, hw * 0.4), (rb - 0.016, -hw * 0.4)]
    return lathe(prof, 120, mat, closed=True)


def hub(half_w, flange_r, barrel_r, flange_y):
    prof = [(0.010, -half_w), (barrel_r * 0.8, -half_w), (barrel_r, -half_w + 0.006), (barrel_r, -flange_y - 0.004),
            (flange_r, -flange_y - 0.003), (flange_r, -flange_y + 0.003), (barrel_r * 0.9, -flange_y + 0.008),
            (barrel_r * 0.75, 0.0), (barrel_r * 0.9, flange_y - 0.008), (flange_r, flange_y - 0.003),
            (flange_r, flange_y + 0.003), (barrel_r, flange_y + 0.004), (barrel_r, half_w - 0.006),
            (barrel_r * 0.8, half_w), (0.010, half_w)]
    return lathe(prof, 48, "hub")


def spokes(n, hub_r, flange_y, rim_r, rim_hw, cross=3):
    """Laced spokes: n/2 per flange, each going to a rim hole CROSS x (360 / (n/2)) degrees around (3-cross)."""
    m = Mesh()
    per = n // 2
    alpha = 2 * math.pi * cross / per
    for side, fy in ((0, -flange_y), (1, flange_y)):
        for i in range(per):
            a_h = 2 * math.pi * (i + 0.5 * side) / per
            d = 1 if i % 2 == 0 else -1
            a_r = a_h + d * alpha
            ry = (-1 if side == 0 else 1) * rim_hw * 0.3
            p0 = np.array([hub_r * math.cos(a_h), fy, hub_r * math.sin(a_h)])
            p1 = np.array([rim_r * math.cos(a_r), ry, rim_r * math.sin(a_r)])
            m.add(tube([p0, p1], 0.0019, 6, "spoke", cap0=False, cap1=False))
            dn = (p1 - p0) / np.linalg.norm(p1 - p0)
            m.add(tube([p1 - dn * 0.014, p1], 0.0033, 6, "spoke"))           # nipple
    return m


def petal_disc(r_out, r_in, n_petals, y, thick=0.003):
    """Wave ('petal') disc: scalloped outer edge, ring with two rows of slots, six bolt bosses; mounted on the hub
    by a thin carrier ring (the spokes show through, as on the bike)."""
    a = np.linspace(0, 2 * math.pi, n_petals * 16, endpoint=False)
    ro = r_out - 0.0045 * (1 - np.cos(n_petals * a)) / 2
    outer = np.stack([ro * np.cos(a), ro * np.sin(a)], axis=1)
    holes = [circle(r_in, 64)]
    for k in range(n_petals * 2):
        ang = 2 * math.pi * (k + 0.5) / (n_petals * 2)
        rr = r_in + (r_out - r_in) * (0.38 if k % 2 else 0.62)
        c = (rr * math.cos(ang), rr * math.sin(ang))
        holes.append(slot(c, ang + 1.2, 0.016, 0.006))
    m = plate2d(outer, holes, thick, "disc", lambda u, v, t: (u, y + t, v), step=0.006)
    inner = [circle(0.042, 48)] + [circle(0.0055, 12, 0.060 * math.cos(2 * math.pi * k / 6),
                                          0.060 * math.sin(2 * math.pi * k / 6)) for k in range(6)]
    carrier_outer = circle(r_in + 0.004, 64)
    spokes_out = []
    m.add(plate2d(carrier_outer, [circle(r_in - 0.006, 64)], thick * 1.6, "hub",
                  lambda u, v, t: (u, y + t, v), step=0.006))
    for k in range(6):                          # six arms from the hub flange to the disc ring, with bolts
        ang = 2 * math.pi * k / 6
        d = np.array([math.cos(ang), math.sin(ang)])
        arm = tube([np.array([0.045 * d[0], y, 0.045 * d[1]]), np.array([(r_in + 0.001) * d[0], y, (r_in + 0.001) * d[1]])],
                   [(0.006, 0.003)] * 2, 8, "hub")
        m.add(arm)
        m.add(tube([np.array([0.058 * d[0], y - 0.004, 0.058 * d[1]]), np.array([0.058 * d[0], y + 0.004, 0.058 * d[1]])],
                   0.005, 6, "steel"))
    return m


def sprocket(n, y, mat="sprocket", thick=0.006):
    """Sprocket: tooth profile (rounded trapezoids at the #520 pitch radius), centre bore, lightening windows on the
    big rear sprocket."""
    r = sprocket_r(n)
    pts = []
    for i in range(n):
        a0 = 2 * math.pi * i / n
        for da, rr in ((-0.36, r - 0.0065), (-0.20, r + 0.0015), (-0.10, r + 0.0050), (0.10, r + 0.0050),
                       (0.20, r + 0.0015), (0.36, r - 0.0065)):
            a = a0 + da * 2 * math.pi / n
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    holes = [circle(0.031 if n > 20 else 0.011, 40)]
    if n > 20:
        for k in range(6):                      # six windows between six arms
            a0 = 2 * math.pi * k / 6
            win = []
            for a in np.linspace(a0 + 0.18, a0 + 2 * math.pi / 6 - 0.18, 10):
                win.append(((r - 0.020) * math.cos(a), (r - 0.020) * math.sin(a)))
            for a in np.linspace(a0 + 2 * math.pi / 6 - 0.30, a0 + 0.30, 8):
                win.append((0.058 * math.cos(a), 0.058 * math.sin(a)))
            holes.append(np.array(win))
        for k in range(6):
            a = 2 * math.pi * (k + 0.5) / 6
            holes.append(circle(0.0045, 12, 0.044 * math.cos(a), 0.044 * math.sin(a)))
    return plate2d(np.array(pts), holes, thick, mat, lambda u, v, t: (u, y + t, v), step=0.008)


def front_wheel():
    m = Mesh()
    m.add(tyre("front", R_FRONT, 21, 0.080, 54, 0.0))                   # SPEC 80/100-21, BP OD
    m.add(rim(21, 1.60))                                                 # SPEC 21 x 1.60, black D.I.D
    m.add(hub(0.058, 0.046, 0.030, 0.034))
    m.add(spokes(36, 0.041, 0.034, 0.2667 - 0.012, 0.0203))             # SPEC 36 spokes
    m.add(petal_disc(0.130, 0.080, 12, 0.062))                           # SPEC 260 mm, left side
    return m


def rear_wheel():
    m = Mesh()
    m.add(tyre("rear", R_REAR, 19, 0.100, 50, 0.0))                     # SPEC 100/90-19, BP OD
    m.add(rim(19, 1.85))                                                 # SPEC 19 x 1.85
    m.add(hub(0.070, 0.050, 0.034, 0.040))
    m.add(spokes(36, 0.045, 0.040, 0.2413 - 0.012, 0.0235))             # EST 36 (front is 36)
    m.add(petal_disc(0.120, 0.075, 12, -0.066))                          # SPEC 240 mm, right side
    m.add(sprocket(50, CHAIN_Y))                                         # SPEC 50T
    return m


# ---------------------------------------------------------------- front end (steers about the steering axis)
def fork():
    m = Mesh()
    for side in (-1, 1):
        y = side * FORK_HALF
        # outer tube (gold), from below the lower clamp to above the top clamp
        m.add(tube([on_tube(0.355, y), on_tube(T_TOP_CLAMP + 0.035, y)], 0.0305, 32, "fork_gold"))
        # inner tube (49 mm, dark coated) and the axle lug
        m.add(tube([on_tube(0.035, y), on_tube(0.40, y)], 0.0245, 32, "fork_inner", cap0=False))
        lug = tube([on_tube(-0.04, y), on_tube(0.075, y)], [(0.030, 0.034)] * 2, 24, "fork_lug")
        m.add(lug)
        # fork cap and adjuster on top
        m.add(tube([on_tube(T_TOP_CLAMP + 0.035, y), on_tube(T_TOP_CLAMP + 0.052, y)], 0.024, 24, "anod_black"))
        # dust seal / bottom of the outer tube
        m.add(tube([on_tube(0.345, y), on_tube(0.365, y)], 0.0315, 32, "rubber_black"))
    # front axle
    m.add(tube([FA + np.array([0, -0.115, 0]), FA + np.array([0, 0.115, 0])], 0.010, 16, "steel"))
    return m


def fork_guards():
    """Guards over the inner tubes (shape from OUT 'fork_guard', wrapped around the tube's front half)."""
    m = Mesh()
    poly = np.array(OUT["fork_guard"]) * MM
    # outline in (x, z) -> coordinates along the tube (t) and across its front (a)
    rel = poly - np.array([TUBE0[0], TUBE0[2]])
    t = rel @ np.array([UP[0], UP[2]])
    off = rel @ np.array([-BACK[0], -BACK[2]])                        # forward of the tube axis
    lo, hi = t.min(), t.max()
    ts = np.linspace(lo, hi, 28)
    for side in (-1, 1):
        y = side * FORK_HALF
        rings = []
        for tt in ts:
            # forward extent of the guard at this height (from the outline)
            band = np.abs(t - tt) < 0.012
            front = off[band].max() if band.any() else 0.03
            a = np.linspace(-1.9, 1.9, 14)                  # angle around the tube, 0 = straight forward
            r = 0.031 + 0.012 * np.clip((front - 0.03) / 0.04, 0, 1)
            ring = [on_tube(tt, y) - BACK * (r * math.cos(ai)) + np.array([0, side * r * math.sin(ai) * 1.05, 0])
                    for ai in a]
            rings.append(np.array(ring))
        g = grid(Mesh(), rings, "fork_guard", closed_u=False)
        m.add(g)
    return m


def clamps():
    """Top and bottom triple clamps (aluminium) across both tubes and the steering stem."""
    m = Mesh()
    for t, h, mat in ((T_BOT_CLAMP, 0.045, "alu_cast"), (T_TOP_CLAMP, 0.030, "alu_machined")):
        loop = rounded_rect(0.085, 2 * FORK_HALF + 0.07, 0.035, 6)          # local (along BACK, along y)
        rings = []
        for dt in (-h / 2, h / 2):
            c = on_tube(t + dt)
            rings.append(np.array([c + BACK * (p[0] + 0.012) + np.array([0, p[1], 0]) for p in loop]))
        m.add(grid(Mesh(), rings, mat, cap0=True, cap1=True))
    # steering stem nut
    s_top = STEER0 + (T_TOP_CLAMP + 0.015) * UP
    m.add(tube([s_top, s_top + 0.018 * UP], 0.016, 6, "alu_machined"))
    return m


def bars():
    """Renthal Fatbar (28.6 mm centre, 22.2 mm at the controls), bar mounts, pad, grips, levers, perches."""
    m = Mesh()
    clamp = STEER0 + (T_TOP_CLAMP + 0.045) * UP + BACK * -0.005               # GRID: bar centre z about 1.175
    half = [(0.00, 0.000, 0.000), (0.10, -0.003, 0.004), (0.18, -0.012, 0.012), (0.24, -0.030, 0.030),
            (0.30, -0.052, 0.040), (0.36, -0.065, 0.044), (0.425, -0.073, 0.046)]       # (y, dx, dz) GRID/TOP
    for side in (-1, 1):
        P = np.array([clamp + np.array([dx, side * y, dz]) for y, dx, dz in half])
        r = np.array([0.0143, 0.0143, 0.0143, 0.0123, 0.0111, 0.0111, 0.0111])
        m.add(tube(P, r, 20, "bar_black"))
        # bar mounts (risers) under the bar
        mount = clamp + np.array([0, side * 0.04, 0]) - 0.030 * UP
        m.add(tube([mount, clamp + np.array([0, side * 0.04, 0])], 0.016, 16, "alu_machined"))
        # grip (with flange) and bar end
        g0 = P[4] + (P[5] - P[4]) * 0.2
        m.add(tube([g0, P[6] + (P[6] - P[5]) * 0.08], 0.0165, 20, "grip"))
        m.add(tube([g0 - (P[5] - P[4]) * 0.06, g0], 0.022, 20, "grip"))
        # lever perch, lever, master cylinder (right) / clutch perch (left)
        perch = P[4] + (P[3] - P[4]) * 0.4
        lever_tip = perch + np.array([0.115, side * 0.105, -0.045])
        m.add(tube([perch + np.array([0.02, 0, 0]), lever_tip], [(0.006, 0.0045)] * 2, 10, "lever"))
        m.add(box(perch + np.array([0.0, 0, 0.01]), (0.03, 0.035, 0.03), "anod_black"))
        if side < 0:
            m.add(box(perch + np.array([-0.005, 0.02, 0.03]), (0.045, 0.06, 0.03), "anod_black"))    # master cyl
    # bar pad (red Renthal, DV photo 4)
    pad = rounded_rect(0.060, 0.040, 0.015, 4)
    rings = []
    for y in np.linspace(-0.105, 0.105, 2):
        rings.append(np.array([clamp + np.array([p[0] - 0.005, y, p[1] + 0.022]) for p in pad]))
    m.add(grid(Mesh(), rings, "barpad", cap0=True, cap1=True))
    return m


def number_plate():
    """Front plate: inclined along the fork, ahead of the tubes (OUT 'number_plate' gives its height and lean), slightly
    convex; shape of the face EST from the studio front photo and DV photo 1."""
    m = Mesh()
    w_half = lambda s: 0.080 + 0.050 * min(s / 0.10, 1.0) - 0.012 * max(s - 0.22, 0) / 0.07     # s = along the plate
    S = np.linspace(0.0, 0.30, 24)
    U = np.linspace(-1, 1, 21)
    t0 = t_at_z(0.94)
    rings = []
    for s in S:
        hw = w_half(s)
        ring = []
        for u in U:
            bulge = 0.016 * (1 - u * u)
            ring.append(on_tube(t0 + s) - BACK * (0.068 + bulge) + np.array([0, u * hw, 0]))
        rings.append(np.array(ring))
    m.add(grid(Mesh(), rings, "plate", closed_u=False))
    return m


def front_fender():
    """Loft along x: top line and skirt bottom from OUT 'front_fender', half width TOP, crowned section."""
    poly = np.array(OUT["front_fender"]) * MM
    xs = np.linspace(poly[:, 0].min() + 0.004, poly[:, 0].max() - 0.004, 40)
    top = np.array([poly[np.abs(poly[:, 0] - x) < 0.008, 1].max() for x in xs])
    bot = np.array([poly[np.abs(poly[:, 0] - x) < 0.008, 1].min() for x in xs])
    hw_x = [1.215, 1.25, 1.35, 1.50, 1.60, 1.66, 1.71]
    hw_v = [0.080, 0.086, 0.088, 0.083, 0.072, 0.060, 0.040]                          # TOP
    def sec(i):
        x = xs[i]
        hw = float(np.interp(x, hw_x, hw_v))
        crown = 0.016
        skirt = max(min(top[i] - bot[i] - crown, 0.06), 0.004)
        pts = []
        for u in np.linspace(-1, 1, 21):
            pts.append((x, u * hw, top[i] - crown * u * u))
        ring = [(x, -hw - 0.002, top[i] - crown - skirt)] + pts + [(x, hw + 0.002, top[i] - crown - skirt)]
        return np.array(ring)
    m = loft_sections(range(len(xs)), sec, "fender_front", cap0=False, cap1=False)
    return m


# ---------------------------------------------------------------- bodywork (fixed to the frame)
def smoothstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def shrouds():
    m = Mesh()
    poly = np.array(OUT["shroud"]) * MM

    def y_of(x, z):                       # TOP: shroud +-0.115 at the rear, +-0.20 at the front; curls in at the top
        y = 0.112 + 0.088 * smoothstep(0.60, 1.08, x)
        y -= 0.045 * smoothstep(0.90, 1.00, z) * (1 - 0.5 * smoothstep(0.9, 1.1, x))
        y += 0.010 * math.sin(math.pi * min(max((z - 0.64) / 0.36, 0), 1))           # convex
        return y
    for side in (-1, 1):
        m.add(panel(poly, lambda x, z, s=side: s * y_of(x, z), 0.003, "livery_L" if side > 0 else "livery_R",
                    step=0.012))
    return m


def side_panels():
    m = Mesh()
    poly = np.array(OUT["side_panel"]) * MM
    # black textured lower panel below the red one (GRID, rough)
    lower = np.array([(0.600, 0.868), (0.505, 0.835), (0.502, 0.615), (0.420, 0.620), (0.300, 0.650),
                      (0.230, 0.700), (0.300, 0.752), (0.560, 0.855)])

    seat_hw = lambda x: float(np.interp(x, [0.08, 0.12, 0.25, 0.40, 0.55, 0.70, 0.79],
                                        [0.070, 0.088, 0.092, 0.087, 0.075, 0.062, 0.030]))

    def y_of(x, z):                       # TOP: tucked under the seat's edge at the top, +-0.17 low at the front
        y_top = max(seat_hw(min(max(x, 0.08), 0.79)) + 0.004, 0.075)
        y = y_top + (0.168 - y_top) * smoothstep(0.985, 0.76, z) * (0.6 + 0.4 * smoothstep(0.0, 0.5, x))
        return y - 0.03 * smoothstep(0.05, -0.20, x)
    for side in (-1, 1):
        m.add(panel(poly, lambda x, z, s=side: s * y_of(x, z), 0.003, "livery_L" if side > 0 else "livery_R",
                    step=0.012))
        m.add(panel(lower, lambda x, z, s=side: s * (y_of(x, z) - 0.006), 0.003, "black_texture", step=0.012))
    return m


def seat():
    """Loft along x: top line OUT 'seat_top', half widths TOP (narrow nose, widest over the rear), rounded section."""
    st = np.array(OUT["seat_top"]) * MM
    xs = np.linspace(0.080, 0.790, 48)
    top = np.interp(xs, st[:, 0], st[:, 1])
    hw = np.interp(xs, [0.08, 0.12, 0.25, 0.40, 0.55, 0.70, 0.79], [0.070, 0.088, 0.092, 0.087, 0.075, 0.062, 0.030])
    bottom = np.interp(xs, [0.08, 0.6, 0.79], [0.905, 0.905, 0.975])
    def sec(i):
        loop = rounded_rect(2 * hw[i], top[i] - bottom[i], 0.032, 6)
        zc = (top[i] + bottom[i]) / 2
        return np.array([(xs[i], p[0], zc + p[1]) for p in loop])
    return loft_sections(range(len(xs)), sec, "seat")


def rear_fender():
    ft = np.array(OUT["fender_top"]) * MM
    poly = np.array(OUT["rear_fender"]) * MM
    xs = np.linspace(-0.300, 0.105, 36)
    top = np.interp(xs, ft[:, 0], ft[:, 1])
    hw = np.interp(xs, [-0.30, -0.28, -0.20, -0.10, 0.0, 0.105], [0.012, 0.028, 0.055, 0.075, 0.085, 0.095])
    def sec(i):
        x = xs[i]
        band = np.abs(poly[:, 0] - x) < 0.008
        bot = poly[band, 1].min() if band.any() else top[i] - 0.02
        skirt = max(min(top[i] - bot - 0.012, 0.07), 0.006)
        pts = [(x, u * hw[i], top[i] - 0.012 * u * u) for u in np.linspace(-1, 1, 17)]
        return np.array([(x, -hw[i] - 0.003, top[i] - 0.012 - skirt)] + pts + [(x, hw[i] + 0.003, top[i] - 0.012 - skirt)])
    return loft_sections(range(len(xs)), sec, "livery_fender", cap0=False, cap1=False)


def tank():
    """Titanium tank top visible between the shrouds (GRID x 0.79..0.96, z about 1.02), fuel cap at x 0.893."""
    m = Mesh()
    xs = np.linspace(0.70, 1.02, 18)
    top = np.interp(xs, [0.70, 0.79, 0.88, 0.96, 1.02], [0.985, 1.005, 1.022, 1.015, 0.96])
    hw = np.interp(xs, [0.70, 0.85, 0.95, 1.02], [0.095, 0.100, 0.090, 0.060])
    def sec(i):
        loop = rounded_rect(2 * hw[i], top[i] - 0.80, 0.045, 6)
        return np.array([(xs[i], p[0], (top[i] + 0.80) / 2 + p[1]) for p in loop])
    m.add(loft_sections(range(len(xs)), sec, "tank_ti"))
    cap = np.array([0.893, 0.0, 1.022])
    m.add(tube([cap, cap + np.array([0, 0, 0.022])], 0.036, 24, "plastic_black"))
    m.add(tube([cap + np.array([0, 0, 0.022]), cap + np.array([0, 0, 0.034])], 0.024, 12, "plastic_black"))
    return m


def radiators():
    m = Mesh()
    for side in (-1, 1):
        R = rot_y(math.radians(-12))                    # leans back like the head tube area (EST)
        core = box((0, 0, 0), (0.05, 0.035, 0.30), "radiator", R)
        core.transform(None, (0.985, side * 0.135, 0.775))
        m.add(core)
        # louvres in front of the core (Damien's bike: black slats behind red shroud vents, DV photo 2)
        for k in range(9):
            lv = box((0, 0, 0), (0.004, 0.06, 0.020), "louvre", rot_y(math.radians(-12)) @ rot_x(side * 0.35))
            lv.transform(None, (1.018 - k * 0.006, side * 0.15, 0.66 + k * 0.03))
            m.add(lv)
    return m


# ---------------------------------------------------------------- frame and swingarm
def frame():
    m = Mesh()
    # head tube along the steering axis between the clamps
    m.add(tube([STEER0 + (T_BOT_CLAMP + 0.03) * UP, STEER0 + (T_TOP_CLAMP - 0.02) * UP], 0.029, 28, "alu_frame"))
    for side in (-1, 1):
        s = side
        spar = [(1.00, 0.045, 0.94), (0.93, 0.095, 0.875), (0.84, 0.122, 0.796), (0.66, 0.130, 0.712),
                (0.545, 0.132, 0.640), (0.520, 0.134, 0.560), (0.522, 0.134, 0.470), (0.548, 0.124, 0.370)]   # GRID
        P = np.array([(x, s * y, z) for x, y, z in spar])
        rad = [(0.016, 0.040), (0.017, 0.045), (0.018, 0.042), (0.018, 0.040), (0.018, 0.048), (0.017, 0.058),
               (0.017, 0.060), (0.016, 0.040)]
        m.add(tube(P, rad, 20, "alu_frame"))
        # lower cradle rail under the engine (GRID)
        rail = [(0.975, 0.020, 0.640), (0.965, 0.040, 0.520), (0.935, 0.055, 0.420), (0.880, 0.062, 0.360),
                (0.780, 0.068, 0.345), (0.640, 0.078, 0.346), (0.570, 0.105, 0.362)]
        m.add(tube(np.array([(x, s * y, z) for x, y, z in rail]), 0.0135, 14, "alu_frame"))
        # subframe (mostly under the side panels, EST)
        sub = [(0.545, 0.118, 0.650), (0.40, 0.108, 0.745), (0.20, 0.095, 0.850), (0.00, 0.082, 0.905)]
        m.add(tube(np.array([(x, s * y, z) for x, y, z in sub]), 0.0115, 12, "alu_frame"))
        sub2 = [(0.70, 0.100, 0.860), (0.45, 0.095, 0.905), (0.20, 0.090, 0.915), (0.00, 0.082, 0.915)]
        m.add(tube(np.array([(x, s * y, z) for x, y, z in sub2]), 0.010, 12, "alu_frame"))
    # down tube (single) from the head to the cradle split
    m.add(tube(np.array([(1.045, 0, 0.93), (1.010, 0, 0.78), (0.978, 0, 0.645)]), [(0.022, 0.028)] * 3, 18,
               "alu_frame"))
    # pivot bolt
    m.add(tube([PIVOT + np.array([0, -0.16, 0]), PIVOT + np.array([0, 0.16, 0])], 0.011, 12, "steel"))
    return m


def swingarm():
    m = Mesh()
    for side in (-1, 1):
        y0, y1 = 0.115, 0.118
        P = np.array([PIVOT + np.array([0.0, side * y0, 0]), PIVOT + (RA - PIVOT) * 0.35 + np.array([0, side * y1, 0]),
                      RA + np.array([0.03, side * y1, 0])])
        m.add(tube(P, [(0.020, 0.040), (0.020, 0.036), (0.018, 0.027)], 16, "swing_L" if side > 0 else "swing_R"))
        # axle block / chain adjuster
        m.add(box(RA + np.array([0.0, side * 0.120, 0]), (0.07, 0.030, 0.040), "alu_machined"))
    # cross member near the pivot (EST)
    c = PIVOT + (RA - PIVOT) * 0.18
    m.add(tube([c + np.array([0, -0.10, 0]), c + np.array([0, 0.10, 0])], [(0.025, 0.030)] * 2, 14, "alu_swingarm"))
    # chain slider on the left arm (black)
    sl = [PIVOT + np.array([0.02, 0.122, 0.040]), PIVOT + (RA - PIVOT) * 0.30 + np.array([0, 0.122, 0.036])]
    m.add(tube(sl, [(0.014, 0.010)] * 2, 10, "plastic_black"))
    # rear axle
    m.add(tube([RA + np.array([0, -0.14, 0]), RA + np.array([0, 0.14, 0])], 0.010, 14, "steel"))
    return m


def shock():
    m = Mesh()
    top, bot = np.array([0.475, 0.0, 0.705]), np.array([0.430, 0.0, 0.415])     # EST, behind the engine
    d = (bot - top) / np.linalg.norm(bot - top)
    m.add(tube([top, top + d * 0.17], 0.026, 20, "shock_body"))
    m.add(tube([top + d * 0.12, bot], 0.0085, 12, "chrome"))
    # spring: helix
    n, r = 9, 0.033
    a = np.linspace(0, 2 * math.pi * n, 9 * 40)
    R = frame_z(d)
    pts = [top + d * (0.04 + 0.21 * k / len(a)) + R @ np.array([r * math.cos(t), r * math.sin(t), 0]) for k, t in
           enumerate(a)]
    m.add(tube(pts, 0.0058, 8, "spring"))
    m.add(tube([PIVOT + np.array([-0.04, -0.03, -0.09]), bot], 0.012, 10, "alu_cast"))      # linkage (EST)
    return m


# ---------------------------------------------------------------- engine and exhaust
ENGINE_OUTLINE = [(0.882, 0.760), (0.905, 0.737), (0.905, 0.655), (0.914, 0.601), (0.923, 0.565), (0.923, 0.474),
                  (0.905, 0.415), (0.869, 0.369), (0.751, 0.351), (0.638, 0.369), (0.593, 0.419), (0.584, 0.519),
                  (0.624, 0.583), (0.706, 0.610), (0.760, 0.683), (0.769, 0.737), (0.778, 0.760)]     # GRID


def engine():
    """Side outline traced off the blueprint (GRID), extruded: crankcase +-0.112 below z 0.61, cylinder and head
    +-0.072 above; covers, head cover, intake, hoses and the skid plate added on."""
    m = Mesh()
    out = np.array(ENGINE_OUTLINE)
    low = np.array([p for p in out if p[1] <= 0.62] + [(0.584, 0.61), (0.923, 0.61)])
    low = np.array(sorted(low.tolist(), key=lambda p: math.atan2(p[1] - 0.48, p[0] - 0.76)))
    up = np.array([p for p in out if p[1] >= 0.58] + [(0.70, 0.58), (0.925, 0.58)])
    up = np.array(sorted(up.tolist(), key=lambda p: math.atan2(p[1] - 0.67, p[0] - 0.84)))
    m.add(prism(low, -0.112, 0.112, "engine_case"))
    m.add(prism(up, -0.072, 0.072, "engine_case"))
    # head cover (black), on top of the head (GRID: black cover at the top of the engine)
    hc = np.array([(0.778, 0.760), (0.882, 0.760), (0.874, 0.782), (0.788, 0.782)])
    m.add(prism(hc, -0.062, 0.062, "engine_black", step=0.01))
    # generator cover (left) and clutch cover (right) (GRID: generator centre 0.769, 0.446, r 0.064)
    m.add(tube([np.array([0.769, 0.108, 0.446]), np.array([0.769, 0.138, 0.446])], 0.066, 40, "engine_cover"))
    m.add(tube([np.array([0.769, 0.138, 0.446]), np.array([0.769, 0.142, 0.446])], 0.020, 6, "engine_black"))
    m.add(tube([np.array([0.800, -0.108, 0.470]), np.array([0.800, -0.150, 0.470])], 0.098, 40, "engine_cover"))
    m.add(tube([np.array([0.880, -0.108, 0.540]), np.array([0.880, -0.135, 0.540])], 0.038, 24, "engine_cover"))  # pump
    # intake: throttle body and boot toward the airbox (EST)
    m.add(tube(np.array([(0.78, 0, 0.72), (0.72, 0, 0.77), (0.63, 0, 0.81)]), 0.034, 16, "rubber_black"))
    # radiator hoses (EST)
    for side in (-1, 1):
        m.add(tube(np.array([(0.90, side * 0.02, 0.74), (0.95, side * 0.08, 0.79), (0.98, side * 0.115, 0.86)]),
                   0.012, 10, "rubber_black"))
    # skid plate (black, GRID z 0.325..0.40, x 0.62..1.00)
    sk = []
    for y in (-0.105, 0.105):
        sk.append(np.array([(x, y, z) for x, z in [(1.00, 0.41), (0.97, 0.36), (0.90, 0.330), (0.70, 0.325),
                                                    (0.62, 0.335)]]))
    m.add(grid(Mesh(), sk, "plastic_black", closed_u=False))
    return m


def exhaust():
    m = Mesh()
    header = np.array([(0.950, -0.012, 0.700), (0.995, -0.020, 0.650), (1.010, -0.035, 0.560), (0.990, -0.070, 0.475),
                       (0.920, -0.120, 0.430), (0.800, -0.155, 0.432), (0.660, -0.165, 0.495), (0.530, -0.160, 0.575),
                       (0.430, -0.150, 0.640)])                                     # EST along GRID landmarks
    m.add(tube(header, 0.021, 18, "header_rust"))
    # muffler: oval body from x 0.42 to the end cap at x -0.06 (GRID), heat-treated aluminium
    a, b = np.array([0.425, -0.148, 0.645]), np.array([-0.055, -0.132, 0.868])
    P = np.array([a + (b - a) * s for s in np.linspace(0, 1, 12)])
    rad = [(0.055 * (0.75 + 0.25 * min(s * 5, 1)), 0.048 * (0.75 + 0.25 * min(s * 5, 1))) for s in np.linspace(0, 1, 12)]
    m.add(tube(P, rad, 28, "muffler"))
    m.add(tube([b, b + (b - a) / np.linalg.norm(b - a) * 0.025], [(0.050, 0.044), (0.030, 0.026)], 28, "muffler_cap"))
    return m


def drive():
    """Chain (#520 links around the 13T and 50T sprockets), front sprocket, chain roller (red, DV)."""
    m = Mesh()
    m.add(sprocket(13, 0.0, "steel").transform(None, CS))
    rf, rr = sprocket_r(13), sprocket_r(50)
    c1, c2 = np.array([CS[0], CS[2]]), np.array([RA[0], RA[2]])
    d = c2 - c1
    L = np.linalg.norm(d)
    u = d / L
    nrm = np.array([-u[1], u[0]])
    # external tangents
    ang = math.asin((rr - rf) / L)
    path = []
    def arc(c, r, a0, a1, n):
        return [c + r * np.array([math.cos(a), math.sin(a)]) for a in np.linspace(a0, a1, n)]
    base = math.atan2(nrm[1], nrm[0])
    # top run tangent points
    t1 = c1 + rf * np.array([math.cos(base + ang), math.sin(base + ang)])
    t2 = c2 + rr * np.array([math.cos(base + ang), math.sin(base + ang)])
    b1 = c1 + rf * np.array([math.cos(base + math.pi - ang), math.sin(base + math.pi - ang)])
    b2 = c2 + rr * np.array([math.cos(base + math.pi - ang), math.sin(base + math.pi - ang)])
    loop = arc(c1, rf, base + math.pi - ang - 2 * math.pi, base + ang, 20) + [t1 + (t2 - t1) * s for s in
                                                                              np.linspace(0, 1, 40)[1:-1]]
    loop += arc(c2, rr, base + ang, base + math.pi - ang, 50) + [b2 + (b1 - b2) * s for s in np.linspace(0, 1, 40)[1:-1]]
    loop = np.array(loop)
    seg = np.linalg.norm(np.diff(np.vstack([loop, loop[:1]]), axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    nlinks = int(s[-1] / P520)
    for k in range(nlinks):
        sk = k * s[-1] / nlinks
        i = np.searchsorted(s, sk) - 1
        i = min(max(i, 0), len(loop) - 1)
        p = loop[i] + (loop[(i + 1) % len(loop)] - loop[i]) * ((sk - s[i]) / max(seg[i], 1e-9))
        q = loop[(i + 1) % len(loop)] - loop[i]
        a = math.atan2(q[1], q[0])
        plate_w = 0.0095 if k % 2 else 0.0085
        for yy in (CHAIN_Y - 0.0055, CHAIN_Y + 0.0055):
            pl = box((0, 0, 0), (P520 * 1.05, 0.0014, plate_w), "chain", rot_y(-a))
            pl.transform(None, (p[0], yy, p[1]))
            m.add(pl)
        roller = tube([np.array([p[0], CHAIN_Y - 0.005, p[1]]), np.array([p[0], CHAIN_Y + 0.005, p[1]])], 0.0035, 8,
                      "chain")
        m.add(roller)
    # red anodised chain roller below the pivot (DV photos 1, 2, 5)
    m.add(tube([np.array([0.528, CHAIN_Y - 0.012, 0.392]), np.array([0.528, CHAIN_Y + 0.012, 0.392])], 0.019, 24,
               "red_anod"))
    return m


def controls():
    m = Mesh()
    for side in (-1, 1):
        # footpeg: toothed platform (DV: silver steel pegs)
        y0, y1 = 0.135, 0.235
        m.add(box(PEG + np.array([0, side * (y0 + y1) / 2, 0]), (0.052, y1 - y0, 0.010), "steel"))
        for k in range(5):
            for xx in (-0.024, 0.024):
                tooth = box(PEG + np.array([xx, side * (y0 + 0.01 + k * 0.02), 0.008]), (0.006, 0.006, 0.010), "steel")
                m.add(tooth)
        m.add(tube([PEG + np.array([0.0, side * 0.115, -0.008]), PEG + np.array([0.0, side * 0.14, -0.008])], 0.012,
                   10, "steel"))
    # shift lever (left) and brake pedal (right) (EST)
    m.add(tube(np.array([(0.66, 0.13, 0.46), (0.66, 0.15, 0.43), (0.70, 0.17, 0.41), (0.73, 0.19, 0.41)]), 0.007, 8,
               "steel"))
    m.add(tube(np.array([(0.54, -0.125, 0.43), (0.62, -0.14, 0.40), (0.69, -0.16, 0.395), (0.72, -0.185, 0.40)]),
               0.008, 8, "steel"))
    # front caliper (left, behind the fork leg) and rear caliper (right)
    m.add(box(FA + np.array([-0.075, 0.085, 0.045]), (0.06, 0.035, 0.09), "caliper", rot_y(math.radians(-25))))
    m.add(box(RA + np.array([0.04, -0.09, -0.095]), (0.06, 0.03, 0.05), "caliper"))
    return m


FRONT_END = {"fork": fork, "fork_guards": fork_guards, "clamps": clamps, "bars": bars, "number_plate": number_plate,
             "front_fender": front_fender, "front_wheel": front_wheel}
CHASSIS = {"frame": frame, "swingarm": swingarm, "shock": shock, "engine": engine, "exhaust": exhaust,
           "drive": drive, "controls": controls, "rear_wheel": rear_wheel, "shrouds": shrouds,
           "side_panels": side_panels, "seat": seat, "rear_fender": rear_fender, "tank": tank,
           "radiators": radiators}
PIVOTS = {"front_wheel": FA, "rear_wheel": RA}         # wheels are built about their axle


def build():
    parts = {}
    for name, fn in {**FRONT_END, **CHASSIS}.items():
        mesh = fn()
        if name in PIVOTS:
            mesh.transform(None, PIVOTS[name])
        parts[name] = mesh
    return parts


def save(parts, path):
    data = {}
    mats = sorted({mm for p in parts.values() for mm in p.M})
    data["materials"] = np.array(mats)
    data["names"] = np.array(list(parts))
    for name, p in parts.items():
        V = np.asarray(p.V, np.float32)
        sizes = np.array([len(f) for f in p.F], np.int32)
        flat = np.array([i for f in p.F for i in f], np.int32)
        data[f"{name}__V"] = V
        data[f"{name}__S"] = sizes
        data[f"{name}__F"] = flat
        data[f"{name}__M"] = np.array([mats.index(mm) for mm in p.M], np.int16)
    data["steer_axis"] = np.vstack([STEER0, UP])
    data["ground"] = np.array([RA[0], RA[1], RA[2], GROUND_PITCH])
    np.savez_compressed(path, **data)


if __name__ == "__main__":
    parts = build()
    save(parts, sys.argv[1])
    for name, p in parts.items():
        lo, hi = p.bounds()
        print(f"{name:13s} {len(p.V):6d} v {len(p.F):6d} f   x {lo[0]:+.3f}..{hi[0]:+.3f}  y {lo[1]:+.3f}..{hi[1]:+.3f}"
              f"  z {lo[2]:+.3f}..{hi[2]:+.3f}")
