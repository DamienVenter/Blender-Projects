"""Fast checks of the front-end detail module against the spec table (research/crf250r-2026.md). No Blender."""
import math

import numpy as np
import pytest

import cams
import detail_front as df
import parts


def ground(v):
    """Axle-line frame to the ground frame (nose up about the rear axle, both tyres on the ground)."""
    v = np.asarray(v, float) - parts.RA
    c, s = math.cos(parts.GROUND_PITCH), math.sin(parts.GROUND_PITCH)
    return np.stack([v[:, 0] * c - v[:, 2] * s, v[:, 1], parts.R_REAR + v[:, 0] * s + v[:, 2] * c], axis=1)


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
        g = gold[(side * gold[:, 1] > 0) & (t > 0.41) & (t < 0.605)]                       # lower clamp to the guards
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
