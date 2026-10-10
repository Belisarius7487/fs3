// Weapon simulation. Pulls the REAL firing routines out of the logic file and
// runs them against stand-ins for the world.
//
// What it is for: several of the weapons do something rather than merely
// weigh something - a cone, a round that bursts, a warhead that goes for the
// innards, a salvo that splits over several targets. Numbers can be read off the table;
// behaviour cannot.
//
// Usage: node wpnsim.js <logic.html>
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const src = html.match(/<script[^>]*>([\s\S]*)<\/script>/)[1];

function blockEnd(s, i){
  let j = s.indexOf('{', i), depth = 0;
  for(; j < s.length; j++){
    const c = s[j];
    if(c === '{') depth++;
    else if(c === '}'){ depth--; if(!depth) return j + 1; }
    else if(c === "'" || c === '"' || c === '`'){ const q = c; j++; while(j < s.length && s[j] !== q) j += (s[j] === '\\') ? 2 : 1; }
    else if(s.startsWith('//', j)) j = s.indexOf('\n', j);
    else if(s.startsWith('/*', j)) j = s.indexOf('*/', j) + 1;
  }
  throw new Error('unbalanced');
}
function fn(name){
  const i = src.indexOf('\nfunction ' + name + '(');
  if(i < 0) throw new Error('missing function ' + name);
  return src.slice(i + 1, blockEnd(src, i));
}
function decl(re){
  const m = src.match(re);
  if(!m) throw new Error('missing declaration ' + re);
  return m[0];
}

const names = ['priDef','secDef','curPri','curSec','hullSecCls','weaponName','weaponOpen','waveReached',
               'applyLoadout','rearmFull','aspectTarget','pShootWith',
               'shardBurst','subStrike','subStrikeRaw','pShoot','fireSecondary',
               'liveBurstRound','burstRound','volleyDmg','volleyTotal','primaryCount',
               'flakHas','flakBurst','flakReach','flakFire',
               'swarmTargets','swarmRetarget','swarmHolds','updateSecBullets',
               'secHoldTick','shardSpread',
               // v210: the player's target, the aspect lock, the heat cone
               'tgtLocked','heatSees','heatAcquire','tgtDrawn','tgtSubPos','tgtSet'];
const consts = [
  decl(/const PLAYER_FR_BASE[\s\S]*?\n\];/),
  // v186: the FS2 arsenal and the banks, the AI's old tables.
  (function(){
    const a = src.indexOf('// ── WEAPON BANKS (v186)');
    const b = src.indexOf('\nfunction empBurst(');
    return src.slice(a, blockEnd(src, b+1)) + '\n' + decl(/const AI_SECONDARIES = \[[\s\S]*?\n\];/)
         + '\n' + decl(/const AI_PRIMARIES = \{[\s\S]*?\n\};/) + '\nconst SECONDARIES = ARSENAL_S;\n'
         + decl(/const CLUSTER_CHILD = \{[^}]*\};/);
  })(),
  decl(/const SUB_WARHEAD_MUL = [^;]*;/),
  decl(/const VOLLEY_BASE\s*=\s*[\d.]+;/),
  decl(/const VOLLEY_PER_EXTRA\s*=\s*[\d.]+;/),
  decl(/const FLAK_TYPES[\s\S]*?const FLAK_SHARD_RANGE = \d+;/),
  decl(/let swarmSalvo = 0;/),
  decl(/const SEC_HOLD = \{[^}]*\};/),
  decl(/const HULL_TRAITS = \{[\s\S]*?\n\};/),
  decl(/const TGT = \{[^}]*\};/)
];

const WORLD = `
const W = 800, H = 500, HUD_H = 54;
const MW=W, MH=H, FIELD_K=1, TEMPO_K=1, CAM_BASE_Z=1, WX0=0, WX1=W, WY0=54, WY1=H, SIZE_UPM=3.75, FIELD_CX=W/2, FIELD_CY=(54+H)/2; const CAM={x:W/2, y:(54+H)/2, z:1, zt:1, over:false}; function camSees(){ return true; } function hullPt(e, x, y){ return {x: x, y: y}; } function hullUnPt(e, x, y){ return {x: x, y: y}; } function fxG(){ return 1; } function camHalfW(){ return W/2; } function camHalfH(){ return (H-54)/2; } function w2sX(x){ return x; } function w2sY(y){ return y; } function s2wX(x){ return x; } function s2wY(y){ return y; } function camFollow(){} function camSnap(){} function mouseTick(){} function worldSet(){} function worldForWave(){} function mouseAt(p){ if(typeof MOUSE!=="undefined"){ MOUSE.x=p.x; MOUSE.y=p.y; } } function mouseHold(){ if(typeof MOUSE!=='undefined' && typeof player!=='undefined'){ MOUSE.x=player.x; MOUSE.y=player.y; } }  // v208: the world is the old field in the sims; v209: tempo and zoom 1
var pBullets = [], eBullets = [], PARTS = [], SUB_MSGS = [], enemies = [], allies = [];
var fc = 0, score = 0, FS1_MODE = false, UI_WEAPONS = false;
const UI_TICKETS = false;
const STATS = {shots:0, hits:0, subsKilled:0};
var player = {x:100, y:250, head:0, ang:0, flip:false, ship:'fitoth',
              fR:28, secAmmo:20, secMax:20, secTimer:0, secType:'missile',
              pri:'promr', sec:'harpoon'};
function notice(){}
// Mounts are the hull's business, not the weapon's. Two barrels, fixed, so a
// change in the volley can only come from the gun.
function mountList(){ return [{x:120, y:246}, {x:120, y:254}]; }
function playerSc(){ return 1; }
function isBomberHull(k){ return k.indexOf('bo')===0; }
function shipFac(k){ return 'vasudan'; }
function shipStats(k){ return {sec: isBomberHull(k) ? 10 : 20}; }
function spawnFireball(){} 
// The practice log is not what is tested here.
function sndPlay(){} function sndStart(){} function sndAiShot(){} function sndAiSec(){} function sndExpl(){} function sndBeam(){} const PRI_SND = {};
function plogKill(){} function plogRearm(){} function plogSec(){} function plogHit(){} function plogPick(){} function plogSrc(){} function plogLoss(){} function plogEvent(){} function plogName(){ return ''; } function plogAllyLost(){} function plogDeath(){} function plogSync(){}
function spawnDebris(){}
function spawnRing(){}
function spawnSmoke(){}
function secMount(){ return {x:player.x+20, y:player.y}; }
// Capitals: one mount, a fixed target, so what is under test is where the
// wall ends up and not how a turret picks a ship.
var FLAK_TARGET = null;
function entMounts(e){ return [{x:e.x, y:e.y}]; }
function nearestEnemy(){ return FLAK_TARGET; }
function capGunTarget(){ return FLAK_TARGET; }
function subOK(){ return true; }
function rndR(r){ return (r[0]+r[1])/2; }
// Locking and impact. LOCK_OK stands for the nebula and the EMP storm: off,
// nothing can be held. Every ship is a 30 point square, and a hit is
// written down per ship so the test can ask who was struck.
var LOCK_OK = true, HITS = [];
function canLockOn(o){ return LOCK_OK && !!o; }
function isLargeShip(o){ return o.type==='cruiser' || o.type==='corvette' || o.type==='destroyer'; }
function eBox(e){ return [e.x-15, e.y-15, 30, 30]; }
function overlap(ax,ay,aw,ah,bx,by,bw,bh){ return ax<bx+bw && ax+aw>bx && ay<by+bh && ay+ah>by; }
function bulletOnHull(){ return true; }
function playerOnly(){ return false; }
function damageEnemy(e, d){ e.hp -= d; HITS.push({e:e, d:d}); }
function killEnemy(e, j){ e.dead = true; enemies.splice(j, 1); }
// Subsystems: subHit is the real one, the geometry around it is not what is
// under test here.
function subPos(e, s){ return {x:e.x+s.ox, y:e.y}; }
function subAt(e, hx, hy){
  let best=null, bd=Infinity;
  for(const s of (e.subs||[])){
    if(s.dead) continue;
    const d=Math.abs((e.x+s.ox)-hx);
    if(d<bd){ bd=d; best=s; }
  }
  return (bd<=1) ? best : null;
}
const SUB_HULL_BLEED = 0.25;
// Lasting damage marks are drawing only.
function dmgCrater(){}
function dmgHit(){}
${consts.join('\n')}
${names.map(fn).join('\n')}
${fn('subHit')}
`;

const vm = require('vm');
const ctxObj = {console, Math, Infinity};
vm.createContext(ctxObj);
vm.runInContext(WORLD, ctxObj);
const run = (code)=>vm.runInContext(code, ctxObj);
const get = (name)=>vm.runInContext(name, ctxObj);
const set = (name, v)=>{ ctxObj[name] = v; };

let fails = 0;
function ok(label, cond){ console.log((cond?'  ok    ':'  FAIL  ')+label); if(!cond) fails++; }
const bullets = ()=>get('pBullets');
const clear = ()=>{ ctxObj.pBullets.length = 0; };
const fire = (key)=>{ run("player.pri='"+key+"'; applyLoadout()"); clear(); run('pShoot()'); };

// v186: a fit is put on with the banks of the hull; fitP / fitS set one up.
const fitShip = (ship, p, sec)=>{ run(`player.ship='${ship}'; player.en=null; FITS['${ship}']={p:${JSON.stringify(p)}, s:${JSON.stringify(sec)}}; player.pMode=0; player.sSel=0; applyLoadout()`); clear(); };
const shoot = ()=>{ clear(); for(const b of get('player').pb) b.t=0; run('pShootBanks()'); };

console.log('The standard gun is the gun the game had');
fitShip('fitoth', ['promr'], ['harpoon']); shoot();
{
  const b = bullets(), w = run("priDefP('promr')");
  ok('two barrels, two bolts', b.length===2);
  ok('each carries the full share of the volley', b.every(x=>Math.abs(x.dmg-run('volleyDmg(2)'))<1e-9));
  ok('the Prometheus R carries no factors', b[0].f.a===1 && b[0].f.s===1 && b[0].f.u===1);
  ok('it flies 2 s, the FS2 lifetime', b[0].pLife===120);
  ok('it pays 0.6 from the store', Math.abs(get('player').en-(get('player').enMax-0.6))<1e-9);
  ok('and the bank waits its 27 steps', get('player').pb[0].t===27);
  run('pShootBanks()');
  ok('it does not fire again before that', bullets().length===2);
}

console.log('\nTwo banks: one at a time, or linked');
fitShip('fimyrmidon', ['promr','subach'], ['rockeye','tornado','tempest']);
{
  shoot();
  ok('bank 1 fires from its share of the barrels', bullets().length===1 && bullets()[0].wpn==='promr');
  ok('and lands what a full volley lands', Math.abs(bullets()[0].dmg - run('volleyTotal(2)'))<1e-9);
  run('cyclePrimary()'); shoot();
  ok('bank 2 from the others', bullets().length===1 && bullets()[0].wpn==='subach' && bullets()[0].y===254);
  ok('the Subach keeps its FS2 ratio', Math.abs(bullets()[0].dmg - run('volleyTotal(2)')*15/18)<1e-9);
  run('cyclePrimary()'); run('player.en=player.enMax'); shoot();
  ok('linked, both banks fire', bullets().length===2 && new Set(bullets().map(b=>b.wpn)).size===2);
  ok('and both are paid for', Math.abs(get('player').en-(get('player').enMax-0.8))<1e-9);
  run('player.en=0.5'); shoot();
  ok('a bank the store cannot pay for stays silent', bullets().length===1 && bullets()[0].wpn==='subach');
  run('player.en=0'); shoot();
  ok('an empty store: nothing at all', bullets().length===0);
  // The store: linked fire for about ten seconds from full (Silvio).
  run('player.en=player.enMax; for(const b of player.pb) b.t=0;');
  let t=0; for(; t<3000; t++){ run('bankTick(); pShootBanks()'); if(get('player').en < 0.6) break; }
  ok('linked from full lasts about ten seconds ('+(t/60).toFixed(1)+' s)', t/60 > 8.5 && t/60 < 11.5);
  run('player.pMode=0; player.en=player.enMax; for(const b of player.pb) b.t=0;');
  for(let k=0;k<3600;k++) run('bankTick(); pShootBanks()');
  ok('the Prometheus R alone never runs dry', get('player').en > 0.6);
}

console.log('\nStreuschuss: a cone from one trigger pull');
fitShip('fitoth', ['scatter'], ['harpoon']); shoot();
{
  const b = bullets(), w = run("priDef('scatter')");
  ok('seven pellets per barrel', b.length === 2*w.pellets);
  ok('the volley is shared out, not multiplied',
     Math.abs(b.reduce((a,x)=>a+x.dmg,0) - run('volleyTotal(2)')*w.dmg) < 1e-6);
  const ang = b.map(x=>Math.atan2(x.vy, x.vx));
  const spread = Math.max(...ang)-Math.min(...ang);
  ok('they leave in a spread, not in a line', spread > w.spread*0.5);
  ok('the reach is short', b[0].pLife>0 && b[0].pLife*w.spd <= w.range+w.spd);
}

// v210: a lock as tgtTick() builds it - the target held for its full time
function lockOn(e){ run('TGT.e=null; TGT.sub=null; TGT.lock=0; TGT.lockOf=null'); ctxObj.__t = e; run('tgtSet(__t); TGT.lock=1e6'); }
function lockOff(){ run('TGT.e=null; TGT.sub=null; TGT.lock=0'); }
console.log('\nSwarms (v210): one press, four seekers, all on the locked target');
{
  const mk = (x,y)=>({x:x, y:y, hp:100, dead:false});
  fitShip('fiherc', ['subach','promr'], ['harpoon','tornado']);
  run("player.sSel=1; syncLegacyWeapons(); player.secTimer=0");
  set('enemies', [mk(300,200), mk(300,300), mk(400,250), mk(500,250)]);
  ctxObj.enemies = run('enemies'); clear();
  const before = get('player').sb[1].ammo;
  lockOn(run('enemies')[2]);
  run('fireSecondary()');
  const b = bullets().filter(x=>x.sec);
  ok('four Tornados leave', b.length===4);
  ok('and they cost one round, not four', get('player').sb[1].ammo===before-1);
  ok('all four go for the locked target', b.every(x=>x.target===run('enemies')[2]));
  ok('each carries its FS2 factors (hull 2.0 of a Harpoon)', b.every(x=>x.f && x.f.a===2));
  clear(); lockOff(); run('player.secTimer=0; fireSecondary()');
  ok('without a lock they fly straight (no target)', bullets().filter(x=>x.sec).every(x=>x.target===null));
  lockOff();
}

console.log('\nAspect seekers fly to their lock, heat seekers take what is in their cone (v210)');
{
  const near = {x:200, y:250, hp:100, dead:false}, ahead = {x:600, y:250, hp:100, dead:false}, behind = {x:20, y:250, hp:100, dead:false};
  run('enemies.length=0'); run('enemies').push(behind, ahead);
  fitShip('fitoth', ['promr'], ['harpoon']); lockOn(ahead); run('player.secTimer=0; fireSecondary()');
  const h = bullets().find(x=>x.sec);
  ok('a Harpoon flies to the ship it holds a lock on', h.target===ahead && h.aspect===true);
  run('enemies').push(near);
  run('updateSecBullets()');
  ok('a nearer ship turning up does not take the lock', h.target===ahead);
  clear(); lockOff(); run('player.secTimer=0; fireSecondary()');
  const h0 = bullets().find(x=>x.sec), vy0 = h0.vy;
  run('updateSecBullets()');
  ok('without a lock a Harpoon flies straight', h0.target===null && h0.vy===vy0);
  clear(); run('enemies.length=0'); run('enemies').push(behind);
  fitShip('fitoth', ['promr'], ['rockeye']); run('player.secTimer=0; fireSecondary()');
  const r = bullets().find(x=>x.sec), rvx = r.vx;
  run('updateSecBullets()');
  ok('a Rockeye does not turn back for a ship behind it', !r.aspect && r.heat && r.target===null && r.vx===rvx);
  run('enemies').push(ahead); run('updateSecBullets()');
  ok('a Rockeye takes a heat source in its cone', r.target===ahead);
  clear(); run('enemies.length=0');
}

console.log('\nDante: a burst on impact and a burst by itself');
fitShip('fitoth', ['dante'], ['harpoon']); shoot();
{
  const b = bullets(), w = run("priDef('dante')");
  ok('it carries a fuse', b[0].fuse > 0);
  ok('the fuse is the distance turned into steps', b[0].fuse === Math.max(1, Math.round(w.fuse/w.spd)));
  ok('the round knows which weapon made it, so the burst can be looked up', b[0].wpn==='dante');
}

console.log('\nInfyrno: the button belongs to the round in the air (v187: 14 seekers)');
{
  fitShip('fiherc', ['subach'], ['infyrno']); run('player.secTimer=0');
  const n0 = get('player').sb[0].ammo;
  run('fireSecondary()');
  ok('one round leaves', bullets().length===1 && bullets()[0].burst===true && bullets()[0].homing===false);
  run('player.secTimer=0; fireSecondary()');
  const kids = bullets(), w = run("secDefP('infyrno')");
  ok('the second press lets go 14 small heat seekers', kids.length===14 && kids.every(k=>k.sec && k.homing && !k.aspect));
  ok('and costs no second round', get('player').sb[0].ammo===n0-1);
  ok('each with the table damage: 100 of a Harpoon\'s 100 = 35', Math.abs(kids[0].dmg-35)<1e-9 && w.childDmg===kids[0].dmg);
  ok('table speed 250 m/s = 5 per step, life 0.3 s = 18 steps', kids[0].maxSpd===5 && kids[0].life===18);
  run('enemies.length=0'); clear();
  run('player.secTimer=0; fireSecondary()');
  const r = bullets()[0]; r.life = 1;
  run('updateSecBullets()');
  ok('left alone it goes off at the end of its flight', bullets().length===14);
  clear();
}

console.log('\nv187b: a seeker comes round in its FS2 turn time, whatever its speed');
{
  const h = run("secDefP('harpoon')"), r = run("secDefP('rockeye')");
  const halfCircle = w => Math.PI / (w.turn / w.spd) / 60;   // seconds for 180 degrees
  ok('Harpoon: 1.0 s', Math.abs(halfCircle(h)-1.0) < 1e-9);
  ok('Rockeye: 0.85 s', Math.abs(halfCircle(r)-0.85) < 1e-9);
  // Fired straight down at a fighter well off to the side (65 degrees off
  // the nose, 300 points away): it comes round and gets there. Closer in
  // than its turning circle it would orbit, as in FS2.
  const e = {x:600, y:390, hp:1e6, maxHp:1e6, dead:false, type:'fighter', img:'fidragon', w:30, h:12};
  run('enemies.length=0'); run('enemies').push(e);
  fitShip('fitoth', ['promr'], ['harpoon']); lockOn(e);
  run('player.x=300; player.y=250; player.head=Math.PI/2; player.secTimer=0; fireSecondary()');
  const m = bullets().find(x=>x.sec);
  let best = 1e9;
  for(let i=0;i<150 && bullets().indexOf(m)>=0;i++){ run('updateSecBullets()'); best = Math.min(best, Math.hypot(m.x-e.x, m.y-e.y)); }
  ok('a Harpoon launched sideways still reaches its target (closest '+Math.round(best)+')', best < 12 || bullets().indexOf(m)<0);
  run('enemies.length=0'); clear(); lockOff();
}

console.log('\nv189/v210: the Trebuchet on the locked cruiser, the Stiletto II looks for a capital ship');
{
  const fi = {x:220, y:250, hp:1e6, dead:false, type:'fighter'}, cr = {x:600, y:250, hp:1e6, dead:false, type:'cruiser'};
  run('enemies.length=0'); run('enemies').push(fi, cr);
  fitShip('fitoth', ['promr'], ['trebuchet']); lockOn(cr); run('player.x=100; player.y=250; player.head=0; player.secTimer=0; fireSecondary()');
  ok('a Trebuchet locked on the cruiser flies to it, not to the nearer fighter', bullets().find(x=>x.sec).target === cr);
  clear(); fitShip('fitoth', ['promr'], ['harpoon']); lockOn(fi); run('player.secTimer=0; fireSecondary()');
  ok('a Harpoon locked on the fighter takes the fighter', bullets().find(x=>x.sec).target === fi);
  clear(); lockOff(); fitShip('boosiris', ['mekhu'], ['stiletto2']); run('player.secTimer=0; fireSecondary()');
  const st = bullets().find(x=>x.sec), vy0 = st.vy;
  cr.y = 150; run('updateSecBullets()');
  ok('a Stiletto II steers for the cruiser (up), not the fighter ahead', st.vy < vy0);
  run('enemies.length=0'); run('enemies').push(fi);
  clear(); fitShip('fitoth', ['promr'], ['stiletto2']); run('player.secTimer=0; fireSecondary()');
  run('updateSecBullets()');
  ok('with no capital ship about, the Stiletto II takes the fighter in its cone', bullets().find(x=>x.sec).target === fi);
  run('enemies.length=0'); clear();
}

console.log('\nv187: Lamprey, Hornet, Piranha, Helios are out');
{
  const gone = ['lamprey','hornet','piranha','helios'];
  ok('not in the arsenal', run("ARSENAL_P.concat(ARSENAL_S).map(w=>w.key)").every(k=>gone.indexOf(k)<0));
  const SB = run('SHIP_BANKS');
  ok('no hull carries or may carry one', Object.keys(SB).every(h=>['p','pa','s','sa'].every(f=>SB[h][f].every(k=>gone.indexOf(k)<0))));
  ok('a default fit only holds what the hull may carry', Object.keys(SB).every(h=>SB[h].s.every(k=>SB[h].sa.indexOf(k)>=0 || h==='boosiris')));
  ok('the Ursa: Tornado, Infyrno, Cyclops', SB.boursa.s.join()==='tornado,infyrno,cyclops');
}

console.log('\nStiletto II: the warhead goes inside');
{
  const w = run("secDefP('stiletto2')");
  ok('it hits only subsystems: no shield, hardly any hull', w.f.s===0 && w.f.a<0.02 && w.f.u===2);
  ok('it seeks by heat', w.homing==='heat');
  ok('a fit puts it into the bank that carries it', (fitShip('boosiris', ['mekhu'], ['infyrno','stiletto2','trebuchet']), get('player').sb[1].key==='stiletto2'));
  ok('the rack follows capacity and cargo: 40 / 8 = 5', get('player').sb[1].max===5);
}

console.log('\nA mission fits what it needs');
{
  fitShip('boursa', ['promr','promr'], ['tornado','infyrno','cyclops']);
  run("missionSec(arsenalKey('stiletto'), false)");
  ok('M57: the Stiletto II goes into bank 1, full', get('player').sb[0].key==='stiletto2' && get('player').sb[0].ammo===10);
  run("missionSec(arsenalKey('tag'), true)");
  ok('M67: the TAG-C into the last bank, which is then chosen', get('player').sb[2].key==='tagc' && get('player').sSel===2);
}

// Shrapnel goes all round: no gap wider than 100 degrees.
function allRound(list){
  const a = list.map(x=>Math.atan2(x.vy,x.vx)).sort((p,q)=>p-q);
  let gap = a[0] + Math.PI*2 - a[a.length-1];
  for(let i=1;i<a.length;i++) gap = Math.max(gap, a[i]-a[i-1]);
  return gap < 100*Math.PI/180;
}
console.log('\nCapital flak: a wall, not a shot');
{
  ok('a cruiser carries one', run("flakHas({type:'cruiser'})")===true);
  ok('so do corvettes and destroyers',
     run("flakHas({type:'corvette'})")===true && run("flakHas({type:'destroyer'})")===true);
  ok('a fighter does not', run("flakHas({type:'fighter'})")===false);
  ok('nor a bomber or a freighter',
     run("flakHas({type:'bomber'})")===false && run("flakHas({type:'freighter'})")===false);
}
{
  // The wall must stand out in front, not on the gun and not off the far edge.
  const MIN = run('FLAK_MIN'), MAX = run('FLAK_DIST'), KEEP = run('FLAK_EDGE_KEEP');
  ok('a target further than the gun reaches: the wall stops at its limit',
     run('flakReach(700, 250, Math.PI, 900)') === MAX);
  ok('a target sitting on the muzzle: it never bursts nearer than the minimum',
     run('flakReach(700, 250, Math.PI, 5)') === MIN);
  // Firing left from x=700 at full reach would burst at 400, which is fine.
  // Firing left from x=300 would burst at 0 - off the field. It has to pull in.
  const d = run('flakReach(300, 250, Math.PI, 900)');
  ok('a gun close to the far edge pulls its wall in', d < MAX);
  ok('and the burst lands inside the field with room to spare',
     300 - d >= KEEP - 22);
}
{
  // Shrapnel, on the right side of the fight.
  set('FLAK_TARGET', {x:100, y:250});
  run('pBullets.length=0; eBullets.length=0');
  run("flakBurst(400, 250, true, 'vasudan')");
  const p = get('pBullets');
  ok('an allied gun throws its shrapnel at the enemies',
     Math.abs(p.length-run('FLAK_SHARDS'))<=1 && p.every(b=>b.ally===true) && get('eBullets').length===0);
  ok('star shaped, not thrown one way', allRound(p));
  ok('and it gives out rather than flying to the edge', p.every(b=>b.pLife>0));
  run('pBullets.length=0; eBullets.length=0');
  run("flakBurst(400, 250, false, 'shivan')");
  ok('an enemy gun the other way round',
     Math.abs(get('eBullets').length-run('FLAK_SHARDS'))<=1 && get('pBullets').length===0);
  ok('with a life of its own too', get('eBullets').every(b=>b.eLife>0));
}
{
  // The gun itself: one round, on a fuse, from the mount.
  set('FLAK_TARGET', {x:100, y:250});
  run('pBullets.length=0; eBullets.length=0');
  const cruiser = {type:'cruiser', x:600, y:250, faction:'vasudan', dead:false, warp:0, warpOut:0};
  set('_c', cruiser);
  run('_c.flakT = 1; flakFire(_c, true)');
  const b = get('pBullets');
  ok('one round leaves, not a burst at the muzzle', b.length===1);
  ok('it carries a fuse', b[0].fuse > 0);
  ok('it is flagged as flak so the fuse knows what to do', b[0].flak===true);
  ok('and it travels towards the target', b[0].vx < 0);
  ok('the clock is reset rather than firing every step', cruiser.flakT > 1);
  run('pBullets.length=0');
  run('flakFire(_c, true)');
  ok('and it does not fire again on the next step', get('pBullets').length===0);
}
{
  // A wreck or a ship still in the vortex does not shoot.
  set('FLAK_TARGET', {x:100, y:250});
  run('pBullets.length=0');
  set('_c', {type:'cruiser', x:600, y:250, faction:'vasudan', dead:true, warp:0, warpOut:0, flakT:1});
  run('flakFire(_c, true)');
  set('_c', {type:'cruiser', x:600, y:250, faction:'vasudan', dead:false, warp:30, warpOut:0, flakT:1});
  run('flakFire(_c, true)');
  ok('neither a wreck nor a ship still warping in fires', get('pBullets').length===0);
  set('_c', {type:'fighter', x:600, y:250, faction:'vasudan', dead:false, warp:0, warpOut:0, flakT:1});
  run('flakFire(_c, true)');
  ok('and a fighter has no flak gun to fire', get('pBullets').length===0);
}
ok('both sides run the gun', /flakFire\(e, false\)/.test(src) && /flakFire\(a, true\)/.test(src));
ok('the enemy fuse bursts where it runs out',
   /if\(b\.fuse && --b\.fuse<=0\)\{\n\s*flakBurst\(b\.x, b\.y, false, b\.faction(, b\.fmul)?\)/.test(src));

console.log('\nEvery weapon is reachable and none of them is free');
{
  const all = run('ARSENAL_P').concat(run('PRIMARIES'), run('ARSENAL_S'));
  ok('each one has a name', all.every(w=>!!w.name));
  ok('each one has a note that says what it is for', all.every(w=>!!w.note));
  ok('every default fit is in the arsenal',
     Object.values(run('SHIP_BANKS')).every(b=>b.p.every(k=>run('ARSENAL_P').some(w=>w.key===k)) &&
                                              b.s.every(k=>run('ARSENAL_S').some(w=>w.key===k))));
  ok('no hull has more than two primary or three secondary banks',
     Object.values(run('SHIP_BANKS')).every(b=>b.p.length<=2 && b.s.length<=3 && b.cap.length<=3));
  ok('the Dante comes with the Shivan cycle (mission 61)', run('PRIMARIES').find(w=>w.key==='dante').fromWave===61);
  ok('the TAG-C with mission 67', run('ARSENAL_S').find(w=>w.key==='tagc').fromWave===67);
}

console.log('\n' + (fails ? fails+' FAILED' : 'all passed'));
process.exit(fails?1:0);
