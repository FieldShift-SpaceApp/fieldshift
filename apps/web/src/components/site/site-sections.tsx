// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Sections of the site page (T2). Every data number goes through <Value>/<MetricValue> (VL1);
// text that repeats a record's own facts (labels with thresholds, periods, dataset versions) sits
// inside an element whose data-prov names that record, so its digits are traceable too.
import Link from "next/link";
import type { ReactNode } from "react";
import { DataTypeLabel } from "@/components/provenance/data-type-label";
import { MetricValue } from "@/components/provenance/metric-value";
import { Value } from "@/components/provenance/value";
import { UnitToggle } from "@/components/site/unit-toggle";
import { MonthlyChart } from "@/components/charts/monthly-chart";
import { t } from "@/i18n";
import { calendarMonthLong, monthYear } from "@/lib/months";
import { yearOf, type SiteView } from "@/lib/site-view";

export function Section({ id, title, prov, children }: { id: string; title: ReactNode; prov?: string; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-heading`} className="scroll-mt-6 border-t border-foreground/10 pt-8">
      <h2 id={`${id}-heading`} data-prov={prov} className="text-2xl font-semibold tracking-tight">
        {title}
      </h2>
      {children}
    </section>
  );
}

/** Means of day counts keep one decimal (5.3 days, not 5); other units use the default display rounding. */
function meanDigits(unit: string): number | undefined {
  return unit === "days" || unit === "count" ? 1 : undefined;
}

const linkClass =
  "underline underline-offset-4 hover:no-underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";

export function SiteHeader({ name, view }: { name: string; view: SiteView }) {
  const { point, source } = view;
  return (
    <header className="flex flex-col gap-4">
      <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">{t("site.eyebrow")}</p>
      <h1 className="text-3xl font-semibold tracking-tight">{name}</h1>
      <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-[12rem_1fr]">
        {point ? (
          <>
            <dt className="text-muted-foreground">{t("site.header.point")}</dt>
            <dd>
              <span className="inline-flex flex-wrap gap-x-4 gap-y-1">
                <span>
                  {t("site.header.lat")}{" "}
                  <Value value={point.lat} unit="deg" provenanceId={point.provenanceId} digits={3} />
                </span>
                <span>
                  {t("site.header.lon")}{" "}
                  <Value value={point.lon} unit="deg" provenanceId={point.provenanceId} digits={3} />
                </span>
              </span>
              <span className="mt-1 block text-muted-foreground">{t("site.header.pointNote")}</span>
            </dd>
          </>
        ) : null}
        {source ? (
          <>
            <dt className="text-muted-foreground">{t("site.header.source")}</dt>
            <dd data-prov={source.provenanceId}>
              {source.url ? (
                <a href={source.url} target="_blank" rel="noopener noreferrer" className={linkClass}>
                  {source.dataset}
                </a>
              ) : (
                source.dataset
              )}{" "}
              · {source.product} · {source.version} · {source.provider}{" "}
              <DataTypeLabel dataType="modeled" />
              {source.accessedAt ? (
                <span className="block text-muted-foreground">
                  {t("site.header.accessed", { date: source.accessedAt.slice(0, 10) })}
                </span>
              ) : null}
            </dd>
            <dt className="text-muted-foreground">{t("site.header.record")}</dt>
            <dd data-prov={source.provenanceId}>
              {t("site.header.recordRange", { first: monthYear(source.first), last: monthYear(source.last) })}
            </dd>
          </>
        ) : null}
        <dt className="self-center text-muted-foreground">{t("site.header.units")}</dt>
        <dd>
          <UnitToggle />
        </dd>
      </dl>
      <p className="text-sm text-foreground/80">{t("site.header.howTo")}</p>
    </header>
  );
}

export function RecentSection({ view }: { view: SiteView }) {
  const block = view.recent;
  if (!block) return null;
  const first = block.rows[0]?.t;
  const last = block.rows[block.rows.length - 1]?.t;
  const range = first && last ? { first: monthYear(first), last: monthYear(last) } : { first: "", last: "" };
  const provAll = block.series.map((s) => s.provenanceId).join(" ");
  const headers = [t("site.recent.table.precip"), t("site.recent.table.tmax"), t("site.recent.table.tmin")];

  return (
    <Section id="recent" title={t("site.recent.heading")}>
      <p className="mt-3 text-foreground/80">{t("site.recent.intro")}</p>
      <p className="mt-2 text-sm text-muted-foreground">
        {t("site.recent.noClimatology")} <DataTypeLabel dataType={block.series[0].dataType} />
      </p>
      <div className="mt-5">
        <MonthlyChart block={block} />
      </div>
      <details className="mt-4 rounded-md border border-border">
        <summary className="min-h-11 cursor-pointer px-3 py-2.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-ring">
          {t("site.recent.table.show")}
        </summary>
        <div className="overflow-x-auto px-3 pb-3">
          <table className="w-full text-sm">
            <caption data-prov={provAll} className="py-2 text-left text-muted-foreground">
              {t("site.recent.table.caption", range)}
            </caption>
            <thead>
              <tr className="border-b border-border text-left">
                <th scope="col" className="py-1.5 pr-3 font-medium">
                  {t("site.recent.table.month")}
                </th>
                {headers.map((h) => (
                  <th key={h} scope="col" className="py-1.5 pr-3 text-right font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.rows.map((row) => (
                <tr key={row.t} className="border-b border-border/60">
                  <th scope="row" data-prov={provAll} className="py-1 pr-3 text-left font-normal">
                    {monthYear(row.t)}
                  </th>
                  {row.values.map((v, i) => (
                    <td key={block.series[i].id} className="py-1 pr-3 text-right">
                      <Value value={v} unit={block.series[i].unit} provenanceId={block.series[i].provenanceId} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </Section>
  );
}

function PeriodTitle({ view, keyName }: { view: SiteView; keyName: "site.indices.heading" | "site.profiles.heading" }) {
  return view.period
    ? t(keyName, { start: yearOf(view.period.start), end: yearOf(view.period.end) })
    : t(keyName, { start: "", end: "" }).replace(/,\s*–$/, "");
}

export function IndicesSection({ view }: { view: SiteView }) {
  if (view.metrics.length === 0) return null;
  return (
    <Section
      id="indices"
      title={<PeriodTitle view={view} keyName="site.indices.heading" />}
      prov={view.period?.provenanceIds.join(" ")}
    >
      <p className="mt-3 text-foreground/80">
        {t("site.indices.intro")}{" "}
        <Link href="/data-methods#climate-indices" className={linkClass}>
          {t("site.indices.method")}
        </Link>
      </p>
      <ul className="mt-5 grid gap-3 sm:grid-cols-2">
        {view.metrics.map((m) => (
          <li key={m.id} className="flex flex-col gap-2 rounded-lg border border-border p-4">
            <span data-prov={m.provenance_id} className="text-sm text-foreground/80">
              {m.label.en}
            </span>
            <span className="text-2xl font-semibold">
              <MetricValue metric={m} digits={meanDigits(m.unit)} />
            </span>
          </li>
        ))}
      </ul>
    </Section>
  );
}

export function ProfilesSection({ view }: { view: SiteView }) {
  if (view.profiles.length === 0) return null;
  const prov = view.profiles.map((p) => p.provenance_id).join(" ");
  const start = view.profiles[0].period.start;
  const end = view.profiles[0].period.end;
  return (
    <Section id="by-month" title={t("site.profiles.heading", { start: yearOf(start), end: yearOf(end) })} prov={prov}>
      <p className="mt-3 text-foreground/80">{t("site.profiles.intro")}</p>
      <div
        role="region"
        aria-label={t("site.profiles.scroll")}
        tabIndex={0}
        className="mt-5 overflow-x-auto rounded-md border border-border focus-visible:outline-2 focus-visible:outline-ring"
      >
        <table className="min-w-[44rem] text-sm">
          <caption data-prov={prov} className="px-3 py-2 text-left text-muted-foreground">
            {t("site.profiles.caption", { start: yearOf(start), end: yearOf(end) })}
          </caption>
          <thead>
            <tr className="border-b border-border text-left align-bottom">
              <th scope="col" className="px-3 py-1.5 font-medium">
                {t("site.profiles.month")}
              </th>
              {view.profiles.map((p) => (
                <th key={p.id} scope="col" data-prov={p.provenance_id} className="px-3 py-1.5 text-right font-medium">
                  {p.label.en.replace(/, mean by calendar month.*$/, "")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 12 }, (_, month) => (
              <tr key={month} className="border-b border-border/60">
                <th scope="row" className="px-3 py-1 text-left font-normal">
                  {calendarMonthLong(month)}
                </th>
                {view.profiles.map((p) => (
                  <td key={p.id} className="px-3 py-1 text-right">
                    <Value value={p.values[month]} unit={p.unit} provenanceId={p.provenance_id} digits={meanDigits(p.unit)} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}

export function GroundCheckSection({ view }: { view: SiteView }) {
  return (
    <Section id="limitations" title={t("site.limits.heading")}>
      <p className="mt-3 text-foreground/80">{t("site.limits.intro")}</p>
      <ul className="mt-4 flex flex-col gap-4">
        {view.groundCheck.map((note) => (
          <li
            key={note.text}
            data-prov={note.appliesTo.map((a) => a.id).join(" ")}
            className="rounded-lg border border-border p-4 text-sm leading-6"
          >
            <p>{note.text}</p>
            <p className="mt-2 text-muted-foreground">
              {t("site.limits.appliesTo")} {note.appliesTo.map((a) => a.title).join("; ")}
            </p>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-sm">{t("site.limits.general")}</p>
      <p className="mt-2 text-sm">
        <Link href="/data-methods#satellite-vs-ground-check" className={linkClass}>
          {t("site.limits.more")}
        </Link>
      </p>
    </Section>
  );
}
