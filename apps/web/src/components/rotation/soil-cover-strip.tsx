// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// FR4 / FR21 / FR22: soil state of the current rotation, one cell per month of the agricultural year.
// The state is never shown by color alone: each cell has an icon, a fill pattern and its state as
// text (accessible name and tooltip), and the legend pairs icon, pattern and text. Neutral styling:
// the main visual is a team decision (D4). The container carries `data-prov` (ADR-8, layer 2).
import type { Rotation, RotationTimeline, SoilCoverMonth, SoilState } from "@fieldshift/contracts";
import { CircleDashed, Hourglass, Layers, Sprout, type LucideIcon } from "lucide-react";
import { t, type MessageKey } from "@/i18n";
import { agYearMonths } from "@/lib/agyear";
import { AgYearAxis, monthLong } from "./ag-year-axis";

export const SOIL_STATES: readonly SoilState[] = ["covered", "residue", "transition", "bare"];

const ICONS: Record<SoilState, LucideIcon> = {
  covered: Sprout,
  residue: Layers,
  transition: Hourglass,
  bare: CircleDashed,
};

export function soilStateLabel(state: SoilState): string {
  return t(`soil.state.${state}` as MessageKey);
}

/** Splits the timeline into cycle years and checks it follows the site's agricultural year. */
export function timelineRows(timeline: RotationTimeline, startMonth: number): SoilCoverMonth[][] {
  const order = agYearMonths(startMonth);
  if (timeline.months.length === 0 || timeline.months.length % 12 !== 0) {
    throw new RangeError(`timeline must have a multiple of 12 months, got ${timeline.months.length}`);
  }
  const rows: SoilCoverMonth[][] = [];
  timeline.months.forEach((m, i) => {
    if (m.position !== i || m.year_index !== Math.floor(i / 12) || m.month !== order[i % 12]) {
      throw new RangeError(
        `timeline month ${i} (${m.year_index}/${m.month}) does not follow an agricultural year starting in month ${startMonth}`,
      );
    }
    (rows[m.year_index] ??= []).push(m);
  });
  return rows;
}

function SoilIcon({ state }: { state: SoilState }) {
  const Icon = ICONS[state];
  return <Icon aria-hidden="true" focusable="false" className="size-3.5 shrink-0" strokeWidth={2} />;
}

export interface SoilCoverStripProps {
  timeline: RotationTimeline;
  /** `Site.ag_year.start_month`: must be the one the timeline was derived with. */
  startMonth: number;
  /** When given, each month also names the rotation segments that cover it. */
  rotation?: Rotation;
}

export function SoilCoverStrip({ timeline, startMonth, rotation }: SoilCoverStripProps) {
  const rows = timelineRows(timeline, startMonth);
  const labels = new Map(rotation?.segments.map((s) => [s.id, s.label.en]) ?? []);
  const multiYear = rows.length > 1;

  const cellText = (m: SoilCoverMonth) => {
    const month = monthLong(m.month);
    const state = soilStateLabel(m.state);
    const segments = m.segment_ids.map((id) => labels.get(id)).filter(Boolean);
    return segments.length && rotation
      ? t("soil.cell.segments", { month, state, segments: segments.join(", ") })
      : t("soil.cell", { month, state });
  };

  return (
    <figure data-prov={timeline.provenance_id} className="soil-strip flex flex-col gap-2">
      <figcaption className="text-sm font-medium">{t("soil.strip.label")}</figcaption>
      <div className={multiYear ? "grid grid-cols-[auto_1fr] items-center gap-x-2 gap-y-1" : "flex flex-col gap-1"}>
        {multiYear ? <span aria-hidden="true" /> : null}
        <AgYearAxis startMonth={startMonth} />
        {rows.map((row, y) => {
          const yearLabel = t("agyear.year", { n: y + 1 });
          return [
            multiYear ? (
              <span key={`label-${y}`} className="text-xs text-muted-foreground" aria-hidden="true">
                {yearLabel}
              </span>
            ) : null,
            <ol
              key={`row-${y}`}
              aria-label={multiYear ? `${t("soil.strip.label")}, ${yearLabel}` : t("soil.strip.label")}
              data-year-index={y}
              className="grid grid-cols-12 gap-px"
            >
              {row.map((m) => {
                const text = cellText(m);
                return (
                  <li
                    key={m.position}
                    data-state={m.state}
                    data-month={m.month}
                    title={text}
                    className="soil-cell flex h-8 items-center justify-center rounded-sm"
                  >
                    <SoilIcon state={m.state} />
                    <span className="sr-only">{text}</span>
                  </li>
                );
              })}
            </ol>,
          ];
        })}
      </div>
      <ul aria-label={t("soil.strip.legend")} className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
        {SOIL_STATES.map((state) => (
          <li key={state} data-legend-state={state} className="flex items-center gap-1.5">
            <span data-state={state} className="soil-cell flex size-5 items-center justify-center rounded-sm">
              <SoilIcon state={state} />
            </span>
            {soilStateLabel(state)}
          </li>
        ))}
      </ul>
    </figure>
  );
}
