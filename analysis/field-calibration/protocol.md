# Field protocol: measure straw cover with a 15 m rope (about 20 minutes per field)

> Portuguese version: [`protocolo.md`](protocolo.md). The rope method is the line transect used by Embrapa Soja Documentos 454 (Franchini et al. 2023, pp. 25–29, after Morrison et al. 1993). The photo, location and surface-condition steps borrow from the NASA GLOBE Observer Land Cover protocol (see "What comes from GLOBE" below). FieldShift is not part of GLOBE and has no agreement with NASA or Embrapa.

## You need

- a rope or measuring tape of **15 m**, marked **every 15 cm** (100 marks; a tape measure works: read every 15 cm);
- a phone with camera and GPS (Google Maps);
- this sheet or the app screen `/calibrate` (it counts for you and keeps everything on the phone).

## When

- **Before sowing or just after it**, when the field shows straw and soil, not a closed green canopy. Green plants hide the straw signal in the satellite (Documentos 454 masks NDVI > 0.3).
- **Dry soil.** Do not measure the day after rain: wet soil and wet straw change the satellite index. Write down if the soil is wet.
- **On or near a satellite day.** Landsat 8/9 and Sentinel-2 pass every few days; the closer to the pass, the better (the GLOBE Observer app shows the pass times; ±5 days is the useful limit, because sowing changes the cover quickly).

## Steps

1. **Pick a uniform spot** at least 50 m inside the field, away from roads, headlands and wet patches. The satellite pixel is 30 m; the area around you, about 100 m × 100 m, should look the same (the GLOBE Observer site size).
2. **Stretch the rope on the diagonal** to the crop rows (45°), straight and close to the ground.
3. **Look straight down at each of the 100 marks** and write one letter for what is under the mark:
   - **P** straw (any dead plant residue: wheat, oat, maize, soybean stubble);
   - **S** bare soil (soil or a clod visible under the mark);
   - **V** green plant (living crop or weed).
   Count only what is directly under the mark, the size of a pencil tip. Do not choose: if it touches straw, it is straw.
4. **Straw cover = P marks ÷ 100.** Example: 87 P, 9 S, 4 V → 87% straw.
5. **Repeat on 3 ropes** in different spots of the same field if you can (the calculation in the README shows why one rope is not enough near the 90% line).
6. **One vertical photo** at the centre of the rope, phone held level at chest height, pointing straight down (GLOBE's "down" photo). Optional: four photos facing north, east, south and west.
   - *Photo instead of rope:* lay a 10 × 10 grid over the vertical photo and count the 100 crossings the same way (P / S / V). It is faster but less exact than the rope; mark it as "photo".
7. **Location:** stand at the rope's centre, open Google Maps, long-press your blue dot and copy the coordinates (for example `-28.6385, -53.6063`). These stay with you and the analyst; **they are never published**.
8. **Write down:** date, what was in the field in winter (wheat, oat, ryegrass, fallow, other) and whether it was desiccated or harvested, and whether the soil was dry or wet.

## What happens with the measurement

The analyst runs `fetch_pixel.py` with your coordinates and date: it finds the NASA HLS or Landsat pixel of the closest clear day and its NDTI (the straw index). Then `calibrate.py` adds your point to the Embrapa ruler and recomputes its uncertainty. The public file keeps only date, counts, cover, winter crop and the satellite values, **never the coordinates or your name**.

## What comes from GLOBE, and what does not

| GLOBE Observer Land Cover (NASA) | Here |
|---|---|
| Six photos: north, east, south, west, up, **down** (ground cover) | **Adopted:** the down photo is required, the four sides optional; no up photo (no canopy) |
| Observe a uniform 100 m × 100 m area (50 m each way) | **Adopted** as "pick a uniform spot" |
| Record surface conditions (standing water, snow, leaves) | **Adopted** as dry / wet soil (moisture changes NDTI) |
| Show the Landsat / Sentinel-2 pass times to match the satellite | **Adopted** as "measure near a satellite day" |
| Classify each photo with the Modified UNESCO Classification (MUC) and percent sliders | **Not adopted:** we count 100 points instead of estimating by eye, because the satellite ruler needs a measured percentage |
| Submit to the GLOBE database (open data) | **Not done by FieldShift.** You can also submit the same site through the official GLOBE Observer app yourself |

Sources: GLOBE Observer, "Land Cover: taking observations", https://observer.globe.gov/do-globe-observer/land-cover/taking-observations (accessed 2026-11-15); GLOBE Land Cover Classification protocol, https://www.globe.gov/web/biosphere/protocols/land-cover-classification; Embrapa Soja Documentos 454, https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1156802/1/DOC-454.pdf.
