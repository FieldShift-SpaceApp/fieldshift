# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""The Embrapa ruler: NDTI -> % of soil covered by crop residue, from Embrapa Soja Documentos 454 (2023).

VENDORED COPY of analysis/residue-landsat/embrapa.py (branch surgeon/residue-landsat, PR #54, commit 8a09cbf), kept
identical so this folder runs before that PR is merged; replace with an import once it is on main.


Source: Franchini, J.C.; Debiasi, H.; Balbinot Junior, A.A.; Farias, J.R.B.; Monteiro, J.E.B.A.; Santos, E.L.;
Sartori, A.A.C.; Leonardo, H.C.L. (2023). "Sensoriamento remoto para avaliar o historico de culturas, cobertura do
solo com palha e tempo sem revolvimento do solo em areas agricolas, para uso no Zarc Niveis de Manejo". Londrina:
Embrapa Soja, 33 p. (Documentos 454). The 19 data pairs below are transcribed with citation (facts, not text).
https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1156802/1/DOC-454.pdf (accessed 2026-11-15).

Two conversions are published there:
  1. Field-free, per image (Beeson et al. 2020), pp. 21-23: CR = m * NDTI + b, m = (CRmax - CRmin) /
     (NDTImax - NDTImin), b = -m * NDTImin, with NDTImin / NDTImax = image mean -/+ 3 standard deviations,
     CRmin = 0 %, CRmax = 100 %. Classes there: < 45, 45-60, 60-75, > 75 % (the 2023 criteria table of that
     document, not the classes of IN SPA/MAPA 2/2025).
  2. Field calibration, pp. 25-29: 19 fields in Cambe (PR), Sentinel-2 image of 29/10/2021, residue cover by
     the line-transect method (15 m rope, marks every 15 cm) and by drone image, NDVI > 0.3 masked. The document
     plots a second-order polynomial (Figure 12) and states that NDTI saturates at about 80 % cover, but does not
     print the coefficients; its Table 2 prints the 19 (NDTI, cover) pairs. The quadratic below is fitted here to
     that published table (transect cover), by ordinary least squares.

Conditions, not those of Cruz Alta: north Parana (Cambe), clayey Latossolo, corn and wheat residue, Sentinel-2,
one date in October 2021. Applying it to Cruz Alta (Planalto Medio, RS), to Landsat TM/ETM+/OLI and to HLS is a
transfer without local calibration.
"""

from __future__ import annotations

import numpy as np

# Embrapa Documentos 454, Table 2 (p. 26): field, NDTI (Sentinel-2, 29/10/2021), cover % by transect, by image
TABLE2 = [
    (1, 0.046, 55, 67),
    (2, 0.054, 77, 73),
    (3, 0.079, 82, 90),
    (4, 0.065, 90, 96),
    (5, 0.061, 61, 76),
    (6, 0.052, 78, 90),
    (7, 0.060, 71, 68),
    (8, 0.032, 43, 53),
    (9, 0.047, 44, 37),
    (10, 0.059, 66, 72),
    (11, 0.061, 73, 64),
    (12, 0.055, 56, 61),
    (13, 0.024, 20, 35),
    (14, 0.019, 6, 10),
    (15, 0.015, 5, 10),
    (16, 0.077, 92, 97),
    (17, 0.095, 97, 100),
    (18, 0.101, 96, 99),
    (19, 0.068, 66, 75),
]
SATURATION_COVER = 80.0  # "plato de saturacao do indice NDTI ao redor de 80% de cobertura" (p. 29)
IN_C_BANDS = ((90, 4), (60, 3), (30, 2), (0, 1))  # IN SPA/MAPA 2/2025, Table 1, indicator 5
DOC454_BANDS = (45, 60, 75)  # Documentos 454 classes (2023 criteria)


def fit() -> dict:
    x = np.array([r[1] for r in TABLE2])
    y = np.array([r[2] for r in TABLE2], dtype=float)
    a, b, c = np.polyfit(x, y, 2)
    pred = np.polyval([a, b, c], x)
    r2 = 1 - float(((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum())
    rmse = float(np.sqrt(((y - pred) ** 2).mean()))
    xv = -b / (2 * a)
    return {
        "a": float(a),
        "b": float(b),
        "c": float(c),
        "r2": r2,
        "rmse_points": rmse,
        "n": len(TABLE2),
        "vertex_ndti": float(xv),
        "vertex_cover": float(np.polyval([a, b, c], xv)),
    }


FIT = fit()


def cover(ndti) -> np.ndarray:
    """Residue cover % from NDTI with the quadratic fitted to Table 2; flat beyond the vertex, clipped 0-100."""
    x = np.minimum(np.asarray(ndti, dtype=float), FIT["vertex_ndti"])
    return np.clip(FIT["a"] * x * x + FIT["b"] * x + FIT["c"], 0.0, 100.0)


def ndti_at(cover_pct: float) -> float:
    a, b, c = FIT["a"], FIT["b"], FIT["c"] - cover_pct
    roots = [r.real for r in np.roots([a, b, c]) if abs(r.imag) < 1e-12 and r.real <= FIT["vertex_ndti"]]
    return float(max(roots))


def in_level(c: float) -> int:
    for lo, lv in IN_C_BANDS:
        if c >= lo:
            return lv
    return 1


def in_class_label(c: float) -> str:
    lv = in_level(c)
    if c >= SATURATION_COVER:
        return f"level 3 or 4 (C = {c:.0f}% is above the ~80% NDTI saturation; 60-90 vs >= 90 not separable)"
    return f"level {lv} (C = {c:.0f}%)"


def summary() -> dict:
    return {
        "source": "Embrapa Soja, Documentos 454 (2023), Table 2 (19 fields, Cambe PR, Sentinel-2 29/10/2021, "
        "transect cover), quadratic fitted here; saturation near 80% stated on p. 29",
        "url": "https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1156802/1/DOC-454.pdf",
        "equation": f"C = {FIT['a']:.1f} * NDTI^2 + {FIT['b']:.1f} * NDTI + {FIT['c']:.2f}, flat at "
        f"{FIT['vertex_cover']:.1f}% above NDTI {FIT['vertex_ndti']:.3f}, clipped to 0-100",
        "fit_r2": round(FIT["r2"], 3),
        "fit_rmse_points": round(FIT["rmse_points"], 1),
        "n_fields": FIT["n"],
        "ndti_at_in_class_limits": {f"C={c}%": round(ndti_at(c), 4) for c in (30, 60, 80, 90)},
        "conditions": "north Parana (Cambe), clayey Latossolo, corn and wheat residue, Sentinel-2, one date; not "
        "Cruz Alta, not Landsat TM/ETM+/OLI, not HLS: transferred without local calibration",
    }
