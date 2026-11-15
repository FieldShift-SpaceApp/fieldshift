// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// T6 Data & Methods (Story 1.4, FR17, FR18). Static: everything is read at build time from the
// files scripts/sync-data.mjs copies (RESOURCES.md, SI-USAGE.md, content/**). No fetch, no client JS.
//
// VL1 (ADR-8): this page shows no data values. Its digits are documentation (dataset versions,
// resolutions, periods, dates, citations), so each documentation block is marked
// data-prov-exempt="ui" and listed by the VL1 e2e test for review. Any data value added later
// must use <Value>/<MetricValue> with a provenance id.
import type { ReactNode } from "react";
import type { Metadata } from "next";
import type { DataType } from "@fieldshift/contracts";
import { DocLink, Markdown } from "@/components/content/markdown";
import { SiteNav } from "@/components/content/site-nav";
import { DataTypeLabel } from "@/components/provenance/data-type-label";
import { t, type MessageKey } from "@/i18n";
import { loadDataMethods, resolveDocHref, type GlossaryEntry } from "@/lib/content";

export const metadata: Metadata = {
  title: t("dataMethods.meta.title"),
  description: t("dataMethods.meta.description"),
};

/** Glossary ids that explain each FR9 data type (content/glossary.yaml). */
const DATA_TYPE_TERMS: { type: DataType; termId: string }[] = [
  { type: "satellite_observed", termId: "satellite-observed" },
  { type: "modeled", termId: "modeled" },
  { type: "computed", termId: "computed" },
  { type: "user_provided", termId: "user-provided" },
];

const SECTIONS: { id: string; label: MessageKey }[] = [
  { id: "data", label: "dataMethods.section.data" },
  { id: "satellite-vs-ground", label: "dataMethods.section.satelliteGround" },
  { id: "methods", label: "dataMethods.section.methods" },
  { id: "limitations", label: "dataMethods.section.limitations" },
  { id: "validation", label: "dataMethods.section.validation" },
  { id: "scale", label: "dataMethods.section.scale" },
  { id: "related-work", label: "dataMethods.section.relatedWork" },
  { id: "use-of-ai", label: "dataMethods.section.useOfAi" },
  { id: "glossary", label: "dataMethods.section.glossary" },
];

/** Public analyses that check the NASA data against the ground (repository folders, rerun from public sources). */
const REPO_TREE = "https://github.com/FieldShift-SpaceApp/fieldshift/tree/main";
const VALIDATION: { href: string; label: MessageKey }[] = [
  { href: `${REPO_TREE}/analysis/enso-wheat`, label: "dataMethods.section.validation.ensoWheat" },
  { href: `${REPO_TREE}/analysis/ground-truth-proagro`, label: "dataMethods.section.validation.groundTruth" },
  { href: `${REPO_TREE}/analysis/drought-resilience`, label: "dataMethods.section.validation.drought" },
  { href: `${REPO_TREE}/analysis/farm-reports#second-municipality-júlio-de-castilhos-scale-test`, label: "dataMethods.section.validation.secondMunicipality" },
  { href: `${REPO_TREE}/analysis/seven-cities`, label: "dataMethods.section.validation.sevenCities" },
];

function term(glossary: GlossaryEntry[], id: string): GlossaryEntry {
  const entry = glossary.find((g) => g.id === id);
  // Build-time guard: the page cannot ship without these definitions.
  if (!entry) throw new Error(`data-methods: glossary term "${id}" is missing from content/glossary.yaml`);
  return entry;
}

function Section({ id, label, children }: { id: string; label: MessageKey; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-heading`} className="scroll-mt-6 border-t border-foreground/10 pt-8">
      <h2 id={`${id}-heading`} className="text-2xl font-semibold tracking-tight">
        {t(label)}
      </h2>
      {children}
    </section>
  );
}

export default function DataMethodsPage() {
  const content = loadDataMethods();
  const satelliteGround = term(content.glossary, "satellite-vs-ground");

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-10 px-4 py-10">
      <header className="flex flex-col gap-4">
        <SiteNav />
        <h1 className="text-3xl font-semibold tracking-tight">{t("dataMethods.heading")}</h1>
        <p className="text-lg text-foreground/80">{t("dataMethods.intro")}</p>
        <nav aria-labelledby="toc-heading">
          <h2 id="toc-heading" className="text-sm font-semibold uppercase tracking-wide text-foreground/70">
            {t("dataMethods.toc")}
          </h2>
          <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm">
            {SECTIONS.map((s) => (
              <li key={s.id}>
                <a href={`#${s.id}`} className="underline underline-offset-4 hover:no-underline">
                  {t(s.label)}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      <Section id="data" label="dataMethods.section.data">
        <p className="mt-3 text-foreground/80">{t("dataMethods.section.data.intro")}</p>
        <div data-prov-exempt="ui">
          <Markdown source={content.resources.source} headingOffset={1}>
            {content.resources.body}
          </Markdown>
        </div>
      </Section>

      <Section id="satellite-vs-ground" label="dataMethods.section.satelliteGround">
        <div data-prov-exempt="ui">
          <p className="mt-3 leading-7">{satelliteGround.definition}</p>
          <p className="mt-4">{t("dataMethods.section.satelliteGround.legend")}</p>
          <dl className="mt-2 grid gap-3">
            {DATA_TYPE_TERMS.map(({ type, termId }) => (
              <div key={type} className="grid gap-1 sm:grid-cols-[11rem_1fr] sm:gap-4">
                <dt className="font-medium">
                  <DataTypeLabel dataType={type} />
                </dt>
                <dd>{term(content.glossary, termId).definition}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Section>

      <Section id="methods" label="dataMethods.section.methods">
        {content.methods.map((m) => (
          <article
            key={m.anchor}
            id={m.anchor}
            data-prov-exempt="ui"
            aria-labelledby={`${m.anchor}-heading`}
            className="mt-8 scroll-mt-6"
          >
            <h3 id={`${m.anchor}-heading`} className="text-xl font-semibold">
              {m.title}
            </h3>
            <div>
              <Markdown source={m.source} headingOffset={2}>
                {m.body}
              </Markdown>
              <h4 className="mt-4 font-semibold">{t("content.refs")}</h4>
              <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
                {m.refs.map((r) => (
                  <li key={r.label}>
                    <DocLink href={resolveDocHref(r.url, m.source)}>{r.label}</DocLink>
                  </li>
                ))}
              </ul>
            </div>
          </article>
        ))}
      </Section>

      <Section id="limitations" label="dataMethods.section.limitations">
        <ul data-prov-exempt="ui" className="mt-3 list-disc space-y-2 pl-6">
          {content.methods.flatMap((m) =>
            m.limitations.map((l) => (
              <li key={`${m.anchor}:${l}`}>
                {l}{" "}
                <span className="text-sm text-foreground/70">
                  ({t("dataMethods.methodFrom")} <a href={`#${m.anchor}`} className="underline underline-offset-4">{m.title}</a>)
                </span>
              </li>
            )),
          )}
        </ul>
      </Section>

      <Section id="validation" label="dataMethods.section.validation">
        <div data-prov-exempt="ui">
          <p className="mt-3">{t("dataMethods.section.validation.intro")}</p>
          <ul className="mt-3 list-disc space-y-2 pl-6">
            {VALIDATION.map((v) => (
              <li key={v.href}>
                <DocLink href={v.href}>{t(v.label)}</DocLink>
              </li>
            ))}
          </ul>
        </div>
      </Section>

      <Section id="scale" label="dataMethods.section.scale">
        <div data-prov-exempt="ui">
          <p className="mt-3">{t("dataMethods.section.scale.body")}</p>
          <p className="mt-2">
            <DocLink href={`${REPO_TREE}/analysis/scale`}>{t("dataMethods.section.scale.link")}</DocLink>
          </p>
        </div>
      </Section>

      <Section id="related-work" label="dataMethods.section.relatedWork">
        <div data-prov-exempt="ui">
          <Markdown source={content.relatedWork.source} headingOffset={1}>
            {content.relatedWork.body}
          </Markdown>
        </div>
      </Section>

      <Section id="use-of-ai" label="dataMethods.section.useOfAi">
        <p className="mt-3 text-foreground/80">{t("dataMethods.section.useOfAi.intro")}</p>
        <div data-prov-exempt="ui">
          <Markdown source={content.siUsage.source} headingOffset={1}>
            {content.siUsage.body}
          </Markdown>
        </div>
      </Section>

      <Section id="glossary" label="dataMethods.section.glossary">
        <p className="mt-3">
          {t("dataMethods.section.glossary.body")} <DocLink href="/glossary">{t("nav.glossary")}</DocLink>
        </p>
      </Section>
    </main>
  );
}
