# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""ZarcNM soybean management-level rules, transcribed from the norm text.

Source: Instrução Normativa SPA/MAPA nº 2, de 8 de julho de 2025 (DOU 09/07/2025, ed. 127, seção 1, p. 3),
Annex "Cultura da soja" (cited below as "IN 2/2025, item ..."), and Portaria SPA/MAPA nº 209, de 30 de junho
de 2026 (ZarcNM soybean, Rio Grande do Sul, 2026/27; cited as "Portaria 209/2026, item ...").

This module only applies the published rules to levels that someone supplies. It is not the official
classification: the official one is produced by Embrapa's SINM from registered field data (IN 2/2025, art. 3
and items 4.2-4.3).

Interpretations where the text is ambiguous are marked "INTERPRETATION" and listed in the README.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

# Indicator codes, in the order of IN 2/2025 item 2.1 (I to VI) and Table 1 (rows 1 to 6).
INDICATORS: tuple[str, ...] = ("V%", "Ca", "m%", "T", "C", "D")
SOIL_TEST_INDICATORS: tuple[str, ...] = ("V%", "Ca", "m%")
MANAGEMENT_INDICATORS: tuple[str, ...] = ("T", "C", "D")

INDICATOR_NAMES: dict[str, str] = {
    "V%": "Base saturation (V%) in the 0-20 cm layer",
    "Ca": "Calcium (Ca, cmolc/dm3) in the 20-40 cm layer",
    "m%": "Aluminium saturation (m%) in the 20-40 cm layer",
    "T": "Time (T) without soil tillage, complete years",
    "C": "Soil cover (C) with straw before sowing the main crop, %",
    "D": "Diversity (D) of crops in rotation in the last 3 agricultural years",
}
INDICATOR_NAMES_PT: dict[str, str] = {
    "V%": "Saturação por bases (V%) na camada 0 a 20 cm",
    "Ca": "Teor de cálcio (Ca) na camada 20 a 40 cm",
    "m%": "Saturação por alumínio (m%) na camada 20 a 40 cm",
    "T": "Tempo (T) sem revolvimento do solo (anos)",
    "C": "Cobertura do solo (C) com palhada em pré-semeadura da cultura principal (%)",
    "D": "Diversidade (D) de cultivos nos últimos três anos agrícolas",
}
INDICATOR_CITATION: dict[str, str] = {
    "V%": "IN 2/2025, item 2.1-I and Table 1 row 1",
    "Ca": "IN 2/2025, item 2.1-II and Table 1 row 2",
    "m%": "IN 2/2025, item 2.1-III and Table 1 row 3",
    "T": "IN 2/2025, items 2.1-IV, 2.3 and Table 1 row 4",
    "C": "IN 2/2025, items 2.1-V, 6.7 and Table 1 row 5",
    "D": "IN 2/2025, items 2.1-VI, 2.4 and Table 1 row 6",
}

# Families as written in botanical usage; only the count of distinct families matters for the norm.
FABACEAE = "Fabaceae"
POACEAE = "Poaceae"
SOYBEAN_SPECIES = "Glycine max"

# "mais de 4 meses": INTERPRETATION as more than 4 average months (4 x 365.25 / 12 = 121.75 days).
FOUR_MONTHS_DAYS = 4 * 365.25 / 12
COVER_MIN_DAYS = 45  # "por mais de 45 dias" (Table 1 row 6, levels 3 and 4)

# Portaria 209/2026, item 2.5: effective root depth (Ze, cm) assumed for each management level.
ROOT_DEPTH_CM: dict[int, int] = {1: 40, 2: 60, 3: 80, 4: 100}

SUBSIDY_PCT_SOY: dict[int, int] = {1: 20, 2: 30, 3: 35, 4: 40}  # Resolução CGSR 111/2026, art. 1, par. 4


class IncompleteIndicatorsError(ValueError):
    """IN 2/2025, item 2.2: no classification if any indicator is not measured or informed."""


def _check_level(level: int) -> int:
    if level not in (1, 2, 3, 4):
        raise ValueError(f"indicator level must be 1-4, got {level!r}")
    return level


# --------------------------------------------------------------------------------------------
# Table 1: one function per row
# --------------------------------------------------------------------------------------------


def level_base_saturation(v_pct: float, cec_cmolc_dm3: float) -> int:
    """Table 1 row 1 (IN 2/2025, item 2.1-I): V% in 0-20 cm, with limits that depend on the CEC at pH 7.0.

    CTC < 5:        L1 V < 35 | L2 35 <= V < 40 | L3 40 <= V < 50 | L4 V >= 50
    5 <= CTC < 10:  L1 V < 40 | L2 40 <= V < 45 | L3 45 <= V < 55 | L4 V >= 55
    CTC >= 10:      L1 V < 50 | L2 50 <= V < 55 | L3 55 <= V < 65 | L4 V >= 65
    """
    if not 0 <= v_pct <= 100:
        raise ValueError(f"V% must be within 0-100, got {v_pct}")
    if cec_cmolc_dm3 < 0:
        raise ValueError(f"CEC must be >= 0, got {cec_cmolc_dm3}")
    if cec_cmolc_dm3 < 5:
        limits = (35, 40, 50)
    elif cec_cmolc_dm3 < 10:
        limits = (40, 45, 55)
    else:
        limits = (50, 55, 65)
    return 1 + sum(v_pct >= lim for lim in limits)


def level_calcium(ca_cmolc_dm3: float) -> int:
    """Table 1 row 2 (item 2.1-II): Ca in 20-40 cm. L1 Ca < 0.5 | L2 0.5 <= Ca < 1 | L3 1 <= Ca < 1.5 | L4 Ca >= 1.5."""
    if ca_cmolc_dm3 < 0:
        raise ValueError(f"Ca must be >= 0, got {ca_cmolc_dm3}")
    return 1 + sum(ca_cmolc_dm3 >= lim for lim in (0.5, 1.0, 1.5))


def level_aluminium_saturation(m_pct: float) -> int:
    """Table 1 row 3 (item 2.1-III): m% in 20-40 cm. L1 m >= 20 | L2 10 <= m < 20 | L3 5 <= m < 10 | L4 m < 5."""
    if not 0 <= m_pct <= 100:
        raise ValueError(f"m% must be within 0-100, got {m_pct}")
    return 4 - sum(m_pct >= lim for lim in (5, 10, 20))


def level_years_without_tillage(years: int) -> int:
    """Table 1 row 4 (item 2.1-IV): complete years since the last plough, harrow, subsoiler or chisel operation.

    L1 T < 3 | L2 3 <= T < 5 | L3 5 <= T < 8 | L4 T >= 8. Item 2.3 allows localized tillage in sowing rows,
    terrace maintenance and fire-break headlands without resetting T (the caller decides what counts).
    """
    if isinstance(years, bool) or not isinstance(years, int) or years < 0:
        raise ValueError(f"T is a count of complete years (int >= 0), got {years!r}")
    return 1 + sum(years >= lim for lim in (3, 5, 8))


def level_straw_cover(c_pct: float) -> int:
    """Table 1 row 5 (item 2.1-V): straw cover before sowing.

    L1 0 <= C < 30 | L2 30 <= C < 60 | L3 60 <= C < 90 | L4 C >= 90.
    """
    if not 0 <= c_pct <= 100:
        raise ValueError(f"C must be within 0-100, got {c_pct}")
    return 1 + sum(c_pct >= lim for lim in (30, 60, 90))


@dataclass(frozen=True)
class Crop:
    """One crop (cultivo) in the last 3 agricultural years. A consortium is one crop with several species.

    is_cover: planted as a cover crop (IN 2/2025, item 1.1-I), solo or in consortium.
    days: time in the field.
    conserved_forage: grown for silage or hay; not counted in the number of crops (item 2.4-III).
    short_window_grass: a grass grown as third crop or in the autumn window (item 2.4-I); it can replace one
        cover crop of less than 4 months.
    pasture_months: in crop-livestock integration, months of pasture kept on the area (item 2.4-V).
    grazed: covers may be grazed without losing their status (item 2.4-II); kept for the record only.
    """

    name: str
    species: tuple[str, ...]
    families: tuple[str, ...]
    is_cover: bool = False
    days: int = 0
    conserved_forage: bool = False
    short_window_grass: bool = False
    pasture_months: int = 0
    grazed: bool = False

    @property
    def is_soybean(self) -> bool:
        return self.species == (SOYBEAN_SPECIES,)

    @property
    def legume_only(self) -> bool:
        return bool(self.families) and set(self.families) == {FABACEAE}


@dataclass(frozen=True)
class DiversityCount:
    crops: int
    species: int
    families: int
    long_covers: int  # covers of more than 4 months that include a grass (item 2.4-IV)
    covers_over_45_days: int  # includes the long covers and the item 2.4-I substitutes
    crop_count_waived: bool  # item 2.4-V (pasture >= 12 months in crop-livestock integration)


def count_diversity(crops: Iterable[Crop]) -> DiversityCount:
    """Counts used by Table 1 row 6, with the additional criteria of IN 2/2025 item 2.4."""
    counted = [c for c in crops if not c.conserved_forage]  # item 2.4-III
    species = {s for c in counted for s in c.species}
    families = {f for c in counted for f in c.families}
    long_covers = sum(
        1
        for c in counted
        if c.is_cover and c.days > FOUR_MONTHS_DAYS and POACEAE in c.families  # item 2.4-IV
    )
    # Covers of more than 45 days, plus the item 2.4-I grasses that replace a cover of less than 4 months.
    covers_45 = sum(1 for c in counted if (c.is_cover and c.days > COVER_MIN_DAYS) or c.short_window_grass)
    waived = any(c.pasture_months >= 12 for c in counted)  # item 2.4-V
    return DiversityCount(len(counted), len(species), len(families), long_covers, covers_45, waived)


def level_diversity(crops: Iterable[Crop]) -> int:
    """Table 1 row 6 (item 2.1-VI), read with item 2.4.

    L2: at least 4 crops with at least 2 species and 2 botanical families.
    L3: at least 6 crops with at least 2 species and 2 families, and [1 cover crop of more than 4 months
        OR 3 cover crops (solo or consortium) of more than 45 days each].
    L4: at least 6 crops with at least 4 species and 2 families, and 1 cover crop of more than 4 months
        AND 2 cover crops of more than 45 days each.
    L1: requirements of the other levels not met.

    INTERPRETATION (table layout): the minimum of 6 crops applies to both branches of the level-3 "OU";
    at level 4 the "2 cover crops of more than 45 days" are in addition to the long one (3 covers in all).
    """
    d = count_diversity(crops)

    def enough(n: int) -> bool:
        return d.crop_count_waived or d.crops >= n

    if enough(6) and d.species >= 4 and d.families >= 2 and d.long_covers >= 1 and d.covers_over_45_days >= 3:
        return 4
    if enough(6) and d.species >= 2 and d.families >= 2 and (d.long_covers >= 1 or d.covers_over_45_days >= 3):
        return 3
    if enough(4) and d.species >= 2 and d.families >= 2:
        return 2
    return 1


# --------------------------------------------------------------------------------------------
# Locks that come from the crop sequence
# --------------------------------------------------------------------------------------------


def has_consecutive_soybean(sequence: Sequence[Crop]) -> bool:
    """Item 3.2.1-II input: two or more consecutive soybean crops (soja sobre soja).

    `sequence` lists the crops in time order; a fallow period is simply no crop. INTERPRETATION: the norm does
    not say whether a fallow winter breaks "consecutive"; read literally, soybean-fallow-soybean has two
    consecutive soybean crops. Callers that want the other reading must say so explicitly.
    """
    return any(a.is_soybean and b.is_soybean for a, b in zip(sequence, sequence[1:], strict=False))


def has_legume_only_succession(sequence: Sequence[Crop]) -> bool:
    """Item 3.2.1-III input: a legume-only crop right before or after a soybean crop, with no other species."""
    for i, crop in enumerate(sequence):
        if not crop.is_soybean:
            continue
        neighbours = sequence[max(0, i - 1) : i] + sequence[i + 1 : i + 2]
        if any(n.legume_only for n in neighbours):
            return True
    return False


# --------------------------------------------------------------------------------------------
# Classification (item 3.2)
# --------------------------------------------------------------------------------------------


def mean_of_indicators(levels: Mapping[str, int]) -> float:
    """Item 3.2: the mean of the indicators (Mi)."""
    return sum(_check_level(levels[k]) for k in INDICATORS) / len(INDICATORS)


def nm_from_mean(mi: float) -> int:
    """Item 3.2 I-IV: NM1 if Mi <= 1.75; NM2 if 1.75 < Mi <= 2.75; NM3 if 2.75 < Mi <= 3.50; NM4 if Mi > 3.50."""
    if mi <= 1.75:
        return 1
    if mi <= 2.75:
        return 2
    if mi <= 3.50:
        return 3
    return 4


@dataclass(frozen=True)
class AppliedLock:
    rule: str
    cap: int
    citation: str


@dataclass(frozen=True)
class SiteFacts:
    """Facts outside the six indicators that can override the mean.

    slope_pct / contour_share: mean slope of the field and share of the area sown on the contour in the last
        year (item 3.2.1-I). None = not verified.
    consecutive_soybean / legume_only_succession: items 3.2.1-II and III.
    useful_soil_depth_cm: Zus of Portaria 209/2026 item 2.4. None = not verified.
    """

    slope_pct: float | None = None
    contour_share: float | None = None
    consecutive_soybean: bool = False
    legume_only_succession: bool = False
    useful_soil_depth_cm: float | None = None


@dataclass(frozen=True)
class Classification:
    nm: int
    mean: float
    nm_from_mean: int
    locks: tuple[AppliedLock, ...]
    unverified: tuple[str, ...] = field(default_factory=tuple)


def depth_cap(useful_soil_depth_cm: float) -> int:
    """Portaria 209/2026 item 2.4: the class is limited to the NM whose root depth Ze is below Zus.

    Ze = 40/60/80/100 cm for NM1-NM4 (item 2.5). The text's example: Zus < 50 cm stays at NM1. Soils under
    0.5 m are not indicated for soybean at all (item 3.3-b); this function then still returns 1.
    """
    allowed = [nm for nm, ze in ROOT_DEPTH_CM.items() if ze < useful_soil_depth_cm]
    return max(allowed, default=1)


def classify(levels: Mapping[str, int | None], facts: SiteFacts | None = None) -> Classification:
    """Item 3.2: NM from the mean, unless an exclusion or downgrade criterion of item 3.2.1 applies.

    Item 3.2 gives the criteria priority over the mean. INTERPRETATION: when several apply, the most
    restrictive one wins (each one, read alone, sets or limits the class).
    """
    facts = facts or SiteFacts()
    missing = [k for k in INDICATORS if levels.get(k) is None]
    if missing:
        raise IncompleteIndicatorsError(f"IN 2/2025 item 2.2: indicators not measured or informed: {missing}")
    lv = {k: _check_level(int(levels[k])) for k in INDICATORS}  # type: ignore[arg-type]
    mi = mean_of_indicators(lv)
    base = nm_from_mean(mi)
    locks: list[AppliedLock] = []
    unverified: list[str] = []

    # I - contour planting
    if facts.slope_pct is None or (facts.slope_pct >= 3 and facts.contour_share is None):
        unverified.append("contour planting on slopes >= 3% (IN 2/2025, item 3.2.1-I)")
    elif facts.slope_pct >= 3 and facts.contour_share < 0.75:
        locks.append(AppliedLock("slope >= 3% without contour sowing on 75% of the area", 1, "IN 2/2025, item 3.2.1-I"))
    # II - soybean on soybean
    if facts.consecutive_soybean:
        locks.append(AppliedLock("two or more consecutive soybean crops", 1, "IN 2/2025, item 3.2.1-II"))
    # III - legume-only succession
    if facts.legume_only_succession:
        locks.append(AppliedLock("legume-only crop before or after soybean", 2, "IN 2/2025, item 3.2.1-III"))
    # IV - limiting indicators
    n1 = sum(1 for v in lv.values() if v == 1)
    n2 = sum(1 for v in lv.values() if v == 2)
    if n1 >= 2:
        locks.append(AppliedLock("two or more indicators at level 1", 1, "IN 2/2025, item 3.2.1-IV-a"))
    elif n2 >= 2 or (n1 >= 1 and n2 >= 1):
        locks.append(
            AppliedLock(
                "two or more indicators at level 2, or one at level 1 and one at level 2",
                2,
                "IN 2/2025, item 3.2.1-IV-b",
            )
        )
    # V - aluminium saturation, only when the mean gives NM3 or NM4
    if base >= 3 and lv["m%"] == 1:
        locks.append(AppliedLock("mean at level 3-4 but m% at level 1", 2, "IN 2/2025, item 3.2.1-V-a"))
    elif base >= 3 and lv["m%"] == 2:
        locks.append(AppliedLock("mean at level 3-4 but m% at level 2", 3, "IN 2/2025, item 3.2.1-V-b"))
    # Useful soil depth (Portaria 209/2026)
    if facts.useful_soil_depth_cm is None:
        unverified.append("useful soil depth Zus (Portaria 209/2026, item 2.4)")
    else:
        cap = depth_cap(facts.useful_soil_depth_cm)
        if cap < 4:
            locks.append(
                AppliedLock(
                    f"useful soil depth {facts.useful_soil_depth_cm:g} cm limits root depth",
                    cap,
                    "Portaria 209/2026, item 2.4",
                )
            )

    nm = min([base, *(lock.cap for lock in locks)])
    return Classification(nm=nm, mean=mi, nm_from_mean=base, locks=tuple(locks), unverified=tuple(unverified))
