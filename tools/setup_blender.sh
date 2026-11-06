#!/usr/bin/env bash
# Install the pinned Blender build plus the libraries headless rendering needs.
# Idempotent: safe to run at the start of every session.
#
# Usage: tools/setup_blender.sh            (installs BLENDER_VERSION below as `blender`)
#        BLENDER_VERSION=5.2.0 SET_DEFAULT=0 tools/setup_blender.sh
#            (side-by-side install, run it as `blender-5.2.0`)
set -euo pipefail

BLENDER_VERSION=${BLENDER_VERSION:-5.2.3}
SERIES=${BLENDER_VERSION%.*}                       # e.g. 5.2
NAME="blender-${BLENDER_VERSION}-linux-x64"
URL="https://download.blender.org/release/Blender${SERIES}/${NAME}.tar.xz"
DEST=/opt/blender

# 1. Libraries: EEVEE and Workbench need EGL; Mesa provides software OpenGL
#    (llvmpipe) on machines without a GPU. Cycles CPU does not need these.
if ! ldconfig -p | grep -q 'libEGL.so.1'; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    libegl1 libgl1 libgl1-mesa-dri libglx-mesa0 libxi6 libxkbcommon0 libsm6 >/dev/null
fi

# 2. Blender itself.
if [[ ! -x "${DEST}/${NAME}/blender" ]]; then
  mkdir -p "$DEST"
  curl -fsSL -o "${DEST}/${NAME}.tar.xz" "$URL"
  tar -xf "${DEST}/${NAME}.tar.xz" -C "$DEST"
  rm -f "${DEST}/${NAME}.tar.xz"
fi
ln -sf "${DEST}/${NAME}/blender" "/usr/local/bin/blender-${BLENDER_VERSION}"
# SET_DEFAULT=0 installs a side-by-side version (e.g. for compatibility checks)
# without changing what plain `blender` runs.
if [[ "${SET_DEFAULT:-1}" == "1" ]]; then
  ln -sf "${DEST}/${NAME}/blender" /usr/local/bin/blender
fi

# 3. Verify.
B="/usr/local/bin/blender-${BLENDER_VERSION}"
"$B" --version 2>/dev/null | head -1
"$B" -b --factory-startup --python-expr \
  "import bpy; print('bpy OK', bpy.app.version_string)" 2>/dev/null | grep 'bpy OK'
