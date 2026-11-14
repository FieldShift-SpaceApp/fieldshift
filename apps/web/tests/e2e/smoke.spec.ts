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

// Story 1.4: both content pages open, are linked from the entry page and make no external request.
for (const [route, heading] of [
  ["/data-methods", "Data & Methods"],
  ["/glossary", "Glossary"],
] as const) {
  test(`${route} opens from the entry page with no external request`, async ({ page, baseURL }) => {
    const origin = new URL(baseURL!).origin;
    const external: string[] = [];
    page.on("request", (req) => {
      const url = req.url();
      if (url.startsWith("data:") || url.startsWith("blob:")) return;
      if (new URL(url).origin !== origin) external.push(url);
    });

    await page.goto("/");
    await page.getByRole("navigation", { name: "Pages" }).getByRole("link", { name: heading }).click();
    await expect(page).toHaveURL(new RegExp(`${route}$`));
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();

    const response = await page.goto(route);
    expect(response?.status()).toBe(200);
    await page.waitForLoadState("networkidle");
    expect(external, "external requests").toEqual([]);
  });
}
