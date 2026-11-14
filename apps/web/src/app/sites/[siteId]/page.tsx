// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// T2 site context (FR2, FR19). Static: generateStaticParams lists the sites that scripts/sync-data.mjs
// copied, and the page reads their JSON at build time. A listed site with a broken file fails the
// build; an unknown id answers 404. Concept features (T3–T5) are composed here after D-001 (C1).
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { SiteNav } from "@/components/content/site-nav";
import { ProvenancePanel } from "@/components/provenance/provenance-panel";
import {
  GroundCheckSection,
  IndicesSection,
  ProfilesSection,
  RecentSection,
  SiteHeader,
} from "@/components/site/site-sections";
import { t } from "@/i18n";
import { listSiteIds, loadSiteBundle } from "@/lib/data/loaders";
import { siteName } from "@/lib/site-name";
import { buildSiteView } from "@/lib/site-view";
import { UiStoreProvider } from "@/stores/ui-store";

export function generateStaticParams() {
  const ids = listSiteIds();
  // Cache Components needs at least one param at build time; without site data the placeholder 404s.
  return ids.length > 0 ? ids.map((siteId) => ({ siteId })) : [{ siteId: "__none__" }];
}

export async function generateMetadata({ params }: PageProps<"/sites/[siteId]">): Promise<Metadata> {
  const { siteId } = await params;
  const name = siteName(siteId);
  return {
    title: t("site.meta.title", { name }),
    description: t("site.meta.description", { name }),
  };
}

export default async function SitePage({ params }: PageProps<"/sites/[siteId]">) {
  const { siteId } = await params;
  const bundle = loadSiteBundle(siteId);
  if (!bundle) notFound();
  const view = buildSiteView(bundle);
  const name = siteName(siteId);

  return (
    // No site.json yet, so no per-site default unit (FR23): metric until the agronomist sets it.
    <UiStoreProvider unitSystem="metric">
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-10 px-4 py-10">
        <div className="flex flex-col gap-6">
          <SiteNav />
          <SiteHeader name={name} view={view} />
        </div>
        <RecentSection view={view} />
        <IndicesSection view={view} />
        <ProfilesSection view={view} />
        <GroundCheckSection view={view} />
      </main>
      <ProvenancePanel registry={{ records: view.records }} />
    </UiStoreProvider>
  );
}
