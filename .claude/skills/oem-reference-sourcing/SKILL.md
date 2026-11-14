---
name: oem-reference-sourcing
description: Where to get official specs, high-resolution studio photos and parts diagrams (microfiche) for a production motorcycle or the rider's gear (Leatt), and which sites work from the build server. Use before researching any real vehicle to model (Honda CRF250R first).
---

# Sourcing OEM references for a vehicle model

Learned while researching the 2026 Honda CRF250R (see `motocross-whip/research/crf250r-2026.md`).

## What works from the build server
- **hondanews.eu (Honda Motor Europe press)**: press kits with full technical specs, and full-size photos are public.
  - Photo: `https://hondanews.eu/image/motorcycles/high/<id>/1_1/5?v=2` (studio shots 4000x2250, location shots 8192x5464). `low` = 1350 px preview, `thumb` = small.
  - A press release's image list loads by POST to `/eu/en/motorcycles/medialist/loadmediatypepage` with `pagenumber`, `mediaTypeId=1` and the hidden `params` value from `/eu/en/motorcycles/Media/Related?mediaId=<releaseId>`.
- **hondanews.com (American Honda)**: spec and feature releases per model year are public text. Full-size photo downloads need a media login; 928 px previews are public at `https://wieck-honda-production.s3.amazonaws.com/photos/<id>/preview-928x522.jpg`.
- **Honda NZ parts catalogue**: official fiche with part numbers. `https://www.hondamotorbikes.co.nz/parts/search/model/<code>-<model><suffix>-<year>`, e.g. `k95cf3900-crf250rt-2026` (frame body). Frame sections `k95cfNN00`, engine `k95ceNN00`. Diagram PNG (768x384): `https://images.bwhonda.co.nz/part_diagrams/<CODE>.png`. Wheel sections were not found there.
- Honda South Africa (`cdn.honda.co.za` spec-sheet PDFs) and Honda Australia spec pages are public.
- Official owner's manuals sometimes sit on national Honda sites as PDFs (e.g. motos.honda.es). The spec pages list dimensions per market type (ED, U, GS, LA, MX) and footpeg height.
- Dirt Rider (Arc Publishing) pages embed the article, spec table and original image URLs in page JSON; curl the page and grep `originalUrl`.

## What is blocked (403, 502 or captcha)
powersports.honda.com, RevZilla, Partzilla, CMSNL, BikeBandit, Babbitts / hondapartshouse, Ron Ayers, bike-parts-honda.com, manuals.dk. Use web search snippets for their URLs and ask Damien to open them in a browser if a diagram is essential.

## Riding gear (Leatt), learned 2026-11-12 (see `motocross-whip/research/rider-gear-leatt.md`)
- **us.leatt.com is Shopify and works** (leatt.com and the `za` site redirect to it; `eu`, `uk`, `au` are unreachable,
  www.leatt.co.za resets). `https://us.leatt.com/products/<handle>.js` gives every variant (SKU, EAN, colour, size),
  every image URL (originals 1920 px on cdn.shopify.com) and the description; the HTML page holds the Features list and
  a Size Guide image (`size-chart-content`). Find handles with
  `curl -g 'https://us.leatt.com/search/suggest.json?q=<words>&resources[type]=product&resources[limit]=10'`;
  `/collections/<name>/products.json?limit=250` lists only the current model year. Last year's items move to
  `...-sale-my26` style handles (tag "MY26 Obsolete") and may vanish: save images early.
- **Leatt's NZ distributor feed** (retailer Shopify stores with `ran_<code>` handles, e.g. forzahub.nz,
  motosouth.co.nz): `/products/ran_<code>.js` lists Leatt's full photo set as `LE<SKU>_<n>.jpg` (1600 px), often more
  views (model shots, details) than Leatt US. Some of them duplicate Leatt US shots: keep Leatt's 1920 px copy.
- Leatt SKUs are 10 digits: first = category (1 helmet, 3 boot, 5 apparel, 6 glove, 8 eyewear), next three = the
  design's year code (026 for the 2026 range; carried-over designs keep an older code), last = size index.
- Colour names differ: Leatt file names ("PinataTeal"), variants ("Pinata"), retailers ("Pinata Teal"). Leatt's kit
  photo shoots style each jersey colourway with a helmet and goggle: the quickest way to identify the helmet a rider
  pairs with a kit.
- Product renders can be off in colour (Velocity goggle frame: hot pink render, raspberry in photos): take colours
  from photographs.
- RevZilla, Rocky Mountain ATV/MC (empty to WebFetch) and the Enduro21 article (404) did not load; search snippets did.
- **Leatt's goggle images (2026-11-13)**: the ISO renders share one camera per model line (every Velocity 5.5 MY26
  ISO, file numbers 39274 to 39282; the 4.5 ISOs 39260 to 39268 another, more frontal), so a white colourway at
  the same camera shows the facets a dark one hides. The older "Front" PNGs (2022 to 2025 colourways, transparent)
  are studio photographs of the real goggle, each at its own angle: more views for free. The 4.5 shares the 5.5's
  front frame (no outriggers); the 6.5 has another nose part. Every goggle-alone view is from the right side: no
  left, top, bottom or square front. YouTube frames cannot be fetched from the build server (media requests need a
  browser token) and retailers reuse Leatt's images.

## Lessons
- Specs can differ by market for the same model year (CRF250R rake: 27.6° US vs 28°24' Europe/Australia). Always ask for the owner's market or VIN.
- Model-year naming differs by region (Europe skipped "26YM" for the CRF250R). Check that press photos match the target year: compare images numerically (resize, mean absolute difference) rather than by eye.
- Do not use next-year imagery (the 2027 CRF250R has a new livery and a longer muffler).
- Press studio photos have perspective. Use them for shapes and graphics, never for direct scaling.
- Save downloads into the project `reference/` folder with descriptive names and the source id and resolution in the filename. Downscale very large detail shots (8192 px) to 4096 px to keep LFS lean, and record the original URL.
