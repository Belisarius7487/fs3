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
               'applySpawnOpts', 'halfW', 'halfH',
               'spriteBox', 'hullBox', 'hullsTouch', 'hullDepth', 'hullsBite'];
const consts = [
  decl(/const RAM_PCT_CAPITAL = [\d.]+;/),
  decl(/const RAM_PCT_BOMBER  = [\d.]+;/),
  decl(/const RAM_PCT_FIGHTER = [\d.]+;/),
  decl(/const RAM_OVERLAP = \d+;/),
  decl(/const CAP_RAM_BITE = [\d.]+;/),
  decl(/const CAP_RAM_CLIMB = [\d.]+;/),
  decl(/const SPR_BOX = \{\};/)
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
// The masks the real getMask would build, with a transparent margin around
// the ship the way an actual sprite file has one. MASK_INSET is the share of
// the image taken up by that margin on each side.
var MASK_INSET = 0.2;
function getMask(key){
  const img = IMGS[key];
  if(!img) return null;
  const w = Math.max(2, Math.round(img.width/5)), h = Math.max(2, Math.round(img.height/5));
  const bits = new Uint8Array(w*h);
  const x0 = Math.round(w*MASK_INSET), x1 = w-1-Math.round(w*MASK_INSET);
  const y0 = Math.round(h*MASK_INSET), y1 = h-1-Math.round(h*MASK_INSET);
  for(let y=y0;y<=y1;y++) for(let x=x0;x<=x1;x++) bits[y*w+x] = 1;
  return {w:w, h:h, bits:bits};
}
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
// Call one of the box predicates on two ships held outside the context.
const run2 = (a, b, name)=>{ ctxObj._a = a; ctxObj._b = b;
  return vm.runInContext(name+'(_a, _b, '+(name==='hullsBite'?'CAP_RAM_BITE':name==='hullsTouch'?'RAM_OVERLAP':'')+')', ctxObj); };
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

console.log('\nContact is the visible hull, not the image rectangle');
// The image is 420 by 150 and the ship inside it fills the middle 60 per cent,
// so her visible hull reaches 126 points either side of her centre and 45
// above and below. Between 126 and 210 there is nothing but transparent file.
{
  const t = destroyer();
  const b = bomber('hol', 400+100, 250);
  set('RAM_TARGET', t); set('allies', [t]);
  set('enemies', [b]);
  run('EFFECTS.length=0; tickRamming()');
  // Hold the bomber here rather than reading it back out of the list: a
  // successful ram takes it out of the list, which is the point.
  ok('a bomber on her bow goes up', b.dead===true);
  ok('and she takes the damage', t.hp < 6500);
  ok('the hull was marked at the point of contact',
     get('EFFECTS').some(e=>e.fn==='hullHit'));
  ok('it explodes with the heavier profile, not the usual bomber death',
     get('EFFECTS').some(e=>e.fn==='expl' && e.kind==='corvette'));
  // And it leaves the field. ramBlast sets dead and hp=0, and the reaper only
  // takes ships that are hp<=0 AND NOT dead, so anything left behind here is a
  // ghost: no chevron, not shootable, not counted, still flying and firing.
  ok('and it is taken off the field, not left behind as a ghost',
     get('enemies').length===0);
}
{
  // This is the one that used to go off for no visible reason: inside her
  // image, outside her ship.
  const t = destroyer();
  set('RAM_TARGET', t); set('allies', [t]);
  set('enemies', [bomber('hol', 400+170, 250)]);
  run('tickRamming()');
  ok('a bomber in the transparent margin beside her flies on',
     get('enemies')[0].dead===false);
  ok('and she is untouched', t.hp===6500);
}
{
  const t = destroyer();
  set('RAM_TARGET', t); set('allies', [t]);
  set('enemies', [bomber('hol', 400, 250-60)]);
  run('tickRamming()');
  ok('nor does one in the margin above her', get('enemies')[0].dead===false);
}
{
  const t = destroyer();
  set('RAM_TARGET', t); set('allies', [t]);
  set('enemies', [bomber('hol', 400+260, 250)]);
  run('tickRamming()');
  ok('a bomber clear of her image entirely flies on', get('enemies')[0].dead===false);
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
{
  // The measurement itself, so the reason is checked and not only its effect.
  const b = run("spriteBox('dehatshepsut')");
  ok('the visible hull is narrower than the image', b.hw < 210 && b.hw > 100);
  ok('and shorter than it', b.hh < 75 && b.hh > 30);
  ok('the box is measured once and then kept', run("SPR_BOX['dehatshepsut'] !== undefined")===true);
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

console.log('\nNothing that blows itself up stays in the list');
{
  // The same guarantee for the ramming capital ship, which has always done it
  // right, so the two cannot drift apart again.
  const t = {uid:'A1', img:'dehatshepsut', x:400, y:250, sc:1, small:false,
             dead:false, hp:6500, maxHp:6500, vy:0};
  const e = {uid:'V1', img:'crmentu', x:400, y:250, sc:1, capRam:0.9,
             dead:false, warp:0, rollT:null, minY:64, maxY:490};
  set('allies', [t]); set('enemies', [e]);
  run('tickCapRam()');
  ok('the ramming cruiser leaves the field on impact', get('enemies').length===0);
}
{
  // A bomber that has NOT hit anything must of course stay.
  const t = destroyer();
  set('RAM_TARGET', t); set('allies', [t]);
  set('enemies', [bomber('hol', 400+260, 250)]);
  run('tickRamming()');
  ok('one that has hit nothing stays where it is', get('enemies').length===1);
}

console.log('\nA ram course has to be buried, not brushed');
{
  // Both boxes are rectangles around ships that are not rectangular, so their
  // corners meet well before the ships do. The cruiser is 200 by 120, its
  // visible hull 120 by 72, so half its width is 60 points.
  const t = {uid:'A1', img:'dehatshepsut', x:400, y:250, sc:1, small:false,
             dead:false, hp:6500, maxHp:6500, vy:0};
  const e = {uid:'V1', img:'crmentu', x:400, y:250, sc:1, capRam:0.9,
             dead:false, warp:0, rollT:null, minY:64, maxY:490};
  ok('dead centre on her counts', run2(e, t, 'hullsBite')===true);
  // Just inside the boxes: they overlap, but only barely.
  e.x = 400 + 126 + 60 - 12;
  ok('boxes that merely touch at the edge do not', run2(e, t, 'hullsBite')===false);
  ok('though they do touch', run2(e, t, 'hullsTouch')===true);
  // Far enough in that it is standing in her hull.
  e.x = 400 + 126;
  ok('standing in her hull counts', run2(e, t, 'hullsBite')===true);
}
{
  // The depth is what the rule reads, so it is worth checking directly.
  const t = {img:'dehatshepsut', x:400, y:250, sc:1};
  const e = {img:'crmentu', x:400, y:250, sc:1};
  const d = run2(e, t, 'hullDepth');
  ok('two hulls on the same spot overlap by both half widths',
     Math.abs(d.x - (126+60)) < 2);
  ok('and by both half heights', Math.abs(d.y - (45+36)) < 2);
}

console.log('\nA ram course does not break off its run');
// flySmall sets passT once it is within ATTACK_BREAK and then flies straight
// through. Both the contact test and the yellow chevron want passT to be zero,
// so a rammer that breaks off loses its marking exactly when it matters and
// cannot register the impact. flySmall is too entangled to run here, so the
// guard is checked where it stands.
ok('the break off is skipped for a ram course',
   /else if\(d<ATTACK_BREAK && !ramsOnContact\(e\)\)/.test(src));
ok('and it is still there for everyone else',
   /e\.passT=ATTACK_PASS/.test(src));

console.log('\nNothing but the ram course moves a ram course');
// This is the check that was missing. ramsim ran tickCapRam on its own and
// reported seven out of seven while the cruiser was visibly missing in the
// game, because tickEnemies moves capital ships as well and moved it faster
// than the ram course could steer. tickEnemies is far too large to run here,
// so what is checked is that it stands aside: the station keeping and the
// patrol drift have to sit behind a capRam guard in both capital branches.
ok('the cruiser branch stands aside for a ram course',
   /if\(!e\.capRam\)\{[\s\S]{0,240}?e\.x=Math\.max\(e\.targetX,e\.x-0\.8\)/.test(src));
ok('and so does the corvette and destroyer branch',
   /if\(!e\.capRam\)\{[\s\S]{0,240}?e\.x=Math\.max\(e\.targetX,e\.x-0\.6\)/.test(src));
{
  // capRam has to be the speed itself now, so a step has to be worth it.
  const t = {uid:'A1', img:'dehatshepsut', x:400, y:250, sc:1, small:false,
             dead:false, hp:6500, maxHp:6500, vy:0};
  const e = {uid:'V1', img:'crmentu', x:800, y:250, sc:1, capRam:0.9,
             dead:false, warp:0, rollT:null, minY:64, maxY:490};
  set('allies', [t]); set('enemies', [e]);
  const x0 = e.x;
  run('tickCapRam()');
  ok('one step covers capRam points, not a fraction of somebody else\'s',
     Math.abs((x0 - e.x) - 0.9) < 0.01);
}
{
  // And the mission has to hand it a speed a ship can travel at. 0.05 only
  // ever worked because the station keeping was doing the real moving.
  const m = src.match(/\{id:'V1'[^}]*capRam:([\d.]+)/);
  ok('mission 28 gives the cruiser a real speed', !!m && parseFloat(m[1]) >= 0.5);
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
