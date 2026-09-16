#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v97 -> v98: Wackeln raus, M022, Rammkreuzer, Rettungskapseln, vier Missionen."""
import io, os, sys
SRC="hlp_shooter_v97_logic.html"; DST="hlp_shooter_v98_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── Bildschirmwackeln bei Explosionen aus ──────────────────────────
# Eine Stelle statt neun: addShake wird zum Leerlauf. Die Aufrufe bleiben
# stehen, damit spaeter nur eine Zeile zurueckgenommen werden muss, wenn
# du es doch wieder willst.
sub("shake-off",
"""function addShake(mag, dur){""",
"""// Bildschirmwackeln abgeschaltet. Bei jeder Explosion zu wackeln ist auf
// Dauer eher stoerend als wirkungsvoll. Eine Zeile statt neun Aufrufen,
// damit es sich mit einem Schnitt zurueckholen laesst.
const SHAKE_ON = false;
function addShake(mag, dur){
  if(!SHAKE_ON) return;""")

# ── M022: die Typhon parkte knapp vor der Schwelle ────────────────
# Ich hatte targetX auf W+200 gesetzt, die Wegschwelle aber auf
# W + Breite*0.6. Bei 394 Bildpunkten Breite sind das W+236 - die Fahrt
# eines Grosskampfschiffs stoppt bei targetX, also 36 Bildpunkte davor.
# Sie blieb ausserhalb des Bildes stehen und galt nie als entkommen.
sub("escape-target2",
"""    e.targetX = W + 200;   // nicht null: null wird beim Vergleich zu 0""",
"""    // Weit hinter der Wegschwelle: die Fahrt stoppt bei targetX, und wenn
    // targetX davor liegt, parkt das Schiff ausserhalb des Bildes.
    const _si = IMGS[e.img];
    const _sw = _si ? _si.width*e.sc : 120;
    e.targetX = W + _sw*2;""")
sub("escape-thresh",
"""    const _ei = IMGS[e.img];
    const _ew = _ei ? _ei.width*e.sc : 120;
    if(e.x > W + _ew*0.6){""",
"""    const _ei = IMGS[e.img];
    const _ew = _ei ? _ei.width*e.sc : 120;
    // Ganz draussen heisst: die linke Kante hat den rechten Rand passiert.
    if(e.x - _ew*0.5 > W + 8){""")

# ── Rammende Grosskampfschiffe ────────────────────────────────────
# Bisher rammten nur Jaeger und Bomber. Ein Kreuzer, der sich in ein
# Grosskampfschiff stuerzt, ist dieselbe Vokabel eine Nummer groesser.
sub("capram-const",
"""const RAM_PCT_BOMBER  = 0.04;""",
"""// Ein Kreuzer, der rammt, nimmt sein Ziel zu einem Drittel mit. Er ist
// kein Jaeger: das soll den Kampf entscheiden, nicht anknabbern.
const RAM_PCT_CAPITAL = 0.34;
const RAM_PCT_BOMBER  = 0.04;""")
sub("capram-tick",
"""function tickDeathRoll(){""",
"""// Grosskampfschiff auf Rammkurs. Es sucht sich das naechste verbuendete
// Grosskampfschiff, faehrt darauf zu und schlaegt ein.
function tickCapRam(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(!e.capRam || e.dead || e.warp>0 || e.rollT!=null) continue;
    let t=null, bd=1e9;
    for(const a of allies){
      if(a.dead || a.small) continue;
      const d=(a.x-e.x)*(a.x-e.x)+(a.y-e.y)*(a.y-e.y);
      if(d<bd){ bd=d; t=a; }
    }
    if(!t) continue;
    // Direkter Kurs, ohne Halteposition - er will nicht schiessen.
    e.targetX = null;
    const dx=t.x-e.x, dy=t.y-e.y, L=Math.hypot(dx,dy)||1;
    e.x += dx/L*e.capRam;
    e.y += dy/L*e.capRam;
    const ei=IMGS[e.img], ti=IMGS[t.img];
    const need=((ei?ei.width*e.sc:100)+(ti?ti.width*t.sc:100))*0.30;
    if(L < need){
      t.hp -= Math.max(1, Math.round((t.maxHp||100)*RAM_PCT_CAPITAL));
      hullHit(e.x, e.y);
      triggerExpl(e.x, e.y, 'destroyer', e.faction, e);
      spawnShock(e.x, e.y, 170, 3.0, 0.024);
      SUB_MSGS.push({x:e.x, y:e.y-40, txt:'IMPACT', life:150, ml:150, ally:false});
      e.dead = true; e.hp = 0;
      enemies.splice(i,1);
    }
  }
}
function tickDeathRoll(){""")
sub("capram-call",
"""  tickDeathRoll();""",
"""  tickCapRam();
  tickDeathRoll();""")
sub("capram-apply",
"""  if(sp.scenery) e.scenery = true;""",
"""  if(sp.scenery) e.scenery = true;
  if(sp.capRam){ e.capRam = sp.capRam; e.noFlee = true; }""")
sub("capram-q",
"""             x:u.x, escape:u.escape, invuln:u.invuln, edge:u.edge,""",
"""             x:u.x, escape:u.escape, invuln:u.invuln, edge:u.edge, capRam:u.capRam,""")

# ── Rettungskapseln ───────────────────────────────────────────────
# Klasse ep war nie spawnbar. Eine Kapsel ist wehrlos, treibt nach rechts
# und stirbt an einem Streifschuss - deshalb der Containerzweig und nicht
# der Frachterzweig.
sub("pod-cat",
"""const CAT_FIX = {sg:'sentry', fc:'container', fr:'freighter', tr:'freighter', ast:'ast'};""",
"""const CAT_FIX = {sg:'sentry', fc:'container', fr:'freighter', tr:'freighter',
                 ast:'ast', ep:'container'};""")
sub("pod-protect",
"""function protectType(spr){
  return hullClass(spr)==='fc' ? 'container' : 'freighter';
}""",
"""function protectType(spr){
  const c = hullClass(spr);
  // Container und Rettungskapseln sind wehrlos und duenn. Ein Frachter
  // haelt etwas aus, eine Kapsel nicht - das ist der Punkt.
  return (c==='fc' || c==='ep') ? 'container' : 'freighter';
}""")

def main():
    if not os.path.exists(SRC): sys.exit("FEHLT: "+SRC)
    txt=io.open(SRC,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(DST,"w",encoding="utf-8").write(txt)
    print("Teil A geschrieben")
main()
