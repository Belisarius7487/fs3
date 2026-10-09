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
  'syncCursor','hovering',
  'panelOpen','holdResume','clearResumeHold','drawResumeHint',
  'applyLoadout','rearmFull','curPri','curSec','priDef','secDef','hullSecCls',
  'weaponName','weaponOpen','waveReached','secRounds','corvetteOnField',
  'rearmReady','setRearmMenu','toggleRearmMenu','fitWeapon','rearmLayout',
  'drawRearmMenu','drawRearmIcon','rmPri','rmDef','rmBankKey','rmDps','rmBankDmg','rmValueOf','rmReach','rmFacts','rmBars','rmShipLines','rmSelectBank','rmStep','drawRearmShip','rmWrap','hgName','drawDoneButton','closeKeys','drawInfoCard','hangarCard','allyCard','allyLabel','tickWeaponUnlocks',
  'thFit','callMenuLayout','drawAllyRow','drawKeyChip','drawHullCell',
  
  'insidePanel',
  'thChamferPath','thPlate','thGlowPath','thButton','btnState','btnText','thBevel','thGlow','thBrackets','thScale','thFrame','thRGBA','thGloss','thCutGlint','allyFacOn', 'callCols', 'allyTicket', 'canRefine', 'drawCallMenu', 'callAlly',
  'mountsFor', 'spriteFacing', 'drawHullBg',
  'TH','thLabel','thValue','thBevel','thGlow','thPanel','UI','uiHLP','uiLabel','uiValue','uiCell','uiDialog'];
const menuBgDecl = decl(/const MENU_BG_ALPHA[\s\S]*?const MENU_BG_PAD\s*=\s*[\d.]+;/);
// The support menu's own measurements, from CM_W down to the faction headings.
const callDecl   = decl(/const CM_W[\s\S]*?const CM_FAC_HEAD = \{[^}]*\};/);
// drawHullCell and drawKeyChip are shared with the hangar, so its measurements
// have to come along.
const hangarDecl = decl(/const HG_W[\s\S]*?\n\];/);
const themesDecl = decl(/const THEMES = \{[\s\S]*?\n\};/);
// The weapon tables and the rearm panel's measurements.
const wpnDecl  = decl(/const PLAYER_FR_BASE[\s\S]*?\n\];/);
// v186: the FS2 arsenal and the banks (56_banks.js), the AI's old tables.
const wpnDecl2 = (function(){
  const a = src.indexOf('// ── WEAPON BANKS (v186)');
  const b = src.indexOf('\nfunction empBurst(');
  const ai = src.match(/const AI_SECONDARIES = \[[\s\S]*?\n\];/)[0];
  const aip = src.match(/const AI_PRIMARIES = \{[\s\S]*?\n\};/)[0];
  return src.slice(a, b) + '\n' + ai + '\n' + aip + '\nconst SECONDARIES = ARSENAL_S;\n';
})();
const rmDecl   = decl(/const RM_W[\s\S]*?const RM_BARS = \[[\s\S]*?\n\];/);
// pointerConsumed reaches for the title on a finished run. Starting a run
// is not what these files test, so it is a stub.
const wpnState = 'let rearmMenu = false; let resumeHold = false;'
  // The bar asks where the pointer is sitting; nothing hovers in a test.
  + ' const HOVER = {x:-1, y:-1}; function toTitleOrLaunch(){}; const WPN_SEEN = {}; const UI_WEAPONS = false;';


const CALLS = [];
const ctxStub = new Proxy({}, {
  get:(t,k)=> k in t ? t[k] : function(){
    CALLS.push({fn:String(k), args:[].slice.call(arguments)});
    // createLinearGradient has to hand back something with addColorStop.
    if(k==='createLinearGradient') return {addColorStop:function(){}};
    // thFit measures before it cuts, so the stub has to answer with a width.
    // Roughly 0.55 of the set point size per character is close enough for
    // the layout decisions being checked here.
    if(k==='measureText'){
      const px = parseFloat(String(t.font||'10px').replace(/^bold\s+/,'')) || 10;
      return {width: String(arguments[0]||'').length * px * 0.55};
    }
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
  // The practice log is not what is tested here.
  function plogCall(){} function plogRefine(){}
  function capHull(v){ return Math.round(v); }
  function allyHull(d){ return capHull(HULL[d.cls]); }
  function allyReady(){ return true; }
  function allyAffordable(id){ return affordAll; }
  // v202: support is paid in points
  let score = 1e9; function allyCost(id){ return 1; }
  function mkAlly(id){ return {id:id}; }
  function initSubsystems(){}
  function assignStation(){}
  function setCallMenu(){}
  let capBomberCd=0; const CAP_BOMBER_DELAY=0;
  // One fleet per cycle here; the Shivan cycle's tabs are fieldsim's.
  function cycleTabs(){ return false; }
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
  ${wpnDecl}
  ${wpnDecl2}
  ${rmDecl}
  ${wpnState}
  let ECO={hud:'hlp', scheme:'fire'};
  ${menuBgDecl}
  ${callDecl}
  ${hangarDecl}
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
// The panel used to be as wide as its columns, which is how the Colossus
// line of text came to be wider than the panel it sat in. The width is fixed
// now, and that is the thing to hold on to.
ok('the panel keeps one width whatever is on call',
   W.run('window._callPanelRect').w === W.run('CM_W'));
// v192: the list keeps the left part, the info card the right.
ok('the Colossus row runs the full width of the list', (() => {
  const col = boxes().find(r => r.id === 'colossus');
  return col && Math.abs(col.w - W.run('CM_LIST_W')) <= 1;
})());

console.log('No label can leave the panel');
W.run('callMenu=true');
// Walk the recorded calls in order, carrying the font and the alignment that
// were set before each one, and work out where every string actually ends.
// This is what thFit exists to guarantee, so it is what gets checked.
const spans = ()=>{
  let font='10px', align='left';
  const out=[];
  for(const c of CALLS){
    if(c.fn==='set font') font=String(c.args[0]);
    else if(c.fn==='set textAlign') align=String(c.args[0]);
    else if(c.fn==='fillText'){
      const px = parseFloat(font.replace(/^bold\s+/,'')) || 10;
      const w  = String(c.args[0]).length*px*0.55;
      const x  = c.args[1];
      const l  = align==='right' ? x-w : (align==='center' ? x-w/2 : x);
      out.push({s:String(c.args[0]), l:l, r:l+w});
    }
  }
  return out;
};
{
  CLR(); W.run('drawCallMenu()');
  const pr = W.run('window._callPanelRect');
  ok('every string starts and ends inside the panel',
     spans().every(t => t.l >= pr.x-1 && t.r <= pr.x+pr.w+1));
  ok('the Colossus line is among them', spans().some(t => t.s.indexOf('station') >= 0));
}
{
  // A deliberately impossible label: thFit has to cut it rather than let it
  // run, and what is left has to end in the ellipsis.
  W.run("ALLY_DEFS.vas_aten.label='PVC Aten '+'Of An Unreasonable Length '.repeat(6)");
  CLR(); W.run('drawCallMenu()');
  const pr = W.run('window._callPanelRect');
  ok('an over long name is cut, not allowed to run',
     spans().every(t => t.r <= pr.x+pr.w+1));
  ok('and it is marked as cut', spans().some(t => t.s.indexOf('\u2026') >= 0));
  W.run("ALLY_DEFS.vas_aten.label='PVC Aten'");
}
{
  // thFit on its own, so the guarantee is checked and not just its effect
  // in one particular layout.
  W.run("ctx.font=thValue(13,true)");
  ok('what fits is left alone', W.run("thFit('PVC Aten', 400)")==='PVC Aten');
  const cut = W.run("thFit('PVC Aten Of An Unreasonable Length', 60)");
  ok('what does not fit is cut', cut.length < 'PVC Aten Of An Unreasonable Length'.length);
  ok('and marked as cut', cut.indexOf('\u2026') >= 0);
  ok('a width of zero yields nothing rather than a crash', W.run("thFit('anything', 0)")==='');
}

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
// v192: plus one bigger picture in the info card
const rowDraws = ()=> draws().filter(d=>d.args[3]<=W.run('CM_PIC_W')-5);
ok('five Vasudan rows plus the Colossus row, and the card', rowDraws().length===6 && draws().length===7);
// Each plate's gloss clips too, so this is at least one clip per hull.
ok('each one clipped to its row', clips().length>=6);
// The picture has its own cell now, the same one the hangar uses.
ok('each one fits inside its picture cell',
   rowDraws().every(d=>d.args[4]<=W.run('CM_ROW')-6-5 && d.args[3]>0));
ok('save and restore stay balanced', balanced());
ok('a portrait now, not a watermark', alphas().every(a=>a>0.9 && a<=1));
W.run('affordAll=false'); CLR(); W.run('drawCallMenu()');
ok('rows that cannot be paid for are dimmer',
   alphas().filter(a=>a===W.run('HG_PIC_ALPHA_OFF')).length===6);
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

console.log('Keys (v194)');
ok('the Colossus is called with G, not C (C closes the window)', W.run('ALLY_SPECIAL_KEY') === 'G');
ok('G is no other row\'s key', W.run('ALLY_KEYS').indexOf('G') < 0);

console.log('DONE (v194)');
{
  W.run('drawCallMenu()');
  const all = rects(), done = all.filter(r => r.close), rows = all.filter(r => r.id);
  const pr = W.run('window._callPanelRect');
  ok('one DONE button', done.length === 1);
  const d = done[0] || {};
  ok('inside the panel and on the field',
     d.x >= pr.x && d.x+d.w <= pr.x+pr.w && d.y+d.h <= pr.y+pr.h && pr.y >= 0 && pr.y+pr.h <= 500);
  ok('below every entry, the Colossus row too', rows.every(r => r.y+r.h <= d.y-4));
}

console.log('\n' + (fails ? fails + ' FAILED' : 'all passed'));
process.exit(fails ? 1 : 0);
