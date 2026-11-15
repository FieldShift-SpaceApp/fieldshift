# Field measurements

> **SI-assisted:** written with Claude Code (Anthropic); human review pending. See [`SI-USAGE.md`](../../../SI-USAGE.md).

| File | What | Rows today |
|---|---|---|
| `cruz_alta.csv` | Public rope transects from Cruz Alta (RS), satellite value already looked up | **0**: nobody has measured a Cruz Alta field yet. The slot is empty on purpose; no value is invented |

The 19 Embrapa fields (Cambé, PR) that form the prior are not copied here: they are read from `../../residue-landsat/embrapa.py` (Table 2 of Documentos 454, transcribed with citation).

## Public format (`cruz_alta.csv`)

`id, date, method, points_total, points_straw, points_bare, points_green, pct_straw, winter_crop, ndti, ndvi, scene, days_from_scene`

- `id`: a neutral label (`CA-001`), never the farm, the owner or the CAR code.
- `method`: `rope` (15 m, 100 marks) or `photo` (10 × 10 grid on a vertical photo).
- `pct_straw` = 100 × `points_straw` / (`points_straw` + `points_bare` + `points_green`).
- `ndti`, `ndvi`, `scene`, `days_from_scene` are written by `fetch_pixel.py` (`days_from_scene` = scene date minus measurement date).
- **No coordinates.** `calibrate.py` refuses a public file with `lat`/`lon` columns.

## Private input (never committed)

`fetch_pixel.py` reads a private CSV with `id, lat, lon, date, points_straw, points_bare, points_green, winter_crop` (or `pct_straw`), kept outside the repository (for example in `~/.cache/fieldshift/field-calibration/`). It is the file the `/calibrate` app screen exports. Add a row here only with the consent of the person who measured, and keep photos of people out.
