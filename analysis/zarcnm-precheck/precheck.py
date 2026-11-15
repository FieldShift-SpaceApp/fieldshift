# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""ZarcNM pre-check of three winter paths after soybean at Cruz Alta (RS). Writes results/precheck.json.

A pre-check, not a classification: three of the six indicators come from a soil test that no satellite sees,
contour planting is not checked here, and the straw-to-cover conversion has no field calibration. Every level
below is a range with the premise that produces it. Run: `python precheck.py` (needs only the standard library
and the straw clock already committed in ../storms-bare-soil/results/straw_clock.json).
"""

from __future__ import annotations

import itertools
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import zarcnm_rules as zr

HERE = Path(__file__).resolve().parent
STRAW_CLOCK = HERE.parent / "storms-bare-soil" / "results" / "straw_clock.json"
OUT = HERE / "results" / "precheck.json"

# ----------------------------------------------------------------------------------------------
# Premises and their sources
# ----------------------------------------------------------------------------------------------

# Gregory (1982) mass-to-cover relation: fraction covered = 1 - exp(-Am * M), M in kg/ha.
# Am values as quoted by McCool et al. (2006, ISCO), who cite Gregory (1982) for complete wheat residue
# (0.00054 and 0.00045 ha/kg) and measured 0.00024 ha/kg for winter wheat stems only.
AM_LOW = 0.00024  # stems only: lowest cover per kg (conservative end)
AM_HIGH = 0.00054  # complete wheat residue: highest cover per kg
AM_SOURCE = "S6"

# Cover crop window: sown after the April soybean harvest, desiccated 1 Sep - 31 Oct (straw clock scenario).
# Sowing between 15 Apr and 31 May is a scenario of this pre-check (no Cruz Alta calendar was found).
COVER_DAYS_MIN = (datetime(2026, 9, 1) - datetime(2026, 5, 31)).days  # 93 days
COVER_DAYS_MAX = (datetime(2026, 10, 31) - datetime(2026, 4, 15)).days  # 199 days

T_ASSUMED_YEARS = 8  # continuous no-till for at least 8 complete years: an assumption, to be checked

SOYBEAN = zr.Crop("soybean", (zr.SOYBEAN_SPECIES,), (zr.FABACEAE,), days=130)
WHEAT = zr.Crop("wheat (grain)", ("Triticum aestivum",), (zr.POACEAE,), days=150)


def oat_vetch(days: int) -> zr.Crop:
    return zr.Crop(
        "black oat + common vetch (cover)",
        ("Avena strigosa", "Vicia sativa"),
        (zr.POACEAE, zr.FABACEAE),
        is_cover=True,
        days=days,
    )


def three_years(winter: zr.Crop | None) -> list[zr.Crop]:
    """Crops of the last 3 agricultural years in time order (IN 2/2025 Table 1 row 6), winter after soybean."""
    seq: list[zr.Crop] = []
    for _ in range(3):
        seq.append(SOYBEAN)
        if winter is not None:
            seq.append(winter)
    return seq


def cover_pct(straw_t_ha: float, am_ha_per_kg: float) -> float:
    return 100.0 * (1.0 - math.exp(-am_ha_per_kg * straw_t_ha * 1000.0))


def straw_range(clock: dict, rotation: str) -> tuple[float, float]:
    rows = [r for r in clock["rows"] if r["rotation"] == rotation]
    return min(r["straw_t_ha_low"] for r in rows), max(r["straw_t_ha_high"] for r in rows)


def straw_indicator(clock: dict, rotation: str) -> dict:
    lo_t, hi_t = straw_range(clock, rotation)
    if hi_t == 0.0:
        return {
            "level_min": 1,
            "level_max": 2,
            "cover_pct_min": None,
            "cover_pct_max": None,
            "basis": (
                "No winter straw in the straw clock (no winter crop). Level 1 (C < 30%) if the fallow is kept "
                "clean; level 2 cannot be excluded because the April soybean residue and winter weeds or "
                "volunteers are not modelled (the Cruz Alta trial gives no soybean half-life)."
            ),
            "source": "S4; S5",
        }
    c_lo, c_hi = cover_pct(lo_t, AM_LOW), cover_pct(hi_t, AM_HIGH)
    return {
        "level_min": zr.level_straw_cover(c_lo),
        "level_max": zr.level_straw_cover(c_hi),
        "cover_pct_min": round(c_lo, 1),
        "cover_pct_max": round(c_hi, 1),
        "basis": (
            f"Straw on 1, 16 and 30 November from the straw clock: {lo_t:g}-{hi_t:g} t/ha (arithmetic from measured "
            f"half-lives, not a field measurement). Converted to cover with Gregory (1982), "
            f"cover = 1 - exp(-Am x kg/ha), Am {AM_LOW}-{AM_HIGH} ha/kg (wheat stems only to complete wheat residue; "
            f"no Am for black oat was found, wheat values used): {c_lo:.0f}-{c_hi:.0f}% cover. The norm measures C "
            "with NDTI in the month before sowing (IN 2/2025 item 6.7); no NDTI threshold was calibrated here."
        ),
        "source": "S4; S5; S6",
    }


PATHS = [
    {
        "id": "soy-wheat",
        "label": "Soybean - wheat",
        "winter": WHEAT,
        "winter_alt": None,
        "straw_rotation": "soy-wheat",
    },
    {
        "id": "soy-cover",
        "label": "Soybean - cover (black oat + common vetch)",
        "winter": oat_vetch(COVER_DAYS_MIN),
        "winter_alt": oat_vetch(COVER_DAYS_MAX),
        "straw_rotation": "soy-cover",
    },
    {
        "id": "soy-fallow",
        "label": "Soybean - winter fallow",
        "winter": None,
        "winter_alt": None,
        "straw_rotation": "soy-fallow",
    },
]


def diversity_indicator(path: dict) -> tuple[dict, list[zr.Crop]]:
    seqs = [three_years(path["winter"])]
    if path["winter_alt"] is not None:
        seqs.append(three_years(path["winter_alt"]))
    levels = [zr.level_diversity(s) for s in seqs]
    counts = zr.count_diversity(seqs[0])
    if path["id"] == "soy-cover":
        why = (
            f"6 crops (3 soybean + 3 black oat/vetch covers), 3 species, 2 families. Cover time "
            f"{COVER_DAYS_MIN}-{COVER_DAYS_MAX} days (sown 15 Apr-31 May, desiccated 1 Sep-31 Oct): if more than "
            "4 months it meets level 3 by '1 cover of more than 4 months' (with a grass, item 2.4-IV); if not, "
            "by '3 covers of more than 45 days each'. Level 4 needs 4 species."
        )
    elif path["id"] == "soy-wheat":
        why = (
            "6 crops (3 soybean + 3 wheat), 2 species, 2 families: level 2. No cover crop, so level 3 is not met; "
            "wheat as the main winter crop is not a 3rd crop or autumn-window grass (item 2.4-I)."
        )
    else:
        why = "3 crops (soybean only), 1 species, 1 family: fewer than the 4 crops of level 2, so level 1."
    return (
        {
            "level_min": min(levels),
            "level_max": max(levels),
            "basis": why + f" Counted: {counts.crops} crops, {counts.species} species, {counts.families} families.",
            "source": "S1 (Table 1 row 6, item 2.4); S5",
        },
        seqs[0],
    )


def chem_indicator(code: str) -> dict:
    return {
        "code": code,
        "name": zr.INDICATOR_NAMES[code],
        "name_pt": zr.INDICATOR_NAMES_PT[code],
        "level_min": None,
        "level_max": None,
        "observable": False,
        "basis": "not observable from satellite: needs soil test (georeferenced samples, accredited lab; "
        "IN 2/2025 items 4.1-III and 7).",
        "source": "S1 (" + zr.INDICATOR_CITATION[code] + ")",
    }


def nm_range(
    ind: dict[str, tuple[int, int]], soil_level: int, soy_on_soy_options: tuple[bool, ...], legume_only: bool
) -> tuple[int, int]:
    results = []
    ranges = {k: range(lo, hi + 1) for k, (lo, hi) in ind.items()}
    for t, c, d, sos in itertools.product(ranges["T"], ranges["C"], ranges["D"], soy_on_soy_options):
        levels = {"V%": soil_level, "Ca": soil_level, "m%": soil_level, "T": t, "C": c, "D": d}
        # contour and soil depth assumed compliant (slope < 3% or contour on >= 75%; deep soil): to confirm
        facts = zr.SiteFacts(
            slope_pct=0.0, consecutive_soybean=sos, legume_only_succession=legume_only, useful_soil_depth_cm=200
        )
        results.append(zr.classify(levels, facts).nm)
    return min(results), max(results)


def build() -> dict:
    clock = json.loads(STRAW_CLOCK.read_text(encoding="utf-8"))
    out_paths = []
    for p in PATHS:
        c = straw_indicator(clock, p["straw_rotation"])
        d, seq = diversity_indicator(p)
        t_level = zr.level_years_without_tillage(T_ASSUMED_YEARS)
        t = {
            "level_min": t_level,
            "level_max": t_level,
            "basis": (
                f"Assumed continuous no-till for at least {T_ASSUMED_YEARS} complete years (level 4), the same for "
                "the three paths. Not measured: the norm dates the last tillage from sudden changes in the "
                "satellite time series (item 6.8); the Landsat series is being produced by another front and "
                "will confirm or lower this. 5-7 years gives level 3, 3-4 years level 2, under 3 years level 1."
            ),
            "source": "S1 (items 2.3, 6.8); assumption",
        }
        indicators = [chem_indicator(k) for k in zr.SOIL_TEST_INDICATORS]
        for code, body in (("T", t), ("C", c), ("D", d)):
            indicators.append(
                {
                    "code": code,
                    "name": zr.INDICATOR_NAMES[code],
                    "name_pt": zr.INDICATOR_NAMES_PT[code],
                    "observable": True,
                    **body,
                }
            )
        ind_ranges = {k["code"]: (k["level_min"], k["level_max"]) for k in indicators if k["observable"]}

        sos_literal = zr.has_consecutive_soybean(seq)
        legume_only = zr.has_legume_only_succession(seq)
        sos_options = (True, False) if sos_literal else (False,)
        by_soil = {}
        for n in (1, 2, 3, 4):
            lo, hi = nm_range(ind_ranges, n, sos_options, legume_only)
            by_soil[str(n)] = {"min": lo, "max": hi}
        lo4, hi4 = by_soil["4"]["min"], by_soil["4"]["max"]

        locks = [
            {
                "rule": "slope >= 3% requires contour sowing on at least 75% of the area in the last year, else NM1",
                "citation": "IN 2/2025, item 3.2.1-I",
                "status": "to confirm",
                "note": "Assumed compliant in nm_range. The slope comes from NASADEM (item 6.3, another front); "
                "contour sowing is not checked here.",
            },
            {
                "rule": "two or more consecutive soybean crops (soja sobre soja) -> NM1",
                "citation": "IN 2/2025, item 3.2.1-II",
                "status": "applies under the literal reading" if sos_literal else "does not apply",
                "note": (
                    "Soybean every summer with nothing in winter: read literally, the soybean crops are consecutive. "
                    "The norm does not say whether a fallow winter breaks the sequence; nm_range keeps both readings."
                    if sos_literal
                    else "A winter crop sits between the soybean crops."
                ),
            },
            {
                "rule": "legume-only crop before or after soybean, without other species -> at most NM2",
                "citation": "IN 2/2025, item 3.2.1-III",
                "status": "applies" if legume_only else "does not apply",
                "note": (
                    "The crop before and after each soybean is soybean, a legume."
                    if legume_only
                    else "The winter crop includes a grass (wheat, or black oat in the oat + vetch consortium)."
                ),
            },
            {
                "rule": "two or more indicators at level 1 -> NM1; two at level 2, or one at 1 and one at 2 -> NM2",
                "citation": "IN 2/2025, item 3.2.1-IV",
                "status": "depends on levels",
                "note": "Included in nm_range for every combination of the ranges above.",
            },
            {
                "rule": "mean at level 3-4 with m% at level 1 -> NM2; with m% at level 2 -> NM3",
                "citation": "IN 2/2025, item 3.2.1-V",
                "status": "needs soil test",
                "note": "m% is a soil-test indicator; nm_range_by_soil_level shows its effect.",
            },
            {
                "rule": "the class is limited to the NM whose root depth (40/60/80/100 cm) is below the useful soil "
                "depth Zus; Zus < 50 cm stays at NM1",
                "citation": "Portaria 209/2026, item 2.4",
                "status": "to confirm",
                "note": "Assumed deep soil in nm_range; needs a soil profile, not visible from satellite.",
            },
        ]
        observable = sum(1 for k in indicators if k["observable"])
        summary = (
            f"pre-check: {observable} of 6 indicators observable; NM range {lo4}-{hi4} if soil tests are at "
            "level 4; contour to confirm"
        )
        notes = [summary]
        if p["id"] == "soy-wheat":
            notes.append(
                "At the low end of the straw-cover range (C level 2) C and D are both at level 2, which "
                "caps the class at NM2 (item 3.2.1-IV-b); at C level 3 the mean is exactly 3.50, still NM3."
            )
        if p["id"] == "soy-cover":
            notes.append(
                "NM4 needs C at level 3 or 4 (60% cover or more before sowing); at C level 2 the mean "
                "is 3.50 and the class is NM3."
            )
        if p["id"] == "soy-fallow":
            notes.append(
                "D is at level 1 whatever the straw: one more indicator at level 1 gives NM1 "
                "(item 3.2.1-IV-a). Without the soy-on-soy reading the best case is NM2."
            )
        out_paths.append(
            {
                "id": p["id"],
                "label": p["label"],
                "summary": summary,
                "indicators": indicators,
                "nm_range": {
                    "min": lo4,
                    "max": hi4,
                    "condition": "if all 3 soil-test indicators (V%, Ca, m%) are at level 4, contour sowing is "
                    "confirmed (or slope < 3%), the soil is deeper than 1 m, and no-till holds for 8+ years",
                },
                "nm_range_by_soil_level": by_soil,
                "locks": locks,
                "subsidy_pct_range": {"min": zr.SUBSIDY_PCT_SOY[lo4], "max": zr.SUBSIDY_PCT_SOY[hi4]},
                "subsidy_brl_per_ha": None,
                "notes": notes,
            }
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "site": "cruz-alta",
        "label": "pre-check, not official",
        "norm": {
            "in": "IN SPA/MAPA 2/2025",
            "portaria": "Portaria SPA/MAPA 209/2026",
            "subsidy": "Resolução CGSR 111/2026",
            "subsidy_pct": {"NM1": 20, "NM2": 30, "NM3": 35, "NM4": 40},
            "subsidy_budget_note": (
                "Resolução CGSR 111/2026 (art. 2) sets R$ 1,000,000.00 for soybean in the ZarcNM pilot for 2026, "
                "shared by Paraná, Santa Catarina, Rio Grande do Sul and Mato Grosso do Sul (states as reported by "
                "Agrolink, 7 Aug 2026). The rate applies only while that budget lasts, and only to fields classified "
                "by Embrapa's method; payment depends on federal funds."
            ),
            "subsidy_brl_per_ha_note": (
                "null: no published average soybean premium per hectare for Rio Grande do Sul was found. The PSR "
                "2024 report (Atlas do Seguro Rural) gives only the national soybean figures (R$ 2,007 million of "
                "premium on 4.83 million ha, about R$ 415/ha in 2024) and RS totals for all crops; neither is a "
                "Rio Grande do Sul soybean premium, so no R$/ha is estimated."
            ),
            "subsidy_source_note": "Percentages and budget read on the Legismap transcription of the resolution "
            "(DOU 29/04/2026); the DOU PDF was not opened.",
        },
        "paths": out_paths,
        "caveats": [
            "Pre-check, not a certificate: the official class is produced only by Embrapa's SINM after the three "
            "data subsets are registered by accredited agents (IN 2/2025, items 4.1-4.6).",
            "3 of the 6 indicators (V%, Ca, m%) need a soil test (0-20 and 20-40 cm, accredited lab, valid 24 "
            "months, item 7.8); they are not observable from satellite. nm_range_by_soil_level gives the NM range "
            "with all three soil-test indicators at the same level n (1-4); mixed soil levels are not tabulated.",
            "Contour sowing on slopes >= 3% (item 3.2.1-I) and the useful soil depth (Portaria 209/2026 item 2.4) "
            "are assumed compliant; either can force NM1.",
            "Straw cover is arithmetic: straw clock (one trial's half-lives, scenario windows) converted with "
            "Gregory's mass-to-cover relation using wheat coefficients from US measurements. No NDTI threshold was "
            "calibrated against field cover.",
            "T (years without tillage) is an assumption (8+ years of no-till) until the Landsat series is checked.",
            "The ZarcNM subsidy for soybean has a budget of R$ 1 million in 2026 for four states (Resolução CGSR "
            "111/2026).",
            "Portaria 209/2026 item 2.1 speaks of 'sete indicadores'; IN 2/2025 Table 1, which this pre-check "
            "follows, lists six.",
        ],
        "sources": [
            {
                "id": "S1",
                "label": "Instrução Normativa SPA/MAPA nº 2, de 8 de julho de 2025, Annex (soybean), DOU "
                "09/07/2025, ed. 127, seção 1, p. 3",
                "url": None,
            },
            {
                "id": "S2",
                "label": "Portaria SPA/MAPA nº 209, de 30 de junho de 2026 (ZarcNM soybean, Rio Grande do "
                "Sul, 2026/27), DOU 03/07/2026, seção 1",
                "url": "https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-"
                "agricola-de-risco-climatico/portarias/safra-vigente/rio-grande-do-sul",
            },
            {
                "id": "S3",
                "label": "Resolução CGSR nº 111, de 28 de abril de 2026 (Legismap transcription)",
                "url": "https://legismap.com.br/leis-e-normas/resolucao-cgsr-n-111-de-28-04-2026",
            },
            {
                "id": "S3b",
                "label": "Agrolink, 07/08/2026, 'Seguro rural em agosto: PSR reserva R$ 1 milhão para "
                "soja' (states of the pilot)",
                "url": "https://www.agrolink.com.br/noticias/seguro-rural-em-agosto--psr-reserva-r--1-milhao-para-soja_517600.html",
            },
            {
                "id": "S4",
                "label": "FieldShift straw clock (analysis/storms-bare-soil/results/straw_clock.json): "
                "half-lives from Campos et al. (2011), initial straw from Aita & Giacomini (2003) and Santos et al. "
                "(2019)",
                "url": "https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/storms-bare-soil",
            },
            {
                "id": "S5",
                "label": "Santos et al. (ed.) (2019), Sistemas de produção para cereais de inverno: três "
                "décadas de estudos, Embrapa (winter species, oat + vetch consortium)",
                "url": "https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1111855/1/ID446652019LVSistemasdeproducao.pdf",
            },
            {
                "id": "S6",
                "label": "McCool, D.K.; Sharratt, B.S.; Krauss, H.A.; McClellan, R.C. (2006). Residue "
                "characteristics for wind and water erosion control. 14th ISCO Conference, Marrakech (quotes Gregory, "
                "J.M. 1982, Trans. ASAE 25:1333-1337, Am for wheat residue)",
                "url": "https://topsoil.nserl.purdue.edu/isco/isco14/5%20Erosion%20Process%20&%20Control/Oral/"
                "T5-McCool-Residue%20Characteristics%20for%20Windl-USA.pdf",
            },
            {
                "id": "S7",
                "label": "MAPA, Relatório Geral PSR 2024, Table 11 (national soybean premium and area)",
                "url": "https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/seguro-rural/dados/relatorios/relatorio-geral-psr-2024.pdf",
            },
        ],
    }


def main() -> None:
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for p in data["paths"]:
        print(p["id"], "->", p["summary"], "| subsidy", p["subsidy_pct_range"])


if __name__ == "__main__":
    main()
