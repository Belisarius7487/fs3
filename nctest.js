// Non-combatant rule test (v103). Pulls the real targeting functions out of
// the logic file. The hit loops sit inline in update() and are not run here.
// Usage: node nctest.js hlp_shooter_vNNN_logic.html
//
// playerOnly() has called freighterArmed() since v203, and that one asks
// mountsFor(), so both are lifted out as well. mountsFor() returns null
// while MOUNTS is undefined, which is what an unarmed freighter needs here.
// Whenever a checked function starts calling a new one, it belongs in the
// list below, or the test stops with "x is not defined".
const fs = require('fs');
const src = fs.readFileSync(process.argv[2] || 'hlp_shooter_v103_logic.html', 'utf8').match(/<script[^>]*>([\s\S]*)<\/script>/)[1];
function fn(name){
  const at = src.indexOf('function ' + name + '('); let i = src.indexOf('{', at), d = 0;
  for(; i < src.length; i++){ const c = src[i];
    if(c === '/' && src[i+1] === '/'){ i = src.indexOf('\n', i); continue; }
    if(c === "'" || c === '"'){ const q = c; i++; while(src[i] !== q){ if(src[i] === '\\') i++; i++; } continue; }
    if(c === '{') d++; else if(c === '}' && --d === 0) return src.slice(at, i + 1); }
}
const api = new Function(`
  let enemies = [], allies = [];
  const WPN = { fighter:{}, bomber:{}, cruiser:{} };
  // State the lifted functions read: no disguised wave is running here, so
  // coverHolds() is false and nearestOf() treats every side as it looks.
  let waveDisguise = false, disguiseBlown = false;
  ${['playerOnly','freighterArmed','mountsFor','escortSpares','coverHolds','nearestEnemy','nearestOf','isLargeShip','isSmallShip'].map(fn).join('\n')}
  return { set(e, a){ enemies = e; allies = a; }, get enemies(){ return enemies; }, get allies(){ return allies; },
           playerOnly, nearestEnemy, nearestOf };`)();
let pass = 0, fail = 0;
const check = (n, ok) => { console.log((ok ? '  ok    ' : '  FAIL  ') + n); ok ? pass++ : fail++; };
const ship = (type, x, extra) => Object.assign({ type, x, y: 100, dead: false, warp: 0 }, extra);

check('container is player-only',  api.playerOnly(ship('container')));
check('freighter is player-only',  api.playerOnly(ship('freighter')));
check('fighter is not',            !api.playerOnly(ship('fighter')));
check('cruiser is not',            !api.playerOnly(ship('cruiser')));
check('sentry is not',             !api.playerOnly(ship('sentry')));

const cargo = ship('container', 10), frt = ship('freighter', 20), fig = ship('fighter', 300);
api.set([cargo, frt, fig], []);
check('allied guns skip cargo and freighter, take the fighter', api.nearestEnemy(0, 100) === fig);
check('allied escort search skips them too', api.nearestOf(api.enemies, { x: 0, y: 100 }, 'any') === fig);
api.set([cargo, frt], []);
check('with only non-combatants left, allies have no target', api.nearestEnemy(0, 100) === null);

const myCargo = ship('container', 10);
api.set([], [myCargo]);
check('hostile ships still target the player\'s own cargo', api.nearestOf(api.allies, { x: 0, y: 100 }, 'any') === myCargo);

// Allied fire has to pass through a non-combatant in EVERY loop that lets a
// bolt hit a hull, not in a fixed number of them. Counting the guards found
// two of them at v103 and kept passing while the game grew to four loops; a
// fifth one without the guard would not have shown up either. So the gate is
// paired with the guard: a bolt loop is the place that asks bulletOnHull(),
// and a loop that walks `enemies` has to skip the non-combatants in it.
//
// Loops over `allies` are left out on purpose. playerOnly() is a rule about
// ships in `enemies`; hostile fire is meant to reach the player's own cargo,
// which the check above holds.
const lineOf = (i) => src.slice(0, i).split('\n').length;
const GUARD = /b\.ally && playerOnly\(/;
let boltLoops = 0;
const unguarded = [];
for(const m of src.matchAll(/if\(!bulletOnHull\(/g)){
  const head = src.lastIndexOf('for(', m.index);
  if(head < 0) continue;
  const loopHeader = src.slice(head, src.indexOf(')', head) + 1);
  if(!/enemies/.test(loopHeader)) continue;   // not a loop over the enemy list
  boltLoops++;
  // Anywhere from the loop header down to just past the hit counts: some
  // loops skip them up front, some only for allied bolts.
  if(!/playerOnly\(/.test(src.slice(head, m.index + 240))) unguarded.push(lineOf(m.index));
}
check('every bolt hit loop over the enemy list skips non-combatants (' + boltLoops + ' loops)',
      boltLoops >= 2 && unguarded.length === 0);
if(unguarded.length) console.log('        no playerOnly() guard in the loop at script line(s): ' + unguarded.join(', '));

// The two loops that are not plain bolt hits carry the rule as well.
const body = (name) => { const a = src.indexOf('function ' + name + '('); if(a < 0) return '';
  let i = src.indexOf('{', a), d = 0;
  for(; i < src.length; i++){ if(src[i] === '{') d++; else if(src[i] === '}' && --d === 0) return src.slice(a, i + 1); }
  return ''; };
check('an allied warhead blast spares them (warheadBlast)', GUARD.test(body('warheadBlast')));
const seeker = src.indexOf('if(!canLockOn(enemies[j])) continue;');
check('an allied seeker does not lock onto them',
      seeker > 0 && GUARD.test(src.slice(seeker, seeker + 240)));

console.log('\n' + pass + ' passed, ' + fail + ' failed'); process.exit(fail ? 1 : 0);
