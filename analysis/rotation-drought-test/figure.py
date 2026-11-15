# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""One PNG: C - T soybean NDVI contrast per summer, and the planting-date proxy by winter class.

python -I figure.py <results_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

INK, MUTED, GRID = "#1f2328", "#59636e", "#d0d7de"
COL = {"T": "#b8860b", "C": "#2e7d4f", "O": "#8c8c8c"}


def main() -> None:
    out = Path(sys.argv[1])
    res = json.loads((out / "rotation_drought_test.json").read_text(encoding="utf-8"))
    per = res["per_summer"]
    summers = list(per)
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1.15, 1]})

    # panel a: per-summer contrast, two specifications
    xs = range(len(summers))
    for off, key, lab, mk in (
        (-0.12, "C_minus_T_within_block_only", "same 1 km block", "o"),
        (0.12, "C_minus_T_within_block_and_planting_stratum", "same block and same planting half-month", "s"),
    ):
        est = [per[s][key]["est"] for s in summers]
        lo = [per[s][key]["est"] - per[s][key]["ci95"][0] for s in summers]
        hi = [per[s][key]["ci95"][1] - per[s][key]["est"] for s in summers]
        a.errorbar(
            [x + off for x in xs],
            est,
            yerr=[lo, hi],
            fmt=mk,
            color=INK if mk == "o" else COL["C"],
            ms=5,
            capsize=2,
            lw=1,
            label=lab,
        )
    for x, s in zip(xs, summers, strict=True):
        if per[s]["drought"]:
            a.axvspan(x - 0.45, x + 0.45, color="#f3d9c4", zorder=0)
    a.axhline(0, color=MUTED, lw=0.8)
    a.set_xticks(list(xs), [s + ("\ndrought" if per[s]["drought"] else "") for s in summers], fontsize=8)
    a.set_ylabel("soybean NDVI Jan-Feb: after cover (C) minus after wheat-like (T)", fontsize=8)
    a.set_title("a. C - T, one summer at a time (95% CI, block-clustered)", fontsize=9, loc="left", color=INK)
    a.legend(fontsize=7, frameon=False, loc="lower left")
    a.grid(axis="y", color=GRID, lw=0.5)

    # panel b: planting-date proxy distribution by class, all summers
    pdx = res["planting_date"]
    strata = pdx["strata"]
    w = 0.38
    for name, off in (("T", -w / 2), ("C", w / 2)):
        sh = [100 * v for v in pdx["share_by_class_all_summers"][name]]
        b.bar(
            [i + off for i in range(len(strata))],
            sh,
            width=w,
            color=COL[name],
            label={"T": "after wheat-like cereal (T)", "C": "after cover crop (C)"}[name],
        )
    b.set_xticks(range(len(strata)), strata, fontsize=8)
    b.set_ylabel("% of pixel-summers", fontsize=8)
    b.set_title("b. Summer green-up half-month (planting-date proxy)", fontsize=9, loc="left", color=INK)
    b.legend(fontsize=7, frameon=False)
    b.grid(axis="y", color=GRID, lw=0.5)

    m2 = res["models"]["M2_direct"]["protection_d_C"]
    fig.text(
        0.01,
        0.01,
        "Cruz Alta (RS), 30 m cropland pixels, summers 2020/21-2025/26. Pooled drought minus normal (C - T),"
        f" same pixel, same planting half-month: {m2['est']:+.3f} NDVI [{m2['ci95'][0]:+.3f}; {m2['ci95'][1]:+.3f}]."
        "\nData: NASA HLS v2.0 (L30+S30) NDVI; winter classes from analysis/rotation-fingerprint.",
        fontsize=7,
        color=MUTED,
    )
    for ax in (a, b):
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(labelsize=8, colors=INK)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(out / "rotation-drought-test.png", dpi=150)
    print("figure written", flush=True)


if __name__ == "__main__":
    main()
