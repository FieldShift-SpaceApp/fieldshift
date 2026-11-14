// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// ADR-8, layer 2: the only way a data number reaches the screen. `provenanceId` is required by the
// type, the element carries `data-prov`, and one click opens the provenance panel (FR19).
"use client";

import type { CanonicalUnit, ProvenanceId } from "@fieldshift/contracts";
import { t } from "@/i18n";
import { formatQuantity } from "@/lib/units";
import { useUiStore } from "@/stores/ui-store";

export interface ValueProps {
  value: number | null;
  unit: CanonicalUnit;
  /** Required: a number without provenance never reaches the screen (FR19, VL1). */
  provenanceId: ProvenanceId;
  digits?: number;
}

export function Value({ value, unit, provenanceId, digits }: ValueProps) {
  const unitSystem = useUiStore((s) => s.unitSystem);
  const openProvenance = useUiStore((s) => s.openProvenance);

  if (value === null || !Number.isFinite(value)) {
    return <span data-prov={provenanceId}>{t("value.unavailable")}</span>;
  }

  const q = formatQuantity(value, unit, unitSystem, digits); // conversion only at display (ADR-7)
  return (
    <button
      type="button"
      data-prov={provenanceId}
      onClick={() => openProvenance([provenanceId])}
      aria-label={t("provenance.open", { value: q.text, unit: q.unitLabel })}
      aria-haspopup="dialog"
      className="cursor-pointer tabular-nums underline decoration-dotted underline-offset-4 hover:decoration-solid focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
    >
      {q.text}
      {q.unitLabel ? <span className="ml-0.5 text-muted-foreground">{q.unitLabel}</span> : null}
    </button>
  );
}
