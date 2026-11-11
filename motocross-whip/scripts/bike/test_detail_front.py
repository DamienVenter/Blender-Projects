"""Fast checks of the front-end detail module against the spec table (research/crf250r-2026.md). No Blender."""
import math

import numpy as np
import pytest

import cams
import detail_front as df
import parts


ground = parts.to_ground


@pytest.fixture(scope="module")
def built():
    return {name: fn() for name, fn in df.PARTS.items()}


def verts(mesh, mat=None):
    v = np.asarray(mesh.V, float)
    if mat is None:
        return v
    idx = sorted({i for f, m in zip(mesh.F, mesh.M) if m == mat for i in f})
    return v[idx]


def test_overall_width_is_the_handlebar_827_mm(built):
    assert abs(np.ptp(verts(built["bars"])[:, 1]) - 0.827) < 0.002                       # SPEC overall width


def test_bar_ends_sit_on_the_shared_bar_end(built):
    grip = np.vstack([verts(built["bars"], "grip_rubber"), verts(built["bars"], "grip_bead")])
    assert df.TIP[0] == cams.BAR_END[0] and df.TIP[2] == cams.BAR_END[2]                  # no FRONT_TIP override
    for side in (1, -1):
        d = np.linalg.norm(grip - df.TIP * [1, side, 1], axis=1)
        assert (np.abs(d - 0.01525) < 0.0002).sum() >= 70                                 # the end face's flat rim
        assert abs((side * grip[:, 1]).max() - cams.BAR_END[1]) < 0.0005                  # its outermost point


def _grip_frame(built, side, mat=None):
    sd = df._Side(side)
    g = verts(built["bars"], mat) if mat else np.vstack([verts(built["bars"], k) for k in ("grip_rubber", "grip_bead")])
    g = g[g[:, 1] * side > 0] - sd.T
    a = -(g @ sd.d)
    r = np.linalg.norm(g + np.outer(a, sd.d), axis=1)
    th = np.arctan2(g @ sd.u, g @ sd.f)                                                   # 0 ahead, pi/2 up
    return a, r, th


def test_grip_diamonds_36_round_2_5_mm_along(built):
    for side in (1, -1):
        a, r, th = _grip_frame(built, side, "grip_rubber")
        z = (a > df.G_ZONES[1][0] + 0.003) & (a < df.G_ZONES[1][1] - 0.003)
        tips = z & (np.abs(r - np.array([df.g_tip(x) for x in a])) < 2e-5)
        top = tips & (np.abs(th - math.pi / 2) < 0.06)                                    # tips along the top line
        rows = np.unique(np.round(a[top], 5))
        assert abs(np.median(np.diff(rows)) - 2 * df.G_PITCH) < 0.0002                    # DET829 FFT: 2.47 mm
        ring = tips & (np.abs(a - rows[3]) < 1e-5)
        t = np.unique(np.round(th[ring], 4))
        assert abs(np.median(np.diff(t)) - 2 * math.pi / df.G_ROUND) < 1e-3                # 36 round, 10 deg apart
        assert len(t) == df.G_ROUND - int(round((df.G_BAND[1] - df.G_BAND[0]) / (2 * math.pi / df.G_ROUND)))  # band


def test_grip_diameters_flange_and_rings(built):
    for side in (1, -1):
        a, r, th = _grip_frame(built, side)
        body = r[(a > 0.0085) & (a < 0.0095) & (np.abs(th - math.pi / 2) < 0.5)]
        assert abs(2 * body.max() - 0.0300) < 0.0003                                      # FRONTv / REARv: 30 mm
        assert abs(2 * r[(a > 0.104) & (a < 0.111)].max() - 0.0283) < 0.0004              # tapering to 28.2
        assert abs(2 * r.max() - 0.058) < 0.0003                                          # flange 58 mm (lf34, TOPv)
        fl = a[r > 0.0285]
        assert 0.118 < fl.min() and fl.max() < 0.1225                                     # TOPv: a 118..121
        for c in df.G_RINGS:                                                              # groove round the top
            top = r[(np.abs(a - c) < 0.0009) & (np.abs(th - math.pi / 2) < 0.3)]
            assert top.max() < df.g_tip(c) - df.G_BEAD[1] + 1e-5


def test_overall_height_is_1262_mm_at_the_bars(built):
    # SPEC 1262: the bars (bar, holders, pad, grips) top out at the grips' flange rims 6 mm under it; the hand
    # controls stand 9..12 mm over it, as measured in Honda's photos (hood REAR, reservoir cap RIGHT)
    bars = ground(verts(built["bars"]))[:, 2].max()
    ctrl = ground(verts(built["hand_controls"]))[:, 2].max()
    assert 1.262 - 0.0075 < bars < 1.262 and 1.262 + 0.008 < ctrl < 1.262 + 0.014


def test_throttle_hood_top_is_the_rear_photo_s():
    top = np.asarray(df.throttle_housing().V, float)[:, 2].max()
    assert abs(top - 1.2488) < 0.002          # REAR photo: hood's top edge cast on its own x plane, cols 2290..2330


def test_fork_tubes_spacing_and_diameters(built):
    gold = verts(built["fork"], "fork_gold")
    t = (gold - parts.TUBE0) @ parts.UP
    for side in (1, -1):
        g = gold[(side * gold[:, 1] > 0) & (t > 0.395) & (t < 0.605)]                       # lower clamp to the guards
        assert abs(g[:, 1].mean() - side * parts.FORK_HALF) < 0.0005                      # centres 198 mm apart
        across = np.ptp(g[:, 1])
        assert 0.048 <= across <= 0.053                                                   # photos: 48 to 53 mm
    inner = verts(built["fork"], "chrome")
    assert abs(np.ptp(inner[inner[:, 1] > 0][:, 1]) - 0.049) < 0.0005                     # SPEC: 49 mm inner tubes


def test_rake_is_the_photo_s_fork_angle_and_near_the_spec(built):
    gold = verts(built["fork"], "fork_gold")
    g = ground(gold[gold[:, 1] > 0])
    c = g - g.mean(axis=0)
    axis = np.linalg.svd(c, full_matrices=False)[2][0]
    axis *= np.sign(axis[2])
    rake = math.degrees(math.atan2(-axis[0], axis[2]))
    assert abs(rake - math.degrees(parts.RAKE + parts.GROUND_PITCH)) < 0.05
    assert abs(rake - 27.55) < 0.3                                                        # SPEC 27 deg 33 min (GS, LA, MX)


def test_axle_is_on_the_front_axle_and_clamps_hold_both_tubes(built):
    steel = verts(built["fork"], "steel")
    r = np.hypot(steel[:, 0] - parts.FA[0], steel[:, 2] - parts.FA[2])
    axle = steel[(r < 0.0105) & (np.abs(steel[:, 1]) < 0.1265)]                           # 20 mm axle on parts.FA
    assert len(axle) >= 40 and axle[:, 1].min() < -0.12 and axle[:, 1].max() > 0.12
    cl = verts(built["clamps"])
    assert cl[:, 1].max() > parts.FORK_HALF + 0.030 and cl[:, 1].min() < -parts.FORK_HALF - 0.030


def test_steering_parts_and_budget(built):
    assert set(df.REPLACES) == {"fork", "clamps", "bars", "cables", "disc_guard"}
    assert abs(np.ptp(verts(built["bars"])[:, 1]) - 0.827) < 0.008                       # test_bike.py's width check
    assert "cables" not in df.FRONT_END and set(df.FRONT_END) <= set(df.PARTS)
    assert sum(len(m.V) for m in built.values()) < 220000                                 # brief's budget
    for m in built.values():
        assert np.isfinite(np.asarray(m.V, float)).all()
        assert max(max(f) for f in m.F) < len(m.V)


def test_grips_close_onto_the_bar_and_the_throttle_tube(built):
    for side, lo, hi in ((1, 0.0111, 0.0116), (-1, df.G_THROTTLE_R - 0.0001, df.G_THROTTLE_R + 0.0001)):
        a, r, th = _grip_frame(built, side)
        assert lo < r[a > 0.12].min() < hi                                                # bar 22.2 mm / tube


def test_only_the_stem_is_inside_the_head_tube(built):
    v = verts(built["clamps"]) - parts.STEER0
    s = v @ parts.UP
    rad = np.linalg.norm(v - np.outer(s, parts.UP), axis=1)
    near = rad < 0.030                                                                    # the head tube's radius
    assert not (near & (s > df.FACE_LO + 0.0005) & (s < df.FACE_UP - 0.0005) & (rad > df.STEM_R + 1e-6)).any()
    stem = near & (rad > df.STEM_R - 0.0012) & (rad < df.STEM_R + 1e-6)
    assert s[stem].min() < df.FACE_LO and s[stem].max() > df.FACE_UP


def test_fender_bosses_stop_short_of_the_fender(built):
    v = verts(built["clamps"])
    for side in (1, -1):
        top = v[np.hypot(v[:, 0] - 1.236, v[:, 1] - side * 0.024) < 0.0080]
        skin = min(df._fender_skin(q[0], q[1]) for q in top[top[:, 2] > top[:, 2].max() - 0.0005])
        gap = skin - df.FENDER_T - top[:, 2].max()
        assert 0.0002 < gap < 0.004, gap


def test_top_clamp_bosses_clear_the_number_plate():
    import plastics
    v = np.asarray(plastics.number_plate().V, float)
    rel = v - parts.TUBE0
    t, f = rel @ parts.UP, -(rel @ parts.BACK)
    for side in (1, -1):
        rad = np.hypot(f, v[:, 1] * side - parts.FORK_HALF)
        assert rad[(t > df.T_UP[0]) & (t < df.T_UP[1])].min() > df.R_BOSS_UP + 0.0003


def test_cables_end_on_the_engine_s_anchors():
    import detail_engine as de
    q = df.clutch_path()
    arm = getattr(de, "CLUTCH_ARM_END", None)
    assert np.linalg.norm(q[-1] - (df.CLUTCH_JOIN if arm is None else np.asarray(arm, float))) < 0.004
    mid = de.TB0 + 0.062 * de.TB_DIR
    for path in df.throttle_paths():
        r = np.hypot(path[-1][0] - mid[0], path[-1][2] - mid[2])
        if not hasattr(de, "THROTTLE_DRUM"):
            assert 0.019 + 0.0035 < r < 0.019 + 0.0045                                    # lying on the drum, clear
            assert -(de.TB_BORE / 2 + 0.008 + 0.016) < path[-1][1] < -(de.TB_BORE / 2 + 0.008)


def test_throttle_cables_never_run_through_each_other():
    a, b = df.throttle_paths()
    assert np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2).min() > 0.0072          # two 7 mm cables


def test_bar_pad_closes_onto_the_bar(built):
    pad = verts(built["bars"], "barpad")
    path = df.bar_path()
    for side in (1, -1):
        end = pad[pad[:, 1] * side > df.PAD_Y[1] - 0.0005]
        c = path[np.argmin(np.abs(path[:, 1] - df.PAD_Y[1]))]
        r = np.hypot(end[:, 0] - c[0], end[:, 2] - c[2])
        assert 0.0130 < r.min() < 0.0150                                                  # bore 0.4 mm off the bar


def test_bar_pad_hides_the_holders_and_their_bolts(built):
    import geom
    sec = df.pad_section()
    assert abs(np.ptp(sec[:, 0]) - 0.086) < 0.002 and abs(np.ptp(sec[:, 1]) - 0.056) < 0.002
    for mat in ("bolt", "alu_cast"):
        v = verts(built["bars"], mat)
        rel = v - parts.TUBE0
        f, t = -(rel @ parts.BACK), rel @ parts.UP
        hold = (np.abs(np.abs(v[:, 1]) - df.HOLDER_Y) < 0.016) & (np.abs(f - df.F_BAR) < 0.04) & (t > df.PAD_T[0] + 0.002)
        assert hold.sum() > 100
        assert geom.inside(sec, np.stack([f[hold], t[hold]], axis=1)).all()               # nothing pokes through
        assert np.abs(v[hold, 1]).max() < df.PAD_Y[0]


def test_fatbar_diameters_taper_and_knurl(built):
    bar = verts(built["bars"], "bar_black")
    path = df.bar_path()
    for y, d in ((0.12, 0.0286), (0.25, 0.0222), (0.35, 0.0222)):                     # SPEC 28.6 / 22.2 mm
        c = path[np.argmin(np.abs(path[:, 1] - y))]
        ring = bar[np.abs(bar[:, 1] - c[1]) < 0.0015]
        r = np.linalg.norm((ring - c)[:, [0, 2]], axis=1)
        assert abs(2 * np.median(r[r < 0.016]) - d) < 0.0012, (y, 2 * np.median(r))
    kn = verts(built["bars"], "bar_knurl")
    assert len(kn) > 500
    assert np.abs(kn[:, 1]).min() > df.BAR_KNURL[0] - 5e-4 and np.abs(kn[:, 1]).max() < df.BAR_KNURL[1] + 5e-4
    m = built["bars"]
    knurl = [fi for fi, mm in enumerate(m.M) if mm == "bar_knurl"]
    assert all(fi in m.uv for fi in knurl)                                                # the normal map needs UVs


def test_bar_end_runs_along_the_grip_axis():
    path = df.bar_path()
    for side in (1, -1):
        sd = df._Side(side)
        q = path[path[:, 1] > 0.30] * [1, side, 1] - sd.T
        off = q - np.outer(q @ sd.d, sd.d)
        assert np.linalg.norm(off, axis=1).max() < 0.0006                                # on the axis, upsweep included
    assert abs(math.degrees(df.UPSWEEP) - 1.85) < 0.01


def test_left_switch_buttons_sit_on_the_rear_and_top_photos():
    """Round 2, component 1: the three buttons' tops land on the photo's button centres (REAR within 2.5 px, TOP
    within 3 px; the picks that triangulated them) and keep the measured sizes and the face's 12.5 deg lean."""
    s = df._Side(1)
    P, nf, up, right = df._face_frame(s, df.SW_TILT, df.SW_FACE_F)
    picks = {"m": ((1657.0, 225.3), (1812, 1436)), "tc": ((1657.3, 246.5), (1816.5, 1435)),
             "stop": ((1681.5, 238.2), (1808, 1414))}
    for key, (pr, pt) in picks.items():
        c, rb, rw = df.SW_BTN[key]
        top = P(*c) + 0.0012 * nf
        assert np.linalg.norm(cams.CAMS["rear"].project([top])[0] - pr) < 2.5, key
        assert np.linalg.norm(cams.CAMS["top"].project([top])[0] - pt) < 3.0, key
        assert rw - rb > 0.003                                                          # a dished well round it
    assert abs(df.SW_BTN["stop"][1] / df.SW_BTN["m"][1] - 1.31) < 0.03                # DR06 red / blue
    assert abs(2 * df.SW_BTN["m"][1] - 0.0095) < 0.0005                               # REAR 9.1..9.6 mm
    assert abs(math.degrees(df.SW_TILT) - 12.5) < 0.2


def test_start_switch_frame_sits_on_the_rear_and_top_photos():
    c = df._Side(-1).p(*df.SS_C)
    assert np.linalg.norm(cams.CAMS["rear"].project([c])[0] - (2302.5, 256.5)) < 4.0
    assert np.linalg.norm(cams.CAMS["top"].project([c])[0] - (1805, 845)) < 5.0
    assert df.SS_MOUNT[1] < df.MC_CLAMP[0]                                             # clear of the MC clamp


def test_switch_buttons_carry_their_symbols(built):
    import os
    from PIL import Image
    stock = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "textures", "stock")
    for name in ("sw_m", "sw_stop", "sw_tc", "sw_start"):
        n = np.asarray(Image.open(os.path.join(stock, name + "_n.png")), float)
        assert n.shape[:2] == (512, 512) and (np.abs(n[..., 0] - 128) > 40).mean() > 0.005   # engraved, not flat
        assert df.MATERIALS[name]["normal"] == "stock/%s_n.png" % name
        m = built["hand_controls"]
        faces = [i for i, mm in enumerate(m.M) if mm == name]
        assert faces and all(i in m.uv for i in faces)                                   # every face has UVs


def test_master_cylinder_window_and_lettering():
    """Round 2, component 2: the sight window sits on REAR's window (within 3 px; built 1.5 mm higher so its ring
    clears the bar), its ring stays off the bar, and NISSIN / LWR read left to right from where a person looks."""
    s, lx, ly = df._mc_frame()
    ca, cf, L, W, top = df.MC_CAP
    zb = s.p(ca)[2]
    c = s.p(ca, cf)
    c = np.array([c[0], c[1], zb])
    win = c - (W / 2 * 0.985) * lx + df.MC_WIN[0] * ly + df.MC_WIN[1] * Z_
    assert np.linalg.norm(cams.CAMS["rear"].project([win])[0] - (2256.5, 227.0)) < 3.0
    for t in np.linspace(0, 2 * math.pi, 72, endpoint=False):                          # ring clear of the bar
        p = win + df.MC_WIN[2] * (math.cos(t) * ly + math.sin(t) * Z_)
        a = np.linspace(0.15, 0.28, 400)
        axis = np.array([s.p(x) for x in a])
        assert np.linalg.norm(axis - p, axis=1).min() > df.BAR_R[1] + 0.0003
    m = df.master_cylinder()
    for mat, want in (("mc_nissin", ly), ("mc_lwr", -ly)):          # +u of the relief runs to the reader's right
        i = next(k for k, mm in enumerate(m.M) if mm == mat)
        f, uv = m.F[i], np.array(m.uv[i])
        P = np.asarray(m.V, float)[list(f)]
        du = np.linalg.lstsq(np.c_[uv - uv[0], np.ones(len(uv))][:, :2][1:], (P - P[0])[1:], rcond=None)[0][0]
        assert du @ want > 0.8 * np.linalg.norm(du), mat


Z_ = np.array([0.0, 0.0, 1.0])


def test_clutch_lever_dog_leg():
    """Round 2, component 3: the blade jogs back towards the grip out of the boot (TOP: 19 mm off the boot-to-ball
    line a third of the way along) and runs on to the ball; the ball on FRONT's cast (a 55, f 92, u -20)."""
    line = np.array(df.clutch_lever_line())[:, :2]
    B, E = line[0], line[-1]
    t = (E - B) / np.linalg.norm(E - B)
    off = (line - B) @ np.array([t[1], -t[0]])
    i = int(np.argmin(off))
    assert -0.0215 < off[i] < -0.0185 and 0.25 < np.linalg.norm(line[i] - B) / np.linalg.norm(E - B) < 0.42
    assert abs(df.CP_BALL[0] - 0.055) < 0.002 and abs(df.CP_BALL[1] - 0.092) < 0.002
