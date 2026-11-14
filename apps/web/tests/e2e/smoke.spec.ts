// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Smoke test of the canary page: it opens, shows the FR7 notice and makes zero external requests (NFR2).
import { expect, test } from "@playwright/test";

test("canary page opens with the FR7 notice and no external request", async ({ page, baseURL }) => {
  const origin = new URL(baseURL!).origin;
  const external: string[] = [];
  page.on("request", (req) => {
    const url = req.url();
    if (url.startsWith("data:") || url.startsWith("blob:")) return;
    if (new URL(url).origin !== origin) external.push(url);
  });

  const response = await page.goto("/");
  expect(response?.status()).toBe(200);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByRole("note")).toContainText("does not replace");

  await page.waitForLoadState("networkidle");
  expect(external, "external requests").toEqual([]);
});
