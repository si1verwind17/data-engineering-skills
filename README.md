# data-engineering-skills

Agent skills for data engineering. Each skill is a plain-Markdown `SKILL.md` in the open
[Agent Skills](https://agentskills.io) format, usable from Claude Code, GitHub Copilot, Cursor, Codex, Antigravity CLI
and any other agent that reads it.

Strong models already know general data-engineering practice: medallion layers, watermarks, idempotent reruns,
SCD2, compaction, late data. These skills hold only what agents without them got wrong in testing:

- **A decision, not a menu** (design). The smallest tier that fits is weighed first (a read replica before any
  pipeline), then one tool per layer, each with its alternative and the condition that would switch to it, and a
  check that the chosen versions work together.
- **Ingestion that survives failure** (build). Dead letters that keep the payload and source position, redrive
  guarded by source version so old data never overwrites new, deletes kept as tombstones, the CDC traps that bite in
  production, batch runs that can be rerun for any period, and backfills that run alongside live capture.
- **Sensitive data handled for real** (both). Card data kept out of scope, keyed pseudonyms instead of
  brute-forceable hashes, access enforced in the engine rather than the BI tool, and an erasure job that reaches
  every layer, copy and backup window, with a suppression list so a replay cannot bring an erased person back.
- **Checks that don't cost a fortune** (build). Every change gets the checks for what it guarantees — nothing lost,
  failures visible, deletes kept, data fresh — reading only what the run loaded, never the whole table.

Each request only gets the parts it needs: an ingestion question gets an ingestion design, not a full platform
proposal. Results per scenario, with and without the skill, are in [`eval/`](eval/README.md).

## Demo

**[Open the demo page](https://si1verwind17.github.io/data-engineering-skills/)**: five design documents
`designing-data-platforms` wrote, one per scenario (a new platform, ingestion, a change to a running lakehouse,
sensitive data, an existing platform read from a repo), each under the request it answers. The documents themselves
are in [`demo/`](demo/). `building-data-pipelines` writes code, not documents, so it has no page; its scenarios and
results are in [`eval/`](eval/building-data-pipelines/README.md).

## Install

**Claude Code**

```
/plugin marketplace add si1verwind17/data-engineering-skills
/plugin install data-engineering@data-engineering-skills
```

**GitHub Copilot, Cursor, Codex, Antigravity CLI and others,** via GitHub CLI:

```
gh skill install si1verwind17/data-engineering-skills
```

**Anything else:** copy the `skills/<name>/` directories into your agent's skills folder.

## Skills

- [`designing-data-platforms`](skills/designing-data-platforms/SKILL.md): designs or reviews an analytics data
  platform, from a reporting replica to a lakehouse: tier and per-layer tool choice, batch and CDC ingestion with
  dead-letter handling, serving and reverse ETL, and PII, PCI or health data with erasure. Each design is one
  document under `docs/data-platform/` that opens with the decision and the architecture diagram, then the pipeline
  and the build steps, with the reasons after; an existing platform is recorded once in `docs/data-platform/current-platform.md`. When it is
  done, it offers to render the document as a page for reading — one section at a time, the architecture diagram
  linked to its components, the reasons collapsed by topic (`render.py` in the skill folder, Python 3, nothing to
  install).
- [`building-data-pipelines`](skills/building-data-pipelines/SKILL.md): changes pipeline code and config in your
  repo: ingestion jobs, CDC connectors, dead letters and redrive, deletes, reruns and backfills, reverse-ETL loads,
  pseudonyms and erasure jobs. It reads a design document when there is one, adds the checks that catch silent data
  loss, and hands over what it could not run. No documents.

## Use

Ask in plain words, for example:

> We're on AWS with three Postgres databases and click events in S3. Design our analytics platform.

> Our hourly job double-counted orders after a retry. Redesign ingestion for these sources.

> Our hourly orders job duplicated rows after a retry, and we need to backfill last Tuesday. Fix it.

> Customer service needs an order lookup and merchants need daily sales in our app. Design it on our lakehouse.

> Patient and payment data are coming into BigQuery. How should we govern it and handle erasure requests?

> Review this data platform design for gaps.

## License

MIT, see [`LICENSE`](LICENSE).
