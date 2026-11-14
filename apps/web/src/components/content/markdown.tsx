// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Renders repository markdown (RESOURCES.md, SI-USAGE.md, content/**) as static HTML.
// No raw HTML: `skipHtml` drops it (including the "SI-assisted" HTML comments, which would otherwise
// show up as escaped text); relative links point to the public repo.
import type { ReactNode } from "react";
import Link from "next/link";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { t } from "@/i18n";
import { resolveDocHref } from "@/lib/content";

export function DocLink({ href, children }: { href: string | null; children: ReactNode }) {
  if (!href) return <>{children}</>;
  const cls = "underline underline-offset-4 hover:no-underline";
  if (href.startsWith("/") || href.startsWith("#")) {
    return (
      <Link href={href} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={cls}>
      {children}
      <span className="sr-only"> {t("content.externalLink")}</span>
    </a>
  );
}

type Level = 1 | 2 | 3 | 4 | 5 | 6;
const HEADING_CLASS: Record<Level, string> = {
  1: "text-2xl font-semibold",
  2: "mt-8 text-xl font-semibold",
  3: "mt-6 text-lg font-semibold",
  4: "mt-4 font-semibold",
  5: "mt-4 font-medium",
  6: "mt-4 font-medium",
};

function heading(level: number, offset: number): Components["h1"] {
  const shifted = Math.min(6, level + offset) as Level;
  const Tag = `h${shifted}` as const;
  return function Heading({ children }) {
    return <Tag className={HEADING_CLASS[shifted]}>{children}</Tag>;
  };
}

export function Markdown({
  children,
  source,
  headingOffset = 0,
}: {
  children: string;
  /** Repo-relative path of the markdown file, to resolve relative links. */
  source: string;
  /** Added to every heading level, so a document's "##" fits under the page's own headings. */
  headingOffset?: number;
}) {
  const components: Components = {
    h1: heading(1, headingOffset),
    h2: heading(2, headingOffset),
    h3: heading(3, headingOffset),
    h4: heading(4, headingOffset),
    h5: heading(5, headingOffset),
    h6: heading(6, headingOffset),
    p: ({ children }) => <p className="mt-3 leading-7">{children}</p>,
    ul: ({ children }) => <ul className="mt-3 list-disc space-y-1.5 pl-6">{children}</ul>,
    ol: ({ children }) => <ol className="mt-3 list-decimal space-y-1.5 pl-6">{children}</ol>,
    blockquote: ({ children }) => (
      <blockquote className="mt-3 border-l-4 border-foreground/20 pl-4 text-foreground/80">{children}</blockquote>
    ),
    a: ({ href, children }) => <DocLink href={resolveDocHref(href, source)}>{children}</DocLink>,
    code: ({ children }) => <code className="rounded bg-foreground/5 px-1 py-0.5 font-mono text-[0.9em]">{children}</code>,
    pre: ({ children }) => <pre className="mt-3 overflow-x-auto rounded bg-foreground/5 p-3 text-sm">{children}</pre>,
    table: ({ children }) => (
      <div className="mt-3 overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">{children}</table>
      </div>
    ),
    th: ({ children }) => <th className="border-b border-foreground/20 px-2 py-1.5 align-bottom font-semibold">{children}</th>,
    td: ({ children }) => <td className="border-b border-foreground/10 px-2 py-1.5 align-top">{children}</td>,
  };
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components} skipHtml>
      {children}
    </ReactMarkdown>
  );
}
