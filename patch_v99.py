#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v98 -> v99: elf Korrekturen aus dem Spieltest."""
import io, os, sys
SRC="hlp_shooter_v98_logic.html"; DST="hlp_shooter_v99_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── Todesfolge umging die Abschussabrechnung ──────────────────────
# tickDeathRoll() hat das Schiff selbst aus der Liste genommen und damit
# killEnemy() uebersprungen: seit v97 gaben Zerstoerer, Bosse und
# Stationen weder Punkte noch Tickets. Das war die fehlende
# Zerstoererbelohnung in M022 - und es traf jeden Boss.
sub("death-award",
"""    if(e.rollT <= 0){
      e.rollT = null;
      e.hp = 0; e.dead = true;
      triggerExpl(e.x, e.y, e.type, e.faction, e);
      spawnShock(e.x, e.y, 150, 2.6, 0.020);
      addShake(7, 26);
      enemies.splice(i,1);
    }""",
"""    if(e.rollT <= 0){
      e.rollT = null;
      e.hp = 0;
      spawnShock(e.x, e.y, 150, 2.6, 0.020);
      // Ueber killEnemy, nicht daneben: dort haengen Punkte, Statistik,
      // Ticketwurf und die Bossmarkierung.
      killEnemy(e, i, true, true);
    }""")

# ── Der zweite Geradeausschuetze ──────────────────────────────────
# Zeile 5977: der Strahlen- und Geschuetzzweig fuer Sekundaerwaffen gibt
# den Winkel weiter, aber capitalFire hatte noch einen zweiten Aufruf
# ueber diese Huelle. Ohne Ziel blieb der Winkel null.
sub("gun-aim2",
"""    : function(x,y,a,d){ eSmall(x,y,e.faction,a,null,d); };""",
"""    : function(x,y,a,d){
        // Ohne uebergebenen Winkel auf das naechste Ziel halten statt
        // stur nach links.
        if(a==null){
          const _t = (e.side==='ally') ? nearestEnemy(x,y) : capGunTarget(e);
          if(!_t) return;
          a = Math.atan2(_t.y-y, _t.x-x);
        }
        eSmall(x,y,e.faction,a,null,d);
      };""")

# ── Grosse Strahlen greifen Stationen an ──────────────────────────
# isLargeShip() kannte keine Station, also hielt jeder schwere Strahl das
# Feuer - eine Arcadia war unangreifbar, auch wenn sie verwundbar war.
sub("large-station",
"""function isLargeShip(o){
  return o.type==='cruiser' || o.type==='corvette'
      || o.type==='destroyer' || o.type==='boss';
}""",
"""function isLargeShip(o){
  return o.type==='cruiser' || o.type==='corvette'
      || o.type==='destroyer' || o.type==='boss'
      // Eine Station ist ein Ziel fuer schwere Strahlen - unverwundbare
      // nehmen ohnehin keinen Schaden, aber beschossen werden sie.
      || o.type==='station';
}""")

# ── Rammkreuzer: langsamer, und die Trennung darf nicht eingreifen ─
sub("capram-nosep",
"""      if(a.colossus || b.colossus) continue;   // she does not give way""",
"""      if(a.colossus || b.colossus) continue;   // she does not give way
      // Ein Rammkurs weicht nicht aus, und sein Ziel darf nicht
      // weggedrueckt werden - der Aufprall ist der Sinn der Sache.
      if(a.capRam || b.capRam) continue;""")

# ── Rettungskapseln starten am sterbenden Schiff ──────────────────
# Sie erschienen am rechten Rand, weil der Ort aus der Reihenfolge in der
# Liste kam. Jetzt merkt sich das Spiel, wo ein benanntes Schiff
# verschwunden ist, und Nachzuegler starten dort.
sub("lastpos-var",
"""let EV = [], EV_HELD = {}, EV_SEEN = {}, EV_LEFT = {}, EV_DOCK = {};""",
"""let EV = [], EV_HELD = {}, EV_SEEN = {}, EV_LEFT = {}, EV_DOCK = {};
// Letzter bekannter Ort je Kennung. Wer nach dem Tod eines Schiffs
// eingewarpt wird, soll dort erscheinen und nicht am Bildrand.
let EV_POS = {};""")
sub("lastpos-reset",
"""  EV = []; EV_HELD = {}; EV_SEEN = {}; EV_LEFT = {}; EV_DOCK = {};""",
"""  EV = []; EV_HELD = {}; EV_SEEN = {}; EV_LEFT = {}; EV_DOCK = {}; EV_POS = {};""")
sub("lastpos-track",
"""function tickEvents(){
  if(!EV.length && !evReinf) return;""",
"""function tickEvents(){
  // Ort mitschreiben, solange die Schiffe noch da sind.
  for(const e of enemies) if(e.uid) EV_POS[e.uid] = [e.x, e.y];
  for(const a of allies)  if(a.uid) EV_POS[a.uid] = [a.x, a.y];
  if(!EV.length && !evReinf) return;""")
sub("lastpos-use",
"""      const held = EV_HELD[arg];
      if(held){ for(const q of held){ q.time = spawnT + (q.delay||0); spawnQ.push(q); }""",
"""      const held = EV_HELD[arg];
      // Wer am Ort eines anderen Schiffs starten soll, uebernimmt dessen
      // letzte Position - leicht gestreut, damit sie nicht stapeln.
      const src = (held && held[0] && held[0].at) ? EV_POS[held[0].at] : null;
      if(held){ for(const q of held){
                  q.time = spawnT + (q.delay||0);
                  if(src){ q.x = src[0] + (Math.random()*2-1)*26;
                           q.y = src[1] + (Math.random()*2-1)*22; }
                  spawnQ.push(q); }""")
sub("lastpos-q",
"""           x:xx, y:yy, cross:u.cross});""",
"""           x:xx, y:yy, cross:u.cross, at:u.at});""")

# ── Kapseln sind nicht abgeliefert, sie sind gerettet ─────────────
sub("pod-msg",
"""      SUB_MSGS.push({x:W-90, y:a.y, txt:'DELIVERED', life:150, ml:150, ally:true});""",
"""      SUB_MSGS.push({x:W-90, y:a.y,
                     txt: (hullClass(a.img)==='ep') ? 'RESCUED' : 'DELIVERED',
                     life:150, ml:150, ally:true});""")

# ── Nachschub warpt nicht nur am rechten Rand ein ─────────────────
# In FreeSpace springt ein Verband dort hinein, wo er gebraucht wird.
# Immer vom rechten Rand heisst: man kann sich hinstellen und warten.
sub("reinf-edge",
"""      for(let k=0;k<sz;k++)
        spawnQ.push({time:spawnT+k*WING_STAGGER, type:ty, spr:rh, wing:wid,
                     y:ry + (k-(sz-1)/2)*WING_SPACING*0.5});""",
"""      // Ein Drittel der Staffeln springt mitten ins Feld statt am Rand.
      const rx = (Math.random()<0.34) ? (W*0.45+Math.random()*W*0.4) : null;
      for(let k=0;k<sz;k++)
        spawnQ.push({time:spawnT+k*WING_STAGGER, type:ty, spr:rh, wing:wid,
                     x: rx!=null ? rx+(k-(sz-1)/2)*22 : null,
                     y:ry + (k-(sz-1)/2)*WING_SPACING*0.5});""")

# ── Jagdziel per Ereignis wechselbar ─────────────────────────────
sub("hunt-effect",
"""    case 'nachschub':""",
"""    case 'jagd':
      waveHunt = arg || '';
      // Die Zuweisung gilt fuer neue Schiffe; die im Feld werden
      // nachgezogen, sonst wirkt der Wechsel erst nach der naechsten Welle.
      for(const o of enemies)
        if(o.type==='fighter'||o.type==='bomber') o.hunter = Math.random()<HUNT_SHARE;
      break;
    case 'nachschub':""")

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
