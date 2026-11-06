---
name: video-reference-analysis
description: How to study reference video frame by frame (riding clips, event footage) and turn it into timing and pose data. Use whenever Damien sends a clip or footage needs analysing.
---

# Video reference analysis

## Getting footage
- YouTube blocks downloads from the cloud server ("Sign in to confirm you're not a bot", HTTP 429). Do not try to work around it with Damien's account cookies. Ask Damien to download clips and upload the MP4s, or send screenshots.
- Uploads arrive under `/root/.claude/uploads/<session>/`. Copy them into `<project>/reference/<source>/` with descriptive names (camera position, date) and commit them (LFS).
- WhatsApp re-encodes video: 478x850 portrait, 30 fps, heavy compression, sometimes slightly variable frame rate. For precise work, ask for the original files (share as a document in WhatsApp, or via cloud drive) and for slow-motion or high-frame-rate captures.

## Procedure
1. `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,avg_frame_rate,nb_frames -of default=nw=1 clip.mp4`. If `avg_frame_rate` is not a clean number the clip is variable frame rate: trust timestamps, not frame counts.
2. Overview sheets: `tools/contact_sheet.sh clip.mp4 out/clip_overview 0 <last> 3 8 3`.
3. Detail sheets of the key moment: smaller step plus a crop, e.g. `tools/contact_sheet.sh clip.mp4 out/clip_peak 26 61 2 6 3 478:560:0:80 239`.
4. View sheets with the Read tool. Tiles are labelled with the true 1-based frame number and the timestamp.
5. Write findings as a timeline table (phase, time after a clear event such as lip departure, what happens, best frames) in `<project>/research/`.

## Gotchas
- In an ffmpeg filter chain, `n` after a `select` filter counts the selected frames, not the source frames. The contact-sheet tool converts it back (`START + n*STEP + 1`). Do not hand-label tiles with `%{n}`.
- PNG sheets of compressed phone video are about 5x larger than JPEG at `-q:v 2` with no visible gain. Use JPEG.
- Clips are often edits of several shots. Look for hard cuts before measuring timing across a clip.
- Camera position changes apparent angles a lot (a low camera behind the ramp looks steeply up). Do not read 3D angles off a single view; cross-check views, and for precision, camera-match a 3D model to the frames.

## Measuring 3D attitude from a single camera (learned 2026-11-06, whip measurement)
- Eyeballing angles from close, steep camera angles badly UNDER-estimated Damien's whip (55 deg estimated,
  90 deg real). Always measure from the most distant, straightest camera available (least perspective).
- Method: analysis by synthesis. `motocross-whip/scripts/analysis/attitude_overlay.py` draws the bike and a stick
  rider at a trial attitude from a camera placed like the phone, next to the real frame; adjust until they match.
  Estimate the camera from the scene: distance from a known size (ramp width, wheel diameter 0.69 m), focal length
  from the bike's pixel size (phones zoom; clip 1 was about 1600 px on a 478 px frame), height from the horizon.
- What each cue fixes: axle-line angle in the picture = rotation about the line of sight; wheel ellipse roundness
  = how side-on (round) or flat (a line) the bike is; which side the rider/seat is on = sign; torso tilt = lean.
- The rotation that tips the bike toward or away from the camera is nearly invisible from one view. Write it
  down as unknown and let physics decide it; do not invent it.
- Use a parameterisation that stays well defined where the motion goes: a sideways bike hanging nose-down is
  gimbal lock for yaw-pitch-roll. `R = Rx(drop) Rz(yaw) Ry(-pitch) Rx(roll)` (drop about the travel direction)
  keeps it clean. Interpolate measured keys with pchip (no overshoot) and check against frames in between.
- An edited clip can mix attempts: clip 1 shot B (front) may be a different jump than shot A. Use cross-shot
  timing only for durations.
- Locate the rider automatically in sky frames (`scripts/analysis/find.py`: dark or red blob) before cropping;
  grid crops at fixed offsets miss a moving rider.
