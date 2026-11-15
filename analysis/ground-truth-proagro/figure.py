# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Figure: Sep-Nov rain seen by NASA GPM IMERG x insured wheat area paid for excess rain, one dot per year.
Reads only the committed results; no NASA or agency logo.

    uv run --with matplotlib==3.10.7 python -I analysis/ground-truth-proagro/figure.py <results_dir>
"""

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PHASE = {  # colour + marker (marker is the secondary encoding; neutral is grey on purpose)
    "el_nino": ("#eb6834", "o", "El Niño spring"),
    "neutral": ("#8a8984", "s", "Neutral spring"),
    "la_nina": ("#2a78d6", "D", "La Niña spring"),
}
OFFSET = {"2013": (-12, 9), "2016": (6, 6), "2018": (7, -13), "2019": (-36, 6), "2020": (-14, -16), "2022": (6, 6)}
INK, INK2, GRID, BG = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def main() -> None:
    res = Path(sys.argv[1])
    with (res / "table_by_year.csv").open(encoding="utf-8") as f:
        table = list(csv.DictReader(f))
    t = json.loads((res / "ground_truth.json").read_text(encoding="utf-8"))
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(9, 6), dpi=150, facecolor=BG)
    ax.set_facecolor(BG)
    for ph, (colour, marker, label) in PHASE.items():
        sel = [r for r in table if r["enso_phase_son"] == ph]
        ax.scatter([float(r["imerg_son_total_mean18_mm"]) for r in sel],
                   [float(r["pct_area_paid_excess_rain"]) for r in sel],
                   s=110, c=colour, marker=marker, edgecolors=BG, linewidths=2, label=label, zorder=3)  # fmt: skip
    for r in table:
        x, y = float(r["imerg_son_total_mean18_mm"]), float(r["pct_area_paid_excess_rain"])
        dx, dy = OFFSET.get(r["year"], (7, 5))
        ax.annotate(r["year"], (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=10, color=INK2)
    r15 = next(r for r in table if r["year"] == "2015")
    ax.annotate(f"2015: frost came first\n({float(r15['pct_area_paid_frost']):.0f}% of the area paid for frost)",
                (float(r15["imerg_son_total_mean18_mm"]), float(r15["pct_area_paid_excess_rain"])),
                xytext=(800, 14), fontsize=8.5, color=INK2,
                arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.8})  # fmt: skip
    ax.set_xlabel("NASA GPM IMERG rain, Sep–Nov (mm, mean of 18 municipalities)", color=INK, fontsize=11)
    ax.set_ylabel("Insured wheat area paid for EXCESS RAIN (%)", color=INK, fontsize=11)
    ax.set_ylim(-4, 100)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2)
    sec, sec23, pri = t["secondary_total_son"], t["secondary_total_son_without_2023"], t["primary_days50"]
    fig.suptitle("Wetter springs seen from space, more wheat lost to rain on the ground",
                 x=0.07, ha="left", fontsize=14, fontweight="bold", color=INK)  # fmt: skip
    ax.set_title(
        "Planalto Médio (Rio Grande do Sul, Brazil), 2013–2025, one dot per year (n = 13); regional signal, "
        "not field-level.\n"
        f"Sep–Nov total rain: Spearman ρ = {sec['spearman']:.2f}, permutation p = {sec['p_perm']:.3f} "
        f"(without 2023: ρ = {sec23['spearman']:.2f}).\n"
        f"Pre-registered metric, days ≥ 50 mm: ρ = {pri['spearman']:.2f}, p = {pri['p_perm_one_sided']:.3f} "
        "(not significant).",
        loc="left",
        fontsize=8.5,
        color=INK2,
    )
    ax.legend(frameon=False, loc="upper left", fontsize=10)
    fig.text(0.07, 0.01,
             "Sources: Banco Central do Brasil, Proagro data matrix (event view; wheat; approved claims ÷ insured "
             "area);\nNASA GPM IMERG via the NASA POWER API (municipal centroid pixel); ENSO phase: NOAA CPC ONI, "
             "SON.\nChart drawn by a script written with AI (see SI-USAGE.md).",
             fontsize=7.5, color=INK2)  # fmt: skip
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    fig.savefig(res / "ground-truth-proagro.png", facecolor=BG)


if __name__ == "__main__":
    main()
