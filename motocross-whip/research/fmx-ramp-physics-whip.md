# FMX ramp, landing, trajectory physics and whip technique

Researched 2026-11-06 for the motocross whip animation: Damien on a 2026 Honda CRF250R whips a 75 ft (22.86 m) gap from a steel FMX ramp to a dirt landing (King of the Whip 2025 setting, 60 fps).

Every number has a source URL or is marked as computed (my own calculation, method shown) or estimate (my judgement, no direct source). Some sources could only be read through search-engine excerpts because the site blocks direct fetches; those are marked "(excerpt)". Treat excerpt-only numbers one notch less confident.

Confidence labels: **H** high (primary or several agreeing sources), **M** medium (one good source, or computed from sourced inputs), **L** low (anecdotal, excerpt only, or one weak source), **E** estimate (my judgement).

Coordinate convention used throughout: x = horizontal distance from the lip edge along the jump (positive toward the landing), y = height above flat ground. In Blender (bike faces -Y, Z up, per `CLAUDE.md`): Blender Y = -x, Blender Z = y.

---

## 0. Spec sheet for the build (summary)

| Item | Value | Conf. | Basis |
|---|---|---|---|
| Ramp lip height | 2.51 m (8 ft 3 in) | M | Destruction Ramps "8'3'' Comp Ramp", designed for 75 ft gaps [DR83]; inside FIM range 2.50 to 3.20 m [FIM] |
| Ramp transition | constant radius 9.1 m (30 ft), tangent to the ground at the toe | M | Destruction Ramps "9.1 Meter Aussie/EU consistent radius" plans for 22.86 m / 75 ft [DR8m]; inside FIM recommended 5.5 to 12 m [FIM] |
| Lip angle | 43.6° | M (computed) | acos(1 - 2.51/9.1); matches Cal Poly "40-45 degrees" [CP] |
| Curved deck, horizontal length | 6.28 m (arc length 6.92 m) | M (computed) | R sin(43.6°); Cal Poly "about 20 feet long" [CP], FMXSchool wooden ramp 22 ft [FS] |
| Deck width | 1.07 m (3 ft 6 in); FIM minimum 0.80 m | L | one used-ramp listing (excerpt) [FB]; [FIM] |
| Deck | expanded steel mesh, rust brown on Damien's practice site; KOTW: dark grid grip deck with white edge bands | M | ARD "Gal Mesh" [ARD]; [WA]; [KOTW] |
| Gap (lip edge to knuckle) | 22.86 m | Brief | KOTW 2025 "twenty-three-metre" ramp, measuring points not stated [KOTW] |
| Landing knuckle height | 4.00 m (1.49 m above the lip) | M | FIM 4.00 to 4.50 m for a 26 m gap [FIM] |
| Landing deck (table) | 1.50 m long, at least 2.50 m wide | H (as FIM minimum) | [FIM] |
| Landing downslope | 42° straight for 2.0 m of slope, then concave radius 10.36 m to flat; 8.42 m horizontal from knuckle to flat | E (physics-derived, section 2.3) | matched to the computed trajectory |
| Run-off after landing | at least 12 m | H | [FIM] |
| Run-in | at least 50 m straight, hard surface (paving at KOTW) | E | section 2.5 |
| Takeoff speed (rider plus bike CoM) | 16.06 m/s = 57.8 km/h = 35.9 mph (with air drag); 15.60 m/s without drag | M (computed) | section 3 |
| Airtime (rear wheel leaves lip to touchdown) | 2.27 s (136 frames at 60 fps) | M (computed) | section 3; Damien's clips measured about 2.0 to 2.2 s [WA] |
| Apex | CoM 9.65 m above ground at t = 1.10 s; tyres about 8.8 m (29 ft) above ground | M (computed) | section 3; Destin Cantrell "about 25 to 30 feet in the air" off a 75 ft metal ramp (excerpt) [KN1] |
| Touchdown | about 1.5 m past the knuckle, both wheels nearly together (front 6 cm first), surface height about 2.0 to 2.9 m (about lip height) | M (computed) | section 3 |
| g on ramp face (CoM) | 3.9 g at the lip, 4.2 g at the bottom (speed held), up to 4.8 g if coasting | M (computed) | section 3.8 |
| g at landing bottom | about 4.0 to 4.2 g, about 0.5 s after touchdown | M (computed) | section 3.9 |

---

## 1. Steel FMX ramps

### 1.1 Who builds them

| Builder | Where | What is documented | Source |
|---|---|---|---|
| Australian Ramp Design (ARD) | Australia | Products: 50s Kicker, Standard FMX Competition Kicker, Super Kicker ("radius is tighter than a standard and shoots you high in the air instead of a long distance"), Trailer Kicker ("galvanized steel frame ... surfaced in Gal Mesh steel"), Portable FMX Landing Ramps ("surfaced head to toe in HARD ramp surface"), custom ramps including one for Robbie Maddison's 2005 record. Prices quoted in AUD + GST. No dimensions published | [ARD] |
| ARD at events | Australia | Supplied the ramps for the NSW FMX Cup (down-ramp and berms by Blackwell Bros) (excerpt) | [FN] |
| FMX Kaos | Australia | Custom ramps "engineered to specific measurements", 10-year warranty; team says it built one of Australia's first portable FMX setups, starting with a steel landing ramp on a trailer (excerpt) | [KAOS], [MOTUL] |
| Destruction Ramps (Keith Yost Designs) | not stated | Sells plans, metal ("cut-bend-weld") or plywood-sided: 6' comp ramp (gaps 35 to 65 ft), 8'3'' comp ramp (75 ft gaps), 8 m radius and 9.1 m "Aussie/EU consistent radius" ramps (22.86 m / 75 ft gaps), 9' Super Kicker (45 ft gaps), dirt landing plans; "rail bending radius instructions" | [DR6], [DR83], [DR8m], [DR9] |
| FMXSchool.com | USA | Wooden and metal ramp plans; wooden ramp 8 ft tall, 22 ft long; works at 30 to 70 ft; metal ramps shown at 65 ft to an 11 ft dirt landing; metal plans include a "crank wheel" for moving the ramp | [FS], [FS2] |
| Nate Wessel (Wesselbuilt) | USA | Ramp builder for X Games and Nitro Circus; no material or dimension data found (excerpt) | [WES] |
| Nitro Circus riders | USA | Travis Pastrana: "all the guys on Nitro, they all weld their own ramps and build their own stuff" (excerpt) | [VPAS] |
| Dane Herron | USA | Course designer for Red Bull X-Fighters Texas 2008: 7 competition ramps, gaps 75 to 120 ft, two custom metal quarterpipes, 13,000+ cubic yards of dirt | [RXT] |
| European builders | Europe | **Not found.** FIM rules require metal ramps for FIM events, so European builders exist, but no named company with published specs turned up | [FIM] |

### 1.2 Published dimensions

| Source | Lip height | Length | Angle / radius | Gap | Conf. |
|---|---|---|---|---|---|
| FIM FreeStyle Motocross regulations 2017 [FIM] | 2.50 to 3.20 m | n/a | radius 5.50 to 12.00 m "strongly recommended"; "the smaller the radius, the shorter the jump zone" | jump zone 10 to 28 m | H |
| Destruction Ramps 8'3'' comp ramp [DR83] | 8 ft 3 in (2.51 m) | not stated | not stated | 75 ft | M |
| Destruction Ramps 8 m / 9.1 m ramps [DR8m] | not stated | not stated | 8 m radius; 9.1 m "consistent radius" | 22.86 m / 75 ft | M |
| Cal Poly ATV FMX ramp report (excerpt) [CP] | about 8 ft | about 20 ft | 40 to 45° launch | "heights up to 30 feet ... distances up to 80 feet" | L-M |
| FMXSchool [FS] | 8 ft (wooden) | 22 ft | not stated | 30 to 70 ft | M |
| mxdose (Josh Sheehan triple flip article) [MXD] | "the usual nine-foot ramp used to complete a double" | n/a | n/a | n/a | L |
| Used metal FMX ramp listing (excerpt) [FB] | 8 ft 5 in | 25 ft, width 3 ft 6 in, 30 ft run-up | n/a | n/a | L |
| Scribd "FMX Ramps" construction document (excerpt) [SCR] | n/a | n/a | "not on a constant radius, it is an Elliptical Radius" | 50 to 65 ft | L |
| Vital MX forum (excerpt, unverified) [VFR] | 9 ft | 24 ft, "27-foot transition" | n/a | n/a | L |

Lip angle from height and radius (computed, circular arc tangent to the ground): angle = acos(1 - h/R), horizontal length = R sin(angle).

| h (m) | R (m) | Lip angle | Horizontal length |
|---|---|---|---|
| 2.51 | 8.0 | 46.7° | 5.82 m |
| 2.51 | 9.1 | **43.6°** | **6.28 m** |
| 2.60 | 9.1 | 44.4° | 6.37 m |
| 2.50 | 12.0 | 37.7° | 7.33 m |
| 3.20 | 12.0 | 42.8° | 8.16 m |
| 2.50 | 5.5 | 56.9° | 4.61 m |

So a 2.5 m ramp built to the 8 to 9.1 m radii sold for 75 ft gaps has a lip angle of about 44 to 47°, which agrees with Cal Poly's 40 to 45°.

### 1.3 Construction, deck, finish, anchoring

- **Material:** "Ramps must be metal constructions only; wooden constructions are not permitted. Ramp surfaces may be of wood but must be no-slip and offer sufficient traction" [FIM]. Wikipedia: ramps are "usually made out of metal, as this keeps the 'lips' of the ramp consistent" [WIKI]. Ronnie Renner's 25 ft quarterpipe was "galvanized steel and plywood, modular" [RXR]. (H)
- **Frame:** welded steel, side rails bent to the transition radius ("cut-bend-weld", "rail bending radius instructions") [DR6]. Damien's practice-site ramps: "black steel support frames" [WA]. ARD trailer kicker: galvanised steel frame [ARD]. (M)
- **Deck:** ARD uses "Gal Mesh steel" (galvanised mesh) or its textured "HARD ramp surface" [ARD]. Damien's practice site: "rust-brown expanded-metal decks with lighter (galvanised or painted) edge rails" [WA]. KOTW 2025: "dark grey / black with a grid-like grip texture (looks like expanded metal or a grip mat), with white bands along both deck edges", sides wrapped in black Monster Energy fabric [KOTW]. (M)
- **Finish:** galvanised (ARD), powder coat on consumer grated-steel ramps (excerpt) [GNAR]. Raw rusted steel: seen on Damien's practice-site ramps [WA]; I found no published source saying it is "common". (L)
- **Transition shape:** constant radius ([DR8m] "consistent radius", [FIM] gives a radius) versus elliptical ([SCR]). Peter Verdone notes a straight flat section at the end of a ramp gives a stable takeoff, and that a rider can absorb a 45° lip down to about 35° effective [PV]. KOTW's ramp looks like "straight run-up section, curved transition, kicked lip" [KOTW]. Toe plates: Verdone gives 12 to 18 in plates giving 7° to 4.5° entry angles [PV]. Damien's site has "flat wooden or steel approach boards at the base of the ramps" [WA].
- **Anchoring:** **no source found.** Physics (computed, section 3.8): at the lip the rider and bike push on the deck with about 6.9 kN, which has a horizontal component of about 4.7 kN pushing the ramp **forward, toward the landing**, plus a downward 5.0 kN. A real ramp must be restrained against sliding forward (estimate: ballast, ground stakes, or bracing). At KOTW the ramp "sits directly on the paving" [KOTW].
- **FMX bike details that are visible:** Josh Sheehan's FMX CRF450R: cut grab holes in the airbox top and side plates, grip tape on frame and side plastics, higher bend bars, steering damper, "harder compression and slower rebound" than a supercross setup, 13/51 gearing instead of 13/48, tyres at 15 psi [SHE]. Damien's bike is stock per the brief, so use only if he says so.

### 1.4 What is standard for a 70 to 80 ft gap

The only source that ties a ramp size to 75 ft is Destruction Ramps: an 8 ft 3 in comp ramp and 8 m or 9.1 m radius ramps [DR83], [DR8m]. Cal Poly's "average" ramp (8 ft, 20 ft long, 40 to 45°) is said to reach 80 ft [CP]. FMXSchool's 8 ft ramp is used to 70 ft [FS]. A 9 ft ramp is "usual" for double backflips [MXD]. Tighter-radius, taller "super kickers" are for shorter, higher jumps (45 ft for Destruction's 9 ft super kicker [DR9]; ARD's super kicker "shoots you high ... instead of a long distance" [ARD]). Mike Metzger: "70 to 80 feet with a normal freestyle ramp" versus "about 45 to 55 feet" with a backflip ramp (excerpt) [MET].

### 1.5 Recommended ramp

- Lip height **2.51 m**, constant radius **9.1 m** tangent to the ground, lip angle **43.6°**, curved deck 6.28 m horizontal (6.92 m along the surface), plus an approach plate at the toe (0.3 to 0.45 m, estimate from [PV]). Overall about 6.6 m long. Deck width **1.07 m** (L). (M overall)
- Justification: the only geometry explicitly sold for 75 ft gaps [DR83], [DR8m]; inside every FIM limit [FIM]; angle agrees with [CP]; length agrees with [CP], [FS].
- Optional, to match the KOTW look of a "straight run-up section" [KOTW]: a straight entry at 12° for 0.96 m, then the 9.1 m radius to the same 2.51 m / 43.6° lip; horizontal length 5.32 m (computed). The trajectory is unchanged as long as the lip height and angle are the same.

Ramp profile (computed, constant radius, toe at x = -6.28 m):

| x (m) | -6.28 | -5.38 | -4.48 | -3.59 | -2.69 | -1.79 | -0.90 | 0.00 |
|---|---|---|---|---|---|---|---|---|
| y (m) | 0.00 | 0.04 | 0.18 | 0.41 | 0.74 | 1.18 | 1.76 | 2.51 |
| surface slope | 0.0° | 5.7° | 11.4° | 17.2° | 23.2° | 29.5° | 36.2° | 43.6° |

Formula: y = 9.1 - sqrt(9.1² - (x + 6.28)²).

---

## 2. Dirt landing and run-in

### 2.1 Sources

- FIM: landing areas 4.00 to 4.50 m high "when the distance between the take-off ramp and the landing is 26 m"; "table on top of the landing area must be 1.50 m (L) x 2.50 m (W)" minimum; jump zone 10 to 28 m ("in which case the height of the landing area must be increased accordingly"); arena height above the jump zone at least 14 m; run-off at least 12 m; course surface natural (sand, dirt), "hard standing, capable of giving good traction" [FIM]. (H)
- FMXSchool: metal ramps "set up at 65 feet, to an eleven-foot tall dirt landing" [FS]. (M)
- Wikipedia: "The landing ramp is normally constructed from dirt" [WIKI]. (H)
- Destruction Ramps dirt-jump e-book covers "takeoffs, watering, packing, radius, angles and landings" (contents not published) [DRJ]. (L)
- KOTW 2025: one large machine-sculpted mound of tan/ochre sand on paving, flat trimmed faces, sponsor banner on the ramp-facing face; height guessed at "at least 4 to 5 m" (low confidence); downslope not visible in any photo; sand from Cloete's Sand & Stone and azagneiss [KOTW]. (M)
- No source gives a downslope angle, downslope length or landing width for a 75 ft FMX landing. These are physics-derived below (E).

### 2.2 Gap convention

The brief's 75 ft and KOTW's 23 m do not say what is measured [KOTW]. FIM's "distance between the ramp and the landing (= jump zone)" is also ambiguous [FIM]. I use **lip edge to knuckle** (the knuckle being the top edge where the downslope starts), with the FIM 1.5 m table in front of it. If the gap is instead measured to the front of the table, move the whole landing 1.5 m further away and the takeoff speed rises by about 0.5 m/s (estimate from the point-mass sensitivity in 3.3).

### 2.3 Recommended landing (physics-derived)

Design logic: the trajectory comes down at about 45 to 46° (section 3), so the upper downslope must be steep to keep the landing soft, and it must then curve to flat within a 4.0 m tall mound. A 42° straight for 2.0 m followed by a 10.36 m radius gives about 4 g at the bottom, the same as the takeoff transition.

| Element | x (m) | y (m) | Notes | Conf. |
|---|---|---|---|---|
| Front face base (toward ramp) | 15.65 | 0.00 | 35° face (E) | E |
| Front edge of table | 21.36 | 4.00 | | H for the 1.5 m table [FIM] |
| Knuckle | 22.86 | 4.00 | 1.49 m above the lip | M [FIM] |
| End of 42° straight | 24.35 | 2.66 | slope length 2.0 m | E |
| Concave arc, radius 10.36 m | 24.35 to 31.28 | 2.66 to 0 | slope 37.3° at x = 25, 30.6° at 26, 24.4° at 27, 18.5° at 28, 12.7° at 29, 7.1° at 30 | E |
| Flat run-out starts | 31.28 | 0.00 | | E |
| End of run-off | 43.3 or more | 0.00 | 12 m minimum | H [FIM] |

Arc formula: centre at (31.28, 10.36), y = 10.36 - sqrt(10.36² - (31.28 - x)²).

Other landing values:
- Width: table at least 2.50 m [FIM]. Recommend about 5 m at the crest, widening toward the bottom (E), because Damien's line starts off-centre and the whip moves the bike sideways.
- A small rounding of the knuckle edge (0.5 to 1 m radius) looks natural (E).
- Surface: compacted, watered sand/dirt, hard and grippy [FIM], [DRJ]; KOTW used tan/ochre sand [KOTW].
- Decision #9 in `PROJECT.md` says "landing slightly below lip height". With FIM proportions the **crest is above the lip** (4.0 vs 2.51 m), while the **touchdown point** (surface height about 2.0 to 2.9 m) is about lip height. Please confirm with Damien which he meant.
- Alternative: a 4.5 m knuckle (FIM maximum) allows a longer steep section and about 3.6 g at the bottom, with takeoff speed about 16.2 m/s (computed in a design scan, E).

### 2.4 Approach surface

FIM: run-ups "can be on concrete or paved surfaces ... or 'runway boards' incorporating a grid" and must be "sufficiently long to give the average rider ... enough speed to clear the jump zone distance easily" [FIM]. KOTW 2025: run-in on the interlocking concrete paving, no visible approach boards [KOTW]. (H)

### 2.5 Run-in length (estimate)

No source gives a number. Speed needed at the ramp toe is 16.1 m/s (if the rider holds speed up the face) to 17.7 m/s (if coasting; computed in 3.8). From a standstill at an average 3 to 4 m/s² (0.3 to 0.4 g, E): v²/(2a) = 36 to 48 m. Recommend **at least 50 m of straight, level run-in** (E). At 16.06 m/s the CRF250R's rear wheel turns at 463 rpm; with the 13/50 final drive, 3.047 primary and the gearbox ratios in `crf250r-2026.md`, engine speed is about 10,500 rpm in 2nd, 8,700 rpm in 3rd, 7,300 rpm in 4th (computed). Ben Townley: select the gear before the face and use "low to mid revs" so there is rpm in reserve [BT]. A forum rider uses "3rd gear on a CR250" for a similar ramp (excerpt, L) [VFR]. Gear choice is Damien's (useful for the sound phase).

---

## 3. Physics

### 3.1 Inputs

| Input | Value | Conf. | Source |
|---|---|---|---|
| Total mass, rider plus bike | 180 kg (bike 106 kg, so rider plus kit about 74 kg) | brief / H | brief; CRF250R 234 lb (106 kg) wet [MCOM], [HAU] 107 kg |
| Wheelbase | 1.483 m | H | [HAU], [MCOM] |
| Tyres | 80/100-21 front, 100/90-19 rear; nominal radii 0.347 m and 0.331 m | M (computed) | [MCOM]; `crf250r-2026.md` |
| Combined CoM | 0.70 m ahead of rear axle, 0.47 m above the axle line (about 0.80 m above ground) | E | bike 48.6/51.4 F/R [crf250r-2026.md]; standing-rider CoM estimated |
| Air density | 1.20 kg/m³ | E | sea level, 20 °C. Estimate: Johannesburg is a high-altitude city (roughly 1,500 m, not checked), where density would be roughly 1.0 kg/m³, lowering drag by roughly 15 % |
| CdA, bike plus upright rider | 0.70 m² | E | a faired road bike with an upright rider measured 0.500 m² in a full-scale wind tunnel (excerpt) [WAR]; a naked dirt bike with a standing rider in loose kit is assumed higher |
| CdA, bike crossed up in the whip | rising to 1.10 m² between 0.15 and 1.85 s | E | bike side area presented to the air |
| g | 9.81 m/s² | H | |

### 3.2 Formulas

Point mass, no drag, launch at speed v and angle θ from the lip:
- x(t) = v cosθ · t, y(t) = h_lip + v sinθ · t - g t²/2
- Speed to reach a point (dx, dy) from the lip: v² = g dx² / (2 cos²θ (dx tanθ - dy))
- Time to apex t_a = v sinθ / g; apex height above launch = (v sinθ)² / (2g); total time T = dx / (v cosθ)

With drag (used for the main solution): m dv/dt = -m g ŷ - ½ ρ CdA |v| v, integrated with RK4 at 0.5 ms. The combined CoM is the projectile. At departure the rear tyre is at the lip edge (0, 2.51), the bike pitched at the lip angle, so the CoM starts at (-0.05, 3.57). Touchdown is the first contact of either tyre (modelled as circles) with the landing profile. Bike pitch is interpolated at a constant rate from the lip angle to the landing slope: for a rigid body with no internal torques, angular momentum is conserved, so a constant rate is physically right for the net rotation.

### 3.3 Point-mass check (no drag, lip to landing)

| Launch angle | To knuckle (22.86, +1.49 m) | To 25.5 m, -0.31 m below lip |
|---|---|---|
| 38° | 15.88 m/s, T 1.83 s, apex +4.87 m, descent -33.1° | 15.93 m/s, T 2.03 s, apex +4.90 m, descent -38.9° |
| 40° | 15.71 m/s, 1.90 s, +5.20 m, -35.3° | 15.82 m/s, 2.10 s, +5.27 m, -40.8° |
| 42° | 15.59 m/s, 1.97 s, +5.55 m, -37.6° | 15.75 m/s, 2.18 s, +5.66 m, -42.8° |
| **43.6°** | **15.52 m/s, 2.03 s, +5.84 m, -39.4°** | **15.73 m/s, 2.24 s, +5.99 m, -44.3°** |
| 45° | 15.49 m/s, 2.09 s, +6.11 m, -41.0° | 15.72 m/s, 2.29 s, +6.30 m, -45.7° |
| 48° | 15.48 m/s, 2.21 s, +6.74 m, -44.4° | 15.77 m/s, 2.42 s, +7.00 m, -48.6° |

Takeaways: near 45° the required speed hardly depends on the angle (about 15.5 to 15.9 m/s for any lip from 38 to 48°), so riders control distance with speed; the angle mainly sets height and airtime.

### 3.4 Main solution (with drag, whip CdA profile)

| Quantity | No drag | CdA 0.7 constant | CdA 0.7 rising to 1.1 in the whip (recommended) |
|---|---|---|---|
| Takeoff speed (CoM) | 15.60 m/s, 56.2 km/h, 34.9 mph | 15.94 m/s, 57.4 km/h, 35.7 mph | **16.06 m/s, 57.8 km/h, 35.9 mph** |
| Airtime | 2.25 s | 2.26 s | **2.27 s** |
| Apex (CoM above ground), time | 9.47 m, 1.10 s | 9.59 m, 1.10 s | **9.65 m, 1.10 s** |
| Horizontal speed, takeoff to touchdown | 11.30 constant | 11.52 to 10.78 m/s | 11.63 to 10.66 m/s |
| Touchdown CoM speed, descent | 16.00 m/s, -45.1° | 15.53 m/s, -46.0° | 15.47 m/s, -46.5° |
| Touchdown normal velocity | 2.4 m/s | 2.2 m/s | 2.3 m/s |
| Rear axle at touchdown | (24.56, 3.04) | (24.36, 3.18) | (24.36, 3.18) |
| Pitch rate in the air | -38.0°/s | -37.9°/s | -37.7°/s |
| Rear tyre clearance over knuckle | 0.21 m | 0.22 m | 0.25 m |

All computed (M). The front tyre touches about 6 cm before the rear, which matches Damien's clip ("front wheel marginally first") [WA].

### 3.5 Trajectory table (recommended case, every 0.1 s)

t = 0 when the rear tyre leaves the lip. Frame = t x 60. Pitch is the bike's straight-line attitude (nose up positive); during the whip the bike's own orientation departs from this (section 4), but the **combined CoM must stay on this path**.

| t (s) | frame | x CoM (m) | y CoM (m) | CoM above lip (m) | vx (m/s) | vy (m/s) | speed (m/s) | pitch (°) | rear axle x | rear axle y |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 0 | -0.05 | 3.57 | +1.06 | 11.63 | +11.07 | 16.06 | +43.6 | -0.23 | 2.75 |
| 0.1 | 6 | 1.12 | 4.63 | +2.12 | 11.59 | +10.06 | 15.34 | +39.8 | 0.88 | 3.82 |
| 0.2 | 12 | 2.27 | 5.58 | +3.07 | 11.55 | +9.04 | 14.66 | +36.1 | 1.98 | 4.79 |
| 0.3 | 18 | 3.42 | 6.44 | +3.93 | 11.50 | +8.03 | 14.03 | +32.3 | 3.08 | 5.67 |
| 0.4 | 24 | 4.57 | 7.19 | +4.68 | 11.45 | +7.01 | 13.43 | +28.5 | 4.18 | 6.44 |
| 0.5 | 30 | 5.72 | 7.84 | +5.33 | 11.40 | +6.01 | 12.89 | +24.7 | 5.28 | 7.12 |
| 0.6 | 36 | 6.85 | 8.39 | +5.88 | 11.35 | +5.00 | 12.40 | +21.0 | 6.37 | 7.70 |
| 0.7 | 42 | 7.99 | 8.84 | +6.33 | 11.30 | +4.00 | 11.99 | +17.2 | 7.46 | 8.18 |
| 0.8 | 48 | 9.11 | 9.19 | +6.68 | 11.25 | +3.00 | 11.65 | +13.4 | 8.54 | 8.57 |
| 0.9 | 54 | 10.24 | 9.44 | +6.93 | 11.21 | +2.01 | 11.38 | +9.7 | 9.63 | 8.86 |
| 1.0 | 60 | 11.35 | 9.59 | +7.08 | 11.16 | +1.02 | 11.21 | +5.9 | 10.71 | 9.05 |
| 1.1 | 66 | 12.47 | 9.65 | +7.14 | 11.11 | +0.04 | 11.11 | +2.1 | 11.79 | 9.15 |
| 1.2 | 72 | 13.58 | 9.60 | +7.09 | 11.07 | -0.94 | 11.11 | -1.6 | 12.86 | 9.15 |
| 1.3 | 78 | 14.68 | 9.46 | +6.95 | 11.02 | -1.91 | 11.19 | -5.4 | 13.94 | 9.06 |
| 1.4 | 84 | 15.78 | 9.22 | +6.71 | 10.98 | -2.89 | 11.35 | -9.2 | 15.02 | 8.87 |
| 1.5 | 90 | 16.88 | 8.88 | +6.37 | 10.94 | -3.85 | 11.60 | -13.0 | 16.09 | 8.58 |
| 1.6 | 96 | 17.97 | 8.45 | +5.94 | 10.90 | -4.82 | 11.91 | -16.7 | 17.16 | 8.20 |
| 1.7 | 102 | 19.06 | 7.92 | +5.41 | 10.86 | -5.78 | 12.30 | -20.5 | 18.24 | 7.72 |
| 1.8 | 108 | 20.14 | 7.29 | +4.78 | 10.82 | -6.74 | 12.75 | -24.3 | 19.31 | 7.15 |
| 1.9 | 114 | 21.22 | 6.57 | +4.06 | 10.79 | -7.70 | 13.26 | -28.0 | 20.38 | 6.48 |
| 2.0 | 120 | 22.30 | 5.75 | +3.24 | 10.76 | -8.66 | 13.81 | -31.8 | 21.46 | 5.72 |
| 2.1 | 126 | 23.37 | 4.84 | +2.33 | 10.72 | -9.61 | 14.40 | -35.6 | 22.53 | 4.86 |
| 2.2 | 132 | 24.44 | 3.83 | +1.32 | 10.68 | -10.55 | 15.02 | -39.3 | 23.60 | 3.91 |
| 2.27 (touchdown) | 136 | 25.20 | 3.06 | +0.55 | 10.66 | -11.22 | 15.47 | -42.0 | 24.36 | 3.18 |

### 3.6 Does air drag matter?

- Drag force at 16 m/s: 77 N (CdA 0.5), 108 N (0.7), 170 N (1.1), i.e. 0.04 to 0.10 g (computed).
- Visually: no. The arc shape is indistinguishable.
- For placing the landing: yes. Using the no-drag speed (15.60 m/s) with real drag puts the rear axle at x = 20.8 m instead of 23.9 m, about 3 m short: a case. Drag costs about 0.46 m/s (+2.9 %) of takeoff speed, of which the whip itself costs about 0.11 m/s. This agrees with Townley: "You'll need to hit the ramp faster than you would for a straight jump" [BT].
- CdA is an estimate. An error of plus or minus 0.3 m² changes the required speed by about plus or minus 0.15 m/s, the same size as the landing window below. At KOTW's altitude (lower air density) the required speed would be a little lower.

### 3.7 Landing window (sensitivity, computed)

| Takeoff speed change | Rear axle vs knuckle | Result |
|---|---|---|
| -0.10 m/s | -1.0 m | front wheel hits the table: case, about 9 m/s into flat ground |
| -0.05 m/s | +0.9 m | soft, normal velocity 0.9 m/s |
| 0 (nominal) | +1.5 m | 2.3 m/s |
| +0.05 m/s | +1.9 m | 3.2 m/s |
| +0.10 m/s | +2.2 m | 4.0 m/s |
| +0.20 m/s | +2.8 m | 5.2 m/s (landing where the slope has flattened) |

The trajectory and the 42° slope are nearly parallel, so a small speed error moves the touchdown point a long way along the slope. The soft window is only about 0.15 to 0.25 m/s (under 1 km/h) on this 4.0 m landing, and short is far worse than long. This explains why FMX riders need a very repeatable run-in, and why a taller landing (4.5 m) is kinder. For the animation the rider hits the nominal by definition.

### 3.8 Ramp face, lip and suspension (computed unless stated)

- Time on the curved deck: 6.92 m / 16.06 m/s = **0.43 s** (26 frames at 60 fps).
- Speed at the ramp toe: 16.06 m/s if the rider holds speed with throttle, up to 17.67 m/s (63.6 km/h) if coasting (CoM rises 2.77 m: v_base² = v_lip² + 2 g · 2.77).
- Load on the CoM, whose path radius is 9.1 - 0.8 = 8.3 m: a = v²/8.3 + g cos(slope). **3.9 g at the lip, 4.2 g at the bottom** with speed held; 4.8 g at the bottom if coasting.
- Force on the deck at the lip: 180 kg x 38.2 m/s² = 6.9 kN, pushing the ramp forward (4.7 kN) and down (5.0 kN).
- Bike pitch rate on the transition: +v/R = 16.06/9.1 rad/s = **+101°/s nose-up**. In the air it is **-38°/s nose-down**. The switch happens in the 0.09 s between front and rear wheel leaving the lip (wheelbase 1.483 m / 16.06 m/s): once the front is off, the rear-wheel normal force acts behind the CoM and pitches the bike nose-down (estimate of the needed torque: 55 kg·m² x 2.4 rad/s / 0.09 s, about 1.5 kN·m, i.e. about 2 kN at the rear tyre, well below the 6.9 kN available). On video this reads as the bike "pivoting" at the lip.
- At departure the CoM is almost directly above the rear tyre (horizontal offset 0.05 m), so gravity gives no pitching torque at that instant.
- Suspension: travel 310 mm front, 308 mm rear [HAU] (307.3 mm [MCOM]); Honda's standard rear race sag is 100 mm, range 90 to 110 mm (older CRF250R manual, excerpt) [SAG]. With about 4 g for 0.4 s the fork and shock go deep into their stroke while the rider's legs also bend (estimate: 60 to 85 % of travel). At the lip the load drops to 0 g, the suspension rebounds and the wheels hang at full extension in the air (about the sag distance further from the chassis than at ride height). Pingree pushes "the bike down into the face to get as much lift as I can as the suspension rebounds" [PIN]. No FMX spring-rate data was found.

### 3.9 Landing loads (computed)

- Touchdown normal velocity about 2.3 m/s: normal kinetic energy ½ x 180 x 2.3² = 476 J. Absorbed over about 0.2 m of suspension and legs: about 1.4 g plus 0.74 g (gravity component on 42°), so about 2 g for the first 0.1 to 0.15 s.
- Then the concave run-out (CoM path radius 10.36 - 0.8 = 9.56 m) at about 16.85 m/s: **about 4.0 to 4.2 g**, reached about 0.5 s after touchdown (path length about 8 m to the flat). The suspension is deep in its stroke again; bottoming is likely on any mismatched or long landing (E).

### 3.10 Wheel spin, throttle, brake and gyroscopic effects

- Wheel speed at takeoff: rear 48.5 rad/s = **463 rpm** (7.7 rev/s), front 442 rpm (computed). At 60 fps the rear turns 46° per frame, so 36-spoke wheels alias badly: use motion blur.
- Wheel angular momentum (estimate, I_rear about 0.9 kg·m², I_front about 0.7 kg·m²): rear about 44, front about 32 kg·m²/s.
- Rear brake in the air: stopping the rear wheel completely changes the system pitch rate by about 36 to 63°/s nose-down (system pitch inertia 40 to 70 kg·m², E). A short tap does a fraction of that. Riders: "If your front end is too high in the air ... dab some rear brake"; "If your front end is too low in the air, give it some throttle" [LEE2]; "your bike rotates forward and your front end drops" [LEE1]; pull the clutch with the brake so the engine does not stall (excerpt, L) [VRB]. Some forum riders dispute the physics explanation, not the effect (excerpt) [VRB].
- Throttle shut in the air with the clutch engaged: engine braking slows the rear wheel, a mild nose-down reaction (physics, E). Townley closes the throttle as the rear leaves the lip so that the rear "is free to rise and turn around the headstock" [BT].
- Throttle on in the air: spins the rear up, nose-up reaction, and increases gyroscopic stiffness. Townley: "prolonged high revs are needed to ensure the wheel rotates fast enough" to bring the bike back [BT]; Bernard: "rev your bike once your whip gets bigger, to help it come back faster" [MB].
- Gyroscopic coupling (physics, M): with wheels spinning forward, rolling the bike to its left produces a nose-left yaw (the same effect that steers a leaning bicycle into the lean). For a rear-to-the-right whip this helps: lay it over left and the gyros swing the tail right. Rolling it back upright produces nose-right yaw, which straightens it. With about 76 kg·m²/s of wheel angular momentum, a 150 N·m roll input from the rider corresponds to about 2 rad/s of yaw precession (estimate): the gyros are a first-order effect in a whip, not a detail.

### 3.11 Comparison with reported values

| Reported | Value | Our result | Source |
|---|---|---|---|
| Height off a 75 ft metal ramp | "about 25 to 30 feet in the air" | tyres 8.8 m (29 ft), CoM 9.65 m (31.7 ft) | (excerpt) [KN1] |
| Typical FMX ramp performance | "heights up to 30 feet and ... distances up to 80 feet" | touchdown 24.4 to 25.5 m (80 to 84 ft) from the lip | (excerpt) [CP] |
| 75 ft show gap | "jumps up to 40 ft. high in the air" | 29 to 32 ft | [CPR] (promotional, probably exaggerated) |
| Damien's clips | airtime about 2.0 to 2.2 s | 2.27 s | [WA] |
| Show ramp speed | "hit the ramp at 30 miles per hour and jump 35 feet in the air" | 35.9 mph | (excerpt) [HW] promotional, different setup |
| Nitro Circus 45 ft Giganta (roll-in mega ramp) | "40 miles per hour" | 35.9 mph | (excerpt) [NIT] different ramp type |

No measured takeoff speed or airtime for a standard 75 ft FMX jump was found. The 0.1 to 0.2 s difference from Damien's clips is within his ±0.05 s measuring error plus my landing assumptions; matching it exactly would need either a slightly lower effective launch angle (about 40°, airtime about 2.1 s) or a touchdown higher on the landing.

---

## 4. The whip

### 4.1 Definition and variants

- "A Whip is when the rider makes their bike fly sideways in the air"; "The aim of the game here is to get your bike as backwards, upside-down and twisted as humanly possible"; "the oldest trick in the book" [RB].
- Variants named: turn-down, turn-up, supercross whips [RB]; X Games list the turn up, turn down, oppo and seat bounce whip (excerpt) [XG].

### 4.2 Technique, step by step (sourced)

| Phase | What the sources say |
|---|---|
| Approach and face | Hit the ramp faster than for a straight jump; select gear before the face; "torque up the ramp" at "low to mid revs" with rpm in reserve; same line as a normal jump at the base, then "veer about 300-500mm off that line as you leave the lip"; body as for a normal jump with "weight slightly to the inside" [BT]. Matt Bernard (5th, X Games Sydney Best Whip): for a whip with the bike out to the right, start "slightly left of centre of the jump" and "start steering the bike slightly to the right" up the face [MB]. Start the turn on the face, not in the air [OMX]. Stand on the balls of the feet, head forward [PIN]. Do not back off the throttle on the face [LEE2] |
| Lip | Bernard: when the front wheel reaches the top, "drop your shoulder to flatten out your bike", "simultaneously sit back as far as you can", turn "the handlebars on full lock (turning towards the direction you whip the bike out)", "push down with your feet on the footpegs"; "it's the timing of your lean that makes or breaks a big whip" [MB]. Townley: weight goes back to centre and you countersteer as the front leaves; close the throttle as the rear follows [BT]. MTB analogue: the turn off the lip "should be little more than a gesture"; hips push the bike toward the whip [BF] |
| Peak | Townley: "At the top of the flight, your inside hand barely touches the bars"; the torso moves past the normal seated position toward the top side of the horizontal bike; keep the lower foot on its peg (main contact); the upper foot on looks better; body English from the torso, not head and shoulders [BT]. Bernard: "You are pulling the handlebars past your torso" [MB] |
| Return | Townley: high revs, so the gyro brings the bike back; late or half-hearted throttle causes problems; both hands and both feet back on before landing [BT]. Bernard: turn the bars "a second time in the opposite direction" if the return is hard [MB]. MTB: hips back toward the landing "in one fluid action" [BF] |
| Landing | Bike and bars pointing down the landing [BF]; land "on the balls of your feet so you can absorb the landing softly" and "apply throttle as you land" [PIN]; on a proper downslope, both wheels together is softer than front first (MTB, Jeff Kendall-Weed) [JKW] |

Biomechanics research: none found for FMX whips. A 2024 IMU pilot study of motocross riders (two riders, cornering and jumping) is the closest; its authors note the lack of field kinematics data [OST].

### 4.3 Our direction: rear wheel to the right

From Damien's clips [WA]: seen from behind the ramp the nose swings to image-left and the tail to image-right; at the peak the front fender is out to his left and the rear is high to the right; his weight shifts left over the front; torso and helmet face the direction of travel; the twist is in hips and legs.

Consistent geometry (physics inference, M): nose yawed left and tail right, bike rolled onto its **left side** at the peak (right-side panels toward the sky), so the **left footpeg is the low one** and the left foot is the main contact; the rider's mass sits left and above. This is Bernard's "whipping to the right" ("I am personally more comfortable having the bike out towards the right, while I lean towards the left") [MB], and it is the direction the gyroscopic coupling assists (3.10).

Open question: **bar direction at the peak.** Bernard says bars to full lock toward the side the bike goes out (right, for us) [MB], while turn-down whips point the front wheel toward the ground (left, for a bike on its left side) [RB]. Check clip 2, frames 35 to 43.

For a left-whipping rider everything mirrors. Bernard's test for your natural side: most riders who "whip the bike out towards left" "lean towards the right" [MB].

### 4.4 What makes a whip look good to judges

- X Games Best Whip: "the most flawlessly executed, stylish whip" [XGV]; "most flawlessly executed, stylish, and difficult" (excerpt) [XG]. Some X Games editions were decided by fan vote (excerpt) [XG], [RX13].
- Red Bull: as "backwards, upside-down and twisted as humanly possible"; crowds love "a big dirty Whip" [RB].
- Crankworx Whip-Off (mountain bike, but the closest published criteria): "amplitude, style, degree of whip past 90 degrees and, most importantly, the return of the bike to a straight position down the fall line"; other write-ups add fluidity ("carving off the lip, not looking stiff and landing nicely") and how long the bike is held out to the side (excerpt) [CW].
- FIM: "Personal appreciation" rewards "show" and "style"; deductions for "dead sailors, bad landings" [FIM].
- Transmoto opinion: "a perfectly executed whip is like a sunset", "Less is more" [TMW]. Dirt Shark Biggest Whip 2013: judged by professionals so it is not a popularity contest; Twitch: "There are no rules, man" [RXD].
- Damien's style [WA]: instant aggressive initiation, genuinely flat peak that is held, two-stage return (un-roll first, un-yaw later), long cross-up, late quick straighten.

### 4.5 Whip timing breakdown (for the animation)

Damien's measured phases [WA] scaled by 2.27/2.10 = 1.08 to the computed airtime. Frames at 60 fps. Bike angles are blocking estimates (E) to be replaced by the camera-matched values planned in `whip-analysis-user-clips.md`. Roll = left side toward the ground; yaw = nose left of travel, tail right.

| Phase | t (s) | Frames | % airtime | Bike (E) | Rider and controls |
|---|---|---|---|---|---|
| Face | -0.43 to 0.00 | -26 to 0 | | upright, line left of centre, steering slightly right; 4 g compression | standing, balls of feet, steady throttle, weight slightly inside [BT], [MB], [PIN] |
| Front wheel leaves lip | -0.09 | -6 | | pitch +43.6°, pitch rate flips from +101°/s | initiation starts: shoulder drop, bar input, sit back, push pegs [MB] |
| 1. Leave lip, initiate | 0.00 to 0.11 | 0 to 6 | 0 to 5 % | roll to about 15°, yaw about 10° | throttle closed as the rear leaves [BT] |
| 2. Lay it down | 0.11 to 0.32 | 6 to 19 | 5 to 14 % | roll to about 75°, yaw about 45° | weight shifts left over the front; torso upright, facing forward [WA] |
| 3. Peak flat, held | 0.32 to 0.54 | 19 to 33 | 14 to 24 % | roll 85 to 90° (flat), yaw 50 to 60°, rear higher than front | left foot on the low peg, hand on the low grip light [BT]; held, not passed through [WA] |
| 4. Stand it back up | 0.54 to 0.97 | 33 to 58 | 24 to 43 % | roll back toward 0 to 20° while yaw stays large; nose steeply down ("from behind the bike looks vertical with the front wheel at the bottom") [WA] | revs start rising [BT], [MB] |
| 5. Hold the cross-up | 0.97 to 1.89 | 58 to 113 | 43 to 83 % | yaw held, pitch eases toward the landing slope; apex at 1.10 s (frame 66) | torso faces forward, twist in hips and legs [WA] |
| 6. Straighten and land | 1.89 to 2.27 | 113 to 136 | 83 to 100 % | yaw to about 0 late and quick; pitch -42° at touchdown; front tyre about 6 cm first | both hands and both feet back on [BT]; throttle on at touchdown [PIN] |
| Landing transition | 2.27 to about 2.8 | 136 to about 168 | | suspension deep, about 4 g at the bottom | legs absorb [PIN] |

Physical constraints for the animator:
- The **combined** CoM follows the table in 3.5 regardless of the whip. With bike 106 kg and rider 74 kg, if the bike's CoM moves 0.30 m right, the rider's must move 0.43 m left (computed).
- No net lateral drift in plan view: Bernard's off-centre start exists so that "you fly straight and don't drift off the side" [MB]. Keep the CoM within about 0.5 m of the centreline (E).
- Damien peaks flat early (0.3 to 0.5 s, still climbing). Townley's generic MX whip peaks "at the top of the flight" [BT]. Follow Damien's clips.

---

## 5. Rider and bike behaviour summary (ramp, lip, air, landing)

- **Face:** standing, balls of feet, head forward [PIN]; steady throttle, low to mid revs, gear chosen beforehand [BT]; "Hold the throttle ... say at 1/2", do not back off, "Leave the throttle open until you take off"; optional "Right at the top of the lip, crank it up to 3/4 for a sec" for extra lift [LEE2]; suspension compressed deep by about 4 g (3.8).
- **Lip:** pitch at departure equals the lip angle, 43.6° (computed; Damien's clip: "pitched up at roughly the lip angle" [WA]); front leaves 0.09 s before the rear; the bike's pitch rate reverses from +101°/s to -38°/s.
- **Air:** rear wheel at 463 rpm, slowed by engine braking with the throttle shut, revved up for the return (3.10); rear brake only if the nose is high [LEE2]; a rider "can adjust the bike's attitude with body position, throttle, and rear brake" [PIN].
- **Landing:** both wheels nearly together, front marginally first [WA], [JKW]; normal velocity about 2.3 m/s, then about 4 g in the run-out; throttle on as you land [PIN].

---

## 6. Conflicts between sources

1. **Lip angle:** Cal Poly 40 to 45° [CP]; low-quality buying guides say 25 to 35° or 10 to 35° (excerpt, not used); FIM height and radius limits allow 38 to 65° [FIM]. Kept 43.6° (computed from [DR83], [DR8m]).
2. **Ramp height for about 75 ft:** 8 ft [CP], [FS]; 8 ft 3 in [DR83]; "usual nine-foot ramp" [MXD]; 8 ft 5 in listing [FB]; FIM 2.50 to 3.20 m [FIM].
3. **Ramp length:** 20 ft [CP], 22 ft [FS], 25 ft [FB], 24 ft with a 27 ft transition [VFR].
4. **Transition shape:** constant radius [DR8m], [FIM] versus elliptical [SCR]; flat section at the end recommended by [PV]; KOTW looks like a straight entry plus curve [KOTW].
5. **Landing height:** FIM 4.0 to 4.5 m at 26 m [FIM] versus 11 ft (3.35 m) at 65 ft [FS]; KOTW guessed at 4 to 5 m [KOTW]. Also `PROJECT.md` decision #9 ("slightly below lip height") versus FIM's crest above the lip (see 2.3).
6. **Gap definition:** lip to knuckle (used here) versus FIM "jump zone" versus unspecified 23 m at KOTW [FIM], [KOTW].
7. **Height in the air:** 25 to 30 ft [KN1], up to 30 ft [CP], up to 40 ft [CPR]. Physics gives 29 to 32 ft.
8. **Bike weight and travel:** 106 kg wet [MCOM] versus 107 kg kerb [HAU] versus 102 kg (EU "dry"); rear travel 307.3 mm [MCOM] versus 308 mm [HAU].
9. **Whip direction words:** "whip right" is ambiguous; Bernard's "bike out towards the right, while I lean towards the left" [MB] matches Damien's clips. Bar direction at the peak is unresolved (4.3).
10. **Peak timing:** Damien peaks early (0.3 to 0.5 s) [WA]; Townley at the top of the flight [BT].
11. **Throttle at the lip:** steady [BT], [LEE2] versus a short blip for lift [LEE2 Tip A] versus pushing into the face for rebound [PIN].
12. **Gyro and brake physics:** riders agree on the effect (brake drops the nose, throttle lifts it, revs help the return) [LEE1], [BT], [MB]; forum posters dispute the explanation [VRB].
13. **Judging:** judges versus fan vote at X Games [XG], [RX13]; "as twisted as humanly possible" [RB] versus "less is more" [TMW].

## 7. Unknowns and gaps

- No commercial spec sheet with lip angle, radius, width and frame details for a named steel FMX ramp. No European builder identified.
- Deck width: one listing only. Anchoring: no source at all.
- No published downslope angle, length or width for a 75 ft FMX landing; section 2.3 is physics-derived. KOTW landing downslope unseen.
- No measured takeoff speed or airtime for a 75 ft FMX jump; no FMX CdA; no FMX suspension spring or valving data.
- No biomechanics study of the FMX whip; angles in 4.5 are estimates pending camera matching.
- CoM location of bike plus standing rider and the pitch inertia are estimates.
- Bar direction at Damien's peak, and whether the 75 ft / 23 m is measured to the knuckle.

## 8. Sources

- [FIM] FIM International FreeStyle Motocross Appendix and World Championship Regulations 2017 (read in full from the PDF): https://www.fim-moto.com/fileadmin/library/FreeStyle.En.pdf
- [DR6] Destruction Ramps 6' FMX ramp plans: https://www.destructionramps.com/6-fmx-ramp
- [DR83] Destruction Ramps 8'3'' comp ramp plans: https://www.destructionramps.com/8-3-fmx-ramp
- [DR8m] Destruction Ramps 8 m and 9.1 m ramp plans: https://www.destructionramps.com/8m-9-1m-fmx-ramp
- [DR9] Destruction Ramps 9' super kicker plans: https://www.destructionramps.com/9-super-kicker-fmx-ramp
- [DRJ] Destruction Ramps, how to build dirt jumps: https://www.destructionramps.com/how-to-build-dirt-jumps
- [CP] T. Pedro, Design and Cost Analysis of an ATV Freestyle Motocross Ramp, Cal Poly (excerpt; site blocks direct fetch): https://digitalcommons.calpoly.edu/cgi/viewcontent.cgi?article=1051&context=braesp
- [FS] FMXSchool ramp plans: https://www.fmxschool.com/rampplansforsale.htm
- [FS2] FMXSchool ramp plans page 2: https://www.fmxschool.com/fmx_ramp_plans.htm
- [ARD] Australian Ramp Design FMX products: https://www.ard.com.au/fmx
- [FN] Fullnoise, NSW FMX Cup entries (excerpt): https://www.fullnoise.com.au/fullnoise-news/entries-now-open-for-xsport-games-nsw-fmx-cup/
- [KAOS] FMX Kaos custom ramps: http://www.fmxkaos.com.au/new-index
- [MOTUL] Motul, FMX Kaos story (excerpt): https://powersport.motul.com/stories/read/1915-fmx-kaos-anyone-who-wants-to-jump-ramps-are-a-bit-crazy
- [WES] Red Bull, Nate Wessel profile (excerpt): https://www.redbull.com/us-en/ramp-build-genius-nate-wessel
- [VPAS] Vital MX, Travis Pastrana interview (excerpt): https://www.vitalmx.com/features/Travis-Pastrana,5720
- [RXT] Racer X, Red Bull X-Fighters Texas, creating an FMX playground: https://racerxonline.com/2008/06/12/red-bull-x-fighters-texas-creating-an-fmx-playground
- [RXR] Racer X, Renner quarterpipe record: https://racerxonline.com/2008/07/01/motorcycle-highest-air-world-record
- [WIKI] Wikipedia, Freestyle motocross: https://en.wikipedia.org/wiki/Freestyle_motocross
- [PV] Peter Verdone, Jump Ramps and Kickers: https://www.peterverdone.com/jump-ramps-and-kickers/
- [MXD] mxdose, Josh Sheehan triple backflip preview: https://mxdose.com/?p=22817
- [MET] Mike Metzger press release, Road Racing World (excerpt): https://roadracingworld.com/?p=60653
- [FB] Facebook Marketplace FMX ramp listing (excerpt): https://www.facebook.com/marketplace/item/230439129979361/
- [SCR] Scribd, FMX Ramps (excerpt): https://www.scribd.com/document/65050827/FMX-Ramps
- [VFR] Vital MX forum, FMX ramps, what type of ramp do I own (excerpt): https://www.vitalmx.com/forums/Moto-Related,20/FMX-ramps-What-type-of-ramp-do-i-own,1344555
- [GNAR] Gnarfactory portable moto jump ramp (excerpt): https://livethegnar.com/products/portable-moto-jump-ramp
- [KN1] K&N, Destin Cantrell (excerpt): https://knfilters.com/blog/fmx-rider-destin-cantrell-soars-to-heights-that-most-people-can-only-imagine
- [CPR] Chicago Pneumatic, FreestyleMX tour: https://tools.cp.com/en/news-events/company-news/freestylemx
- [HW] Hot Wheels Monster Trucks Live (excerpt): https://hotwheelsstuntshow.com/?p=421
- [NIT] Nitro Circus event listing (excerpt): https://ediblerenotahoe.com/event/nitro-circus/
- [HAU] Honda Australia CRF250R specifications: https://motorcycles.honda.com.au/models/offroad/competition/crf250r/specifications
- [MCOM] Motorcycle.com, 2026 Honda CRF250R specs: https://www.motorcycle.com/specs/honda/off-road/2026/crf/250r/detail.html
- [SAG] Honda CRF250R owner's manual, rear suspension race sag (excerpt): https://www.manualslib.com/manual/784204/Honda-Crf250r.html?page=116
- [WAR] University of Warwick, effect of rider position on energy consumption (excerpt): https://wrap.warwick.ac.uk/180779/1/WRAP-Effect-rider-position-energy-consumption-23.pdf
- [BT] Transmoto, How-To: Whip with Ben Townley: https://transmoto.com.au/whip-w-ben-townley/
- [MB] Dirt Action, Matt Bernard, How to whip your motocross bike (07/12/2022): https://www.dirtaction.com.au/?p=40171
- [BF] BikeRadar, How to whip like Brendan Fairclough: https://www.bikeradar.com/features/how-to-whip-like-brendan-fairclough
- [OMX] OMX Graphics, Just whip it: https://omxgraphics.com/blog/just-whip-it-how-to-whip-a-dirt-bike/
- [PIN] Racer X, Motocross 101 (David Pingree): https://digital.racerxonline.com/issue/january-2020wv/motocross-101/
- [JKW] Jeff Kendall-Weed, front or rear wheel first: https://jeffkendallweed.com/how-to-land-jumps-front-wheel-or-rear-wheel-first/
- [LEE1] Lee McCormack, using brakes in mid air: https://www.leelikesbikes.com/?p=262
- [LEE2] Lee McCormack, moto riding for an MTBer part 1: https://leelikesbikes.com/moto-riding-for-an-mtber-part-1.html
- [VRB] Vital MX, tapping rear brake in mid air (excerpt): https://www.vitalmx.com/comment/2069204
- [SHE] Transmoto, Bike Dissected: Sheeny's FMX machine: https://transmoto.com.au/?p=47989
- [RB] Red Bull FMX trick list: https://www.redbull.com/gb-en/fmx-trick-list-dictionary
- [XG] X Games Moto X Best Whip (excerpt): https://www.xgames.com/events/x-games-california-2023/competitions/moto-x-best-whip
- [XGV] Visit Ventura, X Games Ventura 2024 Best Whip: https://visitventuraca.com/event/x-games-ventura-2024-moto-x-best-whip/
- [RX13] Racer X, X Games Best Whip 2013: https://racerxonline.com/2013/08/02/x-games-best-whip-freestyle
- [RXD] Racer X, Dirt Shark Biggest Whip: https://racerxonline.com/2013/09/11/dirt-shark-biggest-whip-at-mec
- [TMW] Transmoto, Who really has the best whip?: https://transmoto.com.au/?p=24143
- [CW] Crankworx Whip-Off championships (excerpt): https://www.crankworx.com/whistler/events/whip-off-championships/
- [OST] Ostermeier, Sindinger, Marschall, IMU-based assessment of rider kinematics in motocross, a pilot study (AHFE): https://openaccess.cms-conferences.org/publications/book/978-1-964867-35-9/article/978-1-964867-35-9_222
- [WA] Project file `research/whip-analysis-user-clips.md` (Damien's clips)
- [KOTW] Project file `research/kotw-2025.md`
- Gear ratios and tyre diameters: project file `research/crf250r-2026.md`

Calculation scripts (scratch, not in the repo): RK4 CoM integration with tyre-circle contact against the landing profile; inputs exactly as in 3.1.
