// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// ADR-7 / VL7: same parity file as services/science (fieldshift.calendar.agyear).
import fixture from "@fieldshift/contracts/fixtures/agyear-cases.json";
import type { AgYear } from "@fieldshift/contracts";
import { describe, expect, it } from "vitest";
import { agMonthIndex, agYearLabel, agYearMonths, agYearOf, toAgYearOrder, yearMonth } from "@/lib/agyear";

interface AgYearCase {
  t: string;
  start_month: number;
  label: AgYear["label"];
  ag_year: number;
  ag_month_index: number;
  ag_year_label: string;
}

const cases = fixture.cases as AgYearCase[];

describe("agricultural year: parity fixture (packages/contracts/fixtures/agyear-cases.json)", () => {
  it("has cases to check", () => {
    expect(cases.length).toBeGreaterThan(0);
  });

  it.each(cases)("$t, start $start_month -> $ag_year_label (index $ag_month_index)", (c) => {
    const agYear = agYearOf(c.t, c.start_month);
    expect(agYear).toBe(c.ag_year);
    expect(agMonthIndex(yearMonth(c.t).month, c.start_month)).toBe(c.ag_month_index);
    expect(agYearLabel(agYear, c.label)).toBe(c.ag_year_label);
  });
});

describe("agricultural year: invalid input fails loudly", () => {
  it.each([0, 13, 1.5])("start month %s", (start) => {
    expect(() => agYearOf("2024-01", start)).toThrow(RangeError);
  });

  it.each(["2024", "2024-13", "24-01", "2024/01", ""])("date %j", (t) => {
    expect(() => agYearOf(t, 9)).toThrow(RangeError);
  });

  it("month outside 1..12", () => {
    expect(() => agMonthIndex(0, 9)).toThrow(RangeError);
  });
});

describe("agricultural-year order", () => {
  it("every axis starts at the site's start month", () => {
    expect(agYearMonths(9)).toEqual([9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8]);
    expect(agYearMonths(1)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);
  });

  it("reorders January-first monthly values and keeps nulls", () => {
    const values = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", null];
    const ordered = toAgYearOrder(values, 10);
    expect(ordered[0]).toEqual({ month: 10, value: "oct" });
    expect(ordered[2]).toEqual({ month: 12, value: null });
    expect(ordered[3]).toEqual({ month: 1, value: "jan" });
    expect(ordered).toHaveLength(12);
  });

  it("rejects a profile that is not 12 months long", () => {
    expect(() => toAgYearOrder([1, 2, 3], 9)).toThrow(RangeError);
  });
});
