# Web app (INCO)

> **SI-assisted:** written with Claude Code (Anthropic); human review pending. See `SI-USAGE.md` at the repo root.

Next.js 16 (App Router, static generation) + TypeScript + Tailwind CSS 4 + shadcn/ui, as defined in the architecture v0.1 (ADR-1, ADR-9).

- All user-facing strings live in `src/i18n/en.ts` (NFR15); use `t("key")`.
- The support disclaimer (FR7) is rendered on every page by `src/app/layout.tsx`.
- Add UI components with `npx shadcn@4.23.0 add <component>` from this folder.

```bash
npm run dev        # from the repo root
npm run lint && npm run typecheck && npm run build
```
