# Motocross Whip: Blender Animation

## Brief
Damien, on his own 2026 Honda CRF250R, whips a 75 ft gap from a standard steel FMX ramp
to a dirt landing, in the setting of King of the Whip 2025. Photoreal, 4K, 60 fps.

Philosophy: detail first. Do fewer things, do them better. Model the details nobody notices:
fabric weave, sticker edges, weld beads, tyre mould lines, dust on the plastics, light through the goggle lens.

## REQUIRED FINAL PHASE: SOUND
No sound for now. **Sound gets added at the end. Do not forget.**
Engine: Honda CRF250R four-stroke (2026), so the engine sound is a 250 cc single-cylinder four-stroke.

## Phase order
0. Setup and research (current)
1. Bike: 2026 CRF250R, dimensionally exact, recreating Damien's own bike from his photos
2. Rider: Damien, 185 cm, built from his photos; rig
3. Kit and bike graphics: Leatt gear only; custom sticker kit from Damien's references; fabrics, materials, shading
4. Environment: King of the Whip 2025 setting, steel FMX ramp, dirt landing, 75 ft gap
5. Animation: approach, takeoff, whip in Damien's style, landing, suspension, secondary motion
6. Lighting, cameras, render (day version first, night version later)
7. **Sound** (final phase)

## Decisions log
| # | Date | Decision | Source |
|---|---|---|---|
| 1 | 2026-11-06 | Everything lives in the `blender-projects` repo; lessons are written as skills in `.claude/skills/` | Damien |
| 2 | 2026-11-06 | Damien uses Blender 5.2.0 LTS. Build server uses 5.2.3 LTS; files are checked in 5.2.0 before delivery | Damien |
| 3 | 2026-11-06 | Review: interactive 3D viewer links in chat for bike, rider, ramp; videos for animation; close-up renders matching every reference photo Damien sends | Damien |
| 4 | 2026-11-06 | Bike: 2026 Honda CRF250R (four-stroke), stock, recreating Damien's real bike | Damien |
| 5 | 2026-11-06 | Real logos and branding (private project for now) | Damien |
| 6 | 2026-11-06 | Sticker kit: designed by us from Damien's reference images (to come) | Damien |
| 7 | 2026-11-06 | Rider: Damien, about 185 cm. Gear: Leatt only (sponsor). No goggle tear-offs. No neck brace | Damien |
| 8 | 2026-11-06 | Whip: rear wheel to Damien's right; style and timing from his clips (see `research/whip-analysis-user-clips.md`). Clips' bike look and kit are not used | Damien |
| 9 | 2026-11-06 | Ramp: steel FMX ramp. Landing: dirt, slightly below lip height. Physics-derived trajectory, cross-checked with footage | Damien |
| 10 | 2026-11-06 | Setting: replicate King of the Whip 2025 exactly (scene, surroundings, dirt). Day first, night version later | Damien |
| 11 | 2026-11-06 | Shot: 8 to 12 s (approach, takeoff, air, landing, ride-away). Several versions of the same moment (different cameras) | Damien |
| 12 | 2026-11-06 | Output: 4K UHD landscape (3840x2160), 60 fps. Portrait version later | Damien |
| 13 | 2026-11-06 | Look: photoreal with a cinematic colour grade | Damien |
| 14 | 2026-11-06 | No skull, demon or occult imagery in any graphics | Claude, accepted |
| 15 | 2026-11-06 | Approval cadence: decided case by case. No deadline | Damien |

## Research
- `research/whip-analysis-user-clips.md`: Damien's whip, phase by phase timing.
- `research/kotw-2025.md`: King of the Whip 2025 setting.
- `research/crf250r-2026.md`: bike specifications and reference sources.
- `research/fmx-ramp-physics-whip.md`: ramp and landing dimensions, trajectory physics, whip technique.
- `research/blender-pipeline.md`: Blender 5.x API changes, tools, materials, render settings, web viewer.

## Toolchain (verified 2026-11-06)
- Blender 5.2.3 LTS headless (`tools/setup_blender.sh`), plus 5.2.0 side by side for compatibility checks.
- Cycles CPU (4 cores, no GPU): default cube at 1080p, 64 samples, 11.6 s. EEVEE is slower here (software OpenGL).
- YouTube downloads are blocked from the server. Footage must be uploaded.
