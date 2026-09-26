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

const NAMES = ['dockPoint','dockOffset','unitAlive','idPending','cargoLost','claimCargo',
  'leaveEmpty','cargoStillWanted','carryCargo','dropCargo','tickCarry','tickDocking',
  'tickCrossGuards','killEnemy','byId','evSeen','mountsFor','hullClass',
  'liveThreatCount','scriptUnitsResolved'];

const world = `
let enemies=[], allies=[], SUB_MSGS=[], EV_DOCK={}, EV_SEEN={}, EV_HELD={}, EV_LEFT={}, spawnQ=[];
let protSaved=0, protLost=0, guardLost=false, guardGone=false, crossDone=0, crossTotal=0;
let score=0, bossAlive=false, bossSlain=false, expl=0;
const W=800, H=500, HUD_H=44, DOCK_SPD=0.55, DOCK_NEAR=22;
const MOUNTS = ${JSON.stringify(MOUNTS)};
const IMGS = { frbast:{width:60,height:26}, fcvc3:{width:30,height:22},
  trisis:{width:60,height:24}, dehatshepsut:{width:391,height:150} };
function statKill(){} function maybeDropTicket(){}
function triggerExpl(){ expl++; }
${NAMES.map(fn).join('\n')}
${constObj('SCRIPT_WAVES')}
`;
const TICK_HZ = 100;
const api = new Function('TICK_HZ', world + `
return { get enemies(){return enemies;}, set enemies(v){enemies=v;},
  get allies(){return allies;}, set allies(v){allies=v;},
  get protSaved(){return protSaved;}, get protLost(){return protLost;},
  get expl(){return expl;}, SUB_MSGS, EV_SEEN, EV_HELD, spawnQ,
  reset(){ enemies=[]; allies=[]; SUB_MSGS.length=0; for(const k in EV_DOCK) delete EV_DOCK[k];
    for(const k in EV_SEEN) delete EV_SEEN[k]; for(const k in EV_HELD) delete EV_HELD[k];
    spawnQ.length=0; protSaved=0; protLost=0; guardLost=false; expl=0; },
  tickDocking, tickCrossGuards, tickCarry, killEnemy, dockPoint, liveThreatCount,
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
  // carried cargo: both dock points meet, with no lag after moving
  for(const f of api.allies) if(f.dockedTo && !f.dockedTo.dead){
    const a = api.dockPoint(f), b = api.dockPoint(f.dockedTo);
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
check('M009: two containers, two freighters', cnt(9, 'F1').n === 2 && cnt(9, 'C1').pickup);
check('M023: three containers, now three freighters', cnt(23, 'F1').n === 3 && cnt(23, 'C1').pickup,
      'was ' + api.SCRIPT_WAVES[23].u.find(u => u.id === 'F1').n);
check('M027: transports unchanged', cnt(27, 'T1').n === 1 && !cnt(27, 'A1').pickup);
check('mission data itself untouched', api.SCRIPT_WAVES[23].u.find(u => u.id === 'F1').n === 2);

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
