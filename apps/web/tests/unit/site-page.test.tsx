// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Site page (T2): loader, view model and sections, read from the published Cruz Alta files
// (data/sites/cruz-alta/output, the source scripts/sync-data.mjs copies). Values are compared with
// the JSON itself, never with numbers typed here (VL1, "never invent numbers").
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { ClimateIndices, ProvenanceRegistry, SeriesBundle } from "@fieldshift/contracts";
import { ProvenancePanel } from "@/components/provenance/provenance-panel";
import {
  GroundCheckSection,
  IndicesSection,
  ProfilesSection,
  RecentSection,
  SiteHeader,
} from "@/components/site/site-sections";
import { listSiteIds, loadSiteBundle, readSiteBundle } from "@/lib/data/loaders";
import { siteName } from "@/lib/site-name";
import { buildSiteView, recentRows, requestedPoint, RECENT_MONTHS } from "@/lib/site-view";
import { UiStoreProvider } from "@/stores/ui-store";
import { scanVl1 } from "../support/vl1-dom";

afterEach(cleanup);

const REPO = path.resolve(import.meta.dirname, "../../../..");
const SITE_DIR = path.join(REPO, "data", "sites", "cruz-alta", "output");
const readRaw = <T,>(file: string) => JSON.parse(readFileSync(path.join(SITE_DIR, file), "utf8")) as T;

describe("data loaders", () => {
  it("reads the published Cruz Alta files and checks the contract major", () => {
    const bundle = readSiteBundle(SITE_DIR, "cruz-alta");
    expect(bundle.series.series.length).toBeGreaterThan(0);
    expect(bundle.indices.metrics.length).toBeGreaterThan(0);
    expect(Object.keys(bundle.provenance.records).length).toBeGreaterThan(0);
  });

  it("fails when site_id does not match the folder", () => {
    expect(() => readSiteBundle(SITE_DIR, "other-site")).toThrow(/does not match folder/);
  });

  it("lists only folders with every required file and returns null for unknown ids", () => {
    const root = mkdtempSync(path.join(tmpdir(), "fieldshift-sites-"));
    mkdirSync(path.join(root, "complete"));
    mkdirSync(path.join(root, "partial"));
    for (const f of ["series.json", "indices.json", "provenance.json"]) {
      writeFileSync(path.join(root, "complete", f), "{}");
    }
    writeFileSync(path.join(root, "partial", "series.json"), "{}");
    mkdirSync(path.join(root, "Bad_Id"));
    expect(listSiteIds(root)).toEqual(["complete"]);
    expect(loadSiteBundle("partial", root)).toBeNull();
    expect(loadSiteBundle("../complete", root)).toBeNull();
    expect(listSiteIds(path.join(root, "missing"))).toEqual([]);
  });

  it("fails on a contract major the app does not know (ADR-4)", () => {
    const root = mkdtempSync(path.join(tmpdir(), "fieldshift-major-"));
    for (const f of ["series.json", "indices.json", "provenance.json"]) {
      writeFileSync(path.join(root, f), JSON.stringify({ schema_version: "9.0.0", site_id: "x" }));
    }
    expect(() => readSiteBundle(root, "x")).toThrow(/expects 1\.x/);
  });
});

describe("site view model", () => {
  const bundle = readSiteBundle(SITE_DIR, "cruz-alta");
  const view = buildSiteView(bundle);
  const series = readRaw<SeriesBundle>("series.json").series;
  const registry = readRaw<ProvenanceRegistry>("provenance.json");

  it("reads the point back from the NASA POWER request URL in the provenance", () => {
    const precip = series.find((s) => s.variable_key === "precip")!;
    const url = new URL(registry.records[precip.provenance_id].access!.url);
    expect(view.point).toEqual({
      lat: Number(url.searchParams.get("latitude")),
      lon: Number(url.searchParams.get("longitude")),
      provenanceId: precip.provenance_id,
    });
    expect(requestedPoint(undefined)).toBeNull();
  });

  it("copies the last months of precipitation, Tmax and Tmin as published", () => {
    expect(view.recent?.rows).toHaveLength(RECENT_MONTHS);
    const keys = ["precip", "air_temp_max", "air_temp_min"];
    for (const row of view.recent!.rows) {
      keys.forEach((key, i) => {
        const s = series.find((x) => x.variable_key === key && x.frequency === "monthly")!;
        expect(row.values[i]).toBe(s.points.find((p) => p.t === row.t)!.v);
      });
    }
    const last = view.recent!.rows.at(-1)!.t;
    expect(last).toBe(series.find((s) => s.variable_key === "precip")!.coverage.last);
  });

  it("aligns series by month and skips months without any value", () => {
    const a = { ...series[0], points: [{ t: "2000-01", v: 1 }, { t: "2000-02", v: null }, { t: "2000-03", v: 3 }] };
    const b = { ...series[0], points: [{ t: "2000-01", v: 5 }, { t: "2000-02", v: null }] };
    expect(recentRows([a, b], 5)).toEqual([
      { t: "2000-01", values: [1, 5] },
      { t: "2000-03", values: [3, null] },
    ]);
  });

  it("every provenance id on the page exists, and only those records go to the client", () => {
    expect(view.provenanceIds.length).toBeGreaterThan(0);
    for (const id of view.provenanceIds) expect(registry.records[id]).toBeDefined();
    expect(Object.keys(view.records).sort()).toEqual([...view.provenanceIds].sort());
    expect(view.metrics).toEqual(readRaw<ClimateIndices>("indices.json").metrics);
  });

  it("surfaces the ground-check limitations (#31) of the records on the page", () => {
    expect(view.groundCheck.length).toBeGreaterThanOrEqual(2);
    for (const note of view.groundCheck) {
      expect(note.text.startsWith("Ground check")).toBe(true);
      for (const a of note.appliesTo) {
        expect(registry.records[a.id].limitations.map((l) => l.en)).toContain(note.text);
      }
    }
  });

  it("fails when a value points to a missing record (VL1)", () => {
    const broken = structuredClone(bundle);
    delete broken.provenance.records[broken.indices.metrics[0].provenance_id];
    expect(() => buildSiteView(broken)).toThrow(/provenance records missing/);
  });
});

describe("site page sections", () => {
  const view = buildSiteView(readSiteBundle(SITE_DIR, "cruz-alta"));

  function Page() {
    return (
      <UiStoreProvider unitSystem="metric">
        <main>
          <SiteHeader name={siteName("cruz-alta")} view={view} />
          <RecentSection view={view} />
          <IndicesSection view={view} />
          <ProfilesSection view={view} />
          <GroundCheckSection view={view} />
        </main>
        <ProvenancePanel registry={{ records: view.records }} />
      </UiStoreProvider>
    );
  }

  it("every number in <main> has provenance, with no exemption (VL1 layer 3)", () => {
    render(<Page />);
    const report = scanVl1();
    expect(report.offenders).toEqual([]);
    expect(report.exemptions).toEqual([]);
  });

  it("a metric opens its record with the ground-check limitation", () => {
    render(<Page />);
    const heat = view.metrics.find((m) => m.index_key === "heat_days")!;
    const button = document.querySelector<HTMLButtonElement>(`button[data-prov="${heat.provenance_id}"]`)!;
    expect(button).not.toBeNull();
    fireEvent.click(button);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText(heat.provenance_id)).toBeDefined();
    expect(within(dialog).getByText(/^Ground check/)).toBeDefined();
  });

  it("links to the ground-check method section", () => {
    render(<Page />);
    const link = screen.getByRole("link", { name: "Satellite and reanalysis vs. ground stations" });
    expect(link.getAttribute("href")).toBe("/data-methods#satellite-vs-ground-check");
  });

  it("falls back to the site id when a name is not in the strings file", () => {
    expect(siteName("cruz-alta")).toBe("Cruz Alta, RS, Brazil");
    expect(siteName("unknown-site")).toBe("unknown-site");
  });
});
