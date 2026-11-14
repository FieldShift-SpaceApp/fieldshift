// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Data Loaders (architecture: "Data Loaders", server-only). Read the site JSON files that
// scripts/sync-data.mjs copies to public/data/sites/<site>/, at build time, and check the contract
// major (ADR-4). Synchronous reads, like src/lib/content.ts: the route stays fully static.
//
// Only series.json, indices.json and provenance.json are published today (PR #36); site.json,
// manifest.json and index.json join when the pipeline writes them. A missing required file fails
// the build instead of shipping a page without its numbers.
// The turbopackIgnore comments keep these build-time reads out of the server file tracing: the
// page is prerendered, so nothing reads the data folder at request time.
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import {
  CONTRACT_MAJOR,
  type ClimateIndices,
  type ProvenanceRegistry,
  type SeriesBundle,
} from "@fieldshift/contracts";

export const SITES_DATA_DIR = path.join(process.cwd(), "public", "data", "sites");

/** Files a site needs before it gets a page. */
export const REQUIRED_SITE_FILES = ["series.json", "indices.json", "provenance.json"] as const;

/** Site ids are folder names; anything else never reaches the file system. */
const SITE_ID = /^[a-z0-9][a-z0-9-]*$/;

export interface SiteBundle {
  siteId: string;
  series: SeriesBundle;
  indices: ClimateIndices;
  provenance: ProvenanceRegistry;
}

function readJson<T>(file: string): T {
  try {
    return JSON.parse(readFileSync(/*turbopackIgnore: true*/ file, "utf8")) as T;
  } catch (error) {
    throw new Error(`[data] cannot read ${file}: ${(error as Error).message}. Run "npm run data:sync".`);
  }
}

function assertContract(file: string, doc: { schema_version: string; site_id: string }, siteId: string): void {
  const major = Number(String(doc.schema_version).split(".")[0]);
  if (major !== CONTRACT_MAJOR) {
    throw new Error(`[data] ${file}: contract ${doc.schema_version}; the app expects ${CONTRACT_MAJOR}.x (ADR-4).`);
  }
  if (doc.site_id !== siteId) {
    throw new Error(`[data] ${file}: site_id "${doc.site_id}" does not match folder "${siteId}".`);
  }
}

/** Sites with every required file, sorted. An absent data folder means no sites yet. */
export function listSiteIds(dataDir: string = SITES_DATA_DIR): string[] {
  if (!existsSync(/*turbopackIgnore: true*/ dataDir)) return [];
  return readdirSync(/*turbopackIgnore: true*/ dataDir)
    .filter((id) => SITE_ID.test(id) && statSync(path.join(/*turbopackIgnore: true*/ dataDir, id)).isDirectory())
    .filter((id) => REQUIRED_SITE_FILES.every((f) => existsSync(path.join(/*turbopackIgnore: true*/ dataDir, id, f))))
    .sort();
}

/** Reads one site's files from `siteDir` (a folder holding series/indices/provenance.json). */
export function readSiteBundle(siteDir: string, siteId: string): SiteBundle {
  const series = readJson<SeriesBundle>(path.join(siteDir, "series.json"));
  const indices = readJson<ClimateIndices>(path.join(siteDir, "indices.json"));
  const provenance = readJson<ProvenanceRegistry>(path.join(siteDir, "provenance.json"));
  assertContract("series.json", series, siteId);
  assertContract("indices.json", indices, siteId);
  assertContract("provenance.json", provenance, siteId);
  return { siteId, series, indices, provenance };
}

/** The bundle of a listed site, or null for an unknown id (the page answers 404). */
export function loadSiteBundle(siteId: string, dataDir: string = SITES_DATA_DIR): SiteBundle | null {
  if (!listSiteIds(dataDir).includes(siteId)) return null;
  return readSiteBundle(path.join(/*turbopackIgnore: true*/ dataDir, siteId), siteId);
}
