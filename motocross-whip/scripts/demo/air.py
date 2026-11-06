"""Airborne dynamics: bike + rider as two rigid bodies plus spinning wheels.

The system centre of mass flies ballistically (gravity + aerodynamic drag).
Rotation obeys conservation of total angular momentum about the system CoM:

    L = I_A w_A + I_B w_B + mu D x dD/dt + L_wheels = L0     (constant)

A = bike, B = rider (rigid, neutral attack pose), D = rider CoM - bike CoM,
mu = mA mB / M, L_wheels = (If wf + Ir wr) along the bike's axle (left).
The rider's action is the prescribed relative rotation R_rel(t) of the bike
with respect to the rider (R_A = R_B R_rel), pivoting at the peg midpoint.
Solving the conservation law each step gives the rider's absolute angular
velocity; the bike follows. Gyroscopic coupling from the wheels is exact.
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

    def rel_rotations(self, ts, T_air, knots):
        """R_rel(t) from Euler knots {'f': fractions, 'yaw': deg, 'pitch': deg, 'roll': deg}."""
        fr = np.concatenate([[0.0], knots["f"], [1.0]]) * T_air
        ang = {k: np.radians(pchip(fr, np.concatenate([[0.0], knots[k], [0.0]]), np.clip(ts, 0, T_air)))
               for k in ("yaw", "pitch", "roll")}
        return [euler_from(ang["yaw"][i], ang["pitch"][i], ang["roll"][i]) for i in range(len(ts))]

    def run(self, take, whip, dt=1.0 / 1200.0, t_max=3.5, rec_dt=1.0 / 120.0, T_air_est=2.2, record=True):
        """take: dict X, Z, VX, VZ, beta, W, sf, sr, wf, wr. whip: r0, p0 (rad/s), knots, b, t_b."""
        S = self.S
        n = int(t_max / dt) + 2
        ts = np.arange(n) * dt
        th = ts + dt / 2
        Rrel = self.rel_rotations(ts, T_air_est, whip["knots"])
        Rrel_h = self.rel_rotations(th, T_air_est, whip["knots"])
        # rider-frame relative angular velocity, central difference at half steps
        wrel_h = [logm_so3(Rrel[i + 1] @ Rrel[i].T) / dt for i in range(n - 1)]
        wrel = [np.zeros(3)] + [0.5 * (wrel_h[i - 1] + wrel_h[i]) for i in range(1, n - 1)] + [wrel_h[-1]]
        # Rotate R_rel frame derivative into rider frame: R_rel' R_rel^T is spatial in rider frame
        wr_spin = take["wr"] * (1.0 + whip.get("b", 0.0) * smoothstep((ts - whip.get("t_b", 0.9)) / 0.15))
        wr_spin_h = take["wr"] * (1.0 + whip.get("b", 0.0) * smoothstep((th - whip.get("t_b", 0.9)) / 0.15))
        If, Ir = P.WHEEL_SPIN_INERTIA_FRONT, P.WHEEL_SPIN_INERTIA_REAR

        RA0 = Ry(-take["beta"])
        RB = RA0.copy()
        w0 = np.array([0.0, -take["W"], 0.0]) + whip.get("r0", 0.0) * EZ + whip.get("p0", 0.0) * (RA0 @ EX)

        def parts(RB, Rr):
            RA = RB @ Rr
            IAw = RA @ self.IA @ RA.T
            IBw = RB @ self.IB @ RB.T
            u = RA @ self.p_rel
            e = RB @ self.cB
            D = u + e
            return RA, IAw, IBw, u, D

        RA, IAw, IBw, u, D = parts(RB, Rrel[0])
        Mtot0 = IAw + IBw + self.mu * (np.dot(D, D) * np.eye(3) - np.outer(D, D))
        L0 = Mtot0 @ w0 + (If * take["wf"] + Ir * wr_spin[0]) * (RA @ EY)

        def omega_B(RB, Rr, wr_rider, wspin):
            RA, IAw, IBw, u, D = parts(RB, Rr)
            w = RB @ wr_rider
            Mt = IAw + IBw + self.mu * (np.dot(D, D) * np.eye(3) - np.outer(D, D))
            rhs = L0 - IAw @ w - self.mu * cross(D, cross(w, u)) - (If * take["wf"] + Ir * wspin) * (RA @ EY)
            return np.linalg.solve(Mt, rhs), RA, D

        # translation (independent of rotation): RK4 with drag
        def acc(v):
            sp = math.sqrt(v[0] ** 2 + v[2] ** 2)
            k = 0.5 * P.RHO * P.CDA * sp / self.M
            return np.array([-k * v[0], 0.0, -P.G - k * v[2]])

        C = np.array([take["X"], 0.0, take["Z"]])
        V = np.array([take["VX"], 0.0, take["VZ"]])
        sf, sr = take["sf"], take["sr"]
        rec, contact = [], None
        next_rec = 0.0
        wB = w0
        for i in range(n - 1):
            t = ts[i]
            wB, RA, D = omega_B(RB, Rrel[i], wrel[i], wr_spin[i])
            # contact check (wheel centres vs. terrain contact curves)
            bike_c = C - (self.mB / self.M) * D
            hit = None
            for wheel, s in (("rear", sr), ("front", sf)):
                q = (B.front_axle_at(s) if wheel == "front" else B.rear_axle_at(s))
                ax = bike_c + RA @ (np.array([q[0], 0.0, q[1]]) - self.cA)
                zc, _ = self.T.centre(wheel, ax[0])
                if ax[2] <= zc and t > 0.3:
                    hit = wheel
                    break
            if record and t >= next_rec - 1e-9:
                rec.append({"t": t, "C": C.copy(), "V": V.copy(), "RA": RA.copy(), "RB": RB.copy(), "D": D.copy(),
                            "wB": wB.copy(), "sf": sf, "sr": sr, "wf": take["wf"], "wr": wr_spin[i],
                            "Rrel": Rrel[i].copy()})
                next_rec += rec_dt
            if hit:
                contact = {"t": t, "wheel": hit, "C": C.copy(), "V": V.copy(), "RA": RA.copy(), "RB": RB.copy(),
                           "D": D.copy(), "sf": sf, "sr": sr, "wr": wr_spin[i], "wf": take["wf"]}
                break
            # rotation: midpoint
            RBh = expm_so3(wB * dt / 2) @ RB
            wBh, _, _ = omega_B(RBh, Rrel_h[i], wrel_h[i], wr_spin_h[i])
            RB = expm_so3(wBh * dt) @ RB
            # translation: RK4
            k1v = acc(V); k1x = V
            k2v = acc(V + k1v * dt / 2); k2x = V + k1v * dt / 2
            k3v = acc(V + k2v * dt / 2); k3x = V + k2v * dt / 2
            k4v = acc(V + k3v * dt); k4x = V + k3v * dt
            C = C + (k1x + 2 * k2x + 2 * k3x + k4x) * dt / 6
            V = V + (k1v + 2 * k2v + 2 * k3v + k4v) * dt / 6
            # suspension extends against rebound damping (massless wheel)
            sf = max(sf - S.spring("front", sf) / S.c_reb("front") * dt, 0.0)
            sr = max(sr - S.spring("rear", sr) / S.c_reb("rear") * dt, 0.0)
        self.L0 = L0
        return rec, contact

    # ------------------------------------------------------------------ inverse formulation
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

    def run_inverse(self, take, prof, b=0.0, t_b=0.9, dt=1.0 / 1200.0, t_max=3.5, rec_dt=1.0 / 120.0, record=True):
        """Bike orientation prescribed; the rider's rotation follows from conservation of L."""
        S = self.S
        h = 1e-4
        If, Ir = P.WHEEL_SPIN_INERTIA_FRONT, P.WHEEL_SPIN_INERTIA_REAR
        n = int(t_max / dt) + 2
        grid = np.arange(n) * dt
        tq = np.concatenate([grid, grid + dt / 2])
        ang = [self.bike_angles(prof, x) for x in (tq, tq + h, np.maximum(tq - h, 0.0))]
        Rs = [[euler_from(a[0][i], a[1][i], a[2][i]) for i in range(len(tq))] for a in ang]
        RA_all = Rs[0]
        wA_all = [logm_so3(Rs[1][i] @ Rs[2][i].T) / (h + min(tq[i], h)) for i in range(len(tq))]

        def bike_state(k, half=False):
            j = k + (n if half else 0)
            return RA_all[j], wA_all[j]

        def wr_at(t):
            return take["wr"] * (1.0 + b * float(smoothstep((t - t_b) / 0.15)))

        RA, wA = bike_state(0)
        RB = RA.copy()
        u, e = RA @ self.p_rel, RB @ self.cB
        D = u + e
        IAw, IBw = RA @ self.IA @ RA.T, RB @ self.IB @ RB.T
        L0 = (IAw + IBw + self.mu * (np.dot(D, D) * np.eye(3) - np.outer(D, D))) @ wA \
            + (If * take["wf"] + Ir * wr_at(0.0)) * (RA @ EY)
        self.L0 = L0

        def omega_B(RB, RA, wA, wr):
            IAw, IBw = RA @ self.IA @ RA.T, RB @ self.IB @ RB.T
            u, e = RA @ self.p_rel, RB @ self.cB
            D = u + e
            Mt = IBw + self.mu * (np.dot(D, e) * np.eye(3) - np.outer(e, D))
            rhs = L0 - IAw @ wA - self.mu * cross(D, cross(wA, u)) - (If * take["wf"] + Ir * wr) * (RA @ EY)
            return np.linalg.solve(Mt, rhs), D

        def acc(v):
            sp = math.sqrt(v[0] ** 2 + v[2] ** 2)
            k = 0.5 * P.RHO * P.CDA * sp / self.M
            return np.array([-k * v[0], 0.0, -P.G - k * v[2]])

        C = np.array([take["X"], 0.0, take["Z"]])
        V = np.array([take["VX"], 0.0, take["VZ"]])
        sf, sr = take["sf"], take["sr"]
        rec, contact = [], None
        next_rec = 0.0
        for k in range(n - 1):
            t = grid[k]
            RA, wA = bike_state(k)
            wr = wr_at(t)
            wB, D = omega_B(RB, RA, wA, wr)
            bike_c = C - (self.mB / self.M) * D
            hit = None
            if t > 0.3:
                for wheel, s in (("rear", sr), ("front", sf)):
                    q = (B.front_axle_at(s) if wheel == "front" else B.rear_axle_at(s))
                    ax = bike_c + RA @ (np.array([q[0], 0.0, q[1]]) - self.cA)
                    zc, _ = self.T.centre(wheel, ax[0])
                    if ax[2] <= zc:
                        hit = wheel
                        break
            if record and t >= next_rec - 1e-9:
                rec.append({"t": t, "C": C.copy(), "V": V.copy(), "RA": RA, "RB": RB.copy(), "D": D.copy(),
                            "wB": wB.copy(), "wA": wA.copy(), "sf": sf, "sr": sr, "wf": take["wf"], "wr": wr})
                next_rec += rec_dt
            if hit:
                contact = {"t": t, "wheel": hit, "C": C.copy(), "V": V.copy(), "RA": RA, "RB": RB.copy(),
                           "D": D.copy(), "sf": sf, "sr": sr, "wr": wr, "wf": take["wf"]}
                break
            RBh = expm_so3(wB * dt / 2) @ RB
            RAh, wAh = bike_state(k, half=True)
            wBh, _ = omega_B(RBh, RAh, wAh, wr_at(t + dt / 2))
            RB = expm_so3(wBh * dt) @ RB
            k1v = acc(V); k1x = V
            k2v = acc(V + k1v * dt / 2); k2x = V + k1v * dt / 2
            k3v = acc(V + k2v * dt / 2); k3x = V + k2v * dt / 2
            k4v = acc(V + k3v * dt); k4x = V + k3v * dt
            C = C + (k1x + 2 * k2x + 2 * k3x + k4x) * dt / 6
            V = V + (k1v + 2 * k2v + 2 * k3v + k4v) * dt / 6
            sf = max(sf - S.spring("front", sf) / S.c_reb("front") * dt, 0.0)
            sr = max(sr - S.spring("rear", sr) / S.c_reb("rear") * dt, 0.0)
        return rec, contact
