"""The cameras of his photos 07, 08 and 09, fitted relative to the helmet (joint front fit, decision 47).

python3 his_cameras.py            writes research/his-photo-cameras.json (about 12 min)

head_closeups.py's views p07, p08 and p09 were set by eye; p08 looked at his face from below where his photo sees
the crown from above (his head pitched far down). Each photo's camera is now fitted to the helmet itself, in its
frame (helmet.py: metres, x his left, y back, z up), so a view rides the helmet whatever the pose:
  1. landmarks read on the photo (READINGS, photo px with a sigma) against the helmet's measured points: the
     landmarks of Leatt's photos solved together (research/helmet-ba.json), the centres of the print's elements
     (helmet_art.json) and of each visor chevron (cast like the drawn ones). A search over the view direction and
     roll, scale and shift in closed form (weak perspective; the photos are long-lens shots, 9 to 12 m), keeps the
     camera on the side that sees the readings' surfaces;
  2. the print's colour: around that direction (+-SWEEP deg) each camera is scored by the correlation of the photo's
     and the textured helmet's Lab a*, b* (chroma: the daylight's shading cancels) inside MASKS (the helmet, his
     goggle and body left out), and the best one refined (Powell) on that score plus the landmarks' chi-square.
The camera is helmet_ba's convention (rows of R: x right, y up, z forward; v = cy - f y / z). DIST: the distance
the long-lens perspective is set at (07: research/rider-cameras.json's cam07, fitted to the bike, stands 9.2 m
off; 08 and 09: 12 m, a 300 mm lens at their scale; the perspective over the helmet's depth differs by 3 %).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "research", "his-photo-cameras.json"))
REF = os.path.normpath(os.path.join(HERE, "..", "..", "reference", "damien-bike-2026-11-12"))
PHOTOS = {"07": "07_left-side-riding-pan.jpg", "08": "08_whip-from-below_right-side.jpg",
          "09": "09_whip-from-below_left-front.jpg"}
# Readings (photo px, sigma px) on 3x to 6x crops. art:<frame> is a print element's centre (helmet_art.json),
# chevL<i>/chevR<i> visor chevron i on his left/right (0 the rear one, 6 the front one). 07: a panning shot, the
# helmet about 150 px long; the visor's dark top slot (733, 45) is one of its top windows (not modelled), left out.
READINGS = {
    "07": {"visor_tip": (606, 97, 4), "chevL6": (625, 91, 2), "chevL0": (667, 73, 2), "art:side_icon": (695, 163, 2)},
    "08": {"art:visor_chevrons": (1250, 321, 3), "art:visor_chevrons_R": (1204, 254, 3),
           "crown_vent_L": (1272, 285, 3), "visor_rear_edge": (1251, 269, 4), "visor_tip": (1196, 304, 6)},
    "09": {"brow_badge": (1166, 346, 2), "visor_tip": (1120, 328, 4), "art:side_icon": (1218, 441, 3),
           "visor_rear_edge": (1197, 301, 4), "art:visor_chevrons": (1207, 331, 3)},
}
# the helmet in each photo, his goggle (lens, frame, strap) and body left out (photo px)
MASKS = {
    "07": [(604, 96), (660, 62), (700, 45), (735, 32), (758, 42), (772, 80), (772, 125), (745, 150), (718, 178),
           (690, 190), (655, 182), (648, 150), (690, 142), (698, 105), (650, 100)],
    "08": [(1190, 245), (1225, 224), (1265, 226), (1290, 248), (1296, 290), (1283, 322), (1255, 338), (1240, 334),
           (1215, 300), (1196, 268)],
    "09": [(1100, 330), (1150, 305), (1200, 298), (1240, 300), (1262, 320), (1275, 350), (1272, 400), (1255, 430),
           (1235, 455), (1210, 460), (1195, 440), (1240, 400), (1250, 370), (1150, 355), (1110, 345)],
}
AZ_RANGE = {"07": (30, 150), "08": (-90, 90), "09": (-90, 90)}   # his face shows in all three: camera ahead
DIST = {"07": 9.2, "08": 12.0, "09": 12.0}
SWEEP, STEP = 25.0, 5.0
# the crop round his head in each photo (x, y, size px: the comparison sheets' crops) that the views render
CROP = {"07": (590, 14, 240), "08": (1080, 170, 280), "09": (1036, 234, 280)}
LAM = 0.02                         # landmark chi-square weight against the colour correlation (about 1 at best)
COVER = 0.5                        # weight of the mask's covered share (keeps the helmet filling its outline)


def basis(az, el, roll):
    """Camera rows (x right, y up, z forward) and the unit vector to the camera: az 0 ahead (-y), 90 on his left
    (+x); el up; roll turns the image clockwise."""
    a, e, r = np.radians([az, el, roll])
    back = np.array([np.sin(a) * np.cos(e), -np.cos(a) * np.cos(e), np.sin(e)])
    zc = -back
    xc = np.cross(zc, [0, 0, 1.0])
    xc /= np.linalg.norm(xc)
    yc = np.cross(xc, zc)
    return np.vstack([np.cos(r) * xc - np.sin(r) * yc, np.sin(r) * xc + np.cos(r) * yc, zc]), back


def project(cam, X):
    q = (np.atleast_2d(X) - cam["C"]) @ np.asarray(cam["R"]).T
    return np.c_[cam["cx"] + cam["f"] * q[:, 0] / q[:, 2], cam["cy"] - cam["f"] * q[:, 1] / q[:, 2]]


def rotvec(v):
    th = np.linalg.norm(v)
    if th < 1e-12:
        return np.eye(3)
    k = v / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def points():
    """The helmet's measured points (helmet frame): solved landmarks (L, R, centre), print element centres, visor
    chevron centres."""
    import helmet_art as A
    ba = json.load(open(os.path.join(HERE, "..", "..", "research", "helmet-ba.json")))["landmarks"]
    pts = {}
    for k, v in ba.items():
        X = np.array(v["X"])
        if v["kind"].startswith("pair"):
            pts[k + "_L"], pts[k + "_R"] = X, X * [-1, 1, 1]
        else:
            pts[k] = X
    d = json.load(open(A.DATA))
    r, c, P, N, S = A.texels(2048)
    for f in d["frames"]:
        pts["art:" + f["name"]] = np.array(f["o"])
        if f["name"].startswith("visor_chevrons"):
            sh = np.asarray(f["proj"].get("shift", (0.0, 0.0)))
            X, _ = A.photo_to_shell(P[S == 1], N[S == 1], "top", [np.asarray(p).mean(0) + sh for p in f["polys"]],
                                    P[::3])
            for i, x in enumerate(X):
                pts["chev%s%d" % ("R" if f["name"].endswith("_R") else "L", i)] = x
    return pts


def lab(rgb):
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def textured(tex=512):
    """The helmet's outer surfaces as points with their print's Lab a*, b*."""
    import helmet_art as A
    from PIL import Image
    r, c, P, N, S = A.texels(tex)
    img = np.asarray(Image.open(os.path.join(HERE, "..", "..", "textures", "rider", "helmet_pinata.png"))
                     .convert("RGB"))
    k = img.shape[0] // tex
    return P, N, lab(img[r * k + k // 2, c * k + k // 2])


def objective(ph, pts, model):
    """The scores of a camera for photo ph: colour(cam) -> (correlation, mask share covered), chi(cam) -> the
    landmarks' chi-square, and score(cam), the fit's objective (lower is better)."""
    from matplotlib.path import Path
    from PIL import Image
    from scipy import ndimage
    rd = READINGS[ph]
    X = np.array([pts[k] for k in rd])
    uvr = np.array([v[:2] for v in rd.values()], float)
    sg = np.array([v[2] for v in rd.values()], float)
    P, N, mlab = model
    from scipy.spatial import cKDTree
    Nx = N[cKDTree(P).query(X)[1]]
    photo = np.asarray(Image.open(os.path.join(REF, PHOTOS[ph])).convert("RGB")).astype(float)
    H, W = photo.shape[:2]
    poly = np.array(MASKS[ph], float)
    x0, y0 = np.floor(poly.min(0)).astype(int) - 10
    x1, y1 = np.ceil(poly.max(0)).astype(int) + 10
    yy, xx = np.mgrid[y0:y1, x0:x1]
    inside = Path(poly).contains_points(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    ref = lab(ndimage.gaussian_filter(photo[y0:y1, x0:x1], (1.2, 1.2, 0)))

    def colour(cam):
        uv = project(cam, P)
        z = (P - cam["C"]) @ cam["R"][2]
        face = np.sum(N * (cam["C"] - P), 1) > 0
        u, v = np.round(uv[:, 0]).astype(int) - x0, np.round(uv[:, 1]).astype(int) - y0
        idx = np.nonzero(face & (u >= 0) & (u < x1 - x0 - 1) & (v >= 0) & (v < y1 - y0 - 1))[0]
        idx = idx[np.argsort(-z[idx])]
        img = np.zeros((y1 - y0, x1 - x0, 2))
        has = np.zeros((y1 - y0, x1 - x0), bool)
        for du in (0, 1):
            for dv in (0, 1):
                img[v[idx] + dv, u[idx] + du] = mlab[idx]
                has[v[idx] + dv, u[idx] + du] = True
        m = has & inside
        if m.sum() < 200:
            return -1.0, 0.0
        s = 0.0
        for k in (0, 1):
            a, b = img[..., k][m] - img[..., k][m].mean(), ref[..., k][m] - ref[..., k][m].mean()
            s += np.sum(a * b) / np.sqrt(np.sum(a * a) * np.sum(b * b) + 1e-9)
        return s / 2, m.sum() / inside.sum()

    def chi(cam):
        return float(np.sum(((project(cam, X) - uvr) / sg[:, None]) ** 2))

    def score(cam):                              # the colour term: the sum of a* and b*'s correlations
        ncc, cover = colour(cam)
        return -2 * ncc - COVER * cover + LAM * chi(cam)
    return dict(colour=colour, chi=chi, score=score, X=X, uvr=uvr, sg=sg, Nx=Nx, W=W, H=H, rd=rd)


def fit(ph, pts, model, log=print):
    from scipy import optimize
    ob = objective(ph, pts, model)
    colour, chi, X, uvr, Nx, rd = (ob[k] for k in ("colour", "chi", "X", "uvr", "Nx", "rd"))
    D = DIST[ph]

    def weak(az, el, ro):
        R, back = basis(az, el, ro)
        q = X @ R.T
        a = np.c_[q[:, 0], -q[:, 1]]
        am, um = a.mean(0), uvr.mean(0)
        s = np.sum((a - am) * (uvr - um)) / np.sum((a - am) ** 2)
        t = um - s * am
        return dict(R=R, C=back * D, f=s * D, cx=t[0], cy=t[1]), s, back

    best = None                                  # 1: landmarks, every direction and roll
    for az in np.arange(*AZ_RANGE[ph], 6.0):
        for el in np.arange(-84.0, 85.0, 6.0):
            for ro in np.arange(-180.0, 180.0, 6.0):
                cam, s, back = weak(az, el, ro)
                if s <= 0:
                    continue
                cost = chi(cam) + 50 * np.sum(np.clip(0.05 - Nx @ back, 0, None))
                if best is None or cost < best[0]:
                    best = (cost, az, el, ro)
    log(ph, "landmarks alone: az %.0f el %.0f roll %.0f" % best[1:])
    top = None                                   # 2: the print's colour round it
    for az in np.arange(best[1] - SWEEP, best[1] + SWEEP + 1e-6, STEP):
        for el in np.arange(best[2] - SWEEP, best[2] + SWEEP + 1e-6, STEP):
            for ro in np.arange(best[3] - SWEEP, best[3] + SWEEP + 1e-6, STEP):
                cam, s, back = weak(az, el, ro)
                if s <= 0:
                    continue
                sc = ob["score"](cam)
                if top is None or sc < top[0]:
                    top = (sc, az, el, ro, cam)
    log(ph, "colour sweep: az %.0f el %.0f roll %.0f" % top[1:4])
    c0 = top[4]

    def cam_of(p):
        return dict(R=rotvec(p[:3]) @ c0["R"], C=c0["C"] + p[3:6] * 0.001 * D, f=c0["f"] * (1 + p[6] * 0.01),
                    cx=c0["cx"], cy=c0["cy"])

    p = optimize.minimize(lambda p: ob["score"](cam_of(p)), np.zeros(7), method="Powell",
                          options=dict(xtol=1e-3, ftol=1e-4, maxfev=3000)).x
    log(ph, "refined: turned %.2f deg, moved %.0f mm, f x %.3f" % (np.degrees(np.linalg.norm(p[:3])),
                                                                 np.linalg.norm(p[3:6]) * D, 1 + p[6] * 0.01))
    cam = cam_of(p)
    uv = project(cam, X)
    err = np.linalg.norm(uv - uvr, axis=1)
    ncc, cover = colour(cam)
    view = -cam["R"][2]                          # helmet -> camera, unit
    out = dict(R=cam["R"].tolist(), C=cam["C"].tolist(), f=float(cam["f"]), cx=float(cam["cx"]),
               cy=float(cam["cy"]), W=ob["W"], H=ob["H"], crop=CROP[ph], photo=PHOTOS[ph],
               to_camera=np.round(view, 4).tolist(),
               az_el_deg=[round(float(np.degrees(np.arctan2(view[0], -view[1]))), 1),
                          round(float(np.degrees(np.arcsin(view[2]))), 1)],
               landmark_rms_px=round(float(np.sqrt(np.mean(err ** 2))), 2), colour_ncc=round(float(ncc), 3),
               mask_covered=round(float(cover), 3), px_per_mm=round(float(cam["f"] / D / 1000), 3),
               readings={k: dict(read=list(v), model=np.round(m, 1).tolist(), err_px=round(float(e), 1))
                         for (k, v), m, e in zip(rd.items(), uv, err)})
    log(ph, "fitted: to the camera az %.1f el %.1f deg, landmarks rms %.2f px, colour %.3f" % (
        out["az_el_deg"][0], out["az_el_deg"][1], out["landmark_rms_px"], ncc))
    return out


def load(path=OUT):
    """{photo: camera dict (R, C as arrays)} from the json."""
    d = json.load(open(path))["cameras"]
    return {k: dict(v, R=np.array(v["R"]), C=np.array(v["C"])) for k, v in d.items()}


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    pts = points()
    model = textured()
    cams = {ph: fit(ph, pts, model) for ph in sorted(READINGS)}
    json.dump(dict(frame="HELMET: metres, x to the wearer's left, y back, z up (helmet.py)",
                   convention="rows of R: camera x right, y up, z forward; u = cx + f x / z, v = cy - f y / z",
                   method="his_cameras.py: landmark readings, then the print colour (Lab a*, b* correlation)",
                   sources="photos: reference/damien-bike-2026-11-12; helmet points: research/helmet-ba.json, "
                           "helmet_art.json", cameras=cams),
              open(OUT, "w"), indent=1)
    print("written", OUT)
