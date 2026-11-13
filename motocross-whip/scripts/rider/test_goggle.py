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
    centre plane: top lip front at y -149 mm, top at z +41 to +43.5 mm, the beak's front at y -156 to -157 mm, its
    bottom (the tabs either side of the nose notch) at z -64.6 to -66 mm (helmet frame). The built frame within
    4 to 5 mm of each."""
    V, info = frame_in_helmet_frame()
    c = V[np.abs(V[:, 0]) < 0.004]
    top = c[c[:, 2] > 0.02]
    bot = V[(np.abs(V[:, 0]) < 0.03) & (V[:, 2] < -0.04)]
    assert abs(top[:, 1].min() - (-0.149)) < 0.004
    assert abs(top[:, 2].max() - 0.0425) < 0.004
    assert abs(bot[:, 1].min() - (-0.1565)) < 0.005
    assert abs(bot[:, 2].min() - (-0.065)) < 0.004


def test_velocity55_shape_from_leatts_iso():
    """Leatt's ISO (camera fitted to the goggle's silhouette, then pixels back-projected): a thin front rim round a
    lens that fills the front (lens top +31 to +36 mm under a frame top of +43 to +44 mm), crisp flat faces behind
    it; fins rising about 6 mm at the top band's ends; the beak's tabs about 20 mm either side of the centre, 20 to
    25 mm below the pointed notch over the nose (notch -43 mm, tabs -67 mm); posts about 17 mm in from the lens's
    visible end; the outriggers start behind the frame's tall side faces."""
    gp = G.GP
    rings, info = G.frame_rings()
    Co, Cu = info["Co"], info["Cu"]
    rim = np.linalg.norm(rings[G.RING_RIM] - rings[2], axis=1)
    assert 0.0018 < rim.min() and rim.max() < 0.0035                       # narrow flat front rim
    assert gp["lip"] > 0.001                                                # stands proud of the lens
    o, u = dict(enumerate(gp["open"])), dict(enumerate(gp["out"]))
    assert all(u[k][1] - o[k][1] < 0.011 for k in (0, 1, 2))                # the top band over a big lens
    assert 0.029 <= o[0][1] <= 0.036 and abs(u[0][1] - 0.0425) < 0.002
    assert u[4][0] - o[4][0] < 0.008                                        # thin rim at the ends too
    # fins
    f = G.build_fins()
    zf = f.V[:, 2].max()
    s_tip = G.FIN_S[1]
    z_band = np.interp(s_tip, [p[0] for p in gp["out"][1:4]], [p[1] for p in gp["out"][1:4]])
    assert 0.004 < zf - z_band < 0.008
    # beak: pointed notch, tabs either side
    assert 0.018 < u[8][0] < 0.025 and 0.018 < u[10][1] - u[8][1] < 0.026
    assert abs(u[10][1] - (-0.043)) < 0.003 and gp["fillet_out"][10] <= 0.002 and gp["fillet_out"][8] <= 0.002
    ng = G.build_nose_guard()
    assert ng.V[:, 2].min() > u[8][1]                                       # the guard stays inside the tabs
    # posts
    assert 0.014 < G.POST_S_IN < 0.020
    # outriggers behind the side faces
    L = info["L"]
    for sg, (box, end, n) in G.outrigger_frames().items():
        front = box[[0, 1]].mean(0)
        P, N = L.point(sg * u[4][0], front[2], 0.0)
        assert (P - front) @ N > 0.012                                      # more than 12 mm behind the lens front


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
    """Red-pink frame: his 08 and 09 measure hue 346 deg (median 165/20/54); the base is set bluer (337 deg) so the
    render (AgX shifts reds towards orange) measures 347 deg in his 09 view. Black outriggers with their LEATT, fins,
    the lower band's LEATT, bare tear-off posts (no tear-offs, decision 7), nose guard, foam, strap."""
    import colorsys
    r, g, b = G.MATERIALS["goggle_frame"]["rgb"]
    h = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 360
    assert 330 < h < 345 and r > 120 and g < 10
    for name in ("goggle_frame", "goggle_fins", "goggle_logo", "goggle_lens", "goggle_posts", "goggle_outriggers",
                 "goggle_noseguard", "goggle_foam", "goggle_strap"):
        assert name in built["parts"]
    assert "goggle_vent" in built["parts"]["goggle_frame"].M


def test_leatt_wordmark_is_the_official_slanted_one():
    """Strap, outriggers and the lower band carry Leatt's official slanted LEATT (reference file from Leatt's own
    site), at its own aspect (about 4.0 long per height): the strap's two white logos, the lower band's logo at his
    left cheek (MY27 front-iso and left side views), 4 mm high."""
    from PIL import Image
    a = G.wordmark_aspect()
    assert 3.8 < a < 4.2
    im = np.array(Image.open(os.path.join(H.TEXDIR, "goggle_strap.png")).convert("RGB")).astype(int)
    white = im.min(-1) > 235
    w = im.shape[1]
    for half in (white[:, :w // 2], white[:, w // 2:]):
        ys, xs = np.nonzero(half)
        assert abs(np.ptp(xs) / np.ptp(ys) - a) < 0.3
    lg = G.build_frame_logo()
    V = G.g2h(lg.V)
    assert (V[:, 0] > 0.03).all()                                           # his left cheek
    ext = np.ptp(V, 0)
    assert G.LOGO_H - 0.0015 < ext[2] < G.LOGO_H + 0.002 and abs(ext[0] / G.LOGO_H - a) < 0.8


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
