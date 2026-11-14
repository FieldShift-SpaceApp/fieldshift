// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
import Link from "next/link";
import { t } from "@/i18n";

export function SiteNav() {
  return (
    <nav aria-label={t("nav.label")} className="flex flex-wrap gap-x-5 gap-y-2 text-sm">
      <Link href="/" className="underline-offset-4 hover:underline">
        {t("nav.home")}
      </Link>
      <Link href="/data-methods" className="underline-offset-4 hover:underline">
        {t("nav.dataMethods")}
      </Link>
      <Link href="/glossary" className="underline-offset-4 hover:underline">
        {t("nav.glossary")}
      </Link>
    </nav>
  );
}
