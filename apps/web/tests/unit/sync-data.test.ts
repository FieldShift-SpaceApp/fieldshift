// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { syncData } from "../../../../scripts/sync-data.mjs";

function fakeRepo(): string {
  const root = mkdtempSync(path.join(tmpdir(), "fieldshift-sync-"));
  writeFileSync(path.join(root, "RESOURCES.md"), "# Resources\n");
  writeFileSync(path.join(root, "SI-USAGE.md"), "# SI usage\n");
  return root;
}

const quiet = () => {};

describe("scripts/sync-data.mjs", () => {
  it("does not fail when there is no site data yet", () => {
    const root = fakeRepo();
    const result = syncData({ repoRoot: root, log: quiet });
    expect(result.sites).toEqual([]);
    expect(existsSync(path.join(root, "apps/web/src/generated/SI-USAGE.md"))).toBe(true);
  });

  it("copies data/sites/<site>/output into public/data/sites/<site>", () => {
    const root = fakeRepo();
    mkdirSync(path.join(root, "data/sites/demo/output"), { recursive: true });
    writeFileSync(path.join(root, "data/sites/demo/output/site.json"), '{"id":"demo"}');
    mkdirSync(path.join(root, "data/sites/no-output"), { recursive: true });

    const result = syncData({ repoRoot: root, log: quiet });

    expect(result.sites).toEqual(["demo"]);
    const copied = path.join(root, "apps/web/public/data/sites/demo/site.json");
    expect(readFileSync(copied, "utf8")).toBe('{"id":"demo"}');
  });

  it("fails when a required compliance file is missing", () => {
    const root = mkdtempSync(path.join(tmpdir(), "fieldshift-sync-"));
    expect(() => syncData({ repoRoot: root, log: quiet })).toThrow(/RESOURCES\.md, SI-USAGE\.md/);
  });
});
