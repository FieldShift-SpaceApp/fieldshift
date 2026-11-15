# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Plain-PyTorch re-implementation (no mmsegmentation) of the NASA/IBM Prithvi-EO-1.0-100M multi-temporal crop
classification model, so its published checkpoint runs on a CPU.

Architecture copied from the official config `multi_temporal_crop_classification_Prithvi_100M.py` (Hugging Face
ibm-nasa-geospatial/Prithvi-EO-1.0-100M-multi-temporal-crop-classification) and the module code of
github.com/NASA-IMPACT/hls-foundation-os (geospatial_fm): TemporalViTEncoder (3 frames, 6 bands, 224 x 224,
patch 16, tubelet 1, embed 768, depth 6, 8 heads) -> ConvTransformerTokensToEmbeddingNeck (tokens to a 2304-channel
14 x 14 map, two x4 transposed-conv stages to 224 x 224) -> FCNHead (one 3x3 conv 256 + BN + ReLU, 1x1 to 13 CDL
classes). The auxiliary head is not used at inference. `load` refuses a checkpoint with missing or unexpected keys.
"""

from __future__ import annotations

import torch
from torch import nn

CLASSES = (
    "Natural Vegetation",
    "Forest",
    "Corn",
    "Soybeans",
    "Wetlands",
    "Developed/Barren",
    "Open Water",
    "Winter Wheat",
    "Alfalfa",
    "Fallow/Idle Cropland",
    "Cotton",
    "Sorghum",
    "Other",
)
# input normalisation of the official config (HLS reflectance x 10000), per band, same for the 3 frames
MEANS = [494.905781, 815.239594, 924.335066, 2968.881459, 2634.621962, 1739.579917]
STDS = [284.925432, 357.84876, 575.566823, 896.601013, 951.900334, 921.407808]
T, C, IMG, P, D, DEPTH, HEADS = 3, 6, 224, 16, 768, 6, 8


class Attention(nn.Module):  # timm vision_transformer.Attention, qkv_bias=True
    def __init__(self):
        super().__init__()
        self.qkv = nn.Linear(D, 3 * D)
        self.proj = nn.Linear(D, D)

    def forward(self, x):
        b, n, _ = x.shape
        q, k, v = self.qkv(x).reshape(b, n, 3, HEADS, D // HEADS).permute(2, 0, 3, 1, 4)
        x = nn.functional.scaled_dot_product_attention(q, k, v)
        return self.proj(x.transpose(1, 2).reshape(b, n, D))


class Mlp(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(D, 4 * D)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(4 * D, D)

    def forward(self, x):
        return self.fc2(self.act(self.fc1(x)))


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.norm1 = nn.LayerNorm(D)
        self.attn = Attention()
        self.norm2 = nn.LayerNorm(D)
        self.mlp = Mlp()

    def forward(self, x):
        x = x + self.attn(self.norm1(x))
        return x + self.mlp(self.norm2(x))


class PatchEmbed(nn.Module):
    def __init__(self):
        super().__init__()
        self.proj = nn.Conv3d(C, D, kernel_size=(1, P, P), stride=(1, P, P))

    def forward(self, x):  # (B, C, T, H, W) -> (B, T*14*14, D), tokens ordered (t, h, w)
        return self.proj(x).flatten(2).transpose(1, 2)


class Backbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.patch_embed = PatchEmbed()
        self.cls_token = nn.Parameter(torch.zeros(1, 1, D))
        self.pos_embed = nn.Parameter(torch.zeros(1, T * (IMG // P) ** 2 + 1, D), requires_grad=False)
        self.blocks = nn.ModuleList([Block() for _ in range(DEPTH)])
        self.norm = nn.LayerNorm(D)

    def forward(self, x):
        x = self.patch_embed(x) + self.pos_embed[:, 1:]
        cls = (self.cls_token + self.pos_embed[:, :1]).expand(x.shape[0], -1, -1)
        x = torch.cat((cls, x), 1)
        for blk in self.blocks:
            x = blk(x)
        return self.norm(x)


class Norm2d(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.ln = nn.LayerNorm(dim, eps=1e-6)

    def forward(self, x):
        return self.ln(x.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)


class Neck(nn.Module):
    def __init__(self):
        super().__init__()
        e = D * T
        self.fpn1 = nn.Sequential(nn.ConvTranspose2d(e, e, 2, 2), Norm2d(e), nn.GELU(), nn.ConvTranspose2d(e, e, 2, 2))
        self.fpn2 = nn.Sequential(nn.ConvTranspose2d(e, e, 2, 2), Norm2d(e), nn.GELU(), nn.ConvTranspose2d(e, e, 2, 2))

    def forward(self, x):
        x = x[:, 1:, :]  # drop cls token
        x = x.permute(0, 2, 1).reshape(x.shape[0], -1, IMG // P, IMG // P)  # (B, 768*3, 14, 14) as in the original
        return self.fpn2(self.fpn1(x))


class ConvBNReLU(nn.Module):  # mmcv ConvModule names: conv, bn
    def __init__(self, cin, cout):
        super().__init__()
        self.conv = nn.Conv2d(cin, cout, 3, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(cout)

    def forward(self, x):
        return torch.relu(self.bn(self.conv(x)))


class Head(nn.Module):
    def __init__(self):
        super().__init__()
        self.convs = nn.Sequential(ConvBNReLU(D * T, 256))
        self.conv_seg = nn.Conv2d(256, len(CLASSES), 1)

    def forward(self, x):
        f = self.convs(x)
        return self.conv_seg(f), f


class PrithviCrop(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = Backbone()
        self.neck = Neck()
        self.decode_head = Head()

    def forward(self, x):
        """x: (B, 6, 3, 224, 224) normalised. Returns logits (B, 13, 224, 224) and head features (B, 256, 224, 224)."""
        return self.decode_head(self.neck(self.backbone(x)))


def load(path: str) -> tuple[PrithviCrop, dict]:
    ck = torch.load(path, map_location="cpu", weights_only=False)
    sd = ck.get("state_dict", ck)
    sd = {k: v for k, v in sd.items() if not k.startswith("auxiliary_head.")}
    m = PrithviCrop()
    res = m.load_state_dict(sd, strict=False)
    missing = [k for k in res.missing_keys]
    unexpected = [k for k in res.unexpected_keys if not k.endswith("num_batches_tracked")]
    if missing or unexpected:
        raise RuntimeError(f"checkpoint mismatch: missing {missing[:10]}, unexpected {unexpected[:10]}")
    m.eval()
    # only short training facts; the checkpoint also stores the training machine's environment and full config
    keep = ("exp_name", "mmseg_version", "mmcv_version", "epoch", "iter", "time")
    meta = {k: v for k, v in ck.get("meta", {}).items() if k in keep} if isinstance(ck, dict) else {}
    return m, meta
