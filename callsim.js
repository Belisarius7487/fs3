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

const names = [
  
  'insidePanel',
  'thChamferPath','thPlate','thGlowPath','thBrackets','thScale','thFrame','thRGBA','thGloss','thCutGlint','allyFacOn', 'callCols', 'allyTicket', 'canRefine', 'drawCallMenu', 'callAlly',
  'mountsFor', 'spriteFacing', 'drawHullBg',
  'TH','thLabel','thValue','thBevel','thGlow','thPanel','UI','uiHLP','uiLabel','uiValue','uiCell','uiDialog'];
const menuBgDecl = decl(/const MENU_BG_ALPHA[\s\S]*?const MENU_BG_PAD\s*=\s*[\d.]+;/);
const themesDecl = decl(/const THEMES = \{[\s\S]*?\n\};/);

const CALLS = [];
const ctxStub = new Proxy({}, {
  get:(t,k)=> k in t ? t[k] : function(){
    CALLS.push({fn:String(k), args:[].slice.call(arguments)});
    // createLinearGradient has to hand back something with addColorStop.
    if(k==='createLinearGradient') return {addColorStop:function(){}};
  },
  set:(t,k,v)=>{ CALLS.push({fn:'set '+String(k), args:[v]}); t[k]=v; return true; }
});
// Helpers over the recorded drawing calls.
const CLR    = ()=>{ CALLS.length = 0; };
const draws  = ()=> CALLS.filter(c=>c.fn==='drawImage');
const clips  = ()=> CALLS.filter(c=>c.fn==='clip');
const alphas = ()=> CALLS.filter(c=>c.fn==='set globalAlpha').map(c=>c.args[0]);
// Every sprite has to sit inside a save/restore pair, otherwise its clip and
// its alpha leak into whatever is drawn next.
function balanced(){
  let d = 0, okAll = true;
  for(const c of CALLS){
    if(c.fn==='save') d++;
    else if(c.fn==='restore'){ d--; if(d<0) okAll=false; }
    else if((c.fn==='drawImage' || c.fn==='clip') && d<1) okAll=false;
  }
  return okAll && d===0;
}

const world = `
  const W=800, H=500;
  const ctx=CTX; const window={};
  let callMenu=true, allies=[], called=[], affordAll=true;
  let tickets={cruiser:9, corvette:9, destroyer:9, colossus:9};
  let IMGS={};
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
  ${themesDecl}
  let ECO={hud:'hlp', scheme:'fire'};
  ${menuBgDecl}
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

console.log('Hull sprites behind the rows');
const IMG = (w,h)=>({width:w, height:h});
W.set('IMGS', {});
CLR(); W.run('drawCallMenu()');
ok('nothing loaded yet: no sprite, no crash', draws().length===0 && rects().length>0);
W.set('IMGS', {craten:IMG(200,120), crmentu:IMG(200,120), cosobek:IMG(300,120),
               detyphon:IMG(420,150), dehatshepsut:IMG(420,150), sdcolossus:IMG(560,200)});
CLR(); W.run('drawCallMenu()');
ok('five Vasudan rows plus the Colossus row', draws().length===6);
// Each plate's gloss clips too, so this is at least one clip per hull.
ok('each one clipped to its row', clips().length>=6);
ok('each one fits inside its row', draws().every(d=>d.args[3]<=190-5 && d.args[4]<=38-5 && d.args[3]>0));
ok('save and restore stay balanced', balanced());
ok('faint, not opaque', alphas().every(a=>a>0 && a<0.4));
W.run('affordAll=false'); CLR(); W.run('drawCallMenu()');
ok('rows that cannot be paid for are dimmer', alphas().length===6 && alphas().every(a=>a===0.11));
W.run('affordAll=true');
W.set('IMGS', {});

console.log('The call menu draws');
CLR(); W.run('drawCallMenu()');
const hFonts = CALLS.filter(c=>c.fn==='set font').map(c=>String(c.args[0]));
const cRects = rects().filter(r=>r.id).map(r=>r.id+':'+r.x+','+r.y).join('|');
ok('no Courier left in it', hFonts.every(f=>f.indexOf('Courier')<0));
ok('every row reports a place of its own', cRects.length>0);
ok('the Colossus row gets the full ring', CALLS.some(c=>c.fn==='set shadowBlur'));
ok('nothing leaks out of a save/restore', balanced());
W.run("ECO.scheme='void'"); CLR(); W.run('drawCallMenu()');
ok('it draws in Void as well', CALLS.length>50);
W.run("ECO.scheme='fire'");

console.log('The call menu swallows its own clicks too');
{
  W.run('drawCallMenu()');
  const pr = W.run('window._callPanelRect');
  ok('the panel reports its outline', pr && pr.w>0 && pr.h>0);
  // pointerConsumed asks insidePanel before it closes anything, so this is
  // the decision itself: on the header yes, beside the panel no.
  ok('the header counts as inside',
     W.run(`insidePanel(window._callPanelRect,{x:${pr.x+30},y:${pr.y+5}})`)===true);
  ok('a gap below the last row counts as inside',
     W.run(`insidePanel(window._callPanelRect,{x:${pr.x+30},y:${pr.y+pr.h-3}})`)===true);
  ok('beside the panel does not',
     W.run(`insidePanel(window._callPanelRect,{x:${pr.x-14},y:${pr.y+pr.h/2}})`)===false);
}

console.log('\n' + (fails ? fails + ' FAILED' : 'all passed'));
process.exit(fails ? 1 : 0);
