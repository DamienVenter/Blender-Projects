# Jersey and pant rounds 3, 3b and 3c (2026-11-15, decision 52)

A crisp print, true colours, his number and sponsors checked at 1:1; round 3b, the six fixes of the coordinator's
1:1 review; round 3c, the review of 3b (one regression, three faults). **Round 3c's column replaces round 3b's**
(round 3b's sheets: git history, commit 56b403a). The windows of his photos (01 to 04, 09, 10) are rendered through
cameras fitted to each photo by the print (0.9 px in 06, 2.4 in 09, 2.3 in 08), enlarged 4x (06) or 8x (09, 08) and
turned upright, now in decision 54's scene look, its "daylight" kind (sun and sky, the compositor's gains and tone
curve; until round 3b AgX - Punchy -0.6): his photo | main | round 3c, both rendered again that way (round 3, rendered
in the old look, is left out of these). Leatt's studio views (05 to 07, 11) are in the Standard view:
main | round 3 | round 3c. The inks are unchanged by the look. Numbers: research/rider-ledger/kit.md, sections "Round 3", "Round 3b"
and "Round 3c".

| File | What to look at |
|---|---|
| 01 | Back vs 06 at 4x: the 114 and DAMIEN, the yoke's magenta to the raglan seams (fix 1), the lower back's light dots (fix 3: 4 rows of 15, matched to the light 06 shows). |
| 02, 03 | Front vs 09 and 08 at 8x: the chest LEATT, the sponsors, the stripes' edges, the yoke over his right shoulder (one magenta across the raglan seam). |
| 04 | Riding vs 07: his left sleeve and thigh (the zebra round the outer thigh). |
| 05 | Leatt's front: the flat (the colour reference), the NZ on-model photo (the shapes), main, round 3 and 3c at Standard -1.6 (no clipping): the yoke (fix 1), the sleeve fronts' bands, FIVE.FIVE, the chevrons' faded tops; at the bottom, his right hip beside the buckle (fix 2; 12 shows it at 3x). |
| 06 | Leatt's back: the NZ on-model and back 3/4 photos, main, round 3 and 3c at Standard -1.0: the yoke across the top (fix 1), the sleeves' backs and side panels, the lower back's holes (fix 3). |
| 07 | The pant front and back (Leatt US on-model): the waistband (fix 2), the shins (clean strokes; Leatt's diagonal is open, fix 4); the thigh LEATT and his left side (the outer thigh's zebra). |
| 08 | The colour check: each ink's measured core, sRGB and its ratio to the white beside it (linear). Standard -1.6: round 3c's inks are round 3's (magenta 209 53 127). The daylight half now in the daylight kind (the front view under its default sun): the inks come out lighter than in his photos (teal 161 253 236 against his 09's 102 171 162; the magenta's green 0.07 of the white against 0.01), the jersey's material, a later round. |
| 09 | The 114 at 1:1 (the photo's own pixels, shown 3x) and at 4x. |
| 10 | Each front logo at 8x through the cameras fitted to 09 and 08. |
| 11 | Each sleeve all round (front, back, outer, inner) in round 3c at 1:1 (900 px renders, not scaled), round 3 at half size, Leatt's four views of the sleeves, and under his left arm (the side panel). |
| 12 | Round 3c's places, main, round 3b and round 3c: the yoke front and back (fix 1), his right hip at 3x (fix 2), the lower back at 3x and in his 06's window (fix 3). |

Round 3 against main: the print is cut (stripes and white edges crisp at 1:1), the inks are the flat's (the back's
magenta now as deep as the front's: 28 to 11 of 255 apart in the texture), each sleeve is one print and meets the
trunk without a step (top line 51 to 5, raglan 37 to 2), and the sleeves and back no longer carry the photos' fold
shading.

Still not right in round 3 (all but the lower patches and the daylight look are round 3b's fixes): the faded tops of
the top chevrons under FIVE.FIVE are ragged (the trace cuts the fade); at grazing angles the sleeves keep the
photos' shapes, smoothed (soft grey bands on the black); the pant's outer sides are plain black; FIVE.FIVE reads as
dots at 0.8 mm per texel; the lower patches (USN, Motul, Cycleworx) sit 20 to 40 mm off each photo, in opposite
directions in the two. The daylight look desaturates the magenta (not the kit's). Asked: what shows through the
lower back's holes (06 shows about 5 rows of light dots); not answered yet, so round 3b estimates it.

Round 3b against round 3 (each with a test that fails on round 3 and main): the sleeve fronts carry the flat's bands
again (IoU against the flat 0.27 to 0.85 and over); the sleeves' backs are their fronts mirrored, the raglan part
plain, the forearm LEATTs and the elbow icon from Leatt's files (IoU 0.99), no white fragments (unstamped pieces
under 200 mm2: 25 in round 3, none); the side panels traced on the back 3/4 flat and the back beside them plain
(stripe share 0.222 to 0.001); the pant's outer thighs carry the zebra (0.09 to 0.43 and 0.53) and its shins smooth
sweeps (roughness 0.126 to 0.099 and 0.053); the lower back shows 5 rows of light dots (estimate); the chevrons'
tops are a clean gradient (0.28 to 0.53 at mid brightness); FIVE.FIVE is set on the print overlay at 0.164 mm a
texel and reads as letters.

Round 3c against round 3b (each with a test that fails on round 3b and main): the yoke's magenta reaches the raglan
seams again, front and back (seen square on, its share of the width 0.45 to 0.56 to 0.92 to 1.00 at the chest, 0.53
to 0.64 to 0.99 to 1.00 across the upper back; Leatt's flat 0.99): round 3b had traced the sleeves' raglan part as
unseen, its ground from the black sleeve; the pant's waistband beside the Waistlock is traced (the Waistlock and the
jersey over it outlined in Leatt's photo and plain black, no nearest-pixel fill): no teal blocks (8 mm raggedness
0.126 to 0.068, outline along the texture's axes 0.15 to 0.06), and the jersey's lower side above it loses the NZ
photo's fold steps (0.052 to 0.032); the lower back's holes are his 06's: a rectangular grid of 4 rows (the review's
"about 5" counts 4 in 06 and on Leatt's back flat) of 15, 13.7 by 19.4 mm, each showing 9.2 mm2 of white (06 about
10, round 3b 1.7); in the daylight render of the 06 window the dots' light measures 1.08 px2 of the white against
the photo's 1.09. Open: the shins' strokes on Leatt US's back diagonal with airbrushed upper ends (fix 4).

Still estimated (round 3c): his left sleeve (the flat's right mirrored) and both sleeves' backs (their fronts
mirrored); the yoke's fade over the shoulder's top (the flat's); the left forearm LEATT's place; the pant's outer
sides past 60 deg; the waistband under the Waistlock and the jersey's overhang (plain black); the holes' size and
tone (matched to the light 06 shows); FIVE.FIVE's typeface (Inter SemiBold). The line's jog at his left elbow is not
drawn. The jersey's material in daylight (gloss, sheen) is a later round.
