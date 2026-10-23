// ── PHIDIAS REPAIR DRONES (v275, F89) ─────────────────────────
// Decided with Silvio, 23.10.2026 (OFFENE_FEHLER.md, F89, "Reparatur"):
// - A transport sends out Phidias drones that repair a capital ship with
//   a beam. Only the hull is repaired, never a subsystem.
// - Always ten drones. They fly like fighters and work along her hull,
//   the damage marks first; a mark fades under the beam and is gone.
// - Done when her hull is full; how fast is the mission's (repPct: per
//   cent of her hull per second with all ten at work). Then the drones fly
//   back and the transport jumps out.
// - Drones and transport can be shot down. The transport lost: the
//   drones flee to the nearer edge, left or right. Drones shot: the rest
//   work on until the hull is full or none is left; none left first and
//   the transport jumps, the repair failed.
// - The drone is Mike's Phidias (his OK given), drawn at 10 m. Model,
//   beam pictures and sounds come with the model ZIP, not from the repo.
// Mission language: on the transport unit repair:'<ship id>', repPct:N;
// triggers 'repariert' (ship id) and 'reparaturGescheitert' (transport).
const REP_HULL = 'suphidias';
const REP_DRONES = 10;
const REP_GAP = 35;            // steps between two launches
const REP_HOLD_D = 30;         // how far from her plating a drone hovers
const REP_ARRIVE = 14;         // close enough to its place to start the beam
const REP_LOST = 60;           // pushed this far off its place: fly back to it
const REP_FADE_MIN = 150, REP_FADE_MAX = 800;   // steps one mark takes to fade
const REP_BARE = 300;          // a stretch of hull without a mark: steps of beam
const REP_PTS = 25;            // an enemy drone shot down
const REP_SPREAD = 90;         // drones keep about this far from each other's work

function repairSetup(t, sp){
  t.repairId = sp.repair;
  t.repPct = (sp.repPct > 0) ? sp.repPct : 1;
  t.rep = {n: 0, next: REP_GAP, state: 'work', drones: [], target: null};
}
function repTarget(t){
  const S = byId(t.repairId)[0];
  return (S && !S.dead && S.rollT == null && !(S.warpOut > 0) && !(S.warp > 0)) ? S : null;
}
function repAlive(o){ return unitAlive(o) && o.rollT == null && o.hp > 0; }
// Hull points one beaming drone puts back per step.
function repRate(t, S){ return S.maxHp*t.repPct/100/TICK_HZ/REP_DRONES; }
function repJump(t){
  if(!(t.warpOut > 0)){ t.warpOut = t.warpMax = 120; t.warpX = t.x; t.warpY = t.y; }
  if(t.uid) EV_LEFT[t.uid] = true;
  t.rep.state = 'gone';
}
function repLaunch(t, S){
  const d = mkAllySmall('fighter', t.faction || 'terran', REP_HULL, t.y);
  d.x = d.warpX = t.x; d.y = d.warpY = t.y;
  d.warp = 0; d.warpMax = 70;          // out of the hold, no vortex; at the end it jumps like a fighter
  d.drone = true; d.host = t; d.mode = 'out'; d.spot = null;
  d.fT = 1e9;                           // never fires
  d.minY = WY0; d.maxY = WY1;
  d.head = Math.atan2(S.y - t.y, S.x - t.x) + (Math.random() - 0.5)*1.2;
  d.cs = d.spd*0.6; d.vx = Math.cos(d.head)*d.cs; d.vy = Math.sin(d.head)*d.cs;
  const p = poseFor(d.head, d.flip); d.ang = p.ang; d.flip = p.flip;
  if(t.side === 'ally') allies.push(d);
  else { d.side = 'enemy'; d.pts = REP_PTS; enemies.push(d); }
  t.rep.drones.push(d);
}
// Once a step: the transports with a repair job.
function repairTick(){
  for(const t of enemies.concat(allies)){
    const R = t.rep;
    if(!R || t.dead || t.rollT != null || t.warp > 0 || R.state === 'gone') continue;
    R.drones = R.drones.filter(repAlive);
    const S = repTarget(t);
    if(S) R.target = S;
    if(R.state === 'work'){
      if(!S){ if(evSeen(t.repairId) && !idPending(t.repairId)) R.state = 'home'; }
      else if(S.hp >= S.maxHp){
        S.hp = S.maxHp; R.state = 'home';
        if(S.uid) EV_REPAIRED[S.uid] = true;
      } else {
        if(R.n < REP_DRONES && --R.next <= 0){ repLaunch(t, S); R.n++; R.next = REP_GAP; }
        if(R.n >= REP_DRONES && !R.drones.length){
          if(t.uid) EV_REPFAIL[t.uid] = true;
          repJump(t);
          continue;
        }
      }
    }
    // Done: what marks are left go quietly, the drones are on their way back.
    if(R.state === 'home'){
      const T = R.target, D = T && T.dm;
      if(D && T.hp >= T.maxHp){
        for(let i = D.scorch.length - 1; i >= 0; i--){
          const s = D.scorch[i]; s.fix = (s.fix||0) + 1/TICK_HZ;
          if(s.fix >= 1) D.scorch.splice(i, 1);
        }
        for(const g of D.gashes) g.fix = Math.min(1, (g.fix||0) + 1/TICK_HZ);
        if(fc % 10 === 0) D.dirty = true;
      }
      if(!R.drones.length) repJump(t);
    }
  }
  repSndTick();
}
// A place on her hull to work on: a damage mark no other drone has - near
// to it, and away from where the others work, so they spread over her -
// else a solid stretch of plating.
function repPickSpot(S, e){
  const D = S.dm, R = e.host.rep, mine = new Set(), others = [];
  for(const o of R.drones) if(o !== e && o.spot){ if(o.spot.m) mine.add(o.spot.m); others.push(repSpotPt(S, o.spot)); }
  let best = null, bd = Infinity;
  if(D && IMGS[S.img]){
    const marks = D.scorch.concat(D.gashes.filter(function(g){ return !g.fixed; }));
    for(const m of marks){
      if(mine.has(m) || (m.fix||0) >= 1) continue;
      const p = dmgWorld(S, m.u, m.v);
      let near = REP_SPREAD;
      for(const q of others) near = Math.min(near, Math.hypot(q.x - p.x, q.y - p.y));
      const cost = Math.hypot(p.x - e.x, p.y - e.y)*0.3 - near;
      if(cost < bd){ bd = cost; best = m; }
    }
  }
  let u, v;
  if(best){ u = best.u; v = best.v; }
  else {
    u = Math.random()*1.6 - 0.8; v = Math.random()*1.0 - 0.5;
    for(let i = 0; i < 12 && D && !dmgSolid(D.inf, u, v, 0); i++){ u = Math.random()*1.6 - 0.8; v = Math.random()*1.0 - 0.5; }
  }
  // hovers outward of the spot, seen from her middle
  const out = Math.atan2(v, u*2) + (Math.random() - 0.5)*1.4;
  return {m: best, u: u, v: v, ang: out, t: 0};
}
function repSpotPt(S, sp){
  if(IMGS[S.img]) return dmgWorld(S, sp.u, sp.v);
  const hw = hullWidth(S.img)/2;
  return {x: S.x + sp.u*hw*(S.flip ? -1 : 1), y: S.y + sp.v*hw*0.25};
}
function repHoldPt(S, sp){
  const p = repSpotPt(S, sp);
  return {x: p.x + Math.cos(sp.ang)*REP_HOLD_D, y: p.y + Math.sin(sp.ang)*REP_HOLD_D, px: p.x, py: p.y};
}
function repBeam(e, on){
  if(!!e.beamOn === on) return;
  e.beamOn = on;
  if(typeof sndPlay === 'function') sndPlay(on ? 'repair_up' : 'repair_down', e.x, 1, e.y);
}
// One step of a drone. true: it is gone (back aboard, or out at the edge).
function droneTick(e){
  const t = e.host, R = t && t.rep;
  if(!t || !R || !repAlive(t) || (t.warpOut > 0 && R.state !== 'gone')){
    if(e.mode !== 'flee'){ repBeam(e, false); e.mode = 'flee'; e.fleeX = (e.x < (WX0 + WX1)/2) ? WX0 - 100 : WX1 + 100; }
  } else if(R.state !== 'work' && e.mode !== 'home'){ repBeam(e, false); e.mode = 'home'; }
  if(e.mode === 'flee'){
    flyDrone(e, e.fleeX, e.y, false);
    const b = shipBound(e);
    if(e.x <= WX0 + b + 3 || e.x >= WX1 - b - 3){ if(e.uid) EV_LEFT[e.uid] = true; return true; }
    return false;
  }
  if(e.mode === 'home'){
    flyDrone(e, t.x, t.y, true);
    return Math.hypot(t.x - e.x, t.y - e.y) < Math.max(14, shipBound(t)*0.35);
  }
  const S = repTarget(t);
  if(!S){ flyDrone(e, t.x, t.y, true); return false; }
  if(!e.spot || (e.spot.m && (e.spot.m.fix||0) >= 1)){ e.spot = repPickSpot(S, e); repBeam(e, false); e.mode = 'out'; }
  const h = repHoldPt(S, e.spot);
  const dh = Math.hypot(h.x - e.x, h.y - e.y);
  if(e.mode === 'out'){
    flyDrone(e, h.x, h.y, true);
    if(dh < REP_ARRIVE){
      e.mode = 'beam'; repBeam(e, true);
      // how long its mark takes: the marks left share out the time the
      // hull still needs, so the last one goes about as she is full
      const D = S.dm, left = D ? D.scorch.length + D.gashes.filter(function(g){ return !g.fixed; }).length : 0;
      const n = Math.max(1, R.drones.length), need = (S.maxHp - S.hp)/(repRate(t, S)*n);
      e.spot.steps = Math.max(REP_FADE_MIN, Math.min(REP_FADE_MAX, need*n/Math.max(1, left)*0.7));
    }
    return false;
  }
  // beam: hold the place, nose on the spot, and work
  if(dh > REP_LOST){ e.mode = 'out'; repBeam(e, false); return false; }
  droneHover(e, h);
  S.hp = Math.min(S.maxHp, S.hp + repRate(t, S));
  const m = e.spot.m;
  if(m){
    m.fix = Math.min(1, (m.fix||0) + 1/(e.spot.steps || REP_FADE_MIN));
    if(S.dm && fc % 8 === 0) S.dm.dirty = true;
    if(m.fix >= 1){
      const D = S.dm, k = D ? D.scorch.indexOf(m) : -1;
      if(k >= 0) D.scorch.splice(k, 1); else m.fixed = true;
      if(D) D.dirty = true;
      e.spot = null; e.mode = 'out'; repBeam(e, false);
    }
  } else if(++e.spot.t >= REP_BARE){ e.spot = null; e.mode = 'out'; repBeam(e, false); }
  return false;
}
// Flight towards a point with the fighters' flight model (flySmall): the
// turn builds up and dies away, the path follows the nose with a lag.
// arrive: slows down on the last stretch.
function flyDrone(e, px, py, arrive){
  const dx = px - e.x, dy = py - e.y, d = Math.hypot(dx, dy) || 0.001;
  let want = 1;
  if(arrive) want = Math.max(0.25, Math.min(1, d/120));
  let df = Math.atan2(dy, dx) - e.head;
  while(df > Math.PI) df -= Math.PI*2;
  while(df < -Math.PI) df += Math.PI*2;
  const tw = Math.max(-e.turn, Math.min(e.turn, df));
  e.tv = (e.tv||0);
  e.tv += Math.max(-e.turn*FLY_TURN_ACC, Math.min(e.turn*FLY_TURN_ACC, tw - e.tv));
  e.head += e.tv;
  if(e.head > Math.PI) e.head -= Math.PI*2; else if(e.head < -Math.PI) e.head += Math.PI*2;
  want *= 1 - 0.3*Math.min(1, Math.abs(df)/1.2);
  if(e.cs == null) e.cs = e.spd*want;
  const ca = e.spd*FLY_ACC;
  e.cs += Math.max(-ca, Math.min(ca, e.spd*want - e.cs));
  if(e.vx == null || !isFinite(e.vx)){ e.vx = 0; e.vy = 0; }
  // a drone does not slide past its spot: a tighter lag than a fighter's
  const sl = arrive && d < 80 ? FLY_SLIDE*3 : FLY_SLIDE;
  e.vx += (Math.cos(e.head)*e.cs - e.vx)*sl; e.vy += (Math.sin(e.head)*e.cs - e.vy)*sl;
  e.x += e.vx; e.y += e.vy;
  const b = shipBound(e);
  e.x = Math.max(WX0 + b, Math.min(WX1 - b, e.x));
  e.y = Math.max(WY0 + b, Math.min(WY1 - b, e.y));
  const p = poseFor(e.head, e.flip); e.ang = p.ang; e.flip = p.flip;
}
// At its place: almost still, drifting with her, the nose turning onto
// the spot so the beam leaves it straight.
function droneHover(e, h){
  const want = Math.atan2(h.py - e.y, h.px - e.x);
  let df = want - e.head;
  while(df > Math.PI) df -= Math.PI*2;
  while(df < -Math.PI) df += Math.PI*2;
  const tw = Math.max(-e.turn, Math.min(e.turn, df));
  e.tv = (e.tv||0);
  e.tv += Math.max(-e.turn*FLY_TURN_ACC, Math.min(e.turn*FLY_TURN_ACC, tw - e.tv));
  e.head += e.tv;
  if(e.head > Math.PI) e.head -= Math.PI*2; else if(e.head < -Math.PI) e.head += Math.PI*2;
  e.cs = (e.cs||0)*0.95;
  e.vx = (e.vx||0)*0.92 + (h.x - e.x)*0.004;
  e.vy = (e.vy||0)*0.92 + (h.y - e.y)*0.004;
  e.x += e.vx; e.y += e.vy;
  const p = poseFor(e.head, e.flip); e.ang = p.ang; e.flip = p.flip;
}

// ── the beam on the field ──
// Mike's pictures (models/suphidias/repair_*.webp) once they are there; a
// plain golden ray of the same colour until then, or without them.
const REP_FX = {core: null, haze: null, glow: null, spark: null, asked: false};
const REP_COL = '#ffd860';
function repFxLoad(){
  if(REP_FX.asked || typeof Image === 'undefined') return;
  REP_FX.asked = true;
  for(const k of ['core', 'haze', 'glow', 'spark']){
    const img = new Image();
    img.onload = function(){ REP_FX[k] = img; };
    img.src = ((typeof M3D_BASE !== 'undefined') ? M3D_BASE : 'models/') + REP_HULL + '/repair_' + k + '.webp';
  }
}
function drawRepairBeams(){
  let any = false;
  for(const L of [allies, enemies]) for(const e of L){
    if(!e.drone || !e.beamOn || e.mode !== 'beam' || !e.spot) continue;
    const S = e.host && e.host.rep && e.host.rep.target;
    if(!S || S.dead) continue;
    if(!any){ any = true; repFxLoad(); camOn(); ctx.save(); ctx.globalCompositeOperation = 'lighter'; }
    const p = repSpotPt(S, e.spot);
    const nose = shipBound(e)*0.8;
    const x0 = e.x + Math.cos(e.head)*nose, y0 = e.y + Math.sin(e.head)*nose;
    const dx = p.x - x0, dy = p.y - y0, len = Math.hypot(dx, dy), ang = Math.atan2(dy, dx);
    if(!(len > 1)) continue;
    const w = 3.2, fl = 0.85 + 0.15*Math.sin(fc*0.31 + (e.x|0));
    ctx.save(); ctx.translate(x0, y0); ctx.rotate(ang);
    if(REP_FX.core){
      if(REP_FX.haze){
        const hw = REP_FX.haze.width, off = (fc*2) % hw;
        ctx.globalAlpha = 0.55*fl;
        ctx.drawImage(REP_FX.haze, off, 0, hw - off, REP_FX.haze.height, 0, -w*2.2, len*(hw - off)/hw, w*4.4);
        ctx.drawImage(REP_FX.haze, 0, 0, off, REP_FX.haze.height, len*(hw - off)/hw, -w*2.2, len*off/hw, w*4.4);
      }
      ctx.globalAlpha = fl;
      ctx.drawImage(REP_FX.core, 0, -w, len, w*2);
    } else {
      ctx.restore();
      if(typeof drawBeamRay === 'function') drawBeamRay(x0, y0, ang, len, w*0.6, REP_COL, 0.9*fl, fc, w);
      ctx.save(); ctx.translate(x0, y0); ctx.rotate(ang);
    }
    ctx.restore();
    // the glow at both ends, the sparks where it meets her plating
    if(REP_FX.glow){
      ctx.globalAlpha = 0.8*fl;
      ctx.drawImage(REP_FX.glow, x0 - w*1.5, y0 - w*1.5, w*3, w*3);
      ctx.drawImage(REP_FX.glow, p.x - w*2.5, p.y - w*2.5, w*5, w*5);
    } else if(typeof glowAt === 'function'){
      glowAt(x0, y0, w*2, w*2, REP_COL, 0.7*fl, 0.9);
      glowAt(p.x, p.y, w*3.5, w*3.5, REP_COL, 0.8*fl, 0.9);
    }
    if(REP_FX.spark){
      const fr = ((fc/4.5)|0) % 11, c = REP_FX.spark.height;
      ctx.globalAlpha = 0.9;
      ctx.drawImage(REP_FX.spark, fr*c, 0, c, c, p.x - w*2.5, p.y - w*2.5, w*5, w*5);
    }
    ctx.globalAlpha = 1;
  }
  if(any){ ctx.restore(); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; }
}
// One loop for the whole repair, at the ship being worked on, while any
// drone has its beam on (ten loops at once would drown the field).
let REP_LOOP = null;
function repSndTick(){
  if(typeof sndCtx === 'undefined' || !sndCtx) return;
  let at = null;
  for(const L of [allies, enemies]) for(const e of L) if(e.drone && e.beamOn){ at = e; break; }
  if(at && !REP_LOOP) REP_LOOP = sndStart('repair_loop', at.x, 1, true, 'repair_loop', at.y);
  else if(!at && REP_LOOP){ sndStop(REP_LOOP); REP_LOOP = null; }
  else if(at && REP_LOOP && fc % 10 === 0) REP_LOOP._g.gain.value = REP_LOOP._base*sndAtt(at.x, at.y);
}
