"""Tests of Damien's gloves (gloves.py): size from his hand and Leatt's chart, the glove's fit and offsets, the cuff
and strap from Leatt's photos, skinning, hide_body, UVs, the gear npz, and the glove over its own skin with the
fist closed and the wrist bent (numpy skinning, as Blender's armature does it). Needs tools/fetch_makehuman.sh.

python3 -m pytest -q test_gloves.py
"""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body as BD     # noqa: E402
import gloves as GL   # noqa: E402


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    d = tmp_path_factory.mktemp("gloves")
    bp = str(d / "body.npz")
    np.savez_compressed(bp, **BD.build())
    out, G, B = GL.build(bp, str(d / "gloves.npz"), textures=False)
    return dict(path=str(d / "gloves.npz"), G=G, B=B, npz=np.load(str(d / "gloves.npz")))


def test_size_from_his_hand_and_leatts_chart(built):
    """His hand on body.npz: knuckle circumference 21.9 cm (Leatt's chart: M 21-22, L 22-23) and hand length
    21.4 cm (wrist crease to the middle fingertip, flat). Size L by the chart's primary measure."""
    B = built["B"]
    m = GL.hand_measures(B, "L")
    assert 21.5 < m["circumference_cm"] < 22.3
    assert 21.0 < m["length_cm"] < 21.8
    lo, hi, length = GL.CHART[GL.SIZE]
    assert GL.SIZE == "L" and lo - 0.5 <= m["circumference_cm"] <= hi
    # the glove itself over his knuckles: his tape plus the fabric (2 x 1.0 to 2.5 mm round 22 cm: +0.6 to 1.6 cm)
    g = GL.hand_measures(B, "L", glove=built["G"])
    assert 0.5 < g["circumference_cm"] - m["circumference_cm"] < 1.7


def test_glove_stays_over_the_skin_at_rest(built):
    """1.0 mm (fabric) over the hand, at most 2.5 mm where it spans skin grooves, 2 mm more at the tips, 4 mm at
    the cuff; never under the skin."""
    G = built["G"]
    N = GL.vertex_normals(G["P0"], G["F"])
    h = np.einsum("ij,ij->i", G["P"] - G["P0"], N)
    assert h.min() > GL.OFF_HAND - 1e-4
    hand = G["L"][:, 1] > GL.CREASE_Y + 0.01
    assert np.percentile(h[hand], 50) < 0.0016 and h[hand].max() < 0.0062


def test_cuff_and_strap_from_leatts_photos(built):
    """Cuff band 32 mm from the wrist crease (top at s = -27 mm), strap 24 mm wide and 1.6 mm thick, white pull
    28 x 7.5 mm, at the thumb-side edge of the wrist."""
    G, B = built["G"], built["B"]
    o, R, fa = GL.hand_frame(B, "L")
    s_top = (G["P"][G["top"]] - o) @ fa
    assert abs(s_top.mean() - GL.CUFF_TOP) < 0.0015 and np.ptp(s_top) < 0.004
    assert abs(GL.CREASE_Y - GL.CUFF_TOP - 0.032) < 1e-9
    st = G["straps"]["strap"]["V"]
    ss = (st - o) @ fa
    assert abs(np.ptp(ss) - GL.STRAP_W) < 0.002
    tab = G["straps"]["tab"]["V"]
    c = tab.mean(0) - o
    assert (c @ R[0]) > 0.02                                   # thumb side
    span = np.ptp((tab - o) @ fa)
    assert abs(span - GL.TAB[1]) < 0.0015


def test_skin_weights(built):
    z = built["npz"]
    names = [str(n) for n in z["names"]]
    nb = len(built["B"]["names"])
    for p in names:
        nv = len(z[p + "__V"])
        wv, wb, ww = z[p + "__wv"], z[p + "__wb"], z[p + "__ww"]
        tot = np.bincount(wv, weights=ww, minlength=nv)
        assert np.allclose(tot, 1.0, atol=1e-4), p                # every vertex skinned, normalised
        assert wb.max() < nb
        bn = {built["B"]["names"][b] for b in np.unique(wb)}
        side = p[-1]
        assert all(b.endswith("." + side) for b in bn), (p, bn)   # the right glove rides the right hand


def test_hide_body_is_under_the_glove(built):
    """The skin it hides is the hand distal of the wrist ring (the ring stays: the skin ends 8 mm or more inside the
    cuff's top edge); both hands, mirror images."""
    B, z = built["B"], built["npz"]
    hide = z["hide_body"]
    V = B["V"]
    o, R, fa = GL.hand_frame(B, "L")
    left = hide[V[hide, 0] > 0]
    s = (V[left] - o) @ fa
    assert s.min() > GL.CUFF_TOP + 0.008
    m = GL.mirror_index(V)
    assert set(m[left].tolist()) == set(hide[V[hide, 0] < 0].tolist())
    assert 1400 < len(left) < 1700


def test_gear_file(built):
    z = built["npz"]
    names = [str(n) for n in z["names"]]
    assert set(names) == {f"glove{p}_{s}" for p in ("", "_strap", "_tab") for s in "LR"}
    mats = json.loads(str(z["materials"]))
    for m in [str(x) for x in z["mats"]]:
        assert m in mats
    for p in names:
        V, F, FS, M = z[p + "__V"], z[p + "__F"], z[p + "__FS"], z[p + "__M"]
        assert FS.sum() == len(F) and F.max() < len(V) and len(M) == len(FS)
        if p + "__UV" in z:
            assert len(z[p + "__UV"]) == FS.sum()
    # left and right are mirror images
    L, R = z["glove_L__V"], z["glove_R__V"]
    assert np.allclose(L * [-1, 1, 1], R, atol=1e-6)
    meta = json.loads(str(z["meta"]))
    assert meta["size"] == "L"


def test_uv_islands_do_not_overlap(built):
    """Each texel belongs to one face: no island folds over itself (every face's UV winding the same as its
    island's), no two islands' boxes overlap, all inside [0, 1]; texel density within a factor 2.6 from the 1st to
    the 99th percentile face (cylinder unwraps at the finger roots and tips; patterns are painted from 3D positions,
    so density changes only the local resolution, not their size)."""
    G = built["G"]
    UV, isl = G["UV"], G["isl"]
    a = UV[:, 2] - UV[:, 0]
    b = UV[:, 3] - UV[:, 1]
    area = 0.5 * (a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])
    boxes = []
    for i in np.unique(isl):
        m = isl == i
        sgn = np.sign(np.sum(area[m]))
        assert (np.sign(area[m]) == sgn).mean() > 0.995, i
        Q = UV[m].reshape(-1, 2)
        boxes.append((Q.min(0), Q.max(0)))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (l1, h1), (l2, h2) = boxes[i], boxes[j]
            assert (h1 <= l2 + 1e-6).any() or (h2 <= l1 + 1e-6).any()
    assert UV.min() >= 0 and UV.max() <= 1
    P = G["P"][G["F"]]
    a3 = 0.5 * np.linalg.norm(np.cross(P[:, 2] - P[:, 0], P[:, 3] - P[:, 1]), axis=1)
    dens = np.sqrt(np.abs(area) / a3)
    assert np.percentile(dens, 99) / np.percentile(dens, 1) < 2.6


def test_construction_panels(built):
    """Painted at 1024 px: the NanoGrip palm about 40 % of the hand's glove (palm, finger fronts, thumb pad), the
    stretch-mesh fourchettes and tip caps present on every finger, the welded overlays 4000 to 7000 mm2 (four
    knuckle overlays 15.5 mm wide seen from the back, about 19 mm round the finger's curve, 30 mm long: about
    600 mm2 each; two on the little-finger edge, about 1000; one along the thumb, about 1300; the parts over the
    knuckles themselves), stitches on the seams; relief within -0.5..+0.5 mm."""
    G = built["G"]
    TG = GL.texel_geometry(G, G["UV"], 1024)
    col, h, m = GL.paint(G, TG, "L")
    texel_mm = 1000.0 / (G["texel_per_m"] * 1024 / GL.TEX)
    a = texel_mm ** 2
    dens = np.sqrt(np.abs(np.linalg.det(np.stack([G["UV"][:, 1] - G["UV"][:, 0], G["UV"][:, 3] - G["UV"][:, 0]], 1))))
    hand = ~m["cuff"]
    frac = m["palm"].sum() / hand.sum()
    assert 0.33 < frac < 0.50, frac
    assert m["side"].sum() * a > 1500 and m["tip"].sum() * a > 400
    ov = m["overlay"].sum() * a
    assert 4000 < ov < 7000, ov
    st = (np.abs(col - GL.STITCH).sum(1) < 1e-6).sum()
    assert st * a > 150
    assert -0.5 < h.min() and h.max() < 0.5


def test_glove_over_its_skin_with_the_fist_closed(built):
    """Fingers curled as build_rider.aim_pose closes them on the grip (0.95, 1.05, 0.75 rad; thumb 0.35) and the
    wrist straight or bent 30 deg either way: skin and glove posed by linear blend skinning with their own weights.
    The cuff keeps 3 mm over the forearm (the skin there is not hidden: none of it may come through); the outside of
    the fist (the back half of the hand and fingers, what a viewer sees) stays over the skin; only on the palm side,
    inside the finger joints' flexion creases, the fabric folds in (by less than 4 mm, as real fabric bunches there,
    hidden in the fist)."""
    B, G = built["B"], built["G"]
    o, R, fa = GL.hand_frame(B, "L")
    N = GL.vertex_normals(G["P0"], G["F"]) @ R.T
    pv = G["palm_dir"] / np.linalg.norm(G["palm_dir"], axis=1, keepdims=True)
    palmar = np.einsum("ij,ij->i", N, pv) > 0.0
    cuff = G["s"] < GL.CREASE_Y - 0.012
    for wrist in (-30.0, 0.0, 30.0):
        Vp, Pg = GL.pose_hand(B, G, "L", wrist_deg=wrist)
        h = GL.heights(G, Vp, Pg)
        assert h[cuff].min() > 0.003, wrist
        assert h[~palmar].min() > 0.0002, wrist
        assert h[palmar].min() > -0.004, wrist
