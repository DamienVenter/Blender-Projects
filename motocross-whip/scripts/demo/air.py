"""Airborne dynamics: bike + rider as two rigid bodies plus spinning wheels.

The system centre of mass flies ballistically (gravity + aerodynamic drag).
Rotation obeys conservation of total angular momentum about the system CoM:

    L = I_A w_A + I_B w_B + mu D x dD/dt + L_wheels = L0     (constant)

A = bike, B = rider (rigid upper body), D = rider CoM - bike CoM,
mu = mA mB / M, L_wheels = (If wf + Ir wr) along the bike's axle (left).
The rider acts by rotating the bike relative to his body (R_A = R_B R_rel), by
shifting his hips (to keep hands on the grips and feet on the pegs), and by
throttle/brake on the rear wheel. Solving the conservation law each step gives
both absolute rotations. Gyroscopic coupling from the wheels is exact.

- run_rel: open-loop rider action (tests, experiments).
- run_control: closed-loop rider steering the bike toward a whip target (pipeline).
"""
import math
import numpy as np
import params as P
import bike as B

EX, EY, EZ = np.eye(3)


def cross(a, b):
    """Cross product for 3-vectors (numpy.cross has large overhead on tiny arrays)."""
    return np.array([a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]])


def skew(v):
    return np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]])


def expm_so3(w):
    th = math.sqrt(w[0] * w[0] + w[1] * w[1] + w[2] * w[2])
    if th < 1e-12:
        return np.eye(3) + skew(w)
    K = skew(w / th)
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def logm_so3(R):
    c = max(min((np.trace(R) - 1) / 2, 1.0), -1.0)
    th = math.acos(c)
    if th < 1e-9:
        return np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / 2
    return th / (2 * math.sin(th)) * np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler_from(yaw, pitch_up, roll):
    """Yaw about world Z (nose left +), nose-up pitch, roll about the long axis (right lean +)."""
    return Rz(yaw) @ Ry(-pitch_up) @ Rx(roll)


def euler_of(R):
    """Inverse of euler_from: (yaw, pitch_up, roll) in radians."""
    return (math.atan2(R[1, 0], R[0, 0]), math.asin(max(min(R[2, 0], 1.0), -1.0)), math.atan2(R[2, 1], R[2, 2]))


def pchip(xk, yk, x, m0=0.0, m1=0.0):
    """Monotone piecewise cubic Hermite interpolation (Fritsch-Carlson), end slopes m0, m1."""
    xk, yk = np.asarray(xk, float), np.asarray(yk, float)
    h = np.diff(xk)
    d = np.diff(yk) / h
    m = np.zeros_like(yk)
    for i in range(1, len(yk) - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0], m[-1] = m0, m1
    idx = np.clip(np.searchsorted(xk, x) - 1, 0, len(h) - 1)
    t = (x - xk[idx]) / h[idx]
    h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
    return h00 * yk[idx] + h10 * h[idx] * m[idx] + h01 * yk[idx + 1] + h11 * h[idx] * m[idx + 1]


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)


class AirSim:
    def __init__(self, sysm, terrain):
        S = sysm
        self.S, self.T = S, terrain
        self.mA, self.mB, self.M = S.mb, S.mr, S.M
        self.mu = S.mb * S.mr / S.M
        self.IA, self.IB = S.Ib, S.Ir
        self.cA = S.cb                      # bike CoM, bike frame
        self.cB = S.cr                      # rider CoM rel. peg midpoint, rider frame
        self.p_rel = S.peg - S.cb           # peg midpoint rel. bike CoM, bike frame
        # hands-on-grips / feet-on-pegs pairs: bike points g (bike frame, rel. peg midpoint) and
        # rider points h (rider frame, rel. rider origin), with their neutral distances
        import rider as RD
        lm = RD.neutral_landmarks()
        self.att_g = np.array([lm["grip_l"], lm["grip_r"], lm["ankle_l"], lm["ankle_r"]])
        self.att_h = np.array([lm["shoulder_l"], lm["shoulder_r"], lm["hip_l"], lm["hip_r"]])
        self.att_L = np.linalg.norm(self.att_g - self.att_h, axis=1)

    def body_shift(self, RrelT, s0, lam=0.6, iters=3):
        """Hip shift s (bike frame) that keeps hands on the grips and feet on the pegs.

        Least squares on the four limb lengths with a small pull back to neutral.
        RrelT = R_A^T R_B (rider orientation seen from the bike).
        """
        s = s0.copy()
        h = (RrelT @ self.att_h.T).T
        for _ in range(iters):
            v = self.att_g - s - h
            d = np.sqrt((v * v).sum(axis=1))
            r = d - self.att_L
            J = -v / d[:, None]
            A = J.T @ J + lam * np.eye(3)
            b = -(J.T @ r + lam * s)
            s = s + np.linalg.solve(A, b)
        v = self.att_g - s - h
        return s, np.sqrt((v * v).sum(axis=1)) - self.att_L

    def reach_errors(self, RrelT, s):
        """Limb length errors (m) for hip shift s: positive = stretched beyond neutral."""
        v = self.att_g - s - (RrelT @ self.att_h.T).T
        return np.sqrt((v * v).sum(axis=1)) - self.att_L

    # hip motion limits: hips follow the least-squares target like a body with mass and muscles
    SHIFT_TAU = 0.08          # s, response time
    SHIFT_VMAX = 2.0          # m/s, fastest hip movement relative to the bike
    SHIFT_MAX = 0.45          # m, anatomical range from the neutral attack pose

    def rel_rotations(self, ts, T_air, knots):
        """R_rel(t) from Euler knots {'f': fractions, 'yaw': deg, 'pitch': deg, 'roll': deg}."""
        fr = np.concatenate([[0.0], knots["f"], [1.0]]) * T_air
        ang = {k: np.radians(pchip(fr, np.concatenate([[0.0], knots[k], [0.0]]), np.clip(ts, 0, T_air)))
               for k in ("yaw", "pitch", "roll")}
        return [euler_from(ang["yaw"][i], ang["pitch"][i], ang["roll"][i]) for i in range(len(ts))]

    def run(self, take, whip, dt=1.0 / 1200.0, t_max=3.5, rec_dt=1.0 / 120.0, T_air_est=2.2, record=True):
        """Forward model with knot-based rider input (used by tests). See run_rel."""
        rel_fn = lambda t: self.rel_rotations(t, T_air_est, whip["knots"])
        return self.run_rel(take, rel_fn, r0=whip.get("r0", 0.0), p0=whip.get("p0", 0.0), b=whip.get("b", 0.0),
                            t_b=whip.get("t_b", 0.9), dt=dt, t_max=t_max, rec_dt=rec_dt, record=record,
                            use_shift=whip.get("use_shift", False))

    def hip_shift_track(self, Rrel_list, dt):
        """Rate-limited hip shift (bike frame) following the reach target for a known R_rel(t)."""
        out, rates = [], []
        s = np.zeros(3)
        for R in Rrel_list:
            target, _ = self.body_shift(R.T, s)
            nt = np.linalg.norm(target)
            if nt > self.SHIFT_MAX:
                target *= self.SHIFT_MAX / nt
            v = (target - s) / self.SHIFT_TAU
            sp = np.linalg.norm(v)
            if sp > self.SHIFT_VMAX:
                v *= self.SHIFT_VMAX / sp
            out.append(s.copy())
            rates.append(v)
            s = s + v * dt
        return out, rates

    def run_rel(self, take, rel_fn, r0=0.0, p0=0.0, b=0.0, t_b=0.9, dt=1.0 / 1200.0, t_max=3.5,
                rec_dt=1.0 / 120.0, record=True, use_shift=True):
        """Forward model: the rider's action R_rel(t) (bike relative to rider) is prescribed; the rider's
        and bike's absolute rotations follow from conservation of angular momentum (gyro included).

        rel_fn(t_array) -> list of 3x3 R_rel. r0, p0: yaw and roll rates (rad/s) given to the whole system
        off the lip. b: rear-wheel spin change (+ throttle, - brake) starting at t_b.
        """
        S = self.S
        n = int(t_max / dt) + 2
        ts = np.arange(n) * dt
        th = ts + dt / 2
        Rrel = rel_fn(ts)
        Rrel_h = rel_fn(th)
        wrel_h = [logm_so3(Rrel[i + 1] @ Rrel[i].T) / dt for i in range(n - 1)]
        wrel = [np.zeros(3)] + [0.5 * (wrel_h[i - 1] + wrel_h[i]) for i in range(1, n - 1)] + [wrel_h[-1]]
        if use_shift:
            shifts, shift_rates = self.hip_shift_track(Rrel, dt)
        else:
            shifts = shift_rates = [np.zeros(3)] * n
        wr_spin = take["wr"] * (1.0 + b * smoothstep((ts - t_b) / 0.15))
        wr_spin_h = take["wr"] * (1.0 + b * smoothstep((th - t_b) / 0.15))
        If, Ir = P.WHEEL_SPIN_INERTIA_FRONT, P.WHEEL_SPIN_INERTIA_REAR

        RA0 = Ry(-take["beta"])
        RB = RA0.copy()
        w0 = np.array([0.0, -take["W"], 0.0]) + r0 * EZ + p0 * (RA0 @ EX)
        u0 = RA0 @ self.p_rel
        D0 = u0 + RB @ self.cB
        IAw0, IBw0 = RA0 @ self.IA @ RA0.T, RB @ self.IB @ RB.T
        L0 = (IAw0 + IBw0 + self.mu * (np.dot(D0, D0) * np.eye(3) - np.outer(D0, D0))) @ w0 \
            + (If * take["wf"] + Ir * wr_spin[0]) * (RA0 @ EY)

        def omega_B(RB, Rr, wr_rider, wspin, shift, shift_dot):
            RA = RB @ Rr
            IAw = RA @ self.IA @ RA.T
            IBw = RB @ self.IB @ RB.T
            u = RA @ (self.p_rel + shift)
            D = u + RB @ self.cB
            w = RB @ wr_rider
            Mt = IAw + IBw + self.mu * (np.dot(D, D) * np.eye(3) - np.outer(D, D))
            rhs = (L0 - IAw @ w - self.mu * cross(D, cross(w, u)) - self.mu * cross(D, RA @ shift_dot)
                   - (If * take["wf"] + Ir * wspin) * (RA @ EY))
            return np.linalg.solve(Mt, rhs), RA, D

        def acc(v):
            sp = math.sqrt(v[0] ** 2 + v[2] ** 2)
            k = 0.5 * P.RHO * P.CDA * sp / self.M
            return np.array([-k * v[0], 0.0, -P.G - k * v[2]])

        C = np.array([take["X"], 0.0, take["Z"]])
        V = np.array([take["VX"], 0.0, take["VZ"]])
        sf, sr = take["sf"], take["sr"]
        rec, contact = [], None
        next_rec = 0.0
        for i in range(n - 1):
            t = ts[i]
            wB, RA, D = omega_B(RB, Rrel[i], wrel[i], wr_spin[i], shifts[i], shift_rates[i])
            bike_c = C - (self.mB / self.M) * D
            hit = None
            if t > 0.3:
                for wheel, sw in (("rear", sr), ("front", sf)):
                    q = (B.front_axle_at(sw) if wheel == "front" else B.rear_axle_at(sw))
                    ax = bike_c + RA @ (np.array([q[0], 0.0, q[1]]) - self.cA)
                    zc, _ = self.T.centre(wheel, ax[0])
                    if ax[2] <= zc:
                        hit = wheel
                        break
            if record and t >= next_rec - 1e-9:
                rec.append({"t": t, "C": C.copy(), "V": V.copy(), "RA": RA.copy(), "RB": RB.copy(), "D": D.copy(),
                            "wB": wB.copy(), "sf": sf, "sr": sr, "wf": take["wf"], "wr": wr_spin[i],
                            "Rrel": Rrel[i].copy(), "shift": shifts[i].copy(),
                            "reach_err": self.reach_errors(Rrel[i].T, shifts[i])})
                next_rec += rec_dt
            if hit:
                contact = {"t": t, "wheel": hit, "C": C.copy(), "V": V.copy(), "RA": RA.copy(), "RB": RB.copy(),
                           "D": D.copy(), "sf": sf, "sr": sr, "wr": wr_spin[i], "wf": take["wf"],
                           "Rrel": Rrel[i].copy(), "shift": shifts[i].copy()}
                break
            RBh = expm_so3(wB * dt / 2) @ RB
            sh_h = shifts[i] + shift_rates[i] * dt / 2
            wBh, _, _ = omega_B(RBh, Rrel_h[i], wrel_h[i], wr_spin_h[i], sh_h, shift_rates[i])
            RB = expm_so3(wBh * dt) @ RB
            k1v = acc(V); k1x = V
            k2v = acc(V + k1v * dt / 2); k2x = V + k1v * dt / 2
            k3v = acc(V + k2v * dt / 2); k3x = V + k2v * dt / 2
            k4v = acc(V + k3v * dt); k4x = V + k3v * dt
            C = C + (k1x + 2 * k2x + 2 * k3x + k4x) * dt / 6
            V = V + (k1v + 2 * k2v + 2 * k3v + k4v) * dt / 6
            sf = max(sf - S.spring("front", sf) / S.c_reb("front") * dt, 0.0)
            sr = max(sr - S.spring("rear", sr) / S.c_reb("rear") * dt, 0.0)
        self.L0 = L0
        return rec, contact

    # ------------------------------------------------------------------ closed-loop rider (used by the pipeline)
    REL_MAX = math.radians(75)      # largest bike-to-rider rotation the body can hold (with the hip shift)
    REL_RATE_MAX = 6.0              # rad/s, fastest the rider can twist the bike under him
    WR_MAX_RATIO = 1.8              # rear wheel over-rev in the air vs takeoff (rev limiter, gearing; EST)
    WR_UP, WR_DOWN = 300.0, 400.0   # rad/s^2, throttle spin-up and rear-brake spin-down (EST)
    STEER_MAX = math.radians(35)    # steering lock (EST, CRF250R about 35 to 40 deg)
    STEER_RATE = 8.0                # rad/s, fast bar input (EST)

    def run_control(self, take, target_fn, r0=0.0, p0=0.0, dt=1.0 / 1200.0, t_max=3.5, rec_dt=1.0 / 120.0,
                    record=True, T_land=2.3, gains=None):
        """Closed-loop rider. Each step the rider chooses
          w   : how fast he twists the bike relative to his body (world frame, rad/s), and
          dwr : throttle/brake change of the rear-wheel spin,
        by weighted least squares on: steer the bike to target_fn(t); keep his torso facing forward and
        upright; stay inside reach; return to the neutral pose before touchdown. Angular momentum is
        conserved exactly (wheels' gyro included); the body rotation follows from it."""
        g = dict(kp=9.0, w_track=1.0, w_rider=0.15, w_rate=0.02, w_wheel=2e-4, w_steer=0.02, w_lim=4.0, w_land=3.0)
        g.update(gains or {})
        S = self.S
        If, Ir = P.WHEEL_SPIN_INERTIA_FRONT, P.WHEEL_SPIN_INERTIA_REAR
        RA = Ry(-take["beta"])
        RB = RA.copy()
        wr = take["wr"]
        wr_max = take["wr"] * self.WR_MAX_RATIO
        delta = 0.0                                       # steering angle (rad), + turns the front wheel left
        s_ax = np.array([-math.sin(math.radians(P.RAKE_DEG)), 0.0, math.cos(math.radians(P.RAKE_DEG))])
        w0 = np.array([0.0, -take["W"], 0.0]) + r0 * EZ + p0 * (RA @ EX)
        D0 = RA @ self.p_rel + RB @ self.cB
        IAw0, IBw0 = RA @ self.IA @ RA.T, RB @ self.IB @ RB.T
        L0 = (IAw0 + IBw0 + self.mu * (np.dot(D0, D0) * np.eye(3) - np.outer(D0, D0))) @ w0 \
            + (If * take["wf"] + Ir * wr) * (RA @ EY)
        self.L0 = L0
        shift = np.zeros(3)

        def front_axis(delta):
            return expm_so3(s_ax * delta) @ EY            # front wheel spin axis in the bike frame

        def model(RA, RB, shift, shift_dot, wr, delta):
            IAw, IBw = RA @ self.IA @ RA.T, RB @ self.IB @ RB.T
            u = RA @ (self.p_rel + shift)
            D = u + RB @ self.cB
            Mt = IAw + IBw + self.mu * (np.dot(D, D) * np.eye(3) - np.outer(D, D))
            Mi = np.linalg.inv(Mt)
            a = RA @ EY
            af = RA @ front_axis(delta)
            c = L0 - self.mu * cross(D, RA @ shift_dot) - If * take["wf"] * af - Ir * wr * a
            K = IAw + self.mu * (np.dot(D, u) * np.eye(3) - np.outer(u, D))
            hs = Mi @ (If * take["wf"] * (RA @ cross(s_ax, front_axis(delta))))
            # omega_B = wB0 - MK w - h dwr - hs ddelta ; omega_A = omega_B + w
            return Mi @ c, Mi @ K, Mi @ (Ir * a), hs, D

        def choose(RA, RB, shift, shift_dot, wr, delta, t, dt_ctrl):
            wB0, MK, h, hs, D = model(RA, RB, shift, shift_dot, wr, delta)
            RT, wT = target_fn(t)
            e = logm_so3(RT @ RA.T)
            wA_des = wT + g["kp"] * e
            # rider's preferred torso: facing the travel direction, pitched like the bike, no lean
            _, pitch_b, _ = euler_of(RA)
            e_r = logm_so3(Ry(-pitch_b) @ RB.T)
            wB_des = 3.0 * e_r
            rel = logm_so3(RA @ RB.T)
            ang = np.linalg.norm(rel)
            rows, rhs = [], []
            # unknowns x = [w (3), dwr (1), ddelta (1)]
            GA = np.hstack([np.eye(3) - MK, -h[:, None], -hs[:, None]])
            GB = np.hstack([-MK, -h[:, None], -hs[:, None]])
            land = smoothstep((t - (T_land - 0.45)) / 0.3)
            wt = math.sqrt(g["w_track"])
            rows.append(wt * GA); rhs.append(wt * (wA_des - wB0))
            wrd = math.sqrt(g["w_rider"] * (1.0 - land))
            rows.append(wrd * GB); rhs.append(wrd * (wB_des - wB0))
            # neutral pose before touchdown: relative rotation decays to zero
            wl = math.sqrt(g["w_land"] * land)
            rows.append(wl * np.hstack([np.eye(3), np.zeros((3, 2))])); rhs.append(wl * (-4.0 * rel))
            rows.append(np.array([[0, 0, 0, 0, wl]])); rhs.append(np.array([wl * (-4.0 * delta * dt_ctrl)]))
            # reach limit: oppose further twisting beyond 60 % of the limit
            if ang > 0.6 * self.REL_MAX:
                f = math.sqrt(g["w_lim"]) * min((ang - 0.6 * self.REL_MAX) / (0.4 * self.REL_MAX), 1.5)
                ax = rel / ang
                rows.append(f * np.hstack([ax, [0.0, 0.0]])[None, :]); rhs.append(np.array([-3.0 * (ang - 0.6 * self.REL_MAX)]) * f)
            rows.append(math.sqrt(g["w_rate"]) * np.hstack([np.eye(3), np.zeros((3, 2))])); rhs.append(np.zeros(3))
            rows.append(np.array([[0, 0, 0, math.sqrt(g["w_wheel"]), 0]])); rhs.append(np.zeros(1))
            # steering preference: cost on the bar rate (rad/s) plus a gentle pull back to straight (0.5 /s)
            ws = math.sqrt(g["w_steer"])
            rows.append(np.array([[0, 0, 0, 0, ws / dt_ctrl]])); rhs.append(np.array([-ws * 0.5 * delta]))
            A = np.vstack(rows)
            y = np.concatenate(rhs)
            x = np.linalg.lstsq(A, y, rcond=None)[0]
            w, dwr, dd = x[:3], x[3], x[4]
            sp = np.linalg.norm(w)
            if sp > self.REL_RATE_MAX:
                w *= self.REL_RATE_MAX / sp
            if ang > self.REL_MAX and np.dot(w, rel) > 0:
                w -= np.dot(w, rel / ang) * (rel / ang)
            dwr = float(np.clip(dwr, -self.WR_DOWN * dt_ctrl, self.WR_UP * dt_ctrl))
            dwr = float(np.clip(wr + dwr, 0.0, wr_max) - wr)
            dd = float(np.clip(dd, -self.STEER_RATE * dt_ctrl, self.STEER_RATE * dt_ctrl))
            dd = float(np.clip(delta + dd, -self.STEER_MAX, self.STEER_MAX) - delta)
            wB = wB0 - MK @ w - h * dwr - hs * dd
            return w, dwr, dd, wB, wB + w, D, e

        def acc(v):
            sp = math.sqrt(v[0] ** 2 + v[2] ** 2)
            k = 0.5 * P.RHO * P.CDA * sp / self.M
            return np.array([-k * v[0], 0.0, -P.G - k * v[2]])

        C = np.array([take["X"], 0.0, take["Z"]])
        V = np.array([take["VX"], 0.0, take["VZ"]])
        sf, sr = take["sf"], take["sr"]
        rec, contact = [], None
        next_rec = 0.0
        n = int(t_max / dt)
        for k in range(n):
            t = k * dt
            RrelT = RA.T @ RB
            target, _ = self.body_shift(RrelT, shift)
            nt = np.linalg.norm(target)
            if nt > self.SHIFT_MAX:
                target *= self.SHIFT_MAX / nt
            shift_dot = (target - shift) / self.SHIFT_TAU
            sp = np.linalg.norm(shift_dot)
            if sp > self.SHIFT_VMAX:
                shift_dot *= self.SHIFT_VMAX / sp
            w, dwr, dd, wB, wA, D, e = choose(RA, RB, shift, shift_dot, wr, delta, t, dt)
            wr = wr + dwr
            delta = delta + dd
            bike_c = C - (self.mB / self.M) * D
            hit = None
            if t > 0.3:
                for wheel, sw in (("rear", sr), ("front", sf)):
                    q = (B.front_axle_at(sw) if wheel == "front" else B.rear_axle_at(sw))
                    ax = bike_c + RA @ (np.array([q[0], 0.0, q[1]]) - self.cA)
                    zc, _ = self.T.centre(wheel, ax[0])
                    if ax[2] <= zc:
                        hit = wheel
                        break
            if record and t >= next_rec - 1e-9:
                rec.append({"t": t, "C": C.copy(), "V": V.copy(), "RA": RA.copy(), "RB": RB.copy(), "D": D.copy(),
                            "wB": wB.copy(), "wA": wA.copy(), "sf": sf, "sr": sr, "wf": take["wf"], "wr": wr,
                            "shift": shift.copy(), "reach_err": self.reach_errors(RrelT, shift),
                            "track_err": float(np.linalg.norm(e)), "w_rel": w.copy(), "steer": delta})
                next_rec += rec_dt
            if hit:
                contact = {"t": t, "wheel": hit, "C": C.copy(), "V": V.copy(), "RA": RA.copy(), "RB": RB.copy(),
                           "D": D.copy(), "sf": sf, "sr": sr, "wr": wr, "wf": take["wf"], "shift": shift.copy(),
                           "steer": delta}
                break
            # midpoint step: same rider action over the step, re-solve the conservation law at the midpoint
            RAh, RBh = expm_so3(wA * dt / 2) @ RA, expm_so3(wB * dt / 2) @ RB
            wB0h, MKh, hh, _, _ = model(RAh, RBh, shift + shift_dot * dt / 2, shift_dot, wr, delta)
            wBh = wB0h - MKh @ w
            RA, RB = expm_so3((wBh + w) * dt) @ RA, expm_so3(wBh * dt) @ RB
            shift = shift + shift_dot * dt
            k1v = acc(V); k1x = V
            k2v = acc(V + k1v * dt / 2); k2x = V + k1v * dt / 2
            k3v = acc(V + k2v * dt / 2); k3x = V + k2v * dt / 2
            k4v = acc(V + k3v * dt); k4x = V + k3v * dt
            C = C + (k1x + 2 * k2x + 2 * k3x + k4x) * dt / 6
            V = V + (k1v + 2 * k2v + 2 * k3v + k4v) * dt / 6
            sf = max(sf - S.spring("front", sf) / S.c_reb("front") * dt, 0.0)
            sr = max(sr - S.spring("rear", sr) / S.c_reb("rear") * dt, 0.0)
        return rec, contact

    # ------------------------------------------------------------------ whip target (controller reference)
    @staticmethod
    def bike_angles(prof, t):
        """Vectorised prescribed bike motion: (yaw, pitch_up, roll) in radians at times t.

        prof: yaw_t, yaw (deg) knots with r0 (deg/s) start slope; roll_t, roll with p0;
              beta0, beta_dot0, beta_land (rad, rad/s) and T (s) for a cubic Hermite pitch.
        """
        t = np.asarray(t, float)
        T, bL = prof["T"], prof["beta_land"]
        bd1 = (bL - prof["beta0"]) / T
        s = np.clip(t / T, 0.0, 1.0)
        h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
        pitch = h00 * prof["beta0"] + h10 * T * prof["beta_dot0"] + h01 * bL + h11 * T * bd1
        pitch = np.where(t > T, bL + bd1 * (t - T), pitch)
        yaw = np.radians(pchip(prof["yaw_t"], prof["yaw"], np.minimum(t, prof["yaw_t"][-1]), m0=prof["r0"]))
        roll = np.radians(pchip(prof["roll_t"], prof["roll"], np.minimum(t, prof["roll_t"][-1]), m0=prof["p0"]))
        return yaw, pitch, roll
