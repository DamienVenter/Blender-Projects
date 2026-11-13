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

## Pose on the bike (2026-11-13)
- Contacts come from the bike model in its ground frame (parts.to_ground): grips 60 mm in from the bar ends
  (0.914, +-0.352, 1.228), peg tops (0.551, +-0.179, 0.446), seat top about 0.98 at its low point (x 0.53). The
  boot sole (25 mm, estimated) lifts the ball of the foot off the peg.
- pose.py writes targets; build_rider.aim_pose turns them into bones: pelvis tipped and moved (hip joints'
  midpoint), the trunk's extra lean shared over spine05..01, the neck and head brought back to look ahead,
  two-bone IK for legs and arms with pole directions, each MakeHuman split bone (upperleg01/02, lowerarm01/02)
  aimed at the same joint, fingers curled. Hands land within 0.3 mm, feet within 9 mm.
- His photo 05 (seated, stopped) has a fitted camera (research/rider-cameras.json, 6 bike landmarks, 5.3 px rms;
  a telephoto from 7.5 m). Through it his body sits right on the bike (thigh, knee, peg foot, reach). The boot on
  the ground there is his RIGHT foot on the far side: a ground point that "lands on the wrong side" may simply be
  the far foot. It is out of reach with the bike upright: the bike leans onto that foot, and the lean cannot be
  fitted from axles, contacts and grips (it trades against camera roll).
- Photo 07 (panning, seated riding) cannot be fitted from the axles, contacts and fender tips: with him on board
  the suspension sags (the rear fender tip sits 13 px above the front tip where the unladen model has it 0.19 m
  higher). A free sag pitch and drop make the fit degenerate (camera underground). Needs more frame landmarks, or
  the bike posed with rider sag. build_bike's cu_p07 camera was placed by eye, never overlaid.
- Read pose renders carefully: a scaled sheet fooled me into "both poses are identical"; projecting the joints onto
  the render (world_to_camera_view) showed the skin follows the skeleton exactly.

## Helmet and goggle (2026-11-13, `helmet.py`, ledger `research/rider-ledger/helmet.md`)
- **More views of the same shell**: us.leatt.com product JSON of older colourways (V25 Royal, Glamis, ...) carries
  near-orthographic Left, Right, Back, Top and Turbine views of the 8.5; MY27 kits show it with the goggle on
  (grey background, no alpha). Same shell: compare outlines first.
- **Scale from a known part**: the goggle strap (45 mm, Leatt spec) measured across its run in a side view with the
  goggle on; carry it to the alpha-matted profile by a similarity fit of the outlines (chamfer, 18 px). Allow for
  perspective (strap 0.13 m nearer the camera than the centre plane: about 9 %). Cross-check: the top view scaled
  by the profile's length put the visor tip 3 mm from the profile's.
- **Shell as a width field over the side profile**: x = +-hw(y, z) over the traced profile domain; rims (centre
  plane) and free edges (face port, lower edge) are parts of the outline; hw = W(z) Q(y) f(d_rim / L) with a
  superellipse falloff, fitted to the back and top silhouettes by least squares with a smoothness penalty
  (alternating multiplicative updates oscillate). The nearest-rim distance has creases on its medial axis: smooth
  the field away from the rims (Gaussian, 10 mm). Rings of vertices at falloff-even offsets from the rims.
- Collinear outline points at a rim/edge corner give Delaunay slivers whose winding flips: drop |area| ~ 0.
- **Fit on the head**: port top edge 40 mm above the eye centres, then pitch and fore-aft for an even stand-off
  (51 mm all round on his head); the shell came out pitched 18 deg nose down from Leatt's profile photo.
- **Graphics by projection**: fit a pinhole camera to each product photo against the model's outline (Powell then
  Nelder-Mead, about 2 min a view), rasterise an atlas (islands by face normal), sample each texel from the views
  that see it (cos^4, depth buffer from the texels themselves), mirror point as fallback. Mask anything in front
  of the helmet (the goggle in iso-right). Studio reflections come along: a cleanup pass is still to do.
- **The big side LEATT in Leatt's iso-right and his photos is the goggle strap's print**, not the helmet's.
- Text on a strap reads correctly on both sides from outside if it runs in one direction from the left outrigger
  round the back. An outrigger face seen from the other side mirrors its UVs: give each side its own image half.
- A head pitch put on the head bone alone drives the chin bar into the throat; share it over neck01-03 and head.
- Test closure and orientation of the solid (every directed edge once each way) before trusting winding numbers.

## Boots: Leatt Moto 6.5 White (2026-11-13, `boots.py`, ledger research/rider-ledger/boots.md)
- Which boot a Leatt view shows: work it out from the camera, not the caption. 02 (outer side, buckles, toe
  right) and 03 (inner side, toe left) are both the RIGHT boot; in 06 (soles, toes up) the right boot is the
  image's left one; in 05 (back) the right boot is the right one. Camera on the boot's outer side, toe to the right
  = right boot.
- Never read positions off a displayed image: my first readings of 02 were off by 500 px (the view is scaled).
  Grid crops with pixel labels (`grid.py`-style) or masks by script only.
- Leatt's studio white is retouched: parts of the white boot are exactly the background grey (236, 236, 236), so
  colour or gradient masks bite into the outline (02's heel cup lost 45 mm). Fill such bites from the other side's
  photo in a known band, and check every mask drawn on the photo.
- 02 and 03 are not mirror images of one ortho view: 03's shaft leans 2.5 deg further forward. Use one photo as
  the outline and shear the other when projecting from it.
- Size from his foot: MakeHuman's foot 277 mm > US 9's 27.5 cm, so US 10; sole length = chart foot + 19 mm toe room
  (Gaerne's rule) + walls = 330 mm; that length scales the side photo (0.286 mm/px). Leatt publishes no shaft
  height or sole length.
- His leg against Leatt's empty boot: the calf is 127 mm wide where the closed, empty shaft is 106 mm, and his
  shank leans 6 deg inward in the rest pose (A stance): centre the shaft's sections on his leg and open them for
  the calf (the worn shaft's panels open); his ball needed a 2.3 deg yaw (Leatt's last curves outward) and the
  boot a 2 deg toe-down pitch (heel drop) for his toes to fit the low toe box.
- Shell shape that worked (after CSG unions of sections wobbled): an "inflated side outline". Every point inside
  the side outline carries the shell's half-width there, rounded toward the outline (superellipse over the row's
  depth in the shaft, over 22 mm on the foot). The outline is the photo's back, front and instep lines each a
  robust B-spline that ignores points standing out (buckles, keepers, plates, the spine are parts), not the raw
  mask (the raw outline gave drapes and ripples). Meshed with surface nets (numpy, 2.5 mm, faces flipped outward:
  check orientation numerically, Cycles hides it).
- Graphics by projecting each photo onto the faces that look at it, as PAINT (black where dark, red where red,
  white elsewhere) plus a high-pass normal map, never the photo itself (its shading would be baked). The mirrored
  left boot uses the same UVs with every logo box flipped in place; find the boxes as dark-pixel bounding boxes,
  my hand boxes missed two logos.
- The sole's lugs from photo 06: the moulding's fine texture (local high-pass energy) marks lugs, peg zone and
  logos; the smooth grey between them is the recessed base. Each sole's bottom texture is Leatt's own sole of that
  side (the left's LEATT reads right).
- Clearance in a pose without Blender: skin and boot both linear-blend skinned on a sagittal knee and ankle
  rotation; take each posed skin point back through the boot's blend exactly (per point, the blend is affine:
  invert it, re-evaluate the weights, repeat) and look it up in the shell's field. A plain fixed-point iteration
  diverged at 60 deg of knee.
- Check renders: from +x the camera sees the LEFT boot first; hide the other boot (and the body for soles).

## Gloves (2026-11-13, `gloves.py`, Leatt 2.5 X-Flow Black, ledger research/rider-ledger/gloves.md)
- Leatt's glove size chart is not on the product JSON: the page HTML links
  `us.leatt.com/cdn/shop/files/GloveMen_SizingChart_04-02-2026.jpg` (circumference at the knuckles, hand length).
  MakeHuman's hand at 1.85 m: knuckle circumference 21.9 cm, hand length 21.4 cm (long: 11.6 % of stature).
- Build gear on skin from the skin itself: the glove is the body's hand patch (distal of a clean edge ring) plus
  rings cast from the bone axis, one Catmull-Clark step (the body renders with subsurf 1, so this IS the rendered
  skin), then offset. Keep every gear vertex as a sparse combination of body vertices: its skin weights are then
  the same combination, exact. The body mesh is exactly mirror-symmetric but its weights are not (0.17 apart on the
  hands): build the right side from the left's topology but with the right hand's own weights.
- MakeHuman's nail folds and joint creases show through a 1 mm offset. Bridge them: Laplacian smoothing with the
  height over the skin clamped to [offset, offset + 1.5 mm] (unclamped, the palm lifted 5.5 mm over its hollow).
- UVs like the real pattern pieces (hand back, palm, edges planar along their normals; each phalanx a cylinder
  about its bone, seam mid-palm; tip caps; cuff a cylinder): about isometric, so patterns drawn in mm stay true.
  A cylinder over a bent finger overlaps itself at the joints: one island per phalanx. Paint every texel from its
  3D point (rasterise the UV triangles with PIL, barycentrics, interpolate positions, normals and weights): chart
  seams then never show, and panel boundaries are smooth curves (weight-blended per-bone palmar directions), not
  face edges.
- build_rider's gear material has one roughness and colour-image + normal-map inputs only: put construction in the
  normal map; a smooth overlay among bumpy mesh reads glossier by itself. Black fabric turned mid grey with sheen
  0.3 under a white world: sheen 0.1, roughness 0.7.
- Leatt's views: work out which glove each photo shows (thumb side + palm facing): MY26 back/palm and MY27 back are
  the RIGHT glove, MY27 "other angle" the LEFT. The two gloves carry the same graphic in the hand's own frame (mirror
  images: hatches lean the other way), but every word and logo reads right on both: mirror letters only, inside
  their own box. The photo maps onto his hand's back at 0.178 mm/px (two independent scales agreed).
- Printing a photo's graphic by thresholding it directly gives blotches (mesh texture, lighting): redraw shapes
  measured on the photo rectified to the hand, and take only clean letter shapes from it (the large holes enclosed
  by the white core; place them rigidly, not row by row, or the slanting edge shears them).
- Check renders: `gloves.py check` on build_rider's saved rider.blend (no studio views needed): cameras from the
  posed hand's own joints, a camera-only white background (Light Path) for Leatt's product angles with the body
  hidden, clearances from evaluated meshes with the hide_body Mask switched off (or the hidden skin is missing).
- Seated pose (pose.py + aim_pose, 2026-11-13): the grip's axis crosses the hand only 6 mm palmar of the bones,
  so the grip passes through the palm (skin 14 mm inside it). A power grip needs the axis about 36 mm palmar (palm
  skin 20 + glove 1 + grip radius 14.8), across the distal palm at about 25 deg to the knuckle line (right now).


## Jersey and pant: Leatt 5.5 Tiger Pink (kit.py, 2026-11-13)
- Cloth = his own body faces, cut along smooth cut surfaces (boundary vertices slid along their edges onto the
  cut), subdivided, then draped: curvature flow (the normal part of the umbrella Laplacian) plus a collision step
  along the skin's normals with a clearance per vertex. Curvature flow alone is body paint (pecs, belly, ballooned
  knees). Loose cloth needs ENVELOPES: per-slice convex hull round an axis (trunk: vertical; each leg: hip to
  ankle), hung with a fall rate (jersey 0.35 m/m off the chest, pant leg 0.08: straight legs). Keep the trunk's
  envelope out of the crotch: a radial push from a vertical axis tore a hole there.
- Ease from the chart: a convex girth grows 2 pi per metre of offset, so clearance = (garment - his girth) / 2 pi.
  Taking ease from the sides shrinks the girth unless the rest is scaled up (a girth test caught it).
- Draping drifts the openings: project the edge back onto its cut surface (Newton on the cut function) and hold it
  for the last relax. Turned facings: place the inner row 1.5 t under the LOCAL surface (k-nearest average); the
  nearest single vertex poked out and crumpled the neckline.
- Two layers (jersey tucked under the waistband): order the clearances (jersey 2.5 mm, band 11 mm) and clamp the
  tucked part from both sides, else curvature flow bridges the spine groove outside the pant; give the tucked part
  the pant's weights. Face-material regions (I.K.S panels) stair-step: snap the seam's neighbours onto the field's
  zero first. Weight smoothing 6 passes on the jersey, 2 on the pant (it follows the kneecap).
- Sizes: measure him where the garment is worn. The pant band's height came from Leatt's on-model rise (22 cm);
  my first band (18 cm rise) put his band girth at 90 cm (XL); at the right height it is 84 cm (L / US34).
- Print: one UV chart per pattern piece (LSCM; numpy 2 refuses 2D cross products, use the determinant), texels
  painted from their rasterised 3D rest position, so the layout never decides where a graphic lands. Leatt's
  frontal on-model photos (long lens) project well onto front and back panels; flat product shots are 3/4 on forms.
  Mask the studio background (border-connected near-white, or the PNG alpha) and fill from the nearest garment
  pixel, and map across arms and legs by the photo's silhouette (normalised), never in metres: the soft edge
  otherwise smears white along the sleeves. In the pant photos the gloves are runs of the silhouette rows: take
  the leg runs nearest the middle; find the crotch row from the alpha. Logos the photos see edge-on (the outer
  thigh LEATT) are printed flat from a side canvas.
- Tests in a pose without Blender: numpy linear blend skinning (bone turns about their heads, children follow).
  "No skin through the cloth away from the openings" must skip 4 rings from the open edge (facing, fold, edge).
- The Bash tool's worktree guard refuses any command containing the letters g-i-t (even in "digits"): put Python
  patches in a file.

## Jersey: his number, name and sponsors (round 2, 2026-11-13, kit.py "Damien's additions")
- **Read his photos upright**: rotate each crop so his body stands vertical (PIL rotate about a centre, enlarged
  7x, unsharp mask) and read positions on a labelled grid, converting back to photo pixels by script. Rotated, 09
  and 08 showed the front sponsors under the yoke either side of the centre chevron; round 1 had read 09 sideways
  as "a column on the side panel".
- **The photos' names are the bike's side**, not his: he is twisted in a whip. Each of 09 and 08 sees one side of
  his chest nearer (patch widths disagree by up to 30 %): combine both (geometric mean), never trust one.
- **Ruler on the cloth**: Leatt's chest LEATT is already on the model at known places. Fit it to his photo by
  normalised cross-correlation of Leatt's logo mask with his light letters: affine coarse to fine (blur 2.5, 1.5,
  0.8 px), then a little perspective with a penalty (a free homography collapses to a sliver: NCC is blind to
  scale). Check the outline overlay. The fitted plane extrapolates badly above and below the logo (the chest turns
  35 deg toward the collar; photos from below): use it near the logo, and local ratios (patch to letter height,
  to logo length) plus the official artwork's aspect for sizes.
- **Official logos, where they are**: BikeWise and USN: the og:image of their own Shopify sites; Motul: the inline
  SVG in motul.com's header (white `fill` on a `#ed1c24` box in its CSS); Pirelli: pirelli.com's og image;
  Cycleworx Suspension (Randburg) has no site: `graph.facebook.com/<page>/picture?width=1000` returns its profile
  logo while the page itself answers 400 (cycleworx.co.za is a different firm, a bicycle shop). Files and URLs in
  `reference/sponsors/README.md`. A small SVG path filler (M L H V C S Q Z, even-odd) rasterises vector logos.
- **His 114 is his own art**: lift the white glyph components from his plate art (largest three in the number's
  field; drop the bolt hole and logos), keep its keylines; outline by a distance transform.
- **Print like sublimation**: the back in unrolled coordinates (arc length across each horizontal section from the
  spine, up each vertical from z 1.45), so the number wraps the curved back and crosses the raglan seams in one
  piece; small front patches on their tangent plane. Building the unroll: keep only the outer back (cloth round
  the front of the neck also faces back at the same (x, z); y above the side seam), one point per 3 mm cell (seams
  carry duplicate vertices: Delaunay slivers made a 20 cm jump), median-filter, and integrate up from shoulder-blade
  height (from the hem the armpits' steep cloth sheared the letters at the sides).
- **Sharper print without new UVs**: an overlay part = the jersey faces under the graphics, 0.1 mm out, with the
  jersey vertices' own weights; UVs = the jersey's UVs scaled and moved per island, never rotated (tangent frames
  agree, so the jersey's normal map can be copied); the background sampled from the jersey's own print at the same
  cloth point. Check it by rendering with and without the overlay and differencing: 0.3 mm lift drew 2 px contact-
  shadow lines along the island edges. build_rider's gear materials take no alpha, so a cut-out decal is not an
  option.
- **A word cut by a fold is not the whole word**: in 06 the name ran into a fold of the jersey at the collar,
  so round 2 took DAMI for DAMIEN and set the whole name over the number's left half. Damien: it is centred.
  Read which letters are visible, then scale by the font's own ink widths (DAMIEN / DAMI). Off-centre graphics on
  a twisted rider are usually the twist: ask before printing something asymmetric.
- His name replaced Leatt's back LEATT (06 shows none beside it): erase it from Leatt's photo before projecting
  (normalised Gaussian fill).
