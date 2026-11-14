// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// ADR-8, layer 3: every text node with a digit inside <main> needs an ancestor with [data-prov]
// or [data-prov-exempt]. Shared by the Vitest test (jsdom) and the Playwright spec (real browser):
// the function must stay self-contained, because Playwright serializes it into the page.

export interface Vl1Report {
  /** Text with a digit and no provenance ancestor (must be empty). */
  offenders: string[];
  /** Every exemption on the page, so the PR review sees them (ADR-8: each one is reviewed). */
  exemptions: { reason: string; text: string }[];
}

export function scanVl1(): Vl1Report {
  const root = document.querySelector("main");
  if (!root) return { offenders: ["<main> not found"], exemptions: [] };
  const offenders: string[] = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const text = node.textContent ?? "";
    if (!/\d/.test(text)) continue;
    const el = node.parentElement;
    if (!el || el.closest("script, style, [data-prov], [data-prov-exempt]")) continue;
    offenders.push(text.trim().slice(0, 80));
  }
  const exemptions = Array.from(root.querySelectorAll("[data-prov-exempt]")).map((el) => ({
    reason: el.getAttribute("data-prov-exempt") ?? "",
    text: (el.textContent ?? "").trim().slice(0, 80),
  }));
  return { offenders, exemptions };
}
