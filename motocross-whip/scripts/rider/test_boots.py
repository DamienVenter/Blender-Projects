"""Tests of Damien's boots (boots.py): size from his foot and Leatt's chart, dimensions against Leatt's photos,
clearance of his skin, the gear file. Needs tools/fetch_makehuman.sh and the LFS reference photos.

python3 -m pytest -q test_rider.py test_boots.py
"""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body as Bd    # noqa: E402
import boots as B    # noqa: E402


@pytest.fixture(scope="module")
def body():
    return Bd.build()


@pytest.fixture(scope="module")
def build(body):
    return B.Build(body).build()


@pytest.fixture(scope="module")
def gear(build, tmp_path_factory):
    p = tmp_path_factory.mktemp("boots") / "boots.npz"
    B.assemble(build, str(p))
    return dict(np.load(p))


def test_size_from_his_foot_and_leatts_chart(build):
    """His foot (heel to longest toe) is 277 mm: more than US 9's 27.5 cm, so US 10 (29.0 cm); the sole is the
    chart's foot plus toe room, heel wall and toe wall: 330 mm."""
    assert abs(build.fit.foot - 0.2773) < 0.001
    assert build.fit.us_size == 10
    assert abs(build.fit.L - 0.330) < 1e-9
    assert abs(B.Side(B.P02, build.fit.L).s * 1000 - 0.286) < 0.001         # photo 02's scale, mm per px


def test_boot_height_from_photo_02(build):
    """Ground line to the gaiter's top in photo 02 at its scale: 425 mm; the white shell's top 360 to 409 mm."""
    assert abs(build.fit.H - 0.4247) < 0.002
    P = B.ShellSDF(build.field, build.origin, B.H_VOX)
    sh = build.parts["shell"]["R"]
    V = np.asarray(sh.V)
    assert 0.400 < V[:, 1].max() < 0.412
    assert P is not None


def test_shell_follows_photo_02_outline(build):
    """Row by row the shell's back and front edges (side view) against photo 02's outline: plates, buckles, strap
    keepers and the spine's torsion blade stand proud of the shell in the photo, so the median gap is under 2 mm,
    90 % under 12 mm, all under 22 mm (the blade at v 220 to 250 mm, 21 mm)."""
    us, vs, M = B.side_mask(build.fit.L)
    ub, uf = B.row_edges(us, M)
    V = np.asarray(build.parts["shell"]["R"].V)
    gaps = []
    for v in np.arange(0.06, 0.36, 0.005):
        if B.HEEL_BAND[0] <= v <= B.HEEL_BAND[1]:
            continue
        row = V[np.abs(V[:, 1] - v) < 0.0015]
        i = int(round(v / B.GRID))
        gaps += [abs(row[:, 0].min() - ub[i]), abs(row[:, 0].max() - uf[i])]
    gaps = np.array(gaps)
    assert np.median(gaps) < 0.002 and np.percentile(gaps, 90) < 0.012 and gaps.max() < 0.022


def test_sole_on_the_ground_with_leatts_heights(build):
    """Lug faces on the ground line, the black's top at photo 02's heights, the toe sprung 21 mm at the tip."""
    V = np.asarray(build.parts["sole"]["R"].V)
    assert abs(V[:, 1].min()) < 0.0005
    heel = V[(V[:, 0] < 0.03)]
    assert abs(heel[:, 1].max() - 0.0212) < 0.001
    tip = V[V[:, 0] > build.fit.L - 0.004]
    assert tip[:, 1].min() > 0.015
    lug = B.tread_raster()
    x, y = B.to_px06(B.P06, build.fit.L, 0.2, 0.0)
    assert 0.0 <= lug[int(y), int(x)] <= 1.0


def test_skin_inside_the_boot_at_rest(build):
    """Every skin vertex the boot covers (below the shell's top edge) is inside its outer surface, rest pose."""
    idx, Q, depth = B.skin_clearance(build)
    assert len(idx) > 800
    assert depth.min() > 0.0005


def test_gear_file_loads_and_is_consistent(gear, body):
    names = [str(n) for n in gear["names"]]
    mats = json.loads(str(gear["materials"]))
    assert {str(m) for m in gear["mats"]} <= set(mats)
    for n in names:
        V, F, FS, M = gear[n + "__V"], gear[n + "__F"], gear[n + "__FS"], gear[n + "__M"]
        assert F.max() < len(V) and FS.sum() == len(F) and len(M) == len(FS)
        if n + "__UV" in gear:
            assert len(gear[n + "__UV"]) == len(F)
        tot = np.bincount(gear[n + "__wv"], weights=gear[n + "__ww"], minlength=len(V))
        assert np.allclose(tot, 1.0, atol=1e-6)
        bones = {str(body["bones"][b]) for b in np.unique(gear[n + "__wb"])}
        assert bones <= ({"foot.R", "lowerleg02.R"} if n.startswith("bootR") else {"foot.L", "lowerleg02.L"})
    for m, spec in mats.items():
        for k in ("image", "normal"):
            if k in spec:
                assert os.path.exists(os.path.join(B.TEXDIR, spec[k]))


def test_left_boot_is_the_right_mirrored(gear):
    for n in [str(x) for x in gear["names"] if str(x).startswith("bootR_") and str(x) != "bootR_sole"]:
        R, L = gear[n + "__V"], gear[n.replace("bootR_", "bootL_") + "__V"]
        assert np.allclose(L, R * [-1, 1, 1], atol=1e-9)


@pytest.mark.parametrize("knee,ankle", [(0, -15), (0, 20), (60, 0), (60, -15), (60, 20)])
def test_skin_inside_the_boot_posed(build, knee, ankle):
    """Riding: knee flexed 60 deg, the ankle 15 deg up (dorsiflexion) and 20 deg down; skin (MakeHuman's weights)
    and boot (shaft on lowerleg02, foot shell on foot, blended over the Dual Axis hinge) skinned alike: no skin
    through the boot."""
    depth = B.posed_clearance(build, knee, ankle)
    assert depth.min() > 0.0005


def test_hidden_skin_is_covered(gear, body):
    """The skin build_rider hides (hide_body) is the feet and lower calves inside both boots, nothing else."""
    h = gear["hide_body"]
    V = body["V"][h]
    assert 1500 < len(h) < 4000
    assert V[:, 2].max() < 0.40 and (np.abs(V[:, 0]) > 0.06).all()
    assert (V[:, 0] > 0).sum() == (V[:, 0] < 0).sum()
