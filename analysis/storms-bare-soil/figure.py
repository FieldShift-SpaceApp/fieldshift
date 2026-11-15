# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Static figure for the app: heavy-rain frequency and cropland with no green by fortnight, and the
straw-clock ranges for November. Reads only the committed results; no NASA or agency logo.

    python -I figure.py <results_dir>
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# reference categorical palette (light mode): slot 1 blue, 2 orange, 3 aqua, 4 yellow, 6 green
BLUE, ORANGE, AQUA, YELLOW, GREEN = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#008300"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#fcfcfb"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def main() -> None:
    results = Path(sys.argv[1])
    storms = json.loads((results / "storms_bare_soil.json").read_text(encoding="utf-8"))
    straw = json.loads((results / "straw_clock.json").read_text(encoding="utf-8"))
    rows = storms["fortnights"]
    x = [r["fortnight_index"] + 0.5 for r in rows]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED})
    fig = plt.figure(figsize=(8, 7.2), dpi=150, facecolor=SURFACE)
    ax = fig.add_axes((0.08, 0.53, 0.89, 0.35))
    ax.set_facecolor(SURFACE)

    ax.axvspan(20, 22, color=GRID, zorder=0)
    ax.text(21, 101, "November", ha="center", va="bottom", color=INK2, fontsize=8)

    lo = [r["s2_no_green_min_pct"] for r in rows]
    hi = [r["s2_no_green_max_pct"] for r in rows]
    ax.fill_between(x, lo, hi, color=ORANGE, alpha=0.16, linewidth=0, zorder=1)
    ax.plot(x, [r["s2_no_green_median_pct"] for r in rows], color=ORANGE, lw=2, zorder=3)
    ax.plot(x, [r["modis_no_green_median_pct"] for r in rows], color=MUTED, lw=1.5, ls=(0, (4, 2)), zorder=2)

    ax.plot(x, [r["imerg_pct_years_heavy"] for r in rows], color=BLUE, lw=2, marker="o", ms=4.5, zorder=4)
    ax.plot(
        x,
        [r["ana_pct_years_heavy"] for r in rows],
        ls="none",
        marker="o",
        ms=5,
        mfc=SURFACE,
        mec=AQUA,
        mew=1.5,
        zorder=5,
    )
    ax.plot(
        x, [r["power_pct_years_heavy"] for r in rows], ls="none", marker="x", ms=4.5, color=MUTED, mew=1.2, zorder=5
    )

    ax.set_xlim(0, 24)
    ax.set_ylim(0, 100)
    ax.set_xticks([2 * m + 1 for m in range(12)], MONTHS)
    ax.set_xticks(range(0, 25, 2), minor=True)
    ax.tick_params(axis="x", which="major", length=0, colors=INK2)
    ax.tick_params(axis="x", which="minor", length=3, colors=MUTED)
    ax.tick_params(axis="y", colors=INK2)
    ax.set_yticks(range(0, 101, 20), [f"{v}%" for v in range(0, 101, 20)])
    ax.grid(axis="y", color=GRID, lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_axisbelow(True)

    handles = [
        plt.Line2D([], [], color=ORANGE, lw=2),
        plt.Rectangle((0, 0), 1, 1, color=ORANGE, alpha=0.16, lw=0),
        plt.Line2D([], [], color=MUTED, lw=1.5, ls=(0, (4, 2))),
        plt.Line2D([], [], color=BLUE, lw=2, marker="o", ms=4.5),
        plt.Line2D([], [], ls="none", marker="o", ms=5, mfc=SURFACE, mec=AQUA, mew=1.5),
        plt.Line2D([], [], ls="none", marker="x", ms=4.5, color=MUTED, mew=1.2),
    ]
    names = [
        "No green (NDVI < 0.25), Sentinel-2 10 m, median 2019-25",
        "  range between years (Sentinel-2)",
        "  no green, MODIS 250 m (NASA), median",
        "Years with a day >= 50 mm, GPM IMERG (NASA), 2001-25",
        "  same, ANA rain gauge 2853015",
        "  same, NASA POWER",
    ]
    ax.legend(
        handles,
        names,
        loc="upper left",
        bbox_to_anchor=(-0.01, -0.08),
        ncol=2,
        frameon=False,
        fontsize=7.2,
        labelcolor=INK2,
        handlelength=2.2,
        columnspacing=1.2,
    )
    fig.text(
        0.08,
        0.955,
        "When do storms fall on cropland with no green? Cruz Alta, RS, Brazil",
        fontsize=11.5,
        color=INK,
        weight="bold",
    )
    fig.text(
        0.08,
        0.925,
        "Share of years with a heavy-rain day, and share of cropland with no green cover, by half-month",
        fontsize=8.5,
        color=INK2,
    )

    # straw clock: range bars per rotation for the three November dates
    bx = fig.add_axes((0.30, 0.14, 0.45, 0.19))
    bx.set_facecolor(SURFACE)
    rot_colors = {"soy-wheat": YELLOW, "soy-cover": GREEN, "soy-fallow": MUTED}
    targets = ["11-01", "11-16", "11-30"]
    tnames = {"11-01": "1 Nov", "11-16": "16 Nov", "11-30": "30 Nov"}
    order = ["soy-wheat", "soy-cover", "soy-fallow"]
    for i, rid in enumerate(order):
        for j, t in enumerate(targets):
            row = next(r for r in straw["rows"] if r["rotation"] == rid and r["target"] == t)
            y = i + (j - 1) * 0.26
            lo_, hi_ = row["straw_t_ha_low"], row["straw_t_ha_high"]
            if lo_ is None:
                bx.text(
                    9.15, y, f"{tnames[t]}: crop still standing", va="center", fontsize=6.8, color=INK2, clip_on=False
                )
                continue
            if hi_ - lo_ < 0.05:
                bx.plot([lo_], [y], marker="|", ms=8, mew=2, color=rot_colors[rid])
                bx.text(9.15, y, f"{tnames[t]}: no winter straw", va="center", fontsize=6.8, color=INK2, clip_on=False)
                continue
            bx.plot([lo_, hi_], [y, y], color=rot_colors[rid], lw=5, solid_capstyle="round", alpha=0.55 + 0.15 * j)
            part = " (harvested only)" if row["share_of_window_not_yet_managed_pct"] else ""
            bx.text(
                9.15,
                y,
                f"{tnames[t]}: {lo_:.1f}-{hi_:.1f} t/ha{part}",
                va="center",
                fontsize=6.8,
                color=INK2,
                clip_on=False,
            )
    short = {
        "soy-wheat": "Soybean - wheat\n(straw from harvest, Oct-Nov)",
        "soy-cover": "Soybean - black oat cover\n(desiccated Sep-Oct)",
        "soy-fallow": "Soybean - winter fallow",
    }
    bx.set_yticks(range(3), [short[r] for r in order], fontsize=7.3, color=INK)
    bx.invert_yaxis()
    bx.set_xlim(0, 9)
    bx.set_ylim(2.55, -0.55)
    bx.set_xlabel(
        "Winter straw still on the ground (t/ha); bars: 1, 16 and 30 Nov, top to bottom", fontsize=7.5, color=INK2
    )
    bx.tick_params(colors=INK2, labelsize=7.5)
    bx.grid(axis="x", color=GRID, lw=0.8)
    bx.set_axisbelow(True)
    for s in ("top", "right"):
        bx.spines[s].set_visible(False)
    fig.text(
        0.08,
        0.375,
        "Straw clock: what is still lying on the ground in November?",
        fontsize=10,
        color=INK,
        weight="bold",
    )
    fig.text(
        0.08,
        0.352,
        "Arithmetic from measured half-lives (oat 124 d, wheat 139 d; Cruz Alta no-till trial), "
        "not a field measurement",
        fontsize=8,
        color=INK2,
    )

    fig.text(
        0.08,
        0.012,
        "Rain: NASA GPM IMERG and NASA POWER (POWER API, NASA LaRC); ANA HidroWeb gauge 2853015. "
        "Cover: contains modified\n"
        "Copernicus Sentinel data [2019-2025] (ESA, partner data) and NASA MODIS MOD13Q1/MYD13Q1 v061. No green is not "
        "bare soil:\nNDVI cannot tell straw from soil. Straw: half-lives from Campos et al. 2011b; initial straw from "
        "Aita & Giacomini 2003 and Embrapa (Santos et al. 2019).",
        fontsize=6.4,
        color=INK2,
        va="bottom",
    )
    out = results / "storms-bare-soil.png"
    fig.savefig(out, facecolor=SURFACE)
    print("wrote", out)


if __name__ == "__main__":
    main()
