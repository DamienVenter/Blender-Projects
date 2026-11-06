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
