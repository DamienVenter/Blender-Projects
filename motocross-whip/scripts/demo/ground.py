"""Sagittal (2D) dynamics on the ground: approach, ramp face, lip, landing, ride-away.

Two bodies:
- Bike: rigid body (X, Z, pitch beta) with massless wheels on a telescopic fork
  and a swingarm. Each suspension is a non-linear spring (preload, progressive
  bottoming cone, hard stop) with direction-dependent damping. A wheel is in
  contact when the ground pushes its axle above the most-extended position the
  rebound damper allows this step. Ground forces act along the surface normal;
  the rear tyre also carries drive force (power and traction limited).
- Rider: a point mass (88.5 kg) held at the pegs and bars by the legs and arms,
  modelled as an anisotropic spring-damper in the bike frame: soft along the
  bike's vertical (legs: about 2 Hz, crouch and extend), stiffer fore-aft. The
  legs have a rest length above the neutral pose, so the rider extends when the
  load drops (lip, air) and crouches under load (ramp transition, landing). The
  rider's rotational inertia turns with the bike.
"""
import math
import numpy as np
import params as P
import bike as B
import rider as RD

DT = 1.0 / 4000.0

LEG_KW, LEG_CW, LEG_KU, LEG_CU = P.LEG_KW, P.LEG_CW, P.LEG_KU, P.LEG_CU
CROUCH_MAX, EXTEND_MAX = P.CROUCH_MAX, P.EXTEND_MAX


class System:
    def __init__(self):
        self.mb, self.cb, self.Ib = B.mass_properties()
        self.mr, cr, self.Ir = RD.mass_properties()
        self.peg = np.array([P.FOOTPEG[0], 0.0, P.FOOTPEG[1]])
        self.cr = cr                                      # rider CoM rel. peg midpoint (rider frame)
        self.cr_bike = self.peg + cr                      # rider CoM, bike frame, neutral pose
        self.M = self.mb + self.mr
        self.c = (self.mb * self.cb + self.mr * self.cr_bike) / self.M
        d_b, d_r = self.cb - self.c, self.cr_bike - self.c
        self.Isys = (self.Ib + self.mb * (np.dot(d_b, d_b) * np.eye(3) - np.outer(d_b, d_b))
                     + self.Ir + self.mr * (np.dot(d_r, d_r) * np.eye(3) - np.outer(d_r, d_r)))
        self.Iyy_bike = self.Ib[1, 1] + self.Ir[1, 1]     # bike + rider's own rotation
        self.cb2 = np.array([self.cb[0], self.cb[2]])
        self.rn2 = np.array([self.cr_bike[0], self.cr_bike[2]]) - self.cb2   # rider neutral rel. bike CoM
        self.fork_dir = B.fork_axis()
        self.leg_rest = self.mr * P.G / LEG_KW            # legs compressed this much at 1 g
        Nf = self.M * P.G * self.c[0] / P.WHEELBASE
        Nr = self.M * P.G - Nf
        # preloads so the progressive springs sit exactly at the target sags under static load
        sf, sr = P.TARGET_SAG_FRONT, P.TARGET_SAG_REAR
        air = P.FORK_K * P.FORK_TRAVEL * P.FORK_AIR_GAIN * (sf / P.FORK_TRAVEL) ** 3
        self.x0_f = (Nf * self.fork_dir[1] - air) / P.FORK_K - sf
        fac = 1.0 + P.REAR_RISING * (sr / P.REAR_TRAVEL) ** 2
        self.x0_r = Nr * B.rear_travel_dir(sr)[1] / (P.REAR_K * fac) - sr
        self.Nf_static, self.Nr_static = Nf, Nr
        self.T_face = 0.0                                 # steady throttle force up the ramp face (N)

    def spring(self, wheel, s):
        if wheel == "front":
            k, x0, T = P.FORK_K, self.x0_f, P.FORK_TRAVEL
            F = k * (s + x0) + k * T * P.FORK_AIR_GAIN * (max(s, 0.0) / T) ** 3
        else:
            k, x0, T = P.REAR_K, self.x0_r, P.REAR_TRAVEL
            F = k * (s + x0) * (1.0 + P.REAR_RISING * (max(s, 0.0) / T) ** 2)
        b0 = P.BUMP_START * T
        if s > b0:
            F += P.BUMP_GAIN * k * (s - b0) ** 3 / (T - b0) ** 2
        if s > T:
            F += 5.0e5 * (s - T)
        return F

    def damp(self, wheel, sdot):
        if wheel == "front":
            return (P.FORK_C_COMP if sdot > 0 else P.FORK_C_REB) * sdot
        return (P.REAR_C_COMP if sdot > 0 else P.REAR_C_REB) * sdot

    def c_reb(self, wheel):
        return P.FORK_C_REB if wheel == "front" else P.REAR_C_REB

    def axle_local(self, wheel, s):
        return B.front_axle_at(s) if wheel == "front" else B.rear_axle_at(s)

    def travel_dir_local(self, wheel, s):
        return self.fork_dir if wheel == "front" else B.rear_travel_dir(s)

    def to_world(self, X, Z, beta, q):
        """Bike-frame point (u, w) to world, with (X, Z) the bike CoM."""
        cb, sb = math.cos(beta), math.sin(beta)
        u, w = q[0] - self.cb2[0], q[1] - self.cb2[1]
        return X + u * cb - w * sb, Z + u * sb + w * cb


def rot2(beta, v):
    cb, sb = math.cos(beta), math.sin(beta)
    return (v[0] * cb - v[1] * sb, v[0] * sb + v[1] * cb)


class GroundSim:
    """State: [Xb, Zb, beta, VXb, VZb, W, xr, zr, vxr, vzr] (bike CoM, pitch, rider point mass)."""

    def __init__(self, sysm, terrain):
        self.S = sysm
        self.T = terrain

    def static_pose(self, X, z_ground=0.0):
        """Bike CoM height, pitch and rider position on flat ground at the target sags."""
        S = self.S
        sf, sr = P.TARGET_SAG_FRONT, P.TARGET_SAG_REAR
        fa, ra = S.axle_local("front", sf), S.axle_local("rear", sr)
        chord = fa - ra
        beta = math.asin((P.R_FRONT - P.R_REAR) / np.linalg.norm(chord)) - math.atan2(chord[1], chord[0])
        _, rz0 = S.to_world(0.0, 0.0, beta, ra)
        Zb = z_ground + P.R_REAR - rz0
        rx, rz = rot2(beta, S.rn2)
        return [X, Zb, beta, 0.0, 0.0, 0.0, X + rx, Zb + rz, 0.0, 0.0], {"front": sf, "rear": sr}

    def wheel_update(self, wheel, X, Z, beta, s_prev, dt):
        S, T = self.S, self.T
        s_min = max(s_prev - S.spring(wheel, max(s_prev, 0.0)) / S.c_reb(wheel) * dt, 0.0)

        def g(s):
            ax, az = S.to_world(X, Z, beta, S.axle_local(wheel, s))
            zc, _ = T.centre(wheel, ax)
            return az - zc

        if g(s_min) >= 0.0:
            return s_min, False
        lo, hi = s_min, max(s_prev, s_min) + 0.05
        while g(hi) < 0.0 and hi < 1.0:
            hi += 0.05
        for _ in range(28):
            mid = 0.5 * (lo + hi)
            if g(mid) < 0.0:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi), True

    def rider_force(self, st):
        """Force on the rider from legs/arms (world), and rider offset (du, dw) in the bike frame."""
        S = self.S
        Xb, Zb, beta, VXb, VZb, W, xr, zr, vxr, vzr = st
        ax, az = rot2(beta, S.rn2)
        cb, sb = math.cos(beta), math.sin(beta)
        ex, ez = xr - (Xb + ax), zr - (Zb + az)                      # offset from neutral, world
        du, dw = ex * cb + ez * sb, -ex * sb + ez * cb                  # in bike frame
        vax, vaz = VXb - W * az, VZb + W * ax                           # attachment point velocity
        evx, evz = vxr - vax, vzr - vaz
        dvu, dvw = evx * cb + evz * sb, -evx * sb + evz * cb
        Fu = -LEG_KU * du - LEG_CU * dvu
        Fw = -LEG_KW * (dw - S.leg_rest) - LEG_CW * dvw
        if dw < CROUCH_MAX:
            Fw += 3.0e5 * (CROUCH_MAX - dw)
        if dw > EXTEND_MAX:
            Fw -= 3.0e5 * (dw - EXTEND_MAX)
        Fx, Fz = Fu * cb - Fw * sb, Fu * sb + Fw * cb
        return (Fx, Fz), (du, dw), (ax, az)

    def forces(self, st, s_prev, dt, drive_mode, v_set):
        S, T = self.S, self.T
        Xb, Zb, beta, VXb, VZb, W, xr, zr, vxr, vzr = st
        FX, FZ, TAU = 0.0, -S.mb * P.G, 0.0
        # aero drag on the whole machine, split by mass
        Vx = (S.mb * VXb + S.mr * vxr) / S.M
        Vz = (S.mb * VZb + S.mr * vzr) / S.M
        sp = math.hypot(Vx, Vz)
        fdx = fdz = 0.0
        if sp > 0:
            fd = 0.5 * P.RHO * P.CDA * sp * sp
            fdx, fdz = -fd * Vx / sp, -fd * Vz / sp
        FX += fdx * S.mb / S.M
        FZ += fdz * S.mb / S.M
        # rider coupling
        (Frx, Frz), (du, dw), (ax_r, az_r) = self.rider_force(st)
        FX -= Frx
        FZ -= Frz
        TAU += ax_r * (-Frz) - az_r * (-Frx)
        out = {"rider": (du, dw)}
        for wheel in ("front", "rear"):
            s, contact = self.wheel_update(wheel, Xb, Zb, beta, s_prev[wheel], dt)
            info = {"s": s, "contact": contact, "N": 0.0, "T": 0.0}
            if contact:
                sdot = (s - s_prev[wheel]) / dt
                Fs = max(S.spring(wheel, s) + S.damp(wheel, sdot), 0.0)
                ax, az = S.to_world(Xb, Zb, beta, S.axle_local(wheel, s))
                _, n = T.centre(wheel, ax)
                d = rot2(beta, S.travel_dir_local(wheel, s))
                t = (n[1], -n[0])
                nd = max(n[0] * d[0] + n[1] * d[1], 0.2)
                v_t = Vx * t[0] + Vz * t[1]
                Tq = 0.0
                if wheel == "rear" and drive_mode == "hold":
                    want = S.M * 4.0 * (v_set - v_t) + S.M * P.G * t[1] + 0.5 * P.RHO * P.CDA * v_t * abs(v_t)
                    Tq = min(max(want, 0.0), P.ENGINE_POWER / max(v_t, 1.0), P.TYRE_MU * Fs / nd)
                elif wheel == "rear" and drive_mode == "cruise":
                    want = 0.5 * P.RHO * P.CDA * v_t * abs(v_t) + 0.02 * S.M * P.G
                    Tq = min(want, P.TYRE_MU * Fs / nd)
                elif wheel == "rear" and drive_mode == "face":
                    # rider holds a steady throttle up the face (sets the bike's rotation off the lip)
                    Tq = min(S.T_face, P.ENGINE_POWER / max(v_t, 1.0), P.TYRE_MU * Fs / nd)
                N = max((Fs - Tq * (t[0] * d[0] + t[1] * d[1])) / nd, 0.0)
                Fx, Fz = N * n[0] + Tq * t[0], N * n[1] + Tq * t[1]
                FX += Fx
                FZ += Fz
                TAU += (ax - Xb) * Fz - (az - Zb) * Fx
                info.update({"N": N, "T": Tq})
            out[wheel] = info
        ar = ((Frx + fdx * S.mr / S.M) / S.mr, (Frz + fdz * S.mr / S.M) / S.mr - P.G)
        return (FX / S.mb, FZ / S.mb, TAU / S.Iyy_bike), ar, out

    def system_state(self, st):
        """System CoM, velocity and pitch angular momentum about the system CoM (nose-up +)."""
        S = self.S
        Xb, Zb, beta, VXb, VZb, W, xr, zr, vxr, vzr = st
        C = ((S.mb * Xb + S.mr * xr) / S.M, (S.mb * Zb + S.mr * zr) / S.M)
        V = ((S.mb * VXb + S.mr * vxr) / S.M, (S.mb * VZb + S.mr * vzr) / S.M)
        Ly = S.Iyy_bike * W
        for m, x, z, vx, vz in ((S.mb, Xb, Zb, VXb, VZb), (S.mr, xr, zr, vxr, vzr)):
            rx, rz = x - C[0], z - C[1]
            Ly += m * (rz * (vx - V[0]) * -1.0 + rx * (vz - V[1]))
        return C, V, Ly

    def run(self, st, s0, t0, stop, drive_mode="hold", v_set=16.0, rec_dt=1.0 / 120.0, t_max=20.0):
        st = list(st)
        s_prev = dict(s0)
        t = t0
        rec = []
        next_rec = t0
        while t < t_max:
            mode = drive_mode(t, st) if callable(drive_mode) else drive_mode
            (ax, az, al), (arx, arz), contacts = self.forces(st, s_prev, DT, mode, v_set)
            s_prev = {w: contacts[w]["s"] for w in ("front", "rear")}
            if t >= next_rec - 1e-9:
                rec.append({"t": t, "st": list(st), "sf": s_prev["front"], "sr": s_prev["rear"],
                            "cf": contacts["front"]["contact"], "cr": contacts["rear"]["contact"],
                            "Nf": contacts["front"]["N"], "Nr": contacts["rear"]["N"], "Tr": contacts["rear"]["T"],
                            "rider": contacts["rider"]})
                next_rec += rec_dt
            if stop(t, st, contacts):
                break
            st[3] += ax * DT
            st[4] += az * DT
            st[5] += al * DT
            st[8] += arx * DT
            st[9] += arz * DT
            st[0] += st[3] * DT
            st[1] += st[4] * DT
            st[2] += st[5] * DT
            st[6] += st[8] * DT
            st[7] += st[9] * DT
            t += DT
        return t, st, s_prev, rec
