"""Physics validation for the whip demo. Run: python3 -m pytest -q test_physics.py"""
import math
import numpy as np
import pytest

import params as P
import terrain
import ground
import air
import sim


@pytest.fixture(scope="module")
def pl():
    return sim.Pipeline()


def test_site_constants():
    # Johannesburg (Fourways, about 1480 m, 26 deg S): gravity and air density
    assert 9.783 < P.G < 9.789
    assert 0.98 < P.RHO < 1.03


def test_terrain_geometry(pl):
    T = pl.T
    assert abs(T.ground(-1e-6) - P.LIP_HEIGHT) < 0.01
    # lip slope equals the lip angle (last centimetre: the arc steepens right up to the edge)
    s = (T.ground(-0.0026) - T.ground(-0.0126)) / 0.01
    assert abs(math.degrees(math.atan(s)) - P.LIP_ANGLE_DEG) < 0.15
    # the gap is measured lip to knuckle
    assert abs(T.keys["knuckle"] - P.GAP) < 1e-9
    # landing downslope angle
    x = 0.5 * (T.keys["downslope_start"] + T.keys["downslope_end"])
    s = (T.ground(x + 0.05) - T.ground(x - 0.05)) / 0.10
    assert abs(math.degrees(math.atan(-s)) - P.LANDING_ANGLE_DEG) < 0.3
    # wheel-centre curve over the lip edge is the lip height plus the radius
    zc, _ = T.centre("rear", 0.0)
    assert abs(zc - (P.LIP_HEIGHT + P.R_REAR)) < 0.003


def test_static_sag(pl):
    G = pl.G
    st, s0 = G.static_pose(-60.0)
    t, st, sp, rec = G.run(st, s0, 0.0, lambda t, s, c: t > 1.5, "coast", 0.0)
    assert abs(sp["front"] - P.TARGET_SAG_FRONT) < 0.004
    assert abs(sp["rear"] - P.TARGET_SAG_REAR) < 0.004
    assert abs(rec[-1]["rider"][1]) < 0.004            # rider legs settle at the neutral pose


def test_ballistic_matches_analytic(pl, monkeypatch):
    monkeypatch.setattr(P, "CDA", 0.0)
    take = dict(X=0.0, Z=4.0, VX=11.0, VZ=10.0, beta=math.radians(40), W=-0.6, sf=0.0, sr=0.0, wf=40.0, wr=42.0)
    no_input = dict(knots=dict(f=sim.KNOT_F, yaw=[0] * 7, pitch=[0] * 7, roll=[0] * 7))
    rec, con = pl.A.run(take, no_input, dt=1 / 1200, rec_dt=1 / 120)
    for r in rec:
        t = r["t"]
        assert abs(r["C"][0] - 11.0 * t) < 1e-6
        assert abs(r["C"][2] - (4.0 + 10.0 * t - 0.5 * P.G * t * t)) < 1e-6


def _L(pl, RA, RB, wA, wB, D, Ddot, wr, wf, steer=0.0):
    """Total angular momentum about the system CoM, computed independently of the solvers."""
    A = pl.A
    IAw = RA @ A.IA @ RA.T
    IBw = RB @ A.IB @ RB.T
    s_ax = np.array([-math.sin(math.radians(P.RAKE_DEG)), 0.0, math.cos(math.radians(P.RAKE_DEG))])
    a_front = RA @ air.expm_so3(s_ax * steer) @ np.array([0.0, 1.0, 0.0])
    Lw = P.WHEEL_SPIN_INERTIA_FRONT * wf * a_front + P.WHEEL_SPIN_INERTIA_REAR * wr * (RA @ np.array([0.0, 1.0, 0.0]))
    return IAw @ wA + IBw @ wB + A.mu * np.cross(D, Ddot) + Lw


def test_angular_momentum_conserved_independent_check(pl):
    """Recompute L from finite differences of the recorded orientations (independent of the solver)."""
    take = dict(X=0.0, Z=4.0, VX=11.0, VZ=10.0, beta=math.radians(40), W=-0.6, sf=0.0, sr=0.0, wf=45.0, wr=47.0)
    whip = dict(r0=math.radians(80), p0=math.radians(-150), b=0.3, t_b=0.8,
                knots=dict(f=sim.KNOT_F, yaw=[10, 25, 30, 20, 10, 5, 2], pitch=[0, 5, 10, 5, 0, -5, 0],
                           roll=[-15, -35, -40, -30, -10, 0, 0]))
    dt = 1 / 1200
    rec, con = pl.A.run(take, whip, dt=dt, rec_dt=dt / 2, T_air_est=2.0, t_max=1.6)
    L0 = pl.A.L0
    worst = 0.0
    for a, b in zip(rec[:-1], rec[1:]):
        h = b["t"] - a["t"]
        RA, RB = 0.5 * (a["RA"] + b["RA"]), 0.5 * (a["RB"] + b["RB"])
        wA = air.logm_so3(b["RA"] @ a["RA"].T) / h
        wB = air.logm_so3(b["RB"] @ a["RB"].T) / h
        D = 0.5 * (a["D"] + b["D"])
        Ddot = (b["D"] - a["D"]) / h
        L = _L(pl, RA, RB, wA, wB, D, Ddot, 0.5 * (a["wr"] + b["wr"]), a["wf"])
        worst = max(worst, np.linalg.norm(L - L0) / np.linalg.norm(L0))
    assert worst < 5e-3, worst


def test_gyro_whip_direction(pl):
    """Laying the bike down to the LEFT with spinning wheels must swing the rear to the RIGHT (nose left)."""
    take = dict(X=0.0, Z=6.0, VX=11.0, VZ=10.0, beta=0.0, W=0.0, sf=0.0, sr=0.0, wf=45.0, wr=47.0)
    whip = dict(r0=0.0, p0=0.0, b=0.0, t_b=5.0,
                knots=dict(f=sim.KNOT_F, yaw=[0] * 7, pitch=[0] * 7, roll=[-10, -30, -45, -45, -45, -45, -45]))
    rec, _ = pl.A.run(take, whip, dt=1 / 1200, rec_dt=1 / 120, T_air_est=2.0, t_max=0.8)
    yaw, _, roll = air.euler_of(rec[-1]["RA"])
    assert roll < 0          # leaning left
    assert yaw > 0           # nose left, rear right


def test_no_penetration_on_ramp(pl):
    t, st, sp, rec = pl.to_takeoff(17.0)
    S, T = pl.S, pl.T
    for r in rec:
        X, Z, beta = r["st"][:3]
        for wheel, s in (("front", r["sf"]), ("rear", r["sr"])):
            ax, az = S.to_world(X, Z, beta, S.axle_local(wheel, s))
            zc, _ = T.centre(wheel, ax)
            assert az - zc > -0.002, (wheel, r["t"], az - zc)


def test_body_shift_neutral_is_zero(pl):
    s, err = pl.A.body_shift(np.eye(3), np.zeros(3))
    assert np.linalg.norm(s) < 1e-9
    assert np.abs(err).max() < 1e-9


def _target(pl, take, T, x):
    return pl.target_fn(take, T, x)


def test_controller_conserves_L(pl):
    """Closed-loop rider with hip shift and throttle: independent finite-difference check of L."""
    take = dict(X=0.0, Z=4.0, VX=11.0, VZ=10.0, beta=math.radians(44), W=math.radians(-20), sf=0.0, sr=0.0,
                wf=45.0, wr=47.0)
    x = [0.0, -100.0, 0.0, 40.0, 20.0, -20.0]
    dt = 1 / 1200
    rec, con = pl.A.run_control(take, _target(pl, take, 2.2, x), r0=0.0, p0=math.radians(-100), dt=dt,
                                rec_dt=dt / 2, t_max=1.2, T_land=2.2)
    L0 = pl.A.L0
    worst = 0.0
    for a, b in zip(rec[:-1], rec[1:]):
        h = b["t"] - a["t"]
        RA, RB = 0.5 * (a["RA"] + b["RA"]), 0.5 * (a["RB"] + b["RB"])
        wA = air.logm_so3(b["RA"] @ a["RA"].T) / h
        wB = air.logm_so3(b["RB"] @ a["RB"].T) / h
        D = 0.5 * (a["D"] + b["D"])
        Ddot = (b["D"] - a["D"]) / h
        L = _L(pl, RA, RB, wA, wB, D, Ddot, 0.5 * (a["wr"] + b["wr"]), a["wf"], 0.5 * (a["steer"] + b["steer"]))
        worst = max(worst, np.linalg.norm(L - L0) / np.linalg.norm(L0))
    assert worst < 1e-2, worst


def test_controller_tracks_gentle_whip(pl, monkeypatch):
    """A mild whip (30 % of Damien's peak) is well inside the body's limits: the bike must follow it closely."""
    monkeypatch.setattr(pl, "PEAK_YAW", [v * 0.3 for v in pl.PEAK_YAW])
    monkeypatch.setattr(pl, "PEAK_ROLL", [v * 0.3 for v in pl.PEAK_ROLL])
    take = dict(X=0.0, Z=4.0, VX=11.0, VZ=10.0, beta=math.radians(44), W=math.radians(-38), sf=0.0, sr=0.0,
                wf=45.0, wr=47.0)
    x = [0.0, 0.0, 0.0, 15.0, 8.0, -6.0]
    rec, con = pl.A.run_control(take, _target(pl, take, 2.2, x), dt=1 / 1200, rec_dt=1 / 60, t_max=1.5, T_land=2.2)
    assert max(math.degrees(r["track_err"]) for r in rec) < 6.0


def test_full_whip_peak_is_flown(pl):
    """Damien's full-size whip peak (bike flat at -85 deg, rear out 55 deg) is reached within 10 deg RMS."""
    pl.S.T_face = 1344.4
    t, st, sp, rec = pl.to_takeoff(14.868)
    take = pl.take_from(st, sp, rec)
    d = pl.objective(np.array([0.0, -80.0, 15.0, 45.0, 25.0, -30.0]), take, 2.23, detail=True)
    assert d["peak_track_rms_deg"] < 10.0
    assert d["worst_overreach_m"] < 0.15


def test_recorded_flight_matches_scored_flight(pl):
    """The flight that is rendered must be the one the optimiser scored (same controller settings)."""
    pl.S.T_face = 1344.4
    t, st, sp, rec = pl.to_takeoff(14.873)
    take = pl.take_from(st, sp, rec)
    x = np.array([12.5, -44.4, 0.0, 36.9, 14.4, 0.0])
    det = pl.objective(x, take, 2.2317, dt=1.0 / 1200, detail=True)
    recA, con = pl.fly(take, x, 2.2317)
    ya, pa, ra = (math.degrees(v) for v in air.euler_of(con["RA"]))
    assert abs(con["t"] - det["t_air"]) < 1e-9
    assert abs(ya - det["land_yaw"]) < 1e-6 and abs(ra - det["land_roll"]) < 1e-6
