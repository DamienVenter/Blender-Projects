"""Calibrated pinhole cameras of Honda's studio photos (left, right, front, rear, top), in the bike's axle-line frame
(metres; x forward, y left, z up, origin on the ground under the rear axle).

Why: the photos are perspective views from raised cameras pitched down at the bike, not flat blueprints.
Evidence (2026-11-10):
  side   the muffler's tail (y = -0.147) sits 48 mm apart between the left and right photos -> distance about 4.7 m;
         the left bar end (y = +0.41, z = 1.217) appears at z 1.225, the footpeg top (spec 422 mm, y = +0.19) at
         about 0.393 and the seat's low point (spec 955 mm) at 0.962 -> camera height about 1.13 m, pitched 5 deg down
  front  six landmarks, least squares (front_camera below): bar ends 1107 px apart at row 252, front tyre top
         (knob tips) row 1014 and bottom row 2062, fender nose tip row 902, fender wing tips 294 px apart
         -> 4.69 m ahead of the front axle, 1.04 m high, 5.3 deg down, f 6954 px, residuals under 11 px
  rear   five landmarks (rear_camera): bar ends 1045 px apart at row 241, rear tyre bottom row 2028, rear axle row
         1537, fender tail edge row 562 -> 5.17 m behind the rear axle, 1.18 m high, 6.2 deg down, f 7652 px,
         residuals under 7 px; check: footpeg tips predicted at columns 1671 and 2329, measured 1673 and 2328
  (first fit, same day, was wrong: it took the red seen under the fender nose for the nose itself. That red is the
   fender's rear flap behind the fork, seen over the tyre. Use more landmarks than unknowns, and look at each one.)
  top    front tyre tip, front and rear fender tips on the centre line, bar ends 949 px apart -> fitted below
All views frame the bike at about 1278 px per metre at its centre.

Use: `CAMS[view].project(P)` -> pixel (u, v) in the 4000x2250 photo; `CAMS[view].on_plane(u, v, axis, value)` -> the
3D point on a plane (e.g. axis 'y', value 0.15) seen at that pixel. `python3 cams.py` refits and prints the cameras.
"""
import json
import math
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "research")
BPS = json.load(open(os.path.join(RES, "bike-blueprint.json")))
W, H = 4000, 2250
TARGET = np.array([0.7527, 0.0, 0.6957])          # where the side photos' centre pixel hits the centre plane
SIDE_DIST = 4.7                                    # m (muffler parallax)
SIDE_HEIGHT = 1.13                                 # m (bar end, footpeg and seat heights in the side photo)
R_REAR = BPS["left"]["rear_tyre_od_mm"] / 2000.0


class Cam:
    def __init__(self, C, F, up_hint, f, roll=0.0, cx=W / 2, cy=H / 2):
        self.C = np.asarray(C, float)
        F = np.asarray(F, float) / np.linalg.norm(F)
        R = np.cross(F, up_hint)
        R /= np.linalg.norm(R)
        U = np.cross(R, F)
        c, s = math.cos(roll), math.sin(roll)
        self.R, self.U, self.F = c * R + s * U, -s * R + c * U, F
        self.f, self.cx, self.cy = float(f), cx, cy

    def project(self, P):
        d = np.atleast_2d(np.asarray(P, float)) - self.C
        dep = d @ self.F
        return np.stack([self.cx + self.f * (d @ self.R) / dep, self.cy - self.f * (d @ self.U) / dep], axis=-1)

    def ray(self, u, v):
        d = self.F + ((np.asarray(u, float) - self.cx) / self.f)[..., None] * self.R \
            + ((self.cy - np.asarray(v, float)) / self.f)[..., None] * self.U
        return d

    def on_plane(self, u, v, axis, value):
        """3D points on the plane {axis = value} seen at pixels (u, v) (arrays)."""
        k = "xyz".index(axis)
        d = self.ray(np.atleast_1d(u), np.atleast_1d(v))
        t = (value - self.C[k]) / d[..., k]
        return self.C + t[..., None] * d

    def to_dict(self):
        return {"C": self.C.tolist(), "R": self.R.tolist(), "U": self.U.tolist(), "F": self.F.tolist(), "f": self.f}


def side_camera(view, dist=SIDE_DIST, height=SIDE_HEIGHT):
    """Left or right profile camera: abeam its target at DIST and HEIGHT; focal length, roll and target are solved so
    that both axles (centre plane, at the rear tyre's radius above the ground) land exactly on their measured
    pixels (bike-blueprint.json)."""
    bp = BPS[view]
    sgn = 1.0 if view == "left" else -1.0
    fa_px, ra_px = np.array(bp["front_axle_px"]), np.array(bp["rear_axle_px"])
    A = np.array([[1.483, 0.0, R_REAR], [0.0, 0.0, R_REAR]])

    def make(p):
        f, roll, tx, tz = p
        C = np.array([tx, sgn * dist, height])
        return Cam(C, np.array([tx, 0.0, tz]) - C, (0, 0, 1.0), f, roll)

    def res(p):
        uv = make(p).project(A)
        return np.concatenate([uv[0] - fa_px, uv[1] - ra_px])
    sol = least_squares(res, [1278.0 * dist, 0.0, TARGET[0], TARGET[2]], x_scale=[1000, 0.01, 0.1, 0.1])
    assert np.abs(sol.fun).max() < 0.01, sol.fun
    return make(sol.x)


def end_camera(sign, f, x, z, pitch):
    """Front (sign +1) or rear (-1) camera on the centre plane, pitched down by PITCH (rad)."""
    return Cam((x, 0.0, z), (-sign * math.cos(pitch), 0.0, -math.sin(pitch)), (0, 0, 1.0), f)


def _tyre(x_axle, radius):
    ang = np.radians(np.arange(0, 360, 0.25))
    return np.stack([x_axle + radius * np.cos(ang), 0 * ang, R_REAR + radius * np.sin(ang)], axis=1)


BAR_END = (0.910, 0.4135, 1.207)                   # left grip's end cap centre. z: cap at rows 454.5 and 455 of the
# side photos. x: the side photos give 0.903 and 0.904, the top photo 0.917 (cap spans columns 1797..1830): the mean,
# +-7 mm. y: bar 827 mm wide (spec; 949 px between the caps' outer points in the top photo is 829 mm)


def front_camera():
    """Front camera fitted to six landmarks of the front photo (pixels measured 2026-11-10, see the module text)."""
    tyre = _tyre(1.483, BPS["left"]["front_tyre_od_mm"] / 2000.0)

    def res(p):
        c = end_camera(1, p[3], p[0], p[1], p[2])
        bars = c.project([BAR_END, (BAR_END[0], -BAR_END[1], BAR_END[2])])
        tv = c.project(tyre)[:, 1]
        wing = c.project([(1.508, 0.100, 0.86), (1.508, -0.100, 0.86)])      # widest point of the fender (top photo)
        return [abs(bars[0, 0] - bars[1, 0]) - 1107.0, bars[:, 1].mean() - 252.0, tv.min() - 1014.0,
                tv.max() - 2062.0, c.project([(1.708, 0, 0.778)])[0, 1] - 902.0, abs(wing[0, 0] - wing[1, 0]) - 294.0]
    sol = least_squares(res, [6.0, 1.0, 0.09, 7000.0], x_scale=[1, 0.3, 0.05, 2000])
    return end_camera(1, sol.x[3], sol.x[0], sol.x[1], sol.x[2]), sol


def rear_camera():
    """Rear camera fitted to five landmarks of the rear photo."""
    tyre = _tyre(0.0, R_REAR)

    def res(p):
        c = end_camera(-1, p[3], p[0], p[1], p[2])
        bars = c.project([BAR_END, (BAR_END[0], -BAR_END[1], BAR_END[2])])
        return [abs(bars[0, 0] - bars[1, 0]) - 1045.0, bars[:, 1].mean() - 241.0, c.project(tyre)[:, 1].max() - 2028.0,
                c.project([(0.0, 0.13, R_REAR)])[0, 1] - 1537.0, c.project([(-0.303, 0, 1.007)])[0, 1] - 562.0]
    sol = least_squares(res, [-4.5, 1.0, 0.09, 6500.0], x_scale=[1, 0.3, 0.05, 2000])
    return end_camera(-1, sol.x[3], sol.x[0], sol.x[1], sol.x[2]), sol


def top_camera():
    """Camera above the centre line looking straight down (image right = toward the rear). Fitted to the centre-line
    landmarks of the top photo: front tyre tip px 844 at (1.8336, 0.3505), rear fender tip px 3187 at (-0.303, 1.007),
    front fender tip px 959 at (1.708, 0.778) (half weight: the tip's height is less certain), and the bar ends
    949 px apart (0.827 m at z 1.217)."""
    land = [((1.8336, 0.3505), 844.0, 1.0), ((-0.303, 1.007), 3187.0, 1.0), ((1.708, 0.778), 959.0, 0.5)]

    def make(p):
        f, xc, h = p
        c = Cam((xc, 0.0, h), (0, 0, -1.0), (0, 1.0, 0), f, cy=1123.0)
        c.R, c.U = np.array([-1.0, 0, 0]), np.array([0, -1.0, 0])       # image right = -x (front at the left),
        # image up = -y: seen from above with the front to the left, the bike's left side is at the bottom (the
        # muffler, on the right, is in the top half of the photo)
        return c

    def res(p):
        c = make(p)
        r = [(c.project((x, 0, z))[0, 0] - px) * w for (x, z), px, w in land]
        uv = c.project([(0.93, 0.4135, 1.217), (0.93, -0.4135, 1.217)])
        r.append((abs(uv[0, 1] - uv[1, 1]) - 949.0))
        return r
    sol = least_squares(res, [13000.0, 0.75, 12.0], x_scale=[3000, 0.1, 3])
    return make(sol.x), sol


def build():
    cams = {"left": side_camera("left"), "right": side_camera("right")}
    cams["front"], _ = front_camera()
    cams["rear"], _ = rear_camera()
    cams["top"], _ = top_camera()
    return cams


CAMS = build()
FILES = {"left": "studio_left-profile_honda-eu-25ym-475600_4000x2250.jpg",
         "right": "studio_right-profile_honda-eu-25ym-475596_4000x2250.jpg",
         "front": "studio_front_honda-eu-25ym-475602_4000x2250.jpg",
         "rear": "studio_rear_honda-eu-25ym-475598_4000x2250.jpg",
         "top": "studio_top_honda-eu-25ym-475594_4000x2250.jpg"}


def linear_to_px(view, x_mm, z_mm):
    """Pixels of the old linear 'image-plane' coordinates (axle-based, used by segment.py windows and the stored
    outlines): the exact inverse of that linear map."""
    bp = BPS[view]
    fa, ra = np.array(bp["front_axle_px"]), np.array(bp["rear_axle_px"])
    s = bp["mm_per_px"]
    u = (fa - ra) / np.linalg.norm(fa - ra)
    v = np.array([-u[1], u[0]]) if bp["front_side"] == "left" else np.array([u[1], -u[0]])
    if v[1] > 0:
        v = -v
    r0 = bp["rear_tyre_od_mm"] / 2
    P = ra + np.outer(np.asarray(x_mm, float) / s, u) + np.outer((np.asarray(z_mm, float) - r0) / s, v)
    return P[:, 0], P[:, 1]


if __name__ == "__main__":
    top, sol = top_camera()
    print("top fit residuals px:", np.round(sol.fun, 1), " f %.0f  x %.3f  height %.2f" % tuple(sol.x))
    for nm, fn in (("front", front_camera), ("rear", rear_camera)):
        c, sl = fn()
        print(f"{nm} fit residuals px:", np.round(sl.fun, 1), " pitch %.2f deg" % math.degrees(math.asin(-c.F[2])))
    for name, c in CAMS.items():
        print(f"{name:6s} C {np.round(c.C, 3)}  f {c.f:.0f}  F {np.round(c.F, 3)}")
    # checks: where known points land in the left photo
    L = CAMS["left"]
    for label, P in (("left bar end", (0.93, 0.4135, 1.217)), ("left footpeg top (spec 422)", (0.556, 0.19, 0.422)),
                     ("seat low point (spec 955)", (0.50, 0.0, 0.955)), ("front tyre contact", (1.483, 0, 0.0)),
                     ("rear tyre contact", (0.0, 0, 0.0))):
        u, v = L.project(P)[0]
        print(f"   {label:28s} -> px ({u:7.1f}, {v:7.1f})")
    json.dump({k: c.to_dict() for k, c in CAMS.items()}, open(os.path.join(RES, "bike-cameras.json"), "w"), indent=1)
