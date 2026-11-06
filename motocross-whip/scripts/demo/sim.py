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
import whip_measured as WM
from pose import Poser, quat_from_matrix

FPS_SIM = 120
DEG = math.pi / 180

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

    # ---------- whip: Damien's whip as measured from his clips (whip_measured.py)
    # What his camera behind the ramp shows is fixed: how the bike turns in the picture, how side-on it is, and
    # how far his torso leans. What it cannot show is solved so that angular momentum is conserved and his body
    # stays human: the bike tipping toward or away from the camera, and how far he turns and pitches his torso.
    # Those hidden angles are smooth curves through knots the optimiser places; the closed-loop rider then flies
    # the combined target with the full physics (gyro, throttle, steering, reach, momentum).
    HID_T = (0.20, 0.40, 0.65, 0.90, 1.15, 1.50)       # hidden-angle knot times, Damien's timeline (s)
    _n = len(HID_T)
    X_NAMES = (("yaw_kick", "roll_kick", "dW", "t_straight")
               + tuple(f"depth_{t:.2f}" for t in HID_T) + tuple(f"torso_yaw_{t:.2f}" for t in HID_T)
               + tuple(f"torso_pitch_{t:.2f}" for t in HID_T)
               + ("lg_w_bike_drop", "lg_w_hidden", "lg_w_torso", "lg_w_bike_hold", "lg_w_torso_pitch"))
    #   yaw_kick, roll_kick : rotation rates (deg/s) the lip gives as he throws the rear out and lays the bike over
    #   dW                  : takeoff pitch-rate change (deg/s), realised afterwards as a lift on the bars at the lip
    #   t_straight          : when he starts pulling it straight (s, Damien's timeline), within what his cameras allow
    #   depth_*             : bike tipped toward (+) or away from the camera, about the unseen axis (deg)
    #   torso_yaw_*, torso_pitch_*: his torso turned left (+) and pitched nose-up (+) in the world (deg)
    #   lg_w_bike_drop      : log10 how firmly he steers the bike while the gyro drops the nose (peak to 1.1 s)
    #   lg_w_bike_hold      : log10 how firmly he steers it while holding the cross-up (1.1 s to the straighten)
    #   lg_w_torso_pitch    : log10 how firmly he keeps his torso from pitching over the bars (relative to his lean)
    #   lg_w_hidden         : log10 how firmly the hidden angles are held at their knots (low = physics decides)
    #   lg_w_torso          : log10 how firmly he holds his torso lean
    LO = np.array([-150.0, -450.0, -10.0, WM.T_STRAIGHT_RANGE[0]] + [-60.0] * _n + [-70.0] * _n + [-85.0] * _n
                  + [-2.0, -2.0, -1.0, -2.0, -2.0])
    HI = np.array([350.0, 100.0, 19.0, WM.T_STRAIGHT_RANGE[1]] + [60.0] * _n + [70.0] * _n + [60.0] * _n
                  + [0.0, 0.0, 1.0, 0.5, 0.5])
    X0 = np.array([5.398, -59.721, 18.970, 1.824, 43.342, -59.624, -57.841, -57.758, 10.989, 5.118, -67.286,
                   -28.839, -40.090, 2.441, -6.712, 64.657, -4.385, 4.703, -4.190, 57.930, -23.601, -15.308,
                   -1.231, -1.829, -0.113, -0.997, 0.498])   # best flight of the full CMA-ES search (2026-11-06)
    SEEN_RMS_OK = 35.0       # regression bound for the match to Damien's footage (best search result 29.9 deg)
    HOLD_START = 1.10        # s, Damien's timeline: the nose has dropped to hanging; he holds and lifts it
    PEAK_END = 0.45          # s, Damien's timeline: lay-down and flat peak are steered firmly up to here (f43)

    def keys(self, take, x):
        """Measured key table on Damien's timeline (target_fn scales it to this jump's airtime)."""
        return WM.table(math.degrees(take["beta"]), self.landing_pitch, t_straight=float(x[3]))

    @staticmethod
    def unseen_axis(R):
        """World axis the camera behind cannot see the bike rotate about: perpendicular to the line of sight (x)
        and to the bike's long axis as projected in the picture."""
        n = np.array([0.0, R[1, 0], R[2, 0]])
        nn = np.linalg.norm(n)
        n = n / nn if nn > 1e-6 else np.array([0.0, 1.0, 0.0])
        return np.cross([1.0, 0.0, 0.0], n)

    def target_fn(self, take, T_air, x):
        """Controller target f(t) -> (R_bike, omega_bike, R_torso). f.seen(t) -> (R_bike_measured, torso_lean_deg):
        what the footage shows, used to score the flight."""
        sc = T_air / WM.T_DAMIEN
        tab = self.keys(take, x)
        tab[:, 0] *= sc
        rate0 = math.degrees(take["W"])
        b0, b1 = math.degrees(take["beta"]), self.landing_pitch
        n = self._n
        t_s = float(x[3]) * sc
        t_ok = min(t_s + WM.STRAIGHTEN * sc, T_air - 0.02)
        kt = np.array([0.0] + [v * sc for v in self.HID_T] + [t_s, t_ok, T_air])
        dep = np.array([0.0] + list(x[4:4 + n]) + [0.0, 0.0, 0.0])
        tyaw = np.array([0.0] + list(x[4 + n:4 + 2 * n]) + [float(x[4 + 2 * n - 1]), 0.0, 0.0])
        tpit = np.array([b0] + list(x[4 + 2 * n:4 + 3 * n]) + [float(x[4 + 3 * n - 1]), b1, b1])
        w_drop, w_hid, w_hold = 10.0 ** float(x[4 + 3 * n]), 10.0 ** float(x[5 + 3 * n]), 10.0 ** float(x[7 + 3 * n])
        w_pit = 10.0 ** float(x[8 + 3 * n])
        t_peak, t_hold = self.PEAK_END * sc, self.HOLD_START * sc
        h = 1e-3

        def seen(t):
            d, y, p, r, rr = (float(v) for v in WM.params_at(t, tab, pitch_rate0=rate0, yaw_rate0=float(x[0]),
                                                             roll_rate0=float(x[1])))
            return WM.attitude(d, y, p, r), rr

        def parts(t):
            Rm, rr = seen(t)
            tc = min(max(t, 0.0), T_air)
            dd = math.radians(float(air.pchip(kt, dep, tc)))
            RA = air.expm_so3(dd * self.unseen_axis(Rm)) @ Rm
            ty = math.radians(float(air.pchip(kt, tyaw, tc)))
            tp = math.radians(float(air.pchip(kt, tpit, tc, m0=rate0)))
            return RA, air.Rz(ty) @ air.Ry(-tp) @ air.Rx(math.radians(rr))

        def f(t):
            R0, RB0 = parts(t)
            R1, _ = parts(t + h)
            whip = t < t_s
            Wb = self.soft_axis(self.unseen_axis(R0), w_hid) if whip else np.eye(3)
            if whip and t > t_peak:
                Wb = math.sqrt(w_drop if t < t_hold else w_hold) * Wb
            # torso: lean (about the travel direction) as filmed; pitch held at w_pit; turn (yaw) loosely
            Wr = (np.diag([1.0, 0.0, 0.0]) + math.sqrt(w_pit) * np.outer(RB0[:, 1], RB0[:, 1])
                  + math.sqrt(w_hid) * np.diag([0.0, 0.0, 1.0])) if whip else np.eye(3)
            return R0, air.logm_so3(R1 @ R0.T) / h, RB0, Wb, Wr
        f.seen = seen
        f.t_straight = t_s
        return f

    @staticmethod
    def soft_axis(w, weight):
        """sqrt weight matrix: full weight except `weight` about axis w."""
        return np.eye(3) - (1.0 - math.sqrt(weight)) * np.outer(w, w)

    def gains(self, T_air, x):
        """Controller settings: one place, used by the optimiser and the recorded flight."""
        return {"w_rider": 10.0 ** float(x[6 + 3 * self._n])}

    @staticmethod
    def torso_lean(RB):
        """His torso lean as seen from behind (deg, head to his left negative) and how clearly it shows (0..1)."""
        z = RB[:, 2]
        return math.degrees(math.atan2(-z[1], z[2])), math.hypot(z[1], z[2])

    RIDER_SPIN_MAX = 6.0     # rad/s: faster body rotation than this is a tumble, not riding
    DEPTH_WEIGHT = 0.05      # scoring weight on bike rotation the camera behind cannot see

    # How precisely the footage shows each feature (research/whip-attitude-measured.md, Uncertainty)
    SD_IMG, SD_ROUND, SD_LEAN = 10.0, 0.15, 15.0

    @staticmethod
    def features(RA, RB=None):
        """What the camera straight behind sees: axle-line angle in the picture (deg), wheel roundness (0 edge-on,
        1 side-on), which way the seat faces in the picture (deg), torso lean (deg) and whether his head is up."""
        n, yb, zb = RA[:, 0], RA[:, 1], RA[:, 2]
        f = {"img": math.degrees(math.atan2(-n[2], n[1])), "round": abs(float(yb[0])),
             "top": math.degrees(math.atan2(-zb[1], zb[2]))}
        if RB is not None:
            z = RB[:, 2]
            f["lean"] = math.degrees(math.atan2(-z[1], z[2]))
            f["lean_vis"] = math.hypot(z[1], z[2])
            f["head_up"] = float(z[2])
        return f

    @staticmethod
    def wrap(a):
        return (a + 180.0) % 360.0 - 180.0

    def seen_error(self, Fm, Fs):
        """Feature mismatch in 'degrees of picture angle' (each feature scaled by how precisely it is measured).
        The axle-line angle is ambiguous by 180 deg only when the bike points straight at the camera; the seat
        direction resolves it."""
        e_img = self.wrap(Fs["img"] - Fm["img"])
        e_round = (Fs["round"] - Fm["round"]) / self.SD_ROUND * self.SD_IMG
        e_top = self.wrap(Fs["top"] - Fm["top"]) * 0.5
        return e_img, e_round, e_top

    def ctrl_cost(self, rec, con, x, T_air, detail=False, take=None, f=None):
        """The whole whip looks like Damien's from his camera, the landing is straight, the body stays human."""
        arm = RD.L_UPPER_ARM + RD.L_FOREARM + RD.L_HAND_GRIP
        leg = RD.L_THIGH + RD.L_SHANK
        Lmax = np.array([arm + RD.SCAPULA_REACH, arm + RD.SCAPULA_REACH, leg, leg])
        reach = seen = lean = body = 0.0
        n_s = 0
        worst = -1.0
        spin = 0.0
        head_min = 1.0
        for r in rec:
            d = self.A.att_L + r["reach_err"]
            reach += float((np.maximum(d - 0.97 * Lmax, 0) ** 2).sum() + (np.maximum(0.40 * Lmax - d, 0) ** 2).sum())
            worst = max(worst, float((d - Lmax).max()))
            Fs = self.features(r["RA"], r["RB"])
            if r["t"] <= T_air:
                Rm, rr = f.seen(r["t"])
                if r["t"] < f.t_straight:
                    Fm = self.features(Rm)
                    seen += sum(e * e for e in self.seen_error(Fm, Fs))
                else:                                   # straighten and landing: full 3D attitude
                    seen += math.degrees(float(np.linalg.norm(air.logm_so3(Rm @ r["RA"].T)))) ** 2
                lean += Fs["lean_vis"] * (self.wrap(Fs["lean"] - rr) / self.SD_LEAN * self.SD_IMG) ** 2
                n_s += 1
            head_min = min(head_min, Fs["head_up"])
            yb, pb, rb = (math.degrees(v) for v in air.euler_of(r["RB"]))
            # head stays above his hips (he never goes upside down), torso turned at most 70 deg; no tumbling
            body += max(0.35 - Fs["head_up"], 0) ** 2 * 4e4 + max(abs(yb) - 70.0, 0) ** 2
            ws = float(np.linalg.norm(r["wB"]))
            spin = max(spin, ws)
            body += (max(ws - self.RIDER_SPIN_MAX, 0) * 20.0) ** 2
        n = len(rec)
        reach = reach / n / 0.02 ** 2
        seen_rms = math.sqrt(seen / max(n_s, 1))
        lean_rms = math.sqrt(lean / max(n_s, 1))
        body = body / n / 10.0 ** 2
        ya, pa, ra = (math.degrees(v) for v in air.euler_of(con["RA"]))
        rel_c = math.degrees(np.linalg.norm(air.logm_so3(con["RB"].T @ con["RA"])))
        land = (ya / 4) ** 2 + (ra / 4) ** 2 + ((pa - self.landing_pitch) / 3) ** 2 + (rel_c / 10) ** 2
        reg = (x[0] / 300) ** 2 + (x[1] / 400) ** 2 + (x[2] / 40) ** 2
        J = (seen_rms / 5) ** 2 + (lean_rms / 10) ** 2 + land + reach + body + 0.3 * reg
        if detail:
            return dict(J=J, seen_rms_deg=seen_rms, torso_lean_rms_deg=lean_rms, body=body, reach=reach,
                        worst_overreach_m=worst, head_up_min=head_min, land_yaw=ya, land_pitch=pa, land_roll=ra,
                        rider_rel_at_contact_deg=rel_c, reg=reg, rider_spin_max_deg_s=math.degrees(spin),
                        t_air=con["t"], contact=con["wheel"], x={k: float(v) for k, v in zip(self.X_NAMES, x)})
        return J

    KICK_BIKE_ONLY = False   # the lip sends bike and rider off rotating together (he rolls left with the bike)

    def objective(self, x, take, T_air, dt=1.0 / 600, detail=False):
        tk = dict(take)
        tk["W"] = take["W"] + math.radians(x[2])
        f = self.target_fn(tk, T_air, x)
        rec, con = self.A.run_control(tk, f, r0=math.radians(x[0]), p0=math.radians(x[1]),
                                      dt=dt, rec_dt=1.0 / 30, t_max=T_air + 0.6, T_land=T_air,
                                      gains=self.gains(T_air, x), kick_bike_only=self.KICK_BIKE_ONLY)
        if con is None:
            return 1e6
        return self.ctrl_cost(rec, con, x, T_air, detail, take=tk, f=f)

    def optimise(self, take, T_air, x0, sigma=0.25, gens=60, fix_dW=None, seed=1):
        """CMA-ES over the inputs, normalised to their allowed ranges; the population is evaluated on all
        cores (fork shares this pipeline). fix_dW holds the takeoff-rotation change (once the lip pull is real)."""
        import cma
        import concurrent.futures as cf
        import multiprocessing as mp
        global _OPT_CTX
        lo, hi = self.LO.copy(), self.HI.copy()
        if fix_dW is not None:
            lo[2] = hi[2] = fix_dW
        free = np.where(hi - lo > 1e-9)[0]
        span = hi - lo
        u0 = np.clip((np.asarray(x0, float) - lo) / np.where(span > 0, span, 1.0), 0.0, 1.0)[free]
        _OPT_CTX = (self, take, T_air, lo, hi, free)
        es = cma.CMAEvolutionStrategy(list(u0), sigma, {"bounds": [0.0, 1.0], "seed": seed, "verbose": -9,
                                                         "popsize": 16, "maxiter": gens, "tolfun": 1e-3})
        t0 = time.time()
        with cf.ProcessPoolExecutor(max_workers=4, mp_context=mp.get_context("fork")) as ex:
            while not es.stop():
                U = es.ask()
                es.tell(U, list(ex.map(_opt_worker, U)))
                if es.countiter % 5 == 0:
                    xb = _u_to_x(es.result.xbest, lo, hi, free)
                    print(f"      gen {es.countiter:3d}: best J {es.result.fbest:.3f} (median now {float(np.median(es.fit.fit)):.1f},"
                          f" sigma {es.sigma:.3f}) x {[round(float(v), 2) for v in xb]}", flush=True)

        class Res:
            pass
        res = Res()
        res.fun, res.x = float(es.result.fbest), _u_to_x(es.result.xbest, lo, hi, free)
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
    def fly(self, take, x, T_air):
        """The recorded flight: exactly the controller settings the optimiser scored."""
        return self.A.run_control(take, self.target_fn(take, T_air, x), r0=math.radians(x[0]), p0=math.radians(x[1]),
                                  dt=1.0 / 1200, rec_dt=1.0 / FPS_SIM, t_max=T_air + 0.6, T_land=T_air,
                                  gains=self.gains(T_air, x), kick_bike_only=self.KICK_BIKE_ONLY)

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

    # CMA-ES refinement around X0 (the best flight found by the full search, see research/whip-attitude-measured.md;
    # a fresh full search is sigma 0.25 and about 100 generations)
    SIGMA0, GENS = 0.06, 20

    def run_all(self, out_dir, face_throttle=None):
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
        x0, sigma, gens = self.X0.copy(), self.SIGMA0, self.GENS
        for it in range(4):
            res, e = self.optimise(take_nom, T_air, x0, sigma=sigma, gens=gens, seed=it + 1)
            el += e
            det = self.objective(res.x, take_nom, T_air, dt=1.0 / 1200, detail=True)
            print(f"    pass {it}: T_air {T_air:.4f} -> contact {det['t_air']:.4f}, J {det['J']:.3f}, "
                  f"x {[round(float(v), 3) for v in res.x]}", flush=True)
            with open(f"{out_dir}/whip_pass{it}.json", "w") as f:
                json.dump({"T_air": T_air, "x": [float(v) for v in res.x], "detail": _jsonable(det)}, f)
            if abs(det["t_air"] - T_air) < 0.01:
                break
            T_air = float(det["t_air"])
            x0, sigma, gens = res.x, 0.04, max(gens // 2, 10)
        # realise the takeoff rotation change in the ground model (rider lifts on the bars at the lip)
        pull = self.solve_lip_pull(v, take_nom["W"] + math.radians(res.x[2]))
        t_off, st, sp, rec_g1 = self.to_takeoff(v)
        take = self.take_from(st, sp, rec_g1)
        print(f"    lip pull {pull:.0f} N -> takeoff rotation {math.degrees(take['W']):.2f} deg/s "
              f"(wanted {math.degrees(take_nom['W']) + res.x[2]:.2f})", flush=True)
        # final stage: re-optimise the remaining inputs on the REAL takeoff state (rotation change now physically
        # inside the takeoff), iterating the landing time to the actual contact
        x0 = np.array(res.x, float)
        x0[2] = 0.0
        sigma, gens = 0.05, self.GENS
        for it in range(4):
            res2, e = self.optimise(take, T_air, x0, sigma=sigma, gens=gens, fix_dW=0.0, seed=11 + it)
            el += e
            det = self.objective(res2.x, take, T_air, dt=1.0 / 1200, detail=True)
            print(f"    final pass {it}: T_air {T_air:.4f} -> contact {det['t_air']:.4f}, J {det['J']:.3f}, "
                  f"x {[round(float(v), 3) for v in res2.x]}", flush=True)
            if abs(det["t_air"] - T_air) < 0.01:
                break
            T_air = float(det["t_air"])
            x0, sigma, gens = res2.x, 0.04, max(self.GENS // 2, 10)
        x_real = np.array(res2.x, float)
        print(f"[3] whip optimised in {el:.0f}s: "
              f"{json.dumps({k: (round(float(v), 3) if isinstance(v, (int, float, np.floating)) else v) for k, v in det.items()})}")
        recA, con = self.fly(take, x_real, T_air)
        res.x = x_real
        log["lip_pull_N"] = pull
        log["T_air_target"] = T_air
        rec_g2 = self.landing(recA, con)
        log.update(dict(mass_total=self.S.M, mass_bike=self.S.mb, mass_rider=self.S.mr, t_off=t_off, take=take, whip_x=list(map(float, res.x)), detail=det, contact_wheel=con["wheel"],
                        t_air=con["t"], L0=list(map(float, self.A.L0))))
        return log, rec_g1, recA, con, rec_g2


_OPT_CTX = None


def _u_to_x(u, lo, hi, free):
    x = lo.copy()
    x[free] = lo[free] + np.clip(np.asarray(u, float), 0.0, 1.0) * (hi - lo)[free]
    return x


def _opt_worker(u):
    pl, take, T_air, lo, hi, free = _OPT_CTX
    return float(pl.objective(_u_to_x(u, lo, hi, free), take, T_air))


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
        if "--refly" in sys.argv:
            pl.S.lip_pull = log.get("lip_pull_N", 0.0)
            T_air = float(sys.argv[sys.argv.index("--refly") + 1]) if len(sys.argv) > sys.argv.index("--refly") + 1 \
                and not sys.argv[sys.argv.index("--refly") + 1].startswith("-") else log.get("T_air_target", log["t_air"])
            ra, con = pl.fly(log["take"], np.array(log["whip_x"]), T_air)
            g2 = pl.landing(ra, con)
            log["detail"] = pl.objective(np.array(log["whip_x"]), log["take"], T_air, dt=1.0 / 1200, detail=True)
            log.update(T_air_target=T_air, t_air=con["t"], contact_wheel=con["wheel"], L0=list(map(float, pl.A.L0)))
            print("[refly]", json.dumps(_jsonable({k: (round(float(v), 3) if isinstance(v, (int, float, np.floating)) else v)
                                                   for k, v in log["detail"].items()})))
            with open(f"{out}/records.pkl", "wb") as f:
                pickle.dump((log, g1, ra, con, g2, T_face), f)
    else:
        ft = float(sys.argv[sys.argv.index("--face-throttle") + 1]) if "--face-throttle" in sys.argv else None
        log, g1, ra, con, g2 = pl.run_all(out, face_throttle=ft)
        with open(f"{out}/records.pkl", "wb") as f:
            pickle.dump((log, g1, ra, con, g2, pl.S.T_face), f)
    np.savez(f"{out}/flight.npz", t=np.array([r["t"] for r in ra]), RA=np.array([r["RA"] for r in ra]),
             RB=np.array([r["RB"] for r in ra]))         # for scripts/analysis/attitude_overlay.py --sim
    info = export.build(pl, log, g1, ra, con, g2, out)
    log["export"] = info
    with open(f"{out}/summary.json", "w") as f:
        json.dump(_jsonable(log), f, indent=1)
    print("[4] export", json.dumps(_jsonable(info)))
