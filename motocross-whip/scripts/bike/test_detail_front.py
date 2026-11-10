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
    grip = verts(built["bars"], "grip")
    assert df.TIP[0] == cams.BAR_END[0] and df.TIP[2] == cams.BAR_END[2]                  # no FRONT_TIP override
    for side in (1, -1):
        d = np.linalg.norm(grip - df.TIP * [1, side, 1], axis=1)
        assert (np.abs(d - df.R_GRIP) < 0.0005).sum() >= 20                               # the end face's rim
        assert abs((side * grip[:, 1]).max() - cams.BAR_END[1]) < 0.0005                  # its outermost point


def test_overall_height_is_1262_mm_at_the_bars(built):
    assert abs(ground(verts(built["bars"]))[:, 2].max() - 1.262) < 0.008                 # SPEC overall height


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
    assert "cables" not in df.FRONT_END and set(df.FRONT_END) <= set(df.PARTS)
    assert sum(len(m.V) for m in built.values()) < 70000
    for m in built.values():
        assert np.isfinite(np.asarray(m.V, float)).all()
        assert max(max(f) for f in m.F) < len(m.V)


def test_grips_close_onto_the_bar(built):
    grip = verts(built["bars"], "grip")
    for side in (1, -1):
        sd = df._Side(side)
        g = grip[grip[:, 1] * side > 0] - sd.T
        r = np.linalg.norm(g - np.outer(g @ sd.d, sd.d), axis=1)
        assert 0.0111 < r[r > 0.001].min() < 0.0116                                       # 22.2 mm bar, 0.3 mm short


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
