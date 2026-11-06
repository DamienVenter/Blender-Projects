"""Whip demo: full simulation pipeline.

1. Solve the approach speed so the rear wheel touches down on the landing sweet spot.
2. Optimise the rider's whip inputs so the bike's motion matches Damien's clip
   (research/whip-analysis-user-clips.md) using only physically available
   inputs: a yaw/roll kick off the lip, the rider moving the bike relative to
   his body (within arm and leg reach), and the rear wheel's gyro (throttle blip
   or brake tap). Angular momentum is conserved exactly in the air.
3. Land, ride away, and export per-frame transforms for Blender.

Usage: python3 sim.py OUT_DIR
"""
import json
import math
import sys
import time
import numpy as np
from scipy.optimize import minimize, brentq

import params as P
import terrain
import ground
import air
import rider as RD
from pose import Poser, quat_from_matrix

FPS_SIM = 120
DEG = math.pi / 180

# Damien's whip (bike world orientation), times in seconds after the lip for a 2.05 s flight.
# yaw: nose left +, roll: right lean + (so a left lay-down is negative).
TARGET = {
    "t":    [0.00, 0.10, 0.30, 0.45, 0.60, 0.90, 1.30, 1.70, 1.90, 2.05],
    "yaw":  [0.0, 10.0, 40.0, 55.0, 60.0, 60.0, 50.0, 35.0, 12.0, 2.0],
    "roll": [0.0, -25.0, -75.0, -85.0, -70.0, -25.0, -12.0, -5.0, 0.0, 0.0],
}
KNOT_F = [0.06, 0.16, 0.26, 0.42, 0.62, 0.82, 0.93]     # forward-model knot times (tests)


class Pipeline:
    def __init__(self):
        self.T = terrain.Terrain()
        self.S = ground.System()
        self.G = ground.GroundSim(self.S, self.T)
        self.A = air.AirSim(self.S, self.T)
        k = self.T.keys
        # rear tyre contact target, and the rear axle position that puts the contact there
        x_contact = k["knuckle"] + P.TOUCHDOWN_PAST_KNUCKLE
        slope = math.atan(-(self.T.ground(x_contact + 0.05) - self.T.ground(x_contact - 0.05)) / 0.10)
        self.x_sweet = x_contact - P.R_REAR * math.sin(slope)
        self.touchdown_slope = math.degrees(slope)
        self.landing_pitch = -self.touchdown_slope + 2.0     # rear tyre a touch before the front

    # ---------- ground to takeoff
    def to_takeoff(self, v, lead=2.5):
        X0 = self.T.keys["ramp_bottom"] - v * lead
        st0, s0 = self.G.static_pose(X0)
        st0[3] = st0[8] = v
        rb = self.T.keys["ramp_bottom"]
        dm = lambda t, s: "hold" if s[0] < rb - 1.0 else "face"
        stop = lambda t, s, c: (s[0] > 0.0 and not c["front"]["contact"] and not c["rear"]["contact"])
        t, st, sp, rec = self.G.run(st0, s0, 0.0, stop, dm, v)
        return t, st, sp, rec

    def take_from(self, st, sp, rec):
        C, V, Ly = self.G.system_state(st)
        Iyy = self.S.Isys[1, 1]
        vf = [r for r in rec if r["cf"]][-1]["st"]
        vr = [r for r in rec if r["cr"]][-1]["st"]
        wf = math.hypot(vf[3], vf[4]) / P.R_FRONT
        wr = math.hypot(vr[3], vr[4]) / P.R_REAR
        # rigid-equivalent pitch rate carrying the true system angular momentum (incl. wheel spin
        # is handled in the air model separately; Ly here is bodies only)
        return dict(X=C[0], Z=C[1], VX=V[0], VZ=V[1], beta=st[2], W=Ly / Iyy, sf=sp["front"], sr=sp["rear"],
                    wf=wf, wr=wr, W_bike=st[5])

    def no_whip(self, take, dt=1.0 / 1200):
        """Rigid flight with no rider input. contact['pitch_cont'] is the unwrapped bike pitch (deg)."""
        knots = dict(f=KNOT_F, yaw=[0] * 7, pitch=[0] * 7, roll=[0] * 7)
        rec, con = self.A.run(take, dict(knots=knots), dt=dt, rec_dt=0.02, record=True)
        if con is not None:
            # unwrapped pitch: accumulate the small rotation between records about the lateral axis
            pitch = take["beta"]
            Rs = [r["RA"] for r in rec] + [con["RA"]]
            for a, b in zip(Rs[:-1], Rs[1:]):
                pitch += -air.logm_so3(b @ a.T)[1]
            con["pitch_cont"] = math.degrees(pitch)
        return rec, con

    def solve_face_throttle(self, lo=0.0, hi=1700.0):
        """Steady face throttle (N at the rear tyre) whose natural rotation lands the bike at the target pitch."""
        def err(T):
            self.S.T_face = T
            v = self.solve_speed()
            t, st, sp, rec = self.to_takeoff(v)
            _, con = self.no_whip(self.take_from(st, sp, rec))
            pa = con["pitch_cont"]
            print(f"   face throttle {T:7.1f} N -> approach {v:.3f} m/s, no-whip landing pitch {pa:6.2f} deg")
            return pa - self.landing_pitch
        T = brentq(err, lo, hi, xtol=5.0)
        self.S.T_face = T
        return T

    def solve_speed(self):
        def miss(v):
            t, st, sp, rec = self.to_takeoff(v)
            take = self.take_from(st, sp, rec)
            _, con = self.no_whip(take)
            bike_c = con["C"] - (self.S.mr / self.S.M) * con["D"]
            ra = bike_c + con["RA"] @ (np.array([0.0, 0.0, P.R_REAR]) - self.S.cb)
            return ra[0] - self.x_sweet
        v = brentq(miss, 10.0, 24.0, xtol=0.005)
        return v

    # ---------- whip optimisation (inverse: bike motion prescribed, rider from conservation)
    def profile(self, take, T_air, x):
        """Damien's whip, time-scaled to this airtime. x: r0, p0 (deg/s), roll scale, yaw scale, b, t_b."""
        sc = T_air / TARGET["t"][-1]
        tk = [t * sc for t in TARGET["t"]]
        return dict(T=T_air, beta0=take["beta"], beta_dot0=take["W"], beta_land=math.radians(self.landing_pitch),
                    yaw_t=tk, yaw=[v * x[3] for v in TARGET["yaw"]], r0=x[0] / sc,
                    roll_t=tk, roll=[v * x[2] for v in TARGET["roll"]], p0=x[1] / sc)

    def target_fn(self, take, T_air, x):
        """Damien's whip (scaled by x[3] roll, x[4] yaw) as the controller's target: (R, omega) at t."""
        prof = self.profile(take, T_air, [x[0], x[1], x[3], x[4], 0.0, 0.9])
        h = 1e-3

        def R(t):
            y, p, r = self.A.bike_angles(prof, np.array([t]))
            return air.euler_from(y[0], p[0], r[0])

        def f(t):
            R0, R1 = R(t), R(t + h)
            return R0, air.logm_so3(R1 @ R0.T) / h
        return f

    def ctrl_cost(self, rec, con, x, detail=False):
        arm = RD.L_UPPER_ARM + RD.L_FOREARM + RD.L_HAND_GRIP
        leg = RD.L_THIGH + RD.L_SHANK
        Lmax = np.array([arm, arm, leg, leg])
        reach = track = yawc = 0.0
        worst = -1.0
        for r in rec:
            d = self.A.att_L + r["reach_err"]
            reach += float((np.maximum(d - 0.97 * Lmax, 0) ** 2).sum() + (np.maximum(0.40 * Lmax - d, 0) ** 2).sum())
            worst = max(worst, float((d - Lmax).max()))
            track += math.degrees(r["track_err"]) ** 2
            yb, _, _ = air.euler_of(r["RB"])
            yawc += math.degrees(yb) ** 2
        n = len(rec)
        reach = reach / n / 0.02 ** 2
        track_rms = math.sqrt(track / n)
        yaw_rms = math.sqrt(yawc / n)
        ya, pa, ra = (math.degrees(v) for v in air.euler_of(con["RA"]))
        rel_c = math.degrees(np.linalg.norm(air.logm_so3(con["RB"].T @ con["RA"])))
        land = (ya / 4) ** 2 + (ra / 4) ** 2 + ((pa - self.landing_pitch) / 4) ** 2 + (rel_c / 10) ** 2
        reg = (x[0] / 150) ** 2 + (x[1] / 250) ** 2 + (x[2] / 30) ** 2
        amp = 25.0 * ((1 - x[3]) ** 2 + (1 - x[4]) ** 2)   # prefer Damien's full whip: shrink only if physics forces it
        J = (track_rms / 8) ** 2 + land + reach + 0.3 * (yaw_rms / 30) ** 2 + 0.3 * reg + amp
        if detail:
            return dict(J=J, track_rms_deg=track_rms, rider_yaw_rms_deg=yaw_rms, reach=reach, worst_overreach_m=worst,
                        land_yaw=ya, land_pitch=pa, land_roll=ra, rider_rel_at_contact_deg=rel_c, reg=reg, amp=amp,
                        t_air=con["t"], contact=con["wheel"])
        return J

    def objective(self, x, take, T_air, dt=1.0 / 600, detail=False):
        tk = dict(take)
        tk["W"] = take["W"] + math.radians(x[2])
        rec, con = self.A.run_control(tk, self.target_fn(tk, T_air, x), r0=math.radians(x[0]), p0=math.radians(x[1]),
                                      dt=dt, rec_dt=1.0 / 30, t_max=T_air + 0.6, T_land=T_air)
        if con is None:
            return 1e6
        return self.ctrl_cost(rec, con, x, detail)

    LO = np.array([-200.0, -300.0, -10.0, 0.50, 0.40])
    HI = np.array([200.0, 300.0, 19.0, 1.00, 1.10])

    STARTS = ([0, -54, 19, 0.70, 0.60], [0, -80, 19, 0.85, 0.8], [0, -60, 15, 0.6, 0.5], [20, -120, 19, 0.9, 0.9])

    def optimise(self, take, T_air, maxiter=250):
        """Nelder-Mead from several starts, one per CPU core (fork shares this pipeline)."""
        import concurrent.futures as cf
        import multiprocessing as mp
        global _OPT_CTX
        _OPT_CTX = (self, take, T_air, maxiter)
        t0 = time.time()
        with cf.ProcessPoolExecutor(max_workers=min(4, len(self.STARTS)), mp_context=mp.get_context("fork")) as ex:
            results = list(ex.map(_opt_worker, self.STARTS))
        for x0, (fun, x) in zip(self.STARTS, results):
            print(f"      start {x0} -> J {fun:.3f} x {[round(float(v), 2) for v in x]}", flush=True)
        fun, x = min(results, key=lambda r: r[0])

        class Res:
            pass
        res = Res()
        res.fun, res.x = fun, np.clip(np.array(x), self.LO, self.HI)
        return res, time.time() - t0

    def solve_lip_pull(self, v, W_target):
        """Rider's lift on the bars at the lip (N) that gives the takeoff rotation W_target (rad/s)."""
        def err(pull):
            self.S.lip_pull = pull
            t, st, sp, rec = self.to_takeoff(v)
            return self.take_from(st, sp, rec)["W"] - W_target
        lo, hi = -1000.0, 1000.0
        if err(lo) * err(hi) > 0:
            self.S.lip_pull = hi if abs(err(hi)) < abs(err(lo)) else lo
            return self.S.lip_pull
        pull = brentq(err, lo, hi, xtol=2.0)
        self.S.lip_pull = pull
        return pull

    # ---------- landing and ride-away
    def landing(self, recA, con, ride_time=2.6):
        S = self.S
        mA, mB, M = S.mb, S.mr, S.M
        r1, r2 = recA[-2], recA[-1]
        dtr = r2["t"] - r1["t"]
        pb = con["C"] - (mB / M) * con["D"]
        pr = con["C"] + (mA / M) * con["D"]
        pb1 = r1["C"] - (mB / M) * r1["D"]
        pr1 = r1["C"] + (mA / M) * r1["D"]
        vb = con["V"] + (pb - con["C"] - (pb1 - r1["C"])) / max(con["t"] - r1["t"], 1e-6)
        vr = con["V"] + (pr - con["C"] - (pr1 - r1["C"])) / max(con["t"] - r1["t"], 1e-6)
        _, beta, _ = air.euler_of(con["RA"])
        _, beta1, _ = air.euler_of(r1["RA"])
        W = (beta - beta1) / max(con["t"] - r1["t"], 1e-6)
        st = [pb[0], pb[2], beta, vb[0], vb[2], W, pr[0], pr[2], vr[0], vr[2]]
        s0 = {"front": con["sf"], "rear": con["sr"]}
        t_end = ride_time
        t, st, sp, rec = self.G.run(st, s0, 0.0, lambda t, s, c: t >= t_end, "coast", 0.0)
        return rec

    def run_all(self, out_dir, maxiter=120, face_throttle=None):
        log = {}
        tw = time.time()
        if face_throttle is None:
            T_face = self.solve_face_throttle()
        else:
            T_face = self.S.T_face = face_throttle       # previously solved value, recorded as supplied
            log["face_throttle_supplied"] = True
        v = self.solve_speed()
        log["approach_speed"] = v
        log["face_throttle_N"] = T_face
        print(f"[1] approach speed {v:.3f} m/s ({v*3.6:.1f} km/h)  ({time.time()-tw:.0f}s)")
        t_off, st, sp, rec_g1 = self.to_takeoff(v)
        take = self.take_from(st, sp, rec_g1)
        _, con0 = self.no_whip(take)
        T_air = con0["t"]
        print(f"[2] takeoff t={t_off:.3f}s |V|={math.hypot(take['VX'], take['VZ']):.2f} m/s "
              f"pitch {math.degrees(take['beta']):.1f} deg, W={math.degrees(take['W']):.1f} deg/s, no-whip airtime {T_air:.3f}s")
        # optimise rider inputs with the closed-loop rider; iterate the landing time to the actual contact
        el = 0.0
        take_nom = take
        for it in range(4):
            res, e = self.optimise(take_nom, T_air, maxiter=maxiter)
            el += e
            det = self.objective(res.x, take_nom, T_air, dt=1.0 / 1200, detail=True)
            print(f"    pass {it}: T_air {T_air:.4f} -> contact {det['t_air']:.4f}, J {det['J']:.3f}, "
                  f"x {[round(float(v), 3) for v in res.x]}", flush=True)
            with open(f"{out_dir}/whip_pass{it}.json", "w") as f:
                json.dump({"T_air": T_air, "x": [float(v) for v in res.x], "detail": _jsonable(det)}, f)
            if abs(det["t_air"] - T_air) < 0.01:
                break
            T_air = float(det["t_air"])
        # realise the takeoff rotation change in the ground model (rider lifts on the bars at the lip)
        pull = self.solve_lip_pull(v, take_nom["W"] + math.radians(res.x[2]))
        t_off, st, sp, rec_g1 = self.to_takeoff(v)
        take = self.take_from(st, sp, rec_g1)
        print(f"    lip pull {pull:.0f} N -> takeoff rotation {math.degrees(take['W']):.2f} deg/s "
              f"(wanted {math.degrees(take_nom['W']) + res.x[2]:.2f})", flush=True)
        x_real = np.array(res.x, float)
        x_real[2] = 0.0                                   # the rotation change is now in the takeoff itself
        det = self.objective(x_real, take, T_air, dt=1.0 / 1200, detail=True)
        print(f"[3] whip optimised in {el:.0f}s: "
              f"{json.dumps({k: (round(float(v), 3) if isinstance(v, (int, float, np.floating)) else v) for k, v in det.items()})}")
        recA, con = self.A.run_control(take, self.target_fn(take, T_air, x_real), r0=math.radians(x_real[0]),
                                       p0=math.radians(x_real[1]), dt=1.0 / 1200, rec_dt=1.0 / FPS_SIM,
                                       t_max=T_air + 0.6, T_land=T_air)
        res.x = x_real
        log["lip_pull_N"] = pull
        rec_g2 = self.landing(recA, con)
        log.update(dict(mass_total=self.S.M, mass_bike=self.S.mb, mass_rider=self.S.mr, t_off=t_off, take=take, whip_x=list(map(float, res.x)), detail=det, contact_wheel=con["wheel"],
                        t_air=con["t"], L0=list(map(float, self.A.L0))))
        return log, rec_g1, recA, con, rec_g2


_OPT_CTX = None


def _opt_worker(x0):
    pl, take, T_air, maxiter = _OPT_CTX
    lo, hi = pl.LO, pl.HI
    f = lambda z: pl.objective(np.clip(z, lo, hi), take, T_air) + 1e3 * np.sum(((z - np.clip(z, lo, hi)) / (hi - lo)) ** 2)
    res = minimize(f, np.array(x0, float), method="Nelder-Mead",
                   options=dict(maxiter=maxiter, xatol=0.5, fatol=1e-3, adaptive=True))
    return float(res.fun), [float(v) for v in res.x]


def _jsonable(o):
    if isinstance(o, dict):
        return {k: _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o


if __name__ == "__main__":
    import os
    import export
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    import pickle
    pl = Pipeline()
    if "--reuse" in sys.argv and os.path.exists(f"{out}/records.pkl"):
        with open(f"{out}/records.pkl", "rb") as f:
            log, g1, ra, con, g2, T_face = pickle.load(f)
        pl.S.T_face = T_face
    else:
        ft = float(sys.argv[sys.argv.index("--face-throttle") + 1]) if "--face-throttle" in sys.argv else None
        log, g1, ra, con, g2 = pl.run_all(out, face_throttle=ft)
        with open(f"{out}/records.pkl", "wb") as f:
            pickle.dump((log, g1, ra, con, g2, pl.S.T_face), f)
    info = export.build(pl, log, g1, ra, con, g2, out)
    log["export"] = info
    with open(f"{out}/summary.json", "w") as f:
        json.dump(_jsonable(log), f, indent=1)
    print("[4] export", json.dumps(_jsonable(info)))
