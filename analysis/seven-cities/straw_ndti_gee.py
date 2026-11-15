# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Straw signal (NDTI from MODIS MCD43A4) in October, November and April, by winter state, seven municipalities.

REQUIRES A GOOGLE EARTH ENGINE ACCOUNT; NOT REPRODUCIBLE ANONYMOUSLY. The committed result is
results/team_straw_ndti_seven_cities.csv (FieldShift team research, run with this logic); straw_summary.py aggregates it.
English port of the team's script 43b: same definitions, no credentials in the code. Set EE_PROJECT to your own Cloud project.

Per municipality and winter year a (2002-2024):
- soybean mask: MapBiomas Collection 11 class 39 (soybean) in the summer a+1, aggregated to the MCD43A4 grid, share >= 0.8;
- winter state: mean MOD13Q1 NDVI of Jul-Sep: "low green" if <= 0.60, "green" if >= 0.70 (in between: excluded);
- for Oct (a), Nov (a) and Apr (a+1): monthly mean nadir reflectance; NDVI = (B2 - B1) / (B2 + B1); pixels with NDVI < 0.5
  are "low NDVI"; NDTI = (B6 - B7) / (B6 + B7) averaged over the low-NDVI pixels (higher NDTI = more crop residue).
April is the control month (after the soybean harvest, the winter state of the previous year should not matter).
Municipality boundaries: IBGE malhas API (GeoJSON of RS municipalities, property `codarea`), passed as a local file.
Run: EE_PROJECT=<project> python straw_ndti_gee.py <rs_municipalities.geojson> <out.csv>
"""

import csv
import json
import os
import sys

import ee

CITIES = {
    "4306106": "Cruz Alta",
    "4310207": "Ijuí",
    "4311155": "Jóia",
    "4319158": "São Miguel das Missões",
    "4318903": "São Luiz Gonzaga",
    "4307500": "Espumoso",
    "4311205": "Júlio de Castilhos",
}
COVERAGE = "projects/mapbiomas-public/assets/brazil/lulc/collection11/mapbiomas_brazil_collection11_coverage_v3"
HEADER = [
    "municipality",
    "winter_year",
    "month",
    "winter_state",
    "n_soy_pixels",
    "frac_ndvi_below_0_5",
    "n_pixels_ndvi_below_0_5",
    "ndti_in_low_ndvi_pixels",
    "ndvi_in_low_ndvi_pixels",
]


def main(geojson_path: str, out_path: str) -> None:
    ee.Initialize(project=os.environ["EE_PROJECT"])
    feats = json.load(open(geojson_path, encoding="utf-8"))["features"]
    cov = ee.Image(COVERAGE)
    nbar = ee.ImageCollection("MODIS/061/MCD43A4")
    vi = ee.ImageCollection("MODIS/061/MOD13Q1")
    proj = nbar.first().select(0).projection()
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        for code, name in CITIES.items():
            geom = ee.Geometry([x for x in feats if x["properties"]["codarea"] == code][0]["geometry"])
            rows = []
            for a in range(2002, 2025):
                soy = (
                    cov.select(f"classification_{a + 1}")
                    .eq(39)
                    .reduceResolution(ee.Reducer.mean(), maxPixels=1024)
                    .reproject(proj)
                    .gte(0.8)
                )
                winter = vi.filterDate(f"{a}-07-01", f"{a}-10-01").select("NDVI").mean().multiply(0.0001)
                cls = ee.Image(0).where(winter.lte(0.60), 1).where(winter.gte(0.70), 2).rename("cls")
                months = (
                    ("oct", f"{a}-10-01", f"{a}-11-01"),
                    ("nov", f"{a}-11-01", f"{a}-12-01"),
                    ("apr", f"{a + 1}-04-01", f"{a + 1}-05-01"),
                )
                for month, d0, d1 in months:
                    m = nbar.filterDate(d0, d1).mean()
                    ndvi = m.normalizedDifference(["Nadir_Reflectance_Band2", "Nadir_Reflectance_Band1"]).rename("ndvi")
                    ndti = m.normalizedDifference(["Nadir_Reflectance_Band6", "Nadir_Reflectance_Band7"]).rename("ndti")
                    low = ndvi.lt(0.5)
                    img = (
                        ee.Image.cat([ndti.updateMask(low), ndvi.updateMask(low), low.toFloat().rename("frac_low"), cls])
                        .updateMask(soy)
                        .updateMask(cls.gt(0))
                    )
                    reducer = ee.Reducer.mean().combine(ee.Reducer.count(), "", True).repeat(3).group(3, "cls")
                    r = img.reduceRegion(reducer, geom, crs=proj, scale=463.3127, maxPixels=1e9).getInfo()
                    for g in r["groups"]:
                        mm, cc = g["mean"], g["count"]
                        rows.append(
                            [
                                name,
                                a,
                                month,
                                {1: "low green", 2: "green"}[g["cls"]],
                                cc[2],
                                round(mm[2], 4) if mm[2] is not None else "",
                                cc[0],
                                round(mm[0], 4) if mm[0] is not None else "",
                                round(mm[1], 4) if mm[1] is not None else "",
                            ]
                        )
            w.writerows(rows)
            fh.flush()
            print(name, len(rows), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
