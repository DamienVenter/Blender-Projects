"""Convert simulation records into Blender keyframe data (frames.json, scene.json, summary.json)."""
import json
import math
import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator

import params as P
import bike as B
import rider as RD
import air
from air import Rz, Ry, Rx
from pose import Poser, quat_from_matrix, matrix_from_quat as R_of_quat

FPS = 120
LEAD, TAIL = 2.2, 2.4          # seconds shown before the lip and after touchdown
LOOK_AHEAD = 10.0              # m: how far up the track he looks once the landing is reached
PREROLL = 0.5                  # s posed before the first shown frame, so the elbow, knee and head memory has settled
# Joins between the simulations (record sets that do not meet exactly) are made continuous in value, rate and
# curvature. Per channel: which side is bent onto the other ("before": the earlier records anticipate the later ones;
# "after": inertialization, the later records start where the earlier ones were going) and over how long (s).
LIP_T = 0.20                   # s on the lip in which the whip is started (bike turns, rider moves into the air posture)
LIP_PLAN_RIDER = {k: ("before", LIP_T) for k in ("RA", "R_rel", "o_rel", "spine", "crouch", "look")}
LIP_PLAN_BIKE = {
            # bike position: the ramp holds the rear tyre up as the bike pitches up on the lip (export lifts it to
            # the ramp surface), so it leaves the lip higher than the straight-bike simulation; the flight takes off
            # from there and settles onto the physics centre-of-mass path (rate jump over 0.15 s, height over 0.8 s)
            "pb": ("after", 0.80, 0.15)}
LAND_PLAN = {k: ("after", 0.12) for k in list(LIP_PLAN_RIDER) + list(LIP_PLAN_BIKE)}


JOIN_ORDER = 3       # a join matches value, rate and acceleration (matching the jerk too gave no visible gain)


def _fade_basis(n=JOIN_ORDER):
    """Polynomials f_k (k < n) of degree 2n - 1 on [0, 1]: f_k^(m)(0) = 1 if m == k else 0 and f_k^(m)(1) = 0, for
    m < n. An offset sum_k d_k T^k f_k(s / T) removes jumps d_0 (value), d_1 (rate), d_2 (acceleration) over the
    time T and leaves the joined curve continuous in all of them (n = 3: the quintic smootherstep family)."""
    deg = 2 * n - 1
    basis = []
    for k in range(n):
        c = np.zeros(deg + 1)
        c[k] = 1.0 / math.factorial(k)
        A = np.array([[math.factorial(j) / math.factorial(j - m) if j >= m else 0.0 for j in range(n, deg + 1)]
                      for m in range(n)])
        rhs = -np.array([sum(c[j] * math.factorial(j) / math.factorial(j - m) for j in range(m, n)) for m in range(n)])
        c[n:] = np.linalg.solve(A, rhs)
        basis.append(np.polynomial.Polynomial(c))
    return basis


FADE = _fade_basis()


def fade(tau):
    tau = min(max(tau, 0.0), 1.0)
    return [float(f(tau)) for f in FADE]


CHANNELS_ROT = ("RA", "R_rel")                                   # blended as rotations (world / bike frame)


def _side_state(D, idx, key, rot, tj):
    """Value and its first JOIN_ORDER - 1 time derivatives of a driver channel at tj, from a polynomial through the
    JOIN_ORDER records idx (nearest first). Rotations are handled in the tangent space of the nearest record
    (world-frame rotation vectors), so the derivatives are angular velocity and acceleration."""
    n = JOIN_ORDER
    recs = [D[i] for i in idx[:n]]
    t = np.array([r["t"] for r in recs]) - tj
    base = recs[0][key]
    Y = np.array([air.logm_so3(r[key] @ base.T) if rot else np.asarray(r[key], float) for r in recs])
    C = np.linalg.solve(np.vander(t, n, increasing=True), Y.reshape(n, -1)).reshape((n,) + Y.shape[1:])
    out = [C[k] * math.factorial(k) for k in range(n)]
    if rot:
        out[0] = air.expm_so3(out[0]) @ base
    return out


def blend_join(D, tj, plan, later):
    """Remove the jump in value, rate and acceleration of the driver channels where two simulations meet at tj.

    plan: {channel: (side, T[, T_rate])}. side "before": the records in the T before tj are bent onto the ones
    after (anticipation). side "after": the records in the T after tj start from where the earlier ones were going
    and settle onto their own values (inertialization). The value jump fades over T, the rate and acceleration
    jumps over T_rate (default T), each with a fade from _fade_basis: the joined curve is continuous in value, rate
    and acceleration. later: the record kinds of the later simulation.
    Returns the jumps removed: {channel: (value jump, rate jump, acceleration jump)}."""
    before = [i for i, d in enumerate(D) if d["kind"] not in later]
    after = [i for i, d in enumerate(D) if d["kind"] in later]
    if len(before) < JOIN_ORDER or len(after) < JOIN_ORDER:
        return {}
    ia, ib = before[::-1][:JOIN_ORDER], after[:JOIN_ORDER]
    report = {}
    for key, spec in plan.items():
        side, T = spec[0], spec[1]
        Tr = spec[2] if len(spec) > 2 else T
        rot = key in CHANNELS_ROT
        A_ = _side_state(D, ia, key, rot, tj)
        B_ = _side_state(D, ib, key, rot, tj)
        # jump d_k in the k-th derivative, along s (s = tj - t before the join: odd derivatives change sign)
        if side == "before":
            d = [air.logm_so3(B_[0] @ A_[0].T) if rot else B_[0] - A_[0]]
            d += [(-1) ** k * (B_[k] - A_[k]) for k in range(1, JOIN_ORDER)]
            targets = [i for i in before if D[i]["t"] > tj - max(T, Tr)]
        else:
            d = [air.logm_so3(A_[0] @ B_[0].T) if rot else A_[0] - B_[0]]
            d += [A_[k] - B_[k] for k in range(1, JOIN_ORDER)]
            targets = [i for i in after if D[i]["t"] < tj + max(T, Tr)]
        report[key] = tuple(float(np.linalg.norm(x)) for x in d[:3])
        for i in targets:
            s_ = abs(D[i]["t"] - tj)
            f, g = fade(s_ / T), fade(s_ / Tr)
            off = d[0] * f[0] + sum(d[k] * Tr ** k * g[k] for k in range(1, JOIN_ORDER))
            D[i][key] = air.expm_so3(off) @ D[i][key] if rot else np.asarray(D[i][key], float) + off
    return report


TYRE_THETA = np.linspace(0.0, 2.0 * np.pi, 180, endpoint=False)


def tyre_clearance(RA, pb, sf, sr, cb, ground, which=("rear", "front")):
    """Lowest height of the tyres' tread above the surface ground(x) (m; negative = into it), bike CoM at pb."""
    best = np.inf
    tyres = {"rear": (B.rear_axle_at(sr), P.R_REAR), "front": (B.front_axle_at(sf), P.R_FRONT)}
    for ax, R in (tyres[w] for w in which):
        c = pb + RA @ (np.array([ax[0], 0.0, ax[1]]) - cb)
        pts = c[None, :] + R * (np.cos(TYRE_THETA)[:, None] * RA[:, 0] + np.sin(TYRE_THETA)[:, None] * RA[:, 2])
        best = min(best, float(np.min(pts[:, 2] - np.array([ground(x) for x in pts[:, 0]]))))
    return best


def look_quat(pos, target, up=(0.0, 0.0, 1.0)):
    f = np.asarray(target, float) - np.asarray(pos, float)
    f /= np.linalg.norm(f)
    z = -f
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return quat_from_matrix(np.column_stack([x, y, z]))


def seen_from_behind(RA, RB, lean=None):
    """What a camera straight behind the ramp sees: the bike's axle line angle in the picture (deg, nose to the
    left = 0, nose down = 90), how side-on the bike is (0 edge-on/flat, 1 full profile), the torso lean (deg)."""
    n, yb = RA[:, 0], RA[:, 1]
    out = {"bike_img": math.degrees(math.atan2(-n[2], n[1])), "bike_side": abs(float(yb[0]))}
    if RB is not None:
        z = RB[:, 2]
        lean = math.degrees(math.atan2(-z[1], z[2]))
    out["torso_lean"] = float(lean)
    return out


def smooth(series, tau, dt):
    out, a = [], None
    k = dt / (tau + dt)
    for v in series:
        v = np.asarray(v, float)
        a = v if a is None else a + k * (v - a)
        out.append(a.copy())
    return out


def build(pl, log, g1, recA, con, g2, out_dir, seen_fn=None, debug=None):
    S, T = pl.S, pl.T
    poser = Poser(S)
    mA, mB, M = S.mb, S.mr, S.M
    t_off, t_c = log["t_off"], con["t"]
    t_start, t_end = t_off - LEAD, t_off + t_c + TAIL
    ya_c, _, ra_c = air.euler_of(con["RA"])
    # what Damien's camera behind the ramp shows, simulated and measured (whip_measured.py)
    T_air_t = log.get("T_air_target", con["t"])
    if seen_fn is None:
        seen_fn = pl.target_fn(log["take"], T_air_t, np.array(log["whip_x"])).seen
    pb_c = con["C"] - (mB / M) * con["D"]

    def gaze(x_bike):
        """Where he looks: the landing sweet spot, and once he is near it, a point LOOK_AHEAD up the track. The
        switch is a smooth maximum, so the target never jumps and never ends up behind him."""
        k = 1.5
        xa, xb = pl.x_sweet, x_bike + LOOK_AHEAD
        xt = max(xa, xb) + k * math.log1p(math.exp(-abs(xa - xb) / k))
        return np.array([xt, 0.0, T.ground(xt) + 0.3])
    x_lip = T.keys["lip"]
    slope_lip = (T.ground(x_lip) - T.ground(x_lip - 0.01)) / 0.01
    # the ramp face, continued past the lip along its tangent (the tyre contact on the lip without the corner)
    face = lambda x: T.ground(x) if x <= x_lip else T.ground(x_lip) + slope_lip * (x - x_lip)
    rel_c = air.logm_so3(con["RA"].T @ con["RB"])        # rider relative to bike at touchdown (bike frame)

    # ---- unify records into (t_global, kind, rec)
    seq = [(r["t"], "g1", r) for r in g1 if r["t"] < t_off]
    seq += [(t_off + r["t"], "air", r) for r in recA]
    seq += [(t_off + t_c + r["t"], "g2", r) for r in g2 if r["t"] > 0]
    seq = [s for s in seq if t_start - PREROLL - 1e-6 <= s[0] <= t_end + 0.1]

    # ---- pass 1: the drivers of the pose (bike attitude and position, rider attitude, hips, spine, crouch, look)
    last_rider = g1[-1]["rider"] if g1 else (0.0, 0.0)
    last_steer = 0.0
    last_spine = np.zeros(3)
    w_f = w_r = None
    D = []
    for tg, kind, r in seq:
        if kind == "air":
            RA, RB = r["RA"], r["RB"]
            pb = r["C"] - (mB / M) * r["D"]
            prc = r["C"] + (mA / M) * r["D"]
            fade = math.exp(-r["t"] / 0.12)
            spine = np.asarray(r.get("spine", np.zeros(3)), float)
            last_spine = spine
            origin = (prc - RB @ (S.cr + pl.A.upper_shift(spine))
                      + RA @ np.array([last_rider[0], 0.0, last_rider[1]]) * fade)
            crouch = float(np.clip(-last_rider[1] * 0.9, -0.08, 0.25)) * fade
            sf, sr = r["sf"], r["sr"]
            w_f, w_r = r["wf"], r["wr"]
            Vsys = r["V"]
            Csys = r["C"]
            steer = r.get("steer", 0.0)
            last_steer = steer
            loads = (0.0, 0.0)
            look = gaze(pb[0])
            phase = "AIR"
        else:
            st = r["st"]
            res = 1.0
            if kind == "g2":
                res = 1.0 - air.smoothstep(r["t"] / 0.15)
                RA = Rz(ya_c * res) @ Ry(-st[2]) @ Rx(ra_c * res)
                pb = np.array([st[0], pb_c[1] * res, st[1]])
                look = gaze(st[0])
            else:
                RA = Ry(-st[2])
                pb = np.array([st[0], 0.0, st[1]])
                look = gaze(st[0])
            RB = RA @ air.expm_so3(rel_c * res) if kind == "g2" else RA
            spine = last_spine * res if kind == "g2" else np.zeros(3)
            du, dw = r["rider"]
            if kind == "g1":
                last_rider = (du, dw)
            Wb = lambda q: pb + RA @ (np.asarray(q, float) - S.cb)
            origin = Wb(S.peg) + RA @ np.array([du, 0.0, dw])
            if kind == "g2":                        # hips slide back from the air position over the first 0.15 s
                origin = origin + RA @ (np.asarray(con.get("shift", np.zeros(3))) * res)
            crouch = float(np.clip(-dw * 0.9, -0.08, 0.25))
            sf, sr = r["sf"], r["sr"]
            vb = math.hypot(st[3], st[4])
            if r["cf"] or w_f is None:
                w_f = vb / P.R_FRONT
            if r["cr"] or w_r is None:
                w_r = vb / P.R_REAR
            Vsys = np.array([(mA * st[3] + mB * st[8]) / M, 0.0, (mA * st[4] + mB * st[9]) / M])
            steer = last_steer * res if kind == "g2" else 0.0
            Csys = np.array([(mA * st[0] + mB * st[6]) / M, 0.0, (mA * st[1] + mB * st[7]) / M])
            loads = (r["Nf"], r["Nr"])
            if kind == "g1":
                phase = "RAMP" if st[0] > T.keys["ramp_bottom"] - 0.5 else "APPROACH"
            else:
                phase = "LANDING" if r["t"] < 0.6 else "RIDE AWAY"
        D.append({"t": tg, "kind": kind, "r": r, "RA": RA, "pb": np.asarray(pb, float), "R_rel": RA.T @ RB,
                  "lip_window": kind == "g1" and tg - t_off > -LIP_T,
                  "o_rel": RA.T @ (np.asarray(origin, float) - pb), "spine": np.asarray(spine, float),
                  "crouch": np.array([crouch]), "look": np.asarray(look, float), "sf": sf, "sr": sr, "steer": steer,
                  "w_f": w_f, "w_r": w_r, "Vsys": Vsys, "Csys": Csys, "loads": loads, "phase": phase})

    # ---- pass 2: the lip and touchdown joins, where two simulations meet, made continuous in value, rate and
    # curvature (single-frame pops otherwise: the spine and hips of the air solution are not those of the ramp)
    # The whip starts on the lip (clips 2 and 3: already turning at the lip frame). Over the last LIP_T on the ramp
    # the bike's attitude is bent from the ramp simulation's onto the measured lip attitude and rate, and the rider
    # onto his air posture (one blend, matched in value, rate and acceleration at the lip). The bike turns about the
    # centre of mass, which keeps the ramp simulation's path: as in the air, the bike moves the other way to the
    # rider's body, and the ramp holds the rear tyre (the last contact) on its surface: the bike is lifted by however
    # far the turn would push it in. The rear end steps out sideways as the whip is thrown.
    rel_com = lambda d: d["RA"] @ d["o_rel"] + d["RA"] @ d["R_rel"] @ (S.cr + pl.A.upper_shift(d["spine"]))
    sim_state = {i: (rel_com(d), d["RA"].copy(), d["pb"].copy()) for i, d in enumerate(D) if d["lip_window"]}
    joins = {"lip_rider": blend_join(D, t_off, LIP_PLAN_RIDER, ("air", "g2"))}
    for i, (Db, RA0, pb0) in sim_state.items():
        d = D[i]
        d["pb"] = pb0 - (mB / M) * (rel_com(d) - Db)
        d["pb"][2] += tyre_clearance(RA0, pb0, d["sf"], d["sr"], S.cb, face, ("rear",)) \
            - tyre_clearance(d["RA"], d["pb"], d["sf"], d["sr"], S.cb, face, ("rear",))
    joins["lip_bike"] = blend_join(D, t_off, LIP_PLAN_BIKE, ("air", "g2"))
    joins["touchdown"] = blend_join(D, t_off + t_c, LAND_PLAN, ("g2",))
    for d in D:                                                # rider pose back in the world
        d["RB"] = d["RA"] @ d["R_rel"]
        d["origin"] = d["pb"] + d["RA"] @ d["o_rel"]

    if debug is not None:
        debug["drivers"] = D

    # ---- pass 3: every driver onto the even frame grid (C2 cubics through the records; the suspension and wheel
    # speeds monotone, so a real kink such as the rear unloading on the lip does not overshoot), then pose each frame.
    # Posing at an even step matters: the elbow, knee and head keep a memory of the previous frame.
    # records closer than 3 ms to the next one are dropped (at the lip the ramp's last record is 1.2 ms before the
    # air's first): a spline through a very short interval turns tiny differences into acceleration spikes
    TD = np.array([d["t"] for d in D])
    keep = np.concatenate([np.diff(TD) > 0.003, [True]])
    D = [d for d, k in zip(D, keep) if k]
    TD = TD[keep]
    cub = lambda key: CubicSpline(TD, np.array([np.asarray(d[key], float) for d in D]), axis=0)
    mono = lambda key: PchipInterpolator(TD, np.array([float(d[key]) for d in D]))
    lin = lambda key: (lambda t, a=np.array([np.asarray(d[key], float) for d in D]): np.array(
        [np.interp(t, TD, a[:, j]) for j in range(a.shape[1])]) if a.ndim == 2 else float(np.interp(t, TD, a)))

    def quat_spline(key):
        Q = np.array([quat_from_matrix(d[key]) for d in D])
        for i in range(1, len(Q)):
            if Q[i] @ Q[i - 1] < 0:
                Q[i] = -Q[i]
        return CubicSpline(TD, Q, axis=0)

    F = {k: cub(k) for k in ("pb", "o_rel", "spine", "crouch", "look")}
    F.update({k: quat_spline(k) for k in ("RA", "R_rel")})
    F.update({k: mono(k) for k in ("sf", "sr", "steer", "w_f", "w_r")})
    Lv = {k: lin(k) for k in ("Vsys", "Csys")}
    loads_a = np.array([d["loads"] for d in D], float)
    n_pre = int(round(PREROLL * FPS))
    n_end = int(math.floor((t_end - t_start) * FPS + 1e-6))
    grid = [t_start + k / FPS for k in range(-n_pre, n_end + 1) if t_start + k / FPS >= TD[0]]
    spin_f = spin_r = 0.0
    names = None
    frames, hud, rider_c = [], [], []
    for gi, tg in enumerate(grid):
        j = int(np.clip(np.searchsorted(TD, tg, side="right") - 1, 0, len(D) - 1))
        kind, phase = D[j]["kind"], D[j]["phase"]
        RA = R_of_quat(F["RA"](tg))
        RB = RA @ R_of_quat(F["R_rel"](tg))
        pb = F["pb"](tg)
        origin = pb + RA @ F["o_rel"](tg)
        sf, sr, steer = float(F["sf"](tg)), float(F["sr"](tg)), float(F["steer"](tg))
        w_r = float(F["w_r"](tg))
        if gi > 0:
            spin_f += float(F["w_f"](tg)) / FPS
            spin_r += w_r / FPS
        crouch = float(F["crouch"](tg)[0])
        Vsys, Csys = Lv["Vsys"](tg), Lv["Csys"](tg)
        loads = (float(np.interp(tg, TD, loads_a[:, 0])), float(np.interp(tg, TD, loads_a[:, 1])))
        parts, Wb2, Wf2, Rfront = poser.bike_parts(RA, pb, sf, sr, spin_f, spin_r, steer)
        rp = poser.rider_parts(RA, RB, Wb2, origin, F["look"](tg), crouch, Wf=Wf2, R_front=Rfront, spine=F["spine"](tg))
        if tg < t_start - 1e-9:                    # pre-roll: posed for the memories, not shown
            continue
        allp = {**{f"bike:{k}": v for k, v in parts.items()}, **{f"rider:{k}": v for k, v in rp.items()}}
        if names is None:
            names = sorted(allp)
        frames.append({"t": tg, "f": float(round((tg - t_start) * FPS) + 1),
                       "tf": [[*map(float, allp[n][0]), *map(float, quat_from_matrix(allp[n][1]))] for n in names]})
        rider_c.append(origin + RB @ S.cr)
        rear_ax = Wb2(np.array([B.rear_axle_at(sr)[0], 0.0, B.rear_axle_at(sr)[1]]))
        height = max(rear_ax[2] - P.R_REAR - T.ground(rear_ax[0]), 0.0)
        ya, pa, ra = air.euler_of(RA)
        yb, pbb, rb = air.euler_of(RB)
        seen = seen_from_behind(RA, RB)
        if kind == "air":
            Rm, lean_m = seen_fn(tg - t_off)
            seen.update({f"meas_{k}": v for k, v in seen_from_behind(Rm, None, lean_m).items()})
        hud.append({**seen, "t": tg - t_off, "kmh": float(np.linalg.norm(Vsys) * 3.6), "height": float(height),
                    "x": float(pb[0]), "phase": phase, "bike_yaw": math.degrees(ya), "bike_roll": math.degrees(ra),
                    "bike_pitch": math.degrees(pa), "rider_yaw": math.degrees(yb), "rider_roll": math.degrees(rb),
                    "sf": sf, "sr": sr, "cx": float(Csys[0]), "cz": float(Csys[2]),
                    "Nf": loads[0], "Nr": loads[1], "crouch": crouch,
                    "steer": math.degrees(steer), "wr": w_r})
    for i in range(1, len(frames)):                # quaternion sign continuity (Blender interpolates components)
        for j in range(len(names)):
            q0, q1 = frames[i - 1]["tf"][j][3:], frames[i]["tf"][j][3:]
            if sum(a * b for a, b in zip(q0, q1)) < 0:
                frames[i]["tf"][j][3:] = [-v for v in q1]

    # ---- cameras
    dtf = 1.0 / FPS
    rc_s = smooth(rider_c, 0.12, dtf)
    rc_slow = smooth(rider_c, 0.35, dtf)
    k = T.keys
    cams = []

    def path_of(pos_fn, tgt_series):
        p = []
        for i, fr in enumerate(frames):
            pos = pos_fn(i)
            q = look_quat(pos, tgt_series[i])
            p.append([fr["f"], *map(float, pos), *map(float, q)])
        return p

    side_pos = np.array([12.0, 36.0, 5.0])         # frames x = -6.5 .. 30.5 m: ramp toe to landing bottom
    cams.append({"name": "CAM_SIDE", "lens": 35.0, "path": path_of(lambda i: side_pos, [np.array([12.0, 0.0, 4.2])] * len(frames))})
    dam_pos = np.array([k["ramp_bottom"] - 3.5, 2.5, 1.5])      # matched to Damien's clip 3 framing
    cams.append({"name": "CAM_DAMIEN", "lens": 35.0, "path": path_of(lambda i: dam_pos, rc_s)})
    cams.append({"name": "CAM_TRACK", "lens": 45.0,
                 "path": path_of(lambda i: rc_slow[i] + np.array([3.0, 9.0, 0.8]), rc_s)})
    # matched to Damien's two phones on the clips 2 and 3 jump (research/whip-attitude-3d/cams_clips23.json): both
    # behind and left of the jump line, zoomed (focal length from the bike's pixel size at the flat peak), panning
    # with the rider; lens for a portrait frame (36 mm across the long side)
    for name, cpos, fpx in (("CAM_CLIP3", (-16.0, 4.0, 1.5), 1200.0), ("CAM_CLIP2", (-6.0, 2.5, 1.0), 1300.0)):
        cposa = np.array(cpos)
        cams.append({"name": name, "lens": 18.0 * fpx / 425.0, "path": path_of(lambda i, c=cposa: c, rc_s)})
    land_pos = np.array([k["landing_bottom"] + 7.0, 6.0, 1.3])
    cams.append({"name": "CAM_LAND", "lens": 28.0, "path": path_of(lambda i: land_pos, rc_s)})

    # ---- scene description
    lm = RD.neutral_landmarks()
    xs = T.xs[::10]
    zs = T.zs[::10]
    keys = dict(T.keys)
    keys["lip_height"] = P.LIP_HEIGHT
    scene = {
        "bike": {"front_axle": list(P.FRONT_AXLE), "rear_axle": list(P.REAR_AXLE), "pivot": list(P.SWINGARM_PIVOT),
                 "fork_axis": list(map(float, B.fork_axis())), "rake_deg": P.RAKE_DEG, "grip": list(P.GRIP),
                 "grip_half": P.GRIP_HALF_SPAN, "peg": list(P.FOOTPEG), "r_front": P.R_FRONT, "r_rear": P.R_REAR},
        "rider": {"landmarks": {n: list(map(float, v)) for n, v in lm.items()},
                  "lengths": {"thigh": RD.L_THIGH, "shank": RD.L_SHANK, "upper_arm": RD.L_UPPER_ARM,
                              "forearm": RD.L_FOREARM + RD.L_HAND_GRIP}},
        "terrain": {"xs": list(map(float, xs)), "zs": list(map(float, zs)), "keys": {n: float(v) for n, v in keys.items()}},
        "ramp_width": P.RAMP_WIDTH, "landing_width": P.LANDING_WIDTH, "cameras": cams,
    }
    with open(f"{out_dir}/scene.json", "w") as f:
        json.dump(scene, f)
    with open(f"{out_dir}/frames.json", "w") as f:
        json.dump({"objects": names, "frames": frames, "t_start": t_start, "t_off": t_off, "t_land": t_off + t_c}, f)
    with open(f"{out_dir}/hud.json", "w") as f:
        json.dump(hud, f)
    return {"frames": len(frames), "t_start": t_start, "t_off": t_off, "t_land": t_off + t_c, "t_end": t_end,
            "reach_violations": poser.reach_violations, "max_overreach_m": poser.max_overreach,
            "max_reach_ratio": {k: round(v, 4) for k, v in poser.max_ratio.items()},
            "joins_removed": {j: {k: [round(v[0], 4), round(v[1], 3), round(v[2], 1)] for k, v in rep.items()}
                              for j, rep in joins.items()}}
