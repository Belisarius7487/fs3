#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FS3  v86 -> v87

Eine Welle mit querenden Schuetzlingen endete, sobald der letzte Gegner
fiel - egal wo die Frachter gerade waren. Grund: die Endbedingung lautet
"Warteschlange leer und kein Gegner mehr im Feld", und Schuetzlinge stehen
in allies, die liveThreatCount() nicht zaehlt.
"""
import io, os, sys
SRC="hlp_shooter_v86_logic.html"; DST="hlp_shooter_v87_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

sub("cross-pending",
"""let crossDone = 0, crossTotal = 0;""",
"""let crossDone = 0, crossTotal = 0;
// Ist noch ein Schuetzling unterwegs? Abgeschossene stehen nicht mehr in
// allies, die Welle haengt also nicht, wenn einer verloren geht.
function crossPending(){
  for(const a of allies) if(a.crossing && !a.dead) return true;
  return false;
}""")

sub("cross-endcond",
"""    if(transitSecs>0 ? guardGone
       : (disableTarget ? disableDone()
          : (!spawnQ.length&&!liveThreatCount()))){""",
"""    if(transitSecs>0 ? guardGone
       : (disableTarget ? disableDone()
          : (!spawnQ.length && !liveThreatCount() && !crossPending()))){""")

def main():
    if not os.path.exists(SRC): sys.exit("FEHLT: "+SRC)
    txt=io.open(SRC,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(DST,"w",encoding="utf-8").write(txt)
    print("\ngeschrieben: %s  (%.2f MB)"%(DST,os.path.getsize(DST)/1048576.0))
main()
