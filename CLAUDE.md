# Blender Projects: working rules

Damien's Blender work. Each project lives in its own folder with a `PROJECT.md`
(brief, phase plan, decisions log). Read the project's `PROJECT.md` before doing anything.

## Session start (every time; the container is wiped between sessions)
1. `git lfs install --local && git lfs pull`. A fresh clone holds only LFS pointer files (about 130 bytes each) until this runs.
2. `tools/setup_blender.sh` installs the pinned Blender (5.2.3 LTS) and the headless libraries.
3. For compatibility checks: `BLENDER_VERSION=5.2.0 SET_DEFAULT=0 tools/setup_blender.sh` (Damien runs 5.2.0 LTS).
4. Read `.claude/skills/*/SKILL.md` for what has already been learned. Do not relearn it.

## Standards
- Detail over quantity. Do less, do it better. Model the details nobody notices.
- Verify everything: every dimension checked by script against the spec table, every model reviewed in renders from fixed angles, every file reopened in Blender 5.2.0 before delivery. No gaps, no inconsistencies.
- Every number comes from a source (spec sheet, Damien's photos, footage, physics). Record the source in the project's research or decisions log.
- Scripts are the source of truth: models are built by Python scripts in `<project>/scripts/`, so any change is reproducible. Hand-made `.blend` edits must be written back into scripts.
- Real-world units: metres, 1 Blender unit = 1 m, Z up, the bike faces -Y (Blender's front view).
- Graphics and textures never use skull, demon or occult imagery.

## Communication with Damien
- Brief explanations. Never use the em-dash character in anything (chat, docs, commits).
- Ask questions when unsure.
- Show work as: interactive 3D viewer pages (glTF + three.js, published as a private Artifact), close-up renders matching Damien's reference photo angles, and videos for animation.

## Skills
When something is learned (from Damien's feedback, a mistake, or research), write it into the
matching `.claude/skills/<name>/SKILL.md` in the same session, or create a new skill.
Skills are the memory of this repo.

## Git
- Binary assets (`.blend`, images, video, glTF) go through Git LFS (`.gitattributes`). Keep an eye on LFS storage: do not commit bulky intermediates.
- Renders: only curated checkpoints go in `<project>/renders/checkpoints/`.
- Commit at each verified step with a clear message.
