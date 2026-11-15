# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Figure: soybean yield deviation against standardized Dec-Feb rain, before and after 1995.

python -I figure.py <results_dir>
"""

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

OUT = Path(sys.argv[1])
LABEL_YEARS = {1991, 2005, 2012, 2022, 2023}
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dc"
COLOR = {"A": "#eb6834", "B": "#2a78d6"}  # categorical slots 2 and 1 of the dataviz reference palette

with (OUT / "panel.csv").open(encoding="utf-8") as f:
    panel = [{k: (float(v) if k in ("dev_linear", "z_rain") else v) for k, v in r.items()} for r in csv.DictReader(f)]
res = json.loads((OUT / "resilience.json").read_text(encoding="utf-8"))["primary"]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharex=True, sharey=True)
for ax, key, a, b in ((axes[0], "A", 1982, 1994), (axes[1], "B", 1995, 2025)):
    sel = [r for r in panel if a <= int(r["harvest_year"]) <= b]
    x = np.array([r["z_rain"] for r in sel])
    y = np.array([r["dev_linear"] for r in sel]) * 100
    ax.scatter(x, y, s=14, color=COLOR[key], alpha=0.35, linewidths=0)
    k = res[f"slope_{key.lower()}"]
    lo, hi = res[f"slope_{key.lower()}_ci95"]
    xs = np.array([x.min(), x.max()])
    ax.plot(xs, (np.mean(y) / 100 + k * (xs - np.mean(x))) * 100, color=COLOR[key], lw=2)
    for yr in sorted({int(r["harvest_year"]) for r in sel} & LABEL_YEARS):
        yy = [r for r in sel if int(r["harvest_year"]) == yr]
        mx, my = np.mean([r["z_rain"] for r in yy]), np.mean([r["dev_linear"] for r in yy]) * 100
        ax.scatter([mx], [my], s=46, color=COLOR[key], edgecolors="white", linewidths=1.5, zorder=3)
        ax.annotate(str(yr), (mx, my), xytext=(6, -3), textcoords="offset points", fontsize=8.5, color=INK)
    ax.set_title(
        f"{a}–{b} ({len({r['harvest_year'] for r in sel})} harvests)\n"
        f"slope {k * 100:+.1f}% per SD of rain (95% CI {lo * 100:+.1f} to {hi * 100:+.1f}), "
        f"r = {res[f'r_{key.lower()}']:.2f}",
        fontsize=10,
        color=INK,
        loc="left",
    )
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8.5)
    ax.set_xlabel("Dec–Feb rain, standardized (NASA POWER PRECTOTCORR; negative = drier)", fontsize=9, color=INK)
axes[0].set_ylabel("Soybean yield vs municipal trend (%)", fontsize=9, color=INK)
fig.suptitle(
    "Planalto Médio, RS (18 municipalities): soybean yield follows Dec–Feb rain about as closely after 1995 as before\n"
    f"Change in slope after 1995: {res['delta'] * 100:+.1f} points (95% CI {res['delta_ci95'][0] * 100:+.1f} to "
    f"{res['delta_ci95'][1] * 100:+.1f}); permutation by year p = {res['p_two_sided_perm_by_year']:.2f}",
    fontsize=10,
    color=INK,
    x=0.01,
    ha="left",
)
fig.text(
    0.01,
    0.005,
    "Sources: IBGE PAM (SIDRA 1612), NASA POWER daily. Small dots: one municipality-year. "
    "Larger dots: mean of the municipalities in labelled drought years.",
    fontsize=8,
    color=MUTED,
)
fig.tight_layout(rect=(0, 0.03, 1, 0.93))
fig.savefig(OUT / "drought-resilience.png", dpi=150)
print("wrote", OUT / "drought-resilience.png")
