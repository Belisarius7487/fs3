#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v101 -> v102: docking with reservation, freighter count from the
containers, cargo offset from the mount file, abandoned cargo.

Decisions (Silvio, v102):
  - cargo not picked up by wave end  -> partial success (yellow)
  - container destroyed before dock  -> freighter leaves empty
  - carrier destroyed with cargo     -> cargo is destroyed with it
"""
import io, os, sys
SRC = "hlp_shooter_v101_logic.html"; DST = "hlp_shooter_v102_logic.html"
edits = []
def sub(t, a, b): edits.append((t, a, b))

# ── 1. Freighter count follows the containers ───────────────────
sub("resolve-units",
"""function buildScripted(def){""",
"""// Freighters follow the containers: one per container, never set by hand.
// Containers someone is sent to fetch are marked as pickups, so one that is
// left behind can be released instead of holding the wave open.
function scriptUnitsResolved(def){
  const us = def.u || [];
  return us.map(function(u){
    const o = Object.assign({}, u);
    const tg = u.dockTo ? us.find(function(x){ return x.id===u.dockTo; }) : null;
    if(tg && tg.c==='fc') o.n = tg.n || 1;
    if(u.c==='fc' && us.some(function(x){ return x.dockTo===u.id; })) o.pickup = true;
    return o;
  });
}

function buildScripted(def){""")

sub("resolve-loop",
"""  for(const u of (def.u||[])) scriptUnit(u, def.fac, q);""",
"""  for(const u of scriptUnitsResolved(def)) scriptUnit(u, def.fac, q);""")

# The pickup mark has to travel from the unit to the ship.
sub("pickup-put-ally",
"""x:xx, y:yy, cross:u.cross, at:u.at, dockTo:u.dockTo});""",
"""x:xx, y:yy, cross:u.cross, at:u.at, dockTo:u.dockTo,
           pickup:u.pickup?1:0});""")
sub("pickup-put-enemy",
"""scenery:(fix==='ast')?1:0});""",
"""scenery:(fix==='ast')?1:0, pickup:u.pickup?1:0});""")
sub("pickup-protected",
"""  a.faction = sp.fac || 'terran';""",
"""  a.faction = sp.fac || 'terran';
  if(sp.pickup) a.pickup = true;""")
sub("pickup-opts",
"""  if(sp.dockTo) e.dockTo = sp.dockTo;""",
"""  if(sp.dockTo) e.dockTo = sp.dockTo;
  if(sp.pickup) e.pickup = true;""")

# ── 2. Docking rebuilt ──────────────────────────────────────────
sub("docking",
"""function tickDocking(){
  const all = enemies.concat(allies);
  for(const e of all){
    if((!e.dockTo && !e.dockedTo) || e.dead || e.warp>0) continue;
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
    // Erst laden, dann abfahren.
    if(e.crossAfter) e.crossing = e.crossAfter;
  }
}""",
"""// Offset of a ship's first dock point from its centre.
function dockOffset(o){
  const p = dockPoint(o);
  return {x:p.x-o.x, y:p.y-o.y};
}
// Still in one of the two lists and not dead.
function unitAlive(o){
  return !!o && !o.dead && (allies.indexOf(o)>=0 || enemies.indexOf(o)>=0);
}
// Are ships of this id still on their way into the field?
function idPending(id){
  for(const q of spawnQ) if(q.uid===id) return true;
  return !!(EV_HELD[id] && EV_HELD[id].length);
}
// Counts one cargo run as lost, once. Every path that loses cargo goes
// through here, so a container can never be counted twice.
function cargoLost(c){
  if(!c || c.lostCounted) return;
  c.lostCounted = true;
  protLost++; guardLost = true;
}
// One container per freighter. Nearest free one of the id, where free means
// alive, not carried, not left behind and not promised to a living freighter.
// byId() alone always answered with the first ship, which is how two
// freighters ended up fighting over one container.
function claimCargo(e){
  let best = null, bd = 1e18;
  for(const c of byId(e.dockTo)){
    if(c.type!=='container' || c.carried || c.stranded) continue;
    if(c.resBy && c.resBy!==e && unitAlive(c.resBy)) continue;
    const d = (c.x-e.x)*(c.x-e.x) + (c.y-e.y)*(c.y-e.y);
    if(d < bd){ bd = d; best = c; }
  }
  if(best){ best.resBy = e; e.dockRes = best; }
  return best;
}
// Decided: a freighter whose container is gone leaves empty. It does not
// look for another one, and it does not count as a delivery.
function leaveEmpty(e, wasCargo){
  if(e.dockRes && e.dockRes.resBy===e) e.dockRes.resBy = null;
  e.dockRes = null; e.dockTo = null;
  if(wasCargo){
    e.emptyRun = true;
    SUB_MSGS.push({x:e.x, y:e.y-28, txt:'NO CARGO', life:150, ml:150,
                   ally:false, tone:'bad'});
  }
  if(e.crossAfter) e.crossing = e.crossAfter;
}
// Is anybody still able to come for this container? A living freighter
// heading for its id without a claim on another one, or one still queued
// or held back for an event.
function cargoStillWanted(c){
  for(const o of enemies.concat(allies))
    if(!o.dead && o.dockTo===c.uid && (!o.dockRes || o.dockRes===c)) return true;
  for(const q of spawnQ) if(q.dockTo===c.uid) return true;
  for(const k in EV_HELD) for(const q of EV_HELD[k]) if(q.dockTo===c.uid) return true;
  return false;
}
// Moves carried cargo so that both dock points meet. Runs after all
// movement in the step, otherwise the cargo trails one step behind.
function carryCargo(e){
  const c = e.dockedTo;
  if(!c) return;
  if(!unitAlive(c)){
    // Shot off the carrier on the way: he arrives with nothing.
    e.dockedTo = null; e.hasCargo = false; e.emptyRun = true;
    cargoLost(c);
    return;
  }
  const p = dockPoint(e), o = dockOffset(c);
  c.x = p.x - o.x; c.y = p.y - o.y;
  c.vx = 0; c.vy = 0; c.warpX = c.x; c.warpY = c.y;
}
// Decided: cargo dies with its carrier. The carrier was already counted
// as lost, the cargo is not counted a second time.
function dropCargo(c){
  if(!c || c.dead) return;
  c.lostCounted = true;
  c.dead = true; c.hp = 0;
  triggerExpl(c.x, c.y, 'container', c.faction || 'vasudan', c);
  let k = allies.indexOf(c);  if(k>=0) allies.splice(k,1);
  k = enemies.indexOf(c);     if(k>=0) enemies.splice(k,1);
}
function tickCarry(){
  for(const e of enemies.concat(allies)) if(e.dockedTo) carryCargo(e);
  for(const c of enemies.concat(allies))
    if(c.carrier && !c.dead && !unitAlive(c.carrier)) dropCargo(c);
}
function tickDocking(){
  const all = enemies.concat(allies);
  // Containers nobody can come for any more. This runs before the wave end
  // test, so an abandoned container never holds the wave open.
  for(const c of all){
    if(!c.pickup || c.carried || c.stranded || c.dead || c.warp>0) continue;
    if(cargoStillWanted(c)) continue;
    c.stranded = true; c.scenery = true; c.guard = false;
    // A freighter that died on its way here was already counted as lost.
    if(c.resBy && c.resBy.dead) c.lostCounted = true;
    else cargoLost(c);
    c.resBy = null;
    SUB_MSGS.push({x:c.x, y:c.y-24, txt:'CARGO LEFT BEHIND', life:170, ml:170,
                   ally:false, tone:'bad'});
  }
  for(const e of all){
    if(!e.dockTo || e.dead || e.warp>0) continue;
    const group = byId(e.dockTo);
    let t = group[0];
    if(t && t.type==='container') e.wantsCargo = true;
    if(!t || t.type==='container'){
      if(e.dockRes){
        // Decided: his container is gone, he does not look for another.
        if(!unitAlive(e.dockRes) || e.dockRes.carried || e.dockRes.stranded){
          leaveEmpty(e, true); continue; }
        t = e.dockRes;
      } else if(t){
        t = claimCargo(e);
      }
      if(!t){
        // Containers of this id may still be arriving - then wait.
        if(idPending(e.dockTo) || !evSeen(e.dockTo)) continue;
        leaveEmpty(e, !!e.wantsCargo);
        continue;
      }
    }
    // Head for the spot where his dock point meets the target's.
    const p = dockPoint(t), o = dockOffset(e);
    const dx = (p.x-o.x) - e.x, dy = (p.y-o.y) - e.y;
    const L = Math.hypot(dx, dy);
    e.vx = 0; e.vy = 0;
    // The field clamp can keep him off the exact spot. If he stops getting
    // closer while near enough, he docks where he is.
    if(e.dockBest==null || L < e.dockBest-0.05){ e.dockBest = L; e.dockStall = 0; }
    else e.dockStall = (e.dockStall||0) + 1;
    if(!(L <= 1 || (L <= DOCK_NEAR && e.dockStall > 60))){
      const sx = DOCK_SPD*1.6, sy = DOCK_SPD;
      e.x += Math.max(-sx, Math.min(sx, dx));
      e.y += Math.max(-sy, Math.min(sy, dy));
      continue;
    }
    // Docked.
    EV_DOCK[e.uid] = true;
    SUB_MSGS.push({x:e.x, y:e.y-28, txt:'DOCKED', life:150, ml:150,
                   ally:true, tone:'good'});
    if(t.type==='container'){
      e.dockedTo = t; t.carrier = e; t.resBy = e;
      t.carried = true; t.guard = false; t.scenery = true;
      e.hasCargo = true;
      carryCargo(e);
    }
    e.dockTo = null; e.dockRes = null;
    // Load first, then leave.
    if(e.crossAfter) e.crossing = e.crossAfter;
  }
}""")

# Cargo follows after everything has moved in this step.
sub("carry-call",
"""  for(const o of allies)  if(o.img) clampToField(o);""",
"""  for(const o of allies)  if(o.img) clampToField(o);
  tickCarry();""")

# ── 3. Counting ─────────────────────────────────────────────────
# A pickup container shot by the player counts as lost cargo.
sub("kill-pickup",
"""function killEnemy(e, idx, award, drop){
  if(!e || e.dead) return;
  e.dead = true;""",
"""function killEnemy(e, idx, award, drop){
  if(!e || e.dead) return;
  e.dead = true;
  if(e.pickup) cargoLost(e);""")

# An empty freighter got through, but it delivered nothing.
sub("empty-not-saved",
"""crossDone++; protSaved++;
      allies.splice(i,1);""",
"""crossDone++; if(!a.emptyRun) protSaved++;
      { const _fi = allies.indexOf(a); if(_fi>=0) allies.splice(_fi,1); }""")

# Found by docksim: the cargo usually sits before its carrier in allies.
# Splicing it first moved the carrier down one place, and splice(i,1) then
# removed whichever ship came next - the carrier stayed, crossed the edge
# again and was counted twice. Walk a copy and remove by identity.
sub("cross-loop",
"""  for(let i=allies.length-1;i>=0;i--){
    const a = allies[i];
    if(!a.crossing || a.dead) continue;""",
"""  for(const a of allies.slice()){
    if(!a.crossing || a.dead || allies.indexOf(a)<0) continue;""")
sub("empty-msg",
"""txt: (hullClass(a.img)==='ep') ? 'RESCUED' : 'DELIVERED',""",
"""txt: (hullClass(a.img)==='ep') ? 'RESCUED'
                          : (a.emptyRun ? 'LEFT EMPTY' : 'DELIVERED'),""")

def main():
    if not os.path.exists(SRC): sys.exit("MISSING: "+SRC)
    txt = io.open(SRC, encoding="utf-8").read()
    for t, a, b in edits:
        n = txt.count(a)
        if n != 1: sys.exit("ABORT %s: %d matches instead of 1" % (t, n))
        txt = txt.replace(a, b, 1); print("  ok   "+t)
    io.open(DST, "w", encoding="utf-8").write(txt)
    print("written: "+DST)
main()
