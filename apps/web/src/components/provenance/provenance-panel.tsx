// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// FR19 / ADR-8: click 1 on a number opens this panel with the Provenance fields; click 2 is the
// source link. Reads which records to show from the page's UI store; the registry comes by props.
"use client";

import type { ReactNode } from "react";
import { Dialog } from "radix-ui";
import type { Provenance, ProvenanceId, ProvenanceRegistry, Ref } from "@fieldshift/contracts";
import { t, type MessageKey } from "@/i18n";
import { unitLabel } from "@/lib/units";
import { useUiStore } from "@/stores/ui-store";
import { DataTypeLabel } from "./data-type-label";

/** Only http(s) URLs become links; anything else is shown as text. */
function safeHref(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.href : null;
  } catch {
    return null;
  }
}

function doiHref(doi: string): string | null {
  return safeHref(/^https?:/i.test(doi) ? doi : `https://doi.org/${doi}`);
}

function ExternalLink({ href, children }: { href: string | null; children: ReactNode }) {
  if (!href) return <>{children}</>;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="underline underline-offset-4 hover:no-underline">
      {children}
    </a>
  );
}

function Field({ label, children }: { label: MessageKey; children: ReactNode }) {
  return (
    <div className="grid gap-0.5 py-1.5 sm:grid-cols-[11rem_1fr] sm:gap-3">
      <dt className="text-muted-foreground">{t(label)}</dt>
      <dd className="break-words">{children}</dd>
    </div>
  );
}

function RefItem({ item }: { item: Ref }) {
  const href = safeHref(item.url) ?? (item.doi ? doiHref(item.doi) : null);
  return (
    <li>
      <ExternalLink href={href}>{item.label}</ExternalLink>
      {item.citation ? <span className="text-muted-foreground"> · {item.citation}</span> : null}
    </li>
  );
}

function supportKey(support: Provenance["spatial"]["support"]): MessageKey {
  switch (support) {
    case "point":
      return "provenance.support.point";
    case "polygon":
      return "provenance.support.polygon";
    case "containing_pixel":
      return "provenance.support.containing_pixel";
    case "regional":
      return "provenance.support.regional";
    default:
      return "provenance.none";
  }
}

/** All FR19 fields of one record. Optional fields appear only when the record has them. */
export function ProvenanceRecord({ record }: { record: Provenance }) {
  const { source, access, method } = record;
  return (
    <section aria-labelledby={`prov-title-${record.id}`} className="border-t border-border pt-3 first:border-t-0 first:pt-0">
      <h3 id={`prov-title-${record.id}`} className="font-medium">
        {record.title.en}
      </h3>
      <p className="font-mono text-xs text-muted-foreground">{record.id}</p>
      <dl className="mt-2 text-sm">
        <Field label="provenance.field.dataType">
          <DataTypeLabel dataType={record.data_type} />
        </Field>
        {source ? (
          <>
            <Field label="provenance.field.dataset">
              {source.dataset} · {source.provider}
            </Field>
            <Field label="provenance.field.product">
              {source.product} · {source.version}
            </Field>
            {source.collection_id ? (
              <Field label="provenance.field.collection">
                <span className="font-mono">{source.collection_id}</span>
              </Field>
            ) : null}
          </>
        ) : null}
        <Field label="provenance.field.variable">
          {record.variable.name.en} ({record.variable.code}) · {unitLabel(record.variable.unit) || record.variable.unit}
        </Field>
        {record.variable.native_unit ? (
          <Field label="provenance.field.nativeUnit">{record.variable.native_unit}</Field>
        ) : null}
        <Field label="provenance.field.spatial">
          {record.spatial.resolution} · {t(supportKey(record.spatial.support))}
        </Field>
        <Field label="provenance.field.temporal">{record.temporal.resolution}</Field>
        <Field label="provenance.field.period">
          {t("provenance.period.range", { start: record.temporal.period.start, end: record.temporal.period.end })}
        </Field>
        <Field label="provenance.field.aggregation">{record.aggregation.en}</Field>
        {method ? (
          <Field label="provenance.field.method">
            {method.name} ·{" "}
            <ExternalLink href={safeHref(method.ref.url) ?? (method.ref.doi ? doiHref(method.ref.doi) : null)}>
              {method.ref.label}
            </ExternalLink>
          </Field>
        ) : null}
        {record.inputs && record.inputs.length > 0 ? (
          <Field label="provenance.field.inputs">
            <ul className="font-mono text-xs">
              {record.inputs.map((id) => (
                <li key={id}>{id}</li>
              ))}
            </ul>
          </Field>
        ) : null}
        {record.authored_by ? <Field label="provenance.field.authoredBy">{record.authored_by}</Field> : null}
        {record.refs && record.refs.length > 0 ? (
          <Field label="provenance.field.refs">
            <ul>
              {record.refs.map((ref) => (
                <RefItem key={`${ref.label}-${ref.url ?? ref.doi ?? ""}`} item={ref} />
              ))}
            </ul>
          </Field>
        ) : null}
        {access ? (
          <>
            <Field label="provenance.field.link">
              <ExternalLink href={safeHref(access.url)}>{t("provenance.link.source")}</ExternalLink>
            </Field>
            {access.doi ? (
              <Field label="provenance.field.doi">
                <ExternalLink href={doiHref(access.doi)}>{access.doi}</ExternalLink>
              </Field>
            ) : null}
            <Field label="provenance.field.accessedAt">{access.accessed_at}</Field>
            <Field label="provenance.field.terms">
              <ExternalLink href={safeHref(access.terms_url)}>{t("provenance.link.terms")}</ExternalLink>
            </Field>
            {access.license ? <Field label="provenance.field.license">{access.license}</Field> : null}
          </>
        ) : null}
        <Field label="provenance.field.limitations">
          {record.limitations.length > 0 ? (
            <ul className="list-disc pl-4">
              {record.limitations.map((item) => (
                <li key={item.en}>{item.en}</li>
              ))}
            </ul>
          ) : (
            t("provenance.none")
          )}
        </Field>
      </dl>
    </section>
  );
}

export interface ProvenancePanelProps {
  /** Site registry (or only the records this page shows: payload rule, Frontend Services Layer). */
  registry: Pick<ProvenanceRegistry, "records">;
}

export function ProvenancePanel({ registry }: ProvenancePanelProps) {
  const open = useUiStore((s) => s.provenance.open);
  const ids = useUiStore((s) => s.provenance.ids);
  const closeProvenance = useUiStore((s) => s.closeProvenance);

  return (
    <Dialog.Root open={open} onOpenChange={(next) => (next ? undefined : closeProvenance())}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-foreground/30" />
        <Dialog.Content
          data-prov={ids.join(" ")}
          className="fixed inset-y-0 right-0 z-50 flex w-full max-w-lg flex-col gap-3 overflow-y-auto border-l border-border bg-background p-5 shadow-lg focus:outline-none"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="text-lg font-semibold">{t("provenance.panel.title")}</Dialog.Title>
              <Dialog.Description className="text-sm text-muted-foreground">
                {t("provenance.panel.description")}
              </Dialog.Description>
            </div>
            <Dialog.Close className="min-h-11 rounded px-3 text-sm underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-ring">
              {t("provenance.panel.close")}
            </Dialog.Close>
          </div>
          {ids.map((id: ProvenanceId) => {
            const record = registry.records[id];
            return record ? (
              <ProvenanceRecord key={id} record={record} />
            ) : (
              <p key={id} role="alert" className="text-sm">
                {t("provenance.panel.notFound", { id })}
              </p>
            );
          })}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
