// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// T7 Glossary (FR8). Static: read at build time from content/glossary.yaml (copied by sync-data).
// Each term is an anchor (/glossary#<id>) so in-page term tooltips can link here later.
import type { Metadata } from "next";
import { DocLink } from "@/components/content/markdown";
import { SiteNav } from "@/components/content/site-nav";
import { t } from "@/i18n";
import { GENERATED_DIR, loadGlossary, resolveDocHref } from "@/lib/content";

export const metadata: Metadata = {
  title: t("glossary.meta.title"),
  description: t("glossary.meta.description"),
};

export default function GlossaryPage() {
  const terms = loadGlossary(GENERATED_DIR);

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-10">
      <header className="flex flex-col gap-4">
        <SiteNav />
        <h1 className="text-3xl font-semibold tracking-tight">{t("glossary.heading")}</h1>
        <p className="text-lg text-foreground/80">{t("glossary.intro")}</p>
      </header>

      {/* Definitions are documentation, not data values ("2 m", "0 °C" in a definition): VL1 exemption (ADR-8). */}
      <dl data-prov-exempt="ui" className="flex flex-col gap-6">
        {terms.map((entry) => (
          <div key={entry.id} id={entry.id} className="scroll-mt-6 border-t border-foreground/10 pt-4">
            <dt className="text-lg font-semibold">{entry.term}</dt>
            <dd className="mt-2 leading-7">
              <p>{entry.definition}</p>
              {entry.refs.length > 0 ? (
                <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
                  {entry.refs.map((r) => (
                    <li key={r.url}>
                      <DocLink href={resolveDocHref(r.url, "content/glossary.yaml")}>{r.label}</DocLink>
                    </li>
                  ))}
                </ul>
              ) : null}
              <p className="mt-2 text-xs text-foreground/60">
                {entry.reviewedBy === "pending"
                  ? t("glossary.reviewPending")
                  : t("glossary.reviewedBy", { name: entry.reviewedBy })}
              </p>
            </dd>
          </div>
        ))}
      </dl>
    </main>
  );
}
