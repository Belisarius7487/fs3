#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v102 -> v103: non-combatants can only be damaged by the player.

Decision (Silvio, v103): cargo containers, escape pods and unarmed freighters
on the hostile side are never targeted by allied weapons, and allied fire
passes through them. Hostile fire on the player's own protected ships is
unchanged - defending those is the point of those missions.

Background: in M023 allied fighters and cruisers shot the hostile cargo that
was to be scanned and picked up. Scan containers already carried noTarget,
but allied fighters use nearestOf(), which ignored it, and stray bolts hit
anything in their path.
"""
import io, os, sys
SRC = "hlp_shooter_v102_logic.html"; DST = "hlp_shooter_v103_logic.html"
edits = []
def sub(t, a, b): edits.append((t, a, b))

# ── 1. One rule, in one place ──────────────────────────────────
sub("rule",
"""function nearestEnemy(x, y){""",
"""// Non-combatants: cargo containers, escape pods (both spawn as type
// container) and freighters. Freighters have no entry in WPN and never fire;
// should one ever get guns, it drops out of this rule on its own.
// Only the player may damage these. Allied weapons never pick them as a
// target and allied fire passes through them.
function playerOnly(o){
  if(!o) return false;
  if(o.type==='container') return true;
  return o.type==='freighter' && !WPN[o.type];
}

function nearestEnemy(x, y){""")

# ── 2. Targeting ───────────────────────────────────────────────
# nearestEnemy() serves allied guns, allied capital turrets and allied
# secondaries only.
sub("target-nearest",
"""    if(o.noTarget) continue;
    const d=(o.x-x)**2 + (o.y-y)**2;""",
"""    if(o.noTarget || playerOnly(o)) continue;
    const d=(o.x-x)**2 + (o.y-y)**2;""")

# nearestOf() is shared by both sides. Only its search through the hostile
# list is an allied search.
sub("target-nearestof",
"""    if(want==='bomber' && o.type!=='bomber') continue;""",
"""    if(want==='bomber' && o.type!=='bomber') continue;
    if(list===enemies && playerOnly(o)) continue;""")

# Allied missiles homed onto whatever hostile ship was nearest.
sub("target-homing",
"""        if(!canLockOn(enemies[j])) continue;   // stealth hulls cannot be held""",
"""        if(!canLockOn(enemies[j])) continue;   // stealth hulls cannot be held
        if(b.ally && playerOnly(enemies[j])) continue;""")

# ── 3. Hits ────────────────────────────────────────────────────
# Secondaries (missiles and bombs) from the player's bullet list.
sub("hit-secondary",
"""        if(!bulletOnHull(e,b)) continue;   // impact landed on empty space
        e.shotAt=true;
        damageEnemy(e,b.dmg,b.x,b.y,!b.ally,'sec');""",
"""        if(!bulletOnHull(e,b)) continue;   // impact landed on empty space
        if(b.ally && playerOnly(e)) continue;   // allied fire passes through
        e.shotAt=true;
        damageEnemy(e,b.dmg,b.x,b.y,!b.ally,'sec');""")

# Bolts from the player's bullet list.
sub("hit-bolt",
"""        if(!bulletOnHull(e,b)) continue;   // impact landed on empty space
        laserHit(b.x,b.y);""",
"""        if(!bulletOnHull(e,b)) continue;   // impact landed on empty space
        if(b.ally && playerOnly(e)) continue;   // allied fire passes through
        laserHit(b.x,b.y);""")

# Feuding hostile factions: not the player either.
sub("hit-feud",
"""        if(o.type==='asteroid') continue;
        if(!o.faction || o.faction===b.faction) continue;""",
"""        if(o.type==='asteroid' || playerOnly(o)) continue;
        if(!o.faction || o.faction===b.faction) continue;""")

def main():
    if not os.path.exists(SRC): sys.exit("MISSING: "+SRC)
    txt = io.open(SRC, encoding="utf-8").read()
    for t, a, b in edits:
        n = txt.count(a)
        if n != 1: sys.exit("ABORT %s: %d matches instead of 1" % (t, n))
        txt = txt.replace(a, b, 1); print("  ok   "+t)
    io.open(DST, "w", encoding="utf-8").write(txt)
    print("written: "+DST)
main()
