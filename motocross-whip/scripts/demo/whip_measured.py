"""Damien's whip, measured frame by frame from his clips (research/whip-attitude-measured.md).

Method: the bike (and a stick rider) is drawn at a trial world attitude, seen from a camera placed like
Damien's (clip 1 shot A: about 25 m behind the lip, 1.5 m high, 1600 px focal length), next to the real
frame; the attitude is adjusted until the two match (scripts/analysis/attitude_overlay.py). Wheel ellipses
(round = side-on, a line = edge-on), the in-image angle of the axle line and which side the rider sits on
fix the three angles. Clip 1 shot B (front camera at the bottom of the landing) confirms the peak and
gives the straighten and touchdown timing.

Times are seconds after the rear wheel leaves the lip on Damien's jump (lip = clip 1 frame 30, 30 fps,
touchdown about 2.05 s). The simulation scales them to its own airtime.

Bike attitude, degrees, composed about WORLD axes (x along the jump, y to the rider's left, z up):
    R = Rx(drop) . Rz(yaw) . Ry(-pitch) . Rx(roll)
  roll  : lay-down about the bike's long axis (left lay-down negative)
  pitch : nose up positive
  yaw   : nose to the rider's left positive (rear wheel out to his right)
  drop  : the whole bike turned about the travel direction; with the bike fully sideways (yaw 90) this is
          the nose dropping, seen from behind as the bike rotating from horizontal to hanging nose-down.
rider_roll: Damien's torso lean seen from behind (head to his left negative), facing forward.
"""
import numpy as np

T_DAMIEN = 2.20          # s, lip to touchdown: shot A still shows the bike crossed up at 2.00 s, just before he
                         # drops behind the knuckle (2.03 s); touchdown follows (clip analysis said 2.0 to 2.2 s)
STRAIGHTEN = 0.18        # s to pull the bike straight (shot B f148 to f154, front view: crossed up to straight)
T_STRAIGHT = 1.90        # s, default start of the straighten (shot A: still crossed up at 1.97 s; shot B, a
                         # possibly different jump: straight 0.2 s before touchdown). Free within T_STRAIGHT_RANGE.
T_STRAIGHT_RANGE = (1.78, 1.97)
TAKEOFF = "takeoff"      # pitch at the lip comes from the ground simulation
LANDING = "landing"      # pitch at touchdown comes from the landing slope

#        t      drop   yaw   pitch     roll  rider_roll  source (clip 1 shot A frame, lip = f30)
KEYS = [
    (0.00,   0.0,   0.0, TAKEOFF,    0.0,    0.0, "f30: rear wheel leaves the lip"),
    (0.13,   0.0,  40.0,  38.0,    -35.0,  -25.0, "f34: rear wheel swinging out right, bike leaning left"),
    (0.23,   0.0,  60.0,  28.0,    -65.0,  -45.0, "f37: diagonal, rear wheel low right seen as an ellipse"),
    (0.33,   0.0,  90.0,   5.0,    -90.0,  -65.0, "f40: flat and fully sideways, wheels edge-on, rider horizontal"),
    (0.43,   0.0,  90.0,   0.0,    -90.0,  -70.0, "f43: held flat, level"),
    (0.53, -15.0,  90.0,   0.0,    -80.0,  -60.0, "f46: rear starts to rise, still flat"),
    (0.63, -30.0,  90.0,   0.0,    -75.0,  -50.0, "f49: axle line 32 deg"),
    (0.73, -41.0,  90.0,   0.0,    -70.0,  -45.0, "f52: axle line 41 deg, still mostly flat"),
    (0.83, -56.0,  90.0,   0.0,    -55.0,  -30.0, "f55: axle line 56 deg, front wheel becoming visible"),
    (0.93, -70.0,  90.0,   0.0,    -45.0,  -15.0, "f58: front wheel ellipse about 0.6 round"),
    (1.03, -78.0,  90.0,   0.0,    -30.0,  -10.0, "f61: hanging nose-down"),
    (1.13, -78.0,  90.0,   0.0,    -15.0,   -5.0, "f64: profile, front wheel nearly round"),
    (1.33, -75.0,  90.0,   0.0,      0.0,    0.0, "f70: full profile, rider upright"),
    (1.53, -58.0,  90.0,   0.0,      0.0,    0.0, "f76: nose coming up, still fully crossed up"),
    (1.73, -30.0,  90.0,   0.0,      0.0,    0.0, "f82: axle line 29 deg"),
    (1.87, -32.0,  90.0,   0.0,      0.0,    0.0, "f86: still crossed up, axle line 32 deg"),
    (1.97, -32.0,  90.0,   0.0,      0.0,    0.0, "f89: still crossed up as he drops toward the knuckle"),
]
END_KEYS = [  # appended after the straighten starts (times relative to it, and to touchdown)
    ("straight", 0.0, 4.0, LANDING, 0.0, 0.0, "shot B f154: pulled straight, small residual angle"),
    ("touchdown", 0.0, 0.0, LANDING, 0.0, 0.0, "shot B f160: touchdown, front wheel marginally first"),
]

FIELDS = ("t", "drop", "yaw", "pitch", "roll", "rider_roll")


def table(takeoff_pitch, landing_pitch, t_straight=T_STRAIGHT, t_land=T_DAMIEN):
    """Numeric key table (n x 6) on Damien's timeline: the measured keys up to the start of the straighten
    (held value at that instant), then straight and touchdown keys."""
    fill = lambda p: takeoff_pitch if p == TAKEOFF else landing_pitch if p == LANDING else p
    meas = np.array([[k[0], k[1], k[2], fill(k[3]), k[4], k[5]] for k in KEYS], float)
    rows = [r for r in meas if r[0] < t_straight - 1e-6]
    hold = [t_straight] + [float(np.interp(t_straight, meas[:, 0], meas[:, j])) for j in range(1, 6)]
    rows.append(hold)
    t_ok = min(t_straight + STRAIGHTEN, t_land - 0.02)
    for (name, d, y, p, r, rr, _), t in zip(END_KEYS, (t_ok, t_land)):
        rows.append([t, d, y, fill(p), r, rr])
    return np.array(rows, float)


def params_at(t, tab, pitch_rate0=0.0, pitch_rate1=0.0, yaw_rate0=0.0, roll_rate0=0.0):
    """Interpolated (drop, yaw, pitch, roll, rider_roll) in degrees at times t (s, the table's timeline).
    Monotone cubic (pchip) per parameter: no overshoot between the measured keys. Start slopes (deg/s): pitch at
    the takeoff rotation rate, yaw and roll at the lip kick rates; end slopes at rest (pitch: pitch_rate1)."""
    import air
    t = np.clip(np.asarray(t, float), tab[0, 0], tab[-1, 0])
    m0 = {2: yaw_rate0, 3: pitch_rate0, 4: roll_rate0}
    out = []
    for j in range(1, 6):
        out.append(air.pchip(tab[:, 0], tab[:, j], t, m0=m0.get(j, 0.0), m1=pitch_rate1 if j == 3 else 0.0))
    return out


def attitude(drop, yaw, pitch, roll):
    """Bike rotation matrix from the measurement angles (degrees)."""
    import air
    d = np.radians
    return air.Rx(d(drop)) @ air.Rz(d(yaw)) @ air.Ry(-d(pitch)) @ air.Rx(d(roll))
