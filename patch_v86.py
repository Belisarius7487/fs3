#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FS3  v85 -> v86

  1  Roter Winkel nur an Gegnern
  2  Groesse misst die groessere Seite, nicht nur die Breite
"""
import io, os, sys
SRC="hlp_shooter_v85_logic.html"; DST="hlp_shooter_v86_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# 1  Die Zeichenschleife laeuft ueber enemies.concat(allies) - ohne
#    Seitenabfrage bekam auch jeder Verbuendete einen Winkel.
sub("chev-side",
"""function drawHostileMark(e){
  if(e.type!=='fighter' && e.type!=='bomber') return;""",
"""function drawHostileMark(e){
  // SHIPS_ON_FIELD ist enemies.concat(allies) - ohne diese Zeile bekaeme
  // jeder Verbuendete denselben Winkel. Ein Ueberlaeufer hat nach defect()
  // side='enemy' und bekommt ihn dann zu Recht.
  if(e.side === 'ally') return;
  if(e.type!=='fighter' && e.type!=='bomber') return;""")

# 2  Ein Sprite, das hoeher als breit ist, wurde bisher an der Breite
#    gemessen: 30 px Breite koennen bei einem Geschuetzturm 90 px Hoehe
#    bedeuten. Fuer Schiffe aendert sich nichts, weil deren Sprites
#    breiter als hoch sind - dort ist die groessere Seite die Breite.
sub("scale-max",
"""function hullScale(key, fallback){
  const img = IMGS[key];
  if(!img || !img.width) return fallback||0.5;
  return hullWidth(key)/img.width;
}""",
"""function hullScale(key, fallback){
  const img = IMGS[key];
  if(!img || !img.width) return fallback||0.5;
  // Massgeblich ist die groessere Seite. Sonst wird ein Sprite, das hoeher
  // als breit ist, viel zu gross gezeichnet: 30 Bildpunkte Breite sind bei
  // einem hochkant stehenden Geschuetzturm 90 Bildpunkte Hoehe.
  // Bei Schiffen ist die groessere Seite die Breite, dort aendert sich nichts.
  return hullWidth(key)/Math.max(img.width, img.height||img.width);
}""")

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
