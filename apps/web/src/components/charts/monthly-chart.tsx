// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Recent monthly record: precipitation bars over Tmax/Tmin lines, two panels sharing the month axis
// (no dual axis). Values are drawn as published and converted only at display (ADR-7). The figure
// carries data-prov with the ids of the series it draws (VL1); the exact numbers, each with its own
// provenance button, are in <RecentTable> next to it. Lines differ by dash and marker, not color.
"use client";

import { useEffect, useRef, useState } from "react";
import type { CanonicalUnit } from "@fieldshift/contracts";
import { t } from "@/i18n";
import { convert, unitLabel } from "@/lib/units";
import type { RecentBlock } from "@/lib/site-view";
import { monthShort, monthYear } from "@/lib/months";
import { useUiStore } from "@/stores/ui-store";

const PAD = { top: 12, right: 12, bottom: 28, left: 52 };
const PANEL_HEIGHT = 170;

/** 2–5 round ticks covering [min, max]. Interface scale marks, not data. */
export function niceTicks(min: number, max: number, target = 4): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [];
  if (min === max) return [min];
  const rawStep = (max - min) / target;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= rawStep) ?? rawStep;
  const ticks: number[] = [];
  for (let v = Math.floor(min / step) * step; v <= max + step * 1e-9; v += step) ticks.push(Number(v.toFixed(10)));
  if (ticks[ticks.length - 1] < max) ticks.push(ticks[ticks.length - 1] + step);
  return ticks;
}

function useWidth(initial: number) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(initial);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      const w = Math.round(entry.contentRect.width);
      if (w > 0) setWidth(w);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return { ref, width };
}

const fmt = (v: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(v);

interface PanelProps {
  width: number;
  months: string[];
  titleId: string;
  title: string;
  desc: string;
  unit: string;
  ticks: number[];
  children: (x: (i: number) => number, y: (v: number) => number, band: number) => React.ReactNode;
}

function Panel({ width, months, titleId, title, desc, unit, ticks, children }: PanelProps) {
  const innerW = Math.max(width - PAD.left - PAD.right, 10);
  const innerH = PANEL_HEIGHT - PAD.top - PAD.bottom;
  const band = innerW / Math.max(months.length, 1);
  const lo = ticks[0] ?? 0;
  const hi = ticks[ticks.length - 1] ?? 1;
  const x = (i: number) => PAD.left + band * (i + 0.5);
  const y = (v: number) => PAD.top + innerH - ((v - lo) / (hi - lo || 1)) * innerH;
  const every = width < 480 ? 6 : 3;

  return (
    <svg
      role="img"
      aria-labelledby={`${titleId} ${titleId}-desc`}
      width={width}
      height={PANEL_HEIGHT}
      viewBox={`0 0 ${width} ${PANEL_HEIGHT}`}
      className="block max-w-full overflow-visible"
    >
      <title id={titleId}>{title}</title>
      <desc id={`${titleId}-desc`}>{desc}</desc>
      <g aria-hidden="true" fontSize={11} fill="var(--muted-foreground)">
        {ticks.map((v) => (
          <g key={v}>
            <line x1={PAD.left} x2={width - PAD.right} y1={y(v)} y2={y(v)} stroke="var(--border)" />
            <text x={PAD.left - 6} y={y(v)} dy="0.32em" textAnchor="end">
              {fmt(v)}
            </text>
          </g>
        ))}
        <text x={4} y={PAD.top - 2} dy="0.32em">
          {unit}
        </text>
        {months.map((m, i) =>
          i % every === 0 || i === months.length - 1 ? (
            <text key={m} x={x(i)} y={PANEL_HEIGHT - PAD.bottom + 14} textAnchor="middle">
              {monthShort(m)}
              {i === 0 || m.endsWith("-01") ? ` ${m.slice(0, 4)}` : ""}
            </text>
          ) : null,
        )}
      </g>
      <g aria-hidden="true">{children(x, y, band)}</g>
    </svg>
  );
}

function linePath(points: { x: number; y: number | null }[]): string {
  let d = "";
  let pen = false;
  for (const p of points) {
    if (p.y === null) {
      pen = false;
      continue;
    }
    d += `${pen ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`;
    pen = true;
  }
  return d;
}

export function MonthlyChart({ block }: { block: RecentBlock }) {
  const unitSystem = useUiStore((s) => s.unitSystem);
  const { ref, width } = useWidth(640);
  const months = block.rows.map((r) => r.t);
  const first = months[0] ?? "";
  const last = months[months.length - 1] ?? "";
  const range = first && last ? { first: monthYear(first), last: monthYear(last) } : { first: "", last: "" };

  const display = (i: number) => {
    const unit = block.series[i].unit as CanonicalUnit;
    const values = block.rows.map((r) => {
      const v = r.values[i];
      return v === null ? null : convert(v, unit, unitSystem).value;
    });
    return { values, unit: unitLabel(convert(0, unit, unitSystem).unit) };
  };
  const precip = display(0);
  const tmax = display(1);
  const tmin = display(2);

  const precipValues = precip.values.filter((v): v is number => v !== null);
  const precipTicks = niceTicks(0, Math.max(...precipValues, 0));
  const temps = [...tmax.values, ...tmin.values].filter((v): v is number => v !== null);
  const tempTicks = niceTicks(Math.min(...temps), Math.max(...temps));

  return (
    <figure
      data-prov={block.series.map((s) => s.provenanceId).join(" ")}
      className="flex flex-col gap-3"
    >
      <div ref={ref} className="w-full min-w-0">
        <Panel
          width={width}
          months={months}
          titleId="chart-precip"
          title={t("site.recent.precipChart", range)}
          desc={t("site.recent.chartDesc")}
          unit={precip.unit}
          ticks={precipTicks}
        >
          {(x, y, band) =>
            precip.values.map((v, i) =>
              v === null ? null : (
                <rect
                  key={months[i]}
                  x={x(i) - band * 0.35}
                  width={band * 0.7}
                  y={y(v)}
                  height={Math.max(y(precipTicks[0] ?? 0) - y(v), 0)}
                  fill="var(--chart-2)"
                />
              ),
            )
          }
        </Panel>
        <Panel
          width={width}
          months={months}
          titleId="chart-temp"
          title={t("site.recent.tempChart", range)}
          desc={t("site.recent.chartDesc")}
          unit={tmax.unit}
          ticks={tempTicks}
        >
          {(x, y) => (
            <>
              <path
                d={linePath(tmax.values.map((v, i) => ({ x: x(i), y: v === null ? null : y(v) })))}
                fill="none"
                stroke="var(--foreground)"
                strokeWidth={2}
              />
              <path
                d={linePath(tmin.values.map((v, i) => ({ x: x(i), y: v === null ? null : y(v) })))}
                fill="none"
                stroke="var(--foreground)"
                strokeWidth={2}
                strokeDasharray="6 4"
              />
              {tmax.values.map((v, i) =>
                v === null ? null : <circle key={`max-${months[i]}`} cx={x(i)} cy={y(v)} r={3} fill="var(--foreground)" />,
              )}
              {tmin.values.map((v, i) =>
                v === null ? null : (
                  <rect
                    key={`min-${months[i]}`}
                    x={x(i) - 3}
                    y={y(v) - 3}
                    width={6}
                    height={6}
                    fill="var(--background)"
                    stroke="var(--foreground)"
                    strokeWidth={1.5}
                  />
                ),
              )}
            </>
          )}
        </Panel>
      </div>
      <figcaption>
        <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted-foreground">
          <li className="inline-flex items-center gap-2">
            <svg aria-hidden="true" width="14" height="10">
              <rect width="14" height="10" fill="var(--chart-2)" />
            </svg>
            {t("site.recent.legend.precip")}
          </li>
          <li className="inline-flex items-center gap-2">
            <svg aria-hidden="true" width="24" height="10">
              <line x1="0" x2="24" y1="5" y2="5" stroke="var(--foreground)" strokeWidth="2" />
              <circle cx="12" cy="5" r="3" fill="var(--foreground)" />
            </svg>
            {t("site.recent.legend.tmax")}
          </li>
          <li className="inline-flex items-center gap-2">
            <svg aria-hidden="true" width="24" height="10">
              <line x1="0" x2="24" y1="5" y2="5" stroke="var(--foreground)" strokeWidth="2" strokeDasharray="6 4" />
              <rect x="9" y="2" width="6" height="6" fill="var(--background)" stroke="var(--foreground)" strokeWidth="1.5" />
            </svg>
            {t("site.recent.legend.tmin")}
          </li>
        </ul>
      </figcaption>
    </figure>
  );
}
