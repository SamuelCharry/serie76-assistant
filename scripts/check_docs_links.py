"""Check local Markdown targets and GitHub heading/source-line anchors; no network access.

Run from any directory with Python 3.12. Includes tracked Markdown and the new wiki;
ignores fenced/inline code, remote URLs and historical prose without Markdown links.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def prose(text: str) -> str:
    text = re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", text)
    return re.sub(r"`+[^`\n]*`+", "", text)


def anchors(text: str) -> set[str]:
    found = set(re.findall(r'''\b(?:id|name)=["']([^"']+)["']''', text))
    counts: dict[str, int] = {}
    for heading in re.findall(r"(?m)^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", text):
        heading = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", heading)
        heading = re.sub(r"<[^>]*>", "", heading).lower()
        slug = "".join(c for c in heading if c.isalnum() or c in " _-").replace(" ", "-")
        number = counts.get(slug, 0)
        counts[slug] = number + 1
        found.add(slug + (f"-{number}" if number else ""))
    return found


def main() -> int:
    names = subprocess.check_output(
        ["git", "ls-files", "--", "*.md"], cwd=ROOT, text=True, encoding="utf-8"
    ).splitlines()
    paths = {ROOT / name for name in names}
    paths.update((ROOT / "docs/wiki").rglob("*.md"))
    paths.update(ROOT.glob("README*.md"))
    paths.add(ROOT / "reports/submission/T3.md")
    broken = []
    checked = 0
    for path in sorted(p for p in paths if p.is_file()):
        text = prose(path.read_text(encoding="utf-8-sig"))
        targets = re.findall(r"!?\[[^]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"'][^\n]*?[\"'])?\s*\)", text)
        refs = dict(re.findall(r"(?m)^\s*\[([^]]+)\]:\s*(\S+)", text))
        for label, reference in re.findall(r"\[([^]]+)\]\[([^]]*)\]", text):
            key = reference or label
            if key not in refs:
                broken.append(f"{path.relative_to(ROOT)}: missing link definition [{key}]")
            else:
                targets.append(refs[key])
        for target in targets:
            target = target.strip("<>")
            split = urlsplit(target)
            if split.scheme or split.netloc:
                continue
            checked += 1
            dest = (ROOT / unquote(split.path).lstrip("/")) if split.path.startswith("/") else path.parent / unquote(split.path)
            dest = dest.resolve()
            fragment = unquote(split.fragment)
            reason = None
            if not dest.exists():
                reason = "target does not exist"
            elif fragment:
                if not dest.is_file():
                    reason = "anchor on directory"
                else:
                    source = dest.read_text(encoding="utf-8-sig")
                    line = re.fullmatch(r"L(\d+)(?:-L(\d+))?", fragment)
                    if line:
                        start = int(line[1]); end = int(line[2] or line[1])
                        if not 1 <= start <= end <= len(source.splitlines()):
                            reason = "source line out of range"
                    elif fragment not in anchors(source):
                        reason = "heading/id anchor does not exist"
            if reason:
                broken.append(f"{path.relative_to(ROOT).as_posix()}: {target}: {reason}")
    for error in broken:
        print(error)
    print(f"Checked {checked} relative Markdown links/anchors; {len(broken)} broken")
    return int(bool(broken))


if __name__ == "__main__":
    raise SystemExit(main())
