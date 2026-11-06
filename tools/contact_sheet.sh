#!/usr/bin/env bash
# Build labelled contact sheets from a video, for frame-by-frame reference study.
#
# Every tile is labelled with the TRUE 1-based frame number (matching
# `ffmpeg -i video f%03d.png` file names) and the presentation timestamp.
#
# Usage:
#   tools/contact_sheet.sh VIDEO OUT_PREFIX [START] [END] [STEP] [COLS] [ROWS] [CROP] [TILE_W]
#     VIDEO       input video
#     OUT_PREFIX  output path prefix; sheets are written as OUT_PREFIX_01.jpg, _02.jpg ...
#     START, END  0-based frame range, inclusive (default: whole video)
#     STEP        take every STEP-th frame (default 3)
#     COLS, ROWS  tiles per sheet (default 8x3)
#     CROP        ffmpeg crop expression w:h:x:y applied before scaling (default none)
#     TILE_W      tile width in px (default 240)
#
# Example:
#   tools/contact_sheet.sh clip.mp4 sheets/clip_peak 26 61 2 6 3 478:560:0:80 239
set -euo pipefail

if [[ $# -lt 2 ]]; then
  sed -n '2,20p' "$0"; exit 1
fi

VIDEO=$1; OUT=$2
NFRAMES=$(ffprobe -v error -count_frames -select_streams v:0 \
  -show_entries stream=nb_read_frames -of csv=p=0 "$VIDEO")
START=${3:-0}; END=${4:-$((NFRAMES - 1))}; STEP=${5:-3}
COLS=${6:-8}; ROWS=${7:-3}; CROP=${8:-}; TILE_W=${9:-240}

CROPF=""
[[ -n "$CROP" ]] && CROPF="crop=${CROP},"

LABEL="f%{eif\:${START}+n*${STEP}+1\:d}  %{pts\:hms}"
mkdir -p "$(dirname "$OUT")"
ffmpeg -v error -y -i "$VIDEO" -vf \
  "select='between(n\,${START}\,${END})*not(mod(n-${START}\,${STEP}))',${CROPF}scale=${TILE_W}:-2,drawtext=text='${LABEL}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.65,tile=${COLS}x${ROWS}" \
  -fps_mode passthrough -q:v 2 "${OUT}_%02d.jpg"

echo "video frames: $NFRAMES  range: $START-$END step $STEP"
ls -1 "${OUT}"_*.jpg
