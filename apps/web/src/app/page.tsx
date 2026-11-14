// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
import Link from "next/link";
import { SiteNav } from "@/components/content/site-nav";
import { t } from "@/i18n";
import { listSiteIds } from "@/lib/data/loaders";
import { siteName } from "@/lib/site-name";

export default function Home() {
  const sites = listSiteIds();
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center gap-4 px-4 py-16">
      <SiteNav />
      <h1 className="text-3xl font-semibold tracking-tight">{t("canary.heading")}</h1>
      {/* "2026" is the event name, not data: interface number exempt from VL1 (ADR-8). */}
      <p data-prov-exempt="ui" className="text-lg text-foreground/80">
        {t("canary.body")}
      </p>
      {sites.length > 0 ? (
        <section aria-labelledby="sites-heading" className="mt-6 flex flex-col gap-3">
          <h2 id="sites-heading" className="text-xl font-semibold tracking-tight">
            {t("home.sites.heading")}
          </h2>
          <p className="text-foreground/80">{t("home.sites.intro")}</p>
          <ul className="flex flex-col gap-2">
            {sites.map((id) => (
              <li key={id}>
                <Link
                  href={`/sites/${id}`}
                  className="inline-flex min-h-11 items-center rounded-md border border-border px-4 font-medium underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                >
                  {siteName(id)}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  );
}
