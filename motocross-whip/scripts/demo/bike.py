"""Bike geometry and mass properties (bike frame: u forward, v left, w up; metres)."""
import numpy as np
import params as P

# Characteristic box sizes (lu, lv, lw) per mass part, for self inertia (EST)
_SIZES = {
    "front_wheel": None, "rear_wheel": None,
    "fork_clamps_bars": (0.15, 0.80, 0.80),
    "engine": (0.40, 0.30, 0.40),
    "frame": (0.90, 0.25, 0.60),
    "swingarm_linkage_shock": (0.60, 0.25, 0.20),
    "fuel_and_tank": (0.35, 0.30, 0.20),
    "radiators_coolant": (0.10, 0.45, 0.30),
    "exhaust": (0.70, 0.12, 0.15),
    "seat_plastics_subframe_airbox": (1.00, 0.30, 0.30),
    "electrics_misc": (0.30, 0.20, 0.20),
    "chain_sprockets_brakes": (1.20, 0.15, 0.30),
}


def mass_properties():
    """Mass, CoM (u, v, w) and inertia tensor about the CoM, bike frame.

    Wheel spin is NOT in this tensor's spin axis term beyond the rigid ring;
    spin angular momentum is added separately in the air model.
    """
    M = sum(p[1] for p in P.BIKE_MASS_PARTS)
    pos = {p[0]: np.array([p[2], 0.0, p[3]]) for p in P.BIKE_MASS_PARTS}
    com = sum(p[1] * pos[p[0]] for p in P.BIKE_MASS_PARTS) / M
    I = np.zeros((3, 3))
    for name, m, u, w in P.BIKE_MASS_PARTS:
        d = pos[name] - com
        I += m * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
        if name == "front_wheel":
            Is = P.WHEEL_SPIN_INERTIA_FRONT
            I += np.diag([Is / 2, Is, Is / 2])
        elif name == "rear_wheel":
            Is = P.WHEEL_SPIN_INERTIA_REAR
            I += np.diag([Is / 2, Is, Is / 2])
        else:
            lu, lv, lw = _SIZES[name]
            I += np.diag([m * (lv**2 + lw**2) / 12, m * (lu**2 + lw**2) / 12, m * (lu**2 + lv**2) / 12])
    return M, com, I


def fork_axis():
    """Unit vector from the front axle up the fork (compression direction), bike frame 2D (u, w)."""
    r = np.radians(P.RAKE_DEG)
    return np.array([-np.sin(r), np.cos(r)])


SWINGARM_LEN = float(np.hypot(P.REAR_AXLE[0] - P.SWINGARM_PIVOT[0], P.REAR_AXLE[1] - P.SWINGARM_PIVOT[1]))
SWINGARM_ANGLE0 = float(np.arctan2(P.REAR_AXLE[1] - P.SWINGARM_PIVOT[1], P.REAR_AXLE[0] - P.SWINGARM_PIVOT[0]))


def rear_axle_at(s):
    """Rear axle (u, w) at wheel travel s (arc length at the axle); positive s raises the axle."""
    a = SWINGARM_ANGLE0 - s / SWINGARM_LEN     # axle is behind the pivot: angle near pi, rising = decreasing
    return np.array([P.SWINGARM_PIVOT[0] + SWINGARM_LEN * np.cos(a), P.SWINGARM_PIVOT[1] + SWINGARM_LEN * np.sin(a)])


def rear_travel_dir(s):
    """Unit direction the rear axle moves under compression at travel s (bike frame 2D)."""
    a = SWINGARM_ANGLE0 - s / SWINGARM_LEN
    return np.array([np.sin(a), -np.cos(a)])


def front_axle_at(s):
    return np.array(P.FRONT_AXLE) + fork_axis() * s


if __name__ == "__main__":
    M, com, I = mass_properties()
    print(f"bike mass {M:.1f} kg  CoM {np.round(com, 3)}  inertia diag {np.round(np.diag(I), 2)}")
    print(f"swingarm length {SWINGARM_LEN:.3f} m, angle {np.degrees(SWINGARM_ANGLE0):.1f} deg")
    for s in (0.0, 0.1, 0.318):
        print(f"rear axle at s={s:.3f}: {np.round(rear_axle_at(s), 4)} dir {np.round(rear_travel_dir(s), 3)}")
    print("front weight share (bike alone):", round(com[0] / P.WHEELBASE, 3))
