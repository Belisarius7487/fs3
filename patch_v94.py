#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v93 -> v94: elf Fehler, dazu entkommende Gegner und zwei Missionen."""
import io, os, sys
SRC="hlp_shooter_v93_logic.html"; DST="hlp_shooter_v94_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── Asteroiden: Feld statt Tabelle ───────────────────────────
# Meine Formel setzte sie auf drei x-Spalten und eine gleichmaessige
# y-Leiter. Ein Feld ist zufaellig, und es steht von der ersten Sekunde an.
sub("ast-scatter",
"""    const stagger = (fix==='ast') ? 10 : 0;""",
"""    const stagger = 0;   // alles steht ab dem ersten Bild da""")
sub("ast-pos",
"""    const yy = (u.y!=null) ? u.y : H*(0.20+0.60*((i+0.5)/n));
    const xx = (u.x!=null) ? u.x : W*(0.55+0.12*(i%3));""",
"""    // Brocken streuen ueber das ganze Feld, alles andere bleibt rechts.
    const yy = (u.y!=null) ? u.y
             : (fix==='ast' ? HUD_H+24+Math.random()*(H-HUD_H-48)
                            : H*(0.18+0.64*((i+0.5)/n)));
    const xx = (u.x!=null) ? u.x
             : (fix==='ast' ? W*0.18+Math.random()*W*0.78
                            : W*(0.52+0.30*Math.random()));""")

# Der Asteroidenstrom laeuft unabhaengig weiter und wirft Brocken bei W+30
# ein. Mit stehendem Feld haben die die Geschwindigkeit null und bleiben
# dort fuer immer liegen - unsichtbar, aber treffbar.
sub("ast-stream-off",
"""  astStill = !!def.stillRocks;""",
"""  astStill = !!def.stillRocks;
  // Ein stehendes Feld wird gesetzt, nicht gespeist. Sonst sammeln sich
  // unbewegliche Brocken ausserhalb des rechten Randes.
  astStreamCd = astStill ? 1e9 : AST_STREAM_MEAN;""")

# ── Staffelschleuse auch in geschriebenen Wellen ─────────────
# Sie laesst die naechste Staffel erst herein, wenn das Feld frei ist.
# Abgeschaltet kamen alle nach Uhr - daher die Wartezeiten und die
# gleichzeitigen Einfluege.
sub("gate-on",
"""  guardWanted=false; guardSpawned=false; guardLost=false; guardGone=false;
  astAim=false; transitSecs=0; gateWings=false; gateWing=0;""",
"""  guardWanted=false; guardSpawned=false; guardLost=false; guardGone=false;
  // Schleuse an: die naechste Staffel wartet auf ein freies Feld statt auf
  // die Uhr. Auf einer Querung muss sie aus sein, sonst blockiert die
  // erste Staffel sich selbst - dort gibt es kein freies Feld.
  astAim=false; transitSecs=0; gateWings=!def.crossEnds; gateWing=0;""")

# ── Ausloeser duerfen nicht feuern, bevor es etwas gibt ──────
# "Auftrag erfuellt" war zu Wellenbeginn wahr: es gab noch keinen
# Container, also auch nichts zu scannen. Die Gegner warpten sofort ein.
sub("erfuellt-guard",
"""    case 'erfuellt':     return !objectiveText();""",
"""    case 'erfuellt':
      // Zu Wellenbeginn ist noch nichts im Feld, und "nichts zu tun" sieht
      // aus wie "erledigt". Erst wenn der Auftrag einmal bestanden hat.
      if(!objSeenOnce) return false;
      if(spawnQ.length) return false;
      return !objectiveText();""")
sub("objseen-var",
"""let astStill = false;""",
"""let astStill = false;
// Hat der Auftrag in dieser Welle ueberhaupt schon einmal gegolten?
let objSeenOnce = false;""")
sub("objseen-set",
"""  const ob=objectiveText();
  if(ob){
    txt=ob.txt; col=ob.col; ink=ob.ink;
    objWasSet = true;""",
"""  const ob=objectiveText();
  if(ob){
    txt=ob.txt; col=ob.col; ink=ob.ink;
    objWasSet = true; objSeenOnce = true;""")
sub("objseen-reset",
"""  objWasSet=false; objDoneT=0; objFailed=false;""",
"""  objWasSet=false; objDoneT=0; objFailed=false; objSeenOnce=false;""")

# ── Die Welle darf nicht enden, solange ein Ereignis noch wirken kann ──
# In M014 starb die letzte Gegnerstaffel, die Wellenendpruefung lief im
# selben Bild vor tickEvents - und der Ueberlaeufer wechselte erst danach.
sub("pending-events",
"""function crossPending(){""",
"""// Steht noch ein Ereignis aus, das Schiffe ins Feld bringt oder die Seite
// wechselt? Dann ist die Welle nicht vorbei, auch wenn gerade nichts lebt.
function evPending(){
  for(const e of EV)
    if(!e.done && (e.w==='einwarpen' || e.w==='seite' || e.w==='nachschub')) return true;
  return false;
}
function crossPending(){""")
sub("endcond-ev",
"""          : (!spawnQ.length && !liveThreatCount() && !crossPending()))){""",
"""          : (!spawnQ.length && !liveThreatCount() && !crossPending() && !evPending()))){""")

# ── Grosskampfschiffe derselben Kennung bekommen eigene Hoehenbaender ──
# Ohne sie wandern sie durch das ganze Feld und prallen aneinander ab.
sub("cap-band",
"""             capBack:(n>1)? i*86 : 0});""",
"""             capBack:(n>1)? i*86 : 0,
             bandY:(n>1)? [H*(0.16+0.68*(i/n))+30, H*(0.16+0.68*((i+1)/n))-30] : null});""")
sub("cap-band-apply",
"""  if(sp.capBack && e.targetX!=null) e.targetX -= sp.capBack;""",
"""  if(sp.capBack && e.targetX!=null) e.targetX -= sp.capBack;
  // Eigenes Hoehenband, damit mehrere Schiffe derselben Kennung nicht
  // durch dasselbe Feld wandern und aneinander abprallen.
  if(sp.bandY){ e.minY = sp.bandY[0]; e.maxY = sp.bandY[1];
                e.y = (e.minY+e.maxY)/2; e.warpY = e.y; }""")
# Der vorderste Kreuzer stand zu weit links, dadurch war es rechts zu eng.
sub("cr-station",
"""      pts:400,x:W-20,y,warpX:W-20,warpY:y,targetX:W-150-Math.random()*40,""",
"""      pts:400,x:W-20,y,warpX:W-20,warpY:y,targetX:W-118-Math.random()*40,""")

# ── Gegner, die nach rechts entkommen ───────────────────────
# Neue Vokabel fuer M004 und M025: ein Schiff, das das Feld nach rechts
# verlaesst, ist entkommen - das kostet Punkte und endet die Welle.
sub("escape-const",
"""const GUARD_PENALTY = 900;""",
"""const GUARD_PENALTY = 900;
// Ein entkommener Gegner kostet, was er wert gewesen waere, noch einmal.
const ESCAPE_PENALTY = 1.0;""")
sub("escape-tick",
"""function tickCrossGuards(){""",
"""// Gegner mit Fluchtkurs nach rechts. Erreichen sie den Rand, sind sie weg.
let escTotal = 0, escGone = 0;
function tickEscapers(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(!e.escaping || e.dead || e.warp>0) continue;
    e.x += e.escaping;
    if(e.x > W+70){
      escGone++;
      EV_LEFT[e.uid] = true;
      score = Math.max(0, score - Math.round((e.pts||200)*ESCAPE_PENALTY));
      SUB_MSGS.push({x:W-110, y:e.y, txt:'TARGET ESCAPED', life:170, ml:170, ally:false});
      enemies.splice(i,1);
    }
  }
}
function tickCrossGuards(){""")
sub("escape-call",
"""  tickCrossGuards();""",
"""  tickEscapers();
  tickCrossGuards();""")
sub("escape-apply",
"""  if(sp.disable) e.noFlee = true;""",
"""  if(sp.escape){
    e.escaping = sp.escape;          // Bildpunkte je Schritt nach rechts
    e.noFlee = true;                 // sie springt nicht, sie faehrt
    e.targetX = null; e.vy = 0;
    e.flip = needsFlip(e.img, false);
  }
  if(sp.disable) e.noFlee = true;""")
sub("escape-q",
"""          : {time:t0+i*140, type:ty, spr:u.spr||'', y:yy, x:u.x,""",
"""          : {time:t0+i*140, type:ty, spr:u.spr||'', y:yy, x:u.x, escape:u.escape,""")
sub("escape-q2",
"""      put({time:t0+i*stagger, type:fix, spr:u.spr||'', fac:fac, noWarp:(fix!=='ast')?1:0,
           x:xx, y:yy, scan:u.scan?1:0});""",
"""      put({time:t0+i*stagger, type:fix, spr:u.spr||'', fac:fac, noWarp:(fix!=='ast')?1:0,
           x:xx, y:yy, scan:u.scan?1:0, escape:u.escape});""")
sub("escape-count",
"""  waveHunt = def.hunt || '';""",
"""  escTotal = 0; escGone = 0;
  for(const u of (def.u||[])) if(u.escape) escTotal += (u.n||1);
  waveHunt = def.hunt || '';""")
# Eine Fluchtwelle endet, wenn keiner mehr da ist - zerstoert oder entkommen.
sub("escape-end",
"""  for(const e of EV)
    if(!e.done && (e.w==='einwarpen' || e.w==='seite' || e.w==='nachschub')) return true;
  return false;
}""",
"""  for(const e of EV)
    if(!e.done && (e.w==='einwarpen' || e.w==='seite' || e.w==='nachschub')) return true;
  return false;
}
// Ist noch ein Fluechtling unterwegs? Dann laeuft die Welle, auch wenn
// sonst nichts mehr im Feld steht.
function escPending(){
  for(const e of enemies) if(e.escaping && !e.dead) return true;
  return false;
}""")
sub("escape-endcond",
"""!crossPending() && !evPending()))){""",
"""!crossPending() && !evPending() && !escPending()))){""")

def main():
    if not os.path.exists(SRC): sys.exit("FEHLT: "+SRC)
    txt=io.open(SRC,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(DST,"w",encoding="utf-8").write(txt)
    print("geschrieben: "+DST)
main()
