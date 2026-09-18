#!/usr/bin/env python3
"""FS3 v122 - the rearm button answers to being pressed.

The button was drawn, it lit when a corvette was on the field, and it
reported its rectangle in window._rearmBtnRect. Nothing ever read that
rectangle. pointerConsumed handled the ship switch button on the line above
and simply had no case for this one, so pressing it did nothing at all.

The simulation missed it because it opened the panel by calling
toggleRearmMenu() directly. That tests the panel and not the button. It now
presses the rectangle the bar reports, which is what a player does.

Reads hlp_shooter_v121_logic.html, writes hlp_shooter_v122_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v121_logic.html", "hlp_shooter_v122_logic.html"

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)

src = open(SRC, encoding="utf-8").read()

src = replace_once(
    src,
    "  var rsw=window._shipBtnRect;\n"
    "  if(rsw&&p.x>=rsw.x&&p.x<=rsw.x+rsw.w&&p.y>=rsw.y&&p.y<=rsw.y+rsw.h){ toggleShipMenu(); return true; }",
    "  var rsw=window._shipBtnRect;\n"
    "  if(rsw&&p.x>=rsw.x&&p.x<=rsw.x+rsw.w&&p.y>=rsw.y&&p.y<=rsw.y+rsw.h){ toggleShipMenu(); return true; }\n"
    "  // The rearm button sits beside it and was drawn without ever being\n"
    "  // asked about here, so it lit up and did nothing.\n"
    "  var rrm=window._rearmBtnRect;\n"
    "  if(rrm&&p.x>=rrm.x&&p.x<=rrm.x+rrm.w&&p.y>=rrm.y&&p.y<=rrm.y+rrm.h){ toggleRearmMenu(); return true; }",
    "rearm button tap",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
