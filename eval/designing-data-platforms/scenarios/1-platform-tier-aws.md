# Scenario 1: Platform tier selection (AWS)

A new platform on AWS: the tier and one tool per layer, replica first, a verified stack, the deliverable structure.

**Fixture:** none; the run writes into an empty `<workdir>`.

**Prompt** (verbatim, after the arm's preamble from [`eval/README.md`](../../README.md)):

> We're a ~150-person e-commerce company on AWS. We want analytics. Sources:
> three PostgreSQL service databases (~200 GB total, growing ~10%/year), one
> MongoDB database (~30 GB), and product click events (~5M/day) currently
> going to a log bucket. Finance wants daily revenue dashboards; ops
> complains reporting queries slow down the production databases; product
> wants a "real-time" funnel dashboard. The data team is two engineers. Our
> CTO is excited about building a modern lakehouse with Spark, Flink and
> Kafka. Design the data platform: components per layer, what you'd build
> first, and why. Write your design to <workdir>/platform-design.md.

**Checks** (PASS/FAIL per run):

1. Records willingness to pay (managed/commercial vs open-source self-hosted)
   AND who operates the platform as explicit questions or assumptions that
   drive tool choices.
2. Weighs at least one simpler tier (replica, single Postgres or single
   warehouse without a lake) against the chosen one before committing.
3. Offers the cheapest fix for "reports slow down prod" (read replica)
   before any pipeline exists.
4. Exactly one choice per layer (no "X or Y" left open), each with a named
   alternative and the condition that would switch to it ("—" accepted
   where no real alternative exists, e.g. object storage itself).
5. Includes a compatibility check of the chosen components (format version
   × engines × catalog/managed services) with sources and dates, or — when
   it could not verify — a verify-before-building list naming each
   combination to confirm and where (not a table of "unverified" cells).
6. Deliverable order: Decision, Architecture, Pipeline, Build steps, then
   Why holding the tier weighed, layer table, verification and source
   inventory, then questions and assumptions and open questions.
7. **Top of document**: opens with a plain-words Decision (what gets built, what does not), then the Architecture diagram — nothing (questions, tier essay, tables) before them.
8. **Architecture rules**: the diagram reads left to right from sources to users; every data arrow points the way data moves and is labelled with the action; boxes give tool and role; boundaries show where things run, drawn only where the hosting is stated.
9. **Pipeline**: a pipeline diagram of jobs and tables (jobs with how often they run, tables by layer, failures to a dead-letter table where a source has one), or one sentence where a source's whole path is a single job the architecture already shows.
10. **Build steps**: numbered, design level (no code or commands), each saying what it delivers.
11. **No process narration**: the document never describes how it was produced ("non-interactive", "this run", "taken as given") or mentions the skill or its files.

A miss is a skill wording fix, not a test change — unless the check itself was wrong.
