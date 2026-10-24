# Evaluations: building-data-pipelines

Hands-on pipeline changes in small repos: the change must land in code with the checks that catch silent data loss,
and the reply must hand over honestly. The checks cover only what an agent without the skill missed: a probe run
without the skill dropped every check it already passed (period from the run instead of a watermark, keyed
delete-and-insert, a lookback for late commits, following the repo's design document, the large-column placeholder,
WAL cap and slot-lag alarm, version-guarded apply on LSN, tombstones, opt-in filtering, a suppression filter, saying
dbt was not run).

Runs get Bash as well as the usual tools, because the work includes running the repo's tests.

## Scenarios

| Scenario | What it tests |
|---|---|
| [1](scenarios/1-duplicating-poll.md) | an hourly poll that duplicates on retry, with a copy-pasted manual twin DAG |
| [2](scenarios/2-orders-cdc.md) | build step 2 of a CDC design the repo holds; variant A on Aurora |
| [3](scenarios/3-phone-pseudonyms.md) | pseudonyms and erasure in a dbt project on BigQuery that nothing can run |

## Pending validation

None.

## Latest results

Each scenario's latest run, Sonnet, graded by an independent judge. `Skill@` is the commit whose skill content was
evaluated.

| Scenario | Skill@ | Arm | Result | Notes |
|---|---|---|---|---|
| 1 | 206f0d9 | skill | 53/55 (5 runs) | every run fails the run on a bad row naming the keys, sets the failure email in code and adds no dead-letter table; captures deletes by key and tests a replayed delete; two replies ask who owns the alert instead of proposing one |
| 2 | 6d812bf | skill | 21/21 (3 runs); variant A 6/6 at 4e912f2 | CDC dead letters with LSN still built and tested; heartbeat written on the primary and slot loss on rebuild named in every run |
| 3 | 206f0d9 | skill | 24/27 (3 runs) | misses: alert owners left to the user (2), erasure closed on a check that reads only raw (1) |
| 1 | — | control | 10/33 (3 runs) | deletes left unhandled, no shared lock with the manual DAG, core table dropped and recreated, no alerts, no tests |
| 2 | — | control | 17/21 (3 runs) | heartbeat interval only on a read-only replica; slot loss on replica rebuild never named |
| 3 | — | control | 9/27 (3 runs) | salted SHA-256 with the key rendered into SQL, raw identifiers left in staging, no fail-safe in the deadline, no zero-match check |

At e6ce8de (before one fix round) the skill arm scored 20/33, 18/21 and 22/27: no dead-letter table, deletes compared
only over the run's own hour, the core table still dropped and recreated, alert owners left blank, tests that searched
the source text.

## Activation probe

Both skills installed as project skills, no preamble, the Skill tool allowed, one run per prompt, at e6ce8de.

| Prompts | Loaded |
|---|---|
| 4 hands-on (fix the duplicating job, implement a CDC build step, pseudonymize a column, add a dead-letter table) | `building-data-pipelines`, 4/4; no design document written |
| 4 design (new platform, ingestion design, sensitive-data governance, "what should we build?") | `designing-data-platforms`, 4/4 |
