"""Tests of Damien's helmet and goggle (helmet.py). Needs tools/fetch_makehuman.sh.

python3 -m pytest -q test_rider.py test_helmet.py
"""
import json
import math
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body as B      # noqa: E402
import helmet as H    # noqa: E402


@pytest.fixture(scope="module")
def body():
    d = B.build()
    return {k: d[k] for k in d}


@pytest.fixture(scope="module")
def built(body, tmp_path_factory):
    parts, info, (R, t) = H.build(body)
    path = str(tmp_path_factory.mktemp("helmet") / "helmet.npz")
    H.write_npz(path, parts, H.extras(body, parts, (R, t)))
    return dict(parts={P.name: P for P in parts}, info=info, R=R, t=t, path=path)


def tris(P):
    out = []
    for f in P.F:
        for i in range(1, len(f) - 1):
            out.append([f[0], f[i], f[i + 1]])
    return np.array(out)


def winding(points, V, T, chunk=256):
    """Generalised winding number of each point w.r.t. a closed triangle mesh (1 inside, 0 outside)."""
    A, Bv, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    out = np.zeros(len(points))
    for s in range(0, len(points), chunk):
        p = points[s:s + chunk, None, :]
        a, b, c = A[None] - p, Bv[None] - p, C[None] - p
        la, lb, lc = (np.linalg.norm(x, axis=2) for x in (a, b, c))
        num = np.einsum("ijk,ijk->ij", a, np.cross(b, c))
        den = la * lb * lc + np.einsum("ijk,ijk->ij", a, b) * lc + np.einsum("ijk,ijk->ij", b, c) * la + \
            np.einsum("ijk,ijk->ij", c, a) * lb
        out[s:s + chunk] = np.arctan2(num, den).sum(1) / (2 * np.pi)
    return out


def test_size_from_his_head(body):
    """Leatt sizes by head girth; his 59.2 cm head is a size L (59 to 60 cm)."""
    c = H.head_circumference(body)
    assert 0.585 < c < 0.600
    assert H.size_for(c) == "L"


def test_shell_dimensions_from_leatt_photos(built):
    """Outer shell to the strap-scaled photos: width 255 to 262 mm (back view), shell length chin to back
    365 to 372 mm, overall length with the visor (side view, 371 mm) within 4 mm."""
    Vo, Fo, prof = H.shell_outer()
    assert 0.255 < 2 * Vo[:, 0].max() < 0.262
    assert 0.362 < np.ptp(Vo[:, 1]) < 0.372
    vis = H.visor_surface(prof)
    total = max(Vo[:, 1].max(), vis[..., 1].max()) - min(Vo[:, 1].min(), vis[..., 1].min())
    assert abs(total - 1494 * H.S) < 0.004


def test_shell_is_closed_and_symmetric(built):
    P = built["parts"]["helmet_shell"]
    E = {}
    for f in P.F:
        for a, b in zip(f, np.roll(f, -1)):
            k = (min(a, b), max(a, b))
            E[k] = E.get(k, 0) + 1
    assert all(v == 2 for v in E.values())
    D = {}
    for f in P.F:
        for a, b in zip(f, np.roll(f, -1)):
            D[(a, b)] = D.get((a, b), 0) + 1
    assert all(v == 1 and D.get((b, a)) == 1 for (a, b), v in D.items())        # consistently wound
    V = (P.V - built["t"]) @ built["R"]                 # back in the helmet frame
    m = V.copy(); m[:, 0] *= -1
    from scipy.spatial import cKDTree
    assert cKDTree(V).query(m)[0].max() < 1e-6


def normal_turn_variation(V, F, region):
    """Normal turn along each edge (|n_i - n_j| / |v_i - v_j|, 1/m) less the median over the edges round its two
    vertices: a ridge or a scallop stands out, a fair surface stays near zero."""
    N = H.normals(V, F)
    E = np.unique(np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0)
    E = E[region[E[:, 0]] & region[E[:, 1]]]
    k = np.linalg.norm(N[E[:, 0]] - N[E[:, 1]], axis=1) / np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    inc = {}
    for e, (a, b) in enumerate(E):
        inc.setdefault(a, []).append(e)
        inc.setdefault(b, []).append(e)
    med = np.array([np.median(k[inc[a] + inc[b]]) for a, b in E])
    return E, k - med


def test_shell_is_fair_at_the_crown_back():
    """Round 2 (decision 44): main's crown back carried ridges 20 mm either side of the centre line (the width
    field's distance to a 3 mm sampled rim) and slope steps at the width tables' knots, seen as banded, spiky
    reflections in Leatt's back view (px 860 to 1060). Behind y = 30 mm and above z = -130 mm, 8 mm or more from
    the free edges, no edge's normal turn may stand more than 120 /m above its neighbours' (main: 190 /m)."""
    from scipy.spatial import cKDTree
    V, F, _ = H.shell_outer()
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    u, c = np.unique(E, axis=0, return_counts=True)
    free = cKDTree(V[np.unique(u[c == 1])]).query(V)[0] > 0.008
    E, dk = normal_turn_variation(V, F, (V[:, 1] > 0.03) & (V[:, 2] > -0.13) & free)
    assert len(E) > 5000
    worst = V[E[np.argmax(dk)]].mean(0) * 1000
    assert dk.max() < 120.0, f"normal turn {dk.max():.0f} /m above its neighbours at {np.round(worst)} mm"


def port_edge_px(view, rows, port=None):
    """The face port's rear edge on the near side through one of Leatt's cameras: the loop's rightmost crossing
    of each image row (iso-left: the helmet's left side, its back to the right)."""
    V, F, _ = H.shell_outer(H.Profile(port=port))
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    u, c = np.unique(E, axis=0, return_counts=True)
    B = u[c == 1]
    # the port's loop: free edges above the lower edge (z > -0.09 m at their mid points) and ahead of y = 0
    m = V[B].mean(1)
    B = B[(m[:, 2] > -0.09) & (m[:, 1] < 0.0) & (m[:, 0] > 0)]
    q = H.cam_project(H.CAMS[view], V)[0]
    out = []
    for r in rows:
        a, b = q[B[:, 0]], q[B[:, 1]]
        hit = (a[:, 1] - r) * (b[:, 1] - r) <= 0
        t = (r - a[hit, 1]) / (b[hit, 1] - a[hit, 1] + 1e-12)
        out.append(float(np.max(a[hit, 0] + t * (b[hit, 0] - a[hit, 0]))))
    return np.array(out)


def test_face_port_edge_on_leatt_iso_left():
    """Round 2 (decision 44): the shell's port edge (the rubber trim's inner edge) where Leatt's Pinata iso-left
    photo shows it, picked on a 1:1 crop at rows 830 to 1040: x 1195, 1193, 1189, 1183 px. Main's edge followed
    the side photo's notch (the cheek pads), about 40 mm ahead: 185 to 221 px left of the photo, and the print's
    black trim and grip panel spread over the shell there. Round 2's "iso" port: -5 to +4 px. The build keeps
    the "side" port (helmet.PORT) until the goggle moves back to meet this edge (decision 44)."""
    rows = [830, 900, 970, 1040]
    err = port_edge_px("isoleft", rows, port="iso") - np.array([1195.0, 1193.0, 1189.0, 1183.0])
    assert np.all(np.abs(err) < 12.0), f"port edge off Leatt's iso-left by {np.round(err, 1)} px"


def test_fit_on_his_head(built):
    """Even stand-off all round the skull (EPS and pads), brow ahead of the forehead, eyes in the face port."""
    g = built["info"]["gaps_mm"]
    ring = [g["top"], g["back"], g["left"], g["right"]]
    assert 40 < min(ring) and max(ring) - min(ring) < 4
    assert g["fore"] >= 31.5


CHAIN = ("neck01", "neck02", "neck03", "head")


def deform_head(body, pitch_deg):
    """His skin with the head pitched down by pitch_deg relative to the trunk, shared equally by the three neck
    bones and the head (cervical flexion), by linear blend skinning of the rest mesh. Returns the skin, and the
    head bone's rigid motion (R, j, d): p -> R (p - j) + j + d."""
    names = list(body["bones"])
    parents = list(body["parents"])
    heads = body["heads"]
    Ra = H.rot_x(math.radians(pitch_deg / len(CHAIN)))
    M = {}                                               # bone -> (R, d): p -> R p + d
    R, d = np.eye(3), np.zeros(3)
    for n in CHAIN:
        j = heads[names.index(n)]
        jw = R @ j + d                                    # the joint where the chain has carried it
        R, d = Ra @ R, Ra @ (d - jw) + jw + 0 * j
        M[n] = (R.copy(), d.copy())
    under = {"head"}
    grow = True
    while grow:
        new = {n for n, p in zip(names, parents) if p in under} - under
        grow = bool(new)
        under |= new
    for n in under:
        M[n] = M["head"]
    V = body["V"]
    out = np.zeros_like(V)
    tot = np.zeros(len(V))
    for bi, n in enumerate(names):
        sel = body["w_bone"] == bi
        vi, w = body["w_vert"][sel], body["w_val"][sel]
        Rb, db = M.get(n, (np.eye(3), np.zeros(3)))
        np.add.at(out, vi, w[:, None] * (V[vi] @ Rb.T + db))
        np.add.at(tot, vi, w)
    out /= tot[:, None]
    return out, M["head"]


@pytest.mark.parametrize("pitch", [0.0, 20.0])
def test_no_skin_inside_the_shell(body, built, pitch):
    """No skin vertex inside the shell's solid (shell, EPS, liner), at rest and with the head pitched down 20 deg
    as when riding (shared by the neck and head; the helmet rides the head bone, chest and shoulders do not).
    Pitching the head bone alone by 20 deg brings the chin bar's lower inner rim 6 vertices into his throat."""
    P = built["parts"]["helmet_shell"]
    Vs, (R, d) = deform_head(body, pitch)
    Vh = P.V @ R.T + d
    lo, hi = Vh.min(0) - 0.01, Vh.max(0) + 0.01
    near = np.all((Vs > lo) & (Vs < hi), axis=1)
    w = winding(Vs[near], Vh, tris(P))
    assert (w < 0.5).all(), f"{(w >= 0.5).sum()} skin vertices inside the shell"


def test_npz_loads_for_build_rider(built):
    g = np.load(built["path"])
    mats = json.loads(str(g["materials"]))
    for name in g["names"]:
        name = str(name)
        assert str(g[name + "__bone"]) in ("head", "eye.L", "eye.R")        # his eyes ride their eye bones
        FS, F, M = g[name + "__FS"], g[name + "__F"], g[name + "__M"]
        assert FS.sum() == len(F) and len(M) == len(FS) and F.max() < len(g[name + "__V"])
        if name + "__UV" in g:
            assert len(g[name + "__UV"]) == FS.sum()
    for m in g["mats"]:
        assert str(m) in mats


def test_goggle_in_the_port_on_his_eyes(body, built):
    """Lens ahead of both eyes, nothing of the lens inside the shell; the strap 45 mm wide (Leatt); the frame
    raspberry (his photos, not Leatt's hot pink render). More in test_goggle.py."""
    P = built["parts"]
    L = H.head_landmarks(body)
    lens = P["goggle_lens"].V
    for sgn in (1, -1):
        e = L["eye"] + [sgn * 0.031, 0, 0]
        near = lens[np.abs(lens[:, 0] - e[0]) < 0.004]
        assert near[:, 2].min() < e[2] < near[:, 2].max()            # the eye's height is inside the lens
        assert 0.035 < e[1] - near[:, 1].max() < 0.09                # lens back 35 to 90 mm ahead of the eye centre
    sh = P["helmet_shell"]
    assert (winding(lens, sh.V, tris(sh)) < 0.5).all()
    st = P["goggle_strap"]
    n = len(st.V) // 4
    w = np.linalg.norm(st.V[n:2 * n] - st.V[:n], axis=1)
    assert np.allclose(np.median(w), H.STRAP_W, atol=0.002)
    import goggle as G
    r, g, b = G.MATERIALS["goggle_frame"]["rgb"]
    assert r > 120 and g < 60 and b < 110


def test_textures_present():
    for f in ("helmet_pinata.png", "goggle_strap.png", "goggle_outrigger.png"):
        assert os.path.getsize(os.path.join(H.TEXDIR, f)) > 1000


# ---------------------------------------------------------------- the Pinata art (helmet_art.py)
SMALL = 1024                                            # the tests draw and read the art at 1024 texels (0.93 mm)


def shrink(img, n=SMALL):
    s = img.shape[0] // n
    return img.reshape(n, s, n, s, 3).mean((1, 3))


@pytest.fixture(scope="module")
def art(tmp_path_factory):
    """The art drawn twice at 1024 texels by the script, and the delivered 4096 texture shrunk to 1024."""
    from PIL import Image
    import helmet_art as A
    Image.MAX_IMAGE_PIXELS = None
    d = tmp_path_factory.mktemp("art")
    drawn = []
    for k in range(2):
        p = str(d / f"art{k}.png")
        A.draw(p, tex=SMALL, log=lambda *a: None)
        drawn.append(np.asarray(Image.open(p).convert("RGB")).astype(np.float32))
    tex = np.asarray(Image.open(os.path.join(H.TEXDIR, "helmet_pinata.png")).convert("RGB")).astype(np.float32)
    r, c, P, N, S = A.texels(SMALL)
    cov = np.zeros((SMALL, SMALL), bool)
    cov[r, c] = True
    return dict(A=A, drawn=drawn, tex=tex, small=shrink(tex), cov=cov)


def test_art_drawn_deterministically(art):
    """The print is drawn by script from helmet_art.json and helmet_art_field.png (no photo pixels, no randomness):
    two draws are identical, and the delivered texture is that drawing at 4096 texels."""
    a, b = art["drawn"]
    assert np.array_equal(a, b)
    assert art["tex"].shape == (H.TEX, H.TEX, 3)
    cov = art["cov"]
    d = np.abs(art["small"] - a)[cov].mean(1)
    assert np.mean(d) < 3.0 and np.percentile(d, 90) < 6.0        # only the finer edges of the 4096 drawing differ


def test_no_studio_light_in_the_flat_print(art):
    """Lighting comes only from Blender: inside the white base and the black areas (3 texels from any edge) the
    print is flat. The luminance spread there is under 4 levels (the old projection of the studio photos: 40) and
    under 5 % of those texels have a local (7 x 7 texel, 6.5 mm) luminance deviation over 2 (the old: 29 %)."""
    from scipy import ndimage
    a = art["small"]
    L = a @ [0.2126, 0.7152, 0.0722]
    m1, m2 = ndimage.uniform_filter(L, 7), ndimage.uniform_filter(L * L, 7)
    sd = np.sqrt(np.maximum(m2 - m1 * m1, 0.0))
    core = ndimage.binary_erosion(art["cov"], iterations=3)
    spread = a.max(-1) - a.min(-1)
    for name, ink in (("white", (a.min(-1) > 190) & (spread < 25)), ("black", (a.max(-1) < 60))):
        inner = ndimage.binary_erosion(ink & core, np.ones((3, 3)), iterations=3)
        assert inner.sum() > 5000, name
        lo, hi = np.percentile(L[inner], [0.5, 99.5])
        assert hi - lo < 4.0, (name, lo, hi)
        assert (sd[inner] > 2.0).mean() < 0.05, name


def test_brow_badge_carries_one_leatt(art):
    """The brow badge is part of the art (helmet.py no longer paints goggle.paint_brow_badge over it): purple, with
    one white LEATT from Leatt's own file, 34.6 mm wide and centred, its white area that of one wordmark."""
    import inspect
    A = art["A"]
    assert "paint_brow_badge(" not in inspect.getsource(H)
    tex = art["tex"]
    r, c, P, N, S = A.texels(H.TEX)
    px = tex[r, c]
    brow = A.brow_zone(P, N) & (S == 0)
    from matplotlib.path import Path
    inside = brow & Path(A.badge_outline()).contains_points(P[:, [0, 2]])
    white = inside & (px.min(1) > 200)
    purple = inside & (np.abs(px - A.BADGE_RGB).sum(1) < 30)
    assert purple.sum() > 3 * white.sum()
    x = P[white, 0]
    assert abs(0.5 * (x.min() + x.max())) < 0.0015
    assert abs(np.ptp(x) - A.BADGE_LOGO["width"]) < 0.002
    m = A.wordmark_mask()
    w = A.BADGE_LOGO["width"]
    area = m.mean() * w * w * m.shape[0] / m.shape[1]           # one wordmark (m^2, in x and z)
    measured = white.sum() / H.ATLAS_K ** 2                      # front island: one texel is 1 / ATLAS_K in x and z
    assert 0.8 < measured / area < 1.25


def test_paint_is_a_gloss_clear_over_flat_print():
    """helmet_paint: the print under a full clear coat (IOR 1.5, glossy). The print/coat interface reflects next to
    nothing, so the base has no specular of its own (Blender 5.2 does not remove it under a coat by itself)."""
    m = H.MATERIALS["helmet_paint"]
    assert m["coat"] == 1.0 and m["spec"] == 0.0 and m["coat_rough"] <= 0.05


def test_art_data_complete():
    """helmet_art.json: the five inks, polygons for each, the element frames (Leatt's files, the labels) and the
    traced colour of the elements that take one."""
    import helmet_art as A
    d = json.load(open(A.DATA))
    assert set(d["inks"]) == set(A.INKS) and all(len(d["polygons"][k]) > 0 for k in A.INKS)
    names = {f["name"] for f in d["frames"]}
    for n in ("back_leatt", "back_icon", "side_icon", "side_icon_R", "visor_side_leatt", "visor_side_leatt_R",
              "turbine", "dot_label", "size_label", "emergency", "emergency_R", "chin_text", "chin_text_R",
              "visor_chevrons", "visor_chevrons_R"):
        assert n in names, n
    assert any(n.startswith("eight") for n in names)
    assert "visor_leatt" not in names                     # the visor's LEATT band is traced (its file did not fit)
    assert len(d["element_rgb"]["back_icon"]) == 3


def test_visor_chevrons_from_the_top_photo(art):
    """The visor's chevrons: seven per side, vectorised from Leatt's top photo (the stored outlines are the photo's,
    redone the same), on the visor's top at mirror places (within 3 mm), and drawn crisp: black ink, the band
    between them plain white (no traced copy beside the drawn one)."""
    A = art["A"]
    d = json.load(open(A.DATA))
    fr = {f["name"]: f for f in d["frames"] if f["name"].startswith("visor_chevrons")}
    again = A.chevron_polys()
    for name, f in fr.items():
        assert len(f["polys"]) == 7 and f["surface"] == 1
        for p, q in zip(f["polys"], again[name]):
            assert np.allclose(np.asarray(p), q, atol=0.01)
    oL, oR = (np.asarray(fr[k]["o"]) for k in ("visor_chevrons", "visor_chevrons_R"))
    assert np.linalg.norm(oL * [-1, 1, 1] - oR) < 0.003
    chevron_band_check(A, art["tex"], [f for n, f in sorted(fr.items())], d["frames"])


def chevron_band_check(A, tex, chev, frames):
    """Inside the drawn chevrons black; in the band round them (0.5 to 3 mm from one, not under the visor's black
    LEATT) the white print only: the share of dark texels there."""
    from scipy import ndimage
    r, c, P, N, S = A.texels(tex.shape[0])
    sel = np.nonzero(S == 1)[0]
    others = [f for f in frames if f["name"].startswith("visor_side_leatt")]
    under, _ = A.erase_mask(others, P[sel], N[sel], S[sel])
    out = []
    for f in chev:
        px = A.frame_px(f, P[sel], N[sel])
        ok = ~np.isnan(px[:, 0])
        art_a = A.poly_art(f)[..., 3]
        dist = ndimage.distance_transform_edt(art_a < 0.5) * A.px_size(f)
        a, dd = np.zeros(len(sel)), np.full(len(sel), 1.0)
        a[ok] = ndimage.map_coordinates(art_a, [px[ok, 1], px[ok, 0]], order=1, cval=0.0)
        dd[ok] = ndimage.map_coordinates(dist, [px[ok, 1], px[ok, 0]], order=0, cval=1.0)
        rgb = tex[r[sel], c[sel]]
        ink = a > 0.95
        band = ok & (a < 0.02) & (dd > 0.0005) & (dd < 0.003) & ~under
        assert ink.sum() > 200 and np.median(rgb[ink].max(1)) < 40, f["name"]
        assert band.sum() > 200, f["name"]
        out.append(float((rgb[band].max(1) < 120).mean()))
    assert max(out) < 0.01, out
    return out
