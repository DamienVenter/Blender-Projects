"""Honda's five studio photos beside the Blender renders from the same calibrated cameras, with the scores.

python3 studio_sheet.py RENDER_DIR SCORES.json OUT.jpg [TITLE]
  RENDER_DIR  holds render_honda_<view>.png (build_bike.py, transparent film: put on white here)
  SCORES.json from compare.py (OUT_PREFIX_scores.json)
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cams                                             # noqa: E402

REF = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")
CROPS = {"left": (150, 250, 3850, 2150), "right": (150, 250, 3850, 2150), "top": (700, 500, 3300, 1750),
         "front": (1250, 150, 2750, 2150), "rear": (1250, 150, 2750, 2150)}
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"


def pair(view, rdir, width):
    """(photo, render) of VIEW, both cropped alike and scaled to WIDTH."""
    u0, v0, u1, v1 = CROPS[view]
    ph = Image.open(os.path.join(REF, cams.FILES[view])).convert("RGB").crop((u0, v0, u1, v1))
    rd = Image.open(os.path.join(rdir, f"render_honda_{view}.png")).convert("RGBA")
    bg = Image.new("RGBA", rd.size, (255, 255, 255, 255))
    bg.alpha_composite(rd)
    k = rd.width / 4000.0
    rd = bg.convert("RGB").crop((int(u0 * k), int(v0 * k), int(u1 * k), int(v1 * k)))
    h = round(width * (v1 - v0) / (u1 - u0))
    return ph.resize((width, h), Image.LANCZOS), rd.resize((width, h), Image.LANCZOS)


def main(rdir, scores_path, out, title="CRF250R plastics pass"):
    sc = json.load(open(scores_path))
    f_big, f_mid, f_small = (ImageFont.truetype(FONT, s) for s in (40, 26, 20))
    W, gap, pad = 2400, 16, 28
    half = (W - 2 * pad - gap) // 2
    quarter = (W - 2 * pad - 3 * gap) // 4
    blocks = []
    for view in ("left", "right", "top"):
        blocks.append((view, [pair(view, rdir, half)]))
    fr = pair("front", rdir, quarter) + pair("rear", rdir, quarter)
    y = pad + 64
    rows = []
    for view, pairs in blocks:
        a, b = pairs[0]
        rows.append((view, y, [(pad, a), (pad + half + gap, b)]))
        y += a.height + 58
    rows.append(("front and rear", y, [(pad + i * (quarter + gap), im) for i, im in enumerate(fr)]))
    y += fr[0].height + 58
    sheet = Image.new("RGB", (W, y + pad - 20), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((pad, pad - 6), title, fill=(20, 20, 22), font=f_big)
    d.text((W - pad, pad + 8), "Honda's studio photo on the left of each pair, the model through the same camera on the right",
           fill=(110, 110, 115), font=f_small, anchor="ra")
    for view, y0, items in rows:
        for x, im in items:
            sheet.paste(im, (x, y0))
        yb = y0 + items[0][1].height + 8
        if view in sc:
            s = sc[view]
            txt = f"{view.upper()}   red plastics overlap {round(100 * s['red'])} %   whole silhouette {round(100 * s['silhouette'])} %"
        else:
            txt = "FRONT   red plastics overlap %d %%   silhouette %d %%          REAR   red plastics overlap %d %%   silhouette %d %%" % (
                round(100 * sc["front"]["red"]), round(100 * sc["front"]["silhouette"]),
                round(100 * sc["rear"]["red"]), round(100 * sc["rear"]["silhouette"]))
        d.text((pad, yb), txt, fill=(60, 60, 64), font=f_mid)
    sheet.save(out, quality=90)
    print(out, sheet.size)


if __name__ == "__main__":
    main(*sys.argv[1:5])
