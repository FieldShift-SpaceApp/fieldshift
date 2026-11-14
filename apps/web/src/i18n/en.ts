// All user-facing strings live here (NFR15). Portuguese (pt.ts) is a stretch goal.
// The product name and concept are team decisions (C1): keep the working title until DECISIONS.md says otherwise.
export const en = {
  "meta.title": "FieldShift (working title)",
  "meta.description": "NASA Space Apps Challenge 2026 project. Work in progress.",
  "canary.heading": "FieldShift (working title)",
  "canary.body": "NASA Space Apps Challenge 2026. This page is a deployment canary: the app is under construction.",
  "disclaimer.support":
    "This tool supports, and does not replace, the judgment of farmers and agronomists. It explores options; it does not prescribe actions or promise yields, profit or carbon credits.",
} as const;

export type MessageKey = keyof typeof en;
