// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Site page view model (T2). Pure functions over the published contracts: they select and align
// values, they never compute new numbers. Every value keeps the provenance id of the record it
// came from (FR19, VL1), and only the records the page shows go to the client (payload rule).
import type {
  CanonicalUnit,
  DataType,
  Metric,
  MonthlyProfile,
  Provenance,
  ProvenanceId,
  ProvenanceRegistry,
  TimeSeries,
} from "@fieldshift/contracts";
import type { SiteBundle } from "./data/loaders";

/** Monthly series shown in the "recent months" chart, in display order. */
export const RECENT_KEYS = ["precip", "air_temp_max", "air_temp_min"] as const;
export type RecentKey = (typeof RECENT_KEYS)[number];

/** How many recent months the chart shows (an interface choice, not data). */
export const RECENT_MONTHS = 24;

/** Prefix of the ground-check limitations (services/science/src/fieldshift/provenance/ground_check.py). */
export const GROUND_CHECK_PREFIX = "Ground check";

export interface SeriesRef {
  id: string;
  label: string;
  unit: CanonicalUnit;
  provenanceId: ProvenanceId;
  dataType: DataType;
}

export interface RecentRow {
  /** ISO month, "YYYY-MM". */
  t: string;
  /** One value per RECENT_KEYS entry, as published (null = gap). */
  values: (number | null)[];
}

export interface RecentBlock {
  series: SeriesRef[];
  rows: RecentRow[];
}

export interface PointValue {
  lat: number;
  lon: number;
  provenanceId: ProvenanceId;
}

export interface SourceSummary {
  provenanceId: ProvenanceId;
  dataset: string;
  provider: string;
  product: string;
  version: string;
  accessedAt: string | null;
  url: string | null;
  first: string;
  last: string;
}

export interface GroundCheckNote {
  text: string;
  /** Records (and their titles) whose limitations include this note. */
  appliesTo: { id: ProvenanceId; title: string }[];
}

export interface SiteView {
  siteId: string;
  point: PointValue | null;
  source: SourceSummary | null;
  recent: RecentBlock | null;
  metrics: Metric[];
  profiles: MonthlyProfile[];
  /** Ids of the metrics (for the period in the section heading). */
  period: { start: string; end: string; provenanceIds: ProvenanceId[] } | null;
  groundCheck: GroundCheckNote[];
  /** Every provenance id that reaches the screen. */
  provenanceIds: ProvenanceId[];
  /** Subset of the registry for the client panel. */
  records: Record<ProvenanceId, Provenance>;
}

export function findMonthlySeries(series: TimeSeries[], key: string): TimeSeries | undefined {
  return series.find((s) => s.variable_key === key && s.frequency === "monthly");
}

/**
 * The point NASA POWER was queried for, read back from the request URL in the provenance record
 * (`latitude=` / `longitude=`). Null when the record has no such URL.
 */
export function requestedPoint(record: Provenance | undefined): PointValue | null {
  const url = record?.access?.url;
  if (!url) return null;
  try {
    const params = new URL(url).searchParams;
    const lat = Number(params.get("latitude"));
    const lon = Number(params.get("longitude"));
    if (!params.has("latitude") || !params.has("longitude") || !Number.isFinite(lat) || !Number.isFinite(lon)) {
      return null;
    }
    return { lat, lon, provenanceId: record.id };
  } catch {
    return null;
  }
}

/**
 * The last `count` months of the given monthly series, aligned by month. A month enters only when
 * at least one series has a value for it; values are copied as published (null stays null).
 */
export function recentRows(series: TimeSeries[], count: number = RECENT_MONTHS): RecentRow[] {
  const byMonth = new Map<string, (number | null)[]>();
  series.forEach((s, i) => {
    for (const p of s.points) {
      const row = byMonth.get(p.t) ?? series.map(() => null);
      row[i] = p.v;
      byMonth.set(p.t, row);
    }
  });
  return [...byMonth.entries()]
    .filter(([, values]) => values.some((v) => v !== null))
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .slice(-count)
    .map(([t, values]) => ({ t, values }));
}

/** Ground-check limitations on the given records, deduplicated by text. */
export function groundCheckNotes(registry: ProvenanceRegistry, ids: ProvenanceId[]): GroundCheckNote[] {
  const notes = new Map<string, GroundCheckNote>();
  for (const id of ids) {
    const record = registry.records[id];
    if (!record) continue;
    for (const limitation of record.limitations) {
      if (!limitation.en.startsWith(GROUND_CHECK_PREFIX)) continue;
      const note = notes.get(limitation.en) ?? { text: limitation.en, appliesTo: [] };
      if (!note.appliesTo.some((a) => a.id === id)) note.appliesTo.push({ id, title: record.title.en });
      notes.set(limitation.en, note);
    }
  }
  return [...notes.values()];
}

function seriesRef(s: TimeSeries): SeriesRef {
  return { id: s.id, label: s.label.en, unit: s.unit, provenanceId: s.provenance_id, dataType: s.data_type };
}

export function buildSiteView(bundle: SiteBundle): SiteView {
  const { series, indices, provenance } = bundle;

  const recentSeries = RECENT_KEYS.map((key) => findMonthlySeries(series.series, key));
  const complete = recentSeries.every((s): s is TimeSeries => s !== undefined);
  const recent: RecentBlock | null = complete
    ? { series: recentSeries.map(seriesRef), rows: recentRows(recentSeries) }
    : null;

  // Header: point and source come from the precipitation record (all POWER records share them).
  const precip = recentSeries[0];
  const precipRecord = precip ? provenance.records[precip.provenance_id] : undefined;
  const point = requestedPoint(precipRecord);
  const source: SourceSummary | null =
    precip && precipRecord?.source
      ? {
          provenanceId: precipRecord.id,
          dataset: precipRecord.source.dataset,
          provider: precipRecord.source.provider,
          product: precipRecord.source.product,
          version: precipRecord.source.version,
          accessedAt: precipRecord.access?.accessed_at ?? null,
          url: precipRecord.refs?.[0]?.url ?? null,
          first: precip.coverage.first,
          last: precip.coverage.last,
        }
      : null;

  const metrics = indices.metrics;
  const profiles = indices.profiles;
  const first = metrics[0];
  const samePeriod = metrics.every(
    (m) => m.period.start === first?.period.start && m.period.end === first?.period.end,
  );
  const period =
    first && samePeriod
      ? { start: first.period.start, end: first.period.end, provenanceIds: metrics.map((m) => m.provenance_id) }
      : null;

  const ids = new Set<ProvenanceId>();
  recent?.series.forEach((s) => ids.add(s.provenanceId));
  metrics.forEach((m) => ids.add(m.provenance_id));
  profiles.forEach((p) => ids.add(p.provenance_id));
  const provenanceIds = [...ids];

  const missing = provenanceIds.filter((id) => !provenance.records[id]);
  if (missing.length > 0) {
    // VL1: a number whose record is missing never ships (the data layer should have caught it).
    throw new Error(`[site] ${bundle.siteId}: provenance records missing: ${missing.join(", ")}`);
  }

  const records: Record<ProvenanceId, Provenance> = {};
  for (const id of provenanceIds) records[id] = provenance.records[id];

  return {
    siteId: bundle.siteId,
    point,
    source,
    recent,
    metrics,
    profiles,
    period,
    groundCheck: groundCheckNotes(provenance, provenanceIds),
    provenanceIds,
    records,
  };
}

/** "1991-01-01" → "1991" (a date from the data, shown as a year). */
export function yearOf(isoDate: string): string {
  return isoDate.slice(0, 4);
}
