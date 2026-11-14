// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// Content loaders for /data-methods and /glossary (Story 1.4, FR8, FR17, FR18).
// Build-time only: reads the files that scripts/sync-data.mjs copies into src/generated/
// (RESOURCES.md, SI-USAGE.md, content/**). Synchronous fs reads keep the pages fully static.
// Every loader takes `baseDir` so tests can point it at the repo root, which has the same layout.
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { parse as parseYaml } from "yaml";

export const GENERATED_DIR = path.join(process.cwd(), "src", "generated");

/** Public repository, used to turn relative links inside the root markdown files into absolute ones. */
export const REPO_BLOB_URL = "https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/";

const ANCHOR_RE = /^[a-z0-9-]+$/;

export interface ContentRef {
  label: string;
  url: string;
}

export interface MethodDoc {
  anchor: string;
  title: string;
  order: number;
  refs: ContentRef[];
  limitations: string[];
  /** Markdown body, without front-matter. */
  body: string;
  /** Repo-relative path of the source file, used to resolve relative links. */
  source: string;
}

export interface GlossaryEntry {
  id: string;
  term: string;
  definition: string;
  refs: ContentRef[];
  reviewedBy: string;
}

export interface MarkdownDoc {
  body: string;
  source: string;
  data: Record<string, unknown>;
}

export interface DataMethodsContent {
  resources: MarkdownDoc;
  siUsage: MarkdownDoc;
  relatedWork: MarkdownDoc;
  methods: MethodDoc[];
  glossary: GlossaryEntry[];
}

function readRequired(baseDir: string, rel: string): string {
  const file = path.join(baseDir, rel);
  if (!existsSync(file)) {
    throw new Error(`content: missing ${rel} in ${baseDir} (did scripts/sync-data.mjs run?)`);
  }
  return readFileSync(file, "utf8");
}

/** Drops the first level-1 heading: the page supplies its own section headings. */
export function stripTitle(markdown: string): string {
  return markdown.replace(/^\s*#\s+[^\n]*\n/, "");
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function nonEmptyString(v: unknown, where: string): string {
  if (typeof v !== "string" || v.trim() === "") throw new Error(`content: ${where} must be a non-empty string`);
  return v.trim();
}

function parseRefs(v: unknown, where: string): ContentRef[] {
  if (v === undefined || v === null) return [];
  if (!Array.isArray(v)) throw new Error(`content: ${where}.refs must be a list`);
  return v.map((r, i) => {
    if (!isRecord(r)) throw new Error(`content: ${where}.refs[${i}] must be { label, url }`);
    return { label: nonEmptyString(r.label, `${where}.refs[${i}].label`), url: nonEmptyString(r.url, `${where}.refs[${i}].url`) };
  });
}

export function loadMarkdownDoc(baseDir: string, rel: string): MarkdownDoc {
  const parsed = matter(readRequired(baseDir, rel));
  return { body: stripTitle(parsed.content), source: rel, data: parsed.data };
}

/** content/methods/*.md (README.md excluded), sorted by `order` then title. */
export function loadMethods(baseDir: string): MethodDoc[] {
  const dirRel = path.posix.join("content", "methods");
  const dir = path.join(baseDir, dirRel);
  if (!existsSync(dir)) throw new Error(`content: missing ${dirRel} in ${baseDir}`);
  const files = readdirSync(dir).filter((f) => f.endsWith(".md") && f.toLowerCase() !== "readme.md");
  const seen = new Set<string>();
  const methods = files.map((file): MethodDoc => {
    const source = path.posix.join(dirRel, file);
    const { data, content } = matter(readFileSync(path.join(dir, file), "utf8"));
    const anchor = nonEmptyString(data.anchor, `${source} anchor`);
    if (!ANCHOR_RE.test(anchor)) throw new Error(`content: ${source} anchor "${anchor}" must match ${ANCHOR_RE}`);
    if (seen.has(anchor)) throw new Error(`content: duplicate method anchor "${anchor}" (${source})`);
    seen.add(anchor);
    const refs = parseRefs(data.refs, source);
    if (refs.length === 0) throw new Error(`content: ${source} needs at least one ref`);
    const limitations = data.limitations === undefined ? [] : data.limitations;
    if (!Array.isArray(limitations)) throw new Error(`content: ${source} limitations must be a list`);
    return {
      anchor,
      title: nonEmptyString(data.title, `${source} title`),
      order: typeof data.order === "number" ? data.order : Number.MAX_SAFE_INTEGER,
      refs,
      limitations: limitations.map((l, i) => nonEmptyString(l, `${source} limitations[${i}]`)),
      body: content.trim(),
      source,
    };
  });
  return methods.sort((a, b) => a.order - b.order || a.title.localeCompare(b.title));
}

/** content/glossary.yaml, in file order. */
export function loadGlossary(baseDir: string): GlossaryEntry[] {
  const rel = path.posix.join("content", "glossary.yaml");
  const doc: unknown = parseYaml(readRequired(baseDir, rel));
  if (!isRecord(doc) || !Array.isArray(doc.terms)) throw new Error(`content: ${rel} must have a "terms" list`);
  const seen = new Set<string>();
  return doc.terms.map((raw, i): GlossaryEntry => {
    const where = `${rel} terms[${i}]`;
    if (!isRecord(raw)) throw new Error(`content: ${where} must be a mapping`);
    const id = nonEmptyString(raw.id, `${where}.id`);
    if (!ANCHOR_RE.test(id)) throw new Error(`content: ${where}.id "${id}" must match ${ANCHOR_RE}`);
    if (seen.has(id)) throw new Error(`content: duplicate glossary id "${id}"`);
    seen.add(id);
    const term = isRecord(raw.term) ? raw.term.en : undefined;
    const definition = isRecord(raw.definition) ? raw.definition.en : undefined;
    return {
      id,
      term: nonEmptyString(term, `${where}.term.en`),
      definition: nonEmptyString(definition, `${where}.definition.en`),
      refs: parseRefs(raw.refs, where),
      reviewedBy: nonEmptyString(raw.reviewed_by, `${where}.reviewed_by`),
    };
  });
}

export function loadDataMethods(baseDir: string = GENERATED_DIR): DataMethodsContent {
  return {
    resources: loadMarkdownDoc(baseDir, "RESOURCES.md"),
    siUsage: loadMarkdownDoc(baseDir, "SI-USAGE.md"),
    relatedWork: loadMarkdownDoc(baseDir, path.posix.join("content", "related-work.md")),
    methods: loadMethods(baseDir),
    glossary: loadGlossary(baseDir),
  };
}

/**
 * Link target for an href found in a markdown file at repo path `source`.
 * Absolute http(s) and in-site links ("/x", "#x") pass through; other schemes are dropped;
 * relative paths point to the file in the public repository.
 */
export function resolveDocHref(href: string | undefined, source: string): string | null {
  if (!href) return null;
  if (href.startsWith("#") || (href.startsWith("/") && !href.startsWith("//"))) return href;
  if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith("//")) {
    try {
      const url = new URL(href.startsWith("//") ? `https:${href}` : href);
      return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
    } catch {
      return null;
    }
  }
  const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(source), href));
  if (resolved.startsWith("..")) return null;
  return REPO_BLOB_URL + resolved.replace(/^\.\//, "");
}
