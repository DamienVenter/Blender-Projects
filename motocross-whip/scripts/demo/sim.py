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

    def rider_cost(self, rec, con, x, detail=False):
        lm = self.lm
        arm = RD.L_UPPER_ARM + RD.L_FOREARM + RD.L_HAND_GRIP
        leg = RD.L_THIGH + RD.L_SHANK
        reach = yawc = rollc = 0.0
        worst = 0.0
        for r in rec:
            Rr = r["RB"].T @ r["RA"]
            for s in ("l", "r"):
                da = np.linalg.norm(Rr @ lm[f"grip_{s}"] - lm[f"shoulder_{s}"])
                dl = np.linalg.norm(Rr @ lm[f"ankle_{s}"] - lm[f"hip_{s}"])
                over = max(da - 0.97 * arm, 0) + max(dl - 0.97 * leg, 0)
                under = max(0.45 * arm - da, 0) + max(0.45 * leg - dl, 0)
                reach += over ** 2 + under ** 2
                worst = max(worst, da - arm, dl - leg)
            yb, pb, rb = air.euler_of(r["RB"])
            yawc += (math.degrees(yb) / 30) ** 2
            rollc += (math.degrees(rb) / 35) ** 2
        n = len(rec)
        reach = reach / n / 0.02 ** 2
        yawc, rollc = yawc / n, rollc / n
        Rr_end = con["RB"].T @ con["RA"]
        land = (math.degrees(np.linalg.norm(air.logm_so3(Rr_end))) / 8) ** 2
        reg = (x[0] / 300) ** 2 + (x[1] / 400) ** 2 + x[4] ** 2
        J = reach + 0.5 * yawc + 0.5 * rollc + land + 0.3 * reg
        if detail:
            ya, pa, ra = air.euler_of(con["RA"])
            return dict(J=J, reach=reach, rider_yaw=yawc, rider_roll=rollc, land_rel=land, reg=reg, t_air=con["t"],
                        worst_overreach_m=worst, land_yaw=math.degrees(ya), land_pitch=math.degrees(pa),
                        land_roll=math.degrees(ra), contact=con["wheel"])
        return J

    def objective(self, x, take, T_air, dt=1.0 / 600, detail=False):
        prof = self.profile(take, T_air, x)
        rec, con = self.A.run_inverse(take, prof, b=x[4], t_b=x[5], dt=dt, rec_dt=1.0 / 30, t_max=T_air + 0.5)
        if con is None:
            return 1e6
        return self.rider_cost(rec, con, x, detail)

    def optimise(self, take, T_air, maxiter=600):
        self.lm = RD.neutral_landmarks()
        lo = np.array([-300, -500, 0.80, 0.70, -0.6, 0.4])
        hi = np.array([300, 500, 1.06, 1.20, 0.6, 1.6])
        f = lambda z: self.objective(np.clip(z, lo, hi), take, T_air) + 1e3 * np.sum((z - np.clip(z, lo, hi)) ** 2)
        best = None
        t0 = time.time()
        for x0 in ([60, -150, 1.0, 1.0, 0.0, 0.9], [120, -300, 0.95, 1.0, 0.2, 0.9], [0, -50, 1.0, 1.0, -0.2, 1.1]):
            res = minimize(f, np.array(x0, float), method="Nelder-Mead",
                           options=dict(maxiter=maxiter, xatol=0.5, fatol=1e-3, adaptive=True))
            if best is None or res.fun < best.fun:
                best = res
        best.x = np.clip(best.x, lo, hi)
        return best, time.time() - t0

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
        # optimise, then make the prescribed landing time equal the actual first contact and repeat
        el = 0.0
        for it in range(4):
            res, e = self.optimise(take, T_air, maxiter=maxiter)
            el += e
            det = self.objective(res.x, take, T_air, dt=1.0 / 1200, detail=True)
            print(f"    pass {it}: T_air {T_air:.4f} -> contact {det['t_air']:.4f}, J {det['J']:.3f}", flush=True)
            if abs(det["t_air"] - T_air) < 0.01:
                break
            T_air = float(det["t_air"])
        print(f"[3] whip optimised in {el:.0f}s, {res.nit} it: {json.dumps({k: round(v, 3) for k, v in det.items()})}")
        prof = self.profile(take, T_air, res.x)
        recA, con = self.A.run_inverse(take, prof, b=res.x[4], t_b=res.x[5], dt=1.0 / 1200, rec_dt=1.0 / FPS_SIM,
                                       t_max=T_air + 0.5)
        rec_g2 = self.landing(recA, con)
        log.update(dict(mass_total=self.S.M, mass_bike=self.S.mb, mass_rider=self.S.mr, t_off=t_off, take=take, whip_x=list(map(float, res.x)), detail=det, contact_wheel=con["wheel"],
                        t_air=con["t"], L0=list(map(float, self.A.L0))))
        return log, rec_g1, recA, con, rec_g2


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
