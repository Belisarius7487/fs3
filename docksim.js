// Docking simulation. Pulls the REAL functions out of the logic file and
// runs them against a minimal world. Only the ship objects, the death of an
// ally and the tick order are stand-ins; every docking rule is the game's.
// Usage: node docksim.js hlp_shooter_v102_logic.html hlp_mounts_final.json
const fs = require('fs');
const html = fs.readFileSync(process.argv[2] || 'hlp_shooter_v102_logic.html', 'utf8');
const src = html.match(/<script[^>]*>([\s\S]*)<\/script>/)[1];
const MOUNTS = JSON.parse(fs.readFileSync(process.argv[3] || 'hlp_mounts_final.json', 'utf8'));

// Brace matching that skips strings and comments.
function block(from){
  let i = src.indexOf('{', from), d = 0;
  for(; i < src.length; i++){
    const ch = src[i], nx = src[i+1];
    if(ch === '/' && nx === '/'){ i = src.indexOf('\n', i); continue; }
    if(ch === '/' && nx === '*'){ i = src.indexOf('*/', i) + 1; continue; }
    if(ch === '"' || ch === "'" || ch === '`'){
      const q = ch; i++;
      while(src[i] !== q){ if(src[i] === '\\') i++; i++; }
      continue;
    }
    if(ch === '{') d++;
    else if(ch === '}'){ d--; if(d === 0) return i + 1; }
  }
  throw new Error('unbalanced at ' + from);
}
function fn(name){
  const at = src.indexOf('function ' + name + '(');
  if(at < 0) throw new Error('missing function ' + name);
  return src.slice(at, block(at));
}
function constObj(name){
  const at = src.indexOf('const ' + name + ' =');
  return src.slice(at, block(at)) + ';';
}

const NAMES = ['dockPoint','dockPointN','tickRiders','dockOffset','unitAlive','idPending','cargoLost','claimCargo',
  'leaveEmpty','cargoStillWanted','carryCargo','cargoDockUp','cargoSeat','dropCargo','tickCarry','tickDocking',
  'tickCrossGuards','killEnemy','byId','evSeen','mountsFor','hullClass',
  'liveThreatCount','scriptUnitsResolved','spriteFacing','needsFlip','faceTurn','tickFaceTurns',
  // F99 (v283): docking from the models' dock data (31_dock.js)
  'dkList','dkHas','dkHalf','dkIsCargo','dkInPlane','dkPick','dkRideIndex','dkRight','dkPose','dkGrid',
  'dkClear','dkMeet','dkDepthOf','dkMustRoll','dkNeedsUpsideDown','dkPlanFor','dkPlaceCargo','dkSeat',
  'dkApproach','dkCastOff','dkCastOffStep','dkPairInfo'];
// their constants, as the game has them
const DK_CONSTS = (src.match(/^(?:const|let) (?:DK_\w+|DOCK_ROLL_STEPS|FACE_TURN_STEPS)\b.*$/mg) || []).join('\n');

const world = `
let wave=0, enemies=[], allies=[], SUB_MSGS=[], EV_DOCK={}, EV_SEEN={}, EV_HELD={}, EV_LEFT={}, EV_TAKEN={}, EV_EMPTY={}, spawnQ=[];
let protSaved=0, protLost=0, guardLost=false, guardGone=false, crossDone=0, crossTotal=0;
let score=0, bossAlive=false, bossSlain=false, expl=0;
const W=800, H=500, HUD_H=44, DOCK_SPD=0.55, DOCK_NEAR=22;
const MW=W, MH=H, FIELD_K=1, TEMPO_K=1, CAM_BASE_Z=1, WX0=0, WX1=W, WY0=54, WY1=H, SIZE_UPM=3.75, FIELD_CX=W/2, FIELD_CY=(54+H)/2; const CAM={x:W/2, y:(54+H)/2, z:1, zt:1, over:false}; function camSees(){ return true; } function camHalfW(){ return W/2; } function camHalfH(){ return (H-54)/2; } function w2sX(x){ return x; } function w2sY(y){ return y; } function s2wX(x){ return x; } function s2wY(y){ return y; } function camFollow(){} function camSnap(){} function mouseTick(){} function worldSet(){} function worldForWave(){} function mouseAt(p){ if(typeof MOUSE!=="undefined"){ MOUSE.x=p.x; MOUSE.y=p.y; } } function mouseHold(){ if(typeof MOUSE!=='undefined' && typeof player!=='undefined'){ MOUSE.x=player.x; MOUSE.y=player.y; } }  // v208: the world is the old field in the sims; v209: tempo and zoom 1
const MOUNTS = ${JSON.stringify(MOUNTS)};
const IMGS = { frbast:{width:60,height:26}, fcvc3:{width:30,height:22}, frasmodeus:{width:80,height:30},
  trisis:{width:60,height:24}, dehatshepsut:{width:391,height:150} };
function statKill(){} function maybeDropTicket(){} function payShieldPts(){}
// The practice log is not what is tested here.
function plogKill(){} function plogRearm(){} function plogSec(){} function plogHit(){} function plogPick(){} function plogSrc(){} function plogLoss(){} function plogEvent(){} function plogName(){ return ''; } function plogAllyLost(){} function plogDeath(){} function plogSync(){}
function triggerExpl(){ expl++; }
// The long death of a capital ship (v183) is not what is tested here: they go at once.
function startDeathRoll(){ return false; }
${DK_CONSTS}
${NAMES.map(fn).join('\n')}
${constObj('SCRIPT_WAVES')}
`;
const TICK_HZ = 100;
const api = new Function('TICK_HZ', world + `
return { get enemies(){return enemies;}, set enemies(v){enemies=v;},
  get allies(){return allies;}, set allies(v){allies=v;},
  get protSaved(){return protSaved;}, get protLost(){return protLost;},
  get expl(){return expl;}, SUB_MSGS, EV_SEEN, EV_HELD, EV_LEFT, EV_TAKEN, spawnQ,
  reset(){ enemies=[]; allies=[]; SUB_MSGS.length=0; for(const k in EV_DOCK) delete EV_DOCK[k]; for(const k in EV_EMPTY) delete EV_EMPTY[k];
    for(const k in EV_SEEN) delete EV_SEEN[k]; for(const k in EV_HELD) delete EV_HELD[k];
    for(const k in EV_LEFT) delete EV_LEFT[k]; for(const k in EV_TAKEN) delete EV_TAKEN[k];
    spawnQ.length=0; protSaved=0; protLost=0; guardLost=false; expl=0; },
  tickDocking, tickCrossGuards, tickCarry, killEnemy, dockPoint, cargoSeat, liveThreatCount,
  dockPointN, dkRideIndex, dkSeat, dkHas, dkPose, dkPairInfo, dkPlanFor, dkPick, dkPlaceCargo, needsFlip, IMGS,
  hullClassFn: hullClass, setWave(w){ wave = w; DK_PLAN = {wave: null, g: {}}; },
  scriptUnitsResolved, SCRIPT_WAVES };`)(TICK_HZ);

// ── Stand-ins ─────────────────────────────────────────────────
let uidc = 0;
function freighter(uid, x, y, dockTo, side){
  const o = {uid, type:'freighter', img:'frbast', x, y, sc:1, flip:false, warp:0, dead:false,
    guard:true, dockTo, crossAfter:0.38, hp:100, maxHp:100, _n:++uidc};
  api.EV_SEEN[uid] = true;
  (side === 'enemy' ? api.enemies : api.allies).push(o); return o;
}
function container(uid, x, y, side){
  const o = {uid, type:'container', img:'fcvc3', x, y, sc:1, flip:side==='enemy', warp:0,
    dead:false, guard:side!=='enemy', pickup:true, hp:60, maxHp:60, pts:40, _n:++uidc};
  api.EV_SEEN[uid] = true;
  (side === 'enemy' ? api.enemies : api.allies).push(o); return o;
}
// Mirrors the death branch of updateAllies(): splice, and count a guard.
function allyDies(a){
  a.dead = true; a.hp = 0;
  const i = api.allies.indexOf(a); if(i >= 0) api.allies.splice(i, 1);
  if(a.guard){ /* updateAllies: protLost++ */ api._lostByGuard = (api._lostByGuard||0) + 1; }
}
// tick order as in update(): docking ... crossing ... movement, then carry
let shared = 0, lag = 0;
function step(){
  api.tickDocking();
  api.tickCrossGuards();
  api.tickCarry();
  // no two freighters on one container, ever
  const seen = new Map();
  for(const f of api.enemies.concat(api.allies)){
    const c = f.dockedTo || f.dockRes;
    if(!c) continue;
    if(seen.has(c)) shared++;
    seen.set(c, f);
  }
  // carried cargo sits in its seat at her dock point, with no lag after
  // moving. F97 (v281): the seat, not the container's own dock point - the
  // container is turned to meet hers, as in FreeSpace (Silvio).
  for(const f of api.allies) if(f.dockedTo && !f.dockedTo.dead){
    const a = api.cargoSeat(f, f.dockedTo), b = f.dockedTo;
    lag = Math.max(lag, Math.hypot(a.x-b.x, a.y-b.y));
  }
}
function run(n, hook){ for(let t = 0; t < n; t++){ if(hook) hook(t); step(); } }
const lost = () => api.protLost + (api._lostByGuard||0);
let pass = 0, fail = 0;
function check(name, ok, info){
  console.log((ok ? '  ok    ' : '  FAIL  ') + name + (info ? '   (' + info + ')' : ''));
  ok ? pass++ : fail++;
}
function begin(title){ api.reset(); api._lostByGuard = 0; shared = 0; lag = 0; console.log('\n' + title); }
const msgs = t => api.SUB_MSGS.filter(m => m.txt === t).length;

// ── 1. Equal numbers ──────────────────────────────────────────
begin('1  two freighters, two containers');
container('C1', 150, 180); container('C1', 170, 320);
freighter('F1', -40, 200, 'C1'); freighter('F1', -40, 300, 'C1');
run(6000);
check('both delivered', api.protSaved === 2 && msgs('DELIVERED') === 2, 'saved ' + api.protSaved);
check('nothing lost', lost() === 0);
check('never two on one container', shared === 0);
check('cargo sits exactly on the dock point', lag < 0.01, 'max gap ' + lag.toFixed(4) + ' px');

// ── 2. More freighters than containers ────────────────────────
begin('2  three freighters, two containers');
container('C1', 150, 180); container('C1', 170, 320);
freighter('F1', -40, 200, 'C1'); freighter('F1', -60, 250, 'C1'); freighter('F1', -80, 300, 'C1');
run(6000);
check('two delivered, one left empty', api.protSaved === 2 && msgs('LEFT EMPTY') === 1,
      'saved ' + api.protSaved + ', empty ' + msgs('LEFT EMPTY'));
check('never two on one container', shared === 0);
check('wave not held (no freighter left)', api.allies.length === 0, api.allies.length + ' left');

// ── 3. More containers than freighters ────────────────────────
begin('3  two freighters, three containers (raw, without the count fix)');
container('C1', 150, 150); container('C1', 170, 250); container('C1', 190, 350);
freighter('F1', -40, 200, 'C1'); freighter('F1', -40, 300, 'C1');
run(6000);
check('two delivered', api.protSaved === 2);
check('third one left behind and counted once', msgs('CARGO LEFT BEHIND') === 1 && lost() === 1);
check('left-behind container is scenery, no longer a guard',
      api.allies.every(c => c.scenery && !c.guard));
check('result would read PARTIAL 2/3', api.protSaved === 2 && lost() === 1);

// ── 4. Carrier dies with cargo ────────────────────────────────
begin('4  carrier destroyed while carrying');
const c4 = container('C1', 150, 200); const f4 = freighter('F1', -40, 250, 'C1');
run(6000, t => { if(f4.dockedTo && f4.x > 400 && !f4.dead) allyDies(f4); });
check('cargo destroyed with it', c4.dead && api.allies.indexOf(c4) < 0 && api.expl === 1);
check('counted once (the freighter), not twice', lost() === 1, 'lost ' + lost());
check('not reported as left behind', msgs('CARGO LEFT BEHIND') === 0);

// ── 5. Cargo dies before docking (allied container) ───────────
begin('5  allied container destroyed before docking');
const c5 = container('C1', 300, 180); container('C1', 320, 320);
const f5 = freighter('F1', -40, 200, 'C1'); freighter('F1', -40, 300, 'C1');
run(6000, t => { if(t === 100) allyDies(f5.dockRes); });
check('its freighter leaves empty, does not take the other', msgs('LEFT EMPTY') === 1 && api.protSaved === 1,
      'saved ' + api.protSaved);
check('never two on one container', shared === 0);
check('counted once', lost() === 1, 'lost ' + lost());

// ── 5b. Enemy container shot by the player (M023) ─────────────
begin('5b scanned enemy container shot before pickup');
const c5b = container('C1', 300, 200, 'enemy'); container('C1', 320, 330, 'enemy');
freighter('F1', -40, 200, 'C1'); freighter('F1', -40, 300, 'C1');
run(6000, t => { if(t === 100) api.killEnemy(c5b, null, true, false); });
check('one delivered, one empty', api.protSaved === 1 && msgs('LEFT EMPTY') === 1);
check('counted once', lost() === 1, 'lost ' + lost());
check('no enemy container holds the wave', api.liveThreatCount() === 0, 'threats ' + api.liveThreatCount());

// ── 6. Freighter dies on the way ──────────────────────────────
begin('6  freighter destroyed before docking');
container('C1', 300, 200); const f6 = freighter('F1', -40, 250, 'C1');
run(6000, t => { if(t === 100) allyDies(f6); });
check('container released as left behind', msgs('CARGO LEFT BEHIND') === 1);
check('counted once (the freighter), not twice', lost() === 1, 'lost ' + lost());

// ── 7. Freighter arrives before its container ─────────────────
begin('7  freighter in the field, container still queued');
freighter('F1', -40, 250, 'C1'); api.EV_SEEN['C1'] = true;
api.spawnQ.push({uid:'C1', type:'protect', spr:'fcvc3'});
run(50);
check('waits instead of leaving empty', msgs('LEFT EMPTY') === 0 && msgs('NO CARGO') === 0);

// ── 8. Freighters held back for an event (M023) ───────────────
begin('8  freighters held for an event');
container('C1', 300, 200, 'enemy');
api.EV_HELD['F1'] = [{uid:'F1', type:'protect', dockTo:'C1'}];
run(50);
check('container is not declared left behind', msgs('CARGO LEFT BEHIND') === 0);

// ── 9. M027: three transports, one destroyer ──────────────────
begin('9  transports docking at a destroyer one after another');
const d9 = {uid:'A1', type:'destroyer', img:'dehatshepsut', x:520, y:300, sc:1, flip:false,
            warp:0, dead:false, hp:2000, maxHp:6500};
api.allies.push(d9); api.EV_SEEN['A1'] = true;
const ts = [];
let docks = 0, gap = 0;
run(9000, t => {
  if(t === 0 || (ts.length && ts.length < 3 && ts[ts.length-1].crossing && ts.length === docks))
    ts.push(Object.assign(freighter('T' + (ts.length+1), -40, 200, 'A1'), {img:'trisis', guard:true}));
  const last = ts[ts.length-1];
  if(last && last.crossing && !last._c){ last._c = 1; docks++;
    const a = api.dockPoint(last), b = api.dockPoint(d9); gap = Math.max(gap, Math.hypot(a.x-b.x, a.y-b.y)); }
});
check('all three docked', docks === 3, docks + ' docked');
check('dock points meet', gap <= 1.01, 'gap ' + gap.toFixed(2) + ' px');
check('nothing reported as cargo', msgs('NO CARGO') === 0 && msgs('LEFT EMPTY') === 0);

// ── 10. Freighter count from the mission data ─────────────────
begin('10 freighter count follows the containers');
const cnt = (m, id) => api.scriptUnitsResolved(api.SCRIPT_WAVES[m]).find(u => u.id === id);
// v253: M9 is an FS1 mission now; M3's freighters each fetch one container.
check('M003: one container, one freighter each', cnt(3, 'F1').n === 1 && cnt(3, 'C1').pickup);
check('M023: three containers, now three freighters', cnt(23, 'F1').n === 3 && cnt(23, 'C1').pickup,
      'was ' + api.SCRIPT_WAVES[23].u.find(u => u.id === 'F1').n);
check('M027: transports unchanged', cnt(27, 'T1').n === 1 && !cnt(27, 'A1').pickup);
check('mission data itself untouched', api.SCRIPT_WAVES[23].u.find(u => u.id === 'F1').n === 2);

// ── 11. Cargo riding on a freighter (v253, Shieldbreaker) ─────
begin('11 cargo rides on its freighter, dies or leaves with her');
function rider(uid, ride, slot, side){
  const o = container(uid, 0, 0, side); o.rideId = ride; o.rideSlot = slot; o.pickup = false; return o;
}
{
  const f = freighter('F1', 300, 250, null, 'enemy'); f.img = 'frasmodeus'; f.dockTo = null;
  const a = rider('K1', 'F1', 0, 'enemy'), b = rider('K2', 'F1', 1, 'enemy');
  run(1);
  // F99 (v283): with the models' dock data a rider sits on her cargo dock
  // for its slot (dkRideIndex: those towards the viewer first), dock on
  // dock (dkSeat) - no longer on her first dock point of the old,
  // hand-placed list. Its own dock lies on hers, out the way hers faces.
  const seatOk = (c, slot) => { const s = api.dkSeat(f, c, api.dkRideIndex(f, slot)); return Math.abs(c.x - s.x) < 0.01 && Math.abs(c.y - s.y) < 0.01; };
  const onLine = (c, slot) => { const P = api.dkPose(f, api.dkRideIndex(f, slot)), q = api.dkPose(c, 0);
    return Math.abs((q.x - P.x)*P.vy - (q.y - P.y)*P.vx) < 0.5; };
  check('first rider on her first cargo dock, above her', seatOk(a, 0) && onLine(a, 0) && a.y < f.y, a.x.toFixed(1) + ',' + a.y.toFixed(1));
  check('second rider on her second dock point', Math.abs(b.x - a.x) > 20, 'gap ' + Math.abs(b.x - a.x).toFixed(1));
  f.x += 50; run(1);
  check('riders move with her, no lag', seatOk(a, 0) && onLine(a, 0));
  // she is destroyed: the cargo goes up with her
  f.dead = true; api.enemies.splice(api.enemies.indexOf(f), 1);
  const e0 = api.expl; run(1);
  check('destroyed: both riders go up', a.dead && b.dead && api.expl - e0 === 2, 'expl ' + (api.expl - e0));
  check('destroyed: not counted as left', !api.EV_LEFT.K1 && !api.EV_LEFT.K2);
}
{
  const f = freighter('F2', 300, 250, null, 'enemy'); f.img = 'frasmodeus'; f.dockTo = null;
  const a = rider('K3', 'F2', 0, 'enemy');
  run(1);
  f.warpOut = 50; f.warpMax = 160; run(1);
  check('her jump: the rider jumps on the same clock', a.warpOut === 50);
  api.EV_LEFT.F2 = true; f.dead = true; api.enemies.splice(api.enemies.indexOf(f), 1);
  const e0 = api.expl; run(1);
  check('jumped out: rider leaves with her, no blast', a.dead && api.expl === e0 && api.EV_LEFT.K3 && api.enemies.indexOf(a) < 0);
}
{
  const f = freighter('T1', 300, 250, null, 'ally'); f.img = 'frasmodeus'; f.dockTo = null;
  const a = rider('K4', 'T1', 0, 'ally');
  run(1);
  const s4 = api.dkSeat(f, a, api.dkRideIndex(f, 0));
  check('a rider of ours sits on her too', Math.abs(a.x - s4.x) < 0.01 && Math.abs(a.y - s4.y) < 0.01);
}

// ── 12. F99 (v283): every dock of missions 1-18 against the real hulls ──
// Silvio (24.10.2026): docking from the models' own dock data, for every
// mission. A container must sit on its freighter's dock - between the
// Poseidon's arms, between the Chronos' end blocks - not rest on top of
// them: what keeps it off her dock (dkMeet, from both hulls' height maps)
// may be at most half its own height. Sizes as the game draws them.
begin('12 F99: every container fits its freighter (missions 1-18)');
const SIZE = new Function('hullClass', [
  (src.match(/^const HULL_LEN = .*$/m) || [''])[0], (src.match(/^const SIZE_KEY_MUL = .*$/m) || [''])[0],
  (src.match(/^const SIZE_DRAW_CLASS_MUL = .*$/m) || [''])[0], (src.match(/^const CAP_L0 = .*$/m) || [''])[0],
  'const SIZE_UPM = 3.75;', fn('hullWidth'), 'return hullWidth;'].join('\n'));
const realWidth = SIZE(api.hullClassFn);
function realSized(k){ if(!api.IMGS[k] || !api.IMGS[k]._real) api.IMGS[k] = {width: realWidth(k), height: realWidth(k)/3, _real: true}; }
const pairs = new Map();
for(let m = 1; m <= 18; m++){
  const d = api.SCRIPT_WAVES[m]; if(!d) continue;
  for(const u of d.u){
    if(!u.dockTo || u.dockBeside != null || !u.spr) continue;
    for(const t of d.u.filter(x => x.id === u.dockTo && x.c === 'fc' && x.spr))
      pairs.set(u.spr + '|' + t.spr + '|' + (t.big || 1), {m, f: u.spr, c: t.spr, big: t.big || 1});
  }
  for(const u of d.u){
    if(!u.ride || !u.spr) continue;
    const f = d.u.find(x => x.id === u.ride && x.spr);
    if(f) pairs.set(f.spr + '|' + u.spr + '|' + (u.big || 1), {m, f: f.spr, c: u.spr, big: u.big || 1, ride: true});
  }
}
for(const q of pairs.values()){
  realSized(q.f); realSized(q.c);
  if(!api.dkHas({img: q.f}) || !api.dkHas({img: q.c})){ check('M' + q.m + ' ' + q.f + ' + ' + q.c + ': dock data from the models', false, 'run tools/pof/mkdocks.py'); continue; }
  const r = api.dkPairInfo(q.f, q.c, q.big);
  // the largest it may be, for the message (from small up: the first that no longer sits)
  let lo = 0;
  for(let b = 0.05; b <= 6; b += 0.05){ const x = api.dkPairInfo(q.f, q.c, b); if(x.gap <= 0.5*x.height) lo = b; else break; }
  check('M' + q.m + ' ' + q.f + ' + ' + q.c + (q.big !== 1 ? ' x' + q.big : '') + (q.ride ? ' (rides)' : '') + ': sits on her dock',
        r.gap <= 0.5*r.height, 'off her dock ' + r.gap.toFixed(1) + ' of ' + r.height.toFixed(1) + (r.upsideDown ? ', upside down' : '') +
        (r.thin < 1 ? ', drawn ' + Math.round(r.thin*100) + '% deep' : '') +
        ', at most x' + lo.toFixed(2));
}

// ── 13. F99 (v283): the approach, phase by phase ──────────────────
// Silvio (24.10.2026, F99): the Chronos stops under the container and
// rises into it; the Poseidon's arms must not lie behind it on the way.
// She drives up only at a height where nothing touches, then slides in
// straight along the dock path; from the slide on the container is drawn
// with her (f3dCargoHost reads _inBy).
function approach(fkey, ckey, big, fromLeft){
  begin('13 F99: ' + fkey + ' takes a ' + ckey + (big !== 1 ? ' x' + big : ''));
  realSized(fkey); realSized(ckey);
  api.SCRIPT_WAVES[99] = {u: [{id: 'C9', c: 'fc', spr: ckey, x: 500, y: 300, big: big},
                              {id: 'F9', c: 'fr', spr: fkey, x: fromLeft ? 100 : 900, y: 300, dockTo: 'C9'}]};
  api.setWave(99);
  const c = container('C9', 500, 300); c.img = ckey; c.sc = big; c.flip = false; c.uid = 'C9';
  api.dkPlaceCargo(c, 'C9');
  const f = freighter('F9', fromLeft ? 100 : 900, 300, 'C9'); f.img = fkey; f.crossAfter = 0;
  f.flip = api.needsFlip(fkey, !fromLeft); f.dockHold = 300; f.holdT = null;
  const fw = api.IMGS[fkey].width/2, cw = api.IMGS[ckey].width*big/2;
  let phases = [], bad = 0, slideDx = 0, slideDir = 0, inByEarly = false, inByLate = false, last = null;
  for(let t = 0; t < 12000 && !f.dockedTo; t++){
    const k = f._dk, ph = k ? k.ph : '-';
    if(phases[phases.length-1] !== ph) phases.push(ph);
    // lengthwise over it: at least her standoff away along the dock's way
    if(k && ph === 'go' && Math.abs(f.x - c.x) < fw + cw){
      const B = api.dkPose(c, k.iB), A = api.dkPose(f, k.iA);
      const sep = (A.x - B.x)*B.vx + (A.y - B.y)*B.vy;
      if(sep < k.stand - 2.5) bad++;
    }
    if(ph === 'in' && last && last.ph === 'in'){ slideDx = Math.max(slideDx, Math.abs(f.x - last.x)); slideDir += f.y - last.y; }
    if(ph === 'go' && c._inBy) inByEarly = true;
    if(ph === 'in' && c._inBy === f) inByLate = true;
    last = {x: f.x, y: f.y, ph: ph};
    step();
  }
  check('she docks: go, then in, then on', phases.join(' ').indexOf('go in on') >= 0 && !!f.dockedTo, phases.join(' '));
  check('never over it at a height where they touch', bad === 0, bad + ' steps');
  check('the slide is straight along the dock path', slideDx < 0.01, 'sideways ' + slideDx.toFixed(3));
  check('drawn with her from the slide on, not before', inByLate && !inByEarly);
  return {slideDir, f, c};
}
let a1 = approach('frchronos', 'fcvc3', 1, true);
check('the Chronos rises into it', a1.slideDir < -1, 'moved ' + a1.slideDir.toFixed(1));
let a2 = approach('frposeidon', 'fcvc3', 1, true);
check('the Poseidon sinks onto it, the container upside down', a2.slideDir > 1 && a2.c.rollC === -1,
      'moved ' + a2.slideDir.toFixed(1) + ', container ' + (a2.c.rollC === -1 ? 'upside down' : 'upright') + (a2.f._dk && a2.f._dk.roll ? ', she rolled' : ''));
let a3 = approach('frmaat', 'fcvac4', 1, false);
check('the Ma\'at rises into it', a3.slideDir < -1, 'moved ' + a3.slideDir.toFixed(1));

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
