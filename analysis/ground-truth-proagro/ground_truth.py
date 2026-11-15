# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Year-by-year test: insured wheat area paid for EXCESS RAIN (Proagro) x Sep-Nov rain seen by NASA GPM IMERG.

    uv run --with numpy==2.5.4 python -I analysis/ground-truth-proagro/ground_truth.py \
        <results_dir> data/sites/cruz-alta/output/enso-rain-signal.json

Pre-registration (written by the team before looking at the correlation, 2026-11-14):
  primary Y   = % of the Proagro-insured wheat area of the 18 municipalities with a claim APPROVED
                ("deferida") for CHUVA EXCESSIVA (excess rain), by year of contract issue (= that winter's crop).
  primary X   = mean over the 18 municipalities of the IMERG days with >= 50 mm, Sep 1 - Nov 30.
  test        = Spearman by YEAR (n = years, never municipality-years), one-sided permutation p (rho > 0),
                200,000 draws, fixed seed.
  robustness  = leave one year out (above all 2023); Pearson; Sep-Nov total rain; approved BRL; frost as
                a negative control.
  ENSO        = NOAA operational SON phase (the same as enso-rain-signal.json).
  excluded    = 2026 (crop still under claim adjustment).
The Sep-Nov TOTAL rain is a secondary metric: it was not the pre-registered primary X. Every p-value this
script computes is reported, with Bonferroni and Holm corrections over two declared families.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

RES = Path(sys.argv[1])
SIGNAL = Path(sys.argv[2])
RNG = np.random.default_rng(20261114)
NPERM = 200_000
YEARS = list(range(2013, 2026))
EXCESS = "CHUVA EXCESSIVA"  # Proagro event label (excess rain)
FROST = "GEADA"
DROUGHT = "SECA"


def read(name: str) -> list[dict]:
    with (RES / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rank(a: np.ndarray) -> np.ndarray:
    o = np.argsort(a, kind="mergesort")
    r = np.empty(len(a))
    r[o] = np.arange(len(a))
    for v in np.unique(a):  # ties: mean rank
        m = a == v
        r[m] = r[m].mean()
    return r


def spearman(x, y) -> float:
    return float(np.corrcoef(rank(np.asarray(x, float)), rank(np.asarray(y, float)))[0, 1])


def pearson(x, y) -> float:
    return float(np.corrcoef(np.asarray(x, float), np.asarray(y, float))[0, 1])


def perm_p(x, y, stat=spearman) -> float:
    """One-sided permutation p-value (statistic >= observed)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    obs = stat(x, y)
    ry = rank(y) if stat is spearman else y
    rx = rank(x) if stat is spearman else x
    rx = (rx - rx.mean()) / rx.std()
    perms = np.array([RNG.permutation(ry) for _ in range(NPERM)])
    perms = (perms - perms.mean(1, keepdims=True)) / perms.std(1, keepdims=True)
    sims = perms @ rx / len(rx)
    return float((np.sum(sims >= obs - 1e-12) + 1) / (NPERM + 1))


def corrections(pvals: dict[str, float]) -> dict:
    """Bonferroni and Holm adjusted p-values (capped at 1) for one family of tests."""
    k = len(pvals)
    order = sorted(pvals, key=pvals.get)
    holm, running = {}, 0.0
    for i, name in enumerate(order):
        running = max(running, min(1.0, (k - i) * pvals[name]))
        holm[name] = round(running, 4)
    return {
        "k": k,
        "raw": {n: pvals[n] for n in order},
        "bonferroni": {n: round(min(1.0, k * pvals[n]), 4) for n in order},
        "holm": holm,
    }


def main() -> None:
    sig = json.loads(SIGNAL.read_text(encoding="utf-8"))
    imerg_years = [y for s in sig["sources"] if s["id"] == "gpm-imerg" for y in s["years"]]
    phase = {y["year"]: y["phase"] for y in imerg_years}
    oni = {y["year"]: y["oni"] for y in imerg_years}

    insured = defaultdict(float)
    insured_mun = defaultdict(float)
    for r in read("proagro_wheat_enrolment_by_municipality.csv"):
        insured[int(r["issue_year"])] += float(r["adesao_area_amparada_ha"])
        insured_mun[(r["ibge_code"], int(r["issue_year"]))] += float(r["adesao_area_amparada_ha"])
    area_ev = defaultdict(lambda: defaultdict(float))
    brl_ev = defaultdict(lambda: defaultdict(float))
    excess_mun = defaultdict(float)
    for r in read("proagro_wheat_claims_by_municipality_event.csv"):
        y, e = int(r["issue_year"]), r["event"]
        area_ev[y][e] += float(r["cop_deferida_area_ha"])
        brl_ev[y][e] += float(r["cop_deferida_valor_deferido"])
        if e == EXCESS:
            excess_mun[(r["ibge_code"], y)] += float(r["cop_deferida_area_ha"])
    days50 = defaultdict(list)
    total = defaultdict(list)
    days50_mun = {}
    for r in read("imerg_son_by_municipality.csv"):
        y = int(r["year"])
        days50[y].append(int(r["son_days_ge_50mm"]))
        total[y].append(float(r["son_total_mm"]))
        days50_mun[(r["ibge_code"], y)] = int(r["son_days_ge_50mm"])

    table = []
    for y in YEARS:
        all_area = sum(area_ev[y].values())
        all_brl = sum(brl_ev[y].values())
        table.append({
            "year": y, "enso_phase_son": phase[y], "oni_son": oni[y],
            "imerg_days_ge_50mm_mean18": round(float(np.mean(days50[y])), 2),
            "imerg_son_total_mean18_mm": round(float(np.mean(total[y])), 1),
            "n_municipalities_imerg": len(days50[y]),
            "insured_area_ha": round(insured[y]),
            "pct_area_paid_excess_rain": round(100 * area_ev[y][EXCESS] / insured[y], 2),
            "pct_area_paid_frost": round(100 * area_ev[y][FROST] / insured[y], 2),
            "pct_area_paid_drought": round(100 * area_ev[y][DROUGHT] / insured[y], 2),
            "pct_area_paid_all_causes": round(100 * all_area / insured[y], 2),
            "brl_approved_excess_rain_nominal": round(brl_ev[y][EXCESS]),
            "brl_approved_all_causes_nominal": round(all_brl),
            "pct_brl_excess_rain": round(100 * brl_ev[y][EXCESS] / all_brl, 1) if all_brl else 0.0,
        })  # fmt: skip
    with (RES / "table_by_year.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(table)

    x = np.array([t["imerg_days_ge_50mm_mean18"] for t in table])
    xt = np.array([t["imerg_son_total_mean18_mm"] for t in table])
    y = np.array([t["pct_area_paid_excess_rain"] for t in table])
    yv = np.array([t["brl_approved_excess_rain_nominal"] for t in table], float)
    yg = np.array([t["pct_area_paid_frost"] for t in table])
    idx = np.arange(len(YEARS))
    out: dict = {"n_years": len(YEARS), "years": YEARS, "n_permutations": NPERM, "seed": 20261114}
    # the order of the permutation calls below is fixed: it keeps the p-values reproducible to the digit
    out["primary_days50"] = {
        "spearman": round(spearman(x, y), 3), "p_perm_one_sided": round(perm_p(x, y), 4),
        "pearson": round(pearson(x, y), 3), "p_perm_pearson": round(perm_p(x, y, pearson), 4),
    }  # fmt: skip
    out["primary_leave_one_year_out_spearman"] = {
        str(a): round(spearman(x[idx != i], y[idx != i]), 3) for i, a in enumerate(YEARS)
    }
    no23 = np.array([a != 2023 for a in YEARS])
    out["primary_without_2023"] = {
        "spearman": round(spearman(x[no23], y[no23]), 3), "p_perm": round(perm_p(x[no23], y[no23]), 4),
        "pearson": round(pearson(x[no23], y[no23]), 3),
    }  # fmt: skip
    no25 = np.array([a < 2025 for a in YEARS])
    out["primary_without_2025"] = {
        "spearman": round(spearman(x[no25], y[no25]), 3),
        "p_perm": round(perm_p(x[no25], y[no25]), 4),
    }
    out["secondary_total_son"] = {"spearman": round(spearman(xt, y), 3), "p_perm": round(perm_p(xt, y), 4)}
    out["secondary_total_son_without_2023"] = {
        "spearman": round(spearman(xt[no23], y[no23]), 3),
        "p_perm": round(perm_p(xt[no23], y[no23]), 4),
    }
    out["secondary_total_son_leave_one_year_out_min"] = round(
        min(spearman(xt[idx != i], y[idx != i]) for i in range(len(YEARS))), 3
    )
    out["days50_vs_brl_excess_rain_nominal"] = {
        "spearman": round(spearman(x, yv), 3),
        "p_perm": round(perm_p(x, yv), 4),
    }
    out["control_frost_vs_days50"] = {"spearman": round(spearman(x, yg), 3)}

    # within a year, across municipalities: does the rainier pixel lose more? (secondary, no p-value)
    within = []
    for a in YEARS:
        codes = sorted({c for (c, aa) in insured_mun if aa == a and insured_mun[(c, aa)] >= 200
                        and (c, aa) in days50_mun})  # fmt: skip
        xs = np.array([days50_mun[(c, a)] for c in codes], float)
        ys = np.array([100 * excess_mun[(c, a)] / insured_mun[(c, a)] for c in codes])
        if len(codes) >= 8 and xs.std() > 0 and ys.std() > 0:
            within.append({"year": a, "n_municipalities": len(codes), "spearman": round(spearman(xs, ys), 3)})
    out["within_year_across_municipalities"] = {
        "by_year": within,
        "mean_rho": round(float(np.mean([w["spearman"] for w in within])), 3),
        "years_rho_positive": sum(w["spearman"] > 0 for w in within),
        "years_tested": len(within),
    }

    by_phase = {}
    for f_ in ("el_nino", "neutral", "la_nina"):
        sel = [t for t in table if t["enso_phase_son"] == f_]
        by_phase[f_] = {
            "years": [t["year"] for t in sel],
            "mean_pct_area_excess_rain": round(float(np.mean([t["pct_area_paid_excess_rain"] for t in sel])), 1),
            "median_pct_area_excess_rain": round(float(np.median([t["pct_area_paid_excess_rain"] for t in sel])), 1),
            "mean_pct_area_frost": round(float(np.mean([t["pct_area_paid_frost"] for t in sel])), 1),
            "mean_days50": round(float(np.mean([t["imerg_days_ge_50mm_mean18"] for t in sel])), 2),
        }
    out["by_enso_phase"] = by_phase
    # El Nino > other years: label permutation on the difference of means
    en = np.array([t["enso_phase_son"] == "el_nino" for t in table])
    obs = y[en].mean() - y[~en].mean()
    sims = []
    for _ in range(NPERM // 4):
        p = RNG.permutation(en)
        sims.append(y[p].mean() - y[~p].mean())
    out["el_nino_vs_other_years"] = {
        "diff_mean_pp": round(float(obs), 1),
        "p_perm_one_sided": round(float((np.sum(np.array(sims) >= obs) + 1) / (len(sims) + 1)), 4),
        "without_2023_diff_pp": round(float(y[en & no23].mean() - y[~en].mean()), 1),
    }

    # multiple testing: family A = the distinct full-sample tests; family B = every p-value above
    fam_a = {
        "primary_days50_spearman": out["primary_days50"]["p_perm_one_sided"],
        "primary_days50_pearson": out["primary_days50"]["p_perm_pearson"],
        "secondary_total_son_spearman": out["secondary_total_son"]["p_perm"],
        "days50_vs_brl_nominal_spearman": out["days50_vs_brl_excess_rain_nominal"]["p_perm"],
        "el_nino_vs_other_years": out["el_nino_vs_other_years"]["p_perm_one_sided"],
    }
    fam_b = {
        **fam_a,
        "primary_without_2023": out["primary_without_2023"]["p_perm"],
        "primary_without_2025": out["primary_without_2025"]["p_perm"],
        "secondary_total_son_without_2023": out["secondary_total_son_without_2023"]["p_perm"],
    }
    # approximate 95% interval of the secondary rho (Fisher z, se = 1/sqrt(n - 3)); no bootstrap
    z, se = np.arctanh(out["secondary_total_son"]["spearman"]), 1 / np.sqrt(len(YEARS) - 3)
    out["secondary_total_son"]["fisher_95ci_approx"] = [round(float(np.tanh(z - 1.96 * se)), 2),
                                                        round(float(np.tanh(z + 1.96 * se)), 2)]  # fmt: skip
    out["multiple_testing"] = {
        "family_a_full_sample_tests": corrections(fam_a),
        "family_b_every_p_value": corrections(fam_b),
    }
    (RES / "ground_truth.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for t in table:
        print(
            t["year"],
            t["enso_phase_son"],
            t["imerg_son_total_mean18_mm"],
            t["imerg_days_ge_50mm_mean18"],
            t["pct_area_paid_excess_rain"],
            t["pct_area_paid_frost"],
            t["brl_approved_excess_rain_nominal"],
        )
    print(
        json.dumps(
            {
                k: out[k]
                for k in (
                    "primary_days50",
                    "primary_without_2023",
                    "secondary_total_son",
                    "secondary_total_son_without_2023",
                    "multiple_testing",
                )
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
