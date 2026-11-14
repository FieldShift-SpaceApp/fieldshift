// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// T2 site page on the production build: opens from the entry page, shows numbers with provenance,
// every data-prov id exists in the site's provenance.json, no console error, no external request,
// no horizontal scroll at 360 px.
import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import type { ProvenanceRegistry } from "@fieldshift/contracts";

const ROUTE = "/sites/cruz-alta";
const registry = JSON.parse(
  readFileSync(path.join(process.cwd(), "public", "data", "sites", "cruz-alta", "provenance.json"), "utf8"),
) as ProvenanceRegistry;

function watch(page: Page, origin: string) {
  const errors: string[] = [];
  const external: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });
  page.on("pageerror", (err) => errors.push(err.message));
  page.on("request", (req) => {
    const url = req.url();
    if (url.startsWith("data:") || url.startsWith("blob:")) return;
    if (new URL(url).origin !== origin) external.push(url);
  });
  return { errors, external };
}

test("site page opens from the entry page and shows numbers with provenance", async ({ page, baseURL }) => {
  const { errors, external } = watch(page, new URL(baseURL!).origin);

  await page.goto("/");
  await page.getByRole("link", { name: "Cruz Alta, RS, Brazil" }).click();
  await expect(page).toHaveURL(new RegExp(`${ROUTE}$`));
  await expect(page.getByRole("heading", { level: 1, name: "Cruz Alta, RS, Brazil" })).toBeVisible();

  const values = page.locator("main button[data-prov]");
  expect(await values.count()).toBeGreaterThan(10);

  // Every data-prov on the page points to a record of the site registry (ADR-8, layer 3).
  const ids = await page.locator("main [data-prov]").evaluateAll((els) =>
    els.flatMap((el) => (el.getAttribute("data-prov") ?? "").split(" ").filter(Boolean)),
  );
  const unknown = [...new Set(ids)].filter((id) => !registry.records[id]);
  expect(unknown, "data-prov ids missing from provenance.json").toEqual([]);

  // Click 1 opens the panel with the FR19 fields and the ground-check limitation (#31).
  await page.getByRole("button", { name: /days\. Show data source/ }).first().click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText("Limitations")).toBeVisible();
  await expect(dialog.getByText(/^Ground check/)).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();

  await expect(page.getByRole("link", { name: "Satellite and reanalysis vs. ground stations" })).toHaveAttribute(
    "href",
    "/data-methods#satellite-vs-ground-check",
  );

  await page.waitForLoadState("networkidle");
  expect(errors, "console errors").toEqual([]);
  expect(external, "external requests").toEqual([]);
});

test("unit toggle converts the numbers on the site page (FR23)", async ({ page }) => {
  await page.goto(ROUTE);
  await page.getByRole("button", { name: "Imperial" }).click();
  await expect(page.getByRole("button", { name: /°F·d\. Show data source/ }).first()).toBeVisible();
});

test("site page has no horizontal scroll at 360 px", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto(ROUTE);
  await page.waitForLoadState("networkidle");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});

// With Cache Components the fallback shell streams first, so `next start` answers HTTP 200 and
// renders the not-found page; the check is on the content, not the status code.
test("unknown site id renders the not-found page", async ({ page }) => {
  await page.goto("/sites/not-a-site");
  await expect(page.getByText("This page could not be found.")).toBeVisible();
  await expect(page.locator("main button[data-prov]")).toHaveCount(0);
});
