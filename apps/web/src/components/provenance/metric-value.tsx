// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// A contract `Metric` on screen: the value through <Value> (data-prov, panel) plus its data type (FR9).
"use client";

import type { Metric } from "@fieldshift/contracts";
import { DataTypeLabel } from "./data-type-label";
import { Value } from "./value";

export interface MetricValueProps {
  metric: Pick<Metric, "value" | "unit" | "provenance_id" | "data_type">;
  digits?: number;
}

export function MetricValue({ metric, digits }: MetricValueProps) {
  return (
    <span className="inline-flex items-baseline gap-2">
      <Value value={metric.value} unit={metric.unit} provenanceId={metric.provenance_id} digits={digits} />
      <DataTypeLabel dataType={metric.data_type} />
    </span>
  );
}
