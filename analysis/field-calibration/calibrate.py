# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Re-fit the Embrapa NDTI -> straw-cover ruler with local field measurements, and show how the uncertainty falls.

    python -I calibrate.py [--measurements measurements/cruz_alta.csv] [--alpha 0.5]

Inputs: the 19 fields of Embrapa Documentos 454 (Cambe, PR) as the prior, and a measurement file in the public
format of ``measurements/README.md`` (one row per rope transect, with the NDTI already looked up by
``fetch_pixel.py``; no coordinates). Today the Cruz Alta file has a header and no rows: nobody has measured a
Cruz Alta field yet, so the posterior equals the prior and the script says so.

Writes to results/: calibration.json (prior, posterior, learning curves, power analysis, app parameters),
calibration.png (the ruler with its uncertainty) and uncertainty_by_n.png (how it falls per measurement).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

import bayes

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
IN_LIMITS = (30, 60, 90)  # IN SPA/MAPA 2/2025, Table 1, indicator 5 (straw cover in pre-sowing)
CRUZ_ALTA_NOGREEN_NDTI = (0.16, 0.18)  # median NDTI of no-green cropland pixels, ../residue-landsat/README.md
Z_A1 = 1.6449  # one-sided 5%
Z_A2 = 1.9600  # two-sided 5%
Z_B = 0.8416  # power 80%


def read_measurements(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if not r.get("id", "").startswith("#")]
    for col in ("lat", "lon", "latitude", "longitude"):
        if rows and col in rows[0]:
            raise SystemExit(f"{path} has a '{col}' column: public measurement files must not carry coordinates")
    out = []
    for r in rows:
        if not r.get("ndti") or not r.get("pct_straw"):
            continue
        if r.get("ndvi") and float(r["ndvi"]) >= 0.30:
            # Documentos 454 masks NDVI > 0.3: green plants hide the straw signal in SWIR
            print(f"skipped {r.get('id')}: NDVI {r['ndvi']} >= 0.30 (green canopy, not a straw reading)")
            continue
        out.append({"id": r.get("id", ""), "ndti": float(r["ndti"]), "pct_straw": float(r["pct_straw"])})
    return out


def ndti_at_cover(m: np.ndarray, cover: float) -> float:
    grid = np.linspace(0.0, bayes.NDTI_SAT, 2201)
    mean = bayes.basis(grid) @ m
    above = np.nonzero(mean >= cover)[0]
    return float(grid[above[0]]) if len(above) else float("nan")


def learning_curve_embrapa(n_orders: int = 400, seed: int = 454) -> dict:
    """Median ruler SD at the three IN limits as the 19 Embrapa fields are added one by one, random orders.

    Starts from a weak prior (coefficients ~ N(0, 100^2) on the u = 10 * NDTI basis). Uses the real Embrapa NDTI
    values, so it shows how a calibration of this kind tightens with n; it is not a Cruz Alta result.
    """
    x, _ = bayes.embrapa_xy()
    m0, s0, sigma = bayes.embrapa_posterior()
    weak = np.eye(3) * 100.0**2
    targets = [ndti_at_cover(m0, c) for c in IN_LIMITS]
    rng = np.random.default_rng(seed)
    sds = np.zeros((n_orders, len(x) + 1, len(targets)))
    for k in range(n_orders):
        order = rng.permutation(len(x))
        sds[k, 0] = bayes.curve_sd(weak, targets)
        for n in range(1, len(x) + 1):
            s = bayes.covariance_after(weak, x[order[:n]], sigma)
            sds[k, n] = bayes.curve_sd(s, targets)
    med = np.median(sds, axis=0)
    return {
        "prior": "weak: coefficients ~ N(0, 100^2) on the basis (1, u, u^2), u = 10 * min(NDTI, 0.110)",
        "orders": n_orders,
        "seed": seed,
        "targets_ndti": [round(t, 4) for t in targets],
        "targets_cover": list(IN_LIMITS),
        "n": list(range(len(x) + 1)),
        "median_sd_points": {f"C={c}%": [round(float(v), 2) for v in med[:, i]] for i, c in enumerate(IN_LIMITS)},
    }


def design_curves(alpha_list=(0.25, 0.5, 1.0), n_max: int = 40) -> dict:
    """Ruler SD after n new local measurements, from the transfer prior; needs only where the points fall."""
    m0, _, _ = bayes.embrapa_posterior()
    targets = [ndti_at_cover(m0, c) for c in IN_LIMITS]
    designs = {
        # most Cruz Alta no-till straw reads NDTI 0.16-0.18, above the plateau: these points inform the plateau
        "all_on_plateau": lambda n: np.full(n, 0.17),
        # a deliberate spread from ploughed to full straw (what a planned campaign would aim for)
        "spread_0.02_to_0.11": lambda n: np.linspace(0.02, 0.11, n) if n > 1 else np.array([0.065])[:n],
    }
    out = {
        "targets_ndti": [round(t, 4) for t in targets],
        "targets_cover": list(IN_LIMITS),
        "n": list(range(n_max + 1)),
    }
    for a in alpha_list:
        _, s0, sigma = bayes.transfer_prior(a)
        for name, f in designs.items():
            vals = []
            for n in range(n_max + 1):
                s = s0 if n == 0 else bayes.covariance_after(s0, f(n), sigma)
                vals.append([round(float(v), 2) for v in bayes.curve_sd(s, targets)])
            out[f"alpha={a}|{name}"] = vals
    return out


def power_analysis() -> dict:
    """How many measurements would separate straw-cover level 3 (60-90%) from level 4 (>= 90%)?

    That boundary is the straw part of NM3 vs NM4 (IN SPA/MAPA 2/2025, indicator 5); the NM level also needs the
    other indicators and the soil tests, so separating level 3 from 4 of straw is necessary, not sufficient.
    """
    x, y = bayes.embrapa_xy()
    _, s_emb, sigma = bayes.embrapa_posterior()
    delta = 5.0  # a field at 95% (or 85%) cover, 5 points from the 90% line
    z1 = Z_A1 + Z_B

    # (A) satellite + ruler, one field: the prediction SD never falls below sigma, however many calibration points
    p_correct_floor = 0.5 * (1 + math.erf(delta / sigma / math.sqrt(2)))
    sigma_needed = delta / z1

    # (B) does NDTI respond between ~85% and ~95% cover at all? inverse regression on the Embrapa fields >= 60%
    hi = y >= 60
    b, a = np.polyfit(y[hi], x[hi], 1)
    resid = x[hi] - (a + b * y[hi])
    sd_t = float(np.sqrt((resid**2).sum() / (hi.sum() - 2)))
    d_ndti = 10.0 * b
    n_per_group = math.ceil(2 * (Z_A2 + Z_B) ** 2 * sd_t**2 / d_ndti**2) if d_ndti > 0 else None

    # (C) the field itself: rope transects of 100 points, binomial error plus a between-rope (spatial) SD tau
    def ropes(p: float, tau: float) -> int:
        var1 = (100 * math.sqrt(p * (1 - p) / 100)) ** 2 + tau**2
        return math.ceil(z1**2 * var1 / delta**2)

    # Documentos 454 measured the same 19 fields by transect and by drone image: their disagreement is the only
    # published measure of method-to-method scatter for this protocol
    img = np.array([r[3] for r in bayes.embrapa.TABLE2], dtype=float)
    diff = y - img
    return {
        "question": "separate straw-cover level 3 (60-90%) from level 4 (>= 90%) for a field 5 points from the 90% "
        "line, one-sided 5% error, 80% power",
        "A_satellite_one_field": {
            "per_field_scatter_sigma_points": round(sigma, 2),
            "best_case_probability_of_right_side": round(p_correct_floor, 3),
            "sigma_needed_points": round(sigma_needed, 2),
            "verdict": "no number of calibration points is enough: the ruler's own uncertainty falls with n, but "
            "a single field scatters about the ruler by ~sigma (Embrapa: about 9 points), and NDTI saturates near "
            "80% cover, so the satellite alone cannot put one field above or below 90%",
        },
        "B_does_ndti_respond_85_vs_95": {
            "embrapa_fields_used": int(hi.sum()),
            "ndti_per_10_points_cover": round(d_ndti, 4),
            "ndti_residual_sd": round(sd_t, 4),
            "fields_per_group_needed": n_per_group,
            "groups": "fields measured near 85% and near 95% cover, two-sided 5%, 80% power",
            "note": "from the Cambe fields (the only published data); the Cruz Alta value is unknown until measured",
        },
        "C_ropes_per_field": {
            "binomial_sd_one_rope_points_at_90pct": round(100 * math.sqrt(0.9 * 0.1 / 100), 2),
            "ropes_needed_tau_0": ropes(0.9, 0.0),
            "ropes_needed_tau_5": ropes(0.9, 5.0),
            "ropes_needed_tau_10": ropes(0.9, 10.0),
            "tau": "between-rope SD in cover points inside one field (spatial variation); not measured in Cruz Alta",
            "embrapa_transect_minus_image_sd_points": round(float(diff.std(ddof=1)), 2),
            "embrapa_transect_minus_image_mean_points": round(float(diff.mean()), 2),
        },
        "embrapa_sigma_used": round(sigma, 2),
        "embrapa_curve_sd_at_90pct_points": round(float(bayes.curve_sd(s_emb, [bayes.embrapa.ndti_at(90)])[0]), 2),
    }


def figure_curve(m_post, s_post, s_prior, sigma, local: list[dict], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x, y = bayes.embrapa_xy()
    m_emb, s_emb, _ = bayes.embrapa_posterior()
    g = np.linspace(0.0, 0.20, 401)
    pe = bayes.predict(m_emb, s_emb, g, sigma)
    pp = bayes.predict(m_post, s_prior, g, sigma)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
    ax.axvspan(*CRUZ_ALTA_NOGREEN_NDTI, color="#e9d8a6", alpha=0.6, lw=0)
    ax.text(
        0.17,
        30,
        "Cruz Alta straw\ntoday (median\nNDTI of no-green\ncropland,\n0.16-0.18):\n0 field\nmeasurements",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#5a4a12",
        zorder=7,
    )
    ax.axvspan(bayes.NDTI_SAT, 0.20, color="#cccccc", alpha=0.25, lw=0)
    ax.fill_between(
        g,
        np.clip(pp["mean"] - 1.96 * pp["sd_field"], 0, 105),
        np.clip(pp["mean"] + 1.96 * pp["sd_field"], 0, 105),
        color="#9ecae1",
        alpha=0.35,
        lw=0,
        label="95% range for one new field (transfer prior)",
    )
    ax.fill_between(
        g,
        pp["mean"] - 1.96 * pp["sd_curve"],
        pp["mean"] + 1.96 * pp["sd_curve"],
        color="#3182bd",
        alpha=0.35,
        lw=0,
        label="95% band of the ruler, transfer prior (alpha = 0.5)",
    )
    ax.fill_between(
        g,
        pe["mean"] - 1.96 * pe["sd_curve"],
        pe["mean"] + 1.96 * pe["sd_curve"],
        color="#08519c",
        alpha=0.5,
        lw=0,
        label="95% band of the ruler, Cambe fields only",
    )
    ax.plot(g, pe["mean"], color="#08306b", lw=2, label="Embrapa ruler (quadratic, flat above NDTI 0.110)")
    ax.scatter(x, y, s=36, color="#d95f02", edgecolor="white", zorder=5, label="Embrapa DOC 454, 19 fields, Cambe PR")
    if local:
        ax.scatter(
            [r["ndti"] for r in local],
            [r["pct_straw"] for r in local],
            s=60,
            marker="D",
            color="#1b9e77",
            edgecolor="black",
            zorder=6,
            label=f"local measurements (n = {len(local)})",
        )
    for c, lab in zip(IN_LIMITS, ("level 1 | 2", "level 2 | 3", "level 3 | 4"), strict=True):
        ax.axhline(c, color="#555", lw=0.8, ls="--")
        ax.text(0.001, c + 1, f"C = {c}% ({lab}, IN 2/2025)", fontsize=8, color="#333")
    ax.set_xlim(0, 0.20)
    ax.set_ylim(0, 105)
    ax.set_xlabel("NDTI = (SWIR1 - SWIR2) / (SWIR1 + SWIR2)")
    ax.set_ylabel("straw cover C, % of the soil (rope transect)")
    ax.set_title("The straw ruler and its uncertainty: Embrapa fields as the prior, Cruz Alta slot empty", fontsize=11)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.95)
    fig.text(
        0.01,
        0.005,
        "Data: Embrapa Soja Documentos 454 (Franchini et al. 2023), Table 2; Sentinel-2 29 Oct 2021. "
        "Grey: above the Embrapa saturation, the ruler is held flat.",
        fontsize=7,
        color="#444",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def figure_by_n(design: dict, learning: dict, sigma: float, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=120)
    ax = axes[0]
    n = learning["n"]
    for c in IN_LIMITS:
        ax.plot(n, learning["median_sd_points"][f"C={c}%"], marker="o", ms=3, label=f"at C = {c}%")
    ax.axhline(sigma, color="#999", ls=":", lw=1)
    ax.text(19, sigma + 0.6, f"one field scatters ~{sigma:.1f} points\nabout any ruler", ha="right", fontsize=8)
    ax.set_ylim(0, 25)
    ax.set_xlabel("Embrapa fields added (random order, median of 400)")
    ax.set_ylabel("SD of the ruler, cover points")
    ax.set_title("How a calibration tightens: the 19 Cambe fields", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    nn = design["n"]
    idx = IN_LIMITS.index(90)
    styles = {0.25: ":", 0.5: "-", 1.0: "--"}
    for key, vals in design.items():
        if not key.startswith("alpha="):
            continue
        a = float(key.split("|")[0].split("=")[1])
        name = key.split("|")[1]
        color = "#1b9e77" if name.startswith("spread") else "#d95f02"
        ax.plot(nn, [v[idx] for v in vals], ls=styles[a], color=color, label=f"{name}, alpha = {a}")
    ax.set_xlabel("new Cruz Alta measurements (none exist yet)")
    ax.set_ylabel("SD of the ruler at C = 90%, cover points")
    ax.set_title("Cruz Alta, planned: uncertainty at the level 3 | 4 line", fontsize=10)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main(measurements: Path | None, alpha: float) -> None:
    RESULTS.mkdir(exist_ok=True)
    m_emb, s_emb, sigma = bayes.embrapa_posterior()
    m0, s0, _ = bayes.transfer_prior(alpha)
    local = read_measurements(measurements)
    if local:
        m1, s1 = bayes.update(m0, s0, [r["ndti"] for r in local], [r["pct_straw"] for r in local], sigma)
    else:
        m1, s1 = m0, s0
    print(f"local measurements: {len(local)}" + ("" if local else " (posterior = prior: nobody has measured yet)"))

    grid = np.round(np.linspace(0.0, 0.20, 41), 3)
    sd0 = bayes.curve_sd(s0, grid)
    sd1 = bayes.curve_sd(s1, grid)
    learning = learning_curve_embrapa()
    design = design_curves()
    power = power_analysis()
    one_point = {
        f"{xn:.3f}": round(float(np.mean(bayes.reduction_pct(s1, xn, sigma, np.linspace(0.0, 0.11, 23)))), 2)
        for xn in (0.02, 0.05, 0.08, 0.11, 0.17)
    }
    doc = {
        "run_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": {
            "equation": "C = b0 + b1*u + b2*u^2 + e, u = 10*min(NDTI, NDTI_SAT), e ~ N(0, sigma^2), sigma known",
            "ndti_sat": bayes.NDTI_SAT,
            "u_scale": bayes.SCALE,
            "sigma_points": round(sigma, 3),
            "alpha_power_prior": alpha,
            "prior_source": "Embrapa Soja Documentos 454 (2023), Table 2, 19 fields, Cambe PR, Sentinel-2 29/10/2021",
        },
        "embrapa_posterior": {"mean": m_emb.tolist(), "cov": s_emb.tolist()},
        "prior": {"mean": m0.tolist(), "cov": s0.tolist()},
        "local": {
            "file": str(measurements.relative_to(HERE)) if measurements else None,
            "n": len(local),
            "points": local,
            "status": "no Cruz Alta measurement exists yet; the slot is empty on purpose" if not local else "updated",
        },
        "posterior": {"mean": m1.tolist(), "cov": s1.tolist()},
        "ruler_sd_points": {
            "ndti": grid.tolist(),
            "prior": np.round(sd0, 2).tolist(),
            "posterior": np.round(sd1, 2).tolist(),
        },
        "one_more_point_mean_reduction_pct_over_ndti_0_0.11": one_point,
        "learning_curve_embrapa": learning,
        "design_curves_cruz_alta": design,
        "power_nm3_vs_nm4": power,
        "ndti_at_in_limits_embrapa": {f"C={c}%": round(ndti_at_cover(m_emb, c), 4) for c in IN_LIMITS},
        "caveats": [
            "the prior comes from another soil, region and sensor (Cambe PR, Sentinel-2); alpha is a choice",
            "NDTI_SAT is held at the Embrapa vertex, so local points above it inform only the plateau level",
            "sigma is held at the Embrapa residual SD; local scatter may differ",
            "straw cover is one of the ZarcNM indicators; the NM level also needs the others and the soil tests",
        ],
    }
    (RESULTS / "calibration.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    figure_curve(m1, s1, s0, sigma, local, RESULTS / "calibration.png")
    figure_by_n(design, learning, sigma, RESULTS / "uncertainty_by_n.png")
    print(json.dumps(power, indent=1))
    print("one more point, mean % reduction of ruler SD over NDTI 0-0.11:", one_point)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--measurements", type=Path, default=HERE / "measurements" / "cruz_alta.csv")
    ap.add_argument("--alpha", type=float, default=0.5)
    a = ap.parse_args()
    main(a.measurements, a.alpha)
