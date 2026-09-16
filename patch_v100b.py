#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v100 Teil B: Andocken mit Ladung."""
import io, os, sys
F="hlp_shooter_v100_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── ANDOCKEN ─────────────────────────────────────────────────────
# Die Andockpunkte stehen in der Mountdatei - Position und Winkel, auf 95
# Schiffen gepflegt - und wurden von nichts gelesen. Ein Frachter faehrt
# den Punkt an, haelt, und ab da traegt er, was dort lag.
sub("dock-const",
"""const DEATH_ROLL = 110;          // 1,1 s""",
"""// Andocken. Der Frachter faehrt den Andockpunkt seines Ziels an; ist er
// nah genug, gilt es als angedockt. Danach haengt die Fracht an ihm:
// sie wird mitgezeichnet, mitgetroffen und stirbt mit ihm.
const DOCK_SPD = 0.55;           // Bildpunkte je Schritt
const DOCK_NEAR = 22;            // ab hier angedockt
const DEATH_ROLL = 110;          // 1,1 s""")

sub("dock-fn",
"""function tickCapRam(){""",
"""// Weltkoordinaten des ersten Andockpunkts eines Schiffs.
function dockPoint(o){
  const m = mountsFor(o.img), img = IMGS[o.img];
  if(!m || !m.docks || !m.docks.length || !img) return {x:o.x, y:o.y};
  const d = m.docks[0];
  const s = o.flip ? -1 : 1;
  return {x:o.x + (img.width*o.sc*0.5)*d.dx*s,
          y:o.y + (img.height*o.sc*0.5)*d.dy};
}
function tickDocking(){
  const all = enemies.concat(allies);
  for(const e of all){
    if(!e.dockTo || e.dead || e.warp>0) continue;
    if(e.dockedTo){
      // Angedockt: die Fracht faehrt mit.
      const c = e.dockedTo;
      if(c.dead){ e.dockedTo=null; continue; }
      c.x = e.x + (e.cargoDX||0);
      c.y = e.y + (e.cargoDY||0);
      continue;
    }
    const t = byId(e.dockTo)[0];
    if(!t) continue;
    const p = dockPoint(t);
    const dx = p.x-e.x, dy = p.y-e.y, L = Math.hypot(dx,dy)||1;
    if(L > DOCK_NEAR){
      e.x += dx/L*DOCK_SPD*1.6;
      e.y += dy/L*DOCK_SPD;
      e.vx = 0; e.vy = 0;
      continue;
    }
    // Angedockt.
    EV_DOCK[e.uid] = true;
    SUB_MSGS.push({x:e.x, y:e.y-28, txt:'DOCKED', life:150, ml:150,
                   ally:true, tone:'good'});
    if(t.type==='container'){
      // Die Fracht haengt ab jetzt am Traeger.
      e.dockedTo = t; e.cargoDX = 0; e.cargoDY = 26;
      t.carried = true; t.guard = false; t.scenery = true;
      e.hasCargo = true;
    }
    e.dockTo = null;
  }
}
function tickCapRam(){""")
sub("dock-call",
"""  tickCapRam();""",
"""  tickDocking();
  tickCapRam();""")
sub("dock-apply",
"""  if(sp.capRam){ e.capRam = sp.capRam; e.noFlee = true; }""",
"""  if(sp.capRam){ e.capRam = sp.capRam; e.noFlee = true; }
  if(sp.dockTo) e.dockTo = sp.dockTo;""")
sub("dock-q",
"""           x:xx, y:yy, cross:u.cross, at:u.at});""",
"""           x:xx, y:yy, cross:u.cross, at:u.at, dockTo:u.dockTo});""")

# Traeger, der mit Fracht das Feld verlaesst: Fracht ist geliefert.
sub("dock-deliver",
"""    if(a.x > W+60){
      crossDone++; protSaved++;""",
"""    if(a.x > W+60){
      if(a.dockedTo){ a.dockedTo.dead = true;
        const _ci = allies.indexOf(a.dockedTo);
        if(_ci>=0) allies.splice(_ci,1);
        const _ce = enemies.indexOf(a.dockedTo);
        if(_ce>=0) enemies.splice(_ce,1); }
      crossDone++; protSaved++;""")

# ── Wirkung heilen: ein angedockter Transporter repariert ────────
sub("heal-effect",
"""    case 'jagd':""",
"""    case 'heilen': {
      // M027: jeder angedockte Transporter setzt den Rumpf ein Stueck
      // hoch. Wer schlecht verteidigt, wartet laenger.
      const ht = byId(arg)[0];
      if(ht){ ht.hp = Math.min(ht.maxHp, ht.hp + ht.maxHp*0.25);
              SUB_MSGS.push({x:ht.x, y:ht.y-40, txt:'HULL REPAIRED',
                             life:150, ml:150, ally:true, tone:'good'});
              if(ht.hp >= ht.maxHp*0.999){
                ht.warpOut = ht.warpMax || 100;
                SUB_MSGS.push({x:ht.x, y:ht.y-56, txt:'REPAIRS COMPLETE',
                               life:180, ml:180, ally:true, tone:'good'}); } }
      break;
    }
    case 'jagd':""")

def main():
    txt=io.open(F,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(F,"w",encoding="utf-8").write(txt)
    print("Teil B geschrieben")
main()
