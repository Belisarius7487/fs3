#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FS3  v83 -> v84

  1  Sperrgeschuetze bekommen einen eigenen Boden statt des Jaegerbodens
  2  Manticore zehn Prozent kleiner
  3  Schuetzlinge koennen das Feld queren statt darin herumzustehen

Kein Ereignissystem, kein Andocken - die kommen, sobald die geschriebenen
Missionen zeigen, welche Vokabeln wirklich gebraucht werden.
"""

import io, os, sys

SRC = "hlp_shooter_v83_logic.html"
DST = "hlp_shooter_v84_logic.html"

edits = []
def sub(tag, old, new):
    edits.append((tag, old, new))


# ─────────────────────────────────────────────────────────────
# 1  Sperrgeschuetze
#
# Der Boden aus v81 haengt an der Jaegergroesse: nichts wird kleiner
# gezeichnet als ein Jaeger, wenn es laenger ist als einer. Fuer Schiffe
# stimmt das, fuer Geschuetztuerme nicht - die vergleicht niemand mit einem
# Jaeger. Das Belial ist 22 m lang und landete damit auf 60, die Trident
# mit 11 m auf 41. Mit eigenem Boden von 30:
#   Cerberus 9 m, Watchdog 9 m, Ankh 10 m, Trident 11 m,
#   Alastor 13 m, Belial 22 m  ->  alle 30
#   Mjolnir 108 m              ->  58, die Kurve gewinnt
# ─────────────────────────────────────────────────────────────
sub("sg-floor",
"""const SIZE_FIXED = {sdcolossus: 556};
const SIZE_CLASS_FIXED = {fi: 60, bo: 65, ep: 60};""",
"""// Die Manticore fuellt bei gleicher Breite mehr Flaeche als die uebrigen
// Jaeger und wirkt dadurch massiger. Zehn Prozent schmaler.
const SIZE_FIXED = {sdcolossus: 556, fimanticore: 54};
const SIZE_CLASS_FIXED = {fi: 60, bo: 65, ep: 60};
// Eigener Boden je Klasse, wo der Jaegerboden nicht passt. Ein
// Geschuetzturm ist kein Schiff und wird nicht mit einem Jaeger verglichen.
const SIZE_CLASS_MIN = {sg: 30};""")

sub("sg-floor-use",
"""  const curve = SIZE_K*Math.pow(L, SIZE_E);
  const floor = Math.min(SIZE_REF_W, SIZE_REF_W*Math.pow(L/SIZE_REF_L, SIZE_E));
  return Math.round(Math.min(SIZE_MAX, Math.max(floor, curve)));""",
"""  const curve = SIZE_K*Math.pow(L, SIZE_E);
  const floor = (SIZE_CLASS_MIN[c] != null)
    ? SIZE_CLASS_MIN[c]
    : Math.min(SIZE_REF_W, SIZE_REF_W*Math.pow(L/SIZE_REF_L, SIZE_E));
  return Math.round(Math.min(SIZE_MAX, Math.max(floor, curve)));""")

# ─────────────────────────────────────────────────────────────
# 2  Querende Schuetzlinge
#
# spawnProtected() nagelt den Schuetzling fest: vx=0 und minY=maxY, weil
# updateAllies() die Senkrechte sonst verschiebt. Zwei Poseidon, die
# reglos im Feld stehen, sehen nach Kulisse aus und nicht nach Konvoi.
#
# Mit cross bewegen sie sich waagerecht von links nach rechts. Die
# Senkrechte bleibt gepinnt, damit updateAllies() nicht dagegenarbeitet,
# und die Waagerechte laeuft ueber einen eigenen Tick statt ueber vx - so
# gibt es nichts, was sie ueberschreiben koennte.
# ─────────────────────────────────────────────────────────────
sub("cross-spawn",
"""  a.vx = 0; a.vy = 0;
  a.minY = a.y; a.maxY = a.y;      // updateAllies() nudges vy, so pin it
  a.warp = 0; a.warpMax = 1;
  a.flip = needsFlip(a.img, false);
  if(sp.x != null) a.x = sp.x;
  allies.push(a);""",
"""  a.vx = 0; a.vy = 0;
  a.minY = a.y; a.maxY = a.y;      // updateAllies() nudges vy, so pin it
  a.warp = 0; a.warpMax = 1;
  a.flip = needsFlip(a.img, false);
  if(sp.x != null) a.x = sp.x;
  if(sp.cross){
    a.crossing = sp.cross;         // Bildpunkte je Schritt
    a.flip = needsFlip(a.img, true);
    if(sp.x == null) a.x = -40;    // von links herein
  }
  allies.push(a);""")

sub("cross-tick",
"""function tickDefectors(){""",
"""// Waagerechte Fahrt eines Schuetzlings. Verlaesst er rechts das Feld, ist
// er durchgebracht: er wird still entfernt, ohne guardLost zu setzen -
// sonst zaehlte der Erfolg als Verlust.
let crossDone = 0, crossTotal = 0;
function tickCrossGuards(){
  for(let i=allies.length-1;i>=0;i--){
    const a = allies[i];
    if(!a.crossing || a.dead) continue;
    a.x += a.crossing;
    if(a.x > W+60){
      crossDone++;
      allies.splice(i,1);
      SUB_MSGS.push({x:W-90, y:a.y, txt:'DELIVERED', life:150, ml:150, ally:true});
    }
  }
  // Sind alle durch, ist der Auftrag erfuellt und die Welle raeumt nur noch auf.
  if(crossTotal && crossDone >= crossTotal) guardGone = true;
}

function tickDefectors(){""")

sub("cross-call",
"""  tickDefectors();""",
"""  tickDefectors();
  tickCrossGuards();""")

# Zaehler je Welle zuruecksetzen
sub("cross-reset",
"""  waveTitle=''; titleT=0;
  objWasSet=false; objDoneT=0;""",
"""  waveTitle=''; titleT=0;
  objWasSet=false; objDoneT=0;
  crossDone=0; crossTotal=0;""")

# Der Auftrag protect setzt sie jetzt als Querung
sub("cross-objective",
"""  if(o==='protect'){
    for(const pair of (spec0.ships||[]))
      for(let i=0;i<pair[1];i++)
        q.push({time:1, type:'protect', spr:pair[0], fac:'terran', noWarp:1,
                x:W*(0.28+0.10*i), y:H*(0.34+0.18*i)});
  }""",
"""  if(o==='protect'){
    // Leicht versetzt, damit zwei Frachter nicht als Block wirken.
    for(const pair of (spec0.ships||[]))
      for(let i=0;i<pair[1];i++){
        q.push({time:1+i*90, type:'protect', spr:pair[0], fac:'terran', noWarp:1,
                cross:PROTECT_CROSS_SPD, x:-40-i*70, y:H*(0.34+0.16*i)});
        crossTotal++;
      }
  }""")

sub("cross-speed",
"""const GUARD_PENALTY = 900;""",
"""const GUARD_PENALTY = 900;
// Fahrt eines querenden Schuetzlings, Bildpunkte je Schritt. Bei 100
// Schritten je Sekunde sind 0.42 rund 42 px/s, also gut 20 Sekunden fuer
// die 880 Bildpunkte von links aussen bis rechts hinaus. Lange genug, um
// ihn verlieren zu koennen, kurz genug, um nicht zu warten.
const PROTECT_CROSS_SPD = 0.42;""")

# cross wird ueber _sp durchgereicht, spawnProtected bekommt den ganzen
# Warteschlangeneintrag - kein Patch noetig.


def main():
    if not os.path.exists(SRC):
        sys.exit("FEHLT: " + SRC)
    txt = io.open(SRC, "r", encoding="utf-8").read()
    for tag, old, new in edits:
        n = txt.count(old)
        if n != 1:
            sys.exit("ABBRUCH %s: %d Treffer statt 1" % (tag, n))
        txt = txt.replace(old, new, 1)
        print("  ok   " + tag)
    io.open(DST, "w", encoding="utf-8").write(txt)
    print("\ngeschrieben: %s  (%.2f MB)" % (DST, os.path.getsize(DST)/1048576.0))


if __name__ == "__main__":
    main()
