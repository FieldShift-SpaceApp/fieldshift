#!/usr/bin/env node
// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// scripts/sync-data.mjs — Data Sync (architecture.md, "App > Data Sync"). Runs as `prebuild` of apps/web.
// Copies data/sites/<site>/output → apps/web/public/data/sites/<site>/ and
// content/** + RESOURCES.md + SI-USAGE.md → apps/web/src/generated/.
// No site data yet is fine (prints a notice); a missing compliance file is an error.
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const REQUIRED_DOCS = ["RESOURCES.md", "SI-USAGE.md"];

/**
 * @param {{ repoRoot: string, log?: (msg: string) => void }} options
 * @returns {{ sites: string[], docs: string[], content: boolean }}
 */
export function syncData({ repoRoot, log = console.log }) {
  const webRoot = path.join(repoRoot, "apps", "web");
  const sitesSrc = path.join(repoRoot, "data", "sites");
  const sitesDst = path.join(webRoot, "public", "data", "sites");
  const generatedDst = path.join(webRoot, "src", "generated");

  const missing = REQUIRED_DOCS.filter((f) => !existsSync(path.join(repoRoot, f)));
  if (missing.length > 0) {
    throw new Error(`sync-data: required file(s) missing at repo root: ${missing.join(", ")}`);
  }

  // Both destinations are generated and git-ignored: start clean so removed files do not linger.
  rmSync(sitesDst, { recursive: true, force: true });
  rmSync(generatedDst, { recursive: true, force: true });
  mkdirSync(sitesDst, { recursive: true });
  mkdirSync(generatedDst, { recursive: true });

  const sites = [];
  if (existsSync(sitesSrc)) {
    for (const site of readdirSync(sitesSrc).sort()) {
      const output = path.join(sitesSrc, site, "output");
      if (existsSync(output) && statSync(output).isDirectory()) {
        cpSync(output, path.join(sitesDst, site), { recursive: true });
        sites.push(site);
      }
    }
  }
  if (sites.length === 0) {
    log("sync-data: no data/sites/*/output yet; the app builds without site data");
  }

  for (const file of REQUIRED_DOCS) {
    cpSync(path.join(repoRoot, file), path.join(generatedDst, file));
  }

  const contentSrc = path.join(repoRoot, "content");
  const content = existsSync(contentSrc);
  if (content) {
    cpSync(contentSrc, path.join(generatedDst, "content"), { recursive: true });
  }

  log(`sync-data: sites=[${sites.join(", ")}] docs=[${REQUIRED_DOCS.join(", ")}] content=${content}`);
  return { sites, docs: [...REQUIRED_DOCS], content };
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  try {
    syncData({ repoRoot });
  } catch (err) {
    console.error(err instanceof Error ? err.message : err);
    process.exit(1);
  }
}
