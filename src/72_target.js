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
const TGT_BRACKET_MIN = 14;    // screen px, the smallest bracket box
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
function tgtHostile(o){ return enemies.indexOf(o) >= 0 && !playerOnly(o); }
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
  if(TGT.lockOf !== key){ TGT.lock = 0; TGT.lockOf = key; }
  if(w && w.homing === 'aspect' && o && o.kind !== 'bomb' && enemies.indexOf(o) >= 0 && canLockOn(o)
     && bank.ammo > 0 && tgtDist(o) <= w.spd*w.life && tgtOff(o.x, o.y) <= TGT_LOCK_CONE){
    TGT.lock = Math.min(TGT.lock + 1, w.lockT || 1);
  } else TGT.lock = 0;
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
function drawTargetMarks(){
  if(GS !== 'playing' || inJump()) return;
  const o = TGT.e; if(!o) return;
  const ally = allies.indexOf(o) >= 0, col = (o.kind === 'bomb') ? OFF_COL.enemy : offColour(o, ally);
  ctx.save();
  ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 1.4; ctx.lineJoin = 'round';
  // her box as drawn: the hit box of v210 (eBox) on the screen
  let bx, by, bw, bh;
  if(o.kind === 'bomb'){ bx = o.x - 8; by = o.y - 8; bw = 16; bh = 16; }
  else { const b = eBox(o); bx = b[0]; by = b[1]; bw = b[2]; bh = b[3]; }
  let sx = w2sX(bx), sy = w2sY(by), sw = bw*CAM.z, sh = bh*CAM.z;
  if(sw < TGT_BRACKET_MIN){ sx -= (TGT_BRACKET_MIN - sw)/2; sw = TGT_BRACKET_MIN; }
  if(sh < TGT_BRACKET_MIN){ sy -= (TGT_BRACKET_MIN - sh)/2; sh = TGT_BRACKET_MIN; }
  sx -= 3; sy -= 3; sw += 6; sh += 6;
  if(sx + sw > 0 && sx < W && sy + sh > HUD_H && sy < H){
    const L = Math.max(4, Math.min(14, Math.min(sw, sh)*0.25));
    ctx.beginPath();
    ctx.moveTo(sx, sy + L); ctx.lineTo(sx, sy); ctx.lineTo(sx + L, sy);
    ctx.moveTo(sx + sw - L, sy); ctx.lineTo(sx + sw, sy); ctx.lineTo(sx + sw, sy + L);
    ctx.moveTo(sx + sw, sy + sh - L); ctx.lineTo(sx + sw, sy + sh); ctx.lineTo(sx + sw - L, sy + sh);
    ctx.moveTo(sx + L, sy + sh); ctx.lineTo(sx, sy + sh); ctx.lineTo(sx, sy + sh - L);
    ctx.stroke();
    // the subsystem: a small box of its own
    if(TGT.sub && o.kind !== 'bomb'){
      const p = tgtSubPos(o, TGT.sub), px = w2sX(p.x), py = w2sY(p.y), r = 6;
      ctx.strokeRect(px - r, py - r, r*2, r*2);
      ctx.font = thLabel(8); ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
      ctx.fillText(String(TGT.sub.label || '').toUpperCase(), px, py - r - 2);
    }
    // the lock: a diamond closing in on her while it builds, solid when held
    const bank = selSecBank(), w = bank ? secDefP(bank.key) : null;
    if(w && w.homing === 'aspect' && TGT.lock > 0){
      const f = Math.min(1, TGT.lock/(w.lockT || 1)), locked = f >= 1;
      const cx = sx + sw/2, cy = sy + sh/2, r = Math.max(sw, sh)*0.5*(1 + (1 - f)*1.5) + 4;
      ctx.save();
      ctx.strokeStyle = locked ? '#ffe040' : col; ctx.globalAlpha = locked ? 1 : 0.7;
      if(!locked) ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(cx, cy - r); ctx.lineTo(cx + r, cy); ctx.lineTo(cx, cy + r); ctx.lineTo(cx - r, cy); ctx.closePath(); ctx.stroke();
      if(locked){ ctx.fillStyle = '#ffe040'; ctx.font = thLabel(8); ctx.textAlign = 'center'; ctx.textBaseline = 'top'; ctx.fillText('LOCK', cx, cy + r + 2); }
      ctx.restore();
    }
  }
  // the lead indicator: only for a ship, within the reach of the primaries
  // now firing, and only where it is on the screen
  if(o.kind !== 'bomb'){
    const pr = tgtPriReach();
    if(pr.spd > 0 && tgtDist(o) <= pr.reach){
      const L = tgtLead(o, pr.spd);
      if(L){
        const lx = w2sX(L.x), ly = w2sY(L.y);
        if(lx > 0 && lx < W && ly > HUD_H && ly < H){
          ctx.lineWidth = 1.2; ctx.globalAlpha = 0.9;
          ctx.beginPath(); ctx.arc(lx, ly, 5, 0, Math.PI*2); ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(lx - 9, ly); ctx.lineTo(lx - 6, ly); ctx.moveTo(lx + 6, ly); ctx.lineTo(lx + 9, ly);
          ctx.moveTo(lx, ly - 9); ctx.lineTo(lx, ly - 6); ctx.moveTo(lx, ly + 6); ctx.lineTo(lx, ly + 9);
          ctx.stroke();
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
  // the mission area, edge to edge; ships outside it sit on the edge
  const ax0 = 0, ax1 = MW, ay0 = HUD_H, ay1 = MH;
  const sx = (w-4)/(ax1-ax0), sy = (h-4)/(ay1-ay0);
  const px = v => x + 2 + (Math.max(ax0, Math.min(ax1, v)) - ax0)*sx;
  const py = v => y + 2 + (Math.max(ay0, Math.min(ay1, v)) - ay0)*sy;
  ctx.imageSmoothingEnabled = true;
  const list = [];
  for(const e of enemies) if(!e.dead && e.img && e.type !== 'asteroid' && !(e.warp > 0) && !e.scenery) list.push([e, false]);
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
  const bw = lw*Math.abs(Math.cos(a)) + lh*Math.abs(Math.sin(a)), bh = lw*Math.abs(Math.sin(a)) + lh*Math.abs(Math.cos(a));
  const kk = Math.max(bw/(w*0.92), bh/(h*0.80));             // world units per bar unit
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
// called at the end of drawHUDHLP with the first free x after SUPPORT
function drawBarScope(x0){
  const H2 = HUD_H, bX0 = W - 5*22 - 4*3 - 4;
  const x = x0 + 5, y = 5, w = bX0 - 6 - x, h = H2 - 10;
  thDivider(x0, 4, H2 - 4);
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(x, y, w, h);
  ctx.beginPath(); ctx.rect(x+1, y+1, w-2, h-2); ctx.clip();
  const e = TGT.e;
  const ship = e && e.kind !== 'bomb';
  // 1  the target's model, in her real orientation, under everything
  if(ship){ ctx.globalAlpha = 0.75; barTargetModel(e, x, y, w, h); ctx.globalAlpha = 1; }
  // 2  the radar: the whole mission area, kept in proportion, centred
  const rw = Math.round(h*MW/(MH - HUD_H));
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
  } else {
    ctx.fillStyle = TH('textDim'); ctx.font = thLabel(7); ctx.textAlign = 'left'; ctx.textBaseline = 'top';
    ctx.fillText('NO TARGET', x + 3, y + 3);
  }
  ctx.restore();
  thBevel(x, y, w, h);
}
