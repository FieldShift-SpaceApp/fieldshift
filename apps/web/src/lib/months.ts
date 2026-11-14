// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Month names for ISO months ("YYYY-MM") and calendar-month indexes, from the strings file (NFR15).
import { t, type MessageKey } from "@/i18n";

function monthNumber(isoMonth: string): number {
  const n = Number(isoMonth.slice(5, 7));
  if (!Number.isInteger(n) || n < 1 || n > 12) throw new Error(`months: not an ISO month: "${isoMonth}"`);
  return n;
}

/** "2026-10" → "Oct". */
export function monthShort(isoMonth: string): string {
  return t(`month.short.${monthNumber(isoMonth)}` as MessageKey);
}

/** "2026-10" → "Oct 2026". */
export function monthYear(isoMonth: string): string {
  return `${monthShort(isoMonth)} ${isoMonth.slice(0, 4)}`;
}

/** Calendar month index 0..11 → "January". */
export function calendarMonthLong(index: number): string {
  return t(`month.long.${index + 1}` as MessageKey);
}
