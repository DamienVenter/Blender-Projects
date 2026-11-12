"""Checks of the bike model against Honda's studio photos. Run before any render of the bike:

    python3 -m pytest -q test_bike.py          (about 2 minutes: the parts are built and drawn through all five cameras)

What is locked in here (plastics pass and detail pass, 2026-11-10):
  cameras    each photo's camera fits its landmarks; the rear camera predicts the footpeg tips it was not fitted to
  agreement  the top and front photos give the same shroud width
  exactness  a photo panel's side view is the photo's outline
  scores     overlap with every photo is not allowed to fall below what this pass reached
  intruders  nothing shows through the plastics in the profiles
"""
import json
import math
import os
import sys

import numpy as np
import pytest
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams               # noqa: E402
import compare            # noqa: E402
import parts              # noqa: E402
import plastics           # noqa: E402


@pytest.fixture(scope="module")
def npz(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("bike") / "parts.npz")
    parts.save(parts.build(), path)
    return path


@pytest.fixture(scope="module")
def scores(npz, tmp_path_factory):
    prefix = str(tmp_path_factory.mktemp("cmp") / "cmp")
    compare.score(npz, prefix)
    return json.load(open(prefix + "_scores.json"))


# ---------------------------------------------------------------- cameras
def test_side_cameras_put_both_axles_on_their_pixels():
    for view in ("left", "right"):
        bp = cams.BPS[view]
        uv = cams.CAMS[view].project([(1.483, 0.0, cams.R_REAR), (0.0, 0.0, cams.R_REAR)])
        assert np.abs(uv[0] - bp["front_axle_px"]).max() < 0.05
        assert np.abs(uv[1] - bp["rear_axle_px"]).max() < 0.05


def test_front_and_rear_cameras_fit_more_landmarks_than_unknowns():
    cf, sf = cams.front_camera()
    cr, sr = cams.rear_camera()
    assert len(sf.fun) > 4 and len(sr.fun) > 4                    # four unknowns each
    assert np.abs(sf.fun).max() < 12.0, sf.fun                    # px (the tyre's knob tips are the loosest)
    assert np.abs(sr.fun).max() < 8.0, sr.fun


def test_end_cameras_belong_to_one_rig():
    """All four cameras round the bike stand about 1.1 m high and look 5 to 7 degrees down."""
    for view in ("front", "rear"):
        c = cams.CAMS[view]
        assert 0.95 < c.C[2] < 1.25
        assert 4.5 < math.degrees(math.asin(-c.F[2])) < 7.2
    for view in ("left", "right"):
        assert 4.5 < math.degrees(math.asin(-cams.CAMS[view].F[2])) < 6.0


def test_rear_camera_predicts_the_footpeg_tips():
    """Not used in the fit: tips measured at columns 1673 and 2328 of the rear photo (y from the top photo)."""
    uv = cams.CAMS["rear"].project([(0.556, 0.248, 0.41), (0.556, -0.248, 0.41)])
    assert abs(uv[0, 0] - 1673.0) < 6.0 and abs(uv[1, 0] - 2328.0) < 6.0


def test_front_camera_puts_the_tyre_top_above_the_flap_edge():
    """The landmark that was misread: the front tyre's top must show ABOVE row 1030 (the fender flap's lower edge),
    so that the knobs stand in front of the flap as they do in the photo."""
    ang = np.radians(np.arange(0, 360, 0.5))
    rf = cams.BPS["left"]["front_tyre_od_mm"] / 2000.0
    tyre = np.stack([1.483 + rf * np.cos(ang), 0 * ang, cams.R_REAR + rf * np.sin(ang)], axis=1)
    assert cams.CAMS["front"].project(tyre)[:, 1].min() < 1030.0


# ---------------------------------------------------------------- agreement between photos
def test_shroud_width_agrees_between_top_and_front_photos():
    """Top photo: plan envelope at the shroud's widest. Front photo (rows 704..776): 0.200 m either side."""
    for side in (1, -1):
        w = plastics._shroud_plan(side)(1.08)
        assert abs(w - 0.200) < 0.004, w


def test_shroud_skin_edge_is_the_same_on_both_sides():
    a = np.array(plastics.OUT["shroud_skin"])
    b = np.array(plastics.OUT["shroud_skin_R"])
    za = np.linspace(700, 860, 17)
    xa = np.interp(za, a[::-1, 1], a[::-1, 0])
    xb = np.interp(za, b[::-1, 1], b[::-1, 0])
    assert np.median(np.abs(xa - xb)) < 4.0                       # mm


def test_fork_guards_sit_inboard_of_the_tubes():
    assert abs(parts.FORK_HALF - 0.099) < 0.002
    assert 27.0 < math.degrees(parts.RAKE + parts.GROUND_PITCH) < 28.0        # Honda: 27 deg 33 min


# ---------------------------------------------------------------- photo panels
def test_shroud_side_view_is_the_photo_outline(npz):
    """The shroud drawn through the left camera covers its extracted outline (and nothing else)."""
    data = np.load(npz)
    names = [str(n) for n in data["names"]]
    part = compare.raster(npz, None, "left", by_part=True)
    # the shroud is partly behind the fork and cables in the model as in the photo: test where it is in front
    poly = np.array(plastics.OUT["shroud"])
    u, v = cams.linear_to_px("left", poly[:, 0], poly[:, 1])
    im = Image.new("L", (cams.W // 2, cams.H // 2), 0)
    ImageDraw.Draw(im).polygon([(float(x) / 2, float(y) / 2) for x, y in zip(u, v)], fill=1)
    tgt = np.asarray(im) > 0
    mine = np.isin(part, [names.index(n) + 1 for n in ("shrouds", "shroud_decks")])
    other_in_front = tgt & ~mine & (part > 0)
    covered = (tgt & mine).sum() / max((tgt & ~other_in_front).sum(), 1)
    spill = (mine & ~tgt).sum() / max(mine.sum(), 1)
    assert covered > 0.975, covered          # the outline is smoothed over 4 mm before the panel is cut
    assert spill < 0.03, spill


def test_number_plate_has_no_slit_on_the_centre_line(npz):
    """The plate's outline is ordered without a fold: the centre column shows plate from top to bottom."""
    data = np.load(npz)
    names = [str(n) for n in data["names"]]
    part = compare.raster(npz, None, "front", by_part=True)
    col = part[330 // 2:560 // 2, 1999 // 2]
    ok = np.isin(col, [names.index(n) + 1 for n in ("number_plate", "cables", "bars")])
    assert ok.mean() > 0.97, ok.mean()


# ---------------------------------------------------------------- scores and intruders
FLOORS = {"left": (0.87, 0.89), "right": (0.86, 0.885), "front": (0.87, 0.79), "rear": (0.885, 0.62), "top": (0.865, 0.855)}


@pytest.mark.parametrize("view", list(FLOORS))
def test_overlap_with_each_photo_does_not_fall(scores, view):
    sil, red = FLOORS[view]
    assert scores[view]["silhouette"] >= sil, scores[view]
    assert scores[view]["red"] >= red, scores[view]


def test_nothing_shows_through_the_plastics(npz):
    found = compare.intruders(npz, min_cm2=2.0)
    # the side panel's air intake is a real dark opening inside its outline
    found = {k: a for k, a in found.items() if k[1] != "side_panels"}
    assert not found, found


# ---------------------------------------------------------------- Honda's spec sheet (research/crf250r-2026.md)
def _ground(npz):
    """Every part's vertices on the ground (the parts are built in the axle-line frame, tilted nose-up and lifted)."""
    d = np.load(npz)
    return {n: parts.to_ground(d[f"{n}__V"]) for n in [str(q) for q in d["names"]]}


def test_overall_dimensions_against_the_spec_sheet(npz):
    G = _ground(npz)
    allv = np.vstack(list(G.values()))
    assert abs(allv[:, 2].min()) < 0.002                                   # both tyres stand on the ground
    # length 2179: wheelbase + both tyre radii at the knob tips (2176)
    assert abs(np.ptp(allv[:, 0]) - 2.179) < 0.006
    # height 1262. The bar's own top (1.256) sits on the front photo's bar edge (test below); the throttle hood and
    # the brake reservoir stand higher in the photos (1.274, 1.271), as the photo bike stands high elsewhere (seat +20,
    # belly +15). Accept the spec within -8 / +15 mm (2026-11-11)
    top = max(G[n][:, 2].max() for n in ("bars", "hand_controls") if n in G)
    assert G["bars"][:, 2].max() > 1.262 - 0.008 and top < 1.262 + 0.015
    # ground clearance 330. The belly's lowest outline in both side photos is 333 to 335 if it is on the centre line
    # and 346 to 348 if it is the near cradle rail, as modelled: up to 18 mm over the spec sheet
    low = np.vstack([G[n] for n in ("frame", "engine", "exhaust")])
    assert 0.330 <= low[(low[:, 0] > 0.55) & (low[:, 0] < 1.0)][:, 2].min() < 0.350


def test_seat_height_against_the_spec_sheet(npz):
    """955 mm in the spec; the seat of the studio photos, which the model follows, is 20 mm higher."""
    d = np.load(npz)
    V = d["seat__V"].astype(float)
    xs = np.round(V[:, 0] / 0.005)          # 5 mm bins: the seat is no longer a loft with stations (2026-11-11)
    top = np.array([V[xs == x][np.argmax(V[xs == x][:, 2])] for x in np.unique(xs)])
    zg = parts.to_ground(top)[:, 2]
    m = (top[:, 0] > 0.25) & (top[:, 0] < 0.70)
    assert 0.955 <= zg[m].min() < 0.980, zg[m].min()


def test_overall_width_against_the_spec_sheet(npz):
    G = _ground(npz)
    assert abs(np.ptp(G["bars"][:, 1]) - 0.827) < 0.008


def test_a_plugin_cannot_silently_replace_another_plugins_part(monkeypatch):
    """2026-11-11: two modules named a part `rear_brake` and the later one silently dropped the other's pedal."""
    import types
    a = types.SimpleNamespace(__name__="mod_a", PARTS={"thing": lambda: parts.Mesh()}, MATERIALS={"m": dict(rgb=(1, 2, 3))})
    b = types.SimpleNamespace(__name__="mod_b", PARTS={"thing": lambda: parts.Mesh()})
    monkeypatch.setattr(parts, "plugins", lambda: [a, b])
    with pytest.raises(ValueError, match="would replace mod_a"):
        parts.build()
    c = types.SimpleNamespace(__name__="mod_c", PARTS={}, MATERIALS={"m": dict(rgb=(9, 9, 9))})
    monkeypatch.setattr(parts, "plugins", lambda: [a, c])
    with pytest.raises(ValueError, match="material 'm'"):
        parts.build()


def test_bar_top_edge_on_the_front_photo(npz):
    """The bar's upper edge, drawn through the front camera, lies on the photo's where nothing stands above it
    (measured 2026-11-11: 0.4, 0.0, -0.1, -2.7, -1.1 px; at the other columns the controls and cables stand higher)."""
    d = np.load(npz)
    V = d["bars__V"].astype(float)
    c = cams.CAMS["front"]
    ref = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")
    im = np.asarray(Image.open(os.path.join(ref, cams.FILES["front"])).convert("L")).astype(int)
    uv = c.project(V)
    u = np.round(uv[:, 0]).astype(int)
    for yb in (0.18, 0.22, 0.34, -0.30, -0.34):
        m = np.abs(V[:, 1] - yb) < 0.004
        uc = int(np.median(u[m]))
        top = uv[m & (np.abs(u - uc) <= 2), 1].min()
        col = im[int(top) - 60:int(top) + 40, uc - 1:uc + 2].mean(1)
        photo = int(top) - 60 + np.where(col < 170)[0].min()
        assert abs(photo - top) < 4, (yb, photo, top)


def test_the_see_through_check_still_sees_a_missing_fender(npz, tmp_path):
    """The check looks only where the photo shows red (2026-11-11): it must still catch a plastic that is missing."""
    d = dict(np.load(npz, allow_pickle=True))
    names = [str(n) for n in d["names"]]
    out = {k: v for k, v in d.items() if not k.startswith("rear_fender__")}
    out["names"] = np.array([n for n in names if n != "rear_fender"])
    p = str(tmp_path / "nofender.npz")
    np.savez(p, **out)
    found = compare.intruders(p, min_cm2=2.0)
    assert found.get(("left", "(hole: background shows)"), 0) > 40
    assert found.get(("right", "(hole: background shows)"), 0) > 40


def test_viewer_split_cuts_a_mesh_too_big_for_one_file():
    """glb2json: a mesh over the per-file budget is cut by primitives onto child nodes (2026-11-12, rear wheel)."""
    import glb2json
    doc = {"nodes": [{"name": "wheel", "mesh": 0}], "meshes": [{"name": "wheel", "primitives": []}],
           "accessors": [], "bufferViews": []}
    for k in range(3):                                      # three primitives of 4 MB each
        doc["bufferViews"].append({"buffer": 0, "byteOffset": 0, "byteLength": 4_000_000})
        doc["accessors"].append({"bufferView": k, "count": 1, "type": "VEC3", "componentType": 5126})
        doc["meshes"][0]["primitives"].append({"attributes": {"POSITION": k}})
    glb2json.split_big_meshes(doc, 9_000_000)
    assert [len(m["primitives"]) for m in doc["meshes"]] == [2, 1]
    assert doc["nodes"][0]["children"] == [1] and doc["nodes"][1] == {"name": "wheel_2", "mesh": 1}
