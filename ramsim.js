// Ramming simulation. Pulls the REAL functions out of the logic file and runs
// them against stand-ins for the world.
//
// This exists because the ram test in mechsim.js works from a hand written
// copy of tickCapRam with minY and maxY already set to the full height of the
// field. It passed seven out of seven while the cruiser in mission 28 was
// missing in the game, because the fault was not in tickCapRam at all - it was
// in applySpawnOpts, which pinned the attacker to its spawn height. A copy
// cannot catch that. This file reads what actually ships.
//
// Usage: node ramsim.js <logic.html>
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

const names = ['ramsOnContact', 'tickRamming', 'tickCapRam', 'ramBlast',
               'applySpawnOpts', 'halfW', 'halfH'];
const consts = [
  decl(/const RAM_PCT_CAPITAL = [\d.]+;/),
  decl(/const RAM_PCT_BOMBER  = [\d.]+;/),
  decl(/const RAM_PCT_FIGHTER = [\d.]+;/),
  decl(/const RAM_OVERLAP = \d+;/)
];

// A world just large enough for the ramming to run in. Everything the real
// functions reach for that has nothing to do with ramming is a stub that
// records rather than draws.
const WORLD = `
const W = 800, H = 500, HUD_H = 54;
// var, not let: a let binding inside the context cannot be replaced from
// outside, and these lists are set up fresh for every case below.
var enemies = [], allies = [], PARTS = [], SUB_MSGS = [], spawnQ = [];
var fc = 0, wave = 1, protLost = 0, guardLost = false;
const EV_HELD = {}, EV_SEEN = {}, EV_POS = {};
var player = {x:100, y:250, hp:100, maxHp:100, sh:0, maxSh:100, small:true, side:'ally'};
const IMGS = {
  dehatshepsut:{width:420, height:150},
  crmentu:     {width:200, height:120},
  bobakha:     {width:40,  height:24},
  boosiris:    {width:40,  height:24}
};
const EFFECTS = [];
function hullHit(x,y){ EFFECTS.push({fn:'hullHit', x:x, y:y}); }
function shieldHit(x,y){ EFFECTS.push({fn:'shieldHit', x:x, y:y}); }
function triggerExpl(x,y,kind,fac,e){ EFFECTS.push({fn:'expl', kind:kind, x:x, y:y}); }
function spawnShock(){ EFFECTS.push({fn:'shock'}); }
function addShake(){}
function playerDie(){ EFFECTS.push({fn:'playerDie'}); }
function mountsFor(){ return null; }
// smallTarget is replaced wholesale: what a bomber picks is not what is under
// test here, only what happens once it is over what it picked.
var RAM_TARGET = null;
function smallTarget(e){ return RAM_TARGET; }
${consts.join('\n')}
${names.map(fn).join('\n')}
`;

const vm = require('vm');
const ctxObj = {console};
vm.createContext(ctxObj);
vm.runInContext(WORLD, ctxObj);
const run = (code)=>vm.runInContext(code, ctxObj);
const get = (name)=>vm.runInContext(name, ctxObj);
const set = (name, v)=>{ ctxObj[name] = v; };

let fails = 0;
function ok(label, cond){ console.log((cond?'  ok    ':'  FAIL  ')+label); if(!cond) fails++; }

// A destroyer sized ally, and a bomber placed relative to her hull.
const destroyer = ()=>({uid:'A1', img:'dehatshepsut', x:400, y:250, sc:1,
                        small:false, dead:false, side:'ally',
                        hp:6500, maxHp:6500, vy:0});
const bomber = (fac, x, y)=>({img:'bobakha', x:x, y:y, sc:1, type:'bomber',
                              faction:fac, side:'enemy', role:'attack', passT:0,
                              dead:false, warp:0, warpOut:0, hp:100, maxHp:100});

console.log('Who rams, and who does not');
ok('a Hammer of Light bomber does', run("ramsOnContact({type:'bomber',faction:'hol'})")===true);
ok('an NTF bomber does not',        run("ramsOnContact({type:'bomber',faction:'ntf'})")===false);
ok('a Shivan bomber does not',      run("ramsOnContact({type:'bomber',faction:'shivan'})")===false);
ok('a renegade bomber does not',    run("ramsOnContact({type:'bomber',faction:'renegade'})")===false);
ok('a Hammer of Light fighter does not, without being told',
   run("ramsOnContact({type:'fighter',faction:'hol'})")===false);
ok('a fighter briefed for it does', run("ramsOnContact({type:'fighter',faction:'hol',rammer:true})")===true);
ok('and so does a briefed fighter of any faction',
   run("ramsOnContact({type:'fighter',faction:'ntf',rammer:true})")===true);

console.log('\nContact is hull against hull, not centre against centre');
{
  // Sitting on her hull, well clear of her centre: this is the case that did
  // nothing before, because the distance to her centre is about 150.
  const t = destroyer();
  set('RAM_TARGET', t);
  set('allies', [t]);
  set('enemies', [bomber('hol', 550, 250)]);
  run('EFFECTS.length=0; tickRamming()');
  ok('a bomber over her bow goes up', get('enemies')[0].dead===true);
  ok('and she takes the damage', t.hp < 6500);
  ok('the hull was marked at the point of contact',
     get('EFFECTS').some(e=>e.fn==='hullHit'));
  ok('it explodes with the heavier profile, not the usual bomber death',
     get('EFFECTS').some(e=>e.fn==='expl' && e.kind==='corvette'));
}
{
  // Just past her stern: no overlap, so no hit.
  const t = destroyer();
  set('RAM_TARGET', t); set('allies',[t]);
  set('enemies', [bomber('hol', 400+210+20+10, 250)]);
  run('tickRamming()');
  ok('a bomber that misses her hull flies on', get('enemies')[0].dead===false);
}
{
  // Above her, horizontally lined up. A circular test would have fired here.
  const t = destroyer();
  set('RAM_TARGET', t); set('allies',[t]);
  set('enemies', [bomber('hol', 400, 250-75-12-10)]);
  run('tickRamming()');
  ok('a bomber passing over her, not through her, flies on',
     get('enemies')[0].dead===false);
}
{
  const t = destroyer();
  set('RAM_TARGET', t); set('allies',[t]);
  set('enemies', [bomber('ntf', 400, 250), bomber('shivan', 420, 250)]);
  run('tickRamming()');
  ok('an NTF bomber sitting on her hull does nothing', get('enemies')[0].dead===false);
  ok('nor does a Shivan one',                          get('enemies')[1].dead===false);
  ok('and she is untouched',                           t.hp===6500);
}
{
  // The player is not a ram target: being flown into without warning is not
  // kamikaze, it is an unfair hit.
  set('RAM_TARGET', get('player'));
  set('allies', []);
  set('enemies', [bomber('hol', 100, 250)]);
  run('tickRamming()');
  ok('the player is never rammed', get('enemies')[0].dead===false);
}

console.log('\nA ram course keeps the whole height of the field');
{
  // This is the fault that mechsim could not see: the spawn options, not the
  // movement. still belongs to the target, not to the attacker.
  const e = {img:'crmentu', x:820, y:120, sc:1, vy:2, dead:false, warp:0, rollT:null};
  set('_e', e);
  run("applySpawnOpts(_e, {capRam:0.05, still:true})");
  ok('still no longer pins a ram course to its spawn height',
     e.minY < e.y && e.maxY > e.y);
  ok('it still stops the up and down', e.vy===0);
  ok('and it reaches from under the bar to the bottom edge',
     e.minY===get('HUD_H')+10 && e.maxY===get('H')-10);
}
{
  const e = {img:'crmentu', x:600, y:200, sc:1, vy:2, dead:false, warp:0, rollT:null};
  set('_e', e);
  run("applySpawnOpts(_e, {still:true})");
  ok('a ship that is merely still is still pinned, as before',
     e.minY===e.y && e.maxY===e.y && e.vy===0);
}

console.log('\nThe ramming cruiser reaches its target from any height');
{
  let hit = 0; const missed = [];
  for(const startY of [60,120,180,250,320,400,460]){
    const t = {uid:'A1', img:'dehatshepsut', x:560, y:250, sc:1, small:false,
               dead:false, hp:6500, maxHp:6500, vy:0, minY:250, maxY:250};
    const e = {uid:'V1', img:'crmentu', x:820, y:startY, sc:1, vy:2,
               dead:false, warp:0, rollT:null};
    set('_e', e);
    run("applySpawnOpts(_e, {capRam:0.05, still:true})");
    set('allies', [t]); set('enemies', [e]);
    let done = false;
    for(let f=0; f<9000 && !done; f++){
      run('tickCapRam()');
      if(get('enemies').length===0) done = true;
    }
    if(done && t.hp < 6500) hit++; else missed.push(startY);
  }
  ok('it connects from all seven starting heights, spawn options included',
     hit===7, missed);
  if(missed.length) console.log('         missed from y=' + missed.join(', '));
}
{
  // Target gone mid approach. Without this it keeps a course to nothing and
  // sits on the left edge until the wave is over.
  const e = {uid:'V1', img:'crmentu', x:300, y:250, sc:1, capRam:0.05,
             noFlee:true, dead:false, warp:0, rollT:null};
  set('allies', []); set('enemies', [e]);
  run('tickCapRam()');
  ok('a ram course with nothing left to hit gives the course up', !e.capRam);
  ok('and is allowed to leave again', e.noFlee===false);
}

console.log('\n' + (fails ? fails+' FAILED' : 'all passed'));
process.exit(fails?1:0);
