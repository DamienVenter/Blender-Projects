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
0. Setup and research (done), physics demo (current: `scripts/demo/`, see its README)
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
| 9 | 2026-11-06 | Ramp: steel FMX ramp. Landing: dirt. Physics-derived trajectory, cross-checked with footage. Landing height superseded by decision 20 | Damien |
| 10 | 2026-11-06 | Setting: replicate King of the Whip 2025 exactly (scene, surroundings, dirt). Day first, night version later | Damien |
| 11 | 2026-11-06 | Shot: 8 to 12 s (approach, takeoff, air, landing, ride-away). Several versions of the same moment (different cameras) | Damien |
| 12 | 2026-11-06 | Output: 4K UHD landscape (3840x2160), 60 fps. Portrait version later | Damien |
| 13 | 2026-11-06 | Look: photoreal with a cinematic colour grade | Damien |
| 14 | 2026-11-06 | No skull, demon or occult imagery in any graphics | Claude, accepted |
| 15 | 2026-11-06 | Approval cadence: decided case by case. No deadline | Damien |
| 16 | 2026-11-06 | KOTW 2025 = Volkswagen Amarok King of the Whip, Montecasino, Fourways, Johannesburg, 29 Nov 2025: one steel ramp to a sculpted sand landing, 23 m gap. **Confirmed by Damien** | research/kotw-2025.md, Damien |
| 17 | 2026-11-06 | Bike spec: South African (ED-type) 2026 CRF250R: rake 28.4 deg, trail 117 mm, wheelbase 1483 mm, 107 kg wet, Pirelli MX32 tyres. Identical to 2025 | research/crf250r-2026.md |
| 18 | 2026-11-06 | Jump geometry: ramp 2.51 m lip, 9.1 m constant radius (43.6 deg), deck about 1.5 m wide; landing knuckle 4.0 m high, 1.5 m table, 42 deg downslope into a 10.36 m radius. Touchdown at about lip height. Gap per decision 20 | research/fmx-ramp-physics-whip.md, KOTW photo 07 |
| 19 | 2026-11-06 | Physics demo built (scripts/demo): simulated, not hand-animated. Site gravity 9.786 m/s2 and air density 1.00 kg/m3 (Johannesburg) | skills/moto-jump-physics |
| 20 | 2026-11-06 | Follow KOTW measurements: gap 23.0 m lip to knuckle (KOTW "twenty-three-metre competition ramp"); landing crest above the lip as at KOTW. Unpublished KOTW dimensions (lip height, landing shape) to be measured from event photos in the environment phase | Damien |
| 21 | 2026-11-06 | Rider mass: 80 kg body plus about 8.5 kg of gear | Damien |
| 22 | 2026-11-06 | The whip target is Damien's MEASURED whip (camera-matched, clip 1 shot A), not an estimate: 90 deg sideways and flat by 0.33 s, gyro nose-drop to hanging by 1.0 s, held crossed up to about 2.0 s, straightened in the last 0.2 s. The simulation matches what his camera saw and leaves unseen angles to physics | Damien ("nowhere near as big as my whip"), research/whip-attitude-measured.md |
| 23 | 2026-11-09 | Replicate Damien's whip EXACTLY and smoothly: the bike's attitude in the air comes from the two-phone 3D measurement (clips 2 and 3, one jump, two phones), not from a controller; physics drives run-in, ramp, takeoff, flight path, suspension and landing; the rider's unseen body angles are solved for reach and momentum and the momentum mismatch is reported. The previous demo was only 25 to 40 deg sideways against his 80 to 90 | Damien ("still too small ... way more sideways ... replicate it exactly ... super smooth"), research/whip-attitude-measured.md |
| 24 | 2026-11-09 | Smoothness is audited over the whole clip, rotations and positions, with `smoothness.py` (and a test). Simulations are joined by blending the pose drivers (value, rate and acceleration matched), posed on the even frame grid; the whip starts on the lip with the bike turning about its centre of mass while the ramp holds the rear tyre (pivoting about the tyre jumped the bike 33 cm at the lip); the shoulder blade eases the arms straight | Damien ("super choppy"), research/whip-attitude-measured.md |
| 25 | 2026-11-09 | His BODY differs from the replica in the first 0.4 s (laid flat and low from the lip; replica upright): measured from his helmet in both phones and reported, not yet fitted (the measurement's scale and anchor are not consistent enough; fitting it broke reach and momentum). Next step: per-frame scale, a second body point, wheel anchor | research/whip-attitude-measured.md (his body) |

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
