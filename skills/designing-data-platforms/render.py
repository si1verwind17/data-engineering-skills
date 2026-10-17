#!/usr/bin/env python3
"""Render a data-platform design document (Markdown) as a page to read.

    python3 render.py docs/data-platform/reporting-platform.md [more.md ...] [-o page.html]

Each input becomes its own page beside it, with an .html suffix. The Markdown
stays the source of truth: the page is a reading view, nothing reads it back.

The page follows the document's sections: one page per `##` section with a
contents sidebar, one at a time by default. Known sections get their own view:
the Architecture diagram with its component table as a panel, Build steps as a
roadmap, Why as collapsed topics, Questions and Open questions together as
"Decisions needed". Any other section renders as written. Mermaid blocks become
diagrams through Mermaid and its ELK layout, loaded from a CDN, coloured by the
shape of each box; offline, each diagram shows as its source. Python 3 standard
library only.
"""
import argparse, html, json, re, sys
from pathlib import Path

MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@12.1.0/dist/mermaid.esm.min.mjs"
ELK_URL = "https://cdn.jsdelivr.net/npm/@mermaid-js/layout-elk@1.0.1/dist/mermaid-layout-elk.esm.min.mjs"

# ---------------------------------------------------------------- inline


def inline(text):
    """Inline Markdown to HTML. Code spans and finished links become placeholders,
    so nothing inside them is touched (no emphasis inside a URL) while bold and
    links can still wrap around them."""
    held = []

    def hold(markup):
        held.append(markup)
        return f"\x00{len(held) - 1}\x00"
    text = re.sub(r"(`+)(.+?)\1", lambda m: hold(f"<code>{html.escape(m.group(2).strip())}</code>"), text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>])", lambda m: f"&#{ord(m.group(1))};", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: hold(_link(m.group(1), m.group(2))), text)
    text = _emphasis(text)
    while "\x00" in text:
        text = re.sub(r"\x00(\d+)\x00", lambda m: held[int(m.group(1))], text)
    return text


def _emphasis(text):
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", text)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])|(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)",
                  lambda m: f"<em>{m.group(1) or m.group(2)}</em>", text)


def _link(label, url):
    # the URL is already HTML-escaped with the text; only quotes still need it.
    # Only web, mail, in-page and relative links: any other scheme (javascript:, data:, ...) keeps just its text,
    # judged after dropping the control characters and spaces a browser would ignore
    bare = re.sub(r"[\x00-\x20]", "", html.unescape(url))
    if (m := re.match(r"([A-Za-z][\w+.-]*):", bare)) and m.group(1).lower() not in ("http", "https", "mailto"):
        return _emphasis(label)
    return f'<a href="{url.replace(chr(34), "&quot;")}">{_emphasis(label)}</a>'


# ---------------------------------------------------------------- blocks

LIST_RE = re.compile(r"^( *)([-*+]|\d+[.)])\s+(.*)$")
FENCE_RE = re.compile(r"^ *(```+|~~~+)\s*([\w-]*)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def split_row(line):
    """Cells of one pipe-table row; pipes inside code spans or escaped stay in the cell."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells, cur, in_code, i = [], "", False, 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur += "|"; i += 2; continue
        if c == "`":
            in_code = not in_code
        if c == "|" and not in_code:
            cells.append(cur.strip()); cur = ""
        else:
            cur += c
        i += 1
    cells.append(cur.strip())
    return cells


class Doc:
    """One rendered document: its HTML, title and table of contents."""

    def __init__(self, prefix):
        self.prefix, self.title, self.toc, self.ids = prefix, None, [], set()

    def slug(self, text):
        base = re.sub(r"[^\w\s-]", "", re.sub(r"<[^>]+>", "", text)).strip().lower()
        base = self.prefix + (re.sub(r"[\s_]+", "-", base) or "section")
        s, n = base, 2
        while s in self.ids:
            s, n = f"{base}-{n}", n + 1
        self.ids.add(s)
        return s

    def blocks(self, lines):
        out, i = [], 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1; continue
            if m := FENCE_RE.match(line):
                fence, lang, body, i = m.group(1), m.group(2).lower(), [], i + 1
                while i < len(lines) and not lines[i].strip().startswith(fence):
                    body.append(lines[i]); i += 1
                i += 1
                src = html.escape("\n".join(body))
                if lang == "mermaid":
                    src = html.escape(diagram_kinds("\n".join(body)))
                    src = src.replace("\\n", "&lt;br&gt;")   # a literal \n in a label is meant as a line break
                    out.append(f'<figure class="diagram"><pre class="mermaid">{src}</pre></figure>')
                else:
                    cls = f' class="lang-{lang}"' if lang else ""
                    out.append(f"<pre><code{cls}>{src}</code></pre>")
                continue
            if m := HEADING_RE.match(line):
                level, text = len(m.group(1)), inline(m.group(2))
                if level == 1 and self.title is None:
                    self.title = re.sub(r"<[^>]+>", "", text)
                    out.append(f'<h1 class="doc-title">{text}</h1>')
                else:
                    sid = self.slug(text)
                    if level in (2, 3):
                        self.toc.append((level, sid, re.sub(r"<[^>]+>", "", text)))
                    out.append(f'<h{level} id="{sid}">{text}</h{level}>')
                i += 1; continue
            if re.match(r"^ {0,3}([-*_])( *\1){2,} *$", line):
                out.append("<hr>"); i += 1; continue
            if "|" in line and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1]):
                head, aligns = split_row(line), []
                for c in split_row(lines[i + 1]):
                    aligns.append("center" if c.startswith(":") and c.endswith(":")
                                  else "right" if c.endswith(":") else "")
                i += 2
                rows = []
                while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                    rows.append(split_row(lines[i])); i += 1

                def cell(tag, j, txt):
                    a = aligns[j] if j < len(aligns) else ""
                    style = ' style="text-align:%s"' % a if a else ""
                    return f"<{tag}{style}>{inline(txt)}</{tag}>"
                th = "".join(cell("th", j, c) for j, c in enumerate(head))
                body = "".join("<tr>" + "".join(cell("td", j, r[j] if j < len(r) else "")
                                                for j in range(len(head))) + "</tr>" for r in rows)
                out.append(f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead>'
                           f"<tbody>{body}</tbody></table></div>")
                continue
            if line.lstrip().startswith(">"):
                quote = []
                while i < len(lines) and lines[i].lstrip().startswith(">"):
                    quote.append(re.sub(r"^\s*> ?", "", lines[i])); i += 1
                out.append(f"<blockquote>{''.join(self.blocks(quote))}</blockquote>")
                continue
            if LIST_RE.match(line):
                html_list, i = self.list_block(lines, i)
                out.append(html_list); continue
            para = []
            while i < len(lines) and lines[i].strip() and not self.starts_block(lines, i):
                para.append(lines[i].strip()); i += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
        return out

    def starts_block(self, lines, i):
        line = lines[i]
        return bool(FENCE_RE.match(line) or HEADING_RE.match(line) or LIST_RE.match(line)
                    or line.lstrip().startswith(">")
                    or ("|" in line and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1])))

    def list_block(self, lines, i):
        first = LIST_RE.match(lines[i])
        base, ordered = len(first.group(1)), first.group(2)[0].isdigit()
        start = int(first.group(2)[:-1]) if ordered else 1
        items = []
        while i < len(lines):
            m = LIST_RE.match(lines[i])
            if not m or len(m.group(1)) != base or m.group(2)[0].isdigit() != ordered:
                break
            offset = len(lines[i]) - len(m.group(3))
            body, i = [m.group(3)], i + 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip():
                    # a blank line ends the item unless indented content follows
                    if i + 1 < len(lines) and lines[i + 1].strip() and \
                            len(lines[i + 1]) - len(lines[i + 1].lstrip()) > base:
                        body.append(""); i += 1; continue
                    break
                indent = len(nxt) - len(nxt.lstrip())
                lm = LIST_RE.match(nxt)
                if lm and len(lm.group(1)) <= base:
                    break
                if indent <= base and self.starts_block(lines, i):
                    break
                body.append(nxt[min(indent, offset):] if indent > base else nxt.strip())
                i += 1
            items.append(body)
            while i < len(lines) and not lines[i].strip() and i + 1 < len(lines) and \
                    (m2 := LIST_RE.match(lines[i + 1])) and len(m2.group(1)) == base:
                i += 1
        lis = []
        for body in items:
            parts = self.blocks(body)
            if parts and parts[0].startswith("<p>"):
                parts[0] = parts[0][3:-4]   # tight item: first paragraph without <p>
            lis.append(f"<li>{''.join(parts)}</li>")
        tag = "ol" if ordered else "ul"
        attr = f' start="{start}"' if ordered and start != 1 else ""
        return f"<{tag}{attr}>{''.join(lis)}</{tag}>", i


def render_doc(markdown, prefix=""):
    doc = Doc(prefix)
    doc.body = "".join(doc.blocks(markdown.replace("\t", "    ").splitlines()))
    return doc


# ---------------------------------------------------------------- diagram kinds

NODE_RE = re.compile(r"(?<![\w-])([A-Za-z_][\w-]*)\s*(\[\(|\(\[|\(\(|\[\[|\[|\(|\{)")
KEYWORDS = {"subgraph", "end", "classDef", "class", "style", "click", "linkStyle", "direction",
            "flowchart", "graph"}
KIND_CLASSES = ("ksrc", "kstore", "kjob", "ktool", "kperson", "kwarn")


def diagram_kinds(src):
    """Tag each flowchart node with a kind class from its shape and place, so the
    page can colour it: existing sources (inside an existing-systems or sources
    boundary), storage (cylinder), jobs (rounded), people (circle), dead letters
    and quarantine, and every other box a tool. The source is otherwise kept."""
    lines = src.splitlines()
    body = [l.strip() for l in lines]
    start = next((i for i, l in enumerate(body) if re.match(r"(flowchart|graph)\b", l)), None)
    if start is None:
        return src
    kinds, stack = {}, []
    for raw in body[start + 1:]:
        line = re.sub(r'"[^"]*"', '""', raw)
        if m := re.match(r"subgraph\s+([\w-]+)?\s*(?:\[(.*)\])?", line):
            label = (m.group(1) or "") + " " + re.sub(r'"', "", raw)
            stack.append(bool(re.search(r"(?i)\b(existing|sources?)\b", label)))
            continue
        if line == "end":
            if stack:
                stack.pop()
            continue
        if not line or line.split()[0] in KEYWORDS:
            continue
        for m in NODE_RE.finditer(line):
            nid, shape = m.group(1), m.group(2)
            if nid in kinds or nid in KEYWORDS:
                continue
            label = raw[m.start():m.start() + 120]
            if stack and stack[-1]:
                kinds[nid] = "ksrc"
            elif re.search(r"(?i)dead.?letter|quarantine", nid + " " + label) or nid in ("dl", "dlq"):
                kinds[nid] = "kwarn"
            else:
                kinds[nid] = {"[(": "kstore", "([": "kjob", "((": "kperson"}.get(shape, "ktool")
    if not kinds:
        return src
    extra = [f"  classDef {k} stroke-dasharray:0" for k in KIND_CLASSES]
    by = {}
    for nid, k in kinds.items():
        by.setdefault(k, []).append(nid)
    extra += [f"  class {','.join(ids)} {k}" for k, ids in by.items()]
    # kind classes first, so a document's own class lines (new) still apply after them
    first_class = next((i for i, l in enumerate(lines) if i > start and re.match(r"\s*(classDef|class)\s", l)), len(lines))
    return "\n".join(lines[:first_class] + extra + lines[first_class:])


# ---------------------------------------------------------------- sections

def sections(markdown):
    """(title, preamble lines, [(heading, lines)]) split on level-2 headings
    outside code fences."""
    title, pre, secs, cur, fence = None, [], [], None, None
    for line in markdown.replace("\t", "    ").splitlines():
        if m := FENCE_RE.match(line):
            if fence is None:
                fence = m.group(1)
            elif line.strip().startswith(fence):
                fence = None
        elif fence is None:
            if title is None and (m := re.match(r"^#\s+(.*?)\s*#*\s*$", line)) and not secs and cur is None:
                title = re.sub(r"<[^>]+>", "", inline(m.group(1))); continue
            if m := re.match(r"^##\s+(.*?)\s*#*\s*$", line):
                cur = (m.group(1), []); secs.append(cur); continue
        (cur[1] if cur else pre).append(line)
    return title, pre, secs


def list_items(lines):
    """Top-level list items as single lines of Markdown (continuations joined)."""
    items, base = [], None
    for line in lines:
        m = LIST_RE.match(line)
        if m and (base is None or len(m.group(1)) <= base):
            base = len(m.group(1)); items.append(m.group(3).strip())
        elif items and line.strip():
            items[-1] += " " + line.strip()
    return items


def build_steps(lines):
    """Roadmap steps from the Build steps list: title, what it delivers, the rest."""
    items = list_items(lines)
    # a step holding code or a nested list renders as written, not flattened into one line
    if not items or any(FENCE_RE.match(l) or (LIST_RE.match(l) and LIST_RE.match(l).group(1)) for l in lines):
        return None
    steps = []
    for text in items:
        delivers, before = "", text
        if m := re.search(r"(?i)\s*(?:[—–-]\s*)?delivers:\s*(.+)$", text):
            delivers, before = m.group(1).strip(), text[:m.start()].strip()
        if m := re.match(r"\*\*(.+?)\*\*\s*(.*)$", before):
            title, rest = m.group(1), m.group(2)
        else:
            title, rest = before, ""
        steps.append({"title": inline(title), "delivers": inline(delivers), "rest": inline(rest)})
    return steps


def asks(lines):
    """Questions as {q, assumed, rest} in Markdown: the bold lead or the text up
    to the first question mark, an italic "Assumed:" part, and what follows."""
    out = []
    for text in list_items(lines):
        if m := re.match(r"\*\*(.+?)\*\*\s*(.*)$", text):
            q, rest = m.group(1), m.group(2)
        elif "?" in text:
            q, rest = text[:text.index("?") + 1], text[text.index("?") + 1:]
        else:
            q, rest = text, ""
        assumed = ""
        if m := re.search(r"[*_]Assumed:?\s*(.+?)[*_](?:\s|$)", rest):
            assumed, rest = m.group(1).strip(), (rest[:m.start()] + rest[m.end():])
        out.append({"q": q.strip(), "assumed": assumed, "rest": rest.strip()})
    return out


def _plain(markdown):
    return html.unescape(re.sub(r"<[^>]+>", "", inline(markdown)))


def _first_sentence(lines):
    para = []
    for l in lines:
        if not l.strip():
            if para:
                break
            continue
        if FENCE_RE.match(l) or l.lstrip().startswith(("|", "#", ">")) or LIST_RE.match(l):
            if para:
                break
            continue
        para.append(l.strip())
    text = _plain(" ".join(para))
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    text = m.group(1) if m else text
    return text if len(text) <= 200 else text[:197].rsplit(" ", 1)[0] + "…"


class Brief:
    """A document as pages: (id, label, html, sub-links), plus its components."""

    def __init__(self, title):
        self.title, self.pages, self.components, self.doc = title, [], [], Doc("")


PLUS = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 4v12M4 10h12"/></svg>'


def brief(markdown, before=(), after=()):
    """Pages for one document; `before` and `after` are extra (heading, Markdown)
    sections, such as the request a design answers."""
    title, pre, secs = sections(markdown)
    b = Brief(title or "Data platform design")
    d = b.doc
    named = {h.strip().lower(): (h, l) for h, l in secs}
    asks_done = False
    order = [(h, m.replace("\t", "    ").splitlines()) for h, m in before] + secs + \
            [(h, m.replace("\t", "    ").splitlines()) for h, m in after]
    for n, (heading, lines) in enumerate(order):
        key = heading.strip().lower()
        if n == len(before) and pre and any(l.strip() for l in pre):
            lines = pre + [""] + lines
        if key in ("questions and assumptions", "open questions"):
            if asks_done:
                continue
            asks_done = True
            b.pages.append(_asks_page(d, named))
            continue
        sid = d.slug(heading)
        subs = []
        if key == "architecture":
            body = _architecture(d, lines, b)
        elif key == "build steps" and (steps := build_steps(lines)):
            body = _roadmap(steps)
        elif key == "why":
            body, subs = _topics(d, lines, sid)
        else:
            body = "".join(d.blocks(lines))
        b.pages.append((sid, _plain(heading), body, subs))
    if not b.pages:
        # a document without level-2 sections is one page, as written
        b.pages.append((d.slug("document"), b.title if title else "Document", "".join(d.blocks(pre)), []))
    return b


def _architecture(d, lines, b):
    out, rest, i = [], [], 0
    table = None
    while i < len(lines):
        if table is None and "|" in lines[i] and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1]) \
                and "component" in lines[i].lower():
            head = [c.lower() for c in split_row(lines[i])]
            j = i + 2
            rows = []
            while j < len(lines) and lines[j].strip() and "|" in lines[j]:
                rows.append(split_row(lines[j])); j += 1
            table = lines[i:j]
            col = lambda r, *names: next((r[k] for k, h in enumerate(head) if k < len(r) and any(n in h for n in names)), "")
            b.components = [{"name": _plain(col(r, "component")), "what": _plain(col(r, "what", "does")),
                             "tool": _plain(col(r, "tool"))} for r in rows]
            i = j; continue
        rest.append(lines[i]); i += 1
    body = "".join(d.blocks(rest))
    body = body.replace('<figure class="diagram">', '<figure class="diagram arch">', 1)
    if b.components:
        body += ('<div class="inspector" id="brief-inspector" aria-live="polite"></div>'
                 f'<details class="topic comp-table"><summary><div><h3>All components as a table</h3></div>{PLUS}</summary>'
                 f'<div class="tbody">{"".join(d.blocks(table))}</div></details>')
    return body


def _roadmap(steps):
    li = "".join(
        f'<li class="step"><div class="tick"><b>{n}</b></div><h3>{s["title"]}</h3>'
        + (f'<p class="del">{s["delivers"]}</p>' if s["delivers"] else "")
        + (f'<p class="what">{s["rest"]}</p>' if s["rest"] else "") + "</li>"
        for n, s in enumerate(steps, 1))
    return f'<ol class="road">{li}</ol>'


def _topics(d, lines, sid):
    intro, topics, cur = [], [], None
    for line in lines:
        if m := re.match(r"^###\s+(.*?)\s*#*\s*$", line):
            cur = (m.group(1), []); topics.append(cur); continue
        (cur[1] if cur else intro).append(line)
    out, subs = ["".join(d.blocks(intro))], []
    for n, (h, body) in enumerate(topics):
        tid = d.slug(f"{sid} {h}")
        subs.append((tid, _plain(h)))
        summary = _first_sentence(body)
        out.append(f'<details class="topic" id="{tid}"{" open" if n == 0 else ""}><summary><div><h3>{inline(h)}</h3>'
                   + (f"<p>{html.escape(summary)}</p>" if summary else "")
                   + f'</div>{PLUS}</summary><div class="tbody">{"".join(d.blocks(body))}</div></details>')
    return "".join(out), subs


def _asks_page(d, named):
    cols = []
    for key, label in (("questions and assumptions", "Asked, with the assumption used"),
                       ("open questions", "Still open")):
        if key not in named:
            continue
        lines = named[key][1]
        items = asks(lines)
        if not items:
            cols.append(f'<div><h3 class="colh">{label}</h3>{"".join(d.blocks(lines))}</div>'); continue
        rows = "".join(
            f'<div class="ask"><p class="q">{inline(a["q"])}</p>'
            + (f'<p class="assume"><span>Assumed</span>{inline(a["assumed"])}</p>' if a["assumed"] else "")
            + (f'<p class="then">{inline(a["rest"])}</p>' if a["rest"] else "") + "</div>"
            for a in items)
        cols.append(f'<div><h3 class="colh">{label}</h3>{rows}</div>')
    return (d.slug("Decisions needed"), "Decisions needed", f'<div class="asks">{"".join(cols)}</div>', [])


# ---------------------------------------------------------------- page

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700'
         '&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">')

TOKENS_DARK = """--paper:#14181c;--plate:#1a1f24;--ink:#e7e9ea;--ink-2:#b4bcc3;--ink-3:#8c959d;--rule:#2c333a;
--rule-2:#232a30;--accent:#4fc1b2;--accent-soft:#173b37;--accent-ink:#8ee0d4;--src:#94a3b8;--src-fill:#222a33;
--store:#e0a63c;--store-fill:#2e2617;--job:#6aa8ec;--job-fill:#1a2838;--tool:#a99bf0;--tool-fill:#252240;
--person:#e48ab3;--person-fill:#36202b;--warn:#f08a68;--warn-fill:#3a221a;--code:#232a30;
--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 28px -14px rgba(0,0,0,.6);color-scheme:dark"""

CSS = """
:root{--paper:#f5f3ee;--plate:#fbfaf7;--ink:#1b2127;--ink-2:#4a535c;--ink-3:#6b737b;--rule:#dcd8cf;
--rule-2:#e8e5de;--accent:#0d6b62;--accent-soft:#d6ece8;--accent-ink:#0a4f48;--src:#64748b;--src-fill:#e9edf2;
--store:#a16207;--store-fill:#f8edd7;--job:#1d5fa8;--job-fill:#e1ecf8;--tool:#5b4bb3;--tool-fill:#ebe7f8;
--person:#9d3f6b;--person-fill:#f6e3ec;--warn:#b4401f;--warn-fill:#fbe4dc;--code:#ecebe5;
--shadow:0 1px 2px rgba(27,33,39,.06),0 8px 24px -12px rgba(27,33,39,.18);color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){%s}}
:root[data-theme=dark]{%s}
*{box-sizing:border-box}
html{scroll-padding-top:24px}
body{margin:0;background:var(--paper);color:var(--ink);font:400 16px/1.6 Geist,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
::selection{background:var(--accent-soft);color:var(--accent-ink)}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:4px}
a{color:var(--accent-ink);text-underline-offset:3px;text-decoration-thickness:1px}
code{font:13.5px/1.5 "Geist Mono",ui-monospace,Menlo,Consolas,monospace;background:var(--code);padding:1px 5px;border-radius:4px}
pre{background:var(--code);padding:14px 16px;border-radius:8px;overflow:auto}
pre code{background:none;padding:0}
strong{font-weight:600}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:var(--rule);border-radius:10px;border:2px solid var(--paper)}
.shell{display:grid;grid-template-columns:268px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;overflow:auto;border-right:1px solid var(--rule-2);padding:28px 20px;
display:flex;flex-direction:column;gap:22px}
.side .doc{font-weight:600;font-size:15px;line-height:1.35}
.side .doc a{color:var(--ink-3);font-weight:400;font-size:13px;text-decoration:none;display:block;margin-bottom:10px}
.toc{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:1px}
.toc a{display:block;color:var(--ink-2);text-decoration:none;font-size:14.5px;padding:7px 10px;border-radius:7px;line-height:1.35}
.toc a:hover{background:var(--rule-2);color:var(--ink)}
.toc a.on{background:var(--accent-soft);color:var(--accent-ink);font-weight:500}
.toc ul{list-style:none;margin:2px 0 6px;padding:0 0 0 12px}
.toc ul a{font-size:13.5px;padding:5px 10px;color:var(--ink-3)}
.mode{margin-top:auto;border-top:1px solid var(--rule-2);padding-top:16px;font-size:13.5px;color:var(--ink-2)}
.switch{display:flex;align-items:center;gap:10px;cursor:pointer}
.switch input{appearance:none;width:34px;height:20px;border-radius:999px;background:var(--rule);position:relative;margin:0;
cursor:pointer;transition:background .2s;flex:none}
.switch input::after{content:"";position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%%;background:var(--plate);
box-shadow:0 1px 2px rgba(0,0,0,.2);transition:transform .25s cubic-bezier(.16,1,.3,1)}
.switch input:checked{background:var(--accent)}.switch input:checked::after{transform:translateX(14px)}
main{max-width:1480px;padding:0 48px 120px;min-width:0}
h1.doc-title{font-size:30px;line-height:1.2;letter-spacing:-.02em;font-weight:600;margin:40px 0 36px;padding-bottom:20px;
border-bottom:1px solid var(--rule);text-wrap:balance}
.pg{padding-top:8px}
.pg+.pg{padding-top:56px}
.paged .pg{display:none}.paged .pg.cur{display:block;padding-top:8px}
h2{font-size:26px;letter-spacing:-.02em;font-weight:600;margin:0 0 16px;text-wrap:balance}
h3{font-size:18px;font-weight:600;margin:24px 0 8px}
h4,h5,h6{font-size:16px;margin:20px 0 6px}
p,ul,ol{margin:0 0 14px}
.pg>p,.tbody>p,.pg li{max-width:76ch}
ul,ol{padding-left:24px}
li{margin:3px 0}
blockquote{margin:0 0 16px;padding:14px 18px;background:var(--plate);border:1px solid var(--rule);border-radius:10px;color:var(--ink-2)}
blockquote p:last-child{margin:0}
hr{border:0;border-top:1px solid var(--rule);margin:28px 0}
.table-wrap{overflow:auto;margin:0 0 18px;max-height:80vh}
table{border-collapse:collapse;width:100%%;font-size:14.5px;line-height:1.45}
th{text-align:left;font-weight:600;color:var(--ink-3);font-size:13px;padding:8px 12px 8px 0;border-bottom:1.5px solid var(--ink-2);
position:sticky;top:0;background:var(--paper)}
td{padding:11px 12px 11px 0;border-bottom:1px solid var(--rule-2);vertical-align:top;color:var(--ink-2)}
td:first-child{color:var(--ink);font-weight:500}
figure.diagram{margin:0 0 18px;padding:24px;background:var(--plate);border:1px solid var(--rule);border-radius:14px;overflow:auto}
figure.diagram pre.mermaid{background:none;margin:0;color:var(--ink-2);font-size:13px}
figure.diagram pre.mermaid[data-processed]{width:max-content;min-width:100%%;padding:0;text-align:center}
figure.diagram{position:relative}
figure.diagram pre.mermaid[data-processed]{width:auto;min-width:0}
figure.diagram.actual pre.mermaid[data-processed]{width:max-content;text-align:left}
figure.diagram.actual{cursor:grab;user-select:none;touch-action:none}
figure.diagram.actual.dragging{cursor:grabbing}
figure.diagram.actual .node.pick{cursor:pointer}
.dtools{position:sticky;left:0;display:flex;justify-content:flex-end;gap:6px;margin:-8px -8px 8px}
.dtools button{all:unset;cursor:pointer;font-size:13px;color:var(--ink-2);padding:5px 11px;border-radius:7px;border:1px solid var(--rule);background:var(--plate)}
.dtools button:hover{background:var(--rule-2);color:var(--ink)}
.dtools button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.dtools button[hidden]{display:none}
figure.diagram:fullscreen{background:var(--paper);border:0;border-radius:0;padding:24px 32px;overflow:auto;display:flex;flex-direction:column}
figure.diagram:fullscreen .dtools{margin:0 0 12px}
figure.diagram:fullscreen:not(.actual) pre.mermaid{flex:1;display:flex;align-items:center;justify-content:center;min-height:0}
figure.diagram:fullscreen:not(.actual) svg{max-height:calc(100vh - 100px);width:auto!important;max-width:100%%!important}
.diagram .node .nodeLabel,.diagram .node .nodeLabel p{font-family:Geist,sans-serif!important;color:var(--ink)!important}
.diagram .node .nodeLabel i{font-style:normal;color:var(--ink-3);font-size:.86em}
.diagram .edgeLabel,.diagram .edgeLabel p{font-family:Geist,sans-serif!important;font-size:12px!important;background:var(--plate)!important;color:var(--ink-2)!important}
.diagram .edgeLabel rect,.diagram .labelBkg{fill:var(--plate)!important;background:var(--plate)!important;opacity:1!important}
.diagram .cluster rect{fill:transparent!important;stroke:var(--rule)!important}
.diagram .cluster .nodeLabel,.diagram .cluster-label .nodeLabel,.diagram .cluster-label p{font-weight:600;color:var(--ink-3)!important}
.diagram .flowchart-link{stroke:var(--ink-3)!important;stroke-width:1.4px!important}
.diagram marker path{fill:var(--ink-3)!important;stroke:var(--ink-3)!important}
.diagram .node :is(rect,path,polygon,circle,ellipse){fill:var(--tool-fill)!important;stroke:var(--tool)!important;stroke-width:1.5px!important}
.diagram .node.ksrc :is(rect,path,polygon,circle,ellipse){fill:var(--src-fill)!important;stroke:var(--src)!important}
.diagram .node.kstore :is(rect,path,polygon,circle,ellipse){fill:var(--store-fill)!important;stroke:var(--store)!important}
.diagram .node.kjob :is(rect,path,polygon,circle,ellipse){fill:var(--job-fill)!important;stroke:var(--job)!important}
.diagram .node.kperson :is(rect,path,polygon,circle,ellipse){fill:var(--person-fill)!important;stroke:var(--person)!important}
.diagram .node.kwarn :is(rect,path,polygon,circle,ellipse){fill:var(--warn-fill)!important;stroke:var(--warn)!important}
.diagram .node.new :is(rect,path,polygon,circle,ellipse){stroke:var(--accent)!important;stroke-width:2.5px!important;stroke-dasharray:5 3}
.diagram .node{transition:filter .25s cubic-bezier(.16,1,.3,1)}
.diagram .node.pick{cursor:pointer}
.diagram .node.pick:hover{filter:drop-shadow(0 4px 10px rgba(0,0,0,.18))}
.diagram .node.sel :is(rect,path,polygon,circle,ellipse){stroke:var(--accent)!important;stroke-width:3.5px!important;stroke-dasharray:none}
.legend{display:flex;flex-wrap:wrap;gap:16px;margin:-6px 0 18px;font-size:13px;color:var(--ink-2)}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px;border:1.5px solid}
.lg-src{background:var(--src-fill);border-color:var(--src)!important}.lg-store{background:var(--store-fill);border-color:var(--store)!important}
.lg-job{background:var(--job-fill);border-color:var(--job)!important}.lg-tool{background:var(--tool-fill);border-color:var(--tool)!important}
.lg-person{background:var(--person-fill);border-color:var(--person)!important;border-radius:50%%!important}
.lg-warn{background:var(--warn-fill);border-color:var(--warn)!important}
.lg-new{background:transparent;border:2px dashed var(--accent)!important}
.inspector{border:1px solid var(--rule);background:var(--plate);border-radius:14px;padding:20px 24px;margin:0 0 18px;min-height:96px}
.inspector .k{font-size:13px;color:var(--ink-3);margin:0 0 8px}
.inspector h3{margin:0 0 8px;font-size:21px}
.inspector .tool{display:inline-block;font-size:13px;font-weight:500;padding:3px 10px;border-radius:999px;background:var(--accent-soft);
color:var(--accent-ink);margin:0 0 10px}
.inspector p{margin:0;color:var(--ink-2);max-width:70ch}
.chips{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px}
.chips button,.back{all:unset;cursor:pointer;display:inline-flex;gap:8px;align-items:center;padding:6px 12px;border-radius:999px;
border:1px solid var(--rule);font-size:14px;color:var(--ink-2)}
.chips button:hover,.back:hover{background:var(--rule-2);color:var(--ink)}
.chips button:focus-visible,.back:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.chips small{color:var(--ink-3);font-size:12.5px}
.back{margin-bottom:12px;padding:4px 10px;font-size:13px}
.road{list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:24px 0;margin:8px 0 0;padding:0}
.step{padding:0 20px 0 0;margin:0}
.step .tick{display:flex;align-items:center;margin-bottom:16px}
.step .tick b{width:30px;height:30px;border-radius:50%%;display:grid;place-items:center;background:var(--ink);color:var(--paper);
font-size:13px;font-weight:600;flex:none}
.step .tick::after{content:"";height:2px;background:var(--rule);flex:1;margin-left:10px}
.step:first-child .tick b{background:var(--accent)}
.step h3{font-size:16px;margin:0 0 8px;line-height:1.35}
.step .del{font-size:15px;color:var(--accent-ink);font-weight:500;margin:0 0 8px}
.step .what{font-size:14px;color:var(--ink-3);margin:0}
details.topic{border-bottom:1px solid var(--rule)}
.pg>details.topic:first-of-type,.pg>p+details.topic{border-top:1px solid var(--rule)}
details.topic summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:24px;
align-items:center;padding:20px 4px}
details.topic summary::-webkit-details-marker{display:none}
details.topic summary h3{margin:0;font-size:18px}
details.topic summary p{margin:4px 0 0;color:var(--ink-2);font-size:15px;max-width:80ch}
details.topic summary svg{width:20px;height:20px;fill:none;stroke:var(--ink-3);stroke-width:1.6;transition:transform .35s cubic-bezier(.16,1,.3,1)}
details.topic[open] summary svg{transform:rotate(45deg)}
details.topic summary:hover h3{color:var(--accent-ink)}
.tbody{padding:0 4px 24px}
.asks{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px 48px}
.colh{font-size:14px;color:var(--ink-2);margin:0 0 6px}
.ask{padding:14px 0;border-top:1px solid var(--rule-2)}
.ask p{margin:0}
.ask .q{font-weight:500}
.ask .assume{display:flex;gap:10px;margin-top:6px;color:var(--ink-2);font-size:14.5px}
.ask .assume span{flex:none;font-size:12.5px;font-weight:500;color:var(--store);background:var(--store-fill);padding:1px 8px;
border-radius:999px;height:fit-content;margin-top:2px}
.ask .then{font-size:14px;color:var(--ink-3);margin-top:4px}
.pager{display:none;justify-content:space-between;gap:12px;margin-top:48px;padding-top:20px;border-top:1px solid var(--rule)}
.paged .pager{display:flex}
.pager button{all:unset;cursor:pointer;font-size:14px;color:var(--ink-2);padding:8px 14px;border-radius:8px;border:1px solid var(--rule)}
.pager button:hover{background:var(--rule-2);color:var(--ink)}
.pager button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.pager button[hidden]{display:block;visibility:hidden}
footer{margin-top:56px;color:var(--ink-3);font-size:13px}
.cards{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.cards a{display:flex;flex-direction:column;gap:10px;height:100%%;padding:22px;border:1px solid var(--rule);border-radius:14px;background:var(--plate);
text-decoration:none;color:var(--ink);transition:border-color .2s,transform .3s cubic-bezier(.16,1,.3,1)}
.cards a:hover{border-color:var(--accent);transform:translateY(-2px)}
.cards h2{font-size:19px;margin:0}
.cards .req{color:var(--ink-2);font-size:14.5px;margin:0}
.cards .shows{color:var(--accent-ink);font-size:14px;margin:auto 0 0}
.landing{max-width:1100px;margin:0 auto;padding:56px 32px 96px}
.landing>p{color:var(--ink-2);max-width:72ch;margin:0 0 32px}
@media (max-width:900px){.shell{display:block}.side{position:static;height:auto;border-right:0;border-bottom:1px solid var(--rule-2)}
.toc ul{display:none}main{padding:0 16px 80px}.landing{padding:32px 16px 64px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
@media print{.side,.pager{display:none!important}.shell{display:block}.paged .pg{display:block}details.topic>.tbody{display:block}}
""" % (TOKENS_DARK, TOKENS_DARK)

JS = r"""
const body=document.body,pages=[...document.querySelectorAll('.pg')],tocs=[...document.querySelectorAll('.toc > li > a')];
const flat=document.getElementById('flat');let cur=0;
// each diagram's source, kept before anything draws, so a redraw never reads a drawn picture back as source
document.querySelectorAll('pre.mermaid').forEach(pre=>{pre.dataset.src=pre.textContent;});
// diagrams fit the width by default; "Actual size" scrolls sideways at full size, "Full screen" fills the screen
function fitDiagram(svg){const w=svg.viewBox.baseVal.width||parseFloat(svg.style.maxWidth);if(!w)return;
const f=svg.closest('figure');svg.style.maxWidth='none';svg.style.width='100%';svg.style.height='auto';
f.dsvg=svg;f.dw=w;f.classList.remove('actual');   // a redraw replaces the picture; the buttons read the current one
const old=f.querySelector('.dtools');if(old){const s=old.firstChild;s.hidden=w<=f.clientWidth-50;s.textContent='Actual size';return;}
const tools=document.createElement('div');tools.className='dtools';
const size=document.createElement('button');size.type='button';
const full=document.createElement('button');full.type='button';full.textContent='Full screen';
size.hidden=w<=f.clientWidth-50;size.textContent='Actual size';
size.onclick=()=>{const actual=f.classList.toggle('actual');f.dsvg.style.width=actual?f.dw+'px':'100%';size.textContent=actual?'Fit to width':'Actual size';};
full.onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else (f.requestFullscreen||f.webkitRequestFullscreen).call(f);};
f.addEventListener('fullscreenchange',()=>{const on=document.fullscreenElement===f;full.textContent=on?'Exit full screen':'Full screen';
f.classList.remove('actual');f.dsvg.style.width='100%';size.textContent='Actual size';});
tools.append(size,full);f.prepend(tools);
// at actual size, drag the diagram to move around it; a drag never counts as a click on a box
let drag=null,moved=false;
f.addEventListener('pointerdown',e=>{if(!f.classList.contains('actual')||e.button!==0||e.target.closest('.dtools'))return;
drag={x:e.clientX,y:e.clientY,l:f.scrollLeft,t:f.scrollTop,id:e.pointerId};moved=false;});
f.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;
if(!moved&&Math.hypot(dx,dy)<4)return;if(!moved){moved=true;f.setPointerCapture(drag.id);f.classList.add('dragging');}
f.scrollLeft=drag.l-dx;f.scrollTop=drag.t-dy;});
const end=()=>{drag=null;f.classList.remove('dragging');};
f.addEventListener('pointerup',end);f.addEventListener('pointercancel',end);
f.addEventListener('click',e=>{if(moved){e.stopPropagation();e.preventDefault();moved=false;}},true);}
function draw(){if(!window.drawDiagrams)return;(body.classList.contains('paged')?[pages[cur]]:pages).forEach(p=>window.drawDiagrams(p));}
function mark(id){tocs.forEach(a=>a.classList.toggle('on',decodeURIComponent(a.hash.slice(1))===id));}
function show(i,keep){cur=Math.max(0,Math.min(pages.length-1,i));pages.forEach((p,j)=>p.classList.toggle('cur',j===cur));
mark(pages[cur].id);if(!keep)scrollTo(0,0);draw();}
function pageOf(id){const el=id&&document.getElementById(id);const p=el&&el.closest('.pg');return p?pages.indexOf(p):-1;}
function go(id){const i=pageOf(id);if(i<0)return;const el=document.getElementById(id);
if(el.tagName==='DETAILS')el.open=true;if(body.classList.contains('paged'))show(i,true);
history.replaceState(null,'','#'+encodeURIComponent(id));if(el!==pages[i]||!body.classList.contains('paged'))el.scrollIntoView({block:'start'});else scrollTo(0,0);}
document.querySelectorAll('.toc a').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();go(decodeURIComponent(a.hash.slice(1)));}));
document.querySelectorAll('.pager button').forEach(b=>b.addEventListener('click',()=>{show(cur+(+b.dataset.go));
history.replaceState(null,'','#'+pages[cur].id);}));
flat.addEventListener('change',()=>{body.classList.toggle('paged',!flat.checked);if(flat.checked){mark(pages[cur].id);draw();
pages[cur].scrollIntoView();}else show(cur);});
addEventListener('scroll',()=>{if(body.classList.contains('paged'))return;let c=pages[0];
for(const p of pages)if(p.getBoundingClientRect().top<160)c=p;cur=pages.indexOf(c);mark(c.id);},{passive:true});
const hashId=h=>decodeURIComponent(h.slice(1));   // headings may be non-ASCII; hashes come back percent-encoded
if(pages.length){show(Math.max(0,pageOf(hashId(location.hash))));if(location.hash)go(hashId(location.hash));}
// architecture: the component table as a panel, linked to the diagram's boxes
const comps=JSON.parse((document.getElementById('brief-components')||{}).textContent||'[]');
const insp=document.getElementById('brief-inspector');
const words=s=>(s||'').toLowerCase().replace(/[^a-z0-9 ]+/g,' ').split(/\s+/).filter(w=>w.length>2&&!['the','and','for','with','job','jobs'].includes(w));
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let nodeOf={};
function overview(){if(!insp)return;insp.innerHTML='<p class="k">Select a box in the diagram, or a component:</p><ul class="chips">'+
comps.map((c,i)=>`<li><button type="button" data-i="${i}">${esc(c.name)} <small>${esc(c.tool)}</small></button></li>`).join('')+'</ul>';
insp.querySelectorAll('button[data-i]').forEach(b=>b.onclick=()=>pick(+b.dataset.i));
document.querySelectorAll('.diagram .node.sel').forEach(n=>n.classList.remove('sel'));}
function pick(i){const c=comps[i];if(!c||!insp)return;
insp.innerHTML=`<button class="back" type="button">← All components</button><h3>${esc(c.name)}</h3>`+
(c.tool?`<span class="tool">${esc(c.tool)}</span>`:'')+`<p>${esc(c.what)}</p>`;
insp.querySelector('.back').onclick=overview;
document.querySelectorAll('.diagram .node.sel').forEach(n=>n.classList.remove('sel'));if(nodeOf[i])nodeOf[i].classList.add('sel');}
window.linkComponents=fig=>{if(!comps.length)return;const pairs=[];for(const k in nodeOf)if(!nodeOf[k].isConnected)delete nodeOf[k];
const hit=(cw,lw)=>cw.length?cw.filter(w=>lw.some(l=>l===w||l===w+'s'||w===l+'s')).length/cw.length:0;
fig.querySelectorAll('.node').forEach(n=>{const lab=n.querySelector('.nodeLabel');
const txt=(lab?lab.innerHTML:n.textContent).replace(/<br\s*\/?>/gi,'\n').replace(/<[^>]+>/g,' ');
const lw=words(txt),first=(txt.trim().split(/\s+/)[0]||'').toLowerCase();comps.forEach((c,i)=>{
const cw=words(c.name),s=hit(cw,lw),tw=words(c.tool),t=hit(tw,lw);
// the name decides (all of a short name, most of a long one); a box named by its tool matches when it starts with that tool
if(s>=(cw.length<=2?1:0.6))pairs.push([s+0.25*t,n,i]);
else if(!s&&tw.length&&first===tw[0])pairs.push([0.6,n,i]);});});
pairs.sort((a,b)=>b[0]-a[0]);const used=new Set();
for(const [,n,i] of pairs){if(i in nodeOf||used.has(n))continue;nodeOf[i]=n;used.add(n);
n.classList.add('pick');n.setAttribute('tabindex','0');n.setAttribute('role','button');
n.addEventListener('click',()=>pick(i));n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick(i);}});}};
overview();
// a diagram inside a collapsed topic draws when the topic opens
document.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>{if(d.open&&window.drawDiagrams)window.drawDiagrams(d);}));
"""

MERMAID_JS = """
<script type="module">
try{const {default:m}=await import('%s');const {default:elk}=await import('%s');
m.registerLayoutLoaders(elk);   // ELK lays diagrams out with right-angle connectors
m.initialize({startOnLoad:false,theme:'base',securityLevel:'strict',
themeVariables:{fontFamily:'Geist, system-ui, sans-serif',fontSize:'15px'},flowchart:{htmlLabels:true}});
// one drawing at a time, only on a page that is showing; a diagram drawn while its page was hidden comes out
// empty, so it is drawn again from its saved source the next time the page shows
let queue=Promise.resolve();
window.drawDiagrams=p=>queue=queue.then(async()=>{if(!p.getClientRects().length)return;const todo=[];
for(const pre of p.querySelectorAll('pre.mermaid')){if(!pre.dataset.src||!(pre.checkVisibility?pre.checkVisibility():pre.getClientRects().length))continue;   // hidden (a closed topic): drawn when shown
const svg=pre.querySelector('svg');if(pre.hasAttribute('data-processed')&&svg&&svg.getBoundingClientRect().height>24)continue;
if(pre.hasAttribute('data-processed')){pre.removeAttribute('data-processed');pre.textContent=pre.dataset.src;}todo.push(pre);}
if(!todo.length)return;await m.run({nodes:todo});
todo.forEach(pre=>{const svg=pre.querySelector('svg');if(svg)fitDiagram(svg);
const f=pre.closest('figure.diagram.arch');if(f&&window.linkComponents)window.linkComponents(f);});}).catch(e=>console.warn(e));
draw();}catch(e){console.warn('Mermaid unavailable; diagrams shown as source',e);}
</script>
""" % (MERMAID_URL, ELK_URL)

LEGEND = ('<div class="legend"><span><i class="lg-src"></i>Existing source</span><span><i class="lg-store"></i>Storage</span>'
          '<span><i class="lg-job"></i>Job</span><span><i class="lg-tool"></i>Tool or service</span>'
          '<span><i class="lg-person"></i>People</span><span><i class="lg-warn"></i>Failed records</span>'
          '<span><i class="lg-new"></i>New or changed</span></div>')


def page(b, title=None, home=None):
    """The HTML page for one Brief; `home` is an optional back link (href, text)."""
    title = title or b.title
    toc, pages = [], []
    for n, (sid, label, body, subs) in enumerate(b.pages):
        sub = "".join(f'<li><a href="#{t}">{html.escape(l)}</a></li>' for t, l in subs)
        toc.append(f'<li><a href="#{sid}">{html.escape(label)}</a>' + (f"<ul>{sub}</ul>" if sub else "") + "</li>")
        if 'class="mermaid"' in body:
            body = re.sub(r"(</figure>)", r"\1" + LEGEND, body, count=1)
        prev = html.escape(b.pages[n - 1][1]) if n else ""
        nxt = html.escape(b.pages[n + 1][1]) if n + 1 < len(b.pages) else ""
        pager = (f'<div class="pager"><button type="button" data-go="-1"{"" if prev else " hidden"}>← {prev}</button>'
                 f'<button type="button" data-go="1"{"" if nxt else " hidden"}>{nxt} →</button></div>')
        pages.append(f'<section class="pg" id="{sid}"><h2>{html.escape(label)}</h2>{body}{pager}</section>')
    diagrams = MERMAID_JS if any('class="mermaid"' in p[2] for p in b.pages) else ""
    # raw JSON in the script tag (entities are not decoded there); <, > and & escaped as JSON so nothing can close it
    data = json.dumps(b.components).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    comps = f'<script type="application/json" id="brief-components">{data}</script>' if b.components else ""
    back = f'<a href="{html.escape(home[0])}">← {html.escape(home[1])}</a>' if home else ""
    note = ("Rendered from Markdown, which stays the source of truth."
            + (" Diagrams need network access to draw; offline they show as their source." if diagrams else ""))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>{FONTS}<style>{CSS}</style></head>
<body class="paged"><div class="shell">
<aside class="side" aria-label="Contents"><div class="doc">{back}{html.escape(b.title)}</div>
<ul class="toc">{''.join(toc)}</ul>
<div class="mode"><label class="switch"><input type="checkbox" id="flat"> Show everything</label></div></aside>
<main><h1 class="doc-title">{html.escape(b.title)}</h1>{''.join(pages)}<footer>{note}</footer></main>
</div>{comps}<script>{JS}</script>{diagrams}</body></html>
"""


def landing(cards, title, intro=""):
    """An index page: one card per document (href, label, request, shows)."""
    items = "".join(
        f'<li><a href="{html.escape(c["href"])}"><h2>{html.escape(c["label"])}</h2>'
        f'<p class="req">{html.escape(c["request"])}</p><p class="shows">{html.escape(c["shows"])}</p></a></li>'
        for c in cards)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>{FONTS}<style>{CSS}</style></head>
<body><main class="landing"><h1 class="doc-title">{html.escape(title)}</h1><p>{inline(intro)}</p>
<ul class="cards">{items}</ul></main></body></html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("inputs", nargs="+", type=Path, help="Markdown documents; each becomes its own page")
    ap.add_argument("-o", "--output", type=Path, help="output HTML for a single input (default: the input as .html)")
    ap.add_argument("--title", help="page title (default: the document's first heading)")
    args = ap.parse_args(argv)
    if args.output and len(args.inputs) > 1:
        ap.error("-o takes a single input")
    for p in args.inputs:
        if not p.is_file():
            ap.error(f"{p}: no such file")
    for p in args.inputs:
        out = args.output or p.with_suffix(".html")
        out.write_text(page(brief(p.read_text(encoding="utf-8")), title=args.title), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    sys.exit(main())
