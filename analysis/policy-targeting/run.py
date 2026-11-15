# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Soil-test vouchers for Cruz Alta: budget -> hectares at NM3+, subsidy unlocked, small farms served.

Reads the per-property table that analysis/farm-reports keeps OUTSIDE git (raw folder, no CAR code), recomputes the
satellite-side NM for the unfavourable soil outcome with the same rules module, runs the greedy targeting and the
first-come baseline, and writes only aggregates to results/: policy_targeting.json (read by the app),
budget_curves.csv, curves.png and one map per objective (outlines coloured by the budget at which the property gets
a voucher; no labels, no codes).

    python -I analysis/policy-targeting/run.py [--raw DIR] [--runs 300]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis" / "farm-reports"))
import indicators as ind  # noqa: E402
import targeting as tg  # noqa: E402

DEFAULT_IBGE = "4306106"
BUDGETS = [50_000 * k for k in range(1, 21)]  # R$ 50 thousand to R$ 1 million
SCENARIOS_P = (0.3, 0.5, 0.7)
MAP_BRACKETS = (50_000, 100_000, 250_000, 500_000, 1_000_000)
MAP_COLORS = ("#0f5132", "#2f7d4f", "#5ea36a", "#9cc78f", "#d4e6c3")
PILOT_BUDGET_BRL = 1_000_000  # CGSR 111/2026: soybean pilot, PR + SC + RS + MS
INK, MUTED = "#0b0b0b", "#6b6a66"
ATTRIBUTION = (
    "Data: NASA/USGS Landsat Collection 2; NASA HLS v2.0; NASADEM (NASA JPL); property outlines: CAR/SICAR, "
    "Serviço Florestal Brasileiro; cropland: ESA WorldCover 2021 (CC BY 4.0). Pre-check: analysis/farm-reports."
)


def load_farms(raw: Path) -> list[tg.Farm]:
    rows = json.loads((raw / "farm_results.json").read_text(encoding="utf-8"))
    farms = []
    for r in rows:
        if not r["has_cropland"]:
            continue
        lv = r["levels"]
        assessed = r["nm_if_soil_level4"] is not None
        f = tg.Farm(
            idx=r["farm"],
            cropland_ha=float(r["cropland_ha"]),
            declared_ha=float(r["area_declared_ha"]),
            size_class=r["size_class"],
            assessed=assessed,
        )
        if assessed:
            t, c, d = (lv["T"]["lo"], lv["T"]["hi"]), (lv["C"]["lo"], lv["C"]["hi"]), (lv["D"]["lo"], lv["D"]["hi"])
            slope = r["slope"]["slope_mean_pct"]
            fallow = (r["winter"].get("fallow_winter_share") or 0) >= 0.5
            for s in (4, 3, 2, 1):
                rng = ind.nm_range(t, c, d, slope, fallow, soil_level=s)
                f.nm_by_soil[s] = (rng["nm_min"], rng["nm_max"])
            # the recomputed ranges must match what farm-reports stored
            for s, key in ((4, "nm_if_soil_level4"), (3, "nm_if_soil_level3")):
                stored = r[key]
                if f.nm_by_soil[s] != (stored["nm_min"], stored["nm_max"]):
                    raise SystemExit(f"farm {f.idx}: recomputed soil-{s} range differs from farm-reports")
            f.contour_needed = slope is not None and slope >= 3
            sn = r.get("straw_now") or {}
            f.straw_share = sn.get("straw_share") if sn.get("straw_share") is not None else 1.0
        farms.append(f)
    return farms


def outcomes(farms: list[tg.Farm], a: tg.Assumptions) -> dict[int, tg.Outcome]:
    outs = {f.idx: tg.outcome(f, a) for f in farms if f.assessed}
    rates = tg.size_rates([f for f in farms if f.assessed], outs)
    for f in farms:
        if not f.assessed:
            outs[f.idx] = tg.pooled_outcome(f, a, rates)
    return outs


def rnd(m: dict[str, float]) -> dict[str, float]:
    return {k: (round(v) if abs(v) >= 10 else round(v, 1)) for k, v in m.items()}


def run_scenarios(farms, runs: int, base: tg.Assumptions):
    by = {f.idx: f for f in farms}
    curves, first, orders = {}, {}, {}
    for p in SCENARIOS_P:
        a = tg.Assumptions(**{**base.to_dict(), "p_soil_favourable": p})
        outs = outcomes(farms, a)
        cost = {k: o.cost_brl for k, o in outs.items()}
        key = f"{p:.1f}"
        curves[key] = {}
        for obj in tg.OBJECTIVES:
            order = tg.greedy_order(farms, outs, obj)
            orders[(key, obj)] = (order, cost)
            curves[key][obj] = [
                {"budget_brl": b, **rnd(tg.metrics(tg.fill(order, cost, b), by, outs))} for b in BUDGETS
            ]
        first[key] = []
        for b in BUDGETS:
            fc = tg.first_come(farms, outs, b, runs)
            first[key].append(
                {"budget_brl": b, **{s: rnd({k: v[s] for k, v in fc.items()}) for s in ("mean", "p05", "p95")}}
            )
    return curves, first, orders


def selection_bracket(order, cost) -> dict[int, int]:
    """Smallest map bracket at which each farm gets a voucher."""
    got = {}
    for i, b in enumerate(MAP_BRACKETS):
        for k in tg.fill(order, cost, b):
            got.setdefault(k, i)
    return got


def rings_utm(geom: dict) -> list[np.ndarray]:
    from rasterio.warp import transform_geom

    g = transform_geom("EPSG:4326", "EPSG:32722", geom)
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return [np.asarray(p[0])[:, :2] / 1000.0 for p in polys]


OBJ_TITLE = {
    "subsidy": "most subsidy unlocked per real",
    "protected": "most straw-covered cropland brought into NM3+ per real",
    "families": "small properties (< 50 ha) first",
}


def draw_map(farms, rows_all, geoms, got, objective: str, p: str, path: Path) -> None:
    by = {f.idx: f for f in farms}
    fig, ax = plt.subplots(figsize=(8, 8.6), dpi=110)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    order = sorted(range(len(rows_all)), key=lambda k: -rows_all[k]["area_declared_ha"])
    polys, colors = [], []
    for k in order:
        f = by.get(rows_all[k]["farm"])
        if f is None:
            col = "#ffffff"
        elif not f.assessed:
            col = "#cfcdc6"
        else:
            col = MAP_COLORS[got[f.idx]] if f.idx in got else "#f1efe6"
        for ring in rings_utm(geoms[k]):
            polys.append(ring)
            colors.append(col)
    ax.add_collection(PolyCollection(polys, facecolors=colors, edgecolors="#ffffff", linewidths=0.25))
    mun = ROOT / "data" / "dev" / "dev-cruz-alta" / "ibge" / f"malha_municipio_{DEFAULT_IBGE}_2022.geojson"
    if mun.exists():
        g = json.loads(mun.read_text(encoding="utf-8"))
        g = g["features"][0]["geometry"] if "features" in g else g
        for ring in rings_utm(g):
            ax.plot(ring[:, 0], ring[:, 1], color=INK, lw=0.9)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    x0, _ = ax.get_xlim()
    y0, _ = ax.get_ylim()
    ax.plot([x0 + 1, x0 + 11], [y0 + 1, y0 + 1], color=INK, lw=2)
    ax.text(x0 + 6, y0 + 1.6, "10 km", ha="center", fontsize=8, color=INK)
    labels = ["voucher with R$ 50k", "with R$ 100k", "with R$ 250k", "with R$ 500k", "with R$ 1 million"]
    handles = [Patch(color=c, label=lb) for c, lb in zip(MAP_COLORS, labels, strict=True)]
    handles += [
        Patch(facecolor="#f1efe6", edgecolor="#bbbbbb", label="not reached with R$ 1 million"),
        Patch(color="#cfcdc6", label="cropland, no satellite pre-check"),
        Patch(facecolor="#ffffff", edgecolor="#bbbbbb", label="no cropland in the mask"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0, -0.01), ncol=3, fontsize=7.4, frameon=False)
    fig.suptitle(
        f"Cruz Alta: where a free soil test goes first ({OBJ_TITLE[objective]})",
        x=0.04,
        y=0.975,
        ha="left",
        fontsize=11.5,
        color=INK,
        weight="bold",
    )
    fig.text(
        0.04,
        0.945,
        f"Scenario, not a forecast: {int(float(p) * 100)}% of soil tests favourable (assumption), "
        "contour sowing confirmed, greedy choice by benefit per real.\nCAR outlines are self-declared and "
        "overlap. No names or CAR codes.",
        fontsize=7.8,
        color=MUTED,
        va="top",
    )
    fig.text(0.04, 0.012, ATTRIBUTION, fontsize=6.0, color=MUTED, wrap=True)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.91, bottom=0.12)
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def draw_curves(curves, first, path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=110)
    fig.patch.set_facecolor("#fcfcfb")
    x = np.array(BUDGETS) / 1000
    panels = (
        ("ha_nm3plus", "Cropland expected at NM3+ (ha)", 1),
        ("subsidy_gain_brl", "Subsidy unlocked (R$ million/yr)", 1e6),
        ("small_served", "Small properties (< 50 ha) with a voucher", 1),
    )
    for ax, (k, title, div) in zip(axes, panels, strict=True):
        for obj, col in (("subsidy", "#1f6f4a"), ("families", "#c27c0e")):
            lo = np.array([r[k] for r in curves["0.3"][obj]]) / div
            mid = np.array([r[k] for r in curves["0.5"][obj]]) / div
            hi = np.array([r[k] for r in curves["0.7"][obj]]) / div
            ax.plot(x, mid, color=col, lw=2, label=f"targeted: {obj}")
            ax.fill_between(x, lo, hi, color=col, alpha=0.12, lw=0)
        fc = first["0.5"]
        ax.plot(x, np.array([r["mean"][k] for r in fc]) / div, color="#6b6a66", lw=2, ls="--", label="first come")
        ax.fill_between(
            x,
            np.array([r["p05"][k] for r in fc]) / div,
            np.array([r["p95"][k] for r in fc]) / div,
            color="#6b6a66",
            alpha=0.12,
            lw=0,
        )
        ax.set_title(title, fontsize=10, color=INK, loc="left")
        ax.set_xlabel("Voucher budget (R$ thousand)", fontsize=8.5, color=MUTED)
        ax.grid(alpha=0.25)
        ax.tick_params(labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].legend(fontsize=8, frameon=False)
    fig.suptitle(
        "Cruz Alta soil-test vouchers: budget curves (scenario, not a forecast)",
        x=0.01,
        ha="left",
        fontsize=12,
        weight="bold",
        color=INK,
    )
    fig.text(
        0.01,
        0.005,
        "Lines: 50% of soil tests favourable; bands: 30-70% (targeted) and 5-95% of 300 random "
        "arrival orders (first come). Contour sowing assumed confirmed. Premium R$ 488/ha (PSR RS 2024).",
        fontsize=7.5,
        color=MUTED,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def write_json(path: Path, obj) -> None:
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=1, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ibge", default=DEFAULT_IBGE)
    ap.add_argument(
        "--raw", default=None, help="farm-reports raw folder (default ~/.cache/fieldshift/farm-reports/<ibge>)"
    )
    ap.add_argument("--results", default=str(HERE / "results"))
    ap.add_argument("--runs", type=int, default=300, help="random arrival orders for the first-come baseline")
    ap.add_argument("--premium", type=float, default=488.0)
    ap.add_argument("--contour", type=float, default=1.0, help="P(contour confirmed) where slope >= 3%%")
    ap.add_argument(
        "--fixed-cost", type=float, default=0.0, help="per-farm sampling/operator cost, R$ (no public price)"
    )
    ap.add_argument("--range-end", choices=("lower", "upper"), default="lower")
    ap.add_argument("--no-maps", action="store_true")
    a = ap.parse_args()
    raw = Path(a.raw) if a.raw else Path.home() / ".cache" / "fieldshift" / "farm-reports" / a.ibge
    if not (raw / "farm_results.json").exists():
        raise SystemExit(f"{raw / 'farm_results.json'} not found: run analysis/farm-reports/reproduce.py first")
    res = Path(a.results)
    res.mkdir(parents=True, exist_ok=True)
    base = tg.Assumptions(
        premium_brl_ha=a.premium,
        p_contour_confirmed=a.contour,
        fixed_cost_per_farm_brl=a.fixed_cost,
        range_end=a.range_end,
    )
    farms = load_farms(raw)
    assessed = [f for f in farms if f.assessed]
    curves, first, orders = run_scenarios(farms, a.runs, base)

    outs = outcomes(farms, base)
    cost_all = sum(outs[f.idx].cost_brl for f in assessed)
    contour_ha = sum(f.cropland_ha for f in assessed if f.contour_needed)
    inputs = {
        "properties_with_cropland": len(farms),
        "properties_assessed": len(assessed),
        "properties_not_assessed": len(farms) - len(assessed),
        "small_properties_assessed": sum(f.small for f in assessed),
        "small_properties_with_cropland": sum(f.small for f in farms),
        "cropland_assessed_ha": round(sum(f.cropland_ha for f in assessed)),
        "ready_nm3plus_if_soil_level3": sum(f.nm_by_soil[3][0] >= 3 for f in assessed),
        "ready_nm3plus_if_soil_level4": sum(f.nm_by_soil[4][0] >= 3 for f in assessed),
        "nm2_cap_if_soil_level2": sum(f.nm_by_soil[2][1] <= 2 for f in assessed),
        "assessed_needing_contour": sum(f.contour_needed for f in assessed),
        "assessed_cropland_needing_contour_share": round(contour_ha / sum(f.cropland_ha for f in assessed), 3),
        "voucher_cost_to_test_every_assessed_property_brl": round(cost_all),
        "voucher_cost_per_ha_brl": round(cost_all / sum(f.cropland_ha for f in assessed), 2),
    }
    key_budget = 100_000
    i = BUDGETS.index(key_budget)
    headline = {
        "budget_brl": key_budget,
        "soil_favourable": 0.5,
        "targeted": {obj: curves["0.5"][obj][i] for obj in tg.OBJECTIVES},
        "first_come_mean": first["0.5"][i]["mean"],
    }
    out = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "what": "Who should get a free soil test so that the ZarcNM soybean subsidy reaches the most? Greedy targeting "
        "of soil-test vouchers over the CAR properties of the farm-reports pre-check, against first come, first "
        "served. Scenario, not a forecast.",
        "municipality": {"name": "Cruz Alta (RS)", "ibge": a.ibge},
        "privacy": "Aggregates only. Built from the farm-reports per-property table kept outside git (no CAR code, no "
        "owner field); maps colour self-declared outlines without labels.",
        "assumptions": {
            **base.to_dict(),
            "p_soil_favourable": "scenario: 0.3 / 0.5 / 0.7",
            "first_come_runs": a.runs,
            "first_come_rule": "every property with cropland equally likely to apply; properties without "
            "the satellite pre-check get the averages of assessed properties of their size class",
        },
        "sources": {
            "subsidy_by_level": "Resolução CGSR 111/2026: 20/30/35/40% of the premium for NM1-NM4 (2026/27 pilot)",
            "premium": "MAPA PSR open data (SISSER), soybean, RS 2024: R$ 488/ha average (Cruz Alta R$ 408/ha)",
            "soil_test": "IN SPA/MAPA 2/2025 items 7.2-7.9 (0-20 and 20-40 cm, <= 10 ha per sampling area); prices "
            "UFPel (R$ 50 chemical, R$ 40 texture)",
            "pilot_budget": "CGSR 111/2026: R$ 1 million for soybean in PR, SC, RS and MS",
            "uptake": "MAPA 29 May 2026: Paraná 2025/26 pilot, R$ 206 thousand contracted of R$ 8 million",
        },
        "inputs": inputs,
        "pilot_budget_brl": PILOT_BUDGET_BRL,
        "budgets_brl": BUDGETS,
        "scenarios_soil_favourable": [f"{p:.1f}" for p in SCENARIOS_P],
        "curves_targeted": curves,
        "curves_first_come": first,
        "headline": headline,
        "maps": {obj: f"map-{obj}.png" for obj in tg.OBJECTIVES},
        "attribution": ATTRIBUTION,
    }
    write_json(res / "policy_targeting.json", out)

    with (res / "budget_curves.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        cols = [
            "farms",
            "spent_brl",
            "ha_nm3plus",
            "ha_nm4",
            "subsidy_gain_brl",
            "subsidy_total_brl",
            "small_served",
            "small_nm3plus",
            "protected_ha",
        ]
        w.writerow(["soil_favourable", "policy", "budget_brl", *cols])
        for p in curves:
            for obj in tg.OBJECTIVES:
                for r in curves[p][obj]:
                    w.writerow([p, f"targeted:{obj}", r["budget_brl"], *[r[c] for c in cols]])
            for r in first[p]:
                w.writerow([p, "first_come_mean", r["budget_brl"], *[r["mean"][c] for c in cols]])

    draw_curves(curves, first, res / "curves.png")
    if not a.no_maps:
        rows_all = json.loads((raw / "farm_results.json").read_text(encoding="utf-8"))
        geoms = json.loads((raw / "farm_geoms.json").read_text(encoding="utf-8"))
        for obj in tg.OBJECTIVES:
            order, cost = orders[("0.5", obj)]
            draw_map(farms, rows_all, geoms, selection_bracket(order, cost), obj, "0.5", res / f"map-{obj}.png")

    print(json.dumps({"inputs": inputs, "headline": headline}, indent=1))


if __name__ == "__main__":
    main()
