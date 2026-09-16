#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v95 -> v96: Rumpfanzeige neu, Missionskorrekturen."""
import io, os, sys
SRC="hlp_shooter_v95_logic.html"; DST="hlp_shooter_v96_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── Rumpfanzeige: Bloecke statt Balken ──────────────────────
# Fuenf von acht liest man ohne Vergleichen, 62 Prozent Laenge ist eine
# Schaetzung. Dazu die Subsysteme mit denselben Symbolen wie auf dem Rumpf
# und der Schiffsname - bei einem Verband aus drei Schiffen ist das der
# Unterschied zwischen drei Balken und drei Schiffen.
sub("hullbar",
"""          ctx.fillStyle='rgba(0,0,0,0.6)';
          ctx.fillRect(bx,by,bw|0,7);
          ctx.globalAlpha=(hpRatio<=HULL_CRIT&&!showShield)?(0.55+0.45*Math.sin(fc*0.22)):1;
          ctx.fillStyle=showShield?'#6fd8ff':hullCol(hpRatio);
          ctx.fillRect(bx,by,(bw*hpRatio)|0,7);
          ctx.globalAlpha=1;
          ctx.strokeStyle=(e.side==='ally')?'rgba(120,190,255,0.85)':'rgba(255,110,90,0.85)';
          ctx.lineWidth=1;
          ctx.strokeRect(bx,by,bw|0,7);""",
"""          drawHullBlocks(e, bx, by, bw, hpRatio, showShield);""")

sub("hullbar-fn",
"""function drawSubGlyph(id, r){""",
"""// ── RUMPFANZEIGE ─────────────────────────────────────────────
// Drei Zeilen dicht am Rumpf: Name, Bloecke, Subsysteme. Die Blockzahl
// haengt an der Breite des Schiffs - ein Aten traegt keine acht Bloecke
// plus fuenf Symbole, ohne breiter zu werden als er selbst.
const HB_SEG_W = 13, HB_SEG_GAP = 3, HB_SEG_H = 9;
function hullSegCount(bw){
  const n = Math.floor((bw + HB_SEG_GAP) / (HB_SEG_W + HB_SEG_GAP));
  return Math.max(3, Math.min(10, n));
}
function drawHullBlocks(e, bx, by, bw, ratio, showShield){
  const n = hullSegCount(bw);
  const full = n*HB_SEG_W + (n-1)*HB_SEG_GAP;
  const x0 = (e.x - full*0.5)|0;
  const lit = Math.max(0, Math.min(n, Math.ceil(ratio*n)));
  const col = showShield ? '#6fd8ff' : hullCol(ratio);
  const crit = (ratio<=HULL_CRIT && !showShield);
  for(let i=0;i<n;i++){
    const sx = x0 + i*(HB_SEG_W+HB_SEG_GAP);
    ctx.globalAlpha = 1;
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.fillRect(sx, by, HB_SEG_W, HB_SEG_H);
    if(i < lit){
      // Nur der letzte verbleibende Block pulsiert, nicht die ganze Reihe.
      ctx.globalAlpha = (crit && i===lit-1) ? (0.45+0.55*Math.sin(fc*0.22)) : 1;
      ctx.fillStyle = col;
      ctx.fillRect(sx, by, HB_SEG_W, HB_SEG_H);
    }
  }
  ctx.globalAlpha = 1;
  ctx.strokeStyle = (e.side==='ally') ? 'rgba(120,190,255,0.75)' : 'rgba(255,110,90,0.75)';
  ctx.lineWidth = 1;
  ctx.strokeRect(x0-1.5, by-1.5, full+3, HB_SEG_H+3);

  // Subsysteme, dieselben Symbole wie auf dem Rumpf.
  if(e.subs && e.subs.length){
    const sr = 5, sg = 5;
    const sw = e.subs.length*(sr*2) + (e.subs.length-1)*sg;
    let sx = e.x - sw*0.5 + sr;
    const sy = by + HB_SEG_H + 9;
    for(const s of e.subs){
      const ok = s.hp > 0;
      ctx.save();
      ctx.translate(sx|0, sy|0);
      ctx.globalAlpha = ok ? 0.95 : 0.4;
      ctx.strokeStyle = ok ? '#8fd6ff' : '#ff5a44';
      ctx.fillStyle   = ok ? '#8fd6ff' : '#ff5a44';
      ctx.lineWidth = 1.2;
      drawSubGlyph(s.id, sr*1.7);
      if(!ok){
        ctx.beginPath();
        ctx.moveTo(-sr,-sr); ctx.lineTo(sr,sr);
        ctx.moveTo(sr,-sr);  ctx.lineTo(-sr,sr);
        ctx.stroke();
      }
      ctx.restore();
      sx += sr*2 + sg;
    }
  }

  // Name. Aus derselben Quelle wie die Auftragszeile.
  const nm = e.label || shipName(e.img, '');
  if(nm){
    ctx.save();
    ctx.font = 'bold 9px Courier New';
    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
    ctx.globalAlpha = 0.85;
    ctx.fillStyle = (e.side==='ally') ? '#9fd0ff' : '#ffb0a0';
    ctx.fillText(nm, e.x|0, by-5);
    ctx.restore();
  }
}

function drawSubGlyph(id, r){""")

# Der Balken sitzt jetzt naeher am Rumpf, weil zwei Zeilen dazukommen.
sub("hullbar-y",
"""          const bx=(e.x-bw*.5)|0,by=(e.y-hbImg.height*e.sc*.5-12)|0;""",
"""          const bx=(e.x-bw*.5)|0,by=(e.y-hbImg.height*e.sc*.5-6)|0;""")

# ── Kreuzer etwas groesser, damit die Bloecke Platz haben ──
# Ein Fenris war 100 Bildpunkte breit und trug damit sieben Bloecke.
# 118 sind es neun, und er bleibt deutlich unter der Korvette mit 195.
sub("cr-bigger",
"""const SIZE_K = 2.880, SIZE_E = 0.641, SIZE_MAX = 400;""",
"""const SIZE_K = 2.880, SIZE_E = 0.641, SIZE_MAX = 400;
// Kreuzer eine Stufe groesser. Bei 100 Bildpunkten Breite trug die
// Rumpfanzeige nur sieben Bloecke; mit dem Zuschlag sind es neun, und
// der Abstand zur Korvette mit 195 bleibt deutlich.
const SIZE_CLASS_MUL = {cr: 1.18};""")
sub("cr-bigger-use",
"""  return Math.round(Math.min(SIZE_MAX, Math.max(floor, curve)));""",
"""  const mul = SIZE_CLASS_MUL[c] || 1;
  return Math.round(Math.min(SIZE_MAX, Math.max(floor, curve)*mul));""")

# ── M022: Antrieb zerstoert heisst stehenbleiben ────────────
sub("escape-engines",
"""    if(!e.escaping || e.dead || e.warp>0) continue;
    e.x += e.escaping;
    if(e.x > W+70){""",
"""    if(!e.escaping || e.dead || e.warp>0) continue;
    // Kein Antrieb, keine Fahrt. Das war der Sinn des Subsystems.
    if(hasSubsystems(e) && !subOK(e,'engines')) continue;
    e.x += e.escaping;
    // Erst weg, wenn der Rumpf ganz draussen ist - nicht wenn die Mitte
    // den Rand erreicht und das Heck noch im Bild steht.
    const _ei = IMGS[e.img];
    const _ew = _ei ? _ei.width*e.sc : 120;
    if(e.x > W + _ew*0.6){""")

# ── M025: der Spieler muss erfahren, was zu tun ist ────────
sub("escape-objective",
"""  if(nRun)
    return {txt:'[ STOP '+nRun+' FREIGHTER'+(nRun>1?'S':'')+' ]',""",
"""  let nEsc=0;
  for(const e of enemies) if(e.escaping && !e.dead) nEsc++;
  if(nEsc)
    return {txt:'[ STOP '+nEsc+' RUNNER'+(nEsc>1?'S':'')+' ]',
            col:'#ffbb22', ink:'#ffd257'};
  if(nRun)
    return {txt:'[ STOP '+nRun+' FREIGHTER'+(nRun>1?'S':'')+' ]',""")

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
