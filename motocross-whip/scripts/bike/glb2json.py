"""GLB -> self-contained glTF JSON (buffer embedded as a data URI), for hosts that serve .json but not .glb.
python3 glb2json.py IN.glb OUT.json"""
import base64, json, struct, sys

data = open(sys.argv[1], "rb").read()
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
doc["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binary).decode("ascii")
json.dump(doc, open(sys.argv[2], "w"), separators=(",", ":"))
print(sys.argv[2], round(len(json.dumps(doc)) / 1e6, 2), "MB")
