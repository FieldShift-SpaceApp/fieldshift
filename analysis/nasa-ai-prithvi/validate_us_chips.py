# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Sanity check of the plain-PyTorch re-implementation on the model's own validation chips (US, CDL labels).

    python -I validate_us_chips.py <validation_chips_dir> <checkpoint.pth> <results_dir>

Reads the first chips of `validation_chips.tgz` of the Hugging Face dataset
ibm-nasa-geospatial/multi-temporal-crop-classification (pairs `chip_*_merged.tif` + `chip_*.mask.tif`) and reports
pixel accuracy for two channel orders: (a) the official mmseg pipeline (`Reshape` of the 18 file channels, stored
time-major, straight to 6 x 3, as in the config), (b) the semantic order bands x frames. The order that reproduces
the published accuracy (aAcc 60.6% on the full validation set) is the one the model was trained with, and is the
one run_prithvi.py uses.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import prithvi_crop as pc  # noqa: E402


def to_input(x18: np.ndarray, order: str) -> torch.Tensor:
    """x18: (18, H, W) file order (time-major: t*6 + band). Returns (1, 6, 3, H, W) normalised."""
    m = np.tile(pc.MEANS, 3)[:, None, None]
    s = np.tile(pc.STDS, 3)[:, None, None]
    z = ((x18.astype("float32") - m) / s).astype("float32")
    if order == "official_reshape":
        z = z.reshape(6, 3, *z.shape[1:])
    else:  # semantic: [band, frame]
        z = z.reshape(3, 6, *z.shape[1:]).transpose(1, 0, 2, 3)
    return torch.from_numpy(np.ascontiguousarray(z))[None]


def main() -> None:
    d, ckpt, res = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    model, _ = pc.load(ckpt)
    chips = sorted(p for p in d.glob("chip_*_merged.tif") if not p.name.startswith("._"))
    chips = [p for p in chips if (d / p.name.replace("_merged.tif", ".mask.tif")).exists()][:40]
    out = {"chips": len(chips)}
    for order in ("official_reshape", "semantic"):
        ok = tot = 0
        with torch.inference_mode():
            for p in chips:
                with rasterio.open(p) as src:
                    x = src.read()
                with rasterio.open(d / p.name.replace("_merged.tif", ".mask.tif")) as src:
                    y = src.read(1).astype(int) - 1  # reduce_zero_label: 0 -> ignore, 1..13 -> 0..12
                lg, _ = model(to_input(x, order))
                pred = lg[0].argmax(0).numpy()
                v = (y >= 0) & (y < 13)
                ok += int((pred[v] == y[v]).sum())
                tot += int(v.sum())
        out[order] = {"pixel_accuracy": round(ok / tot, 4), "pixels": tot}
        print(order, out[order], flush=True)
    out["published_aAcc_full_validation_set"] = 0.6064
    out["source"] = "https://huggingface.co/datasets/ibm-nasa-geospatial/multi-temporal-crop-classification"
    (res / "us_validation_check.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
