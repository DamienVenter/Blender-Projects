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


def _check_L(pl, rec):
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
    return worst


@pytest.mark.parametrize("bike_only", [False, True])
def test_controller_conserves_L(pl, bike_only):
    """Closed-loop rider with hip shift, spine, throttle and steering: independent finite-difference check of L,
    with the lip kick shared by bike and rider or given to the bike alone (the L0 formula must match the motion)."""
    take = dict(X=0.0, Z=4.0, VX=11.0, VZ=10.0, beta=math.radians(44), W=math.radians(-20), sf=0.0, sr=0.0,
                wf=45.0, wr=47.0)
    x = pl.X0.copy()
    dt = 1 / 1200
    rec, con = pl.A.run_control(take, _target(pl, take, 2.2, x), r0=math.radians(120), p0=math.radians(-200), dt=dt,
                                rec_dt=dt / 2, t_max=1.2, T_land=2.2, gains=pl.gains(2.2, x), kick_bike_only=bike_only)
    worst = _check_L(pl, rec)
    assert worst < 1e-2, worst


def test_controller_tracks_feasible_motion(pl):
    """A motion the physics can do (a free flight after a lip kick, the rider holding still) must be followed
    closely when given as the target: the controller adds no error of its own."""
    take = dict(X=0.0, Z=4.0, VX=11.0, VZ=10.0, beta=math.radians(44), W=math.radians(-38), sf=0.0, sr=0.0,
                wf=45.0, wr=47.0)
    hold = lambda t: (np.eye(3), np.zeros(3))
    free, _ = pl.A.run_control(take, hold, r0=math.radians(60), p0=math.radians(-80), dt=1 / 1200, rec_dt=1 / 1200,
                               t_max=1.2, T_land=9.0, gains={"w_track": 0.0, "w_rider": 0.0})
    ts = np.array([r["t"] for r in free])

    def target(t):
        i = min(int(round(t * 1200)), len(free) - 2)
        R0, R1 = free[i]["RA"], free[i + 1]["RA"]
        return R0, air.logm_so3(R1 @ R0.T) * 1200, free[i]["RB"]
    rec, _ = pl.A.run_control(take, target, r0=math.radians(60), p0=math.radians(-80), dt=1 / 1200, rec_dt=1 / 60,
                              t_max=1.15, T_land=9.0, gains={"w_rider": 0.0})
    assert ts[-1] > 1.1
    assert max(math.degrees(r["track_err"]) for r in rec) < 2.0


def test_measured_whip_is_flown(pl):
    """The flown solution matches Damien's measured whip as his camera sees it, with a human body."""
    pl.S.T_face = 1344.4
    t, st, sp, rec = pl.to_takeoff(14.873)
    take = pl.take_from(st, sp, rec)
    d = pl.objective(pl.X0, take, 2.23, detail=True)
    assert d["seen_rms_deg"] < sim.Pipeline.SEEN_RMS_OK
    assert d["worst_overreach_m"] < 0.20                 # arms at full stretch plus shoulder blades
    assert d["rider_spin_max_deg_s"] < math.degrees(sim.Pipeline.RIDER_SPIN_MAX)
    assert d["head_up_min"] > 0.15                        # never upside down
    assert abs(d["land_yaw"]) < 5 and abs(d["land_roll"]) < 5


def test_recorded_flight_matches_scored_flight(pl):
    """The flight that is rendered must be the one the optimiser scored (same controller settings)."""
    pl.S.T_face = 1344.4
    t, st, sp, rec = pl.to_takeoff(14.873)
    take = pl.take_from(st, sp, rec)
    x = pl.X0.copy()
    x[2] = 0.0
    det = pl.objective(x, take, 2.2317, dt=1.0 / 1200, detail=True)
    recA, con = pl.fly(take, x, 2.2317)
    ya, pa, ra = (math.degrees(v) for v in air.euler_of(con["RA"]))
    assert abs(con["t"] - det["t_air"]) < 1e-9
    assert abs(ya - det["land_yaw"]) < 1e-6 and abs(ra - det["land_roll"]) < 1e-6


# ---------------------------------------------------------------- replica of the measured 3D whip (replicate.py)
@pytest.fixture(scope="module")
def rep(pl):
    import replicate as RP
    pl.S.T_face = 1344.4
    t, st, sp, rec = pl.to_takeoff(14.873)
    take = pl.take_from(st, sp, rec)
    return RP.Replicator(pl, take, 2.232)


def test_replica_follows_3d_measurement(rep):
    """The replica's bike attitude is the two-phone 3D measurement (within its noise) from 0.15 s after the lip."""
    ts, Rs = rep.bike.samples
    err = [math.degrees(np.linalg.norm(air.logm_so3(rep.bike.R(t) @ R.T))) for t, R in zip(ts, Rs) if t > 0.15]
    assert math.sqrt(np.mean(np.square(err))) < 4.0


def test_replica_motion_is_smooth(rep):
    """No jerks: bike angular acceleration stays below 15000 deg/s2 up to the straighten, spin rate continuous
    through the lip."""
    tg = np.arange(-0.2, rep.bike.t_s, 1 / 120)
    Rg = [rep.bike.R(t) for t in tg]
    w = np.array([np.degrees(air.logm_so3(Rg[i + 1] @ Rg[i].T)) * 120 for i in range(len(Rg) - 1)])
    a = np.linalg.norm(np.diff(w, axis=0), axis=1) * 120
    assert a.max() < 15000.0


def test_momentum_calculation_matches_simulation(pl, rep, monkeypatch):
    """The replica's angular momentum calculation is constant on a flight the simulator produced (which conserves
    it by construction): validates the physics check reported for the replica (bars straight, as in the replica)."""
    monkeypatch.setattr(pl.A, "STEER_MAX", 0.0)
    take = rep.take
    f = lambda t: (air.Ry(-take["beta"]) @ air.Rx(math.radians(-30) * min(t / 0.4, 1.0)), np.zeros(3), air.Ry(-take["beta"]))
    rec, _ = pl.A.run_control(take, f, r0=math.radians(40), p0=math.radians(-60), dt=1 / 1200, rec_dt=1 / 120,
                              t_max=1.0, T_land=9.0, gains={"w_rider": 0.1})
    tg = np.array([r["t"] for r in rec])
    ser = [(r["RA"], r["RB"], r["shift"], r["spine"], r["wr"]) for r in rec]
    L, _, _ = rep.momentum(ser, tg)
    dev = np.linalg.norm(L[3:-3] - pl.A.L0, axis=1).max()
    assert dev < 0.03 * np.linalg.norm(pl.A.L0), dev


def test_soft_ik_has_no_snap():
    """The elbow moves continuously as the arm reaches full extension (no square-root snap)."""
    import rider as RD
    root, pole = np.zeros(3), np.array([0.0, 0.0, 1.0])
    L = RD.L_UPPER_ARM + RD.L_FOREARM + RD.L_HAND_GRIP
    prev, worst = None, 0.0
    for d in np.linspace(0.85 * L, 1.05 * L, 400):
        mid, end, ok = RD.two_bone(root, np.array([d, 0.0, 0.0]), RD.L_UPPER_ARM, RD.L_FOREARM + RD.L_HAND_GRIP, pole)
        if prev is not None:
            worst = max(worst, np.linalg.norm(mid - prev))
        prev = mid
    assert worst < 0.004          # m per 0.5 mm step of reach


def test_shoulder_blade_eases_the_arm_straight():
    """Near full stretch the shoulder blade takes a smoothly growing share of the reach: the elbow speeds up and then
    eases into the straight arm in one hump (no pause and restart: a stutter), never faster than 0.5 deg per mm of
    reach, and the hand reaches the grip all the way to the arm plus the shoulder blade's reach."""
    import rider as RD
    l1, l2 = RD.L_UPPER_ARM, RD.L_FOREARM + RD.L_HAND_GRIP
    A = l1 + l2
    ds = np.linspace(0.7 * A, A + RD.SCAPULA_REACH, 4000)
    sl = np.array([RD.scapula_slide(d, l1, l2) for d in ds])
    r = ds - sl
    assert np.all(np.diff(sl) >= -1e-12)                          # the shoulder blade only slides forward
    assert np.all(np.diff(r) >= -1e-12)                           # the arm only extends
    assert r.max() < A and sl.max() <= RD.SCAPULA_REACH + 0.001   # reachable (the elbow keeps its 5 deg: 0.7 mm)
    bend = np.degrees(np.arccos(np.clip((r * r - l1 * l1 - l2 * l2) / (2 * l1 * l2), -1, 1)))
    rate = -np.diff(bend) / np.diff(ds) / 1000.0                   # deg per mm of reach
    assert rate.max() < 0.5
    k = int(np.argmax(rate))
    assert np.all(np.diff(rate[:k]) >= -1e-6) and np.all(np.diff(rate[k:]) <= 1e-6)    # one hump
    assert abs(bend[-1] - RD.ELBOW_MIN_BEND_DEG) < 0.01


def test_join_blend_is_smooth():
    """Two records that meet with a jump in value, rate and acceleration are joined smoothly: after the blend (either
    side bent onto the other) all three agree at the join, measured from each side."""
    import export
    tj, h = 1.0, 3e-6
    f_a = lambda t: np.array([np.sin(3 * t), 0.2 * t ** 3])            # earlier simulation
    f_b = lambda t: np.array([0.3 + np.cos(2 * t), -t ** 2 + 0.5])      # later one (jumps in every derivative)
    # records every 1/120 s, plus three either side of the join a few microseconds apart, so that the derivatives
    # read from each side are exact enough to show what is left of the jumps
    ts = [t for t in np.arange(0.5, 1.5, 1 / 120) if abs(t - tj) > 0.01] + [tj - k * h for k in (1, 2, 3)] \
        + [tj + k * h for k in (0, 1, 2)]
    for side in ("before", "after"):
        D = [{"t": t, "kind": "a" if t < tj else "b", "v": (f_a if t < tj else f_b)(t)} for t in sorted(ts)]
        ia = [i for i, d in enumerate(D) if d["kind"] == "a"][::-1][:3]
        ib = [i for i, d in enumerate(D) if d["kind"] == "b"][:3]
        jumps0 = [np.abs(x - y) for x, y in zip(export._side_state(D, ia, "v", False, tj),
                                                 export._side_state(D, ib, "v", False, tj))]
        export.blend_join(D, tj, {"v": (side, 0.2)}, ("b",))
        jumps = [np.abs(x - y) for x, y in zip(export._side_state(D, ia, "v", False, tj),
                                                export._side_state(D, ib, "v", False, tj))]
        for k, (j0, j1) in enumerate(zip(jumps0, jumps)):
            assert np.all(j1 <= 0.02 * j0 + 1e-6), (side, k, j0, j1)     # value, rate, acceleration


@pytest.fixture(scope="module")
def export_unsolved(pl, rep, tmp_path_factory):
    """The full export pipeline (ramp, lip join, air, touchdown join, landing) on the replica with its hidden angles at
    zero (no 6-minute solve): what export does at the joins does not depend on them."""
    import export
    import replicate as RP
    rep.x = np.zeros(rep.n_x())
    recA, con = rep.records()
    g2 = pl.landing(recA, con)
    t, st, sp, g1 = pl.to_takeoff(14.873)
    log = dict(mode="replicated", t_off=t, take=rep.take, t_air=con["t"], T_air_target=rep.T_air, whip_x=None)
    out = str(tmp_path_factory.mktemp("export"))
    dbg = {}
    info = export.build(pl, log, g1, recA, con, g2, out, debug=dbg,
                        seen_fn=lambda tt: (rep.bike.R(tt), float(RP.lean_filmed(tt / rep.sc))))
    return out, info, dbg["drivers"], log


def test_exported_animation_has_no_pops(export_unsolved):
    """Over the whole clip, every part moves smoothly: no one-frame pops at the first frame, the lip or touchdown
    (before the fix: 3150 deg/s arm pops and a 33 cm whole-bike jump at the lip, a head flip after touchdown)."""
    import smoothness
    out, info, D, log = export_unsolved
    res, (dmin, dmax) = smoothness.audit(f"{out}/frames.json")
    assert dmax - dmin < 1e-9                                    # even frames
    for name, r in res.items():
        assert r["wobble_max"] < 400.0, (name, r)                # deg/s
        assert r["vwobble_max"] < 2.0, (name, r)                 # m/s
    assert res["bike:frame"]["vwobble_max"] < 0.6


def test_tyres_stay_out_of_the_ramp_on_the_lip(pl, export_unsolved):
    """While the whip is thrown on the lip the ramp holds the rear tyre: it never sinks into the ramp face."""
    import export
    out, info, D, log = export_unsolved
    S, T = pl.S, pl.T
    for d in D:
        if -0.3 < d["t"] - log["t_off"] < 0.0:
            c = export.tyre_clearance(d["RA"], d["pb"], d["sf"], d["sr"], S.cb, T.ground, ("rear",))
            assert c > -0.01, (d["t"] - log["t_off"], c)
