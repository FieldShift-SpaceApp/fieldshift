# Contributing (team FieldShift)

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
