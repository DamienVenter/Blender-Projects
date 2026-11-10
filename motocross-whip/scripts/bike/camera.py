"""The studio photos' camera: perspective, not orthographic.

Evidence (2026-11-10): the muffler's rear end (0.15 m right of the centre plane) is at x = 8 mm in the left profile
photo and at x = -40 mm in the right one. A camera on the bike's side at distance D, aimed at the image centre, scales
a point at lateral position y by D / (D - y) about the image centre (y toward that camera). The 48 mm gives
D = 4.8 m; `calibrate()` refines D by maximising the overlap of right-side parts with the left photo.

All blueprint coordinates (outlines, grids) are "image-plane" values: true only for points on the centre plane
(y = 0, where the axles calibrate the scale). `unproject` gives the true position of a point seen at image-plane
(x_i, z_i) when its lateral position y is known; `project` is the inverse (used to draw the model like the photo).
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BPS = json.load(open(os.path.join(HERE, "..", "..", "research", "bike-blueprint.json")))
D_CAM = float(os.environ.get("BIKE_DCAM", 4.8))     # m, camera to the bike's centre plane (see above)


def centre(view):
    """Bike coordinates (x, z in metres, axle-line frame) of the photo's centre (the optical axis)."""
    bp = BPS[view]
    fa, ra = np.array(bp["front_axle_px"]), np.array(bp["rear_axle_px"])
    s = bp["mm_per_px"] / 1000.0
    u = (fa - ra) / np.linalg.norm(fa - ra)
    v = np.array([-u[1], u[0]]) if bp["front_side"] == "left" else np.array([u[1], -u[0]])
    if v[1] > 0:
        v = -v
    c = np.array(bp["size_px"], float) / 2 - ra
    return float(c @ u * s), float(c @ v * s + bp["rear_tyre_od_mm"] / 2000.0)


def _k(view, y, d):
    yc = np.asarray(y, float) if view == "left" else -np.asarray(y, float)      # toward that photo's camera
    return d / (d - yc)


def project(view, x, y, z, d=None):
    """True (x, y, z) -> image-plane (x_i, z_i)."""
    d = D_CAM if d is None else d
    xc, zc = centre(view)
    k = _k(view, y, d)
    return xc + (np.asarray(x, float) - xc) * k, zc + (np.asarray(z, float) - zc) * k


def unproject(view, xi, zi, y, d=None):
    """Image-plane (x_i, z_i) of a point whose lateral position is y -> true (x, z)."""
    d = D_CAM if d is None else d
    xc, zc = centre(view)
    k = _k(view, y, d)
    return xc + (np.asarray(xi, float) - xc) / k, zc + (np.asarray(zi, float) - zc) / k
