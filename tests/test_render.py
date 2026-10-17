"""Tests for skills/designing-data-platforms/render.py (stdlib unittest; CI runs them)."""
import html.parser, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "designing-data-platforms" / "render.py"
sys.path.insert(0, str(SCRIPT.parent))
import render  # noqa: E402

VOID = {"meta", "br", "hr", "img", "input", "link"}


class Balance(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(tag)


def balanced(markup):
    p = Balance(); p.feed(markup)
    return not p.stack and not p.errors


SAMPLE = """# Data platform design

## 1. Questions and assumptions

| # | Question | Assumption |
|---|---|---:|
| 1 | Willing to **pay**? | `yes` \\| managed |

## 2. Data-flow diagram

```mermaid
flowchart LR
  A["Orders\\nPostgres"] --> B[Warehouse]
```

### 2.1 Notes

- one
  - nested `x*y`
- two

1. first
2. second

> **Why:** a quote.

---
"""


class Inline(unittest.TestCase):
    def test_bold_wraps_code(self):
        self.assertEqual(render.inline("**`a > b` loses rows.**"),
                         "<strong><code>a &gt; b</code> loses rows.</strong>")

    def test_code_is_untouched(self):
        self.assertEqual(render.inline("`x*y*z` and _b_"), "<code>x*y*z</code> and <em>b</em>")

    def test_snake_case_and_arithmetic_stay_plain(self):
        self.assertEqual(render.inline("snake_case_name"), "snake_case_name")
        self.assertEqual(render.inline("2 * 3 * 4"), "2 * 3 * 4")

    def test_link_and_escaping(self):
        self.assertEqual(render.inline("[a <b>](https://x.y/?q=1&r=2)"),
                         '<a href="https://x.y/?q=1&amp;r=2">a &lt;b&gt;</a>')

    def test_script_links_are_dropped(self):
        self.assertEqual(render.inline("[x](javascript:alert(1))"), "x)")


class Blocks(unittest.TestCase):
    def setUp(self):
        self.doc = render.render_doc(SAMPLE)

    def test_title_and_toc(self):
        self.assertEqual(self.doc.title, "Data platform design")
        self.assertEqual([(lv, t) for lv, _, t in self.doc.toc],
                         [(2, "1. Questions and assumptions"), (2, "2. Data-flow diagram"), (3, "2.1 Notes")])

    def test_table_cells_alignment_and_escaped_pipe(self):
        body = self.doc.body
        self.assertIn("<th>#</th><th>Question</th><th style=\"text-align:right\">Assumption</th>", body)
        self.assertIn("<td>Willing to <strong>pay</strong>?</td>", body)
        self.assertIn("<code>yes</code> | managed", body)

    def test_mermaid_keeps_source_and_line_breaks(self):
        self.assertIn('<pre class="mermaid">flowchart LR', self.doc.body)
        self.assertIn("Orders&lt;br&gt;Postgres", self.doc.body)

    def test_lists_quote_rule(self):
        body = self.doc.body
        self.assertIn("<ul><li>one<ul><li>nested <code>x*y</code></li></ul></li><li>two</li></ul>", body)
        self.assertIn("<ol><li>first</li><li>second</li></ol>", body)
        self.assertIn("<blockquote><p><strong>Why:</strong> a quote.</p></blockquote>", body)
        self.assertIn("<hr>", body)

    def test_mermaid_front_matter_verbatim(self):
        doc = render.render_doc("```mermaid\n---\nconfig:\n  layout: elk\n---\nflowchart LR\n  A --> B\n```")
        self.assertIn("---\nconfig:\n  layout: elk\n---\nflowchart LR", doc.body)
        self.assertNotIn("<hr>", doc.body)

    def test_html_in_source_is_escaped(self):
        doc = render.render_doc("<script>alert(1)</script>\n\n```\n<b>\n```")
        self.assertNotIn("<script>alert", doc.body)
        self.assertIn("&lt;b&gt;", doc.body)


DESIGN = """# Data platform design — shop analytics

## Decision

Build a small warehouse. Reporting moves to read replicas first.

## Architecture

```mermaid
---
config:
  layout: elk
---
flowchart LR
  subgraph existing[Existing systems]
    pg[("Shop database<br/><i>PostgreSQL</i>")]
  end
  rep[("Read replica<br/><i>PostgreSQL</i>")]
  job["Extract job<br/><i>dlt</i>"]
  wh[("Warehouse<br/><i>Redshift</i>")]
  user((Business user))
  pg -- replicate --> rep -- extract --> job -- load --> wh -- query --> user
  classDef new stroke-width:3px
  class rep new
```

| Component | What it does | Tool |
|---|---|---|
| Read replica | Serves reporting reads | PostgreSQL |
| Warehouse | Stores report tables | Redshift |

## Pipeline

```mermaid
flowchart LR
  s[("orders")] --> j(["Poll<br/><i>hourly</i>"]) --> r[("raw.orders")]
  j -.-> dl[("dead_letter")]
```

## Build steps

1. **Read replicas.** Point reports at them. Delivers: reports stop slowing production.
2. Warehouse and revenue model — delivers: finance's daily dashboard

## Why

### Tier

A replica alone cannot join sources. More text.

### Layer table

| Layer | Default |
|---|---|
| BI | Metabase |

## Questions and assumptions

1. **Willing to pay?** *Assumed: yes, managed services.* If not, self-hosted.

## Open questions

1. Who owns the alerts?

## Something else

Plain text.
"""


class Sections(unittest.TestCase):
    def test_split_on_level_two_outside_fences(self):
        title, pre, secs = render.sections("# T\n\nintro\n\n## A\n\n```\n## not a heading\n```\n\n## B\n\nb")
        self.assertEqual(title, "T")
        self.assertEqual([h for h, _ in secs], ["A", "B"])
        self.assertIn("## not a heading", "\n".join(secs[0][1]))
        self.assertEqual("".join(pre).strip(), "intro")

    def test_build_steps_both_forms(self):
        _, _, secs = render.sections(DESIGN)
        steps = render.build_steps(dict(secs)["Build steps"])
        self.assertEqual([s["title"] for s in steps], ["Read replicas.", "Warehouse and revenue model"])
        self.assertEqual(steps[0]["delivers"], "reports stop slowing production.")
        self.assertEqual(steps[1]["delivers"], "finance's daily dashboard")
        self.assertEqual(steps[0]["rest"], "Point reports at them.")

    def test_build_steps_none_without_a_list(self):
        self.assertIsNone(render.build_steps(["Some prose."]))

    def test_asks_with_assumption(self):
        a = render.asks(["1. **Willing to pay?** *Assumed: yes, managed services.* If not, self-hosted."])
        self.assertEqual(a, [{"q": "Willing to pay?", "assumed": "yes, managed services.", "rest": "If not, self-hosted."}])

    def test_asks_plain(self):
        self.assertEqual(render.asks(["1. Who owns the alerts?"]), [{"q": "Who owns the alerts?", "assumed": "", "rest": ""}])


class DiagramKinds(unittest.TestCase):
    SRC = "\n".join(["---", "config:", "  layout: elk", "---", "flowchart LR",
                      "  subgraph existing[Existing systems]", '    pg[("DB")]', "  end",
                      '  rep[("Replica")]', '  j(["Poll"])', '  t["Airflow"]', "  u((User))", '  dl[("dead_letter")]',
                      "  class rep new"])

    def test_kinds_from_shape_and_place(self):
        out = render.diagram_kinds(self.SRC)
        self.assertTrue(out.startswith("---\nconfig:\n  layout: elk\n---\nflowchart LR"))
        for line in ("class pg ksrc", "class rep kstore", "class j kjob", "class t ktool", "class u kperson", "class dl kwarn"):
            self.assertIn(line, out)
        self.assertIn("class rep new", out)
        self.assertIn("classDef kstore", out)

    def test_non_flowchart_untouched(self):
        self.assertEqual(render.diagram_kinds("sequenceDiagram\n  A->>B: hi"), "sequenceDiagram\n  A->>B: hi")


class Page(unittest.TestCase):
    def setUp(self):
        self.out = render.page(render.brief(DESIGN))

    def test_balanced_and_paged_by_default(self):
        self.assertTrue(balanced(self.out))
        self.assertIn('<body class="paged">', self.out)
        self.assertIn("Show everything", self.out)

    def test_one_page_per_section_with_contents(self):
        for sid in ("decision", "architecture", "pipeline", "build-steps", "why", "decisions-needed", "something-else"):
            self.assertIn(f'<section class="pg" id="{sid}"', self.out)
            self.assertIn(f'href="#{sid}"', self.out)
        self.assertNotIn('id="questions-and-assumptions"', self.out)

    def test_why_topics_collapsed_first_open(self):
        self.assertEqual(self.out.count('<details class="topic"'), 2)
        self.assertIn('<details class="topic" id="why-tier" open>', self.out)
        self.assertIn("A replica alone cannot join sources.", self.out)

    def test_architecture_components_for_the_inspector(self):
        self.assertIn('"name": "Read replica"', self.out)
        self.assertIn('"tool": "Redshift"', self.out)

    def test_roadmap_and_asks(self):
        self.assertIn('class="road"', self.out)
        self.assertIn("reports stop slowing production.", self.out)
        self.assertIn("Assumed", self.out)
        self.assertIn("Who owns the alerts?", self.out)

    def test_diagram_source_kept_with_kinds(self):
        self.assertIn("Shop database&lt;br/&gt;&lt;i&gt;PostgreSQL&lt;/i&gt;", self.out)
        self.assertIn("class pg ksrc", self.out)

    def test_elk_loaded_inside_try(self):
        self.assertIn("mermaid@12.1.0", self.out)
        self.assertIn("@mermaid-js/layout-elk@1.0.1", self.out)
        script = self.out[self.out.index('<script type="module">'):]
        self.assertLess(script.index("try{"), script.index("import("))

    def test_no_mermaid_script_without_diagrams(self):
        self.assertNotIn("mermaid@", render.page(render.brief("# T\n\n## Decision\n\ntext")))

    def test_any_document_renders(self):
        out = render.page(render.brief(SAMPLE))
        self.assertTrue(balanced(out))
        self.assertIn('id="1-questions-and-assumptions"', out)

    def test_extra_sections_before_and_after(self):
        out = render.page(render.brief(DESIGN, before=[("The request", "> Build it.")],
                                       after=[("Current platform", "## Components\n\ntext")]))
        self.assertLess(out.index('id="the-request"'), out.index('id="decision"'))
        self.assertLess(out.index('id="something-else"'), out.index('id="current-platform"'))
        self.assertTrue(balanced(out))

    def test_cli_writes_next_to_each_input(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.md", Path(d) / "b.md"
            a.write_text(DESIGN, encoding="utf-8"); b.write_text(SAMPLE, encoding="utf-8")
            subprocess.run([sys.executable, str(SCRIPT), str(a), str(b)], check=True, capture_output=True)
            for f in ("a.html", "b.html"):
                self.assertTrue(balanced((Path(d) / f).read_text(encoding="utf-8")))


class Landing(unittest.TestCase):
    def test_cards_link_to_pages(self):
        out = render.landing([{"href": "1.html", "label": "New platform", "request": "We want <analytics>.", "shows": "a new platform"}],
                             title="Demo", intro="Five designs.")
        self.assertTrue(balanced(out))
        self.assertIn('href="1.html"', out)
        self.assertIn("We want &lt;analytics&gt;.", out)


class Edges(unittest.TestCase):
    def test_document_without_sections_keeps_its_content(self):
        for md in ("# Title\n\nJust a paragraph.", "notes\n\n- a\n- b"):
            out = render.page(render.brief(md))
            self.assertTrue(balanced(out))
            self.assertEqual(out.count('<section class="pg"'), 1)
            self.assertIn("Just a paragraph." if "Title" in md else "<li>a</li>", out)

    def test_empty_document_still_has_a_page(self):
        self.assertEqual(render.page(render.brief("")).count('<section class="pg"'), 1)

    def test_component_json_round_trips(self):
        import json, re
        md = "# T\n\n## Architecture\n\n| Component | What it does | Tool |\n|---|---|---|\n| Q&A store | keeps <raw> rows | S3 & Athena |\n"
        out = render.page(render.brief(md))
        raw = re.search(r'<script type="application/json" id="brief-components">(.*?)</script>', out, re.S).group(1)
        self.assertNotIn("</", raw)
        self.assertEqual(json.loads(raw), [{"name": "Q&A store", "what": "keeps <raw> rows", "tool": "S3 & Athena"}])


class Minors(unittest.TestCase):
    def test_link_scheme_allowlist(self):
        self.assertNotIn("href", render.inline("[x](\x01javascript:alert(1))"))
        self.assertNotIn("href", render.inline("[x](vbscript:msgbox)"))
        self.assertIn('href="#decision"', render.inline("[x](#decision)"))
        self.assertIn('href="docs/a.md"', render.inline("[x](docs/a.md)"))
        self.assertIn('href="mailto:a@b.c"', render.inline("[x](mailto:a@b.c)"))

    def test_emphasis_never_touches_an_href(self):
        out = render.inline("[docs _here_](https://example.com/_private_/x) and _this_")
        self.assertIn('href="https://example.com/_private_/x"', out)
        self.assertIn("<em>here</em>", out)
        self.assertIn("<em>this</em>", out)

    def test_resources_boundary_is_not_a_source(self):
        out = render.diagram_kinds("flowchart LR\n  subgraph aws[AWS resources]\n    a[(\"S3\")]\n  end\n  subgraph src[Sources]\n    b[(\"DB\")]\n  end")
        self.assertIn("class a kstore", out)
        self.assertIn("class b ksrc", out)

    def test_build_steps_with_code_render_as_written(self):
        lines = ["1. First — delivers: x", "", "   ```sql", "   select 1", "   ```", "2. Second — delivers: y"]
        self.assertIsNone(render.build_steps(lines))
        self.assertIsNone(render.build_steps(["1. First", "   - nested", "2. Second"]))


if __name__ == "__main__":
    unittest.main()
