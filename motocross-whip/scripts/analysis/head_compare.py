"""Where the replica's helmet appears in each of Damien's phone pictures, against where his helmet is.

Both are offsets (px) from the red plastics' bbox centre (the phones pan with the rider). The replica's head and
bike come from an export (frames.json); its time is Damien's time x sc (replicate.Replicator.sc).
python3 head_compare.py FRAMES.json SC HELM_C2.json HELM_C3.json OUT.png
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "demo"))
from fit3d import red_points                    # noqa: E402
from head3d import project, R3D                # noqa: E402
from smoothness import q2R                     # noqa: E402


def replica_offsets(frames_path, sc, cams, lip=29, frames=range(29, 77)):
    fr = json.load(open(frames_path))
    names, F = fr["objects"], fr["frames"]
    T = np.array([f["t"] for f in F]) - fr["t_off"]
    jb, jh = names.index("bike:frame"), names.index("rider:head")
    pts, _ = red_points()
    out = {}
    for f in frames:
        t = (f - lip) / 30.0 * sc
        i = int(np.argmin(abs(T - t)))
        o, R = np.array(F[i]["tf"][jb][:3]), q2R(F[i]["tf"][jb][3:])
        head = np.array(F[i]["tf"][jh][:3])
        red = o + (R @ pts.T).T
        pos = red.mean(axis=0)
        res = {}
        for v in ("clip2", "clip3"):
            cam, fl = np.array(cams[v]["cam"]), cams[v]["f_size"]
            # the phone's position relative to the jump: the replica flies the physics path, the phone stands where
            # it stood relative to the lip
            p_red = project(cam, pos, fl, red)
            lo, hi = np.percentile(p_red, 2, axis=0), np.percentile(p_red, 98, axis=0)
            res[v] = (project(cam, pos, fl, head[None, :])[0] - 0.5 * (lo + hi)).tolist()
        out[f] = res
    return out


def main():
    frames_path, sc = sys.argv[1], float(sys.argv[2])
    helm = {"clip2": json.load(open(sys.argv[3])), "clip3": json.load(open(sys.argv[4]))}
    out_png = sys.argv[5]
    cams = json.load(open(os.path.join(R3D, "cams_clips23.json")))
    rep = replica_offsets(frames_path, sc, cams)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Inter", "font.size": 10, "axes.grid": True, "grid.color": "#e6e8eb",
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axs = plt.subplots(2, 2, figsize=(13, 7.5), dpi=150, sharex=True)
    for col, v in enumerate(("clip2", "clip3")):
        fs = sorted(int(f) for f in helm[v] if helm[v][f][3])
        t = [(f - 29) / 30 for f in fs]
        for row, k, lab in ((0, 0, "across the picture (px, right +)"), (1, 1, "up the picture (px, down +)")):
            axs[row, col].plot(t, [helm[v][str(f)][k] for f in fs], "o", ms=3.5, color="#4b5563", label="your helmet")
            tr = [(f - 29) / 30 for f in sorted(rep)]
            axs[row, col].plot(tr, [rep[f][v][k] for f in sorted(rep)], color="#c8102e", lw=2, label="replica helmet")
            axs[row, col].set_title(f"{'Clip 2' if v == 'clip2' else 'Clip 3'} phone: helmet from bike centre, {lab}",
                                    loc="left", fontsize=10)
    axs[0, 0].legend(frameon=False)
    for ax in axs[1]:
        ax.set_xlabel("time after the lip (s, your clock)")
    fig.suptitle("Where your head is relative to the bike, as each phone sees it", x=0.06, ha="left", fontsize=14,
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out_png, facecolor="white")
    err = {v: np.array([np.subtract(rep[int(f)][v], helm[v][f][:2]) for f in helm[v] if helm[v][f][3] and int(f) in rep])
           for v in helm}
    for v, e in err.items():
        print(v, "RMS error px", np.round(np.sqrt((e ** 2).mean(axis=0)), 1))
    json.dump({str(f): r for f, r in rep.items()}, open(out_png.replace(".png", ".json"), "w"))


if __name__ == "__main__":
    main()
