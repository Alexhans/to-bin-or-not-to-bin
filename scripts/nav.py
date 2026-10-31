"""Keep the tutorial's navigation in step with its folders, and check every link.

The structure is the source of truth:

- order comes from folder names: `steps/NN-*`, then `tracks/<track>/NN-*`;
- titles come from each page's `# N. Title` heading;
- a page is "not written yet" while it contains the line `> Not written yet.`

Only text between guards is generated, so prose is never touched:

    <!-- nav:top --> … <!-- /nav:top -->          first line of every chapter
    <!-- nav:bottom --> … <!-- /nav:bottom -->    last line of every chapter
    <!-- start --> … <!-- /start -->              where the home page says where to start
    <!-- toc --> … <!-- /toc -->                  the full table of contents on the home page

    uv run python scripts/nav.py           rewrite out-of-date blocks, then check links
    uv run python scripts/nav.py --check   change nothing; fail if anything is out of date

Exits 1 if it changed a file or found a problem, so a pre-commit hook stops the commit.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADING = re.compile(r"^#\s+(\d+)\.\s+(.+?)\s*$", re.M)
PLACEHOLDER = "> Not written yet."
PICK_YOUR_TRACK = "#pick-your-track"
# Checked for in the pages that invite feedback.
FEEDBACK_LINKS = (
    "https://github.com/Alexhans/to-bin-or-not-to-bin/issues",
    "https://linktr.ee/alex.guglielmone.nemi",
)
TRACK_ORDER = ["airflow", "agent"]  # tracks not listed here come after, alphabetically
TRACK_NAMES = {"airflow": "Airflow track", "agent": "Coding agent track"}


@dataclass(frozen=True)
class Chapter:
    path: Path
    number: int
    title: str
    written: bool

    def link(self, start: Path) -> str:
        return f"[{self.number}. {self.title}]({rel(self.path, start)})"


@dataclass(frozen=True)
class Track:
    folder: Path
    name: str
    chapters: list[Chapter]


def rel(target: Path, start: Path) -> str:
    return Path(os.path.relpath(target, start.parent)).as_posix()


def chapter(path: Path) -> Chapter:
    text = path.read_text()
    m = HEADING.search(text)
    if not m:
        raise SystemExit(f"{path.relative_to(ROOT)}: no '# N. Title' heading")
    return Chapter(path, int(m[1]), m[2], PLACEHOLDER not in text)


def discover() -> tuple[list[Chapter], list[Track]]:
    steps = [chapter(p) for p in sorted(ROOT.glob("steps/[0-9][0-9]-*/README.md"))]
    tracks = []
    folders = sorted((d for d in ROOT.glob("tracks/*") if d.is_dir()), key=lambda d: (
        TRACK_ORDER.index(d.name) if d.name in TRACK_ORDER else len(TRACK_ORDER), d.name))
    for folder in folders:
        chapters = [chapter(p) for p in sorted(folder.glob("[0-9][0-9]-*/README.md"))]
        if chapters:
            tracks.append(Track(folder, TRACK_NAMES.get(folder.name, folder.name.title() + " track"), chapters))
    return steps, tracks


def nav_lines(steps: list[Chapter], tracks: list[Track]) -> dict[Path, str]:
    """The nav line for every chapter page."""
    home = ROOT / "README.md"
    lines = {}
    for i, c in enumerate(steps):
        parts = [f"[Home]({rel(home, c.path)})", f"[Contents]({rel(home, c.path)}#contents)"]
        if i:
            parts.append(f"Previous: {steps[i - 1].link(c.path)}")
        parts.append(f"Next: {steps[i + 1].link(c.path)}" if i + 1 < len(steps) else f"Next: [Pick your track]({PICK_YOUR_TRACK})")
        lines[c.path] = " · ".join(parts)
    for t in tracks:
        for i, c in enumerate(t.chapters):
            before = t.chapters[i - 1] if i else steps[-1]
            parts = [f"[Home]({rel(home, c.path)})", f"[Contents]({rel(home, c.path)}#contents)",
                     t.name, f"Previous: {before.link(c.path)}"]
            if i + 1 < len(t.chapters):
                parts.append(f"Next: {t.chapters[i + 1].link(c.path)}")
            lines[c.path] = " · ".join(parts)
    return lines


def start_line(steps: list[Chapter]) -> str:
    first, last = steps[0], steps[-1]
    home = ROOT / "README.md"
    return (f"Then start with [step {first.number}: {first.title}]({rel(first.path, home)}). After step {last.number}\n"
            "you'll choose whether to carry on with Airflow or with your coding agent.")


def contents(steps: list[Chapter], tracks: list[Track]) -> str:
    home = ROOT / "README.md"
    lines = [""]
    lines += [f"{c.number}. [{c.title}]({rel(c.path, home)})" for c in steps]
    for t in tracks:
        lines += ["", f"{t.name}:", ""]
        lines += [f"{c.number}. [{c.title}]({rel(c.path, home)})" + ("" if c.written else " (not written yet)")
                  for c in t.chapters]
    return "\n".join(lines)


def replace_block(text: str, name: str, body: str, path: Path) -> str:
    pattern = re.compile(rf"(<!-- {name} -->\n)(?:.*?\n)?(<!-- /{name} -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"{path.relative_to(ROOT)}: missing <!-- {name} --> … <!-- /{name} -->")
    return pattern.sub(lambda m: m[1] + body + "\n" + m[2], text, count=1)


def slug(heading: str) -> str:
    """GitHub's anchor for a heading."""
    s = re.sub(r"[^\w\- ]", "", heading.strip().lower().replace("`", ""))
    return s.replace(" ", "-")


def feedback_links() -> list[str]:
    """Every page that invites feedback has to use the same two links."""
    problems = []
    for name in ("README.md", "tracks/airflow/07-no-model/README.md", "tracks/agent/06-no-model/README.md"):
        text = (ROOT / name).read_text()
        for link in FEEDBACK_LINKS:
            if link not in text:
                problems.append(f"{name}: missing the feedback link {link}")
    return problems


def broken_links() -> list[str]:
    problems = []
    for md in sorted(ROOT.rglob("*.md")):
        if any(part in {".venv", ".airflow", "node_modules"} for part in md.parts):
            continue
        for link in re.findall(r"\]\(([^)\s]+)\)", md.read_text()):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            target, _, anchor = link.partition("#")
            dest = (md.parent / target).resolve() if target else md
            if not dest.exists():
                problems.append(f"{md.relative_to(ROOT)}: the link {link} doesn't exist")
            elif anchor and dest.suffix == ".md":
                anchors = {slug(h) for h in re.findall(r"^#+\s+(.+)$", dest.read_text(), re.M)}
                if anchor not in anchors:
                    problems.append(f"{md.relative_to(ROOT)}: {link} has no heading #{anchor}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Update the tutorial's navigation and check its links.")
    parser.add_argument("--check", action="store_true", help="change nothing; fail if anything is out of date")
    args = parser.parse_args()

    steps, tracks = discover()
    wanted: dict[Path, list[tuple[str, str]]] = {}
    for path, line in nav_lines(steps, tracks).items():
        wanted[path] = [("nav:top", line), ("nav:bottom", line)]
    wanted[ROOT / "README.md"] = [("start", start_line(steps)), ("toc", contents(steps, tracks))]

    stale = []
    for path, blocks in wanted.items():
        text = path.read_text()
        new = text
        for name, body in blocks:
            new = replace_block(new, name, body, path)
        if new != text:
            stale.append(path.relative_to(ROOT))
            if not args.check:
                path.write_text(new)

    problems = broken_links() + feedback_links()
    for p in stale:
        print(f"{'out of date' if args.check else 'updated'}: {p}")
    for p in problems:
        print(f"problem: {p}")
    return 1 if stale or problems else 0


if __name__ == "__main__":
    sys.exit(main())
