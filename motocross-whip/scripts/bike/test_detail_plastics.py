"""Fast checks of the seat and rear plastics (plastics.py, detail_plastics.py) against the photo measurements written
next to their tables (research/detail-ledger/plastics.md).

python3 -m pytest -q test_detail_plastics.py
"""
import os

import numpy as np
import pytest
from PIL import Image

import cams
import detail_plastics as dp
import plastics as pl


@pytest.fixture(scope="module")
def seat():
    return pl.seat()


def test_seat_plan_follows_the_top_photo(seat):
    """The hem's plan (the seat's outermost line) through the top camera lands on the measured columns and rows."""
    V = np.asarray(seat.V)
    for u, hw_px in pl.SEAT_PLAN_PX:
        if not 1975 < u < 2745:                                # the nose's corners and the tail's point are
            continue                                           # rounded by the 2 mm smoothing
        x = cams.CAMS["top"].on_plane(np.array([u]), np.array([pl.SEAT_ROW]), "z", 0.96)[0][0]
        k = np.abs(V[:, 0] - x) < 0.002
        half = (V[k, 1].max() - V[k, 1].min()) / 2
        want = pl.seat_hem_hw(x)
        assert abs(half - want) < 0.0025, (u, half, want)
    xs, hw = pl._seat_plan()
    assert abs(xs[-1] - 0.7826) < 0.002 and abs(xs[0] - 0.0776) < 0.002        # nose front, tail point
    assert abs(hw.max() - 0.0888) < 0.0015                                       # 99.5 px at u 2260..2620
    assert abs(V[:, 1].max() + V[:, 1].min()) < 0.001                           # symmetric


def test_seat_top_line_on_the_left_photo(seat):
    """The seat's highest vertex at each station projects onto the photo's silhouette row within 2 px."""
    V = np.asarray(seat.V)
    L = cams.CAMS["left"]
    a = np.asarray(Image.open(os.path.join(pl.HERE, "..", "..", "reference", "crf250r-2026", cams.FILES["left"]))
                   .convert("RGB")).astype(float).min(axis=2)
    for u in (2050, 2200, 2300, 2450, 2600, 2750, 2830):
        x = L.on_plane(np.array([float(u)]), np.array([780.0]), "y", -0.025)[0][0]
        k = np.abs(V[:, 0] - x) < 0.003
        v = L.project(V[k])[:, 1].min()
        col = a[650:900, u]
        photo = 650 + int(np.argmax(col < 235.0))
        assert abs(v - photo) < 2.5, (u, v, photo)


def test_seat_hem_on_each_side_photo(seat):
    """The hem's outer points, through each side's camera, on the seam rows (SEAT_HEM_PX) less HEM_LIFT."""
    S = pl._seat_sections()
    for side, view in ((1, "left"), (-1, "right")):
        cam = cams.CAMS[view]
        k = S.B[:, 1] * side > 0.04
        P = np.column_stack([S.B[k], S.zb[k] - pl.HEM_LIFT])
        uv = cam.project(P)
        hm = np.array(pl.SEAT_HEM_PX, float)
        ul = uv[:, 0] if side > 0 else 3999.0 - uv[:, 0]
        m = (ul > 2000) & (ul < 2840)
        d = uv[m, 1] - np.interp(ul[m], hm[:, 0], hm[:, 1])
        assert np.abs(d).max() < 3.0, (view, np.abs(d).max())


def test_seat_shoulder_against_the_rear_photo(seat):
    """The nose seen from behind: half-widths under the top within 7 px of the photo's (rms under 4 px)."""
    photo = {514: 34, 518: 52, 522: 60, 526: 65.5, 530: 71.5, 534: 74.5, 538: 76.5, 542: 79.5, 546: 81.5,
             550: 83.5, 554: 85, 558: 85.5, 562: 87}
    uv = cams.CAMS["rear"].project(np.asarray(seat.V))
    top = uv[:, 1].min()
    err = []
    for v, hw in photo.items():
        k = np.abs(uv[:, 1] - (v - 513.0 + top)) < 1.0
        err.append((uv[k, 0].max() - uv[k, 0].min()) / 2 - hw)
    err = np.array(err)
    assert np.abs(err).max() < 7.0 and np.sqrt((err ** 2).mean()) < 4.0, err


def test_seat_mesh_is_clean(seat):
    V = np.asarray(seat.V)
    assert all(0 <= i < len(V) for f in seat.F for i in f) and len(seat.F) == len(seat.M)
    area = np.array([np.linalg.norm(np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])) for f in seat.F])
    assert area.min() > 1e-8                                    # no zero-area faces
    assert all(len(seat.uv[i]) == len(f) for i, f in enumerate(seat.F) if i in seat.uv)
    assert sum(1 for m in seat.M if m == "seat") == len(seat.uv)   # every cover face carries its grain's UVs
    # compare.raster draws faces under 2 px as one pixel: keep the cover's top faces over that in the top view
    P = cams.CAMS["top"].project(V) / 2
    small = [(np.ceil(P[list(f)].max(0)) - np.floor(P[list(f)].min(0))).max() <= 2
             for f, m in zip(seat.F, seat.M) if m == "seat" and np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])[2] > 0]
    assert np.mean(small) < 0.02


def test_seat_grain_texture():
    """The grain's normal map exists, is tileable (its edges match) and its pebble pitch is the measured 1.3 mm."""
    path = os.path.join(dp.TEXTURES, "seat_grain_n.png")
    a = np.asarray(Image.open(path)).astype(float)
    g = dp.SEAT_GRAIN
    assert a.shape == (g["size"], g["size"], 3)
    assert abs(a[0] - a[-1]).mean() < 40 and abs(a[:, 0] - a[:, -1]).mean() < 40
    n = (a / 255.0) * 2 - 1
    assert (n[..., 2] > 0.3).all()                              # a bump map, not noise
    # pitch: the autocorrelation of the x slope falls to its first minimum at about half a pebble
    s = n[..., 0] - n[..., 0].mean()
    f = np.abs(np.fft.rfft(s, axis=1)) ** 2
    k = np.argmax(f.mean(axis=0)[1:]) + 1
    pitch_mm = g["tile"] / k
    assert 0.5 < pitch_mm < 2.0, pitch_mm
    assert dp.MATERIALS["seat"]["normal"] == "stock/seat_grain_n.png"


@pytest.fixture(scope="module")
def fender():
    return pl.rear_fender()


def test_rear_fender_plan_and_point(fender):
    """Half-widths at the top photo's columns within 2 mm; an arrow point (half-width falls 50 mm in the last 50 mm)
    and not the old round tongue (60 mm there); the tip at the mean of the top and side photos."""
    V = np.asarray(fender.V)
    px, phw, T, E = pl._fender_lines()
    for x in (-0.25, -0.20, -0.14, -0.06):
        k = np.abs(V[:, 0] - x) < 0.0035
        half = (V[k, 1].max() - V[k, 1].min()) / 2
        assert abs(half - np.interp(x, px, phw)) < 0.002, (x, half)
    assert abs(V[:, 0].min() - (-0.2971)) < 0.002
    x0 = V[:, 0].min()
    k = np.abs(V[:, 0] - (x0 + 0.025)) < 0.002
    assert (V[k, 1].max() - V[k, 1].min()) / 2 < 0.036    # the point: 25 mm from it 32 mm (TOP u 3160: 36 px)
    assert abs(V[:, 1].max() + V[:, 1].min()) < 0.001


def test_rear_fender_profile_on_the_left_photo(fender):
    """The top line and the near flank's lower edge project onto the photo's rows within 3 px."""
    V = np.asarray(fender.V)
    L = cams.CAMS["left"]
    uv = L.project(V)
    for (u, v) in pl.FENDER_TOP_PX[3:-2]:
        k = np.abs(uv[:, 0] - u) < 5.0
        assert abs(uv[k, 1].min() - v) < 3.0, (u, uv[k, 1].min(), v)
    for (u, v) in pl.FENDER_LOW_PX[2:-2]:
        k = np.abs(uv[:, 0] - u) < 5.0
        assert abs(uv[k, 1].max() - v) < 3.5, (u, uv[k, 1].max(), v)


def test_side_cover_ribs():
    """The side panels' black lower part carries UVs on every face (the Y-rib normal map), right-handed on the outer
    faces (or the ribs read as grooves); the map's rib lattice is the measured 9.0 mm pitch (LEFT: 12 px)."""
    m = pl.side_panels()
    V = np.asarray(m.V)
    faces = [i for i, q in enumerate(m.M) if q == "black_texture"]
    assert faces and all(i in m.uv for i in faces)
    good = []
    for i in faces:
        P, uv = V[list(m.F[i])][:3], np.array(m.uv[i])[:3]
        A = np.array([uv[1] - uv[0], uv[2] - uv[0]])
        if abs(np.linalg.det(A)) < 1e-12:
            continue
        T, B = np.linalg.solve(A, np.array([P[1] - P[0], P[2] - P[0]]))
        n = np.cross(P[1] - P[0], P[2] - P[0])
        if n[1] * P[0, 1] > 0:                                   # outer face
            good.append(np.dot(np.cross(T, B), n) > 0)
    assert np.mean(good) > 0.99
    a = np.asarray(Image.open(os.path.join(dp.TEXTURES, "side_cover_n.png")))
    assert a.shape[:2] == (dp.SIDE_COVER["size"][1], dp.SIDE_COVER["size"][0])
    h, sx, sy = dp._tristar_height()
    assert abs(h.shape[1] * sx - 2 * dp.SIDE_COVER["pitch"]) < 1e-6 and abs(sx / sy - 1.0) < 0.002
    assert 0.08 < (h > 0.05).mean() < 0.25                     # ribs cover a measured share of the surface


def test_round2_plastics():
    """The panel's lower edge over the can is each photo's red edge (round 3: PANEL_LOW_PX, within 2 px; the right
    one the RIGHT photo's red-to-silver edge, 20 to 27 px over round 2's); the intake carries the green foam with UVs;
    the panel bolt sits at its pocket's floor; the mudguard's top fills the wall's arch ahead of the wall."""
    assert np.interp(2800, *np.array(pl.PANEL_LOW_PX[-1]).T) == 936.5          # RIGHT, the red-to-silver edge
    for side in (1, -1):
        Pn = pl._panel(side)
        for u in (2760, 2800, 2830, 2850, 2870):
            v = float(np.interp(u, *np.array(pl.PANEL_LOW_PX[side]).T))
            uu = u if side > 0 else 3999.0 - u
            k = np.abs(Pn.px[:, 0] - uu) < 2.0
            assert abs(Pn.px[k, 1].max() - v) < 2.0, (side, u, Pn.px[k, 1].max(), v)
    m = pl.side_panels()
    mesh = [i for i, q in enumerate(m.M) if q == "intake_foam"]
    assert mesh and all(i in m.uv for i in mesh)
    assert "intake_foam" in dp.MATERIALS and dp.CLASS["intake_foam"] == "black"
    b = np.asarray(dp.panel_bolts().V)
    u, v = dp._px(1, *pl.PANEL_BOLT_PX)
    face = pl.panel_point(1, u, v, inset=0.006)
    assert b[b[:, 1] > 0][:, 1].min() < face[1] - pl.POCKET_D + 0.001      # the bolt starts at the floor
    t = np.asarray(dp.mudguard_top().V)
    assert t[:, 0].min() > dp._wall_x() + 0.002 and t[:, 0].max() < 0.204   # ahead of the wall, behind the member


def test_round3_panel_tail():
    """The panel's tail (round 3): it ends in the photo's point (no upright rear edge standing proud of the fender: the
    lr34 "wedge"), its rear edge is D's seam with the fender's flank (within 2 px) and lies on that flank (the 3 mm
    shell plus 0.5 mm, within 1 mm), its crease is at TOP's half-width (within 3 mm), and its top is smooth (second
    differences along its rows under 1.5 mm at 3 px steps: the round 2 wrinkle at x 0.085..0.125 was 20 mm)."""
    for side in (1, -1):
        Pn = pl._panel(side)
        ul = Pn.px[:, 0] if side > 0 else 3999.0 - Pn.px[:, 0]
        assert ul.max() < pl.PANEL_TIP_PX[0] + 2.0
        for u, v in pl.PANEL_SEAM_TAIL_PX[:-1]:
            i = int(np.argmin(np.hypot(ul - u, Pn.px[:, 1] - v)))
            assert np.hypot(ul[i] - u, Pn.px[i, 1] - v) < 2.0, (side, u, v)
            P = pl.panel_point(side, *Pn.px[i])               # the outline's own point: a boundary vertex
            assert abs(abs(P[1]) - pl.fender_outer_y(P[0], P[2]) - 0.0035) < 0.0015, (side, u, P)
        for u, v in pl.PANEL_CREASE_PX[3::3]:
            uu = u if side > 0 else 3999.0 - u
            P = pl.panel_point(side, uu, v)
            want = np.interp(P[0], *np.array(pl.PANEL_CREASE_Y).T)
            assert abs(abs(P[1]) - want) < 0.003, (side, u, P, want)
    Pn = pl._panel(1)
    for v in (796, 800, 806):
        ys = np.array([pl.panel_point(1, float(u), float(v))[1] for u in range(2850, 2936, 3)
                       if pl.inside(Pn.px, np.array([[u, v]], float))[0]])
        assert len(ys) > 20 and np.abs(np.diff(ys, 2)).max() < 0.0015, v


def test_round3_tunnel_wall():
    """The wall under the tail (round 3): its upper part is the dome, DOME_D deep at the ledge's centre; the rib
    blocks stand proud behind it but stay inside the fender's root (its flanks at 75.5 mm, 3 mm shell)."""
    V = np.asarray(dp.tail_under().V)
    X0 = dp._wall_x()
    uc, vc, a, b = dp.WALL_DOME
    zc = cams.CAMS["rear"].on_plane(np.array([uc]), np.array([vc - 8.0]), "x", X0)[0][2]
    k = (np.abs(V[:, 1]) < 0.02) & (np.abs(V[:, 2] - zc) < 0.004)
    assert abs(V[k, 0].max() - (X0 + 0.002 + dp.DOME_D)) < 0.0015, V[k, 0].max()
    k = (V[:, 0] < X0 - 0.0025) & (V[:, 2] > 0.86) & (V[:, 2] < 0.93)              # the rib blocks' faces
    assert k.any() and np.abs(V[k, 1]).max() < 0.0715


def test_round4_intake_and_airbox_cover():
    """Round 4, the left panel's intake: the opening is the photo's (red mesh edge vertices on INTAKE_PX within 1 px,
    nothing red across it); the scoop is 0 on its outline and SCOOP_D at the opening (facet above, lip below); the
    foam sits INTAKE_FOAM_D behind the edge. The airbox cover: its plateau stands COVER_RISE over its edge, and the
    ribbed side cover is cut away round it; the ribs' lattice is 9.0 mm, 12 px in LEFT. The right panel has no
    intake."""
    L = cams.CAMS["left"]
    o = np.array(pl.INTAKE_PX)
    for u, v in pl.SCOOP_PX[::4]:
        assert pl.scoop_depth(u, v) < 0.0002, (u, v)
    assert abs(pl.scoop_depth(2480.0, 914.7) - pl.SCOOP_D[0]) < 0.0006               # under the top edge
    assert abs(pl.scoop_depth(2500.0, 965.6) - pl.SCOOP_D[1]) < 0.001                # over the lower-rear edge
    m = pl.side_panels()
    V = np.asarray(m.V)
    mat_v = lambda name: np.unique([i for fi, q in enumerate(m.M) if q == name for i in m.F[fi]])
    foam, red = mat_v("intake_foam"), mat_v("plastic_red")
    assert (V[foam, 1] > 0).all()                                                    # left only
    near = L.project(V[red])
    near = near[(np.abs(near[:, 0] - 2485) < 105) & (np.abs(near[:, 1] - 940) < 45)]
    d = np.array([np.hypot(*(o - p).T).min() for p in near])
    assert (d < 1.0).sum() > 60                                                       # the opening's own edge
    edge = pl.panel_point(1, 2480.0, 914.7)
    fv = V[foam]
    k = np.hypot(*(L.project(fv) - [2480.0, 925.0]).T) < 6.0
    assert k.any() and abs(fv[k, 1].mean() - (edge[1] - pl.INTAKE_FOAM_D)) < 0.0015
    Pn = pl._panel(1)
    C = np.asarray(pl._airbox_cover(Pn, L).V)
    k = np.hypot(*(L.project(C) - [2290.0, 1080.0]).T) < 15.0                       # the plateau's middle
    top = np.array([Pn.width(x) for x in C[k, 0]]) - 0.006 - pl.COVER_SET + pl.COVER_RISE
    assert k.any() and np.abs(C[k, 1] - top).max() < 0.0003
    bt = V[mat_v("black_texture")]
    ut = L.project(bt[bt[:, 1] > 0])                                                   # the left side cover
    assert not pl.inside(np.array(pl.COVER_TOP_PX)[:, :2], ut).any()
    assert pl.SIDE_COVER_TILE == 2 * 0.009 and abs(dp.SIDE_COVER["pitch"] - 12.0 * pl.MPP * 1000) < 0.1


def test_round4_mudguard_and_flap():
    """Round 4, inner mudguard and mud flap: the face's sides on REAR's columns 1913 / 2094 (4.5 px: the photo's face is 2.5 mm right of
    the centre line, the model's symmetric), its
    foot on row 999 (2.5 px); the flanges and tabs stop short of the subframe's rails (MUD_Y_MAX); the flap's back on
    LEFT's rear edge (MUD_FLAP_PX, 2 px), its foot clear of the tyre (5 mm); the two screws sit on the flap's back
    (0.5 mm); the thick flap replaces parts.py's single surface."""
    import parts as P
    R, L = cams.CAMS["rear"], cams.CAMS["left"]
    V = np.asarray(pl.inner_mudguard().V)
    uv = R.project(V[np.abs(V[:, 1]) <= pl.MUD_HW + 0.0005])
    k = np.abs(uv[:, 1] - 880) < 30
    assert abs(uv[k, 0].min() - 1913) < 4.5 and abs(uv[k, 0].max() - 2094) < 4.5, (uv[k, 0].min(), uv[k, 0].max())
    c = np.abs(uv[:, 0] - 2003.5) < 6
    assert abs(uv[c, 1].max() - 999) < 2.5, uv[c, 1].max()
    assert np.abs(V[:, 1]).max() < pl.MUD_Y_MAX + 0.003
    rings = np.array(pl._mud_flap_rings())
    q = L.project(rings[:, len(rings[0]) // 2])               # the back's centre line
    for v, uf, ur in pl.MUD_FLAP_PX:
        i = int(np.argmin(np.abs(q[:, 1] - v)))
        assert abs(q[i, 0] - ur) < 2.0 and abs(q[i, 1] - v) < 6, (v, q[i], ur)
    low = rings[-1]
    tyre = P.AXLE_Z + np.sqrt(np.maximum(0.335 ** 2 - low[:, 0] ** 2, 0.0))
    assert (low[:, 2] - tyre).min() > 0.005
    H = np.asarray(dp.mud_hardware().V)
    for s in (1, -1):
        h = H[H[:, 1] * s > 0]
        yc, zc = h[:, 1].mean(), h[:, 2].mean()
        xb = min(float(np.interp(-zc, -rings[:, 0, 2], [np.interp(yc + dy, r[:, 1], r[:, 0]) for r in rings]))
                 for dy in np.linspace(-0.00275, 0.00275, 5))          # the back under the head's rim, most rearward
        assert -0.0001 < xb - h[:, 0].max() < 0.0005, (xb, h[:, 0].max())
    assert "mud_flap" in dp.REPLACES and "rear_flap" in dp.PARTS


def test_round4_seats():
    """Round 4, seats instead of cuts: the shroud decks start DECK_SEAT inside the skin's top edge (on its 3 mm shell;
    audit 1.5 mm before); the panel bolt's pocket floor is flat and square to the bolt with a hole its shank passes
    through (audit 1.8 mm before)."""
    for side in (1, -1):
        edge = pl._shroud_shells(side)[1]
        rows = pl._deck(side)
        for p, r in zip(edge[::7], rows[::7]):
            assert abs(abs(p[1]) - abs(r[0, 1]) - pl.DECK_SEAT) < 1e-9 and abs(r[0, 2] - p[2]) < 1e-9
    B = np.asarray(dp.panel_bolts().V)
    assert pl.POCKET_HOLE > 0.0029 + 0.0002
    for side in (1, -1):
        u, v = dp._px(side, *pl.PANEL_BOLT_PX)
        seat = pl.panel_point(side, u, v, inset=0.006 + pl.POCKET_D)
        b = B[B[:, 1] * side > 0]
        inner = b[(b[:, 1] - seat[1]) * side < -0.0003]                 # the shank, behind the floor
        assert len(inner) and np.hypot(inner[:, 0] - seat[0], inner[:, 2] - seat[2]).max() < pl.POCKET_HOLE


def test_round5_seat_fender_panel_junction():
    """The junction (round 5): the seat's tail sits on the fender's deck (the deck 1.5 to 7 mm outside the hem within
    2.5 mm of the hem's lowest point, x 0.085 .. 0.11: no slit (4 to 8 mm before); the audit finds no cut); the
    fender's root is shallow
    (the lip's lower edge 3 to 8 mm under the top
    line at x 0.08 .. 0.10, 17 to 24 mm at x 0.0 .. 0.03: LEFT); both panels' top edges stay under the lip's top behind
    x 0.11 (the right one stood 3 mm over it in rounds 1 to 4); the tail ends square at PANEL_END_U."""
    F = np.asarray(pl.rear_fender().V)
    S = pl._seat_sections()
    for x in (0.085, 0.09, 0.10, 0.11):
        for sg in (1, -1):
            i = int(np.argmin(np.abs(S.B[:, 0] - x) + 10 * (S.B[:, 1] * sg < 0)))
            p = S.B[i]
            d = np.hypot(F[:, 0] - p[0], F[:, 1] - p[1])
            near = F[(d > 0.0015) & (d < 0.007) & (np.abs(F[:, 1]) > abs(p[1]))]
            gap = (S.zb[i] - pl.HEM_R) - near[:, 2].max()
            assert len(near) and -0.0005 < gap < 0.0025, (x, sg, gap)
    top, _ = pl._fender_top_edge()
    px, phw = pl._fender_lines()[:2]
    for x, lo, hi in ((0.08, 0.003, 0.008), (0.10, 0.003, 0.008), (0.03, 0.017, 0.024), (0.0, 0.017, 0.024)):
        h = pl._fender_half(x, float(np.interp(x, px, phw)))
        depth = top(x) - h[-5, 1]                              # the flank's top: the lip's lower edge
        assert lo < depth < hi, (x, depth)
    P = np.asarray(pl.side_panels().V)
    for sg in (1, -1):
        for x in (0.05, 0.07, 0.09, 0.11):
            pp = P[(np.abs(P[:, 0] - x) < 0.003) & (P[:, 1] * sg > 0) & (P[:, 2] > 0.9)]
            ff = F[(np.abs(F[:, 0] - x) < 0.003) & (np.abs(F[:, 1]) > 0.075)]
            assert pp[:, 2].max() < ff[:, 2].max() - 0.001, (sg, x, pp[:, 2].max(), ff[:, 2].max())
    for side in (1, -1):
        Pn = pl._panel(side)
        ul = Pn.px[:, 0] if side > 0 else 3999.0 - Pn.px[:, 0]
        end = Pn.px[ul > pl.PANEL_END_U - 1.5]
        assert end[:, 1].max() - end[:, 1].min() > 12.0          # an upright end, not a point
