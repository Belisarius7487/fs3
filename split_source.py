#!/usr/bin/env python3
"""FS3 - one time only: cut the logic file into parts.

Reads hlp_shooter_v126_logic.html and writes src/. Run once; from then on the
parts are the source and assemble.py puts them back together.

The cuts are at CONTIGUOUS line ranges, on section banners the file already
has. That matters: the file is not sorted by theme - SHOOTING is at 6514 and
the weapon tables at 10570 - so a part is "mostly this" rather than "exactly
this". Gathering scattered sections into thematic files would mean reordering
the code, and then the result could no longer be checked by comparing it with
what we have. A contiguous cut can be: assemble.py must reproduce the input
byte for byte or the cut is wrong.
"""
import os, sys

SRC = "hlp_shooter_v126_logic.html"

# start line (1 based, inclusive) -> file name. The last entry runs to the
# line before tail.html starts.
PARTS = [
    (41,    "10_core.js",    "canvas, resolution, stored settings, palette, fonts"),
    (239,   "20_render.js",  "surface kit, sprites, masks, nebula, bodies, stars, particles"),
    (1228,  "30_waves.js",   "eras, campaign, spawn options, wave plan, scripted waves"),
    (3531,  "40_world.js",   "enemy factory, damage, shields, station keeping, tickets, escorts"),
    (5703,  "50_combat.js",  "asteroids, flight, targeting, subsystems, beams, armament"),
    (8229,  "60_effects.js", "hit effects, explosions, collision, the update pass"),
    (9274,  "70_ui.js",      "the draw pass, bar, panels, title, game over, input"),
]
HEAD_END = 40      # lines 1..40 are the shell before <script>
TAIL_START = 11763 # </script> onwards


def main():
    lines = open(SRC, encoding="utf-8").read().split("\n")
    os.makedirs("src", exist_ok=True)

    open("src/00_head.html", "w", encoding="utf-8").write("\n".join(lines[:HEAD_END]))
    open("src/99_tail.html", "w", encoding="utf-8").write("\n".join(lines[TAIL_START-1:]))

    bounds = [p[0] for p in PARTS] + [TAIL_START]
    for i, (start, name, what) in enumerate(PARTS):
        end = bounds[i+1]
        body = "\n".join(lines[start-1:end-1])
        open("src/"+name, "w", encoding="utf-8").write(body)
        print("%-16s Zeilen %5d-%5d  %5d Zeilen  %s" % (name, start, end-1, end-start, what))

    print("\nsrc/00_head.html  Zeilen     1-%5d" % HEAD_END)
    print("src/99_tail.html  Zeilen %5d-%5d" % (TAIL_START, len(lines)))


if __name__ == "__main__":
    main()
