#!/usr/bin/env python3
"""FS3 v119 - a bomber that rams itself is taken off the field.

ramBlast() sets e.dead = true and e.hp = 0. The reaper at the end of the
damage pass removes a ship only when e.hp <= 0 AND NOT e.dead - the dead flag
is how it knows it has already dealt with something. A ship that arrives there
already flagged is never removed at all.

So the bomber stayed in enemies for good: flagged dead, which is why it lost
its chevron, why the hits registered as sparks and never as damage, and why it
did not hold the mission open. But nothing in the flight code asks about dead,
so it kept flying and kept firing.

tickCapRam has always spliced its rammer out itself, on the line after the
blast. tickRamming never did. It does now.

This fault is older than the ramming work. It could not show while the contact
test measured centre to centre, because under that test a bomber essentially
never connected, so ramBlast was essentially never called.

Points are deliberately not awarded: a bomber that has just driven itself into
your destroyer was not shot down.

Reads hlp_shooter_v118_logic.html, writes hlp_shooter_v119_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v118_logic.html", "hlp_shooter_v119_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

src = replace_once(
    src,
    "    ramBlast(e);\n"
    "  }\n"
    "}",
    "    ramBlast(e);\n"
    "    // Vom Feld nehmen, hier und sofort, genau wie tickCapRam() es mit\n"
    "    // seinem Rammer tut. Die Aufraeumschleife raeumt ihn nicht mehr weg:\n"
    "    // sie greift nur bei e.hp<=0 UND NICHT e.dead, und ramBlast setzt\n"
    "    // beides. Blieb er stehen, war er ein Geist - ohne Winkel, nicht\n"
    "    // abschiessbar, nicht mitgezaehlt, aber weiter fliegend und feuernd.\n"
    "    enemies.splice(i, 1);\n"
    "  }\n"
    "}",
    "splice rammer",
)

src = replace_once(
    src,
    "  e.dead = true; e.hp = 0;\n"
    "}\n"
    "\n"
    "function tickEvents(){",
    "  // Beide Marken setzen und das Schiff dem Aufrufer zum Entfernen\n"
    "  // ueberlassen: wer ramBlast ruft, nimmt es danach selbst aus enemies.\n"
    "  e.dead = true; e.hp = 0;\n"
    "}\n"
    "\n"
    "function tickEvents(){",
    "ramBlast contract",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
