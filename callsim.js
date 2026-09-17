// Support call menu simulation. Pulls the REAL functions out of the logic
// file and runs them against stand-ins for the world, to check the faction
// gating and the layout that follows from it.
// Usage: node callsim.js <logic.html>
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

const defs   = decl(/const ALLY_DEFS = \{[\s\S]*?\n\};/);
const order  = decl(/const ALLY_ORDER = \[[\s\S]*?\];/);
const keys   = decl(/const ALLY_KEYS  = \[[\s\S]*?\];/);
const terN   = decl(/const ALLY_TER_N = \d+;/);
const spec   = decl(/const ALLY_SPECIAL = '[a-z]+';/);
const specK  = decl(/const ALLY_SPECIAL_KEY = '[A-Z]';/);
const facOn  = decl(/const ALLY_FAC_ON = \{[^}]*\};/);
const colT   = decl(/const COLOSSUS_TIME = \d+;/);
const refine = decl(/const REFINE_COST = \d+;/);

const names = ['allyFacOn', 'callCols', 'allyTicket', 'canRefine', 'drawCallMenu', 'callAlly'];

const ctxStub = new Proxy({}, {get: (t, k) => k in t ? t[k] : () => {}, set: (t, k, v) => { t[k] = v; return true; }});
const world = `
  const W=800, H=500;
  const ctx=CTX; const window={};
  let callMenu=true, allies=[], called=[], affordAll=true;
  let tickets={cruiser:9, corvette:9, destroyer:9, colossus:9};
  const HULL={cruiser:1200, corvette:1800, destroyer:2600};
  const STATS={escortsCalled:0};
  function capHull(v){ return Math.round(v); }
  function allyReady(){ return true; }
  function allyAffordable(id){ return affordAll; }
  function mkAlly(id){ return {id:id}; }
  function initSubsystems(){}
  function assignStation(){}
  function setCallMenu(){}
  let capBomberCd=0; const CAP_BOMBER_DELAY=0;
  ${defs}
  ${order}
  ${keys}
  ${terN}
  ${spec}
  ${specK}
  ${facOn}
  ${colT}
  ${refine}
  const REFINE_UP={cruiser:'corvette', corvette:'destroyer', destroyer:'colossus'};
  ${names.map(fn).join('\n')}
  return {get:(k)=>eval(k), set:(k,v)=>eval(k+'=v'), run:(code)=>eval(code)};`;

const W = new Function('CTX', world)(ctxStub);
let fails = 0;
function ok(label, cond){ console.log((cond ? '  ok    ' : '  FAIL  ') + label); if(!cond) fails++; }

const rects = () => { W.run('drawCallMenu()'); return W.run('window._callRects') || []; };
const ids   = () => rects().filter(r => r.id).map(r => r.id);
const boxes = () => rects().filter(r => r.id);

console.log('This cycle: Vasudan only');
ok('one column of entries', W.run('callCols().length') === 1);
ok('five Vasudan entries in it', W.run('callCols()[0].length') === 5);
ok('no Terran ship is offered', ids().every(id => id.indexOf('ter_') !== 0));
ok('all five Vasudan ships are offered',
   ['vas_aten', 'vas_mentu', 'vas_sobek', 'vas_typhon', 'vas_hatshepsut'].every(id => ids().indexOf(id) >= 0));
ok('the Colossus keeps her own row', ids().indexOf('colossus') >= 0);
ok('their keys stay Q W E R T', W.run('callCols()[0]').map(e => e.key).join('') === 'QWERT');

console.log('Layout');
ok('everything stays on the 800x500 field',
   boxes().every(r => r.x >= 0 && r.y >= 0 && r.x + r.w <= 800 && r.y + r.h <= 500));
ok('no two entries overlap', (() => {
  const b = boxes();
  for(let i = 0; i < b.length; i++) for(let j = i + 1; j < b.length; j++){
    const a = b[i], c = b[j];
    if(a.x < c.x + c.w && c.x < a.x + a.w && a.y < c.y + c.h && c.y < a.y + a.h) return false;
  }
  return true;
})());
ok('the Colossus row sits below the last entry', (() => {
  const col = boxes().find(r => r.id === 'colossus');
  return boxes().filter(r => r.id !== 'colossus').every(r => r.y + r.h <= col.y);
})());
ok('the menu is narrower than the two column version was',
   Math.max(...boxes().map(r => r.x + r.w)) < 620);

console.log('The gate holds where it matters');
W.run("called=[]; callAlly('ter_orion')");
ok('a Terran destroyer cannot be called', W.get('STATS').escortsCalled === 0);
W.run("callAlly('vas_typhon')");
ok('a Vasudan destroyer can', W.get('STATS').escortsCalled === 1);
W.run("callAlly('colossus')");
ok('the Colossus can, she is GTVA', W.get('STATS').escortsCalled === 2);
W.run("callAlly('ter_fenris')");
ok('nor a Terran cruiser', W.get('STATS').escortsCalled === 2);

console.log('Ticket classes still have somewhere to go');
{
  const offered = W.run('callCols()[0]').map(e => W.run(`allyTicket('${e.id}')`));
  offered.push(W.run("allyTicket('colossus')"));
  ok('cruiser, corvette, destroyer and colossus tickets can all be spent',
     ['cruiser', 'corvette', 'destroyer', 'colossus'].every(k => offered.indexOf(k) >= 0));
}

console.log('Switching a faction back on, as a later cycle would');
W.run("ALLY_FAC_ON.terran=true");
ok('two columns again', W.run('callCols().length') === 2);
ok('eleven entries plus the Colossus', ids().length === 12);
ok('still on the field',
   boxes().every(r => r.x >= 0 && r.y >= 0 && r.x + r.w <= 800 && r.y + r.h <= 500));
W.run("called=[]; STATS.escortsCalled=0; callAlly('ter_orion')");
ok('and the Terran destroyer answers now', W.get('STATS').escortsCalled === 1);
W.run("ALLY_FAC_ON.terran=false");

console.log('With nothing affordable');
W.run('affordAll=false');
ok('no entry is tappable, and nothing crashes', rects().filter(r => r.id).length === 0);
W.run('affordAll=true');

console.log('\n' + (fails ? fails + ' FAILED' : 'all passed'));
process.exit(fails ? 1 : 0);
