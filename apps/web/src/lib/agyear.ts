// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// ADR-7 / FR22: agricultural year per site. No logic uses season or hemisphere.
// Parity with services/science/src/fieldshift/calendar/agyear.py through
// packages/contracts/fixtures/agyear-cases.json.
import type { AgYear, Month } from "@fieldshift/contracts";

const ISO = /^(\d{4})-(0[1-9]|1[0-2])(-\d{2})?$/;

function checkStartMonth(startMonth: number): void {
  if (!Number.isInteger(startMonth) || startMonth < 1 || startMonth > 12) {
    throw new RangeError(`startMonth must be 1..12, got ${startMonth}`);
  }
}

function checkMonth(month: number): void {
  if (!Number.isInteger(month) || month < 1 || month > 12) {
    throw new RangeError(`month must be 1..12, got ${month}`);
  }
}

/** Civil year and month of an ISO "YYYY-MM" or "YYYY-MM-DD" string (no time zone involved). */
export function yearMonth(t: string): { year: number; month: Month } {
  const match = ISO.exec(t);
  if (!match) throw new RangeError(`expected YYYY-MM or YYYY-MM-DD, got "${t}"`);
  return { year: Number(match[1]), month: Number(match[2]) as Month };
}

/** `year` if `month >= startMonth`, else `year - 1`. */
export function agYearOf(t: string, startMonth: number): number {
  checkStartMonth(startMonth);
  const { year, month } = yearMonth(t);
  return month >= startMonth ? year : year - 1;
}

/** Position of a civil month inside the agricultural year: 0 = startMonth … 11. */
export function agMonthIndex(month: number, startMonth: number): number {
  checkStartMonth(startMonth);
  checkMonth(month);
  return (((month - startMonth) % 12) + 12) % 12;
}

/** "single" -> "2024"; "split" -> "2024/25" (agricultural year crossing the new year). */
export function agYearLabel(agYear: number, label: AgYear["label"]): string {
  switch (label) {
    case "single":
      return String(agYear);
    case "split":
      return `${agYear}/${String((agYear + 1) % 100).padStart(2, "0")}`;
    default:
      throw new RangeError(`label must be "single" or "split", got "${String(label)}"`);
  }
}

/** The 12 civil months in agricultural-year order: every time axis starts at the site's startMonth. */
export function agYearMonths(startMonth: number): Month[] {
  checkStartMonth(startMonth);
  return Array.from({ length: 12 }, (_, i) => (((startMonth - 1 + i) % 12) + 1) as Month);
}

/**
 * Reorders a January-first array of 12 monthly values (e.g. `MonthlyProfile.values`)
 * so it starts at the site's startMonth. Values are kept as they are (null stays null).
 */
export function toAgYearOrder<T>(values: readonly T[], startMonth: number): { month: Month; value: T }[] {
  if (values.length !== 12) throw new RangeError(`expected 12 monthly values, got ${values.length}`);
  return agYearMonths(startMonth).map((month) => ({ month, value: values[month - 1] }));
}
