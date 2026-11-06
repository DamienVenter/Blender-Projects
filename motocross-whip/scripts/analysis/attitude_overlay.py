"""Measure Damien's whip from his clips: draw the bike (and a stick rider) at a hypothesised world
attitude, seen from a camera placed like his, next to the real frame. Adjust the attitude keyframes
(research/whip-attitude-measured.md) until the drawings match the footage.

Attitude parameters (degrees), composed in this order, all about WORLD axes:
    R = Rx(drop) . Rz(yaw) . Ry(-pitch) . Rx(roll)
  roll  : lay the bike over about its own long axis (left lay-down is negative)
  pitch : nose up positive
  yaw   : nose to the rider's left positive (rear wheel out to his right)
  drop  : turn the whole bike about the travel direction (seen from behind: clockwise positive).
          A crossed-up bike (yaw 90) with drop -90 hangs nose-down, top facing left.
This order keeps a fully sideways, nose-down bike free of gimbal lock.

python3 attitude_overlay.py OUT.jpg CLIP_DIR LIP_FRAME CAM SPEC [SPEC ...] [--sim REC.npz]
  CAM  = x,y,z,f_px    camera position (world, lip at x=0) and focal length in pixels
  SPEC = frame                (attitude from the measured table, scripts/demo/whip_measured.py), or
         frame:drop:yaw:pitch:roll[:rider_yaw:rider_pitch:rider_roll][@cx,cy,size]
         (@ gives the real crop centre and size in pixels when the automatic blob finder fails)
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "demo"))
import params as P          # noqa: E402
import bike as B            # noqa: E402
import ground               # noqa: E402
import air                  # noqa: E402
import terrain              # noqa: E402
from pose import Poser      # noqa: E402

FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FPS_CLIP = 30.0
D = math.radians


def attitude(drop, yaw, pitch, roll):
    return air.Rx(D(drop)) @ air.Rz(D(yaw)) @ air.Ry(-D(pitch)) @ air.Rx(D(roll))


def bike_lines():
    """(colour, width, [points]) polylines in the bike frame (x fwd, y left, z up; origin on the ground
    under the rear axle at full extension)."""
    out = []
    circ = lambda c, r: [(c[0] + r * math.cos(a), 0.0, c[1] + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 41)]
    out.append(("#111111", 5, circ(P.REAR_AXLE, P.R_REAR)))
    out.append(("#111111", 5, circ(P.FRONT_AXLE, P.R_FRONT)))
    fa = B.fork_axis()
    F = lambda d: (P.FRONT_AXLE[0] + fa[0] * d, 0.0, P.FRONT_AXLE[1] + fa[1] * d)
    out.append(("#c8a020", 4, [F(0.0), F(0.97)]))                                   # fork
    out.append(("#777777", 4, [(0.0, 0.0, P.R_REAR), (P.SWINGARM_PIVOT[0], 0.0, P.SWINGARM_PIVOT[1])]))
    out.append(("#444444", 6, [(0.60, 0, 0.33), (0.96, 0, 0.33), (0.96, 0, 0.67), (0.60, 0, 0.67), (0.60, 0, 0.33)]))
    out.append(("#d01818", 6, [(-0.40, 0, 0.95), (0.02, 0, 0.89), (0.45, 0, 0.98), (0.84, 0, 1.00), (1.07, 0, 0.92)]))
    out.append(("#d01818", 5, [(1.26, 0, 0.87), (1.74, 0, 0.99)]))                   # front fender
    g = P.GRIP
    out.append(("#999999", 4, [(g[0], P.GRIP_HALF_SPAN, g[1]), (g[0] + 0.05, 0, g[1]), (g[0], -P.GRIP_HALF_SPAN, g[1])]))
    return out


class Overlay:
    def __init__(self):
        self.S = ground.System()
        self.A = air.AirSim(self.S, terrain.Terrain())
        self.poser = Poser(self.S)
        self.lines = bike_lines()

    def world_points(self, RA, RB, pb):
        """Bike polylines and rider joints in world coordinates for bike CoM at pb."""
        S = self.S
        W = lambda q: pb + RA @ (np.asarray(q, float) - S.cb)
        polys = [(c, w, [W(p) for p in pts]) for c, w, pts in self.lines]
        q, _ = self.A.posture(RA.T @ RB, np.zeros(6))
        hip, spine = q[:3], q[3:]
        origin = W(S.peg) + RA @ hip
        rp = self.poser.rider_parts(RA, RB, W, origin, pb + np.array([20.0, 0, -5]), 0.0, spine=spine)
        J = {k: v[0] for k, v in rp.items()}
        rider = []
        for s in ("l", "r"):
            knee = rp[f"shank_{s}"][0]
            ankle = rp[f"foot_{s}"][0]
            rider.append(("#202020", 7, [J[f"thigh_{s}"], knee, ankle]))
            rider.append(("#2e8b6a", 6, [J[f"upper_arm_{s}"], J[f"forearm_{s}"], J[f"hand_{s}"]]))
        sh = 0.5 * (J["upper_arm_l"] + J["upper_arm_r"])
        rider.append(("#2e8b6a", 12, [J["pelvis"], sh]))
        return polys, rider, J["head"]

    @staticmethod
    def project(cam, look, f, pts, size):
        fwd = look - cam
        fwd /= np.linalg.norm(fwd)
        right = np.cross(fwd, [0.0, 0.0, 1.0])
        right /= np.linalg.norm(right)
        up = np.cross(right, fwd)
        W, H = size
        out = []
        for p in pts:
            d = np.asarray(p) - cam
            z = d @ fwd
            out.append((W / 2 + f * (d @ right) / z, H / 2 - f * (d @ up) / z))
        return out

    def draw(self, RA, RB, pb, cam, f, size, ss=3):
        polys, rider, head = self.world_points(RA, RB, pb)
        W, H = size
        im = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        look = pb
        P2 = lambda pts: [(x * ss, y * ss) for x, y in self.project(cam, look, f, pts, size)]
        for c, w, pts in rider[:4]:            # far side first is not known; draw legs/arms under the bike
            dr.line(P2(pts), fill=c, width=w * ss // 2, joint="curve")
        for c, w, pts in polys:
            dr.line(P2(pts), fill=c, width=w * ss // 2, joint="curve")
        for c, w, pts in rider[4:]:
            dr.line(P2(pts), fill=c, width=w * ss // 2, joint="curve")
        hx, hy = P2([head])[0]
        r = f * 0.15 / np.linalg.norm(head - cam) * ss
        dr.ellipse([hx - r, hy - r, hx + r, hy + r], fill="#f4f4f4", outline="#555555", width=ss)
        return im.resize(size, Image.LANCZOS)


def trajectory():
    """Bike CoM path (x, z) after the lip from the demo's no-whip flight (Damien's practice jump is
    similar in size; only used to place the drawing in front of the camera)."""
    import sim
    pl = sim.Pipeline()
    pl.S.T_face = 1344.4
    v = 14.873
    t, st, sp, rec = pl.to_takeoff(v)
    take = pl.take_from(st, sp, rec)
    rec, con = pl.no_whip(take)
    ts = np.array([r["t"] for r in rec])
    pb = np.array([r["C"] - (pl.S.mr / pl.S.M) * r["D"] for r in rec])
    return ts, pb


SIMREC = None


def main():
    global SIMREC
    if "--sim" in sys.argv:                    # --sim REC.npz: arrays t, RA, RB of a simulated flight (t after lip)
        i = sys.argv.index("--sim")
        SIMREC = dict(np.load(sys.argv[i + 1]))
        del sys.argv[i:i + 2]
    out, clip, lip = sys.argv[1], sys.argv[2], float(sys.argv[3])
    cx, cy, cz, f = map(float, sys.argv[4].split(","))
    cam = np.array([cx, cy, cz])
    ov = Overlay()
    ts, pbs = trajectory()
    font = ImageFont.truetype(FONT, 15)
    tiles = []
    for spec in sys.argv[5:]:
        spec, _, at = spec.partition("@")
        if SIMREC is not None and ":" not in spec:   # frame number only, with --sim: draw the simulated flight
            fr0 = float(spec)
            tq = (fr0 - lip) / FPS_CLIP
            i = int(np.argmin(np.abs(SIMREC["t"] - tq)))
            RA, RB = SIMREC["RA"][i], SIMREC["RB"][i]
            spec = f"{fr0}:SIM"
        elif ":" not in spec:                  # frame number only: use the measured key table
            import whip_measured as WM
            fr0 = float(spec)
            dr_, yw_, pt_, rl_, rr_ = (float(a) for a in WM.params_at((fr0 - lip) / FPS_CLIP, WM.table(44.0, -40.0)))
            spec = f"{fr0}:{dr_}:{yw_}:{pt_}:{rl_}:0:0:{rr_}"
        if spec.endswith(":SIM"):
            fr = float(spec.split(":")[0])
            label = "simulated flight"
        else:
            v = [float(s) for s in spec.split(":")]
            fr, drop, yaw, pitch, roll = v[:5]
            ry, rp, rr = v[5:8] if len(v) >= 8 else (0.0, 0.0, 0.0)
            RA = attitude(drop, yaw, pitch, roll)
            RB = air.Rz(D(ry)) @ air.Ry(-D(rp)) @ air.Rx(D(rr))
            label = f"drop {drop:.0f} yaw {yaw:.0f} pitch {pitch:.0f} roll {roll:.0f}"
        t = (fr - lip) / FPS_CLIP
        pb = np.array([np.interp(t, ts, pbs[:, k]) for k in range(3)])
        real = Image.open(f"{clip}/f_{int(fr):03d}.png").convert("RGB")
        size = real.size
        dw = ov.draw(RA, RB, pb, cam, f, size)
        # crop both around the drawing's bounding box (the camera tracks the rider like the real operator)
        bb = dw.getbbox() or (0, 0, *size)
        c0 = ((bb[0] + bb[2]) // 2, (bb[1] + bb[3]) // 2)
        half = max(bb[2] - bb[0], bb[3] - bb[1]) // 2 + 25
        sim_bg = Image.new("RGB", size, (150, 185, 225))
        sim_bg.paste(dw, (0, 0), dw)
        sim_crop = sim_bg.crop((c0[0] - half, c0[1] - half, c0[0] + half, c0[1] + half)).resize((300, 300), Image.LANCZOS)
        sys.path.insert(0, HERE)
        from find import blob
        if at:
            ax, ay, aw = (int(a) for a in at.split(","))
            bl = (ax, ay, aw, aw)
        else:
            bl = blob(f"{clip}/f_{int(fr):03d}.png", (0, 0, size[0], int(size[1] * 0.72)))
        rc = (bl[0], bl[1]) if bl else c0
        rhalf = max(half, (max(bl[2], bl[3]) // 2 + 15) if bl else half)
        real_crop = real.crop((rc[0] - rhalf, rc[1] - rhalf, rc[0] + rhalf, rc[1] + rhalf)).resize((300, 300), Image.LANCZOS)
        tile = Image.new("RGB", (300, 640), (16, 20, 24))
        tile.paste(real_crop, (0, 20))
        tile.paste(sim_crop, (0, 335))
        d = ImageDraw.Draw(tile)
        d.text((4, 2), f"f{int(fr)}  t={t:+.2f}s  real", fill="white", font=font)
        d.text((4, 320), label, fill="#ffd700", font=font)
        tiles.append(tile)
    sheet = Image.new("RGB", (len(tiles) * 304, 640), (0, 0, 0))
    for i, tl in enumerate(tiles):
        sheet.paste(tl, (i * 304, 0))
    sheet.save(out, quality=90)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
