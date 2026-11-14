// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// ADR-8 layer 2 + FR19 + FR23, on test fixtures only (tests/fixtures/provenance-registry.ts).
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MetricValue } from "@/components/provenance/metric-value";
import { ProvenancePanel } from "@/components/provenance/provenance-panel";
import { Value } from "@/components/provenance/value";
import { UnitToggle } from "@/components/site/unit-toggle";
import { t } from "@/i18n";
import { UiStoreProvider } from "@/stores/ui-store";
import { scanVl1 } from "../support/vl1-dom";
import { COMPUTED_ID, MISSING_ID, OBSERVED_ID, fixtureMetric, fixtureRegistry } from "../fixtures/provenance-registry";

afterEach(cleanup);

function Page({ unitSystem = "metric" as const, children }: { unitSystem?: "metric" | "imperial"; children: React.ReactNode }) {
  return (
    <UiStoreProvider unitSystem={unitSystem}>
      <main>
        <UnitToggle />
        {children}
      </main>
      <ProvenancePanel registry={fixtureRegistry} />
    </UiStoreProvider>
  );
}

describe("<Value>", () => {
  it("carries data-prov and converts to imperial only at display (ADR-7, VL1)", () => {
    render(
      <UiStoreProvider unitSystem="imperial">
        <Value value={25} unit="degC" provenanceId={OBSERVED_ID} digits={0} />
      </UiStoreProvider>,
    );
    const el = screen.getByRole("button");
    expect(el.getAttribute("data-prov")).toBe(OBSERVED_ID);
    expect(el.textContent).toBe("77°F");
  });

  it("a missing value still carries data-prov and says it is not available", () => {
    render(
      <UiStoreProvider unitSystem="metric">
        <Value value={null} unit="mm" provenanceId={OBSERVED_ID} />
      </UiStoreProvider>,
    );
    const el = screen.getByText(t("value.unavailable"));
    expect(el.getAttribute("data-prov")).toBe(OBSERVED_ID);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("fails outside a page store instead of rendering an unconverted number", () => {
    expect(() => render(<Value value={1} unit="mm" provenanceId={OBSERVED_ID} />)).toThrow(/UiStoreProvider/);
  });
});

describe("<MetricValue>", () => {
  it("renders the metric through <Value> and shows its data type (FR9)", () => {
    render(
      <Page>
        <MetricValue metric={fixtureMetric} digits={1} />
      </Page>,
    );
    const button = screen.getByRole("button", { name: /show data source/i });
    expect(button.getAttribute("data-prov")).toBe(OBSERVED_ID);
    expect(button.textContent).toBe("25.0°C");
    expect(screen.getByText(t("dataType.satellite_observed"))).toBeTruthy();
  });
});

describe("<UnitToggle> (FR23)", () => {
  it("switching units converts every number on the page", () => {
    render(
      <Page>
        <Value value={0} unit="degC" provenanceId={OBSERVED_ID} digits={0} />
        <Value value={1} unit="delta_degC" provenanceId={OBSERVED_ID} digits={1} />
        <Value value={25.4} unit="mm" provenanceId={COMPUTED_ID} digits={1} />
      </Page>,
    );
    const texts = () => Array.from(document.querySelectorAll("main button[data-prov]")).map((b) => b.textContent);
    expect(texts()).toEqual(["0°C", "1.0°C", "25.4mm"]);

    fireEvent.click(screen.getByRole("button", { name: t("units.system.imperial") }));
    expect(texts()).toEqual(["32°F", "1.8°F", "1.0in"]);
    expect(screen.getByRole("button", { name: t("units.system.imperial") }).getAttribute("aria-pressed")).toBe("true");

    fireEvent.click(screen.getByRole("button", { name: t("units.system.metric") }));
    expect(texts()).toEqual(["0°C", "1.0°C", "25.4mm"]);
  });
});

describe("<ProvenancePanel> (FR19: number -> fields -> source in 2 clicks)", () => {
  it("click 1 opens the panel with the FR19 fields; click 2 target is the source link", () => {
    render(
      <Page>
        <Value value={25} unit="degC" provenanceId={OBSERVED_ID} />
      </Page>,
    );
    expect(screen.queryByRole("dialog")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /show data source/i })); // click 1
    const dialog = screen.getByRole("dialog");
    expect(dialog.getAttribute("data-prov")).toBe(OBSERVED_ID);
    const panel = within(dialog);

    const fields = [
      "provenance.field.dataType",
      "provenance.field.dataset",
      "provenance.field.product",
      "provenance.field.collection",
      "provenance.field.variable",
      "provenance.field.nativeUnit",
      "provenance.field.spatial",
      "provenance.field.temporal",
      "provenance.field.period",
      "provenance.field.aggregation",
      "provenance.field.link",
      "provenance.field.doi",
      "provenance.field.accessedAt",
      "provenance.field.terms",
      "provenance.field.license",
      "provenance.field.limitations",
    ] as const;
    for (const key of fields) expect(panel.getByText(t(key)), key).toBeTruthy();

    expect(panel.getByText("Fixture dataset · Fixture provider")).toBeTruthy();
    expect(panel.getByText("Fixture product · fixture-v0")).toBeTruthy();
    expect(panel.getByText(t("provenance.period.range", { start: "2000-01-01", end: "2000-12-31" }))).toBeTruthy();
    expect(panel.getByText("2000-01-01T00:00:00-03:00")).toBeTruthy();

    const source = panel.getByRole("link", { name: t("provenance.link.source") }); // click 2
    expect(source.getAttribute("href")).toBe("https://example.org/fixture-source");
    expect(source.getAttribute("target")).toBe("_blank");
    expect(source.getAttribute("rel")).toContain("noopener");
    expect(panel.getByRole("link", { name: "10.0000/fixture" }).getAttribute("href")).toBe("https://doi.org/10.0000/fixture");
    expect(panel.getByRole("link", { name: t("provenance.link.terms") }).getAttribute("href")).toBe(
      "https://example.org/fixture-terms",
    );
  });

  it("closes and clears the selection", () => {
    render(
      <Page>
        <Value value={25} unit="degC" provenanceId={OBSERVED_ID} />
      </Page>,
    );
    fireEvent.click(screen.getByRole("button", { name: /show data source/i }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: t("provenance.panel.close") }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("a computed record shows method and lineage; a non-http URL is never a link", () => {
    render(
      <Page>
        <Value value={10} unit="mm" provenanceId={COMPUTED_ID} />
      </Page>,
    );
    fireEvent.click(screen.getByRole("button", { name: /show data source/i }));
    const panel = within(screen.getByRole("dialog"));
    expect(panel.getByText(t("provenance.field.method"))).toBeTruthy();
    expect(panel.getByText(t("provenance.field.inputs"))).toBeTruthy();
    expect(panel.getByText(OBSERVED_ID, { selector: "li" })).toBeTruthy();
    expect(panel.getByText(/Fixture method · Fixture reference/)).toBeTruthy();
    expect(panel.queryByRole("link", { name: "Fixture reference" })).toBeNull();
    expect(panel.getByText(t("provenance.none"))).toBeTruthy(); // empty limitations are stated, not hidden
  });

  it("an id missing from the registry is reported, not silently dropped", () => {
    render(
      <Page>
        <Value value={1} unit="mm" provenanceId={MISSING_ID} />
      </Page>,
    );
    fireEvent.click(screen.getByRole("button", { name: /show data source/i }));
    expect(within(screen.getByRole("dialog")).getByRole("alert").textContent).toBe(
      t("provenance.panel.notFound", { id: MISSING_ID }),
    );
  });
});

describe("VL1 DOM scan (ADR-8 layer 3, shared with the Playwright spec)", () => {
  it("passes when every number is inside <Value> or an exemption", () => {
    render(
      <Page>
        <MetricValue metric={fixtureMetric} />
        <p data-prov-exempt="ui">Step 2 of 3</p>
      </Page>,
    );
    const report = scanVl1();
    expect(report.offenders).toEqual([]);
    expect(report.exemptions).toEqual([{ reason: "ui", text: "Step 2 of 3" }]);
  });

  it("flags a raw number rendered without provenance", () => {
    render(
      <Page>
        <p>Rainfall was 42 mm</p>
      </Page>,
    );
    expect(scanVl1().offenders).toEqual(["Rainfall was 42 mm"]);
  });
});
