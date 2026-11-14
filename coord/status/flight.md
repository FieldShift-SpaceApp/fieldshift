# Status — FLIGHT

> Only the FLIGHT front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 13:25 — FLIGHT (INFRA chat, Claude Code)
Done: #15 web tests: Vitest 5.1.0 + Testing Library + jsdom 29.1.1 (FR7 notice and sync-data unit tests), Playwright 1.65.1 Chromium smoke (canary opens, FR7 notice, zero external requests), `scripts/sync-data.mjs` as prebuild/dev (no site data = notice, not error), CI web job runs test + build + e2e. #14 Story 1.2: `SI-USAGE.md` in the PRD format (conventions, retroactive entries, header rule, watermark rule), `RESOURCES.md` (NASA POWER selected; NASA and other candidates with licenses and "In git?"), `DECISIONS.md` (D-000 = CO-1..CO-6, empty D-001 for the team), `docs/submission/checklist.md`, "SI-assisted" headers on files generated so far.
Next: CI green on the PR; human review and merge by FLIGHT.
Blocked by: none
Needs from others: team fills D-001 (no AI); reviewers replace "pending" in SI-USAGE.md; architecture owner updates the Tech Stack table: jsdom 29.1.1 instead of 31.0.1 (jsdom >= 30 needs Node >= 24.15; machines run 24.14 with engine-strict).
Contract changes: none

## 2026-11-14 13:05 — FLIGHT (INFRA chat, Claude Code)
Done: `.github/workflows/ci.yml` with jobs `hygiene` (forbidden paths + gitleaks v8.30.1 over full history), `science` (uv 0.11.3, `uv sync --locked`, ruff, pytest) and `web` (npm ci, lint, typecheck, build).
Next: after CI is green, Otávio marks `hygiene`, `science`, `web` as required on `main`; Vercel import.
Blocked by: Otávio (branch protection, Vercel)
Needs from others: none
Contract changes: none

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
