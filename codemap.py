#!/usr/bin/env python3
"""Refresh the generated part of CODEMAP.md from the newest logic file.

Only the text between the AUTO markers is rewritten; the hand-written guide
above it is kept. Run after every patch, before committing:
    python3 codemap.py
"""
import glob
import os
import re
import sys

START, END = "<!-- AUTO:START -->", "<!-- AUTO:END -->"
COMMENT_MAX = 70


def newest_logic_file():
    def ver(p):
        m = re.search(r"_v(\d+)_logic\.html$", p)
        return int(m.group(1)) if m else -1
    files = sorted(glob.glob("hlp_shooter_v*_logic.html"), key=ver)
    return files[-1] if files else None


def comment_above(lines, i):
    """First line of the // comment block directly above line i, if any."""
    j, block = i - 1, []
    while j >= 0 and lines[j].strip().startswith("//"):
        block.insert(0, lines[j].strip()[2:].strip())
        j -= 1
    block = [b for b in block if b and "──" not in b]
    if not block:
        return ""
    # Orphaned comments from removed code often sit stacked above a function.
    # The one that belongs to it is the last comment unit, i.e. the last line
    # that starts after a line ending a sentence.
    starts = [k for k in range(len(block)) if k == 0 or block[k - 1].endswith((".", ":", "!", "?"))]
    text = block[starts[-1]]
    return text if len(text) <= COMMENT_MAX else text[:COMMENT_MAX - 1].rstrip() + "…"


def build_index(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    sections, cur = [], None
    for i, line in enumerate(lines):
        s = line.strip()
        # Only unindented banners start a section; indented ones sit inside a function.
        if line.startswith("//") and "──" in s:
            title = re.sub(r"─+", " ", s).strip("/ ").strip()
            title = re.sub(r"\s{2,}", " — ", title)
            if title:
                cur = {"title": title, "line": i + 1, "funcs": [], "consts": []}
                sections.append(cur)
            continue
        m = re.match(r"^(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", line)
        c = re.match(r"^(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=", line)
        if not (m or c):
            continue
        if cur is None:
            cur = {"title": "(file start)", "line": 1, "funcs": [], "consts": []}
            sections.append(cur)
        if m:
            cur["funcs"].append((i + 1, m.group(1), comment_above(lines, i)))
        else:
            cur["consts"].append(c.group(1))

    out = ["Generated from `%s` by `codemap.py` — do not edit by hand." % os.path.basename(path), ""]
    for sec in sections:
        if not sec["funcs"] and not sec["consts"]:
            continue
        out.append("### %s (line %d)" % (sec["title"], sec["line"]))
        for ln, name, com in sec["funcs"]:
            out.append("- `%s()` %d%s" % (name, ln, (" — " + com) if com else ""))
        if sec["consts"]:
            out.append("- data: " + ", ".join("`%s`" % n for n in sec["consts"]))
        out.append("")
    return "\n".join(out)


def main():
    logic = newest_logic_file()
    if not logic:
        sys.exit("Abbruch: keine Logikdatei gefunden.")
    if not os.path.exists("CODEMAP.md"):
        sys.exit("Abbruch: CODEMAP.md fehlt.")
    with open("CODEMAP.md", encoding="utf-8") as fh:
        doc = fh.read()
    if doc.count(START) != 1 or doc.count(END) != 1:
        sys.exit("Abbruch: AUTO-Markierungen in CODEMAP.md nicht genau einmal vorhanden.")
    head, rest = doc.split(START)
    tail = rest.split(END)[1]
    doc = head + START + "\n" + build_index(logic) + "\n" + END + tail
    with open("CODEMAP.md", "w", encoding="utf-8") as fh:
        fh.write(doc)
    print("CODEMAP.md aktualisiert aus %s" % logic)


if __name__ == "__main__":
    main()
