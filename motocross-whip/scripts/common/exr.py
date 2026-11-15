"""A small reader for the uncompressed scanline EXR files Blender writes (numpy only, no OpenEXR library).

    channels = read("render.exr")      # {"ViewLayer.Combined.R": float32 array (H, W), ...}
    rgb = layer(channels, "Combined")  # (H, W, 3) or (H, W, 4) with alpha

scene_look.apply(scene, "linear") writes such files: a multilayer EXR, 32-bit float, compression NONE, so the scene
look can be fitted offline on the scene-referred values (decision 54). Blender 5.2 writes multilayer files as
multi-part EXR (version flags 0x1402: long names, multi-part), one part per pass, and plain ones as single-part
(0x402). Only scanline parts, compression NONE, HALF, FLOAT or UINT channels; anything else raises.
"""
import struct

import numpy as np

_PIXEL = {0: np.uint32, 1: np.float16, 2: np.float32}


def _cstr(f):
    s = b""
    while True:
        c = f.read(1)
        if c in (b"\0", b""):
            return s
        s += c


def _header(f):
    """One header's attributes: name -> (type, raw bytes); {} for the empty header that ends a multi-part list."""
    out = {}
    while True:
        name = _cstr(f)
        if not name:
            return out
        typ = _cstr(f)
        size = struct.unpack("<i", f.read(4))[0]
        out[name.decode()] = (typ.decode(), f.read(size))


def _chlist(raw):
    chans, i = [], 0
    while raw[i:i + 1] != b"\0":
        j = raw.index(b"\0", i)
        name = raw[i:j].decode()
        ptype, = struct.unpack("<i", raw[j + 1:j + 5])
        xs, ys = struct.unpack("<ii", raw[j + 9:j + 17])
        if (xs, ys) != (1, 1):
            raise ValueError("subsampled channel %s" % name)
        chans.append((name, ptype))
        i = j + 17
    return chans


def _part(a, path):
    if a["compression"][1][0] != 0:
        raise ValueError("compressed EXR (%d) not supported: %s" % (a["compression"][1][0], path))
    if "type" in a and a["type"][1].rstrip(b"\0") != b"scanlineimage":
        raise ValueError("only scanline parts are supported: %s" % path)
    x0, y0, x1, y1 = struct.unpack("<iiii", a["dataWindow"][1])
    W, H = x1 - x0 + 1, y1 - y0 + 1
    chans = sorted(_chlist(a["channels"][1]))
    n = struct.unpack("<i", a["chunkCount"][1])[0] if "chunkCount" in a else H
    return dict(W=W, H=H, y0=y0, chans=chans, chunks=n)


def _line(out, p, y, buf):
    k = 0
    for n, t in p["chans"]:
        dt = np.dtype(_PIXEL[t]).newbyteorder("<")
        m = p["W"] * dt.itemsize
        out[n][y - p["y0"]] = np.frombuffer(buf[k:k + m], dtype=dt).astype(np.float32)
        k += m


def read(path):
    """All channels of an uncompressed scanline EXR (single or multi-part) as float32 arrays, rows top to bottom."""
    with open(path, "rb") as f:
        magic, version = struct.unpack("<ii", f.read(8))
        if magic != 20000630:
            raise ValueError("not an EXR file: %s" % path)
        if version & 0x200:
            raise ValueError("tiled EXR not supported: %s" % path)
        multi = bool(version & 0x1000)
        parts = []
        while True:
            a = _header(f)
            if not a:
                break
            parts.append(_part(a, path))
            if not multi:
                break
        out = {}
        for p in parts:
            out.update({n: np.zeros((p["H"], p["W"]), np.float32) for n, _ in p["chans"]})
            f.read(8 * p["chunks"])                       # offset table (chunks are read in file order)
        for _ in range(sum(p["chunks"] for p in parts)):
            k = struct.unpack("<i", f.read(4))[0] if multi else 0
            y, size = struct.unpack("<ii", f.read(8))
            _line(out, parts[k], y, f.read(size))
    return out


def layer(channels, name, view_layer=None):
    """One pass as an (H, W, C) array: RGB(A) passes as R, G, B(, A); X/Y/Z or V passes as their channels."""
    keys = [k for k in channels if k.split(".")[-2:-1] == [name] and (view_layer is None or k.split(".")[0] == view_layer)]
    if not keys:
        raise KeyError("no pass %r in %s" % (name, sorted({k.rsplit(".", 1)[0] for k in channels})))
    order = "RGBAXYZV"
    keys.sort(key=lambda k: order.index(k[-1]) if k[-1] in order else 9)
    return np.stack([channels[k] for k in keys], -1)
