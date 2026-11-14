# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Step 2. Low-yield seasons of wheat and soybean by ENSO phase (ONI JJA), 18 municipalities of
the Planalto Medio (Rio Grande do Sul, Brazil).

Usage: python -I wheat_soy_enso.py <raw_dir> <results_dir>
Reads municipalities_rs.json, sidra_1612_v112.json and oni.ascii.txt written by fetch_sources.py.
Writes wheat_soy_enso.json (every variant, per winter) and municipality_year.csv (base case).

Base rule (the one behind the claim, unadjusted):
- low-yield season ("loss") = yield < 75% of the municipality's own linear trend, fitted on the
  years with valid data inside the window 1981-2025 (the year itself included);
- El Nino = ONI JJA >= +0.5; La Nina = ONI JJA <= -0.5; otherwise neutral;
- wheat: phase of the JJA of the same year; soybean: harvest of Y+1 against the JJA phase of Y.
"""

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

WHEAT, SOY = "2716", "2713"  # SIDRA table 1612, classification c81
MIN_POINTS = 10  # minimum valid years to fit a trend in a municipality
PERMUTATIONS = 20000
SEED = 20261114  # fixed seed: the p-value is reproducible run to run


def load(raw_dir: Path):
    munis = json.loads((raw_dir / "municipalities_rs.json").read_text(encoding="utf-8"))
    rows = json.loads((raw_dir / "sidra_1612_v112.json").read_text(encoding="utf-8"))[1:]
    yld = {}  # (code, product, year) -> float
    marker = {}  # (code, product, year) -> raw text when not numeric
    for r in rows:
        k = (r["D1C"], r["D4C"], int(r["D3C"]))
        v = r["V"].strip()
        try:
            f = float(v)
        except ValueError:
            marker[k] = v
            continue
        if f <= 0:
            marker[k] = v
            continue
        yld[k] = f
    oni = {}
    seasons = {}
    for ln in (raw_dir / "oni.ascii.txt").read_text(encoding="utf-8").splitlines()[1:]:
        p = ln.split()
        if len(p) == 4:
            seasons[(p[0], int(p[1]))] = float(p[3])
            if p[0] == "JJA":
                oni[int(p[1])] = float(p[3])
    return munis, yld, marker, oni, seasons


def phase(x: float) -> str:
    if x >= 0.5:
        return "el_nino"
    if x <= -0.5:
        return "la_nina"
    return "neutral"


def ratios(yld, code, product, y0, y1, degree):
    """Yield / trend ratio per year for one municipality, inside the window [y0, y1]."""
    years = [a for a in range(y0, y1 + 1) if (code, product, a) in yld]
    if len(years) < MIN_POINTS:
        return {}, len(years)
    x = np.array(years, dtype=float)
    y = np.array([yld[(code, product, a)] for a in years])
    coef = np.polyfit(x - 2000.0, y, degree)
    trend = np.polyval(coef, x - 2000.0)
    return {
        a: (yld[(code, product, a)], float(t), float(yld[(code, product, a)] / t))
        for a, t in zip(years, trend, strict=True)
    }, len(years)


def scenario(munis, yld, marker, oni, product, y0, y1, threshold, degree, lag):
    """lag=0: wheat of year Y vs JJA Y. lag=1: harvest Y+1 vs JJA Y."""
    pairs = []  # (code, name, winter_year, harvest_year, phase, oni, yield, trend, ratio, loss)
    excluded = Counter()
    for m in munis:
        code = m["code"] = str(m["code"])
        rz, _ = ratios(yld, code, product, y0, y1, degree)
        for wy in range(y0, y1 + 1 - lag):
            hy = wy + lag
            if wy not in oni:
                excluded["no ONI JJA"] += 1
                continue
            if hy not in rz:
                k = (code, product, hy)
                if k in marker:
                    excluded[f"SIDRA marker '{marker[k]}'"] += 1
                elif k in yld:
                    excluded["municipality with < 10 valid years"] += 1
                else:
                    excluded["no SIDRA row"] += 1
                continue
            r, t, q = rz[hy]
            pairs.append((code, m["name"], wy, hy, phase(oni[wy]), oni[wy], r, t, q, q < threshold))
    return pairs, excluded


def summary(pairs):
    g = defaultdict(lambda: [0, 0])
    by_year = defaultdict(lambda: [0, 0])
    for p in pairs:
        g[p[4]][0] += 1
        g[p[4]][1] += p[9]
        by_year[(p[4], p[2])][0] += 1
        by_year[(p[4], p[2])][1] += p[9]
    out = {}
    for f in ("el_nino", "neutral", "la_nina"):
        n, q = g[f]
        years = sorted((a, v[0], v[1]) for (ff, a), v in by_year.items() if ff == f)
        out[f] = {
            "pairs": n,
            "losses": q,
            "pct": round(100 * q / n, 1) if n else None,
            "winters": len(years),
            "median_ratio": round(float(np.median([p[8] for p in pairs if p[4] == f])), 3) if n else None,
            "by_winter": [{"winter_year": a, "pairs": nn, "losses": qq} for a, nn, qq in years],
        }
        # how much the percentage depends on the 1 and 2 winters with the most losses
        top = sorted(years, key=lambda t: -t[2])
        for k in (1, 2):
            drop = {a for a, _, _ in top[:k]}
            n2 = sum(nn for a, nn, _ in years if a not in drop)
            q2 = sum(qq for a, _, qq in years if a not in drop)
            out[f][f"pct_without_top{k}"] = round(100 * q2 / n2, 1) if n2 else None
            out[f][f"top{k}_winters"] = sorted(drop)
    return out


def permutation_by_winter(pairs, oni, rng):
    """Shuffle the phase labels between winters, keeping the municipalities of a winter together.
    Tests whether the El Nino - La Nina difference survives when the independent unit is the winter."""
    years = sorted({p[2] for p in pairs})
    n_year = {a: sum(1 for p in pairs if p[2] == a) for a in years}
    q_year = {a: sum(p[9] for p in pairs if p[2] == a) for a in years}
    labels = [phase(oni[a]) for a in years]

    def diff(lbls):
        tot = {"el_nino": [0, 0], "la_nina": [0, 0]}
        for a, f in zip(years, lbls, strict=True):
            if f in tot:
                tot[f][0] += n_year[a]
                tot[f][1] += q_year[a]
        return tot["el_nino"][1] / tot["el_nino"][0] - tot["la_nina"][1] / tot["la_nina"][0]

    obs = diff(labels)
    sims = np.array([diff(list(rng.permutation(labels))) for _ in range(PERMUTATIONS)])
    return {
        "winters": len(years),
        "observed_diff_pp": round(100 * obs, 1),
        "p_two_sided": round(float(np.mean(np.abs(sims) >= abs(obs) - 1e-12)), 4),
        "permutations": PERMUTATIONS,
        "seed": SEED,
    }


def main() -> None:
    raw_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    munis, yld, marker, oni, seasons = load(raw_dir)
    access = json.loads((raw_dir / "access_log_fetch.json").read_text(encoding="utf-8"))
    res = {
        "sources": {k: access[k] for k in ("ibge_localities", "ibge_sidra_1612", "noaa_cpc_oni")},
        "oni_jja": {a: oni[a] for a in range(1981, 2026)},
        "variants": [],
    }

    variants = []
    for product, name, lag in ((WHEAT, "wheat", 0), (SOY, "soybean_next_summer", 1)):
        for window in ((1981, 2025), (1990, 2025)):
            for threshold in (0.70, 0.75, 0.80):
                for degree in (1, 2):
                    variants.append((product, name, lag, window, threshold, degree))

    base_pairs = {}
    for product, name, lag, (y0, y1), threshold, degree in variants:
        pairs, excluded = scenario(munis, yld, marker, oni, product, y0, y1, threshold, degree, lag)
        res["variants"].append(
            {
                "series": name,
                "window": f"{y0}-{y1}",
                "threshold": threshold,
                "trend": "linear" if degree == 1 else "quadratic",
                "possible": len(munis) * (y1 + 1 - lag - y0),
                "included": len(pairs),
                "excluded": dict(excluded),
                "phases": summary(pairs),
            }
        )
        if (y0, y1) == (1981, 2025) and threshold == 0.75 and degree == 1:
            base_pairs[name] = pairs

    rng = np.random.default_rng(SEED)
    res["permutation_by_winter"] = {}
    for name, pairs in base_pairs.items():
        res["permutation_by_winter"][name] = permutation_by_winter(pairs, oni, rng)
        r = res["permutation_by_winter"][name]
        print(f"permutation {name}: diff {r['observed_diff_pp']} pp, p={r['p_two_sided']}")

    wheat = base_pairs["wheat"]
    # strong El Nino (ONI JJA >= +1.0), as in the team's first regional table
    strong = [p for p in wheat if p[5] >= 1.0]
    res["wheat_strong_el_nino"] = {
        "pairs": len(strong),
        "losses": sum(p[9] for p in strong),
        "pct": round(100 * sum(p[9] for p in strong) / len(strong), 1) if strong else None,
        "median_ratio": round(float(np.median([p[8] for p in strong])), 3) if strong else None,
    }
    # wheat 2023: municipality detail and sensitivity to the threshold
    w23 = [p for p in wheat if p[2] == 2023]
    res["wheat_2023"] = {
        "municipalities_with_data": len(w23),
        "losses_75": sum(p[9] for p in w23),
        "losses_70": sum(p[8] < 0.70 for p in w23),
        "losses_80": sum(p[8] < 0.80 for p in w23),
        "detail": [
            {"municipality": p[1], "yield_kg_ha": p[6], "trend_kg_ha": round(p[7]), "ratio": round(p[8], 3)}
            for p in sorted(w23, key=lambda p: p[8])
        ],
    }
    # Cruz Alta: El Nino winters with wheat data
    res["cruz_alta_el_nino"] = [
        {"year": p[2], "oni_jja": p[5], "ratio": round(p[8], 3), "loss": p[9]}
        for p in wheat
        if p[1] == "Cruz Alta" and p[4] == "el_nino"
    ]
    res["el_nino_jja_years_1981_2025"] = [a for a in range(1981, 2026) if oni[a] >= 0.5]
    res["la_nina_jja_years_1981_2025"] = [a for a in range(1981, 2026) if oni[a] <= -0.5]
    # observed ONI before wheat sowing (JFM, FMA, MAM) in the El Nino winters
    res["oni_before_sowing_el_nino_winters"] = {
        a: {s: seasons.get((s, a)) for s in ("JFM", "FMA", "MAM", "JJA")} for a in res["el_nino_jja_years_1981_2025"]
    }
    # coverage per municipality (base case): [pairs, first harvest year]
    cov = {}
    for name, pairs in base_pairs.items():
        c = Counter(p[1] for p in pairs)
        cov[name] = {
            m["name"]: [c.get(m["name"], 0), min((p[3] for p in pairs if p[1] == m["name"]), default=None)]
            for m in munis
        }
    res["coverage_per_municipality_base"] = cov

    (out_dir / "wheat_soy_enso.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out_dir / "municipality_year.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "series",
                "ibge_code",
                "municipality",
                "winter_year",
                "harvest_year",
                "phase_jja",
                "oni_jja",
                "yield_kg_ha",
                "trend_kg_ha",
                "ratio",
                "loss_75",
            ]
        )
        for name, pairs in base_pairs.items():
            for p in pairs:
                w.writerow(
                    [name, p[0], p[1], p[2], p[3], p[4], p[5], round(p[6]), round(p[7]), round(p[8], 4), int(p[9])]
                )

    # screen: essentials only
    for v in res["variants"]:
        f = v["phases"]
        print(
            f"{v['series']:20} {v['window']} thr={v['threshold']:.2f} {v['trend']:9} "
            f"n={v['included']}/{v['possible']} | "
            f"EN {f['el_nino']['losses']}/{f['el_nino']['pairs']}={f['el_nino']['pct']}% "
            f"(w/o top1 {f['el_nino']['pct_without_top1']}, top2 {f['el_nino']['pct_without_top2']}) | "
            f"neutral {f['neutral']['pct']}% | "
            f"LN {f['la_nina']['losses']}/{f['la_nina']['pairs']}={f['la_nina']['pct']}% "
            f"(w/o top1 {f['la_nina']['pct_without_top1']})"
        )
    print("wheat 2023:", res["wheat_2023"]["losses_75"], "/", res["wheat_2023"]["municipalities_with_data"])
    print("strong El Nino:", res["wheat_strong_el_nino"])


if __name__ == "__main__":
    main()
