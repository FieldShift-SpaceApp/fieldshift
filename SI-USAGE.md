# SI (AI) usage log

Required by the Space Apps Project Submission Guide: describe how AI tools were used. AI-generated images/videos carry a visible watermark; AI-generated code, data and audio are declared here and in metadata.

**Not used for:** generating the solution concept, differentiator or name (decided by the team; see `DECISIONS.md`).

| Date/time (BRT) | Who | Tool | Used for | Files / PR |
|---|---|---|---|---|
| 2026-11-14 | FLIGHT | Claude Code (Anthropic) | Research on past winners, official challenge text and NASA data access; repository scaffolding (structure, templates, AGENTS.md) | initial commit |
| 2026-11-14 12:20 | FLIGHT (INFRA chat) | Claude Code (Anthropic) | Repository restructure to the architecture v0.1 layout (CO-2): moved files, updated path references | PR `infra/restructure` |
| 2026-11-14 12:50 | FLIGHT (INFRA chat) | Claude Code (Anthropic) | Monorepo bootstrap: npm workspaces, `apps/web` scaffold (create-next-app + shadcn CLI) with canary page and strings file, `services/science` uv package with CLI stub and tests, hygiene script, editor/runtime config | PR `infra/bootstrap` |
| 2026-11-14 13:05 | FLIGHT (INFRA chat) | Claude Code (Anthropic) | CI workflow (hygiene with pinned gitleaks, science with uv, web lint/typecheck/build) | PR `infra/ci` |
| 2026-11-14 13:15 | GUIDO (CONTRACTS chat, issue #12) | Claude Code (Anthropic) | Implementation of the v1.0.0 data contracts specified in the architecture (pydantic models, JSON Schema export CLI, TS generation with json-schema-to-typescript), agricultural-year function and parity fixtures, pytest tests, CI drift checks. No concept decisions (Crop/Ranker left out) | PR `guido/contracts-codegen` |
