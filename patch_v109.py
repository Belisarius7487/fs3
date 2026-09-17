#!/usr/bin/env python3
"""FS3 v109 - two fixes.

1) M017 had n:3 on each of its three fighter units. For c:'fi' the n counts
   WINGS, not ships, and every wing is three or four fighters, so the mission
   fielded nine wings - between 27 and 36 fighters instead of nine. Now n:1
   per unit: three wings, three or four fighters each.

2) The pause flag had four independent writers: the switch menu, the call
   menu, the settings panel and the pause button. pointerConsumed() also runs
   before the gear is even looked at, so a tap meant for the gear first
   counted as a tap outside the switch menu and cleared the pause. Replaying
   tap sequences found 60 of 512 three step sequences that left a panel on
   screen over a running game.

   The flag now has one owner. Panels and the pause button each state their
   own wish and syncPause() derives the result. Two panels can no longer be
   open at once either, which was the other half of the problem.

Reads hlp_shooter_v108_logic.html, writes hlp_shooter_v109_logic.html.
Every search text must occur its expected number of times, otherwise nothing
is written.
"""
import sys

SRC, DST = "hlp_shooter_v108_logic.html", "hlp_shooter_v109_logic.html"


def replace_n(text, old, new, label, times=1):
    n = text.count(old)
    if n != times:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet %d-mal." % (label, n, times))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. M017: n counts wings, not ships ──────────────────────────────
src = replace_n(
    src,
    "       {id:'E1', c:'fi', n:3},\n"
    "       {id:'E2', c:'fi', n:3, wait:true},\n"
    "       {id:'E3', c:'fi', n:3, wait:true},\n"
    "       {id:'A1', c:'de', n:1, spr:'detyphon', side:'ally', wait:true}",
    "       // n counts wings, not ships: one wing is WING_MIN..WING_MAX\n"
    "       // fighters, so three wings of three or four is what arrives.\n"
    "       {id:'E1', c:'fi', n:1},\n"
    "       {id:'E2', c:'fi', n:1, wait:true},\n"
    "       {id:'E3', c:'fi', n:1, wait:true},\n"
    "       {id:'A1', c:'de', n:1, spr:'detyphon', side:'ally', wait:true}",
    "M017 wings",
)

# ── 2. One owner for the pause flag ─────────────────────────────────
src = replace_n(
    src,
    "let paused=false;",
    "let paused=false;\n"
    "// The pause flag has one owner. Panels and the pause button each state\n"
    "// their own wish below and syncPause() derives the result. Assigning\n"
    "// paused from several places is what let a panel sit on screen while the\n"
    "// game kept running: whichever writer ran last won.\n"
    "let userPaused=false;   // the pause button and the P key\n"
    "function syncPause(){\n"
    "  paused = !!(shipMenu || callMenu || settingsOpen || userPaused);\n"
    "}",
    "syncPause",
)

src = replace_n(
    src,
    "function setShipMenu(open){\n  shipMenu = open;\n  paused   = open;",
    "function setShipMenu(open){\n"
    "  shipMenu = open;\n"
    "  // Two panels at once meant closing one took the pause the other still\n"
    "  // needed, so opening one closes the other.\n"
    "  if(open) callMenu = false;\n"
    "  syncPause();",
    "setShipMenu",
)

src = replace_n(
    src,
    "function setCallMenu(open){\n  callMenu = open;\n  paused   = open;",
    "function setCallMenu(open){\n"
    "  callMenu = open;\n"
    "  if(open) shipMenu = false;\n"
    "  syncPause();",
    "setCallMenu",
)

src = replace_n(
    src,
    "// Remembers whether the game was already paused, so closing the panel\n"
    "// restores that state rather than always resuming.\n"
    "let settingsWasPaused=false;\n"
    "function setSettings(v){\n"
    "  v=!!v;\n"
    "  if(v && !settingsOpen){\n"
    "    settingsWasPaused = paused;\n"
    "    if(GS==='playing') paused = true;\n"
    "  } else if(!v && settingsOpen){\n"
    "    if(GS==='playing') paused = settingsWasPaused;\n"
    "  }\n"
    "  settingsOpen=v;",
    "// No need to remember the previous pause any more: closing the panel\n"
    "// simply drops this panel's own reason to pause, and syncPause() works\n"
    "// out whether anything else still wants the game held.\n"
    "function setSettings(v){\n"
    "  v=!!v;\n"
    "  settingsOpen=v;\n"
    "  syncPause();",
    "setSettings",
)

# The pause button, in the mouse handler and both touch handlers.
src = replace_n(
    src,
    "{paused=!paused;return;}}",
    "{userPaused=!userPaused;syncPause();return;}}",
    "pause button",
    times=3,
)

src = replace_n(
    src,
    "    if(paused) paused=false;",
    "    // Tapping the field resumes, but only from a pause the player set;\n"
    "    // a panel keeps its own hold.\n"
    "    if(userPaused){ userPaused=false; syncPause(); }",
    "tap to resume",
)

src = replace_n(
    src,
    "    paused=!paused; ev.preventDefault();",
    "    userPaused=!userPaused; syncPause(); ev.preventDefault();",
    "pause key",
)

# Starting a run or a wave clears every reason to pause.
src = replace_n(
    src,
    "callMenu=false;paused=false;",
    "callMenu=false;shipMenu=false;userPaused=false;paused=false;",
    "resets",
    times=2,
)

if "paused   = open;" in src:
    sys.exit("Abbruch: eine Stelle setzt paused noch direkt aus einem Menue.")
for name in ("function syncPause(", "userPaused"):
    if name not in src:
        sys.exit("Abbruch: '%s' fehlt im Ergebnis." % name)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
