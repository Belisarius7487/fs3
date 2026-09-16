#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v94 -> v95: Fehler, Installationen, vier weitere Missionen."""
import io, os, sys
SRC="hlp_shooter_v94_logic.html"; DST="hlp_shooter_v95_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── M004: die Sobek blieb links kleben ──────────────────────
# Ich hatte targetX auf null gesetzt. Die Fahrt eines Grosskampfschiffs
# vergleicht x mit targetX, und null wird dabei zu 0 - das Schiff steuerte
# also den linken Rand an, waehrend tickEscapers es nach rechts schob.
sub("escape-target",
"""    e.targetX = null; e.vy = 0;""",
"""    e.targetX = W + 200;   // nicht null: null wird beim Vergleich zu 0
    e.vy = 0;""")

# ── M025: Frachter im Rueckwaertsgang ───────────────────────
# Die alte Fluchtmechanik dreht einen beschossenen Frachter nach links.
# Ein Schiff auf Fluchtkurs nach rechts hat damit nichts zu schaffen.
sub("freighter-flee",
"""      if(!e.fleeing && e.shotAt){ e.fleeing=true; e.vx=-1.9; }""",
"""      if(!e.fleeing && e.shotAt && !e.escaping){ e.fleeing=true; e.vx=-1.9; }""")
sub("escape-vx",
"""    e.targetX = W + 200;   // nicht null: null wird beim Vergleich zu 0
    e.vy = 0;""",
"""    e.targetX = W + 200;   // nicht null: null wird beim Vergleich zu 0
    e.vx = 0; e.vy = 0;    // gefahren wird ueber tickEscapers, nicht ueber vx""")

# ── Verbuendete feuern nicht mehr ins Leere ─────────────────
# Ohne Ziel blieb der Winkel null, und damit schossen die Geschuetze stur
# in eine Richtung - bei gespiegeltem Rumpf nach links, obwohl nichts da war.
sub("ally-noshot",
"""      const tg = nearestEnemy(pts[i].x, pts[i].y);
      let ang = 0;
      if(tg){""",
"""      const tg = nearestEnemy(pts[i].x, pts[i].y);
      if(!tg) continue;                 // kein Ziel, kein Schuss
      let ang = 0;
      if(tg){""")

# ── Gesetzte Brocken halten die Welle nicht offen ───────────
# Ein stehendes Feld ist Gelaende. Es zu raeumen kann eine Aufgabe sein,
# aber es darf keine Bedingung fuer das Wellenende sein.
sub("ast-scenery",
"""      put({time:t0+i*stagger, type:fix, spr:u.spr||'', fac:fac, noWarp:(fix!=='ast')?1:0,
           x:xx, y:yy, scan:u.scan?1:0, escape:u.escape});""",
"""      put({time:t0+i*stagger, type:fix, spr:u.spr||'', fac:fac, noWarp:(fix!=='ast')?1:0,
           x:xx, y:yy, scan:u.scan?1:0, escape:u.escape,
           scenery:(fix==='ast')?1:0});""")
sub("ast-scenery-apply",
"""  if(sp.escape){""",
"""  if(sp.scenery) e.scenery = true;
  if(sp.escape){""")

# ── Mehrere Grosskampfschiffe nutzen die volle Hoehe ────────
# Die Baender waren zu eng. Schiffe kollidieren nicht miteinander, der
# Tiefenversatz genuegt - sie stehen an verschiedenen Stellen.
sub("cap-fullband",
"""             bandY:(n>1)? [H*(0.16+0.68*(i/n))+30, H*(0.16+0.68*((i+1)/n))-30] : null});""",
"""             phaseY:(n>1)? (i/n) : 0});""")
sub("cap-phase",
"""  if(sp.bandY){ e.minY = sp.bandY[0]; e.maxY = sp.bandY[1];
                e.y = (e.minY+e.maxY)/2; e.warpY = e.y; }""",
"""  // Volle Hoehe fuer alle, aber versetzt gestartet und in wechselnder
  // Richtung: sie schweben aneinander vorbei statt uebereinander.
  if(sp.phaseY){
    e.y = e.minY + (e.maxY-e.minY)*sp.phaseY;
    e.warpY = e.y;
    if(sp.phaseY > 0.5) e.vy = -Math.abs(e.vy||0.3);
  }""")

# ── Nachschubstaffeln fliegen einen Rumpf ───────────────────
sub("reinf-hull",
"""      const ty = 'fi_' + FAC_TAG[currentFaction];
      for(let k=0;k<sz;k++)
        spawnQ.push({time:spawnT+k*WING_STAGGER, type:ty, wing:wid,
                     y:H*(0.22+Math.random()*0.56)});""",
"""      const ty = 'fi_' + FAC_TAG[currentFaction];
      const rp = poolFor(ty);
      const rh = rp ? rnd(rp) : '';     // eine Staffel, ein Rumpf
      const ry = H*(0.22+Math.random()*0.56);
      for(let k=0;k<sz;k++)
        spawnQ.push({time:spawnT+k*WING_STAGGER, type:ty, spr:rh, wing:wid,
                     y:ry + (k-(sz-1)/2)*WING_SPACING*0.5});""")

# ── Antijaegerstrahlen ──────────────────────────────────────
# Sie laden lange und feuern selten. Bei einem Zyklus von ueber fuenfzehn
# Sekunden trifft ein Jaeger sie kaum als Bedrohung wahr.
sub("beam-af",
"""function initBeams(e) {""",
"""// Antijaegerstrahlen: kuerzere Ladezeit, kuerzere Pause. Die schweren
// Strahlen bleiben unangetastet - die sind gegen Grosskampfschiffe
// ausgelegt und halten gegen Jaeger ohnehin das Feuer.
const AF_CHARGE_MUL = 0.55, AF_COOL_MUL = 0.60;
function initBeams(e){""")
sub("beam-af-apply",
"""    return {
      ...d,
      state:'idle',
      jit: jit,""",
"""    // Antijaegerstrahlen laden kuerzer und pausieren kuerzer. Bei einem
    // Zyklus von ueber fuenfzehn Sekunden nimmt ein Jaeger sie kaum als
    // Bedrohung wahr.
    const af = !d.large;
    return {
      ...d,
      chargeT: Math.round((d.chargeT||400) * (af?AF_CHARGE_MUL:1)),
      coolT:   Math.round((d.coolT||400)   * (af?AF_COOL_MUL:1)),
      state:'idle',
      jit: jit,""")

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
