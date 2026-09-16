// Non-combatant rule test (v103). Pulls the real targeting functions out of
// the logic file. The hit loops sit inline in update() and are not run here.
// Usage: node nctest.js hlp_shooter_v103_logic.html
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
  ${['playerOnly','nearestEnemy','nearestOf','isLargeShip','isSmallShip'].map(fn).join('\n')}
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

check('allied bolts pass through (both hit loops patched)',   (src.match(/if\(b\.ally && playerOnly\(e\)\) continue;/g) || []).length === 2);
console.log('\n' + pass + ' passed, ' + fail + ' failed'); process.exit(fail ? 1 : 0);
