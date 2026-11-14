// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Story 2.3 (FR4, FR21, FR22): agricultural-year axis and soil-cover strip, on the TEST FIXTURE only.
import { cleanup, render, screen, within } from "@testing-library/react";
import type { RotationTimeline } from "@fieldshift/contracts";
import { afterEach, describe, expect, it } from "vitest";
import { AgYearAxis } from "@/components/rotation/ag-year-axis";
import { SOIL_STATES, SoilCoverStrip, soilStateLabel, timelineRows } from "@/components/rotation/soil-cover-strip";
import { t } from "@/i18n";
import { scanVl1 } from "../support/vl1-dom";
import { FIXTURE_START_MONTH, fixtureRotationFile } from "../fixtures/rotation-file";

afterEach(cleanup);

const SEASON_WORDS = /\b(summer|winter|spring|autumn|fall)\b/i;
const { rotation, timeline } = fixtureRotationFile;

function oneYearTimeline(startMonth: number): RotationTimeline {
  const months = Array.from({ length: 12 }, (_, i) => ({
    position: i,
    year_index: 0,
    month: (((startMonth - 1 + i) % 12) + 1) as RotationTimeline["months"][number]["month"],
    state: i < 4 ? ("bare" as const) : ("covered" as const),
    segment_ids: [],
  }));
  return { ...timeline, months };
}

describe("<AgYearAxis>", () => {
  it.each([
    [9, ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]],
    [1, ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]],
    [10, ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]],
  ])("starts at month %i and names the 12 months in order", (startMonth, expected) => {
    render(<AgYearAxis startMonth={startMonth} />);
    const axis = screen.getByRole("list");
    expect(within(axis).getAllByRole("listitem").map((li) => li.textContent)).toEqual(expected);
    expect(axis.getAttribute("aria-label")).toContain(t(`month.long.${startMonth}` as "month.long.1"));
  });

  it("gives the full month name and never a season label (they flip between hemispheres)", () => {
    const { container } = render(<AgYearAxis startMonth={4} />);
    expect(container.querySelector("abbr")?.getAttribute("title")).toBe("April");
    expect(container.textContent).not.toMatch(SEASON_WORDS);
    expect(container.innerHTML).not.toMatch(SEASON_WORDS);
  });

  it("rejects an invalid start month", () => {
    expect(() => render(<AgYearAxis startMonth={13} />)).toThrow(RangeError);
  });
});

describe("<SoilCoverStrip>", () => {
  it("marks the container with the timeline provenance (ADR-8) and passes the VL1 scan", () => {
    const { container } = render(
      <main>
        <SoilCoverStrip timeline={timeline} startMonth={FIXTURE_START_MONTH} rotation={rotation} />
      </main>,
    );
    expect(container.querySelector("figure")?.getAttribute("data-prov")).toBe(timeline.provenance_id);
    expect(scanVl1().offenders).toEqual([]);
  });

  it("renders one row per cycle year, each starting at the site's start month", () => {
    render(<SoilCoverStrip timeline={timeline} startMonth={FIXTURE_START_MONTH} />);
    const rows = screen.getAllByRole("list").filter((el) => el.hasAttribute("data-year-index"));
    expect(rows).toHaveLength(rotation.cycle_years);
    for (const row of rows) {
      const cells = within(row).getAllByRole("listitem");
      expect(cells).toHaveLength(12);
      expect(cells[0].getAttribute("data-month")).toBe(String(FIXTURE_START_MONTH));
    }
    expect(screen.getByText(t("agyear.year", { n: 2 }))).toBeTruthy();
  });

  it("states every month as text and icon, not by color alone", () => {
    const { container } = render(
      <SoilCoverStrip timeline={timeline} startMonth={FIXTURE_START_MONTH} rotation={rotation} />,
    );
    const cells = Array.from(container.querySelectorAll("li[data-month][data-state]"));
    expect(cells).toHaveLength(timeline.months.length);
    cells.forEach((cell, i) => {
      const m = timeline.months[i];
      expect(cell.getAttribute("data-state")).toBe(m.state);
      expect(cell.textContent).toContain(soilStateLabel(m.state));
      expect(cell.getAttribute("title")).toContain(soilStateLabel(m.state));
      expect(cell.querySelector("svg[aria-hidden='true']")).not.toBeNull();
    });
    // Each state has its own icon, so the four states differ in shape as well as in pattern.
    const iconOf = (state: string) =>
      container.querySelector(`li[data-state='${state}'] svg`)?.getAttribute("class");
    expect(new Set(SOIL_STATES.map(iconOf)).size).toBe(SOIL_STATES.length);
  });

  it("shows the bare, residue and transition months of the fixture where the pipeline put them", () => {
    render(<SoilCoverStrip timeline={timeline} startMonth={FIXTURE_START_MONTH} rotation={rotation} />);
    expect(screen.getByText("July: Bare soil (TEST FIXTURE bare fallow)")).toBeTruthy();
    expect(screen.getByText("September: Bare soil")).toBeTruthy(); // year 2: no segment
    expect(screen.getByText("September: Crop residue (TEST FIXTURE fallow with residue)")).toBeTruthy();
    expect(
      screen.getByText("February: Covered (TEST FIXTURE cash crop, year 1, TEST FIXTURE second crop, year 1)"),
    ).toBeTruthy();
  });

  it("has a legend with icon and text for the four soil states", () => {
    render(<SoilCoverStrip timeline={timeline} startMonth={FIXTURE_START_MONTH} />);
    const legend = screen.getByRole("list", { name: t("soil.strip.legend") });
    const items = within(legend).getAllByRole("listitem");
    expect(items.map((li) => li.textContent)).toEqual(SOIL_STATES.map(soilStateLabel));
    for (const li of items) expect(li.querySelector("svg")).not.toBeNull();
  });

  it("a one-year cycle has no year labels", () => {
    render(<SoilCoverStrip timeline={oneYearTimeline(4)} startMonth={4} />);
    expect(screen.queryByText(t("agyear.year", { n: 1 }))).toBeNull();
    expect(screen.getByText("April: Bare soil")).toBeTruthy();
  });

  it("refuses a timeline derived with another start month instead of mislabeling months", () => {
    expect(() => render(<SoilCoverStrip timeline={timeline} startMonth={1} />)).toThrow(RangeError);
    expect(() => timelineRows({ ...timeline, months: timeline.months.slice(0, 5) }, FIXTURE_START_MONTH)).toThrow(
      /multiple of 12/,
    );
  });

  it("uses no season labels", () => {
    const { container } = render(
      <SoilCoverStrip timeline={timeline} startMonth={FIXTURE_START_MONTH} rotation={rotation} />,
    );
    expect(container.innerHTML).not.toMatch(SEASON_WORDS);
  });
});
