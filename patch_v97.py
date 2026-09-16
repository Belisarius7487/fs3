#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v96 -> v97: Anzeige schmaler, sieben Korrekturen."""
import io, os, sys
SRC="hlp_shooter_v96_logic.html"; DST="hlp_shooter_v97_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── 1  Anzeige schmaler, alles oberhalb des Rumpfs, eine Farbe ─────
# Vorher lagen die Symbole unter dem Balken und damit im Rumpf. Bei einer
# Aten mit 111 Bildpunkten Breite sah man Balken, Name und Symbole - aber
# kein Schiff. Jetzt steht alles uebereinander ueber dem Rumpf, und die
# Symbole haben keine eigene Farbe mehr: hell heisst heil, rot heisst hin.
sub("bar-slim",
"""const HB_SEG_W = 13, HB_SEG_GAP = 3, HB_SEG_H = 9;""",
"""const HB_SEG_W = 12, HB_SEG_GAP = 3, HB_SEG_H = 5;""")
sub("bar-stack",
"""  // Subsysteme, dieselben Symbole wie auf dem Rumpf.
  if(e.subs && e.subs.length){
    const sr = 5, sg = 5;
    const sw = e.subs.length*(sr*2) + (e.subs.length-1)*sg;
    let sx = e.x - sw*0.5 + sr;
    const sy = by + HB_SEG_H + 9;""",
"""  // Subsysteme, dieselben Symbole wie auf dem Rumpf - aber OBERHALB des
  // Balkens, sonst liegen sie auf dem Schiff.
  if(e.subs && e.subs.length){
    const sr = 4, sg = 4;
    const sw = e.subs.length*(sr*2) + (e.subs.length-1)*sg;
    let sx = e.x - sw*0.5 + sr;
    const sy = by - 8;""")
sub("bar-icon-col",
"""      ctx.globalAlpha = ok ? 0.95 : 0.4;
      ctx.strokeStyle = ok ? '#8fd6ff' : '#ff5a44';
      ctx.fillStyle   = ok ? '#8fd6ff' : '#ff5a44';
      ctx.lineWidth = 1.2;
      drawSubGlyph(s.id, sr*1.7);""",
"""      // Keine eigene Farbe: hell heisst heil, rot heisst hin. Das UI hat
      // genug Farben.
      ctx.globalAlpha = ok ? 0.75 : 0.9;
      ctx.strokeStyle = ok ? '#cfcfc8' : '#ff5a44';
      ctx.fillStyle   = ok ? '#cfcfc8' : '#ff5a44';
      ctx.lineWidth = 1;
      drawSubGlyph(s.id, sr*1.7);""")
sub("bar-name-y",
"""    ctx.fillText(nm, e.x|0, by-5);""",
"""    ctx.fillText(nm, e.x|0, by-19);""")
sub("bar-frame",
"""  ctx.strokeRect(x0-1.5, by-1.5, full+3, HB_SEG_H+3);""",
"""  ctx.strokeRect(x0-1.5, by-1.5, full+3, HB_SEG_H+3);
  ctx.globalAlpha = 1;""")

# Stationen bekommen eine Anzeige, unverwundbare nicht.
sub("bar-station",
"""      if(e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||e.type==='boss'){""",
"""      if(e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||
         e.type==='boss'||e.type==='station'){""")

# ── 2  M005: der Lohn richtet sich nach dem beschuetzten Schiff ────
sub("guard-reward",
"""        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;
                _a.defectLock = evWillDefect(_sp.uid); allies.push(_a); }""",
"""        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;
                // Wer eine Korvette durchbringt, bekommt kein Kreuzerticket.
                guardReward = (_a.type==='destroyer') ? 'destroyer'
                            : (_a.type==='corvette') ? 'corvette' : 'cruiser';
                _a.defectLock = evWillDefect(_sp.uid); allies.push(_a); }""")
# ── 3  M007: ein Ereignis, das nie feuern kann, blockierte das Ende ─
# evPending() hielt die Welle offen, solange irgendein Nachschubereignis
# offen war. Der Funkraum der Typhon wurde nie zerstoert, weil sie ganz
# starb - also blieb das Ereignis fuer immer offen.
sub("evpending",
"""function evPending(){
  for(const e of EV)
    if(!e.done && (e.w==='einwarpen' || e.w==='seite' || e.w==='nachschub')) return true;
  return false;
}""",
"""function evPending(){
  for(const e of EV){
    if(e.done) continue;
    // Nachschub abzuschalten haelt keine Welle offen.
    if(e.w!=='einwarpen' && e.w!=='seite') continue;
    // Ein Ausloeser, dessen Ziel nie im Feld war oder schon weg ist, kann
    // nicht mehr feuern. Sonst haengt die Welle fuer immer.
    if(['zerstoert','alleZerstoert','verlaesst','anzahlUnter','rumpfUnter','subsystem'].indexOf(e.t)>=0){
      if(evSeen(e.a) && byId(e.a).length===0) continue;
    }
    return true;
  }
  return false;
}""")

# ── 4  M014: Ueberlaeufer behalten die Fraktion der Welle ──────────
# 'renegade' ist ein terranischer Abtruennigenanstrich mit tuerkisen
# Triebwerken. Ein vasudanischer Ueberlaeufer bleibt vasudanisch.
sub("defect-fac",
"""  a.defectLock = false;      // gewechselt, ab jetzt normal zu toeten
  a.faction = 'renegade';""",
"""  a.defectLock = false;      // gewechselt, ab jetzt normal zu toeten
  a.faction = (currentFaction==='hol') ? 'hol' : 'renegade';""")

# ── 6  M021: Tiefenversatz muss die Breite uebersteigen ────────────
# separateCapitals() drueckt zwei Schiffe auseinander, sobald
# |a.x-b.x| <= halbe Breite a + halbe Breite b. Bei drei Aten sind das
# 111 Bildpunkte, mein Versatz war 86 - sie schubsten sich also dauernd.
# Und meine eigenen Bahnen arbeiteten gegen assignStation(), das die Hoehe
# ohnehin kollisionsfrei waehlt.
sub("lane-out",
"""             phaseY:(n>1)? (i/n) : 0, lane:(u.lanes&&n>1)? (i/n) : 0});""",
"""             capIndex:(n>1)? i : 0});""")
sub("lane-apply-out",
"""  // Eigene Bahn: volle Hoehe, aber gegenlaeufig und mit festem Vorlauf.
  // Zwei Schiffe mit gleicher Richtung holen sich sonst wieder ein.
  if(sp.lane){
    e.y = e.minY + (e.maxY-e.minY)*sp.lane;
    e.warpY = e.y;
    const dir = (Math.round(sp.lane*4) % 2) ? -1 : 1;
    e.vy = dir * (0.22 + sp.lane*0.20);
  }
  if(sp.phaseY && !sp.lane){
    e.y = e.minY + (e.maxY-e.minY)*sp.phaseY;
    e.warpY = e.y;
    if(sp.phaseY > 0.5) e.vy = -Math.abs(e.vy||0.3);
  }""",
"""  // Tiefenversatz aus der eigenen Breite: er muss die Summe der halben
  // Breiten uebersteigen, sonst greift separateCapitals() dauernd ein und
  // die Schiffe schubsen sich gegenseitig aus ihrer Bahn. Teilen sie sich
  // keinen Bildraum, waehlt assignStation() die Hoehe frei - und alle
  // nutzen das ganze Feld.
  if(sp.capIndex){
    const _ci = IMGS[e.img];
    const _cw = _ci ? _ci.width*e.sc : 120;
    e.targetX = (e.targetX!=null ? e.targetX : e.x) - sp.capIndex*(_cw + 16);
  }""")
sub("capback-out",
"""  if(sp.capBack && e.targetX!=null) e.targetX -= sp.capBack;""",
"""""")
sub("capback-q",
"""             capBack:(n>1)? i*86 : 0,
             capIndex:(n>1)? i : 0});""",
"""             capIndex:(n>1)? i : 0});""")

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
