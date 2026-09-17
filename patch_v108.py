#!/usr/bin/env python3
"""FS3 v108 - M017 "Die Tsunami".

The thirtieth and last missing mission of the Hammer of Light cycle.

An Aten and a Mentu stand in the field from the start, but a fighter cannot
crack them in reasonable time. Three wings of three fighters come first,
each called in by the previous one falling. Only when the third wing is gone
does an allied Typhon warp in, and she is what opens the hangar: with a
destroyer of his own faction on the field the player can switch to a bomber
and bring the heavy secondary to bear on the two cruisers.

That ordering is deliberate. The objective stays one thing - clear the field
- and the bomber is the means, not a second task. No follow up wing hangs on
the clock; every one of them hangs on an event.

Reads hlp_shooter_v107_logic.html, writes hlp_shooter_v108_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v107_logic.html", "hlp_shooter_v108_logic.html"

M017 = """  17:{name:'Die Tsunami', fac:'hol', o:'clear', live:6, u:[
       {id:'K1', c:'cr', n:1, spr:'craten'},
       {id:'K2', c:'cr', n:1, spr:'crmentu'},
       {id:'E1', c:'fi', n:3},
       {id:'E2', c:'fi', n:3, wait:true},
       {id:'E3', c:'fi', n:3, wait:true},
       {id:'A1', c:'de', n:1, spr:'detyphon', side:'ally', wait:true}
      ], ev:[
        // Three wings, each one called in by the last one falling. Nothing
        // here hangs on the clock.
        {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
        {t:'alleZerstoert', a:'E2', w:'einwarpen', a2:'E3'},
        // The Typhon arrives last, and she is the hangar: only with a
        // Vasudan destroyer on the field can the player take a bomber, and
        // only a bomber cracks the two cruisers in reasonable time.
        {t:'alleZerstoert', a:'E3', w:'einwarpen', a2:'A1'},
        {t:'alleZerstoert', a:'E3', w:'meldung',   a2:'GVD Typhon inbound - hangar open'}
      ]},

"""


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

if "17:{name:" in src:
    sys.exit("Abbruch: M017 ist schon vorhanden.")

src = replace_once(
    src,
    "  18:{name:'Tenderizer', fac:'hol', o:'guard', live:6,",
    M017 + "  18:{name:'Tenderizer', fac:'hol', o:'guard', live:6,",
    "insert M017",
)

if "17:{name:'Die Tsunami'" not in src:
    sys.exit("Abbruch: M017 fehlt im Ergebnis.")

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
