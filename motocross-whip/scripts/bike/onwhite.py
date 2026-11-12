"""Put turntable.py's RGBA renders on white (Honda's studio), JPEG out.

python3 onwhite.py IN.png [IN2.png ...] OUTDIR

The shadow-catching floor's alpha carries faint denoiser noise (1 to 5 of 255) over the whole background, which
shows as grey streaks on white (2026-11-12): alpha under 6 is cleared and the rest stretched back to full range.
The real contact shadows are far denser (alpha 40 to 140), so they keep their shape.
"""
import os
import sys

import numpy as np
from PIL import Image

FLOOR = 6.0


def on_white(path):
    a = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)
    al = np.clip((a[..., 3] - FLOOR) / (255.0 - FLOOR), 0.0, 1.0)[..., None]
    rgb = a[..., :3] * al + 255.0 * (1.0 - al)
    return Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    out = sys.argv[-1]
    os.makedirs(out, exist_ok=True)
    for p in sys.argv[1:-1]:
        on_white(p).save(os.path.join(out, os.path.splitext(os.path.basename(p))[0] + ".jpg"), quality=93)
