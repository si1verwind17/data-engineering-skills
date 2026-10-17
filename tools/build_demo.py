#!/usr/bin/env python3
"""Build the demo site: a landing page with one card per demo/<n>-<name>/
folder, and one page per folder — the request the design answers, the design
document the skill wrote, then the current-platform record when the run wrote
one — rendered with the skill's own render.py. The pages workflow publishes it.

    python3 tools/build_demo.py [-o _site]
"""
import argparse, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "designing-data-platforms"))
import render  # noqa: E402

LABELS = {
    "1-new-platform-aws": "New platform on AWS",
    "2-ingestion": "Ingestion",
    "3-change-to-a-lakehouse": "Change to a lakehouse",
    "4-sensitive-data-bigquery": "Sensitive data on BigQuery",
    "5-existing-platform": "Existing platform, from a repo",
}


def shows():
    """The demo README's "What it shows" column, by folder."""
    out = {}
    for line in (ROOT / "demo" / "README.md").read_text(encoding="utf-8").splitlines():
        if m := re.match(r"\|\s*\[`([^`]+)`\]\([^)]*\)\s*\|[^|]*\|\s*(.+?)\s*\|\s*$", line):
            out[m.group(1)] = m.group(2)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=Path, default=ROOT / "_site")
    args = ap.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    what, cards = shows(), []
    for folder in sorted(p for p in (ROOT / "demo").iterdir() if p.is_dir()):
        request = (folder / "request.md").read_text(encoding="utf-8").rstrip()
        design = next(p for p in sorted(folder.glob("*.md")) if p.name != "request.md")
        quote = "\n".join("> " + l if l else ">" for l in request.splitlines())
        after = []
        current = folder / "docs" / "data-platform" / "current-platform.md"
        if current.is_file():
            # the record of what already existed, written first, shown after the design it served
            body = current.read_text(encoding="utf-8").split("\n", 1)[1]
            after.append(("Current platform (recorded)", body.replace("\n## ", "\n### ")))
        b = render.brief(design.read_text(encoding="utf-8"), before=[("The request", quote)], after=after)
        name = f"{folder.name}.html"
        (args.output / name).write_text(render.page(b, home=("index.html", "All examples")), encoding="utf-8")
        first = re.match(r"(.+?[.!?])(\s|$)", render._plain(" ".join(request.split())))
        cards.append({"href": name, "label": LABELS.get(folder.name, folder.name),
                      "request": first.group(1) if first else request[:160], "shows": what.get(folder.name, "")})
    intro = ("Design documents `designing-data-platforms` wrote, one per evaluation scenario, as the agent wrote them. "
             "Each opens on its decision; the sidebar walks through the architecture, the pipeline, the build order, "
             "the reasons and the decisions it needs from you.")
    (args.output / "index.html").write_text(render.landing(cards, "Designing data platforms: examples", intro),
                                            encoding="utf-8")
    print(args.output / "index.html")


if __name__ == "__main__":
    sys.exit(main())
