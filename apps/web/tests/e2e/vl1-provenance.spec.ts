// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// ADR-8, layer 3 (VL1 in the DOM). Add each new route here as it ships; the registry check
// ("every data-prov exists in the site registry") joins when real site data exists (Story 2.2).
import { expect, test } from "@playwright/test";
import { scanVl1 } from "../support/vl1-dom";

// /data-methods and /glossary show documentation, not data values; their blocks are exempt and listed.
// /sites/cruz-alta shows data: every number has data-prov (the registry check is in site-page.spec.ts).
const ROUTES = ["/", "/data-methods", "/glossary", "/sites/cruz-alta"];

for (const route of ROUTES) {
  test(`VL1: every number in <main> on ${route} has provenance or a reviewed exemption`, async ({ page }) => {
    await page.goto(route);
    const report = await page.evaluate(scanVl1);
    expect(report.offenders, `numbers without provenance on ${route}`).toEqual([]);
    // ADR-8: only interface numbers may be exempt, and every exemption is listed for review.
    for (const exemption of report.exemptions) expect(exemption.reason, exemption.text).toBe("ui");
    test.info().annotations.push({
      type: "vl1-exemptions",
      description: JSON.stringify(report.exemptions),
    });
  });
}
