// ── DOCKING FROM THE MODELS (F99, v283) ─────────────────────────────
// Decided by Silvio (24.10.2026): docking is never solved per mission or
// per ship. Every dock runs on the dock data of the FreeSpace models
// (tools/pof/mkdocks.py -> MOUNTS[hull].docks) and through one procedure:
//   go    she drives up - forwards, turning visibly - until she holds just
//         clear of the target, straight over or under its dock point; a
//         ship whose dock faces the same way as the target's rolls half
//         round on the way (the Halkins under the Taranis, F51)
//   in    she slides in, slowly and straight along the dock path (the
//         Chronos rises into the container, the Poseidon sinks onto it)
//   on    in contact: loading/boarding (dockHold) and the rest as before
// A container waits the way up its freighter needs it (dkPlanFor), and
// from the moment she slides in it is drawn with her, in her depth, so her
// arms and end blocks lie in front of it or behind it as they really are
// (f3dCargoHost, 59_field3d.js). Where the two touch comes from the height
// maps of both hulls: nothing goes through anything (dkMeet).
//
// Coordinates of a dock (mkdocks.py): shares of half the model's length,
// x along her length as the sprite faces, y down, d towards the viewer;
// half her length in the field is img.width*sc/2 (dkHalf).

const DK_SLIDE = 0.33;            // sliding in along the path, per step (0.6 DOCK_SPD)
const DK_MARGIN = 6;              // air left before she slides in
const DK_DEPTH_STEPS = 80;        // a container goes into her depth (0.8 s)

function dkList(o){ const m = o && mountsFor(o.img); return (m && m.docks) || []; }
// Has this hull dock data from its model (the new form)?
function dkHas(o){ const l = dkList(o); return !!(l.length && l[0].p && l[0].hm); }
function dkHalf(o){ const img = IMGS[o.img]; return img ? img.width*o.sc*0.5 : 30; }
function dkIsCargo(d){ return /cargo/i.test((d && d.n) || ''); }
// A dock facing straight into or out of the picture (the Faustus' port and
// starboard docks) cannot be reached in a side view.
function dkInPlane(d){ return !!(d && d.v && Math.abs(d.v[2]) < 0.7); }
// Which of her docks a ship uses: a container is taken on her cargo dock,
// a ship is met with her first other dock.
function dkPick(o, toCargo){
  const L = dkList(o);
  if(o.type === 'container' || L.length < 2) return 0;
  let i = toCargo ? L.findIndex(function(d){ return dkIsCargo(d) && dkInPlane(d); }) : -1;
  if(i < 0) i = L.findIndex(function(d){ return !dkIsCargo(d) && dkInPlane(d); });
  if(i < 0) i = L.findIndex(dkInPlane);
  return i < 0 ? 0 : i;
}
// Cargo riding from the start (ride/slot): slot n is her n-th cargo dock,
// those on the side towards the viewer first (the Asmodeus has two on
// each side; one behind the other would hide).
function dkRideIndex(f, slot){
  const L = dkList(f), near = [], far = [];
  L.forEach(function(d, i){ if(dkIsCargo(d) && dkInPlane(d)) (d.p[2] >= 0 ? near : far).push(i); });
  const all = near.concat(far);
  return all.length ? all[Math.min(slot || 0, all.length - 1)] : dkPick(f, true);
}
// Is she drawn facing right (the 3D model's yaw, f3dMat)?
function dkRight(o, flip){ return (spriteFacing(o.img) === 'right') !== !!(flip == null ? o.flip : flip); }
// Dock i of o in the field: position, depth (towards the viewer, relative
// to her middle) and the way it faces. r: her roll (1, or -1 rolled half
// round); flip: her heading if it is not the present one.
function dkPose(o, i, r, flip){
  const d = dkList(o)[i], H = dkHalf(o);
  const sx = (flip != null) ? ((flip ? -1 : 1)) : (o.flip ? -1 : 1)*(o.turnC != null ? o.turnC : 1);
  if(r == null) r = (o.rollC != null ? o.rollC : 1);
  const ds = (dkRight(o, flip) ? -1 : 1)*r;
  return {x: o.x + d.p[0]*H*sx, y: o.y + d.p[1]*H*r, z: d.p[2]*H*ds,
          vx: d.v[0]*sx, vy: d.v[1]*r, sx: sx, r: r, ds: ds, d: d, H: H};
}
function dkGrid(d){
  const hm = d && d.hm;
  if(!hm) return null;
  if(!hm._g) hm._g = String(hm.g).split(',').map(function(s){ return s === '' ? null : (+s)/1000; });
  return hm;
}
// How far the hull reaches out beyond the dock's plane (field units).
function dkClear(o, i){ const d = dkList(o)[i]; return (d && d.clear || 0)*dkHalf(o); }
// How A and B meet, docked face to face: the gap between their two dock
// points - the least at which no cell of A's height map meets one of B's
// (a container that fits sits on her dock, gap 0; one too long for the
// Chronos' deck rests on her end blocks) - and, for a container, how much
// thinner than its model it is drawn towards the viewer.
// Why thinner: the side view shows a container's length and height, never
// its depth. The Poseidon's arms hold it from both sides (Silvio, F97); a
// container wider than the room between them is drawn only as deep as
// that room, as F97 did with a fixed share (v281) - here the room is
// measured on her model. A wall is a row of her hull reaching out beyond
// DK_WALL of the container's height, inside its length; low bumps on a
// deck (the Bast) are no walls, the container rests on them.
const DK_WALL = 0.3;
function dkMeet(A, iA, rA, fA, B, iB, rB, thinOk){
  const PA = dkPose(A, iA, rA, fA), PB = dkPose(B, iB, rB);
  const ga = dkGrid(PA.d), gb = dkGrid(PB.d);
  if(!ga || !gb) return {gap: 0, thin: 1};
  // the common line along both dock planes in the picture
  let tx = -PB.vy, ty = PB.vx; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
  const ka = (ga.uv[0]*PA.sx*tx + ga.uv[1]*PA.r*ty), kb = (gb.uv[0]*PB.sx*tx + gb.uv[1]*PB.r*ty);
  if(Math.abs(kb) < 0.3 || Math.abs(gb.wd) < 0.3) return {gap: 0, thin: 1};   // not face to face
  const ca = ga.c*PA.H, cb = gb.c*PB.H;
  const wa = ga.wd*PA.ds, wb = gb.wd*PB.ds;
  // B's extent along the line and across (depth), field units
  let s0 = 1e9, s1 = -1e9, half = 0;
  for(let r = 0; r < gb.nw; r++) for(let c = 0; c < gb.nu; c++){
    if(gb._g[r*gb.nu + c] == null) continue;
    const sv = (c + gb.u0)*cb*kb, dv = Math.abs((r + gb.w0)*cb*wb);
    if(sv < s0) s0 = sv; if(sv > s1) s1 = sv; if(dv > half) half = dv;
  }
  let thin = 1;
  if(thinOk && half > 0){
    const wall = DK_WALL*dkDepthOf(B, iB);
    let near = 1e9, mid = false;
    for(let r = 0; r < ga.nw; r++){
      const dep = (r + ga.w0)*ca*wa;
      let isWall = false;
      for(let c = 0; c < ga.nu && !isWall; c++){
        const ha = ga._g[r*ga.nu + c], sv = (c + ga.u0)*ca*ka;
        if(ha != null && ha*PA.H > wall && sv >= s0 - ca && sv <= s1 + ca) isWall = true;
      }
      if(!isWall) continue;
      if(Math.abs(dep) < ca) mid = true;
      near = Math.min(near, Math.abs(dep) - ca);
    }
    if(!mid && near < half) thin = Math.max(0.05, near/half);
  }
  let gap = -1e9;
  for(let r = 0; r < ga.nw; r++){
    const dep = (r + ga.w0)*ca*wa;                    // depth of this row
    const jb = Math.round(dep/thin/(cb*wb)) - gb.w0;
    if(jb < 0 || jb >= gb.nw) continue;
    for(let c = 0; c < ga.nu; c++){
      const ha = ga._g[r*ga.nu + c];
      if(ha == null) continue;
      const sv = (c + ga.u0)*ca*ka;                    // along the line
      const ib = Math.round(sv/(cb*kb)) - gb.u0;
      if(ib < 0 || ib >= gb.nu) continue;
      const hb = gb._g[jb*gb.nu + ib];
      if(hb == null) continue;
      const g = ha*PA.H + hb*PB.H;
      if(g > gap) gap = g;
    }
  }
  return {gap: Math.max(0, gap), thin: thin};
}
// A hull's own height along the way its dock faces (field units): a
// container stands this tall off her dock.
function dkDepthOf(o, i){
  const m = mountsFor(o.img), d = dkList(o)[i];
  if(!m || !m.m3d || !d) return 0;
  const sz = m.m3d.size, k = dkHalf(o)/(m.m3d.len/2);
  return (Math.abs(d.v[1]) >= Math.abs(d.v[0]) ? sz[1] : sz[0])*k;
}
// Must she roll half round to meet this dock? Her dock and the target's
// must face each other.
function dkMustRoll(A, iA, B, iB){
  const a = dkList(A)[iA], b = dkPose(B, iB);
  if(!a) return false;
  const ay = a.v[1]*(A.rollC != null ? A.rollC : 1);
  return Math.abs(b.vy) >= Math.abs(b.vx) && ay*b.vy > 0;
}
// Before a container ever moves: which of a group lie upside down, so that
// every freighter coming for the group finds one the way up she needs it
// (the Poseidon holds a VC3 under her keel, the Chronos and the Ma'at on
// their decks). Each freighter that needs one takes the nearest still free.
let DK_PLAN = {wave: null, g: {}};
function dkNeedsUpsideDown(dkey, ckey){
  const dm = MOUNTS[dkey], cm = MOUNTS[ckey];
  if(!dm || !cm || !dm.docks || !cm.docks || !cm.docks[0] || !cm.docks[0].v) return false;
  const i = dm.docks.findIndex(function(d){ return dkIsCargo(d) && dkInPlane(d); });
  const a = dm.docks[i < 0 ? 0 : i];
  return !!(a && a.v && a.v[1]*cm.docks[0].v[1] > 0);
}
function dkPlanFor(gid){
  const w = (typeof wave !== 'undefined') ? wave : 0;
  if(DK_PLAN.wave !== w) DK_PLAN = {wave: w, g: {}};
  if(DK_PLAN.g[gid]) return DK_PLAN.g[gid];
  const def = (typeof SCRIPT_WAVES !== 'undefined') ? SCRIPT_WAVES[w] : null, us = (def && def.u) || [];
  const conts = us.filter(function(u){ return u.id === gid && u.c === 'fc'; });
  const plan = {n: 0, flip: conts.map(function(){ return false; })};
  for(const u of us){
    if(u.dockTo !== gid || !u.spr) continue;
    let best = -1, bd = 1e18;
    conts.forEach(function(c, j){
      if(plan.flip[j] || !dkNeedsUpsideDown(u.spr, c.spr)) return;
      const d = Math.pow((c.x||0) - (u.x||0), 2) + Math.pow((c.y||0) - (u.y||0), 2);
      if(d < bd){ bd = d; best = j; }
    });
    if(best >= 0) plan.flip[best] = true;
  }
  return DK_PLAN.g[gid] = plan;
}
// A container as it is placed: upside down if its plan says so.
function dkPlaceCargo(e, uid){
  if(!e || e.type !== 'container' || !uid || !dkHas(e)) return;
  const plan = dkPlanFor(uid), j = plan.n++;
  if(plan.flip[j]){ e.rollV = 1; e.rollC = -1; }
}
// Where carried cargo sits: its dock on hers, as far off as their two
// hulls let it (dkMeet). Also its depth against her middle (c._seatZ)
// and how thin it is drawn between her arms (c._thin).
function dkSeat(f, c, iA){
  if(iA == null) iA = (f._dk && f._dk.t === c) ? f._dk.iA : dkPick(f, true);
  if(c._gapFor !== f || c._gapI !== iA){
    c._gapFor = f; c._gapI = iA;
    const mt = dkMeet(f, iA, null, null, c, 0, null, true);
    c._gap = mt.gap; c._thin = mt.thin;
  }
  const A = dkPose(f, iA), C = dkPose(c, 0);
  const px = A.x + A.vx*c._gap, py = A.y + A.vy*c._gap;
  c._seatZ = A.z - C.z;
  return {x: px - (C.x - c.x), y: py - (C.y - c.y)};
}
// One step of her way to the dock. True once she is in contact.
function dkApproach(e, t){
  const toC = t.type === 'container';
  let k = e._dk;
  if(!k || k.t !== t){
    k = e._dk = {t: t, iA: dkPick(e, toC), iB: dkPick(t, false), ph: 'go'};
    // the way she will face: towards it, from the side she comes from;
    // she keeps it to the end (nothing flies backwards, F24)
    k.left = t.x < e.x;
    k.flip = needsFlip(e.img, k.left);
    k.roll = dkMustRoll(e, k.iA, t, k.iB);
    const r0 = (e.rollC != null ? e.rollC : 1);
    k.rEnd = k.roll ? -r0 : r0;
    const mt = dkMeet(e, k.iA, k.rEnd, k.flip, t, k.iB, null, toC);
    k.gap = mt.gap; k.thin = mt.thin;
    k.stand = Math.max(k.gap, dkClear(e, k.iA) + dkClear(t, k.iB)) + DK_MARGIN;
    if(!!e.flip !== k.flip){
      // F96: one seen arriving turns; one there from the start is set
      if(!(e.warpMax > 1) && !e._dockFaced){ e.flip = k.flip; }
      else faceTurn(e, k.left);
    }
    e._dockFaced = true;
  }
  // her half roll (v254, F51), now wherever the two docks face the same way
  if(k.roll && (e.rollV == null || e.rollV < 1)){
    if(e.rollV == null) e.rollV = 0;
    e.rollV = Math.min(1, e.rollV + 1/DOCK_ROLL_STEPS);
    e.rollC = Math.cos(Math.PI*e.rollV);
  }
  const B = dkPose(t, k.iB), A = dkPose(e, k.iA, k.rEnd, k.flip);
  const ox = A.x - e.x, oy = A.y - e.y;
  if(k.ph === 'go'){
    const hx = B.x + B.vx*k.stand - ox, hy = B.y + B.vy*k.stand - oy;
    const dx = hx - e.x, dy = hy - e.y, L = Math.hypot(dx, dy);
    if(k.best == null || L < k.best - 0.05){ k.best = L; k.stall = 0; } else k.stall++;
    if(L > 1 && !(L <= DOCK_NEAR && k.stall > 60)){
      // lengthwise over the target, but not yet at her height: height
      // first, so she never sweeps through it
      const over = Math.abs(e.x - t.x) < dkHalf(e) + dkHalf(t) + DK_MARGIN;
      let mx = Math.max(-DOCK_SPD*1.6, Math.min(DOCK_SPD*1.6, dx));
      const my = Math.max(-DOCK_SPD, Math.min(DOCK_SPD, dy));
      if(over && Math.abs(dy) > 2) mx = 0;
      e.x += mx; e.y += my;
      return false;
    }
    if((k.roll && e.rollV < 1) || e._face) return false;     // turned and rolled first
    if(L <= 1){ e.x = hx; e.y = hy; }        // held off the spot (field edge): slides from where she is
    k.ph = 'in';
  }
  if(k.ph === 'in'){
    // from now on it is drawn with her, in her depth (f3dCargoHost)
    if(toC){ t._inBy = e; t._dz = Math.min(1, (t._dz || 0) + 1/DK_DEPTH_STEPS); t._seatZ = A.z - B.z;
             t._thin = k.thin; t._gapFor = e; t._gapI = k.iA; t._gap = k.gap; }
    const cx = B.x + B.vx*k.gap - ox, cy = B.y + B.vy*k.gap - oy;
    const dx = cx - e.x, dy = cy - e.y, L = Math.hypot(dx, dy);
    if(L > DK_SLIDE){ e.x += dx/L*DK_SLIDE; e.y += dy/L*DK_SLIDE; return false; }
    e.x = cx; e.y = cy;
    if(toC && t._dz < 1) return false;
    k.ph = 'on';
  }
  return true;
}
// Casting off (abdocken): she slides back out along the dock path before
// she turns and goes (tickCrossGuards).
function dkCastOff(u){
  const k = u._dk;
  if(!k || k.ph !== 'on' || !k.t) return false;
  const B = dkPose(k.t, k.iB);
  u._dkOut = {vx: B.vx, vy: B.vy, left: Math.max(0, k.stand - k.gap)};
  return true;
}
function dkCastOffStep(a){
  const o = a._dkOut;
  if(!o) return false;
  const s = Math.min(DK_SLIDE, o.left);
  a.x += o.vx*s; a.y += o.vy*s; o.left -= s;
  if(o.left <= 0){ a._dkOut = null; faceTurn(a, a.crossing < 0); }
  return true;
}
// For the checks (docksim): how a freighter of key dk and a container of
// key ck at scale big meet - the gap, the container's height, whether she
// must roll and whether the container lies upside down.
function dkPairInfo(dk, ck, big){
  const f = {img: dk, x: 0, y: 0, sc: 1, flip: false}, c = {img: ck, type: 'container', x: 0, y: 0, sc: big || 1, flip: false};
  const ifr = IMGS[dk], ic = IMGS[ck];
  if(ifr && typeof hullWidth === 'function') f.sc = hullWidth(dk)/ifr.width;
  if(ic && typeof hullWidth === 'function') c.sc = hullWidth(ck)/ic.width*(big || 1);
  const up = dkNeedsUpsideDown(dk, ck);
  if(up){ c.rollV = 1; c.rollC = -1; }
  const iA = dkPick(f, true), mt = dkMeet(f, iA, null, null, c, 0, null, true);
  return {gap: mt.gap, thin: mt.thin, height: dkDepthOf(c, 0), upsideDown: up,
          roll: dkMustRoll(f, iA, c, 0)};
}
