# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Bayesian re-fit of the Embrapa NDTI -> straw-cover ruler, with the 19 Cambe fields as the prior.

Model (the same shape as ../residue-landsat/embrapa.py, written as a Bayesian linear regression):

    C = b0 + b1 * u + b2 * u^2 + e,    u = 10 * min(NDTI, NDTI_SAT),    e ~ Normal(0, sigma^2)

* NDTI_SAT = 0.110 is the vertex of the quadratic fitted to Embrapa Documentos 454, Table 2: above it the ruler is
  flat (the document states that NDTI saturates near 80% cover). It is held fixed here, so a Cruz Alta field with
  NDTI 0.17 informs the plateau level, not the shape beyond it (a limitation, see README).
* sigma is held fixed at the residual standard deviation of the Embrapa fit (SSE / (n - 3)). With sigma known the
  model is conjugate: the posterior is Normal and its covariance does not depend on the measured cover, only on
  where (at which NDTI) the measurements are. That is what lets the app say "your point would reduce the
  uncertainty by X%" before the rope is laid.
* Prior for another region: the Embrapa posterior with its covariance divided by alpha (a power prior; alpha = 0.5
  means the 19 Parana fields count as 9.5 local ones). alpha is a choice, not a measurement; 0.25 and 1 are run too.

Only numpy. Every function takes and returns plain arrays so the same algebra can be re-written in the app.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "residue-landsat"))
import embrapa  # noqa: E402  (Table 2 of Documentos 454, on main)

NDTI_SAT = round(embrapa.FIT["vertex_ndti"], 3)  # 0.110
SCALE = 10.0  # u = 10 * NDTI keeps the normal equations well conditioned
VAGUE_SD = 1e4


def basis(ndti) -> np.ndarray:
    u = SCALE * np.minimum(np.asarray(ndti, dtype=float), NDTI_SAT)
    return np.stack([np.ones_like(u), u, u * u], axis=-1)


def embrapa_xy() -> tuple[np.ndarray, np.ndarray]:
    x = np.array([r[1] for r in embrapa.TABLE2], dtype=float)
    y = np.array([r[2] for r in embrapa.TABLE2], dtype=float)
    return x, y


def residual_sd(x: np.ndarray, y: np.ndarray) -> float:
    phi = basis(x)
    beta, *_ = np.linalg.lstsq(phi, y, rcond=None)
    sse = float(((y - phi @ beta) ** 2).sum())
    return float(np.sqrt(sse / (len(y) - phi.shape[1])))


def update(m0: np.ndarray, s0: np.ndarray, x, y, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    """Conjugate Normal update with known sigma. Returns posterior mean and covariance."""
    phi = basis(np.atleast_1d(x))
    y = np.atleast_1d(np.asarray(y, dtype=float))
    p0 = np.linalg.inv(s0)
    p1 = p0 + phi.T @ phi / sigma**2
    s1 = np.linalg.inv(p1)
    m1 = s1 @ (p0 @ m0 + phi.T @ y / sigma**2)
    return m1, (s1 + s1.T) / 2


def covariance_after(s0: np.ndarray, x, sigma: float) -> np.ndarray:
    """Posterior covariance after measurements at NDTI values x (the cover values are not needed)."""
    phi = basis(np.atleast_1d(x))
    s1 = np.linalg.inv(np.linalg.inv(s0) + phi.T @ phi / sigma**2)
    return (s1 + s1.T) / 2


def curve_sd(s: np.ndarray, ndti) -> np.ndarray:
    """Standard deviation of the mean curve (the ruler itself) at each NDTI."""
    phi = basis(ndti)
    return np.sqrt(np.einsum("...i,ij,...j->...", phi, s, phi))


def predict(m: np.ndarray, s: np.ndarray, ndti, sigma: float) -> dict:
    phi = basis(ndti)
    mean = phi @ m
    sd_curve = curve_sd(s, ndti)
    return {"mean": mean, "sd_curve": sd_curve, "sd_field": np.sqrt(sd_curve**2 + sigma**2)}


def embrapa_posterior() -> tuple[np.ndarray, np.ndarray, float]:
    x, y = embrapa_xy()
    sigma = residual_sd(x, y)
    m, s = update(np.zeros(3), np.eye(3) * VAGUE_SD**2, x, y, sigma)
    return m, s, sigma


def transfer_prior(alpha: float = 0.5) -> tuple[np.ndarray, np.ndarray, float]:
    m, s, sigma = embrapa_posterior()
    return m, s / alpha, sigma


def reduction_pct(s0: np.ndarray, x_new, sigma: float, at) -> np.ndarray:
    """% fall of the ruler's standard deviation at NDTI `at` from one more measurement at NDTI x_new."""
    s1 = covariance_after(s0, x_new, sigma)
    return 100.0 * (1.0 - curve_sd(s1, at) / curve_sd(s0, at))
