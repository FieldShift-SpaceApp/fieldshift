# Decisions log (append-only)

> **SI-assisted:** structure written with Claude Code (Anthropic); human review pending. The **content of D-001 and later human decisions is written by people, not AI** (event rule C1).

Concept, name, scope cuts, stack, demo format. Never edit or delete past entries; supersede them with a new one ("Supersedes" column). Single source: the brief and the PRD only link to the decision ID, they do not copy it.

## D-000 — Technical coordination decisions (2026-11-14)

Technical and process decisions made before the concept, valid for any concept. Proposed by the coordination chat (Claude Code) and vetoable by FLIGHT, except CO-6, which is FLIGHT's own decision. None of them is about the product concept. Exact times were not recorded; all were taken on 2026-11-14 before 13:00 BRT.

| # | Decision | Who decided | Why | Supersedes |
|---|---|---|---|---|
| D-000/CO-1 | The public repository stays `FieldShift-SpaceApp/fieldshift` (the architecture's `field-shift` is only a code name) | coordination, vetoable by FLIGHT | already public with links shared; renaming later is reversible | — |
| D-000/CO-2 | Folder layout follows architecture v0.1 (`packages/contracts`, `content/`, `data/`, `DECISIONS.md`, `RESOURCES.md`), keeping `AGENTS.md`, `CLAUDE.md` and `coord/status/` (protocol between the team's AI assistants) | coordination, vetoable by FLIGHT | the architecture is more detailed; the AI protocol does not conflict with it | — |
| D-000/CO-3 | License stays Apache-2.0 (the architecture suggested MIT) | coordination, vetoable by FLIGHT | Apache-2.0 is the default in the Space Apps terms | — |
| D-000/CO-4 | ORNL MODIS Subsets is not counted as a guaranteed fallback data path | coordination, vetoable by FLIGHT | the service returned HTTP 503 on 2026-11-14 | — |
| D-000/CO-5 | The team's work fronts run as agents of one coordination session | coordination, vetoable by FLIGHT | separate editor tabs and terminal windows were not stable | — |
| D-000/CO-6 | Team members' pre-existing private projects are used **only as reference**; all code is written during the event, nothing is copied | FLIGHT | those repositories have no license, and the event rules treat prior code as third-party material (license + citation) | — |

## D-001 — Concept (human decision, GATE-1)

**Status: OPEN.** Filled in by the team, without AI, at the concept meeting. It becomes **FINAL** only when every field is filled. Until then, nothing concept-specific is built (C1).

| Field (all required) | Decision |
|---|---|
| ID / status | D-001 · PROVISIONAL → FINAL when every field is filled |
| Origin of the idea | |
| Local Lead answer about AI use | |
| Concept | |
| One-line differentiator | |
| Product name (provisional is fine) | |
| Main demo visual | |
| Demo format | |
| Priority site (if one is cut) | |
| Primary · secondary award | |
| Who decided (names) and time (BRT) | |
| Risks from checklist VC1–VC10 | |

## Later decisions

| # | Date/time (BRT) | Decision | Who decided | Why | Supersedes |
|---|---|---|---|---|---|
