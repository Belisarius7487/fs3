// Pause and panel state simulation. Pulls the REAL menu and settings
// functions out of the logic file and replays tap sequences against them,
// looking for a state the player can reach where a panel is open while the
// game keeps running.
//
// The tap order below mirrors the mousedown and touchstart handlers, which
// live inside addEventListener closures and cannot be pulled out. If that
// order changes in the logic file, this mirror has to change with it.
//
// Usage: node pausesim.js <logic.html>
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
function fn(name, optional){
  const i = src.indexOf('\nfunction ' + name + '(');
  if(i < 0){ if(optional) return ''; throw new Error('missing function ' + name); }
  return src.slice(i + 1, blockEnd(src, i));
}

// The weapon tables and the rearm panel's measurements, so the bar and the
// pause logic can see what they now reach for.
const wpnDecl  = src.match(/const PLAYER_FR_BASE[\s\S]*?\n\];/)[0];
const wpnDecl2 = src.match(/const SECONDARIES = \[[\s\S]*?\n\];/)[0];
const rmDecl   = src.match(/const RM_W[\s\S]*?const RM_COLS_SEC = \[[\s\S]*?\n\];/)[0];
// pointerConsumed reaches for the title on a finished run. Starting a run
// is not what these files test, so it is a stub.
const wpnState = 'let rearmMenu = false; let resumeHold = false;'
  // The bar asks where the pointer is sitting; nothing hovers in a test.
  + ' const HOVER = {x:-1, y:-1}; function toTitleOrLaunch(){}; const WPN_SEEN = {}; const UI_WEAPONS = false;';
const names = [
  'syncCursor','hovering',
  'panelOpen','holdResume','clearResumeHold','drawResumeHint',
  'applyLoadout','rearmFull','curPri','curSec','priDef','secDef','hullSecCls',
  'weaponName','weaponOpen','secondariesFor','defaultSec','corvetteOnField',
  'rearmReady','setRearmMenu','toggleRearmMenu','fitWeapon','rearmLayout',
  'drawRearmMenu','drawRearmIcon','rearmGroups','rmValue','tickWeaponUnlocks',
  'insidePanel',
  'thChamferPath','thPlate','thGlowPath','thBrackets','thScale','thFrame','thRGBA','thGloss','thCutGlint','setShipMenu', 'toggleShipMenu', 'shipSwapReady', 'setCallMenu', 'toggleCallMenu',
               'setSettings', 'pointerConsumed', 'shipOffered', 'shipFac', 'hullFac',
               'hangarFacs', 'isHangarShip', 'colossusOnField', 'hangarServes', 'hullClass'];
const optional = ['syncPause'];

const world = `
  const W=800, H=500, HUD_H=54;
  let GS='playing', paused=false, userPaused=false;
  let shipMenu=false, callMenu=false, settingsOpen=false, settingsPage=0;
  let settingsWasPaused=false, shipUnlocked=3, shipSwapWave=-1, wave=1;
  let FS1_MODE=false, allies=[], MOUSE={x:0,y:0};
  let empOut=0, allyCd=0, tickets={cruiser:9}, GEAR_OK=true;
  const document={body:{classList:{add(){}, remove(){}}}};
  const window={};
  const HULL_FAC={detyphon:'vasudan', dehatshepsut:'vasudan', deorionright:'terran', sdcolossus:'gtva'};
  const PLAYER_SHIPS=[{key:'fitoth', fac:'vasudan'}, {key:'fihorus', fac:'vasudan'}, {key:'boosiris', fac:'vasudan'}];
  let forcedPrev='';   // no mission-lent hull in these tests
  let player={ship:'fitoth', x:400, y:250};
  function inJump(){ return false; }
  function allyReady(){ return true; }
  function swapShip(){}
  function refineTicket(){}
  function callAlly(){}
  function settingsClick(){}
  function fireSecondary(){}
  ${wpnDecl}
  ${wpnDecl2}
  ${rmDecl}
  ${wpnState}
  ${names.map(n=>fn(n)).join('\n')}
  ${optional.map(n=>fn(n, true)).join('\n')}
  // The three HUD buttons, laid out as the bar does.
  window._shipBtnRect  = {x:600, y:10, w:40, h:34};
  window._allyBtnRect   = {x:655, y:10, w:40, h:34};
  window._settingsBtnRect = {x:748, y:10, w:40, h:34};
  window._pauseBtnRect  = {x:700, y:10, w:40, h:34};
  // Mirror of the handler order in mousedown / touchstart.
  function tap(x, y){
    const p={x:x, y:y};
    const hit=(r)=> r && p.x>=r.x && p.x<=r.x+r.w && p.y>=r.y && p.y<=r.y+r.h;
    if(pointerConsumed(p)) return;
    if(settingsOpen){ settingsClick(p.x,p.y); return; }
    if(hit(window._settingsBtnRect)){ setSettings(true); return; }
    if(hit(window._pauseBtnRect)){
      // After the fix the pause button owns its own flag; before it, it
      // wrote the shared one.
      if(typeof syncPause === 'function'){ userPaused=!userPaused; syncPause(); }
      else paused=!paused;
      return;
    }
    if(hit(window._secBtnRect)){ fireSecondary(); return; }
  }
  return {get:(k)=>eval(k), set:(k,v)=>eval(k+'=v'), run:(code)=>eval(code)};`;

const W = new Function(world)();
const fixed = W.run("typeof syncPause === 'function'");
let fails = 0;
function ok(label, cond){ console.log((cond ? '  ok    ' : '  FAIL  ') + label); if(!cond) fails++; }

const GEAR  = [768, 27];
const PAUSE = [720, 27];
const SHIPB = [620, 27];
const FIELD = [400, 300];

function reset(){
  W.run("shipMenu=false; callMenu=false; settingsOpen=false; paused=false; userPaused=false; settingsWasPaused=false; window._shipRects=[]; window._callRects=[];");
  W.set('allies', [{img:'detyphon', small:false, dead:false, warpOut:false}]);
}
// A panel on screen while the game keeps running is the failure we look for.
function broken(){
  const s = W.run("({paused:paused, shipMenu:shipMenu, callMenu:callMenu, settingsOpen:settingsOpen})");
  return (s.settingsOpen || s.shipMenu || s.callMenu) && !s.paused;
}
function state(){
  const s = W.run("({paused:paused, shipMenu:shipMenu, callMenu:callMenu, settingsOpen:settingsOpen})");
  return (s.shipMenu?'ship ':'') + (s.callMenu?'call ':'') + (s.settingsOpen?'settings ':'')
       + (s.paused?'PAUSED':'running');
}

console.log(fixed ? 'Logic file has the derived pause' : 'Logic file writes pause from several places');

console.log('\nOpening a panel has to stop the game');
reset(); W.run('toggleShipMenu()');
ok('switch menu pauses', W.get('paused')===true && W.get('shipMenu')===true);
reset(); W.run('toggleCallMenu()');
ok('call menu pauses', W.get('paused')===true);
reset(); W.run('setSettings(true)');
ok('settings pauses', W.get('paused')===true);

console.log('\nThe tap sequence from the report');
reset(); W.run('toggleShipMenu()');
W.run(`tap(${GEAR[0]}, ${GEAR[1]})`);
const afterOne = state();
W.run(`tap(${GEAR[0]}, ${GEAR[1]})`);
console.log('    after one tap on the gear:  ' + afterOne);
console.log('    after the second tap:       ' + state());
ok('a stylus tap counted twice does not leave a panel over a running game', !broken());

console.log('\nEvery order of two panels');
const acts = {
  'open switch menu': 'toggleShipMenu()',
  'open call menu':   'toggleCallMenu()',
  'open settings':    'setSettings(true)',
  'close settings':   'setSettings(false)',
  'tap the gear':     `tap(${GEAR[0]}, ${GEAR[1]})`,
  'tap pause':        `tap(${PAUSE[0]}, ${PAUSE[1]})`,
  'tap the ship button': `tap(${SHIPB[0]}, ${SHIPB[1]})`,
  'tap the field':    `tap(${FIELD[0]}, ${FIELD[1]})`
};
const keys = Object.keys(acts);
let bad = [];
for(const a of keys) for(const b of keys) for(const c of keys){
  reset();
  W.run(acts[a]); W.run(acts[b]); W.run(acts[c]);
  if(broken()) bad.push(a + ' -> ' + b + ' -> ' + c + '  =  ' + state());
}
if(bad.length){
  console.log('    ' + bad.length + ' of ' + keys.length**3 + ' sequences leave a panel over a running game, e.g.');
  for(const b of bad.slice(0,6)) console.log('      ' + b);
}
ok('no sequence of three actions leaves a panel over a running game', bad.length===0);

console.log('\nClosing everything has to give the game back');
reset(); W.run('toggleShipMenu()'); W.run('setShipMenu(false)');
// Closing a panel no longer hands the game straight back: it is held until
// one further tap, the same for every panel and every way of leaving one.
ok('closing the switch menu holds rather than resumes',
   W.get('paused')===true && W.get('resumeHold')===true);
W.run('clearResumeHold()');
ok('and the tap gives the game back', W.get('paused')===false);
reset(); W.run('clearResumeHold()'); W.run(`tap(${PAUSE[0]}, ${PAUSE[1]})`);
ok('the pause button still pauses on its own', W.get('paused')===true);
W.run('setSettings(true)'); W.run('setSettings(false)');
ok('settings opened and closed on top of a manual pause keeps the pause', W.get('paused')===true);
reset(); W.run('setSettings(true)'); W.run('setSettings(false)');
ok('settings opened and closed without a manual pause resumes', W.get('paused')===false);

console.log('\n' + (fails ? fails + ' FAILED' : 'all passed'));
process.exit(fails ? 1 : 0);
