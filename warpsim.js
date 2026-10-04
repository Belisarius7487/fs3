// warpsim.js - watches every jump in and out of every written mission with
// the FreeSpace style warp (?warp=oval) and reports what would look wrong.
//
//   node warpsim.js hlp_shooter_vNNN_logic.html [mounts.json] [missions]
//   missions: e.g. "1-60" (default) or "52" or "50-55"
//
// Checked, tick by tick, for every ship that jumps:
//   pop      part of the hull shows up (or vanishes) at once instead of
//            sliding out of (into) the vortex
//   stop     the ship's speed jumps or it moves backwards during the jump
//   close    a vortex closes while the hull still sticks in it on screen
//   plane    the edge that cuts the hull is not where the vortex is drawn
// Exit code 1 if anything was found.
const fs = require('fs'), path = require('path'), os = require('os');
const {execSync} = require('child_process');
const {chromium} = require(path.join(execSync('npm root -g').toString().trim(), 'playwright'));

const logic = process.argv[2];
const mounts = process.argv[3] || 'hlp_mounts_final.json';
const range = (process.argv[4] || '1-60').split('-').map(Number);
const M0 = range[0], M1 = range[1] || range[0];

// A 1x1 picture stands in for the vortex and glow sheets: the vortex is
// only drawn once its picture has loaded, and the real ones are not in git.
const DOT = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';
let html = fs.readFileSync(logic, 'utf8');
for(const n of ['warp_img', 'warp_knossos', 'warp_glow', 'warp_glow_knossos'])
  html = html.split('@@FS3_ASSET:images/' + n + '.webp@@').join(DOT);
html = html.replace(/<script([^>]*)>/, '<script$1>\nconst MOUNTS=' +
  JSON.stringify(JSON.parse(fs.readFileSync(mounts, 'utf8'))) + ';\n');
const tmp = path.join(os.tmpdir(), 'warpsim_' + process.pid + '.html');
fs.writeFileSync(tmp, html);

// Runs inside the page, one mission.
const BODY = `
  if(typeof fsNose !== 'function') window.fsNose = e => { const s = (e.flip?-1:1)*(spriteFacing(e.img)==='left'?-1:1), a = e.ang||0; return {x:Math.cos(a)*s, y:Math.sin(a)*s}; };
  for(const k of Object.keys(HULL_LEN)){
    const small = /^(fi|bo|sg|fc|ep)/.test(k) && HULL_LEN[k] < 80;
    const c = document.createElement('canvas');
    c.width = small ? 60 : 320; c.height = small ? 40 : 90;
    IMGS[k] = c;
  }
  imgsLoaded = TOTAL; nebsLoaded = 0;
  launchGame();
  const startWave = wave;
  const T = new Map();          // ship -> track
  const found = [];
  function note(kind, e, txt){
    const id = e.img + (e.uid ? '/' + e.uid : '');
    if(found.some(f => f.kind===kind && f.id===id)) return;
    found.push({kind, id, wave, txt});
  }
  // Hull along the nose: centre, length, and what of it can be seen.
  function look(e){
    const img = IMGS[e.img]; if(!img) return null;
    const L = img.width*e.sc;
    const g = fsWarp(e);
    let p = null;                       // cutting plane, if any
    if(g){ if(!g.vis) return {vis:0, g, L, cx:null}; p = {px:g.px, py:g.py, fx:g.fx, fy:g.fy, keepFront:!g.out}; }
    else if(typeof fsPostClip === 'function'){ const q = fsPostClip(e); if(q) p = q; }
    const f = g ? {x:g.fx, y:g.fy} : fsNose(e);
    const cx = e.x + (g ? g.dx : 0), cy = e.y + (g ? g.dy : 0);
    // Hull as a segment along the nose, parameter s from -L/2 to L/2.
    let a = -L/2, b = L/2;
    if(p){
      const d0 = (cx-p.px)*p.fx + (cy-p.py)*p.fy;      // centre past the plane
      if(p.keepFront) a = Math.max(a, -d0); else b = Math.min(b, -d0);
    }
    // On screen: x between 0 and W.
    if(Math.abs(f.x) > 1e-6){
      const s0 = (0 - cx)/f.x, s1 = (W - cx)/f.x;
      a = Math.max(a, Math.min(s0, s1)); b = Math.min(b, Math.max(s0, s1));
    }
    return {vis: Math.max(0, b-a), g, L, cx, cy, f, p};
  }
  const MAXT = 40000;
  let t = 0, done = -1;
  while(t < MAXT){
    player.hp = player.maxHp; player.sh = player.maxSh; lives = 3;
    if(t % 200 === 0){
      for(const e of enemies){
        if(e.warp>0 || e.invuln || e.scenery) continue;
        if(e.captureLock){ for(const s of (e.subs||[])) if(s.id==='engines'||s.id==='weapons'||s.id==='navigation'){ s.dead=true; s.hp=0; } continue; }
        if(e.scanSubs && !e.scanned){ for(const s of e.subs) s.scanT = 1e9; continue; }
        if(e.scanLock && !e.scanned){ e.scanned = true; continue; }
        // Big ships get time to be seen before they go.
        if(!e.small && e.type!=='fighter' && e.type!=='bomber' && e._age == null) e._age = t;
        if(e._age != null && t - e._age < 1500) continue;
        e.hp = 0;
      }
      ITEMS.length = 0;
    }
    update(); draw(); t++;
    for(const e of enemies.concat(allies)){
      if(e.type==='asteroid') continue;   // portal jumps too, since v161
      const inJump = e.warp>0 || e.warpOut>0;
      let tr = T.get(e);
      if(!tr){ if(!inJump) continue; tr = {prev:null}; T.set(e, tr); }
      const now = look(e); if(!now) continue;
      const pr = tr.prev; tr.prev = now;
      if(!pr) continue;
      // Speed of the picture along the nose.
      let v = null;
      if(now.cx!=null && pr.cx!=null && now.f) v = (now.cx-pr.cx)*now.f.x + (now.cy-pr.cy)*now.f.y;
      const vPrev = tr.v; tr.v = v;
      // The tick a hull vanishes has no speed of its own: the last one counts.
      const move = Math.abs(v!=null ? v : (vPrev||0)) + 1.5;
      // pop: more hull turns visible (or invisible) than the motion explains.
      // The first visible tick of a jump in is the nose coming through.
      const dvis = now.vis - pr.vis;
      if(Math.abs(dvis) > move + 2 && !(pr.vis===0 && e.warp>0))
        note('pop', e, (dvis>0?'+':'')+dvis.toFixed(0)+'px of hull at once (' + pr.vis.toFixed(0) + ' -> ' + now.vis.toFixed(0) + ', speed ' + (v==null?'-':v.toFixed(2)) + ')' +
             (e.warp>0?' (jump in)':(e.warpOut>0?' (jump out)':' (after jump in)')));
      // stop: a jump in speed, or backwards during a jump.
      // Fighters turn and speed up on their own right away; for them a
      // little more is let through, and after the jump their flight model
      // takes over at once, so only the jump itself is checked.
      if(v!=null && vPrev!=null && Math.abs(v - vPrev) > (fsSmall(e) ? 0.6 : 0.35) &&
         (inJump || (tr.wasJump && !fsSmall(e))))
        note('stop', e, 'speed ' + vPrev.toFixed(2) + ' -> ' + v.toFixed(2) + ' px/tick' + (e.warp>0?' (jump in)':(e.warpOut>0?' (jump out)':' (after jump)')));
      if(v!=null && v < -0.05 && inJump) note('stop', e, 'backwards ' + v.toFixed(2) + ' px/tick');
      // plane: the cut and the drawn vortex have to agree.
      if(e.warp>0 && now.g && now.g.vis && e._fsp &&
         Math.hypot(now.g.px - e._fsp.px, now.g.py - e._fsp.py) > 2)
        note('plane', e, 'cut ' + Math.hypot(now.g.px-e._fsp.px, now.g.py-e._fsp.py).toFixed(0) + 'px from the vortex');
      // The hand-over: the few ticks after a jump. Later changes of speed
      // are the ship's own (arriving at its station, turning).
      tr.wasJump = inJump || (tr.wasJump && ++tr.after < 3);
      if(inJump) tr.after = 0;
    }
    // close: a closing vortex with a hull still across it, on screen.
    for(const p of FS_PORTALS){
      if(p.closeT < 0 || p.px < 0 || p.px > W) continue;
      // On the screen edge, what is behind the vortex is off the screen. A
      // ship that stays there half out is no fault; one still coming out is.
      if((p.px <= 0 || p.px >= W) && !fsPortalMoving(p)) continue;
      const e = p.e; if(enemies.indexOf(e)<0 && allies.indexOf(e)<0) continue;
      const img = IMGS[e.img]; if(!img) continue;
      const L = img.width*e.sc, g = e.warp>0 ? fsWarp(e) : null;
      const cx = e.x + (g?g.dx:0), cy = e.y + (g?g.dy:0);
      const d0 = (cx-p.px)*p.fx + (cy-p.py)*p.fy;
      if(d0 - L/2 < -1 && d0 + L/2 > 1) note('close', e, 'vortex closes on ' + (-(d0-L/2)).toFixed(0) + 'px of hull');
    }
    if(done < 0 && wave > startWave) done = t;
    if(done >= 0 && t - done > 200) break;
  }
  return {found, ticks: t, ended: done >= 0, jumps: T.size};
`;

(async()=>{
  const browser = await chromium.launch();
  let bad = 0;
  for(let m=M0; m<=M1; m++){
    const page = await browser.newPage();
    const errs = [];
    page.on('pageerror', e=>errs.push(String(e.message||e)));
    await page.goto('file://' + tmp + '?m=' + m + '&warp=oval&practice=1');
    await page.waitForTimeout(300);
    let r = null;
    try{ r = await page.evaluate('(function(){' + BODY + '})()'); }
    catch(e){ errs.push(String(e.message||e)); }
    const head = 'M' + String(m).padStart(2,'0');
    if(r){
      console.log(head + '  ' + r.jumps + ' ships jumped' + (r.ended ? '' : '  (wave did not end)') +
                  (r.found.length ? '' : '  ok'));
      for(const f of r.found) console.log('   ' + f.kind.padEnd(6) + f.id.padEnd(22) + f.txt);
      bad += r.found.length;
    }
    if(errs.length){ bad++; console.log(head + '  page errors: ' + errs.slice(0,3).join(' | ')); }
    await page.close();
  }
  await browser.close();
  fs.unlinkSync(tmp);
  console.log(bad ? '\n' + bad + ' findings' : '\nall clean');
  process.exit(bad ? 1 : 0);
})();
