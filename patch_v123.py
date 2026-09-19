#!/usr/bin/env python3
"""FS3 v123 - a review switch for the weapons.

?wpn=1 opens every weapon regardless of score, the way ?ships=N opens the
hulls. Without it the rearm panel cannot be judged until the score has been
played up to, and a panel that cannot be seen cannot be reviewed.

It is deliberately NOT folded into ?ui=1: with ui alone the thresholds still
apply, so the locked rows can be looked at too.

Reads hlp_shooter_v122_logic.html, writes hlp_shooter_v123_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v122_logic.html", "hlp_shooter_v123_logic.html"

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)

src = open(SRC, encoding="utf-8").read()

src = replace_once(
    src,
    "const UI_TICKETS = /[?&]ui=1/.test(location.search);",
    "const UI_TICKETS = /[?&]ui=1/.test(location.search);\n"
    "// ?wpn=1 opens every weapon whatever the score. Separate from ?ui=1 on\n"
    "// purpose, so the locked rows can still be looked at with ui alone.\n"
    "const UI_WEAPONS = /[?&]wpn=1/.test(location.search);",
    "weapon switch",
)

src = replace_once(
    src,
    "// ?ships=N opens N hulls from the start, ?ui=1 puts one ticket of every\n"
    "// class in hand, so any panel can be looked at without playing up to it\n"
    "// first. Neither touches a rule the panel is being judged on.",
    "// ?ships=N opens N hulls from the start, ?ui=1 puts one ticket of every\n"
    "// class in hand and ?wpn=1 opens every weapon, so any panel can be looked\n"
    "// at without playing up to it first. None of them touches a rule the panel\n"
    "// is being judged on.",
    "review comment",
)

src = replace_once(
    src,
    "function weaponOpen(w){ return FS1_MODE || score >= (w.unlock||0); }",
    "function weaponOpen(w){ return FS1_MODE || UI_WEAPONS || score >= (w.unlock||0); }",
    "weaponOpen",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
