# Methods

> **SI-assisted:** written with Claude Code (Anthropic); human review pending. See `SI-USAGE.md` at the repo root.

One method per file (`<method>.md`), rendered on the public `/data-methods` page in `order`. This README is not rendered.

Front-matter (checked by `apps/web/tests/unit/content.test.ts`):

```yaml
anchor: et0-fao56        # required, ^[a-z0-9-]+$, unique; becomes the section id on /data-methods
title: ...               # required
order: 20                # optional, sort key
refs:                    # required, at least one: { label, url }
  - label: ...
    url: https://...
limitations:             # optional; listed under "Limitations" on /data-methods, linked back to the method
  - "..."
```

The `method.doc_anchor` of every provenance record must point to an anchor defined here (VL1, ADR-8); the unit test checks this against every `provenance.json` in `data/`.

Owners: GUIDO + SURGEON. Datasets and tools are listed in [`RESOURCES.md`](../../RESOURCES.md).

## Limitations and uncertainty

Limitations live in the `limitations` list of the method they affect, so the page and the method never disagree.
