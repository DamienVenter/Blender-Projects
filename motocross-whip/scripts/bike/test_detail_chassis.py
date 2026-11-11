"""Fast checks of detail_chassis.py against the spec table (research/crf250r-2026.md) and Honda's photos.
python3 -m pytest -q test_detail_chassis.py   (a few seconds)"""
import math
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams               # noqa: E402
import parts              # noqa: E402
import detail_chassis as dc   # noqa: E402


@pytest.fixture(scope="module")
def V():
    return {name: np.asarray(fn().V, float) for name, fn in dc.PARTS.items()}


ground = parts.to_ground


def test_vertex_budget(V):
    assert sum(len(v) for v in V.values()) < 260000          # micro pass round 3 brief: up to 260,000


def test_footpeg_height_is_422_mm(V):
    """SPEC: footpeg height 422 mm: top of the teeth at the peg's root, on the ground."""
    G = ground(V["footpegs"])
    for side in (1, -1):
        root = G[(G[:, 1] * side > 0.150) & (G[:, 1] * side < 0.175)]
        assert abs(root[:, 2].max() - 0.422) < 0.006, root[:, 2].max()


def test_footpeg_tips_are_where_the_rear_photo_has_them(V):
    """REAR: tips at columns 1673 and 2328, row about 1294."""
    P = V["footpegs"]
    for side, col in ((1, 1673), (-1, 2328)):
        tip = P[np.argmax(P[:, 1] * side)]
        top = P[(P[:, 1] * side > 0.235)][:, 2].max()
        u, v = cams.CAMS["rear"].project(np.array([tip[0], tip[1], top]))[0]
        assert abs(u - col) < 8 and abs(v - 1294) < 8, (u, v)


def test_ground_clearance_leaves_330_mm_under_the_cradle(V):
    """SPEC: 330 mm under the engine's guard. The cradle rails sit just above it and nothing of the frame is lower."""
    G = ground(V["frame"])
    low = G[(G[:, 0] > 0.55) & (G[:, 0] < 1.0)][:, 2].min()
    assert 0.330 <= low < 0.368, low


def test_swingarm_turns_on_the_shared_pivot_and_reaches_the_axle(V):
    """SPEC: swingarm 585.2 mm. parts.PIVOT, the pivot cap in the photos cast on the plate's plane, gives 584.5."""
    assert abs(np.linalg.norm(parts.PIVOT - parts.RA) - 0.5852) < 0.002
    S = V["swingarm"]
    nose = S[S[:, 0] > parts.PIVOT[0] + 0.010]             # pivot tube and the slider wrapped round it
    r = np.hypot(nose[:, 0] - parts.PIVOT[0], nose[:, 2] - parts.PIVOT[2])
    assert r.max() < 0.036 and len(nose) > 20
    assert S[:, 0].min() < -0.028                                     # LEFT, RIGHT: the cast end 28 to 31 mm behind the axle


def test_muffler_outlet_is_where_the_rear_photo_has_it():
    """REAR: outlet at about pixel (2202, 788)."""
    u, v = cams.CAMS["rear"].project(dc.OUTLET)[0]
    assert abs(u - 2202) < 6 and abs(v - 788) < 6, (u, v)


def test_muffler_top_reaches_the_left_photo_line(V):
    """LEFT: the muffler's top edge at the rear is at row 878 near column 2950 (it was 20 px too low before)."""
    E = V["exhaust"]
    rear = E[E[:, 0] < 0.03]
    v = cams.CAMS["left"].project(rear)[:, 1].min()
    assert abs(v - 878) < 8, v


def test_rear_tyre_has_room(V):
    """Nothing of the chassis inside the rear tyre's sweep (tyre 105 mm wide, 12 mm of air each side)."""
    for name in ("swingarm", "linkage", "shock", "exhaust", "subframe", "frame", "brake_pedal"):
        P = V[name]
        near = (np.hypot(P[:, 0], P[:, 2] - parts.R_REAR) < parts.R_REAR + 0.012) & (np.abs(P[:, 1]) < 0.0525 + 0.012)
        assert not near.any(), (name, int(near.sum()))


def test_link_lengths_match_both_profile_photos():
    """Pro-Link bolts seen from both sides: link 144 mm, arm 49 and 78 mm."""
    assert abs(np.linalg.norm(dc.LINK_B - dc.F_LINK) - 0.144) < 0.004
    assert abs(np.linalg.norm(dc.LINK_T - dc.LINK_B) - 0.049) < 0.004
    assert abs(np.linalg.norm(dc.LINK_T - dc.SHOCK_A) - 0.078) < 0.004


# ---------------------------------------------------------------- round 2: fits with the merged bike
def test_chain_slider_follows_the_shared_chain_line(V):
    """The slider's upper face is parts.chain_top(x) - 0.009 from x 0.44 to the pivot; nothing of the swingarm
    stands in the chain's top run (15 mm tall, 21 wide)."""
    S = V["swingarm"]
    band = S[np.abs(S[:, 1] - parts.CHAIN_Y) < 0.0105]
    for x in (0.46, 0.50, 0.54, 0.564, 0.58):
        top = band[np.abs(band[:, 0] - x) < 0.006][:, 2].max()
        assert top < float(parts.chain_top(x)) - 0.0078, (x, top)
        assert abs(top - (float(parts.chain_top(x)) - 0.009)) < 0.0015, (x, top)
    assert dc.R_PIV <= 0.019


def test_frame_keeps_out_of_the_chain_runs(V):
    """Roller and lower cross member under the lower run (left photo: straight from (0.604, 0.428) to (0.171, 0.270),
    15 mm tall, 21 wide); nothing of the frame in the top run either."""
    F = V["frame"]
    band = F[(np.abs(F[:, 1] - parts.CHAIN_Y) < 0.0105) & (F[:, 0] > 0.45) & (F[:, 0] < 0.60)]
    low = 0.270 + (band[:, 0] - 0.171) * 0.3649
    assert not (np.abs(band[:, 2] - low) < 0.0075).any()
    assert not (np.abs(band[:, 2] - parts.chain_top(band[:, 0])) < 0.0075).any()


def test_chain_guide_slot_takes_the_chain(V):
    """The wear blocks leave a slot round the lower run, whichever way it comes onto the 50T sprocket."""
    G = V["chain_guide"]
    x0, z0, slope, half = dc.GUIDE_SLOT
    band = G[np.abs(G[:, 1] - parts.CHAIN_Y) < 0.0115]              # the chain's width (21 mm) and 1 mm each side
    assert (np.abs(band[:, 2] - (z0 + slope * (band[:, 0] - x0))) > half - 0.001).all()
    teeth = G[np.abs(G[:, 1] - parts.CHAIN_Y) < 0.0065]                 # the 50T's plane, 2 mm each side
    assert np.hypot(teeth[:, 0], teeth[:, 2] - parts.RA[2]).min() > 0.1306 + 0.002     # clear of the sprocket's teeth
    ang = np.degrees(np.arctan2(band[:, 2] - parts.RA[2], band[:, 0]))
    on = (ang > 95) | (ang < -64)                                       # the chain wraps the 50T from the top run's
    wrap = band[on & (np.hypot(band[:, 0], band[:, 2] - parts.RA[2]) < 0.1306 + 0.012)]   # tangent round to the lower's
    assert (np.hypot(wrap[:, 0], wrap[:, 2] - parts.RA[2]) < 0.1264 - 0.0075).all()
    for x in (0.13, 0.15, 0.17, 0.19):
        runs = (0.2485 + 0.375 * (x - 0.15), 0.270 + (x - 0.171) * 0.3649, 0.270 - max(0.171 - x, 0) * 0.494)
        for z in runs:
            assert abs(z - (z0 + slope * (x - x0))) + 0.0075 < half, (x, z)


def test_frame_outline_is_clean_and_its_rim_even():
    """Round 3 (crumpled, serrated frame plates): the cast outline is resampled and smoothed before use, and the
    rounded edge is a function of the exact distance to it, so the rim's height cannot wander from vertex to vertex."""
    o = dc._frame_outline()
    d = np.diff(np.vstack([o, o[:1]]), axis=0)
    turn = np.abs((np.diff(np.degrees(np.arctan2(d[:, 1], d[:, 0])), append=0.0) + 180) % 360 - 180)[:-1]
    assert turn.max() < 45, turn.max()                               # no pixel steps, no folded tips
    dist = dc._edge_dist([o])
    mids = (o + np.roll(o, -1, axis=0)) / 2
    assert max(dist(u, v) for u, v in mids[::10]) < 1e-9


def test_head_tube_leaves_room_for_the_stem_and_clamps(V):
    """detail_front.py: lower clamp's top face at t 0.716, top clamp's bridge from 0.913, stem r 14.5 mm."""
    F = V["frame"]
    t = (F - parts.STEER0) @ parts.UP
    rad = np.linalg.norm(F - parts.STEER0 - np.outer(t, parts.UP), axis=1)
    near = rad < 0.036
    assert t[near].min() >= 0.716 + 0.001 - 1e-6 and t[near].max() <= 0.913 - 0.001 + 1e-6, (t[near].min(), t[near].max())
    assert rad.min() > 0.0145 + 0.002, rad.min()


# ---------------------------------------------------------------- micro pass (2026-11-11): axle ends, blocks, arm
def test_axle_ends_stand_out_as_in_the_rear_photo(V):
    """REAR row 1545: the left head's lit edge at y 0.1303, the right axle's end at col 2205 (y -0.1405)."""
    A = V["rear_axle"]
    assert abs(A[:, 1].max() - 0.1303) < 0.0012, A[:, 1].max()
    assert abs(A[:, 1].min() + 0.1402) < 0.0012, A[:, 1].min()


def test_axle_nut_is_a_32_mm_hexagon(V):
    """Honda's 22 mm U-nut takes a 32 mm socket: corners at 18.5 mm from the axle, flats at 16."""
    A = V["rear_axle"]
    hexp = A[(A[:, 1] < -dc.Y_BLK_O - 0.0013) & (A[:, 1] > -dc.Y_BLK_O - dc.NUT_H + 0.0013)]
    r = np.hypot(hexp[:, 0] - parts.RA[0], hexp[:, 2] - parts.RA[2])
    assert abs(r.max() - 0.016 / math.cos(math.pi / 6)) < 0.0003, r.max()
    assert dc.NUT_AF == 0.032


def test_block_slides_in_its_slot():
    """The block (37.3 x 37.4) is 0.2 mm inside the slot's height and clear of its arc-shaped rear end."""
    assert dc.SLOT_H - dc.BLK[1] >= 0.00015
    fc = dc.WIN[0] + dc.REAR_R
    corner = fc - math.sqrt(dc.REAR_R ** 2 - dc.BLK[1] ** 2)
    assert corner < -dc.BLK[0] - 0.0001, corner
    assert dc.POCKET_F > dc.BLK[0]


def test_arm_is_the_tall_box_of_the_photos():
    """Both side photos: the arm is 60 mm tall at its rear weld and 75 mm from s 0.26 on (it was 37 and 57 mm)."""
    h = lambda s: float(dc._t_top(s) - dc._t_bot(s))
    assert abs(h(0.08) - 0.0618) < 0.003 and abs(h(0.30) - 0.0760) < 0.003 and abs(h(0.40) - 0.0760) < 0.003


def test_index_marks_two_rows_of_nine_each_side(V):
    """lr34, rr34: a row of nine marks above and below each window, 2 mm apart."""
    m = dc.swingarm()
    assert sum(1 for q in m.M if q == "groove") == 2 * 2 * 9 * 6
    assert dc.MARKS[:2] == (9, 0.002)


def test_brake_pedal_is_not_shadowed_by_the_caliper():
    """detail_wheels.py's caliper is called rear_brake: the pedal and master cylinder keep their own name."""
    import detail_wheels
    assert "rear_brake" not in dc.PARTS and "brake_pedal" in dc.PARTS
    assert "rear_brake" in detail_wheels.PARTS


def test_chain_guide_is_the_stock_plate(V):
    """LEFT u 2743..2913: the plate reaches from the block's nose (x 0.183) back over the 50T (x 0.051); it lies
    outside the chain (0.0985) and inside the arm's outer face; three M6 flange bolts (fiche K95CF3200 18, 19)."""
    G = V["chain_guide"]
    assert G[:, 0].min() < 0.056 and 0.180 < G[:, 0].max() < 0.205, (G[:, 0].min(), G[:, 0].max())
    assert dc.GUIDE_Y[0] > parts.CHAIN_Y + 0.0105 + 0.005 and dc.GUIDE_Y[1] < 0.129
    assert len(dc.GUIDE_BOLTS) == 3


def test_muffler_section_is_the_rear_photos_octagon():
    """REAR (cast on x 0): the cap's outer side is flat from z 0.799 to 0.866 and its top flat from y -0.1015 to
    -0.1658; the outlet's lip is 37 mm (54.8 px) and square to the cap's leaning face."""
    S = dc.MUF_SEC
    side = S[np.abs(S[:, 1]) < 0.35]
    assert (side[side[:, 0] > 0][:, 0] > 0.97).all()
    top = S[(S[:, 1] > 0.97)]
    assert top[:, 0].min() < -0.55 and top[:, 0].max() > 0.35
    E = np.asarray(dc.exhaust().V, float)
    ax = (E - dc.OUTLET) @ dc.OUT_AXIS
    r = np.linalg.norm(np.cross(E - dc.OUTLET, dc.OUT_AXIS), axis=1)
    lip = r[(ax > -0.004) & (ax < 0.001) & (r < 0.021)]                  # the part standing proud of the cap
    assert abs(lip.max() - 0.0185) < 0.0006, lip.max()


# ---------------------------------------------------------------- round 3: the frame's rear casting
def test_frame_rear_casting_follows_both_photos():
    """Each side's plate covers its own photo's lower section (front branch, bottom, cradle weld) and, on the right
    only, the master cylinder's two tabs; the two sides' lower sections agree within 11 mm (one casting, mirrored;
    the photos disagree by 10 mm at the bottom of the cradle weld, LEFT z 0.348, RIGHT 0.358: each side keeps its own)."""
    from scipy.spatial import cKDTree
    from geom import inside
    L, R = dc._side_outline(1), dc._side_outline(-1)
    for s, o in ((1, L), (-1, R)):
        view = "left" if s > 0 else "right"
        low = dc._cast_px(view, dc.LOW_PX[view], s * dc.Y_MID)
        g = np.stack(np.meshgrid(np.arange(0.50, 0.70, 0.002), np.arange(0.33, 0.50, 0.002)), -1).reshape(-1, 2)
        dist = dc._edge_dist([low])
        g = g[inside(low, g)]
        g = g[np.array([dist(u, v) for u, v in g]) > 0.003]          # 3 mm inside the traced polygon
        assert inside(o, g).all()
    tabs = dc._cast_px("right", dc.TAB_BOLTS_PX, -dc.Y_MID)
    assert inside(R, tabs).all() and not inside(L, tabs).any()
    lowL = L[(L[:, 1] < 0.42) & (L[:, 0] > 0.55)]
    assert cKDTree(R).query(lowL)[0].max() < 0.011


def test_pivot_ends_are_the_photos_nut_and_recessed_head():
    """piv2: right, a 21 mm nut in a 31.8 mm counterbore (its corners clear the bore); left, a head in a hexagonal
    recess 27.7 mm across flats with a dark gap round it; both ends hollow."""
    af, _ = dc.PIV_NUT
    assert af / math.cos(math.pi / 6) < 2 * dc.PIV_CB[0] - 0.003
    assert 0.002 < dc.PIV_HEX[0] - dc.PIV_HEAD[0] < 0.004
    assert dc.PIV_END[1] > 0.003 and dc.PIV_HEAD[1] > 0.004


def test_master_cylinder_clears_the_frame_tabs(V):
    """The tabs are lugs outside the cylinder's own lugs: nothing of the brake part inside the right plate."""
    from geom import inside
    c = dc._Cast(-1)
    B = V["brake_pedal"]
    P = B[inside(c.o, B[:, [0, 2]])]
    yo, yi = c.surf(P[:, [0, 2]], True), c.surf(P[:, [0, 2]], False)
    depth = np.minimum(yo - np.abs(P[:, 1]), np.abs(P[:, 1]) - yi)
    assert depth.max() < 0.0005, depth.max()


def test_master_cylinder_is_one_casting_where_the_photos_have_it():
    """Round 4: one closed casting (not two tubes), its outline on RIGHT's and its width on REAR's readings."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    m = dc._surface_nets(dc._mc_sdf, (0.425, -0.145, 0.472), (0.505, -0.098, 0.586), 0.0012, "mc_cast")
    V, F = np.asarray(m.V), np.asarray(m.F)
    e = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 3]], F[:, [3, 0]]])
    n, _ = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(V), len(V))), directed=False)
    assert n == 1
    _, cnt = np.unique(np.sort(e, axis=1), axis=0, return_counts=True)
    assert (cnt == 2).all()                                   # watertight: every edge in two faces
    lo, hi = V.min(0), V.max(0)
    assert abs(lo[0] - 0.4335) < 0.0015 and abs(hi[2] - 0.5790) < 0.0015 and abs(lo[2] - 0.4796) < 0.0015
    assert -0.1350 < lo[1] < -0.1335 and -0.1075 < hi[1] < -0.1060            # REAR: cols 2143..2181
    R, B = cams.CAMS["right"], cams.CAMS["rear"]
    up = np.array([dc.MC_AXIS[1][0], dc.MC_YC, dc.MC_AXIS[1][1]])
    assert np.abs(R.project(up[None])[0] - (1627, 1319)).max() < 2          # the neck's top under the banjo
    assert abs(B.project(np.array([[dc.MC_AXIS[0][0], dc.MC_YC, 0.47]]))[0][0] - 2162.5) < 2   # the boot's centre
    # its lugs seat on the frame tabs from inside: 0.5 mm off their inner face, nothing outboard of it beside the tabs
    # (ahead of the tabs' rear edge x 0.479 (TAB_PX u 1639), above the lower tab's foot at z 0.4925; the skirt under it is wider, REAR)
    near = V[(V[:, 0] > 0.479) & (V[:, 2] > 0.4925)]
    assert near[:, 1].min() > -(dc.Y_PLATE - dc.TAB_T) + 0.0004


def test_frame_leg_turns_away_and_the_pivot_boss_has_its_rim():
    """Round 4: the leg's face is crowned (it turns away over the last 18 mm, most at the C round the engine: detail
    photo 475836), and the boss round the pivot is 34 mm in radius with a raised rim at its fold (RIGHT, LEFT)."""
    from geom import inside
    for s in (1, -1):
        c = dc._Cast(s)
        xs = np.linspace(0.50, 0.66, 641)
        P = np.column_stack([xs, np.full(len(xs), 0.60)])
        P = P[inside(c.o, P)]
        yo = c.surf(P, True)
        front = c.surf(np.array([[P[-1, 0] - 0.005, 0.60]]), True)[0]
        assert yo.max() - front > 0.0015                     # 5 mm inside the front edge: turned away
        piv = c.piv
        at = lambda r: c.surf((piv + r * np.array([-0.7071, 0.7071]))[None], True)[0]   # noqa: E731
        assert at(dc.BOSS_R - dc.BOSS_RIM[0]) - at(0.020) > 0.0006     # the rim stands over the boss's face
        assert at(0.020) - at(dc.BOSS_R + 0.006) > 0.0012              # the boss stands over the leg
