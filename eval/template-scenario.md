# Scenario <n>: <short name>

<One sentence: what this scenario tests.>

**Fixture:** <none, or the setup the run needs in <workdir>>.

**Prompt** (verbatim, after the arm's preamble from [`eval/README.md`](../../README.md)):

> <the full task prompt — realistic, slightly underspecified where the skill should make the agent ask or decide,
> with any tempting pressure included; "You are working non-interactively: …" when it should not stop to ask>

**Checks** (PASS/FAIL per run):

1. **<name>**: <an observable property of the output — one per rule the scenario exercises>.
2. …

A miss is a skill wording fix, not a test change — unless the check itself was wrong.
