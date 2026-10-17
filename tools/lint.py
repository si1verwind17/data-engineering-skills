#!/usr/bin/env python3
"""Repo lint: manifests resolve, every skill has a well-formed SKILL.md,
descriptions start with "Use when" and stay under the cap, and no tracked file
names a private project. The private terms (one per line) live only on the
maintainer's machine, in ~/.config/viz-code/private-terms.txt
(VIZCODE_PRIVATE_TERMS overrides the path); that check skips without the file.
Stdlib only."""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESC_CAP = 500
errors = []
err = errors.append

mp = ROOT / ".claude-plugin" / "marketplace.json"
if not mp.exists():
    err("missing .claude-plugin/marketplace.json")
    plugins = []
else:
    plugins = json.loads(mp.read_text()).get("plugins", [])

seen_skills = set()
for entry in plugins:
    pdir = (ROOT / entry["source"]).resolve()
    skills = entry.get("skills")
    if not skills:
        manifest = pdir / ".claude-plugin" / "plugin.json"
        if not manifest.exists():
            err(f"{entry['name']}: no inline skills and no plugin.json"); continue
        skills = json.loads(manifest.read_text()).get("skills", [])
    if entry.get("skills") and entry.get("strict", True):
        err(f"{entry['name']}: inline skills need strict: false")
    for rel in skills:
        sdir = (pdir / rel).resolve()
        seen_skills.add(sdir)
        skill_md = sdir / "SKILL.md"
        if not skill_md.exists():
            err(f"{entry['name']}: skill {rel} has no SKILL.md")
            continue
        text = skill_md.read_text()
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not m:
            err(f"{rel}: no frontmatter"); continue
        fields, key = {}, None
        for line in m.group(1).splitlines():
            km = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
            if km:
                key, val = km.group(1), km.group(2).strip()
                fields[key] = "" if val in (">-", ">", "|", "|-") else val
            elif key and line.startswith("  "):
                fields[key] = (fields[key] + " " + line.strip()).strip()
        if set(fields) - {"name", "description", "license"}:
            err(f"{rel}: frontmatter has extra keys {sorted(set(fields) - {'name', 'description', 'license'})}")
        if fields.get("name") != sdir.name:
            err(f"{rel}: name {fields.get('name')!r} != directory {sdir.name!r}")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", sdir.name):
            err(f"{rel}: directory name must be lowercase-hyphen")
        desc = fields.get("description", "")
        if not desc.startswith("Use when"):
            err(f"{rel}: description must start with 'Use when'")
        if len(desc) > DESC_CAP:
            err(f"{rel}: description is {len(desc)} chars (cap {DESC_CAP})")
        for ptr in re.findall(r"`example/([^`]+)`", text):
            if not (sdir / "example" / ptr).exists():
                err(f"{rel}: pointer example/{ptr} does not resolve")
        if (sdir / "eval.md").exists():
            err(f"{rel}: eval.md belongs in eval/, not beside the skill")

# every skills/*/SKILL.md must belong to some plugin, or an installer ships it unlisted
for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")) if (ROOT / "skills").is_dir() else []:
    if skill_md.parent.resolve() not in seen_skills:
        err(f"skills/{skill_md.parent.name}: present in skills/ but in no plugin entry")

# the repo is public: no tracked file names a private project; the owner's handle
# is allowed in the licence, the manifest, the repo's own URL, and its Pages site
TERMS = Path(os.environ.get("VIZCODE_PRIVATE_TERMS", Path.home() / ".config/viz-code/private-terms.txt"))
OWNER_FILES = {"LICENSE", ".claude-plugin/marketplace.json"}
OWNER_URLS = ("si1verwind17/data-engineering-skills", "si1verwind17.github.io/data-engineering-skills")   # the repo and its Pages site
if TERMS.is_file():
    terms = [t.strip().lower() for t in TERMS.read_text().splitlines() if t.strip() and not t.strip().startswith("#")]
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    for name in sorted(n for n in tracked.decode("utf-8", "surrogateescape").split("\0") if n):
        p = ROOT / name
        if name in OWNER_FILES or not p.is_file():
            continue
        for n, line in enumerate(p.read_bytes().decode("utf-8", "ignore").splitlines(), 1):
            low = line.lower()
            for url in OWNER_URLS:
                low = low.replace(url, "")
            for term in terms:
                if term in low:
                    err(f"{name}:{n}: private term {term!r}")

if errors:
    print("\n".join(f"LINT: {e}" for e in errors)); print(f"\n{len(errors)} problem(s).")
    sys.exit(1)
print(f"lint clean ({len(seen_skills)} skills, {len(plugins)} plugins).")
