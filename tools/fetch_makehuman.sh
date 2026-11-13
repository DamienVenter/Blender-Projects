#!/usr/bin/env bash
# MakeHuman data for the rider's body: the base mesh, the shape targets and the default skeleton with its skin
# weights, from MPFB 2.0.18 (MakeHuman's Blender extension). Pinned by checksum; idempotent.
#
# The data is CC0 (MakeHuman moved the base mesh and targets from AGPL to CC0 in September 2020:
# https://static.makehumancommunity.org/oldsite/faq/what_changed_regarding_the_license_in_2020.html; the weight file
# says "license": "CC0"). MPFB's code (GPL-3) is not used: scripts/rider/mhdata.py reads the files itself.
#
# Usage: tools/fetch_makehuman.sh          -> ${MH_DATA:-$HOME/.cache/makehuman/mpfb-2.0.18}/data
set -euo pipefail

VERSION=2.0.18
SHA=c075b3e9b94b8e5556a5f03f4653602d02ea306de08126e8f55ed6dee28a2dad
URL="https://extensions.blender.org/download/sha256:${SHA}/add-on-mpfb-v${VERSION}.zip?repository=%2Fapi%2Fv1%2Fextensions%2F&blender_version_min=4.2.0"
DEST=${MH_DATA:-$HOME/.cache/makehuman/mpfb-${VERSION}}

if [[ -f "${DEST}/data/3dobjs/base.obj" && -f "${DEST}/data/rigs/standard/weights.default.json" ]]; then
  echo "MakeHuman data present: ${DEST}/data"
  exit 0
fi
mkdir -p "$DEST"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
curl -fsSL --max-time 900 -o "${TMP}/mpfb.zip" "$URL"
echo "${SHA}  ${TMP}/mpfb.zip" | sha256sum -c -
# only the data this project reads (no code)
python3 -I - "${TMP}/mpfb.zip" "$DEST" <<'EOF'
import sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
keep = ("data/3dobjs/", "data/targets/", "data/rigs/standard/rig.default.json",
        "data/rigs/standard/weights.default.json")
names = [n for n in z.namelist() if n.startswith(keep) and not n.endswith("/") and ".." not in n]
for n in names:
    z.extract(n, sys.argv[2])
print(len(names), "files")
EOF
echo "MakeHuman data: ${DEST}/data"
