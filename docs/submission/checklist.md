# Submission checklist (compliance)

> **SI-assisted:** written with Claude Code (Anthropic); human review pending. See `SI-USAGE.md` at the repo root.

Owner: FLIGHT. Run before the internal submit (Sun 15/11 20:00 BRT). Each item is checked by a person, with the evidence written next to it. Latest automated run, with corrections and owners: [`preflight.md`](preflight.md).

| # | Rule | Check | Evidence |
|---|---|---|---|
| 1 | C1: concept, differentiator and name decided by people | `DECISIONS.md` D-001 is FINAL (every field filled, names and time) | |
| 2 | C2: AI use declared | `SI-USAGE.md` has a row for every AI-assisted PR; the "Use of AI" section of the submission page is filled from it | |
| 3 | C2: AI-generated images and videos | every AI-generated image, slide visual, thumbnail and video frame carries a **visible watermark** ("AI-generated"), readable at the size shown | |
| 4 | C2: AI-generated audio, code and data | acknowledged in the submission text and in metadata (file headers, `provenance.json`) | |
| 5 | C3 / CON3: no NASA logos, flags or mission insignia | no NASA logo ("meatball", "worm"), flag or mission patch in the app, repo assets, slides or video; dataset names cited as text only. Check: `git ls-files '*.png' '*.jpg' '*.jpeg' '*.svg' '*.gif' '*.webp' '*.ico'` and open each file; watch the pitch assets | |
| 6 | C4: at least one NASA dataset | `RESOURCES.md` lists it (name + link) with status `selected`, and the app shows numbers read from it | |
| 7 | Licenses | every dataset used is in `RESOURCES.md` with its license; nothing marked "In git? no" is committed (`data/`, `apps/web/public/`) | |
| 8 | Public link | production URL opens without login (`curl -s -o /dev/null -w '%{http_code}' <url>` → 200) | |
| 9 | Secrets | CI `hygiene` job green on the submitted commit (forbidden paths + gitleaks) | |
| 10 | Eligibility | all members (≤ 6) on the Members tab, confirmed at the Florianópolis Local Event, none on the waitlist; official challenge selected | |
| 11 | Required fields | every field of [`page-draft.md`](page-draft.md) filled, no `[PENDING …]` left | |
| 12 | English everywhere | page text **and every linked material** (repo files incl. `coord/` and code comments, app, demo); a video in another language has English captions | |
| 13 | Demo limits | video ≤ 30.0 s (`ffprobe` output here) **or** ≤ 7 slides incl. title and intro — over the limit = not eligible for Global Judging ([`demo-plan.md`](demo-plan.md)) | |
| 14 | Demo SI labels | synthetic voice acknowledged in description, metadata and `SI-USAGE.md`; SI cards watermarked "AI-generated"; non-data cards labeled "Illustrative" | |
| 15 | Minors | no image, video, audio or likeness of anyone under 18 in the demo or the project | |
| 16 | References field complete | every library, font, icon, image and music track used is in `RESOURCES.md` and in field 8 (the final declaration checkbox depends on it) | |
| 17 | Demo and app links | demo link and app URL open in a private window, logged out, and on a phone; no Google Drive link set to "Restricted" | |
| 18 | Submit | "Submit for Judging" by 20:00 BRT Sun; confirmation screenshot in `coord/status/flight.md`; only the last save before 23:59 counts | |
