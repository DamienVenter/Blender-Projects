# Gear materials round 1, phase B (decision 61), 2026-11-16

Numbers and method: `research/scene-look.md` ("The gear, materials round 1, phase B (decision 61)") and the ledgers
(`research/rider-ledger/kit.md` phase B, `gloves.md` correction).

His photos: his photo | A | B at the photo's pixels (scaled up by 2), both renders through `scene_look.display` at
the photo's PHOTO_EV with the lift and, for 07, its tint. The rider's pose is the blend's seated pose, not his:
compare colours, not shapes.

| file | A / B | what to look at |
|---|---|---|
| `07_p07_tint.jpg` | head_closeups' look without / with 07's tint (main's rider, main's rig) | the helmet's black print 47, 46, 44 -> 46, 48, 57 (his 35, 37, 56; dE 15.3 -> 8.7); the white shell unchanged (3.0) |
| `08_rig_p07_p08_p09.jpg` | main's rig / this round's (main's rider) | the white shell's shade, bluer as his: dE 6.4 -> 2.3, 8.2 -> 5.7, 11.1 -> 6.2; lit sides 2.0 -> 2.4, 1.4 -> 0.8, 3.8 -> 4.2; black print 8.7 -> 7.0, 5.2 -> 2.9; 09's gloves (held out) 10.7 -> 9.9 |
| `09_rig_cam07.jpg` | main's rig / this round's (main's rider) | the darks hold: jersey 2.7 -> 3.0, pant 2.0 -> 2.2, gloves 2.3 -> 2.2, tyre 6.1 -> 6.3 |
| `10_inks_p07_p08_p09.jpg` | main's kit / phase B's (this round's rig) | the jersey's pink redder and deeper: 09 15.4 -> 8.9, 08 36.5 -> 33.9, 07 31.7 -> 27.9; the jersey's black 7.3 -> 7.1, 6.0 -> 4.6, 5.2 -> 4.6 |
| `11_inks_cam07.jpg` | main's kit / phase B's | the pant's pink 14.9 -> 6.6; the darks 3.0 -> 4.6 (jersey) and 2.2 -> 3.3 (pant), a little darker than his; the lime 15.3 -> 18.4 (its blue was the grey layer's sky) |

Maker's photos: Leatt | main | phase B, our studio renders (build_rider's studio, rest pose, Standard), one exposure
for both (main's jersey white at the flat's white luminance). The flat is a flat lay, ours is on the body: compare
the inks, not the shapes.

| file | what to look at |
|---|---|
| `12_leatt_front.jpg` | Leatt US's front flat: the magenta's green veil gone (ratio to the white 0.868, 0.048, 0.296 -> 0.891, 0.018, 0.244; flat 0.933, 0.004, 0.274; dE 10.7 -> 6.3); the black 0.041 -> 0.035 of the white (flat 0.009) |
| `13_leatt_back.jpg` | Leatt NZ's back on-model: the back's magenta and its fade into the black (dE 8.5 -> 5.2) |
| `14_leatt_pant_front.jpg` | Leatt US's pant front on-model: the pant's lime (dE 8.7 -> 4.8) and black (0.046 -> 0.041) |

Blender 5.2.0: p09 rendered from phase B's saved 5.2.3 blend is identical to 5.2.3's render (every pixel through the
look). head_closeups' own p07 render (Blender's compositor) reads the black print 44, 47, 60: the tint is applied.
