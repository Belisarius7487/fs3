// Weapon simulation. Pulls the REAL firing routines out of the logic file and
// runs them against stand-ins for the world.
//
// What it is for: four of the weapons do something rather than merely weigh
// something - a cone, a bolt that carries on through, a round that bursts,
// a warhead that goes for the innards. Numbers can be read off the table;
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
               'liveBurstRound','burstRound','volleyDmg','volleyTotal','primaryCount'];
const consts = [
  decl(/const PLAYER_FR_BASE[\s\S]*?\n\];/),
  decl(/const SECONDARIES = \[[\s\S]*?\n\];/),
  decl(/const VOLLEY_BASE\s*=\s*[\d.]+;/),
  decl(/const VOLLEY_PER_EXTRA\s*=\s*[\d.]+;/)
];

const WORLD = `
const W = 800, H = 500, HUD_H = 54;
var pBullets = [], PARTS = [], SUB_MSGS = [], enemies = [], allies = [];
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
  ok('one pellet on its own is slight', b[0].dmg < run('volleyDmg(2)')/3);
  // Angles: the cone has to be a cone, and it has to point forward.
  const ang = b.map(x=>Math.atan2(x.vy, x.vx));
  const spread = Math.max(...ang) - Math.min(...ang);
  ok('they leave in a spread, not in a line', spread > w.spread*0.5);
  ok('and the spread stays inside what the table allows', spread <= w.spread*1.6);
  ok('all of them still go forward', ang.every(a=>Math.abs(a) < Math.PI/2));
  // pLife is whole steps, so the reach lands within one step of the table.
  ok('the reach is short', b[0].pLife>0 && b[0].pLife*w.spd <= w.range+w.spd);
}

console.log('\nDurchschlag: a line, once each');
fire('pierce');
{
  const b = bullets(), w = run("priDef('pierce')");
  ok('one bolt per barrel again', b.length===2);
  ok('it is allowed four hulls', b[0].pierce===w.pierce);
  ok('and it carries no fuse', !b[0].fuse);
  ok('no reach limit, so the line runs the field', !b[0].pLife);
  // The rule that stops a long hull being hit once per step lives in the
  // collision loop, which is too entangled to run here.
  ok('a pierced hull is remembered so it cannot be hit twice',
     /b\.hitList && b\.hitList\.indexOf\(e\)>=0\) continue/.test(src));
  ok('and piercing decrements rather than removing the bolt',
     /b\.pierce--/.test(src) && /b\.hitList\.push\(e\)/.test(src));
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
