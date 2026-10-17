# Development

## Layout

| Path | What it is |
|---|---|
| `skills/<name>/` | The skills as installed: a `SKILL.md` each, plus the area files it routes to. `designing-data-platforms` writes design documents; `building-data-pipelines` changes code. Neither reads the other's files |
| `eval/` | Agent evaluations: the shared protocol and one folder per skill (latest results, one file per scenario) |
| `skills/designing-data-platforms/render.py` | The optional HTML renderer the skill offers; tested by `tests/test_render.py` (`python3 -m unittest discover -s tests`; CI runs it) |
| `demo/` | One design document per scenario, as the agent wrote it, with its request. Agents never read it |
| `tools/build_demo.py` | Builds the demo site from `demo/` with `render.py` (a landing page, one page per example); the `pages` workflow publishes it |
| `tools/lint.py` | Manifest, frontmatter and private-terms checks (stdlib only; CI runs it) |

## After a change

- Run `python3 tools/lint.py` and `python3 -m unittest discover -s tests`.
- **Adding a skill:** add it to the `skills` list in `.claude-plugin/marketplace.json` and to the README.
- **Agent behaviour:** run the scenarios in `eval/<skill>/scenarios/` the change touches, per
  [`eval/README.md`](eval/README.md), and update the latest results in `eval/<skill>/README.md`. An edit not yet
  measured goes under that README's **Pending validation**.
- **Landscape refresh:** `designing-data-platforms` states its snapshot date. When tools or versions move, re-check
  its defaults and compatibility notes against current sources and update the date.
- **A release:** bump `version` in `.claude-plugin/marketplace.json` (both places).
- **The demo:** replace a document in `demo/` only with a graded run of the current skill, and check the page with
  `python3 tools/build_demo.py`.
