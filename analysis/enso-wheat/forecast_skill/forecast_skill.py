# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Forecast skill, step B. Do ENSO forecasts issued in Jan/Feb/Mar get the phase of the southern
winter (JJA) right?

Usage: python -I forecast_skill.py <cache_dir> <results_dir>

Truth: NOAA CPC ONI for JJA (El Nino >= +0.5; La Nina <= -0.5; neutral in between), the same rule
as the wheat analysis.

Sources (each scored separately by issue month):
- NMME (CPC, NMME/ENSO): ensemble-mean Nino-3.4 per model; anomaly against the model's own
  1991-2020 climatology per start month and lead (removes drift); mean of JUN, JUL, AUG.
  "NMME mean" = simple mean of the models available that year.
- IRI plume (fig. 4): "COMBINED AVG" (mean of all models), "DYN Average" and "NASA GMAO".
- IRI objective probability (fig. 3) and the official CPC/IRI consensus (quick look table):
  forecast phase = category with the highest probability.

Committed outputs (results_dir): forecast_skill_metrics.csv and forecast_skill.json (metrics and
the IRI/official cases). Per-forecast values, NMME included, go to <cache_dir>/forecasts_jja.csv
only, because no license text was found for the NMME files (see RESOURCES.md).
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
import xarray as xr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from parse_iri import parse_plume, parse_probbars, parse_quicklook  # noqa: E402

C = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
ISSUE = {1: "jan", 2: "feb", 3: "mar"}
R: dict = {}


def phase(v: float, lim: float = 0.5) -> str:
    return "EN" if v >= lim else ("LN" if v <= -lim else "N")


# ------------------------------------------------------------------ observed
oni = {}
for ln in (C / "oni.ascii.txt").read_text().splitlines()[1:]:
    p = ln.split()
    if len(p) == 4:
        oni[(p[0], int(p[1]))] = float(p[3])
ONI_JJA = {a: v for (s, a), v in oni.items() if s == "JJA"}
R["sources"] = json.loads((C / "sources.json").read_text(encoding="utf-8"))
R["oni_jja_last_year"] = max(ONI_JJA)
R["el_nino_jja_years"] = sorted(a for a, v in ONI_JJA.items() if v >= 0.5)
R["la_nina_jja_years"] = sorted(a for a, v in ONI_JJA.items() if v <= -0.5)

mth, abs_m = {}, {}
for ln in (C / "ersst5.nino.mth.91-20.ascii").read_text().splitlines()[1:]:
    p = ln.split()
    if len(p) >= 10:
        mth[(int(p[0]), int(p[1]))] = float(p[9])  # Nino-3.4 anomaly (1991-2020 base)
        abs_m[(int(p[0]), int(p[1]))] = float(p[8])  # Nino-3.4 absolute

# ------------------------------------------------------------------ NMME
recs = []
for f in sorted((C / "nmme").glob("*.Nino34.fcst.nc")):
    mod, _, ym = f.name.split(".")[:3]
    ds = xr.open_dataset(f, decode_times=False)
    v = ds["fcst"].values.ravel().astype(float)
    recs.append({"model": mod, "year": int(ym[:4]), "month": int(ym[4:6]), "v": v})
    ds.close()

# Which month is the first target? The file name says month M (folder MM0100 = start on 1/M), but
# the initial_time coordinate points to M+1 if 0 = Jan/1960. Test: shape of the model's 1991-2020
# annual cycle against the observed one, assuming target0 = M or M+1. (Inference, not documentation.)
for r in recs:  # years with missing values are left out
    r["ok"] = bool(np.all(np.isfinite(r["v"])))
R["nmme_files_with_nan"] = sorted(f"{r['model']} {r['year']}-{r['month']:02d}" for r in recs if not r["ok"])
recs = [r for r in recs if r["ok"]]
oclim = [np.mean([abs_m[(a, m)] for a in range(1991, 2021)]) for m in range(1, 13)]
check = {}
for mod in sorted({r["model"] for r in recs}):
    for mon in (1, 2, 3):
        rr = [r for r in recs if r["model"] == mod and r["month"] == mon and 1991 <= r["year"] <= 2020]
        if not rr:
            continue
        L = min(len(r["v"]) for r in rr)
        mc = np.mean([r["v"][:L] for r in rr], axis=0)
        check[f"{mod} {mon:02d}"] = {
            f"target0=M{'+1' if d else ''}": round(
                float(np.corrcoef(mc, [oclim[(mon - 1 + d + i) % 12] for i in range(L)])[0, 1]), 3
            )
            for d in (0, 1)
        }
R["nmme_target0_check_annual_cycle_shape"] = check
votes = sum(c["target0=M"] > c["target0=M+1"] for c in check.values())
SHIFT = 0 if votes > len(check) / 2 else 1
R["nmme_target0_shift"] = SHIFT
R["nmme_target0_votes_for_M"] = f"{votes}/{len(check)}"

nmme_rows = []
for mod in sorted({r["model"] for r in recs}):
    for mon in (1, 2, 3):
        rr = [r for r in recs if r["model"] == mod and r["month"] == mon]
        idx = [6 - (mon + SHIFT) + i for i in range(3)]  # positions of JUN, JUL, AUG
        if not rr or max(idx) >= min(len(r["v"]) for r in rr):
            continue
        base = [r for r in rr if 1991 <= r["year"] <= 2020]
        clim = np.mean([r["v"][idx] for r in base], axis=0)
        for r in rr:
            an = float(np.mean(r["v"][idx] - clim))
            nmme_rows.append({"source": f"NMME {mod}", "issue": mon, "year": r["year"], "fcst": round(an, 3)})
# multi-model mean
by = {}
for x in nmme_rows:
    by.setdefault((x["issue"], x["year"]), []).append(x["fcst"])
for (mon, year), vs in sorted(by.items()):
    nmme_rows.append({"source": "NMME mean", "issue": mon, "year": year, "fcst": round(float(np.mean(vs)), 3)})

# ------------------------------------------------------------------ IRI
iri_rows, iri_prob_rows, official_rows, iri_read = [], [], [], {}
for year in range(2002, 2027):
    for mon in (1, 2, 3):
        f4 = C / "iri" / f"figure4_plot_{year}_{mon:02d}.svg"
        if f4.exists():
            p = parse_plume(f4)
            iri_read[f"{year}-{mon:02d}"] = {
                "title": p["title"],
                "ambiguous": p["ambiguous"],
                "n_models": len(p["models"]),
                "calibration": p["calibration"],
                "y_labels_agree": p["y_labels_agree"],
            }
            for name, key in (
                ("IRI plume: mean of all models", "COMBINED AVG"),
                ("IRI plume: mean of dynamical models", "DYN Average"),
                ("IRI plume: NASA GMAO", "NASA GMAO"),
                ("IRI plume: CPC CONSOL", "CPC CONSOL"),
            ):
                v = p["models"].get(key, {}).get("JJA")
                if v is not None:
                    iri_rows.append({"source": name, "issue": mon, "year": year, "fcst": v})
        f3 = C / "iri" / f"figure3_plot_{year}_{mon:02d}.svg"
        if f3.exists():
            q = parse_probbars(f3).get("prob", {}).get("JJA")
            if q and len(q) == 3:
                iri_prob_rows.append({"source": "IRI objective probability", "issue": mon, "year": year, **q})
        fq = C / "iri" / f"quicklook_{year}_{mon:02d}.html"
        if fq.exists():
            tabs = parse_quicklook(fq)
            if tabs:
                t = tabs[0]  # first table = official early-month CPC/IRI consensus
                row = [x for x in t["rows"] if x["season"] == "JJA"]
                if row:
                    official_rows.append(
                        {
                            "source": "CPC/IRI official (consensus)",
                            "issue": mon,
                            "year": year,
                            "la_nina": row[0]["la_nina"],
                            "neutral": row[0]["neutral"],
                            "el_nino": row[0]["el_nino"],
                            "table": t["title"],
                        }
                    )
R["iri_svg_read"] = iri_read
R["iri_svg_y_labels_disagree"] = sorted(k for k, v in iri_read.items() if not v.get("y_labels_agree"))

# 2026: no HTML table; the CPC synopsis states the favoured JJA category when it passes 50%
synopses = {}
for mon, s in ((1, "jan2026"), (2, "feb2026"), (3, "mar2026")):
    f = C / "cpc" / f"disc_{s}.html"
    if not f.exists():
        continue
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", f.read_text(encoding="utf-8", errors="replace")))
    t = t.replace("&#37;", "%").replace("&nbsp;", " ").replace("&ntilde;", "ñ")
    m = re.search(r"Synopsis:\s*(.*?\.)(?:\s+[A-Z][^.]*\.)?", t)
    syn = m.group(0).replace("Synopsis:", "").strip() if m else ""
    synopses[s] = syn
    jja = re.search(
        r"(El Niño|La Niña|ENSO-neutral)[^.]{0,120}?\((\d+)% chance in June-August 2026\)", syn
    ) or re.search(r"June-August 2026, (El Niño|La Niña|ENSO-neutral) is likely to emerge \((\d+)% chance\)", syn)
    if jja:
        cat = {"El Niño": "EN", "La Niña": "LN", "ENSO-neutral": "N"}[jja.group(1)]
        official_rows.append(
            {
                "source": "CPC/IRI official (consensus)",
                "issue": mon,
                "year": 2026,
                "la_nina": None,
                "neutral": None,
                "el_nino": None,
                "phase_fcst": cat,
                "p_phase_fcst": float(jja.group(2)),
                "table": "CPC discussion synopsis (favoured category only)",
            }
        )
R["cpc_synopses_2026"] = synopses


# ------------------------------------------------------------------ metrics
def phase_prob(r):
    if r.get("phase_fcst"):
        return r["phase_fcst"]
    return max((("LN", r["la_nina"]), ("N", r["neutral"]), ("EN", r["el_nino"])), key=lambda t: t[1])[0]


def prob_txt(r):
    if r.get("phase_fcst"):
        return f"{r['phase_fcst']} {r['p_phase_fcst']:.0f}% (synopsis)"
    return f"{r['la_nina']:.0f}/{r['neutral']:.0f}/{r['el_nino']:.0f}"


def _cat(pf, po):
    n = len(po)
    d = {
        "phase_hit_rate": round(sum(a == b for a, b in zip(pf, po, strict=True)) / n, 2),
        "always_neutral_hit_rate": round(sum(b == "N" for b in po) / n, 2),
    }
    for k in ("EN", "LN"):
        obs = sum(b == k for b in po)
        fc = sum(a == k for a in pf)
        hit = sum(a == k and b == k for a, b in zip(pf, po, strict=True))
        d[f"obs_{k}"] = obs
        d[f"fcst_{k}"] = fc
        d[f"hits_{k}"] = hit
        d[f"POD_{k}"] = round(hit / obs, 2) if obs else None
        d[f"FAR_{k}"] = round((fc - hit) / fc, 2) if fc else None
    return d


def met_det(rows, obs=None):
    obs = obs or ONI_JJA
    xs = [(r["fcst"], obs[r["year"]]) for r in rows if r["year"] in obs]
    if len(xs) < 3:
        return None
    f = np.array([a for a, _ in xs])
    o = np.array([b for _, b in xs])
    return _cat([phase(a) for a in f], [phase(b) for b in o]) | {
        "n": len(xs),
        "r": round(float(np.corrcoef(f, o)[0, 1]), 2),
        "years": f"{min(r['year'] for r in rows)}-{max(r['year'] for r in rows if r['year'] in obs)}",
    }


# Sensitivity: observed with a fixed 1991-2020 base (the same as the NMME model anomalies), instead
# of the ONI, whose 30-year base moves every 5 years.
OBS_FIXED = {
    a: round(float(np.mean([mth[(a, m)] for m in (6, 7, 8)])), 3)
    for a in range(1982, 2027)
    if all((a, m) in mth for m in (6, 7, 8))
}


def met_prob(rows):
    xs = [r for r in rows if r["year"] in ONI_JJA]
    if len(xs) < 3:
        return None
    pf = [phase_prob(r) for r in xs]
    po = [phase(ONI_JJA[r["year"]]) for r in xs]
    pen_en = [r["el_nino"] for r, o in zip(xs, po, strict=True) if o == "EN" and r["el_nino"] is not None]
    pen_out = [r["el_nino"] for r, o in zip(xs, po, strict=True) if o != "EN" and r["el_nino"] is not None]
    return _cat(pf, po) | {
        "n": len(xs),
        "r": None,
        "years": f"{min(r['year'] for r in xs)}-{max(r['year'] for r in xs)}",
        "mean_p_el_nino_in_el_nino_years": round(float(np.mean(pen_en)), 1) if pen_en else None,
        "mean_p_el_nino_in_other_years": round(float(np.mean(pen_out)), 1) if pen_out else None,
    }


tab = []
groups = {}
for r in nmme_rows + iri_rows:
    groups.setdefault((r["source"], r["issue"]), []).append(r)
for (source, mon), rows in sorted(groups.items()):
    m = met_det(rows)
    if m:
        tab.append({"source": source, "issue": ISSUE[mon], **m})
# NMME only over the period shared with the IRI plume (2003-2022), and against the fixed base
for mon in (1, 2, 3):
    rows = [r for r in nmme_rows if r["source"] == "NMME mean" and r["issue"] == mon and r["year"] >= 2003]
    m = met_det(rows)
    if m:
        tab.append({"source": "NMME mean (2003-2022 only)", "issue": ISSUE[mon], **m})
    rows = [r for r in nmme_rows if r["source"] == "NMME mean" and r["issue"] == mon]
    m = met_det(rows, OBS_FIXED)
    if m:
        tab.append({"source": "NMME mean vs observed, fixed 1991-2020 base", "issue": ISSUE[mon], **m})
for source, rows_all in (
    ("IRI objective probability", iri_prob_rows),
    ("CPC/IRI official (consensus)", official_rows),
):
    for mon in (1, 2, 3):
        m = met_prob([r for r in rows_all if r["issue"] == mon])
        if m:
            tab.append({"source": source, "issue": ISSUE[mon], **m})
R["metrics"] = tab

# ------------------------------------------------------------------ cases (IRI and official only)
case_years = sorted(set([2002, 2009, 2015, 2023, 2026] + [a for a in R["la_nina_jja_years"] if a >= 2007]))
cases = []
for year in case_years:
    row = {"year": year, "oni_jja": ONI_JJA.get(year)}
    for mon in (1, 2, 3):
        for r in iri_rows:
            if r["year"] == year and r["issue"] == mon:
                row[f"{r['source']}|{ISSUE[mon]}"] = r["fcst"]
        for r in iri_prob_rows + official_rows:
            if r["year"] == year and r["issue"] == mon:
                row[f"{r['source']}|{ISSUE[mon]}"] = prob_txt(r)
    cases.append(row)
R["cases"] = cases

# ------------------------------------------------------------------ write
with (C / "forecasts_jja.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["source", "issue", "year", "fcst_anomaly_or_prob_LN/N/EN", "oni_jja_obs", "phase_fcst", "phase_obs"])
    for r in nmme_rows + iri_rows:
        o = ONI_JJA.get(r["year"])
        w.writerow(
            [
                r["source"],
                ISSUE[r["issue"]],
                r["year"],
                r["fcst"],
                o,
                phase(r["fcst"]),
                phase(o) if o is not None else "",
            ]
        )
    for r in iri_prob_rows + official_rows:
        o = ONI_JJA.get(r["year"])
        w.writerow(
            [
                r["source"],
                ISSUE[r["issue"]],
                r["year"],
                prob_txt(r),
                o,
                phase_prob(r),
                phase(o) if o is not None else "",
            ]
        )
with (OUT / "forecast_skill_metrics.csv").open("w", newline="", encoding="utf-8") as fh:
    cols = list(dict.fromkeys(k for t in tab for k in t))
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(tab)
(OUT / "forecast_skill.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

print(
    json.dumps(
        {
            k: R[k]
            for k in (
                "nmme_target0_votes_for_M",
                "nmme_target0_shift",
                "nmme_files_with_nan",
                "el_nino_jja_years",
                "la_nina_jja_years",
            )
        }
    )
)
for t in tab:
    print(
        f"{t['source']:44s} {t['issue']} n={t['n']:2d} {t['years']} hit={t['phase_hit_rate']} "
        f"(always neutral={t['always_neutral_hit_rate']}) r={t['r']} EN: POD={t['POD_EN']} FAR={t['FAR_EN']} "
        f"({t['hits_EN']}/{t['obs_EN']}, fcst {t['fcst_EN']}) LN: POD={t['POD_LN']} FAR={t['FAR_LN']}"
    )
