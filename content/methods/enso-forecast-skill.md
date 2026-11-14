---
anchor: enso-forecast-skill
title: ENSO-phase skill of February forecasts for the JJA winter (forecast scorecard)
order: 60
refs:
  - label: "Wilks, D.S. (2011). Statistical Methods in the Atmospheric Sciences, 3rd ed., chapter 8 (forecast verification)."
    url: https://doi.org/10.1016/C2017-0-03921-6
  - label: "NOAA CPC, Oceanic Niño Index (oni.ascii.txt)"
    url: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
  - label: "IRI ENSO forecast archive (figures 3 and 4)"
    url: https://ensoforecast.iri.columbia.edu/
  - label: "NOAA CPC NMME ENSO files (NASA_GEOS5v2 = NASA GMAO GEOS-S2S)"
    url: https://ftp.cpc.ncep.noaa.gov/NMME/ENSO/
limitations:
  - "This is skill at the ENSO phase of the June-August winter, not a local measure of crop, rain or farm outcomes."
  - "Samples are small (2 to 7 El Niño winters per source); one winter changes the El Niño hit count by a large share, and no confidence interval is given."
  - "Sources cover different years; each rate is compared with the 'always neutral' rate of the same years, not across sources."
  - "NASA GMAO GEOS-S2S in the NMME is a hindcast (run later with the current model) before 2011."
  - "IRI values are read from the archive figures the IRI server draws today; objective probabilities can differ from the text published at the time by up to 4 points."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from services/science/src/fieldshift/complements/scorecard.py (EECOM, complements); review by GUIDO + SURGEON pending (see SI-USAGE.md). -->

**What it is.** For each forecast source, how often the forecast issued in **February** got the ENSO phase of the **June-August (JJA)** winter of the same year right. Every source is scored on the same issue month and the same target. NASA GMAO GEOS-S2S is listed first.

**Sources (February issue, JJA target).** NASA GMAO GEOS-S2S as the NMME member `NASA_GEOS5v2` (1982-2022, ensemble-mean Niño-3.4 anomaly against the model's own 1991-2020 climatology for the same start and lead); the NASA GMAO line and the all-model average of the IRI plume (2003-2025); the IRI objective probabilities (2004-2025); the NOAA CPC / IRI official consensus probabilities (2014-2025). Each row of `data/sites/cruz-alta/input/enso-forecasts.csv` keeps the URL of the file the value was read from (`services/science/scripts/enso_forecast_inputs.py`).

**Observed phase.** ONI JJA from NOAA CPC: El Niño if ≥ +0.5 °C, La Niña if ≤ −0.5 °C, neutral in between (1982-2025; JJA 2026 is still preliminary and left out).

**Predicted phase.** For an anomaly, the same ±0.5 °C threshold on the ensemble mean. For probabilities, the category with the largest probability (a tie goes to neutral).

**Metrics.** Phase hit rate, next to the hit rate of a forecast that always says "neutral". El Niño hits over observed El Niño winters, and the false-alarm ratio (El Niño forecasts that did not happen over all El Niño forecasts). For probability sources, the Brier score of P(El Niño), against climatology (frequency of El Niño JJA in 1982-2025) and against "always neutral" (P = 0); Brier skill score = 1 − Brier / Brier of climatology.
