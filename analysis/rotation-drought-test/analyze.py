# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Rotation x drought test at 30 m: soybean NDVI after a cover crop (C) vs after a wheat-like cereal (T).

    python -I analyze.py <summer_raw_dir> <fingerprint_raw_dir> <results_dir>

Implements the pre-registered method of README.md: half-month median NDVI composites October-March per pixel and
summer (2020/21-2025/26) from NASA HLS, outcomes (mean NDVI January-February; peak December-February), a summer
green-up half-month as planting-date proxy, and fixed-effect regressions of the outcome on the winter class of
analysis/rotation-fingerprint (pixel FE, 1 km block x summer FE, planting-date stratum x summer FE), with standard
errors clustered by block, placebos (future winter; fake drought summers) and robustness runs.
"""

from __future__ import annotations

import json
import sys
import warnings
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

SUMMERS = list(range(2020, 2026))  # summer Y/Y+1 follows winter Y
DROUGHT = {2021, 2022}  # 2021/22 and 2022/23, fixed before the run (README, pre-registration)
NB = 12  # half-months Oct-1 (0) .. Mar-2 (11)
BIN_NAMES = [f"{m}-{h}" for m in ("Oct", "Nov", "Dec", "Jan", "Feb", "Mar") for h in (1, 2)]
NOV1, DEC1, DEC2, JAN1, FEB1, FEB2 = 2, 4, 5, 6, 8, 9
GREEN = 0.50  # same green threshold as the fingerprint rules
NODATA = -32768
BLOCK = 33  # 33 x 33 pixels of 30 m = 990 m
NONE, WHEAT, COVER, FALLOW, OTHER = 0, 1, 2, 3, 4  # fingerprint class codes
STRATA = ["<=Nov-1", "Nov-2", "Dec-1", "Dec-2", "Jan-1", ">=Jan-2", "none"]
CONS_COVER_MAX_U, CONS_WHEAT_MIN_U = 4, 7  # winter green-up bins (fingerprint): Jun-1 and Jul-2


def bin_of(d: str) -> tuple[int, int] | None:
    y, m, day = int(d[:4]), int(d[5:7]), int(d[8:10])
    if 4 <= m <= 9:
        return None
    summer = y if m >= 10 else y - 1
    k = (m - 10) if m >= 10 else (m + 2)
    return summer, k * 2 + (0 if day <= 15 else 1)


def granules(raw: Path) -> list[tuple[str, Path]]:
    idx = json.loads((raw / "scene_index.json").read_text(encoding="utf-8"))["granules"]
    out = []
    for g in idx:
        p = raw / "ndvi" / f"{g['id']}.npz"
        if g.get("status") == "ok" and p.exists():
            out.append((g["date"], p))
    return out


def composites(files: list[tuple[str, Path]], n: int) -> tuple[dict, dict]:
    by = defaultdict(list)
    for d, p in files:
        sb = bin_of(d)
        if sb and sb[0] in SUMMERS:
            by[sb].append(p)
    comp, count = {}, {}
    for s in SUMMERS:
        md = np.full((NB, n), NODATA, dtype=np.int16)
        for b in range(NB):
            ps = by.get((s, b), [])
            if not ps:
                continue
            f = np.stack([np.load(p)["ndvi"] for p in ps]).astype("float32")
            f[f == NODATA] = np.nan
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                m = np.nanmedian(f, axis=0)
            md[b] = np.where(np.isfinite(m), np.round(m), NODATA).astype(np.int16)
        comp[s] = md
        count[s] = [len(by.get((s, b), [])) for b in range(NB)]
        print(s, "granules per half-month", count[s], flush=True)
    return comp, count


def fill(comp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    v = np.where(comp == NODATA, np.nan, comp.astype("float32") / 10000)
    valid = np.isfinite(v)
    idx = np.arange(NB)[:, None]
    prev = np.maximum.accumulate(np.where(valid, idx, -1), axis=0)
    nxt = np.minimum.accumulate(np.where(valid, idx, NB)[::-1], axis=0)[::-1]
    vp = np.take_along_axis(v, np.clip(prev, 0, NB - 1), 0)
    vn = np.take_along_axis(v, np.clip(nxt, 0, NB - 1), 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        lin = vp + (vn - vp) * (idx - prev) / (nxt - prev)
    out = np.where(valid, v, np.where((prev >= 0) & (nxt < NB), lin, np.where(prev >= 0, vp, vn)))
    eligible = (valid.sum(0) >= 8) & (valid[JAN1 : FEB2 + 1].sum(0) >= 2) & valid[NOV1 : DEC2 + 1].any(0)
    return out.astype("float32"), eligible


def metrics(v: np.ndarray) -> dict:
    idx = np.arange(NB)[:, None]
    gap = v[: DEC2 + 1].argmin(0)  # lowest half-month Oct-1 .. Dec-2: between winter canopy and summer crop
    up = (idx > gap) & (idx <= FEB1) & (v >= GREEN)
    g = np.where(up.any(0), up.argmax(0), 99)
    stratum = np.select([g <= NOV1, g == 3, g == DEC1, g == DEC2, g == JAN1, g <= FEB1], [0, 1, 2, 3, 4, 5], 6)
    return {
        "y_mean_janfeb": v[JAN1 : FEB2 + 1].mean(0),
        "y_peak_decfeb": v[DEC1 : FEB2 + 1].max(0),
        "stratum": stratum.astype(np.int8),
    }


# ---------------------------------------------------------------- fixed-effect OLS with block-clustered errors


def demean(cols: np.ndarray, groups: list[np.ndarray], tol: float = 1e-9, it: int = 200) -> np.ndarray:
    x = cols.copy()
    sizes = [np.bincount(g) for g in groups]
    for _ in range(it):
        delta = 0.0
        for g, sz in zip(groups, sizes, strict=True):
            for j in range(x.shape[1]):
                mu = np.bincount(g, weights=x[:, j], minlength=sz.size) / np.maximum(sz, 1)
                x[:, j] -= mu[g]
                delta = max(delta, float(np.abs(mu).max()))
        if delta < tol:
            break
    return x


def fe_ols(y: np.ndarray, x: np.ndarray, groups: list[np.ndarray], cluster: np.ndarray) -> dict:
    groups = [np.unique(g, return_inverse=True)[1] for g in groups]
    z = demean(np.column_stack([y, x]).astype("float64"), groups)
    yd, xd = z[:, 0], z[:, 1:]
    xtx = xd.T @ xd
    beta = np.linalg.solve(xtx, xd.T @ yd)
    e = yd - xd @ beta
    cl = np.unique(cluster, return_inverse=True)[1]
    ng = cl.max() + 1
    s = np.column_stack([np.bincount(cl, weights=xd[:, j] * e, minlength=ng) for j in range(xd.shape[1])])
    n, k = xd.shape
    inv = np.linalg.inv(xtx)
    vcov = inv @ (s.T @ s) @ inv * (ng / (ng - 1)) * ((n - 1) / (n - k))
    return {"beta": beta, "vcov": vcov, "n": int(n), "clusters": int(ng)}


def lin(fit: dict, w: list[float]) -> dict:
    w = np.array(w, dtype="float64")
    b = float(w @ fit["beta"])
    se = float(np.sqrt(w @ fit["vcov"] @ w))
    return {"est": round(b, 4), "se": round(se, 4), "ci95": [round(b - 1.96 * se, 4), round(b + 1.96 * se, 4)]}


# ---------------------------------------------------------------- main


def main() -> None:
    sraw, fraw, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    gz = np.load(fraw / "grid.npz")
    idx, shape = gz["idx"], tuple(int(s) for s in gz["shape"])
    n = idx.size
    r, c = idx // shape[1], idx % shape[1]
    block = (r // BLOCK) * (shape[1] // BLOCK + 1) + (c // BLOCK)
    cls = np.load(fraw / "classes.npz")

    cache = sraw / "summer_metrics.npz"
    files = granules(fraw) + granules(sraw)
    if cache.exists():
        mt = dict(np.load(cache))
        count = json.loads((sraw / "summer_counts.json").read_text(encoding="utf-8"))
    else:
        comp, count = composites(files, n)
        mt = {}
        for s in SUMMERS:
            v, ok = fill(comp[s])
            m = metrics(v)
            mt[f"ok_{s}"] = ok
            for k, a in m.items():
                mt[f"{k}_{s}"] = a
            del v
        np.savez_compressed(cache, **mt)
        (sraw / "summer_counts.json").write_text(json.dumps(count), encoding="utf-8")

    # ---- panel
    rows = defaultdict(list)
    for s in SUMMERS:
        k = cls[f"cls_{s}"]
        fut = cls[f"cls_{s + 1}"]
        hist = np.zeros(n)
        nh = np.zeros(n)
        for w in range(2020, s + 1):
            cw = cls[f"cls_{w}"]
            hist += cw == COVER
            nh += cw != NONE
        keep = mt[f"ok_{s}"] & (k != NONE)
        rows["pix"].append(np.flatnonzero(keep))
        rows["summer"].append(np.full(keep.sum(), s, dtype=np.int16))
        rows["cls"].append(k[keep])
        rows["fut"].append(fut[keep])
        rows["u"].append(cls[f"u_{s}"][keep])
        rows["hist"].append((hist / np.maximum(nh, 1))[keep])
        for m in ("y_mean_janfeb", "y_peak_decfeb", "stratum"):
            rows[m].append(mt[f"{m}_{s}"][keep])
    P = {k: np.concatenate(v) for k, v in rows.items()}
    P["blk"] = block[P["pix"]]
    P["drought"] = np.isin(P["summer"], list(DROUGHT)).astype("float64")
    P["C"] = (P["cls"] == COVER).astype("float64")
    P["O"] = np.isin(P["cls"], [OTHER, FALLOW]).astype("float64")
    P["T"] = (P["cls"] == WHEAT).astype("float64")
    P["bxs"] = P["blk"].astype(np.int64) * 10 + (P["summer"] - 2020)
    P["gxs"] = P["stratum"].astype(np.int64) * 10 + (P["summer"] - 2020)
    N = P["pix"].size
    print(f"panel {N:,} pixel-summers, {np.unique(P['pix']).size:,} pixels", flush=True)

    def run(mask, y="y_mean_janfeb", treat=("C", "O"), dvar="drought", direct=True, src=None):
        src = src or P
        m = mask
        x = []
        for t in treat:
            x.append(src[t][m])
        for t in treat:
            x.append(src[t][m] * src[dvar][m])
        groups = [src["pix"][m], src["bxs"][m]] + ([src["gxs"][m]] if direct else [])
        fit = fe_ols(src[y][m], np.column_stack(x), groups, src["blk"][m])
        kk = len(treat)
        w_norm = [1.0] + [0.0] * (2 * kk - 1)
        w_dr = [1.0] + [0.0] * (kk - 1) + [1.0] + [0.0] * (kk - 1)
        w_int = [0.0] * kk + [1.0] + [0.0] * (kk - 1)
        return {
            "n": fit["n"],
            "pixels": int(np.unique(src["pix"][m]).size),
            "blocks": fit["clusters"],
            "C_minus_T_normal": lin(fit, w_norm),
            "C_minus_T_drought": lin(fit, w_dr),
            "protection_d_C": lin(fit, w_int),
        }

    allm = np.ones(N, dtype=bool)
    res: dict = {"models": {}, "placebos": {}, "robustness": {}}
    res["models"]["M1_total"] = run(allm, direct=False)
    print("M1", res["models"]["M1_total"], flush=True)
    res["models"]["M2_direct"] = run(allm)
    print("M2", res["models"]["M2_direct"], flush=True)

    # common support of the planting-date proxy: strata with >= 10% of both C and T pixel-summers
    share = {}
    for name, t in (("C", P["C"] == 1), ("T", P["T"] == 1)):
        share[name] = (np.bincount(P["stratum"][t], minlength=7) / t.sum()).round(4).tolist()
    common = [i for i in range(7) if share["C"][i] >= 0.10 and share["T"][i] >= 0.10]
    res["planting_date"] = {
        "strata": STRATA,
        "share_by_class_all_summers": share,
        "common_support_strata": [STRATA[i] for i in common],
    }
    by_summer = {}
    for s in SUMMERS:
        d = {}
        for name, code in (("T", [WHEAT]), ("C", [COVER]), ("O", [OTHER, FALLOW])):
            t = (P["summer"] == s) & np.isin(P["cls"], code)
            d[name] = (np.bincount(P["stratum"][t], minlength=7) / max(t.sum(), 1)).round(4).tolist()
        by_summer[f"{s}/{str(s + 1)[2:]}"] = d
    res["planting_date"]["share_by_class_and_summer"] = by_summer
    res["models"]["M3_matched"] = run(np.isin(P["stratum"], common), direct=False)
    res["models"]["M3_matched"]["strata"] = [STRATA[i] for i in common]
    print("M3", res["models"]["M3_matched"], flush=True)

    # per-summer cross-sectional contrast: block FE + stratum FE, one summer at a time
    per = {}
    for s in SUMMERS:
        m = P["summer"] == s
        fit = fe_ols(
            P["y_mean_janfeb"][m],
            np.column_stack([P["C"][m], P["O"][m]]),
            [P["blk"][m], P["stratum"][m]],
            P["blk"][m],
        )
        fit0 = fe_ols(P["y_mean_janfeb"][m], np.column_stack([P["C"][m], P["O"][m]]), [P["blk"][m]], P["blk"][m])
        per[f"{s}/{str(s + 1)[2:]}"] = {
            "drought": s in DROUGHT,
            "n": fit["n"],
            "C_minus_T_within_block_and_planting_stratum": lin(fit, [1, 0]),
            "C_minus_T_within_block_only": lin(fit0, [1, 0]),
            "mean_ndvi_janfeb": {
                k: round(float(P["y_mean_janfeb"][m & (P[k] == 1)].mean()), 4) for k in ("T", "C", "O")
            },
            "share": {k: round(float(P[k][m].mean()), 4) for k in ("T", "C", "O")},
        }
    res["per_summer"] = per
    print("per summer", json.dumps(per, indent=0)[:1500], flush=True)

    # placebo P1: class of the following winter (Y+1)
    Q = dict(P)
    okf = P["fut"] != NONE
    Q["C"] = (P["fut"] == COVER).astype("float64")
    Q["O"] = np.isin(P["fut"], [OTHER, FALLOW]).astype("float64")
    res["placebos"]["P1_future_winter_total"] = run(okf, direct=False, src=Q)
    res["placebos"]["P1_future_winter_direct"] = run(okf, src=Q)
    print("P1", res["placebos"]["P1_future_winter_direct"], flush=True)

    # placebo P2: fake drought among the normal summers
    normal = ~np.isin(P["summer"], list(DROUGHT))
    fake = {}
    for f in sorted(set(SUMMERS) - DROUGHT):
        P["fake"] = (P["summer"] == f).astype("float64")
        fake[f"{f}/{str(f + 1)[2:]}"] = run(normal, dvar="fake")["protection_d_C"]
    res["placebos"]["P2_fake_drought_direct_d_C"] = fake
    print("P2", fake, flush=True)

    # robustness
    hm = P["summer"] >= 2021
    res["robustness"]["R1_cover_history_share_direct"] = run(hm, treat=("hist",))
    res["robustness"]["R1_cover_history_share_direct"]["note"] = (
        "treatment = share of cover-crop winters 2020..Y; 'C_minus_T' rows read as the effect of going from 0 to 1"
    )
    cons = ~(((P["cls"] == COVER) & (P["u"] > CONS_COVER_MAX_U)) | ((P["cls"] == WHEAT) & (P["u"] < CONS_WHEAT_MIN_U)))
    res["robustness"]["R2_conservative_classes_direct"] = run(cons)
    res["robustness"]["R2_conservative_classes_direct"]["dropped_share"] = round(float(1 - cons.mean()), 4)
    res["robustness"]["R3_peak_decfeb_total"] = run(allm, y="y_peak_decfeb", direct=False)
    res["robustness"]["R3_peak_decfeb_direct"] = run(allm, y="y_peak_decfeb")
    loo = {}
    for s in SUMMERS:
        loo[f"drop {s}/{str(s + 1)[2:]}"] = run(P["summer"] != s)["protection_d_C"]
    res["robustness"]["R4_leave_one_summer_out_direct_d_C"] = loo
    print("R", json.dumps(res["robustness"], indent=0)[:2500], flush=True)

    # decision rule (README, fixed before the run)
    d = res["models"]["M2_direct"]["protection_d_C"]
    p1 = res["placebos"]["P1_future_winter_direct"]["protection_d_C"]["est"]
    rule = {
        "M2_d_C_ci_above_zero": d["ci95"][0] > 0,
        "M2_d_C_above_every_fake_d_C": all(d["est"] > v["est"] for v in fake.values()),
        "P1_less_than_half_of_d_C": abs(p1) < 0.5 * abs(d["est"]) if d["est"] else False,
    }
    rule["supported"] = all(rule.values())
    res["decision_rule"] = rule

    res["meta"] = {
        "run_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "outcome_primary": "mean NDVI of Jan-1..Feb-2 half-month median composites (NASA HLS L30+S30)",
        "outcome_secondary": "peak NDVI Dec-1..Feb-2",
        "drought_summers": [f"{s}/{str(s + 1)[2:]}" for s in sorted(DROUGHT)],
        "summers": [f"{s}/{str(s + 1)[2:]}" for s in SUMMERS],
        "block_m": BLOCK * 30,
        "half_months": BIN_NAMES,
        "granules_per_half_month": count,
        "granules_used": len(files),
        "panel_pixel_summers": int(N),
        "panel_pixels": int(np.unique(P["pix"]).size),
        "eligible_share_by_summer": {f"{s}/{str(s + 1)[2:]}": round(float(mt[f"ok_{s}"].mean()), 4) for s in SUMMERS},
        "class_share_in_panel": {k: round(float(P[k].mean()), 4) for k in ("T", "C", "O")},
    }
    (out / "rotation_drought_test.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    # small per-summer table for the figure and the README
    lines = ["summer,drought,n,share_T,share_C,ndvi_T,ndvi_C,ndvi_O,CminusT_block,se,CminusT_block_planting,se"]
    for k, v in per.items():
        a, b = v["C_minus_T_within_block_only"], v["C_minus_T_within_block_and_planting_stratum"]
        lines.append(
            f"{k},{int(v['drought'])},{v['n']},{v['share']['T']},{v['share']['C']},"
            f"{v['mean_ndvi_janfeb']['T']},{v['mean_ndvi_janfeb']['C']},{v['mean_ndvi_janfeb']['O']},"
            f"{a['est']},{a['se']},{b['est']},{b['se']}"
        )
    (out / "per_summer.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("decision", rule, flush=True)


if __name__ == "__main__":
    main()
