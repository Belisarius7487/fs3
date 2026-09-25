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

const names = ['priDef','secDef','curPri','curSec','hullSecCls','weaponName','weaponOpen',
               'secondariesFor','defaultSec','applyLoadout','rearmFull',
               'shardBurst','subStrike','pShoot','fireSecondary',
               'liveBurstRound','burstRound','volleyDmg','volleyTotal','primaryCount',
               'flakHas','flakBurst','flakReach','flakFire',
               'swarmTargets','swarmRetarget','swarmHolds','updateSecBullets','rmValue'];
const consts = [
  decl(/const PLAYER_FR_BASE[\s\S]*?\n\];/),
  decl(/const SECONDARIES = \[[\s\S]*?\n\];/),
  decl(/const VOLLEY_BASE\s*=\s*[\d.]+;/),
  decl(/const VOLLEY_PER_EXTRA\s*=\s*[\d.]+;/),
  decl(/const FLAK_TYPES[\s\S]*?const FLAK_SHARD_RANGE = \d+;/),
  decl(/let swarmSalvo = 0;/)
];

const WORLD = `
const W = 800, H = 500, HUD_H = 54;
var pBullets = [], eBullets = [], PARTS = [], SUB_MSGS = [], enemies = [], allies = [];
var fc = 0, score = 0, FS1_MODE = false, UI_WEAPONS = false;
const UI_TICKETS = false;
const STATS = {shots:0, hits:0, subsKilled:0};
var player = {x:100, y:250, head:0, ang:0, flip:false, ship:'fitoth',
              fR:28, secAmmo:20, secMax:20, secTimer:0, secType:'missile',
              pri:'prometheus', sec:'mx64'};
// Mounts are the hull's business, not the weapon's. Two barrels, fixed, so a
// change in the volley can only come from the gun.
function mountList(){ return [{x:120, y:246}, {x:120, y:254}]; }
function playerSc(){ return 1; }
function isBomberHull(k){ return k.indexOf('bo')===0; }
function shipFac(k){ return 'vasudan'; }
function shipStats(k){ return {sec: isBomberHull(k) ? 10 : 20}; }
function spawnFireball(){} 
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

console.log('The standard gun is the gun the game had');
fire('prometheus');
{
  const b = bullets();
  ok('two barrels, two bolts', b.length===2);
  ok('each carries the full share of the volley',
     Math.abs(b[0].dmg - run('volleyDmg(2)')) < 0.001);
  ok('and it runs to the edge of the field', !b[0].pLife);
  ok('it neither pierces nor bursts', !b[0].pierce && !b[0].fuse);
}

console.log('\nStreuschuss: a cone from one trigger pull');
fire('scatter');
{
  const b = bullets(), w = run("priDef('scatter')");
  ok('seven pellets per barrel', b.length === 2*w.pellets);
  const total = b.reduce((s,x)=>s+x.dmg, 0);
  ok('the volley is shared out, not multiplied',
     Math.abs(total - run('volleyDmg(2)')*2*w.dmg) < 0.01);
  // Slight against the volley of a single barrel, which is what a pellet
  // has to be for the cone to mean anything.
  ok('one pellet on its own is slight', b[0].dmg < run('volleyDmg(2)'));
  // Angles: the cone has to be a cone, and it has to point forward.
  const ang = b.map(x=>Math.atan2(x.vy, x.vx));
  const spread = Math.max(...ang) - Math.min(...ang);
  ok('they leave in a spread, not in a line', spread > w.spread*0.5);
  ok('and the spread stays inside what the table allows', spread <= w.spread*1.6);
  ok('all of them still go forward', ang.every(a=>Math.abs(a) < Math.PI/2));
  // pLife is whole steps, so the reach lands within one step of the table.
  ok('the reach is short', b[0].pLife>0 && b[0].pLife*w.spd <= w.range+w.spd);
}

console.log('\nDurchschlag is gone');
{
  ok('it is no longer in the table', run('PRIMARIES').every(w=>w.key!=='pierce'));
  run("player.pri='pierce'; applyLoadout()");
  ok('a ship that still had it fitted falls back to the Prometheus',
     get('player').pri==='prometheus');
  ok('and nothing is left of the piercing mechanism',
     !/b\.pierce/.test(src) && !/hitList/.test(src));
}

console.log('\nTornado: one press, four seekers, four targets');
// A fresh field: four enemies ahead of the ship, spread top to bottom.
function field(ys){
  run('enemies.length=0; HITS.length=0; pBullets.length=0; LOCK_OK=true');
  for(const y of ys) run('enemies.push({x:500, y:'+y+', hp:100, dead:false})');
  run("player.pri='prometheus'; player.sec='tornado'; player.ship='fitoth'; applyLoadout(); player.secAmmo=player.secMax; player.secTimer=0");
}
// Runs the real flight and impact routine, the one the game runs every step.
function fly(steps){ for(let i=0;i<steps;i++){ run('fc++'); run('updateSecBullets()'); } }
{
  const w = run("secDef('tornado')");
  ok('it is in the table as a missile', !!w && w.key==='tornado' && w.cls==='missile');
  ok('it opens at 22,000, where the Durchschlag was', w.unlock===22000);
  ok('a fighter is offered it', run("secondariesFor('fitoth')").some(x=>x.key==='tornado'));
  ok('a bomber is not', run("secondariesFor('boosiris')").every(x=>x.key!=='tornado'));
  ok('the rearm panel shows the salvo, not one missile',
     run("rmValue(secDef('tornado'), 'dmg', false)")===w.swarm+'\u00d7'+w.dmg);
}
{
  field([150, 220, 290, 360]);
  const before = get('player').secAmmo;
  run('fireSecondary()');
  const b = bullets().filter(x=>x.sec);
  ok('four missiles leave', b.length===4);
  ok('and they cost one round, not four', get('player').secAmmo===before-1);
  ok('every one of them seeks', b.every(x=>x.homing));
  ok('each has a different target', new Set(b.map(x=>x.target)).size===4);
  const ang = b.map(x=>Math.atan2(x.vy, x.vx));
  ok('they leave in a fan, not in a line', Math.max(...ang)-Math.min(...ang) > 0.5);
  fly(200);
  const struck = new Set(get('HITS').map(h=>h.e.y));
  ok('in flight, all four targets are struck - not the nearest one four times',
     struck.size===4);
  ok('four impacts, each carrying one missile\'s damage',
     get('HITS').length===4 && get('HITS').every(h=>h.d===run("secDef('tornado').dmg")));
}
{
  field([200, 300]);
  run('fireSecondary()');
  fly(200);
  const ys = get('HITS').map(h=>h.e.y);
  ok('two targets: the salvo splits over both instead of dropping missiles',
     ys.filter(y=>y===200).length===2 && ys.filter(y=>y===300).length===2);
}
{
  // A target that dies on the way: its missile has to find a free one.
  field([150, 250, 350]);
  run("player.secTimer=0");
  run('fireSecondary()');
  const lost = run('enemies[0]');
  fly(3);
  run('enemies[0].dead=true; enemies.splice(0,1)');
  fly(200);
  ok('a missile whose target is gone does not fly on into nothing',
     get('HITS').length===4);
  ok('and it never strikes the dead one', get('HITS').every(h=>h.e!==lost));
}
{
  // No lock in a nebula or a storm: straight flight, like every other seeker.
  field([150, 250, 350, 450]);
  run('LOCK_OK=false');
  run('fireSecondary()');
  const b = bullets().filter(x=>x.sec);
  ok('without a lock the missiles leave with no target', b.every(x=>x.target===null));
  const v0 = b.map(x=>x.vy);
  fly(10);
  ok('and they keep their heading', bullets().filter(x=>x.sec).every((x,i)=>Math.abs(x.vy-v0[i])<1e-9));
}
{
  // Other seekers are unchanged: the MX-64 still goes for the nearest.
  field([240, 400]);
  run("player.sec='mx64'; applyLoadout(); player.secAmmo=5; player.secTimer=0");
  run('fireSecondary()');
  ok('the MX-64 still fires a single missile', bullets().filter(x=>x.sec).length===1);
  fly(200);
  ok('and it still takes the nearest', get('HITS').length===1 && get('HITS')[0].e.y===240);
}

console.log('\nDante: a burst on impact and a burst by itself');
fire('dante');
{
  const b = bullets(), w = run("priDef('dante')");
  ok('it carries a fuse', b[0].fuse > 0);
  ok('the fuse is the distance turned into steps',
     Math.abs(b[0].fuse - Math.round(w.fuse/w.spd)) <= 1);
  ok('the fuse goes off before the reach runs out',
     b[0].fuse < b[0].pLife || !b[0].pLife);
  ok('the round knows which weapon made it, so the burst can be looked up',
     b[0].wpn==='dante');
  ok('the fuse is counted down and burst where it stands',
     /if\(b\.fuse && --b\.fuse<=0\)/.test(src));
}
{
  // The burst itself.
  clear();
  run("shardBurst(400, 250, 9, 5, 3.4, 70, '#fff', 'rgba(0,0,0,0)')");
  const s = bullets();
  ok('nine shards leave the point', s.length===9);
  ok('every one of them carries the damage it was given', s.every(x=>x.dmg===5));
  ok('all at the same speed', s.every(x=>Math.abs(Math.hypot(x.vx,x.vy)-3.4)<0.001));
  ok('and they are short lived', s.every(x=>x.pLife>0 && x.pLife<=Math.ceil(70/3.4)));
  // Star shaped means the directions cancel out. A cone would not.
  const sx = s.reduce((a,x)=>a+x.vx, 0), sy = s.reduce((a,x)=>a+x.vy, 0);
  ok('star shaped, not thrown one way', Math.abs(sx)<0.001 && Math.abs(sy)<0.001);
  ok('they all start where the round was', s.every(x=>x.x===400 && x.y===250));
}

console.log('\nInfyrno: the button belongs to the round in the air');
{
  run("player.pri='prometheus'; player.sec='infyrno'; applyLoadout(); player.secAmmo=6; player.secTimer=0");
  clear();
  run('fireSecondary()');
  ok('one round leaves', bullets().length===1);
  ok('it is flagged as one that can be burst', bullets()[0].burst===true);
  ok('and it does not seek', bullets()[0].homing===false);
  ok('a round was taken from the rack', get('player').secAmmo===5);
  // Pressing again must burst it, not fire another.
  run('player.secTimer=0');
  run('fireSecondary()');
  const after = bullets();
  ok('the second press does not fire another',
     after.every(b=>!b.sec) );
  ok('it bursts into shrapnel instead', after.length===run("secDef('infyrno').shards"));
  ok('and costs no second round', get('player').secAmmo===5);
  ok('with one gone, the button fires again', run('liveBurstRound()')===null);
}
{
  // Never pressed: it has to give out rather than burst for free.
  run("player.secAmmo=6; player.secTimer=0");
  clear();
  run('fireSecondary()');
  const b = bullets()[0];
  ok('it carries a finite reach', b.life>0);
  ok('which is the table value', b.life===run("secDef('infyrno').life"));
}

console.log('\nStiletto: the warhead goes inside');
{
  const sub = (label, ox, hp)=>({label:label, ox:ox, hp:hp, dead:false});
  const ship = {x:400, y:250, side:'enemy',
                subs:[sub('ENGINES', -40, 30), sub('NAVIGATION', 40, 30)]};
  // Impact near the bow, engines are at the stern: a warhead that only hit
  // what lay under it would waste itself on the hull.
  set('_e', ship);
  const bleed = run("subStrike(_e, 70, 460, 250)");
  ok('the nearest living subsystem takes it', ship.subs[1].hp <= 0 || ship.subs[1].dead);
  ok('and it is the one nearest the impact', ship.subs[0].hp === 30);
  ok('only the bleed is left for the hull', bleed < 70 && bleed > 0);
}
{
  const ship = {x:400, y:250, side:'enemy',
                subs:[{label:'ENGINES', ox:-40, hp:30, dead:true}]};
  set('_e', ship);
  ok('nothing left to wreck: the full warhead goes to the hull',
     run("subStrike(_e, 70, 400, 250)")===70);
  set('_e', {x:400, y:250, side:'enemy'});
  ok('a ship with no subsystems at all is the same',
     run("subStrike(_e, 70, 400, 250)")===70);
}
ok('the secondary impact asks the weapon, not the projectile shape',
   /sw && sw\.subs\) damageEnemy\(e,subStrike/.test(src));

console.log('\nWhat a hull may carry is unchanged');
{
  run("player.ship='fitoth'; applyLoadout()");
  ok('a fighter is offered the Infyrno but not the Stiletto',
     run("secondariesFor('fitoth')").some(w=>w.key==='infyrno') &&
     run("secondariesFor('fitoth')").every(w=>w.key!=='stiletto'));
  ok('and a bomber the other way round',
     run("secondariesFor('boosiris')").some(w=>w.key==='stiletto') &&
     run("secondariesFor('boosiris')").every(w=>w.key!=='infyrno'));
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
     p.length===run('FLAK_SHARDS') && p.every(b=>b.ally===true) && get('eBullets').length===0);
  const sx = p.reduce((a,b)=>a+b.vx,0), sy = p.reduce((a,b)=>a+b.vy,0);
  ok('star shaped, not thrown one way', Math.abs(sx)<0.001 && Math.abs(sy)<0.001);
  ok('and it gives out rather than flying to the edge', p.every(b=>b.pLife>0));
  run('pBullets.length=0; eBullets.length=0');
  run("flakBurst(400, 250, false, 'shivan')");
  ok('an enemy gun the other way round',
     get('eBullets').length===run('FLAK_SHARDS') && get('pBullets').length===0);
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
   /if\(b\.fuse && --b\.fuse<=0\)\{\n\s*flakBurst\(b\.x, b\.y, false, b\.faction\)/.test(src));

console.log('\nEvery weapon is reachable and none of them is free');
{
  const all = run('PRIMARIES').concat(run('SECONDARIES'));
  ok('each one has a name', all.every(w=>!!w.name));
  ok('each one has a note that says what it is for', all.every(w=>!!w.note));
  ok('the thresholds rise rather than repeat',
     new Set(all.map(w=>w.unlock)).size >= all.length-2);
  ok('the standard fit is the only free gun',
     run('PRIMARIES').filter(w=>!w.unlock).length===1);
}

console.log('\n' + (fails ? fails+' FAILED' : 'all passed'));
process.exit(fails?1:0);
