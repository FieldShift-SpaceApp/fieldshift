// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// FR23: switch between metric and imperial; every <Value> on the page re-renders converted.
"use client";

import type { UnitSystem } from "@fieldshift/contracts";
import { t } from "@/i18n";
import { useUiStore } from "@/stores/ui-store";

const SYSTEMS = [
  { id: "metric", label: "units.system.metric" },
  { id: "imperial", label: "units.system.imperial" },
] as const satisfies readonly { id: UnitSystem; label: string }[];

export function UnitToggle() {
  const unitSystem = useUiStore((s) => s.unitSystem);
  const setUnitSystem = useUiStore((s) => s.setUnitSystem);

  return (
    <div role="group" aria-label={t("units.selector.label")} className="inline-flex rounded-md border border-border p-0.5 text-sm">
      {SYSTEMS.map((system) => {
        const active = unitSystem === system.id;
        return (
          <button
            key={system.id}
            type="button"
            aria-pressed={active}
            onClick={() => setUnitSystem(system.id)}
            className={`min-h-11 rounded px-3 focus-visible:outline-2 focus-visible:outline-ring ${
              active ? "bg-primary text-primary-foreground" : "text-foreground hover:bg-muted"
            }`}
          >
            {t(system.label)}
          </button>
        );
      })}
    </div>
  );
}
