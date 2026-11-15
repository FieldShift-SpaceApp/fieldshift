# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Where should one public real be spent? Soil-test vouchers for the ZarcNM soybean subsidy (pure functions).

Input: one row per CAR property of the farm-reports pre-check (analysis/farm-reports), with its cropland area, size
and the satellite-side NM it reaches for each soil-test outcome. Output: who gets a free soil test for a given budget
and objective, and what that is expected to unlock. No network, no imagery, no personal data.

Every number that is not read from the farm-reports run is an ASSUMPTION and lives in `Assumptions`, with its source
or the word "assumption" next to it. See README.md.
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass, field

# CGSR 111/2026 (2026/27 soybean pilot): share of the premium paid by the federal subsidy, by ZarcNM level.
SUBSIDY_BY_NM = {1: 0.20, 2: 0.30, 3: 0.35, 4: 0.40}
SUBSIDY_BASELINE = 0.20  # standard soybean subsidy without a classification (Plano Trienal; = NM1 in CGSR 111/2026)
SMALL_HA = 50.0  # "small" = declared area < 50 ha (the PSR policy-size cut used in docs/research/verifica-impacto.md)

OBJECTIVES = ("subsidy", "protected", "families")


@dataclass(frozen=True)
class Assumptions:
    """Every input that does not come from the satellite pre-check. Defaults and their sources: README.md."""

    # P(the three soil indicators V%, Ca, m% come back at level >= 3). No published distribution for RS soybean
    # fields was found: scenario 0.3 / 0.5 / 0.7 (assumption).
    p_soil_favourable: float = 0.5
    # Of the favourable outcomes, the share at level 4 (the rest at level 3). Assumption.
    share_level4_given_favourable: float = 0.5
    # Unfavourable outcome: the three soil indicators at this level (2 -> IN 2/2025 lock IV-b caps at NM2). Assumption.
    soil_level_unfavourable: int = 2
    # P(contour sowing on >= 75% of the area is confirmed) where the mean slope is >= 3% (IN 2/2025 item 3.2.1-I).
    # farm-reports assumes 1.0; not observable from space. Assumption.
    p_contour_confirmed: float = 1.0
    # PSR soybean premium, R$/ha: RS average 2024 (MAPA SISSER via docs/research/verifica-impacto.md); Cruz Alta 408.
    premium_brl_ha: float = 488.0
    # Soil-test outlay per sampling area of <= 10 ha (IN 2/2025 items 7.2-7.9): two chemical analyses (0-20 and
    # 20-40 cm) at R$ 50 + one texture analysis at R$ 40 (UFPel price list, via verifica-impacto.md).
    sample_area_ha: float = 10.0
    chem_price_brl: float = 50.0
    texture_price_brl: float = 40.0
    # Sampling visit / accredited operator: no public price. 0 by default; a sensitivity, not a value.
    fixed_cost_per_farm_brl: float = 0.0
    # Which end of the satellite-side NM range counts: "lower" (conservative, as farm-reports' "ready") or "upper".
    range_end: str = "lower"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Farm:
    """One property, anonymous. `nm_by_soil[s]` = (nm_min, nm_max) with the three soil indicators at level s."""

    idx: int
    cropland_ha: float
    declared_ha: float
    size_class: str
    assessed: bool
    contour_needed: bool = True
    straw_share: float = 1.0  # share of the cropland seen without green that read as straw (farm-reports C)
    nm_by_soil: dict[int, tuple[int, int]] = field(default_factory=dict)

    @property
    def small(self) -> bool:
        return self.declared_ha < SMALL_HA


@dataclass(frozen=True)
class Outcome:
    """Expected result of giving one farm a soil test."""

    cost_brl: float
    p_nm3plus: float
    p_nm4: float
    subsidy_gain_brl: float  # per year, (subsidy at level - 20%) x premium x cropland, expected
    subsidy_total_brl: float  # per year, full subsidy at level x premium x cropland, expected (pilot-budget draw)


def soil_test_cost(cropland_ha: float, a: Assumptions) -> float:
    """Lab outlay of the first year: ceil(area / 10 ha) sampling areas x (2 chemical + 1 texture) + fixed cost."""
    areas = max(1, math.ceil(cropland_ha / a.sample_area_ha - 1e-9))
    return areas * (2 * a.chem_price_brl + a.texture_price_brl) + a.fixed_cost_per_farm_brl


def soil_distribution(a: Assumptions) -> dict[int, float]:
    p, q = a.p_soil_favourable, a.share_level4_given_favourable
    if not (0 <= p <= 1 and 0 <= q <= 1):
        raise ValueError("probabilities must be in [0, 1]")
    return {4: p * q, 3: p * (1 - q), a.soil_level_unfavourable: 1 - p}


def outcome(f: Farm, a: Assumptions) -> Outcome:
    cost = soil_test_cost(f.cropland_ha, a)
    if not f.assessed:
        raise ValueError("outcome() needs an assessed farm; use pooled outcomes for the others")
    end = 0 if a.range_end == "lower" else 1
    p_contour = a.p_contour_confirmed if f.contour_needed else 1.0
    p3 = p4 = gain = total = 0.0
    for s, ps in soil_distribution(a).items():
        if ps == 0:
            continue
        nm = f.nm_by_soil[s][end]
        p3 += ps * (nm >= 3)
        p4 += ps * (nm == 4)
        gain += ps * (SUBSIDY_BY_NM[nm] - SUBSIDY_BASELINE)
        total += ps * SUBSIDY_BY_NM[nm]
    # contour not confirmed on a slope >= 3% -> NM1 (gain 0, subsidy at the baseline 20%)
    total = p_contour * total + (1 - p_contour) * SUBSIDY_BY_NM[1]
    money = a.premium_brl_ha * f.cropland_ha
    return Outcome(cost, p_contour * p3, p_contour * p4, p_contour * gain * money, total * money)


def pooled_outcome(f: Farm, a: Assumptions, rate_by_size: dict[str, dict[str, float]]) -> Outcome:
    """A farm without the satellite pre-check gets the per-hectare averages of the assessed farms of its size class.

    Used only for the first-come baseline (which cannot see the pre-check); it is generous to that baseline.
    """
    r = rate_by_size[f.size_class]
    return Outcome(
        soil_test_cost(f.cropland_ha, a),
        r["p_nm3plus"],
        r["p_nm4"],
        r["gain_per_ha"] * f.cropland_ha,
        r["total_per_ha"] * f.cropland_ha,
    )


def size_rates(farms: list[Farm], outs: dict[int, Outcome]) -> dict[str, dict[str, float]]:
    rates = {}
    for cls in {f.size_class for f in farms}:
        sel = [f for f in farms if f.size_class == cls and f.idx in outs]
        ha = sum(f.cropland_ha for f in sel) or 1.0
        n = len(sel) or 1
        rates[cls] = {
            "p_nm3plus": sum(outs[f.idx].p_nm3plus for f in sel) / n,
            "p_nm4": sum(outs[f.idx].p_nm4 for f in sel) / n,
            "gain_per_ha": sum(outs[f.idx].subsidy_gain_brl for f in sel) / ha,
            "total_per_ha": sum(outs[f.idx].subsidy_total_brl for f in sel) / ha,
        }
    return rates


def benefit(f: Farm, o: Outcome, objective: str) -> tuple[float, ...]:
    """Score to rank farms (higher first). Tuples rank lexicographically."""
    if objective == "subsidy":
        return (o.subsidy_gain_brl / o.cost_brl,)
    if objective == "protected":
        # straw-covered cropland brought into the NM3+ incentive, per real
        return (o.p_nm3plus * f.cropland_ha * f.straw_share / o.cost_brl,)
    if objective == "families":
        # small properties first (by chance of NM3+ per real), then the rest by subsidy per real
        return (1.0 if f.small else 0.0, (o.p_nm3plus if f.small else o.subsidy_gain_brl) / o.cost_brl)
    raise ValueError(f"unknown objective {objective}")


def fill(order: list[int], cost: dict[int, float], budget: float) -> list[int]:
    """Take farms in `order` while the budget lasts; a farm that does not fit is skipped, later ones may still fit."""
    chosen, left = [], budget
    for k in order:
        if cost[k] <= left + 1e-9:
            chosen.append(k)
            left -= cost[k]
    return chosen


def greedy_order(farms: list[Farm], outs: dict[int, Outcome], objective: str) -> list[int]:
    cand = [f for f in farms if f.assessed and f.idx in outs]
    cand.sort(key=lambda f: (benefit(f, outs[f.idx], objective), -f.idx), reverse=True)
    return [f.idx for f in cand]


def metrics(chosen: list[int], farms_by_idx: dict[int, Farm], outs: dict[int, Outcome]) -> dict[str, float]:
    m = {
        "farms": 0.0,
        "spent_brl": 0.0,
        "cropland_tested_ha": 0.0,
        "ha_nm3plus": 0.0,
        "ha_nm4": 0.0,
        "subsidy_gain_brl": 0.0,
        "subsidy_total_brl": 0.0,
        "small_served": 0.0,
        "small_nm3plus": 0.0,
        "protected_ha": 0.0,
    }
    for k in chosen:
        f, o = farms_by_idx[k], outs[k]
        m["farms"] += 1
        m["spent_brl"] += o.cost_brl
        m["cropland_tested_ha"] += f.cropland_ha
        m["ha_nm3plus"] += o.p_nm3plus * f.cropland_ha
        m["ha_nm4"] += o.p_nm4 * f.cropland_ha
        m["subsidy_gain_brl"] += o.subsidy_gain_brl
        m["subsidy_total_brl"] += o.subsidy_total_brl
        m["small_served"] += f.small
        m["small_nm3plus"] += o.p_nm3plus * f.small
        m["protected_ha"] += o.p_nm3plus * f.cropland_ha * f.straw_share
    return m


def first_come(
    farms: list[Farm],
    outs: dict[int, Outcome],
    budget: float,
    runs: int,
    seed: int = 20261115,
) -> dict[str, dict[str, float]]:
    """Baseline "first come, first served": every property with cropland is equally likely to apply first.

    Returns mean, 5th and 95th percentile of each metric over `runs` random arrival orders.
    """
    rng = random.Random(seed)
    idx = [f.idx for f in farms if f.idx in outs]
    cost = {k: outs[k].cost_brl for k in idx}
    by = {f.idx: f for f in farms}
    samples: dict[str, list[float]] = {}
    for _ in range(runs):
        order = idx[:]
        rng.shuffle(order)
        for key, v in metrics(fill(order, cost, budget), by, outs).items():
            samples.setdefault(key, []).append(v)
    out = {}
    for key, vals in samples.items():
        vals.sort()
        out[key] = {
            "mean": sum(vals) / len(vals),
            "p05": vals[int(0.05 * (len(vals) - 1))],
            "p95": vals[int(0.95 * (len(vals) - 1))],
        }
    return out
