// ── TARGETING (v210) ───────────────────────────────────────────
// FreeSpace 2 targeting (Silvio): the player holds one target - a ship or
// a bomb - and on a ship one of her subsystems. Keys as in FS2 (BINDS,
// 'target'): T / Shift+T every ship, H / Shift+H hostiles, F / Shift+F
// friendlies, Y the ship in the reticle, R the nearest ship attacking the
// player, B / Shift+B bombs, S / Shift+S / V subsystems. A target that is
// lost (destroyed, gone, out of sight) is replaced by the nearest hostile
// at once (Silvio), as is no target at all.
// What hangs on it: brackets in her side colour, the lead indicator of
// the primaries, the aspect lock of the secondaries, the edge marker, and
// the radar window in the bar with her model (drawBarScope).
const TGT = {e: null, sub: null, lock: 0, lockOf: null, px: 0, py: 0, vx: 0, vy: 0};
const TGT_LOCK_CONE = 0.35;    // rad off the nose a lock is built in (the reticle)
const TGT_RETICLE_CONE = 0.35; // rad: Y / V take what lies within this of the nose
function tgtIsBomb(o){ return !!o && o.kind === 'bomb' && eBullets.indexOf(o) >= 0 && (o.hp||0) > 0; }
// May the player hold this one?
function tgtCan(o){
  if(!o) return false;
  if(o.kind === 'bomb') return tgtIsBomb(o);
  if(o.dead || o.type === 'asteroid' || o.scenery || o.ghost || o.invuln && o.scenery) return false;
  if(o.warp > 0) return false;                              // still in her vortex
  const ally = allies.indexOf(o) >= 0;
  if(!ally && enemies.indexOf(o) < 0) return false;
  // a stealth hull cannot be held (the Loki of the NTF, as canLockOn)
  if(!ally && typeof LOCKLESS_HULLS !== 'undefined' && LOCKLESS_HULLS[o.img]) return false;
  // in the gas only as far as the chevrons are seen
  if(nebulaOn() && Math.hypot(o.x - player.x, o.y - player.y) > CHEV_FADE) return false;
  return true;
}
function tgtHostile(o){ return enemies.indexOf(o) >= 0 && !neutralLike(o); }   // F37
function tgtDist(o){ return Math.hypot(o.x - player.x, o.y - player.y); }
function tgtSet(o, sub){
  if(o !== TGT.e){ TGT.lock = 0; TGT.lockOf = null; TGT.vx = 0; TGT.vy = 0; if(o){ TGT.px = o.x; TGT.py = o.y; } }
  TGT.e = o || null; TGT.sub = sub || null;
}
// the next (dir 1) or previous (-1) of a list, nearest first
function tgtCycle(list, dir){
  if(!list.length) return null;
  list.sort(function(a, b){ return tgtDist(a) - tgtDist(b); });
  const i = list.indexOf(TGT.e);
  if(i < 0) return dir > 0 ? list[0] : list[list.length-1];
  return list[(i + dir + list.length) % list.length];
}
function tgtShips(f){
  const out = [];
  for(const e of enemies) if(tgtCan(e) && (!f || f(e))) out.push(e);
  for(const a of allies) if(tgtCan(a) && (!f || f(a))) out.push(a);
  return out;
}
function tgtNearestHostile(){
  let best = null, bd = Infinity;
  for(const e of enemies){
    if(!tgtCan(e) || !tgtHostile(e)) continue;
    const d = tgtDist(e); if(d < bd){ bd = d; best = e; }
  }
  return best;
}
// how far off the player's nose a point lies, rad
function tgtOff(x, y){
  let off = Math.atan2(y - player.y, x - player.x) - (player.head || 0);
  while(off > Math.PI) off -= Math.PI*2; while(off < -Math.PI) off += Math.PI*2;
  return Math.abs(off);
}
// where a ship is drawn (v210: a capital ship's model sunk below the plane)
function tgtDrawn(o){
  if(o && o.kind !== 'bomb' && typeof hullView === 'function'){
    const v = hullView(o);
    if(v) return {x: v.cx + (o.x - v.cx)*v.k, y: v.cy + (o.y - v.cy)*v.k};
  }
  return {x: o.x, y: o.y};
}
function tgtSubPos(o, s){
  const p = subPos(o, s);
  return (typeof hullPt === 'function') ? hullPt(o, p.x, p.y) : p;
}
// v210: heat seekers (FS2 +View Cone). Does a round flying along head see
// her within its half cone?
function heatSees(x, y, head, cone, o){
  const p = tgtDrawn(o);
  let off = Math.atan2(p.y - y, p.x - x) - head;
  while(off > Math.PI) off -= Math.PI*2; while(off < -Math.PI) off += Math.PI*2;
  return Math.abs(off) <= (cone || Math.PI/2);
}
// the nearest heat source in its cone and its reach; Stiletto II (bigFirst)
// looks among the capital ships first
function heatAcquire(b){
  const head = Math.atan2(b.vy, b.vx), reach = Math.hypot(b.vx, b.vy)*Math.max(1, b.life);
  const bigOnly = !!(b.wd && b.wd.bigFirst);
  for(let pass = 0; pass < 2; pass++){
    let best = null, bd = reach;
    for(const e of enemies){
      if(e.dead || !canLockOn(e) || (playerOnly(e) && e !== TGT.e)) continue;
      if(pass === 0 && bigOnly && !isLargeShip(e)) continue;
      const d = Math.hypot(e.x - b.x, e.y - b.y);
      if(d < bd && heatSees(b.x, b.y, head, b.cone, e)){ bd = d; best = e; }
    }
    if(best || !bigOnly) return best;
  }
  return null;
}
// The keys. True when the key was one of them.
function tgtKey(ev){
  const IDS = ['tgtNext', 'tgtPrev', 'tgtHostNext', 'tgtHostPrev', 'tgtFriendNext', 'tgtFriendPrev',
             'tgtReticle', 'tgtAttacker', 'tgtBombNext', 'tgtBombPrev', 'subNext', 'subPrev', 'subReticle'];
  let id = null;
  for(const k of IDS) if(bindIs(k, ev)){ id = k; break; }
  if(!id) return false;
  if(id === 'tgtNext' || id === 'tgtPrev') tgtSet(tgtCycle(tgtShips(), id === 'tgtNext' ? 1 : -1) || TGT.e);
  else if(id === 'tgtHostNext' || id === 'tgtHostPrev') tgtSet(tgtCycle(tgtShips(tgtHostile), id === 'tgtHostNext' ? 1 : -1) || TGT.e);
  else if(id === 'tgtFriendNext' || id === 'tgtFriendPrev'){
    const f = tgtCycle(tgtShips(function(o){ return allies.indexOf(o) >= 0; }), id === 'tgtFriendNext' ? 1 : -1);
    if(f) tgtSet(f);
  }
  else if(id === 'tgtReticle'){
    let best = null, bo = TGT_RETICLE_CONE;
    for(const o of tgtShips()){ const off = tgtOff(o.x, o.y); if(off < bo){ bo = off; best = o; } }
    if(best) tgtSet(best);
  }
  else if(id === 'tgtAttacker'){
    // whoever has the player as her prey, nearest first; else the nearest
    // hostile fighter or bomber
    let best = null, bd = Infinity;
    for(const e of enemies){
      if(!tgtCan(e) || e.focusOn !== player) continue;
      const d = tgtDist(e); if(d < bd){ bd = d; best = e; }
    }
    if(!best) for(const e of enemies){
      if(!tgtCan(e) || !tgtHostile(e) || (e.type !== 'fighter' && e.type !== 'bomber')) continue;
      const d = tgtDist(e); if(d < bd){ bd = d; best = e; }
    }
    if(best) tgtSet(best);
  }
  else if(id === 'tgtBombNext' || id === 'tgtBombPrev'){
    const bs = eBullets.filter(tgtIsBomb);
    const b = tgtCycle(bs, id === 'tgtBombNext' ? 1 : -1);
    if(b) tgtSet(b);
  }
  else if(TGT.e && TGT.e.subs && TGT.e.kind !== 'bomb'){
    const subs = TGT.e.subs.filter(function(s){ return !s.dead; });
    if(subs.length){
      if(id === 'subReticle'){
        let best = null, bo = TGT_RETICLE_CONE;
        for(const s of subs){ const p = subPos(TGT.e, s), off = tgtOff(p.x, p.y); if(off < bo){ bo = off; best = s; } }
        if(best) TGT.sub = best;
      } else {
        const i = subs.indexOf(TGT.sub), d = (id === 'subNext') ? 1 : -1;
        TGT.sub = (i < 0) ? subs[d > 0 ? 0 : subs.length-1] : subs[(i + d + subs.length) % subs.length];
      }
      TGT.lock = 0;
    }
  }
  return true;
}
// Once a step: keep the target valid, its motion for the lead, the lock.
function tgtTick(){
  if(GS !== 'playing') return;
  if(!tgtCan(TGT.e)) tgtSet(tgtNearestHostile());
  if(TGT.sub && (TGT.sub.dead || !TGT.e || !TGT.e.subs || TGT.e.subs.indexOf(TGT.sub) < 0)) TGT.sub = null;
  const o = TGT.e;
  if(o){
    TGT.vx = TGT.vx*0.6 + (o.x - TGT.px)*0.4; TGT.vy = TGT.vy*0.6 + (o.y - TGT.py)*0.4;
    TGT.px = o.x; TGT.py = o.y;
  }
  // The aspect lock (FS2 $Min Lock Time): the chosen secondary seeks by
  // aspect, the target is a ship that can be held, within its reach and
  // near the nose. Out of that the lock starts over.
  const bank = selSecBank(), w = bank ? secDefP(bank.key) : null;
  const key = w ? w.key : null;
  // v253 (Silvio): with a subsystem chosen the lock is taken on it, not on
  // the middle of the hull.
  const lp = (o && TGT.sub && !TGT.sub.dead && o.subs) ? tgtSubPos(o, TGT.sub) : o;
  if(TGT.lockOf !== key){ TGT.lock = 0; TGT.lockOf = key; }
  // v263 (F84, Silvio 22.10.2026): the lock builds wherever the target is,
  // as long as it is in the part of the field the player can see. Held
  // only near the nose and within reach, it broke off all the time against
  // targets that move this fast. One behind him is his own lookout: the
  // missile turns a long way round for it.
  if(w && w.homing === 'aspect' && o && o.kind !== 'bomb' && enemies.indexOf(o) >= 0 && canLockOn(o)
     && bank.ammo > 0 && camSees(lp.x, lp.y, 0)){
    TGT.lock = Math.min(TGT.lock + 1, w.lockT || 1);
  } else TGT.lock = 0;
  // F84: the seeker tone while it builds, the lock tone once it holds
  // (FS1 sounds.tbl: trk-loop.wav, lock.wav).
  if(typeof sndLock === 'function'){
    const _lt = (w && w.lockT) || 1;
    sndLock(TGT.lock > 0 && TGT.lock < _lt, TGT.lock > 0 && TGT.lock >= _lt);
  }
}
function tgtLocked(){
  const bank = selSecBank(), w = bank ? secDefP(bank.key) : null;
  return !!(w && w.homing === 'aspect' && TGT.e && TGT.lock >= (w.lockT || 1));
}
// the reach of the primaries now firing - linked, the shorter one
function tgtPriReach(){
  const fb = firingBanks();
  let r = Infinity, s = 0;
  for(const b of fb){ const w = priDefP(b.key); r = Math.min(r, (w.spd||0)*(w.life||0)); s = Math.max(s, w.spd||0); }
  return {reach: isFinite(r) ? r : 0, spd: s};
}
// where to aim so a bolt meets her (her motion as seen, bolt speed s)
function tgtLead(o, s){
  const p = tgtDrawn(o), dx = p.x - player.x, dy = p.y - player.y, vx = TGT.vx, vy = TGT.vy;
  const a = vx*vx + vy*vy - s*s, b = 2*(dx*vx + dy*vy), c = dx*dx + dy*dy;
  let t;
  if(Math.abs(a) < 1e-6) t = b ? -c/b : 0;
  else {
    const q = b*b - 4*a*c; if(q < 0) return null;
    const r1 = (-b - Math.sqrt(q))/(2*a), r2 = (-b + Math.sqrt(q))/(2*a);
    t = Math.min(r1, r2) > 0 ? Math.min(r1, r2) : Math.max(r1, r2);
  }
  if(!(t > 0)) return null;
  return {x: p.x + vx*t, y: p.y + vy*t};
}
// The marks on the field, on the screen (after camScreen): brackets, the
// subsystem, the lock and the lead indicator.
// v211 (Silvio): the marks as FreeSpace draws them (hudbrackets.cpp,
// draw_brackets_square): four corners, each a quarter of the box long and
// fading towards its end, round her drawn outline plus a margin, never
// smaller than FS's 30 px at 1024 (23 here). The distance as a plain
// number right aligned under the lower right corner. A dark edge under
// every line so the marks hold against fire and beams.
const TGT_BOX_MIN = 23, TGT_BOX_PAD = 3, MARK_HALO = 'rgba(0,0,0,0.78)';
function fsBrackets(x1, y1, x2, y2, col, lw, alpha){
  const bw = (x2-x1)/4, bh = (y2-y1)/4;
  const seg = [[x1,y1,x1+bw,y1],[x1,y2,x1+bw,y2],[x2,y1,x2-bw,y1],[x2,y2,x2-bw,y2],
               [x1,y1,x1,y1+bh],[x2,y1,x2,y1+bh],[x1,y2,x1,y2-bh],[x2,y2,x2,y2-bh]];
  ctx.save(); ctx.globalAlpha *= alpha; ctx.lineCap = 'butt';
  ctx.strokeStyle = MARK_HALO; ctx.lineWidth = lw + 2;
  ctx.beginPath(); for(const q of seg){ ctx.moveTo(q[0],q[1]); ctx.lineTo(q[2],q[3]); } ctx.stroke();
  ctx.lineWidth = lw;
  for(const q of seg){
    const g = ctx.createLinearGradient(q[0],q[1],q[2],q[3]); g.addColorStop(0, col); g.addColorStop(1, col + '30');
    ctx.strokeStyle = g; ctx.beginPath(); ctx.moveTo(q[0],q[1]); ctx.lineTo(q[2],q[3]); ctx.stroke();
  }
  ctx.restore();
}
// her drawn box on the screen, with a margin and a smallest size
const LOCK_RING_R = 16;      // v216: the lock ring's radius on the screen
function markBox(o, pad, min){
  let b;
  if(o.kind === 'bomb') b = [o.x - 8, o.y - 8, 16, 16]; else b = eBox(o);
  let x1 = w2sX(b[0]) - pad, y1 = w2sY(b[1]) - pad, x2 = w2sX(b[0]+b[2]) + pad, y2 = w2sY(b[1]+b[3]) + pad;
  if(x2-x1 < min){ const c = (x1+x2)/2; x1 = c - min/2; x2 = c + min/2; }
  if(y2-y1 < min){ const c = (y1+y2)/2; y1 = c - min/2; y2 = c + min/2; }
  return [x1, y1, x2, y2];
}
function markText(t, x, y, col, al, bl){
  ctx.font = thValue(9, true); ctx.textAlign = al; ctx.textBaseline = bl; ctx.lineJoin = 'round';
  ctx.lineWidth = 3; ctx.strokeStyle = MARK_HALO; ctx.strokeText(t, x, y);
  ctx.fillStyle = col; ctx.fillText(t, x, y);
}
// ── MISSION MARKS (v253, Silvio) ─────────────────────────────
// A ship the mission wants something particular done to wears pulsing
// corner brackets in her usual colour (red, green). What to do is spelled
// out underneath - DISABLE, DESTROY, PROTECT - under the same rule as a
// subsystem's name: while she is the target, or while the pointer (or,
// without one, the player's ship) is on her. Set per unit with mark:, and
// changed in a mission with the effect 'markieren' (a2: 'id:word', 'id:'
// takes the mark off).
const MARK_WORDS = {disable:'DISABLE', destroy:'DESTROY', protect:'PROTECT'};
function missionMark(e){
  if(typeof EV_MARK === 'undefined' || !e || e.uid == null) return '';
  return MARK_WORDS[EV_MARK[e.uid]] || '';
}
function drawMissionMark(e){
  const word = missionMark(e); if(!word) return;
  if(e.dead || e.warp > 0 || e.captured) return;
  const img = IMGS[e.img]; if(!img) return;
  const ally = (e.side === 'ally') || allies.indexOf(e) >= 0;
  const col = ally ? OFF_COL.friend : OFF_COL.enemy;
  // On the screen, a little outside the TAG box so both can be seen.
  const hw = img.width*e.sc*0.5*CAM.z + 12, hh = img.height*e.sc*0.5*CAM.z + 12;
  const L = 12, k = 0.45 + 0.55*(0.5 + 0.5*Math.sin(fc*0.15));
  const cx = w2sX(e.x), cy = w2sY(e.y);
  const x0 = cx-hw, x1 = cx+hw, y0 = cy-hh, y1 = cy+hh;
  ctx.save();
  camScreen();
  ctx.globalAlpha = k;
  ctx.strokeStyle = col; ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x0, y0+L); ctx.lineTo(x0, y0); ctx.lineTo(x0+L, y0);
  ctx.moveTo(x1-L, y0); ctx.lineTo(x1, y0); ctx.lineTo(x1, y0+L);
  ctx.moveTo(x1, y1-L); ctx.lineTo(x1, y1); ctx.lineTo(x1-L, y1);
  ctx.moveTo(x0+L, y1); ctx.lineTo(x0, y1); ctx.lineTo(x0, y1-L);
  ctx.stroke();
  ctx.globalAlpha = 1;
  if(GS === 'playing'){
    const scr = (typeof MOUSE !== 'undefined') && MOUSE.scr;
    const rx = scr ? MOUSE.sx : w2sX(player.x), ry = scr ? MOUSE.sy : w2sY(player.y);
    const on = rx >= x0 && rx <= x1 && ry >= y0 && ry <= y1;
    if(TGT.e === e || on){
      // Below the brackets; at the bottom edge it moves up so it is not cut.
      const ty = Math.min(y1 + 4, H - 14);
      markText(word, cx, ty, col, 'center', 'top');
    }
  }
  ctx.restore();
}
function drawTargetMarks(){
  if(GS !== 'playing' || inJump()) return;
  const o = TGT.e; if(!o) return;
  const ally = allies.indexOf(o) >= 0, col = (o.kind === 'bomb') ? OFF_COL.enemy : offColour(o, ally);
  ctx.save();
  const [x1, y1, x2, y2] = markBox(o, TGT_BOX_PAD, TGT_BOX_MIN);
  if(x2 > 0 && x1 < W && y2 > HUD_H && y1 < H){
    fsBrackets(x1, y1, x2, y2, col, 1.6, 1);
    markText(String(Math.round(tgtDist(o)/SIZE_UPM)), x2 + 1, y2 + 3, col, 'right', 'top');   // metres, as in the bar
    // the subsystem: FS's small square brackets (12 px at 1024 or more)
    if(TGT.sub && o.kind !== 'bomb'){
      const p = tgtSubPos(o, TGT.sub), px = w2sX(p.x), py = w2sY(p.y), r = 6;
      const dead = !!TGT.sub.dead;          // FS: grey once destroyed
      fsBrackets(px - r, py - r, px + r, py + r, dead ? '#9a9a9a' : col, 1.3, 1);
      markText(String(TGT.sub.label || '').toUpperCase(), px, py - r - 3, col, 'center', 'bottom');
    }
    // the aspect lock as in FS2: the lock ring travels from the nose to
    // her while it builds, then spins round her, LOCKED under it. In her
    // side colour (Silvio).
    const bank = selSecBank(), w = bank ? secDefP(bank.key) : null;
    if(w && w.homing === 'aspect' && TGT.lock > 0){
      const f = Math.min(1, TGT.lock/(w.lockT || 1)), locked = f >= 1;
      // F90 (Silvio, 23.10.2026): with a subsystem chosen the ring goes to
      // the subsystem, where the lock is taken and the missile flies (v253),
      // not to the middle of the hull
      const lsub = (TGT.sub && !TGT.sub.dead && o.subs && o.kind !== 'bomb') ? tgtSubPos(o, TGT.sub) : null;
      const cx = lsub ? w2sX(lsub.x) : (x1+x2)/2, cy = lsub ? w2sY(lsub.y) : (y1+y2)/2;
      const ns = player.flip ? -1 : 1, na = player.ang || 0;
      const p0x = w2sX(player.x + Math.cos(na)*ns*40), p0y = w2sY(player.y + Math.sin(na)*ns*40);
      const lx = locked ? cx : p0x + (cx - p0x)*f, ly = locked ? cy : p0y + (cy - p0y)*f;
      // v216 (Silvio: huge on a destroyer): FS draws the lock ring at one
      // size whatever the target, so it does here (LOCK_RING_R, screen px)
      const R = LOCK_RING_R, rot = locked ? fc*0.06 : f*5;
      ctx.lineWidth = 3.4; ctx.strokeStyle = MARK_HALO; ctx.beginPath(); ctx.arc(lx, ly, R, 0, Math.PI*2); ctx.stroke();
      ctx.lineWidth = 1.4; ctx.strokeStyle = col; ctx.globalAlpha = locked ? 1 : 0.85;
      ctx.beginPath(); ctx.arc(lx, ly, R, 0, Math.PI*2); ctx.stroke();
      for(let k = 0; k < 3; k++){
        const a = rot + k*Math.PI*2/3, c = Math.cos(a), si = Math.sin(a);
        ctx.beginPath(); ctx.moveTo(lx + c*(R-6), ly + si*(R-6));
        ctx.lineTo(lx + c*(R+3) - si*4, ly + si*(R+3) + c*4); ctx.lineTo(lx + c*(R+3) + si*4, ly + si*(R+3) - c*4); ctx.closePath();
        ctx.strokeStyle = MARK_HALO; ctx.lineWidth = 2; ctx.stroke(); ctx.fillStyle = col; ctx.fill();
      }
      ctx.globalAlpha = 1;
      if(locked) markText('LOCKED', lx, ly + R + 6, col, 'center', 'top');
    }
  }
  // the lead indicator as in FS2: four small triangles pointing in. Only
  // for a ship, within the reach of the primaries now firing, on screen.
  if(o.kind !== 'bomb'){
    const pr = tgtPriReach();
    if(pr.spd > 0 && tgtDist(o) <= pr.reach){
      const L = tgtLead(o, pr.spd);
      if(L){
        const lx = w2sX(L.x), ly = w2sY(L.y), r0 = 3.5, r1 = 8;
        if(lx > 0 && lx < W && ly > HUD_H && ly < H){
          for(const pass of [0, 1]) for(let k = 0; k < 4; k++){
            const a = k*Math.PI/2, c = Math.cos(a), si = Math.sin(a);
            ctx.beginPath(); ctx.moveTo(lx + c*r0, ly + si*r0);
            ctx.lineTo(lx + c*r1 - si*2.6, ly + si*r1 + c*2.6); ctx.lineTo(lx + c*r1 + si*2.6, ly + si*r1 - c*2.6); ctx.closePath();
            if(pass === 0){ ctx.strokeStyle = MARK_HALO; ctx.lineWidth = 2; ctx.stroke(); }
            else { ctx.fillStyle = col; ctx.fill(); }
          }
        }
      }
    }
  }
  ctx.restore();
}

// ── RADAR AND TARGET VIEW IN THE BAR (v210, draft of 10.10.) ──
// One window between SUPPORT and the five buttons: the target's model in
// her real orientation (no flames) under the radar of the whole mission
// area, MediaVP icons tinted in the side colour, the player white; hull
// and shield on the left, the distance on the right.
const RADAR_IMG = {}, RADAR_TINT = {};
function radarImgs(){
  if(radarImgs.done || typeof Image === 'undefined') return;
  radarImgs.done = true;
  for(const k in RADAR_PNG){ const im = new Image(); im.src = 'data:image/png;base64,' + RADAR_PNG[k]; RADAR_IMG[k] = im; }
}
function radarIcon(name, col){
  const k = name + col;
  if(RADAR_TINT[k]) return RADAR_TINT[k];
  const im = RADAR_IMG[name]; if(!im || !im.complete || !im.naturalWidth) return null;
  const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
  const g = c.getContext('2d');
  g.drawImage(im, 0, 0);
  g.globalCompositeOperation = 'multiply'; g.fillStyle = col; g.fillRect(0, 0, c.width, c.height);
  g.globalCompositeOperation = 'destination-in'; g.drawImage(im, 0, 0);
  return (RADAR_TINT[k] = c);
}
function radarIconOf(e){
  if(e.type === 'fighter') return 'radar-fighter';
  if(e.type === 'bomber') return 'radar-bomber';
  return RADAR_MAP[e.img] || RADAR_MAP[(typeof F3D_ALIAS !== 'undefined' && F3D_ALIAS[e.img]) || ''] || 'radar-unknownbig';
}
// an icon at 0.36 of the MediaVP picture, fighters at least 3.5 across
const RADAR_ICO_K = 0.36, RADAR_ICO_MIN = 3.5;
function drawBarRadar(x, y, w, h){
  radarImgs();
  ctx.save();
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  // The WHOLE WORLD, edge to edge - not the mission area. Ships fly in the
  // world, which is wider and taller, and everything out there used to be
  // pushed onto the border where it piled up (Silvio, v232: "Ich will dass
  // das Radar das gesamte Spielfeld beruecksichtigt. Ansonsten brauch ich
  // kein Radar, wenn ich raten muss, an welcher Position sich bestimmte
  // Schiffe befinden"). The clamp below stays as a last resort: a crossing
  // freighter is carried up to 60 units past the edge before she is taken
  // out of the field, and half an icon outside the box is worse than one on
  // its edge for a moment.
  const ax0 = WX0, ax1 = WX1, ay0 = WY0, ay1 = WY1;
  const sx = (w-4)/(ax1-ax0), sy = (h-4)/(ay1-ay0);
  const px = v => x + 2 + (Math.max(ax0, Math.min(ax1, v)) - ax0)*sx;
  const py = v => y + 2 + (Math.max(ay0, Math.min(ay1, v)) - ay0)*sy;
  ctx.imageSmoothingEnabled = true;
  const list = [];
  // F75 (v259): an untouchable super destroyer is scenery for the fight,
  // but she is a ship on the field and the radar shows her (the Lucifer).
  for(const e of enemies) if(!e.dead && e.img && e.type !== 'asteroid' && !(e.warp > 0) && (!e.scenery || e.type === 'boss')) list.push([e, false]);
  for(const e of allies)  if(!e.dead && e.img && !(e.warp > 0)) list.push([e, true]);
  // big ones first, the small craft over them
  const wOf = o => IMGS[o.img] ? IMGS[o.img].width*o.sc : 0;
  list.sort((a, b) => wOf(b[0]) - wOf(a[0]));
  for(const [e, ally] of list){
    const ic = radarIcon(radarIconOf(e), offColour(e, ally)); if(!ic) continue;
    let iw = ic.width*RADAR_ICO_K, ih = ic.height*RADAR_ICO_K;
    if(iw < RADAR_ICO_MIN){ ih *= RADAR_ICO_MIN/iw; iw = RADAR_ICO_MIN; }
    const right = (spriteFacing(e.img) === 'right') !== !!e.flip;
    ctx.save(); ctx.translate(px(e.x), py(e.y)); if(!right) ctx.scale(-1, 1);
    ctx.globalAlpha = (e === TGT.e) ? 1 : 0.85;
    ctx.drawImage(ic, -iw/2, -ih/2, iw, ih);
    ctx.restore();
  }
  // v262 (Silvio, 22.10.2026): what can still be picked up shows on the
  // radar as a small blinking dot in its own colour - green for repair,
  // blue for a life - so at the end of a mission it is plain that
  // something is still out there.
  if(typeof ITEMS !== 'undefined' && ITEMS.length){
    const _bl = 0.55 + 0.45*Math.sin(fc*0.12);   // same beat as the pickup itself
    for(const it of ITEMS){
      ctx.fillStyle = (it.kind === 'repair' ? 'rgba(70,255,140,' : 'rgba(120,235,255,') + _bl.toFixed(2) + ')';
      ctx.beginPath(); ctx.arc(px(it.x), py(it.y), 2.2, 0, Math.PI*2); ctx.fill();
    }
  }
  // the player, in white
  const pic = radarIcon(isBomberHull(player.ship) ? 'radar-bomber' : 'radar-fighter', '#ffffff');
  if(pic){ const s = RADAR_ICO_MIN/pic.width; ctx.save(); ctx.translate(px(player.x), py(player.y)); if(player.flip) ctx.scale(-1, 1);
           ctx.drawImage(pic, -pic.width*s/2, -pic.height*s/2, pic.width*s, pic.height*s); ctx.restore(); }
  ctx.restore();
}
// the target's model, drawn by the field renderer through a camera of its
// own (f3dRender with warm: no flames, no shield hits, no copy to the field)
function barTargetModel(e, x, y, w, h){
  if(typeof f3dReadyLevel !== 'function' || F3D.off) return false;
  const k = f3dKey(e), L = k ? f3dReadyLevel(k) : null; if(!L) return false;
  const img = IMGS[e.img]; if(!img) return false;
  const a = e.ang || 0, lw = img.width*e.sc, lh = img.height*e.sc;
  // v212 (Silvio): one fixed size per ship - fitted to her length, not to
  // her turned outline, which made the picture zoom in and out as she turned
  // her outline seen level (as at a heading of 0) fills the window; turned
  // steeply she may reach past its edge, which the window cuts off
  const kk = Math.max(lw/(w*0.92), lh/(h*0.80));              // world units per bar unit

  const D = kk*H/(2*Math.tan(F3D_FOV/2));
  const M = f3dMat(e, 0, 0, L);
  M[14] = 0;                                                  // her middle on the plane
  const vp0 = f3dVP;
  f3dVP = function(){
    const asp = W/H, f = 1/Math.tan(F3D_FOV/2), near = D*0.2, far = D*3, nf = 1/(near - far);
    const P = [f/asp,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0];
    const o = new Float32Array(P); o[14] = P[14] + P[10]*(-D); o[15] = P[15] + P[11]*(-D);
    return {vp: o, eye: [0, 0, D]};
  };
  try{ f3dRender([{e: e, L: L, x: 0, y: 0, a: 1, clip: null, M: M}], true); }
  catch(er){ F3D.err = String(er && er.message || er); return false; }
  finally{ f3dVP = vp0; }
  const can = F3D.can, fx = can.width/W, fy = can.height/H;
  ctx.drawImage(can, (W/2 - w/2)*fx, (H/2 - h/2)*fy, w*fx, h*fy, x, y, w, h);
  return true;
}
// ── SUBSYSTEM ICONS IN THE TARGET VIEW (F89, Silvio 23.10.2026) ──
// The five subsystems of the target, in the right margin of the target view
// (not in the radar box). Coloured like the HULL bar, red and struck through
// once destroyed. Weapons, sensors, navigation and communication are
// Material Symbols, outlined (Apache-2.0, see licenses/README.md); the
// engines are a bell nozzle lying on its side, drawn by hand in the same
// line style (tools/f89_subsystem_icons_mock.js).
const SUB_ICON_D = {
  weapons: 'M450-42v-75q-137-14-228-105T117-450H42v-60h75q14-137 105-228t228-105v-75h60v75q137 14 228 105t105 228h75v60h-75q-14 137-105 228T510-117v75h-60Zm244.5-223.5Q784-355 784-480t-89.5-214.5Q605-784 480-784t-214.5 89.5Q176-605 176-480t89.5 214.5Q355-176 480-176t214.5-89.5Zm-321-108Q330-417 330-480t43.5-106.5Q417-630 480-630t106.5 43.5Q630-543 630-480t-43.5 106.5Q543-330 480-330t-106.5-43.5ZM544-416q26-26 26-64t-26-64q-26-26-64-26t-64 26q-26 26-26 64t26 64q26 26 64 26t64-26Zm-64-64Z',
  sensors: 'M324-111.5Q251-143 197-197t-85.5-127Q80-397 80-480t31.5-156Q143-709 197-763t127-85.5Q397-880 480-880t156 31.5Q709-817 763-763t85.5 127Q880-563 880-480t-31.5 156Q817-251 763-197t-127 85.5Q563-80 480-80t-156-31.5ZM480-140q63 0 118.5-20.5T699-219l-72-71q-31 23-68 36.5T480-240q-100 0-170-70t-70-170q0-100 70-170t170-70q100 0 170 70t70 170q0 42-13.5 79T670-333l71 71q37-45 58-100t21-118q0-142-99-241t-241-99q-142 0-241 99t-99 241q0 142 99 241t241 99Zm0-160q29 0 55.5-8.5T584-333l-74-73q-7 3-14.5 4.5T480-400q-33 0-56.5-23.5T400-480q0-33 23.5-56.5T480-560q33 0 56.5 23.5T560-480q0 8-2 16t-5 16l74 72q16-22 24.5-48.5T660-480q0-75-52.5-127.5T480-660q-75 0-127.5 52.5T300-480q0 75 52.5 127.5T480-300Z',
  navigation: 'm303-303 270-83 83-270-270 83-83 270Zm176.76-137q-16.76 0-28.26-11.74-11.5-11.73-11.5-28.5 0-16.76 11.74-28.26 11.73-11.5 28.5-11.5 16.76 0 28.26 11.74 11.5 11.73 11.5 28.5 0 16.76-11.74 28.26-11.73 11.5-28.5 11.5Zm.51 360q-82.74 0-155.5-31.5Q252-143 197.5-197.5t-86-127.34Q80-397.68 80-480.5t31.5-155.66Q143-709 197.5-763t127.34-85.5Q397.68-880 480.5-880t155.66 31.5Q709-817 763-763t85.5 127Q880-563 880-480.27q0 82.74-31.5 155.5Q817-252 763-197.68q-54 54.31-127 86Q563-80 480.27-80Zm.22-60Q622-140 721-239.49q99-99.48 99-241Q820-622 721-721t-240.51-99q-141.52 0-241 99Q140-622 140-480.49q0 141.52 99.49 241 99.48 99.49 241 99.49ZM480-480Z',
  communication: 'M198-278q-60-58-89-133T80-560q0-74 29-149t89-133l35 35q-50 49-76.5 116.5T130-560q0 63 26.5 130.5T233-313l-35 35Zm92-92q-40-37-59-89.5T212-560q0-48 19-100.5t59-89.5l35 35q-29 29-46 72.5T262-560q0 35 17.5 79.5T325-405l-35 35Zm4 290 133-405q-17-12-27.5-31T389-560q0-38 26.5-64.5T480-651q38 0 64.5 26.5T571-560q0 25-10.5 44T533-485L666-80h-59l-29-90H383l-30 90h-59Zm108-150h156l-78-238-78 238Zm268-140-35-35q29-29 46-72.5t17-82.5q0-35-17.5-79.5T635-715l35-35q39 37 58.5 89.5T748-560q0 47-19.5 100T670-370Zm92 92-35-35q49-49 76-116.5T830-560q0-63-27-130.5T727-807l35-35q60 58 89 133t29 149q0 75-27.5 149.5T762-278Z',
};
const SUB_ICON_P = {};
function subIconPath(id){
  if(!SUB_ICON_D[id] || typeof Path2D === 'undefined') return null;
  return SUB_ICON_P[id] || (SUB_ICON_P[id] = new Path2D(SUB_ICON_D[id]));
}
const SUB_ICON_ORDER = ['weapons','engines','sensors','navigation','communication'];
const SUB_DEAD_COL = '#ff4a33';
function drawEngineGlyph(cx, cy, sz, col){
  const k = sz/24;
  ctx.save(); ctx.translate(cx - sz/2, cy - sz/2); ctx.scale(k, k);
  ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  // chamber on the right, a narrow throat, the bell flaring to the left
  ctx.beginPath(); ctx.moveTo(18, 9); ctx.lineTo(21.5, 9); ctx.lineTo(21.5, 15); ctx.lineTo(18, 15); ctx.closePath(); ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(18, 10.5); ctx.lineTo(15.5, 11);
  ctx.quadraticCurveTo(11, 5, 2.5, 3.5);
  ctx.lineTo(2.5, 20.5);
  ctx.quadraticCurveTo(11, 19, 15.5, 13);
  ctx.lineTo(18, 13.5); ctx.stroke();
  // two rings on the bell
  ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(11.5, 7.6); ctx.lineTo(11.5, 16.4); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(7, 5.2); ctx.lineTo(7, 18.8); ctx.stroke();
  ctx.restore();
}
function drawSubIcon(id, cx, cy, sz, col){
  if(id === 'engines'){ drawEngineGlyph(cx, cy, sz, col); return; }
  const P = subIconPath(id); if(!P) return;
  ctx.save(); ctx.translate(cx - sz/2, cy - sz/2); ctx.scale(sz/960, sz/960); ctx.translate(0, 960);
  ctx.fillStyle = col; ctx.fill(P); ctx.restore();
}
// the icons of e's subsystems in the box x, y, w, h: three on top, two under
function drawBarSubIcons(e, x, y, w, h){
  window._barSubIcons = [];
  if(!e || e.kind === 'bomb' || !e.subs || !e.subs.length || w < 12) return;
  const cols = 3, cell = Math.min(w/cols, h/2), sz = cell*0.86;
  let i = 0;
  for(const id of SUB_ICON_ORDER){
    const s = e.subs.find(function(q){ return q.id === id; });
    const cx = x + (i%cols + 0.5)*(w/cols), cy = y + (Math.floor(i/cols) + 0.5)*cell;
    i++; if(!s) continue;
    const dead = !!s.dead || !(s.hp > 0);
    const col = dead ? SUB_DEAD_COL : hullCol(Math.max(0, s.hp/s.maxHp));
    ctx.save(); ctx.globalAlpha = dead ? 0.55 : 1; drawSubIcon(id, cx, cy, sz, col); ctx.restore();
    if(dead){
      ctx.save(); ctx.strokeStyle = SUB_DEAD_COL; ctx.lineWidth = Math.max(1.5, sz*0.1); ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(cx - sz*0.45, cy + sz*0.45); ctx.lineTo(cx + sz*0.45, cy - sz*0.45); ctx.stroke(); ctx.restore();
    }
    window._barSubIcons.push({id: id, x: cx, y: cy, sz: sz, col: col, dead: dead});
  }
}
// called at the end of drawHUDHLP with the first free x after the ship and
// weapon buttons; x1 is where the system buttons (sound, settings, pause)
// begin (F89: the target view is wider by the two buttons that moved)
function drawBarScope(x0, x1){
  const H2 = HUD_H, bX0 = (x1 != null) ? x1 : W - 3*22 - 2*3 - 4;
  const x = x0 + 5, y = 5, w = bX0 - 6 - x, h = H2 - 10;
  thDivider(x0, 4, H2 - 4);
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(x, y, w, h);
  ctx.beginPath(); ctx.rect(x+1, y+1, w-2, h-2); ctx.clip();
  const e = TGT.e;
  const ship = e && e.kind !== 'bomb';
  // 1  the target's model, in her real orientation, under everything
  if(ship){ ctx.globalAlpha = 0.75; barTargetModel(e, x, y, w, h); ctx.globalAlpha = 1; }
  // 2  the radar: the whole world, kept in proportion, centred
  const rw = Math.round(h*(WX1 - WX0)/Math.max(1, WY1 - WY0));
  ctx.strokeStyle = 'rgba(255,255,255,0.10)'; ctx.lineWidth = 1;
  ctx.strokeRect(x + (w - rw)/2 + 0.5, y + 0.5, rw - 1, h - 1);
  drawBarRadar(x + (w - rw)/2, y, rw, h);
  // 3  the target's values: hull and shield in the left margin (share
  //    over its bar), the distance in the right margin
  if(e){
    const col = ship ? offColour(e, allies.indexOf(e) >= 0) : OFF_COL.enemy, mg = (w - rw)/2;
    const rows = [];
    if(ship){
      const hR = Math.max(0, e.hp/e.maxHp), sR = e.maxSh ? Math.max(0, e.sh/e.maxSh) : -1;
      rows.push([hR, hullCol(hR), 'HULL']);
      if(sR >= 0) rows.push([sR, sR > .5 ? '#0099ff' : '#0055cc', 'SHIELD']);
    }
    const bx = x + 3, bwid = mg - 6;
    for(let i = 0; i < rows.length; i++){
      const [r, c, t] = rows[i], ry = y + 5 + i*19;
      ctx.textBaseline = 'middle';
      ctx.fillStyle = TH('textDim'); ctx.font = thLabel(5.5); ctx.textAlign = 'left'; ctx.fillText(t, bx, ry);
      ctx.fillStyle = TH('text'); ctx.font = thValue(7, true); ctx.textAlign = 'right'; ctx.fillText(Math.round(r*100) + '%', bx + bwid, ry + 6);
      ctx.fillStyle = TH('edgeDark'); ctx.fillRect(bx, ry + 11, bwid, 3);
      ctx.fillStyle = c; ctx.fillRect(bx, ry + 11, bwid*r, 3);
    }
    if(!ship){ ctx.fillStyle = col; ctx.font = thLabel(7); ctx.textAlign = 'left'; ctx.textBaseline = 'top'; ctx.fillText('BOMB', bx, y + 3); }
    ctx.font = thValue(8, true); ctx.textBaseline = 'top'; ctx.textAlign = 'right'; ctx.fillStyle = col;
    ctx.fillText(Math.round(tgtDist(e)/SIZE_UPM) + 'm', x + w - 3, y + 3);
    // F89: the subsystems in the right margin, under the distance
    if(ship) drawBarSubIcons(e, x + w - mg + 3, y + 16, mg - 6, h - 16);
  } else {
    ctx.fillStyle = TH('textDim'); ctx.font = thLabel(7); ctx.textAlign = 'left'; ctx.textBaseline = 'top';
    ctx.fillText('NO TARGET', x + 3, y + 3);
  }
  ctx.restore();
  thBevel(x, y, w, h);
}
