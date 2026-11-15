# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Static figure for the app and the pitch: share of Cruz Alta cropland with a probable bare-soil signature in
late October - mid November, 1984-2026, with the threshold sensitivity and the census no-till marks.
Reads only the committed results; no NASA or agency logo.

    python -I figure.py <results_dir>
"""

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

MID, LO, HI = "emb_pct_C_lt30_median", "emb_pct_C_lt30_rmse_low_median", "emb_pct_C_lt30_rmse_high_median"
# reference categorical palette (light mode), fixed order: slot 1 blue, 3 aqua, 2 orange; HLS by shape (ink)
BLUE, AQUA, ORANGE = "#2a78d6", "#1baf7a", "#eb6834"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#fcfcfb"
FAMILY = {"TM": ("Landsat 4/5 TM", BLUE), "ETM": ("Landsat 7 ETM+", AQUA), "OLI": ("Landsat 8/9 OLI", ORANGE)}


def family(sensors: str) -> str:
    if "OLI" in sensors:
        return "OLI"
    if "ETM" in sensors:
        return "ETM"
    return "TM"


def f(x: str) -> float | None:
    return float(x) if x not in ("", "None") else None


def main() -> None:
    results = Path(sys.argv[1])
    rows = list(csv.DictReader((results / "series.csv").open(encoding="utf-8")))
    doc = json.loads((results / "residue_landsat.json").read_text(encoding="utf-8"))
    census = doc["census_check"]["summary"]["no_till_area_over_soybean_plus_maize_pct"]
    spring = [r for r in rows if r["season"] == "spring"]
    ls = [r for r in spring if r["family"] == "landsat"]
    hls = [r for r in spring if r["family"] == "hls"]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED})
    fig = plt.figure(figsize=(8, 4.8), dpi=150, facecolor=SURFACE)
    ax = fig.add_axes((0.08, 0.17, 0.89, 0.66))
    ax.set_facecolor(SURFACE)

    # Landsat: annual median (dot) and sensitivity NDTI 0.04-0.10 (vertical bar)
    for key, (label, color) in FAMILY.items():
        sel = [r for r in ls if family(r["sensors"]) == key]
        if not sel:
            continue
        for r in sel:
            y = int(r["year"]) + (0.18 if key == "ETM" else 0)
            ax.plot(
                [y, y],
                [f(r[LO]), f(r[HI])],
                color=color,
                lw=2,
                alpha=0.35,
                solid_capstyle="round",
                zorder=2,
            )
        ax.plot(
            [int(r["year"]) + (0.18 if key == "ETM" else 0) for r in sel],
            [f(r[MID]) for r in sel],
            ls="none",
            marker="o",
            ms=5.5,
            color=color,
            mec=SURFACE,
            mew=1.2,
            label=label,
            zorder=4,
        )
    if hls:
        for r in hls:
            y = int(r["year"]) - 0.25
            ax.plot(
                [y, y],
                [f(r[LO]), f(r[HI])],
                color=INK2,
                lw=1.2,
                alpha=0.5,
                zorder=2,
            )
        ax.plot(
            [int(r["year"]) - 0.25 for r in hls],
            [f(r[MID]) for r in hls],
            ls="none",
            marker="s",
            ms=5,
            mfc=SURFACE,
            mec=INK,
            mew=1.3,
            label="NASA HLS (L30 + S30)",
            zorder=5,
        )

    ymax = max(f(r[HI]) or 0 for r in spring) * 1.12 + 1
    for yr in (2006, 2017):
        ax.axvline(yr, color=MUTED, lw=1, ls=(0, (3, 3)), zorder=1)
        ax.text(
            yr + 0.3,
            ymax * 0.97,
            f"Census {yr}: no-till area\n≈ {census[str(yr)]:.0f}% of summer-crop area",
            color=INK2,
            fontsize=7.5,
            va="top",
        )
    last = [r for r in ls + hls if r["year"] == "2026"]
    if last:
        r26 = min(last, key=lambda r: f(r[MID]))
        v = f(r26[MID])
        x26 = 2026 - (0.25 if r26["family"] == "hls" else 0)
        ax.annotate(
            f"2026: {v:.1f}%\n({r26['sensors']}, {r26['dates'].split()[0]})",
            (x26, v),
            xytext=(2019.6, ymax * 0.33),
            color=INK,
            fontsize=8,
            arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.8},
        )

    ax.set_xlim(1983, 2027.5)
    ax.set_ylim(0, ymax)
    ax.set_ylabel("% of no-green cropland at C < 30%", color=INK2)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK2)
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.80), frameon=False, fontsize=8, labelcolor=INK2)

    fig.text(
        0.08, 0.93, "Cruz Alta in early November: from ploughed soil to straw", fontsize=12.5, weight="bold", color=INK
    )
    sub = (
        "Straw cover C from NDTI with the Embrapa Doc 454 ruler (Cambé, PR calibration, not local); "
        "C < 30% = IN 2/2025 level 1.\n"
        "Pixels with NDVI < 0.30, 20 Oct – 20 Nov. Dot = median of the clear scenes; "
        "bar = calibration RMSE (±8 points)."
    )
    fig.text(0.08, 0.855, sub, fontsize=8, color=INK2, linespacing=1.4)
    fig.text(
        0.08,
        0.055,
        "Since 1995, 97–99% of no-green cropland reads above the ~80% NDTI saturation (levels 3 and 4 not separable).\n"
        "Census ratio: IBGE Censo Agropecuário no-till area / IBGE PAM soybean + maize planted area.",
        fontsize=7,
        color=MUTED,
    )
    fig.text(
        0.08,
        0.02,
        "Data: NASA/USGS Landsat, NASA HLS · ESA WorldCover 2021 cropland mask · IBGE",
        fontsize=7.5,
        color=INK2,
    )
    fig.savefig(results / "residue-landsat.png", facecolor=SURFACE)
    print("wrote", results / "residue-landsat.png")


if __name__ == "__main__":
    main()
