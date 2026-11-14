// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Visible marker for a section that a later story fills (Story 1.4, AC3 and AC5).
import type { ReactNode } from "react";
import { t } from "@/i18n";

export function PendingNotice({ children }: { children: ReactNode }) {
  return (
    <div data-pending="" className="mt-3 rounded-md border border-dashed border-foreground/30 px-4 py-3 text-sm">
      <strong className="mr-2 font-semibold uppercase tracking-wide">{t("content.pending")}</strong>
      {children}
    </div>
  );
}
