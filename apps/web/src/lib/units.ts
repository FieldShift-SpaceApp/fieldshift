// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// ADR-7: data stays in canonical SI; conversion happens only here, at display time.
// Parity cases: packages/contracts/fixtures/units-cases.json (same file the Python test reads).
import type { CanonicalUnit, UnitSystem } from "@fieldshift/contracts";
import { t, type MessageKey } from "@/i18n";

export type { UnitSystem };

/** Units that exist only on screen, after conversion to the imperial system. */
export type ImperialUnit =
  | "degF"
  | "delta_degF"
  | "degF_d"
  | "in"
  | "in/d"
  | "in/month"
  | "ft"
  | "ac"
  | "mph";

export type DisplayUnit = CanonicalUnit | ImperialUnit;

export interface Converted {
  value: number;
  unit: DisplayUnit;
}

// Exact factors by definition: 1 in = 25.4 mm; 1 ft = 0.3048 m; 1 ac = 4046.8564224 m²; 1 mph = 0.44704 m/s.
const MM_PER_IN = 25.4;
const M_PER_FT = 0.3048;
const M2_PER_AC = 4046.8564224;
const M_S_PER_MPH = 0.44704;

const TO_IMPERIAL: Partial<Record<CanonicalUnit, { unit: ImperialUnit; fn: (v: number) => number }>> = {
  degC: { unit: "degF", fn: (v) => v * 1.8 + 32 },
  // A temperature DIFFERENCE scales by 1.8 and never gets +32 (ADR-7, classic bug).
  delta_degC: { unit: "delta_degF", fn: (v) => v * 1.8 },
  degC_d: { unit: "degF_d", fn: (v) => v * 1.8 },
  mm: { unit: "in", fn: (v) => v / MM_PER_IN },
  "mm/d": { unit: "in/d", fn: (v) => v / MM_PER_IN },
  "mm/month": { unit: "in/month", fn: (v) => v / MM_PER_IN },
  m: { unit: "ft", fn: (v) => v / M_PER_FT },
  ha: { unit: "ac", fn: (v) => (v * 10_000) / M2_PER_AC },
  "m/s": { unit: "mph", fn: (v) => v / M_S_PER_MPH },
};

/** Converts a canonical SI value to the display system. Units without an imperial form pass through. */
export function convert(value: number, unit: CanonicalUnit, system: UnitSystem): Converted {
  if (system === "imperial") {
    const rule = TO_IMPERIAL[unit];
    if (rule) return { value: rule.fn(value), unit: rule.unit };
  }
  return { value, unit };
}

/** Default number of decimals shown per display unit (display rounding only; data is not rounded). */
const DEFAULT_DIGITS: Partial<Record<DisplayUnit, number>> = {
  mm: 0,
  "mm/month": 0,
  in: 1,
  "in/month": 1,
  "mm/d": 1,
  "in/d": 2,
  "m3/m3": 2,
  probability: 2,
  days: 0,
  count: 0,
  "%": 0,
};

const UNIT_LABEL_KEY: Record<DisplayUnit, MessageKey> = {
  degC: "unit.degC",
  delta_degC: "unit.delta_degC",
  degC_d: "unit.degC_d",
  mm: "unit.mm",
  "mm/d": "unit.mm/d",
  "mm/month": "unit.mm/month",
  "m3/m3": "unit.m3/m3",
  "MJ/m2/d": "unit.MJ/m2/d",
  "m/s": "unit.m/s",
  kPa: "unit.kPa",
  "%": "unit.%",
  m: "unit.m",
  ha: "unit.ha",
  deg: "unit.deg",
  days: "unit.days",
  count: "unit.count",
  probability: "unit.probability",
  "1": "unit.1",
  degF: "unit.degF",
  delta_degF: "unit.delta_degF",
  degF_d: "unit.degF_d",
  in: "unit.in",
  "in/d": "unit.in/d",
  "in/month": "unit.in/month",
  ft: "unit.ft",
  ac: "unit.ac",
  mph: "unit.mph",
};

export function unitLabel(unit: DisplayUnit): string {
  return t(UNIT_LABEL_KEY[unit]);
}

export interface Quantity extends Converted {
  /** Number formatted for display (en-US grouping, fixed decimals). */
  text: string;
  /** Unit symbol from the strings file; empty for dimensionless values. */
  unitLabel: string;
}

/** Convert + round + format. The only way a data number becomes display text (ADR-7). */
export function formatQuantity(
  value: number,
  unit: CanonicalUnit,
  system: UnitSystem,
  digits?: number,
): Quantity {
  const converted = convert(value, unit, system);
  const decimals = digits ?? DEFAULT_DIGITS[converted.unit] ?? 1;
  let text = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(converted.value);
  // A value that rounds to zero is shown as "0", never "-0".
  if (/^-0(\.0+)?$/.test(text)) text = text.slice(1);
  return { ...converted, text, unitLabel: unitLabel(converted.unit) };
}
