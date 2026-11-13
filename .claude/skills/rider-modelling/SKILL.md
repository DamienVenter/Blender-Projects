---
name: rider-modelling
description: How Damien the rider is built (body from MakeHuman's CC0 data shaped to his measurements, skeleton, pose, Leatt gear) and checked. Use before changing motocross-whip/scripts/rider or modelling any person or riding gear.
---

# Rider modelling (motocross-whip/scripts/rider)

## Body (2026-11-13)
- Source: MakeHuman's base mesh, shape targets and default skeleton with skin weights, CC0 since 2020
  (static.makehumancommunity.org FAQ "What changed regarding the license in 2020"). They ship inside MPFB 2.0.18
  (extensions.blender.org); `tools/fetch_makehuman.sh` downloads it pinned by sha256 and keeps only data/ in
  ~/.cache/makehuman. MPFB's own code is GPL and is not used: `mhdata.py` reads the files.
- Hosts from the build server: github.com is refused by the proxy (403); files.makehumancommunity.org,
  static.makehumancommunity.org and extensions.blender.org work. The "system assets" zip (280 MB) has skins and
  clothes but NOT the base mesh and targets: those are in MPFB's data/.
- Formats: base.obj in decimetres, y up, facing +z, left at +x; one vertex list for the body and the helpers
  (groups 'body', 'helper-*', 'joint-*'), and targets index that list. Targets are gzip text "index dx dy dz"; the
  average shapes are empty files. Rig JSON numbers are in "MB" = metres, z up, facing -y: MB = 0.1 (x, -z, y).
  Joint strategies: CUBE (centre of the joint-<name> helper cube), VERTEX, MEAN. Our default shape reproduces the
  rig file's joints within 1.9 mm (test).
- Macro rule (macro.json): each slider splits into its two neighbouring named levels with linear weights; the shape
  = base + race x gender x age targets + universal-gender-age-muscle-weight + height/... + proportions/...
  (+ breast/... for female shapes).
- His numbers: 1.85 m, 80 kg body (gear separate, 8.5 kg), lean athletic, age not given (25). The skin is closed
  (no boundary edges), so mass = (volume - 3.1 L gas) x 1.065 kg/L, exact. The weight slider is solved for it,
  the height slider for the stature. MakeHuman's "average" man at 1.85 m weighs 68 kg (BMI 20) and more muscle
  makes it tighter, not bigger: his BMI 23.4 needs weight about 0.67 with muscle 0.75.
- Proportions vs Drillis and Contini: legs within 1 to 3 %; acromion to fingertip 0.80 m vs 0.81; MakeHuman puts
  the elbow joint high (upper arm 27.5 cm, forearm 28.3 cm): reach is right, the split is not. Hip joint centres
  22.7 cm apart (wide). Watch both when posing.
- Blender: build_rider.py makes the mesh (UVs per face corner, smooth, subsurf 1), the armature (heads, tails,
  rolls, parents, connect flags from the rig file) and vertex groups, under an empty "rider" turned +90 deg about
  z so he faces +x like the bike.
