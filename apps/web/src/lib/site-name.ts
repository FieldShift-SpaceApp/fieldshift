// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Display name of a site from the strings file (NFR15). Falls back to the id, so a new site still
// gets a page before its name is added. Replaced by site.json `name` once the pipeline writes it.
import { en } from "@/i18n/en";
import { t, type MessageKey } from "@/i18n";

export function siteName(siteId: string): string {
  const key = `site.name.${siteId}`;
  return key in en ? t(key as MessageKey) : siteId;
}
