"""Render all demo views and assemble the review videos.

python3 assemble.py DATA_DIR WORK_DIR OUT_DIR [--skip-render]

Outputs in OUT_DIR:
  whip_demo.mp4        all views with titles and a physics data overlay (1920x1080, 60 fps)
  whip_vs_damien.mp4   Damien's real clip next to the simulation from a matching angle, synced at the lip
"""
import bisect
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
CLIPS = os.path.join(REPO, "motocross-whip/reference/user-clips")
# the clips 2 and 3 jump (two phones), rear wheel leaving the lip at frame 29 in both
DAMIEN = {"clip3": (os.path.join(CLIPS, "clip3_back-wide_2026-11-06_102401k.mp4"), 0.9396, "CAM_CLIP3"),
          "clip2": (os.path.join(CLIPS, "clip2_back-close_2026-11-06_102401.mp4"), 0.9333, "CAM_CLIP2")}
CMP_LEAD, CMP_AFTER = 0.8, 2.15          # s before / after the lip in the comparison (clip 3 loses him at 2.0 s)
FPS = 120


def run(cmd):
    print(" ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    subprocess.run(cmd, check=True)


def views(fr):
    t0, toff, tl = fr["t_start"], fr["t_off"], fr["t_land"]
    f = lambda t: max(1, int(round((t - t0) * FPS)) + 1)
    last = int(fr["frames"][-1]["f"])
    return {
        "side": dict(cam="CAM_SIDE", res=(1920, 1080), f0=1, f1=last, step=2,
                     title="SIDE VIEW  |  REAL TIME"),
        "clip3": dict(cam="CAM_CLIP3", res=(1080, 1920), f0=f(toff - CMP_LEAD), f1=min(f(toff + CMP_AFTER), last), step=2,
                      title="YOUR CLIP 3 PHONE  |  REAL TIME"),
        "clip2": dict(cam="CAM_CLIP2", res=(1080, 1920), f0=f(toff - CMP_LEAD), f1=min(f(toff + CMP_AFTER), last), step=2,
                      title="YOUR CLIP 2 PHONE  |  REAL TIME"),
        "track": dict(cam="CAM_TRACK", res=(1920, 1080), f0=f(toff - 0.15), f1=min(f(tl + 0.25), last), step=1,
                      title="TRACKING  |  HALF SPEED"),
        "land": dict(cam="CAM_LAND", res=(1920, 1080), f0=f(toff + 0.6), f1=min(f(tl + 2.0), last), step=2,
                     title="FROM THE LANDING  |  REAL TIME"),
    }


def ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def hud_ass(hud, fr, v, path, playback_fps=60):
    """One subtitle event per rendered frame with the physics readout."""
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hud,Inter,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,3,10,0,7,40,40,36,1
Style: Phase,Inter,34,&H0000D7FF,&H0000D7FF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,3,10,0,9,40,40,36,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [head]
    idx = 0
    fs = [q["f"] for q in fr["frames"]]
    for i in range(v["f0"], v["f1"] + 1, v["step"]):
        k = bisect.bisect_left(fs, i)
        if k > 0 and (k == len(fs) or abs(fs[k - 1] - i) <= abs(fs[k] - i)):
            k -= 1
        h = hud[k]
        a, b = idx / playback_fps, (idx + 1) / playback_fps
        t = h["t"]
        tl = f"t {t:+.2f} s" if t < 0 else f"t +{t:.2f} s after lip"
        txt = (f"{tl}\\N{h['kmh']:.1f} km/h\\Nrear tyre {h['height']:.2f} m above ground\\N"
               f"bike: yaw {h['bike_yaw']:+.0f}°  lean {h['bike_roll']:+.0f}°  pitch {h['bike_pitch']:+.0f}°\\N"
               f"rider: yaw {h['rider_yaw']:+.0f}°  lean {h['rider_roll']:+.0f}°\\N"
               f"bars {h.get('steer', 0.0):+.0f}°   rear wheel {h.get('wr', 0.0) * 60 / 6.2832:.0f} rpm\\N"
               f"suspension: fork {h['sf']*1000:.0f} mm  shock {h['sr']*1000:.0f} mm")
        lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Hud,,0,0,0,,{txt}\n")
        lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Phase,,0,0,0,,{h['phase']}\n")
        idx += 1
    with open(path, "w") as f:
        f.writelines(lines)


def main():
    data, work, out = sys.argv[1], sys.argv[2], sys.argv[3]
    skip = "--skip-render" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    os.makedirs(work, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    with open(f"{data}/frames.json") as f:
        fr = json.load(f)
    with open(f"{data}/hud.json") as f:
        hud = json.load(f)
    V = views(fr)
    blend = f"{work}/whip_demo.blend"
    if not skip:
        run(["blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python",
             f"{HERE}/build_scene.py", "--", data, blend])
        for name, v in V.items():
            if only and name not in only:
                continue
            d = f"{work}/frames_{name}"
            subprocess.run(["rm", "-rf", d], check=True)
            os.makedirs(d, exist_ok=True)
            run(["blender", "-b", blend, "--python-exit-code", "1", "--python", f"{HERE}/render_view.py", "--",
                 v["cam"], str(v["res"][0]), str(v["res"][1]), str(v["f0"]), str(v["f1"]), str(v["step"]), d])
    clips = []
    for name, v in V.items():
        d = f"{work}/frames_{name}"
        enc = f"{work}/{name}.mp4"
        vf = []
        if name == "side":
            hud_ass(hud, fr, v, f"{work}/hud_side.ass")
            vf.append(f"subtitles={work}/hud_side.ass")
        if v["res"][1] > v["res"][0]:      # portrait view: centre it on a 1920x1080 canvas
            vf.append("scale=-2:1080,pad=1920:1080:(ow-iw)/2:0:color=0x101418")
        vf.append(f"drawtext=fontfile={FONT}:text='{v['title']}':x=w-tw-40:y=h-th-36:fontsize=30:fontcolor=white:"
                  f"box=1:boxcolor=black@0.55:boxborderw=12")
        run(["ffmpeg", "-v", "error", "-y", "-framerate", "60", "-pattern_type", "glob", "-i", f"{d}/f_*.png",
             "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", enc])
        clips.append(enc)
    # title card
    card = f"{work}/title.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x101418:s=1920x1080:r=60:d=3",
         "-vf", f"drawtext=fontfile={FONT}:text='WHIP PHYSICS DEMO':x=(w-tw)/2:y=h/2-90:fontsize=72:fontcolor=white,"
                f"drawtext=fontfile={FONT}:text='2026 CRF250R  |  23 m KOTW steel ramp to dirt  |  rider 185 cm':"
                f"x=(w-tw)/2:y=h/2+10:fontsize=34:fontcolor=0xC8C8C8,"
                f"drawtext=fontfile={FONT}:text='Proxy shapes only. Whip angles from your two phones in 3D. Flight, ramp and landing simulated.':"
                f"x=(w-tw)/2:y=h/2+70:fontsize=28:fontcolor=0xFFD700",
         "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", card])
    lst = f"{work}/concat.txt"
    with open(lst, "w") as f:
        for c in [card] + clips:
            f.write(f"file '{c}'\n")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", f"{out}/whip_demo.mp4"])
    # Damien's two phones next to the replica from the same spots, synced at the lip: 4 portrait panels
    ins, filt = [], []
    for k, (name, lab) in enumerate((("clip3", "CLIP 3"), ("clip2", "CLIP 2"))):
        path, lip_t, cam = DAMIEN[name]
        v = V[name]
        sim_lip = fr["t_off"] - (fr["t_start"] + (v["f0"] - 1) / FPS)
        ins += ["-ss", f"{max(lip_t - sim_lip, 0.0):.3f}", "-i", path,
                "-framerate", "60", "-pattern_type", "glob", "-i", f"{work}/frames_{name}/f_*.png"]
        filt.append(f"[{2 * k}:v]fps=60,scale=-2:850,setsar=1,drawtext=fontfile={FONT}:text='YOU  {lab}':x=12:y=12:"
                    f"fontsize=26:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=6[r{k}]")
        filt.append(f"[{2 * k + 1}:v]scale=-2:850,setsar=1,drawtext=fontfile={FONT}:text='REPLICA':x=12:y=12:"
                    f"fontsize=26:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=6[s{k}]")
    filt.append("[r0][s0][r1][s1]hstack=inputs=4:shortest=1,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x101418")
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(filt), "-an",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", f"{out}/whip_vs_damien.mp4"])
    print("ASSEMBLE OK")


if __name__ == "__main__":
    main()
