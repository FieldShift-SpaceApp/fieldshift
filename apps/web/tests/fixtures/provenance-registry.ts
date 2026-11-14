// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// TEST FIXTURE. Not real data: every field says so, and nothing here is shown on a public page.
// Shape follows the Provenance contract (packages/contracts) so the panel is tested on all FR19 fields.
import type { Metric, ProvenanceRegistry } from "@fieldshift/contracts";

export const OBSERVED_ID = "prov:fixture:test:observed:daily";
export const COMPUTED_ID = "prov:fixture:test:computed:monthly";
export const MISSING_ID = "prov:fixture:test:missing:daily";

export const fixtureRegistry: ProvenanceRegistry = {
  schema_version: "1.0.0",
  site_id: "global",
  records: {
    [OBSERVED_ID]: {
      id: OBSERVED_ID,
      data_type: "satellite_observed",
      title: { en: "TEST FIXTURE observed record" },
      source: {
        dataset: "Fixture dataset",
        provider: "Fixture provider",
        product: "Fixture product",
        version: "fixture-v0",
        collection_id: "FIXTURE/COLLECTION/0",
      },
      variable: { code: "fixture_var", name: { en: "Fixture variable" }, unit: "degC", native_unit: "K" },
      spatial: { resolution: "fixture km", support: "containing_pixel" },
      temporal: { resolution: "daily", period: { start: "2000-01-01", end: "2000-12-31" } },
      aggregation: { en: "Fixture aggregation" },
      access: {
        url: "https://example.org/fixture-source",
        doi: "10.0000/fixture",
        accessed_at: "2000-01-01T00:00:00-03:00",
        terms_url: "https://example.org/fixture-terms",
        license: "Fixture license",
      },
      limitations: [{ en: "Fixture limitation" }],
    },
    [COMPUTED_ID]: {
      id: COMPUTED_ID,
      data_type: "computed",
      title: { en: "TEST FIXTURE computed record" },
      variable: { code: "fixture_sum", name: { en: "Fixture sum" }, unit: "mm" },
      spatial: { resolution: "fixture km", support: "polygon" },
      temporal: { resolution: "monthly", period: { start: "2000-01-01", end: "2000-12-31" } },
      aggregation: { en: "Fixture monthly sum" },
      method: {
        name: "Fixture method",
        ref: { label: "Fixture reference", url: "javascript:alert(1)" },
        doc_anchor: "fixture-method",
      },
      inputs: [OBSERVED_ID],
      limitations: [],
    },
  },
};

export const fixtureMetric: Pick<Metric, "value" | "unit" | "provenance_id" | "data_type"> = {
  value: 25,
  unit: "degC",
  provenance_id: OBSERVED_ID,
  data_type: "satellite_observed",
};
