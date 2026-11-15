"""Tests of Damien's jersey and pant (kit.py): the gear file, sizes against Leatt's charts and his body, the tuck,
skin clearance at rest and in riding poses. Needs tools/fetch_makehuman.sh.

python3 -m pytest -q test_rider.py test_kit_rider.py
"""
import json
import os
import sys

import numpy as np
import pytest
from scipy import sparse
from scipy.spatial import ConvexHull, cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body as B   # noqa: E402
import kit as K    # noqa: E402


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    d = tmp_path_factory.mktemp("kit")
    np.savez_compressed(d / "body.npz", **B.build())
    K.main(str(d / "body.npz"), str(d / "kit.npz"), tex=os.environ.get("KIT_TEX", "1") == "1")
    body = K.Body(str(d / "body.npz"))
    return body, dict(np.load(d / "kit.npz"))


def part(g, name):
    V = g[name + "__V"].astype(float)
    FS, F = g[name + "__FS"], g[name + "__F"]
    st = np.r_[0, np.cumsum(FS)[:-1]]
    faces = [F[s:s + n] for s, n in zip(st, FS)]
    return V, faces


def weights(g, name, n, nb):
    return sparse.coo_matrix((g[name + "__ww"], (g[name + "__wv"], g[name + "__wb"])), (n, nb)).toarray()


def girth(P):
    h = ConvexHull(P[:, :2])
    p = P[h.vertices][:, :2]
    return np.linalg.norm(np.roll(p, -1, 0) - p, axis=1).sum()


def test_gear_file_loads_and_is_consistent(built):
    body, g = built
    mats = [str(m) for m in g["mats"]]
    spec = json.loads(str(g["materials"]))
    assert set(mats) <= set(spec)
    nb = len(body.names)
    for name in [str(n) for n in g["names"]]:
        V, faces = part(g, name)
        F = g[name + "__F"]
        assert F.min() >= 0 and F.max() < len(V)
        assert len(g[name + "__M"]) == len(faces) and g[name + "__M"].max() < len(mats)
        if name + "__UV" in g:
            assert len(g[name + "__UV"]) == len(F)
            assert g[name + "__UV"].min() >= 0 and g[name + "__UV"].max() <= 1
        W = weights(g, name, len(V), nb)
        assert np.allclose(W.sum(1), 1, atol=1e-3)                      # every vertex follows the skeleton
        for key in ("image", "normal"):
            for m in spec.values():
                if key in m:
                    assert os.path.exists(os.path.join(K.TEXDIR, m[key])), m[key]
    hb = g["hide_body"]
    assert hb.min() >= 0 and hb.max() < len(body.V) and len(np.unique(hb)) == len(hb)


def test_sizes_against_the_charts(built):
    """Jersey L: its girth at his chest is the chart's top of L (112 cm) within 3 cm; pant L: the waistband's
    inside, less the tucked jersey under it, inside L's waist range (83 to 88 cm); cuffs where the brief puts
    them."""
    body, g = built
    V, _ = part(g, "jersey")
    s = V[(np.abs(V[:, 2] - 1.36) < 0.006) & (np.abs(V[:, 0]) < 0.20)]
    assert abs(girth(s) - K.JERSEY_CHEST) < 0.03
    P, _ = part(g, "pants")
    _, wtop = K.pant_region(body)
    band = P[(P[:, 2] < wtop(P) - 0.025) & (P[:, 2] > wtop(P) - 0.035)]
    inner = girth(band) - 2 * np.pi * (K.C_PANT_WAIST - K.C_TUCK - 0.001)     # band and facing: 2 x 4 mm
    body_band = inner - 2 * np.pi * (K.C_TUCK + 0.001)                        # his girth under it
    assert 0.83 < body_band < K.PANT_WAIST, body_band
    assert abs(body_band - K.BODY_WAIST_BAND) < 0.005
    # the cuffs' folded edges (the open edges of the mesh are the facings' inner edges, inside the cuff)
    edge = P[P[:, 2] < P[:, 2].min() + 0.004]
    assert abs(P[:, 2].min() - K.PANT_CUFF_Z) < 0.006                    # mid-calf, level (the fold: 4 mm)
    assert (edge[:, 0] > 0).sum() > 20 and (edge[:, 0] < 0).sum() > 20
    # sleeve cuff 12 mm up the forearm from the wrist joint (the glove's cuff goes over it)
    for s, sg in (("L", 1), ("R", -1)):
        E, W = body.j(f"lowerarm01.{s}"), body.j(f"wrist.{s}")
        n = (W - E) / np.linalg.norm(W - E)
        reach = ((V[V[:, 0] * sg > 0.3] - W) @ n).max()
        assert -0.016 < reach < -0.008
    # neckline: low at the front (jugular notch), at the neck's root at the sides
    front = V[(np.abs(V[:, 0]) < 0.01) & (V[:, 1] < -0.05)]
    assert abs(front[:, 2].max() - K.NECK_FRONT) < 0.012


def test_cloth_clears_the_skin_at_rest(built):
    body, g = built
    for name in ("jersey", "pants"):
        V, _ = part(g, name)
        c = K.clearance_to(body, V)                     # the turned-in facings run 1 to 2 mm off the skin
        assert np.percentile(c, 1) > 0.0002 and c.min() > -0.002, name


def test_tucked_jersey_stays_under_the_pant(built):
    """Below the pant's top the jersey runs inside the pant (photo 07: waistband and strap visible)."""
    body, g = built
    J, _ = part(g, "jersey")
    P, _ = part(g, "pants")
    _, wtop = K.pant_region(body)
    m = J[:, 2] < wtop(J) - 0.01
    cj = K.clearance_to(body, J[m])
    _, k = cKDTree(P).query(J[m])
    cp = K.clearance_to(body, P[k])
    assert (cj < cp - 0.001).mean() > 0.99


def _posed(body, g, pose):
    Ms = K.bone_matrices(body, pose)
    nb = len(body.names)
    Vb = K.lbs(body.V, body.W, Ms)
    out = {}
    for name in ("jersey", "pants"):
        V, faces = part(g, name)
        W = weights(g, name, len(V), nb)
        Q = np.array([f for f in faces if len(f) == 4])
        out[name] = (K.lbs(V, W, Ms), Q)
    return Vb, out


@pytest.mark.parametrize("seated", [False, True])
def test_no_skin_through_the_cloth_when_riding(built, seated):
    """Knees and ankles bent, head pitched down 20 deg, arms reaching with elbows bent (and seated: hips and knees
    at 90 deg). (1) No visible skin pokes out through the cloth away from its openings; (2) the cloth stays over
    the skin it hides (masked skin is never drawn; where linear blend skinning folds the skin at the inner elbow,
    the knee and the lower back it may stand a little out of the cloth, but no region slides out from under it)."""
    body, g = built
    Vb, garments = _posed(body, g, K.riding_pose(body, seated))
    hidden = np.zeros(len(body.V), bool)
    hidden[g["hide_body"]] = True
    pts, nrm, edge = [], [], []
    for name, (V, Q) in garments.items():
        n0 = int(np.unique(Q).max()) + 1
        N = K.vnormals(V, Q)
        # vertices within two rings of an opening
        A = K.adjacency(len(V), Q)
        e = np.zeros(len(V), bool)
        e[np.unique(K.boundary_edges(Q))] = True
        for _ in range(4):                 # the facing, the fold, the edge and the first ring inside
            e |= (A @ e.astype(float)) > 0
        pts.append(V)
        nrm.append(N)
        edge.append(e)
    P, N, E = np.concatenate(pts), np.concatenate(nrm), np.concatenate(edge)
    tree = cKDTree(P)
    d, i = tree.query(Vb)
    out = ((Vb - P[i]) * N[i]).sum(1)
    poke = (~hidden) & (d < 0.03) & (out > 0.002) & (~E[i])
    assert poke.sum() == 0, f"{poke.sum()} visible skin vertices through the cloth"
    exposed = hidden & ((d > 0.06) | (out > 0.006))
    assert exposed.sum() < 0.08 * hidden.sum(), f"{exposed.sum()} hidden skin vertices not under cloth"
    assert (hidden & (d > 0.06)).sum() <= 10        # nothing slid off (the kneecap's skin is the only spot)


def test_print_overlay_rides_the_jersey(built):
    """Damien's additions' sharper overlay: every vertex PRINT_LIFT outside a jersey vertex, with that vertex's own
    skin weights (it moves with the cloth), UVs inside the atlas, the overlay's two materials only."""
    body, g = built
    nb = len(body.names)
    J, _ = part(g, "jersey")
    P, faces = part(g, "jersey_print")
    d, k = cKDTree(J).query(P)
    assert np.abs(d - K.PRINT_LIFT).max() < 2e-5
    Wj, Wp = weights(g, "jersey", len(J), nb), weights(g, "jersey_print", len(P), nb)
    assert np.abs(Wp - Wj[k]).max() < 1e-3
    uv = g["jersey_print__UV"]
    assert uv.min() >= 0 and uv.max() <= 1
    mats = [str(m) for m in g["mats"]]
    assert {mats[i] for i in np.unique(g["jersey_print__M"])} <= {"jersey_print_hd", "jersey_print_hd_mesh"}
    assert len(faces) > 300


def test_prints_at_their_measured_places(built):
    """Number (PHOTO 06: 0.30 m across the flat back, its top 0.37 of its height under the collar), name centred
    over it (Damien), sponsors at the ledger's places and widths, heights from the official artwork."""
    body, g = built
    pr = json.loads(str(g["prints"]))
    n = pr["number"]
    assert abs(n["w"] - K.NUMBER_W) < 0.003 and 0.18 < n["h"] < 0.21
    assert abs(n["P0"][0]) < 1e-3 and 1.38 < n["P0"][2] < 1.44 and n["P0"][1] > 0.08      # on his back, centred
    nm = pr["name"]
    assert abs(nm["P0"][0]) < 1e-3                               # centred over the number, on the spine
    assert nm["P0"][2] - nm["h"] / 2 > n["P0"][2] + n["h"] / 2 - 0.01   # above the number
    assert abs(nm["w"] - (K.NAME_RIGHT - K.NAME_LEFT) * n["w"]) < 0.003
    for k, (x, z, w) in K.FRONT.items():
        p = pr[k]
        assert p["kind"] == "front" and p["P0"][1] < -0.1
        assert abs(p["P0"][0] - x) < 1e-6 and abs(p["P0"][2] - z) < 1e-6 and abs(p["w"] - w) < 1e-6
    assert pr["bikewise"]["P0"][0] < 0 < pr["pirelli"]["P0"][0]                  # BikeWise his right, Pirelli left
    assert pr["usn"]["P0"][0] < 0 < pr["cworx"]["P0"][0] and pr["motul"]["P0"][2] < pr["usn"]["P0"][2]
    assert abs(pr["pirelli"]["w"] / pr["pirelli"]["h"] - 476 / 147) < 0.05      # Pirelli's own box


def test_name_length_from_the_letters_seen():
    """PHOTO 06 shows DAMI over 0.585 number widths before a fold at the collar: the whole name scales by the
    lettering's own ink widths (no Blender, no build)."""
    from PIL import ImageFont
    f = ImageFont.truetype(K.NAME_FONT, 600)
    w = lambda s: f.getbbox(s)[2] - f.getbbox(s)[0]
    seen, frac = K.NAME_SEEN
    assert K.NAME.startswith(seen)
    assert abs(frac * w(K.NAME) / w(seen) - K.NAME_LEN) < 0.005
    assert K.NAME_LEFT == -K.NAME_RIGHT                          # centred (Damien)


def test_prints_read_the_right_way_round(built):
    """The 114 is the plate's art, not mirrored; on his back the reader's right is his right (-x), so the 4 lies on
    his right; on his chest the reader's right is his left (+x)."""
    from PIL import Image
    body, g = built
    V, faces = part(g, "jersey")
    Q = np.array([f for f in faces if len(f) == 4])
    N = K.vnormals(V, Q)
    prints = {p.name: p for p in K.damien_prints(V, N)}
    num = prints["number"]
    a = num.art.rgba[..., :3].mean(2)                          # white glyphs, dark outline
    plate = np.asarray(Image.open(os.path.join(K.ART, "plate.png")).convert("L")).astype(float)[635:1425, 256:1498]
    plate = np.asarray(Image.fromarray(plate).resize((a.shape[1], a.shape[0])))
    c = lambda p, q: np.corrcoef(p.ravel(), q.ravel())[0, 1]
    assert c(a, plate) > 0.6 and c(a, plate) > c(a, plate[:, ::-1]) + 0.3
    back = (N[:, 1] > 0.3) & (np.abs(V[:, 2] - num.P0[2]) < 0.05)
    s, t, ok = num.st(V[back], N[back])
    assert (V[back][ok & (s > 0.08), 0] < 0).all() and (V[back][ok & (s < -0.08), 0] > 0).all()
    for k in K.FRONT:
        p = prints[k]
        # reader's right = +x (his left), up = up; the chest icon (round 3, Leatt's place under Pirelli) lies where
        # the chest turns: its right is 28 deg round from +x (R 0.88, 0.47), a mirrored print's would be -0.88
        assert p.R[0] > 0.8 and p.U[2] > 0.5


def test_logos_are_official_files():
    """Every sponsor's artwork is a file in reference/sponsors with its source URL in the README there."""
    readme = open(os.path.join(K.SPONSORS, "README.md")).read()
    for f in ("bikewise_logo.png", "usn_logo.png", "motul_logo.svg", "pirelli_logo.png",
              "cycleworx_suspension_logo.jpg"):
        assert os.path.exists(os.path.join(K.SPONSORS, f)), f
        line = [ln for ln in readme.splitlines() if f in ln]
        assert line and "https://" in line[0], f


def texture(name):
    from PIL import Image
    return np.asarray(Image.open(os.path.join(K.HERE, "..", "..", "textures", "rider", name)).convert("RGB")) / 255.0


def test_jersey_inks_are_leatts_flat(built):
    """Decision 52: the print's inks are those of Leatt US's front flat (evenly lit), not the on-model photos' paler
    ones (round 2: magenta with 4 times the flat's green, teal with 2.3 times its red, lime with twice its blue).
    The teal is not one ink but the end of the stripes' gradient, and the flat's teal box is its hem, tucked under
    the pant on him: test_stripe_gradient_maps_onto_the_flats checks it band by band."""
    a = texture("jersey_color.png")
    ref = K.photo_inks(K.FLAT_REF)
    for ink in ("magenta", "lime", "black"):
        m = K.ink_class(ink, a)
        got = np.median(a[m], 0) * 255
        want = K.to_srgb(ref[ink]) * 255
        assert m.sum() > 20000 and np.abs(got - want).max() < 30, (ink, got.round(), want.round())


def test_stripe_gradient_maps_onto_the_flats(built):
    """The NZ photo's stripes (lime to teal, one airbrushed gradient) land on the flat's colours band by band (round
    3's first map, fitted to four ink boxes, sent the lower stripes past the flat's teal: errors to 93 of 255, a
    tenth of the print's stripe texels at R under 0.15 and B over 0.72, none on the flat's teal)."""
    gs, gd = K.gradient_pairs()
    M = K.ink_map(K.JF_REF)
    err = np.abs(K.to_srgb(gs @ M[:3] + M[3]) - K.to_srgb(gd)).max(1) * 255
    assert len(gs) >= 12 and np.median(err) < 22 and err.max() < 35, err.round()
    x = texture("jersey_color.png").reshape(-1, 3)
    r, g, b = x[:, 0], x[:, 1], x[:, 2]
    st = (g > 0.6) & (g > r) & (x.min(1) < 0.6)
    assert (st & (r < 0.15) & (b > 0.72)).sum() / st.sum() < 0.02
    # nor paler: the flat's teal has red 18 to 80 (medians per 100 rows, 900 to 1700); round 2's had 127
    teal = np.median(x[K.ink_class("teal", x)], 0) * 255
    assert teal[0] < 100, teal.round()


def test_back_yoke_is_the_fronts_magenta(built):
    """One ink on the yoke, front and back (his photo 06 shows his back's magenta as deep as his front's in 09): the
    NZ back photo is brighter than the front, and through the front's map the back read (246, 41, 160) against the
    front's (226, 14, 132): 28 of 255 (main 41)."""
    body, g = built
    V, faces = part(g, "jersey")
    FS, UV = g["jersey__FS"], g["jersey__UV"].reshape(-1, 2)
    C = np.array([V[f].mean(0) for f in faces])
    U = np.array([UV[s:s + n].mean(0) for s, n in zip(np.r_[0, np.cumsum(FS)[:-1]], FS)])
    a = texture("jersey_color.png")
    H, W = a.shape[:2]
    col = a[np.minimum(((1 - U[:, 1]) * H).astype(int), H - 1), np.minimum((U[:, 0] * W).astype(int), W - 1)]
    mag = K.ink_class("magenta", col)
    front = mag & (C[:, 1] < 0) & (C[:, 2] > 1.46) & (np.abs(C[:, 0]) < 0.10)
    back = mag & (C[:, 1] > 0) & (C[:, 2] > 1.30) & (C[:, 2] < 1.48) & (np.abs(C[:, 0]) < 0.10)
    f, b = np.median(col[front], 0) * 255, np.median(col[back], 0) * 255
    assert front.sum() > 30 and back.sum() > 30 and np.abs(f - b).max() < 15, (f.round(), b.round())


def test_print_is_cut_not_blurred(built, texels):
    """The stripes are traced and cut, anti-aliased over one texel: few lime texels at mid brightness, where the
    projected photos had a soft ramp at every edge (round 2: 0.16 jersey, 0.51 pant). Leatt's own airbrushed ends
    are measured apart (round 3b): the sleeves' last 30 % (Leatt US's front flat fades the bands into the lime cuff
    there: 0.26 over its right sleeve, 0.48 to 0.64 at 0.80 to 0.90 of its length) and the chevrons' tops under
    FIVE.FIVE (fix 5), no softer than the flat's sleeve (under 0.30; round 3b 0.265). The rest of the jersey's charts
    under 0.10 (round 3b 0.090; by this measure round 3 0.147, main 0.162), the pant under 0.25 (round 3b 0.058,
    round 3 0.139, main 0.51)."""
    body, g = built
    a, pos, nrm, chm, tx = texels["jersey"]
    bx, bz0, bz1 = K.FP_FADE["box"]
    air = (chm == 0) & (np.abs(pos[..., 0]) < bx) & (pos[..., 2] > bz0) & (pos[..., 2] < bz1)
    for s, base in (("L", 2), ("R", 4)):
        m = (chm == base) | (chm == base + 1)
        _, _, t = K.sleeve_photo_uv(body, pos[m], s, "flat", photo_s="R")
        air[m] |= t > 0.7

    def soft(x):
        r, g_, b = x[:, 0], x[:, 1], x[:, 2]
        G = g_[(r > 0.45 * g_) & (b < 0.45 * g_) & (r < 1.1 * g_)]
        return ((G > 0.3) & (G < 0.7)).sum() / (G >= 0.7).sum()
    on = chm >= 0
    assert soft(a[on & ~air]) < 0.10 and soft(a[air]) < 0.30, (soft(a[on & ~air]), soft(a[air]))
    assert soft(texels["pants"][0].reshape(-1, 3)) < 0.25


def test_pant_rows_above_the_crotch_take_the_whole_pant(built):
    """Leatt's back photo opens a 5 px gap at its centre column 120 rows above the crotch: those rows must still map
    onto the pant (round 2 took the first run, the model's glove, and painted a band of his seat from it)."""
    body, g = built
    V, faces = part(g, "pants")
    crotch = V[np.abs(V[:, 0]) < 0.01][:, 2].min()
    sil = K.pant_silhouette(V, crotch, np.array([f for f in faces if len(f) == 4]))
    for ref, view, sel in ((K.PB_REF, "back", V[:, 1] > 0.02), (K.PF_REF, "front", V[:, 1] < -0.02)):
        ph = K.Photo(ref)
        P = V[sel & (V[:, 2] > 0.862) & (V[:, 2] < 1.0) & (np.abs(V[:, 0]) < 0.15)]
        u, v = K.pant_photo_uv(None, P, view, ph.alpha, sil)
        H, W = ph.alpha.shape
        on = ph.alpha[np.clip(v.astype(int), 0, H - 1), np.clip(u.astype(int), 0, W - 1)]
        assert len(P) > 100 and on.mean() > 0.97, view
        assert (np.abs(u - 960) < 500).all(), view


def test_thigh_logo_where_leatts_front_photo_sees_it():
    """The big LEATT on his left thigh: Leatt US's front photo sees 60 px of it near the leg's outer edge, so it
    faces front-outward, not square to the side (rounds 1 and 2)."""
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(K.REF, K.PF_REF)).convert("RGB")).astype(float) / 255
    ph = K.Photo(K.PF_REF)
    fr = []
    for y in range(900, 1250, 10):
        row = a[y, 1250:1460]
        x = np.nonzero((row.min(1) > 0.6) & (row.max(1) - row.min(1) < 0.2))[0] + 1250
        xs = np.nonzero(ph.alpha[y])[0]
        runs = np.split(xs, np.nonzero(np.diff(xs) > 3)[0] + 1)
        leg = [q for q in runs if 980 < q[0] < 1150][0]           # his left leg (the image's right)
        if len(x) > 8:
            fr.append(((x.min() + x.max()) / 2 - leg.min()) / (leg.max() - leg.min()))
    f = np.median(fr)                                     # across the leg seen from the front, 0 inner .. 1 outer
    from_front = np.degrees(np.arcsin(np.clip(2 * f - 1, -1, 1)))
    assert 0.85 < f < 0.95 and abs((90 - from_front) - K.THIGH_LOGO[1]) < 8


def test_chest_icon_is_leatts_official_mark(built):
    """Leatt's triangle beside the chest LEATT is printed from the official favicon (its stroke 0.13 of its width,
    the printed one 0.14), sharp at 0.1 mm, where the flat print's trace of the photo lost it (3 mm strokes)."""
    body, g = built
    pr = json.loads(str(g["prints"]))
    x, z, w = K.FRONT["icon"]
    assert abs(pr["icon"]["w"] - w) < 1e-6 and 0.12 < x < 0.15 and 1.40 < z < 1.44
    m = K.leatt_icon()
    assert abs(m.shape[1] / m.shape[0] - 1.0) < 0.05 and 0.3 < (m > 0.5).mean() < 0.6


def uv_seam_steps(g, a, select):
    """The colour step (of 255, the largest channel's) across the jersey's UV seams that `select` keeps (by the
    edge's midpoint): the texture a few mm inside each of the edge's two faces."""
    V = g["jersey__V"].astype(float)
    FS, F, UV = g["jersey__FS"], g["jersey__F"], g["jersey__UV"].reshape(-1, 2)
    edges = {}
    for s, n in zip(np.r_[0, np.cumsum(FS)[:-1]], FS):
        f, uv = F[s:s + n], UV[s:s + n]
        for i in range(n):
            j = (i + 1) % n
            mid = (uv[i] + uv[j]) / 2
            ends = np.r_[uv[i], uv[j]] if f[i] < f[j] else np.r_[uv[j], uv[i]]
            edges.setdefault((min(f[i], f[j]), max(f[i], f[j])), []).append((mid + 0.15 * (uv.mean(0) - mid), ends))
    H, W = a.shape[:2]
    out = []
    for (i, j), sides in edges.items():
        if len(sides) != 2 or np.abs(sides[0][1] - sides[1][1]).max() < 1e-4 or not select((V[i] + V[j]) / 2):
            continue                                        # one face, or no UV seam, or not asked for
        c = [a[min(int((1 - v) * H), H - 1), min(int(u * W), W - 1)] for (u, v), _ in sides]
        out.append(np.abs(c[0] - c[1]).max() * 255)
    return np.array(out)


def _along_arm(body, P, s):
    S, E, W, f, o = K.arm_frame(body, s)
    d = (W - S) / np.linalg.norm(W - S)
    t = (P - S) @ d
    return t, np.linalg.norm((P - S) - t * d), (P - S) @ o, np.linalg.norm(W - S)


def test_sleeve_print_runs_on_over_its_top_line(built):
    """Each sleeve is one pattern piece seamed under the arm; its UV charts are cut along its top line too. The flat
    print is cut once over the whole sleeve: along the top line the colour runs on (main, a photo blend: 0 median;
    round 3's first per-chart cut: 51, the stripes and the grounds stepped along the arm)."""
    body, g = built

    def top(P):
        for s in ("L", "R"):
            t, r, out, L = _along_arm(body, P, s)
            if 0.12 < t < L - 0.05 and r < 0.09 and out > 0:
                return True
        return False
    d = uv_seam_steps(g, texture("jersey_color.png"), top)
    assert len(d) > 30 and np.median(d) < 15 and np.percentile(d, 75) < 25, (len(d), np.percentile(d, [50, 75]))


def test_raglan_seam_has_no_colour_step_on_the_yoke(built):
    """The magenta yoke runs over the raglan seams (Leatt's front flat: one ink there). The sleeve's raglan part takes
    its colour from the trunk's photo where it turns away (shaded) and the trunk from further in: round 3's first cut
    stepped 37 along the seam (a zigzag of faces on the shoulder in photo 08's view); main 2."""
    body, g = built

    def yoke(P):
        return P[2] > 1.45 and abs(P[0]) > 0.07 and any(_along_arm(body, P, s)[0] < 0.03 for s in ("L", "R"))
    d = uv_seam_steps(g, texture("jersey_color.png"), yoke)
    assert len(d) > 50 and np.median(d) < 12 and np.percentile(d, 75) < 20, (len(d), np.percentile(d, [50, 75]))


def test_materials_cover_every_part(built):
    body, g = built
    spec = json.loads(str(g["materials"]))
    mats = [str(m) for m in g["mats"]]
    used = {mats[i] for n in g["names"] for i in np.unique(g[str(n) + "__M"])}
    assert {"jersey_print", "pant_print", "pant_iks", "strap", "buckle"} <= used
    for m in used:
        assert 0.0 <= spec[m].get("rough", 0.5) <= 1.0


# ================================================================ round 3b (the review at 1:1, six fixes)
def texel_maps(body, g):
    """Every texel of the jersey's and the pant's colour textures: the texture, the rest-pose point and normal there,
    its chart (-1 off the charts), and the texel's size in m."""
    out = {}
    for name, tex, k in (("jersey", "jersey_color.png", 0), ("pants", "pants_color.png", 1)):
        a = texture(tex)
        V = g[name + "__V"].astype(float)
        Q = g[name + "__F"].reshape(-1, 4)
        N = K.vnormals(V, Q)
        ch = K.jersey_charts(body, V, Q) if name == "jersey" else np.zeros(len(Q), int)
        pos, nrm, chm = K.raster(g[name + "__UV"].reshape(-1, 4, 2), V, N, Q, ch, a.shape[0])
        out[name] = (a, pos[::-1], nrm[::-1], chm[::-1], 1 / (float(g["tex_scale"][k]) * a.shape[0]))
    return out


@pytest.fixture(scope="module")
def texels(built):
    return texel_maps(*built)


def _sleeve(body, P, s):
    """Along the arm (0 shoulder point .. 1 cuff end, sleeve_photo_uv's), the cosine to the arm's front, and whether
    the point is on that sleeve."""
    S, E, W, f, o = K.arm_frame(body, s)
    d = (W - S) / np.linalg.norm(W - S)
    r = np.linalg.norm((P - S) - np.outer((P - S) @ d, d), axis=1)
    cosf, _ = K.arm_facing(body, s, P)
    _, _, t = K.sleeve_photo_uv(body, P, s, "flat", photo_s="R")
    return t, cosf, (P[:, 0] * (1 if s == "L" else -1) > 0.15) & (r < 0.10)


def test_sleeve_fronts_carry_the_flats_bands(built, texels):
    """Fix 1: each sleeve's front shows the front flat's zebra (grey-teal bands on the upper arm, teal, lime at the
    cuff). Band or ground, texel by texel, against Leatt US's front flat (its right sleeve; the left is drawn as its
    mirror image): the band texels' IoU over 0.75 on the upper arm and the forearm of both sleeves (round 3: his
    left 0.27 and 0.37, near black; main 0.21 to 0.36; round 3b 0.85 to 0.88)."""
    body, g = built
    a, pos, nrm, chm, _ = texels["jersey"]
    m = chm >= 0
    fl = K.Photo(K.FLAT_REF)
    band = lambda c: (c.max(1) > 0.28) & ~K.ink_class("white", c)   # noqa: E731
    for s in "LR":
        P = pos[m]
        t, cosf, on = _sleeve(body, P, s)
        u, v, _ = K.sleeve_photo_uv(body, P, s, "flat", photo_s="R")
        sel = on & (cosf > 0.5) & (t > 0.25) & (t < 0.85) & (fl.seen(u, v) > 0.5)
        br, bg = band(K.to_srgb(fl.lin(u[sel], v[sel]))), band(a[m][sel])
        for seg, (lo, hi) in (("upper arm", (0.25, 0.5)), ("forearm", (0.5, 0.85))):
            k = (t[sel] > lo) & (t[sel] < hi)
            iou = (br[k] & bg[k]).sum() / max((br[k] | bg[k]).sum(), 1)
            assert k.sum() > 2000 and iou > 0.75, (s, seg, int(k.sum()), round(float(iou), 2))


def test_back_and_sleeve_backs_carry_no_fragments(built, texels):
    """Fix 2: the back panel is plain, its magenta fading into the black (PHOTO back on-model, back three-quarter
    flat): stripe ink on under 0.02 of its flanks beside the side panels (round 3: 0.22, lime and teal fragments;
    main 0.21; round 3b 0.001). Each forearm's LEATT is Leatt's file at its place: the white over its span all round
    the arm is the stamp's letters, IoU over 0.8 (round 3: 0.27 and 0.13, a blob on his right forearm, a streak and
    letters at two places on his left; main 0.00 and 0.03; round 3b 0.99). No white specks under 20 mm2 on the
    sleeves' backs (main 3 on his left), and no white piece under 200 mm2 anywhere on the sleeves but Leatt's
    stamped marks (round 3: 25, his left 23 up to 75 mm2, his right 183 and 17 mm2; main 14, his left 9 up to
    48 mm2, his right 5 up to 188 mm2; round 3b's build 9: on his left, an 81 mm2 end of the forearm LEATT's traced
    streak and 14 specks of 1 to 2 mm2 over the elbow; round 3b: none)."""
    body, g = built
    a, pos, nrm, chm, tx = texels["jersey"]
    m = chm >= 0
    trunk = (chm == 0) | (chm == 1)
    z = pos[..., 2]
    flank = (trunk & (nrm[..., 1] > 0.3) & (pos[..., 1] > K.Y_SIDE + K.MESH_PANEL[0] + 0.005)
             & (z > K.HEM_Z + 0.03) & (z < 1.30) & (np.abs(pos[..., 0]) > 0.06))
    x = a[flank]
    stripe = (x[:, 1] > 0.25) & (x[:, 1] > x[:, 0]) & ~K.ink_class("white", x)
    assert flank.sum() > 20000 and stripe.mean() < 0.02, (int(flank.sum()), round(float(stripe.mean()), 3))
    marks = K.sleeve_marks(body, pos, nrm, chm)
    white = m & (a.min(-1) > 0.6)
    for mk in [mk for mk in marks if mk["kind"] == "leatt"]:
        stamp = mk["canvas"].apply(np.zeros(a.shape), pos, mk["zone"]).max(-1) > 0.5
        band = m & mk["keep"](pos.reshape(-1, 3)).reshape(m.shape)
        got = white & band
        iou = (got & stamp).sum() / max((got | stamp).sum(), 1)
        assert stamp.sum() * tx ** 2 > 5e-4 and iou > 0.8, (mk["s"], round(float(iou), 2))
    for s in "LR":
        P = pos[m]
        t, cosf, on = _sleeve(body, P, s)
        back = np.zeros(m.shape, bool)
        back[m] = on & (cosf < -0.3) & (t > 0.15) & (t < 0.95)
        from scipy import ndimage
        lab, n = ndimage.label(back & white, np.ones((3, 3)))
        sz = ndimage.sum(back & white, lab, range(1, n + 1)) * tx ** 2 * 1e6
        assert (sz < 20).sum() == 0, (s, int((sz < 20).sum()))
        sl = np.zeros(m.shape, bool)
        sl[m] = on & (t > 0.15) & (t < 0.95)
        stamped = np.any([mk["zone"] for mk in marks], 0)
        lab, n = ndimage.label(sl & white, np.ones((3, 3)))
        sz = ndimage.sum(sl & white, lab, range(1, n + 1)) * tx ** 2 * 1e6
        st = ndimage.maximum(stamped, lab, range(1, n + 1)).astype(bool) if n else np.zeros(0, bool)
        small = np.sort(sz[(sz < 200) & ~st])[::-1]
        assert len(small) == 0, (s, len(small), np.round(small[:3], 1).tolist())


def test_pant_outer_thighs_and_smooth_shins(built, texels):
    """Fix 3: his 07 and Leatt's three-quarter photo show the zebra round the outer thigh, from the hip down to the
    black knee panel: stripe ink on over 0.3 of the leg's side (within 18 deg of it) 30 to 42 cm above the knee
    joint (round 3: 0.09 and 0.09, plain black past 83 deg; main 0.36 and 0.53; round 3b 0.43 and 0.53). And the
    shins' magenta stripes are smooth sweeps (Leatt's photos), not jagged marks: what a 3 mm closing and opening
    changes, under 0.11 of the magenta (round 3: 0.126 and 0.116; main 0.18 and 0.17; round 3b 0.099 and 0.053)."""
    from scipy import ndimage
    body, g = built
    a, pos, nrm, chm, tx = texels["pants"]
    m = chm >= 0
    for s, sg in (("L", 1), ("R", -1)):
        kn = body.j(f"lowerleg01.{s}")[2]
        out = m & (pos[..., 0] * sg > 0.03) & (nrm[..., 0] * sg > 0.95)
        sel = out & (pos[..., 2] > kn + 0.30) & (pos[..., 2] < kn + 0.42)
        share = ((a[sel].max(1) > 0.275) & ~K.ink_class("white", a[sel])).mean()
        assert sel.sum() > 5000 and share > 0.3, (s, round(float(share), 2))
        shin = m & (pos[..., 0] * sg > 0) & (pos[..., 2] < kn - 0.06) & (pos[..., 2] > 0.30)
        mg = shin & K.ink_class("magenta", a)
        r = max(1, int(round(0.003 / tx)))
        sm = ndimage.binary_opening(ndimage.binary_closing(mg, iterations=r), iterations=r)
        rough = (mg ^ sm).sum() / max(mg.sum(), 1)
        assert mg.sum() > 2000 and rough < 0.11, (s, round(float(rough), 3))


def test_lower_back_holes_show_the_base_layer(built, texels):
    """Fixes 4 (round 3b) and 3 (round 3c): the lower back's perforations (LB_HOLES, an estimate; his 06 leads):
    light dots in the base layer's tone (within 0.1) in LB_HOLES' rows, each row holding over 0.8 of its columns, in
    a rectangular grid (his 06 and Leatt NZ's back three-quarter flat: the same x in every row; round 3b staggered
    them by half a pitch), and each dot's light over the black, summed, over 6 mm2 of the white ink (his 06 about
    10 mm2; round 3b 1.7, faint specks; round 3c 9.2). Round 3 and main: none in the tone."""
    from scipy import ndimage
    body, g = built
    a, pos, nrm, chm, tx = texels["jersey"]
    hb = K.LB_HOLES
    reg = ((chm >= 0) & (nrm[..., 1] > 0.3) & (np.abs(pos[..., 0]) < hb["half_width"] + 0.01)
           & (pos[..., 2] > hb["z_top"] - (hb["rows"] - 0.5) * hb["dz"]) & (pos[..., 2] < hb["z_top"] + hb["dz"] / 2))
    tone = np.asarray(hb["tone"]) / 255
    dots = reg & (np.abs(a - tone).max(-1) < 0.1)
    lab, n = ndimage.label(dots, np.ones((3, 3)))
    idx = range(1, n + 1)
    cz = np.array(ndimage.mean(pos[..., 2], lab, idx)) if n else np.zeros(0)
    cx = np.array(ndimage.mean(pos[..., 0], lab, idx)) if n else np.zeros(0)
    rows = np.round((hb["z_top"] - cz) / hb["dz"])
    ok = (rows >= 0) & (rows < hb["rows"])
    per_row = np.bincount(rows[ok].astype(int), minlength=hb["rows"])
    cols = 2 * hb["half_width"] / hb["pitch"] + 1
    assert (per_row > 0.8 * cols).all() and n < 1.2 * cols * hb["rows"], (n, per_row, round(cols, 1))
    # a rectangular grid: every dot within a quarter pitch of a column of the top row
    top = np.sort(cx[ok & (rows == 0)])
    off = np.abs(cx[ok][:, None] - top[None]).min(1)
    assert np.median(off) < hb["pitch"] / 4, round(float(np.median(off)) * 1000, 1)
    # the light: (linear) over the black round the dots, as a share of the white ink's, summed over each dot's rim
    lin = K.to_lin(a)
    blk = np.median(lin[reg & ~ndimage.binary_dilation(dots, iterations=4)], 0)
    wht = K.to_lin(np.array(K.INK_WHITE) / 255)
    e = np.clip(((lin - blk) / (wht - blk)).mean(-1), 0, None)
    labd = np.where(reg, ndimage.grey_dilation(lab, size=(5, 5)), 0)
    per = np.array(ndimage.sum(e, labd, idx)) * tx ** 2 * 1e6           # mm2 of white
    assert np.median(per) > 6.0, round(float(np.median(per)), 2)


def _seen_square(a, pos, nrm, chm, side, z0, z1, dz=0.01, bx=0.005):
    """The jersey seen square from the front (or the back), orthographic: per 5 mm column at each 1 cm row from z0
    to z1 the front-most (back-most) texel. Per row, the share of the garment's width in magenta (white over it
    counted)."""
    sg = -1 if side == "front" else 1
    sel = (chm >= 0) & (nrm[..., 1] * sg > 0)
    P, C = pos[sel], a[sel]
    out = []
    for z in np.arange(z0, z1 + 1e-9, dz):
        k = np.abs(P[:, 2] - z) < dz / 2
        b = np.floor(P[k, 0] / bx).astype(int)
        order = np.lexsort((-P[k, 1] * sg, b))
        _, first = np.unique(b[order], return_index=True)
        c = C[k][order][first]
        out.append((K.ink_class("magenta", c) | K.ink_class("white", c)).mean())
    return np.array(out)


def test_yoke_magenta_reaches_the_raglan_seams(built, texels):
    """Round 3c, fix 1: Leatt's flat, the NZ front and back photos and his 06 carry the yoke's magenta across the
    top to the raglan seams. Seen square on, its share of the garment's width at each 1 cm row (white over it
    counted): Leatt's flat 0.99 at the shoulders, the NZ front 0.97, the NZ back 0.92. Over 0.85 at the chest (z 1.48
    to 1.54) and the upper back (1.55 to 1.59): round 3b 0.45 to 0.56 and 0.53 to 0.64 (the sleeves' raglan part was
    traced as unseen, its ground taken from the black sleeve), main 0.70 to 0.86 and 0.68 to 0.79, round 3c 0.92 to
    1.00 and 0.99 to 1.00."""
    a, pos, nrm, chm, tx = texels["jersey"]
    f = _seen_square(a, pos, nrm, chm, "front", 1.48, 1.54)
    b = _seen_square(a, pos, nrm, chm, "back", 1.55, 1.59)
    assert f.min() > 0.85 and b.min() > 0.85, (np.round(f, 2).tolist(), np.round(b, 2).tolist())


def test_waistband_and_hem_beside_the_waistlock_are_clean(built, texels):
    """Round 3c, fix 2 (sheet 05 at 3x, his right hip beside the buckle): rounds 3b and main took each pant texel
    under a box round the Waistlock from the nearest traced pixel (teal blocks stepping down the waistband), and the
    jersey's lower side above it traced the NZ photo's folds as steps. On the stripe ink (chroma over 0.2): on the
    pant's front within 8 cm of its top (x -0.20 to -0.02) what an 8 mm closing and opening changes under 0.10 and
    the share of its outline running along the texture's axes (the blocks' sides) under 0.10 (main 0.140 and 0.14,
    round 3b 0.126 and 0.15, round 3c 0.068 and 0.06); on the jersey's front 1 to 10 cm over the pant's top (x -0.22
    to -0.10) what a 3 mm closing and opening changes under 0.045 (main 0.063, round 3b 0.052, round 3c 0.032)."""
    from scipy import ndimage
    body, g = built

    def rough(m, tx, rm):
        r = max(1, int(round(rm / tx)))
        sm = ndimage.binary_opening(ndimage.binary_closing(m, iterations=r), iterations=r)
        return (m ^ sm).sum() / max(m.sum(), 1)
    a, pos, nrm, chm, tx = texels["pants"]
    on = chm >= 0
    _, wtop = K.pant_region(body)
    wt = np.zeros(pos.shape[:2])
    wt[on] = wtop(pos[on])
    reg = on & (nrm[..., 1] < -0.3) & (pos[..., 0] > -0.20) & (pos[..., 0] < -0.02) & (pos[..., 2] > wt - 0.08)
    m = reg & ((a.max(-1) - a.min(-1)) > 0.2)
    f = ndimage.gaussian_filter(m.astype(float), 1.0)
    gy, gx = np.gradient(f)
    edge = reg & (np.hypot(gx, gy) > 0.15) & ndimage.binary_erosion(reg, iterations=3)
    ang = np.degrees(np.arctan2(np.abs(gy[edge]), np.abs(gx[edge])))
    axis = ((ang < 4) | (ang > 86)).mean()
    rp = rough(m, tx, 0.008)
    assert m.sum() > 3000 and edge.sum() > 500 and rp < 0.10 and axis < 0.10, (m.sum(), round(rp, 3), round(axis, 2))
    a, pos, nrm, chm, tx = texels["jersey"]
    reg = ((chm == 0) & (pos[..., 0] > -0.22) & (pos[..., 0] < -0.10) & (pos[..., 2] > K.WAIST_FRONT + 0.01)
           & (pos[..., 2] < K.WAIST_FRONT + 0.10))
    m = reg & ((a.max(-1) - a.min(-1)) > 0.2)
    rj = rough(m, tx, 0.003)
    assert m.sum() > 3000 and rj < 0.045, (m.sum(), round(rj, 3))


def test_chevron_fade_is_a_clean_gradient(built, texels):
    """Fix 5: the top chevrons' tops under FIVE.FIVE fade into the black as a clean gradient over the traced shape
    (as the yoke's magenta), not cut: of the band's green texels, over 0.4 at mid brightness (round 3: 0.28, a cut
    edge; main 0.55, the projected photo; round 3b 0.53)."""
    body, g = built
    a, pos, nrm, chm, tx = texels["jersey"]
    bx, bz0, bz1 = K.FP_FADE["box"]
    band = ((chm == 0) & (nrm[..., 1] < -0.3) & (np.abs(pos[..., 0]) < bx - 0.02) & (pos[..., 2] > bz0)
            & (pos[..., 2] < bz1))
    x = a[band]
    green = (x[:, 1] > 0.06) & (x[:, 1] > x[:, 0])
    mid = green & (x[:, 1] < 0.45)
    assert green.sum() > 2000 and mid.sum() / green.sum() > 0.4, round(float(mid.sum() / max(green.sum(), 1)), 2)


def test_fivefive_has_its_own_sharp_print(built):
    """Fix 6: FIVE.FIVE (8 mm capitals) read as dots at the jersey's 0.8 mm texel: it is set on the print overlay at
    its measured place (FRONT) with the logos, at under 0.17 mm a texel (round 3b 0.164: 49 texels to a capital;
    round 3 and main: traced into the jersey texture, no such print)."""
    body, g = built
    pr = json.loads(str(g["prints"]))
    assert "fivefive" in pr, sorted(pr)
    p = pr["fivefive"]
    x, z, w = K.FRONT["fivefive"]
    assert abs(p["P0"][0] - x) < 1e-6 and abs(p["P0"][2] - z) < 1e-6 and abs(p["w"] - w) < 1e-6, (p, (x, z, w))
    V, faces = part(g, "jersey_print")
    FS, UV = g["jersey_print__FS"], g["jersey_print__UV"].reshape(-1, 2)
    st = np.r_[0, np.cumsum(FS)[:-1]]
    tex = []
    for f, s0, n in zip(faces, st, FS):
        c = V[f].mean(0)
        if abs(c[0] - x) < w / 2 and abs(c[2] - z) < 0.006 and c[1] < 0:
            P, U = V[f], UV[s0:s0 + n]
            a3 = (np.linalg.norm(np.cross(P[1] - P[0], P[2] - P[0]))
                  + np.linalg.norm(np.cross(P[2] - P[0], P[-1] - P[0])))
            c2 = lambda p, q: abs(p[0] * q[1] - p[1] * q[0])   # noqa: E731
            a2 = c2(U[1] - U[0], U[2] - U[0]) + c2(U[2] - U[0], U[-1] - U[0])
            tex.append(np.sqrt(a3 / max(a2, 1e-12)) / K.ATLAS_RES)
    assert len(tex) >= 4 and np.median(tex) < 0.17e-3, (len(tex), np.median(tex) if tex else None)
