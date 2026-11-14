// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
import { SiteNav } from "@/components/content/site-nav";
import { t } from "@/i18n";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center gap-4 px-4 py-16">
      <SiteNav />
      <h1 className="text-3xl font-semibold tracking-tight">{t("canary.heading")}</h1>
      {/* "2026" is the event name, not data: interface number exempt from VL1 (ADR-8). */}
      <p data-prov-exempt="ui" className="text-lg text-foreground/80">
        {t("canary.body")}
      </p>
    </main>
  );
}
