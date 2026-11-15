# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Linear probe on the embeddings of the NASA/IBM foundation model itself (Prithvi-EO-2.0-100M-TL, pre-trained on
4.2 M NASA HLS samples, never fine-tuned on crop labels), on the same pixels and weak labels as run_prithvi.py.

    python -I foundation_probe.py <raw_dir> <prithvi2_dir> <results_dir>

<prithvi2_dir> holds the files of huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-100M-TL: config.json,
Prithvi_EO_V2_100M_TL.pt and code/prithvi_mae.py (the official model code, Apache-2.0, not copied here).
Input: the same three HLS dates (Blue, Green, Red, Narrow NIR, SWIR 1, SWIR 2), normalised with the model's own
mean/std, with temporal coordinates (year, day of year) and location coordinates passed as in the official
inference.py (rasterio lnglat order). Embedding: last encoder layer, the 768-d token of each 16 x 16 patch for each
of the 3 frames (2304-d), bilinearly upsampled from 14 x 14 to 224 x 224 per chip (4 non-overlapping chips).
Writes foundation_probe.json to <results_dir>.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import torch
from rasterio.transform import Affine, xy
from rasterio.warp import transform as warp_transform

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_prithvi import RULE, probe  # noqa: E402

N, W = 448, 224


def main() -> None:
    raw, p2, res = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    sys.path.insert(0, str(p2 / "code"))
    from prithvi_mae import PrithviMAE  # official code of the Hugging Face repository

    cfg = json.loads((p2 / "config.json").read_text(encoding="utf-8"))["pretrained_cfg"]
    cfg = {**cfg, "num_frames": 3}
    mean, std = np.array(cfg.pop("mean"), "float32"), np.array(cfg.pop("std"), "float32")
    for k in ("bands", "origin_url", "paper_ids"):
        cfg.pop(k, None)
    model = PrithviMAE(**cfg)
    sd = torch.load(p2 / "Prithvi_EO_V2_100M_TL.pt", map_location="cpu", weights_only=True)
    for k in list(sd):  # fixed sin-cos position embeddings are rebuilt for 3 frames, as in the official inference.py
        if k == "encoder.pos_embed":
            sd[k] = model.encoder.pos_embed
        elif k == "decoder.decoder_pos_embed":
            sd[k] = model.decoder.decoder_pos_embed
    model.load_state_dict(sd, strict=True)
    enc = model.encoder.eval()

    h6 = np.load(raw / "hls6.npz")
    win = np.load(raw / "window.npz")
    idx = np.load(raw / "probe_idx.npz")
    x = h6["x"].astype("float32")  # (3, 6, N, N)
    z = np.where(h6["x"] <= -9999, 0.0, (x - mean[None, :, None, None]) / std[None, :, None, None]).astype("float32")
    z = z.transpose(1, 0, 2, 3)  # (6, 3, N, N): C, T, H, W as in the official inference.py
    tc = []
    for gid in h6["ids"]:
        d = str(gid).split(".")[3]  # e.g. 2024205T133841
        tc.append([int(d[:4]), int(d[4:7])])
    tr = Affine(*win["transform"][:6])
    cx, cy = xy(tr, N // 2, N // 2)
    lon, lat = warp_transform("EPSG:32622", "EPSG:4326", [cx], [cy])
    tcoords = torch.tensor([tc], dtype=torch.float32)
    lcoords = torch.tensor([[lon[0], lat[0]]], dtype=torch.float32)

    pix = np.concatenate([idx["train"], idx["test"]])
    rows, cols = np.divmod(pix, N)
    feats = np.zeros((pix.size, 2304), "float32")
    t0 = time.time()
    with torch.inference_mode():
        for r in (0, W):
            for c in (0, W):
                t = torch.from_numpy(np.ascontiguousarray(z[:, :, r : r + W, c : c + W]))[None]
                tok = enc.forward_features(t, tcoords, lcoords)[-1][:, 1:, :]  # (1, 3*196, 768)
                g = tok.reshape(1, 3, 14, 14, 768).permute(0, 1, 4, 2, 3).reshape(1, 2304, 14, 14)
                up = torch.nn.functional.interpolate(g, size=(W, W), mode="bilinear", align_corners=False)[0].numpy()
                sel = (rows >= r) & (rows < r + W) & (cols >= c) & (cols < c + W)
                feats[sel] = up[:, rows[sel] - r, cols[sel] - c].T
    secs = time.time() - t0
    # fair baseline at the same scale: the 18 raw band values averaged over each 16 x 16 patch, same bilinear upsampling
    base = np.zeros((pix.size, 18), "float32")
    zz = torch.from_numpy(np.ascontiguousarray(z.transpose(1, 0, 2, 3).reshape(18, N, N)))[None]
    for r in (0, W):
        for c in (0, W):
            g = torch.nn.functional.avg_pool2d(zz[:, :, r : r + W, c : c + W], 16)
            up = torch.nn.functional.interpolate(g, size=(W, W), mode="bilinear", align_corners=False)[0].numpy()
            sel = (rows >= r) & (rows < r + W) & (cols >= c) & (cols < c + W)
            base[sel] = up[:, rows[sel] - r, cols[sel] - c].T
    y = idx["y"]
    ntr = idx["train"].size
    metrics, _ = probe(feats[:ntr], y[idx["train"]], feats[ntr:], y[idx["test"]])
    base_metrics, _ = probe(base[:ntr], y[idx["train"]], base[ntr:], y[idx["test"]])
    doc = {
        "run_date": date.today().isoformat(),
        "model": "Prithvi-EO-2.0-100M-TL (NASA/IBM), pre-trained encoder only, no crop fine-tuning",
        "hugging_face": "https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-100M-TL",
        "license": "Apache-2.0",
        "checkpoint_sha256": "d45406d5fc51af1d9657d48f2e2c3ff077408a2e1113f9a242889a4fe4469b17",
        "temporal_coords_year_doy": tc,
        "location_coords_lon_lat": [round(lon[0], 4), round(lat[0], 4)],
        "embedding": "last encoder layer, 768-d x 3 frames per 16 x 16 patch (480 m), bilinear to 30 m",
        "encoder_seconds_cpu": round(secs, 1),
        "labels_note": "weak labels = rule classes T / C / O (P merged into O); spatial hold-out west/east halves",
        "linear_probe": metrics,
        "baseline_raw18_at_patch_scale": base_metrics,
        "classes": list(RULE.values()),
    }
    (res / "foundation_probe.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(
        "foundation",
        metrics["agreement"],
        metrics["kappa"],
        "| raw18 at 480 m",
        base_metrics["agreement"],
        base_metrics["kappa"],
    )


if __name__ == "__main__":
    main()
