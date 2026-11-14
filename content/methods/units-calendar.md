---
anchor: units-calendar
title: Units and agricultural calendar
order: 40
refs:
  - label: "Implementation: display unit conversion (app)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/apps/web/src/lib/units.ts
  - label: Shared test cases for the agricultural year (Python and TypeScript)
    url: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/packages/contracts/fixtures/agyear-cases.json
limitations:
  - "Seasons and hemispheres are not modeled: the calendar logic uses only each site's agricultural-year start month."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the project architecture (ADR-7, accepted); human review pending (see SI-USAGE.md). -->

**Units.** Data are stored in SI units with fixed codes (for example `degC`, `mm`, `mm/month`, `m3/m3`, `MJ/m2/d`, `m/s`, `kPa`). Conversion to imperial units happens only when a value is displayed, never in the stored data.

- A **temperature difference** (an anomaly, for example) converts with × 1.8 and without the + 32 offset used for temperatures. This is a classic error and has its own test.
- Probabilities are stored as a fraction from 0 to 1; the display decides how to show them.

**Agricultural year.** Each site has the month its agricultural year starts in. A date belongs to agricultural year `Y` if its month is on or after the start month, and to `Y − 1` otherwise. When the agricultural year crosses New Year, it is labeled like "2024/25". Every time axis starts at the site's start month and names the months.

No logic uses seasons or hemispheres: the hemisphere is shown for information only. The same function exists in Python and in TypeScript, and both pass the same file of shared test cases.
