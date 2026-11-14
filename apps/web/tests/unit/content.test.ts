// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Content loaders for /data-methods and /glossary, run against the real repository files
// (the repo root has the same layout that scripts/sync-data.mjs copies into src/generated/).
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  loadDataMethods,
  loadGlossary,
  loadMethods,
  REPO_BLOB_URL,
  resolveDocHref,
  stripTitle,
} from "@/lib/content";

const REPO_ROOT = path.resolve(import.meta.dirname, "../../../..");

/** FR8 + task list: terms the glossary must explain. */
const REQUIRED_TERMS = [
  "et",
  "et0",
  "ndvi",
  "anomaly",
  "water-balance",
  "growing-degree-days",
  "frost-risk",
  "soil-moisture",
  "reanalysis",
  "satellite-vs-ground",
  "satellite-observed",
  "modeled",
  "computed",
  "user-provided",
];

function tempRepo(files: Record<string, string>): string {
  const root = mkdtempSync(path.join(tmpdir(), "fieldshift-content-"));
  for (const [rel, text] of Object.entries(files)) {
    mkdirSync(path.dirname(path.join(root, rel)), { recursive: true });
    writeFileSync(path.join(root, rel), text);
  }
  return root;
}

/** Every method.doc_anchor in the published (and DEV) provenance registries under data/. */
function provenanceDocAnchors(): string[] {
  const anchors: string[] = [];
  for (const group of ["sites", "dev"]) {
    const dir = path.join(REPO_ROOT, "data", group);
    if (!existsSync(dir)) continue;
    for (const site of readdirSync(dir)) {
      const file = path.join(dir, site, "output", "provenance.json");
      if (!existsSync(file)) continue;
      const registry = JSON.parse(readFileSync(file, "utf8")) as {
        records: Record<string, { method?: { doc_anchor?: string } | null }>;
      };
      for (const record of Object.values(registry.records)) {
        if (record.method?.doc_anchor) anchors.push(record.method.doc_anchor);
      }
    }
  }
  return anchors;
}

describe("content loaders on the repository files", () => {
  it("loads every Data & Methods source", () => {
    const content = loadDataMethods(REPO_ROOT);
    expect(content.resources.body).toContain("NASA POWER");
    expect(content.resources.body.startsWith("# ")).toBe(false);
    expect(content.siUsage.body).toContain("| Date/time (BRT) |");
    expect(content.methods.length).toBeGreaterThan(0);
    expect(content.glossary.length).toBeGreaterThan(0);
  });

  it("has the methods decided in the architecture, each with refs and a body", () => {
    const methods = loadMethods(REPO_ROOT);
    const anchors = methods.map((m) => m.anchor);
    for (const a of ["nasa-power", "et0-fao56", "monthly-harmonization", "units-calendar", "provenance"]) {
      expect(anchors).toContain(a);
    }
    expect(new Set(anchors).size).toBe(anchors.length);
    for (const m of methods) {
      expect(m.refs.length, m.anchor).toBeGreaterThan(0);
      expect(m.body.length, m.anchor).toBeGreaterThan(0);
    }
    expect(methods.find((m) => m.anchor === "nasa-power")?.limitations.join(" ")).toContain("EVPTRNS");
  });

  it("defines every method.doc_anchor used by a provenance record (VL1, ADR-8)", () => {
    const anchors = new Set(loadMethods(REPO_ROOT).map((m) => m.anchor));
    for (const used of provenanceDocAnchors()) expect(anchors, used).toContain(used);
  });

  it("covers the 11 related-work categories with links and keeps 'how we differ' pending (FR18, C1)", () => {
    const { relatedWork } = loadDataMethods(REPO_ROOT);
    const sections = relatedWork.body.split(/^## /m).slice(1);
    const categories = sections.filter((s) => /^\d+\./.test(s));
    expect(categories.map((s) => Number.parseInt(s, 10))).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]);
    for (const c of categories) expect(c, c.split("\n")[0]).toMatch(/\]\((https:\/\/|\/)/);
    const differ = sections.find((s) => s.startsWith("How we differ"));
    expect(differ).toContain("Pending D-001");
  });

  it("explains every required glossary term and records review status (FR8)", () => {
    const glossary = loadGlossary(REPO_ROOT);
    const ids = glossary.map((g) => g.id);
    for (const id of REQUIRED_TERMS) expect(ids).toContain(id);
    for (const g of glossary) expect(g.reviewedBy, g.id).not.toBe("");
  });
});

describe("content loader validation", () => {
  it("rejects a method without an anchor", () => {
    const root = tempRepo({ "content/methods/x.md": "---\ntitle: X\nrefs:\n  - {label: a, url: https://a.org}\n---\nBody\n" });
    expect(() => loadMethods(root)).toThrow(/anchor/);
  });

  it("rejects duplicate method anchors and methods without refs", () => {
    const method = "---\nanchor: same\ntitle: X\nrefs:\n  - {label: a, url: https://a.org}\n---\nBody\n";
    expect(() => loadMethods(tempRepo({ "content/methods/a.md": method, "content/methods/b.md": method }))).toThrow(/duplicate/);
    expect(() => loadMethods(tempRepo({ "content/methods/a.md": "---\nanchor: a\ntitle: A\n---\nBody\n" }))).toThrow(/ref/);
  });

  it("skips the methods README and sorts by order", () => {
    const m = (anchor: string, order: number) =>
      `---\nanchor: ${anchor}\ntitle: ${anchor}\norder: ${order}\nrefs:\n  - {label: a, url: https://a.org}\n---\nBody\n`;
    const root = tempRepo({
      "content/methods/README.md": "# Methods\n",
      "content/methods/b.md": m("second", 2),
      "content/methods/a.md": m("first", 1),
    });
    expect(loadMethods(root).map((x) => x.anchor)).toEqual(["first", "second"]);
  });

  it("rejects duplicate glossary ids and terms without a definition", () => {
    const term = "  - id: et\n    term: {en: ET}\n    definition: {en: Water loss}\n    reviewed_by: pending\n";
    expect(() => loadGlossary(tempRepo({ "content/glossary.yaml": `terms:\n${term}${term}` }))).toThrow(/duplicate/);
    const noDef = "terms:\n  - id: et\n    term: {en: ET}\n    reviewed_by: pending\n";
    expect(() => loadGlossary(tempRepo({ "content/glossary.yaml": noDef }))).toThrow(/definition/);
  });

  it("fails clearly when a required file is missing", () => {
    expect(() => loadDataMethods(tempRepo({}))).toThrow(/RESOURCES\.md/);
  });
});

describe("markdown helpers", () => {
  it("strips only the leading title", () => {
    expect(stripTitle("# Title\n\nText\n# Not a title")).toBe("\nText\n# Not a title");
  });

  it("resolves links safely", () => {
    expect(resolveDocHref("SI-USAGE.md", "RESOURCES.md")).toBe(`${REPO_BLOB_URL}SI-USAGE.md`);
    expect(resolveDocHref("../../RESOURCES.md", "content/methods/README.md")).toBe(`${REPO_BLOB_URL}RESOURCES.md`);
    expect(resolveDocHref("https://power.larc.nasa.gov/", "RESOURCES.md")).toBe("https://power.larc.nasa.gov/");
    expect(resolveDocHref("#nasa-power", "x.md")).toBe("#nasa-power");
    expect(resolveDocHref("/glossary#et", "x.md")).toBe("/glossary#et");
    expect(resolveDocHref("javascript:alert(1)", "x.md")).toBeNull();
    expect(resolveDocHref("../outside.md", "RESOURCES.md")).toBeNull();
  });
});
