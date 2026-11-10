"""GLB -> self-contained glTF JSON (buffer embedded as a data URI), for hosts that serve .json but not .glb.

python3 glb2json.py IN.glb OUT.json            one file
python3 glb2json.py IN.glb OUT.json MAX_MB     as many files as it takes to keep each under MAX_MB: OUT.json,
                                               OUT_2.json, OUT_3.json ... (the viewer page loads them all)

Every file of a split holds the whole node tree (root, steer and every object's node, so the steering works in each)
but only its share of the meshes, with the accessors, buffer views, materials, textures and images those need.
"""
import base64
import copy
import json
import struct
import sys


def read_glb(path):
    data = open(path, "rb").read()
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    assert magic == b"glTF" and version == 2
    off, doc, binary = 12, None, b""
    while off < length:
        clen, ctype = struct.unpack_from("<I4s", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == b"JSON":
            doc = json.loads(chunk.decode("utf-8"))
        elif ctype == b"BIN\x00":
            binary = chunk
        off += 8 + clen
    return doc, binary


def mesh_views(doc, mi):
    """Buffer views, accessors, materials, textures, images and samplers one mesh needs."""
    acc, mats = set(), set()
    for p in doc["meshes"][mi]["primitives"]:
        acc.update(p.get("attributes", {}).values())
        if "indices" in p:
            acc.add(p["indices"])
        for t in p.get("targets", []):
            acc.update(t.values())
        if "material" in p:
            mats.add(p["material"])
    tex = set()

    def walk(o):
        if isinstance(o, dict):
            if "index" in o and isinstance(o["index"], int) and ("texCoord" in o or len(o) <= 3):
                tex.add(o["index"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for m in mats:
        walk(doc["materials"][m])
    tex = {t for t in tex if t < len(doc.get("textures", []))}
    img = {doc["textures"][t]["source"] for t in tex if "source" in doc["textures"][t]}
    smp = {doc["textures"][t]["sampler"] for t in tex if "sampler" in doc["textures"][t]}
    views = {doc["accessors"][a]["bufferView"] for a in acc if "bufferView" in doc["accessors"][a]}
    views |= {doc["images"][i]["bufferView"] for i in img if "bufferView" in doc["images"][i]}
    return dict(acc=acc, mats=mats, tex=tex, img=img, smp=smp, views=views)


def subset(doc, binary, meshes):
    """A glTF document with only these meshes (indices into doc["meshes"]); everything else pruned and renumbered."""
    need = dict(acc=set(), mats=set(), tex=set(), img=set(), smp=set(), views=set())
    for mi in meshes:
        for k, v in mesh_views(doc, mi).items():
            need[k] |= v
    order = {k: sorted(v) for k, v in need.items()}
    remap = {k: {old: new for new, old in enumerate(v)} for k, v in order.items()}
    mesh_map = {old: new for new, old in enumerate(sorted(meshes))}
    out = {k: copy.deepcopy(v) for k, v in doc.items()
           if k not in ("meshes", "accessors", "bufferViews", "buffers", "materials", "textures", "images", "samplers")}
    for n in out["nodes"]:
        if "mesh" in n:
            if n["mesh"] in mesh_map:
                n["mesh"] = mesh_map[n["mesh"]]
            else:
                del n["mesh"]
    blob = bytearray()
    views = []
    for old in order["views"]:
        bv = dict(doc["bufferViews"][old])
        start = bv.get("byteOffset", 0)
        while len(blob) % 4:
            blob.append(0)
        bv["byteOffset"] = len(blob)
        bv["buffer"] = 0
        blob += binary[start:start + bv["byteLength"]]
        views.append(bv)
    out["bufferViews"] = views
    out["accessors"] = []
    for old in order["acc"]:
        a = dict(doc["accessors"][old])
        if "bufferView" in a:
            a["bufferView"] = remap["views"][a["bufferView"]]
        out["accessors"].append(a)
    if order["smp"]:
        out["samplers"] = [doc["samplers"][s] for s in order["smp"]]
    if order["img"]:
        out["images"] = []
        for old in order["img"]:
            im = dict(doc["images"][old])
            if "bufferView" in im:
                im["bufferView"] = remap["views"][im["bufferView"]]
            out["images"].append(im)
    if order["tex"]:
        out["textures"] = []
        for old in order["tex"]:
            t = dict(doc["textures"][old])
            if "source" in t:
                t["source"] = remap["img"][t["source"]]
            if "sampler" in t:
                t["sampler"] = remap["smp"][t["sampler"]]
            out["textures"].append(t)

    def retex(o):
        if isinstance(o, dict):
            if "index" in o and isinstance(o["index"], int) and o["index"] in remap["tex"] and ("texCoord" in o or len(o) <= 3):
                o["index"] = remap["tex"][o["index"]]
            for v in o.values():
                retex(v)
        elif isinstance(o, list):
            for v in o:
                retex(v)
    out["materials"] = []
    for old in order["mats"]:
        m = copy.deepcopy(doc["materials"][old])
        retex(m)
        out["materials"].append(m)
    out["meshes"] = []
    for old in sorted(meshes):
        m = copy.deepcopy(doc["meshes"][old])
        for p in m["primitives"]:
            p["attributes"] = {k: remap["acc"][v] for k, v in p["attributes"].items()}
            if "indices" in p:
                p["indices"] = remap["acc"][p["indices"]]
            if "targets" in p:
                p["targets"] = [{k: remap["acc"][v] for k, v in t.items()} for t in p["targets"]]
            if "material" in p:
                p["material"] = remap["mats"][p["material"]]
        out["meshes"].append(m)
    out["buffers"] = [dict(byteLength=len(blob),
                           uri="data:application/octet-stream;base64," + base64.b64encode(bytes(blob)).decode("ascii"))]
    return out


def split(doc, binary, max_mb):
    """Groups of meshes, each of whose files stays under max_mb (base64 grows the bytes by a third)."""
    size = {}
    for mi in range(len(doc["meshes"])):
        size[mi] = sum(doc["bufferViews"][v]["byteLength"] for v in mesh_views(doc, mi)["views"])
    budget = max_mb * 1e6 * 0.74 - 0.3e6                     # leave room for the JSON itself
    groups, cur, tot = [], [], 0
    for mi in sorted(size, key=lambda m: -size[m]):
        assert size[mi] < budget, "one mesh alone is over the limit: %s" % doc["meshes"][mi].get("name")
        if tot + size[mi] > budget and cur:
            groups.append(cur)
            cur, tot = [], 0
        cur.append(mi)
        tot += size[mi]
    if cur:
        groups.append(cur)
    return groups


def main():
    src, dst = sys.argv[1], sys.argv[2]
    max_mb = float(sys.argv[3]) if len(sys.argv) > 3 else None
    doc, binary = read_glb(src)
    groups = split(doc, binary, max_mb) if max_mb else [list(range(len(doc["meshes"])))]
    names = []
    for i, g in enumerate(groups):
        path = dst if i == 0 else dst.replace(".json", "_%d.json" % (i + 1))
        text = json.dumps(subset(doc, binary, g), separators=(",", ":"))
        open(path, "w").write(text)
        names.append(path)
        print(path, round(len(text) / 1e6, 2), "MB,", len(g), "meshes")
    return names


if __name__ == "__main__":
    main()
