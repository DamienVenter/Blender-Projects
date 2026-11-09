"""Chart: Damien's whip (two-phone 3D measurement) against simulated/replicated flights, on the quantities that
make a whip look big. python3 differences.py OUT.png MEAS_FIT.json LABEL1=flight1.npz [LABEL2=flight2.npz ...]"""
import json
import math
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CAM3 = np.array([-16.0, 4.0, 1.5])          # clip 3 phone (research/whip-attitude-3d/cams_clips23.json)


def traj(t):
    """Approximate CoM path after the lip (only used for the camera's line of sight)."""
    return np.array([11.75 * t, 0.0, 3.45 + 10.97 * t - 0.5 * 9.786 * t * t])


def quantities(t, R):
    n, yb, zb = R[:, 0], R[:, 1], R[:, 2]
    heading = math.degrees(math.atan2(abs(n[1]), n[0])) if math.hypot(n[0], n[1]) > 0.25 else float("nan")
    laid = math.degrees(math.acos(max(min(zb[2], 1.0), -1.0)))
    los = traj(t) - CAM3
    los /= np.linalg.norm(los)
    right = np.cross(los, [0, 0, 1.0]); right /= np.linalg.norm(right)
    up = np.cross(right, los)
    ang = math.degrees(math.atan2(n @ up, -(n @ right))) % 180.0      # axle line in the picture, 0 = horizontal
    return heading, laid, ang, abs(float(yb @ los))


def series(ts, Rs):
    q = np.array([quantities(t, R) for t, R in zip(ts, Rs)])
    q[:, 2] = np.degrees(np.unwrap(np.radians(q[:, 2]) * 2) / 2)
    return q


def main():
    out, fit = sys.argv[1], json.load(open(sys.argv[2]))
    tm = np.array([fit[k]["t"] for k in sorted(fit, key=int)])
    Rm = [np.array(fit[k]["R"]) for k in sorted(fit, key=int)]
    qm = series(tm, Rm)
    flights = []
    for arg in sys.argv[3:]:
        lab, path = arg.split("=")
        d = np.load(path)
        m = d["t"] <= 2.0
        flights.append((lab, d["t"][m], series(d["t"][m], d["RA"][m])))
    INK, MUTED, GRID = "#1d232b", "#6b7380", "#e6e8eb"
    cols = ["#c8102e", "#1f3b63", "#c9a24a"]
    plt.rcParams.update({"font.family": "Inter", "font.size": 10, "axes.edgecolor": MUTED, "axes.grid": True,
                         "grid.color": GRID, "axes.spines.top": False, "axes.spines.right": False})
    fig, axs = plt.subplots(2, 2, figsize=(14, 8.5), dpi=150)
    titles = [("How sideways (nose from the travel direction, deg)", "90 = fully sideways"),
              ("How far laid over (seat from vertical, deg)", "90 = flat, more = past flat"),
              ("Bike angle in your clip 3 picture (deg)", "0 = horizontal, 90 = hanging nose-down"),
              ("How side-on to your clip 3 phone", "0 = edge-on, 1 = full profile")]
    for j, ax in enumerate(axs.ravel()):
        ax.plot(tm, qm[:, j], "o", ms=3.5, color="#4b5563", label="your whip (two phones, 3D)")
        for (lab, ts, q), c in zip(flights, cols):
            ax.plot(ts, q[:, j], color=c, lw=2, label=lab)
        ax.set_title(titles[j][0], loc="left", color=INK, fontsize=11)
        ax.set_xlabel(f"time after the lip (s)    {titles[j][1]}", fontsize=8.5, color=MUTED)
        ax.set_xlim(0, 2.0)
    axs[0, 0].legend(frameon=False, fontsize=9)
    fig.suptitle("Your whip against my demos: the quantities that make it look big", x=0.06, ha="left",
                 fontsize=14, color=INK, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, facecolor="white")
    print("saved", out)


if __name__ == "__main__":
    main()
