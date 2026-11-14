# AGENTS.md — shared rules for every AI assistant on this repo

> Read by Codex, Cursor, Copilot, Gemini CLI and others. Claude Code reads it through `CLAUDE.md` (`@AGENTS.md`).
> Six people, six AI assistants, one repo. **The repo is how the AIs talk to each other.** Follow this file exactly.

## 1. Project
- **Team:** FieldShift · NASA Space Apps Challenge 2026 · Local Event: Founder Haus, Florianópolis.
- **Challenge:** *Field Shift: Adapting Farms with NASA Data*.
- **Clock (America/Sao_Paulo):** internal submit **Sun 15/11 20:00** · official close **Sun 15/11 23:59**.

## 2. Hard rules (event compliance)
1. **C1 — No AI ideation of the solution.** Do not propose the product concept, the differentiator or the name. Those are human decisions, recorded in `coord/decisions.md`. You may research, implement, review and explain.
2. **C2 — Declare AI use.** Every AI-assisted change gets a line in `SI-USAGE.md` and the PR checkbox. AI images/videos need a visible watermark.
3. **C3 — No NASA logos, flags or mission insignia** anywhere. Dataset names (SMAP, GPM…) may be cited as sources.
4. **C4 — Use at least one NASA dataset**, cited by name and link in `docs/data-and-methods.md`.
5. **Never invent numbers.** Every number shown to users comes from code that reads a cited dataset.
6. **No secrets in git.** Earthdata/API credentials live in `.env` or `~/.netrc` only. No raw HDF/NetCDF in git.

## 3. Fronts and folder ownership

| Front | Code name | Owns |
|---|---|---|
| Flight Director (cadence, compliance, submission page) | FLIGHT | `coord/`, `SI-USAGE.md`, `docs/submission/` |
| Data (NASA ingestion, harmonization) | EECOM | `services/science/ingest/`, `data/processed/` |
| Model (scoring, uncertainty, explainability) | GUIDO | `services/science/model/` |
| App (front-end, map, inputs) | INCO | `apps/web/` |
| Agro & Science (crop base, evidence, glossary) | SURGEON | `data/crops/`, `docs/data-and-methods.md` |
| Story & Pitch (demo, video/slides) | CAPCOM | `docs/pitch/` |

`contracts/` is **shared**: the JSON contracts between fronts. A change there needs approval from every front that reads it.

**Do not edit another front's folder.** Ask through an issue (§4.3).

## 4. Coordination protocol (how AIs talk)

### 4.1 Before you start a work block
1. `git pull` on `main`.
2. Read **all** `coord/status/*.md` (one file per front) and `coord/decisions.md`.
3. List open issues for your front: `gh issue list --label front:<code> --state open` and `gh issue list --label needs:<code>`.

### 4.2 After every work block (or every ~2 h)
Update **only your own** `coord/status/<code>.md` with this format and commit it in your PR:
```
## <YYYY-MM-DD HH:MM> — <who>
Done: …
Next: …
Blocked by: … (link issue)
Needs from others: … (link issue)
Contract changes: none | PR #…
```
One file per front = no merge conflicts between AIs.

### 4.3 Asking another front for something
Open a GitHub issue — never edit their files:
```
gh issue create --label needs:<their-code> --label front:<your-code> \
  --title "<short request>" --body "<what, why, by when, link to contract>"
```
When you finish a request addressed to you, comment the PR link and close the issue.

### 4.4 Contracts
- Producers and consumers code against `contracts/*.schema.json` and the fixtures in `contracts/fixtures/`.
- Changing a contract = a PR that touches `contracts/` only, labeled `contract`, approved by every front that consumes it. Never change a contract silently inside a feature PR.

### 4.5 Decisions
Human decisions (concept, scope cuts, stack, demo format) are appended to `coord/decisions.md` with date, people and reason. Never edit or delete past entries; supersede them with a new one.

## 5. Git workflow
- Never commit to `main`. Branch: `<code>/<topic>` (e.g. `eecom/power-ingest`).
- Small PRs. 1 approval from your coverage pair (EECOM↔GUIDO, INCO↔SURGEON, FLIGHT↔CAPCOM); if the pair is asleep, FLIGHT approves.
- Squash merge. No force push. No `--no-verify`.
- Conventional commits: `feat(web): …`, `fix(ingest): …`, `docs(crops): …`.

## 6. Language
- Code, identifiers, UI, submission material: **English**.
- Team chat and `coord/` notes: Portuguese is fine.
