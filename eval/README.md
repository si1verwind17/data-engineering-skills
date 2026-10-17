# Evaluations: data-engineering skills

One folder per skill: its `README.md` (what the benchmark measures, the scenario list, pending validation, the
latest result per scenario) and `scenarios/`, one file per scenario with its prompt and checks. Fixtures a scenario
copies into its workdir live in [`fixtures/`](fixtures/). Start a new scenario
from [`template-scenario.md`](template-scenario.md).

A single passing run proves a skill *can* work; only repetition proves it works *reliably*, and only a control arm
proves it changes anything.

| Skill | Scenarios |
|---|---|
| [`designing-data-platforms`](designing-data-platforms/README.md) | new platform on AWS, ingestion, change to a running lakehouse, sensitive data on BigQuery, existing platform from a repo |
| [`building-data-pipelines`](building-data-pipelines/README.md) | a poll job that duplicates on retry, CDC from a design document, pseudonyms and erasure in a dbt project |

## Protocol

- **Probe first.** Before writing a check, run the scenario without the skill. A check the control arm already
  passes 3/3 is dead weight: drop it, or the rule behind it.
- **Two arms.** Control: a fresh agent gets the scenario with the skill NOT loaded. Skill arm: identical but with the
  skill loaded. Control prompts MUST explicitly forbid loading any skill or convention guide from the environment,
  because agent harnesses auto-discover skills and a control that silently reads the skill under test measures
  nothing. Check that control outputs don't echo the skill's distinctive vocabulary before trusting the arm.
- **Preambles.** Skill arm: "Before starting, read `<skills>/<skill>/SKILL.md` and follow it as authoritative for
  how you work." Control arm: "Do not read, load, or consult any skill files, SKILL.md files, AGENTS.md, or
  convention guides in this environment — work from your own knowledge only." Both arms then append: "Work
  non-interactively: if you would ask the user something, record the exact question prominently, state your
  assumption, and proceed." Then the scenario's prompt, verbatim, with `<workdir>` filled in. Runs read a frozen copy
  of `skills/` at the commit under test.
- **Reps.** 3 per scenario by default, 5 when a result is close; single runs lie.
- **Independent grading.** A fresh judge (agent or human, on a model at least as strong as the run's) grades each run
  against the checks, blind to the arm, never the session that authored the skill. Judges verify what they can: look
  versions and engine capabilities up rather than trusting either arm.
- **Tools.** Runs get Read, Write, Edit, Glob, Grep, WebSearch and WebFetch; `building-data-pipelines` runs also get
  Bash, because its work includes running the repo's tests.
- **Headless runs.** Pass `--disallowedTools ScheduleWakeup`: a pending fallback wakeup keeps `claude -p` alive after
  its final reply. Set a timeout anyway.
- **When to run.** At creation (both arms); after any substantive edit (skill arm; control too if checks changed);
  when the underlying model changes.
- **Results.** Each skill's README keeps the latest result per scenario; git keeps the history. A substantive edit not
  yet measured goes under **Pending validation** with the commit and the scenario that will validate it; the run that
  validates it deletes the entry.
- **Real misses become checks.** When a skill-loaded agent gets something wrong in real use, add that case as a
  failing check first; the skill edit must flip it.

`Skill@` is the short hash of the commit whose skill content was tested. These hashes refer to the skill's
development history, which was squashed into this repository's first commit, so they do not resolve here; a result
recorded before a later edit to its skill stands until that edit's **Pending validation** entry is measured.
