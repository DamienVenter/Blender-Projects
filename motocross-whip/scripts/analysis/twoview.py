"""Two-camera fit sheet for the clips 2 + 3 jump: rows clip3 real / drawn / clip2 real / drawn; one column per spec.
SPEC = t:drop:yaw:pitch:roll[:ry:rp:rl]   t = s after the lip (lip = frame 29 in both clips)."""
import sys, json, math, numpy as np
sys.path.insert(0, "/home/user/blender-projects/motocross-whip/scripts/analysis")
sys.path.insert(0, "/home/user/blender-projects/motocross-whip/scripts/demo")
from PIL import Image, ImageDraw, ImageFont
import air
from attitude_overlay import Overlay, attitude, trajectory
import os
S = os.environ.get("WHIP_FRAMES", ".")   # folder with cm/c2, cm/c3 frames and box_c2.json, box_c3.json, fit23.json
_b3 = {int(k): v[:2] for k, v in json.load(open(f"{S}/box_c3.json")).items() if v[4] > 0}
C3 = {33: (190, 435), 37: (254, 429), 41: (170, 385), 45: (224, 429), 49: (205, 410), 53: (217, 436), 57: (205, 440),
      61: (202, 466), 65: (210, 455), 69: (195, 465), 73: (180, 475), 77: (150, 540), 81: (125, 600), 85: (150, 645), 29: (276, 474), 31: (285, 460)}
C3.update(_b3)
c2 = {int(k): v for k, v in json.load(open(f"{S}/box_c2.json")).items() if v[4] > 0}
VIEWS = [("clip3", f"{S}/cm/c3", np.array([-16.0, 4.0, 1.5]), 1280.0, C3, 150),
         ("clip2", f"{S}/cm/c2", np.array([-6.0, 2.5, 1.0]), 900.0, {k: v[:2] for k, v in c2.items()}, 300)]
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 15)
ov = Overlay(); ts, pbs = trajectory()
def centre(tab, f):
    ks = np.array(sorted(tab)); return np.array([np.interp(f, ks, [tab[k][j] for k in ks]) for j in (0, 1)])
cols = []
FIT = json.load(open(f"{S}/fit23.json")) if "--fit" in sys.argv else None
args = [a for a in sys.argv[2:] if a != "--fit"]
for spec in args:
    v = [float(s) for s in spec.split(":")]
    t = v[0]
    if FIT is not None:                       # SPEC = t:rider_lean : bike from the 3D fit
        RA = np.array(FIT[str(int(round(29 + 30 * t)))]["R"]); rl = v[1] if len(v) > 1 else 0.0
        RB = air.Ry(-math.radians(max(45 - 40 * t, -40))) @ air.Rx(math.radians(rl)); drop = yaw = pitch = roll = ry = rp = 0
    else:
        drop, yaw, pitch, roll = v[1:5]; ry, rp, rl = v[5:8] if len(v) >= 8 else (0, 0, 0)
        RA = attitude(drop, yaw, pitch, roll); RB = air.Rz(math.radians(ry)) @ air.Ry(-math.radians(rp)) @ air.Rx(math.radians(rl))
    pb = np.array([np.interp(t, ts, pbs[:, k]) for k in range(3)])
    f = int(round(29 + 30 * t))
    col = Image.new("RGB", (300, 4 * 300 + 22), (16, 20, 24)); d = ImageDraw.Draw(col)
    d.text((4, 2), f"t{t:.2f} d{drop:.0f} y{yaw:.0f} p{pitch:.0f} r{roll:.0f} | {ry:.0f},{rp:.0f},{rl:.0f}", fill="white", font=font)
    for i, (name, dr, cam, fpx, tab, half) in enumerate(VIEWS):
        real = Image.open(f"{dr}/f_{f:03d}.png").convert("RGB")
        cx, cy = centre(tab, f); h = half // 2
        rc = real.crop((int(cx) - h, int(cy) - h, int(cx) + h, int(cy) + h)).resize((300, 300), Image.LANCZOS)
        dw = ov.draw(RA, RB, pb, cam, fpx, real.size)
        bb = dw.getbbox() or (0, 0, 478, 850); c0 = ((bb[0] + bb[2]) // 2, (bb[1] + bb[3]) // 2); hh = max(bb[2] - bb[0], bb[3] - bb[1]) // 2 + 20
        bg = Image.new("RGB", real.size, (150, 185, 225)); bg.paste(dw, (0, 0), dw)
        sc = bg.crop((c0[0] - hh, c0[1] - hh, c0[0] + hh, c0[1] + hh)).resize((300, 300), Image.LANCZOS)
        col.paste(rc, (0, 22 + 600 * i)); col.paste(sc, (0, 22 + 600 * i + 300))
        ImageDraw.Draw(col).text((4, 26 + 600 * i), f"{name} f{f}", fill="yellow", font=font)
    cols.append(col)
sh = Image.new("RGB", (304 * len(cols), cols[0].height)); x = 0
for c in cols: sh.paste(c, (x, 0)); x += 304
sh = sh.resize((sh.width * 3 // 4, sh.height * 3 // 4)); sh.save(sys.argv[1], quality=85); print(sh.size)
