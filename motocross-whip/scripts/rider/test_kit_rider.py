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
    """Number (PHOTO 06: 0.30 m across the flat back, its top 0.37 of its height under the collar), name over its
    left half (his left), sponsors at the ledger's places and widths, heights from the official artwork."""
    body, g = built
    pr = json.loads(str(g["prints"]))
    n = pr["number"]
    assert abs(n["w"] - K.NUMBER_W) < 0.003 and 0.18 < n["h"] < 0.21
    assert abs(n["P0"][0]) < 1e-3 and 1.38 < n["P0"][2] < 1.44 and n["P0"][1] > 0.08      # on his back, centred
    nm = pr["name"]
    assert nm["P0"][0] > 0.05                                    # his left (seen from behind: the left)
    assert nm["P0"][2] - nm["h"] / 2 > n["P0"][2] + n["h"] / 2 - 0.01   # above the number
    assert abs(nm["w"] - (K.NAME_RIGHT - K.NAME_LEFT) * n["w"]) < 0.003
    for k, (x, z, w) in K.FRONT.items():
        p = pr[k]
        assert p["kind"] == "front" and p["P0"][1] < -0.1
        assert abs(p["P0"][0] - x) < 1e-6 and abs(p["P0"][2] - z) < 1e-6 and abs(p["w"] - w) < 1e-6
    assert pr["bikewise"]["P0"][0] < 0 < pr["pirelli"]["P0"][0]                  # BikeWise his right, Pirelli left
    assert pr["usn"]["P0"][0] < 0 < pr["cworx"]["P0"][0] and pr["motul"]["P0"][2] < pr["usn"]["P0"][2]
    assert abs(pr["pirelli"]["w"] / pr["pirelli"]["h"] - 476 / 147) < 0.05      # Pirelli's own box


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
        assert p.R[0] > 0.9 and p.U[2] > 0.5                   # reader's right = +x (his left), up = up


def test_logos_are_official_files():
    """Every sponsor's artwork is a file in reference/sponsors with its source URL in the README there."""
    readme = open(os.path.join(K.SPONSORS, "README.md")).read()
    for f in ("bikewise_logo.png", "usn_logo.png", "motul_logo.svg", "pirelli_logo.png",
              "cycleworx_suspension_logo.jpg"):
        assert os.path.exists(os.path.join(K.SPONSORS, f)), f
        line = [ln for ln in readme.splitlines() if f in ln]
        assert line and "https://" in line[0], f


def test_materials_cover_every_part(built):
    body, g = built
    spec = json.loads(str(g["materials"]))
    mats = [str(m) for m in g["mats"]]
    used = {mats[i] for n in g["names"] for i in np.unique(g[str(n) + "__M"])}
    assert {"jersey_print", "pant_print", "pant_iks", "strap", "buckle"} <= used
    for m in used:
        assert 0.0 <= spec[m].get("rough", 0.5) <= 1.0
