"""Honda's studio photo beside the model rendered through the same camera, for one box of the photo, at full size.

python3 pair.py PARTS.npz VIEW u0,v0,u1,v1 OUT.jpg [samples] [zoom]
  VIEW   left, right, front, rear, top (cams.py) or lf34, lr34, rf34, rr34 (fit34.py, if fitted)
  box    in the 4000x2250 photo's pixels: what to compare (a sprocket, an axle block, a muffler cap)
  zoom   enlargement of both halves in the sheet (default: to 900 px tall)
The render is Cycles at the photo's own resolution (BIKE_STUDIO_RES 4000,2250 with BIKE_BORDER), so one pixel of
the render is one pixel of the photo: a part that is 3 px off is 3 px off. About 1 to 3 minutes.
To find a box: cams.CAMS[VIEW].project(points) gives the pixels of 3D points (fit34.load() adds the 34 views).
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "..", "reference", "crf250r-2026")
FILES = {"left": "studio_left-profile_honda-eu-25ym-475600_4000x2250.jpg",
         "right": "studio_right-profile_honda-eu-25ym-475596_4000x2250.jpg",
         "front": "studio_front_honda-eu-25ym-475602_4000x2250.jpg",
         "rear": "studio_rear_honda-eu-25ym-475598_4000x2250.jpg",
         "top": "studio_top_honda-eu-25ym-475594_4000x2250.jpg",
         "lf34": "studio_left-front-34_honda-eu-25ym-475601_4000x2250.jpg",
         "lr34": "studio_left-rear-34_honda-eu-25ym-475599_4000x2250.jpg",
         "rf34": "studio_right-front-34_honda-eu-25ym-475595_4000x2250.jpg",
         "rr34": "studio_right-rear-34_honda-eu-25ym-475597_4000x2250.jpg"}


def main():
    parts, view, box, out = sys.argv[1:5]
    samples = sys.argv[5] if len(sys.argv) > 5 else "48"
    u0, v0, u1, v1 = (int(round(float(q))) for q in box.split(","))
    tmp = out + ".d"
    os.makedirs(tmp, exist_ok=True)
    env = dict(os.environ, BIKE_STUDIO_RES="4000,2250", BIKE_BORDER="%d,%d,%d,%d" % (u0, v0, u1, v1),
               BIKE_SAMPLES=samples)
    subprocess.run(["blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python",
                    os.path.join(HERE, "build_bike.py"), "--", parts, os.path.join(HERE, "..", "..", "textures", "damien-v0"),
                    tmp, "honda_" + view, "stock", "pair"], check=True, env=env,
                   stdout=open(os.path.join(tmp, "log.txt"), "w"), stderr=subprocess.STDOUT)
    ren = Image.open(os.path.join(tmp, "render_honda_%s.png" % view)).convert("RGBA")
    bg = Image.new("RGBA", ren.size, "white")
    bg.alpha_composite(ren)
    ren = bg.convert("RGB")
    ph = Image.open(os.path.join(REF, FILES[view])).convert("RGB").crop((u0, v0, u1, v1))
    ren = ren.resize(ph.size)
    k = float(sys.argv[6]) if len(sys.argv) > 6 else 900.0 / ph.height
    size = (int(ph.width * k), int(ph.height * k))
    sheet = Image.new("RGB", (2 * size[0] + 12, size[1] + 26), "white")
    sheet.paste(ph.resize(size, Image.LANCZOS), (0, 26))
    sheet.paste(ren.resize(size, Image.LANCZOS), (size[0] + 12, 26))
    d = ImageDraw.Draw(sheet)
    d.text((4, 6), "Honda %s photo, px %d,%d..%d,%d" % (view, u0, v0, u1, v1), fill="black")
    d.text((size[0] + 16, 6), "model, same camera", fill="black")
    sheet.save(out, quality=90)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
