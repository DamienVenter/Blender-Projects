---
name: oem-reference-sourcing
description: Where to get official specs, high-resolution studio photos and parts diagrams (microfiche) for a production motorcycle, and which sites work from the build server. Use before researching any real vehicle to model (Honda CRF250R first).
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

## Lessons
- Specs can differ by market for the same model year (CRF250R rake: 27.6° US vs 28°24' Europe/Australia). Always ask for the owner's market or VIN.
- Model-year naming differs by region (Europe skipped "26YM" for the CRF250R). Check that press photos match the target year: compare images numerically (resize, mean absolute difference) rather than by eye.
- Do not use next-year imagery (the 2027 CRF250R has a new livery and a longer muffler).
- Press studio photos have perspective. Use them for shapes and graphics, never for direct scaling.
- Save downloads into the project `reference/` folder with descriptive names and the source id and resolution in the filename. Downscale very large detail shots (8192 px) to 4096 px to keep LFS lean, and record the original URL.
