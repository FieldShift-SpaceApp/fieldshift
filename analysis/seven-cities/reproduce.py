# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Seven-city portability test: re-runs the anonymously reproducible part of the team's table and compares it.

Ported from FieldShift team research (scripts 52 and 53). Criteria, written by the team BEFORE running:
 C1 the water balance tracks the municipality's observed soybean yield: r(WSI, detrended log yield, IBGE PAM) >= 0.60;
 C2 "winter does not change soybean water" repeats: |water-short years with wheat - with fallow| <= 0.5 in 10;
 C3 the satellite pattern repeats (green winter: <= 1 in 10 heavy rains of Jul-Sep hit low plant cover, and Oct-Nov is more
    exposed than after a low-green winter) -- NOT re-run here (needs the team's ~1 km MODIS NDVI cubes); read from the team table;
 C4 more days >= 50 mm in Sep-Nov (IMERG) in El Niño years than in the other years. El Niño = ONI of Jun-Jul-Aug >= +0.5.

Inputs (committed): inputs/daily_imerg_power_seven_cities.csv, inputs/ibge_pam_soy_seven_cities.csv,
results/team_enso_phase_oni_jja.csv (checked against NOAA by oni_phase.py).
Output: results/reproduced_by_city.csv, and a comparison with results/team_criteria_by_city.csv / team_summary_by_city.csv.
Run: uv run --no-project --with pandas --with numpy python reproduce.py
"""

import os

import numpy as np
import pandas as pd

from water_balance import SEQUENCES, et0_penman_monteith, run_sequence

HERE = os.path.dirname(os.path.abspath(__file__))
CITIES = {
    "4306106": "Cruz Alta",
    "4310207": "Ijuí",
    "4311155": "Jóia",
    "4319158": "São Miguel das Missões",
    "4318903": "São Luiz Gonzaga",
    "4307500": "Espumoso",
    "4311205": "Júlio de Castilhos",
}


def main() -> None:
    daily = pd.read_csv(os.path.join(HERE, "inputs", "daily_imerg_power_seven_cities.csv"), parse_dates=["date"])
    pam = pd.read_csv(os.path.join(HERE, "inputs", "ibge_pam_soy_seven_cities.csv"), dtype={"ibge_code": str})
    enso = pd.read_csv(os.path.join(HERE, "results", "team_enso_phase_oni_jja.csv")).set_index("year")
    el_nino = enso.phase_jja == "El Niño"
    rows = []
    for code, name in CITIES.items():
        ca = pam[pam.ibge_code == code].set_index("harvest_year").sort_index()
        lat = round(float(ca.lat.iloc[0]), 2)
        d = daily[daily.municipality == name].set_index("date").sort_index().copy()
        d["et0"] = d.apply(et0_penman_monteith, axis=1, lat=lat)
        wsi = {k: run_sequence(d, seq) for k, seq in SEQUENCES.items()}
        short = {k: round(10 * float((v < 0.7).mean()), 1) for k, v in wsi.items()}
        # C1: correlation of the fallow-soybean WSI with the linearly detrended log yield
        t = np.arange(len(ca))
        ly = np.log(ca.soy_yield_kg_ha)
        res = ly - np.polyval(np.polyfit(t, ly, 1), t)
        x = wsi["soy after winter fallow"]
        j = x.index.intersection(res.index)
        r = float(np.corrcoef(x[j], res[j])[0, 1])
        # C4: days >= 50 mm in Sep-Nov per calendar year, El Niño vs other years
        rain = d.imerg_precip_mm
        son = rain[rain.index.month.isin([9, 10, 11])]
        c50 = (son >= 50).groupby(son.index.year).sum().reindex(enso.index)
        years = [y for y in x.index if 2002 <= y <= 2025]
        djf = pd.Series({y: rain.loc[f"{y - 1}-12-01" : f"{y}-02-28"].sum() for y in years})
        last5 = ca.loc[2021:2025]
        o = dict(
            municipality=name,
            lat=lat,
            annual_rain_mm=round(float(rain.sum() / 25)),
            dec_feb_rain_mm=round(float(djf.mean())),
            soy_thousand_ha_2021_2025=round(float(last5.soy_planted_ha.mean()) / 1000),
            soy_yield_kg_ha_2021_2025=round(float(last5.soy_yield_kg_ha.mean())),
            winter_grain_area_over_soy_2021_2025=round(float(last5.winter_grain_area_over_soy.mean()), 2),
            soy_after_fallow_water_short_in_10=short["soy after winter fallow"],
            soy_after_wheat_water_short_in_10=short["soy after wheat"],
            early_maize_water_short_in_10=short["early maize after oat cover"],
            r_water_model_vs_yield=round(r, 2),
            n_seasons=len(j),
            son_days_ge50mm_el_nino=round(float(c50[el_nino].mean()), 1),
            son_days_ge50mm_other_years=round(float(c50[~el_nino].mean()), 1),
        )
        o["C1_model_tracks_yield"] = o["r_water_model_vs_yield"] >= 0.60
        o["C2_winter_does_not_change_water"] = (
            abs(o["soy_after_wheat_water_short_in_10"] - o["soy_after_fallow_water_short_in_10"]) <= 0.5
        )
        o["C4_el_nino_more_heavy_rain"] = o["son_days_ge50mm_el_nino"] > o["son_days_ge50mm_other_years"]
        rows.append(o)
        print(name, "ok", flush=True)
    rep = pd.DataFrame(rows)
    rep.to_csv(os.path.join(HERE, "results", "reproduced_by_city.csv"), index=False)

    team = pd.read_csv(os.path.join(HERE, "results", "team_criteria_by_city.csv")).set_index("municipality")
    summ = pd.read_csv(os.path.join(HERE, "results", "team_summary_by_city.csv")).set_index("municipality")
    team = team.join(summ[[c for c in summ.columns if c not in team.columns]])
    rep = rep.set_index("municipality")
    mismatches = 0
    for col in rep.columns:
        a, b = rep[col], team.loc[rep.index, col]
        same = (a == b) if a.dtype == bool or a.dtype == object else np.isclose(a.astype(float), b.astype(float))
        if not same.all():
            mismatches += 1
            print(f"MISMATCH {col}:\n", pd.DataFrame({"public run": a, "team table": b})[~same])
    c3 = team.loc[rep.index, "C3_satellite_pattern"]
    passed = rep[["C1_model_tracks_yield", "C2_winter_does_not_change_water", "C4_el_nino_more_heavy_rain"]].sum(axis=1) + c3
    print(pd.DataFrame({"criteria passed (C1, C2, C4 re-run; C3 from team table)": passed}).to_string())
    print("columns compared:", len(rep.columns), "| mismatching columns:", mismatches)


if __name__ == "__main__":
    main()
