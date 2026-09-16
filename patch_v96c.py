#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v96 Teil C: Bahnen fuer mehrere Grosskampfschiffe, invuln ohne Balken."""
import io, os, sys
F="hlp_shooter_v96_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# Bahnen: alle nutzen die volle Hoehe, aber zeitversetzt und in
# wechselnder Richtung. Der Startversatz allein hat nicht gereicht, weil
# sie sich nach einer halben Bahn wieder eingeholt haben.
sub("lanes-q",
"""             phaseY:(n>1)? (i/n) : 0});""",
"""             phaseY:(n>1)? (i/n) : 0, lane:(u.lanes&&n>1)? (i/n) : 0});""")
sub("lanes-apply",
"""  if(sp.phaseY){""",
"""  // Eigene Bahn: volle Hoehe, aber gegenlaeufig und mit festem Vorlauf.
  // Zwei Schiffe mit gleicher Richtung holen sich sonst wieder ein.
  if(sp.lane){
    e.y = e.minY + (e.maxY-e.minY)*sp.lane;
    e.warpY = e.y;
    const dir = (Math.round(sp.lane*4) % 2) ? -1 : 1;
    e.vy = dir * (0.22 + sp.lane*0.20);
  }
  if(sp.phaseY && !sp.lane){""")

# Eine unverwundbare Station braucht keine Rumpfanzeige - sie kann nicht
# fallen, und ein voller Balken sagt nichts.
sub("invuln-nobar",
"""function drawHullBlocks(e, bx, by, bw, ratio, showShield){""",
"""function drawHullBlocks(e, bx, by, bw, ratio, showShield){
  if(e.invuln) return;""")

# Der Ausloeser "Subsystem zerstoert" stand in der Liste der acht, war aber
# nie umgesetzt. M007 benutzt ihn fuer den Funkraum der Typhon.
sub("trig-subsystem",
"""    case 'erfuellt':""",
"""    case 'subsystem': {
      const su = byId(ev.a)[0];
      if(!su || !hasSubsystems(su)) return false;
      return !subOK(su, ev.b || 'communication');
    }
    case 'erfuellt':""")

def main():
    txt=io.open(F,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(F,"w",encoding="utf-8").write(txt)
    print("Teil C geschrieben")
main()
