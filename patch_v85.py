#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FS3  v84 -> v85

  1  Jaeger und Bomber lesen die Ausnahmeliste mit (Manticore auf 54)
  2  Querende Schuetzlinge schauen in Fahrtrichtung
  3  Roter Winkel an gegnerischen Jaegern und Bombern, im Nebel gedaempft
"""

import io, os, sys

SRC = "hlp_shooter_v84_logic.html"
DST = "hlp_shooter_v85_logic.html"

edits = []
def sub(tag, old, new):
    edits.append((tag, old, new))


# ─────────────────────────────────────────────────────────────
# 1  Jaeger und Bomber
#
# Sie sind bewusst von der Laengenkurve ausgenommen: ein 21-Meter-Apollo
# muss mehrfach zu gross gezeichnet werden, sonst ist auf 800x500 nichts
# steuerbar. Nur wurde dabei auch SIZE_FIXED uebergangen, und damit blieb
# der Eintrag fimanticore:54 wirkungslos - die Manticore fuellt bei
# gleicher Breite mehr Flaeche als die uebrigen Jaeger und wirkt massiger.
# Die feste Breite kommt jetzt aus einer Funktion, die Ausnahmen kennt.
# ─────────────────────────────────────────────────────────────
sub("small-width-fn",
"""function hullScale(key, fallback){""",
"""// Breite eines Jaegers oder Bombers. Klassenwert, sofern kein eigener
// Eintrag in SIZE_FIXED steht - dort stehen die Ruempfe, deren Sprite bei
// gleicher Breite mehr Flaeche fuellt als der Rest.
function smallWidth(key, klasse){
  if(SIZE_FIXED[key]!=null) return SIZE_FIXED[key];
  return SIZE_CLASS_FIXED[klasse];
}
function hullScale(key, fallback){""")

sub("fi-width",
"""    const sc=img?Math.min(0.55,60/img.width):0.5;""",
"""    const _fw=smallWidth(spr,'fi');
    const sc=img?Math.min(0.55,_fw/img.width):0.5;""")

sub("bo-width",
"""    const sc=img?Math.min(0.55,65/img.width):0.5;""",
"""    const _bw=smallWidth(spr,'bo');
    const sc=img?Math.min(0.55,_bw/img.width):0.5;""")

# ─────────────────────────────────────────────────────────────
# 2  Fahrtrichtung
#
# needsFlip(key, wantLeft) sagt, ob gespiegelt werden muss, damit das
# Schiff in die gewuenschte Richtung SCHAUT. Ein querender Schuetzling
# faehrt nach rechts, ich hatte true uebergeben - also nach links.
# ─────────────────────────────────────────────────────────────
sub("cross-flip",
"""    a.crossing = sp.cross;         // Bildpunkte je Schritt
    a.flip = needsFlip(a.img, true);""",
"""    a.crossing = sp.cross;         // Bildpunkte je Schritt
    a.flip = needsFlip(a.img, false);   // faehrt nach rechts, schaut nach rechts""")

# ─────────────────────────────────────────────────────────────
# 3  Feind-Freund-Kennung
#
# Die NTF fliegt terranische Ruempfe, und ab dem Schiffswechsel fliegt der
# Spieler dieselben. Ein Herkules gegen einen Herkules ist ohne Kennung
# ein Ratespiel, und der teure Fehler ist nicht, auf einen Verbuendeten zu
# schiessen - Spielergeschosse treffen ohnehin nur enemies -, sondern
# einen Gegner ziehen zu lassen.
#
# Nur an Jaegern und Bombern: Grosskampfschiffe sind ueber die Groesse
# erkennbar, seit die Laengenkurve laeuft.
#
# Im Nebel gedaempft, sonst nimmt die Kennung dem Modifikator seine
# Wirkung. Die Zahlen sind nicht gegriffen: fireRange() deckelt im Nebel
# auf 240, das ist die Sicht- und Schussweite fuer alle. Der Winkel reicht
# halb so weit.
# ─────────────────────────────────────────────────────────────
sub("chevron-fn",
"""function drawFieldBanner(){""",
"""const CHEV_FULL = 120;    // bis hierher voll sichtbar
const CHEV_FADE = 240;    // ab hier gar nicht mehr - Nebelsichtweite
function drawHostileMark(e){
  if(e.type!=='fighter' && e.type!=='bomber') return;
  if(e.dead || e.warp>0 || e.warpOut>0) return;
  let a = 1;
  if(nebulaOn()){
    const d = Math.hypot(e.x-player.x, e.y-player.y);
    if(d >= CHEV_FADE) return;
    a = (d <= CHEV_FULL) ? 1 : (CHEV_FADE-d)/(CHEV_FADE-CHEV_FULL);
  }
  const img = IMGS[e.img];
  const h = img ? img.height*e.sc : 30;
  const y = e.y - h*0.5 - 9;
  ctx.save();
  ctx.globalAlpha = a;
  ctx.strokeStyle = '#ff2a1a';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(e.x-6, y-5); ctx.lineTo(e.x, y); ctx.lineTo(e.x+6, y-5);
  ctx.stroke();
  ctx.restore();
}

function drawFieldBanner(){""")

sub("chevron-call",
"""      drawShip(e.img,e.x|0,e.y|0,e.sc,e.flip,e.ang||0);
      drawScorch(e);""",
"""      drawShip(e.img,e.x|0,e.y|0,e.sc,e.flip,e.ang||0);
      drawHostileMark(e);
      drawScorch(e);""")


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
