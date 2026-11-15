# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Run the NASA/IBM Prithvi crop model on the Cruz Alta window and compare it with the rule-based winter classes.

    python -I run_prithvi.py <raw_dir> <checkpoint.pth> <results_dir>

1. Zero-shot: the published 13-class CDL head (fine-tuned on US 2022 HLS + USDA CDL, no Brazilian data), sliding
   224 x 224 windows with stride 112 over the 448 x 448 window (the test_cfg of the official config), logits averaged.
2. Agreement with the rules of analysis/rotation-fingerprint, pixel by pixel, on cropland pixels that the rules
   classified and that are clear (Fmask) on all three input dates: the full 13 x 4 cross-table, and the binary
   table "Winter Wheat" (Prithvi) against T (rules). Mapping fixed before looking at the result: T = Winter Wheat,
   P = Fallow/Idle Cropland, everything else is "not wheat"; CDL has no cover-crop class.
3. Linear probe (experiment): multinomial logistic regression with the rule classes as WEAK labels (T, C, O; P is
   merged into O, it is < 1% of the cropland) on (a) the 256 per-pixel features of the Prithvi head, (b) the 2304
   per-pixel features of its neck (backbone tokens brought to 30 m) and (c) the 18
   raw band values of the same three dates, trained on 40,000 pixels of the west half of the window and tested on
   30,000 pixels of the east half
   (spatial hold-out). It measures how well three dates seen through Prithvi reproduce the 16-half-month rules;
   it is not an accuracy, the labels are themselves a hypothesis.
Writes prithvi_vs_rules.json, crosstab_cdl_x_rules.csv and prithvi-vs-rules.png to <results_dir>; prediction rasters
to <raw_dir>/prithvi_out.npz (never committed).
"""

from __future__ import annotations

import csv
import json
import platform
import sys
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import prithvi_crop as pc  # noqa: E402

N, W, STRIDE = 448, 224, 112
NONE, WHEAT, COVER, FALLOW, OTHER = 0, 1, 2, 3, 4  # codes of analysis/rotation-fingerprint/classify.py
RULE = {WHEAT: "T", COVER: "C", FALLOW: "P", OTHER: "O"}
WW, FALLOW_CDL = pc.CLASSES.index("Winter Wheat"), pc.CLASSES.index("Fallow/Idle Cropland")
PAM_2024 = {"winter_grains_pct_of_soy": 38.2, "wheat_pct_of_soy": 27.1}  # rotation-fingerprint winter_paths_by_year


def kappa(cm: np.ndarray) -> float:
    n = cm.sum()
    po = np.trace(cm) / n
    pe = (cm.sum(0) * cm.sum(1)).sum() / n**2
    return float((po - pe) / (1 - pe))


def infer(model, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """x (3, 6, N, N) int16 reflectance x 10000 -> logits (13, N, N), features (256, N, N)."""
    xf = x.astype("float32")
    bad = (x <= -9999) | (x == -9999)
    m = np.array(pc.MEANS, dtype="float32")[None, :, None, None]
    s = np.array(pc.STDS, dtype="float32")[None, :, None, None]
    z = np.where(bad, 0.0, (xf - m) / s).astype("float32")  # (3, 6, N, N), no-data -> band mean
    # The official mmseg pipeline reshapes the 18 file channels (time-major, t*6 + band) straight to (6, 3): the model
    # was trained on that order, so it is reproduced here (validate_us_chips.py: 56.6% pixel accuracy on 40 official
    # US validation chips with this order, 16.9% with the semantic band x frame order).
    z = z.reshape(18, N, N).reshape(6, 3, N, N)
    logit = np.zeros((13, N, N), "float32")
    feat = np.zeros((256, N, N), "float32")
    cnt = np.zeros((N, N), "float32")
    with torch.inference_mode():
        for r in range(0, N - W + 1, STRIDE):
            for c in range(0, N - W + 1, STRIDE):
                t = torch.from_numpy(np.ascontiguousarray(z[:, :, r : r + W, c : c + W]))[None]
                lg, f = model(t)
                logit[:, r : r + W, c : c + W] += lg[0].numpy()
                feat[:, r : r + W, c : c + W] += f[0].numpy()
                cnt[r : r + W, c : c + W] += 1
    return logit / cnt, feat / cnt


def neck_features(model, x: np.ndarray, pix: np.ndarray) -> np.ndarray:
    """2304-channel neck output (backbone tokens brought to 30 m by the fine-tuned neck) at flat pixel indices pix,
    from the four non-overlapping 224 x 224 chips (same input order as infer)."""
    m = np.array(pc.MEANS, dtype="float32")[None, :, None, None]
    s = np.array(pc.STDS, dtype="float32")[None, :, None, None]
    z = np.where(x <= -9999, 0.0, (x.astype("float32") - m) / s).astype("float32").reshape(18, N, N).reshape(6, 3, N, N)
    rows, cols = np.divmod(pix, N)
    out = np.zeros((pix.size, 2304), "float32")
    with torch.inference_mode():
        for r in (0, W):
            for c in (0, W):
                sel = (rows >= r) & (rows < r + W) & (cols >= c) & (cols < c + W)
                t = torch.from_numpy(np.ascontiguousarray(z[:, :, r : r + W, c : c + W]))[None]
                f = model.neck(model.backbone(t))[0].numpy()
                out[sel] = f[:, rows[sel] - r, cols[sel] - c].T
    return out


def probe(Xtr: np.ndarray, ytr: np.ndarray, Xte: np.ndarray, yte: np.ndarray) -> tuple[dict, object]:
    """Multinomial logistic regression on standardised features; returns metrics on the test pixels and the model."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=1.0, class_weight="balanced"))
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte)
    labs = sorted(set(yte) | set(pred))
    cm = np.array([[int(((yte == a) & (pred == b)).sum()) for b in labs] for a in labs])
    return {
        "labels": [RULE[int(v)] for v in labs],
        "confusion_rows_rules_cols_probe": cm.tolist(),
        "agreement": round(float(np.trace(cm) / cm.sum()), 4),
        "kappa": round(kappa(cm), 4),
        "features": int(Xtr.shape[1]),
        "train_pixels": int(Xtr.shape[0]),
        "test_pixels": int(Xte.shape[0]),
    }, clf


def probe_indices(valid: np.ndarray, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Spatial hold-out: train on the west half of the window, test on the east half (random pixel samples)."""
    rng = np.random.default_rng(seed)
    cols = np.tile(np.arange(N), N)
    tr = np.flatnonzero(valid.ravel() & (cols < N // 2))
    te = np.flatnonzero(valid.ravel() & (cols >= N // 2))
    return np.sort(rng.choice(tr, min(40000, tr.size), replace=False)), np.sort(
        rng.choice(te, min(30000, te.size), replace=False)
    )


def main() -> None:
    raw, ckpt, res = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    res.mkdir(parents=True, exist_ok=True)
    win = np.load(raw / "window.npz")
    h6 = np.load(raw / "hls6.npz")
    gj = json.loads((raw / "granules.json").read_text(encoding="utf-8"))
    cls, crop = win["cls"], win["crop"]
    torch.set_num_threads(max(1, (torch.get_num_threads())))
    t0 = time.time()
    model, meta = pc.load(ckpt)
    logit, feat = infer(model, h6["x"])
    run_s = time.time() - t0
    pred = logit.argmax(0).astype(np.uint8)
    prob = torch.softmax(torch.from_numpy(logit), 0).numpy()

    clear3 = h6["clear"].all(0)
    valid = crop & (cls != NONE) & clear3
    n = int(valid.sum())
    # 13 x 4 cross-table
    cross = {pc.CLASSES[k]: {RULE[r]: int(((pred == k) & (cls == r) & valid).sum()) for r in RULE} for k in range(13)}
    with (res / "crosstab_cdl_x_rules.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["prithvi_cdl_class", "rules_T", "rules_C", "rules_P", "rules_O", "total", "pct_of_compared"])
        for k, row in cross.items():
            tot = sum(row.values())
            w.writerow([k, row["T"], row["C"], row["P"], row["O"], tot, round(100 * tot / n, 2)])
    # binary wheat table
    pw, rw = (pred == WW)[valid], (cls == WHEAT)[valid]
    cm = np.array([[int((rw & pw).sum()), int((rw & ~pw).sum())], [int((~rw & pw).sum()), int((~rw & ~pw).sum())]])
    binary = {
        "rows_rules_cols_prithvi": ["T / Winter Wheat", "not T / not Winter Wheat"],
        "matrix": cm.tolist(),
        "agreement": round(float(np.trace(cm) / n), 4),
        "kappa": round(kappa(cm), 4),
        "rules_T_share": round(float(rw.mean()), 4),
        "prithvi_winter_wheat_share": round(float(pw.mean()), 4),
        "prithvi_ww_among_rules_T": round(float(pw[rw].mean()), 4) if rw.any() else None,
        "prithvi_ww_among_rules_C": round(float((pred == WW)[valid & (cls == COVER)].mean()), 4),
        "mean_prob_winter_wheat_rules_T": round(float(prob[WW][valid & (cls == WHEAT)].mean()), 4),
        "mean_prob_winter_wheat_rules_C": round(float(prob[WW][valid & (cls == COVER)].mean()), 4),
    }
    # linear probes, spatial hold-out (west half train, east half test), same pixels for every feature set
    y = np.where(cls == FALLOW, OTHER, cls).ravel()
    itr, ite = probe_indices(valid)
    np.savez_compressed(raw / "probe_idx.npz", train=itr, test=ite, y=y)
    Xf = feat.reshape(256, -1).T
    xr = h6["x"].astype("float32").reshape(18, -1).T
    pr_f, clf_f = probe(Xf[itr], y[itr], Xf[ite], y[ite])
    pr_r, clf_r = probe(xr[itr], y[itr], xr[ite], y[ite])
    xn_tr, xn_te = neck_features(model, h6["x"], itr), neck_features(model, h6["x"], ite)
    pr_n, _ = probe(xn_tr, y[itr], xn_te, y[ite])
    map_f = clf_f.predict(Xf).astype(np.uint8)
    map_r = clf_r.predict(xr).astype(np.uint8)
    np.savez_compressed(
        raw / "prithvi_out.npz", pred=pred, probe_feat=map_f.reshape(N, N), probe_raw=map_r.reshape(N, N)
    )
    # post-hoc observation (NOT the pre-set mapping): how the rule classes fall into the CDL class "Other"
    oth = pred == pc.CLASSES.index("Other")
    binary["posthoc_share_in_cdl_other"] = {RULE[r]: round(float(oth[valid & (cls == r)].mean()), 4) for r in RULE}

    rules_share = {RULE[r]: round(float((cls == r)[valid].mean()), 4) for r in RULE}
    doc = {
        "run_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": {
            "name": "Prithvi-EO-1.0-100M multi-temporal crop classification (NASA/IBM)",
            "hugging_face": "https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-1.0-100M-multi-temporal-crop-classification",
            "file": "multi_temporal_crop_classification_Prithvi_100M.pth",
            "license": "Apache-2.0",
            "doi": "10.57967/hf/0954",
            "fine_tuned_on": "US HLS 2022 chips + USDA CDL labels, 13 classes (no Brazilian data, no cover-crop class)",
            "checkpoint_meta": meta,
            "runtime": "CPU, plain PyTorch re-implementation (prithvi_crop.py), no mmsegmentation",
            "inference_seconds": round(run_s, 1),
        },
        "input": gj["prithvi_input"],
        "window": gj["window"],
        "window_cropland_share": round(gj["cropland_share"], 4),
        "year": int(win["year"]),
        "compared_pixels": n,
        "compared_rule": "cropland (WorldCover >= 50%), classified by the rules, clear in Fmask on all three dates",
        "rules_shares_in_compared": rules_share,
        "prithvi_shares_in_compared_top": dict(
            sorted(
                {pc.CLASSES[k]: round(float((pred == k)[valid].mean()), 4) for k in range(13)}.items(),
                key=lambda kv: -kv[1],
            )
        ),
        "binary_wheat": binary,
        "linear_probe_prithvi_features": pr_f,
        "linear_probe_prithvi_neck_features": pr_n,
        "linear_probe_raw_18_bands": pr_r,
        "pam_2024_municipality_reference": PAM_2024
        | {"note": "IBGE PAM is for the whole municipality, the window is 13.4 km x 13.4 km: level check only"},
        "cannot_say": [
            "No field labels: every number is agreement between two methods, not accuracy.",
            "The Prithvi head was fine-tuned on US CDL 2022 (northern-hemisphere calendar, US winter wheat); "
            "applied to a southern-hemisphere winter it is out of its training domain.",
            "CDL has no cover-crop class, so cover crops (black oat) can only fall into other classes.",
            "The linear probe learns the rule labels; high agreement means Prithvi features from 3 dates can reproduce "
            "the rules, not that either is right.",
            "One window, one year, three dates: not representative of the municipality.",
        ],
        "libraries": {
            "python": platform.python_version(),
            **{p: version(p) for p in ("torch", "numpy", "scikit-learn", "rasterio", "matplotlib")},
        },
    }
    (res / "prithvi_vs_rules.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("compared_pixels", "rules_shares_in_compared", "binary_wheat")}, indent=1))
    print("top prithvi:", list(doc["prithvi_shares_in_compared_top"].items())[:6])
    for k_, v_ in (("head256", pr_f), ("neck2304", pr_n), ("raw18", pr_r)):
        print("probe", k_, v_["agreement"], v_["kappa"])
    figure(h6, cls, crop, valid, pred, map_f.reshape(N, N), doc, res / "prithvi-vs-rules.png")


def figure(h6, cls, crop, valid, pred, probe_map, doc, out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    col = {"T": "#c8902b", "C": "#3f8f4f", "P": "#9a8f84", "O": "#7d6fb0", "none": "#ffffff"}
    k = int(np.flatnonzero(h6["periods"] == "Sep")[0])
    x = h6["x"][k].astype("float32")
    rgb = np.stack([x[4], x[3], x[2]], -1)  # SWIR1, NIR, red false colour
    lo, hi = np.percentile(rgb[crop], 2, axis=0), np.percentile(rgb[crop], 98, axis=0)
    rgb = np.clip((rgb - lo) / (hi - lo), 0, 1)

    def to_rgb(codes: np.ndarray) -> np.ndarray:
        cm = {1: col["T"], 2: col["C"], 3: col["P"], 4: col["O"]}
        img = np.ones((N, N, 3))
        for c, hx in cm.items():
            img[codes == c] = matplotlib.colors.to_rgb(hx)
        img[~crop] = 0.93
        return img

    zs = np.where(pred == WW, 1, np.where(pred == FALLOW_CDL, 3, 4)).astype(np.uint8)
    zs[~valid] = 0
    rl = np.where(valid, cls, 0)
    pb = np.where(valid, probe_map, 0)
    b = doc["binary_wheat"]
    fig, ax = plt.subplots(1, 4, figsize=(16, 4.9), dpi=110)
    panels = [
        (rgb, f"NASA HLS {doc['input'][k]['date']} (SWIR1-NIR-red)"),
        (to_rgb(rl), f"Rules, 16 half-months ({doc['year']})"),
        (to_rgb(zs), "Prithvi zero-shot (US CDL head)"),
        (to_rgb(pb), "Prithvi features + linear probe\n(trained W half on rule labels)"),
    ]
    for a, (img, t) in zip(ax, panels, strict=True):
        a.imshow(img, interpolation="nearest")
        a.set_title(t, fontsize=10)
        a.set_xticks([])
        a.set_yticks([])
    ax[3].axvline(N / 2, color="k", lw=0.8, ls="--")
    ax[3].text(N * 0.52, 15, "test", fontsize=8)
    ax[3].text(N * 0.02, 15, "train", fontsize=8)
    leg = [
        Patch(color=col[c], label=lbl)
        for c, lbl in (
            ("T", "T wheat-like / CDL Winter Wheat"),
            ("C", "C cover crop"),
            ("P", "P fallow / CDL Fallow"),
            ("O", "O other / any other CDL class"),
        )
    ]
    fig.legend(handles=leg, loc="lower center", ncol=4, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 0.06))
    pf, pr = doc["linear_probe_prithvi_features"], doc["linear_probe_raw_18_bands"]
    fig.suptitle(
        f"Cruz Alta (RS), winter {doc['year']}, 13.4 km window: NASA/IBM Prithvi vs phenological rules\n"
        f"Zero-shot (US CDL classes): T agreement {b['agreement']:.0%}, kappa {b['kappa']:.2f} (no useful class). "
        f"Probe on held-out east half: Prithvi features {pf['agreement']:.0%} (kappa {pf['kappa']:.2f}), "
        f"same 3 dates as raw bands {pr['agreement']:.0%} (kappa {pr['kappa']:.2f})",
        fontsize=10.5,
    )
    fig.text(
        0.5,
        0.015,
        "Data: NASA HLS v2.0 (L30/S30) via Planetary Computer; ESA WorldCover 2021 cropland mask. "
        "Model: Prithvi-EO-1.0-100M crop classification (NASA/IBM, Apache-2.0). Agreement between two methods, "
        "no field labels.",
        ha="center",
        fontsize=7.5,
        color="#444",
    )
    fig.subplots_adjust(left=0.01, right=0.99, top=0.80, bottom=0.14, wspace=0.03)
    fig.savefig(out)
    print("figure", out)


if __name__ == "__main__":
    main()
