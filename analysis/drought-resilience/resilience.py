# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Pre-registered drought-sensitivity test (see README.md, "Pre-registered method").

    python -I resilience.py <results_dir>

Reads soy_yield.csv, djf_power.csv and djf_ana_2853015.csv written by fetch_sources.py and writes
resilience.json, municipality_slopes.csv, robustness.csv and panel.csv to <results_dir>.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1])
FIRST, LAST = 1982, 2025
CUT = 1995
B2_START = 2005
DRAWS = 10_000
SEED = 20261115
LOESS_SPAN = 0.5
DROP = [2005, 2012, 2022, 2023]
CRUZ_ALTA = "4306106"


def read(name: str) -> list[dict]:
    with (OUT / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def loess(x: np.ndarray, y: np.ndarray, span: float) -> np.ndarray:
    """Local linear fit with tricube weights; span = share of points in each window."""
    k = max(3, math.ceil(span * len(x)))
    fit = np.empty_like(y)
    for i, x0 in enumerate(x):
        d = np.abs(x - x0)
        h = np.sort(d)[k - 1] * 1.000001
        w = np.clip(1 - (d / h) ** 3, 0, None) ** 3
        sw = np.sqrt(w)
        a = np.vstack([np.ones_like(x), x - x0]).T * sw[:, None]
        fit[i] = np.linalg.lstsq(a, y * sw, rcond=None)[0][0]
    return fit


def zscore(v: dict[int, float]) -> dict[int, float]:
    a = np.array(list(v.values()))
    m, s = a.mean(), a.std(ddof=1)
    return {k: (x - m) / s for k, x in v.items()}


# --- build the panel --------------------------------------------------------------------------------
def build_panel() -> list[dict]:
    ylds: dict[str, dict[int, float]] = defaultdict(dict)
    names: dict[str, str] = {}
    for r in read("soy_yield.csv"):
        y = int(r["harvest_year"])
        names[r["ibge_code"]] = r["municipality"]
        if FIRST <= y <= LAST and r["yield_kg_ha"]:
            ylds[r["ibge_code"]][y] = float(r["yield_kg_ha"])
    rain: dict[str, dict[int, float]] = defaultdict(dict)
    dry: dict[str, dict[int, float]] = defaultdict(dict)
    hot: dict[str, dict[int, str]] = defaultdict(dict)
    for r in read("djf_power.csv"):
        c, y = r["ibge_code"], int(r["harvest_year"])
        rain[c][y] = float(r["djf_rain_mm"])
        dry[c][y] = float(r["djf_longest_dry_days"])
        hot[c][y] = r["djf_hot_days"]
    rows = []
    for c, yv in ylds.items():
        years = np.array(sorted(yv), dtype=float)
        vals = np.array([yv[int(t)] for t in years])
        lin = np.polyval(np.polyfit(years, vals, 1), years)
        lo = loess(years, vals, LOESS_SPAN)
        zr = zscore(rain[c])
        zd = {k: -v for k, v in zscore(dry[c]).items()}  # negative = longer dry spell = drier
        for t, v, tl, tlo in zip(years.astype(int), vals, lin, lo, strict=True):
            if t not in zr:
                continue
            rows.append(
                {
                    "ibge_code": c,
                    "municipality": names[c],
                    "harvest_year": int(t),
                    "yield_kg_ha": v,
                    "trend_linear": round(float(tl), 1),
                    "trend_loess": round(float(tlo), 1),
                    "dev_linear": round(float(v / tl - 1), 4),
                    "dev_loess": round(float(v / tlo - 1), 4),
                    "djf_rain_mm": rain[c][t],
                    "z_rain": round(zr[t], 4),
                    "djf_longest_dry_days": dry[c][t],
                    "z_dry": round(zd[t], 4),
                    "djf_hot_days": hot[c][t],
                }
            )
    return rows


# --- statistics by year -----------------------------------------------------------------------------
def year_stats(rows: list[dict], dev: str, z: str, years: list[int]) -> np.ndarray:
    """Sufficient statistics per year: n, Sx, Sy, Sxx, Sxy, Syy (rows of the same year pooled)."""
    s = np.zeros((len(years), 6))
    idx = {y: i for i, y in enumerate(years)}
    for r in rows:
        i = idx.get(r["harvest_year"])
        if i is None:
            continue
        x, y = r[z], r[dev]
        s[i] += (1, x, y, x * x, x * y, y * y)
    return s


def slope_r(tot: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n, sx, sy, sxx, sxy, syy = (tot[..., k] for k in range(6))
    vx, vy, cxy = n * sxx - sx**2, n * syy - sy**2, n * sxy - sx * sy
    return cxy / vx, cxy / np.sqrt(vx * vy)


def test(rows: list[dict], dev: str, z: str, a_years: list[int], b_years: list[int], seed: int = SEED) -> dict:
    a_years = [y for y in a_years if any(r["harvest_year"] == y for r in rows)]
    b_years = [y for y in b_years if any(r["harvest_year"] == y for r in rows)]
    sa, sb = year_stats(rows, dev, z, a_years), year_stats(rows, dev, z, b_years)
    ka, ra = slope_r(sa.sum(0))
    kb, rb = slope_r(sb.sum(0))
    rng = np.random.default_rng(seed)
    # bootstrap by year, within each period
    wa = np.apply_along_axis(np.bincount, 1, rng.integers(0, len(a_years), (DRAWS, len(a_years))), None, len(a_years))
    wb = np.apply_along_axis(np.bincount, 1, rng.integers(0, len(b_years), (DRAWS, len(b_years))), None, len(b_years))
    ba, _ = slope_r(wa @ sa)
    bb, _ = slope_r(wb @ sb)
    # permutation by year between the two periods
    allst = np.vstack([sa, sb])
    na = len(a_years)
    perm = np.argsort(rng.random((DRAWS, len(allst))), axis=1)
    ma = np.zeros((DRAWS, len(allst)))
    np.put_along_axis(ma, perm[:, :na], 1.0, axis=1)
    pa, _ = slope_r(ma @ allst)
    pb, _ = slope_r((1 - ma) @ allst)
    d_obs = kb - ka
    d_perm = pb - pa
    ok = np.isfinite(d_perm)
    p = float((np.sum(np.abs(d_perm[ok]) >= abs(d_obs) - 1e-12) + 1) / (ok.sum() + 1))
    p_less = float((np.sum(d_perm[ok] <= d_obs + 1e-12) + 1) / (ok.sum() + 1))

    def ci(v: np.ndarray) -> list[float]:
        v = v[np.isfinite(v)]
        return [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]

    return {
        "years_a": [a_years[0], a_years[-1], len(a_years)],
        "years_b": [b_years[0], b_years[-1], len(b_years)],
        "n_obs_a": int(sa[:, 0].sum()),
        "n_obs_b": int(sb[:, 0].sum()),
        "slope_a": round(float(ka), 4),
        "slope_a_ci95": ci(ba),
        "r_a": round(float(ra), 3),
        "slope_b": round(float(kb), 4),
        "slope_b_ci95": ci(bb),
        "r_b": round(float(rb), 3),
        "delta": round(float(d_obs), 4),
        "delta_ci95": ci(bb - ba),
        "p_two_sided_perm_by_year": round(p, 4),
        "p_one_sided_less_perm_by_year": round(p_less, 4),
    }


def yrs(a: int, b: int, drop: list[int] | None = None) -> list[int]:
    return [y for y in range(a, b + 1) if y not in (drop or [])]


def regional(rows: list[dict], dev: str, z: str) -> list[dict]:
    by = defaultdict(list)
    for r in rows:
        by[r["harvest_year"]].append(r)
    return [
        {"harvest_year": y, dev: float(np.mean([r[dev] for r in v])), z: float(np.mean([r[z] for r in v]))}
        for y, v in sorted(by.items())
    ]


def main() -> None:
    panel = build_panel()
    A, B, B2 = yrs(FIRST, CUT - 1), yrs(CUT, LAST), yrs(B2_START, LAST)
    base = test(panel, "dev_linear", "z_rain", A, B)
    out: dict = {
        "pre_registered": "README.md, section 'Pre-registered method' (commit before any result)",
        "unit_of_inference": "harvest year (municipalities of a year resampled/permuted together)",
        "draws": DRAWS,
        "seed": SEED,
        "primary": base,
        "primary_b_prime_2005_2025": test(panel, "dev_linear", "z_rain", A, B2),
    }

    rob = [("primary: linear detrend, z_rain, A 1982-1994 vs B 1995-2025", base)]
    for cut in range(1993, 1999):
        rob.append((f"cut year {cut}", test(panel, "dev_linear", "z_rain", yrs(FIRST, cut - 1), yrs(cut, LAST))))
    for d in DROP:
        rob.append((f"without {d}", test(panel, "dev_linear", "z_rain", yrs(FIRST, CUT - 1, [d]), yrs(CUT, LAST, [d]))))
    rob.append(
        (
            "without 2005, 2012, 2022, 2023",
            test(panel, "dev_linear", "z_rain", yrs(FIRST, CUT - 1, DROP), yrs(CUT, LAST, DROP)),
        )
    )
    rob.append(("LOESS detrend (span 0.5)", test(panel, "dev_loess", "z_rain", A, B)))
    rob.append(("longest dry spell (z_dry) instead of rain", test(panel, "dev_linear", "z_dry", A, B)))
    rob.append(("B' = 2005-2025", out["primary_b_prime_2005_2025"]))
    rob.append(
        (
            "regional means (one point per year)",
            test(regional(panel, "dev_linear", "z_rain"), "dev_linear", "z_rain", A, B),
        )
    )
    ca = [r for r in panel if r["ibge_code"] == CRUZ_ALTA]
    rob.append(("Cruz Alta alone, POWER", test(ca, "dev_linear", "z_rain", A, B)))
    ana = {int(r["harvest_year"]): float(r["djf_rain_mm"]) for r in read("djf_ana_2853015.csv")}
    za = zscore(ana)
    ca_ana = [{**r, "z_rain": za[r["harvest_year"]]} for r in ca if r["harvest_year"] in za]
    rob.append(("Cruz Alta alone, ANA gauge 2853015", test(ca_ana, "dev_linear", "z_rain", A, B)))
    pw = {r["harvest_year"]: r["djf_rain_mm"] for r in ca}
    common = sorted(set(pw) & set(ana))
    out["power_vs_ana_cruz_alta"] = {
        "years": len(common),
        "r_djf_rain": round(float(np.corrcoef([pw[y] for y in common], [ana[y] for y in common])[0, 1]), 3),
        "ana_years_missing": [y for y in range(FIRST, LAST + 1) if y not in ana],
    }
    out["robustness"] = [{"variant": k, **v} for k, v in rob]
    cut_drop = [v for k, v in rob if k.startswith(("cut year", "without"))]
    out["decision"] = {
        "delta_negative": base["delta"] < 0,
        "ci_excludes_zero": base["delta_ci95"][1] < 0 or base["delta_ci95"][0] > 0,
        "perm_p_below_0_05": base["p_two_sided_perm_by_year"] < 0.05,
        "sign_kept_in_all_cut_and_drop_variants": all(np.sign(v["delta"]) == np.sign(base["delta"]) for v in cut_drop),
    }
    d = out["decision"]
    out["decision"]["verdict"] = (
        "supported"
        if d["delta_negative"]
        and d["ci_excludes_zero"]
        and d["perm_p_below_0_05"]
        and d["sign_kept_in_all_cut_and_drop_variants"]
        else "not supported"
    )

    # spatial replication (descriptive)
    ms = []
    for c in sorted({r["ibge_code"] for r in panel}):
        rr = [r for r in panel if r["ibge_code"] == c]
        na = sum(FIRST <= r["harvest_year"] < CUT for r in rr)
        if na < 10:
            continue
        sa, _ = slope_r(year_stats(rr, "dev_linear", "z_rain", A).sum(0))
        sb, _ = slope_r(year_stats(rr, "dev_linear", "z_rain", B).sum(0))
        ms.append(
            {
                "ibge_code": c,
                "municipality": rr[0]["municipality"],
                "harvests_a": na,
                "harvests_b": sum(r["harvest_year"] >= CUT for r in rr),
                "slope_a": round(float(sa), 4),
                "slope_b": round(float(sb), 4),
                "delta": round(float(sb - sa), 4),
            }
        )
    out["municipalities"] = {
        "with_10_or_more_harvests_in_a": len(ms),
        "slope_b_lower_than_a": sum(m["delta"] < 0 for m in ms),
        "median_delta": round(float(np.median([m["delta"] for m in ms])), 4),
        "note": "descriptive; municipalities share the same summers and several share one POWER grid cell",
        "distinct_power_cells": len({r["djf_rain_mm"] for r in panel if r["harvest_year"] == 2012}),
    }

    # descriptive context (not tests)
    reg = regional(panel, "dev_linear", "z_rain")
    reg_d = {r["harvest_year"]: r for r in regional(panel, "dev_linear", "z_dry")}

    def per(a: int, b: int) -> dict:
        sel = [r for r in reg if a <= r["harvest_year"] <= b]
        dry_years = [r for r in sel if r["z_rain"] <= -1]
        pan = [r for r in panel if a <= r["harvest_year"] <= b]
        hot = [float(r["djf_hot_days"]) for r in pan if r["djf_hot_days"] != ""]
        return {
            "harvests": len(sel),
            "sd_dev_linear_regional": round(float(np.std([r["dev_linear"] for r in sel], ddof=1)), 4),
            "sd_z_rain_regional": round(float(np.std([r["z_rain"] for r in sel], ddof=1)), 3),
            "mean_z_rain_regional": round(float(np.mean([r["z_rain"] for r in sel])), 3),
            "mean_z_dry_regional": round(float(np.mean([reg_d[r["harvest_year"]]["z_dry"] for r in sel])), 3),
            "post_hoc_dry_years_z_rain_le_minus_1": [
                {"year": r["harvest_year"], "z_rain": round(r["z_rain"], 2), "dev_linear": round(r["dev_linear"], 3)}
                for r in dry_years
            ],
            "post_hoc_mean_dev_in_dry_years": round(float(np.mean([r["dev_linear"] for r in dry_years])), 3)
            if dry_years
            else None,
            "mean_djf_hot_days_power_descriptive": round(float(np.mean(hot)), 1) if hot else None,
            "mean_yield_kg_ha_all_municipalities": round(float(np.mean([r["yield_kg_ha"] for r in pan])), 0),
        }

    out["context_by_period"] = {
        "A_1982_1994": per(FIRST, CUT - 1),
        "B_1995_2025": per(CUT, LAST),
        "B_prime_2005_2025": per(B2_START, LAST),
    }
    area = defaultdict(dict)
    for r in read("soy_yield.csv"):
        if r["planted_ha"]:
            area[int(r["harvest_year"])][r["ibge_code"]] = float(r["planted_ha"])
    out["soy_planted_area_ha_18_municipalities"] = {
        str(y): round(sum(area[y].values()))
        for y in (1985, 1990, 1994, 2000, 2005, 2010, 2015, 2020, 2025)
        if y in area
    }

    keys = [
        "variant",
        "years_a",
        "years_b",
        "n_obs_a",
        "n_obs_b",
        "slope_a",
        "slope_a_ci95",
        "r_a",
        "slope_b",
        "slope_b_ci95",
        "r_b",
        "delta",
        "delta_ci95",
        "p_two_sided_perm_by_year",
        "p_one_sided_less_perm_by_year",
    ]
    with (OUT / "robustness.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(keys)
        for r in out["robustness"]:
            w.writerow(
                [
                    "-".join(map(str, r[k][:2]))
                    if k.startswith("years")
                    else (" to ".join(map(str, r[k])) if isinstance(r[k], list) else r[k])
                    for k in keys
                ]
            )
    for name, rows in (("municipality_slopes.csv", ms), ("panel.csv", panel)):
        with (OUT / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    (OUT / "resilience.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"primary": base, "decision": out["decision"]}, indent=1))
    for r in out["robustness"]:
        print(
            f"{r['variant'][:48]:48s} A {r['slope_a']:+.3f} B {r['slope_b']:+.3f} d {r['delta']:+.3f} "
            f"{r['delta_ci95']} p {r['p_two_sided_perm_by_year']}"
        )


if __name__ == "__main__":
    main()
