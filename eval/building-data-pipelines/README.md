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

- 6d812bf: dead letters only where the source cannot be re-read, a stream blocks, or a high-volume load expects bad
  records; a rerunnable batch fails the run. Checks 7 and 9 of scenario 1 changed. Validates: scenario 1 skill arm
  (5 runs) and control (3 runs, checks changed); scenarios 2 and 3 skill arm.

## Latest results

Each scenario's latest run, Sonnet, graded by an independent judge. `Skill@` is the commit whose skill content was
evaluated.

| Scenario | Skill@ | Arm | Result | Notes |
|---|---|---|---|---|
| 1 | a68c38e | skill | 55/55 (5 runs) | every run captures deletes by key, dead-letters with source position, and tests a replayed delete; at 4e912f2, before the Scope sentence on data-loss gaps, two of three runs deferred deletes (22/33) |
| 2 | a68c38e | skill | 21/21 (3 runs); variant A 6/6 at 4e912f2 | heartbeat written on the primary and slot loss on rebuild named in every run |
| 3 | a68c38e | skill | 27/27 (3 runs) | erasure verified once per request, joined to the request table, in every run |
| 1 | — | control | 11/33 (3 runs) | no dead letters, deletes left unhandled, no shared lock with the manual DAG, core table dropped and recreated, no tests |
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
