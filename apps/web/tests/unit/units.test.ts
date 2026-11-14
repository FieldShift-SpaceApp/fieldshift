// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// ADR-7 / VL7: the same parity file the Python test reads.
import fixture from "@fieldshift/contracts/fixtures/units-cases.json";
import type { CanonicalUnit, UnitSystem } from "@fieldshift/contracts";
import { describe, expect, it } from "vitest";
import { convert, formatQuantity, unitLabel, type DisplayUnit } from "@/lib/units";

interface UnitCase {
  value: number;
  unit: CanonicalUnit;
  system: UnitSystem;
  expected_value: number;
  expected_unit: DisplayUnit;
}

const cases = fixture.cases as UnitCase[];

describe("convert: parity fixture (packages/contracts/fixtures/units-cases.json)", () => {
  it("has cases to check", () => {
    expect(cases.length).toBeGreaterThan(0);
  });

  it.each(cases)("$value $unit -> $system = $expected_value $expected_unit", (c) => {
    const out = convert(c.value, c.unit, c.system);
    expect(out.unit).toBe(c.expected_unit);
    expect(Math.abs(out.value - c.expected_value)).toBeLessThanOrEqual(fixture.tolerance);
  });
});

describe("convert: temperature difference", () => {
  it("delta_degC scales by 1.8 WITHOUT +32", () => {
    expect(convert(2, "delta_degC", "imperial").value).toBeCloseTo(3.6, 12);
    expect(convert(0, "delta_degC", "imperial").value).toBe(0);
  });

  it("degree-days also scale without +32", () => {
    expect(convert(10, "degC_d", "imperial")).toEqual({ value: 18, unit: "degF_d" });
  });

  it("an absolute temperature does get +32", () => {
    expect(convert(25, "degC", "imperial").value).toBeCloseTo(77, 12);
  });
});

describe("convert: metric and pass-through", () => {
  it("metric never converts", () => {
    expect(convert(12.5, "mm", "metric")).toEqual({ value: 12.5, unit: "mm" });
  });

  it.each(["kPa", "MJ/m2/d", "deg", "count", "1"] as const)("%s has no imperial form and passes through", (unit) => {
    expect(convert(3, unit, "imperial")).toEqual({ value: 3, unit });
  });
});

describe("formatQuantity", () => {
  it("converts, rounds and labels for display", () => {
    expect(formatQuantity(25, "degC", "imperial", 0)).toMatchObject({ text: "77", unitLabel: "°F", unit: "degF" });
    expect(formatQuantity(25.4, "mm", "imperial", 2)).toMatchObject({ text: "1.00", unitLabel: "in" });
  });

  it("uses the default digits of the display unit", () => {
    expect(formatQuantity(12.6, "mm", "metric").text).toBe("13");
    expect(formatQuantity(21.54, "degC", "metric").text).toBe("21.5");
  });

  it("groups thousands with en-US separators", () => {
    expect(formatQuantity(1234.5, "mm", "metric", 1).text).toBe("1,234.5");
  });

  it("never shows -0", () => {
    expect(formatQuantity(-0.01, "delta_degC", "metric", 1).text).toBe("0.0");
    expect(formatQuantity(-0.2, "mm", "metric").text).toBe("0");
  });

  it("keeps negative values that do not round to zero", () => {
    expect(formatQuantity(-1, "delta_degC", "imperial", 1).text).toBe("-1.8");
  });
});

describe("unitLabel", () => {
  it("dimensionless units have no label", () => {
    expect(unitLabel("1")).toBe("");
    expect(unitLabel("count")).toBe("");
  });
});
