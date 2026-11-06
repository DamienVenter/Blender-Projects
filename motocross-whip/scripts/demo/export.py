"""Convert simulation records into Blender keyframe data (frames.json, scene.json, summary.json)."""
import json
import math
import numpy as np

import params as P
import bike as B
import rider as RD
import air
from air import Rz, Ry, Rx
from pose import Poser, quat_from_matrix

FPS = 120
LEAD, TAIL = 2.2, 2.4          # seconds shown before the lip and after touchdown


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


def build(pl, log, g1, recA, con, g2, out_dir):
    S, T = pl.S, pl.T
    poser = Poser(S)
    mA, mB, M = S.mb, S.mr, S.M
    t_off, t_c = log["t_off"], con["t"]
    t_start, t_end = t_off - LEAD, t_off + t_c + TAIL
    sweet = np.array([pl.x_sweet, 0.0, T.ground(pl.x_sweet)])
    ya_c, _, ra_c = air.euler_of(con["RA"])
    # what Damien's camera behind the ramp shows, simulated and measured (whip_measured.py)
    T_air_t = log.get("T_air_target", con["t"])
    seen_fn = pl.target_fn(log["take"], T_air_t, np.array(log["whip_x"])).seen
    pb_c = con["C"] - (mB / M) * con["D"]
    rel_c = air.logm_so3(con["RA"].T @ con["RB"])        # rider relative to bike at touchdown (bike frame)

    # ---- unify records into (t_global, kind, rec)
    seq = [(r["t"], "g1", r) for r in g1 if r["t"] < t_off]
    seq += [(t_off + r["t"], "air", r) for r in recA]
    seq += [(t_off + t_c + r["t"], "g2", r) for r in g2 if r["t"] > 0]
    seq = [s for s in seq if t_start - 1e-6 <= s[0] <= t_end]

    last_rider = g1[-1]["rider"] if g1 else (0.0, 0.0)
    last_steer = 0.0
    last_spine = np.zeros(3)
    spin_f = spin_r = 0.0
    w_f = w_r = None
    prev_t = None
    names = None
    frames, hud, rider_c = [], [], []
    for tg, kind, r in seq:
        dt = 0.0 if prev_t is None else tg - prev_t
        prev_t = tg
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
            look = sweet
            phase = "AIR"
        else:
            st = r["st"]
            res = 1.0
            if kind == "g2":
                res = 1.0 - air.smoothstep(r["t"] / 0.15)
                RA = Rz(ya_c * res) @ Ry(-st[2]) @ Rx(ra_c * res)
                pb = np.array([st[0], pb_c[1] * res, st[1]])
                look = np.array([st[0] + 20.0, 0.0, 0.0])
            else:
                RA = Ry(-st[2])
                pb = np.array([st[0], 0.0, st[1]])
                look = sweet
            RB = RA @ air.expm_so3(rel_c * res) if kind == "g2" else RA
            spine = last_spine * res if kind == "g2" else np.zeros(3)
            du, dw = r["rider"]
            if kind == "g1":
                last_rider = (du, dw)
            Wb = lambda q: pb + RA @ (np.asarray(q, float) - S.cb)
            origin = Wb(S.peg) + RA @ np.array([du, 0.0, dw])
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
        spin_f += w_f * dt
        spin_r += w_r * dt
        parts, Wb2, Wf2, Rfront = poser.bike_parts(RA, pb, sf, sr, spin_f, spin_r, steer)
        rp = poser.rider_parts(RA, RB, Wb2, origin, look, crouch, Wf=Wf2, R_front=Rfront, spine=spine)
        allp = {**{f"bike:{k}": v for k, v in parts.items()}, **{f"rider:{k}": v for k, v in rp.items()}}
        if names is None:
            names = sorted(allp)
        frames.append({"t": tg, "tf": [[*map(float, allp[n][0]), *map(float, quat_from_matrix(allp[n][1]))] for n in names]})
        rc = origin + RB @ S.cr
        rider_c.append(rc)
        rear_ax = Wb2(np.array([B.rear_axle_at(sr)[0], 0.0, B.rear_axle_at(sr)[1]]))
        height = max(rear_ax[2] - P.R_REAR - T.ground(rear_ax[0]), 0.0)
        ya, pa, ra = air.euler_of(RA)
        yb, pbb, rb = air.euler_of(RB)
        seen = seen_from_behind(RA, RB)
        if kind == "air":
            Rm, lean_m = seen_fn(r["t"])
            seen.update({f"meas_{k}": v for k, v in seen_from_behind(Rm, None, lean_m).items()})
        hud.append({**seen, "t": tg - t_off, "kmh": float(np.linalg.norm(Vsys) * 3.6), "height": float(height),
                    "x": float(pb[0]), "phase": phase, "bike_yaw": math.degrees(ya), "bike_roll": math.degrees(ra),
                    "bike_pitch": math.degrees(pa), "rider_yaw": math.degrees(yb), "rider_roll": math.degrees(rb),
                    "sf": float(sf), "sr": float(sr), "cx": float(Csys[0]), "cz": float(Csys[2]),
                    "Nf": float(loads[0]), "Nr": float(loads[1]), "crouch": float(crouch),
                    "steer": math.degrees(steer), "wr": float(w_r)})

    # ---- quaternion sign continuity and frame numbers
    for i in range(1, len(frames)):
        for j in range(len(names)):
            q0, q1 = frames[i - 1]["tf"][j][3:], frames[i]["tf"][j][3:]
            if sum(a * b for a, b in zip(q0, q1)) < 0:
                frames[i]["tf"][j][3:] = [-v for v in q1]
    for fr in frames:
        fr["f"] = (fr["t"] - t_start) * FPS + 1.0

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
    # matched to Damien's clip 1 shot A (research/whip-attitude-measured.md): about 25 m behind the lip, 1.5 m up,
    # zoomed phone camera (1600 px focal on a 478 x 850 frame = 30 deg vertical field), panning with the rider
    far_pos = np.array([-25.0, 1.0, 1.5])
    cams.append({"name": "CAM_BEHIND_FAR", "lens": 18.0 / math.tan(math.atan(425.0 / 1600.0)), "path": path_of(lambda i: far_pos, rc_s)})
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
            "reach_violations": poser.reach_violations, "max_overreach_m": poser.max_overreach}
