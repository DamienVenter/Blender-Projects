"""One-page physics sheet for the whip demo (PNG).

python3 physics_sheet.py DATA_DIR OUT_PNG
"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import ground
import params as P
import sim

data, out = sys.argv[1], sys.argv[2]
hud = json.load(open(f"{data}/hud.json"))
scene = json.load(open(f"{data}/scene.json"))
summ = json.load(open(f"{data}/summary.json"))
tr = scene["terrain"]
k = tr["keys"]
t = np.array([h["t"] for h in hud])
air_mask = np.array([h["phase"] == "AIR" for h in hud])
t_air = summ["t_air"]

INK, MUTED, GRID = "#1d232b", "#6b7380", "#e6e8eb"
C_BIKE, C_RIDER, C_TARGET, C_FORK, C_SHOCK = "#c8102e", "#1f3b63", "#9aa3ad", "#c9a24a", "#4b7bb5"
plt.rcParams.update({"font.family": "Inter", "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
                     "axes.spines.top": False, "axes.spines.right": False})
fig = plt.figure(figsize=(16, 10), dpi=150)
gs = fig.add_gridspec(3, 3, height_ratios=[1.25, 1, 1], hspace=0.45, wspace=0.28)

# 1. trajectory to scale
ax = fig.add_subplot(gs[0, :])
xs, zs = np.array(tr["xs"]), np.array(tr["zs"])
m = (xs > k["ramp_bottom"] - 4) & (xs < k["landing_bottom"] + 4)
ax.fill_between(xs[m], 0, zs[m], color="#d8c3a5", lw=0)
ramp = (xs >= k["ramp_bottom"]) & (xs <= 0)
ax.plot(xs[ramp], zs[ramp], color="#5a4a3e", lw=2.5)
cx = np.array([h["cx"] for h in hud]); cz = np.array([h["cz"] for h in hud])
ax.plot(cx, cz, color=INK, lw=1.2, label="centre of mass (bike + rider)")
dots = [i for i in range(len(hud)) if air_mask[i] and int(round(hud[i]["t"] * 10)) != int(round(hud[i - 1]["t"] * 10))]
ax.scatter(cx[dots], cz[dots], s=10, color=INK, zorder=3)
ia = int(np.argmax(np.where(air_mask, cz, -1)))
ax.annotate(f"apex {cz[ia]:.2f} m\n(t = {t[ia]:.2f} s)", (cx[ia], cz[ia]), (cx[ia] + 2, cz[ia] + 0.8),
            arrowprops=dict(arrowstyle="-", color=MUTED), color=INK)
ax.annotate("", (k["knuckle"], k["lip_height"] - 1.6), (0, k["lip_height"] - 1.6),
            arrowprops=dict(arrowstyle="<->", color=MUTED))
ax.text(k["knuckle"] / 2, k["lip_height"] - 1.45, "75 ft (22.86 m) lip to knuckle", ha="center", color=MUTED)
ax.set_aspect("equal")
ax.set_xlim(k["ramp_bottom"] - 3, k["landing_bottom"] + 3)
ax.set_ylim(0, max(cz) + 1.5)
ax.set_xlabel("distance from lip (m)")
ax.set_ylabel("height (m)")
ax.set_title("Flight path to scale, dots every 0.1 s in the air", loc="left", color=INK, fontsize=12)
take = summ["take"]
v_lip = (take["VX"] ** 2 + take["VZ"] ** 2) ** 0.5
facts = (f"Run-in speed at the ramp toe  {summ['approach_speed']*3.6:.1f} km/h\n"
         f"Steady throttle up the face  {summ['face_throttle_N']:.0f} N at the tyre\n"
         f"Lip speed  {v_lip*3.6:.1f} km/h at {np.degrees(np.arctan2(take['VZ'], take['VX'])):.1f} deg\n"
         f"Rotation off the lip  {np.degrees(take['W']):.1f} deg/s nose down\n"
         f"Airtime  {t_air:.2f} s   (your clips: 2.0 to 2.2 s)\n"
         f"Ramp 2.51 m lip, 9.1 m radius, {P.LIP_ANGLE_DEG:.1f} deg\n"
         f"Landing 4.0 m knuckle, {P.LANDING_ANGLE_DEG:.0f} deg downslope\n"
         f"Johannesburg: g = {P.G:.3f} m/s2, air {P.RHO:.2f} kg/m3")
ax.text(0.995, 0.97, facts, transform=ax.transAxes, ha="right", va="top", fontsize=9.5, color=INK,
        bbox=dict(boxstyle="round,pad=0.6", fc="white", ec=GRID))

# 2. bike angles vs Damien's target
ta = t[air_mask]
sc = t_air / sim.TARGET["t"][-1]
tt = np.array(sim.TARGET["t"]) * sc
x = summ["whip_x"]
for j, (key, lab) in enumerate((("bike_yaw", "yaw (nose left +)"), ("bike_roll", "lean (left -)"))):
    ax = fig.add_subplot(gs[1, j])
    tgt = np.array(sim.TARGET["yaw" if key == "bike_yaw" else "roll"]) * (x[3] if key == "bike_yaw" else x[2])
    ax.plot(tt, tgt, "o", color=C_TARGET, ms=4, label="from your clips")
    ax.plot(ta, [h[key] for h, a in zip(hud, air_mask) if a], color=C_BIKE, lw=2, label="bike (simulated)")
    rk = "rider_yaw" if key == "bike_yaw" else "rider_roll"
    ax.plot(ta, [h[rk] for h, a in zip(hud, air_mask) if a], color=C_RIDER, lw=1.6, label="rider torso (from physics)")
    ax.set_title(f"Whip: {lab}", loc="left", color=INK, fontsize=11)
    ax.set_xlabel("time after lip (s)")
    ax.set_ylabel("degrees")
    ax.legend(frameon=False, fontsize=8.5)
ax = fig.add_subplot(gs[1, 2])
ax.plot(ta, [h["bike_pitch"] for h, a in zip(hud, air_mask) if a], color=C_BIKE, lw=2, label="bike pitch")
ax.axhline(-P.LANDING_ANGLE_DEG, color=C_TARGET, ls="--", lw=1, label="landing slope")
ax.set_title("Bike pitch (nose up +)", loc="left", color=INK, fontsize=11)
ax.set_xlabel("time after lip (s)")
ax.set_ylabel("degrees")
ax.legend(frameon=False, fontsize=8.5)

# 3. suspension, loads, rider absorption over the whole run
ax = fig.add_subplot(gs[2, 0:2])
ax.plot(t, [h["sf"] * 1000 for h in hud], color=C_FORK, lw=1.8, label=f"fork (travel {P.FORK_TRAVEL*1000:.0f} mm)")
ax.plot(t, [h["sr"] * 1000 for h in hud], color=C_SHOCK, lw=1.8, label=f"rear wheel (travel {P.REAR_TRAVEL*1000:.0f} mm)")
ax.axhline(P.FORK_TRAVEL * 1000, color=C_FORK, ls=":", lw=1)
ax.axhline(P.REAR_TRAVEL * 1000, color=C_SHOCK, ls=":", lw=1)
ax.axvspan(0, t_air, color="#f2f4f7", zorder=0)
ax.text(t_air / 2, 15, "airborne", ha="center", color=MUTED)
ax.set_title("Suspension travel", loc="left", color=INK, fontsize=11)
ax.set_xlabel("time after lip (s)")
ax.set_ylabel("mm")
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
ax = fig.add_subplot(gs[2, 2])
tot = np.array([h["Nf"] + h["Nr"] for h in hud]) / (ground.System().M * P.G)
ax.plot(t, tot, color=INK, lw=1.4)
ax.axvspan(0, t_air, color="#f2f4f7", zorder=0)
ax.set_title("Ground load on the tyres (g)", loc="left", color=INK, fontsize=11)
ax.set_xlabel("time after lip (s)")
ax.set_ylabel("g")
fig.suptitle("Whip physics demo: 2026 CRF250R, 75 ft steel FMX ramp, rider 185 cm", x=0.06, ha="left",
             fontsize=15, color=INK, fontweight="bold")
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("SHEET OK", out)
