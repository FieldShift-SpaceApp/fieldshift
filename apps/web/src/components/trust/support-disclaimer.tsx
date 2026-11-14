import { t } from "@/i18n";

// FR7: permanent notice, rendered on every page by the root layout.
export function SupportDisclaimer() {
  return (
    <aside
      role="note"
      className="border-t border-foreground/10 px-4 py-3 text-center text-sm text-foreground/80"
    >
      {t("disclaimer.support")}
    </aside>
  );
}
