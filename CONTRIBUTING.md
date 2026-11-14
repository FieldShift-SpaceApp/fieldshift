# Contributing (team FieldShift)

## Setup (5 min, once)
1. Join: open https://github.com/FieldShift-SpaceApp/fieldshift/issues/new?template=join.yml, type the team code from the team chat, submit, then accept the invitation (email or https://github.com/notifications). Then `git clone https://github.com/FieldShift-SpaceApp/fieldshift`.
2. Install and log in to the GitHub CLI: `gh auth login` (your AI uses it to read/write issues).
3. Create a free NASA **Earthdata Login** account (https://urs.earthdata.nasa.gov) if you touch data; copy `.env.example` to `.env`.
4. Open your AI assistant **in the repo root** so it loads `AGENTS.md` (Claude Code loads it via `CLAUDE.md`).
5. First prompt to your AI: *"Read AGENTS.md and all coord/status files, list the open issues for front:<my-front>, and tell me what to do next."*

## The 60-second version
1. Pick or create an issue labeled with your front (`front:eecom`, `front:inco`, …).
2. `git switch -c <front>/<topic>` from an up-to-date `main`.
3. Commit small (`feat(web): …`), push, open a PR, fill the template.
4. Your coverage pair reviews (EECOM↔GUIDO, INCO↔SURGEON, FLIGHT↔CAPCOM). Squash merge.
5. Update your `coord/status/<front>.md`.

## Non-coders (e.g. crop base)
Edit files in `data/crops/` directly on github.com (pencil icon) → "Propose changes" → it opens a PR for you.

## Asking another front for something
Open an issue labeled `needs:<their-front>`. Do not edit their folder.

## Secrets and data
- Copy `.env.example` to `.env`. Never commit `.env`.
- Raw satellite files go in `data/raw/` (git-ignored). Commit only small processed outputs.

## AI use
Allowed for code, research and review — **not** for coming up with the solution idea (event rule). Declare every use in `SI-USAGE.md` and in the PR template.
