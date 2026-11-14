# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Ground-check limitations of NASA POWER (issue #31).

The team compared POWER daily Tmax and rain with ground stations at Cruz Alta (RS, Brazil):
INMET automatic station A853 (2007-2025) and ANA rain gauge 2853015 (1981-2025). Every number
below comes from that analysis (fieldshift-hq `docs/research/estacao-vs-satelite.md`, 2026-11-14)
and is documented on the public method page `content/methods/satellite-vs-ground.md`.
The texts are attached to every record that reads POWER Tmax or rain, whatever the site: they
describe the dataset, and they say that other grid cells were not checked.
"""

from __future__ import annotations

from fieldshift.contracts import LocalizedText

# Method page with the full comparison (VL6: content/methods must define this anchor).
GROUND_CHECK_ANCHOR = "satellite-vs-ground-check"
_SEE = f"Details: Data & Methods, #{GROUND_CHECK_ANCHOR}."

TMAX_GROUND_CHECK = (
    "Ground check (team analysis, Cruz Alta, RS, Brazil; INMET station A853): in "
    "January-February, POWER daily Tmax ran +0.41 °C above the station in 2008-2018 and "
    "+1.84 °C in 2019-2025, while two neighbouring INMET stations (A883, A886) kept a stable "
    "offset to A853, so the shift is in POWER, from about 2019. In 2019-2025 POWER counted 204 "
    "January-February days above 32 °C against 128 at the station. Hot-day counts and any trend "
    "in them from POWER alone may be inflated after 2019: check them against a local weather "
    f"station. Other grid cells were not checked. {_SEE}"
)

RAIN_GROUND_CHECK = (
    "Ground check (team analysis, Cruz Alta, RS, Brazil; INMET station A853 and ANA rain gauge "
    "2853015): POWER flags rain (1 mm or more) on 38-41% of days against 24-28% at the gauges, "
    "so dry spells are shorter in POWER (longest January-February dry spell 7.3 days on average "
    "against 11.7 at gauge 2853015, 41 seasons) and heavy rain is smoothed (on days with 60 mm "
    "or more at the gauge, POWER recorded 46-57% of the amount; a neighbouring gauge, 66-68%). "
    "Dry spells and extreme rain from POWER underestimate what a rain gauge records: check them "
    "against a rain gauge or GPM IMERG (daily r with A853: 0.85 for IMERG, 0.78 for POWER). "
    f"Monthly totals agree better (monthly r with A853: 0.92). {_SEE}"
)

# POWER parameter codes and index keys that read POWER daily Tmax or rain.
_TMAX_KEYS = frozenset({"T2M_MAX", "heat_days"})
_RAIN_KEYS = frozenset(
    {"PRECTOTCORR", "extreme_precip_days", "extreme_precip_total", "precip_percentile"}
)


def ground_check_limitations(key: str) -> list[LocalizedText]:
    """Station-comparison limitations for a POWER parameter code or an index key."""
    if key in _TMAX_KEYS:
        return [LocalizedText(en=TMAX_GROUND_CHECK)]
    if key in _RAIN_KEYS:
        return [LocalizedText(en=RAIN_GROUND_CHECK)]
    return []
