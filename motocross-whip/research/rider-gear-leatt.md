# Rider gear: Leatt (identification for modelling)

Researched 2026-11-12 for Damien's riding gear, from Leatt's own product data first (us.leatt.com product JSON,
feature lists, size charts, studio and model photos), then the Leatt NZ distributor's copy of Leatt's photo sets and
retailer listings. Damien's words: "Leatt 5.5 MX Kit Combo 2026 Tiger Pink ... make sure it's the 5.5 and not the
4.5. Same with the helmet and goggles and gloves and boots. I got the white Leatt 6.5 boots."

Images: `reference/leatt-gear/` (README lists every file with its source URL). Side-by-side proof:
`reference/leatt-gear/comparison/damien-vs-leatt_<item>.jpg`.

## Summary

| # | Item | Identified product | Colourway (Leatt name) | Year | Leatt SKU series (size order) | Confidence |
|---|---|---|---|---|---|---|
| 1 | Jersey | Moto 5.5 UltraWeld Jersey | Tiger Pink | 2026 (MY26) | 5026000200 to 204 (S to XXL) | Confirmed |
| 2 | Pants | Moto 5.5 I.K.S Pant | Tiger Pink | 2026 (MY26) | 5026000320 to 325 (US28 to US38) | Confirmed |
| 3 | Helmet | Moto 8.5 Composite helmet, V26 helmet kit (with Velocity 5.5 goggle) | Pinata Teal ("Pinata") | 2026 (MY26) | kit 1026000250 to 255 (XS to XXL) | Confirmed (11-12 photos) |
| 4 | Goggles | Velocity 5.5 (Iriz) goggle | Pinata Teal, lens Iriz Purple 78% | 2026 | 8026000150 | Frame and strap confirmed; lens likely, not confirmed |
| 5 | Gloves | Moto 2.5 X-Flow glove | Black (11-12 photos); Purple (11-10 photo 05) | Black: design since 2024, still current; Purple: MY26 | Black 6024090150 to 154 (S to XXL) / MY27 6027010260; Purple 6026000200 to 203 | Black: probable; Purple: confirmed |
| 6 | Boots | Moto 6.5 Boot | White | launched late 2025 as the 2026 boot, still current (MY27) | 3025400140 to 146 (US7 to US13) | Confirmed |

"5.5 MX Kit Combo" is a retailer bundle of items 1 and 2: Leatt itself sells the 5.5 jersey and pant separately
(its only "Ride Kit" bundle is the 3.5).

## Damien's photos and what each shows

Photos were cropped and upscaled with PIL (crop boxes in pixels of the original files, used in the comparison
sheets):

- 2026-11-12 `06` (rear left, airborne): jersey back (pink yoke, his number 114 and name), pant seat and left leg,
  pink lower legs, white boots. Crops (190,460)-(560,900) jersey, (500,650)-(740,990) boot.
- `07` (left side, panning): whole left side: helmet left, goggle strap, jersey left side, pant left thigh logo,
  left boot outer. Crops (590,30)-(800,220) helmet, (580,140)-(900,540) kit, (590,500)-(760,730) boot.
- `08` (right side from below): helmet crown and visor, jersey front, right leg, right boot outer.
  Crops (1000,220)-(1300,450), (570,210)-(980,480).
- `09` (left front from below): helmet front and goggle, jersey front, both gloves.
  Crops (1080,280)-(1290,480) helmet, (1130,350)-(1280,430) goggle, (920,570)-(1010,660) left glove.
- `10` (cockpit, his view): pant thighs only: black with lime stripes and a small white LEATT towards the right knee
  (consistent with the 5.5 pant; nothing decisive on its own).
- 2026-11-10 `05` (seated, left side): **a different outfit above the boots**: teal and black brush-camo Leatt
  jersey with sponsor prints, black Leatt pants, purple gloves, and a plain white helmet. Same goggles and same white
  boots as on 11-12. The camo jersey is not part of this task and was not identified (it is not the 5.5 Pinata
  jersey: checked).

## 1. Jersey: Leatt Moto 5.5 UltraWeld Jersey, Tiger Pink, 2026

**Identification.** Leatt US product "Jersey Moto 5.5 UltraWeld" (handle `jersey-moto-5-5-ultraweld-new-sale-my26`,
tagged MY26, colours Purple, Orange, Pinata, Royal, Tiger Pink). Leatt file name
`Leatt_JerseyMoto_5.5Ultraweld_TigerPink_ProductFront_5026000200`. Retailers: "Leatt 2026 5.5 UltraWeld Jersey -
Tiger Pink".

| Size | SKU | EAN | Source |
|---|---|---|---|
| S | 5026000200 | not seen | Leatt image id; size order of the series |
| M | 5026000201 | 6009556540996 | Leatt US, forzahub.nz |
| L | 5026000202 | 6009556541009 | forzahub.nz |
| XL | 5026000203 | 6009556541016 | forzahub.nz, starcyclegear.com.au |
| XXL | 5026000204 | 6009556541023 | Leatt US, starcyclegear.com.au |

**5.5, not 4.5 (or 3.5).** In 2026 the Tiger Pink graphic exists on four Leatt products only: the adult 5.5 jersey
and pant, the **youth** Moto 4.5 Junior jersey and pant (5026000960, 5026001040), the MY27 Moto 3.5 jersey and pant
(5027001600, 5027001620), and the 2.5 X-Flow glove. No adult 4.5 in Tiger Pink was found (Leatt US MY26 adult 4.5
Lite jersey: Orange, Purple, Pixel Blue, Red; 4.5 pant: White, Orange, Pixel Blue, Purple, Red; retailer searches
return only the 4.5 Junior). Discriminators, all visible in his photos (sheet `damien-vs-leatt_jersey.jpg`):

- Back: 5.5 = pink upper back fading through purple into a black mid and lower back, tiger stripes only on the side
  panels, a darker perforated lower-back panel. His `06` shows exactly this (pink upper back, dark below, a dot field
  of perforations on the lower right back). 4.5 Junior = a pink panel running straight down to the hem with plain
  black sides; 3.5 = a solid pink back. Neither matches.
- Neck: 5.5 = low round "no-collar" neckline; 4.5 Junior = V-neck; 3.5 = round collar with white inner print.
- Chest text: 5.5 prints "FIVE.FIVE" under the chest LEATT; 4.5 prints "FOUR.FIVE" (too small to read in his photos).
- The matching pant settles it as well (section 2).

**Colours and pattern.** Black base. Hot pink (magenta) chest and shoulder yoke with a straight lower edge across
the chest, fading at the shoulders through purple into black. Below a black band, the "tiger" pattern: wavy
nested chevron stripes pointing down the centre front, lime (neon yellow-green) at the top grading to teal (mint
aqua) at the hem, black between stripes. Sleeves: black upper sleeve with grey-teal and teal stripes, grading to
lime at the cuff. Back: pink yoke over the shoulder blades fading into black, side panels striped.

**Logos (as worn).** Front: large white LEATT across the pink chest yoke; white outline Leatt "brain" (triangle) icon
above the end of the logo on the wearer's left chest; small spaced "FIVE.FIVE" centred under the yoke. Back: small
white LEATT on the upper back over the wearer's left shoulder blade; small white "Brace Ready" label just below the
back of the collar, right of centre. Sleeves: vertical white LEATT along the outer forearm of both sleeves; small
brain icon near the elbow on the back of the sleeve. A thin white piping line runs along each shoulder seam and
down the back of the upper sleeve.

**Damien's customisation (not Leatt's).** Back: large white number "114" with a dark outline across the pink back,
his name in white above it across the shoulders (not legible at photo resolution). Front: a white "BIKE WISE" box
logo on the upper right chest, a yellow Pirelli patch on the left chest, and a column of small sponsor logos down
the wearer's right side panel ("USN" legible; at least two more, red/white and blue/white, not legible). Ask
Damien for flat photos of the jersey front and back to copy these exactly.

**Construction (Leatt features, MY26 page).** Form-fitting race fit with 360° stretch; 3D anatomically cut from three
panels (compression, anti-snag and abrasion fabrics plus maximum-breathability mesh); minimal seams; "no-collar"
Brace Ready neck; no overlays (all graphics sublimated); bluesign approved fabric with a cooling treatment; 238
laser-cut perforations (visible as dot fields on the sleeves near the shoulder, the side panels and the lower back);
silicone pant gripper at the hem inside. Visible: raglan-style seam from the neck to the underarm (follows the white
piping), long body with a straight hem, close-fitting cuffs.

**Dimensions.** Weight 180 g (size L). Size chart (Leatt adult jerseys, cm): arm length / chest / rider height:
S 76-78 / 96-102 / 168-172, M 78-80 / 102-106 / 172-178, L 80-82 / 106-112 / 178-182, XL 82-84 / 112-116 /
180-185, XXL 84-86 / 116-122 / 182-188. Damien is about 185 cm (decision 7): L or XL by height; his size is not
known.

## 2. Pants: Leatt Moto 5.5 I.K.S Pant, Tiger Pink, 2026

**Identification.** Leatt US "Pants Moto 5.5 I.K.S" (handle `pants-moto-5-5-i-k-s-new-sale-my26`, MY26, colours
Purple, Black, Orange, Pinata, Royal, Tiger Pink). Leatt files `Leatt_PantMOTO_5.5IKS_TigerPink_*_5026000320`.

| Size | SKU | EAN |
|---|---|---|
| XS / US28 / EU46 | 5026000320 | 6009556541344 |
| S / US30 / EU48 | 5026000321 | 6009556541351 |
| M / US32 / EU50 | 5026000322 | 6009556541368 |
| L / US34 / EU52 | 5026000323 | 6009556541375 |
| XL / US36 / EU54 | 5026000324 | 6009556541382 |
| XXL / US38 / EU56 | 5026000325 | 6009556541399 |

Sources: Leatt US variants (US28, US34, US36, US38), motosouth.co.nz (S, M, L), thsmoto.co.nz (XL/US36/EU54).

**5.5, not 4.5 (or 3.5).** The decisive difference: the 5.5 pant has **pink/magenta tiger stripes on both lower legs**
(shin and calf, fading through purple above the knee). The 4.5 Junior and the 3.5 Tiger Pink pants are plain
**black** below the knee. Damien's lower legs are pink-striped in `06`, `07` and `08` (sheet
`damien-vs-leatt_pants.jpg`). Logo placement also matches the 5.5 (below).

**Colours and pattern.** Teal tiger stripes at the waist and seat, lime across the upper thighs and the back of the
seat, fading to black and dark grey at the knees; pink/magenta stripes from below the knee to the cuff, purple in
the fade. Black I.K.S. knee panels on the inner knees. The stripe family is the same nested-chevron tiger as the
jersey.

**Logos (as worn).** Left thigh, outer side (seen from the front three-quarter and from behind): large vertical white
LEATT reading upward from the knee towards the hip (seated, as in his `07`, it reads horizontally along the thigh,
knee to hip; from behind in his `06`). Right lower thigh, front, just above
the knee: small horizontal white LEATT with a white outline brain icon beside it, framed by a thin white "tech" line
(visible in his `08`). Small spaced "FIVE.FIVE" along a thin white line on the left leg above the knee. Rear yoke:
white LEATT across the back of the waist with a thin white line running from it.

**Construction (Leatt features).** 360° Hypalon Waistlock system with a black ratchet strap and buckle at the front
waist; YKK Vislon zip fly; 3D anatomically cut from five panels with pre-curved knees; main shell of Twisted Yarn
Micro Mesh, 100% 4-way stretch, unlined; inner knee panels of leather with multi-layered I.K.S. inner panels (black,
fine ripstop texture, running from the inner thigh to the upper calf); 250 laser-cut perforations (dot fields on the
front thighs, the rear yoke and behind the knees); no overlays; bluesign fabric; over 22% lighter than the previous
model. Cuffs are plain, cut to sit over the boot top.

**Dimensions.** Weight 660 g (size L). Size chart (Leatt adult pants, cm): waist / inseam / rider height:
S 73-78 / 78-79 / 168-172, M 78-83 / 79-81 / 172-178, L 83-88 / 81-83 / 178-182, XL 88-93 / 83-85 / 180-185,
XXL 93-99 / 83-86 / 182-188.

## 3. Helmet: Leatt Moto 8.5 Composite (V26 helmet kit), Pinata Teal

**Identification.** Leatt US "Helmet Kit Moto 8.5 Composite with 5.5 Goggle" (handle
`helmet-kit-moto-8-5-composite-with-5-5-goggles-sale-my26`, MY26, colours Black, Grey, Orange, Pinata, Royal),
colourway "Pinata" (Leatt files `Leatt_HelmetKitMoto_8.5_PinataTeal_*_1026000250`; retailers "Leatt Moto 8.5 V26
Helmet Kit Pinata Teal"). Kit SKUs: XL 1026000254 (EAN 6009556539617), XXL 1026000255 (EAN 6009556539624) seen on
Leatt US; XS to L follow as 1026000250 to 253 (the series pattern of the other colours: Orange XS 1026000200,
S 201; Royal XS 1026000300, XXL 305). Kit contents: Moto 8.5 helmet, Velocity 5.5 goggles, visor extension, helmet
bag. Leatt makes no "Tiger Pink" helmet.

**How it was found and confirmed.** Leatt's own Tiger Pink 5.5 kit photo shoot (pant views 6 to 9 in
`reference/leatt-gear/pants/`) styles the kit with this exact helmet and goggle. Then compared with Damien
(sheet `damien-vs-leatt_helmet.jpg`), every element matches:

- Purple badge with white LEATT on the brow, above the eyeport, with a vent slot each side (`09`).
- Visor: white, a row of black arrow marks across the top surface and a small black LEATT (`08`, `09`).
- Crown: a stencilled LEATT along the top centre in iridescent teal-green to orange to red, with a purple/magenta
  bar (`08`).
- Sides: large white LEATT on an iridescent band (teal-green, yellow-orange, magenta, purple) behind the eyeport;
  below it magenta and purple panels with white chevron arrows towards the back; a white outline brain icon on a
  purple field low on the chin side (`07`, `09`).
- Chin bar: white with a black central vent (`09`).

Rejected: Moto 7.5 MY26 "Purple" (1026000400): white and purple with halftone dots and a pink chin edge, different
shell. No other 2026 Leatt helmet shows this graphic.

**Not matching: photo 05 (2026-11-10).** There he wears a **plain white Moto 8.5** with a fine black speckle print
(Leatt Moto 8.5 "White", V25, 1025100260 series; images saved). Same 8.5 shell, so the geometry is shared; only the
graphic differs. Which helmet to model is a question for Damien (the Pinata Teal goes with the Tiger Pink kit).

**Graphic in detail (from Leatt's four views).** Base colour: very light cool grey-white, gloss. Rear: lower back of
the shell black with a large white LEATT; above it a light band of white arrows with a teal brain icon centred on
a pale iridescent stripe; small black DOT/ECE and size label at the bottom edge. Small text on the chin side
"MX.26 MOTO RACE SPEC LEATT DEVELOPED" in purple. Red "EMERGENCY USE ONLY / PULL RED TAB" cheek-pad sticker at the
lower jaw. Blue Leatt 360 Turbine sticker on the crown. Black rubber eyeport trim.

**Construction (Leatt features).** Composite shell in **three shell sizes**; four densities of impact foam; 360°
Turbine Technology (rotation and low-impact discs, visible inside); Pro-Fit modulating pad set and Ionic+ washable
liner; emergency cheek-pad removal; double-D ring closure; breakaway visor plus visor extension; large ventilation
channels (two mesh-covered crown vents, brow vents either side of the badge, chin vents); designed for neck-brace
mobility; hydration side port. Certified ECE 22.06 and DOT.

**Dimensions.** Weight from 1250 ± 50 g (DOT and ECE). Head sizes: XS 53-54, S 55-56, M 57-58, L 59-60, XL 61-62,
XXL 63-64 cm. Leatt does not publish which head sizes share each of the three shells, nor shell outer dimensions:
measure from the studio views once Damien's helmet size is known.

## 4. Goggles: Leatt Velocity 5.5 (Iriz), Pinata Teal

**Identification.** Leatt US "Velocity 5.5 Goggle - Iriz", colour "Pinata Teal (Purple 78%)", SKU 8026000150,
EAN 6009556540583 (also sold by the NZ distributor as "Leatt Goggle Velocity 5.5 Iriz - Pinata Teal/Purple, 78
VLT"). The same frame and strap come in the 8.5 Pinata Teal helmet kit (the kit page only says "Velocity 5.5
goggles included" and does not name the lens). Spare lens: Velocity Lens Iriz Purple 78%, 8019100070.

**Confirmation.** Matches (sheet `damien-vs-leatt_goggles.jpg`): raspberry-pink frame (`05`, `07`, `09`); black
outriggers with a vertical white LEATT between frame and strap (`09`); iridescent strap (teal-green at the far end,
through purple and magenta to orange-yellow near the frame) with a large white LEATT (`05`, `07`, `09`). Same goggle
on 11-10 and 11-12.

**Not confirmed: the lens.** In `05` his eye shows clearly through the lens (a high-VLT lens, consistent with 78%).
In sunlit `08` and `09` the lens reflects gold, orange and pink, which a light Iriz mirror can do at grazing angles,
but it could also be another Velocity lens. Best candidate: Iriz Purple 78% (the only lens Leatt pairs with this
colourway). Ask Damien.

**Colour note.** Leatt's goggle render shows a hot pink frame; in Leatt's kit photographs and in Damien's photos the
frame reads raspberry red-pink. Take the frame colour from photographs, not the render.

**Construction (Leatt features).** Tapered frame shape for tight eyeports; dual-compound frame with a self-draining
open lower edge; outriggers; 45 mm strap with a 5 mm silicone anti-slip band; triple-layer dual-density face foam
with anti-sweat fleece; OTG fit; 170° WideVision double lens, bulletproof (ANSI Z87.1-2015, MIL-DTL-43511D), permanent
anti-fog, Iriz mirror; tear-off posts and Roll-Off ready (48 mm WideVision). CE EN 1938:2010. Damien runs no
tear-offs (decision 7): model the posts bare.

## 5. Gloves: Leatt Moto 2.5 X-Flow

**2026-11-12 photos: black gloves, most likely Moto 2.5 X-Flow Black.** Black back of hand, black cuff, light grey
palm (`06`), and a light grey-white band across the knuckles carrying a black LEATT (`08`, `09`). This is the
X-Flow Black's signature: a white-to-black gradient band across the knuckles with LEATT. No other Leatt black glove
has it (checked on Leatt US: 1.5 GripR, 2.5 ThermaFlow, 2.5 WindBlock, 3.5 Lite, 4.5 Lite). Leatt US MY26 listing
"Gloves Moto 2.5 X-Flow" Black: S 6024090150 (EAN 6009554067358), M 151, L 152 (inferred), XL 153, XXL 154; the MY27
listing (6027010260) shows the same design. Confidence: probable; the photos are too small to read stitching or
perforation. Sheet `damien-vs-leatt_gloves.jpg`.

**2026-11-10 photo 05: Moto 2.5 X-Flow Purple (MY26).** Purple, white LEATT with speed lines across the knuckles,
teal chevrons on the index and middle fingers: an exact match. M 6026000201 (EAN 6009556543300), L 202, XL 203.

**Not worn in these photos:** the kit-matching 2.5 X-Flow Tiger Pink (6026000240 series, teal/lime stripes with a
pink LEATT band, worn by Leatt's kit model).

**Construction (Leatt features).** Fully vented X-Flow mesh upper; stretch mesh finger sides with FormFit finger
stitching; NanoGrip ultra-thin seamless palm, pre-curved; multi-row Coates stretch-thread stitching; hook-and-loop
cuff closure (black tab with a white pull); touch-screen compatible. Sizes S to XXL. No published dimensions.

## 6. Boots: Leatt Moto 6.5, White

**Identification.** Leatt US "Moto 6.5 Boots" (handle `moto-6-5-boots`, colours Black, Red, White; tagged MY27
current; Leatt files `31673_Leatt_Boot_Moto_6.5_White_N_3025400140`). There is one 6.5 boot: no FlexLock or Enduro
variant exists (FlexLock is the 5.5). Retailers label the same SKUs "V25" or "V26"; a retailer listed it on
2025-11-05 and Leatt US on 2026-01-15, so it is the 2026 boot. Enduro21's first look calls it Leatt's new top of the
range boot, the brand's first with a stitched, replaceable sole and a steel toe cap; RRP EUR 649.

| US | UK | EU | cm (chart) | SKU | EAN |
|---|---|---|---|---|---|
| 7 | 6 | 40.5 | 25.5 | 3025400140 | 6009556506374 |
| 8 | 7 | 42 | 26.5 | 3025400141 | 6009556506381 |
| 9 | 8 | 43 | 27.5 | 3025400142 | 6009556506398 |
| 10 | 9 | 44.5 | 29 | 3025400143 | 6009556506404 |
| 11 | 10 | 45.5 | 29.5 | 3025400144 | 6009556506411 |
| 12 | 11 | 47 | 30.5 | 3025400145 | 6009556506428 |
| 13 | 12 | 48 | 31.5 | 3025400146 | 6009556506435 |

(The product page says "CM 25.5-31" while the size chart gives 31.5 for US13.)

**Confirmation** (sheet `damien-vs-leatt_boots.jpg`). Matches: all-white boot with four buckles on the outer side
(`07`); a black Leatt brain logo on the upper outer shin plate (`08`, `05`); the SlideLock badge at the top front
(`07`); small black inserts at the ankle and forefoot and a small black "6.5" on the outer toe box (`05`, `07`); black
sole. Rejected: 5.5 FlexLock Evo White (black "FlexLock" print, black dot patterns, large "5.5" on the forefoot) and
4.5 Evo White (large black "4.5" on the forefoot, red top buckle). His boots show normal wear: scuffed, dirty sole
edges and toe.

**Visible construction (Leatt's twelve views).** White TPU shell; black PA-fabric stretch collar (gaiter) at the top
with red lining; "LEATT SLIDELOCK" badge (black text, red rule) on the top front; four forged aluminium buckles on
white straps over white TPU plates, outer side; black brain logo on the outer shin plate; large black textured
panel with debossed LEATT over the inner calf, and black grip rubber at the inner ankle and metatarsal; black
arrow-shaped insert on the outer forefoot behind the toe box, "6.5" printed on the toe box, LEATT on the outer
ankle; silver Zamak alloy toe cap riveted to the toe tip, engraved LEATT; black Goodyear-welted sole with the welt
stitching visible, tread with Leatt triangle lugs; rear spine with a black torsion blade limiter and vertical LEATT.

**Construction (Leatt features).** LongLife Ride Kit included (spare buckles, straps, toe caps, soles); SlideLock
one-way sliding closure at the top; forged aluminium buckles with stainless steel base; Dual Axis ankle support;
rear torsion blade limiter (limits front and rear extension); 3DF impact foam at the ankle; extended grip rubber on
the ankle and metatarsal; flat grippy inside; low-profile toe box; heel-grip ankle; DualZone hardness extended
footpeg zone; CE-certified tempered steel shank; breathable 3D mesh liner. CE EN 13634:2017.

**Dimensions.** Foot lengths per size above. Shaft height and weight are **not published** by Leatt (retailer
"weights" are shipping figures). To model: scale Leatt's side view (`boot65_white_02-outer-side-buckles`) by the
sole length of Damien's size once he gives it.

## Approximate colours (starting values only)

Median-cut palettes of Leatt's studio images (sRGB; studio lighting and fabric texture mix into these; calibrate the
shaders against Damien's daylight photos):

- Jersey: pink yoke #C4006D to #C70974, lime #A2D460, teal #2BAC83, black #17161C.
- Pant: lower-leg pink #F058BA (lighter than the jersey yoke in Leatt's photos), base black #25232B to #34333A.
- Helmet: white base #C9CDD6 to #A8ADB7 in the studio shot (it is a cool light grey-white), magenta #750142 in
  shadow.
- Goggle frame (render, hot pink) #E11C8D: use the photos instead, see section 4.

## Questions for Damien

1. Sizes: jersey, pant (waist), helmet, boots (US) and gloves. Shell size and boot shaft height depend on them.
2. Helmet: model the Moto 8.5 Pinata Teal (11-12 photos) or the plain Moto 8.5 White (11-10 photo 05)?
3. Goggle lens: is it the Iriz Purple 78% that came with it, or another lens?
4. Gloves: are the black gloves the 2.5 X-Flow? Does he also ride in the purple X-Flow?
5. Jersey customisation: flat photos of the jersey front and back (name, number 114, sponsor logos and positions).

## Sources

Leatt (us.leatt.com; JSON at `<page>.js`):
- https://us.leatt.com/products/jersey-moto-5-5-ultraweld-new-sale-my26 (features, SKUs, image)
- https://us.leatt.com/products/pants-moto-5-5-i-k-s-new-sale-my26
- https://us.leatt.com/products/helmet-kit-moto-8-5-composite-with-5-5-goggles-sale-my26
- https://us.leatt.com/products/helmet-kit-moto-7-5-with-4-5-goggles-sale-my26 (rejected Purple 7.5)
- https://us.leatt.com/products/goggle-velocity-5-5-iriz-my27 and https://us.leatt.com/products/lens-velocity-iriz-my27
- https://us.leatt.com/products/gloves-moto-2-5-x-flow-sale-my26 and https://us.leatt.com/products/moto-2-5-x-flow-glove
- https://us.leatt.com/products/moto-6-5-boots, https://us.leatt.com/products/moto-5-5-flexlock-evo-boots,
  https://us.leatt.com/products/moto-4-5-evo-boots
- Comparison: https://us.leatt.com/products/jersey-moto-4-5-junior-sale-my26,
  https://us.leatt.com/products/pant-moto-4-5-junior-sale-my26, https://us.leatt.com/products/moto-3-5-jersey,
  https://us.leatt.com/products/moto-3-5-pant, https://us.leatt.com/products/jersey-moto-4-5-lite-sale-my26,
  https://us.leatt.com/products/pants-moto-4-5-sale-my26
- Size charts: https://us.leatt.com/cdn/shop/files/Jersey_Jacket_Adult_chart.jpg,
  https://us.leatt.com/cdn/shop/files/Pants_Shorts_Adult_chart.jpg,
  https://us.leatt.com/cdn/shop/files/helmet-moto-1.jpg,
  https://us.leatt.com/cdn/shop/files/Boots_a87fe527-ee14-48de-8411-5bafec54333e.jpg

Distributor and retailers:
- https://forzahub.nz/products/ran_55ulwdjysytgpnk (jersey photo set, SKUs M to XL)
- https://www.motosouth.co.nz/products/ran_le55iksptgpnk (pant photo set, SKUs S to L)
- https://starcyclegear.com.au/products/ran_55ulwdjysytgpnk (jersey XL, 2XL)
- https://www.thsmoto.co.nz/products/le5026000324 (pant XL/US36/EU54)
- https://forzahub.nz/products/le8026000150 (goggle, lens 78 VLT)
- https://www.motostorm.it/en/helmets/offroad-helmets/leatt-moto-85-v26-helmet-kit-pinata-teal.html (name "Moto 8.5
  V26 Helmet Kit Pinata Teal", LE-102600025)
- https://mojomotosport.com/products/leatt-6-5-boots-v26 and https://sharkleathers.com.au/products/ran_leb65wht (6.5
  SKUs under "V26" and "2026" names)
- https://enduro21.com/en/products-reviews/latest/first-look-new-leatt-moto-6-5-boots-for-enduro-with-stitched-sole
  (via search snippet: first stitched sole, steel toe cap, EUR 649)
