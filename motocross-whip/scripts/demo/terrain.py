"""Jump profile along the jump line (X forward, Z up) and wheel-centre contact curves.

The profile is a single-valued height z(X) sampled every DX. A wheel of radius r
touches the ground when its centre reaches the morphological dilation of the
profile by a disc of radius r ("offset curve"). That handles concave
transitions, the convex lip edge and the landing knuckle exactly.
"""
import math
import numpy as np
import params as P

DX = 0.005
X0, X1 = -120.0, 110.0


def build_profile():
    th = math.radians(P.LIP_ANGLE_DEG)
    R = P.RAMP_RADIUS
    H = P.LIP_HEIGHT
    Ls = (H - R * (1 - math.cos(th))) / math.sin(th)
    if Ls < -1e-9:
        raise ValueError("ramp radius too large for lip height and angle")
    Ls = max(Ls, 0.0)
    xs_straight = -Ls * math.cos(th)
    xb = xs_straight - R * math.sin(th)          # bottom tangent point of the transition

    al = math.radians(P.LANDING_ANGLE_DEG)
    Hk, Rk, Rb = P.KNUCKLE_HEIGHT, P.KNUCKLE_RADIUS, P.LANDING_BOTTOM_RADIUS
    xk = P.GAP
    x_deck0 = xk - P.DECK_LENGTH
    x_back0 = x_deck0 - Hk / math.tan(math.radians(P.BACK_FACE_ANGLE_DEG))
    p1x, p1z = xk + Rk * math.sin(al), Hk - Rk * (1 - math.cos(al))
    if p1z <= Rb * (1 - math.cos(al)):
        raise ValueError("landing too low for the bottom transition radius")
    xc_b = p1x + Rb * math.sin(al) + (p1z - Rb * (1 - math.cos(al))) / math.tan(al)
    q_x = xc_b - Rb * math.sin(al)

    xs = np.arange(X0, X1 + DX / 2, DX)
    zs = np.zeros_like(xs)
    # ramp transition (arc) and straight
    m = (xs >= xb) & (xs < xs_straight)
    zs[m] = R - np.sqrt(np.maximum(R * R - (xs[m] - xb) ** 2, 0.0))
    m = (xs >= xs_straight) & (xs <= 0.0)
    zs[m] = H + xs[m] * math.tan(th)
    # landing back face, deck, knuckle rounding, downslope, bottom transition
    m = (xs >= x_back0) & (xs < x_deck0)
    zs[m] = (xs[m] - x_back0) * math.tan(math.radians(P.BACK_FACE_ANGLE_DEG))
    m = (xs >= x_deck0) & (xs < xk)
    zs[m] = Hk
    m = (xs >= xk) & (xs < p1x)
    zs[m] = (Hk - Rk) + np.sqrt(np.maximum(Rk * Rk - (xs[m] - xk) ** 2, 0.0))
    m = (xs >= p1x) & (xs < q_x)
    zs[m] = p1z - (xs[m] - p1x) * math.tan(al)
    m = (xs >= q_x) & (xs < xc_b)
    zs[m] = Rb - np.sqrt(np.maximum(Rb * Rb - (xs[m] - xc_b) ** 2, 0.0))

    keys = {"ramp_bottom": xb, "ramp_straight": xs_straight, "lip": 0.0,
            "landing_back_foot": x_back0, "deck_start": x_deck0, "knuckle": xk,
            "downslope_start": p1x, "downslope_end": q_x, "landing_bottom": xc_b,
            "straight_len": Ls, "downslope_len": (q_x - p1x) / math.cos(al)}
    return xs, zs, keys


def dilate(xs, zs, r):
    """Wheel-centre height for a wheel of radius r at every X sample."""
    k = int(math.ceil(r / DX))
    out = zs + r
    for j in range(-k, k + 1):
        dx = j * DX
        if abs(dx) > r:
            continue
        lift = math.sqrt(r * r - dx * dx)
        shifted = np.full_like(zs, -1e9)
        if j > 0:
            shifted[:-j] = zs[j:]
        elif j < 0:
            shifted[-j:] = zs[:j]
        else:
            shifted = zs
        np.maximum(out, shifted + lift, out=out)
    return out


class Terrain:
    def __init__(self):
        self.xs, self.zs, self.keys = build_profile()
        self.off = {"front": dilate(self.xs, self.zs, P.R_FRONT), "rear": dilate(self.xs, self.zs, P.R_REAR)}
        self.slope = {k: np.gradient(v, DX) for k, v in self.off.items()}

    def ground(self, x):
        return float(np.interp(x, self.xs, self.zs))

    def centre(self, wheel, x):
        """Wheel-centre contact height and unit surface normal at X."""
        i = (x - X0) / DX
        i0 = int(i)
        f = i - i0
        z = self.off[wheel][i0] * (1 - f) + self.off[wheel][i0 + 1] * f
        s = self.slope[wheel][i0] * (1 - f) + self.slope[wheel][i0 + 1] * f
        n = 1.0 / math.sqrt(1 + s * s)
        return z, (-s * n, n)


if __name__ == "__main__":
    t = Terrain()
    for k, v in t.keys.items():
        print(f"{k:18s} {v:8.3f}")
    print("lip height", t.ground(-1e-3), "knuckle", t.ground(P.GAP))
