# Status — FLIGHT

> Only the FLIGHT front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 12:50 — FLIGHT (INFRA chat, Claude Code)
Done: bootstrap: npm workspaces (`apps/*`, `packages/*`), `apps/web` Next.js 16.4.6 + Tailwind 4 + shadcn (radix-nova) with English canary page, FR7 disclaimer and `src/i18n/en.ts`; `services/science` uv package (Python 3.12, pydantic, ruff, pytest); `packages/contracts` package; `.nvmrc`, `.npmrc`, `.editorconfig`, `scripts/check-public-repo.sh`.
Next: CI workflow (hygiene + science + web, gitleaks pinned), then Vercel setup with Otávio.
Blocked by: none
Needs from others: none
Contract changes: none

## 2026-11-14 12:20 — FLIGHT (INFRA chat, Claude Code)
Done: repo layout reconciled with architecture v0.1 (CO-2): `packages/contracts/`, `data/sites|cache/`, `DECISIONS.md`, `RESOURCES.md`, `content/methods/`; references updated in AGENTS.md, README, CONTRIBUTING, templates, CODEOWNERS.
Next: bootstrap PR (npm workspaces, `apps/web` Next.js + shadcn, `services/science` uv package, hygiene script), then CI.
Blocked by: none
Needs from others: none
Contract changes: none (folder move only)
