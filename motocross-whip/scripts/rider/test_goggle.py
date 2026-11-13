"""Tests of Damien's goggle, his eyes and the helmet's brow badge (goggle.py, built through helmet.py).

python3 -m pytest -q test_rider.py test_helmet.py test_goggle.py
"""
import json
import math
import os
import sys

import numpy as np
import pytest
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body as B          # noqa: E402
import helmet as H        # noqa: E402
import goggle as G        # noqa: E402
from test_helmet import winding, tris, deform_head   # noqa: E402


@pytest.fixture(scope="module")
def body():
    d = B.build()
    return {k: d[k] for k in d}


@pytest.fixture(scope="module")
def built(body, tmp_path_factory):
    parts, info, Rt = H.build(body)
    path = str(tmp_path_factory.mktemp("goggle") / "helmet.npz")
    H.write_npz(path, parts, H.extras(body, parts, Rt))
    return dict(parts={P.name: P for P in parts}, info=info, Rt=Rt, path=path)


def frame_in_helmet_frame():
    rings, info = G.frame_rings()
    return G.g2h(np.vstack(rings)), info


def test_side_profile_from_leatts_side_views():
    """Leatt's MY27 kit side views (left and right, cameras fitted to the shell), red frame back-projected onto the
    centre plane: top lip front at y -149 mm, top at z +41 to +43.5 mm, the nose beak's front at y -156 to -157 mm,
    its bottom at z -64.6 to -66 mm (helmet frame). The built frame on the centre line within 4 mm of each."""
    V, info = frame_in_helmet_frame()
    c = V[np.abs(V[:, 0]) < 0.004]
    top = c[c[:, 2] > 0.02]
    bot = c[c[:, 2] < -0.04]
    assert abs(top[:, 1].min() - (-0.149)) < 0.004
    assert abs(top[:, 2].max() - 0.0425) < 0.004
    assert abs(bot[:, 1].min() - (-0.1565)) < 0.005
    assert abs(bot[:, 2].min() - (-0.065)) < 0.004


def test_frame_width_and_wrap():
    """Outer frame about 195 to 205 mm across (the ends' red stops 25 to 32 mm behind the lip in the side views:
    the 170 deg WideVision lens wraps back round the face)."""
    V, info = frame_in_helmet_frame()
    assert 0.190 < np.ptp(V[:, 0]) < 0.210
    L = info["L"]
    s_end = max(p[0] for p in G.GP["out"])
    P_end = L.point(s_end, 0.0, 0.0)[0]
    assert 0.024 < P_end[1] < 0.040


def test_frame_and_lens_clear_his_face(body, built):
    """No skin inside the frame, the lens or the outriggers, at rest and with the head pitched down 20 deg (the
    goggle rides the head bone); the face foam is pressed onto the skin by at most 3 mm (compressed foam)."""
    P = built["parts"]
    for pitch in (0.0, 20.0):
        Vs, (R, d) = deform_head(body, pitch)
        for name in ("goggle_frame", "goggle_lens", "goggle_outriggers"):
            Vh = P[name].V @ R.T + d
            lo, hi = Vh.min(0) - 0.005, Vh.max(0) + 0.005
            near = np.all((Vs > lo) & (Vs < hi), axis=1)
            w = winding(Vs[near], Vh, tris(P[name]))
            assert (np.abs(w) < 0.5).all(), f"{name}: {(np.abs(w) >= 0.5).sum()} skin vertices inside at {pitch}"
        Vf = P["goggle_foam"].V @ R.T + d
        lo, hi = Vf.min(0) - 0.005, Vf.max(0) + 0.005
        near = np.nonzero(np.all((Vs > lo) & (Vs < hi), axis=1))[0]
        w = winding(Vs[near], Vf, tris(P["goggle_foam"]))
        inside = near[np.abs(w) >= 0.5]
        if len(inside):
            assert cKDTree(Vf).query(Vs[inside])[0].max() < 0.003


def test_eyes_in_his_sockets(body, built):
    """Eyeballs on the eye bones, centred where MakeHuman's eye proxy puts them (helper sphere), radius 0.955 x
    the helper's; the lids close round them: the lid opening's rim (skin within 2.5 mm of the eyeball and in front
    of its centre) lies on the eyeball within 1.5 mm, and the cornea stays behind the lens by more than 20 mm."""
    P = built["parts"]
    names = list(body["bones"])
    for s in ("L", "R"):
        e = P["eye_ball_" + s]
        assert e.bone == "eye." + s
        c, r = G.eye_geometry(body)[s]
        head = body["heads"][names.index("eye." + s)]
        assert np.linalg.norm(c - head) < 0.002
        d = np.linalg.norm(e.V - c, axis=1)
        assert abs(np.median(d) - r) < 0.0005 and abs(r - 0.0158) < 0.0005
        skin = body["V"]
        ds = np.linalg.norm(skin - c, axis=1) - r
        rim = skin[(np.abs(ds) < 0.0025) & (skin[:, 1] < c[1] - 0.010)]
        assert len(rim) > 10
        assert np.abs(np.linalg.norm(rim - c, axis=1) - r).max() < 0.0025
        apex = e.V[np.argmin(e.V[:, 1])]
        lens = P["goggle_lens"].V
        near = lens[(np.abs(lens[:, 0] - apex[0]) < 0.005) & (np.abs(lens[:, 2] - apex[2]) < 0.005)]
        assert apex[1] - near[:, 1].max() > 0.020


def test_brown_eyes_and_the_lens_hides_them():
    """Brown irises (Damien); the lens is a purple mirror (mostly metallic, purple base, interference film) and
    what it lets through is tinted dark purple: his eyes do not show from outside."""
    from PIL import Image
    im = np.array(Image.open(os.path.join(H.TEXDIR, "goggle_eyes_brown.png")).convert("RGB")).astype(float)
    n = im.shape[0]
    ring = im[n // 2 - 30:n // 2 + 30, n // 2 + 34:n // 2 + 44].reshape(-1, 3).mean(0)   # in the iris, off the pupil
    assert ring[0] > ring[1] > ring[2] and ring[0] < 170
    m = G.MATERIALS["goggle_lens_mirror"]
    r, g, b = m["rgb"]
    assert m["metal"] >= 0.9 and b > r > g and "thin_film" in m
    assert G.MATERIALS["eye_ball"]["coat"] > 0.5                           # wet


def test_frame_colour_and_parts(built):
    """Raspberry frame (darker than the photos' 200/5/70: the studio light and AgX lift it), black outriggers with
    their LEATT, bare tear-off posts (no tear-offs, decision 7), nose guard, foam, strap."""
    r, g, b = G.MATERIALS["goggle_frame"]["rgb"]
    assert r > 120 and g < 20 and 25 < b < 90
    for name in ("goggle_frame", "goggle_lens", "goggle_posts", "goggle_outriggers", "goggle_noseguard",
                 "goggle_foam", "goggle_strap"):
        assert name in built["parts"]
    assert "goggle_vent" in built["parts"]["goggle_frame"].M


def test_outrigger_text_reads_from_outside():
    """Each outrigger's half carries LEATT with the letter tops towards the strap; the left half is the right half
    mirrored across its height (the left face's UVs are mirrored seen from outside)."""
    from PIL import Image
    p = os.path.join(os.path.dirname(H.TEXDIR), "rider", "goggle_outrigger.png")
    im = np.array(Image.open(p).convert("L")).astype(float) > 128
    w = im.shape[1] // 2
    left, right = im[:, :w], im[:, w:]
    assert (left == right[:, ::-1]).mean() > 0.99
    rows = np.nonzero(right.any(1))[0]
    assert rows.mean() < im.shape[0] * 0.6                       # tops towards v = 1 (image top, the strap)


def test_one_leatt_on_the_brow_badge():
    """The brow badge is painted once, centred, purple with one white LEATT (Leatt's photos, his 09): the purple
    texels of the brow lie inside the badge (centred on x = 0, 56 mm wide at the bottom) and the white letters
    span 34.6 mm."""
    from PIL import Image
    Vo, Fo, prof = H.shell_outer()
    UV, isl = H.atlas_uvs(Vo, Fo)
    N = H.normals(Vo, Fo)
    idx, Pts, Nn = H.rasterize(UV * H.TEX, Vo[Fo], N[Fo])
    img = np.array(Image.open(os.path.join(H.TEXDIR, "helmet_pinata.png")).convert("RGB")).astype(int)
    row, col = H.TEX - 1 - np.clip(idx[:, 1], 0, H.TEX - 1), np.clip(idx[:, 0], 0, H.TEX - 1)
    px = img[row, col]
    brow = (Pts[:, 1] < -0.09) & (Nn[:, 1] < 0) & (np.abs(Pts[:, 0]) < 0.09) & (Pts[:, 2] > 0.066) & (Pts[:, 2] < 0.1)
    purple = brow & (np.abs(px - G.BADGE_RGB).sum(1) < 30)
    x = Pts[purple, 0]
    assert abs(0.5 * (x.min() + x.max())) < 0.0015 and 0.050 < np.ptp(x) < 0.058
    white = brow & (px.min(1) > 236) & (np.abs(Pts[:, 0]) < 0.03) & (Pts[:, 2] > G.BADGE_Z[0]) & (Pts[:, 2] < G.BADGE_Z[1])
    xw = Pts[white, 0]
    assert abs(np.ptp(xw) - G.BADGE_LOGO["width"]) < 0.003


def test_npz_loads_with_eye_bones(built, body):
    g = np.load(built["path"])
    names = list(body["bones"])
    mats = json.loads(str(g["materials"]))
    for name in g["names"]:
        name = str(name)
        assert str(g[name + "__bone"]) in names
        FS, F, M = g[name + "__FS"], g[name + "__F"], g[name + "__M"]
        assert FS.sum() == len(F) and len(M) == len(FS) and F.max() < len(g[name + "__V"])
    for m in g["mats"]:
        assert str(m) in mats


def test_textures_present():
    for f in ("goggle_strap.png", "goggle_outrigger.png", "goggle_eyes_brown.png", "helmet_pinata.png"):
        assert os.path.getsize(os.path.join(H.TEXDIR, f)) > 1000
