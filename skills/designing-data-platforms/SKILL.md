---
name: designing-data-platforms
description: >-
  Use when designing, proposing or reviewing an analytics data platform or a
  change to one — warehouse, lakehouse, or reporting replica — choosing its
  tier and tools (table format, catalog, query engine, orchestrator, BI),
  choosing how each source is ingested (batch or CDC) and where it can run,
  designing serving and reverse ETL, or deciding how PII, PCI or health data
  is governed and how erasure works. Writes a design document with
  architecture and pipeline diagrams.
---

# Designing data platforms

Decisions for analytics data platforms, from a reporting replica up to a full
lakehouse. Core rule: **work only the area the request is about** — each area's
rules live in their own file, and you read only the files your situation
lists. General data-engineering practice
(medallion layering, watermark pitfalls, idempotent reruns, SCD2, compaction,
late-data windows) is assumed known; this skill holds the decisions that are
commonly got wrong. Landscape snapshot dated **2026-10**.

Publishing events from services (outbox, topic design) is the services'
own design, out of scope here; this skill starts at consuming them. A
request to change pipeline code or config, with no design asked ("fix this
job", "add CDC to this connector"), is not this skill's work: it belongs to
`building-data-pipelines` when installed; this skill designs, it does not
edit the user's pipelines.

## Start here: route, read, ask once

Identify the situation from the request; ask only if it is unclear. The
situation decides **which files you read and which sections the design doc
contains** — read only those files, write only those sections, and add no
placeholder for the rest. `document.md` sets the order and the diagrams.

| Situation | Read | Doc sections | Questions |
|---|---|---|---|
| New platform | `document.md` + all area files | All; Why holds every area | 1–4 |
| Tool or tier choice | `document.md`, `platform-selection.md` | Decision · Architecture · Build steps · Why (tier, layers, verification) · Questions · Open questions | 1–3 |
| Ingestion (new or changed sources) | `document.md`, `ingestion.md` (+ `cdc.md` if CDC is a candidate) | Decision · Architecture · Pipeline · Build steps · Why (source inventory) · Questions · Open questions | 3 |
| Serving, modeling, or reverse ETL on an existing platform | `document.md`, `serving.md` | Decision · Architecture · Pipeline · Build steps · Why (serving and model design) · Questions · Open questions | 3 |
| Governance or erasure | `document.md`, `sensitive-data.md` | Decision · Architecture · Build steps · Why (sensitive data, erasure) · Questions · Open questions | 4 |
| Review of an existing design | The area files it covers | A gap list; change nothing | — |

A request touching two areas reads both rows' files and writes both rows'
sections. Tools and stacks the user already runs or names are given: never
re-weigh, re-pick, or list alternatives for them, and never assign the
existing platform a tier. A fuzzy business ask ("we want analytics") with no
stated consumers or sources first gets its consumers, the questions each
needs answered, and its sources pinned down: ask for them before designing.

Send the situation's questions in **one batch**. If the user is not
available, record each question with your assumption under "Questions and
assumptions" and proceed; the Decision names any assumption it rests on. Never invent an answer to a question the
situation does not ask.

1. **Willing to pay** for managed or commercial tools? Default when not:
   open-source, self-hosted.
2. **Who operates the platform** — a data platform team, one engineer
   part-time, or nobody? Self-hosted is not free to run: with no budget AND no
   operator, the answer is the smallest tier someone can run, never a
   self-hosted lakehouse.
3. **Freshness** each consumer actually needs, in minutes — "real-time" is
   not a requirement until it has a number.
4. **Regulated data** in any source (PII, card data, health data).

## Existing platforms

A request for a new part that neither reads from, writes to, nor changes
existing components is designed like a new platform. One that does
(entangled) starts from what exists, recorded in
`docs/data-platform/current-platform.md` (format in `document.md`):

- **The file exists:** look for it before anything else and read it. Start
  from it; if the request or a repo contradicts it (a tool it doesn't list),
  record one question about which is current and leave the file unchanged
  until the user answers — even when the repo looks newer. The design may
  proceed on the repo's version, stated as an assumption.
- **The request describes the platform:** that description is the answer;
  write the file from it, each component `told by you`.
- **The request gives a repo path:** read its pipeline code, infrastructure
  config and docs first, then write the file, each component `found in
  repo`. Ask only what the repo cannot answer, in the one batch. A path
  that doesn't exist or holds none of these: say so and ask instead.
- **None of these:** offer the choice — answer a short batch of questions,
  or give a repo path to read.

Write the file in the working directory's `docs/data-platform/`, never
inside a repo you were given only to read. Then design the change on it.
When you cannot tell whether a request is entangled, ask.

## The deliverable

`docs/data-platform/<topic>.md` in the working directory (for example
`reporting-platform.md`, `orders-cdc.md`), unless the user names another
path. Markdown is the source of truth. Sections and order: `document.md`.

**Check every engine feature the design relies on** — a function, a UDF
language, a connector or sink, a managed-service capability — against the
vendor's current docs for support and deprecation before the design depends
on it; the snapshot in these files is a starting point, not proof. Without
web access, put each in the doc's verify-before-building list (under Why, or
Open questions when Why has no verification part), not stated as settled.

**The doc stands alone.** Readers never see these files: state each rule's
reason in the doc itself, define any term you use, and never cite these
files or their snapshot as a source.

When the design is done, offer in your reply (never in the doc) to render it
as an HTML page for reading: `python3 render.py <doc>`, with `render.py` from
this skill's folder, writes the page beside it as `.html`. Run it only if the user
wants it; the Markdown stays the source of truth.
