# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Figures of the rotation fingerprint: yearly maps, the year-by-year GIF, shares against IBGE PAM, NDVI profiles
by class and the diversity-level map. No NASA or agency logo; "NASA HLS" attribution in every footer.

    python -I figure.py <raw_dir> <results_dir>
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from PIL import Image  # noqa: E402
from rasterio.transform import Affine  # noqa: E402
from rasterio.warp import transform as warp_transform  # noqa: E402

YEARS = list(range(2020, 2027))
# categorical, fixed order T, C, P, O (checked with the dataviz palette validator: CVD and normal-vision pass)
COL = {"T": "#c08a0f", "C": "#00897b", "P": "#b5452f", "O": "#7b5cb0"}
LABEL = {
    "T": "Wheat-like winter cereal (T)",
    "C": "Winter cover crop (C)",
    "P": "Fallow, no green winter (P)",
    "O": "Other / ambiguous (O)",
}
SURFACE, OUTSIDE_CROP, NODATA = "#fcfcfb", "#ebeae5", "#c9c8c3"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
FOOT = (
    "Data: NASA HLS v2.0 (HLSL30 + HLSS30), 30 m, via Microsoft Planetary Computer · cropland: ESA WorldCover 2021 "
    "(CC BY 4.0) · municipality: IBGE · classes are phenological hypotheses, not field labels · FieldShift"
)
FOOT2 = FOOT.replace(" · municipality: IBGE · ", " · municipality: IBGE\n")
# raster codes for display: 0 outside municipality, 1-4 classes, 5 cropland not classified, 6 non-cropland inside
CMAP = ListedColormap([SURFACE, COL["T"], COL["C"], COL["P"], COL["O"], NODATA, OUTSIDE_CROP])

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "text.color": INK,
        "axes.labelcolor": INK2,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "axes.edgecolor": MUTED,
    }
)


def rasters(raw: Path) -> tuple[dict, tuple, np.ndarray, np.ndarray]:
    g = np.load(raw / "grid.npz")
    idx, shape, inside = g["idx"], tuple(int(x) for x in g["shape"]), g["inside"]
    c = np.load(raw / "classes.npz")
    out = {}
    for y in YEARS:
        a = np.where(inside.ravel(), 6, 0).astype(np.uint8)
        v = c[f"cls_{y}"].copy()
        v[v == 0] = 5
        a[idx] = v
        out[y] = a.reshape(shape)
    return out, shape, idx, inside


def crop_box(inside: np.ndarray) -> tuple[slice, slice]:
    r = np.flatnonzero(inside.any(1))
    cc = np.flatnonzero(inside.any(0))
    return slice(r[0], r[-1] + 1), slice(cc[0], cc[-1] + 1)


def tag(y: int, done: dict) -> str:
    return "" if done.get(str(y), True) else " (to 2 Nov, provisional)"


def maps(maps_: dict, inside, shares: dict, done: dict, out: Path) -> None:
    rs, cs = crop_box(inside)
    fig = plt.figure(figsize=(16, 9.6), dpi=100, facecolor=SURFACE)
    fig.text(0.03, 0.955, "Every field's winter, from space: Cruz Alta (RS), 2020–2026", fontsize=19, weight="bold")
    fig.text(
        0.03,
        0.925,
        "Winter path of each 30 m cropland pixel from its NASA HLS NDVI time series (1 Apr – 30 Nov), explicit "
        "phenological rules; grey = cloud gaps",
        fontsize=11.5,
        color=INK2,
    )
    for k, y in enumerate(YEARS):
        ax = fig.add_axes([0.03 + (k % 4) * 0.24, 0.50 - (k // 4) * 0.43, 0.225, 0.40])
        ax.imshow(maps_[y][rs, cs], cmap=CMAP, vmin=0, vmax=6, interpolation="nearest")
        ax.set_axis_off()
        s = shares[y]
        ax.set_title(
            f"{y}   T {s['T_pct']:.0f}% · C {s['C_pct']:.0f}% · P {s['P_pct']:.0f}% · O {s['O_pct']:.0f}%"
            + ("\nprovisional: imagery to 2 Nov, harvest not over" if tag(y, done) else ""),
            fontsize=11,
            loc="left",
            color=INK,
        )
    lax = fig.add_axes([0.76, 0.10, 0.22, 0.35])
    lax.set_axis_off()
    handles = [Patch(facecolor=COL[k], label=LABEL[k]) for k in COL] + [
        Patch(facecolor=NODATA, label="Cropland, not classified (clouds)"),
        Patch(facecolor=OUTSIDE_CROP, label="Not cropland (WorldCover 2021)"),
    ]
    lax.legend(handles=handles, loc="upper left", frameon=False, fontsize=11)
    lax.text(
        0.0,
        0.12,
        "Shares = % of classified cropland pixels.\nT: green from Jul, peak Aug–Sep, gone Oct–Nov.\n"
        "C: green by Jun, gone Aug – early Nov.\nP: never green Jun–Sep.",
        fontsize=9.5,
        color=INK2,
        transform=lax.transAxes,
        va="bottom",
    )
    fig.text(0.03, 0.015, FOOT, fontsize=8.5, color=MUTED)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def gif(maps_: dict, inside, shares: dict, done: dict, out: Path) -> None:
    rs, cs = crop_box(inside)
    frames = []
    for y in YEARS:
        fig = plt.figure(figsize=(7.2, 8.0), dpi=100, facecolor=SURFACE)
        ax = fig.add_axes([0.03, 0.17, 0.94, 0.70])
        ax.imshow(maps_[y][rs, cs][::2, ::2], cmap=CMAP, vmin=0, vmax=6, interpolation="nearest")
        ax.set_axis_off()
        fig.text(0.04, 0.945, "Cruz Alta (RS): what each field did in winter", fontsize=14, weight="bold")
        fig.text(0.04, 0.905, "30 m pixels classed from the NDVI time series, Apr–Nov", fontsize=10, color=INK2)
        fig.text(0.96, 0.905, str(y), fontsize=34, weight="bold", ha="right", va="bottom")
        if tag(y, done):
            fig.text(0.96, 0.885, "provisional: imagery to 2 Nov", fontsize=9, color=INK2, ha="right", va="top")
        s = shares[y]
        bx = fig.add_axes([0.04, 0.095, 0.92, 0.035])
        left = 0.0
        for k in COL:
            w = s[f"{k}_pct"]
            bx.barh(0, w - 0.4, left=left, color=COL[k], height=1)
            if w >= 7:
                bx.text(
                    left + w / 2,
                    0,
                    f"{k} {w:.0f}%",
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=10,
                    weight="bold",
                )
            left += w
        bx.set_xlim(0, 100)
        bx.set_axis_off()
        fig.text(
            0.04,
            0.06,
            "T wheat-like cereal · C cover crop · P fallow · O other — grey: clouds",
            fontsize=9,
            color=INK2,
        )
        fig.text(0.04, 0.02, "Data: NASA HLS (L30 + S30) · ESA WorldCover 2021 · FieldShift", fontsize=8.5, color=MUTED)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=SURFACE)
        plt.close(fig)
        buf.seek(0)
        frames.append(Image.open(buf).convert("RGB").quantize(colors=64, method=Image.Quantize.MEDIANCUT))
    # 7 frames x 1.3 s = 9.1 s, loops
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=1300, loop=0, optimize=True)


def shares_fig(rows: list[dict], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6.6), dpi=100, facecolor=SURFACE)
    fig.subplots_adjust(left=0.07, right=0.70, top=0.84, bottom=0.16)
    ax.set_facecolor(SURFACE)
    x = np.arange(len(rows))
    bottom = np.zeros(len(rows))
    for k in COL:
        v = np.array([r[f"{k}_pct"] for r in rows])
        ax.bar(x, v - 0.6, bottom=bottom + 0.3, width=0.62, color=COL[k], label=LABEL[k])
        if k == "T":
            for xi, vi in zip(x, v, strict=True):
                ax.text(xi, 3, f"{vi:.0f}%", ha="center", va="bottom", color="white", fontsize=10, weight="bold")
        bottom += v
    pg = [r.get("pam_winter_grain_pct_of_soy") for r in rows]
    pw = [r.get("pam_wheat_pct_of_soy") for r in rows]
    xs = [xi for xi, v in zip(x, pg, strict=True) if v is not None]
    ax.plot(
        xs,
        [v for v in pg if v is not None],
        "D",
        ms=9,
        color=INK,
        mec=SURFACE,
        mew=2,
        label="IBGE PAM, all winter grains\n(% of soybean area)",
    )
    ax.plot(
        xs,
        [v for v in pw if v is not None],
        "o",
        ms=9,
        mfc=SURFACE,
        mec=INK,
        mew=2,
        label="IBGE PAM, wheat only\n(% of soybean area)",
    )
    ax.set_xticks(x, [str(r["year"]) for r in rows])
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of classified cropland pixels")
    ax.grid(axis="y", color="#e4e3df", lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=10)
    fig.text(
        0.07,
        0.93,
        "Winter paths of Cruz Alta cropland by year, and the official winter-grain area",
        fontsize=15,
        weight="bold",
    )
    fig.text(
        0.07,
        0.885,
        "Compare the T (bottom) segment with the markers. 2026 is provisional (imagery to 2 Nov); "
        "PAM has no 2026 value.",
        fontsize=10.5,
        color=INK2,
    )
    fig.text(0.07, 0.02, FOOT2, fontsize=7.5, color=MUTED)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def profiles_fig(prof: dict, out: Path) -> None:
    bins = prof["bins"]
    fig, axs = plt.subplots(1, 4, figsize=(15, 4.8), dpi=100, sharey=True, facecolor=SURFACE)
    fig.subplots_adjust(left=0.05, right=0.99, top=0.80, bottom=0.2, wspace=0.08)
    x = np.arange(len(bins))
    for ax, k in zip(axs, COL, strict=True):
        ax.set_facecolor(SURFACE)
        if k in prof:
            p = prof[k]
            ax.fill_between(x, p["p25"], p["p75"], color=COL[k], alpha=0.25, lw=0)
            ax.plot(x, p["median"], color=COL[k], lw=2)
            ax.set_title(f"{LABEL[k]}\nn = {p['n']:,} pixel-years", fontsize=10.5, loc="left")
        ax.axhline(0.5, color=MUTED, lw=0.8, ls="--")
        ax.axhline(0.4, color=MUTED, lw=0.8, ls=":")
        ax.set_xticks(x[::2], [b.split("-")[0] for b in bins[::2]], fontsize=9)
        ax.grid(axis="y", color="#e4e3df", lw=0.8)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axs[0].set_ylabel("NDVI (half-month median)")
    axs[0].set_ylim(0, 1)
    axs[0].text(0.2, 0.52, "green 0.5", fontsize=8, color=MUTED)
    axs[0].text(0.2, 0.33, "low 0.4", fontsize=8, color=MUTED)
    fig.text(
        0.05,
        0.92,
        "What each class looks like from space: median NDVI and interquartile band, 2020–2026",
        fontsize=14,
        weight="bold",
    )
    fig.text(0.05, 0.02, FOOT2, fontsize=7.5, color=MUTED)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def diversity_fig(raw: Path, inside, idx, shape, stats: dict, quads: list, out: Path) -> None:
    c = np.load(raw / "classes.npz")
    tr = Affine(*np.load(raw / "grid.npz")["transform"])
    rs, cs = crop_box(inside)
    fig = plt.figure(figsize=(14, 7.6), dpi=100, facecolor=SURFACE)
    fig.text(
        0.03,
        0.94,
        "Crop-diversity level of the ZARC-NM rule (IN SPA/MAPA 2/2025, indicator 6), as a satellite sees it",
        fontsize=15,
        weight="bold",
    )
    fig.text(
        0.03,
        0.905,
        "Per 30 m cropland pixel, last three winters; summer assumed soybean; "
        "level 4 needs 4 species, which NDVI cannot count",
        fontsize=10.5,
        color=INK2,
    )
    seq = ListedColormap([SURFACE, "#cde7e2", "#5fb3a6", "#0f5e54", NODATA, OUTSIDE_CROP])
    for k, win in enumerate(("2023-2025", "2024-2026")):
        a = np.where(inside.ravel(), 5, 0).astype(np.uint8)
        v = c[f"level_{win}"].copy()
        v[v == 0] = 4
        a[idx] = v
        ax = fig.add_axes([0.03 + k * 0.36, 0.08, 0.34, 0.78])
        ax.imshow(a.reshape(shape)[rs, cs], cmap=seq, vmin=0, vmax=5, interpolation="nearest")
        ax.set_axis_off()
        for q in quads:
            xs, ys = warp_transform("EPSG:4326", "EPSG:32622", [q["lon"]], [q["lat"]])
            col, row = ~tr * (xs[0], ys[0])
            col, row = col - cs.start, row - rs.start
            ax.plot(col, row, "s", ms=11, mfc="none", mec=INK, mew=2)
            lv = q["diversity_level_IN2_2025"][win]["level_majority_of_pixels"]
            ax.annotate(
                f"{q['quadrat_id']} {q['sequence_2020_2026']} L{lv}",
                (col, row),
                xytext=(8, 6),
                textcoords="offset points",
                fontsize=9,
                color=INK,
                bbox={"boxstyle": "round,pad=0.2", "fc": SURFACE, "ec": "none", "alpha": 0.85},
            )
        s = stats[win]["level_pct_of_those"]
        ax.set_title(
            f"Winters {win}:  L1 {s['1']:.0f}% · L2 {s['2']:.0f}% · L3 {s['3']:.0f}%", fontsize=11.5, loc="left"
        )
    lax = fig.add_axes([0.76, 0.3, 0.22, 0.5])
    lax.set_axis_off()
    lax.legend(
        handles=[
            Patch(facecolor="#cde7e2", label="Level 1: no winter crop in 3 years"),
            Patch(facecolor="#5fb3a6", label="Level 2: ≥ 4 crops, 2 families"),
            Patch(facecolor="#0f5e54", label="Level 3: ≥ 6 crops + long or\nrepeated cover crops"),
            Patch(facecolor=NODATA, label="Cropland, a winter not classified"),
            Patch(facecolor=OUTSIDE_CROP, label="Not cropland"),
        ],
        loc="upper left",
        frameon=False,
        fontsize=10.5,
    )
    fig.text(0.03, 0.02, FOOT, fontsize=8, color=MUTED)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    raw, res = Path(sys.argv[1]), Path(sys.argv[2])
    doc = json.loads((res / "rotation_fingerprint.json").read_text(encoding="utf-8"))
    rows = doc["shares_by_year"]
    shares = {r["year"]: r for r in rows}
    maps_, shape, idx, inside = rasters(raw)
    done = {y: c["season_complete"] for y, c in doc["coverage_by_year"].items()}
    maps(maps_, inside, shares, done, res / "rotation-fingerprint-maps.png")
    gif(maps_, inside, shares, done, res / "rotation-fingerprint.gif")
    shares_fig(rows, res / "rotation-fingerprint-vs-pam.png")
    profiles_fig(doc["ndvi_profiles_by_class"], res / "rotation-fingerprint-profiles.png")
    diversity_fig(
        raw,
        inside,
        idx,
        shape,
        doc["diversity_IN2_2025"]["by_window"],
        json.loads((res / "zarcnm_diversity_examples.json").read_text(encoding="utf-8"))["quadrats"],
        res / "rotation-diversity-zarcnm.png",
    )
    for f in sorted(res.glob("*.png")) + sorted(res.glob("*.gif")):
        print(f.name, f.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
