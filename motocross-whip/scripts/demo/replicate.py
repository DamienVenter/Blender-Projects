"""Damien's whip, replicated exactly and smoothly (research/whip-attitude-measured.md, section 3D).

What comes from where:
- Bike attitude in the air: the two-phone 3D measurement (clips 2 and 3 are one jump filmed by two phones,
  research/whip-attitude-3d/fit_clips23.json), through a smooth quaternion spline. The straighten and touchdown
  timing come from clip 1 (still crossed up at 2.0 s, straightened in about 0.18 s).
- Run-in, ramp, takeoff, centre-of-mass flight (gravity, drag), suspension and landing: the physics simulation.
- Rider: torso lean as filmed. What the cameras cannot see (how far he turns and pitches his torso, his hip shift
  and spine, the rear wheel speed) is solved so that his hands stay on the grips and feet on the pegs and the total
  angular momentum stays as constant as possible. The lip kick (angular momentum the ramp gives) is solved too.
  The remaining momentum mismatch is reported: it is the physics check of the whole reconstruction.

python3 replicate.py OUT_DIR       (writes the same files as sim.py: frames.json, hud.json, summary.json, ...)
python3 replicate.py OUT_DIR --reexport   (export again from OUT_DIR/records.pkl, skipping the solve)
"""
import json
import math
import os
import sys
import time

import numpy as np
from scipy.interpolate import LSQUnivariateSpline, CubicSpline, PchipInterpolator
from scipy.optimize import least_squares

import params as P
import rider as RD
import air
import sim
import whip_measured as WM
from air import Rx, Ry, Rz, EY
from pose import quat_from_matrix, matrix_from_quat

HERE = os.path.dirname(os.path.abspath(__file__))
FIT = os.path.join(HERE, "..", "..", "research", "whip-attitude-3d", "fit_clips23.json")
FPS_OUT = 120

# Damien's torso lean seen from behind (deg, head to his left negative) on the clips 2 and 3 jump, read off the
# frames (rider horizontal at the flat peak, upright once the bike hangs in profile)
LEAN_T = [0.00, 0.10, 0.20, 0.30, 0.40, 0.53, 0.67, 0.80, 0.93, 1.07, 1.20, 2.20]
LEAN = [0.0, -25.0, -50.0, -65.0, -70.0, -55.0, -40.0, -25.0, -15.0, -5.0, 0.0, 0.0]
_LEAN = PchipInterpolator(LEAN_T, LEAN)


def lean_filmed(t_damien):
    """Filmed torso lean (deg) at Damien's time: a smooth monotone curve through the readings (straight lines between
    them would flip the lean rate at every reading, a visible jerk at his deepest lean)."""
    return _LEAN(np.clip(t_damien, LEAN_T[0], LEAN_T[-1]))


T_HOLD_END = 1.97        # s, Damien's timeline: still crossed up (clip 1 f89; clip 3 loses him at about 2.0 s)


R_of_q = matrix_from_quat


class BikeAttitude:
    """Smooth bike attitude R_A(t) (t = s after the lip, simulation clock; defined from 0.2 s before the lip)."""
    INIT_T = 0.10            # s on the lip: the rear tyre is the last contact (front wheel left about 0.09 s earlier)

    def __init__(self, beta0, rate0, landing_pitch, T_air):
        fit = json.load(open(FIT))
        sc = T_air / WM.T_DAMIEN
        qf = lambda R: quat_from_matrix(R)
        dense = 1.0 / 120
        ts, qs, ws = [], [], []

        def add(t, R, w):
            ts.append(t); qs.append(qf(R)); ws.append(w)

        def slerp(R0, R1, s):
            return air.expm_so3(air.logm_so3(R1 @ R0.T) * s) @ R0

        ease = lambda s: s * s * (3 - 2 * s)
        # he starts the whip on the lip itself (clips 2 and 3: already turning at the lip frame). The air phase starts
        # at the measured lip attitude. The samples before the lip only shape the curve's rate through it (the air
        # phase uses t >= 0); on the ramp, export bends the ramp simulation's attitude onto this one (export.LIP_T).
        R_lip = np.array(fit[str(min(map(int, fit)))]["R"])
        self.R_lip, self.R_ramp0 = R_lip, Ry(-beta0)
        # one curve through the lip: the ramp's attitude until INIT_T before it, the measured lip attitude at it
        for t in np.arange(-0.22, -self.INIT_T + 1e-9, dense):
            add(t, Ry(-(beta0 + rate0 * t)), 10.0)
        add(0.0, R_lip, 4.0)
        for t in np.arange(-self.INIT_T + dense, 0.0, dense):
            add(t, slerp(Ry(-(beta0 + rate0 * t)), R_lip, ease(1.0 + t / self.INIT_T)), 0.3)
        meas = [(fit[k]["t"] * sc, np.array(fit[k]["R"])) for k in sorted(fit, key=int) if fit[k]["t"] * sc > 0.02]
        for t, R in meas:                                   # measured, 30 per second (weight for density); the two
            add(t, R, 4.0 if t > 0.09 else 0.5)            # frames right off the lip are the noisiest (motion blur)
        t1, R1 = [(t, R) for t, R in meas if t > 0.09][0]   # regularise the first 0.1 s: eased lip-to-frame path
        for t in np.arange(dense, t1, dense):
            add(t, slerp(R_lip, R1, ease(t / t1)), 0.6)
        t_last, R_last = meas[-1]
        t_s = T_HOLD_END * sc
        t_ok = min(t_s + WM.STRAIGHTEN * sc, T_air - 0.03)
        R_land = Ry(-math.radians(landing_pitch))
        for t in np.arange(t_last + dense, t_s, dense):     # still crossed up until he drops behind the knuckle
            add(t, R_last, 1.0)
        for t in np.arange(t_s, t_ok, dense):               # pulled straight (clip 1 shot B: about 0.18 s)
            add(t, slerp(R_last, R_land, ease((t - t_s) / (t_ok - t_s))), 1.0)
        for t in np.arange(t_ok, T_air + 0.15, dense):
            add(t, R_land, 6.0)
        order = np.argsort(ts)
        ts, q, w = np.array(ts)[order], np.array(qs)[order], np.array(ws)[order]
        for i in range(1, len(q)):                          # sign continuity
            if q[i] @ q[i - 1] < 0:
                q[i] = -q[i]
        knots = list(np.arange(-0.17, t_s - 0.05, 0.10)) + list(np.arange(t_s - 0.05, t_ok + 0.08, 0.035)) \
            + list(np.arange(t_ok + 0.1, ts[-1] - 0.05, 0.1))
        self.spl = [LSQUnivariateSpline(ts, q[:, j], knots, w=w, k=3) for j in range(4)]
        self.t0, self.t1 = ts[0], ts[-1]
        self.samples = ([t for t, R in meas], [R for t, R in meas])
        self.t_s, self.t_ok = t_s, t_ok

    def q(self, t):
        t = min(max(t, self.t0), self.t1)
        v = np.array([s(t) for s in self.spl])
        return v / np.linalg.norm(v)

    def R(self, t):
        return R_of_q(self.q(t))


class Replicator:
    def __init__(self, pl, take, T_air):
        self.pl, self.A, self.S = pl, pl.A, pl.S
        self.take, self.T_air = take, T_air
        self.sc = T_air / WM.T_DAMIEN
        self.bike = BikeAttitude(take["beta"], take["W"], pl.landing_pitch, T_air)
        self.beta0 = take["beta"]
        arm = RD.L_UPPER_ARM + RD.L_FOREARM + RD.L_HAND_GRIP
        leg = RD.L_THIGH + RD.L_SHANK
        self.Lmax = np.array([arm + RD.SCAPULA_REACH, arm + RD.SCAPULA_REACH, leg, leg])
        self.knots = np.linspace(0.0, T_air, int(round(T_air / 0.15)) + 1)
        self.n = len(self.knots)

    # ---- hidden angles: x = [L0 kick (3)] + yaw knots + pitch knots + lean offset knots + rear wheel knots
    def unpack(self, x):
        n = self.n
        kick = x[:3]
        yaw = np.concatenate([[0.0], x[3:3 + n - 1]])
        pit = np.concatenate([[0.0], x[3 + n - 1:3 + 2 * (n - 1)]])
        dle = np.concatenate([[0.0], x[3 + 2 * (n - 1):3 + 3 * (n - 1)]])
        whl = np.concatenate([[0.0], x[3 + 3 * (n - 1):3 + 4 * (n - 1)]])
        return kick, yaw, pit, dle, whl

    def n_x(self):
        return 3 + 4 * (self.n - 1)

    def torso_pitch_ref(self, t):
        """His torso pitched along the flight path (takeoff pitch to landing pitch), deg."""
        b0, b1 = math.degrees(self.beta0), self.pl.landing_pitch
        return b0 + (b1 - b0) * min(max(t / self.T_air, 0.0), 1.0)

    def series(self, x, tg):
        """Everything along the time grid tg for hidden-angle vector x."""
        A, S = self.A, self.S
        kick, yaw, pit, dle, whl = self.unpack(x)
        cs = lambda v: CubicSpline(self.knots, v, bc_type="clamped")
        fy, fp, fd, fw = cs(yaw), cs(pit), cs(dle), cs(whl)
        lean = lean_filmed(np.asarray(tg) / self.sc)
        out = []
        q = np.zeros(6)
        wr0 = self.take["wr"]
        for i, t in enumerate(tg):
            RA = self.bike.R(t)
            ry = math.radians(float(fy(t)))
            rp = math.radians(self.torso_pitch_ref(t) + float(fp(t)))
            rl = math.radians(lean[i] + float(fd(t)))
            RB = Rz(ry) @ Ry(-rp) @ Rx(rl)
            q, _ = A.posture(RA.T @ RB, q, iters=4)
            hip, spine = q[:3].copy(), q[3:].copy()
            nh = np.linalg.norm(hip)
            if nh > A.SHIFT_MAX:
                hip *= A.SHIFT_MAX / nh
            wr = wr0 * float(np.clip(1.0 + fw(t), 0.0, A.WR_MAX_RATIO))
            out.append((RA, RB, hip, spine, wr))
        return out

    def momentum(self, ser, tg):
        """Angular momentum about the system CoM along the grid (central differences)."""
        A = self.A
        If, Ir = P.WHEEL_SPIN_INERTIA_FRONT, P.WHEEL_SPIN_INERTIA_REAR
        Ds = [RA @ (A.p_rel + hip) + RB @ (A.cB + A.upper_shift(spine)) for RA, RB, hip, spine, wr in ser]
        L, W = [], []
        for i in range(len(tg)):
            a, b = max(i - 1, 0), min(i + 1, len(tg) - 1)
            h = tg[b] - tg[a]
            RA, RB, hip, spine, wr = ser[i]
            wA = air.logm_so3(ser[b][0] @ ser[a][0].T) / h
            wB = air.logm_so3(ser[b][1] @ ser[a][1].T) / h
            Dd = (Ds[b] - Ds[a]) / h
            D = Ds[i]
            Lt = (RA @ A.IA @ RA.T) @ wA + (RB @ A.IB @ RB.T) @ wB + A.mu * np.cross(D, Dd) \
                + (If * self.take["wf"] + Ir * wr) * (RA @ EY)
            L.append(Lt); W.append((wA, wB))
        return np.array(L), W, Ds

    def L_takeoff(self):
        """Angular momentum the ramp gives with no kick (straight bike, rider in line, takeoff rotation)."""
        A = self.A
        RA = Ry(-self.beta0)
        w = np.array([0.0, -self.take["W"], 0.0])
        D = RA @ A.p_rel + RA @ A.cB
        M = RA @ A.IA @ RA.T + RA @ A.IB @ RA.T + A.mu * (np.dot(D, D) * np.eye(3) - np.outer(D, D))
        return M @ w + (P.WHEEL_SPIN_INERTIA_FRONT * self.take["wf"] + P.WHEEL_SPIN_INERTIA_REAR * self.take["wr"]) * (RA @ EY)

    # The measured whip cannot be flown by this two-body rider exactly (the momentum mismatch is reported). The body
    # is solved for: hands and feet on the bike (strict), lean as filmed, torso facing forward, smooth; momentum is
    # kept as close as that allows.
    SIG_L = 40.0            # kg m^2/s
    SIG_REACH = 0.004       # m
    def residuals(self, x, tg):
        ser = self.series(x, tg)
        L, W, Ds = self.momentum(ser, tg)
        kick, yaw, pit, dle, whl = self.unpack(x)
        L0 = self.L_takeoff() + kick
        r = [((L - L0) / self.SIG_L).ravel()]
        reach = []
        for RA, RB, hip, spine, wr in ser:
            d = np.sqrt((self.A.limb_vectors(RA.T @ RB, hip, spine) ** 2).sum(axis=1))
            reach.append(np.maximum(d - self.Lmax, 0.0) / self.SIG_REACH)
            reach.append(np.maximum(0.45 * self.Lmax - d, 0.0) / self.SIG_REACH)
        r.append(np.concatenate(reach))
        rel_end = air.logm_so3(ser[-1][0] @ ser[-1][1].T)
        r.append(np.degrees(rel_end) / 3.0)                      # back in the attack position at touchdown
        r.append(dle / 8.0)                                       # lean as filmed
        r.append(yaw / 45.0)                                      # torso facing the travel direction
        r.append(pit / 40.0)
        r.append(np.diff(yaw, 2) / 12.0); r.append(np.diff(pit, 2) / 12.0); r.append(np.diff(dle, 2) / 8.0)
        r.append(np.diff(whl, 2) / 0.3); r.append(whl / 0.6)
        r.append(kick / 150.0)
        return np.concatenate(r)

    def solve(self, dt=1.0 / 50, max_nfev=60):
        tg = np.arange(0.0, self.T_air + 1e-9, dt)
        x0 = np.zeros(self.n_x())
        t0 = time.time()
        sol = least_squares(self.residuals, x0, args=(tg,), method="trf", x_scale=1.0, max_nfev=max_nfev,
                            diff_step=1e-3, verbose=0)
        self.x = sol.x
        ser = self.series(sol.x, tg)
        L, W, Ds = self.momentum(ser, tg)
        kick = sol.x[:3]
        L0 = self.L_takeoff() + kick
        err = np.linalg.norm(L - L0, axis=1)
        over = max(float((np.sqrt((self.A.limb_vectors(RA.T @ RB, hip, sp) ** 2).sum(axis=1)) - self.Lmax).max())
                   for RA, RB, hip, sp, wr in ser)
        self.report = dict(solve_s=round(time.time() - t0, 1), cost=float(sol.cost), L0=list(map(float, L0)),
                           lip_kick=list(map(float, kick)), L_mismatch_rms=float(np.sqrt((err ** 2).mean())),
                           L_mismatch_max=float(err.max()), L0_norm=float(np.linalg.norm(L0)),
                           worst_overreach_m=over)
        return self.report

    # ---- records for export (same structure as AirSim.run_control) at FPS_OUT
    def records(self):
        dt = 1.0 / FPS_OUT
        tg = np.arange(0.0, self.T_air + 1e-9, dt)
        ser = self.series(self.x, tg)
        L, W, Ds = self.momentum(ser, tg)
        # light smoothing of the posture (hip shift, spine): no frame-to-frame jitter from the solver
        hips = np.array([s[2] for s in ser]); spines = np.array([s[3] for s in ser])
        from scipy.signal import savgol_filter
        if len(tg) > 15:
            hips = savgol_filter(hips, 15, 3, axis=0); spines = savgol_filter(spines, 15, 3, axis=0)
        C, V, sf, sr = self.flight_com(tg)
        recs = []
        for i, t in enumerate(tg):
            RA, RB, _, _, wr = ser[i]
            hip, spine = hips[i], spines[i]
            D = RA @ (self.A.p_rel + hip) + RB @ (self.A.cB + self.A.upper_shift(spine))
            reach = np.sqrt((self.A.limb_vectors(RA.T @ RB, hip, spine) ** 2).sum(axis=1)) - self.A.att_L
            recs.append({"t": float(t), "C": C[i], "V": V[i], "RA": RA, "RB": RB, "D": D, "wA": W[i][0], "wB": W[i][1],
                         "sf": sf[i], "sr": sr[i], "wf": self.take["wf"], "wr": wr, "shift": hip, "spine": spine,
                         "reach_err": reach, "track_err": 0.0, "w_rel": W[i][0] - W[i][1], "steer": 0.0})
        last = recs[-1]
        con = {k: last[k] for k in ("C", "V", "RA", "RB", "D", "sf", "sr", "wr", "wf", "shift", "spine", "steer")}
        con.update(t=last["t"], wheel=self.touch_wheel)
        return recs, con

    def flight_com(self, tg):
        """Centre of mass flight and air suspension from the physics (independent of the whip attitude)."""
        rec, con = self.pl.no_whip(self.take, dt=1.0 / 1200)
        self.touch_wheel = con["wheel"]
        ts = np.array([r["t"] for r in rec] + [con["t"]])
        C = np.array([r["C"] for r in rec] + [con["C"]]); V = np.array([r["V"] for r in rec] + [con["V"]])
        sfv = np.array([r["sf"] for r in rec] + [con["sf"]]); srv = np.array([r["sr"] for r in rec] + [con["sr"]])
        ip = lambda arr: np.array([np.interp(tg, ts, arr[:, k]) for k in range(arr.shape[1])]).T
        return ip(C), ip(V), np.interp(tg, ts, sfv), np.interp(tg, ts, srv)


def reexport(out):
    """Export again from OUT/records.pkl (no 6-minute re-solve): for changes to export.py, pose.py or rider.py."""
    import export
    import pickle
    with open(f"{out}/records.pkl", "rb") as f:
        log, rec_g1, recA, con, rec_g2, T_face = pickle.load(f)
    pl = sim.Pipeline()
    pl.S.T_face = T_face
    T_air = log["T_air_target"]
    bike = BikeAttitude(log["take"]["beta"], log["take"]["W"], pl.landing_pitch, T_air)
    sc = T_air / WM.T_DAMIEN
    info = export.build(pl, log, rec_g1, recA, con, rec_g2, out,
                        seen_fn=lambda t: (bike.R(t), float(lean_filmed(t / sc))))
    log["export"] = info
    with open(f"{out}/summary.json", "w") as f:
        json.dump(sim._jsonable(log), f, indent=1)
    print("[3] export", json.dumps(sim._jsonable(info)))


def main():
    import export
    import pickle
    out = sys.argv[1]
    if "--reexport" in sys.argv:
        return reexport(out)
    os.makedirs(out, exist_ok=True)
    pl = sim.Pipeline()
    pl.S.T_face = 1344.4                       # solved face throttle (sim.py records it)
    v = pl.solve_speed()
    t_off, st, sp, rec_g1 = pl.to_takeoff(v)
    take = pl.take_from(st, sp, rec_g1)
    _, con0 = pl.no_whip(take)
    T_air = con0["t"]
    print(f"[1] run-in {v:.3f} m/s, takeoff pitch {math.degrees(take['beta']):.1f} deg, rotation "
          f"{math.degrees(take['W']):.1f} deg/s, airtime {T_air:.3f} s", flush=True)
    rp = Replicator(pl, take, T_air)
    rep = rp.solve()
    print("[2] hidden angles solved:", json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rep.items()}), flush=True)
    recA, con = rp.records()
    rec_g2 = pl.landing(recA, con)
    log_init = {"T": export.LIP_T}
    ya, pa, ra = (math.degrees(a) for a in air.euler_of(con["RA"]))
    detail = dict(land_yaw=ya, land_pitch=pa, land_roll=ra, t_air=con["t"], contact=con["wheel"],
                  rider_rel_at_contact_deg=math.degrees(float(np.linalg.norm(air.logm_so3(con["RB"].T @ con["RA"])))))
    log = dict(mode="replicated", detail=detail, lip_initiation=log_init, approach_speed=v, face_throttle_N=pl.S.T_face, t_off=t_off, take=take,
               t_air=con["t"], T_air_target=T_air, contact_wheel=con["wheel"], replication=rep,
               mass_total=pl.S.M, mass_bike=pl.S.mb, mass_rider=pl.S.mr, lip_pull_N=0.0)
    with open(f"{out}/records.pkl", "wb") as f:
        pickle.dump((log, rec_g1, recA, con, rec_g2, pl.S.T_face), f)
    np.savez(f"{out}/flight.npz", t=np.array([r["t"] for r in recA]), RA=np.array([r["RA"] for r in recA]),
             RB=np.array([r["RB"] for r in recA]))
    info = export.build(pl, log, rec_g1, recA, con, rec_g2, out,
                        seen_fn=lambda t: (rp.bike.R(t), float(lean_filmed(t / rp.sc))))
    log["export"] = info
    with open(f"{out}/summary.json", "w") as f:
        json.dump(sim._jsonable(log), f, indent=1)
    print("[3] export", json.dumps(sim._jsonable(info)))


if __name__ == "__main__":
    main()
