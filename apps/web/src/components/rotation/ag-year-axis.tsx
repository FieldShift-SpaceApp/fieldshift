// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// ADR-7 / FR22: every time axis starts at the site's start month and names the months.
// No season labels: "summer" in Nevada is "winter" in Brazil. Neutral styling (the main visual is D4).
import type { Month } from "@fieldshift/contracts";
import { t, type MessageKey } from "@/i18n";
import { agYearMonths } from "@/lib/agyear";

export function monthShort(month: Month): string {
  return t(`month.short.${month}` as MessageKey);
}

export function monthLong(month: Month): string {
  return t(`month.long.${month}` as MessageKey);
}

export interface AgYearAxisProps {
  /** `Site.ag_year.start_month` (1–12). */
  startMonth: number;
  className?: string;
}

/** The 12 months of the agricultural year, in order, as a 12-column grid. */
export function AgYearAxis({ startMonth, className }: AgYearAxisProps) {
  const months = agYearMonths(startMonth);
  return (
    <ol
      aria-label={t("agyear.axis.label", { month: monthLong(months[0]) })}
      data-start-month={startMonth}
      className={`grid grid-cols-12 gap-px text-center text-xs text-muted-foreground ${className ?? ""}`}
    >
      {months.map((month) => (
        <li key={month} data-month={month}>
          <abbr title={monthLong(month)} className="no-underline">
            {monthShort(month)}
          </abbr>
        </li>
      ))}
    </ol>
  );
}
