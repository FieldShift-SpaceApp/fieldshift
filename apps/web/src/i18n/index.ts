// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
import { en, type MessageKey } from "./en";

/** Looks up a UI string; `{name}` placeholders are replaced from `params`. */
export function t(key: MessageKey, params?: Record<string, string | number>): string {
  const text: string = en[key];
  if (!params) return text;
  return text.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  );
}

export type { MessageKey };
