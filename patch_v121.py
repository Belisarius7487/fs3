#!/usr/bin/env python3
"""FS3 v121 - the review switch hands out one ticket of every class.

?ui=1 gave a destroyer and a Colossus, because the hangar is what needed
testing at the time. The rearm panel needs a CORVETTE on the field, and there
was no way to get one without playing up to it - which made a correctly
working button look dead.

A review switch that can only reach half the panels is not much of a switch.
It now hands out one of each class.

Reads hlp_shooter_v120_logic.html, writes hlp_shooter_v121_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v120_logic.html", "hlp_shooter_v121_logic.html"

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)

src = open(SRC, encoding="utf-8").read()

src = replace_once(
    src,
    "  if(UI_TICKETS){ tickets.destroyer+=1; tickets.colossus+=1; }",
    "  // One of every class: the hangar needs a destroyer, the rearm panel a\n"
    "  // corvette, and the Colossus changes what both of them say.\n"
    "  if(UI_TICKETS){\n"
    "    tickets.cruiser+=1; tickets.corvette+=1;\n"
    "    tickets.destroyer+=1; tickets.colossus+=1;\n"
    "  }",
    "review tickets",
)

src = replace_once(
    src,
    "// ?ships=N opens N hulls from the start, ?ui=1 puts a destroyer and a\n"
    "// Colossus ticket in hand, so a panel can be looked at without playing up\n"
    "// to it first. Neither touches a rule the panel is being judged on.",
    "// ?ships=N opens N hulls from the start, ?ui=1 puts one ticket of every\n"
    "// class in hand, so any panel can be looked at without playing up to it\n"
    "// first. Neither touches a rule the panel is being judged on.",
    "review comment",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
