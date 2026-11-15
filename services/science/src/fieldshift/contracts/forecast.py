# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""ForecastScorecard: ENSO forecasts issued in January-March for the austral winter (JJA) and how
they verified against the observed ONI (v1.2.0).

Shape and one-document invariants only; the metrics are computed by the pipeline.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from fieldshift.contracts.common import (
    Contract,
    LocalizedText,
    Month,
    ProvenanceId,
    SchemaVersion,
    SiteId,
)

type EnsoPhase = Literal["el_nino", "neutral", "la_nina"]
# probability: P(La Niña), P(neutral), P(El Niño); nino34_anomaly: forecast JJA Niño-3.4 anomaly
type ForecastKind = Literal["probability", "nino34_anomaly"]
type ForecastSourceId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9-]{1,47}$")]
type Probability = Annotated[float, Field(ge=0, le=1)]

PROBABILITY_SUM_TOLERANCE = 0.03  # published tables round each category to whole percent


class ForecastSource(Contract):
    id: ForecastSourceId
    label: LocalizedText
    kind: ForecastKind
    provider: str = Field(min_length=1)
    # First target year issued in real time; earlier years are hindcasts (run later). None = all
    # real time.
    real_time_from: int | None = None
    provenance_id: ProvenanceId


class ObservedWinter(Contract):
    year: int
    oni_jja: float  # unit delta_degC (ONI is an anomaly)
    phase: EnsoPhase


class ForecastRecord(Contract):
    source_id: ForecastSourceId
    issue_month: Month
    target_year: int
    p_la_nina: Probability | None = None
    p_neutral: Probability | None = None
    p_el_nino: Probability | None = None
    nino34_anomaly: float | None = None  # unit delta_degC, mean of June, July and August
    predicted_phase: EnsoPhase
    observed_phase: EnsoPhase
    hit: bool
    source_url: str = Field(min_length=1)

    @model_validator(mode="after")
    def _one_kind(self) -> ForecastRecord:
        probs = (self.p_la_nina, self.p_neutral, self.p_el_nino)
        has_probs = all(p is not None for p in probs)
        if any(p is not None for p in probs) and not has_probs:
            raise ValueError(f"{self.source_id} {self.target_year}: give all three probabilities")
        if has_probs == (self.nino34_anomaly is not None):
            raise ValueError(
                f"{self.source_id} {self.target_year}: either three probabilities or an anomaly"
            )
        if has_probs and abs(sum(probs) - 1) > PROBABILITY_SUM_TOLERANCE:  # type: ignore[arg-type]
            raise ValueError(f"{self.source_id} {self.target_year}: probabilities must sum to 1")
        if self.hit != (self.predicted_phase == self.observed_phase):
            raise ValueError(f"{self.source_id} {self.target_year}: hit != (predicted == observed)")
        return self


class ForecastScore(Contract):
    """Verification of one source for one issue month over the target years it covers."""

    source_id: ForecastSourceId
    issue_month: Month
    first_year: int
    last_year: int
    n: int = Field(ge=1)
    phase_hit_rate: Probability
    always_neutral_hit_rate: Probability  # reference: a forecast that always says "neutral"
    el_nino_observed: int = Field(ge=0)
    el_nino_hits: int = Field(ge=0)
    el_nino_forecasts: int = Field(ge=0)
    false_alarm_ratio: Probability | None = None  # None when El Niño was never forecast
    # Probability sources only (None for anomaly sources):
    brier_el_nino: Probability | None = None
    brier_climatology: Probability | None = None
    brier_always_neutral: Probability | None = None
    brier_skill_score: float | None = None  # 1 - brier_el_nino / brier_climatology
    provenance_id: ProvenanceId

    @model_validator(mode="after")
    def _counts(self) -> ForecastScore:
        if self.last_year < self.first_year:
            raise ValueError(f"{self.source_id}: last_year < first_year")
        if self.el_nino_hits > min(self.el_nino_observed, self.el_nino_forecasts):
            raise ValueError(f"{self.source_id}: more El Niño hits than observed or forecast")
        if (self.false_alarm_ratio is None) != (self.el_nino_forecasts == 0):
            raise ValueError(f"{self.source_id}: false_alarm_ratio is None only with 0 forecasts")
        return self


class ForecastScorecard(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    target_season: Literal["JJA"]
    observed: list[ObservedWinter] = Field(min_length=1)
    observed_provenance_id: ProvenanceId
    sources: list[ForecastSource] = Field(min_length=1)
    forecasts: list[ForecastRecord]
    scores: list[ForecastScore]

    @model_validator(mode="after")
    def _consistent(self) -> ForecastScorecard:
        kinds = {s.id: s.kind for s in self.sources}
        if len(kinds) != len(self.sources):
            raise ValueError("source ids must be unique")
        years = {o.year: o.phase for o in self.observed}
        if len(years) != len(self.observed):
            raise ValueError("observed years must be unique")
        seen: set[tuple[str, int, int]] = set()
        for f in self.forecasts:
            key = (f.source_id, f.issue_month, f.target_year)
            if f.source_id not in kinds:
                raise ValueError(f"forecast of unknown source {f.source_id!r}")
            if key in seen:
                raise ValueError(f"duplicate forecast {key}")
            seen.add(key)
            if (kinds[f.source_id] == "probability") != (f.p_el_nino is not None):
                raise ValueError(f"{key}: values do not match the source kind")
            if years.get(f.target_year) != f.observed_phase:
                raise ValueError(f"{key}: observed_phase differs from the observed winter")
        for s in self.scores:
            if s.source_id not in kinds:
                raise ValueError(f"score of unknown source {s.source_id!r}")
        return self
